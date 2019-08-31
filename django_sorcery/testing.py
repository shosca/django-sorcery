# -*- coding: utf-8 -*-
"""
Testing utilities
"""

from sqlalchemy import event
from sqlalchemy.engine import Engine

from .db import databases


class CommitException(BaseException):
    """
    Raised when a commit happens during testing
    """


class Transact(object):
    """
    Helper context manager for handling transactions during tests. Perfect for testing a single
    unit of work.

    For testing sqlalchemy apps the common pattern is to usually, start a transaction or savepoint,
    run the tests and once the test is done rollback. Additionally it also prevents commits
    to the database so that every test gets the same database state.
    """

    @staticmethod
    def _commit(connection, *args, **kwargs):
        raise CommitException("Commits are not allowed")

    def start(self):
        """
        Starts transaction management and hooks commit events
        """
        self.hook()

    def stop(self):
        """
        Stops transaction management, rolls back transactions and unhooks commit events
        """
        self.end()
        self.unhook()

    def hook(self):
        """
        Hooks commit events to prevent commits
        """
        if not event.contains(Engine, "commit", self._commit):
            event.listen(Engine, "commit", self._commit)
        if not event.contains(Engine, "commit_twophase", self._commit):
            event.listen(Engine, "commit_twophase", self._commit)

    def unhook(self):
        """
        Unhooks commit events
        """
        if event.contains(Engine, "commit", self._commit):
            event.remove(Engine, "commit", self._commit)
        if event.contains(Engine, "commit_twophase", self._commit):
            event.remove(Engine, "commit_twophase", self._commit)

    def end(self):
        """
        Rolls back transaction and removes session
        """
        databases.rollback()
        databases.remove()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
