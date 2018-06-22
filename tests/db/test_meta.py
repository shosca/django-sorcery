# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django_sorcery.db import meta  # noqa

from ..base import TestCase
from ..models import COLORS, AllKindsOfFields, Owner, Vehicle, VehicleType, Vertex


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

    def test_model_meta_with_mapper(self):
        mapper = Vehicle.owner.property.parent
        self.assertEqual(meta.model_info(mapper), meta.model_info(Vehicle))


class TestCompositeMeta(TestCase):
    def test_composite_meta(self):

        info = meta.model_info(Vertex)
        self.assertEqual(set(info.composites.keys()), {"start", "end"})

        start = info.composites["start"]
        self.assertEqual(set(start.properties.keys()), {"x", "y"})
        self.assertEqual(start.properties["x"].property, Vertex.x1.property)

        self.assertEqual(set(start.field_names), {"x", "y"})


class TestRelationshipMeta(TestCase):
    def test_relationship_meta(self):
        info = meta.model_info(Owner)

        rel = info.relationships["vehicles"]

        self.assertEqual(rel.related_model, Vehicle)
        self.assertEqual(rel.name, "vehicles")
        self.assertEqual(rel.direction, sa.orm.relationships.ONETOMANY)
        self.assertEqual(list(rel.foreign_keys), Vehicle._owner_id.property.columns)
        self.assertTrue(rel.uselist)
        self.assertEqual(repr(rel), "<relation_info(Owner.vehicles)>")


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
        self.assertEqual(col.parent_model, Vehicle)
        self.assertEqual(repr(col), "<column_info(Vehicle.paint)>")

        info = meta.model_info(AllKindsOfFields)
        col = info.properties["decimal"]
        self.assertDictEqual(
            {"decimal_places": None, "help_text": None, "label": "Decimal", "max_digits": None, "required": False},
            col.field_kwargs,
        )
