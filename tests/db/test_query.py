# -*- coding: utf-8 -*-

from django_sorcery.db.query import QueryProperty

from ..base import TestCase
from ..testapp.models import CompositePkModel, Owner, Point, Vehicle, VehicleType, Vertex, db


class TestQuery(TestCase):
    def setUp(self):
        super().setUp()
        self.owner = Owner(first_name="Test 1", last_name="Owner 1")
        vehicle = Vehicle(name="used", is_used=True, type=VehicleType.car, owner=self.owner)
        vertex = Vertex(start=Point(x=1, y=2), end=Point(x=3, y=4))
        db.add(self.owner)
        db.add(vehicle)
        db.add(vertex)
        db.add(CompositePkModel(id=1, pk=1, active=True, name="Test-1-1"))
        db.flush()
        self.owner_id = self.owner.id
        self.vehicle_id = vehicle.id
        self.vertex_id = vertex.pk
        db.expire_all()

    def tearDown(self):
        super().tearDown()
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

    def test_query_order_by_django_style(self):
        owner1 = Owner(first_name="AAAA 1", last_name="AAAA 1")
        owner2 = Owner(first_name="ZZZZ 2", last_name="ZZZZ 1")
        db.add_all([owner1, owner2])
        db.flush()

        owners = Owner.objects.order_by("-first_name").all()

        self.assertListEqual([owner2, self.owner, owner1], owners)

        owners = Owner.objects.order_by("+first_name", "-last_name").all()
        self.assertListEqual([owner1, self.owner, owner2], owners)

    def test_query_filter_default_equality(self):
        obj = Owner.query.filter(first_name="Test 1").first()
        self.assertEqual(obj.id, self.owner_id)

    def test_query_filter_lookup(self):
        obj = Owner.query.filter(first_name__istartswith="test").first()
        self.assertEqual(obj.id, self.owner_id)

    def test_query_filter_relation_with_lookup(self):
        obj = Vehicle.query.filter(owner__first_name__istartswith="test").first()
        self.assertEqual(obj.id, self.vehicle_id)

    def test_query_filter_relation_with_instance(self):
        obj = Vehicle.query.filter(owner=Owner.objects.get(id=self.owner_id)).first()
        self.assertEqual(obj.id, self.vehicle_id)

    def test_query_filter_composite_with_lookup(self):
        obj = Vertex.query.filter(start__x__gte=1).first()
        self.assertEqual(obj.pk, self.vertex_id)

    def test_query_filter_composite_with_instance(self):
        obj = Vertex.query.filter(start=Vertex.query.get(self.vertex_id).start).first()
        self.assertEqual(obj.pk, self.vertex_id)


class TestQueryProperty(TestCase):
    def setUp(self):
        super().setUp()
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
                "<QueryProperty db=<SQLAlchemy engine=postgresql://postgres@localhost/test>, model='Vehicle'> "
                "object has no attribute 'dummy'",
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
