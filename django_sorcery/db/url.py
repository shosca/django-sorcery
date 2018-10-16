# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os
from importlib import import_module

import six

import sqlalchemy as sa

from django.conf import settings
from django.utils.encoding import force_text
from django.utils.module_loading import import_string


DIALECT_MAP = {
    "django.db.backends.sqlite3": "sqlite",
    "django.db.backends.postgresql": "postgresql",
    "django.db.backends.mysql": "mysql",
    "django.db.backends.oracle": "oracle",
    "sqlserver_ado": "mssql",
}


def boolean(x):
    return six.text_type(x) in ["True", "1"]


def integer(x):
    return int(x)


def string(x):
    return force_text(x)


def string_list(x):
    return force_text(x).split(",")


def importable(x):
    try:
        return import_string(x)
    except ImportError:
        return import_module(x)


def importable_list(x):
    return [importable(i) for i in force_text(x).split(",")]


def importable_list_tuples(x):
    return [(importable(i), j) for i, j in [k.split(":") for k in force_text(x).split(",")]]


ENGINE_OPTIONS_NORMALIZATION = {
    "case_sensitive": boolean,
    # connect_args - direct querystring params in url
    "convert_unicode": boolean,
    "creator": importable,
    "echo": boolean,
    "echo_pool": boolean,
    "empty_in_strategy": string,
    "encoding": string,
    # execution_options - signal should be used instead
    "implicit_returning": boolean,
    "isolation_level": string,
    "label_length": integer,
    "listeners": importable_list,
    "logging_name": string,
    "max_overflow": integer,
    "module": importable,
    "paramstyle": string,
    "plugins": string_list,
    "pool": lambda x: importable(x)(),
    "pool_events": importable_list_tuples,
    "pool_logging_name": string,
    "pool_pre_ping": boolean,
    "pool_recycle": integer,
    "pool_reset_on_return": string,
    "pool_size": integer,
    "pool_threadlocal": boolean,
    "pool_timeout": integer,
    "pool_use_lifo": boolean,
    "poolclass": importable,
    "strategy": string,
}


def get_settings(alias):
    """
    Returns database settings from either ``SQLALCHEMY_CONNECTIONS`` setting or ``DATABASES`` setting.
    """

    if hasattr(settings, "SQLALCHEMY_CONNECTIONS") and alias in settings.SQLALCHEMY_CONNECTIONS:
        return settings.SQLALCHEMY_CONNECTIONS[alias]

    return settings.DATABASES[alias]


def _options_from_url(url, base_options):
    options = base_options.copy()
    options.update(
        {
            "engine_options": {
                k.replace("engine_", ""): ENGINE_OPTIONS_NORMALIZATION.get(k.replace("engine_", ""), lambda x: x)(
                    url.query.pop(k)
                )
                for k in list(url.query)
                if k.startswith("engine_")
            }
        }
    )
    return options


def make_url(alias_or_url):
    """
    Generates a URL either from a url string, environment variable, SQLALCHEMY_CONNECTIONS or DATABASES settings
    ---------------------------------------------------------------------
    alias_or_url: str
        name of the alias or url as string
    """
    settings_url, settings_kwargs = None, {}
    try:
        settings_url, settings_kwargs = make_url_from_settings(alias_or_url)
    except KeyError:
        pass

    try:
        url = sa.engine.url.make_url(alias_or_url)

    except sa.exc.ArgumentError:
        pass

    else:
        return url, _options_from_url(url, settings_kwargs)

    alias = alias_or_url

    url = sa.engine.url.make_url(os.environ.get(alias.upper() + "_URL", None))
    if url:
        return url, _options_from_url(url, settings_kwargs)

    return make_url_from_settings(alias)


def make_url_from_settings(alias):
    """
    Generates a URL using the alias in settings
    -------------------------------------------
    alias: str
        name of the alias

    Overall settings are very similar with django database settings with a few extra keys.

    ``USER`` - database user

    ``PASSWORD`` - database user password

    ``HOST`` - database host

    ``NAME`` - database name

    ``PORT`` - database name

    ``DIALECT`` - dialect to be used in url, if not provided, will use the ``DIALECT_MAP`` to figure out a dialect to
    be used in sqlalchemy url

    ``DRIVER`` - If provided, will be used as the driver in sqlalchemy url

    ``SQLALCHEMY`` - If provided, a custom :py:class:`..sqlalchemy.SQLAlchemy` class to be used

    ``QUERY`` - querystring arguments for sqlalchemy url

    ``ALCHEMY_OPTIONS`` - Optional arguments to be used to initialize the :py:class:`..sqlalchemy.SQLAlchemy` instance

        * ``session_class`` - a custom session class to be used
        * ``registry_class`` - a custom registy class to be used for scoping
        * ``model_class`` - a custom base model class to be used for declarative base models.
        * ``metadata_class`` - a custom metadata class used in delclarative models.
        * ``metadata_options`` - custom options to use in metadata creation such as specifying naming conventions.
        * ``engine_options`` - arguments for sqlalchemy ``create_engine``
        * ``session_options`` - arguments for sqlalchemy ``sessionmaker``

    Other options are ignored.
    """

    data = get_settings(alias)

    if "DIALECT" not in data:
        data["DIALECT"] = DIALECT_MAP.get(data["ENGINE"]) or data["ENGINE"].split(".")[-1]

    names = [data["DIALECT"].lower()]

    if "DRIVER" in data:
        names.append(data["DRIVER"].lower())

    drivername = "+".join(names)

    url = sa.engine.url.URL(drivername, username=data.get("USER") or None, password=data.get("PASSWORD") or None)

    url.host = data.get("HOST") or None
    url.database = data.get("NAME") or None
    try:
        url.port = int(data.get("PORT"))
    except Exception:
        pass

    url.query.update(data.get("QUERY", {}))

    return url, data.get("ALCHEMY_OPTIONS", {})
