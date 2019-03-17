# -*- coding: utf-8 -*-
"""
Metadata for sqlalchemy models
"""
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict, namedtuple
from functools import partial
from itertools import chain

import six

import sqlalchemy as sa

from django.core.exceptions import ValidationError

from ...exceptions import NestedValidationError
from ...validators import ValidationRunner
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
                self.primary_keys[attr.key] = column_info(col, attr, self, name=attr.key)

        for col in self.mapper.columns:
            attr = self.mapper.get_property_by_column(col)
            if attr.key not in self.primary_keys and attr.key not in self.properties:
                self.properties[attr.key] = column_info(col, attr, self, name=attr.key)

        for composite in self.mapper.composites:
            if composite.key not in self.composites:
                self.composites[composite.key] = composite_info(getattr(self.model_class, composite.key), parent=self)
                for prop in composite.props:
                    if prop.key in self.properties:
                        del self.properties[prop.key]

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

    def sa_state(self, instance):
        """
        Returns sqlalchemy instance state
        """
        return sa.inspect(instance)

    @property
    def column_properties(self):
        """
        Returns column properties
        """
        return chain(self.primary_keys.items(), sorted(self.properties.items()))

    @property
    def field_names(self):
        """
        Returns field names for the model
        """
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

    def full_clean(self, instance, exclude=None, **kwargs):
        """
        Run model's full clean chain

        This will run all of these in this order:

        * will validate all columns by using ``clean_<column>`` methods
        * will validate all nested objects (e.g. composites) with ``full_clean``
        * will run through all registered validators on ``validators`` attribute
        * will run full model validation with ``self.clean()``
        * if ``recursive`` kwarg is provided, will recursively clean all relations.
          Useful when all models need to be explicitly cleaned without flushing to DB.
        """
        exclude = exclude or []

        validators = [
            lambda x: getattr(x, "clean_fields", partial(self.clean_fields, instance=instance))(
                exclude=exclude, **kwargs
            ),
            lambda x: getattr(x, "clean_nested_fields", partial(self.clean_nested_fields, instance=instance))(
                exclude=exclude, **kwargs
            ),
            lambda x: getattr(x, "run_validators", partial(self.run_validators, instance=instance))(**kwargs),
            lambda x: x.clean(**kwargs),
        ]
        if kwargs.get("recursive", False):
            validators.append(
                lambda x: getattr(x, "clean_relation_fields", partial(self.clean_relation_fields, instance=instance))(
                    exclude=exclude, **kwargs
                )
            )

        runner = ValidationRunner(validators=validators)
        runner.is_valid(instance, raise_exception=True)

    def clean_fields(self, instance, exclude=None, **kwargs):
        """
        Clean all fields on object
        """
        errors = {}
        exclude = exclude or []
        local_remote_pairs = set()
        for rel in self.relationships.values():
            for col in chain(*rel.local_remote_pairs):
                local_remote_pairs.add(col)

        props = [
            self.properties[prop]
            for prop in getattr(instance, "_get_properties_for_validation", lambda x: self.properties.values())()
            if prop in self.properties
        ]

        for f in props:
            raw_value = getattr(instance, f.name)
            is_blank = not bool(raw_value)
            is_nullable = f.null
            is_fk = f.column in local_remote_pairs
            is_defaulted = f.column.default or f.column.server_default
            is_required = f.required

            # skip validation if:
            # - field is blank and either when field is nullable so blank value is valid
            # - field has either local or server default value since we assume default value will pass validation
            #   since default values are assigned during flush which as after which validation is verified
            # - field is blank and is a foreign key in a relation that will be populated by the relation
            # - field is marked as not required in column info
            is_skippable = is_blank and (is_nullable or is_defaulted or is_fk or not is_required)

            if f.name in exclude or is_skippable:
                continue

            try:
                setattr(instance, f.name, f.clean(raw_value, instance))
            except ValidationError as e:
                errors[f.name] = e.error_list

        if errors:
            raise NestedValidationError(errors)

    def clean_nested_fields(self, instance, exclude=None, **kwargs):
        """
        Clean all nested fields which includes composites
        """
        errors = {}
        exclude = exclude or []
        props = [
            self.composites[prop]
            for prop in getattr(instance, "_get_nested_objects_for_validation", lambda x: self.composites.values())()
            if prop in self.composites
        ]

        for f in props:
            try:
                e = exclude.get(f.name, [])
            except AttributeError:
                e = []

            # only exclude when subexclude is not either list or dict
            # otherwise validate nested object and let it ignore its own subfields
            is_nestable = e and isinstance(e, (dict, list, tuple))

            if f.name not in exclude or is_nestable:
                try:
                    f.full_clean(getattr(instance, f.name), exclude=e)
                except ValidationError as ex:
                    ex = NestedValidationError(ex)
                    errors[f.name] = ex.update_error_dict({})

        if errors:
            raise NestedValidationError(errors)

    def clean_relation_fields(self, instance, exclude=None, **kwargs):
        """
        Clean all relation fields
        """
        exclude = exclude or []
        visited = kwargs.pop("visited", set())
        visited.add(id(instance))
        errors = {}

        props = getattr(instance, "_get_relation_objects_for_validation", lambda x: [])() or self.relationships

        for name in props:
            try:
                e = exclude.get(name, [])
            except AttributeError:
                e = []

            # only exclude when subexclude is not either list or dict
            # otherwise validate nested object and let it ignore its own subfields
            is_nestable = e and isinstance(e, (dict, list, tuple))

            # only validate relation if it is preloaded on the instance
            # otherwise full clean will explode to the complete model tree
            # which is not necessary as unloaded models cannot possibly
            # be in violating
            is_loaded = name in instance.__dict__

            if is_loaded and (name not in exclude or is_nestable):
                value = getattr(instance, name)

                if isinstance(value, (list, tuple)):
                    _errors = []

                    for i in value:
                        if id(i) not in visited:
                            try:
                                i.full_clean(exclude=e, visited=visited, **kwargs)
                            except AttributeError:
                                pass
                            except ValidationError as e:
                                e = NestedValidationError(e)
                                _errors.append(e.update_error_dict({}))

                    if _errors:
                        errors[name] = _errors

                else:
                    try:
                        if id(value) not in visited:
                            value.full_clean(exclude=e, visited=visited, **kwargs)
                    except AttributeError:
                        pass
                    except ValidationError as e:
                        e = NestedValidationError(e)
                        errors[name] = e.update_error_dict({})

        if errors:
            raise NestedValidationError(errors)

    def run_validators(self, instance, exclude=None, **kwargs):
        """
        Check all model validators registered on ``validators`` attribute
        """
        runner = ValidationRunner(validators=getattr(instance, "validators", []))
        runner.is_valid(instance, raise_exception=True)
