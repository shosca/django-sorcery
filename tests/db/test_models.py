# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError

from django_sorcery.db import meta, models
from django_sorcery.utils import make_args

from ..base import TestCase
from ..testapp.models import (
    Address,
    AllKindsOfFields,
    Business,
    DummyEnum,
    Option,
    Owner,
    Part,
    SelectedAutoCoerce,
    Vehicle,
    VehicleType,
    db,
)


class TestModelRepr(TestCase):
    def test_simple_repr(self):

        vehicle = Vehicle()
        self.assertEqual(models.simple_repr(vehicle), "Vehicle(id=None, is_used=False)")

        vehicle.name = "Test"
        self.assertEqual(models.simple_repr(vehicle), "Vehicle(id=None, is_used=False, name='Test')")

        vehicle.id = 1234
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id=1234, is_used=False, name='Test')")

        vehicle.id = "abc"
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id='abc', is_used=False, name='Test')")

        vehicle.id = b"abc"
        self.assertTrue(models.simple_repr(vehicle), "Vehicle(id='abc', is_used=False, name='Test')")


class TestSerialization(TestCase):
    def test_serialize_none(self):
        self.assertIsNone(models.serialize(None))

    def test_shallow_serialize(self):

        vehicle = Vehicle(owner=Owner(first_name="first_name", last_name="last_name"), type=VehicleType.car)

        self.assertDictEqual(
            {
                "_owner_id": None,
                "created_at": None,
                "id": None,
                "is_used": False,
                "name": None,
                "msrp": None,
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
                "employees": 5,
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
                "msrp": None,
                "name": "vehicle",
                "options": [{"id": None, "name": "option 1"}, {"id": None, "name": "option 2"}],
                "owner": {"id": None, "first_name": "first_name", "last_name": "last_name"},
                "paint": "red",
                "parts": [{"id": None, "name": "part 1"}, {"id": None, "name": "part 2"}],
                "type": VehicleType.car,
            },
            models.serialize(vehicle, Vehicle.owner, Vehicle.options, Vehicle.parts),
        )

    def test_deserialize(self):

        data = {
            "_owner_id": None,
            "created_at": None,
            "id": 1,
            "is_used": True,
            "name": "vehicle",
            "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
            "owner": {"id": 2, "first_name": "first_name", "last_name": "last_name"},
            "paint": "red",
            "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
            "type": VehicleType.car,
        }

        vehicle = models.deserialize(Vehicle, data)

        self.assertDictEqual(
            {
                "_owner_id": None,
                "created_at": None,
                "id": 1,
                "is_used": True,
                "msrp": None,
                "name": "vehicle",
                "options": [{"id": 3, "name": "option 1"}, {"id": 4, "name": "option 2"}],
                "owner": {"id": 2, "first_name": "first_name", "last_name": "last_name"},
                "paint": "red",
                "parts": [{"id": 5, "name": "part 1"}, {"id": 6, "name": "part 2"}],
                "type": VehicleType.car,
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
                "employees": 5,
                "location": {"state": "state 1", "street": "street 1", "zip": "zip 1"},
                "other_location": {"state": "state 2", "street": "street 2", "zip": "zip 2"},
            },
            models.serialize(business),
        )


class TestClone(TestCase):
    def setUp(self):
        super().setUp()
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
        self.assertEqual(clone.is_used, self.vehicle.is_used)
        self.assertEqual(clone.msrp, self.vehicle.msrp)
        self.assertEqual(clone.name, self.vehicle.name)
        self.assertEqual(clone.paint, self.vehicle.paint)
        self.assertEqual(clone.type, self.vehicle.type)
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
        clone.paint = "red"

        self.assertIsNot(clone.owner, self.vehicle.owner)
        self.assertNotEqual(clone.owner.as_dict(), self.vehicle.owner.as_dict())
        self.assertNotEqual(clone.owner.id, self.vehicle.owner.id)
        self.assertEqual(clone.owner.first_name, self.vehicle.owner.first_name)
        self.assertEqual(clone.owner.last_name, self.vehicle.owner.last_name)

        self.assertEqual(clone.options, self.vehicle.options)
        self.assertEqual(clone.parts, self.vehicle.parts)

    def test_clone_with_composite(self):
        business = Business(
            name="test",
            location=Address(street="street 1", state="state 1", zip="zip 1"),
            other_location=Address(street="street 2", state="state 2", zip="zip 2"),
        )

        clone = models.clone(business)

        self.assertIsNot(clone, business)
        self.assertIsNot(clone.location, business.location)
        self.assertIsNot(clone.other_location, business.other_location)

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

        for cloned, orig in zip(clone.options, self.vehicle.options):
            self.assertNotEqual(cloned, orig)
            self.assertNotEqual(cloned.as_dict(), orig.as_dict())
            self.assertNotEqual(cloned.id, orig.id)


