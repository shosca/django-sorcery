# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.test import TestCase

from django_sorcery.db import signals
from django_sorcery.db.alembic.signals import include_object


class TestSignals(TestCase):
    def tearDown(self):
        super(TestSignals, self).tearDown()
        signals.alembic_include_object._clear_state()

    def test_default(self):
        self.assertTrue(include_object(None, None, None, None, None))

    def test_true(self):
        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return True

        self.assertTrue(include_object(None, None, None, None, None))

    def test_false(self):
        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return False

        self.assertFalse(include_object(None, None, None, None, None))
