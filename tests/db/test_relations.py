# -*- coding: utf-8 -*-

import sqlalchemy as sa

from .. import models_backpop
from ..base import TestCase
from ..minimalapp import models


class TestSQLAlchemyRelationships(TestCase):
    def tearDown(self):
        super().setUp()
        self.addCleanup(models.db.rollback)
        self.addCleanup(models.db.remove)
        self.addCleanup(models_backpop.db.rollback)
        self.addCleanup(models_backpop.db.remove)

    def _test_relations(self, module):
        self.assertTrue(hasattr(module.Asset, "_order_pk"))
        self.assertTrue(hasattr(module.Order, "_order_item_pk"))
        self.assertTrue(hasattr(module.Order, "_applicant_pk"))
        self.assertTrue(hasattr(module.Order, "_coapplicant_pk"))
        self.assertTrue(hasattr(module.Profile, "_customer_pk"))

        order = module.Order(applicant=module.Customer(profile=module.Profile()))
        order.coapplicant = module.Customer(profile=module.Profile())
        order.assets = [module.Asset(), module.Asset()]

        module.db.add(order)

        self.assertEqual(len(module.db.new), 7)

        module.db.flush()

        self.assertEqual(order.applicant.pk, order._applicant_pk)
        for item in order.assets:
            self.assertEqual(item._order_pk, order.pk)
            self.assertEqual(item.order, order)

        module.db.rollback()

        for _ in range(10):
            order = module.Order(applicant=module.Customer(profile=module.Profile()))
            order.coapplicant = module.Customer(profile=module.Profile())
            order.assets = [module.Asset(), module.Asset()]
            order.contacts = [module.Contact(), module.Contact()]

            other_order = module.Order()
            other_order.contacts.extend(order.contacts)

            module.db.add(order)

        module.db.flush()
        module.db.expire_all()

        association_table_name = module.Order.contacts.info["table_name"]
        self.assertIsNotNone(module.db.Model.metadata.tables.get(association_table_name))

        tbl = module.db.Model.metadata.tables.get(association_table_name)
        rows = module.db.execute(tbl.select()).fetchall()

        orderrows = {}
        contactrows = {}
        for row in rows:
            orderrows.setdefault(row.order_pk, set()).add(row.contact_pk)
            contactrows.setdefault(row.contact_pk, set()).add(row.order_pk)

        for order in module.Order.query:
            self.assertEqual(len(order.contacts), 2)
            for contract in order.contacts:
                self.assertIn(contract.pk, orderrows[order.pk])

        for contact in module.Contact.query:
            self.assertEqual(len(contact.orders), 2)
            for order in contact.orders:
                self.assertIn(order.pk, contactrows[contact.pk])

    def test_relations(self):
        self._test_relations(models)
        self._test_relations(models_backpop)

    def test_bad_many_to_many(self):
        with self.assertRaises(sa.exc.ArgumentError):

            class SuperDummy(models.db.Model):
                bad = models.db.ManyToMany("blah")
