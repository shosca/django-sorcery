# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import functools

import six


class TransactionContext(object):
    """
    Transaction context manager for maintaining a transaction or savepoint
    """

    def __init__(self, *dbs, **kwargs):
        self.dbs = dbs
        self.savepoint = kwargs.get("savepoint", True)
        self.transactions = None

    def __call__(self, func, *args, **kwargs):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapped

    def __enter__(self):
        self.transactions = [db.begin(subtransactions=True, nested=self.savepoint) for db in self.dbs]
        return self

    def __exit__(self, exception_type, value, tb=None):
        if exception_type is None:
            try:
                for transaction in self.transactions:
                    transaction.session.flush()
            except Exception as ex:
                exception_type = ex.__class__
                value = ex
                tb = getattr(ex, "__traceback__", None)
        [transaction.__exit__(exception_type, value, tb) for transaction in self.transactions]
        self.transactions = None
        if value:
            six.reraise(exception_type, value, tb or value.__traceback__)
