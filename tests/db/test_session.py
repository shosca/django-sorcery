# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import signals  # noqa

from ..base import TestCase
from ..testapp.models import CompositePkModel, Owner, OwnerQuery, db


class TestSession(TestCase):
    def setUp(self):
        super(TestSession, self).setUp()
        Owner.query.delete()
        db.commit()
        db.remove()

        self.before_flush_signal_called = False
        self.after_flush_signal_called = False
        self.before_commit_called = False
        self.after_commit_called = False

        signals.before_flush.connect(self._before_flush, weak=False)
        signals.after_flush.connect(self._after_flush, weak=False)
        signals.before_commit.connect(self._before_commit, weak=False)
        signals.after_commit.connect(self._after_commit, weak=False)

    def _before_flush(self, session, **kwargs):
        self.before_flush_signal_called = True

    def _after_flush(self, session, **kwargs):
        self.after_flush_signal_called = True

    def _before_commit(self, session, **kwargs):
        self.before_commit_called = True

    def _after_commit(self, session, **kwargs):
        self.after_commit_called = True

    def tearDown(self):
        super(TestSession, self).tearDown()
        signals.before_flush.disconnect(self._before_flush)
        signals.after_flush.disconnect(self._after_flush)
        signals.before_commit.disconnect(self._before_commit)
        signals.after_commit.disconnect(self._after_commit)
        Owner.query.delete()
        db.commit()

    def test_session_signals(self):
        db.add(Owner(first_name="Joe", last_name="Smith"))
        db.flush()

        self.assertTrue(self.before_flush_signal_called)
        self.assertTrue(self.after_flush_signal_called)

    def test_query_class_usage(self):
        query = db.query(Owner)
        self.assertIsInstance(query, OwnerQuery)

        query = db.query(CompositePkModel)
        self.assertIsInstance(query, db.query_class)

    def test_commit_signals(self):

        with db.atomic():
            db.add(Owner(first_name="Joe", last_name="Smith"))

        self.assertFalse(self.before_commit_called)
        self.assertFalse(self.after_commit_called)

        db.commit()

        self.assertTrue(self.before_commit_called)
        self.assertTrue(self.after_commit_called)
