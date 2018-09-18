# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import alembic

from ...db import signals
from ..alembic import AlembicCommand


class Revision(AlembicCommand):
    help = "Create a migration revision"

    def add_arguments(self, parser):
        parser.add_argument(
            "args", metavar="app_label", nargs=1, help="Specify the app label to create migrations for."
        )
        parser.add_argument(
            "-m", "--message", action="store", required=True, help="Message string to use with 'revision'"
        )
        parser.add_argument(
            "-r", "--rev-id", action="store", help="Specify a hardcoded revision id instead of generating one"
        )
        parser.add_argument(
            "--head", action="store", help="Specify head revision or <branchname>@head to base new revision on."
        )
        parser.add_argument(
            "--branch-label", action="store", help="Specify a branch label to apply to the new revision."
        )
        parser.add_argument(
            "--depends-on",
            action="store",
            help="Specify one or more revision identifiers which this revision should depend on.",
        )
        parser.add_argument(
            "--splice",
            action="store_true",
            default=None,
            help="Allow a non-head revision as the 'head' to splice onto.",
        )
        parser.add_argument(
            "--autogenerate",
            action="store_true",
            dest="autogenerate",
            help="Populate revision script with candidate migration operations, based on comparison of database to model.",
        )
        parser.add_argument(
            "--no-autogenerate",
            action="store_false",
            dest="autogenerate",
            default=True,
            help="Generate blank candidate migration. This will not compare database to models.",
        )

    def handle(
        self,
        app_label,
        message=None,
        head=None,
        splice=None,
        branch_label=None,
        depends_on=None,
        rev_id=None,
        autogenerate=None,
        **kwargs
    ):
        appconfig = self.lookup_app(app_label)

        version_tables = {
            ".".join(
                filter(
                    None,
                    [
                        appconf.config.get_main_option("version_table_schema"),
                        appconf.config.get_main_option("version_table"),
                    ],
                )
            )
            for appconf in self.sorcery_apps.values()
        }

        @signals.alembic_include_object.connect
        def include_object(obj=None, name=None, type_=None, reflected=None, compare_to=None):
            if type_ == "table":
                return obj in appconfig.tables and obj.fullname not in version_tables

            else:
                return obj.table in appconfig.tables

        command_args = dict(
            autogenerate=autogenerate,
            branch_label=branch_label,
            depends_on=depends_on,
            head=head,
            rev_id=rev_id,
            message=message,
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


Command = Revision
