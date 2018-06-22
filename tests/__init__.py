# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

import sqlalchemy as sa

import django

from django_sorcery.db import signals


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"


@signals.engine_created.connect
def hacks(sender, **kwargs):

    # pysqlite workarounds for savepoints
    if "sqlite" in sender.url.drivername:

        @sa.event.listens_for(sender, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @sa.event.listens_for(sender, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.execute("BEGIN")


django.setup()
