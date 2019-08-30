# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from django_sorcery.db.profiler import SQLAlchemyProfiler, SQLAlchemyProfilingMiddleware

from ..base import TestCase
from ..testapp.models import Business, Owner, db


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

    def test_log_results(self):
        with override_settings(DEBUG=True):
            self.assertTrue(SQLAlchemyProfilingMiddleware(get_response).log_results)
        with override_settings(DEBUG=False):
            self.assertFalse(SQLAlchemyProfilingMiddleware(get_response).log_results)

    def test_header_results(self):
        with override_settings(DEBUG=True):
            self.assertTrue(SQLAlchemyProfilingMiddleware(get_response).log_results)
        with override_settings(DEBUG=False):
            self.assertFalse(SQLAlchemyProfilingMiddleware(get_response).log_results)


class TestProfiler(TestCase):
    def test_profiler(self):
        profiler = SQLAlchemyProfiler(exclude=["business"])

        with profiler:
            db.add(Owner(first_name="foo", last_name="bar"))
            db.flush()
            Owner.objects.all()
            Business.objects.all()
            db.rollback()
            db.remove()

        self.assertDictEqual(
            profiler.counts,
            {
                "begin": 1,
                "engine_connect": 1,
                "execute": 2,
                "insert": 1,
                "pool_checkin": 1,
                "pool_checkout": 1,
                "pool_reset": 1,
                "rollback": 1,
                "select": 1,
            },
        )

        insert_query, select_query = profiler.queries

        self.assertTrue(insert_query.statement.lower().startswith("insert into owner"))
        self.assertTrue(insert_query.parameters, [{"first_name": "foo", "last_name": "bar"}])

        self.assertTrue(select_query.statement.lower().startswith("select owner.id"))
        self.assertTrue(select_query.parameters, [{}])
