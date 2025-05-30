# api/user/views.py
from audioop import reverse
from .models import Profile
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from .models import User
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.validators import validate_email
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str  # Add force_str here
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.http import JsonResponse
from django.db.models.signals import post_save
from django.dispatch import receiver
from .forms import ChangeEmailForm, CustomPasswordChangeForm, ChangeUsernameForm, ProfileForm
from django.contrib.auth import update_session_auth_hash
import random
import string
import re
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ObjectDoesNotExist
import os

@login_required
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure the profile exists before trying to save it
        Profile.objects.get_or_create(user=instance)
    instance.profile.save()



@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        # Create profile if it doesn't exist
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect(reverse('user:profile_view'))
    else:
        profile_form = ProfileForm(instance=profile)

    return render(request, 'user/profile.html', {'profile_form': profile_form})

@login_required
def resend_verification_email(request):
    if request.user.is_verified:
        messages.success(request, "Your email is already verified.")
        return redirect('user:dashboard')

    # Generate a new verification link and send it again
    uid = urlsafe_base64_encode(force_bytes(request.user.pk))
    token = default_token_generator.make_token(request.user)
    verification_link = f"http://{request.get_host()}/user/verify/{uid}/{token}/"

    subject = "Verify Your Email Address"
    message = f"Please verify your email by clicking the link below: {verification_link}"
    from_email = settings.DEFAULT_FROM_EMAIL  # Set this to your verified email
    send_mail(subject, message, from_email, [request.user.email])

    messages.info(request, "A new verification email has been sent. Please check your inbox.")
    return redirect('user:pending_verification')  # Redirect back to pending verification page

@login_required
def pending_verification(request):
    # If the user is verified, redirect them to the dashboard
    if request.user.is_verified:
        return redirect('user:dashboard')
    # Otherwise, show the pending verification page
    return render(request, 'user/pending_verification.html')  # Correct path


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(f"Decoded UID: {uid}, User: {user}")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        print("Failed to decode UID or find user.")

    if user is not None:
        is_token_valid = default_token_generator.check_token(user, token)
        print(f"Token valid: {is_token_valid}")

        if is_token_valid:
            try:
                with transaction.atomic():
                    print("Marking user as verified...")
                    user.is_verified = True
                    user.save()
                    print("User marked as verified.")  # Debugging
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                print("User logged in successfully.")  # Debugging
                messages.success(request, "Your email has been verified!")
                return redirect('user:dashboard')
            except Exception as e:
                print(f"Error during transaction: {e}")  # Debugging
                messages.error(request, "There was an error verifying your account.")
                return redirect('user:auth_page')
        else:
            print("Token is invalid.")  # Debugging
    else:
        print("User is None or does not exist.")  # Debugging

    messages.error(request, "The verification link is invalid or has expired.")
    return redirect('user:auth_page')

    
def send_verification_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_link = f"http://{request.get_host()}/user/verify/{uid}/{token}/"

    subject = "Verify Your Email Address"
    message = render_to_string('user/verification_email.html', {
        'user': user,
        'verification_link': verification_link
    })

    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=user.email,
            subject=subject,
            html_content=message
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid Error: {str(e)}")
        return False


        
def validate_password_strength(password):
    # Ensure the password is at least 8 characters long, contains at least one digit, one uppercase letter, and one special character
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError("Password must contain at least one special character.")

def generate_guest_username():
    return f"guest_{get_random_string(8)}"

def set_guest_cookie(response, guest_username):
    response.set_cookie('guest_user', guest_username, max_age=30*24*60*60)

def get_guest_from_cookie(request):
    guest_username = request.COOKIES.get('guest_user')
    if guest_username:
        return User.objects.filter(username=guest_username).first()
    return None

