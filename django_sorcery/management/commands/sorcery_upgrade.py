# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import alembic

from django.core.management import CommandError

from ..alembic import AlembicCommand


class Upgrade(AlembicCommand):
    help = "Apply migration revisions"

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", help="App label of application to limit the output to.")
        parser.add_argument(
            "-r",
            "--revision",
            default="heads",
            help="Database state will be brought to the state after that "
            'migration. Use the name "heads" to apply all migrations.',
        )
        parser.add_argument(
            "-s",
            "--sql",
            default=False,
            action="store_true",
            help="Don't emit SQL to database - dump to standard output/file instead",
        )

    def handle(self, app_label=None, revision=None, sql=False, **kwargs):
        appconfigs = [self.lookup_app(app_label)] if app_label is not None else self.sorcery_apps.values()

        starting_rev = None
        if ":" in revision:
            starting_rev, revision = revision.split(":", 2)

        if revision != "heads" and app_label is None:
            raise CommandError("Revision requires an app_label to be provided")

        for appconfig in appconfigs:
            if not sql:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Running migrations for %s on database %s" % (appconfig.name, appconfig.db.alias)
                    )
                )
            with alembic.context.EnvironmentContext(
                appconfig.config,
                appconfig.script,
                fn=partial(self.upgrade, appconfig=appconfig, revision=revision),
                as_sql=sql,
                starting_rev=starting_rev,
                destination_rev=revision,
            ) as context:
                self.run_env(context, appconfig)

    def upgrade(self, rev, context, appconfig, revision):
        return appconfig.script._upgrade_revs(revision, rev)


Command = Upgrade
