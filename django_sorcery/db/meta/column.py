# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import warnings
from decimal import Decimal

import sqlalchemy as sa

from django import forms as djangoforms
from django.conf import settings
from django.forms import fields as djangofields
from django.utils.text import capfirst

from ... import fields as sorceryfields


class column_info(object):
    """
    A helper class that makes sqlalchemy property and column inspection easier
    """

    default_form_class = None

    __slots__ = ("property", "column", "parent")

    def __new__(cls, *args, **kwargs):
        args = list(args)
        column = kwargs.pop("column", None)
        property = kwargs.pop("property", None)

        if args:
            column = args.pop(0)
        if args:
            property = args.pop(0)

        if not isinstance(column, sa.Column):
            warnings.warn(
                "Instantiating column_info with property is deprecated, "
                "a column instance is now required and its the first argument"
            )
            column = property

        column_info_mapping = getattr(settings, "DJANGO_SORCERY", {}).get("column_info_mapping", COLUMN_INFO_MAPPING)

        override_cls = None
        for base in column.type.__class__.mro():
            if base in column_info_mapping:
                override_cls = column_info_mapping.get(base, cls)
                break

        cls = override_cls or cls
        instance = super(column_info, cls).__new__(cls)
        return instance

    def __init__(self, column, property=None, parent=None):
        if not isinstance(column, sa.Column):
            warnings.warn(
                "Instantiating column_info with property is deprecated, "
                "a column instance is now required and its the first argument"
            )
            column, property = property, column

        self.property = property
        self.column = column
        self.parent = parent

    def __repr__(self):
        return "<{!s}({!s}.{!s}){!s}>".format(
            self.__class__.__name__,
            self.parent_model.__name__ if self.parent_model else "<None>",
            self.name,
            " pk" if self.column.primary_key else "",
        )

    @property
    def validators(self):
        return self.column.info.get("validators") or []

    @property
    def null(self):
        return not self.column.primary_key and self.column.nullable

    @property
    def required(self):
        return self.column.info.get("required", not self.column.nullable)

    @property
    def name(self):
        return self.property.key if self.property is not None else self.column.key

    @property
    def parent_model(self):
        return self.property.parent.class_ if self.property else None

    @property
    def help_text(self):
        return self.column.doc

    @property
    def default(self):
        return getattr(self.column.default, "arg", None)

    @property
    def choices(self):
        return getattr(self.column.type, "enum_class", None) or getattr(self.column.type, "enums", None)

    @property
    def widget(self):
        return self.column.info.get("widget_class")

    @property
    def label(self):
        label = self.column.info.get("label")
        if label:
            return label

        return capfirst(" ".join(self.name.split("_"))) if self.name else None

    @property
    def form_class(self):
        return self.column.info.get("form_class") or self.default_form_class

    def formfield(self, form_class=None, **kwargs):
        form_class = form_class or self.form_class

        if form_class is not None:
            field_kwargs = self.field_kwargs
            field_kwargs.update(kwargs)
            return form_class(**field_kwargs)

    @property
    def field_kwargs(self):
        kwargs = {"required": self.required, "validators": self.validators, "help_text": self.help_text}
        if self.default:
            if not callable(self.default):
                kwargs["initial"] = self.default

        if self.label:
            kwargs["label"] = self.label

        if self.widget:
            kwargs["widget"] = self.widget

        return kwargs


class string_column_info(column_info):
    default_form_class = djangofields.CharField

    @property
    def field_kwargs(self):
        kwargs = super(string_column_info, self).field_kwargs
        kwargs["max_length"] = self.column.type.length
        return kwargs


class text_column_info(string_column_info):
    @property
    def widget(self):
        return super(text_column_info, self).widget or djangoforms.Textarea


class enum_column_info(column_info):
    @property
    def form_class(self):
        form_class = super(enum_column_info, self).form_class
        if form_class:
            return form_class

        return (
            djangofields.TypedChoiceField if isinstance(self.choices, (list, set, tuple)) else sorceryfields.EnumField
        )

    @property
    def field_kwargs(self):
        kwargs = super(enum_column_info, self).field_kwargs

        if isinstance(self.choices, (list, set, tuple)):
            kwargs["choices"] = [(x, x) for x in self.choices]
        else:
            kwargs["choices"] = self.choices

        # Many of the subclass-specific formfield arguments (min_value,
        # max_value) don't apply for choice fields, so be sure to only pass
        # the values that TypedChoiceField will understand.
        for k in list(kwargs):
            if k not in (
                "choices",
                "coerce",
                "disabled",
                "empty_value",
                "enum_class",
                "error_messages",
                "help_text",
                "initial",
                "label",
                "required",
                "show_hidden_initial",
                "validators",
                "widget",
            ):
                del kwargs[k]  # pragma: nocover

        return kwargs


class numeric_column_info(column_info):
    default_form_class = djangofields.DecimalField

    @property
    def field_kwargs(self):
        kwargs = super(numeric_column_info, self).field_kwargs
        max_digits = self.column.type.precision
        decimal_places = self.column.type.scale
        if self.column.type.python_type == Decimal:
            if max_digits is not None:
                kwargs["max_digits"] = max_digits
            if decimal_places is not None:
                kwargs["decimal_places"] = decimal_places
        return kwargs


class boolean_column_info(column_info):
    @property
    def form_class(self):
        form_class = super(boolean_column_info, self).form_class
        if form_class:
            return form_class

        return djangofields.NullBooleanField if self.null else djangofields.BooleanField


class date_column_info(column_info):
    default_form_class = djangofields.DateField


class datetime_column_info(column_info):
    default_form_class = djangofields.DateTimeField


class float_column_info(column_info):
    default_form_class = djangofields.FloatField


class integer_column_info(column_info):
    default_form_class = djangofields.IntegerField


class interval_column_info(column_info):
    default_form_class = djangofields.DurationField


class time_column_info(column_info):
    default_form_class = djangofields.TimeField


COLUMN_INFO_MAPPING = {
    sa.sql.sqltypes.Enum: enum_column_info,
    sa.sql.sqltypes.String: string_column_info,
    sa.sql.sqltypes.Text: text_column_info,
    sa.sql.sqltypes.Numeric: numeric_column_info,
    sa.sql.sqltypes.Float: float_column_info,
    sa.sql.sqltypes.Integer: integer_column_info,
    sa.sql.sqltypes.Boolean: boolean_column_info,
    sa.sql.sqltypes.Date: date_column_info,
    sa.sql.sqltypes.DateTime: datetime_column_info,
    sa.sql.sqltypes.Interval: interval_column_info,
    sa.sql.sqltypes.Time: time_column_info,
}
