# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.test import TestCase

from django_sorcery.management.commands.sorcery import Command

from ...models_multidb import default_db, other_db


class TestCreateAllDropAll(TestCase):
    def setUp(self):
        super(TestCreateAllDropAll, self).setUp()
        default_db.drop_all()
        other_db.drop_all()

    def tearDown(self):
        super(TestCreateAllDropAll, self).setUp()
        default_db.create_all()
        other_db.create_all()

    def test_create_drop_commands(self):

        cmd = Command()

        cmd.run_from_argv(["./manage.py", "sorcery", "createall", "-d", other_db.alias])
        cmd.run_from_argv(["./manage.py", "sorcery", "dropall", "-d", default_db.alias])

        self.assertEqual(default_db.inspector.get_table_names(), [])
        self.assertEqual(other_db.inspector.get_table_names(), ["bar"])

        cmd.run_from_argv(["./manage.py", "sorcery", "dropall", "-d", other_db.alias])
        cmd.run_from_argv(["./manage.py", "sorcery", "createall", "-d", default_db.alias])

        self.assertEqual(default_db.inspector.get_table_names(), ["foo"])
        self.assertEqual(other_db.inspector.get_table_names(), [])

        cmd.run_from_argv(["./manage.py", "sorcery", "createall", "-d", other_db.alias])
        cmd.run_from_argv(["./manage.py", "sorcery", "dropall", "-d", default_db.alias])

        self.assertEqual(default_db.inspector.get_table_names(), [])
        self.assertEqual(other_db.inspector.get_table_names(), ["bar"])
