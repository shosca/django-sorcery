# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand

from django_sorcery.db import databases


class CreateAll(BaseCommand):
    help = "Creates SQLAlchemy database schemas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            "-d",
            action="append",
            dest="databases",
            type=str,
            help="Nominates a database to synchronize. By default will synchronize all.",
        )

    def handle(self, *args, **kwargs):
        dbs = kwargs.get("databases") or databases.keys()
        for key in dbs:
            databases[key].create_all()
            self.stdout.write(self.style.SUCCESS('Successfully ran create_all() for "%s"' % key))


Command = CreateAll
