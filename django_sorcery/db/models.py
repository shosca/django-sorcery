# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict
from itertools import chain

import six

import sqlalchemy as sa
import sqlalchemy.ext.declarative  # noqa
import sqlalchemy.orm  # noqa
from sqlalchemy.orm.base import NO_VALUE

from .meta import model_info


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

    data = {c.key: getattr(instance, c.key) for c in state.mapper.column_attrs}

    rels = set(rels)

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


class Base(object):
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
        return cls.__name__.lower()

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
        rels = getattr(cls, "_relationships", set())
        for relation in rels:
            if relation.direction == sa.orm.interfaces.ONETOMANY:
                relation.mapper.class_._add_foreign_keys(cls, relation)
            elif relation.direction == sa.orm.interfaces.MANYTOONE:
                cls._add_foreign_keys(relation.mapper.class_, relation)
            elif relation.direction == sa.orm.interfaces.MANYTOMANY:
                cls._add_association_table(relation.mapper.class_, relation)

        rels.clear()

    @classmethod
    def _add_foreign_keys(cls, parent_cls, relation):
        """
        Generate fk columns and constraint to the remote class from a relationship
        """
        fk_kwargs = {key[3:]: val for key, val in relation.info.items() if key.startswith("fk_")}
        fk_prefix = fk_kwargs.pop("fk_prefix", "_")
        fk_nullable = fk_kwargs.pop("fk_nullable", True)
        fk_key = fk_kwargs.pop("fk_key", None)

        if not fk_key:
            if relation.direction == sa.orm.interfaces.MANYTOONE:
                fk_key = relation.key.lower()
            elif relation.backref:
                backref, _ = relation.backref
                fk_key = backref.lower()
            else:
                fk_key = parent_cls.__name__.lower()

        cols = {}
        cols_created = False
        for pk_column in parent_cls.__table__.primary_key:
            pk_attr = parent_cls.__mapper__.get_property_by_column(pk_column)
            col_name = "_".join(filter(None, [fk_key, pk_column.name]))
            attr = "{}{}".format(fk_prefix, "_".join(filter(None, [fk_key, pk_attr.key])))

            if col_name not in cls.__table__.columns and not hasattr(cls, attr):
                fk_column = sa.Column(col_name, pk_column.type, nullable=fk_nullable)
                setattr(cls, attr, fk_column)
                cols_created = True
            else:
                fk_column = cls.__table__.columns[col_name]

            cols[pk_column] = fk_column

        relation._user_defined_foreign_keys = cols.values()

        if cols_created:
            # pk and fk ordering must match for foreign key constraint
            pks, fks = [], []
            for pk in cols:
                pks.append(pk)
                fks.append(cols[pk])

            constraint = sa.ForeignKeyConstraint(fks, pks, **fk_kwargs)
            cls.__table__.append_constraint(constraint)

    @classmethod
    def _add_association_table(cls, child_cls, relation):
        """
        Generate association table and fk constraints to satisfy a many-to-many relation
        """
        if relation.secondary is not None:
            return

        table_name = relation.info.get("table_name")
        relation.secondary = cls.metadata.tables.get(table_name)
        if relation.secondary is not None:
            return

        fk_kwargs = {key[3:]: val for key, val in relation.info.items() if key.startswith("fk_")}
        table_kwargs = {key[6:]: val for key, val in relation.info.items() if key.startswith("table_")}
        table_kwargs.pop("name", None)

        column_map = {}
        for pk_column in chain(cls.__mapper__.primary_key, child_cls.__table__.primary_key):
            col_name = "_".join(filter(None, [pk_column.table.name.lower(), pk_column.name]))
            col = sa.Column(col_name, pk_column.type, primary_key=True)
            column_map.setdefault(pk_column.table, []).append(col)

        table_args = list(chain(*column_map.values()))

        for table, columns in column_map.items():
            table_args.append(sa.ForeignKeyConstraint(columns, table.primary_key, **fk_kwargs))

        relation.secondary = sa.Table(
            table_name, cls.metadata, *table_args, schema=cls.__table__.schema, **table_kwargs
        )
