# C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\PuzzleRoom\urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('user/', include(('user.urls', 'user'), namespace='user')),
    path('admin/', admin.site.urls),
    path('puzzles/', include('puzzles.urls')),
    path('jigsaw/', include('jigsaw_puzzle.urls')),
    path('sliding_puzzle/', include('sliding_puzzle.urls', namespace='sliding_puzzle')),
    path('', views.base_page, name='root'),
    path('physics/', include(('physics_puzzle.urls', 'physics_puzzle'), namespace='physics_puzzle')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
