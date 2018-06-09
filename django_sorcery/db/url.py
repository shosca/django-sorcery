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


def get_settings(alias):
    if hasattr(settings, "SQLALCHEMY_CONNECTIONS") and alias in settings.SQLALCHEMY_CONNECTIONS:
        return settings.SQLALCHEMY_CONNECTIONS[alias]

    return settings.DATABASES[alias]


def make_url(alias_or_url):
    """
    Generates a URL either from environment, DATABASES or SQLALCHEMY_CONNECTIONS settings
    ---------------------------------------------------------------------
    alias_or_url: str
        name of the alias or url as string
    """
    try:
        return sa.engine.url.make_url(alias_or_url), {}

    except sa.exc.ArgumentError:
        pass

    alias = alias_or_url

    url = sa.engine.url.make_url(os.environ.get(alias.upper() + "_URL", None))
    if url:
        return url, {}

    return make_url_from_settings(alias)


def make_url_from_settings(alias):
    """
    Generates a URL using the alias in settings
    -------------------------------------------
    alias: str
        name of the alias
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
