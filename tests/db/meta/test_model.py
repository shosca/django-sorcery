# -*- coding: utf-8 -*-

import sqlalchemy as sa

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...otherapp.models import OtherAppInOtherApp
from ...testapp.models import Business, CompositePkModel, Owner, Vehicle


class TestModelMeta(TestCase):
    def test_model_meta(self):
        info = meta.model_info(Owner)

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
                "_init",
                "app_config",
                "app_label",
                "clean_fields",
                "clean_nested_fields",
                "clean_relation_fields",
                "column_properties",
                "composites",
                "concrete_fields",
                "field_names",
                "fields",
                "first_name",
                "full_clean",
                "get_field",
                "get_key",
                "id",
                "identity_key_from_dict",
                "identity_key_from_instance",
                "label",
                "label_lower",
                "last_name",
                "local_fields",
                "mapper",
                "model",
                "model_class",
                "model_name",
                "object_name",
                "opts",
                "ordering",
                "primary_keys",
                "primary_keys_from_dict",
                "primary_keys_from_instance",
                "private_fields",
                "properties",
                "relationships",
                "run_validators",
                "sa_state",
                "unique_together",
                "vehicles",
                "verbose_name",
                "verbose_name_plural",
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

        self.assertEqual(info.label, "tests.testapp.Business")
        self.assertEqual(info.label_lower, "tests.testapp.business")

        info = meta.model_info(Vehicle)
        self.assertEqual(info.private_fields, ())

        self.assertEqual(
            {f.name for f in info.local_fields},
            {"id", "name", "type", "created_at", "paint", "is_used", "msrp", "owner", "parts", "options"},
        )
        for f in info.local_fields:
            self.assertEqual(f, info.get_field(f.name))

    def test_app(self):
        info = meta.model_info(Owner)
        self.assertIs(info.app_config, apps.get_containing_app_config(Owner.__module__))

        info = meta.model_info(OtherAppInOtherApp)
        self.assertIs(info.app_config, apps.get_containing_app_config(Owner.__module__))

    def test_reprs(self):
        owner_info = meta.model_info(Owner)
        self.assertEqual(
            repr(owner_info),
            "\n".join(
                [
                    "<model_info(Owner)>",
                    "    <integer_column_info(Owner.id) pk>",
                    "    <string_column_info(Owner.first_name)>",
                    "    <string_column_info(Owner.last_name)>",
                    "    <relation_info(Owner.vehicles)>",
                ]
            ),
        )

        vehicle_info = meta.model_info(Vehicle)
        self.assertEqual(
            repr(vehicle_info),
            "\n".join(
                [
                    "<model_info(Vehicle)>",
                    "    <integer_column_info(Vehicle.id) pk>",
                    "    <integer_column_info(Vehicle._owner_id)>",
                    "    <datetime_column_info(Vehicle.created_at)>",
                    "    <boolean_column_info(Vehicle.is_used)>",
                    "    <numeric_column_info(Vehicle.msrp)>",
                    "    <string_column_info(Vehicle.name)>",
                    "    <choice_column_info(Vehicle.paint)>",
                    "    <enum_column_info(Vehicle.type)>",
                    "    <relation_info(Vehicle.options)>",
                    "    <relation_info(Vehicle.owner)>",
                    "    <relation_info(Vehicle.parts)>",
                ]
            ),
        )
        business_info = meta.model_info(Business)
        self.assertEqual(
            repr(business_info),
            "\n".join(
                [
                    "<model_info(Business)>",
                    "    <integer_column_info(Business.id) pk>",
                    "    <integer_column_info(Business.employees)>",
                    "    <string_column_info(Business.name)>",
                    "    <composite_info(Address, Business.location)>",
                    "        <enum_column_info(Address.state)>",
                    "        <string_column_info(Address.street)>",
                    "        <string_column_info(Address.zip)>",
                    "    <composite_info(Address, Business.other_location)>",
                    "        <enum_column_info(Address.state)>",
                    "        <string_column_info(Address.street)>",
                    "        <string_column_info(Address.zip)>",
                ]
            ),
        )

    def test_inspect(self):
        info = meta.model_info(Owner)
        self.assertIsInstance(info.sa_state(Owner()), sa.orm.state.InstanceState)

    def test_get_field(self):
        info = meta.model_info(Owner)
        self.assertIs(info.get_field("first_name"), info.properties.get("first_name"))

        with self.assertRaises(FieldDoesNotExist):
            info.get_field("zzzzzz")

    def test_column_properties(self):
        info = meta.model_info(Owner)

        self.assertListEqual(
            list(info.column_properties),
            [("id", info.id), ("first_name", info.first_name), ("last_name", info.last_name)],
        )

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
