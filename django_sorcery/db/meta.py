# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict
from decimal import Decimal
from itertools import chain

import six

import sqlalchemy as sa

from django.utils.text import capfirst

from ..utils import get_args, suppress


class model_info_meta(type):
    _registry = {}

    def __call__(cls, model, *args, **kwargs):
        if isinstance(model, sa.orm.Mapper):
            model = model.class_

        if model not in cls._registry:
            instance = super(model_info_meta, cls).__call__(model, *args, **kwargs)
            cls._registry[model] = instance

        return cls._registry[model]


class composite_info(six.with_metaclass(model_info_meta)):
    """
    A helper class that makes sqlalchemy composite model inspection easier
    """

    __slots__ = ("prop", "properties", "_field_names")

    def __init__(self, composite):
        self._field_names = set()
        self.prop = composite.prop

        attrs = list(sorted([k for k, v in vars(self.prop.composite_class).items() if isinstance(v, sa.Column)]))
        if not attrs:
            attrs = get_args(self.prop.composite_class.__init__)

        self.properties = OrderedDict()
        for attr, prop, col in zip(attrs, self.prop.props, self.prop.columns):
            self.properties[attr] = column_info(prop, col, self)

    @property
    def field_names(self):
        if not self._field_names:
            self._field_names.update(self.properties.keys())

            self._field_names = [attr for attr in self._field_names if not attr.startswith("_")]

        return self._field_names

    @property
    def related_model(self):
        return self.prop.composite_class

    def __repr__(self):
        return "<composite_info({!s}, {!s}.{!s})>".format(
            self.related_model.__name__, self.prop.parent.class_.__name__, self.prop.key
        )


class column_info(object):
    """
    A helper class that makes sqlalchemy property and column inspection easier
    """

    __slots__ = ("property", "column", "parent")

    def __init__(self, prop, column, parent=None):
        self.property = prop
        self.column = column
        self.parent = parent

    @property
    def validators(self):
        return self.column.info.get("validators") or []

    @property
    def required(self):
        return self.column.info.get("required", not self.column.nullable)

    def formfield(self, form_class=None, **kwargs):
        form_class = form_class or self.column.info.get("form_class")
        if form_class is not None:
            field_kwargs = self.field_kwargs
            field_kwargs.update(kwargs)
            return form_class(**field_kwargs)

    @property
    def name(self):
        return self.property.key

    @property
    def parent_model(self):
        return self.property.parent.class_

    @property
    def field_kwargs(self):
        kwargs = {}
        if self.column.doc:
            kwargs["help_text"] = self.column.doc

        label = self.column.info.get("label")
        if label:
            kwargs["label"] = label
        else:
            label = self.property.key if self.property is not None else self.column.key
            if label:
                kwargs["label"] = capfirst(" ".join(label.split("_")))

        with suppress(AttributeError):
            if self.column.type.length is not None:
                kwargs["max_length"] = self.column.type.length

        with suppress(AttributeError):
            enum_class = self.column.type.enum_class
            if enum_class is not None:
                kwargs["enum_class"] = self.column.type.enum_class
            else:
                kwargs["choices"] = [(x, x) for x in self.column.type.enums]

            kwargs.pop("max_length", None)

        with suppress(AttributeError):
            max_digits = self.column.type.precision
            decimal_places = self.column.type.scale
            if self.column.type.python_type == Decimal:
                if max_digits is not None:
                    kwargs["max_digits"] = max_digits
                if decimal_places is not None:
                    kwargs["decimal_places"] = decimal_places

        kwargs["required"] = self.required
        kwargs["validators"] = self.validators

        if self.column.info.get("widget_class"):
            kwargs["widget"] = self.column.info.get("widget_class")

        return kwargs

    def __repr__(self):
        return "<column_info(%s.%s)>" % (self.parent_model.__name__, self.name)


