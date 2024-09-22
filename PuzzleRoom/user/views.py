# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\api\user\views.py
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django.views.decorators.http import require_http_methods

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods

from django.contrib.auth import logout
from django.shortcuts import redirect
# Import User from the correct models location
from .models import User  

@require_http_methods(["GET", "POST"])  # Allow both GET and POST requests
def signup_page(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not username or not first_name or not last_name or not email or not password:
                return JsonResponse({'error_message': 'All fields are required'}, status=400)

            if len(password) < 8:
                return JsonResponse({'error_message': 'Password must be at least 8 characters long'}, status=400)

            # Create the user and hash the password
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(password)  # Hashing password
            )

            # Optionally log the user in after signup
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)

            # Redirect to the sign-in page after signup
            return redirect('login_page')  # Redirect to the 'login_page' URL name

        except IntegrityError:
            return JsonResponse({'error_message': 'Username or Email already exists'}, status=400)
        except ValidationError as e:
            return JsonResponse({'error_message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error_message': 'An error occurred. Please try again later.'}, status=500)
    
    # Render the signup page for GET requests
    return render(request, 'user/signup.html')
  


@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.method == 'POST':  # Use POST for login
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')

            # Check if both fields are provided
            if not email or not password:
                return JsonResponse({'error_message': 'Both email and password are required.'}, status=400)

            # Authenticate the user
            user = authenticate(request, email=email, password=password)
            if user is not None:
                # Log the user in
                login(request, user)
                return redirect('dashboard')  # Corrected: Redirect to the dashboard
            else:
                return JsonResponse({'error_message': 'Invalid email or password.'}, status=400)

        except KeyError:  # Handle missing form fields
            return JsonResponse({'error_message': 'Missing fields in the request.'}, status=400)

        except Exception as e:  # Catch all other exceptions
            return JsonResponse({'error_message': str(e)}, status=500)

    # Render the login page for GET requests
    return render(request, 'user/signIn.html')


def logout_page(request):
    logout(request)
    return redirect('login_page')

def dashboard_page(request):
    return render(request, 'user/dashboard.html')

