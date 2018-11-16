# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import enum

import sqlalchemy as sa

from django.core import validators as django_validators

from django_sorcery.db import fields

from ..base import TestCase


class DummyEnum(enum.Enum):
    one = 1
    two = 2


class TestFields(TestCase):
    def test_boolean_field(self):
        column = fields.BooleanField()
        self.assertIsInstance(column.type, sa.Boolean)

    def test_char_field(self):
        column = fields.CharField()
        self.assertIsInstance(column.type, sa.String)
        self.assertIsNone(column.type.length)

        column = fields.CharField(max_length=120)
        self.assertEqual(column.type.length, 120)

    def test_date_field(self):
        column = fields.DateField()
        self.assertIsInstance(column.type, sa.Date)

    def test_datetime_field(self):
        column = fields.DateTimeField()
        self.assertIsInstance(column.type, sa.DateTime)

    def test_duration_field(self):
        column = fields.DurationField()
        self.assertIsInstance(column.type, sa.Interval)

    def test_decimal_field(self):
        column = fields.DecimalField()
        self.assertIsInstance(column.type, sa.Numeric)
        self.assertTrue(column.type.asdecimal)

    def test_email_field(self):
        column = fields.EmailField()
        self.assertIsInstance(column.type, sa.String)
        self.assertEqual(column.info, {"validators": [django_validators.validate_email], "required": False})

    def test_enum_field(self):
        with self.assertRaises(KeyError):
            column = fields.EnumField()

        with self.assertRaises(KeyError):
            column = fields.EnumField(DummyEnum)

        column = fields.EnumField(choices=DummyEnum)
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)

        column = fields.EnumField(choices=DummyEnum, constraint_name="dummy")
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)
        self.assertEqual(column.type.name, "dummy")

        column = fields.EnumField(choices=DummyEnum, constraint_name="dummy", native_enum=False)
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)
        self.assertEqual(column.type.name, "dummy")
        self.assertFalse(column.type.native_enum)

    def test_float_field(self):
        column = fields.FloatField()
        self.assertIsInstance(column.type, sa.Float)
        self.assertIsNone(column.type.precision)
        self.assertFalse(column.type.asdecimal)

        column = fields.FloatField(precision=10)
        self.assertEqual(column.type.precision, 10)

        column = fields.FloatField(max_digits=10)
        self.assertEqual(column.type.precision, 10)

    def test_integer_field(self):
        column = fields.IntegerField()
        self.assertIsInstance(column.type, sa.Integer)

    def test_biginteger_field(self):
        column = fields.BigIntegerField()
        self.assertIsInstance(column.type, sa.BigInteger)

    def test_smallinteger_field(self):
        column = fields.SmallIntegerField()
        self.assertIsInstance(column.type, sa.SmallInteger)

    def test_nullboolean_field(self):
        column = fields.NullBooleanField()
        self.assertIsInstance(column.type, sa.Boolean)
        self.assertFalse(column.nullable)

    def test_slug_field(self):
        column = fields.SlugField()
        self.assertIsInstance(column.type, sa.String)
        self.assertEqual(column.info, {"validators": [django_validators.validate_slug], "required": False})

    def test_text_field(self):
        column = fields.TextField()
        self.assertIsInstance(column.type, sa.Text)

    def test_time_field(self):
        column = fields.TimeField()
        self.assertIsInstance(column.type, sa.Time)

    def test_timestamp_field(self):
        column = fields.TimestampField()
        self.assertIsInstance(column.type, sa.TIMESTAMP)

    def test_url_field(self):
        column = fields.URLField()
        self.assertIsInstance(column.type, sa.String)
        self.assertIsInstance(column.info["validators"][0], django_validators.URLValidator)

    def test_binary_field(self):
        fields.TimeField()
