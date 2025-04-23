#C:\Users\beka\OneDrive\Desktop\Year4DjangoMajor-Project\DjangoProject\PuzzleRoom\PuzzleRoom\settings.py
from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
load_dotenv() 
# Optional: Customize message tags (optional, for CSS styling)
from django.contrib.messages import constants as message_constants
import logging
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)ytjp2gmp_r3psh*=8swqdck-lvhn(4h5)5iiblap16c5ye9jh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]



# Application definition
INSTALLED_APPS = [
    'jigsaw_puzzle',
    'puzzles',
    'sliding_puzzle',
    'user.apps.UserConfig',
    'physics_puzzle',
    
    # Core Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django Allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # OAuth providers
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
    
    # Other apps
    'oauth2_provider',
    'corsheaders',
    'rest_framework',
    'channels',
    'tailwind',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'APP': {
            'client_id': os.environ.get('CLIENT_ID'),  # Fetch from environment variables
            'secret': os.environ.get('CLIENT_SECRET'),  # Fetch from environment variables
        },
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # Required for messages
]

ROOT_URLCONF = 'PuzzleRoom.urls'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Django's default
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth backend
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PuzzleRoom.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.postgresql',
       'NAME': 'puzzleRoom01',
       'USER': 'postgres',
       'PASSWORD': 'pass',
       'HOST': '127.0.0.1',
       'PORT': '5432',
   }
}

#DATABASES = {
    #'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
#}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('puzzleRoom'),
#         'USER': os.getenv('puzzle_room01'),
#         'PASSWORD': os.getenv('oFFOdaoQlS6ENP7nyUrhqddqP3TL4ZXJ'),
#         'HOST': os.getenv('postgresql://puzzle_rooom01:oFFOdaoQlS6ENP7nyUrhqddqP3TL4ZXJ@dpg-ctddhpjqf0us73bp4fb0-a/puzzle_room01'),
#         'PORT': os.getenv('5432'),
#     }
# }


#DATABASES = {
    #'default': {
       # 'ENGINE': 'django.db.backends.postgresql',
        #'NAME': 'postgres',  # The name of the database
        #'USER': 'postgres.pqxcaxmnuisojsxinayh',  # The username for the database
        #'PASSWORD': 'PlsStopThis45@?',  # The password for the database
        #'HOST': 'aws-0-eu-west-1.pooler.supabase.com',  # The database host
        #'PORT': '6543',  # The port for the database connection
    #}
#}


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'postgres',  # Database name, it's usually 'postgres' in Supabase
#         'USER': os.getenv('DB_USER'),  # Fetch user from environment, default 'postgres'
#         'PASSWORD': os.getenv('DB_PASSWORD'),  # Fetch password from environment
#         'HOST': os.getenv('DB_HOST'),  # Your Supabase host
#         'PORT': os.getenv('DB_PORT'),  # Default port for PostgreSQL
#         'OPTIONS': {
#             'sslmode': 'require',  # Ensure SSL is enabled
#             'connect_timeout': 40,  # Increase timeout for connection
#         },
#     }
# }
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Remove Cloudinary configuration
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Debug should be True for development
DEBUG = True

# Configure WhiteNoise
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Add static finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "https://djangoproject-0bzc.onrender.com"
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://djangoproject-0bzc.onrender.com'
    ''
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]




CORS_ALLOW_CREDENTIALS = True



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',  # OAuth2 auth
        'rest_framework.authentication.SessionAuthentication',  # Optional, for web access
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # Require authentication by default
    )
}

AUTH_USER_MODEL = 'user.User'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ASGI_APPLICATION = 'PuzzleRoom.asgi.application'



# settings.py

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                "redis://default:v8k6iNVv7cIS71IRgvVoS57cib6wagSj@redis-17031.c243.eu-west-1-3.ec2.redns.redis-cloud.com:17031"
            ],
        },
    },
}


LOGIN_REDIRECT_URL = '/user/dashboard/'

LOGOUT_REDIRECT_URL = '/'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
)
SOCIALACCOUNT_AUTO_SIGNUP = True
# This will show detailed logs for debugging purposes.

MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning', 
    message_constants.ERROR: 'error',
}

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# Email settings for SendGrid
DEFAULT_FROM_EMAIL = 'b00147423@mytudublin.ie'  # Your verified sender email
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # Always use "apikey" as the user
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY  # Use the SendGrid API key as the password


LANGUAGES = [
    ('en', 'English'),
]

LOGIN_URL = '/user/auth/'

USE_I18N = True
USE_L10N = True