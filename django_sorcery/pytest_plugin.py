# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest

from .db.profiler import SQLAlchemyProfiler


@pytest.fixture(scope="function")
def sqlalchemy_profiler():
    with SQLAlchemyProfiler() as profiler:
        yield profiler
