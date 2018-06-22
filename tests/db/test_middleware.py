# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

import attr

from django_sorcery.db import SQLAlchemy, databases, middleware

from ..base import mock


class DummyMiddeware(middleware.BaseMiddleware):

    rollback_called = False
    flush_called = False
    commit_called = False
    remove_called = False

    def process_request(self, request):
        super(DummyMiddeware, self).process_request(request)
        if hasattr(self, "dummy"):
            return self.dummy

    def rollback(self, request, response):
        self.rollback_called = True

    def flush(self, request, response):
        self.flush_called = True
        if hasattr(self, "flush_error"):
            raise self.flush_error()

    def commit(self, request, response):
        self.commit_called = True

    def remove(self, request, response):
        self.remove_called = True


def get_response(request):
    return request


@attr.s
class Request(object):
    method = attr.ib(default="GET")
    status_code = attr.ib(default=200)


class TestBaseMiddleware(unittest.TestCase):
    def setUp(self):
        super(TestBaseMiddleware, self).setUp()
        self.middleware = DummyMiddeware(get_response=get_response)

    def test_process_request(self):
        self.middleware.dummy = "abcd"
        self.middleware(Request())
        self.assertFalse(self.middleware.rollback_called)
        self.assertFalse(self.middleware.flush_called)
        self.assertFalse(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_success(self):
        self.middleware(Request())
        self.assertFalse(self.middleware.rollback_called)
        self.assertTrue(self.middleware.flush_called)
        self.assertTrue(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_redirect(self):
        self.middleware(Request(status_code=300))
        self.assertFalse(self.middleware.rollback_called)
        self.assertTrue(self.middleware.flush_called)
        self.assertTrue(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_bad_request(self):
        self.middleware(Request(status_code=400))
        self.assertTrue(self.middleware.rollback_called)
        self.assertFalse(self.middleware.flush_called)
        self.assertFalse(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_server_error(self):
        self.middleware(Request(status_code=400))
        self.assertTrue(self.middleware.rollback_called)
        self.assertFalse(self.middleware.flush_called)
        self.assertFalse(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_flush_error(self):
        self.middleware.flush_error = RuntimeError
        self.middleware(Request(status_code=200))
        self.assertTrue(self.middleware.rollback_called)
        self.assertTrue(self.middleware.flush_called)
        self.assertFalse(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)

    def test_other_methods(self):
        self.middleware(Request(method="HEAD"))
        self.assertTrue(self.middleware.rollback_called)
        self.assertFalse(self.middleware.flush_called)
        self.assertFalse(self.middleware.commit_called)
        self.assertTrue(self.middleware.remove_called)


class TestSQLAlchemyDBMiddleware(unittest.TestCase):
    def setUp(self):
        super(TestSQLAlchemyDBMiddleware, self).setUp()

        self.db = mock.MagicMock()
        self.middleware = type(str("DummySQLAlchemyMiddleware"), (middleware.SQLAlchemyDBMiddleware,), {"db": self.db})(
            get_response
        )

    def test_commit(self):
        self.middleware.commit(None, None)
        self.db.commit.assert_called_once_with()

    def test_rollback(self):
        self.middleware.rollback(None, None)
        self.db.rollback.assert_called_once_with()

    def test_flush(self):
        self.middleware.flush(None, None)
        self.db.flush.assert_called_once_with()

    def test_remove(self):
        self.middleware.remove(None, None)
        self.db.remove.assert_called_once_with()


class TestSQLAlchemyMiddleware(unittest.TestCase):
    def setUp(self):
        super(TestSQLAlchemyMiddleware, self).setUp()
        self.middleware = middleware.SQLAlchemyMiddleware(get_response)
        self.orig_dbs = databases.copy()
        databases.clear()
        databases.update(one=mock.MagicMock(spec=SQLAlchemy), two=mock.MagicMock(spec=SQLAlchemy))

    def tearDown(self):
        super(TestSQLAlchemyMiddleware, self).setUp()
        databases.clear()
        databases.update(self.orig_dbs)

    def test_commit(self):
        self.middleware.commit(None, None)
        for db in databases.values():
            db.commit.assert_called_once_with()

    def test_rollback(self):
        self.middleware.rollback(None, None)
        for db in databases.values():
            db.rollback.assert_called_once_with()

    def test_flush(self):
        self.middleware.flush(None, None)
        for db in databases.values():
            db.flush.assert_called_once_with()

    def test_remove(self):
        self.middleware.remove(None, None)
        for db in databases.values():
            db.remove.assert_called_once_with()
