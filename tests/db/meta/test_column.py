# -*- coding: utf-8 -*-
import enum
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytz

import sqlalchemy as sa

from django import forms as djangoforms
from django.core import validators as django_validators
from django.core.exceptions import ValidationError
from django.forms import fields as djangofields, widgets

from django_sorcery import fields as sorceryfields
from django_sorcery.db import fields as dbfields, meta  # noqa

from ...base import TestCase, mock
from ...testapp.models import COLORS, AllKindsOfFields, Business, Vehicle, VehicleType


class TestColumnMeta(TestCase):
    def test_column_info(self):
        info = meta.model_info(Vehicle)

        col = info.primary_keys["id"]
        self.assertEqual(col.name, "id")
        self.assertFalse(col.null)
        self.assertDictEqual(
            {
                "help_text": "The primary key",
                "label": "Id",
                "required": True,
                "validators": [django_validators.validate_integer, mock.ANY, mock.ANY],
            },
            col.field_kwargs,
        )
        self.assertIs(col.validators, col.column.info["validators"])
        self.assertTrue(col.required)
        self.assertIs(Vehicle.id, col.attribute)

    def test_default_initial(self):
        info = meta.model_info(Business)

        col = info.employees
        self.assertDictEqual(
            {
                "help_text": None,
                "initial": 5,
                "label": "Employees",
                "required": True,
                "validators": [django_validators.validate_integer, mock.ANY, mock.ANY],
            },
            col.field_kwargs,
        )

    def test_column_info_enum(self):
        info = meta.model_info(Vehicle)
        col = info.type
        self.assertFalse(col.null)
        self.assertDictEqual(
            {"choices": VehicleType, "help_text": None, "label": "Type", "required": True, "validators": []},
            col.field_kwargs,
        )
        self.assertTrue(col.required)

    def test_column_info_enum_from_class_from_info(self):
        col = sa.Column(sa.Enum(VehicleType), info={"form_class": djangofields.IntegerField})
        info = meta.column_info(col, name="test")
        self.assertIsInstance(info, meta.enum_column_info)
        self.assertEqual(info.form_class, djangofields.IntegerField)

    def test_column_info_boolean_from_class_from_info(self):
        info = meta.column_info(sa.Column(sa.Boolean(), info={"form_class": djangofields.IntegerField}), name="test")
        self.assertIsInstance(info, meta.boolean_column_info)
        self.assertEqual(info.form_class, djangofields.IntegerField)

    def test_column_info_validators(self):
        info = meta.model_info(Vehicle)
        col = info.properties["msrp"]
        validator = col.column.info["validators"][0]
        self.assertIsInstance(validator, django_validators.DecimalValidator)
        self.assertDictEqual(
            {
                "decimal_places": 2,
                "help_text": None,
                "label": "Msrp",
                "max_digits": 10,
                "required": False,
                "validators": [validator],
            },
            col.field_kwargs,
        )

    def test_column_info_label_and_text(self):
        column = meta.column_info(dbfields.TextField(label="dummy"), name="test")
        self.assertDictEqual(
            column.field_kwargs,
            {
                "help_text": None,
                "label": "dummy",
                "max_length": None,
                "required": False,
                "validators": [],
                "widget": djangoforms.Textarea,
            },
        )

    def test_choice_enum(self):
        info = meta.model_info(Vehicle)
        col = info.paint
        self.assertDictEqual(
            {
                "choices": [(x, x) for x in COLORS],
                "help_text": None,
                "label": "Paint",
                "required": False,
                "validators": [],
            },
            col.field_kwargs,
        )
        self.assertEqual(col.parent_model, Vehicle)
        self.assertEqual(repr(col), "<choice_column_info(Vehicle.paint)>")

    def test_plain_sqla(self):
        info = meta.model_info(AllKindsOfFields)
        col = info.decimal
        self.assertDictEqual(
            {"help_text": None, "label": "Decimal", "required": False, "validators": []}, col.field_kwargs
        )


def _run_tests(test, column_info, tests):
    for value, exp in tests:
        instance = object()
        if exp is ValidationError:
            with test.assertRaises(ValidationError):
                column_info.clean(value, instance)
        else:
            test.assertEqual(column_info.clean(value, instance), exp)


class TestDefaultColumn(TestCase):
    def test_formfield(self):
        info = meta.column_info(sa.Column(sa.sql.sqltypes.ARRAY(item_type=int)), name="test")
        formfield = info.formfield()
        self.assertIsNone(formfield)

    def test_clean(self):
        info = meta.column_info(sa.Column(sa.sql.sqltypes.ARRAY(item_type=int)), name="test")
        tests = [("test", "test"), (1, 1), (None, None)]
        _run_tests(self, info, tests)


