# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import alembic

from ..alembic import AlembicCommand


class Current(AlembicCommand):
    help = "Show current db revisions"

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", help="App label of application to limit the output to.")

    def handle(self, app_label=None, verbosity=0, **kwargs):
        verbose = bool(verbosity - 1)
        appconfigs = [self.lookup_app(app_label)] if app_label is not None else self.sorcery_apps.values()

        for appconfig in appconfigs:
            self.stdout.write(
                self.style.SUCCESS("Revision for %s on database %s" % (appconfig.name, appconfig.db.alias))
            )
            with alembic.context.EnvironmentContext(
                appconfig.config,
                appconfig.script,
                fn=partial(self.display_version, verbose=verbose, appconfig=appconfig),
            ) as context:
                self.run_env(context, appconfig)

    def display_version(self, rev, context, verbose=False, appconfig=None):
        if verbose:
            self.stdout.write("Current revision(s) for {!r}".format(context.connection.engine.url))
        for rev in appconfig.script.get_all_current(rev):
            self.stdout.write(rev.cmd_format(verbose))

        return []


Command = Current
