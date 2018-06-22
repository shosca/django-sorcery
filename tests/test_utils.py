# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.test import TestCase

from django_sorcery import utils


class TestUtils(TestCase):
    def test_suppress(self):

        with utils.suppress(AssertionError):
            assert 1 == 2

    def test_setdefaultattr(self):
        class Dummy(object):
            pass

        obj = Dummy()

        default = set()

        utils.setdefaultattr(obj, "test", default)

        self.assertTrue(hasattr(obj, "test"))
        self.assertEqual(obj.test, default)

        utils.setdefaultattr(obj, "test", set())

        self.assertTrue(hasattr(obj, "test"))
        self.assertEqual(obj.test, default)

    def test_make_args(self):

        value = utils.make_args("abc", kw="something")

        self.assertEqual(value, ("abc", {"kw": "something"}))
