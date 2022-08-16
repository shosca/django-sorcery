import six
from django.conf import settings
from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.sorcery_current import Command
from django_sorcery.management.commands.sorcery_downgrade import Downgrade
from django_sorcery.management.commands.sorcery_upgrade import Upgrade

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

db = databases.get("test")


class TestCurrent(MigrationMixin, TestCase):
    def setUp(self):
        super().setUp()

        for rev in ["000000000000", "000000000001"]:
            self.delete_migration(f"{rev}_.py")

        self.write_migration(M1, "000000000000_.py")
        self.write_migration(M2, "000000000001_.py")

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests_testapp", "--no-color"])

        Upgrade().run_from_argv(["./manage.py sorcery", "upgrade", "tests_testapp", "--no-color"])

    def tearDown(self):
        super().tearDown()

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests_testapp", "--no-color"])

        for rev in ["000000000000", "000000000001"]:
            self.delete_migration(f"{rev}_.py")

        Downgrade().run_from_argv(["./manage.py sorcery", "downgrade", "tests_testapp", "--no-color"])

    def test(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "current", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Revision for tests_testapp on database test\n",
                "000000000001 (head)\n",
                "Revision for tests_otherapp on database test\n",
            ],
        )

    def test_verbose(self):
        out = six.StringIO()
        cmd = Command(stdout=out)
        cmd.run_from_argv(["./manage.py sorcery", "current", "-v", "2", "--no-color"])

        out.seek(0)
        self.assertEqual(
            out.readlines(),
            [
                "Revision for tests_testapp on database test\n",
                f"Current revision(s) for postgresql://postgres:***@{settings.DB_URL.host}/test\n",
                "Rev: 000000000001 (head)\n",
                "Parent: 000000000000\n",
                f"Path: {MIGRATION_DIR}/000000000001_.py\n",
                "\n",
                "    one\n",
                "    \n",
                "    Revision ID: 000000000001\n",
                "    Revises: 000000000000\n",
                "    Create Date: 2018-07-24 02:02:55.504526\n",
                "Revision for tests_otherapp on database test\n",
                f"Current revision(s) for postgresql://postgres:***@{settings.DB_URL.host}/test\n",
            ],
        )
