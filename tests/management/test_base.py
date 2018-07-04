# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand
from django.utils.six import StringIO

from django_sorcery.management import NamespacedCommand

from ..base import TestCase


class SubCommand(BaseCommand):
    help = "subcommand"

    def add_arguments(self, parser):
        parser.add_argument("-d", action="append", dest="dummy", type=str, help="subcommand help message")

    def handle(self, *args, **kwargs):
        return "subcommand triggered"


class DummyCommand(NamespacedCommand):

    sub1 = SubCommand

    class Meta:
        namespace = "dummy"


class TestNamespacedCommand(TestCase):
    def setUp(self):
        super(TestNamespacedCommand, self).setUp()
        self.stdout = StringIO()
        self.stderr = StringIO()

    def test_help_message(self):

        cmd = DummyCommand(stdout=self.stdout, stderr=self.stderr, no_color=True)

        cmd.run_from_argv(["./manage.py", "dummy", "-h"])

        self.stdout.seek(0)
        self.maxDiff = None
        self.assertEqual(
            "\n".join([l.strip() for l in self.stdout.readlines()]),
            "\n".join(
                [
                    "usage: manage.py dummy [-h] sub1",
                    "",
                    "positional arguments:",
                    "sub1        subcommand",
                    "",
                    "optional arguments:",
                    "-h, --help  show this help message and exit",
                ]
            ),
        )

    def test_trigger_subcommand(self):
        cmd = DummyCommand(stdout=self.stdout, stderr=self.stderr, no_color=True)

        cmd.run_from_argv(["./manage.py", "dummy", "sub1"])

        self.stdout.seek(0)
        self.assertEqual("".join([l.strip() for l in self.stdout.readlines()]), "subcommand triggered")
