# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import inspect
import os

from django.core.management.base import BaseCommand, CommandParser


class NamespacedCommand(BaseCommand):
    @property
    def commands(self):
        if not hasattr(self, "_commands"):
            self._commands = {}
            for cls in reversed(self.__class__.mro()):
                self._commands.update(
                    {
                        name: cmd_cls
                        for name, cmd_cls in vars(self.__class__).items()
                        if inspect.isclass(cmd_cls) and hasattr(cmd_cls, "mro") and BaseCommand in cmd_cls.mro()
                    }
                )

        return self._commands

    def run_command_from_argv(self, command, argv):
        command.style = self.style

        cmd_args = argv[:]
        cmd_args[0] = " ".join([cmd_args[0], cmd_args.pop(1)])
        command.run_from_argv(cmd_args)

    def run_from_argv(self, argv):
        self._called_from_command_line = True

        if len(argv) > 2 and not argv[2].startswith("-") and argv[2] in self.commands:
            command = self.commands.get(argv[2])(stdout=self.stdout, stderr=self.stderr)
            self.run_command_from_argv(command, argv)
        else:
            self.print_help(argv[0], argv[1])

    def create_parser(self, prog_name, subcommand):
        parser = CommandParser(
            self, prog="%s %s" % (os.path.basename(prog_name), subcommand), description=self.help or None
        )
        for name, command_cls in self.commands.items():
            parser.add_argument(name, help=command_cls.help)

        return parser

    def print_help(self, prog_name, subcommand):
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help(self.stdout)
