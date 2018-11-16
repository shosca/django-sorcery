# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

import sqlalchemy as sa

from django.core import validators as django_validators
from django.utils import inspect

from ..utils import suppress


__all__ = [
    "BigIntegerField",
    "BinaryField",
    "BooleanField",
    "CharField",
    "DateField",
    "DateTimeField",
    "DecimalField",
    "DurationField",
    "EmailField",
    "EnumField",
    "Field",
    "FloatField",
    "IntegerField",
    "NullBooleanField",
    "SlugField",
    "SmallIntegerField",
    "TextField",
    "TimeField",
    "URLField",
]


class Field(sa.Column):
    default_validators = []
    type_class = None

    def __init__(self, *args, **kwargs):
        args = list(args)
        if args and isinstance(args[0], six.string_types):
            kwargs["name"] = args.pop(0)

        column_type = kwargs.pop("type_", None)
        if args and hasattr(args[0], "_sqla_type"):
            column_type = args.pop(0)

        validators = kwargs.pop("validators", [])
        required = kwargs.pop("required", None)
        column_kwargs = self.get_column_kwargs(kwargs)

        if column_type is None:
            type_class = self.get_type_class(kwargs)
            type_kwargs = self.get_type_kwargs(type_class, kwargs)
            column_type = self.get_type(type_class, type_kwargs)

        column_kwargs["type_"] = column_type
        super(Field, self).__init__(*args, **column_kwargs)
        self.info["validators"] = self.get_validators(validators)
        self.info["required"] = required if required is not None else not self.nullable

    def get_type_kwargs(self, type_class, kwargs):
        args = []
        with suppress(ValueError, TypeError):
            # this is required for python2 for slot wrappers
            args = inspect.get_func_full_args(type_class.__init__)

        type_args = [i for i in args if len(i) == 2]
        return {k: kwargs.pop(k) for k, v in type_args if not k.startswith("*") and k in kwargs}

    def get_column_kwargs(self, kwargs):
        column_args = [
            "autoincrement",
            "comment",
            "default",
            "doc",
            "index",
            "info",
            "key",
            "name",
            "onupdate",
            "server_default",
            "server_onupdate",
            "type_",
            "unique",
            "_proxies",
        ]
        column_kwargs = {}
        for k in column_args:
            if k in kwargs:
                column_kwargs[k] = kwargs.pop(k)

        column_kwargs["primary_key"] = kwargs.pop("primary_key", False)
        column_kwargs["nullable"] = kwargs.pop("nullable", not column_kwargs["primary_key"])
        return column_kwargs

    def get_type_class(self, kwargs):
        return self.type_class

    def get_validators(self, validators):
        return self.default_validators + validators

    def get_type(self, type_class, type_kwargs):
        return type_class(**type_kwargs)


class BooleanField(Field):
    type_class = sa.Boolean


class CharField(Field):
    type_class = sa.String

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(CharField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs["length"] = type_kwargs.get("length") or kwargs.get("max_length")
        return type_kwargs


class DateField(Field):
    type_class = sa.Date


class DateTimeField(Field):
    type_class = sa.DateTime


class DurationField(Field):
    type_class = sa.Interval


class DecimalField(Field):
    type_class = sa.Numeric

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(DecimalField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs.setdefault("precision", kwargs.pop("max_digits", None))
        type_kwargs.setdefault("scale", kwargs.pop("decimal_places", None))
        type_kwargs["asdecimal"] = True
        return type_kwargs

    def get_validators(self, validators):
        return super(DecimalField, self).get_validators(validators) + [
            django_validators.DecimalValidator(self.type.precision, self.type.scale)
        ]


class EmailField(CharField):
    default_validators = [django_validators.validate_email]


class EnumField(Field):
    type_class = sa.Enum

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(EnumField, self).get_type_kwargs(type_class, kwargs)
        choices = kwargs.pop("choices")
        type_kwargs["choices"] = choices if len(choices) > 1 and isinstance(choices, (list, tuple)) else [choices]
        type_kwargs["name"] = kwargs.pop("constraint_name", None)

        enum_args = [
            "native_enum",
            "create_constraint",
            "values_callable",
            "convert_unicode",
            "validate_strings",
            "schema",
            "quote",
            "_create_events",
        ]
        for k in enum_args:
            if k in kwargs:
                type_kwargs[k] = kwargs.pop(k)

        return type_kwargs

    def get_type(self, type_class, type_kwargs):
        choices = type_kwargs.pop("choices")
        return type_class(*choices, **type_kwargs)


class FloatField(Field):
    type_class = sa.Float

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(FloatField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs["precision"] = type_kwargs.get("precision") or kwargs.pop("max_digits", None)
        return type_kwargs


class IntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.Integer


class BigIntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.BigInteger


class SmallIntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.SmallInteger


class NullBooleanField(BooleanField):
    def get_column_kwargs(self, kwargs):
        kwargs["nullable"] = False
        return kwargs


class SlugField(CharField):
    default_validators = [django_validators.validate_slug]


class TextField(CharField):
    type_class = sa.Text


class TimeField(Field):
    type_class = sa.Time


class TimestampField(DateTimeField):
    type_class = sa.TIMESTAMP


class URLField(CharField):
    default_validators = [django_validators.URLValidator()]


class BinaryField(Field):
    type_class = sa.Binary
