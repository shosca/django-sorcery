# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError

from ..base import TestCase
from ..testapp.models import Address, Business, Owner, Part, Vehicle, VehicleType, db


class TestCleanMixin(TestCase):
    maxDiff = None

    def test_full_clean_recursive(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=Owner(first_name="invalid"))])

        self.assertRaisesWithMessageDict(
            owner,
            {"vehicles": [{"paint": ["Can't have a pink car"], "owner": {"first_name": ["Invalid first name"]}}]},
            recursive=True,
        )

    def test_full_clean_recursive_unloaded(self):
        owner = Part(vehicles=[Vehicle(type=VehicleType.car, paint="blue", owner=Owner(first_name="valid"))])
        db.add(owner)
        db.flush()

        # make owner invalid but pop from instance state
        # so full_clean() never validates owner
        owner.vehicles[0].owner.first_name = "invalid"
        owner.vehicles[0].__dict__.pop("owner")

        self.assertIsNone(owner.full_clean(recursive=True))

    def test_full_clean_recursive_empty(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=None), None])

        self.assertRaisesWithMessageDict(owner, {"vehicles": [{"paint": ["Can't have a pink car"]}]}, recursive=True)

    def test_full_clean_exclude_specific_fields(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=Owner(first_name="invalid"))])

        self.assertIsNone(owner.full_clean(recursive=True, exclude=["vehicles"]))
        self.assertIsNone(owner.full_clean(recursive=True, exclude={"vehicles": []}))
        self.assertIsNone(owner.full_clean(recursive=True, exclude={"vehicles": {}}))
        self.assertIsNone(owner.full_clean(recursive=True, exclude={"vehicles": ["paint", "owner"]}))
        self.assertIsNone(owner.full_clean(recursive=True, exclude={"vehicles": {"paint": None, "owner": {}}}))

    def test_full_clean_exclude_recursive_specific_fields(self):
        owner = Part(vehicles=[Vehicle(paint="pink", owner=Owner(first_name="invalid"))])

        self.assertRaisesWithMessageDict(
            owner,
            {"vehicles": [{"owner": {"first_name": ["Invalid first name"]}}]},
            recursive=True,
            exclude={"vehicles": ["paint"]},
        )
        self.assertRaisesWithMessageDict(
            owner,
            {"vehicles": [{"owner": {"first_name": ["Invalid first name"]}}]},
            recursive=True,
            exclude={"vehicles": {"paint": None}},
        )
        self.assertRaisesWithMessageDict(
            owner,
            {"vehicles": [{"paint": ["Can't have a pink car"]}]},
            recursive=True,
            exclude={"vehicles": {"owner": ["first_name"]}},
        )
        self.assertRaisesWithMessageDict(
            owner,
            {"vehicles": [{"paint": ["Can't have a pink car"]}]},
            recursive=True,
            exclude={"vehicles": {"owner": {"first_name": None}}},
        )

    def test_composite_full_clean(self):
        business = Business(location=None, other_location=Address(zip="01234", state="ny"))

        self.assertRaisesWithMessageDict(
            business,
            {
                "location": ["Primary location is required when other location is provided."],
                "other_location": {
                    "__all__": ["All state, street, zip are required."],
                    "state": ["Select a valid choice. ny is not one of the " "available choices."],
                    "zip": ["Zip cannot start with 0."],
                },
            },
            recursive=True,
        )
        self.assertRaisesWithMessageDict(
            business,
            {
                "location": ["Primary location is required when other location is provided."],
                "other_location": {
                    "__all__": ["All state, street, zip are required."],
                    "state": ["Select a valid choice. ny is not one of the available choices."],
                },
            },
            recursive=True,
            exclude={"other_location": {"zip": None}},
        )
        self.assertRaisesWithMessageDict(
            business,
            {
                "location": ["Primary location is required when other location is provided."],
                "other_location": {
                    "__all__": ["All state, street, zip are required."],
                    "state": ["Select a valid choice. ny is not one of the available choices."],
                },
            },
            recursive=True,
            exclude={"other_location": ["zip"]},
        )
        self.assertRaisesWithMessageDict(
            business,
            {"location": ["Primary location is required when other location is provided."]},
            recursive=True,
            exclude=["other_location"],
        )

    def assertRaisesWithMessageDict(self, model, expected, **kwargs):
        with self.assertRaises(ValidationError) as e:
            model.full_clean(**kwargs)

        self.assertEqual(e.exception.message_dict, expected)
