# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import alembic

from django.core.management import CommandError

from ..alembic import AlembicCommand


class Stamp(AlembicCommand):
    help = "Stamp the revision table with migration revisions, doesn't run any migrations"

    def add_arguments(self, parser):
        parser.add_argument("args", metavar="app_label", nargs=1, help="Specify the app label to stamp for.")
        parser.add_argument(
            "-r",
            "--revision",
            default="heads",
            help="Database state will be brought to the state after that "
            'migration. Use the name "base" to unapply all migrations.',
        )

    def handle(self, app_label=None, revision=None, **kwargs):
        appconfig = self.lookup_app(app_label)

        if ":" in revision:
            raise CommandError("Range revision is not allowed")

        self.stdout.write(
            self.style.SUCCESS("Stamping revision for %s on database %s" % (appconfig.name, appconfig.db.alias))
        )

        with alembic.context.EnvironmentContext(
            appconfig.config,
            appconfig.script,
            fn=partial(self.stamp, appconfig=appconfig, revision=revision),
            destination_rev=revision,
        ) as context:
            self.run_env(context, appconfig)

    def stamp(self, rev, context, appconfig, revision):
        return appconfig.script._stamp_revs(revision, rev)


Command = Stamp
