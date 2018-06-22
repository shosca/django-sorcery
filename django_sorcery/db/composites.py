# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

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

        columns = {k: v.copy() for k, v in vars(class_).items() if isinstance(v, sa.Column)}
        for k, c in columns.items():
            c.name = self.prefix + "_" + (c.name or k)
            c.key = "_" + c.name

        super(CompositeField, self).__init__(class_, *[i[1] for i in sorted(columns.items())], **kwargs)

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
        for k, v in zip(self._columns, args):
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classproperty
    def _columns(cls):
        return {k: v for k, v in vars(cls).items() if isinstance(v, sa.Column)}

    def __composite_values__(self):
        return tuple(getattr(self, i) for i in sorted(self._columns))

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
