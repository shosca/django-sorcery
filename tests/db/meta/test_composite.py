# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...testapp.models import Address, Business, Point, Vertex


class TestCompositeMeta(TestCase):
    def test_composite_meta(self):

        info = meta.model_info(Vertex)
        self.assertEqual(set(info.composites.keys()), {"start", "end"})

        self.assertListEqual(
            repr(info).split("\n"),
            [
                "<model_info(Vertex)>",
                "    <integer_column_info(Vertex.pk) pk>",
                "    <composite_info(Point, Vertex.end)>",
                "        <integer_column_info(Point.x)>",
                "        <integer_column_info(Point.y)>",
                "    <composite_info(Point, Vertex.start)>",
                "        <integer_column_info(Point.x)>",
                "        <integer_column_info(Point.y)>",
            ],
        )

        start = info.composites["start"]
        self.assertEqual(set(start.properties.keys()), {"x", "y"})
        self.assertEqual(start.properties["x"].property, Vertex.x1.property)
        self.assertEqual(start.properties["y"].property, Vertex.y1.property)
        self.assertIs(start.attribute, Vertex.start)

        end = info.composites["end"]
        self.assertEqual(set(end.properties.keys()), {"x", "y"})
        self.assertEqual(end.properties["x"].property, Vertex.x2.property)
        self.assertEqual(end.properties["y"].property, Vertex.y2.property)
        self.assertIs(end.attribute, Vertex.end)

        self.assertEqual(set(start.field_names), {"x", "y"})
        self.assertEqual(start.model_class, Point)

    def test_full_clean(self):
        instance = Business(name="foo")
        instance.other_location = Address(street="a", state="ny", zip="0456a")

        with self.assertRaises(ValidationError) as e:
            instance.full_clean()

        self.assertEqual(
            e.exception.message_dict,
            {
                "location": ["Primary location is required when other location is provided."],
                "other_location": {
                    "state": ["Select a valid choice. ny is not one of the available choices."],
                    "street": ["Street should be at least 2 characters."],
                    "zip": ["Zip cannot start with 0."],
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
                "location": ["Primary location is required when other location is provided."],
                "other_location": {
                    "street": ["Street should be at least 2 characters."],
                    "state": ["Select a valid choice. ny is not one of the available choices."],
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
