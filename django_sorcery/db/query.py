# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple
from functools import partial

import sqlalchemy as sa
import sqlalchemy.orm  # noqa

from . import meta


Operation = namedtuple("Operation", ["name", "args", "kwargs"])


class Query(sa.orm.Query):
    """
    A customized sqlalchemy query
    """

    def get(self, *args, **kwargs):
        """
        Return an instance based on the given primary key identifier, either as args or
        kwargs for composite keys. If no instance is found, returns ``None``.
        """
        if kwargs:
            mapper = self._only_full_mapper_zero("get")
            pk = meta.model_info(mapper).primary_keys_from_dict(kwargs)

            if pk is not None:
                return super(Query, self).get(pk)

            return None

        return super(Query, self).get(*args, **kwargs)


class QueryProperty(object):
    def __init__(self, db, model=None, *args, **kwargs):
        self.db = db
        self.model = model

        self.ops = []
        if args:
            self.ops.append(Operation("filter", args, {}))
        if kwargs:
            self.ops.append(Operation("filter_by", (), kwargs))

        # sanity checks
        if self.model:
            assert isinstance(self.model, type) and issubclass(
                self.model, self.db.Model
            ), "{!r} is not SQLAlchemy model subclassing {!r}".format(self, model, self.db.Model)

    def __repr__(self):
        return "<{} db={!r}, model={!r}>".format(self.__class__.__name__, self.db, self.model.__name__)

    def _with_op(self, name, *args, **kwargs):
        prop = type(self)(self.db, self.model)
        prop.ops += self.ops
        prop.ops.append(Operation(name, args, kwargs))
        return prop

    def __getattr__(self, item):
        if not hasattr(getattr(self.model, "query_class", Query), item):
            raise AttributeError("{!r} object has no attribute {!r}".format(self, item))

        return partial(self._with_op, item)

    def __get__(self, instance, owner):
        model = self.model or (owner if issubclass(owner, self.db.Model) else None)

        if not model:
            raise AttributeError(
                "Cannot access {} when not bound to a model. "
                "You can explicitly instantiate descriptor with model class - `db.queryproperty(Model)`."
                "".format(self.__class__.__name__)
            )

        try:
            mapper = sa.orm.class_mapper(model)
        except sa.orm.exc.UnmappedClassError:
            # when subclass references unmapped base class descriptor
            return

        query_class = getattr(model, "query_class", None) or self.db.query_class
        return self._apply_ops(query_class(mapper, session=self.db))

    def _apply_ops(self, query):
        for op in self.ops:
            query = getattr(query, op.name)(*op.args, **op.kwargs)
        return query
