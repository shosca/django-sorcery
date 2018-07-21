# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import alembic

from django_sorcery.db import signals

from ..alembic import AlembicCommand


class MakeMigrations(AlembicCommand):
    help = "Create a migration revision"

    def add_arguments(self, parser):
        parser.add_argument(
            "args", metavar="app_label", nargs=1, help="Specify the app label to create migrations for."
        )
        parser.add_argument(
            "-n", "--name", action="store", dest="name", default=None, help="Use this name for migration file."
        )
        parser.add_argument(
            "-r", "--revision", action="store", dest="rev_id", default=None, help="Revision id for migration file."
        )

    def handle(
        self, app_label, name=None, head=None, splice=None, branch_label=None, depends_on=None, rev_id=None, **kwargs
    ):
        appconfig = self.lookup_app(app_label)

        version_tables = {appconf.config.get_main_option("version_table") for appconf in self.sorcery_apps.values()}

        @signals.alembic_include_object.connect
        def include_object(obj=None, name=None, type_=None, reflected=None, compare_to=None):
            if type_ == "table" and name in version_tables:
                return False

            return True

        command_args = dict(
            autogenerate=True,
            branch_label=branch_label,
            depends_on=depends_on,
            head=head,
            rev_id=rev_id,
            message=name,
            splice=splice,
            sql=False,
            version_path=appconfig.version_path,
        )
        self.revision_context = alembic.autogenerate.RevisionContext(appconfig.config, appconfig.script, command_args)
        with alembic.context.EnvironmentContext(
            appconfig.config,
            appconfig.script,
            fn=partial(self.retrieve_migrations, appconfig=appconfig),
            as_sql=False,
            template_args=self.revision_context.template_args,
            revision_context=self.revision_context,
        ) as context:
            self.run_env(context, appconfig)

        [script for script in self.revision_context.generate_scripts()]

    def retrieve_migrations(self, rev, context, appconfig=None):
        self.revision_context.run_autogenerate(rev, context)
        return []


Command = MakeMigrations
