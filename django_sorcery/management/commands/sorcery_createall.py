# -*- coding: utf-8 -*-
"""
CreateAll command
"""

from sqlalchemy.orm import configure_mappers

from django.core.management.base import BaseCommand

from ...db import databases


class CreateAll(BaseCommand):
    """
    Creates db schema using metadata.create_all
    """

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
        configure_mappers()
        dbs = kwargs.get("databases") or databases.keys()
        for key in dbs:
            databases[key].create_all()
            self.stdout.write(self.style.SUCCESS('Successfully ran create_all() for "%s"' % key))


Command = CreateAll
