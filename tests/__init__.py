# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from psycopg2cffi import compat

import django


compat.register()


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"


django.setup()
