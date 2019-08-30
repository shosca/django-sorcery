# -*- coding: utf-8 -*-

import alembic.config

from django.test import TestCase

from django_sorcery.db.alembic.base import setup_config


class TestSignals(TestCase):
    def test_alembic_config(self):
        config = alembic.config.Config()
        setup_config(config)

        self.assertEqual(config.get_section_option("loggers", "keys"), "root,sqlalchemy,alembic")
        self.assertEqual(config.get_section_option("handlers", "keys"), "console")
        self.assertEqual(config.get_section_option("formatters", "keys"), "generic")
        self.assertEqual(config.get_section_option("logger_root", "level"), "WARN")
        self.assertEqual(config.get_section_option("logger_root", "handlers"), "console")
        self.assertEqual(config.get_section_option("logger_sqlalchemy", "level"), "WARN")
        self.assertEqual(config.get_section_option("logger_sqlalchemy", "qualname"), "sqlalchemy.engine")
        self.assertEqual(config.get_section_option("logger_alembic", "level"), "INFO")
        self.assertEqual(config.get_section_option("logger_alembic", "qualname"), "alembic")
        self.assertEqual(config.get_section_option("handler_console", "class"), "StreamHandler")
        self.assertEqual(config.get_section_option("handler_console", "formatter"), "generic")
