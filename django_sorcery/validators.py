# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_sorcery.db.meta import model_info


class ValidateTogetherModelFields(object):
    """
    Validator for checking that multiple model fields are always saved together

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.Integer())
            bar = db.Column(db.Integer())

            validators = [
                ValidateTogetherModelFields(["foo", "bar"]),
            ]
    """

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


class ValidateUnique(object):
    """
    Validator for checking uniqueness of arbitrary list of attributes on a model

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.Integer())
            bar = db.Column(db.Integer())
            name = db.Column(db.Integer())

            validators = [
                ValidateUnique(db, "name"),      # checks for name uniqueness
                ValidateUnique(db, "foo", "bar"),  # checks for foo and bar combination uniqueness
            ]
    """

    message = _("%(fields)s must make a unique set.")
    code = "required"

    def __init__(self, session, *args, **kwargs):
        self.session = session
        self.message = kwargs.get("message", self.message)
        self.code = kwargs.get("code", self.code)
        self.attrs = args

    def __call__(self, m):
        clauses = [getattr(m.__class__, attr) == getattr(m, attr) for attr in self.attrs]

        info = model_info(m.__class__)
        state = sa.inspect(m)
        if state.persistent:
            # need to exlude the current model since it's already in db
            pks = info.mapper.primary_key_from_instance(m)
            for name, pk in zip(info.primary_keys, pks):
                clauses.append(getattr(m.__class__, name) != pk)

        query = self.session.query(m.__class__).filter(*clauses)
        exists = self.session.query(sa.literal(True)).filter(query.exists()).scalar()

        if exists:
            raise ValidationError(self.message, code=self.code, params={"fields": ", ".join(sorted(self.attrs))})
