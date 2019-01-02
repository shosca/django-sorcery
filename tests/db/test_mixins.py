# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError

from ..base import TestCase
from ..testapp.models import Owner, Part, Vehicle


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

    def test_full_clean_recursive_empty(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=None), None])

        with self.assertRaises(ValidationError) as e:
            owner.full_clean(recursive=True)

        self.assertEqual(e.exception.message_dict, {"vehicles": [{"paint": ["Can't have a pink car"]}]})
