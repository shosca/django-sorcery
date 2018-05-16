# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
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
