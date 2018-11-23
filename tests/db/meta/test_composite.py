# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...testapp.models import Point, Vertex


class TestCompositeMeta(TestCase):
    def test_composite_meta(self):

        info = meta.model_info(Vertex)
        self.assertEqual(set(info.composites.keys()), {"start", "end"})

        start = info.composites["start"]
        end = info.composites["end"]
        self.assertEqual(set(start.properties.keys()), {"x", "y"})
        self.assertEqual(start.properties["x"].property, Vertex.x1.property)
        self.assertEqual(repr(start), "<composite_info(Point, Vertex.start)>")
        self.assertEqual(repr(end), "<composite_info(Point, Vertex.end)>")

        self.assertEqual(set(start.field_names), {"x", "y"})
        self.assertEqual(start.related_model, Point)
