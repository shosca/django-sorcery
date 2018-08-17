# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.test import TestCase

from django_sorcery.management.commands.sorcery_history import Command

from .base import MigrationMixin


MIGRATION = '''"""zero

Revision ID: 000000000000
Revises:
Create Date: 2018-07-24 01:28:40.893136

"""


# revision identifiers, used by Alembic.
revision = '000000000000'
down_revision = None
branch_labels = ('zero', )
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
'''


class TestHistory(MigrationMixin, TestCase):
    def setUp(self):
        super(TestHistory, self).setUp()
        self.write_migration(MIGRATION, "000000000000_zero.py")

    def tearDown(self):
        super(TestHistory, self).tearDown()
        self.delete_migration("000000000000_zero.py")

    def test(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        cmd.run_from_argv(["./manage.py sorcery", "history", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Migrations for tests.testapp on database test\n",
                "<base> -> 000000000000 (zero) (head), zero\n",
                "Migrations for tests.otherapp on database test\n",
            ],
        )

    def test_with_range_noapp(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "history", "-r", "base:head", "--no-color"])

    def test_with_range(self):
        out = six.StringIO()

        cmd = Command(stdout=out)

        cmd.run_from_argv(["./manage.py sorcery", "history", "tests.testapp", "-r", "base:head", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            ["Migrations for tests.testapp on database test\n", "<base> -> 000000000000 (zero) (head), zero\n"],
        )

    def test_bad_range(self):
        out = six.StringIO()
        err = six.StringIO()

        cmd = Command(stdout=out, stderr=err)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "history", "tests.testapp", "-r", "base-head", "--no-color"])

        err.seek(0)
        self.assertEqual(err.readlines(), ["CommandError: History range requires [start]:[end], [start]:, or :[end]\n"])

    def test_not_alembic_app(self):
        out = six.StringIO()
        err = six.StringIO()

        cmd = Command(stdout=out, stderr=err)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "history", "foo", "--no-color"])

        err.seek(0)
        self.assertEqual(err.readlines(), ["CommandError: App 'foo' could not be found. Is it in INSTALLED_APPS?\n"])
