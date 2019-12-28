# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest

from django.core.exceptions import ImproperlyConfigured

from django_sorcery.db import FromCache
from django_sorcery.pytest_plugin import sqlalchemy_profiler  # noqa

from ..testapp.models import CachedModel, CachedReference, OtherCachedModel, Owner, UnCachedModel, cache, db


def test_without_region():  # noqa

    with pytest.raises(ImproperlyConfigured):
        Owner.objects.options(FromCache(None)).filter_by(first_name="foo").one_or_none()


def test_from_cache_option(sqlalchemy_profiler):  # noqa
    db.add(Owner(first_name="foo", last_name="bar"))
    db.flush()
    db.expire_all()
    cache.cache.clear()

    with sqlalchemy_profiler:
        Owner.objects.options(FromCache(cache)).filter_by(first_name="foo").one_or_none()

        assert sqlalchemy_profiler.stats["select"] == 1
        assert len(cache.cache) == 1

    with sqlalchemy_profiler:
        Owner.objects.options(FromCache(cache)).filter_by(first_name="foo").one_or_none()

        assert sqlalchemy_profiler.stats["select"] == 0
        assert len(cache.cache) == 1

    FromCache(cache).invalidate(Owner.objects.options(FromCache(cache)).filter_by(first_name="foo"))
    assert len(cache.cache) == 0

    with sqlalchemy_profiler:
        Owner.objects.options(FromCache(cache)).filter_by(first_name="foo").one_or_none()
        assert sqlalchemy_profiler.stats["select"] == 1
        assert len(cache.cache) == 1

    Owner.objects.options(FromCache(cache)).filter_by(first_name="foo").invalidate()
    assert len(cache.cache) == 0


def test_model_cache_option(sqlalchemy_profiler):  # noqa
    instance = UnCachedModel(
        cached=CachedModel(name="cached"),
        other_cached=[OtherCachedModel(name="other cached 1"), OtherCachedModel(name="other cached 2")],
        references=[CachedReference(name="ref1"), CachedReference(name="ref2")],
    )

    db.add(instance)
    db.flush()
    pk = instance.pk
    cached_pk = instance.cached.pk
    db.expire_all()
    cache.cache.clear()

    with sqlalchemy_profiler:
        instance = CachedModel.objects.get(cached_pk)
        assert sqlalchemy_profiler.stats["select"] == 1
        assert len(cache.cache) == 1

    with sqlalchemy_profiler:
        instance = CachedModel.objects.get(cached_pk)
        assert sqlalchemy_profiler.stats["select"] == 0
        assert len(cache.cache) == 1

    instance = UnCachedModel.objects.filter_by(pk=pk).one()
    db.refresh(instance)
    with sqlalchemy_profiler:
        assert instance.cached.pk == cached_pk
        assert sqlalchemy_profiler.stats["select"] == 0
        assert len(cache.cache) == 1  # many-to-one cached

    instance = UnCachedModel.objects.filter_by(pk=pk).one()
    db.refresh(instance)
    with sqlalchemy_profiler:
        assert len(instance.other_cached) == 2
        assert sqlalchemy_profiler.stats["select"] == 1
        assert len(cache.cache) == 1  # one-to-many not cached

    instance = UnCachedModel.objects.filter_by(pk=pk).one()
    db.refresh(instance)
    with sqlalchemy_profiler:
        assert len(instance.references) == 2
        assert sqlalchemy_profiler.stats["select"] == 1
        assert len(cache.cache) == 1  # many-to-many not cached
