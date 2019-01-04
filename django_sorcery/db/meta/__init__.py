# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import sys
import types


class lazy_module(types.ModuleType):
    def __init__(self, name, old_module, origins):
        super(lazy_module, self).__init__(name)
        self.origins = origins or {}
        self.__dict__.update(
            {
                "__file__": old_module.__file__,
                "__package__": old_module.__package__,
                "__path__": old_module.__path__,
                "__doc__": old_module.__doc__,
            }
        )

    def __getattr__(self, name):
        if name in self.origins:
            module = __import__(self.__name__ + "." + self.origins[name], None, None, [name])
            return getattr(module, name)
        return types.ModuleType.__getattribute__(self, name)


old_module = sys.modules[__name__]
sys.modules[__name__] = lazy_module(
    __name__,
    old_module,
    {"model_info": "model", "Identity": "model", "relation_info": "relations", "column_info": "column"},
)
