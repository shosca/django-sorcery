# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.contrib import admin

from django_sorcery.admin.options import ModelAdmin

from .models import Choice, Question


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    pass


@admin.register(Choice)
class ChoiceAdmin(ModelAdmin):
    pass
