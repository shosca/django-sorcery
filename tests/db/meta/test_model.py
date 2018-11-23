# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...testapp.models import Business, CompositePkModel, Owner, Vehicle


class TestModelMeta(TestCase):
    def test_model_meta(self):
        info = meta.model_info(Owner)

        self.assertEqual(repr(info), "<model_info(Owner)>")
        self.assertEqual(set(info.primary_keys.keys()), {"id"})
        self.assertEqual(info.primary_keys["id"].property, Owner.id.property)

        self.assertEqual(set(info.properties.keys()), {"first_name", "last_name"})
        self.assertEqual(info.properties["first_name"].property, Owner.first_name.property)
        self.assertEqual(info.properties["last_name"].property, Owner.last_name.property)

        self.assertEqual(set(info.relationships.keys()), {"vehicles"})
        self.assertTrue(info.relationships["vehicles"].relationship is Owner.vehicles.property)

        self.assertEqual(set(info.field_names), {"id", "first_name", "last_name", "vehicles"})

        self.assertEqual(
            [attr for attr in dir(info) if not attr.startswith("__")],
            [
                "_configure",
                "_field_names",
                "composites",
                "field_names",
                "first_name",
                "get_key",
                "id",
                "identity_key_from_dict",
                "identity_key_from_instance",
                "last_name",
                "mapper",
                "model_class",
                "primary_keys",
                "primary_keys_from_dict",
                "primary_keys_from_instance",
                "properties",
                "relationships",
                "vehicles",
            ],
        )
        self.assertEqual(info.id, info.primary_keys["id"])
        self.assertEqual(info.first_name, info.properties["first_name"])
        self.assertEqual(info.vehicles, info.relationships["vehicles"])
        with self.assertRaises(AttributeError):
            info.abc

        info = meta.model_info(Business)
        self.assertEqual(info.location, info.composites["location"])
        self.assertEqual(info.other_location, info.composites["other_location"])
        self.assertNotEqual(info.location, info.other_location)

    def test_model_meta_with_mapper(self):
        mapper = Vehicle.owner.property.parent
        self.assertEqual(meta.model_info(mapper), meta.model_info(Vehicle))

    def test_primary_keys_from_dict(self):
        info = meta.model_info(Owner)

        key = info.primary_keys_from_dict({"id": 1})
        self.assertEqual(key, 1)

        info = meta.model_info(CompositePkModel)
        key = info.primary_keys_from_dict({"id": 1, "pk": 2})
        self.assertEqual(key, (1, 2))

    def test_primary_keys_from_instance(self):
        info = meta.model_info(Owner)
        instance = Owner(id=1)

        self.assertIsNone(info.primary_keys_from_instance(None))

        key = info.primary_keys_from_instance(instance)
        self.assertEqual(key, 1)

        info = meta.model_info(CompositePkModel)
        instance = CompositePkModel(id=1, pk=2)

        key = info.primary_keys_from_instance(instance)
        self.assertDictEqual(key, {"id": 1, "pk": 2})

    def test_get_key(self):
        info = meta.model_info(Owner)
        owner = Owner(id=1)

        key = info.get_key(owner)
        self.assertEqual(key, (1,))
        self.assertIsNone(info.get_key(Owner()))

    def test_identity_key_from_instance(self):
        info = meta.model_info(Owner)
        owner = Owner(id=1)

        key = info.identity_key_from_instance(owner)
        self.assertEqual(key, meta.Identity(Owner, (1,)))
        self.assertIsNone(info.identity_key_from_instance(Owner()))

    def test_identity_key_from_dict(self):
        info = meta.model_info(Owner)

        key = info.identity_key_from_dict({"id": 1})
        self.assertEqual(key, meta.Identity(Owner, (1,)))
        self.assertIsNone(info.identity_key_from_dict({}))
