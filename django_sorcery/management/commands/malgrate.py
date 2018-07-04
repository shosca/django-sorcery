# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError

from ...db import databases


class Command(BaseCommand):
    help = "Updates SQLAlchemy database schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="append",
            dest="databases",
            type=str,
            help="Nominates a database to synchronize. By default will synchronize all.",
        )
        parser.add_argument(
            "--createall", action="store_true", default=False, help="Run create_all() for given databases."
        )

    def handle(self, *args, **options):
        for key, db in filter(lambda i: i[0] in (options["databases"] or databases), databases.items()):
            if options["createall"]:
                db.create_all()
                self.stdout.write(self.style.SUCCESS('Successfully ran create_all() for "%s"' % key))
            else:
                raise CommandError("Currently only createall is supported")
