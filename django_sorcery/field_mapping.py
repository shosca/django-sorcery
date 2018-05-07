# -*- coding: utf-8 -*-
"""
Field mapping from SQLAlchemy type's to form fields
"""
from __future__ import absolute_import, print_function, unicode_literals
import datetime
import decimal
import six
from collections import OrderedDict

import sqlalchemy as sa

from django import forms as djangoforms
from django.forms import fields as djangofields

from .db.meta import model_info
from .fields import EnumField, ModelChoiceField, ModelMultipleChoiceField, apply_limit_choices_to_form_field


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

if six.PY2:
    FIELD_LOOKUP[unicode] = djangofields.CharField  # noqa
    FIELD_LOOKUP[long] = djangofields.IntegerField  # noqa


class ModelFieldMapper(OrderedDict):

    def __init__(self, opts, formfield_callback=None, apply_limit_choices_to=True):
        self.opts = opts
        self.formfield_callback = formfield_callback
        self.apply_limit_choices_to = apply_limit_choices_to

    def get_default_kwargs(self, name, **kwargs):
        if self.opts.widgets and name in self.opts.widgets:
            kwargs["widget"] = self.opts.widgets[name]
        if self.opts.localized_fields == ALL_FIELDS:
            kwargs["localize"] = True
        if self.opts.localized_fields and name in self.opts.localized_fields:
            kwargs["localize"] = True
        if self.opts.labels and name in self.opts.labels:
            kwargs["label"] = self.opts.labels[name]
        if self.opts.help_texts and name in self.opts.help_texts:
            kwargs["help_text"] = self.opts.help_texts[name]
        if self.opts.error_messages and name in self.opts.error_messages:
            kwargs["error_messages"] = self.opts.error_messages[name]
        if self.opts.field_classes and name in self.opts.field_classes:
            kwargs["form_class"] = self.opts.field_classes[name]
        return kwargs

    def get_fields(self):

        field_list = []

        info = model_info(self.opts.model)

        for name, attr in info.properties.items():

            if name.startswith("_"):
                continue

            if self.opts.fields and name not in self.opts.fields:
                continue

            if self.opts.exclude and name in self.opts.exclude:
                continue

            kwargs = self.get_default_kwargs(name)
            if callable(self.formfield_callback):
                formfield = self.formfield_callback(attr, **kwargs)
            else:
                formfield = self.build_standard_field(attr)

            if formfield:
                if self.apply_limit_choices_to:
                    apply_limit_choices_to_form_field(formfield)
                field_list.append((name, formfield))

        formfield = None
        for name, rel in info.relationships.items():

            if self.opts.fields and name not in self.opts.fields:
                continue

            if self.opts.exclude and name in self.opts.exclude:
                continue

            kwargs = self.get_default_kwargs(name)
            if callable(self.formfield_callback):
                formfield = self.formfield_callback(rel, **kwargs)
            else:
                formfield = self.build_relationship_field(rel, **kwargs)

            if formfield:
                field_list.append((name, formfield))

        return OrderedDict(field_list)

    def build_relationship_field(self, relation, **kwargs):
        if relation.direction == sa.orm.relationships.MANYTOMANY:
            return self.build_modelmultiplechoice_field(relation, **kwargs)

        if relation.direction == sa.orm.relationships.ONETOMANY and relation.uselist:
            return self.build_modelmultiplechoice_field(relation, **kwargs)

        return self.build_modelchoice_field(relation, **kwargs)

    def build_modelchoice_field(self, relation, **kwargs):
        kwargs["required"] = all([col.nullable for col in relation.foreign_keys])
        return ModelChoiceField(relation.related_model, self.opts.session, **kwargs)

    def build_modelmultiplechoice_field(self, relation, **kwargs):
        kwargs["required"] = False
        return ModelMultipleChoiceField(relation.related_model, self.opts.session, **kwargs)

    def build_standard_field(self, attr, **kwargs):

        for base in attr.column.type.__class__.mro():
            type_func = getattr(self, "build_{}_field".format(base.__name__.lower()), None)
            if type_func and callable(type_func):
                kwargs.update(attr.field_kwargs)
                return type_func(attr, **kwargs)

        python_type = attr.column.type.python_type
        if python_type in FIELD_LOOKUP:
            kwargs.update(attr.field_kwargs)
            return FIELD_LOOKUP[python_type](**kwargs)

    def build_enum_field(self, attr, **kwargs):
        kwargs.pop("max_length", None)

        if attr.column.type.enum_class:
            kwargs["enum_class"] = attr.column.type.enum_class
            return EnumField(**kwargs)

        kwargs["choices"] = [(val, val) for val in attr.column.type.enums]
        return djangofields.TypedChoiceField(**kwargs)

    def build_boolean_field(self, attr, **kwargs):
        if attr.column.nullable:
            return djangofields.NullBooleanField(**kwargs)

        return djangofields.BooleanField(**kwargs)

    def build_integer_field(self, attr, **kwargs):
        return djangofields.IntegerField(**kwargs)

    build_integer_field = build_integer_field
    build_smallinteger_field = build_integer_field
    build_biginteger_field = build_integer_field

    def build_text_field(self, attr, **kwargs):
        kwargs["widget"] = djangoforms.Textarea
        return djangofields.CharField(**kwargs)

    build_clob_field = build_text_field

    def build_binary_field(self, attr, **kwargs):
        pass

    build_blob_field = build_binary_field
    build_largebinary_field = build_binary_field
    build_varbinary_field = build_binary_field