@csrf_protect
@require_http_methods(["GET", "POST"])
def auth_page(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'signup':
            # Handle sign up
            try:
                username = request.POST.get('username')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                password = request.POST.get('password')

                # Edge Case 1: All fields are required
                if not all([username, first_name, last_name, email, password]):
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'All fields are required.',
                        'form': 'signup'  # Stay on the signup form
                    })

                # Edge Case 2: Username should be unique
                if User.objects.filter(username=username).exists():
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'Username is already taken.',
                        'form': 'signup'  # Stay on the signup form
                    })

                # Edge Case 3: Valid Email format
                try:
                    validate_email(email)
                except ValidationError:
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'Please enter a valid email address.',
                        'form': 'signup'  # Stay on the signup form
                    })

                # Edge Case 4: Email should be unique
                if User.objects.filter(email=email).exists():
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'An account with this email already exists.',
                        'form': 'signup'  # Stay on the signup form
                    })

                # Edge Case 5: Password strength
                try:
                    validate_password_strength(password)
                except ValidationError as e:
                    return render(request, 'user/auth_page.html', {
                        'error_message': str(e),
                        'form': 'signup'  # Stay on the signup form
                    })

                # Create the user and hash the password
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password
                )

                # Send email verification
                send_verification_email(user, request)

                # Log the user in after signup
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('user:dashboard')

            except Exception as e:
                print(f"Error during signup: {e}")  # Debugging
                return render(request, 'user/auth_page.html', {
                    'error_message': 'An error occurred. Please try again later.',
                    'form': 'signup'  # Stay on the signup form
                })

        elif form_type == 'signin':
            # Handle sign in
            email = request.POST.get('email')
            password = request.POST.get('password')

            # Edge Case 6: Both email and password are required
            if not email or not password:
                return render(request, 'user/auth_page.html', {
                    'error_message': 'Both email and password are required.',
                    'form': 'signin'
                })

            # Authenticate using email
            try:
                # Edge Case 7: Valid email format
                try:
                    validate_email(email)
                except ValidationError:
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'Please enter a valid email address.',
                        'form': 'signin'  # Stay on the signin form
                    })

                user = User.objects.get(email=email)

                # Edge Case 8: Check if the password matches
                if not user.check_password(password):
                    return render(request, 'user/auth_page.html', {
                        'error_message': 'Invalid email or password.',
                        'form': 'signin'  # Stay on the signin form
                    })

                # Set the backend attribute
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('user:dashboard')

            except User.DoesNotExist:
                # Edge Case 9: Email not registered
                return render(request, 'user/auth_page.html', {
                    'error_message': 'Invalid email or password.',
                    'form': 'signin'  # Stay on the signin form
                })

        elif form_type == 'guest_login':
            # Handle guest login
            guest_username = generate_guest_username()
            guest_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

            user = User.objects.create_user(
                username=guest_username,
                email=f'{guest_username}@guest.com',
                password=guest_password,
                is_guest=True,
                is_verified=True  # Ensure guest accounts are marked as verified
            )

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            response = redirect('user:dashboard')
            set_guest_cookie(response, guest_username)
            return response

        else:
            return render(request, 'user/auth_page.html', {
                'error_message': 'Invalid form submission.',
                'form': 'signin'  # Default to signin form
            })

    else:
        # Default to signin form on GET request
        return render(request, 'user/auth_page.html', {'form': 'signin'})

def logout_page(request):
    user = request.user

    logout(request)

    if getattr(user, 'is_guest', False):
        user.delete()

    response = redirect('user:auth_page')
    response.delete_cookie('guest_user')  

    return response

@login_required
def dashboard_page(request):
    user = request.user
    if not user.is_guest and not user.is_verified:
        return redirect('user:pending_verification')

    
    images_dir = os.path.join(
        settings.BASE_DIR, 'jigsaw_puzzle', 'static', 'jigsaw_puzzle', 'predefined_images'
    )
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_urls = [f'jigsaw_puzzle/predefined_images/{img}' for img in image_files]

    # Example mapping by filename
    CATEGORY_MAP = {
        # Animals
        'puppy': 'animals',
        'animaltwo': 'animals',
        'animalthree': 'animals',

        # Nature
        'natureone': 'nature',
        'naturetwo': 'nature',
        'naturethree': 'nature',

        # Art
        'artone': 'art',
        'arttwo': 'art',
        'artthree': 'art',
    }

    image_data = []
    for img in image_files:
        base = img.lower().split('.')[0]
        category = CATEGORY_MAP.get(base, 'all')
        image_data.append({'url': f'jigsaw_puzzle/predefined_images/{img}', 'category': category})

    context = {
        'is_guest': user.is_guest,
        'username': user.username,
        'image_urls': image_urls,
        'image_data': image_data,
    }
    return render(request, 'user/dashboard.html', context)

from django.shortcuts import render
from .forms import ChangeUsernameForm, ChangeEmailForm, CustomPasswordChangeForm

@login_required
def settings_page(request):
    context = {
        'change_username_form': ChangeUsernameForm(instance=request.user),
        'change_email_form': ChangeEmailForm(instance=request.user),
        'change_password_form': CustomPasswordChangeForm(request.user),
    }
    return render(request, 'user/settings.html', context)



@login_required
def change_username(request):
    if request.method == 'POST':
        form = ChangeUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Update session hash
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your username has been updated.')
            return redirect('user:settings')
        else:
            messages.error(request, 'There was an issue updating your username.')
    else:
        form = ChangeUsernameForm(instance=request.user)
    return render(request, 'user/change_username.html', {'form': form})



@login_required
def change_email(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            new_email = form.cleaned_data['email']
            request.user.email = new_email
            request.user.is_verified = False  # Mark email as unverified
            request.user.save()

            # Send the verification email
            if send_verification_email(request.user, request):
                messages.success(request, 'Please check your new email to verify the change.')
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')

            return redirect('user:settings')
        else:
            messages.error(request, 'There was an issue updating your email.')
    else:
        form = ChangeEmailForm(instance=request.user)

    return render(request, 'user/change_email.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        print("Processing password change...")
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            print("Password changed successfully!")
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('user:settings')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'There was an issue updating your password.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'user/change_password.html', {'form': form})


@login_required
def resend_verification_email(request):
    if request.user.is_verified:
        messages.success(request, "Your email is already verified.")
        return redirect('user:dashboard')

    try:
        if send_verification_email(request.user, request):
            messages.info(request, "A new verification email has been sent. Please check your inbox.")
        else:
            messages.error(request, "Failed to send the verification email. Please try again later.")
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")

    return redirect('user:pending_verification')

@login_required
def verified_account(request):
    return render(request, 'user/verified_account.html', {
        'username': request.user.username
    })

@login_required
def pending_verification_status(request):
    # Check if the user's email is verified
    return JsonResponse({'is_verified': request.user.is_verified})