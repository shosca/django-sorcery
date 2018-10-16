# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from django.test import TestCase, override_settings

from django_sorcery.db.url import (
    boolean,
    importable,
    importable_list,
    importable_list_tuples,
    integer,
    make_url,
    string,
    string_list,
)


@override_settings(
    SQLALCHEMY_CONNECTIONS={
        "bad": {},
        "minimal": {"DIALECT": "sqlite"},
        "from_env_preserve": {"DIALECT": "sqlite", "ALCHEMY_OPTIONS": {"foo": "bar"}},
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
        os.environ["FROM_ENV_PRESERVE_URL"] = "postgresql://usr:hunter2@awesomedomain/db?engine_echo=True"

    def tearDown(self):
        super(TestMakeUrl, self).tearDown()
        os.environ.pop("FROM_ENV_URL", None)
        os.environ.pop("FROM_ENV_PRESERVE_URL", None)

    def test_boolean(self):
        self.assertTrue(boolean("True"))
        self.assertTrue(boolean("1"))
        self.assertFalse(boolean("False"))
        self.assertFalse(boolean("0"))

    def test_integer(self):
        self.assertEqual(integer("5"), 5)

    def test_string(self):
        self.assertEqual(string(b"hello"), "hello")

    def test_string_list(self):
        self.assertEqual(string_list(b"hello"), ["hello"])

    def test_importable(self):
        self.assertIs(importable("django.test.TestCase"), TestCase)
        self.assertIs(importable("os"), os)

    def test_importable_list(self):
        self.assertEqual(importable_list("django.test.TestCase"), [TestCase])

    def test_importable_list_tuples(self):
        self.assertEqual(importable_list_tuples("os:target"), [(os, "target")])

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

    def test_can_override_from_env_preserve(self):
        url, options = make_url("from_env_preserve")
        self.assertEqual(url.database, "db")
        self.assertEqual(url.drivername, "postgresql")
        self.assertEqual(url.host, "awesomedomain")
        self.assertEqual(url.password, "hunter2")
        self.assertEqual(url.port, None)
        self.assertEqual(url.query, {})
        self.assertEqual(url.username, "usr")
        self.assertDictEqual(options, {"engine_options": {"echo": True}, "foo": "bar"})

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
