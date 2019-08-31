# -*- coding: utf-8 -*-
"""
pytest plugins
"""

import pytest

from .db.profiler import SQLAlchemyProfiler
from .testing import Transact


@pytest.fixture(scope="function")
def sqlalchemy_profiler():
    """
    pytest fixture for sqlalchemy profiler
    """
    with SQLAlchemyProfiler() as profiler:
        yield profiler


@pytest.fixture(scope="function")
def transact():
    """
    pytest transact fixture for sqlalchemy
    """
    with Transact() as t:
        yield t
