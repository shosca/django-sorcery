"""Downgrade command."""
from functools import partial

import alembic
from django.core.management import CommandError

from ..alembic import AlembicCommand


class Downgrade(AlembicCommand):
    """Apply downgrade migration revisions."""

    help = "Apply migration revisions"

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", help="App label of application to limit the output to.")
        parser.add_argument(
            "-r",
            "--revision",
            default="base",
            help="Database state will be brought to the state after that "
            'migration. Use the name "base" to unapply all migrations.',
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

        if ":" in revision:
            raise CommandError("Range revision is not allowed")

        if revision != "base" and app_label is None:
            raise CommandError("Revision requires an app_label to be provided")

        for appconfig in reversed(appconfigs):
            if not sql:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Running migrations for {} on database {}".format(appconfig.name, appconfig.db.alias)
                    )
                )
            with alembic.context.EnvironmentContext(
                appconfig.config,
                appconfig.script,
                fn=partial(self.downgrade, appconfig=appconfig, revision=revision),
                as_sql=sql,
                starting_rev=None,
                destination_rev=revision,
            ) as context:
                self.run_env(context, appconfig)

    def downgrade(self, rev, context, appconfig, revision):
        """Executes alembic downgrade revisions to the given revision."""
        return appconfig.script._downgrade_revs(revision, rev)


Command = Downgrade
