# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\PuzzleRoom\urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from oauth2_provider import urls as oauth2_urls
from . import views  # Import your views module

urlpatterns = [
    path('user/', include('user.urls')),  # For user-related URLs like login/signup
    path("admin/", admin.site.urls),
    path('puzzles/', include('puzzles.urls')),
    path('rooms/', include('rooms.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),  # OAuth2 URLs
    path('', views.base_page, name='root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
