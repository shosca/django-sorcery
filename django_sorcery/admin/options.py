# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import wraps

from django.contrib.admin import options
from django.contrib.admin.options import ModelAdmin as DjangoModelAdmin

from ..forms import ModelForm, modelform_factory


def swap(module, attr, replacement):
    def wrapper(f):
        @wraps(f)
        def inner(*args, **kwargs):
            original = getattr(module, attr)
            setattr(module, attr, replacement)
            try:
                return f(*args, **kwargs)
            finally:
                setattr(module, attr, original)

        return inner

    return wrapper


class ModelAdmin(DjangoModelAdmin):
    form = ModelForm

    @swap(options, "modelform_factory", modelform_factory)
    def get_form(self, *args, **kwargs):
        return super(ModelAdmin, self).get_form(*args, **kwargs)
