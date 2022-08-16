import six
from django.test import TestCase

from django_sorcery.management.commands.sorcery_heads import Command

from .base import MIGRATION_DIR
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


class TestHeads(MigrationMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.write_migration(M1, '000000000000_.py')
        self.write_migration(M2, '000000000001_.py')

    def tearDown(self):
        super().tearDown()
        for rev in ["000000000000", "000000000001"]:
            self.delete_migration(f"{rev}_.py")

    def test(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "heads", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Heads for tests_testapp on database test\n",
                "000000000001 (head) <tests_testapp> \n",
                "Heads for tests_otherapp on database test\n",
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
                "Heads for tests_testapp on database test\n",
                "[tests_testapp]\n",
                "Rev: 000000000001 (head)\n",
                "Parent: 000000000000\n",
                f"Path: {MIGRATION_DIR}/000000000001_.py\n",
                "\n",
                "    one\n",
                "    \n",
                "    Revision ID: 000000000001\n",
                "    Revises: 000000000000\n",
                "    Create Date: 2018-07-24 02:02:55.504526\n",
                "Heads for tests_otherapp on database test\n",
            ],
        )
