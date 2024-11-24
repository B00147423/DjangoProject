# api/user/views.py
from base64 import urlsafe_b64decode
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from .models import User
from django.utils.crypto import get_random_string
import random
import string
from django.contrib.auth.decorators import login_required
from .forms import ChangeUsernameForm, ChangeEmailForm, CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.validators import validate_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator as token_generator
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import re
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
# Correct imports for newer Django versions
from django.utils.encoding import force_bytes, force_str  # Add force_str here
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.http import JsonResponse

@login_required
def resend_verification_email(request):
    if request.user.is_verified:
        messages.success(request, "Your email is already verified.")
        return redirect('dashboard')

    # Generate a new verification link and send it again
    uid = urlsafe_base64_encode(force_bytes(request.user.pk))
    token = default_token_generator.make_token(request.user)
    verification_link = f"http://{request.get_host()}/user/verify/{uid}/{token}/"

    subject = "Verify Your Email Address"
    message = f"Please verify your email by clicking the link below: {verification_link}"
    from_email = settings.DEFAULT_FROM_EMAIL  # Set this to your verified email
    send_mail(subject, message, from_email, [request.user.email])

    messages.info(request, "A new verification email has been sent. Please check your inbox.")
    return redirect('pending_verification')  # Redirect back to pending verification page

@login_required
def pending_verification(request):
    # If the user is verified, redirect them to the dashboard
    if request.user.is_verified:
        return redirect('dashboard')
    # Otherwise, show the pending verification page
    return render(request, 'user/pending_verification.html')  # Correct path


@login_required
def verify_email(request, uidb64, token):
    try:
        # Decode the Base64 user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(f"User found: {user}")  # Debug: Confirm the user was found
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f"Error decoding UID or finding user: {str(e)}")  # Debug error
        user = None

    # Verify the token and user
    if user is not None and default_token_generator.check_token(user, token):
        try:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                user.is_verified = True  # Update verification status
                user.save()  # Save the user
                print(f"Verification updated for {user.email}")  # Debug success

            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Your email has been verified!")
            return redirect('dashboard')  # Redirect to dashboard
        except Exception as e:
            print(f"Error during verification: {str(e)}")  # Debug transaction failure
            messages.error(request, "There was an error verifying your account.")
            return redirect('auth_page')
    else:
        print("Invalid token or user does not exist.")  # Debug invalid token
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect('auth_page')
    
def send_verification_email(user, request):
    # Generate a token for the user
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Build the verification link
    verification_link = f"http://{request.get_host()}/user/verify/{uid}/{token}/"

    # Prepare email content
    subject = "Verify Your Email Address"
    message = render_to_string('user/verification_email.html', {
        'user': user,
        'verification_link': verification_link
    })

    # Send email using SendGrid
    try:
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,  # Use verified email
            to_emails=user.email,
            subject=subject,
            html_content=message
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

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
                return redirect('dashboard')

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
                return redirect('dashboard')

            except User.DoesNotExist:
                # Edge Case 9: Email not registered
                return render(request, 'user/auth_page.html', {'error_message': 'Invalid email or password.', 'form': 'signin'})

        elif form_type == 'guest_login':
            # Handle guest login
            user = get_guest_from_cookie(request)

            if user:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('dashboard')
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

                response = redirect('dashboard')
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
    response = redirect('auth_page')
    response.delete_cookie('guest_user')  # Remove the guest cookie

    return response

@login_required
def dashboard_page(request):
    user = request.user

    # Check if the user is verified
    if not user.is_verified:
        # Redirect the user to a pending verification page if the email is not verified
        return redirect('pending_verification')  # You can change this to any URL for the verification page

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
            messages.success(request, 'Your username has been updated.')
            return redirect('settings')
    else:
        form = ChangeUsernameForm(instance=request.user)
    return render(request, 'user/change_username.html', {'form': form})

@login_required
def change_email(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            # Save the new email and set 'is_verified' to False (email is unverified)
            new_email = form.cleaned_data['email']
            request.user.email = new_email
            request.user.is_verified = False  # Email is unverified at this stage
            request.user.save()

            # Send verification email
            send_verification_email(request.user, request)

            messages.success(request, 'Please check your email to confirm the change.')
            return redirect('settings')  # Redirect back to settings page

        else:
            # Log form errors for debugging
            print("Form errors: ", form.errors)
            messages.error(request, 'There was an issue updating your email. Please check the errors.')
    else:
        form = ChangeEmailForm(instance=request.user)

    return render(request, 'user/change_email.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('settings')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'user/change_password.html', {'form': form})

@login_required
def resend_verification_email(request):
    if request.user.is_verified:
        messages.success(request, "Your email is already verified.")
        return redirect('dashboard')

    # Resend the verification email
    send_verification_email(request.user, request)
    messages.info(request, "A new verification email has been sent. Please check your inbox.")
    return redirect('pending_verification')  # Redirect to the pending verification page

def verified_account(request):
    return render(request, 'user/verified_account.html')#

#test send email
def test_send_email(request):
    subject = "Test Email"
    message = "This is a test email from Django."
    from_email = settings.DEFAULT_FROM_EMAIL  # This should be your SendGrid email or any default email
    recipient_list = ["recipient@example.com"]  # Replace with your email

    send_mail(subject, message, from_email, recipient_list)
    return HttpResponse("Email sent successfully!")  # Or any response you'd like to return

@login_required
def pending_verification_status(request):
    # Check if the user's email is verified
    return JsonResponse({'is_verified': request.user.is_verified})