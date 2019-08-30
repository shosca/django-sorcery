# -*- coding: utf-8 -*-
"""
Metadata for composite sqlalchemy properties
"""
from collections import OrderedDict

import six

import sqlalchemy as sa

from django.core.exceptions import ValidationError

from ...exceptions import NestedValidationError
from ...utils import get_args
from ...validators import ValidationRunner
from .base import model_info_meta
from .column import column_info


class composite_info(six.with_metaclass(model_info_meta)):
    """
    A helper class that makes sqlalchemy composite model inspection easier
    """

    __slots__ = ("prop", "properties", "parent", "_field_names")

    def __init__(self, composite, parent=None):
        self._field_names = set()
        self.prop = composite.prop
        self.parent = parent

        attrs = list(sorted(k for k, v in vars(self.prop.composite_class).items() if isinstance(v, sa.Column)))
        if not attrs:
            attrs = get_args(self.prop.composite_class.__init__)

        self.properties = OrderedDict()
        for attr, prop, col in zip(attrs, self.prop.props, self.prop.columns):
            self.properties[attr] = column_info(col, prop, self, name=attr)

    @property
    def field_names(self):
        """
        Returns field names used in composite
        """
        if not self._field_names:
            self._field_names.update(self.properties.keys())

            self._field_names = [attr for attr in self._field_names if not attr.startswith("_")]

        return self._field_names

    @property
    def name(self):
        """
        Returns composite field name
        """
        return self.prop.key

    @property
    def attribute(self):
        """
        Returns composite field instrumented attribute for generating query expressions
        """
        return getattr(self.parent_model, self.name)

    @property
    def parent_model(self):
        """
        Returns the model class that the attribute belongs to
        """
        return self.prop.parent.class_

    @property
    def model_class(self):
        """
        Returns the composite class
        """
        return self.prop.composite_class

    def __repr__(self):
        reprs = [
            "<composite_info({!s}, {!s}.{!s})>".format(self.model_class.__name__, self.parent_model.__name__, self.name)
        ]
        reprs.extend("    " + repr(i) for _, i in sorted(self.properties.items()))
        return "\n".join(reprs)

    def clean_fields(self, instance, exclude=None):
        """
        Clean all fields and raise a ValidationError containing a dict
        of all validation errors if any occur.
        """
        errors = {}
        exclude = exclude or []
        for name, f in self.properties.items():
            raw_value = getattr(instance, name, None)
            is_blank = not bool(raw_value)
            is_nullable = f.null
            is_defaulted = f.column.default or f.column.server_default
            is_required = f.required

            is_skippable = is_blank and (is_nullable or is_defaulted or not is_required)

            if name in exclude or is_skippable:
                continue
            try:
                setattr(instance, name, f.clean(raw_value, instance))
            except ValidationError as e:
                errors[name] = e.error_list
        if errors:
            raise NestedValidationError(errors)

    def run_validators(self, instance):
        """
        Run composite field's validators and raise ValidationError if necessary
        """
        runner = ValidationRunner(validators=getattr(instance, "validators", []))
        runner.is_valid(instance, raise_exception=True)

    def full_clean(self, instance, exclude=None):
        """
        Call clean_fields(), clean(), and run_validators() on the composite model.
        Raise a ValidationError for any errors that occur.
        """
        runner = ValidationRunner(
            name=self.name,
            validators=[
                lambda x: self.clean_fields(x, exclude),
                self.run_validators,
                lambda x: getattr(x, "clean", bool)(),
            ],
        )
        runner.is_valid(instance, raise_exception=True)
