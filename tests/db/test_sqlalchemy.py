# -*- coding: utf-8 -*-

import sqlalchemy as sa

from django_sorcery.db.query import Operation
from django_sorcery.utils import suppress

from ..base import TestCase
from ..testapp.models import ModelOne, Owner, db


class TestSQLAlchemy(TestCase):
    def test_session(self):

        session = db.session()
        self.assertEqual(db.session(), db.session())
        self.assertFalse(session.autocommit)

        db.remove()
        session = db.session(autocommit=True)
        self.assertTrue(session.autocommit)

        with self.assertRaises(sa.exc.InvalidRequestError):
            db.session(autocommit=True)

    def test_callable(self):

        session = db()
        self.assertEqual(db(), db())
        self.assertFalse(session.autocommit)

        db.remove()
        session = db(autocommit=True)
        self.assertTrue(session.autocommit)

        with self.assertRaises(sa.exc.InvalidRequestError):
            db(autocommit=True)

    def test_url(self):
        self.assertEqual(db.bind.url, db.url)

    def test_repr(self):
        self.assertEqual(repr(db), "<SQLAlchemy engine=postgresql://postgres@localhost/test>")

    def test_queryproperty(self):
        qp = db.queryproperty(ModelOne)
        self.assertEqual(qp.model, ModelOne)
        self.assertEqual(qp.ops, [])

        qp = db.queryproperty(ModelOne, name="test")
        self.assertEqual(qp.model, ModelOne)
        self.assertEqual(qp.ops, [Operation(name="filter_by", args=(), kwargs={"name": "test"})])

    def test_inspector(self):
        inspector = db.inspector
        self.assertListEqual(inspector.get_schema_names(), ["information_schema", "public"])

    def test_make_args(self):
        self.assertEqual(db.args("test", other=True), ("test", {"other": True}))

    def test_atomic_decorator(self):
        @db.atomic()
        def do_something():
            db.add(Owner(first_name="test", last_name="last"))

        do_something()
        self.assertEqual(Owner.query.count(), 1)

    def test_atomic_decorator_exception(self):
        @db.atomic()
        def do_something():
            db.add(Owner(first_name="test", last_name="last"))
            raise Exception()

        with suppress(Exception):
            do_something()

        self.assertEqual(Owner.query.count(), 0)

    def test_atomic_context(self):

        with db.atomic():
            db.add(Owner(first_name="test", last_name="last"))

        self.assertEqual(Owner.query.count(), 1)

    def test_atomic_context_exception(self):

        with suppress(Exception), db.atomic():
            db.add(Owner(first_name="test", last_name="last"))
            raise Exception()

        self.assertEqual(Owner.query.count(), 0)
