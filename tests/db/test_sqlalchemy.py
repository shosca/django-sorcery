# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django_sorcery.db.query import Operation
from django_sorcery.utils import suppress

from ..base import TestCase
from ..models import ModelOne, Owner, db


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
        self.assertEqual(repr(db), "<SQLAlchemy engine=sqlite://>")

    def test_queryproperty(self):
        qp = db.queryproperty(ModelOne)
        self.assertEqual(qp.model, ModelOne)
        self.assertEqual(qp.ops, [])

        qp = db.queryproperty(ModelOne, name="test")
        self.assertEqual(qp.model, ModelOne)
        self.assertEqual(qp.ops, [Operation(name="filter_by", args=(), kwargs={"name": "test"})])

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


class TestSQLAlchemyRelationships(TestCase):
    def setUp(self):
        super(TestSQLAlchemyRelationships, self).setUp()
        from ..models_order import db, Asset, Customer, Order, Contact

        self.db = db
        self.asset = Asset
        self.customer = Customer
        self.order = Order
        self.contact = Contact

    def tearDown(self):
        super(TestSQLAlchemyRelationships, self).setUp()
        self.db.rollback()
        self.db.remove()

    def test_relations(self):
        db = self.db
        Asset = self.asset
        Customer = self.customer
        Order = self.order
        Contact = self.contact

        self.assertTrue(hasattr(Asset, "_order_pk"))
        self.assertTrue(hasattr(Order, "_order_item_pk"))
        self.assertTrue(hasattr(Order, "_applicant_pk"))
        self.assertTrue(hasattr(Order, "_coapplicant_pk"))

        order = Order(applicant=Customer())
        order.coapplicant = Customer()
        order.assets = [Asset(), Asset()]

        db.add(order)

        self.assertEqual(len(db.new), 5)

        db.flush()

        self.assertEqual(order.applicant.pk, order._applicant_pk)
        for item in order.assets:
            self.assertEqual(item._order_pk, order.pk)
            self.assertEqual(item.order, order)

        db.rollback()

        for _ in range(10):
            order = Order(applicant=Customer())
            order.coapplicant = Customer()
            order.assets = [Asset(), Asset()]
            order.contacts = [Contact(), Contact()]

            other_order = Order()
            other_order.contacts.extend(order.contacts)

            db.add(order)

        db.flush()
        db.expire_all()

        association_table_name = Order.contacts.info["table_name"]
        self.assertIsNotNone(db.Model.metadata.tables.get(association_table_name))

        tbl = db.Model.metadata.tables.get(association_table_name)
        rows = db.execute(tbl.select()).fetchall()

        orderrows = {}
        contactrows = {}
        for row in rows:
            orderrows.setdefault(row.order_pk, set()).add(row.contact_pk)
            contactrows.setdefault(row.contact_pk, set()).add(row.order_pk)

        for order in Order.query:
            self.assertEqual(len(order.contacts), 2)
            for contract in order.contacts:
                self.assertIn(contract.pk, orderrows[order.pk])

        for contact in Contact.query:
            self.assertEqual(len(contact.orders), 2)
            for order in contact.orders:
                self.assertIn(order.pk, contactrows[contact.pk])

    def test_bad_many_to_many(self):
        db = self.db

        with self.assertRaises(sa.exc.ArgumentError):

            class SuperDummy(db.Model):
                bad = db.ManyToMany("blah")


class TestSQLAlchemyRelationshipsBackPopulates(TestCase):
    def setUp(self):
        super(TestSQLAlchemyRelationshipsBackPopulates, self).setUp()

        from ..models_backpop import db, Asset, Customer, Order, Contact

        self.db = db
        self.asset = Asset
        self.customer = Customer
        self.order = Order
        self.contact = Contact

        db.Model.metadata.create_all(bind=db.engine)

    def test_relations(self):
        db = self.db
        Asset = self.asset
        Customer = self.customer
        Order = self.order
        Contact = self.contact

        self.assertTrue(hasattr(Asset, "_order_pk"))
        self.assertTrue(hasattr(Order, "_order_item_pk"))
        self.assertTrue(hasattr(Order, "_applicant_pk"))
        self.assertTrue(hasattr(Order, "_coapplicant_pk"))

        order = Order(applicant=Customer())
        order.coapplicant = Customer()
        order.assets = [Asset(), Asset()]

        db.add(order)

        self.assertEqual(len(db.new), 5)

        db.flush()

        self.assertEqual(order.applicant.pk, order._applicant_pk)
        for item in order.assets:
            self.assertEqual(item._order_pk, order.pk)
            self.assertEqual(item.order, order)

        db.rollback()

        for _ in range(10):
            order = Order(applicant=Customer())
            order.coapplicant = Customer()
            order.assets = [Asset(), Asset()]
            order.contacts = [Contact(), Contact()]

            other_order = Order()
            other_order.contacts.extend(order.contacts)

            db.add(order)

        db.flush()
        db.expire_all()

        association_table_name = Order.contacts.info["table_name"]
        self.assertIsNotNone(db.Model.metadata.tables.get(association_table_name))

        tbl = db.Model.metadata.tables.get(association_table_name)
        rows = db.execute(tbl.select()).fetchall()

        orderrows = {}
        contactrows = {}
        for row in rows:
            orderrows.setdefault(row.order_pk, set()).add(row.contact_pk)
            contactrows.setdefault(row.contact_pk, set()).add(row.order_pk)

        for order in Order.query:
            self.assertEqual(len(order.contacts), 2)
            for contract in order.contacts:
                self.assertIn(contract.pk, orderrows[order.pk])

        for contact in Contact.query:
            self.assertEqual(len(contact.orders), 2)
            for order in contact.orders:
                self.assertIn(order.pk, contactrows[contact.pk])
