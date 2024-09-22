# C:\Users\beka\OneDrive\Desktop\MajorProjectY4\backend\api\user\login.py
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.models import AccessToken, RefreshToken
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return JsonResponse({'detail': 'Email and password are required.'}, status=400)

    user = authenticate(username=email, password=password)

    if user is None:
        return JsonResponse({'detail': 'Invalid credentials.'}, status=400)

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return JsonResponse({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'username': user.email,  # You can change this to 'user.username' if using a username field
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_view(request):
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return JsonResponse({'detail': 'No refresh token provided'}, status=400)

    try:
        token = RefreshToken(refresh_token)
        access_token = str(token.access_token)

        response = JsonResponse({'access_token': access_token})
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=300,  # 5 minutes
        )
        return response
    except:
        return JsonResponse({'detail': 'Invalid refresh token'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    user = request.user
    return JsonResponse({
        'email': user.email,  # Or 'username' if you have a username field
    })

@ensure_csrf_cookie
@permission_classes([AllowAny])
def session_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})

    return JsonResponse({'isAuthenticated': True, 'username': request.user.email})

@require_POST
@permission_classes([IsAuthenticated])
def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)

    logout(request)
    return JsonResponse({'detail': 'Successfully logged out.'})
