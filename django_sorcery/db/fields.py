# -*- coding: utf-8 -*-
"""
Django-esque declarative fields for sqlalchemy
"""

import six

import sqlalchemy as sa

from django import forms as djangoforms
from django.core import validators as django_validators
from django.db.backends.base import operations
from django.forms import fields as djangofields
from django.utils.module_loading import import_string

from ..utils import suppress
from .url import DIALECT_MAP_TO_DJANGO


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
    """
    Base django-esque field
    """

    default_validators = []
    type_class = None
    form_class = None
    widget_class = None

    def __init__(self, *args, **kwargs):
        self.db = kwargs.pop("db", None)

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
        super().__init__(*args, **column_kwargs)
        self.info["validators"] = self.get_validators(validators)
        self.info["required"] = required if required is not None else not self.nullable
        label = kwargs.pop("label", None)
        if label:
            self.info["label"] = label
        self.info["form_class"] = kwargs.pop("form_class", None) or self.get_form_class(kwargs)
        if self.widget_class:
            self.info["widget_class"] = self.widget_class

    def get_form_class(self, kwargs):
        """
        Returns form field class
        """
        return self.form_class

    def get_type_kwargs(self, type_class, kwargs):
        """
        Returns sqlalchemy type kwargs
        """
        type_args = sa.util.get_cls_kwargs(type_class)
        return {k: kwargs.pop(k) for k in type_args if not k.startswith("*") and k in kwargs}

    def get_column_kwargs(self, kwargs):
        """
        Returns sqlalchemy column kwargs
        """
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
        """
        Returns sqlalchemy column type
        """
        return self.type_class

    def get_validators(self, validators):
        """
        Returns django validators for the field
        """
        return self.default_validators[:] + validators

    def get_type(self, type_class, type_kwargs):
        """
        Returns sqlalchemy column type instance for the field
        """
        return type_class(**type_kwargs)


class BooleanField(Field):
    """
    Django like boolean field
    """

    type_class = sa.Boolean
    form_class = djangofields.BooleanField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super().get_type_kwargs(type_class, kwargs)
        type_kwargs["name"] = kwargs.pop("constraint_name", None)
        return type_kwargs

    def get_column_kwargs(self, kwargs):
        column_kwargs = super().get_column_kwargs(kwargs)
        column_kwargs["nullable"] = False
        column_kwargs.setdefault("default", False)
        return column_kwargs


class CharField(Field):
    """
    Django like char field
    """

    type_class = sa.String
    length_is_required = True
    form_class = djangofields.CharField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super().get_type_kwargs(type_class, kwargs)
        type_kwargs["length"] = type_kwargs.get("length") or kwargs.get("max_length")
        if not type_kwargs["length"] and self.length_is_required:
            raise TypeError('Missing length parameter. Must provide either "max_length" or "length" parameter')
        return type_kwargs

    def get_validators(self, validators):
        validators = super().get_validators(validators)
        if self.type.length and not any(isinstance(i, django_validators.MaxLengthValidator) for i in validators):
            validators.append(django_validators.MaxLengthValidator(self.type.length))
        return validators


class DateField(Field):
    """
    Django like date field
    """

    type_class = sa.Date
    form_class = djangofields.DateField


class DateTimeField(Field):
    """
    Django like datetime field
    """

    type_class = sa.DateTime
    form_class = djangofields.DateTimeField


class DurationField(Field):
    """
    Django like duration field
    """

    type_class = sa.Interval
    form_class = djangofields.DurationField


class DecimalField(Field):
    """
    Django like decimal field
    """

    type_class = sa.Numeric
    form_class = djangofields.DecimalField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super().get_type_kwargs(type_class, kwargs)
        type_kwargs.setdefault("precision", kwargs.pop("max_digits", None))
        type_kwargs.setdefault("scale", kwargs.pop("decimal_places", None))
        type_kwargs["asdecimal"] = True
        return type_kwargs

    def get_validators(self, validators):
        return super().get_validators(validators) + [
            django_validators.DecimalValidator(self.type.precision, self.type.scale)
        ]


