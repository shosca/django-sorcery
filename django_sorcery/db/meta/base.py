# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa


class model_info_meta(type):
    _registry = {}

    def __call__(cls, model, *args, **kwargs):
        if isinstance(model, sa.orm.Mapper):
            model = model.class_

        if model not in cls._registry:
            instance = super(model_info_meta, cls).__call__(model, *args, **kwargs)
            cls._registry[model] = instance

        return cls._registry[model]
