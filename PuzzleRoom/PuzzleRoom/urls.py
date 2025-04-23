# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\PuzzleRoom\urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Import your views module


urlpatterns = [
    path('accounts/', include('allauth.urls')),  # Include allauth URLs
    path('user/', include(('user.urls', 'user'), namespace='user')),
    path('admin/', admin.site.urls),
    path('puzzles/', include('puzzles.urls')),
    path('jigsaw/', include('jigsaw_puzzle.urls')),  # Correctly routes to the jigsaw app
    path('sliding_puzzle/', include('sliding_puzzle.urls', namespace='sliding_puzzle')),
    path('', views.base_page, name='root'),  # Base page view
    path('physics/', include(('physics_puzzle.urls', 'physics_puzzle'), namespace='physics_puzzle')),  # Add namespace
]

# Add static and media files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
