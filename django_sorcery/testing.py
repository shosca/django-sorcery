# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import event
from sqlalchemy.engine import Engine

from .db import databases


class CommitException(BaseException):
    pass


class Transact(object):
    @staticmethod
    def _commit(connection, *args, **kwargs):
        raise CommitException("Commits are not allowed")

    def start(self):
        self.hook()

    def stop(self):
        self.end()
        self.unhook()

    def hook(self):
        if not event.contains(Engine, "commit", self._commit):
            event.listen(Engine, "commit", self._commit)
        if not event.contains(Engine, "commit_twophase", self._commit):
            event.listen(Engine, "commit_twophase", self._commit)

    def unhook(self):
        if event.contains(Engine, "commit", self._commit):
            event.remove(Engine, "commit", self._commit)
        if event.contains(Engine, "commit_twophase", self._commit):
            event.remove(Engine, "commit_twophase", self._commit)

    def end(self):
        databases.rollback()
        databases.remove()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
