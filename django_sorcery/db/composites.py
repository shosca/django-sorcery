# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict

import sqlalchemy as sa
from sqlalchemy.orm import CompositeProperty
from sqlalchemy.util.langhelpers import classproperty

from .meta import column_info
from .mixins import CleanMixin


class CompositeField(CompositeProperty):
    """
    Composite field which understands composite objects with builtin columns.

    See :py:class:`.BaseComposite` for examples.
    """

    def __init__(self, class_, **kwargs):
        self.prefix = kwargs.pop("prefix", None)
        self.random_prefix = class_.__name__ + str(id(self))
        if not self.prefix:
            self.prefix = self.random_prefix

        columns = OrderedDict()
        for k, c in class_._columns.items():
            columns[k] = c = c.copy()
            c.name = self.prefix + "_" + (c.name or k)
            c.key = "_" + c.name

        super(CompositeField, self).__init__(class_, *list(columns.values()), **kwargs)

    def instrument_class(self, mapper):
        if self.prefix == self.random_prefix:
            for c in self.attrs:
                c.name = self.key + c.name.replace(self.random_prefix, "")
                c.key = "_" + self.key + c.key.replace(self.random_prefix, "")[1:]
        return super(CompositeField, self).instrument_class(mapper)


class BaseComposite(CleanMixin):
    """
    Base class for creating composite classes which :py:class:`.CompositeField` will understand

    For example::

        class MyComposite(object):
            foo = db.Column(db.Integer())
            bar = db.Column(db.Integer())

        class MyModel(db.Model):
            test = db.CompositeField(MyComposite)
            # both test_foo and test_bar columns will be added to model
            # their instrumented properties will be _test_foo and _test_bar
    """

    def __init__(self, *args, **kwargs):
        for k in self._columns:
            setattr(self, k, None)
        for k, v in zip(self._columns, args):
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classproperty
    def _columns(cls):
        return OrderedDict([(k, v) for k, v in sorted(vars(cls).items()) if isinstance(v, sa.Column)])

    def __composite_values__(self):
        return tuple(getattr(self, i) for i in self._columns)

    def _get_properties_for_validation(self):
        """
        Return all composite attributes
        """
        return {k: column_info(None, v) for k, v in self._columns.items()}

    def _get_nested_objects_for_validation(self):
        """
        Dont return any fields since composites cant be nested
        """
        return []

    def as_dict(self):
        """
        Serializer composite to a dictionary
        """
        return OrderedDict([(k, getattr(self, k)) for k in self._columns])

    def __repr__(self):
        return "".join(
            [
                self.__class__.__name__,
                "(",
                ", ".join("{}={!r}".format(k, v) for k, v in self.as_dict().items() if v),
                ")",
            ]
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__composite_values__() == other.__composite_values__()

    def __bool__(self):
        return any(vars(self).values())

    __nonzero__ = __bool__
