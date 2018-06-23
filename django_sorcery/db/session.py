# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import event, orm

from . import signals


class SignallingSession(orm.Session):
    """
    A custom sqlalchemy session implementation that provides signals
    """

    def __init__(self, *args, **kwargs):
        super(SignallingSession, self).__init__(*args, **kwargs)

        @event.listens_for(self, "before_flush")
        def before_flush(session, flush_context, instances):
            signals.before_flush.send(session, flush_context=flush_context, instances=instances)

        @event.listens_for(self, "after_flush")
        def after_flush(session, flush_context):
            signals.after_flush.send(session, flush_context=flush_context)

    def query(self, *args, **kwargs):
        """
        Override to try to use the model.query_class
        """
        if len(args) == 1 and hasattr(args[0], "query_class") and args[0].query_class is not None:
            return args[0].query_class(*args, session=self, **kwargs)

        return super(SignallingSession, self).query(*args, **kwargs)

    def commit(self):
        """
        Flushes pending changes and commits the current transaction. If the transaction is the main transaction,
        triggers before and after commit signals.
        """
        is_main = self.transaction and (self.transaction._parent is None or not self.transaction.nested)

        if is_main:
            signals.before_commit.send(self)
            signals.before_scoped_commit.send(self)

        super(SignallingSession, self).commit()

        if is_main:
            signals.after_scoped_commit.send(self)
            signals.after_commit.send(self)

    def rollback(self):
        super(SignallingSession, self).rollback()

        if self.transaction and (self.transaction._parent is None or self.transaction.nested):
            signals.after_scoped_rollback.send(self)
            signals.after_rollback.send(self)
