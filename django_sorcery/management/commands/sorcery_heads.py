# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from ..alembic import AlembicCommand


class ShowHeads(AlembicCommand):
    help = "Display revision heads"

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", help="App label of application to limit the output to.")

    def handle(self, app_label=None, verbosity=0, **kwargs):
        verbosity = bool(verbosity - 1)
        appconfigs = [self.lookup_app(app_label)] if app_label is not None else self.sorcery_apps.values()

        for appconfig in appconfigs:
            self.stdout.write(self.style.SUCCESS("Heads for %s on database %s" % (appconfig.name, appconfig.db.alias)))
            for rev in appconfig.script.get_revisions("heads"):
                if verbosity:
                    self.stdout.write(
                        "".join(
                            [
                                "[",
                                appconfig.name,
                                "]\n",
                                rev.cmd_format(verbosity, include_branches=True, tree_indicators=False),
                            ]
                        )
                    )
                else:
                    self.stdout.write(
                        "".join(
                            [
                                rev.cmd_format(verbosity, include_branches=True, tree_indicators=False),
                                " <",
                                appconfig.name,
                                "> ",
                            ]
                        )
                    )


Command = ShowHeads
