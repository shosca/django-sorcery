# -*- coding: utf-8 -*-
"""
Field mapping from SQLAlchemy type's to form fields
"""
from __future__ import absolute_import, print_function, unicode_literals
import datetime
import decimal
from collections import OrderedDict
from itertools import chain

import six

import sqlalchemy as sa

from django import forms as djangoforms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import fields as djangofields
from django.utils.module_loading import import_string

from .db import meta
from .fields import EnumField, ModelChoiceField, ModelMultipleChoiceField, apply_limit_choices_to_form_field
from .utils import suppress


ALL_FIELDS = "__all__"

FIELD_LOOKUP = {
    # only python types here
    bool: djangofields.BooleanField,
    datetime.date: djangofields.DateField,
    datetime.datetime: djangofields.DateTimeField,
    datetime.time: djangofields.TimeField,
    datetime.timedelta: djangofields.DurationField,
    decimal.Decimal: djangofields.DecimalField,
    float: djangofields.FloatField,
    int: djangofields.IntegerField,
    str: djangofields.CharField,
}
FIELD_LOOKUP.update({t: djangofields.CharField for t in six.string_types})
FIELD_LOOKUP.update({t: djangofields.IntegerField for t in six.integer_types})


def get_field_mapper():
    return (
        import_string(settings.SQLALCHEMY_FORM_MAPPER)
        if hasattr(settings, "SQLALCHEMY_FORM_MAPPER")
        else ModelFieldMapper
    )


class ModelFieldMapper(object):
    """
    Main field mapper between sqlalchemy models and django form fields, provides hooks to control field generation and
    can be extended and overridden by using the ``SQLALCHEMY_FORM_MAPPER`` setting.
    """

    def __init__(self, **kwargs):
        attrs = [
            "model",
            "session",
            "fields",
            "exclude",
            "widgets",
            "localized_fields",
            "labels",
            "help_texts",
            "error_messages",
            "field_classes",
            "formfield_callback",
        ]
        for attr in attrs:
            setattr(self, attr, kwargs.get(attr))

        self.apply_limit_choices_to = kwargs.get("apply_limit_choices_to", True)

        if self.model is None:
            raise ImproperlyConfigured("Creating a field mapper without model attribute prohibited")

        if self.session is None:
            with suppress(AttributeError):
                self.session = self.model.query.session

    def get_default_kwargs(self, name, **kwargs):
        """
        Generate default kwargs from form options.
        """
        if self.widgets and name in self.widgets:
            kwargs["widget"] = self.widgets[name]
        if self.localized_fields == ALL_FIELDS:
            kwargs["localize"] = True
        if self.localized_fields and name in self.localized_fields:
            kwargs["localize"] = True
        if self.labels and name in self.labels:
            kwargs["label"] = self.labels[name]
        if self.help_texts and name in self.help_texts:
            kwargs["help_text"] = self.help_texts[name]
        if self.error_messages and name in self.error_messages:
            kwargs["error_messages"] = self.error_messages[name]
        if self.field_classes and name in self.field_classes:
            kwargs["form_class"] = self.field_classes[name]
        return kwargs

    def get_fields(self):
        """
        Generates django form fields for a sqlalchemy model form.
        """

        field_list = []

        info = meta.model_info(self.model)

        for name, attr in chain(info.properties.items(), info.relationships.items()):

            if name.startswith("_"):
                continue

            if self.fields and name not in self.fields:
                continue

            if self.exclude and name in self.exclude:
                continue

            kwargs = self.get_default_kwargs(name)
            formfield = self.build_field(attr, **kwargs)

            if formfield:
                if self.apply_limit_choices_to:
                    apply_limit_choices_to_form_field(formfield)
                field_list.append((name, formfield))

        return OrderedDict(field_list)

    def build_field(self, info, **kwargs):
        if self.formfield_callback is not None:
            return self.formfield_callback(info, **kwargs)

        if isinstance(info, meta.column_info):
            return self.build_standard_field(info, **kwargs)

        if isinstance(info, meta.relation_info):
            return self.build_relationship_field(info, **kwargs)

    def build_relationship_field(self, relation, **kwargs):
        """
        Build field for a sqlalchemy relationship field.
        """
        if relation.direction == sa.orm.relationships.MANYTOMANY:
            return self.build_modelmultiplechoice_field(relation, **kwargs)

        if relation.direction == sa.orm.relationships.ONETOMANY and relation.uselist:
            return self.build_modelmultiplechoice_field(relation, **kwargs)

        return self.build_modelchoice_field(relation, **kwargs)

    def build_modelchoice_field(self, relation, **kwargs):
        """
        Build field for a sqlalchemy many-to-one relationship field.
        """
        if self.session is None:
            raise ImproperlyConfigured("Creating a field mapper without session attribute prohibited")

        kwargs["required"] = not all([col.nullable for col in relation.foreign_keys])
        return ModelChoiceField(relation.related_model, self.session, **kwargs)

    def build_modelmultiplechoice_field(self, relation, **kwargs):
        """
        Build field for a sqlalchemy one-to-many or many-to-many relationship field.
        """
        if self.session is None:
            raise ImproperlyConfigured("Creating a field mapper without session attribute prohibited")

        kwargs["required"] = False
        return ModelMultipleChoiceField(relation.related_model, self.session, **kwargs)

    def build_standard_field(self, attr, **kwargs):
        """
        Build a field for a sqlalchemy non-relation property depending on their type.
        """
        for base in attr.column.type.__class__.mro():
            type_func = getattr(self, "build_{}_field".format(base.__name__.lower()), None)
            if type_func and callable(type_func):
                kwargs.update(attr.field_kwargs)
                return type_func(attr, **kwargs)

        with suppress(NotImplementedError):
            for base in attr.column.type.python_type.mro():
                if base in FIELD_LOOKUP:
                    kwargs.update(attr.field_kwargs)
                    return FIELD_LOOKUP[base](**kwargs)

    def build_enum_field(self, attr, **kwargs):
        """
        Build field for sqlalchemy enum type.
        """
        kwargs.pop("max_length", None)

        if attr.column.type.enum_class:
            kwargs["enum_class"] = attr.column.type.enum_class
            return EnumField(**kwargs)

        kwargs["choices"] = [(val, val) for val in attr.column.type.enums]
        return djangofields.TypedChoiceField(**kwargs)

    def build_boolean_field(self, attr, **kwargs):
        """
        Build field for sqlalchemy boolean type.
        """
        kwargs.pop("max_length", None)
        if attr.column.nullable:
            return djangofields.NullBooleanField(**kwargs)

        return djangofields.BooleanField(**kwargs)

    def build_integer_field(self, attr, **kwargs):
        """
        Build field for sqlalchemy integer type.
        """
        return djangofields.IntegerField(**kwargs)

    build_integer_field = build_integer_field
    build_smallinteger_field = build_integer_field
    build_biginteger_field = build_integer_field

    def build_text_field(self, attr, **kwargs):
        """
        Build field for sqlalchemy text type.
        """
        kwargs["widget"] = djangoforms.Textarea
        return djangofields.CharField(**kwargs)

    build_clob_field = build_text_field

    def build_binary_field(self, attr, **kwargs):
        pass

    build_blob_field = build_binary_field
    build_largebinary_field = build_binary_field
    build_varbinary_field = build_binary_field
