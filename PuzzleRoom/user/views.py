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
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect(reverse('user:profile_view'))
    else:
        profile_form = ProfileForm(instance=request.user.profile)

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
        print(f"Decoded UID: {uid}, User: {user}")  # Debugging
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        print("Failed to decode UID or find user.")  # Debugging

    if user is not None:
        is_token_valid = default_token_generator.check_token(user, token)
        print(f"Token valid: {is_token_valid}")  # Debugging

        if is_token_valid:
            try:
                with transaction.atomic():
                    print("Marking user as verified...")  # Debugging
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
                    return render(request, 'user/auth_page.html', {'error_message': 'All fields are required.', 'form': 'signup'})

                # Edge Case 2: Username should be unique
                if User.objects.filter(username=username).exists():
                    return render(request, 'user/auth_page.html', {'error_message': 'Username is already taken.', 'form': 'signup'})

                # Edge Case 3: Valid Email format
                try:
                    validate_email(email)
                except ValidationError:
                    return render(request, 'user/auth_page.html', {'error_message': 'Please enter a valid email address.', 'form': 'signup'})

                # Edge Case 4: Email should be unique
                if User.objects.filter(email=email).exists():
                    return render(request, 'user/auth_page.html', {'error_message': 'An account with this email already exists.', 'form': 'signup'})

                # Edge Case 5: Password strength
                try:
                    validate_password_strength(password)
                except ValidationError as e:
                    return render(request, 'user/auth_page.html', {'error_message': str(e), 'form': 'signup'})

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

            except IntegrityError:
                return render(request, 'user/auth_page.html', {'error_message': 'Username or Email already exists', 'form': 'signup'})
            except Exception as e:
                return render(request, 'user/auth_page.html', {'error_message': 'An error occurred. Please try again later.', 'form': 'signup'})


        elif form_type == 'signin':
            # Handle sign in
            email = request.POST.get('email')
            password = request.POST.get('password')

            # Edge Case 6: Both email and password are required
            if not email or not password:
                return render(request, 'user/auth_page.html', {'error_message': 'Both email and password are required.', 'form': 'signin'})

            # Authenticate using email
            try:
                # Edge Case 7: Valid email format
                try:
                    validate_email(email)
                except ValidationError:
                    return render(request, 'user/auth_page.html', {'error_message': 'Please enter a valid email address.', 'form': 'signin'})

                user = User.objects.get(email=email)
                
                # Edge Case 8: Check if the password matches
                if not user.check_password(password):
                    return render(request, 'user/auth_page.html', {'error_message': 'Invalid email or password.', 'form': 'signin'})

                # Set the backend attribute
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('user:dashboard')

            except User.DoesNotExist:
                # Edge Case 9: Email not registered
                return render(request, 'user/auth_page.html', {'error_message': 'Invalid email or password.', 'form': 'signin'})

        elif form_type == 'guest_login':
            # Handle guest login
            user = get_guest_from_cookie(request)

            if user:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('user:dashboard')
            else:
                guest_username = generate_guest_username()
                guest_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

                user = User.objects.create_user(
                    username=guest_username,
                    email=f'{guest_username}@guest.com',
                    password=guest_password,
                    is_guest=True
                )

                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

                response = redirect('user:dashboard')
                set_guest_cookie(response, guest_username)
                return response

        else:
            return render(request, 'user/auth_page.html', {'error_message': 'Invalid form submission.'})

    else:
        return render(request, 'user/auth_page.html')

def logout_page(request):
    # Get the current user
    user = request.user

    # Log the user out
    logout(request)

    # If the user is a guest, delete their account
    if getattr(user, 'is_guest', False):
        user.delete()

    # Delete the guest cookie
    response = redirect('user:auth_page')
    response.delete_cookie('guest_user')  # Remove the guest cookie

    return response

@login_required
def dashboard_page(request):
    user = request.user

    # Check if the user is verified
    if not user.is_verified:
        # Redirect the user to a pending verification page if the email is not verified
        return redirect('user:pending_verification')  # You can change this to any URL for the verification page

    # If the user is verified, proceed to render the dashboard
    context = {
        'is_guest': user.is_guest,
        'username': user.username,
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
        print("Processing password change...")  # Debugging
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            print("Password changed successfully!")  # Debugging
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('user:settings')
        else:
            print("Form errors:", form.errors)  # Debugging
            messages.error(request, 'There was an issue updating your password.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'user/change_password.html', {'form': form})


@login_required
def resend_verification_email(request):
    # Check if the user is already verified
    if request.user.is_verified:
        messages.success(request, "Your email is already verified.")
        return redirect('user:dashboard')  # Redirect to the dashboard if already verified

    # Try sending the verification email
    try:
        if send_verification_email(request.user, request):
            messages.info(request, "A new verification email has been sent. Please check your inbox.")
        else:
            messages.error(request, "Failed to send the verification email. Please try again later.")
    except Exception as e:
        # Log the exception for debugging purposes
        print(f"Error sending verification email: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")

    # Redirect to the pending verification page
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