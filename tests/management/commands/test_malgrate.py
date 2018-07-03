# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import CommandError
from django.test import TestCase

from django_sorcery.db import databases
from django_sorcery.management.commands.malgrate import Command


class TestMalgrate(TestCase):
    def test_add_arguments(self):
        c = Command()
        parser = c.create_parser("name", "command")

        parsed = parser.parse_args(["--database", "foo", "--database", "bar", "--createall"])
        self.assertListEqual(parsed.databases, ["foo", "bar"])
        self.assertTrue(parsed.createall)

    def test_handle_createall(self):
        db = databases.get("minimal")

        class Foo(db.Model):
            __tablename__ = "foo"
            id = db.Column(db.BigInteger(), primary_key=True)

        # sanity check
        self.assertListEqual(db.inspect(db.engine).get_table_names(), [])

        c = Command()
        c.handle(createall=True, databases=["minimal"])

        self.assertListEqual(db.inspect(db.engine).get_table_names(), ["foo"])

    def test_handle_migrate(self):
        c = Command()

        with self.assertRaises(CommandError):
            c.handle(createall=False, databases=None)
