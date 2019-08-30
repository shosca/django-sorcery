# -*- coding: utf-8 -*-
"""
Python compat utils
"""
import contextlib


@contextlib.contextmanager
def suppress(*exceptions):
    """
    Suppresses given exceptions, a backport from py3 contextlib.suppress
    """
    try:
        yield

    except exceptions:
        pass
