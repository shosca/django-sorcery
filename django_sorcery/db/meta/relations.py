# -*- coding: utf-8 -*-
"""
Metadata for sqlalchemy model relationships
"""
from itertools import chain

import sqlalchemy as sa

from django.core.exceptions import ImproperlyConfigured


class relation_info(object):
    """
    A helper class that makes sqlalchemy relationship property inspection easier
    """

    __slots__ = (
        "attribute",
        "direction",
        "field_kwargs",
        "foreign_keys",
        "local_remote_pairs",
        "local_remote_pairs_for_identity_key",
        "name",
        "parent_mapper",
        "parent_model",
        "parent_table",
        "related_mapper",
        "related_model",
        "related_table",
        "relationship",
        "uselist",
    )

    def __init__(self, relationship):
        self.relationship = relationship
        self.name = self.relationship.key
        self.parent_mapper = self.relationship.parent
        self.parent_model = self.relationship.parent.class_
        self.parent_table = self.relationship.parent.tables[0]
        self.related_mapper = self.relationship.mapper
        self.related_model = self.relationship.mapper.class_
        self.related_table = self.relationship.mapper.tables[0]
        self.attribute = getattr(self.parent_model, self.name)
        self.direction = self.relationship.direction
        self.foreign_keys = list(
            set(chain(self.relationship._calculated_foreign_keys, self.relationship._user_defined_foreign_keys))
        )
        self.uselist = self.relationship.uselist
        self.field_kwargs = {}
        if self.uselist:
            self.field_kwargs["required"] = False
        else:
            self.field_kwargs["required"] = not all(col.nullable for col in self.foreign_keys)

        self.local_remote_pairs = self.relationship.local_remote_pairs

        target_pk = list(self.relationship.target.primary_key)
        pairs = {v: k for k, v in self.local_remote_pairs}
        self.local_remote_pairs_for_identity_key = []
        try:
            # ensure local_remote pairs are of same order as remote pk
            for i in target_pk:
                self.local_remote_pairs_for_identity_key.append((pairs[i], i))
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
                if parent_columns & {j.parent for j in i.elements} == parent_columns
                and target_columns & {j.column for j in i.elements} == target_columns
            ]

            if len(matching_constraints) == 1:
                pairs = {i.column: i.parent for i in matching_constraints[0].elements}
                for i in target_pk:
                    self.local_remote_pairs_for_identity_key.append((pairs[i], i))
            else:
                # if everything fails, return default pairs
                self.local_remote_pairs_for_identity_key = self.local_remote_pairs[:]

    def formfield(self, form_class=None, **kwargs):
        if kwargs.get("session") is None:
            raise ImproperlyConfigured("Creating a relation form field without session attribute prohibited")

        form_class = form_class or self.get_form_class()
        if form_class is not None:
            field_kwargs = self.field_kwargs.copy()
            field_kwargs.update(kwargs)
            return form_class(self.related_model, **field_kwargs)

    def get_form_class(self):
        from ...fields import ModelChoiceField, ModelMultipleChoiceField

        if self.uselist:
            return ModelMultipleChoiceField

        return ModelChoiceField

    def __repr__(self):
        return "<relation_info(%s.%s)>" % (self.parent_model.__name__, self.name)
