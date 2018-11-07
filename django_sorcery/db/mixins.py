# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from itertools import chain

from sqlalchemy.exc import NoInspectionAvailable

from django.core.exceptions import ValidationError

from ..exceptions import NestedValidationError
from ..utils import suppress
from .meta import model_info


class CleanMixin(object):
    """
    Mixin for adding django-style ``full_clean`` validation to any object.

    Base model in :py:class:`..sqlalchemy.SQLAlchemy` already uses this mixin applied.

    For example::

        class Address(db.Model):
            city = db.Column(db.String(20))
            state = db.Column(db.String(2))
            date = db.Column(db.Date())

            validators = [
                ValidateTogetherModelFields(["city", "state"]),
            ]

            def clean_date(self):
                if self.date > datetime.date.today():
                    raise ValidationError("Cant pick future date")

            def clean(self):
                if self.date.year < 1776 and self.state == "NY":
                    raise ValidationError("NY state did not exist before 1776")
    """

    def clean(self):
        """
        Hook for adding custom model validations before model is flushed.

        Should raise ``ValidationError`` if any errors are found.
        """

    def clean_fields(self, exclude):
        """
        Clean all fields on object
        """
        errors = {}

        local_remote_pairs = set()
        with suppress(NoInspectionAvailable):
            # It is possible that this could be a composite type so suppress this
            info = model_info(type(self))
            for rel in info.relationships.values():
                for col in chain(*rel.local_remote_pairs):
                    local_remote_pairs.add(col)

        for name, field in self._get_properties_for_validation().items():
            is_blank = not bool(getattr(self, name))
            is_nullable = field.column.nullable
            is_fk = field.column in local_remote_pairs
            is_defaulted = field.column.default or field.column.server_default
            is_required = field.column.info.get("required", not is_nullable)

            # skip validation if:
            # - field is blank and either when field is nullable so blank value is valid
            # - field has either local or server default value since we assume default value will pass validation
            #   since default values are assigned during flush which as after which validation is verified
            # - field is blank and is a foreign key in a relation that will be populated by the relation
            # - field is marked as not required in column info
            is_skippable = is_blank and (is_nullable or is_defaulted or is_fk or not is_required)

            if name not in exclude and not is_skippable:

                for v in field.column.info.get("validators", []):
                    try:
                        v(getattr(self, name))
                    except ValidationError as e:
                        try:
                            e.error_list
                        except AttributeError:
                            errors = e.update_error_dict(errors)
                        else:
                            errors.setdefault(name, []).extend(e.error_list)

                try:
                    getattr(self, "clean_{}".format(name), bool)()

                except ValidationError as e:
                    try:
                        e.error_list
                    except AttributeError:
                        errors = e.update_error_dict(errors)
                    else:
                        errors.setdefault(name, []).extend(e.error_list)

        if errors:
            raise ValidationError(errors)

    def _get_properties_for_validation(self):
        """
        Needs to be implemented to return all properties for the object
        """

    def clean_nested_fields(self, exclude):
        """
        Clean all nested fields which includes composites
        """
        errors = {}

        for name in self._get_nested_objects_for_validation():
            try:
                e = exclude.get(name, [])
            except AttributeError:
                e = []

            # only exclude when subexclude is not either list or dict
            # otherwise validate nested object and let it ignore its own subfields
            is_nestable = e and isinstance(e, (dict, list, tuple))
            if name not in exclude or is_nestable:

                try:
                    try:
                        getattr(self, name).full_clean(exclude=e)
                    except AttributeError:
                        pass

                except ValidationError as e:
                    errors[name] = e.update_error_dict({})

        if errors:
            raise NestedValidationError(errors)

    def _get_nested_objects_for_validation(self):
        """
        Needs to be implemented to return all nested objects
        """

    def run_validators(self):
        """
        Check all model validators registered on ``validators`` attribute
        """
        errors = {}

        for v in getattr(self, "validators", []):
            try:
                v(self)
            except ValidationError as e:
                errors = e.update_error_dict(errors)

        if errors:
            raise ValidationError(errors)

    def full_clean(self, exclude=None):
        """
        Run model's full clean chain

        This will run all of these in this order:

        * will validate all columns by using ``clean_<column>`` methods
        * will validate all nested objects (e.g. composites) with ``full_clean``
        * will run through all registered validators on ``validators`` attribute
        * will run full model validation with ``self.clean()``
        """
        exclude = exclude or []
        errors = {}

        try:
            self.clean_fields(exclude=exclude)
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        try:
            self.clean_nested_fields(exclude=exclude)
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        try:
            self.run_validators()
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        try:
            self.clean()
        except ValidationError as e:
            errors = e.update_error_dict(errors)

        if errors:
            raise NestedValidationError(errors)
