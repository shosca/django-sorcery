# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError

from ..base import TestCase
from ..testapp.models import Owner, Part, Vehicle, VehicleType, db


class TestCleanMixin(TestCase):
    maxDiff = None

    def test_full_clean_recursive(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=Owner(first_name="invalid"))])

        with self.assertRaises(ValidationError) as e:
            owner.full_clean(recursive=True)

        self.assertEqual(
            e.exception.message_dict,
            {"vehicles": [{"paint": ["Can't have a pink car"], "owner": {"first_name": ["Invalid first name"]}}]},
        )

    def test_full_clean_recursive_unloaded(self):
        owner = Part(vehicles=[Vehicle(type=VehicleType.car, paint="blue", owner=Owner(first_name="valid"))])
        db.add(owner)
        db.flush()

        # make owner invalid but pop from instance state
        # so full_clean() never validates owner
        owner.vehicles[0].owner.first_name = "invalid"
        owner.vehicles[0].__dict__.pop("owner")

        owner.full_clean(recursive=True)

    def test_full_clean_recursive_empty(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=None), None])

        with self.assertRaises(ValidationError) as e:
            owner.full_clean(recursive=True)

        self.assertEqual(e.exception.message_dict, {"vehicles": [{"paint": ["Can't have a pink car"]}]})
