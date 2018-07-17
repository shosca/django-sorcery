# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db.composites import CompositeField

from ..base import TestCase
from ..models import Address, Business, db


class TestComposite(TestCase):
    def test_autogenerate_columns(self):

        self.assertIsInstance(Business.location.property, CompositeField)
        self.assertIsInstance(Business.other_location.property, CompositeField)

        location_props = [p.key for p in Business.location.property.props]
        other_location_props = [p.key for p in Business.other_location.property.props]

        self.assertListEqual(["_location_state", "_location_street", "_location_zip"], location_props)

        self.assertListEqual(["_foo_state", "_foo_street", "_foo_zip"], other_location_props)

    def test_can_persist(self):

        instance = Business()
        instance.location = Address("NY", "street", "123")
        instance.other_location = Address(street="other street", state="NJ", zip="456")
        db.add(instance)
        db.flush()
        db.expire_all()

        instance = Business.objects.first()

        self.assertEqual(sorted(instance.location.__composite_values__()), sorted(("street", "NY", "123")))
        self.assertEqual(sorted(instance.other_location.__composite_values__()), sorted(("other street", "NJ", "456")))

    def test_repr(self):
        self.assertEqual(
            repr(Address(street=str("other street"), state=str("NJ"), zip=str("456"))),
            "Address(state='NJ', street='other street', zip='456')",
        )
        self.assertEqual(repr(Address(state=str("NJ"), zip=str("456"))), "Address(state='NJ', zip='456')")

    def test_eq(self):
        self.assertEqual(
            Address(street=str("other street"), state=str("NJ"), zip=str("456")),
            Address(street=str("other street"), state=str("NJ"), zip=str("456")),
        )
        self.assertNotEqual(
            Address(street=str("other street"), state=str("NJ"), zip=str("456")),
            Address(street=str("another street"), state=str("NJ"), zip=str("456")),
        )
        self.assertFalse(Address(street=str("other street"), state=str("NJ"), zip=str("456")).__eq__(None))

    def test_bool(self):
        self.assertTrue(Address(street=str("street")))
        self.assertFalse(Address())
