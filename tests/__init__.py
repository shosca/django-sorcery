# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

import django


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"


django.setup()
