# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.pytest_plugin import sqlalchemy_profiler  # noqa

from .models import Business, Owner, db


def test_profiler(sqlalchemy_profiler):  # noqa
    sqlalchemy_profiler.exclude = ["owner"]

    with sqlalchemy_profiler:
        db.add(Owner(first_name="foo", last_name="bar"))
        db.flush()

        assert sqlalchemy_profiler.stats["select"] == 0
        assert sqlalchemy_profiler.stats["insert"] == 0
        assert sqlalchemy_profiler.stats["duration"] > 0

    with sqlalchemy_profiler:
        b = Business(name="Google")
        db.add(b)
        db.flush()

        assert sqlalchemy_profiler.stats["select"] == 0
        assert sqlalchemy_profiler.stats["insert"] == 1
        assert sqlalchemy_profiler.stats["duration"] > 0

    with sqlalchemy_profiler:
        Business.query.filter_by(id=b.id).one()

        assert sqlalchemy_profiler.stats["select"] == 1
        assert sqlalchemy_profiler.stats["insert"] == 0
        assert sqlalchemy_profiler.stats["duration"] > 0

    db.rollback()
    db.remove()
