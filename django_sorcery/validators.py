# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa
from sqlalchemy import inspect

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .db.meta import model_info


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


class ValidateValue(object):
    """
    Validator for checking correctness of a value by using a predicate callable

    Useful when other multiple fields need to be consulted
    to check if particular field is valid.

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.String())
            bar = db.Column(db.String())

            validators = [
                # allow only "bar" value when model.foo == "foo"
                ValidateValue('bar', lambda m: m.foo != 'foo' or b.bar == 'bar'),
            ]
    """

    message = _("Please enter valid value.")
    code = "invalid"

    negated = False

    def __init__(self, field, predicate, message=None, code=None):
        assert callable(predicate), "predicate must be callable"
        self.field = field
        self.predicate = predicate
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, m):
        e = ValidationError({self.field: ValidationError(self.message, code=self.code, params={"field": self.field})})
        try:
            is_valid = self.predicate(m)
        except Exception:
            raise e
        else:
            if not is_valid:
                raise e


class ValidateEmptyWhen(object):
    """
    Validator for checking a field is empty when predicate is True

    Useful to conditionally enforce a field is not provided depending on related field

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.String())
            bar = db.Column(db.String())

            validators = [
                # do not allow to set bar unless foo is present
                ValidateEmptyWhen('bar', lambda m: not m.foo),
            ]
    """

    message = _("Cannot provide a value to this field.")
    code = "empty"

    allow_empty = True

    def __init__(self, field, predicate, message=None, code=None):
        assert callable(predicate), "predicate must be callable"
        self.field = field
        self.predicate = predicate
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, m):
        is_empty = not bool(getattr(m, self.field, None))

        if (self.allow_empty and is_empty) or (not self.allow_empty and not is_empty):
            return

        if self.predicate(m):
            raise ValidationError(
                {self.field: ValidationError(self.message, code=self.code, params={"field": self.field})}
            )


class ValidateNotEmptyWhen(ValidateEmptyWhen):
    """
    Validator for checking a field is provided when predicate is True

    Useful to conditionally enforce a field is provided depending on related field

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.String())
            bar = db.Column(db.String())

            validators = [
                # enforce bar is provided when foo is provided
                ValidateNotEmptyWhen('bar', lambda m: m.foo),
            ]
    """

    message = _("This field is required.")
    code = "not_empty"

    allow_empty = False


class ValidateOnlyOneOf(object):
    """
    Validate that only one of given fields is provided

    For example::

        class MyModel(db.Model):
            foo = db.Column(db.String())
            bar = db.Column(db.String())

            validators = [
                # enforce only either foo or bar are provided
                ValidateOnlyOneOf(['foo', 'bar']),
            ]
    """

    message = _("Only one of %(fields)s is allowed.")
    code = "exclusive"

    def __init__(self, fields, required=True, message=None, code=None):
        self.fields = fields
        self.required = required
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, m):
        e = ValidationError(self.message, code=self.code, params={"fields": ", ".join(sorted(self.fields))})

        present = len(list(filter(None, (getattr(m, i, None) for i in self.fields))))

        if (self.required and not present) or present > 1:
            raise e


class ValidateCantRemove(object):
    """
   Validate that for data cannot be removed for given field

   For example::

       class MyModel(db.Model):
           foo = db.Column(db.String())

           validators = [
               ValidateCantRemove('foo'),
           ]
   """

    message = _("Cannot remove existing data.")
    code = "remove"

    def __init__(self, field, message=None, code=None):
        self.field = field
        self.message = message or self.message
        self.code = code or self.code

    def __call__(self, m):
        inspected = inspect(m).attrs
        history = getattr(inspected, self.field).history

        if not history.has_changes():
            return

        previous, current = next(iter(history.deleted or ()), None), getattr(m, self.field)
        if previous is not None and current is None:
            raise ValidationError(
                {self.field: ValidationError(self.message, code=self.code, params={"field": self.field})}
            )
