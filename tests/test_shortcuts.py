# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.http import Http404

from django_sorcery import shortcuts

from .base import TestCase
from .models import Owner, db


class TestShortcuts(TestCase):
    def setUp(self):
        super(TestShortcuts, self).setUp()
        db.add_all(
            [
                Owner(first_name="Test 1", last_name="Owner 1"),
                Owner(first_name="Test 2", last_name="Owner 2"),
                Owner(first_name="Test 3", last_name="Owner 3"),
                Owner(first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.flush()

    def test_get_object_or_404(self):

        obj = shortcuts.get_object_or_404(Owner, id=1)
        self.assertIsNotNone(obj)

        with self.assertRaises(Http404):
            shortcuts.get_object_or_404(Owner, id=999)

        obj = shortcuts.get_object_or_404(Owner.query, id=1)
        self.assertIsNotNone(obj)

        with self.assertRaises(Http404):
            shortcuts.get_object_or_404(Owner.query, id=999)

    def test_get_list_or_404(self):

        obj = shortcuts.get_list_or_404(Owner)
        self.assertTrue(list(obj))

        with self.assertRaises(Http404):
            shortcuts.get_list_or_404(Owner, Owner.first_name.ilike("XXX"))

        obj = shortcuts.get_list_or_404(Owner, first_name="Test 1")
        self.assertTrue(list(obj))

        with self.assertRaises(Http404):
            shortcuts.get_list_or_404(Owner, first_name="XXX")
