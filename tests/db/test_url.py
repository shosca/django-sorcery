# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from django.test import TestCase, override_settings

from django_sorcery.db.url import make_url


@override_settings(
    SQLALCHEMY_CONNECTIONS={
        "bad": {},
        "minimal": {"DIALECT": "sqlite"},
        "default": {
            "DIALECT": "postgresql",
            "DRIVER": "psycopg2",
            "USER": "usr",
            "PASSWORD": "hunter2",
            "HOST": "pghost",
            "NAME": "pgdb",
            "PORT": "5432",
        },
        "ora": {"DIALECT": "oracle", "HOST": "orahost", "NAME": "oradb"},
    },
    DATABASES={
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        "dummy": {"ENGINE": "django.db.backends.sqlite3", "DRIVER": "sqlite3", "NAME": "dummy.sqlite3"},
    },
)
class TestMakeUrl(TestCase):
    def setUp(self):
        super(TestMakeUrl, self).setUp()
        os.environ["FROM_ENV_URL"] = "postgresql://usr:hunter2@awesomedomain/db?engine_echo=True"

    def tearDown(self):
        super(TestMakeUrl, self).tearDown()
        os.environ.pop("FROM_ENV_URL", None)

    def test_handles_url(self):
        url, options = make_url("postgresql://usr:hunter2@awesomedomain/db?engine_echo=True")
        self.assertEqual(url.database, "db")
        self.assertEqual(url.drivername, "postgresql")
        self.assertEqual(url.host, "awesomedomain")
        self.assertEqual(url.password, "hunter2")
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, "usr")
        self.assertDictEqual(options, {"engine_options": {"echo": True}})

    def test_requires_dialect(self):
        with self.assertRaises(KeyError):
            make_url("bad")

    def test_can_override_from_env(self):
        url, options = make_url("from_env")
        self.assertEqual(url.database, "db")
        self.assertEqual(url.drivername, "postgresql")
        self.assertEqual(url.host, "awesomedomain")
        self.assertEqual(url.password, "hunter2")
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, "usr")
        self.assertDictEqual(options, {"engine_options": {"echo": True}})

    def test_can_generate_minimal(self):
        url, _ = make_url("minimal")
        self.assertEqual(url.database, None)
        self.assertEqual(url.drivername, "sqlite")
        self.assertEqual(url.host, None)
        self.assertEqual(url.password, None)
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, None)

    def test_can_generate_full(self):
        url, _ = make_url("default")
        self.assertEqual(url.database, "pgdb")
        self.assertEqual(url.drivername, "postgresql+psycopg2")
        self.assertEqual(url.host, "pghost")
        self.assertEqual(url.password, "hunter2")
        self.assertEqual(url.port, 5432)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, "usr")

    def test_can_handle_oracle_tns(self):
        url, _ = make_url("ora")
        self.assertEqual(url.database, "oradb")
        self.assertEqual(url.drivername, "oracle")
        self.assertEqual(url.host, "orahost")
        self.assertEqual(url.password, None)
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, None)

    def test_can_generate_from_databases(self):
        url, _ = make_url("dummy")
        self.assertEqual(url.database, "dummy.sqlite3")
        self.assertEqual(url.drivername, "sqlite+sqlite3")
        self.assertEqual(url.host, None)
        self.assertEqual(url.password, None)
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, None)
