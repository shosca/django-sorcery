# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db import DEFAULT_DB_ALIAS
from django.utils.module_loading import import_string

from ..utils import suppress
from .sqlalchemy import SQLAlchemy
from .url import get_settings


class dbdict(dict):
    def get(self, alias=None, cls=SQLAlchemy, **kwargs):
        alias = alias or DEFAULT_DB_ALIAS
        if alias in self:
            return self[alias]

        with suppress(Exception):
            settings = get_settings(alias)
            cls = import_string(settings.get("SQLALCHEMY"))

        assert SQLAlchemy in cls.mro(), "'%s' needs to subclass from SQLAlchemy" % cls.__name__

        return self.setdefault(alias, cls(alias=alias, **kwargs))

    def update(self, *args, **kwargs):
        for arg in args:
            other = dict(arg)
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def __setitem__(self, alias, val):
        if alias in self:
            raise RuntimeError("Database alias `{alias}` has already been created".format(alias=alias))

        if val in self.values():
            raise RuntimeError("Database alias `{alias}` has already been created".format(alias=alias))

        if not isinstance(val, SQLAlchemy):
            raise RuntimeError("Database alias `{alias}` has wrong type".format(alias=alias))

        super(dbdict, self).__setitem__(alias, val)

    def rollback(self):
        for db in self.values():
            db.rollback()

    def flush(self):
        for db in self.values():
            db.flush()

    def commit(self):
        for db in self.values():
            db.commit()

    def remove(self):
        for db in self.values():
            db.remove()
