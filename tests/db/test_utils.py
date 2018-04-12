# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from django.conf import settings

from django_sorcery.db.sqlalchemy import SQLAlchemy
from django_sorcery.db.utils import dbdict

from ..base import mock


class TestDbDict(unittest.TestCase):

    def setUp(self):
        super(TestDbDict, self).setUp()
        self.settings = mock.patch.dict(settings.SQLALCHEMY_CONNECTIONS, {"minimal": {"DIALECT": "sqlite"}})
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def test_get(self):
        databases = dbdict()

        db = databases.get("minimal")
        self.assertEqual(str(db.url), "sqlite://")

    def test_get_again(self):
        databases = dbdict()

        db1 = databases.get("minimal")

        db2 = databases.get("minimal")
        self.assertEqual(db1, db2)

    def test_update(self):
        databases = dbdict()

        databases.update({"one": SQLAlchemy("sqlite://")}, two=SQLAlchemy("sqlite://"))

    def test_setitem(self):
        databases = dbdict()
        databases["one"] = SQLAlchemy("sqlite://")

    def test_setitem_again(self):
        databases = dbdict()
        databases["one"] = SQLAlchemy("sqlite://")

        with self.assertRaises(RuntimeError):
            databases["one"] = SQLAlchemy("sqlite://")

    def test_setitem_again_same_db(self):
        databases = dbdict()

        db = SQLAlchemy("sqlite://")
        databases["one"] = db

        with self.assertRaises(RuntimeError):
            databases["two"] = db

    def test_setitem_dummy(self):
        databases = dbdict()

        with self.assertRaises(RuntimeError):
            databases["one"] = {}
