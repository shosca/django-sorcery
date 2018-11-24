# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict, namedtuple
from itertools import chain

import six

import sqlalchemy as sa

from .base import model_info_meta
from .column import column_info
from .composite import composite_info
from .relations import relation_info


Identity = namedtuple("Key", ["model", "pk"])


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
                self.primary_keys[attr.key] = column_info(col, attr, self)

        for col in self.mapper.columns:
            attr = self.mapper.get_property_by_column(col)
            if attr.key not in self.primary_keys and attr.key not in self.properties:
                self.properties[attr.key] = column_info(col, attr, self)

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

    def __repr__(self):
        reprs = ["<model_info({!s})>".format(self.model_class.__name__)]
        reprs.extend("    " + repr(i) for i in self.primary_keys.values())
        reprs.extend("    " + repr(i) for _, i in sorted(self.properties.items()))
        reprs.extend("    " + i for i in chain(*[repr(c).split("\n") for _, c in sorted(self.composites.items())]))
        reprs.extend("    " + repr(i) for _, i in sorted(self.relationships.items()))
        return "\n".join(reprs)

    def state(self, instance):
        return sa.inspect(instance)

    @property
    def column_properties(self):
        return chain(self.primary_keys.items(), sorted(self.properties.items()))

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

    def primary_keys_from_dict(self, kwargs):
        """
        Returns the primary key tuple from a dictionary to be used in a sqlalchemy query.get() call
        """
        pks = []

        for attr, _ in self.primary_keys.items():
            pk = kwargs.get(attr)
            pks.append(pk)

        if any(pk is None for pk in pks):
            return None

        if len(pks) < 2:
            return next(iter(pks), None)

        return tuple(pks)

    def primary_keys_from_instance(self, instance):
        """
        Return a dict containing the primary keys of the ``instance``
        """
        if instance is None:
            return None

        if len(self.primary_keys) > 1:
            return OrderedDict((name, getattr(instance, name)) for name in self.primary_keys)

        return getattr(instance, next(iter(self.primary_keys)))

    def get_key(self, instance):
        """
        Returns the primary key tuple from the ``instance``
        """
        keys = self.mapper.primary_key_from_instance(instance)
        if any(key is None for key in keys):
            return
        return keys

    def identity_key_from_instance(self, instance):
        """
        Returns the primary key tuple from the ``instance``
        """
        keys = self.get_key(instance)
        if keys is None:
            return

        return Identity(self.model_class, self.get_key(instance))

    def identity_key_from_dict(self, kwargs):
        """
        Returns identity key from a dictionary for the given model
        """
        pks = self.primary_keys_from_dict(kwargs)
        if pks is None:
            return

        return Identity(self.model_class, pks if isinstance(pks, tuple) else (pks,))
