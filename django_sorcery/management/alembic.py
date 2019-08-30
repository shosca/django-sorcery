# -*- coding: utf-8 -*-
"""
Alembic Django command things
"""
import os
from collections import OrderedDict, namedtuple

import alembic
import alembic.config
import six

from sqlalchemy.orm import configure_mappers

from django.core.management.base import BaseCommand, CommandError
from django.utils.functional import cached_property

from ..db import alembic as sorcery_alembic, databases, meta, signals
from ..db.alembic import include_object, process_revision_directives


SORCERY_ALEMBIC_CONFIG_FOLDER = os.path.abspath(os.path.dirname(sorcery_alembic.__file__))


AlembicAppConfig = namedtuple("AlembicAppConfig", ["name", "config", "script", "db", "app", "version_path", "tables"])


class AlembicCommand(BaseCommand):
    """
    Base alembic django command
    """

    @cached_property
    def sorcery_apps(self):
        """
        All sorcery apps and their alembic configs
        """
        configs = OrderedDict()
        for db in databases.values():
            table_class_map = {model.__table__: model for model in db.models_registry if hasattr(model, "__table__")}
            for table in db.metadata.sorted_tables:
                model = table_class_map.get(table)
                if model:
                    info = meta.model_info(model)
                    app = info.app_config
                    if app:
                        path = self.get_app_version_path(app)
                        if os.path.exists(path):
                            config = self.get_app_config(app, db)
                            appconfig = AlembicAppConfig(
                                name=app.label,
                                config=config,
                                db=db,
                                script=self.get_config_script(config),
                                version_path=path,
                                app=app,
                                tables=[],
                            )
                            configs.setdefault(app.label, appconfig).tables.append(table)
        for app in configs.values():
            signals.alembic_app_created.send(app.app)
            signals.alembic_config_created.send(app.config)
        return configs

    def get_app_config(self, app, db):
        """
        Return alembic config for an app
        """
        # TODO: read these from django db settings
        version_table = (
            getattr(app, "version_table", None)
            or db.kwargs.get("version_table")
            or "alembic_version_%s" % app.label.lower().replace(".", "_")
        )

        max_length = db.engine.dialect.max_identifier_length
        if max_length and len(version_table) >= max_length:
            raise CommandError(
                "'{name}' is {length} characters long which is an invalid identifier "
                "in {dialect!r} as its max idenfier length is {max_length}".format(
                    name=version_table, dialect=db.engine.dialect.name, length=len(version_table), max_length=max_length
                )
            )

        version_table_schema = getattr(app, "version_table_schema", None) or db.kwargs.get("version_table_schema")

        config = alembic.config.Config(output_buffer=self.stdout, stdout=self.stdout)
        config.set_main_option("script_location", SORCERY_ALEMBIC_CONFIG_FOLDER)
        config.set_main_option("version_locations", self.get_app_version_path(app))
        config.set_main_option("version_table", version_table)
        if version_table_schema and db.engine.dialect.name != "sqlite":
            config.set_main_option("version_table_schema", version_table_schema)
        return config

    def get_config_script(self, config):
        """
        Returns the alembic script directory for the config
        """
        return alembic.script.ScriptDirectory.from_config(config)

    def lookup_app(self, app_label):
        """
        Looks up an app's alembic config
        """
        if app_label not in self.sorcery_apps:
            raise CommandError("App '%s' could not be found. Is it in INSTALLED_APPS?" % app_label)

        return self.sorcery_apps[app_label]

    def get_app_version_path(self, app):
        """
        Returns the default migration directory location of al app
        """
        return os.path.join(app.path, "migrations")

    def get_common_config(self, context):
        """
        Common alembic configuration
        """
        config = context.config
        return {
            "include_object": include_object,
            "process_revision_directives": process_revision_directives,
            "version_table": config.get_main_option("version_table"),
            "version_table_schema": config.get_main_option("version_table_schema"),
        }

    def run_env(self, context, appconfig):
        """
        Executes an alembic context, just like the env.py file of alembic
        """
        configure_mappers()
        try:
            if context.is_offline_mode():
                self.run_migrations_offline(context, appconfig)
            else:
                self.run_migrations_online(context, appconfig)
        except alembic.util.exc.CommandError as e:
            raise CommandError(six.text_type(e))

    def run_migrations_online(self, context, appconfig):
        """
        Executes an online alembic context
        """
        with appconfig.db.engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=appconfig.db.metadata, **self.get_common_config(context)
            )

            with context.begin_transaction():
                context.run_migrations()

    def run_migrations_offline(self, context, appconfig):
        """
        Executes an offline alembic context
        """
        context.configure(
            url=appconfig.db.url,
            literal_binds=True,
            target_metadata=appconfig.db.metadata,
            **self.get_common_config(context),
        )
        with context.begin_transaction():
            context.run_migrations()
