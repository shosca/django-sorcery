# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db.query import QueryProperty

from ..base import TestCase
from ..models import CompositePkModel, Owner, Vehicle, VehicleType, db


class TestQuery(TestCase):
    def setUp(self):
        super(TestQuery, self).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner 1"),
                Owner(id=2, first_name="Test 2", last_name="Owner 2"),
                Owner(id=3, first_name="Test 3", last_name="Owner 3"),
                Owner(id=4, first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.add(CompositePkModel(id=1, pk=1, active=True, name="Test-1-1"))
        db.flush()

    def tearDown(self):
        super(TestQuery, self).tearDown()
        db.rollback()
        db.remove()

    def test_query_get_regular(self):
        owner = Owner.query.get(1)
        self.assertEqual(owner.id, 1)

    def test_query_get_with_kwargs(self):
        owner = Owner.query.get(id=1)
        self.assertEqual(owner.id, 1)

    def test_query_get_with_kwargs_composite(self):
        obj = CompositePkModel.query.get(id=1, pk=1)
        self.assertEqual(obj.name, "Test-1-1")

    def test_query_get_with_kwargs_tuple(self):
        obj = CompositePkModel.query.get((1, 1))
        self.assertEqual(obj.name, "Test-1-1")


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
            ("<QueryProperty db=<SQLAlchemy engine=sqlite://>, model='Vehicle'> object has no attribute 'dummy'",),
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
