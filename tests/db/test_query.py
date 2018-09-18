# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db.query import QueryProperty

from ..base import TestCase
from ..testapp.models import CompositePkModel, Owner, Vehicle, VehicleType, db


class TestQuery(TestCase):
    def setUp(self):
        super(TestQuery, self).setUp()
        owner = Owner(first_name="Test 1", last_name="Owner 1")
        db.add(owner)
        db.add(CompositePkModel(id=1, pk=1, active=True, name="Test-1-1"))
        db.flush()
        self.owner_id = owner.id
        db.expire_all()

    def tearDown(self):
        super(TestQuery, self).tearDown()
        db.rollback()
        db.remove()

    def test_query_get_regular(self):
        owner = Owner.query.get(self.owner_id)
        self.assertEqual(owner.id, self.owner_id)

    def test_query_get_with_kwargs(self):
        owner = Owner.query.get(id=self.owner_id)
        self.assertEqual(owner.id, self.owner_id)

    def test_query_get_with_kwargs_composite(self):
        obj = CompositePkModel.query.get(id=1, pk=1)
        self.assertEqual(obj.name, "Test-1-1")

    def test_query_get_with_kwargs_tuple(self):
        obj = CompositePkModel.query.get((1, 1))
        self.assertEqual(obj.name, "Test-1-1")

    def test_query_kwarg_none(self):
        self.assertIsNone(CompositePkModel.query.get(id=1))


class TestQueryProperty(TestCase):
    def setUp(self):
        super(TestQueryProperty, self).setUp()
        db.add_all(
            [
                Vehicle(name="used", is_used=True, type=VehicleType.car),
                Vehicle(name="new", is_used=False, type=VehicleType.car),
            ]
        )
        db.flush()

    def test_options_filter_and_filter_by(self):
        class Dummy(object):
            vehicles = QueryProperty(db, Vehicle).options(db.joinedload(Vehicle.owner))
            used_vehicles = QueryProperty(db, Vehicle, Vehicle.is_used.is_(True))
            new_vehicles = QueryProperty(db, Vehicle, is_used=False)

        dummy = Dummy()

        self.assertEqual(dummy.vehicles.count(), 2)
        self.assertEqual(dummy.used_vehicles.count(), 1)
        self.assertEqual(dummy.new_vehicles.count(), 1)

    def test_bad_attr(self):

        with self.assertRaises(AttributeError) as ctx:
            QueryProperty(db, Vehicle).dummy(db.joinedload(Vehicle.owner))

        self.assertEqual(
            ctx.exception.args,
            (
                "<QueryProperty db=<SQLAlchemy engine=postgresql://postgres@localhost/test>, model='Vehicle'> object has no attribute 'dummy'",
            ),
        )

    def test_no_model(self):
        class Dummy(object):
            vehicles = QueryProperty(db, None)

        with self.assertRaises(AttributeError) as ctx:
            Dummy.vehicles

        self.assertEqual(
            ctx.exception.args,
            (
                "Cannot access QueryProperty when not bound to a model. You can explicitly instantiate descriptor with "
                "model class - `db.queryproperty(Model)`.",
            ),
        )

    def test_stupid(self):

        qp = QueryProperty(db, Vehicle)

        class Dummy(object):
            vehicles = qp

        qp.model = object

        self.assertIsNone(Dummy.vehicles)
