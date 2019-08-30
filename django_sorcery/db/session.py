# -*- coding: utf-8 -*-
"""
sqlalchemy session related things
"""
from itertools import chain

from sqlalchemy import event, orm

from ..utils import setdefaultattr
from . import signals


def before_flush(session, flush_context, instances):
    signals.before_flush.send(session, flush_context=flush_context, instances=instances)


def after_flush(session, flush_context):
    signals.after_flush.send(session, flush_context=flush_context)


def before_commit(session):
    if session.transaction and (session.transaction._parent is None or not session.transaction.nested):
        signals.before_commit.send(session)
        signals.before_scoped_commit.send(session)


def after_commit(session):
    if session.transaction and (session.transaction._parent is None or not session.transaction.nested):
        signals.after_scoped_commit.send(session)
        signals.after_commit.send(session)
        setdefaultattr(session, "models_committed", set()).clear()
        setdefaultattr(session, "models_deleted", set()).clear()


def after_rollback(session):
    if session.transaction and (session.transaction._parent is None or session.transaction.nested):
        signals.after_scoped_rollback.send(session)
        signals.after_rollback.send(session)
        setdefaultattr(session, "models_committed", set()).clear()
        setdefaultattr(session, "models_deleted", set()).clear()


def record_models(session, flush_context=None, instances=None):
    setdefaultattr(session, "models_committed", set())
    setdefaultattr(session, "models_deleted", set())

    for instance in chain(session.new, session.dirty):
        session.models_committed.add(instance)

    for instance in session.deleted:
        session.models_deleted.add(instance)
        if instance in session.models_committed:
            session.models_committed.remove(instance)


class SignallingSession(orm.Session):
    """
    A custom sqlalchemy session implementation that provides signals
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        event.listen(self, "after_flush", record_models)

        event.listen(self, "before_flush", before_flush)
        event.listen(self, "after_flush", after_flush)
        event.listen(self, "before_commit", before_commit)
        event.listen(self, "after_commit", after_commit)
        event.listen(self, "after_rollback", after_rollback)

    def query(self, *args, **kwargs):
        """
        Override to try to use the model.query_class
        """
        if len(args) == 1 and hasattr(args[0], "query_class") and args[0].query_class is not None:
            return args[0].query_class(*args, session=self, **kwargs)

        return super().query(*args, **kwargs)
