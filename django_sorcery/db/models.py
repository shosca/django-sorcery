# -*- coding: utf-8 -*-
"""
sqlalchemy model related things
"""
from itertools import chain

import six

import sqlalchemy as sa
import sqlalchemy.ext.declarative  # noqa
import sqlalchemy.orm  # noqa
from sqlalchemy.orm.base import MANYTOONE, NO_VALUE

from django.core.exceptions import ValidationError
from django.utils.text import camel_case_to_spaces

from . import meta, signals
from .mixins import CleanMixin


def simple_repr(instance, fields=None):
    """
    Provides basic repr for models
    ------------------------------
    instance: Model
        a model instance
    fields: list
        list of fields to display on repr
    """
    info = meta.model_info(instance)
    state = info.sa_state(instance)
    pks = info.primary_keys
    fields = fields or info.properties

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

    info = meta.model_info(instance)
    rels = set(rels)

    data = {name: getattr(instance, name) for name, _ in info.column_properties}

    for name, composite in info.composites.items():
        comp = getattr(instance, name)
        data[name] = vars(comp) if comp else None
        # since we're copying, remove props from the composite
        for _, prop in composite.properties.items():
            data.pop(prop.property.key, None)

    for name in info.relationships:
        attr = getattr(info.model_class, name)
        if attr in rels:
            sub_instance = getattr(instance, name, None)
            sub_rels = [r for r in rels if r is not attr]
            data[name] = serialize(sub_instance, *sub_rels)

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
        info = meta.model_info(val.__class__)
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

                related_info = meta.model_info(rel.related_model)
                ident_key = related_info.identity_key_from_dict(fks)
                if ident_key is not None and ident_key in identity_map:
                    setattr(val, prop, identity_map[ident_key])

    return instance


def _deserialize(model, data, identity_map):
    if data is None:
        return None

    if isinstance(data, (list, tuple, set)):
        return [_deserialize(model, i, identity_map) for i in data]

    info = meta.model_info(model)

    kwargs = {}
    for prop in info.primary_keys:
        if prop in data:
            kwargs[prop] = data.get(prop)

    pk = info.identity_key_from_dict(kwargs)
    if pk is not None and pk in identity_map:
        return identity_map[pk]

    for prop in info.properties:
        if prop in data:
            kwargs[prop] = data.get(prop)

    for prop, composite in info.composites.items():
        if prop in data:
            composite_data = data.get(prop)
            composite_class = composite.model_class
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

    mapper = sa.inspect(instance).mapper
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

    def __new__(mcs, name, bases, attrs):
        klass = super(BaseMeta, mcs).__new__(mcs, name, bases, attrs)
        mcs.db.models_registry.append(klass)
        return klass


def _table_name(cls):
    opts = getattr(cls, "Meta", None)
    return getattr(opts, "db_table", None) or "_".join(camel_case_to_spaces(cls.__name__).split())


def _table_args(cls):
    opts = getattr(cls, "Meta", None)
    return getattr(opts, "table_args", ())


def _mapper_args(cls):
    opts = getattr(cls, "Meta", None)
    return getattr(opts, "mapper_args", ())


class Base(CleanMixin):
    """
    Base model class for SQLAlchemy.

    Can be overwritten by subclasses:

        query_class = None

    Automatically added by declarative base for easier querying:

        query = None
        objects = None
    """

    __tablename__ = sa.ext.declarative.declared_attr(_table_name)
    __table_args__ = sa.ext.declarative.declared_attr(_table_args)
    __mapper_args__ = sa.ext.declarative.declared_attr(_mapper_args)

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
        return meta.model_info(self.__class__).properties

    def _get_nested_objects_for_validation(self):
        """
        Return all composites to be validated
        """
        return meta.model_info(self.__class__).composites

    def _get_relation_objects_for_validation(self):
        """
        Return all relations to be validated
        """
        return meta.model_info(self.__class__).relationships


_instant_defaults = set()


def instant_defaults(cls):
    """
    This function automatically registers attribute events that sets the column defaults to a
    model instance at model instance initialization provided that default values are simple
    types::

        @instant_defaults
        class MyModel(db.Model):
            attr = db.Column(..., default=1)

        assert MyModel().default == 1

    """
    mapper = sa.inspect(cls, raiseerr=False)
    if not mapper:
        return

    _instant_defaults.add(cls)
    return cls


signals.declare_last.connect(instant_defaults)


def _set_instant_defaults(target, args, kwargs):
    info = meta.model_info(target.__class__)
    for prop in info.properties.values():
        if not prop.column.default or not hasattr(prop.column.default, "arg") or callable(prop.column.default.arg):
            continue  # pragma: nocover

        if getattr(target, prop.name, None) is None:
            setattr(target, prop.name, prop.column.default.arg)


@sa.event.listens_for(sa.orm.mapper, "after_configured")
def _configure_instant_defaults():
    for cls in _instant_defaults:
        if not sa.event.contains(cls, "init", _set_instant_defaults):
            sa.event.listen(cls, "init", _set_instant_defaults)

    _instant_defaults.clear()


@signals.before_flush.connect
def full_clean_flush_handler(session, **kwargs):
    """
    Signal handler for executing ``full_clean``
    on all dirty and new objects in session
    """
    for i in session.dirty | session.new:
        if isinstance(i, Base):
            i.full_clean()


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


def _coerce(target, value, oldvalue, initiator):
    minfo = meta.model_info(target)
    cinfo = minfo.properties.get(initiator.key) or minfo.primary_keys.get(initiator.key)
    try:
        return cinfo.to_python(value) if cinfo else value
    except ValidationError as ex:
        raise ValidationError({initiator.key: ex})


@sa.event.listens_for(sa.orm.mapper, "after_configured")
def _configure_coercers():
    for target in _autocoerce_attrs:
        if not sa.event.contains(target, "set", _coerce):
            sa.event.listen(target, "set", _coerce, retval=True)

    _autocoerce_attrs.clear()
