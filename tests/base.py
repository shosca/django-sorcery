# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import test

from .models import db


try:
    from unittest import mock  # noqa
except ImportError:
    import mock  # noqa


class TestCase(test.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.factory = test.RequestFactory()

    def tearDown(self):
        db.rollback()
        db.remove()
        super(TestCase, self).tearDown()
