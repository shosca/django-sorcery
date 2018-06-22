# -*- coding: utf-8 -*-
"""
WSGI config for test_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

from __future__ import absolute_import, print_function, unicode_literals
import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_site.settings")

application = get_wsgi_application()
