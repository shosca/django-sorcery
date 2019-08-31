# -*- coding: utf-8 -*-
"""
sqlalchemy query related things
"""
from collections import namedtuple
from functools import partial

import six

import sqlalchemy as sa
import sqlalchemy.orm  # noqa

from django.db.models.constants import LOOKUP_SEP

from ..utils import lower
from . import meta


Operation = namedtuple("Operation", ["name", "args", "kwargs"])

# todo add transforms support - e.g. column__date__gt
LOOKUP_TO_EXPRESSION = {
    "contains": lambda column, value: column.contains(value),
    # "date"
    # "day"
    "endswith": lambda column, value: column.endswith(value),
    "exact": lambda column, value: column == value,
    "gt": lambda column, value: column > value,
    "gte": lambda column, value: column >= value,
    # "hour"
    "icontains": lambda column, value: sa.func.lower(column).contains(lower(value)),
    "iendswith": lambda column, value: sa.func.lower(column).endswith(lower(value)),
    "iexact": lambda column, value: sa.func.lower(column) == lower(value),
    "iin": lambda column, value: sa.func.lower(column).in_(lower(i) for i in value),
    "in": lambda column, value: column.in_(value),
    # "iregex"
    "isnull": lambda column, value: column == None if value else column != None,  # noqa
    "istartswith": lambda column, value: sa.func.lower(column).startswith(lower(value)),
    "lt": lambda column, value: column < value,
    "lte": lambda column, value: column <= value,
    # "minute"
    # "month"
    # "quarter"
    "range": lambda column, value: column.between(*value),
    # "regex"
    # "second"
    "startswith": lambda column, value: column.startswith(value),
    # "time"
    # "week"
    # "week_day"
    # "year"
}


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
                return super().get(pk)

            return None

        return super().get(*args, **kwargs)

    def order_by(self, *criterion):
        """
        Standard SQLAlchemy ordering plus django-like expressions can be provided:

        For example::

            MyModel.objects.order_by("-id")
            MyModel.objects.order_by("name")
        """
        if len(self._entities) == 1 and all(isinstance(criteria, six.string_types) for criteria in criterion):
            info = meta.model_info(self._entity_zero())
            new_criterion = []
            for criteria in criterion:
                direction = sa.asc
                if criteria[0] == "-":
                    criteria = criteria[1:]
                    direction = sa.desc
                elif criteria[0] == "+":
                    criteria = criteria[1:]

                col_info = info.primary_keys.get(criteria) or info.properties.get(criteria)
                new_criterion.append(direction(col_info.attribute))

            criterion = new_criterion

        return super().order_by(*criterion)

    def filter(self, *args, **kwargs):
        """
        Standard SQLAlchemy filtering plus django-like expressions can be provided:

        For example::

            MyModel.objects.filter(MyModel.id == 5)
            MyModel.objects.filter(id=5)
            MyModel.objects.filter(id__gte=5)
            MyModel.objects.filter(relation__id__gte=5)
        """
        args = args + tuple(self._lookup_to_expression(k, v) for k, v in kwargs.items())
        return super().filter(*args)

    def _lookup_to_expression(self, lookup, value):
        parts = lookup.split(LOOKUP_SEP)
        info = meta.model_info(self._only_full_mapper_zero("get"))

        props = dict(info.column_properties)
        lhs = None

        for i, part in enumerate(parts, 1):
            is_last = i == len(parts)

            if part in LOOKUP_TO_EXPRESSION:
                return LOOKUP_TO_EXPRESSION[part](lhs, value)

            elif part in info.relationships:
                rel = info.relationships[part]

                # directly comparing to model
                # e.g. .filter(relation=instance)
                if is_last:
                    return rel.attribute == value

                lhs = rel.related_model
                props = dict(meta.model_info(lhs).column_properties)

            elif part in info.composites:
                comp = info.composites[part]
                props = comp.properties

                # directly comparing to composite
                # e.g. .filter(composite=instance)
                if is_last:
                    return comp.attribute == value

            else:
                lhs = props[part].attribute

        return lhs == value


class QueryProperty(object):
    """
    A property class that returns a session scoped query object against the class when called.
    Used by the ``SQLAlchemy.queryproperty``

    For example::

        >>> class MyView(object):
        ...     queryset = db.queryproperty(FooModel)

    You can even pass default filtering criteria if needed::

        >>> class MyView(object):
        ...     queryset = db.queryproperty(FooModel, to_be_deleted=False)

    In addition this pattern can be used to implement Django's ORM style model managers::

        >>> class UserModel(db.Model):
        ...     id = db.Column(db.Integer(), primary_key=True)
        ...     username = db.Column(db.String())
        ...     is_active = db.Column(db.Boolean())
        ...
        ...     active = db.queryproperty(is_active=True)

    That can be used directly::

        >>> UserModel.metadata.create_all(bind=db.engine)
        >>> db.add_all([
        ...     UserModel(id=1, username='foo', is_active=False),
        ...     UserModel(id=2, username='bar', is_active=True),
        ... ])
        >>> db.flush()

        >>> UserModel.objects.all()
        [UserModel(id=1, is_active=False, username='foo'), UserModel(id=2, is_active=True, username='bar')]
        >>> UserModel.active.all()
        [UserModel(id=2, is_active=True, username='bar')]

    This pattern is very useful when combined with Django style views::

        >>> class MyView(object):
        ...     queryset = UserModel.active

        >>> MyView().queryset.all()
        [UserModel(id=2, is_active=True, username='bar')]

    Additional filters/options can be applied as well::

        >>> class MyView(object):
        ...     queryset = UserModel.active.filter(UserModel.username == 'test')

        >>> MyView().queryset.all()
        []
    """

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
