# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os


def absjoin(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.dirname(absjoin(__file__))
STATIC_ROOT = absjoin(PROJECT_ROOT, "..", "static")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "default_db",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
    "fromdbs": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fromdbs",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
}

SQLALCHEMY_CONNECTIONS = {
    "default": {
        "DIALECT": "postgresql",
        "NAME": "default_db",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
    "test": {
        "DIALECT": "postgresql",
        "NAME": "test",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
    "minimal": {
        "DIALECT": "postgresql",
        "NAME": "minimal",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
    "minimal_backpop": {
        "DIALECT": "postgresql",
        "NAME": "minimal_backpop",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
    "terrible": {
        "DIALECT": "postgresql",
        "NAME": "minimal_backpop",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    },
}

INSTALLED_APPS = [
    "tests.minimalapp.apps.MinimalAppConfig",
    "tests.testapp.apps.TestAppConfig",
    "tests.otherapp.apps.OtherAppConfig",
    "django_sorcery",
    "django.contrib.staticfiles",
]

ROOT_URLCONF = "tests.urls"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

SECRET_KEY = "secret"

ALLOWED_HOSTS = ["*"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(os.path.dirname(__file__), "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ]
        },
    }
]
