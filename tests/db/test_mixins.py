# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError

from ..base import TestCase
from ..models import Address, Business


class TestCleanMixin(TestCase):
    def test_full_clean(self):
        instance = Business(name="foo")
        instance.other_location = Address(street="a", state="ny", zip="0456a")

        with self.assertRaises(ValidationError) as e:
            instance.full_clean()

        self.assertEqual(
            e.exception.message_dict,
            {
                "location": ["Primary key is required when other location is provided."],
                "other_location": {
                    "street": ["Street should be at least 2 characters."],
                    "state": ["State must be uppercase."],
                    "zip": ["Enter a valid value.", "Zip cannot start with 0."],
                },
            },
        )

    def test_full_clean_exclude_inner_composite_fields(self):
        instance = Business(name="foo")
        instance.other_location = Address(street="a", state="ny", zip="0456a")

        with self.assertRaises(ValidationError) as e:
            instance.full_clean(exclude={"other_location": ["zip"]})

        self.assertEqual(
            e.exception.message_dict,
            {
                "location": ["Primary key is required when other location is provided."],
                "other_location": {
                    "street": ["Street should be at least 2 characters."],
                    "state": ["State must be uppercase."],
                },
            },
        )

    def test_full_clean_exclude_complete_composite(self):
        instance = Business(name="foo")
        instance.location = Address(street="a", state=None, zip=None)
        instance.other_location = Address(street="a", state="ny", zip="0456a")

        with self.assertRaises(ValidationError) as e:
            instance.full_clean(exclude={"other_location": None})

        self.assertEqual(
            e.exception.message_dict,
            {
                "location": {
                    "__all__": ["All state, street, zip are required."],
                    "street": ["Street should be at least 2 characters."],
                }
            },
        )
