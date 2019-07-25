# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery import admin as sorcery_admin

from .models import Choice, Question


sorcery_admin.register(Question)
sorcery_admin.register(Choice)
