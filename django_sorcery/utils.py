# -*- coding: utf-8 -*-
"""
Some common utilities
"""
import contextlib
import inspect
import unicodedata

import six

from django.conf import settings


try:
    suppress = contextlib.suppress
except AttributeError:  # pragma: nocover
    from .compat import suppress  # noqa pragma: nocover


def sanitize_separators(value):
    """
    Sanitize a value according to the current decimal and
    thousand separator setting. Used with form field input.
    """
    if isinstance(value, six.string_types):
        parts = []
        decimal_separator = settings.DECIMAL_SEPARATOR
        if decimal_separator in value:
            value, decimals = value.split(decimal_separator, 1)
            parts.append(decimals)
        thousand_sep = settings.THOUSAND_SEPARATOR
        for replacement in {thousand_sep, unicodedata.normalize("NFKD", thousand_sep)}:
            value = value.replace(replacement, "")
        parts.append(value)
        value = ".".join(reversed(parts))
    return value


def get_args(func):
    """
    Returns the names of the positional arguments for composite model inspection
    """
    try:
        return list(inspect.signature(func).parameters.keys())[1:]

    except AttributeError:  # pragma: nocover
        return inspect.getargspec(func).args[1:]  # pylint:disable=deprecated-pragma pragma:nocover


def setdefaultattr(obj, name, value):
    """
    setdefault for object attributes
    """
    try:
        return getattr(obj, name)

    except AttributeError:
        setattr(obj, name, value)
    return getattr(obj, name)


def make_args(*args, **kwargs):
    """
    Useful for setting table args and mapper args on models and other things
    """
    return tuple(args) + (kwargs,)


def lower(value):
    """
    Convert value to lowercase if possible

    For example::

        >>> print(lower('HELLO'))
        hello
        >>> print(lower(5))
        5
    """
    try:
        return value.lower()
    except AttributeError:
        return value
