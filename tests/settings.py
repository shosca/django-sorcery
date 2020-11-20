import os

from sqlalchemy.engine.url import make_url


def absjoin(*args):
    return os.path.normpath(os.path.abspath(os.path.join(*args)))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = os.path.dirname(absjoin(__file__))
STATIC_ROOT = absjoin(PROJECT_ROOT, "..", "static")

DB_URL = make_url(os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "default_db",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
    "fromdbs": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fromdbs",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
}

SQLALCHEMY_CONNECTIONS = {
    "default": {
        "DIALECT": "postgresql",
        "NAME": "default_db",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
    "test": {
        "DIALECT": "postgresql",
        "NAME": "test",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
    "minimal": {
        "DIALECT": "postgresql",
        "NAME": "minimal",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
    "minimal_backpop": {
        "DIALECT": "postgresql",
        "NAME": "minimal_backpop",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
        "PORT": "",
    },
    "terrible": {
        "DIALECT": "postgresql",
        "NAME": "minimal_backpop",
        "USER": DB_URL.username,
        "PASSWORD": DB_URL.password,
        "HOST": DB_URL.host,
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
