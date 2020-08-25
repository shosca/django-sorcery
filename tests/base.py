from bs4 import BeautifulSoup
from django import test
from django_sorcery.db import databases


try:
    from unittest import mock  # noqa
except ImportError:
    from unittest import mock  # noqa


class TestCase(test.TestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.factory = test.RequestFactory()

    def tearDown(self):
        databases.rollback()
        databases.remove()
        super().tearDown()

    def get_soup(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for select in soup.find_all("select"):
            # normalizing multiple attribute between django versions
            if select.get("multiple"):
                select["multiple"] = ""

        return soup