class EmailField(CharField):
    """
    Django like email field
    """

    default_validators = [django_validators.validate_email]
    form_class = djangofields.EmailField


class EnumField(Field):
    """
    Django like choice field that uses an enum sqlalchemy type
    """

    type_class = sa.Enum

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super().get_type_kwargs(type_class, kwargs)
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
            from ..fields import EnumField as EnumFormField

            return EnumFormField

        return djangofields.TypedChoiceField


class FloatField(Field):
    """
    Django like float field
    """

    type_class = sa.Float
    form_class = djangofields.FloatField

    def get_type_kwargs(self, type_class, kwargs):
        type_kwargs = super().get_type_kwargs(type_class, kwargs)
        type_kwargs["precision"] = type_kwargs.get("precision") or kwargs.pop("max_digits", None)
        return type_kwargs


class ValidateIntegerFieldMixin(object):
    """
    A mixin that provides default min/max validators for integer types
    """

    def get_django_dialect_ranges(self):
        """
        Returns django min/max ranges using current dialect
        """
        ops = operations.BaseDatabaseOperations
        with suppress(ImportError):
            ops = (
                import_string(DIALECT_MAP_TO_DJANGO.get(self.db.url.get_dialect().name) + ".base.DatabaseOperations")
                if self.db
                else operations.BaseDatabaseOperations
            )

        return ops.integer_field_ranges

    def get_dialect_range(self):
        """
        Returns the min/max ranges supported by dialect
        """
        return self.get_django_dialect_ranges()[self.__class__.__name__]

    def get_validators(self, validators):
        """
        Returns django integer min/max validators supported by the database
        """
        validators = super().get_validators(validators)
        min_int, max_int = self.get_dialect_range()
        if not any(isinstance(i, django_validators.MinValueValidator) for i in validators):
            validators.append(django_validators.MinValueValidator(min_int))
        if not any(isinstance(i, django_validators.MaxValueValidator) for i in validators):
            validators.append(django_validators.MaxValueValidator(max_int))
        return validators


class IntegerField(ValidateIntegerFieldMixin, Field):
    """
    Django like integer field
    """

    default_validators = [django_validators.validate_integer]
    type_class = sa.Integer
    form_class = djangofields.IntegerField


class BigIntegerField(ValidateIntegerFieldMixin, Field):
    """
    Django like big integer field
    """

    default_validators = [django_validators.validate_integer]
    type_class = sa.BigInteger
    form_class = djangofields.IntegerField


class SmallIntegerField(ValidateIntegerFieldMixin, Field):
    """
    Django like small integer field
    """

    default_validators = [django_validators.validate_integer]
    type_class = sa.SmallInteger
    form_class = djangofields.IntegerField


class NullBooleanField(BooleanField):
    """
    Django like nullable boolean field
    """

    form_class = djangofields.NullBooleanField

    def get_column_kwargs(self, kwargs):
        kwargs["nullable"] = True
        return kwargs


class SlugField(CharField):
    """
    Django like slug field
    """

    default_validators = [django_validators.validate_slug]
    form_class = djangofields.SlugField


class TextField(CharField):
    """
    Django like text field
    """

    type_class = sa.Text
    length_is_required = False
    form_class = djangofields.CharField
    widget_class = djangoforms.Textarea


class TimeField(Field):
    """
    Django like time field
    """

    type_class = sa.Time
    form_class = djangofields.TimeField


class TimestampField(DateTimeField):
    """
    Django like datetime field that uses timestamp sqlalchemy type
    """

    type_class = sa.TIMESTAMP


class URLField(CharField):
    """
    Django like url field
    """

    default_validators = [django_validators.URLValidator()]
    form_class = djangofields.URLField


class BinaryField(Field):
    """
    Django like binary field
    """

    type_class = sa.Binary
    length_is_required = False
