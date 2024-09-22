# C:\Users\beka\OneDrive\Desktop\MajorProjectY4\backend\api\user\urls.py
from django.urls import path
from .login import  get_user_info
from .views import login_page, signup_page, logout_page, dashboard_page

urlpatterns = [
    path('dashboard/', dashboard_page, name='dashboard'),
    # Rendering signup and login template pages
    path('signup-page/', signup_page, name='signup_page'),
    path('signin-page/', login_page, name='login_page'),
    path('logout/', logout_page, name='logout_page'),
    # User information view
    path('user-info/', get_user_info, name='user-info'),
]
