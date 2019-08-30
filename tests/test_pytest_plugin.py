# -*- coding: utf-8 -*-

import pytest

from django_sorcery.pytest_plugin import sqlalchemy_profiler, transact  # noqa
from django_sorcery.testing import CommitException

from .testapp.models import Business, Owner, db


def test_profiler(sqlalchemy_profiler):  # noqa
    sqlalchemy_profiler.exclude = ["owner"]

    with sqlalchemy_profiler:
        db.add(Owner(first_name="foo", last_name="bar"))
        db.flush()

        assert sqlalchemy_profiler.stats["select"] == 0
        assert sqlalchemy_profiler.stats["insert"] == 0
        assert sqlalchemy_profiler.stats["duration"] >= 0

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


def test_transact(transact):  # noqa
    db.add(Owner(first_name="foo", last_name="bar"))
    db.flush()

    assert Owner.objects.count() == 1

    with pytest.raises(CommitException):
        db.commit()

    transact.stop()

    assert Owner.objects.count() == 0
