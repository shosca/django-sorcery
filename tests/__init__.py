import os

import django
from psycopg2cffi import compat


compat.register()


os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"


django.setup()
