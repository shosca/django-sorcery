# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = "tests.testapp"
    label = "tests.testapp"
    version_table_schema = "public"

    def ready(self):
        from .models import db

        db.configure_mappers()
        db.create_all()
