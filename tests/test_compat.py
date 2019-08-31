# -*- coding: utf-8 -*-

from django.test import TestCase

from django_sorcery import compat


class TestCompat(TestCase):
    def test_suppress(self):

        with compat.suppress(AssertionError):
            assert 1 == 2
