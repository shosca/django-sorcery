"""Exceptions."""

from django.core.exceptions import ValidationError


class NestedValidationError(ValidationError):
    """Django Validation error except which allows nested errors.

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
        if isinstance(message, dict):
            self.error_dict = {}

            for field, messages in message.items():
                _messages = messages
                if not isinstance(messages, ValidationError):
                    _messages = NestedValidationError(messages)
                try:
                    self.error_dict[field] = _messages.error_list
                except AttributeError:
                    self.error_dict[field] = _messages.error_dict

        elif isinstance(message, list):
            self.error_list = []

            for m in message:
                _m = m
                if not isinstance(m, ValidationError):
                    _m = NestedValidationError(m)
                try:
                    self.error_list.extend(_m.error_list)
                except AttributeError:
                    self.error_list.append(_m)

        elif isinstance(message, NestedValidationError):
            self.__dict__.update(vars(message))

        else:
            super().__init__(message, code, params)

    def update_error_dict(self, error_dict):
        if not hasattr(self, "error_dict"):
            return super().update_error_dict(error_dict)

        for field, errors in self.error_dict.items():
            holder = error_dict.setdefault(field, errors.__class__())
            (getattr(holder, "update", None) or holder.extend)(errors)
        return error_dict

    def __iter__(self):
        if hasattr(self, "code"):
            yield from super().__iter__()

        elif hasattr(self, "error_dict"):
            for field, errors in self.error_dict.items():
                errors = NestedValidationError(errors)
                if hasattr(errors, "error_dict"):
                    yield field, dict(errors)
                else:
                    yield field, list(errors)

        else:
            for errors in self.error_list:
                errors = NestedValidationError(errors)
                if hasattr(errors, "error_dict"):
                    yield dict(errors)
                else:
                    yield from errors

    def __repr__(self):
        return "Nested" + super().__repr__()
