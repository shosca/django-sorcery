# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from .. import NamespacedCommand
from .sorcery_createall import CreateAll
from .sorcery_dropall import DropAll


class Command(NamespacedCommand):
    help = "django-sorcery management commands"

    createall = CreateAll
    dropall = DropAll

    class Meta:
        namespace = "sorcery"
