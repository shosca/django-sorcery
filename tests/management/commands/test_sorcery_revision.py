# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

import six

from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_revision import Command
from django_sorcery.management.commands.sorcery_upgrade import Upgrade

from .base import MIGRATION_DIR, MigrationMixin


rev = "000000000000"

db = databases.get("test")


class TestRevision(MigrationMixin, TestCase):
    def setUp(self):
        super(TestRevision, self).setUp()
        Upgrade().run_from_argv(["./manage.py sorcery", "upgrade", "--no-color"])

    def tearDown(self):
        super(TestRevision, self).tearDown()
        self.delete_migration("{}_.py".format(rev))
        self.delete_migration("{}_zero.py".format(rev))
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "--no-color"])

    def test_without_app(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "makemigrations", "--no-color"])

    def test_with_bad_app(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "makemigrations", "dumdum", "--no-color"])

    def test_with_name(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        cmd.run_from_argv(
            ["./manage.py sorcery", "makemigrations", "tests.testapp", "-r", rev, "-m", "zero", "--no-color"]
        )

        self.assertTrue(os.path.isfile(os.path.join(MIGRATION_DIR, "{}_zero.py".format(rev))))

    def test_longer_version_table_identifier(self):
        out = six.StringIO()
        err = six.StringIO()

        cmd = Command(stdout=out, stderr=err)

        original_length = db.engine.dialect.max_identifier_length
        db.engine.dialect.max_identifier_length = 5

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(
                ["./manage.py sorcery", "makemigrations", "tests.testapp", "-r", rev, "-m", "zero", "--no-color"]
            )

        db.engine.dialect.max_identifier_length = original_length

        err.seek(0)
        self.assertEqual(
            err.readlines(),
            [
                "CommandError: 'alembic_version_tests_testapp' is 29 characters long which "
                "is an invalid identifier in 'postgresql' as its max idenfier length is 5\n"
            ],
        )
