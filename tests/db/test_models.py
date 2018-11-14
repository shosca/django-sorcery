# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import datetime
from decimal import Decimal

import pytz

from django.core.exceptions import ValidationError

from django_sorcery.db import models
from django_sorcery.utils import make_args

from ..base import TestCase
from ..testapp.models import (
    Address,
    AllKindsOfFields,
    Business,
    CompositePkModel,
    DummyEnum,
    ModelOne,
    ModelTwo,
    Option,
    Owner,
    Part,
    SelectedAutoCoerce,
    Vehicle,
    VehicleType,
    db,
)


class TestModels(TestCase):
    def test_model_repr(self):
        owner = Owner(id=1, first_name="Meaty", last_name="McManPipes")

        self.assertEqual(repr(owner), "Owner(id=1, first_name='Meaty', last_name='McManPipes')")

    def test_simple_repr(self):

        vehicle = Vehicle()
        self.assertEqual(models.simple_repr(vehicle), "Vehicle(id=None)")

        vehicle.name = "Test"
        self.assertEqual(models.simple_repr(vehicle), "Vehicle(id=None, name='Test')")

        vehicle.id = 1234
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id=1234, name='Test')")

        vehicle.id = "abc"
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id='abc', name='Test')")

        vehicle.id = b"abc"
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id='abc', name='Test')")

    def test_primary_keys(self):
        pks = models.get_primary_keys(Vehicle, {"pk": 1234})
        self.assertIsNone(pks)

    def test_primary_keys_composite(self):
        pks = models.get_primary_keys(CompositePkModel, {"id": 4321, "pk": 1234})
        self.assertEqual(pks, (4321, 1234))

    def test_primary_keys_composite_missing(self):
        pks = models.get_primary_keys(CompositePkModel, {"pk": 1234})
        self.assertIsNone(pks)

    def test_primary_keys_from_instance(self):
        vehicle = Vehicle(id=1234)

        pks = models.get_primary_keys_from_instance(vehicle)

        self.assertEqual(pks, 1234)

    def test_primary_keys_from_instance_composite(self):
        vehicle = CompositePkModel(id=1234, pk=4321)

        pks = models.get_primary_keys_from_instance(vehicle)

        self.assertEqual(pks, {"id": 1234, "pk": 4321})

    def test_primary_keys_from_instance_with_none(self):
        self.assertIsNone(models.get_primary_keys_from_instance(None))

    def test_model_to_dict(self):
        vehicle = Vehicle(
            id=1,
            name="vehicle",
            owner=Owner(id=2, first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(id=3, name="option 1"), Option(id=4, name="option 2")],
            parts=[Part(id=5, name="part 1"), Part(id=6, name="part 2")],
        )

        self.assertEqual(
            {
                "created_at": None,
                "is_used": True,
                "name": "vehicle",
                "options": [3, 4],
                "owner": 2,
                "paint": "red",
                "parts": [5, 6],
                "type": VehicleType.car,
            },
            models.model_to_dict(vehicle),
        )

    def test_model_to_dict_exclude(self):
        vehicle = Vehicle(
            id=1,
            name="vehicle",
            owner=Owner(id=2, first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(id=3, name="option 1"), Option(id=4, name="option 2")],
            parts=[Part(id=5, name="part 1"), Part(id=6, name="part 2")],
        )

        self.assertEqual(
            {
                "created_at": None,
                "is_used": True,
                "name": "vehicle",
                "options": [3, 4],
                "paint": "red",
                "parts": [5, 6],
            },
            models.model_to_dict(vehicle, exclude=["type", "owner"]),
        )

    def test_model_to_dict_fields(self):
        vehicle = Vehicle(
            name="vehicle",
            owner=Owner(first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(name="option 1"), Option(name="option 2")],
            parts=[Part(name="part 1"), Part(name="part 2")],
        )

        self.assertEqual(
            {"is_used": True, "name": "vehicle", "paint": "red"},
            models.model_to_dict(vehicle, fields=["name", "is_used", "paint"]),
        )

    def test_model_to_dict_private_relation(self):
        obj = ModelTwo(pk=2, name="two", _model_one=ModelOne(pk=1, name="one"))

        self.assertEqual({"name": "two"}, models.model_to_dict(obj))

    def test_serialize_none(self):
        self.assertIsNone(models.serialize(None))

    def test_shallow_serialize(self):

        vehicle = Vehicle(owner=Owner(first_name="first_name", last_name="last_name"), type=VehicleType.car)

        self.assertDictEqual(
            {
                "_owner_id": None,
                "created_at": None,
                "id": None,
                "is_used": None,
                "name": None,
                "paint": None,
                "type": VehicleType.car,
            },
            models.serialize(vehicle),
        )

    def test_serialize_with_composites(self):
        business = Business(
            name="test",
            location=Address(street="street 1", state="state 1", zip="zip 1"),
            other_location=Address(street="street 2", state="state 2", zip="zip 2"),
        )

        self.assertDictEqual(
            {
                "id": None,
                "name": "test",
                "employees": None,
                "location": {"state": "state 1", "street": "street 1", "zip": "zip 1"},
                "other_location": {"state": "state 2", "street": "street 2", "zip": "zip 2"},
            },
            models.serialize(business),
        )

    def test_serialize_with_relations(self):

        vehicle = Vehicle(
            name="vehicle",
            owner=Owner(first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(name="option 1"), Option(name="option 2")],
            parts=[Part(name="part 1"), Part(name="part 2")],
        )

        self.assertDictEqual(
            {
                "_owner_id": None,
                "created_at": None,
                "id": None,
                "is_used": True,
                "paint": "red",
                "type": VehicleType.car,
                "name": "vehicle",
                "owner": {"id": None, "first_name": "first_name", "last_name": "last_name"},
                "options": [{"id": None, "name": "option 1"}, {"id": None, "name": "option 2"}],
                "parts": [{"id": None, "name": "part 1"}, {"id": None, "name": "part 2"}],
            },
            models.serialize(vehicle, Vehicle.owner, Vehicle.options, Vehicle.parts),
        )

    def test_deserialize(self):

        data = {
            "_owner_id": None,
            "created_at": None,
            "id": 1,
            "is_used": True,
            "paint": "red",
            "type": VehicleType.car,
            "name": "vehicle",
            "owner": {"id": 2, "first_name": "first_name", "last_name": "last_name"},
            "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
            "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
        }

        vehicle = models.deserialize(Vehicle, data)

        self.assertDictEqual(
            {
                "_owner_id": None,
                "created_at": None,
                "id": 1,
                "is_used": True,
                "paint": "red",
                "type": VehicleType.car,
                "name": "vehicle",
                "owner": {"id": 2, "first_name": "first_name", "last_name": "last_name"},
                "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
                "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
            },
            models.serialize(vehicle, Vehicle.owner, Vehicle.options, Vehicle.parts),
        )

    def test_deserialize_none(self):
        self.assertIsNone(models.deserialize(Vehicle, None))

    def test_deserialize_with_map(self):
        data = [
            {
                "_owner_id": 2,
                "created_at": None,
                "id": 1,
                "is_used": True,
                "paint": "red",
                "type": VehicleType.car,
                "name": "vehicle",
                "owner": {"id": 2, "first_name": "first_name", "last_name": "last_name"},
                "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
                "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
            },
            {
                "_owner_id": 2,
                "created_at": None,
                "id": 7,
                "is_used": True,
                "paint": "red",
                "type": VehicleType.car,
                "name": "vehicle",
                # missing owner to test back population of many to ones
                "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
                "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
            },
        ]

        vehicle1, vehicle2 = models.deserialize(Vehicle, data)

        self.assertEqual(vehicle1.owner, vehicle2.owner)

    def test_deserialize_composites(self):

        data = {
            "id": None,
            "name": "test",
            "location": {"state": "state 1", "street": "street 1", "zip": "zip 1"},
            "other_location": {"state": "state 2", "street": "street 2", "zip": "zip 2"},
        }

        business = models.deserialize(Business, data)

        self.assertDictEqual(
            {
                "id": None,
                "name": "test",
                "employees": None,
                "location": {"state": "state 1", "street": "street 1", "zip": "zip 1"},
                "other_location": {"state": "state 2", "street": "street 2", "zip": "zip 2"},
            },
            models.serialize(business),
        )


