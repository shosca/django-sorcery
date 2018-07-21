# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

import six

from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_makemigrations import Command
from django_sorcery.management.commands.sorcery_upgrade import Upgrade

from .base import MIGRATION_DIR, MigrationMixin


rev = "000000000000"

db = databases.get("test")


class TestMakeMigrations(MigrationMixin, TestCase):
    def setUp(self):
        super(TestMakeMigrations, self).setUp()
        Upgrade().run_from_argv(["./manage.py sorcery", "upgrade"])

    def tearDown(self):
        super(TestMakeMigrations, self).tearDown()
        self.delete_migration("{}_.py".format(rev))
        self.delete_migration("{}_zero.py".format(rev))
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade"])

    def test_without_app(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "makemigrations"])

    def test_with_bad_app(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "makemigrations", "dumdum"])

    def test(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        cmd.run_from_argv(["./manage.py sorcery", "makemigrations", "tests.testapp", "-r", rev])

        self.assertTrue(os.path.isfile(os.path.join(MIGRATION_DIR, "{}_.py".format(rev))))

    def test_with_name(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        cmd.run_from_argv(["./manage.py sorcery", "makemigrations", "tests.testapp", "-r", rev, "-n", "zero"])

        self.assertTrue(os.path.isfile(os.path.join(MIGRATION_DIR, "{}_zero.py".format(rev))))
