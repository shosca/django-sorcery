# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict
from itertools import chain

import six

import sqlalchemy as sa
import sqlalchemy.ext.declarative  # noqa
import sqlalchemy.orm  # noqa
from sqlalchemy.orm.base import NO_VALUE

from django.utils.text import camel_case_to_spaces

from . import signals
from .meta import model_info
from .mixins import CleanMixin


def get_primary_keys(model, kwargs):
    """
    Returns the primary key from a dictionary to be used in a sqlalchemy query.get() call
    """
    info = model_info(model)
    pks = []

    for attr, _ in info.primary_keys.items():
        pk = kwargs.get(attr)
        pks.append(pk)

    if len(pks) < 2:
        return next(iter(pks), None)

    if any(pk is None for pk in pks):
        return None

    return tuple(pks)


def get_primary_keys_from_instance(instance):
    """
    Return a dict containing the primary keys of the ``instance``
    """
    if instance is None:
        return None

    info = model_info(type(instance))

    if len(info.primary_keys) > 1:
        return OrderedDict((name, getattr(instance, name)) for name in info.primary_keys)

    return getattr(instance, next(iter(info.primary_keys)))


def model_to_dict(instance, fields=None, exclude=None):
    """
    Return a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """
    info = model_info(type(instance))

    fields = set(
        fields or list(info.properties.keys()) + list(info.primary_keys.keys()) + list(info.relationships.keys())
    )
    exclude = set(exclude or [])
    data = {}
    for name in info.properties:

        if name.startswith("_"):
            continue

        if name not in fields:
            continue

        if name in exclude:
            continue

        data[name] = getattr(instance, name)

    for name, rel in info.relationships.items():

        if name.startswith("_"):
            continue

        if name not in fields:
            continue

        if name in exclude:
            continue

        if rel.uselist:
            for obj in getattr(instance, name):
                pks = get_primary_keys_from_instance(obj)
                if pks:
                    data.setdefault(name, []).append(pks)
        else:
            obj = getattr(instance, name)
            pks = get_primary_keys_from_instance(obj)
            if pks:
                data[name] = pks

    return data


def simple_repr(instance, fields=None):
    """
    Provides basic repr for models
    ------------------------------
    instance: Model
        a model instance
    fields: list
        list of fields to display on repr
    """
    state = sa.inspect(instance)
    pks = [state.mapper.get_property_by_column(col).key for col in state.mapper.primary_key]
    fields = fields or [
        state.mapper.get_property_by_column(col).key for col in state.mapper.columns if not col.primary_key
    ]

    pk_reprs = []
    for key in pks:
        value = state.attrs[key].loaded_value
        if value == NO_VALUE:
            value = None
        elif isinstance(value, six.text_type):
            # remove pesky "u" prefix in repr for strings
            value = str(value)
        pk_reprs.append("=".join([key, repr(value)]))

    field_reprs = []
    for key in fields:
        value = state.attrs[key].loaded_value
        if isinstance(value, six.text_type):
            # remove pesky "u" prefix in repr for strings
            value = str(value)
        if value != NO_VALUE:
            field_reprs.append("=".join([key, repr(value)]))

    return "".join([instance.__class__.__name__, "(", ", ".join(chain(pk_reprs, sorted(field_reprs))), ")"])


def serialize(instance, *rels):
    """
    Return a dict of column attributes
    ------------------------------
    instance:
        a model instance
    rels: list of relations
        relationships to be serialized
    """
    if instance is None:
        return None

    if isinstance(instance, (list, set)):
        return [serialize(i, *rels) for i in instance]

    state = sa.inspect(instance)
    rels = set(rels)

    data = {c.key: getattr(instance, c.key) for c in state.mapper.column_attrs}

    for composite in state.mapper.composites:
        attr = getattr(state.mapper.class_, composite.key)
        data[composite.key] = vars(getattr(instance, composite.key))
        # since we're copying, remove props from the composite
        for prop in composite.props:
            data.pop(prop.key, None)

    for relation in state.mapper.relationships:
        attr = getattr(state.mapper.class_, relation.key)
        if attr in rels:
            sub_instance = getattr(instance, relation.key, None)
            sub_rels = [r for r in rels if r is not attr]
            data[relation.key] = serialize(sub_instance, *sub_rels)

    return data


def clone(instance, *rels, **kwargs):
    """
    Clone a model instance with or without any relationships
    --------------------------------------------------------
    instance: Model
        a model instance
    relations: list or relations or a tuple of relation and kwargs for that relation
        relationships to be cloned with relationship and optionally kwargs
    kwargs: dict string of any
        attribute values to be overridden
    """
    if instance is None:
        return None

    if isinstance(instance, (list, set)):
        return [clone(i, *rels, **kwargs) for i in instance]

    relations = {}
    for rel in rels:
        r = rel
        rkwargs = {}
        if isinstance(rel, tuple):
            r, rkwargs = rel

        relations[r] = rkwargs

    state = sa.inspect(instance)
    mapper = state.mapper
    kwargs = kwargs or {}

    fks = set(
        chain(
            *[
                fk.columns
                for fk in chain(*[table.constraints for table in mapper.tables])
                if isinstance(fk, sa.ForeignKeyConstraint)
            ]
        )
    )

    for column in mapper.columns:
        prop = mapper.get_property_by_column(column)

        if prop.key in kwargs:
            continue

        if column.primary_key or column in fks:
            continue

        kwargs[prop.key] = getattr(instance, prop.key)

    for composite in mapper.composites:
        value = getattr(instance, composite.key, None)
        if value:
            kwargs[composite.key] = composite.composite_class(*value.__composite_values__())
            # since we're copying, remove props from the composite
            for prop in composite.props:
                kwargs.pop(prop.key, None)

    for relation in mapper.relationships:
        if relation.key in kwargs:
            continue

        attr = getattr(mapper.class_, relation.key)
        if attr in relations:
            sub_instance = getattr(instance, relation.key, None)
            sub_rels = [(r, kw) for r, kw in relations.items() if r is not attr]
            kwargs[relation.key] = clone(sub_instance, *sub_rels, **relations[attr])

    cloned = mapper.class_(**kwargs)
    return cloned


class Base(CleanMixin):
    """
    Base model class for SQLAlchemy.

    Can be overwritten by subclasses:

        query_class = None

    Automatically added by declarative base for easier querying:

        query = None
        objects = None
    """

    @sa.ext.declarative.declared_attr
    def __tablename__(cls):
        """
        Autogenerate a table name
        """
        return "_".join(camel_case_to_spaces(cls.__name__).split())

    def as_dict(self):
        """
        Return a dict of column attributes
        """
        return serialize(self)

    def __repr__(self):
        return simple_repr(self)

    @classmethod
    def __declare_first__(cls):
        """
        Declarative hook called within `before_configure` mapper event, can be called multiple times.
        """
        signals.declare_first.send(cls)

    @classmethod
    def __declare_last__(cls):
        """
        Declarative hook called within `after_configure` mapper event, can be called multiple times.
        """
        signals.declare_last.send(cls)

    def _get_properties_for_validation(self):
        """
        Return all model columns which can be validated
        """
        info = model_info(self.__class__)
        return {k: v for k, v in info.properties.items() if k in info.field_names}

    def _get_nested_objects_for_validation(self):
        """
        Return all composites to be validated
        """
        return model_info(self.__class__).composites


@signals.before_flush.connect
def full_clean_flush_handler(session, **kwargs):
    """
    Signal handler for executing ``full_clean``
    on all dirty and new objects in session
    """
    for i in session.dirty | session.new:
        if isinstance(i, Base):
            i.full_clean()
