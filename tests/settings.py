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
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "db.sqlite3")},
    "fromdbs": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "fromdbs.sqlite3")},
}

SQLALCHEMY_CONNECTIONS = {
    "default": {"DIALECT": "sqlite"},
    "test": {"DIALECT": "sqlite"},
    "minimal": {"DIALECT": "sqlite"},
    "minimal_backpop": {"DIALECT": "sqlite"},
}

INSTALLED_APPS = ["tests.apps.TestConfig", "django_sorcery", "django.contrib.staticfiles"]

ROOT_URLCONF = "tests.urls"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

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
