# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from ... import testapp


MIGRATION_DIR = os.path.abspath(os.path.join(os.path.dirname(testapp.__file__), "migrations"))


class MigrationMixin(object):
    def write_migration(self, content, filename):
        with open(os.path.join(MIGRATION_DIR, filename), "w+") as migration:
            migration.write(content)

    def delete_migration(self, filename):
        try:
            os.remove(os.path.join(MIGRATION_DIR, filename))
        except OSError:
            pass
