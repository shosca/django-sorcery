# -*- coding: utf-8 -*-
"""
DropAll command
"""
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand

from ...db import databases


class DropAll(BaseCommand):
    """
    Drops database schemas using metadata.drop_all
    """

    help = "Drops SQLAlchemy database schemas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            "-d",
            action="append",
            dest="databases",
            type=str,
            help="Nominates a database to drop. By default will drop all.",
        )

    def handle(self, *args, **kwargs):
        dbs = kwargs.get("databases") or databases.keys()
        for key in dbs:
            databases[key].drop_all()
            self.stdout.write(self.style.SUCCESS('Successfully ran drop_all() for "%s"' % key))


Command = DropAll
