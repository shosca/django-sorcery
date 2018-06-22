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
        instance.location = Address("street", "state", "zip")
        instance.other_location = Address(street="other street", state="other state", zip="other zip")
        db.add(instance)
        db.expire_all()

        instance = Business.objects.first()

        self.assertEqual(sorted(instance.location.__composite_values__()), sorted(("street", "state", "zip")))
        self.assertEqual(
            sorted(instance.other_location.__composite_values__()), sorted(("other street", "other state", "other zip"))
        )
