# -*- coding: utf-8 -*-

from django.test import TestCase

from django_sorcery.db import signals
from django_sorcery.db.alembic.signals import include_object, process_revision_directives


class TestIncludeObject(TestCase):
    def tearDown(self):
        super().tearDown()
        signals.alembic_include_object._clear_state()

    def test_default(self):
        self.assertTrue(include_object(None, None, None, None, None))

    def test_true(self):
        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return True

        self.assertTrue(include_object(None, None, None, None, None))

    def test_false(self):
        @signals.alembic_include_object.connect
        def o(*args, **kwargs):
            return False

        self.assertFalse(include_object(None, None, None, None, None))


class TestProcessRevisionDirectives(TestCase):
    def setUp(self):
        super().tearDown()
        signals.alembic_process_revision_directives.connect(self._handler)

    def tearDown(self):
        super().tearDown()
        signals.alembic_process_revision_directives.disconnect(self._handler)

    def _handler(self, context, revision, directives):
        self.context = context
        self.revision = revision
        self.directives = directives

    def test_process_revision_directives(self):
        process_revision_directives({}, "abc", ("1234",))

        self.assertEqual(self.context, {})
        self.assertEqual(self.revision, "abc")
        self.assertEqual(self.directives, ("1234",))
