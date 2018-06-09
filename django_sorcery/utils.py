# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import contextlib
import inspect


try:
    suppress = contextlib.suppress
except AttributeError:  # pragma: nocover
    from .compat import suppress  # noqa pragma: nocover


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
