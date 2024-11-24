# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\PuzzleRoom\urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Import your views module

urlpatterns = [
    path('accounts/', include('allauth.urls')),  # Include allauth URLs
    path('user/', include('user.urls')),  # User app URLs
    path('admin/', admin.site.urls),
    path('puzzles/', include('puzzles.urls')),
    path('jigsaw/', include('jigsaw_puzzle.urls')),  # Use only one prefix
    path('', views.base_page, name='root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
