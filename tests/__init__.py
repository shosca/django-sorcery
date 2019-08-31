# -*- coding: utf-8 -*-
import os

from psycopg2cffi import compat

import django


compat.register()


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"


django.setup()
