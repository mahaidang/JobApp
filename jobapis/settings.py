
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

MEDIA_ROOT = '%s/jobs/static/' % BASE_DIR


SECRET_KEY = 'django-insecure-rq0e(hl)y7@$f-+tgw!5c$bbh2))w)(%!+-*sd@5x&n%ht0rv('

DEBUG = True

ALLOWED_HOSTS = ['*']

SITE_ID=1


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jobs.apps.JobsConfig',
    'ckeditor',
    'ckeditor_uploader',
    'rest_framework',
    'drf_yasg',
    'oauth2_provider',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'dj_rest_auth',
    'rest_framework.authtoken',
    'dj_rest_auth.registration',
    'django.contrib.sites',
    'cloudinary',
    'cloudinary_storage',
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email"
        ],
        "AUTH_PARAMS": {"access_type": "online"},
        'OAUTH_PKCE_ENABLED': True,
    }
}

SOCIALACCOUNT_ADAPTER = 'jobapis.adapters.CustomSocialAccountAdapter'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'jobapis.urls'

CKEDITOR_UPLOAD_PATH = "ckeditors/lessons/"


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jobapis.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jobdb',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '' # mặc định localhost
    }
}

import pymysql
pymysql.install_as_MySQLdb()

AUTH_USER_MODEL='jobs.User'



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



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import cloudinary.uploader

cloudinary.config(
    cloud_name = "dt3k9eyfz",
    api_key = "235356479665888",
    api_secret = "UyKamaPKqSJmOW_JTUyIkaeGGjA",
    secure=True
)

REST_USE_JWT = True
ACCOUNT_EMAIL_VERIFICATION = "none"



FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": "",
    "DELETE_INACTIVE_DEVICES": True,
}



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mahaidang2828@gmail.com'
EMAIL_HOST_PASSWORD = 'nfclwgpxbifnyavi'

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
)

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/admin"

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '276848800708-qs1ir27quckpl0aouhej8cfljovi6s1f.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True