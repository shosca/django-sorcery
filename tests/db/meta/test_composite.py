# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...testapp.models import Point, Vertex


class TestCompositeMeta(TestCase):
    def test_composite_meta(self):

        info = meta.model_info(Vertex)
        self.assertEqual(set(info.composites.keys()), {"start", "end"})

        self.assertListEqual(
            repr(info).split("\n"),
            [
                "<model_info(Vertex)>",
                "    <integer_column_info(Vertex.pk) pk>",
                "    <integer_column_info(Vertex.x1)>",
                "    <integer_column_info(Vertex.x2)>",
                "    <integer_column_info(Vertex.y1)>",
                "    <integer_column_info(Vertex.y2)>",
                "    <composite_info(Point, Vertex.end)>",
                "        <integer_column_info(Vertex.x2)>",
                "        <integer_column_info(Vertex.y2)>",
                "    <composite_info(Point, Vertex.start)>",
                "        <integer_column_info(Vertex.x1)>",
                "        <integer_column_info(Vertex.y1)>",
            ],
        )

        start = info.composites["start"]
        self.assertEqual(set(start.properties.keys()), {"x", "y"})
        self.assertEqual(start.properties["x"].property, Vertex.x1.property)
        self.assertEqual(start.properties["y"].property, Vertex.y1.property)

        end = info.composites["end"]
        self.assertEqual(set(end.properties.keys()), {"x", "y"})
        self.assertEqual(end.properties["x"].property, Vertex.x2.property)
        self.assertEqual(end.properties["y"].property, Vertex.y2.property)

        self.assertEqual(set(start.field_names), {"x", "y"})
        self.assertEqual(start.related_model, Point)