class TestStringColumn(TestCase):
    def test_formfield(self):
        info = meta.column_info(sa.Column(sa.String()), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.CharField)

        info = meta.column_info(sa.Column(sa.Text()), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.CharField)
        self.assertIsInstance(formfield.widget, widgets.Textarea)

    def test_clean(self):
        info = meta.column_info(sa.Column(sa.String()), name="test")

        tests = [
            (None, None),
            ("abc", "abc"),
            (1234, "1234"),
            ("", ""),
            ("é", "é"),
            (Decimal("1234.44"), "1234.44"),
            # excess whitespace tests
            ("\t\t\t\t\n", ""),
            ("\t\tabc\t\t\n", "abc"),
            ("\t\t20,000\t\t\n", "20,000"),
            ("  \t 23\t", "23"),
        ]
        _run_tests(self, info, tests)


class TestChoiceColumn(TestCase):
    def test_formfield(self):
        info = meta.column_info(sa.Column(sa.Enum(*["1", "2", "3"])), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.TypedChoiceField)

    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Enum(*["1", "2", "3"])), name="test")
        tests = [(None, None), ("", None), ("1", "1"), (1, "1"), ("4", ValidationError), (5, ValidationError)]
        _run_tests(self, info, tests)


class TestEnumColumn(TestCase):
    def test_formfield(self):
        class Demo(enum.Enum):
            one = "1"
            two = "2"

        info = meta.column_info(sa.Column(sa.Enum(Demo)), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, sorceryfields.EnumField)

    def test_clean(self):
        class Demo(enum.Enum):
            one = "1"
            two = "2"

        info = meta.column_info(sa.Column(sa.Enum(Demo)), name="test")
        tests = [
            (None, None),
            ("", None),
            ("one", Demo.one),
            ("1", Demo.one),
            (Demo.one, Demo.one),
            (1, ValidationError),
        ]
        _run_tests(self, info, tests)


class TestNumericColumn(TestCase):
    def test_formfield(self):
        info = meta.column_info(sa.Column(sa.Numeric(precision=14, scale=2, asdecimal=True)), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.DecimalField)
        self.assertEqual(formfield.max_digits, 14)
        self.assertEqual(formfield.decimal_places, 2)

    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Numeric(precision=14, scale=2, asdecimal=True)), name="test")
        tests = [
            (None, None),
            ("", None),
            ("1", Decimal("1")),
            (Decimal("1"), Decimal("1")),
            ("abc", ValidationError),
            (1, Decimal("1")),
            (4123411130.3419398, Decimal("4123411130.3419")),
            ("20,000", Decimal("20000")),
            ("1.e-8", Decimal("1E-8")),
            ("1.-8", ValidationError),
            # excess whitespace tests
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000\t\t\n", Decimal("20000")),
            ("  \t 23\t", Decimal("23")),
        ]
        _run_tests(self, info, tests)

        with self.settings(THOUSAND_SEPARATOR=".", DECIMAL_SEPARATOR=","):
            tests = [("20.000", Decimal("20000")), ("20,000", Decimal("20.000"))]
            _run_tests(self, info, tests)


class TestBooleanColumn(TestCase):
    def test_formfield(self):
        info = meta.column_info(sa.Column(sa.Boolean()), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.NullBooleanField)

        info = meta.column_info(sa.Column(sa.Boolean(), nullable=False), name="test")
        formfield = info.formfield()
        self.assertIsInstance(formfield, djangofields.BooleanField)

    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Boolean()), name="test")
        tests = [
            (None, None),
            ("", None),
            (True, True),
            (1, True),
            ("t", True),
            ("true", True),
            ("True", True),
            ("1", True),
            (0, False),
            ("f", False),
            ("false", False),
            ("False", False),
            ("0", False),
        ]
        _run_tests(self, info, tests)


class TestDateColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Date()), name="test")
        tests = [
            (None, None),
            ("Hello", ValidationError),
            (date(2006, 10, 25), date(2006, 10, 25)),
            (datetime(2006, 10, 25, 14, 30), date(2006, 10, 25)),
            (datetime(2006, 10, 25, 14, 30, 59), date(2006, 10, 25)),
            (datetime(2006, 10, 25, 14, 30, 59, 200), date(2006, 10, 25)),
            (datetime(2006, 10, 25, 14, 30, 59, 200, tzinfo=pytz.timezone("EST")), date(2006, 10, 25)),
            ("2006-10-25", date(2006, 10, 25)),
            ("10/25/2006", date(2006, 10, 25)),
            ("10/25/06", date(2006, 10, 25)),
            ("Oct 25 2006", date(2006, 10, 25)),
            ("October 25 2006", date(2006, 10, 25)),
            ("October 25, 2006", date(2006, 10, 25)),
            ("25 October 2006", date(2006, 10, 25)),
            ("25 October, 2006", date(2006, 10, 25)),
            (1335172500.12, date(2012, 4, 23)),
        ]
        _run_tests(self, info, tests)


class TestDateTimeColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.DateTime()), name="test")
        tests = [
            (None, None),
            (
                datetime(2006, 10, 25, 14, 30, 45, 200, tzinfo=pytz.timezone("EST")),
                datetime(2006, 10, 25, 19, 30, 45, 200),
            ),
            (date(2006, 10, 25), datetime(2006, 10, 25, 0, 0)),
            ("2006-10-25 14:30:45.000200", datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("2006-10-25 14:30:45.0002", datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("2006-10-25 14:30:45", datetime(2006, 10, 25, 14, 30, 45)),
            ("2006-10-25 14:30:00", datetime(2006, 10, 25, 14, 30)),
            ("2006-10-25 14:30", datetime(2006, 10, 25, 14, 30)),
            ("2006-10-25", datetime(2006, 10, 25, 0, 0)),
            ("10/25/2006 14:30:45.000200", datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("10/25/2006 14:30:45", datetime(2006, 10, 25, 14, 30, 45)),
            ("10/25/2006 14:30:00", datetime(2006, 10, 25, 14, 30)),
            ("10/25/2006 14:30", datetime(2006, 10, 25, 14, 30)),
            ("10/25/2006", datetime(2006, 10, 25, 0, 0)),
            ("10/25/06 14:30:45.000200", datetime(2006, 10, 25, 14, 30, 45, 200)),
            ("10/25/06 14:30:45", datetime(2006, 10, 25, 14, 30, 45)),
            ("10/25/06 14:30:00", datetime(2006, 10, 25, 14, 30)),
            ("10/25/06 14:30", datetime(2006, 10, 25, 14, 30)),
            ("10/25/06", datetime(2006, 10, 25, 0, 0)),
            ("2012-04-23T09:15:00", datetime(2012, 4, 23, 9, 15)),
            ("2012-4-9 4:8:16", datetime(2012, 4, 9, 4, 8, 16)),
            ("2012-04-23T09:15:00Z", datetime(2012, 4, 23, 9, 15, 0, 0)),
            ("2012-4-9 4:8:16-0320", datetime(2012, 4, 9, 7, 28, 16, 0)),
            ("2012-04-23T10:20:30.400+02:30", datetime(2012, 4, 23, 7, 50, 30, 400000)),
            ("2012-04-23T10:20:30.400+02", datetime(2012, 4, 23, 8, 20, 30, 400000)),
            ("2012-04-23T10:20:30.400-02", datetime(2012, 4, 23, 12, 20, 30, 400000)),
            (1335172500.12, datetime(2012, 4, 23, 9, 15, 0, 120000)),
            ("Hello", ValidationError),
        ]
        _run_tests(self, info, tests)


class TestFloatColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Float()), name="test")
        tests = [
            (None, None),
            ("", None),
            (1.2, 1.2),
            ("1", 1.0),
            ("abc", ValidationError),
            ("1.0", 1.0),
            ("1.", 1.0),
            ("1.001", 1.001),
            ("1.e-8", 1e-08),
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000.02\t\t\n", 20000.02),
            ("  \t 23\t", 23.0),
        ]
        _run_tests(self, info, tests)


class TestIntegerColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Integer()), name="test")
        tests = [
            (None, None),
            ("", None),
            (1, 1),
            ("1", 1),
            ("abc", ValidationError),
            (1.0, 1),
            (1.01, ValidationError),
            ("1.0", 1),
            ("1.01", ValidationError),
            ("\t\t\t\t\n", None),
            ("\t\tabc\t\t\n", ValidationError),
            ("\t\t20,000.02\t\t\n", ValidationError),
            ("\t\t20,000\t\t\n", 20000),
            ("  \t 23\t", 23),
        ]
        _run_tests(self, info, tests)


class TestIntervalColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Interval()), name="test")
        tests = [
            (None, None),
            ("", None),
            ("Hello", ValidationError),
            (1.2, timedelta(seconds=1, microseconds=200000)),
            (timedelta(seconds=30), timedelta(seconds=30)),
            ("30", timedelta(seconds=30)),
            ("15:30", timedelta(minutes=15, seconds=30)),
            ("1:15:30", timedelta(hours=1, minutes=15, seconds=30)),
            ("1 1:15:30.3", timedelta(days=1, hours=1, minutes=15, seconds=30, milliseconds=300)),
        ]
        _run_tests(self, info, tests)


class TestTimeColumn(TestCase):
    def test_clean(self):
        info = meta.column_info(sa.Column(sa.Time()), name="test")
        tests = [
            (None, None),
            ("", None),
            ("Hello", ValidationError),
            (2.3, ValidationError),
            (time(14, 25), time(14, 25)),
            (time(14, 25, 59), time(14, 25, 59)),
            (datetime(2006, 10, 25, 14, 30, 59, 200, tzinfo=pytz.timezone("EST")), time(14, 30, 59, 200)),
            ("14:25", time(14, 25)),
            ("14:25:59", time(14, 25, 59)),
        ]
        _run_tests(self, info, tests)
