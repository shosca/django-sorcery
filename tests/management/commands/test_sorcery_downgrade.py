# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_upgrade import Upgrade

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

M2 = '''"""one

Revision ID: 000000000001
Revises: 000000000000
Create Date: 2018-07-24 02:02:55.504526

"""


# revision identifiers, used by Alembic.
revision = '000000000001'
down_revision = '000000000000'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
'''

db = databases.get("test")


class TestDowngrade(MigrationMixin, TestCase):
    def setUp(self):
        super(TestDowngrade, self).setUp()

        self.write_migration(M1, "{}_.py".format("000000000000"))
        self.write_migration(M2, "{}_.py".format("000000000001"))

        Upgrade().run_from_argv(["./manage.py sorcery", "upgrade", "tests.testapp", "--no-color"])

    def tearDown(self):
        super(TestDowngrade, self).tearDown()

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "--no-color"])
        for rev in ["000000000000", "000000000001"]:
            self.delete_migration("{}_.py".format(rev))

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "--no-color"])

    def test(self):
        out = six.StringIO()
        cmd = Downgrade(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "downgrade", "--no-color"])

        revs = db.execute("select * from public.alembic_version_tests_testapp").fetchall()
        self.assertEqual(revs, [])

        Upgrade().run_from_argv(["./manage.py sorcery", "upgrade", "--no-color"])

        cmd.run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "-r", "000000000000", "--no-color"])
        revs = db.execute("select * from public.alembic_version_tests_testapp").fetchall()
        self.assertEqual(revs, [("000000000000",)])

    def test_sql(self):
        out = six.StringIO()
        cmd = Downgrade(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "downgrade", "-s", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "BEGIN;\n",
                "\n",
                "DROP TABLE alembic_version_tests_otherapp;\n",
                "\n",
                "COMMIT;\n",
                "\n",
                "BEGIN;\n",
                "\n",
                "DROP TABLE public.alembic_version_tests_testapp;\n",
                "\n",
                "COMMIT;\n",
                "\n",
            ],
        )

    def test_with_range_no_app(self):
        out = six.StringIO()
        cmd = Downgrade(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "downgrade", "-r", "000000000000", "--no-color"])

    def test_with_range(self):
        out = six.StringIO()
        cmd = Downgrade(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(
                ["./manage.py sorcery", "downgrade", "tests.testapp", "-r", ":000000000000", "--no-color"]
            )
