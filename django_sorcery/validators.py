# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ValidateTogetherModelFields(object):
    message = _("All %(fields)s are required.")
    code = "required"

    def __init__(self, fields, message=None, code=None):
        self.fields = fields
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, m):
        if not any(getattr(m, i, None) for i in self.fields):
            return
        if not all(getattr(m, i, None) for i in self.fields):
            raise ValidationError(self.message, code=self.code, params={"fields": ", ".join(sorted(self.fields))})
