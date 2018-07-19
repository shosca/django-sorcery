# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from django_sorcery.db.profiler import SQLAlchemyProfilingMiddleware

from ..models import Owner, db


def get_response(request):
    db.add(Owner(first_name="foo", last_name="bar"))
    db.flush()
    db.rollback()
    db.remove()
    return HttpResponse()


class TestSQLAlchemyProfilingMiddleware(TestCase):
    @override_settings(DEBUG=True)
    def test_profiler_debug(self):
        m = SQLAlchemyProfilingMiddleware(get_response)

        response = m(RequestFactory().get("/"))

        self.assertEqual(response["X-SA-Insert"], "1")

    @override_settings(DEBUG=False)
    def test_profiler_no_debug(self):
        m = SQLAlchemyProfilingMiddleware(get_response)

        response = m(RequestFactory().get("/"))

        self.assertNotIn("X-SA-Insert", response)
