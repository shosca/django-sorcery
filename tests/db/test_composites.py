# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db.composites import CompositeField

from ..base import TestCase
from ..testapp.models import Address, Business, States, db


class TestComposite(TestCase):
    def test_autogenerate_columns(self):

        self.assertIsInstance(Business.location.property, CompositeField)
        self.assertIsInstance(Business.other_location.property, CompositeField)

        location_props = [p.key for p in Business.location.property.props]
        other_location_props = [p.key for p in Business.other_location.property.props]

        self.assertListEqual(["_location_state", "_location_street", "_location_zip"], location_props)
        self.assertListEqual(["_foo_state", "_foo_street", "_foo_zip"], other_location_props)

        self.assertEqual(Business._location_state.prop.columns[0].type.name, "states")
        self.assertEqual(Business._foo_state.prop.columns[0].type.name, "foo_states")

    def test_can_persist(self):

        instance = Business()
        instance.location = Address(States.NY, "street", "123")
        instance.other_location = Address(street="other street", state=States.NJ, zip="456")
        db.add(instance)
        db.flush()
        db.expire_all()

        instance = Business.objects.first()

        self.assertEqual(set(instance.location.__composite_values__()), {"street", States.NY, "123"})
        self.assertEqual(set(instance.other_location.__composite_values__()), {"other street", States.NJ, "456"})

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