class relation_info(object):
    """
    A helper class that makes sqlalchemy relationship property inspection easier
    """

    __slots__ = ("relationship",)

    def __init__(self, relationship):
        self.relationship = relationship

    @property
    def name(self):
        return self.relationship.key

    @property
    def parent_mapper(self):
        return self.relationship.parent

    @property
    def parent_model(self):
        return self.relationship.parent.class_

    @property
    def parent_table(self):
        return self.relationship.parent.tables[0]

    @property
    def related_mapper(self):
        return self.relationship.mapper

    @property
    def related_model(self):
        return self.relationship.mapper.class_

    @property
    def related_table(self):
        return self.relationship.mapper.tables[0]

    @property
    def direction(self):
        return self.relationship.direction

    @property
    def foreign_keys(self):
        return list(
            set(chain(self.relationship._calculated_foreign_keys, self.relationship._user_defined_foreign_keys))
        )

    @property
    def local_remote_pairs(self):
        return self.relationship.local_remote_pairs

    @property
    def local_remote_pairs_for_identity_key(self):
        target_pk = list(self.relationship.target.primary_key)
        pairs = {v: k for k, v in self.local_remote_pairs}

        try:
            # ensure local_remote pairs are of same order as remote pk
            return [(pairs[i], i) for i in target_pk]

        except KeyError:
            # if relation is missing one of related pk columns
            # but actual constraint has it defined
            # attempt to deduce what is the missing pk column
            # by inspecting FK constraint on table object itself
            # this only happens for pretty bad table structure
            # where some columns need to be omitted from relation
            # since same column is used in multiple relations
            # for people reading this comment lesson should be
            # DO NOT USE COMPOSITE PKs
            parent_columns = set(pairs.values())
            target_columns = set(target_pk)
            matching_constraints = [
                i
                for i in [c for c in self.parent_table.constraints if isinstance(c, sa.ForeignKeyConstraint)]
                if parent_columns & set(j.parent for j in i.elements) == parent_columns
                and target_columns & set(j.column for j in i.elements) == target_columns
            ]

            if len(matching_constraints) == 1:
                pairs = {i.column: i.parent for i in matching_constraints[0].elements}
                return [(pairs[i], i) for i in target_pk]

            else:
                # if everything fails, return default pairs
                return self.local_remote_pairs

    @property
    def uselist(self):
        return self.relationship.uselist

    def __repr__(self):
        return "<relation_info(%s.%s)>" % (self.parent_model.__name__, self.name)


class model_info(six.with_metaclass(model_info_meta)):
    """
    A helper class that makes sqlalchemy model inspection easier
    """

    __slots__ = ("mapper", "properties", "_field_names", "model_class", "composites", "primary_keys", "relationships")

    def __init__(self, model):
        self.model_class = model
        self.mapper = sa.inspect(model)
        self._field_names = None
        self.properties = {}
        self.composites = {}
        self.relationships = {}
        self.primary_keys = OrderedDict()

        sa.event.listen(self.mapper, "mapper_configured", self._configure)
        self._configure(self.mapper, self.model_class)

    def _configure(self, mapper, class_):
        assert mapper is self.mapper
        assert class_ is self.model_class

        for col in self.mapper.primary_key:
            attr = self.mapper.get_property_by_column(col)
            if attr.key not in self.primary_keys:
                self.primary_keys[attr.key] = column_info(attr, col, self)

        for col in self.mapper.columns:
            attr = self.mapper.get_property_by_column(col)
            if attr.key not in self.primary_keys and attr.key not in self.properties:
                self.properties[attr.key] = column_info(attr, col, self)

        for composite in self.mapper.composites:
            if composite.key not in self.composites:
                self.composites[composite.key] = composite_info(getattr(self.model_class, composite.key))

        for relationship in self.mapper.relationships:
            if relationship.key not in self.relationships:
                self.relationships[relationship.key] = relation_info(relationship)

    def __dir__(self):
        return (
            dir(super(model_info, self))
            + list(vars(type(self)))
            + list(self.primary_keys)
            + list(self.properties)
            + list(self.composites)
            + list(self.relationships)
        )

    def __getattr__(self, name):
        if name in self.primary_keys:
            return self.primary_keys[name]
        if name in self.properties:
            return self.properties[name]
        if name in self.composites:
            return self.composites[name]
        if name in self.relationships:
            return self.relationships[name]
        return getattr(super(model_info, self), name)

    @property
    def field_names(self):
        if not self._field_names:
            self._field_names = [
                attr
                for attr in chain(
                    self.primary_keys.keys(), self.properties.keys(), self.composites.keys(), self.relationships.keys()
                )
                if not attr.startswith("_")
            ]

        return self._field_names

    def __repr__(self):
        return "<model_info(%s)>" % self.model_class.__name__
