# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from .. import NamespacedCommand
from .sorcery_createall import CreateAll
from .sorcery_current import Current
from .sorcery_downgrade import Downgrade
from .sorcery_dropall import DropAll
from .sorcery_heads import ShowHeads
from .sorcery_history import History
from .sorcery_revision import Revision
from .sorcery_stamp import Stamp
from .sorcery_upgrade import Upgrade


class Command(NamespacedCommand):
    help = "django-sorcery management commands"

    createall = CreateAll
    dropall = DropAll
    history = History
    revision = Revision
    heads = ShowHeads
    upgrade = Upgrade
    downgrade = Downgrade
    current = Current
    stamp = Stamp

    class Meta:
        namespace = "sorcery"