class TestClone(TestCase):
    def setUp(self):
        super(TestClone, self).setUp()
        self.vehicle = Vehicle(
            name="vehicle",
            owner=Owner(first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(name="option 1"), Option(name="option 2")],
            parts=[Part(name="part 1"), Part(name="part 2")],
        )

        db.add(self.vehicle)
        db.flush()
        db.expire_all()

    def test_clone_none(self):
        self.assertIsNone(models.clone(None))

    def test_shallow_clone(self):
        clone = models.clone(self.vehicle)
        db.add(clone)
        db.flush()

        self.assertNotEqual(clone, self.vehicle)
        self.assertNotEqual(clone.as_dict(), self.vehicle.as_dict())
        self.assertNotEqual(clone.id, self.vehicle.id)
        self.assertEqual(clone.name, self.vehicle.name)
        # self.assertEqual(models.model_to_dict(clone), models.model_to_dict(self.vehicle))
        self.assertIsNone(clone.owner)
        self.assertEqual(clone.options, [])
        self.assertEqual(clone.parts, [])

    def test_clone_with_relation(self):

        clone = models.clone(
            self.vehicle, Vehicle.owner, paint="blue", options=self.vehicle.options, parts=self.vehicle.parts
        )
        db.add(clone)
        db.flush()

        self.assertNotEqual(clone, self.vehicle)
        self.assertNotEqual(clone.as_dict(), self.vehicle.as_dict())
        self.assertNotEqual(clone.id, self.vehicle.id)
        self.assertEqual(clone.paint, "blue")
        self.assertEqual(clone.name, self.vehicle.name)
        # self.assertNotEqual(models.model_to_dict(clone), models.model_to_dict(self.vehicle))
        clone.paint = "red"
        # self.assertEqual(models.model_to_dict(clone), models.model_to_dict(self.vehicle))

        self.assertNotEqual(clone.owner, self.vehicle.owner)
        self.assertNotEqual(clone.owner.as_dict(), self.vehicle.owner.as_dict())
        self.assertNotEqual(clone.owner.id, self.vehicle.owner.id)
        # self.assertEqual(models.model_to_dict(clone.owner), models.model_to_dict(self.vehicle.owner))

        self.assertEqual(clone.options, self.vehicle.options)
        self.assertEqual(clone.parts, self.vehicle.parts)

    def test_clone_with_composite(self):
        business = Business(
            name="test",
            location=Address(street="street 1", state="state 1", zip="zip 1"),
            other_location=Address(street="street 2", state="state 2", zip="zip 2"),
        )

        clone = models.clone(business)

        self.assertNotEqual(clone, business)
        self.assertDictEqual(models.model_to_dict(clone), models.model_to_dict(business))
        self.assertNotEqual(id(clone.location), id(business.location))
        self.assertNotEqual(id(clone.other_location), id(business.other_location))

        self.assertEqual(clone.location, business.location)
        self.assertEqual(clone.other_location, business.other_location)

    def test_clone_with_relation_options(self):

        clone = models.clone(self.vehicle, make_args(Vehicle.owner, first_name="test"))
        db.add(clone)
        db.flush()

        self.assertNotEqual(clone, self.vehicle)
        self.assertNotEqual(clone.as_dict(), self.vehicle.as_dict())
        self.assertNotEqual(clone.id, self.vehicle.id)

        self.assertNotEqual(clone.owner, self.vehicle.owner)
        self.assertNotEqual(clone.owner.as_dict(), self.vehicle.owner.as_dict())
        self.assertNotEqual(clone.owner.id, self.vehicle.owner.id)
        self.assertEqual(clone.owner.first_name, "test")

    def test_clone_list_relation(self):

        clone = models.clone(self.vehicle, Vehicle.options)
        db.add(clone)
        db.flush()

        self.assertNotEqual(clone, self.vehicle)
        self.assertNotEqual(clone.as_dict(), self.vehicle.as_dict())
        self.assertNotEqual(clone.id, self.vehicle.id)
        # self.assertEqual(models.model_to_dict(clone), models.model_to_dict(self.vehicle))

        for cloned, orig in zip(clone.options, self.vehicle.options):
            self.assertNotEqual(cloned, orig)
            self.assertNotEqual(cloned.as_dict(), orig.as_dict())
            self.assertNotEqual(cloned.id, orig.id)


