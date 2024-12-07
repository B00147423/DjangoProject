#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\user\urls.py
from django.urls import path
from .views import (
    auth_page, logout_page, dashboard_page, pending_verification, resend_verification_email,
    settings_page, change_username, change_email, change_password, verify_email, 
    pending_verification_status, send_verification_email
)
app_name = 'user'
from . import views
urlpatterns = [
    path('dashboard/', dashboard_page, name='dashboard'),
    path('auth/', auth_page, name='auth_page'),
    path('logout/', logout_page, name='logout_page'),
    path('settings/', settings_page, name='settings'),
    path('settings/change_username/', change_username, name='change_username'),
    path('settings/change_email/', change_email, name='change_email'),
    path('settings/change_password/', change_password, name='change_password'),
    path('verify/<uidb64>/<token>/', verify_email, name='verify_email'),
    path('pending-verification/', pending_verification, name='pending_verification'),
    path('pending-verification-status/', pending_verification_status, name='pending_verification_status'),
    path('resend-verification-email/', resend_verification_email, name='resend_verification_email'),
    path('send_verification_email/', send_verification_email, name='send_verification_email'),
    path('profile/', views.profile_view, name='profile_view'),
]