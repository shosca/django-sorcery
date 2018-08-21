# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management import CommandError

from ..alembic import AlembicCommand


class History(AlembicCommand):
    help = "Display alembic revisions"

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", help="App label of application to limit the output to.")
        parser.add_argument(
            "-r",
            "--rev_range",
            action="store",
            dest="rev_range",
            default=None,
            help="Specify a revision range; format is [start]:[end].",
        )

    def handle(self, app_label=None, rev_range=None, verbosity=0, **kwargs):
        verbose = bool(verbosity - 1)
        appconfigs = [self.lookup_app(app_label)] if app_label is not None else self.sorcery_apps.values()

        if rev_range is not None:
            if app_label is None:
                raise CommandError("Revision requires an app label")

            if ":" not in rev_range:
                raise CommandError("History range requires [start]:[end], [start]:, or :[end]")
            base, head = rev_range.strip().split(":")
        else:
            base = head = None

        self.print_history(appconfigs, verbose, base, head)

    def print_history(self, appconfigs, verbose, base, head):
        for appconfig in appconfigs:
            self.stdout.write(
                self.style.SUCCESS("Migrations for %s on database %s" % (appconfig.name, appconfig.db.alias))
            )
            for rev in appconfig.script.walk_revisions(base=base or "base", head=head or "heads"):
                self.stdout.write(
                    rev.cmd_format(verbose=verbose, include_branches=True, include_doc=True, include_parents=True)
                )


Command = History
