# -*- coding: utf-8 -*-
"""
Validation runner
"""

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from ..exceptions import NestedValidationError


class ValidationRunner(object):
    """
    Helper class that can execute a bunch of validators on a given object
    """

    def __init__(self, name=None, validators=None, errors=None):
        self.name = name or NON_FIELD_ERRORS
        self.validators = validators or []
        self.errors = errors or {}

    def is_valid(self, value, raise_exception=False):
        """
        Runs all validators on given value and collect validation errors
        """
        for v in self.validators:
            try:
                v(value)
            except ValidationError as e:
                e = NestedValidationError(e)
                try:
                    e.error_list
                except AttributeError:
                    self.errors = e.update_error_dict(self.errors)
                else:
                    self.errors.setdefault(self.name, []).extend(e.error_list)

        if self.errors and raise_exception:
            raise NestedValidationError(self.errors)

        return not self.errors
