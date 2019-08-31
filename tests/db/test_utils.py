# -*- coding: utf-8 -*-
import unittest

import sqlalchemy as sa

from django.conf import settings

from django_sorcery.db import databases
from django_sorcery.db.sqlalchemy import SQLAlchemy
from django_sorcery.db.utils import dbdict, index_foreign_keys

from ..base import mock
from ..models_multidb import Bar, Foo, default_db, other_db


class TestDbDict(unittest.TestCase):
    def setUp(self):
        super().setUp()
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


class TestMultiDbAtomic(unittest.TestCase):
    def setUp(self):
        super().setUp()
        Foo.objects.delete()
        Bar.objects.delete()
        databases.commit()

    def tearDown(self):
        super().tearDown()
        Foo.objects.delete()
        Bar.objects.delete()
        databases.commit()

    def test_multidb(self):

        with databases.atomic():
            default_db.add(Foo(name="1234"))
            other_db.add(Bar(name="1234"))

        self.assertEqual(Foo.objects.count(), 1)
        self.assertEqual(Bar.objects.count(), 1)
        databases.rollback()

        with self.assertRaises(Exception) as ctx, databases.atomic():
            default_db.add(Foo())
            other_db.add(Bar())

        self.assertIsInstance(ctx.exception, sa.exc.IntegrityError)
        self.assertEqual(Foo.objects.count(), 0)
        self.assertEqual(Bar.objects.count(), 0)
        databases.rollback()

    def test_multidb_flush(self):
        default_db.add(Foo(name="1234"))
        other_db.add(Bar(name="1234"))

        databases.flush()

        self.assertEqual(len(default_db.new) + len(other_db.new), 0)

    def test_multidb_commit(self):
        default_db_session = default_db()
        other_db_session = other_db()

        databases.remove()

        self.assertIsNot(default_db(), default_db_session)
        self.assertIsNot(other_db(), other_db_session)


class TestIndexForeignKeys(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.metadata = sa.MetaData()
        self.parent = sa.Table(
            "parent",
            self.metadata,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), primary_key=True),
        )

        self.child = sa.Table(
            "child",
            self.metadata,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tenant_id", sa.Integer(), primary_key=True),
            sa.Column("parent_id", sa.Integer()),
            sa.ForeignKeyConstraint(["tenant_id", "parent_id"], ["parent.tenant_id", "parent.id"]),
        )

    def test_metadata(self):
        index_foreign_keys(self.metadata)

        self.assertEqual(len(self.metadata.tables["child"].indexes), 1)
        ix = next(iter(self.metadata.tables["child"].indexes))
        self.assertEqual(list(ix.columns), [self.child.c.tenant_id, self.child.c.parent_id])

    def test_table(self):
        index_foreign_keys(self.child)

        self.assertEqual(len(self.metadata.tables["child"].indexes), 1)
        ix = next(iter(self.metadata.tables["child"].indexes))
        self.assertEqual(list(ix.columns), [self.child.c.tenant_id, self.child.c.parent_id])
