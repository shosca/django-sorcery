# -*- coding: utf-8 -*-
"""
Metadata for sqlalchemy model relationships
"""
from __future__ import absolute_import, print_function, unicode_literals
from itertools import chain

import sqlalchemy as sa

from django.core.exceptions import ImproperlyConfigured


class relation_info(object):
    """
    A helper class that makes sqlalchemy relationship property inspection easier
    """

    __slots__ = ("relationship",)

    def __init__(self, relationship):
        self.relationship = relationship

    @property
    def attribute(self):
        """
        Returns the relationship instrumented attribute on the model
        """
        return getattr(self.parent_model, self.name)

    @property
    def name(self):
        """
        Returns the name of the attribute
        """
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

    def formfield(self, form_class=None, **kwargs):
        if kwargs.get("session") is None:
            raise ImproperlyConfigured("Creating a relation form field without session attribute prohibited")

        form_class = form_class or self.get_form_class()
        if form_class is not None:
            field_kwargs = self.field_kwargs
            field_kwargs.update(kwargs)
            return form_class(self.related_model, **field_kwargs)

    def get_form_class(self):
        from ...fields import ModelChoiceField, ModelMultipleChoiceField

        if self.uselist:
            return ModelMultipleChoiceField

        return ModelChoiceField

    @property
    def field_kwargs(self):
        kwargs = {}
        if self.uselist:
            kwargs["required"] = False
        else:
            kwargs["required"] = not all([col.nullable for col in self.foreign_keys])
        return kwargs

    def __repr__(self):
        return "<relation_info(%s.%s)>" % (self.parent_model.__name__, self.name)
