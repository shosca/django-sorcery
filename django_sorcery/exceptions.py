# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError


class NestedValidationError(ValidationError):
    """
    Django Validation error except which allows nested errors

    Useful for validating composite objects.

    For example::

        raise NestedValidationError({
            "field": ["error"],
            "composite": {
                "field": ["error"],
            }
        })
    """

    def __init__(self, message, code=None, params=None):
        if not isinstance(message, dict):
            return super(NestedValidationError, self).__init__(message, code, params)

        super(ValidationError, self).__init__(message, code, params)

        self.error_dict = {}

        for field, messages in message.items():
            if not isinstance(messages, ValidationError):
                messages = NestedValidationError(messages)
            try:
                self.error_dict[field] = messages.error_list
            except AttributeError:
                self.error_dict[field] = messages.error_dict

    def update_error_dict(self, error_dict):
        if hasattr(self, "error_dict"):
            for field, errors in self.error_dict.items():
                holder = error_dict.setdefault(field, errors.__class__())
                (getattr(holder, "update", None) or holder.extend)(errors)
            return error_dict
        else:
            return super(NestedValidationError, self).update_error_dict(error_dict)

    def __iter__(self):
        if hasattr(self, "error_dict"):
            for field, errors in self.error_dict.items():
                errors = NestedValidationError(errors)
                if hasattr(errors, "error_dict"):
                    yield field, dict(errors)
                else:
                    yield field, list(errors)
        else:
            for error in super(NestedValidationError, self).__iter__():
                yield error
