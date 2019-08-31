# -*- coding: utf-8 -*-

import six

from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_upgrade import Command

from .base import MigrationMixin


MIGRATION = '''"""zero

Revision ID: {rev}
Revises:
Create Date: 2018-07-24 01:28:40.893136

"""


# revision identifiers, used by Alembic.
revision = '{rev}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
'''

db = databases.get("test")


class TestUpgrade(MigrationMixin, TestCase):
    def setUp(self):
        super().setUp()
        for rev in ["000000000000", "000000000001"]:
            self.write_migration(MIGRATION.format(rev=rev), "{}_zero.py".format(rev))
            self.write_migration(MIGRATION.format(rev=rev), "{}_zero.py".format(rev))
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "--no-color"])

    def tearDown(self):
        super().tearDown()
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "--no-color"])
        for rev in ["000000000000", "000000000001"]:
            self.delete_migration("{}_zero.py".format(rev))
        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests.testapp", "--no-color"])

    def test(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "upgrade", "--no-color"])

        revs = db.execute("select * from alembic_version_tests_testapp").fetchall()
        self.assertEqual({r.version_num for r in revs}, {"000000000001", "000000000000"})

    def test_sql(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "upgrade", "-s", "--no-color"])

        out.seek(0)
        lines = out.readlines()

        self.assertEqual(len(lines), 23)
        statements = [
            "-- Running upgrade  -> 000000000001\n",
            "INSERT INTO public.alembic_version_tests_testapp (version_num) VALUES ('000000000001');\n",
            "-- Running upgrade  -> 000000000000\n",
            "INSERT INTO public.alembic_version_tests_testapp (version_num) VALUES ('000000000000');\n",
        ]
        for statement in statements:
            self.assertIn(statement, lines)

    def test_with_range_no_app(self):
        out = six.StringIO()
        cmd = Command(stdout=out)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "upgrade", "-r", "000000000001", "--no-color"])

    def test_with_range(self):
        out = six.StringIO()
        cmd = Command(stdout=out)

        cmd.run_from_argv(["./manage.py sorcery", "upgrade", "tests.testapp", "-r", ":000000000000", "--no-color"])
        revs = db.execute("select * from public.alembic_version_tests_testapp").fetchall()
        self.assertEqual(revs, [("000000000000",)])

    def test_catching_alembic_error(self):
        out = six.StringIO()
        err = six.StringIO()

        cmd = Command(stdout=out, stderr=err)

        with self.assertRaises(SystemExit):
            cmd.run_from_argv(["./manage.py sorcery", "upgrade", "tests.testapp", "-r", "revision", "--no-color"])

        err.seek(0)
        self.assertEqual(err.readlines(), ["CommandError: Can't locate revision identified by 'revision'\n"])
