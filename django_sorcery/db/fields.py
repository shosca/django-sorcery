# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

import sqlalchemy as sa

from django import forms as djangoforms
from django.core import validators as django_validators
from django.forms import fields as djangofields


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
    "TimestampField",
    "URLField",
]


class Field(sa.Column):
    default_validators = []
    type_class = None
    form_class = None
    widget_class = None

    def __init__(self, *args, **kwargs):
        name = None
        args = list(args)
        if args and isinstance(args[0], six.string_types):
            name = args.pop(0)

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
        column_kwargs.setdefault("name", name)
        super(Field, self).__init__(*args, **column_kwargs)
        self.info["validators"] = self.get_validators(validators)
        self.info["required"] = required if required is not None else not self.nullable
        label = kwargs.pop("label", None)
        if label:
            self.info["label"] = label
        self.info["form_class"] = kwargs.pop("form_class", None) or self.get_form_class(kwargs)
        if self.widget_class:
            self.info["widget_class"] = self.widget_class

    def get_form_class(self, kwargs):
        return self.form_class

    def get_type_kwargs(self, type_class, kwargs):
        type_args = sa.util.get_cls_kwargs(type_class)
        return {k: kwargs.pop(k) for k in type_args if not k.startswith("*") and k in kwargs}

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
    form_class = djangofields.BooleanField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(BooleanField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs["name"] = kwargs.pop("constraint_name", None)
        return type_kwargs

    def get_column_kwargs(self, kwargs):
        column_kwargs = super(BooleanField, self).get_column_kwargs(kwargs)
        column_kwargs["nullable"] = False
        column_kwargs.setdefault("default", False)
        return column_kwargs


class CharField(Field):
    type_class = sa.String
    form_class = djangofields.CharField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(CharField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs["length"] = type_kwargs.get("length") or kwargs.get("max_length")
        return type_kwargs


class DateField(Field):
    type_class = sa.Date
    form_class = djangofields.DateField


class DateTimeField(Field):
    type_class = sa.DateTime
    form_class = djangofields.DateTimeField


class DurationField(Field):
    type_class = sa.Interval
    form_class = djangofields.DurationField


class DecimalField(Field):
    type_class = sa.Numeric
    form_class = djangofields.DecimalField

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
    form_class = djangofields.EmailField


class EnumField(Field):
    type_class = sa.Enum

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(EnumField, self).get_type_kwargs(type_class, kwargs)
        choices = kwargs.pop("choices", None) or kwargs.pop("enum_class", None)
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

    def get_form_class(self, kwargs):
        if self.type.enum_class:
            from ..fields import EnumField

            return EnumField

        return djangofields.TypedChoiceField


class FloatField(Field):
    type_class = sa.Float
    form_class = djangofields.FloatField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super(FloatField, self).get_type_kwargs(type_class, kwargs)
        type_kwargs["precision"] = type_kwargs.get("precision") or kwargs.pop("max_digits", None)
        return type_kwargs


class IntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.Integer
    form_class = djangofields.IntegerField


class BigIntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.BigInteger
    form_class = djangofields.IntegerField


class SmallIntegerField(Field):
    default_validators = [django_validators.validate_integer]
    type_class = sa.SmallInteger
    form_class = djangofields.IntegerField


class NullBooleanField(BooleanField):
    form_class = djangofields.NullBooleanField

    def __init__(self, *args, **kwargs):
        super(NullBooleanField, self).__init__(*args, **kwargs)

    def get_column_kwargs(self, kwargs):
        kwargs["nullable"] = True
        return kwargs


class SlugField(CharField):
    default_validators = [django_validators.validate_slug]
    form_class = djangofields.SlugField


class TextField(CharField):
    type_class = sa.Text
    form_class = djangofields.CharField
    widget_class = djangoforms.Textarea


class TimeField(Field):
    type_class = sa.Time
    form_class = djangofields.TimeField


class TimestampField(DateTimeField):
    type_class = sa.TIMESTAMP


class URLField(CharField):
    default_validators = [django_validators.URLValidator()]
    form_class = djangofields.URLField


class BinaryField(Field):
    type_class = sa.Binary
