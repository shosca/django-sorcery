# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django_sorcery.db import meta  # noqa

from ..base import TestCase
from ..models import COLORS, Owner, Vehicle, VehicleType, Vertex


class TestModelMeta(TestCase):

    def test_model_meta(self):
        info = meta.model_info(Owner)

        self.assertListEqual(list(info.primary_keys.keys()), ["id"])
        self.assertEqual(info.primary_keys["id"].property, Owner.id.property)

        self.assertListEqual(list(info.properties.keys()), ["first_name", "last_name"])
        self.assertEqual(info.properties["first_name"].property, Owner.first_name.property)
        self.assertEqual(info.properties["last_name"].property, Owner.last_name.property)

        self.assertListEqual(list(info.relationships.keys()), ["vehicles"])
        self.assertTrue(info.relationships["vehicles"].relationship is Owner.vehicles.property)

        self.assertListEqual(info.field_names, ["id", "first_name", "last_name", "vehicles"])


class TestCompositeMeta(TestCase):

    def test_composite_meta(self):

        info = meta.model_info(Vertex)
        self.assertListEqual(list(info.composites.keys()), ["start", "end"])

        start = info.composites["start"]
        self.assertListEqual(sorted(start.properties.keys()), ["x", "y"])
        self.assertEqual(start.properties["x"].property, Vertex.x1.property)

        self.assertListEqual(sorted(start.field_names), ["x", "y"])


class TestRelationshipMeta(TestCase):

    def test_relationship_meta(self):
        info = meta.model_info(Owner)

        rel = info.relationships["vehicles"]

        self.assertEqual(rel.related_model, Vehicle)
        self.assertEqual(rel.name, "vehicles")
        self.assertEqual(rel.direction, sa.orm.relationships.ONETOMANY)
        self.assertEqual(list(rel.foreign_keys), Vehicle._owner_id.property.columns)
        self.assertTrue(rel.uselist)


class TestColumnMeta(TestCase):

    def test_columnInfo(self):
        info = meta.model_info(Vehicle)

        col = info.primary_keys["id"]
        self.assertEqual(col.name, "id")
        self.assertDictEqual({"label": "Id", "help_text": "The primary key", "required": True}, col.field_kwargs)

        col = info.properties["type"]
        self.assertDictEqual(
            {"enum_class": VehicleType, "help_text": None, "label": "Type", "max_length": 3, "required": True},
            col.field_kwargs,
        )

        col = info.properties["paint"]
        self.assertDictEqual(
            {"choices": COLORS, "help_text": None, "label": "Paint", "max_length": 6, "required": False},
            col.field_kwargs,
        )
