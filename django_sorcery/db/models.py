# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict, namedtuple
from functools import partial
from itertools import chain

import six

import sqlalchemy as sa
import sqlalchemy.ext.declarative  # noqa
import sqlalchemy.orm  # noqa
from sqlalchemy.orm.base import MANYTOONE, NO_VALUE

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import DateField
from django.utils.text import camel_case_to_spaces

from . import signals
from .meta import model_info
from .mixins import CleanMixin


Identity = namedtuple("Key", ["model", "pk"])


def get_primary_keys(model, kwargs):
    """
    Returns the primary key from a dictionary to be used in a sqlalchemy query.get() call
    """
    info = model_info(model)
    pks = []

    for attr, _ in info.primary_keys.items():
        pk = kwargs.get(attr)
        pks.append(pk)

    if any(pk is None for pk in pks):
        return None

    if len(pks) < 2:
        return next(iter(pks), None)

    return tuple(pks)


def get_identity_key(model, kwargs):
    """
    Returns identity key from a dictionary for the given model
    """
    pks = get_primary_keys(model, kwargs)
    if pks is None:
        return

    return Identity(model, pks if isinstance(pks, tuple) else (pks,))


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
        comp = getattr(instance, composite.key)
        data[composite.key] = vars(comp) if comp else None
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


def deserialize(model, data):
    """
    Return a model instance from data
    ------------------------------
    model:
        a model class
    data: dict
        values
    """
    identity_map = {}
    instance = _deserialize(model, data, identity_map)

    for val in identity_map.values():
        info = model_info(val.__class__)
        for prop, rel in info.relationships.items():
            if rel.direction == MANYTOONE or not rel.uselist:
                deserialized_instance = getattr(val, prop)
                if deserialized_instance is not None:
                    continue

                fks = {}
                for local, remote in rel.local_remote_pairs_for_identity_key:
                    local_attr = rel.parent_mapper.get_property_by_column(local)
                    remote_attr = rel.related_mapper.get_property_by_column(remote)
                    fks[remote_attr.key] = getattr(val, local_attr.key)

                ident_key = get_identity_key(rel.related_model, fks)
                if ident_key is not None and ident_key in identity_map:
                    setattr(val, prop, identity_map[ident_key])

    return instance


def _deserialize(model, data, identity_map):
    if data is None:
        return None

    if isinstance(data, (list, tuple, set)):
        return [_deserialize(model, i, identity_map) for i in data]

    info = model_info(model)

    kwargs = {}
    for prop in info.primary_keys:
        if prop in data:
            kwargs[prop] = data.get(prop)

    pk = get_identity_key(model, kwargs)
    if pk is not None and pk in identity_map:
        return identity_map[pk]

    for prop in info.properties:
        if prop in data:
            kwargs[prop] = data.get(prop)

    for prop, composite in info.composites.items():
        if prop in data:
            composite_data = data.get(prop)
            composite_class = composite.related_model
            composite_args = [composite_data.get(i) for i in composite.properties]
            kwargs[prop] = composite_class(*composite_args)

    for prop, rel in info.relationships.items():
        if prop in data:
            kwargs[prop] = _deserialize(rel.related_model, data.get(prop), identity_map)

    instance = model(**kwargs)

    if pk is not None:
        identity_map[pk] = instance

    return instance


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


class BaseMeta(sqlalchemy.ext.declarative.DeclarativeMeta):
    """
    Base metaclass for models which registers models to DB model registry
    when models are created.
    """

    def __new__(typ, name, bases, attrs):
        klass = super(BaseMeta, typ).__new__(typ, name, bases, attrs)
        typ.db.models_registry.append(klass)
        return klass


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


def _coerce(target, value, oldvalue, initiator, form_field):
    value = value.strip() if isinstance(value, six.string_types) else value
    try:
        form_field.required = False

        if isinstance(form_field, DateField):
            # somehow input_formats is missing some formats and has to be reset like this
            form_field.input_formats = settings.DATE_INPUT_FORMATS

        return form_field.clean(value)
    except ValidationError as e:
        raise ValidationError({initiator.key: e})


_coercer_memo = {}
_autocoerce_attrs = set()


def autocoerce_properties(*attrs):
    """
    This function automatically registers attribute events that coerces types for given attributes
    using django's form fields.

    ::
        class MyModel(db.Model):
            field1 = Column(...)
            field2 = Column(...)
            field3 = Column(...)
            ...

        autocoerce_properties(MyModel.field1, MyModel.field2)  # Will only force autocoersion on field1 and field2
    """
    _autocoerce_attrs.update(attrs)


def autocoerce(cls):
    """
    This function automatically registers attribute events that coerces types for the attribute
    using django's form fields for a given model classs. If no class is provided, it will wire up
    coersion for all mappers so it can be used as a class decorator or globally.

    ::

        @autocoerce_properties
        class MyModel(db.Model):
            ...

    or::

        class MyModel(db.Model):
            ...

        autocoerce_properties()

    Since django form fields are used for coersion, localization settings such as `USE_THOUSAND_SEPARATOR`,
    `DATE_INPUT_FORMATS` and `DATETIME_INPUT_FORMATS` control type conversions.
    """
    m = sa.inspect(cls)
    autocoerce_properties(*[getattr(cls, attr.key) for attr in m.column_attrs])
    return cls


@sa.event.listens_for(sa.orm.mapper, "after_configured")
def configure_coercers():
    from django_sorcery.field_mapping import get_field_mapper

    for target in _autocoerce_attrs:
        field_mapper = get_field_mapper()(model=target.parent)
        info = model_info(target.parent)
        form_field = field_mapper.build_field(
            info.primary_keys.get(target.key) or info.properties.get(target.key), required=False, localize=True
        )

        if form_field is None:
            continue

        handler = _coercer_memo.setdefault(target, partial(_coerce, form_field=form_field))

        if not sa.event.contains(target, "set", handler):
            sa.event.listen(target, "set", handler, retval=True)

    _autocoerce_attrs.clear()
