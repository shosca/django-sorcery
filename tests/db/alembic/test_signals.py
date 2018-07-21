# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.test import TestCase

from django_sorcery.db import signals
from django_sorcery.db.alembic.signals import include_object, include_symbol


class TestSignals(TestCase):
    def tearDown(self):
        super(TestSignals, self).tearDown()
        signals.alembic_include_object._clear_state()
        signals.alembic_include_symbol._clear_state()

    def test_default(self):
        self.assertTrue(include_symbol(None, None))
        self.assertTrue(include_object(None, None, None, None, None))

    def test_true(self):
        @signals.alembic_include_symbol.connect
        def s(*args, **kwargs):
            return True

        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return True

        self.assertTrue(include_symbol(None, None))
        self.assertTrue(include_object(None, None, None, None, None))

    def test_false(self):
        @signals.alembic_include_symbol.connect
        def s(*args, **kwargs):
            return False

        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return False

        self.assertFalse(include_symbol(None, None))
        self.assertFalse(include_object(None, None, None, None, None))
