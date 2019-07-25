# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import re

from django.contrib import admin as djangoadmin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django_sorcery.db import meta

from ..utils import setdefaultattr
from .options import admin_factory


csrf_protect_m = method_decorator(csrf_protect)


def register(model_or_iterable, admin_class=None, site=None, session=None, **options):
    site = site or djangoadmin.site
    if not isinstance(model_or_iterable, (list, set, tuple)):
        model_or_iterable = [model_or_iterable]

    if admin_class is None:
        admin_class = admin_factory(model_or_iterable[0], session, options)

    for model in model_or_iterable:
        setdefaultattr(model, "_meta", meta.model_info(model))
        if model in site._registry:
            registered_admin = str(site._registry[model])
            msg = "The model %s is already registered " % model.__name__
            if registered_admin.endswith(".ModelAdmin"):
                msg += "in app %r." % re.sub(r"\.ModelAdmin$", "", registered_admin)
            else:
                msg += "with %r." % registered_admin
            raise djangoadmin.sites.AlreadyRegistered(msg)

        site._registry[model] = admin_class(model, site)
