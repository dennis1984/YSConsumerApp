#-*- coding:utf8 -*-
"""
Django settings for YSConsumerApp project.

Generated by 'django-admin startproject' using Django 1.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '2kpeanl_l@*1-coeuk&6i(w8)54svrw)%ohd2n*p6kw2gs-m0*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'oauth2_provider',
    'users',
    'orders',
    'shopping_cart',
    'PAY.wxpay',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'YSConsumerApp.urls'

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

WSGI_APPLICATION = 'YSConsumerApp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi_CS',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
    'business': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    }
}


DATABASE_ROUTERS = ['Business_App.router.BusinessAppRouter']

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


AUTH_USER_MODEL = 'users.ConsumerUser'

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    'users.auth.ConsumerUserBackend',
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    ("picture", os.path.join(STATIC_ROOT, 'picture')),
)

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        'rest_framework.permissions.IsAuthenticated',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',

        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),

    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': 100,
}

# pagination

PAGE_SIZE = 100

MAX_PAGE_SIZE = 500

# domain name

DOMAIN_NAME = 'yinshi.city23.com'

# WEB URL FIX

WEB_URL_FIX = os.path.join('http://', DOMAIN_NAME)

# 图片根目录
PICTURE_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static', 'business', 'picture')

PICTURE_DIRS = {
    'consumer': {
        'head_picture': os.path.join(PICTURE_ROOT, 'head_picture'),   # 用户头像图片目录
    },
    'business': {
        'dishes': os.path.join(PICTURE_ROOT, 'dishes'),               # 菜品图片目录
        'head_picture': os.path.join(PICTURE_ROOT, 'head_picture'),   # 用户头像图片目录
        'qrcode': os.path.join(PICTURE_ROOT, 'qrcode'),               # 二维码图片目录
    }
}

# 缓存服务器配置
REDIS_SETTINGS = {
    'host': '121.42.249.43',
    'port': 6379,
    'db_set': {
        'business': 0,
        'consumer': 1,
        }
}