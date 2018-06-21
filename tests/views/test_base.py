# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from django_sorcery.views.base import SQLAlchemyMixin

from ..models import ClassicModel, Owner, db


class TestBaseView(TestCase):
    def test_get_model(self):
        class DummyView(SQLAlchemyMixin):
            model = None

        with self.assertRaises(ImproperlyConfigured):
            DummyView.get_model()

    def test_get_queryset(self):
        class DummyView(SQLAlchemyMixin):
            model = Owner
            queryset = Owner.query

        view = DummyView()

        query = view.get_queryset()

        self.assertIsInstance(query, sa.orm.Query)
        self.assertEqual(query._only_entity_zero().class_, Owner)

    def test_get_queryset_from_model_only(self):
        class DummyView(SQLAlchemyMixin):
            model = Owner

        view = DummyView()

        query = view.get_queryset()

        self.assertIsInstance(query, sa.orm.Query)
        self.assertEqual(query._only_entity_zero().class_, Owner)

    def test_get_queryset_from_session(self):
        class DummyView(SQLAlchemyMixin):
            model = Owner
            session = db

        view = DummyView()

        query = view.get_queryset()

        self.assertIsInstance(query, sa.orm.Query)
        self.assertEqual(query._only_entity_zero().class_, Owner)

    def test_get_queryset_with_options(self):
        class DummyViewWithOptions(SQLAlchemyMixin):
            model = Owner
            session = db
            query_options = [sa.orm.noload("*")]

        view = DummyViewWithOptions()

        query = view.get_queryset()

        self.assertIsInstance(query, sa.orm.Query)
        self.assertEqual(query._only_entity_zero().class_, Owner)
        self.assertEqual(len(query._with_options), 1)

    def test_get_queryset_fail(self):
        class DummyObject(object):
            pass

        class DummyViewFail(SQLAlchemyMixin):
            model = DummyObject

        view = DummyViewFail()

        with self.assertRaises(ImproperlyConfigured) as ctx:
            view.get_queryset()

        self.assertEqual(
            str(ctx.exception),
            "DummyViewFail is missing a QuerySet. Define DummyViewFail.model and DummyViewFail.session, "
            "DummyViewFail.queryset, or override DummyViewFail.get_queryset().",
        )

    def test_get_queryset_classical_mapping(self):
        class ClassicModelView(SQLAlchemyMixin):
            model = ClassicModel
            session = db

        view = ClassicModelView()

        query = view.get_queryset()

        self.assertIsInstance(query, sa.orm.Query)
        self.assertEqual(query._only_entity_zero().class_, ClassicModel)

    def test_get_session(self):
        class OwnerView(SQLAlchemyMixin):
            model = Owner
            queryset = Owner.query

        view = OwnerView()

        view.get_session()

        self.assertEqual(view.session, db)