class TestBaseModel(TestCase):
    def test_default_table_name(self):
        self.assertEqual(AllKindsOfFields.__table__.name, "all_kinds_of_fields")

    def test_as_dict(self):
        instance = AllKindsOfFields()

        self.assertDictEqual(
            instance.as_dict(),
            {
                "bigint": None,
                "biginteger": None,
                "binary": None,
                "boolean": None,
                "boolean_notnull": None,
                "char": None,
                "date": None,
                "datetime": None,
                "decimal": None,
                "enum": None,
                "enum_choice": None,
                "float": None,
                "int": None,
                "integer": None,
                "interval": None,
                "largebinary": None,
                "nchar": None,
                "numeric": None,
                "pk": None,
                "real": None,
                "smallint": None,
                "smallinteger": None,
                "string": None,
                "text": None,
                "time": None,
                "timestamp": None,
                "unicode": None,
                "unicodetext": None,
                "varchar": None,
            },
        )

    def test_model_repr(self):
        owner = Owner(id=1, first_name="Morty", last_name="McFly")

        self.assertEqual(repr(owner), "Owner(id=1, first_name='Morty', last_name='McFly')")

    def test_get_properties_for_validation(self):
        instance = Owner(id=1, first_name="Morty", last_name="McFly")

        self.assertEqual(set(instance._get_properties_for_validation()), {"first_name", "last_name"})

    def test_get_nested_objects_for_validation(self):
        instance = Business()

        self.assertEqual(set(instance._get_nested_objects_for_validation()), {"location", "other_location"})

    def test_get_relation_objects_for_validation(self):
        instance = Vehicle()
        info = meta.model_info(instance)

        self.assertDictEqual(
            instance._get_relation_objects_for_validation(),
            {"options": info.options, "owner": info.owner, "parts": info.parts},
        )


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
            (None, None),
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
            ("20000", Decimal("20000")),
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

        with self.settings(THOUSAND_SEPARATOR=".", DECIMAL_SEPARATOR=","):
            tests = [("20.000", Decimal("20000")), ("20,000", Decimal("20.000"))]
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
            ("2006-10-25 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("2006-10-25 14:30:45.0002", datetime.datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("2006-10-25 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45)),
            ("2006-10-25 14:30:00", datetime.datetime(2006, 10, 25, 14, 30)),
            ("2006-10-25 14:30", datetime.datetime(2006, 10, 25, 14, 30)),
            ("2006-10-25", datetime.datetime(2006, 10, 25, 0, 0)),
            ("10/25/2006 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("10/25/2006 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45)),
            ("10/25/2006 14:30:00", datetime.datetime(2006, 10, 25, 14, 30)),
            ("10/25/2006 14:30", datetime.datetime(2006, 10, 25, 14, 30)),
            ("10/25/2006", datetime.datetime(2006, 10, 25, 0, 0)),
            ("10/25/06 14:30:45.000200", datetime.datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("10/25/06 14:30:45", datetime.datetime(2006, 10, 25, 14, 30, 45)),
            ("10/25/06 14:30:00", datetime.datetime(2006, 10, 25, 14, 30)),
            ("10/25/06 14:30", datetime.datetime(2006, 10, 25, 14, 30)),
            ("10/25/06", datetime.datetime(2006, 10, 25, 0, 0)),
            ("2012-04-23T09:15:00", datetime.datetime(2012, 4, 23, 9, 15)),
            ("2012-4-9 4:8:16", datetime.datetime(2012, 4, 9, 4, 8, 16)),
            ("2012-04-23T09:15:00Z", datetime.datetime(2012, 4, 23, 9, 15, 0, 0)),
            ("2012-4-9 4:8:16-0320", datetime.datetime(2012, 4, 9, 7, 28, 16, 0)),
            ("2012-04-23T10:20:30.400+02:30", datetime.datetime(2012, 4, 23, 7, 50, 30, 400000)),
            ("2012-04-23T10:20:30.400+02", datetime.datetime(2012, 4, 23, 8, 20, 30, 400000)),
            ("2012-04-23T10:20:30.400-02", datetime.datetime(2012, 4, 23, 12, 20, 30, 400000)),
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


class TestInstantDefaults(TestCase):
    def test(self):
        instance = Business()

        self.assertEqual(instance.employees, 5)

        instance = Business(employees=1)

        self.assertEqual(instance.employees, 1)

    def test_non_model(self):
        self.assertIsNone(models.instant_defaults(list))
