# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_stamp import Command

from .base import MigrationMixin


M1 = '''"""zero

Revision ID: 000000000000
Revises:
Create Date: 2018-07-24 01:28:40.893136

"""


# revision identifiers, used by Alembic.
revision = '000000000000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
'''

db = databases.get("test")


class TestStamp(MigrationMixin, TestCase):
    def setUp(self):
        super(TestStamp, self).setUp()

        self.delete_migration("{}_.py".format("000000000000"))
        self.write_migration(M1, "{}_.py".format("000000000000"))

    def tearDown(self):
        super(TestStamp, self).tearDown()

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "--no-color"])
        self.delete_migration("{}_.py".format("000000000000"))
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "--no-color"])

    def test(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "stamp", "tests.testapp", "--no-color"])

        revs = db.execute("select * from alembic_version_tests_testapp").fetchall()
        self.assertEqual(revs, [("000000000000",)])

    def test_bad_rev(self):
        out = six.StringIO()
        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "stamp", "tests.testapp", "-r", ":000000000000", "--no-color"])
