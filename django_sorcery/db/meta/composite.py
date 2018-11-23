# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict

import six

import sqlalchemy as sa

from ...utils import get_args
from .column import column_info
from .model import model_info_meta


class composite_info(six.with_metaclass(model_info_meta)):
    """
    A helper class that makes sqlalchemy composite model inspection easier
    """

    __slots__ = ("prop", "properties", "_field_names")

    def __init__(self, composite):
        self._field_names = set()
        self.prop = composite.prop

        attrs = list(sorted([k for k, v in vars(self.prop.composite_class).items() if isinstance(v, sa.Column)]))
        if not attrs:
            attrs = get_args(self.prop.composite_class.__init__)

        self.properties = OrderedDict()
        for attr, prop, col in zip(attrs, self.prop.props, self.prop.columns):
            self.properties[attr] = column_info(col, prop, self)

    @property
    def field_names(self):
        if not self._field_names:
            self._field_names.update(self.properties.keys())

            self._field_names = [attr for attr in self._field_names if not attr.startswith("_")]

        return self._field_names

    @property
    def related_model(self):
        return self.prop.composite_class

    def __repr__(self):
        reprs = [
            "<composite_info({!s}, {!s}.{!s})>".format(
                self.related_model.__name__, self.prop.parent.class_.__name__, self.prop.key
            )
        ]
        reprs.extend("    " + repr(i) for _, i in sorted(self.properties.items()))
        return "\n".join(reprs)