class TestAutoCoerce(TestCase):
    def setUp(self):
        self.instance = AllKindsOfFields()

    def _run_tests(self, attr, tests):
        for test, exp in tests:
            if exp is ValidationError:
                with self.assertRaises(ValidationError):
                    setattr(self.instance, attr, test)
            else:
                setattr(self.instance, attr, test)
                self.assertEqual(getattr(self.instance, attr), exp)

    def test_boolean(self):
        self.instance.boolean_notnull = "true"
        self.assertIsInstance(self.instance.boolean_notnull, bool)

        self.instance.boolean = "true"
        self.assertTrue(self.instance.boolean)
        self.assertTrue(type(self.instance.boolean) is bool)

        self.instance.boolean = "false"
        self.assertFalse(self.instance.boolean)
        self.assertTrue(type(self.instance.boolean) is bool)

    def test_enum(self):
        self.instance.enum = 0
        self.assertTrue(self.instance.enum is DummyEnum.zero)

        self.instance.enum = "one"
        self.assertTrue(self.instance.enum is DummyEnum.one)

        self.instance.enum = 2
        self.assertTrue(self.instance.enum is DummyEnum.two)

        self.instance.enum = DummyEnum.one
        self.assertTrue(self.instance.enum is DummyEnum.one)

        with self.assertRaises(ValidationError):
            self.instance.enum = "three"

    def test_enum_choice(self):
        self.instance.enum_choice = "three"
        self.assertEqual(self.instance.enum_choice, "three")

        with self.assertRaises(ValidationError):
            self.instance.enum_choice = "one"

    def test_string(self):
        tests = [
            ("abc", "abc"),
            (1234, "1234"),
            ("", ""),
            ("é", "é"),
            (Decimal("1234.44"), "1234.44"),
            (None, ""),
            # excess whitespace tests
            ("\t\t\t\t\n", ""),
            ("\t\tabc\t\t\n", "abc"),
            ("\t\t20,000\t\t\n", "20,000"),
            ("  \t 23\t", "23"),
        ]

        for attr in ["char", "nchar", "string", "text", "unicode", "unicodetext", "varchar"]:
            self._run_tests(attr, tests)

    def test_decimal(self):
        tests = [
            ("1", Decimal("1")),
            ("abc", ValidationError),
            (1, Decimal("1")),
            ("20,000", Decimal("20000")),
            ("1.e-8", Decimal("1E-8")),
            ("1.-8", ValidationError),
            ("", None),
            (None, None),
            # excess whitespace tests
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000\t\t\n", Decimal("20000")),
            ("  \t 23\t", Decimal("23")),
        ]
        for attr in ["decimal", "numeric"]:
            self._run_tests(attr, tests)

    def test_float(self):
        tests = [
            ("1", 1.0),
            ("abc", ValidationError),
            ("1.0", 1.0),
            ("1.", 1.0),
            ("1.001", 1.001),
            ("1.e-8", 1e-08),
            ("", None),
            (None, None),
            # excess whitespace tests
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000.02\t\t\n", 20000.02),
            ("  \t 23\t", 23.0),
        ]
        for attr in ["float", "real"]:
            self._run_tests(attr, tests)

    def test_integer(self):

        tests = [
            ("1", 1),
            ("abc", ValidationError),
            (1.0, 1),
            (1.01, ValidationError),
            ("1.0", 1),
            ("1.01", ValidationError),
            ("", None),
            (None, None),
            # # excess whitespace tests
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000.02\t\t\n", ValidationError),
            ("\t\t20,000\t\t\n", 20000),
            ("  \t 23\t", 23),
        ]
        for attr in ["int", "integer", "bigint", "biginteger", "smallint", "smallinteger"]:
            self._run_tests(attr, tests)

    def test_date(self):
        tests = [
            (datetime.date(2006, 10, 25), datetime.date(2006, 10, 25)),
            (datetime.datetime(2006, 10, 25, 14, 30), datetime.date(2006, 10, 25)),
            (datetime.datetime(2006, 10, 25, 14, 30, 59), datetime.date(2006, 10, 25)),
            (datetime.datetime(2006, 10, 25, 14, 30, 59, 200), datetime.date(2006, 10, 25)),
            ("2006-10-25", datetime.date(2006, 10, 25)),
            ("10/25/2006", datetime.date(2006, 10, 25)),
            ("10/25/06", datetime.date(2006, 10, 25)),
            ("Oct 25 2006", datetime.date(2006, 10, 25)),
            ("October 25 2006", datetime.date(2006, 10, 25)),
            ("October 25, 2006", datetime.date(2006, 10, 25)),
            ("25 October 2006", datetime.date(2006, 10, 25)),
            ("25 October, 2006", datetime.date(2006, 10, 25)),
            ("Hello", ValidationError),
        ]
        self._run_tests("date", tests)

    def test_datetime(self):
        tests = [
            ("2006-10-25 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200, tzinfo=pytz.utc)),
            ("2006-10-25 14:30:45.0002", datetime.datetime(2006, 10, 25, 14, 30, 45, 200, tzinfo=pytz.utc)),
            ("2006-10-25 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45, tzinfo=pytz.utc)),
            ("2006-10-25 14:30:00", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("2006-10-25 14:30", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("2006-10-25", datetime.datetime(2006, 10, 25, 0, 0, tzinfo=pytz.utc)),
            ("10/25/2006 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200, tzinfo=pytz.utc)),
            ("10/25/2006 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45, tzinfo=pytz.utc)),
            ("10/25/2006 14:30:00", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("10/25/2006 14:30", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("10/25/2006", datetime.datetime(2006, 10, 25, 0, 0, tzinfo=pytz.utc)),
            ("10/25/06 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200, tzinfo=pytz.utc)),
            ("10/25/06 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45, tzinfo=pytz.utc)),
            ("10/25/06 14:30:00", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("10/25/06 14:30", datetime.datetime(2006, 10, 25, 14, 30, tzinfo=pytz.utc)),
            ("10/25/06", datetime.datetime(2006, 10, 25, 0, 0, tzinfo=pytz.utc)),
            ("Hello", ValidationError),
        ]
        self._run_tests("datetime", tests)
        self._run_tests("timestamp", tests)

    def test_interval(self):
        tests = [
            ("30", datetime.timedelta(seconds=30)),
            ("15:30", datetime.timedelta(minutes=15, seconds=30)),
            ("1:15:30", datetime.timedelta(hours=1, minutes=15, seconds=30)),
            ("1 1:15:30.3", datetime.timedelta(days=1, hours=1, minutes=15, seconds=30, milliseconds=300)),
            ("Hello", ValidationError),
        ]
        self._run_tests("interval", tests)

    def test_time(self):
        tests = [
            (datetime.time(14, 25), datetime.time(14, 25)),
            (datetime.time(14, 25, 59), datetime.time(14, 25, 59)),
            ("14:25", datetime.time(14, 25)),
            ("14:25:59", datetime.time(14, 25, 59)),
            ("Hello", ValidationError),
        ]
        self._run_tests("time", tests)

    def test_selected_fields_only(self):
        model = SelectedAutoCoerce()

        with self.assertRaises(ValidationError):
            model.foo = "abc"

        with self.assertRaises(ValidationError):
            model.bar = "abc"

        model.me = "abc"
        self.assertEqual(model.me, "abc")
