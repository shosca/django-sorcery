# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bs4 import BeautifulSoup

from django import test

from django_sorcery.db import databases


try:
    from unittest import mock  # noqa
except ImportError:
    import mock  # noqa


class TestCase(test.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.maxDiff = None
        self.factory = test.RequestFactory()

    def tearDown(self):
        databases.rollback()
        databases.remove()
        super(TestCase, self).tearDown()

    def get_soup(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for select in soup.find_all("select"):
            # normalizing multiple attribute between django versions
            if select.get("multiple"):
                select["multiple"] = ""

        return soup
