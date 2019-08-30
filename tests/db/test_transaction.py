# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError

from django_sorcery.db.transaction import TransactionContext

from ..base import TestCase
from ..testapp.models import Owner, db


class TestTransaction(TestCase):
    def setUp(self):
        super().setUp()
        Owner.query.delete()
        db.commit()
        db.remove()

    def tearDown(self):
        Owner.query.delete()
        db.commit()

    def test_transaction_context(self):

        transaction = TransactionContext(db)
        self.assertEqual(transaction.dbs, (db,))
        self.assertTrue(transaction.savepoint)
        self.assertIsNone(transaction.transactions)

    def test_decorator(self):
        @TransactionContext(db)
        def do_stuff():
            db.add(Owner(first_name="The", last_name="Dude"))

        do_stuff()
        self.assertEqual(Owner.objects.count(), 1)

    def test_decorator_invalid(self):
        @TransactionContext(db)
        def do_stuff():
            db.add(Owner(first_name="invalid", last_name="Dude"))

        with self.assertRaises(ValidationError):
            do_stuff()

        self.assertEqual(Owner.objects.count(), 0)

    def test_context_manager(self):

        with TransactionContext(db):
            db.add(Owner(first_name="The", last_name="Dude"))

        self.assertEqual(Owner.objects.count(), 1)

    def test_context_manager_invalid(self):

        with self.assertRaises(ValidationError):
            with TransactionContext(db):
                db.add(Owner(first_name="invalid", last_name="Dude"))

        self.assertEqual(Owner.objects.count(), 0)
