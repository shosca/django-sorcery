# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.test import TestCase

from django_sorcery.management.commands.sorcery_heads import Command

from .base import MIGRATION_DIR, MigrationMixin


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


class TestHeads(MigrationMixin, TestCase):
    def setUp(self):
        super(TestHeads, self).setUp()
        self.write_migration(M1, "{}_.py".format("000000000000"))
        self.write_migration(M2, "{}_.py".format("000000000001"))

    def tearDown(self):
        super(TestHeads, self).tearDown()
        for rev in ["000000000000", "000000000001"]:
            self.delete_migration("{}_.py".format(rev))

    def test(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "heads", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Heads for tests.testapp on database test\n",
                "000000000001 (head) <tests.testapp> \n",
                "Heads for tests.otherapp on database test\n",
            ],
        )

    def test_verbose(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "heads", "-v", "2", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Heads for tests.testapp on database test\n",
                "[tests.testapp]\n",
                "Rev: 000000000001 (head)\n",
                "Parent: 000000000000\n",
                "Path: {}/000000000001_.py\n".format(MIGRATION_DIR),
                "\n",
                "    one\n",
                "    \n",
                "    Revision ID: 000000000001\n",
                "    Revises: 000000000000\n",
                "    Create Date: 2018-07-24 02:02:55.504526\n",
                "Heads for tests.otherapp on database test\n",
            ],
        )
