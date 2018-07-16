# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

import sqlalchemy as sa

from django.conf import settings


DIALECT_MAP = {
    "django.db.backends.sqlite3": "sqlite",
    "django.db.backends.postgresql": "postgresql",
    "django.db.backends.mysql": "mysql",
    "django.db.backends.oracle": "oracle",
    "sqlserver_ado": "mssql",
}

ENGINE_OPTIONS_NORMALIZATION = {"echo": lambda x: x in ["True", True]}


def get_settings(alias):
    """
    Returns database settings from either ``SQLALCHEMY_CONNECTIONS`` setting or ``DATABASES`` setting.
    """

    if hasattr(settings, "SQLALCHEMY_CONNECTIONS") and alias in settings.SQLALCHEMY_CONNECTIONS:
        return settings.SQLALCHEMY_CONNECTIONS[alias]

    return settings.DATABASES[alias]


def _options_from_url(url):
    return {
        "engine_options": {
            k.replace("engine_", ""): ENGINE_OPTIONS_NORMALIZATION.get(k.replace("engine_", ""), lambda x: x)(
                url.query.pop(k)
            )
            for k in list(url.query)
        }
    }


def make_url(alias_or_url):
    """
    Generates a URL either from a url string, environment variable, SQLALCHEMY_CONNECTIONS or DATABASES settings
    ---------------------------------------------------------------------
    alias_or_url: str
        name of the alias or url as string
    """
    try:
        url = sa.engine.url.make_url(alias_or_url)

    except sa.exc.ArgumentError:
        pass

    else:
        return url, _options_from_url(url)

    alias = alias_or_url

    url = sa.engine.url.make_url(os.environ.get(alias.upper() + "_URL", None))
    if url:
        return url, _options_from_url(url)

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

    ``OPTIONS`` - Optional arguments to be used to initialize the :py:class:`..sqlalchemy.SQLAlchemy` instance

        * ``session_class`` - a custom session class to be used
        * ``registry_class`` - a custom registy class to be used for scoping
        * ``model_class`` - a custom base model class to be used for declarative base models.
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

    return url, data.get("OPTIONS", {})
