# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import signals  # noqa

from ..base import TestCase
from ..models import CompositePkModel, Owner, OwnerQuery, db


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

        def before_flush(session, **kwargs):
            self.before_flush_signal_called = True

        def after_flush(session, **kwargs):
            self.after_flush_signal_called = True

        def before_commit(session, **kwargs):
            self.before_commit_called = True

        def after_commit(session, **kwargs):
            self.after_commit_called = True

        signals.before_flush.connect(before_flush, weak=False)
        signals.after_flush.connect(after_flush, weak=False)
        signals.before_commit.connect(before_commit, weak=False)
        signals.after_commit.connect(after_commit, weak=False)

    def tearDown(self):
        super(TestSession, self).tearDown()
        signals.before_flush._clear_state()
        signals.after_flush._clear_state()
        signals.before_commit._clear_state()
        signals.after_commit._clear_state()
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
