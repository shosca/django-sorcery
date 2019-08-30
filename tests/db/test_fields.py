# -*- coding: utf-8 -*-
import enum

import sqlalchemy as sa

from django import forms as djangoforms
from django.core import validators as django_validators
from django.forms import fields as djangofields

from django_sorcery import fields as formfields
from django_sorcery.db import fields, meta

from ..base import TestCase, mock


class DummyEnum(enum.Enum):
    one = 1
    two = 2


class TestFields(TestCase):
    def test_can_init_like_sqlalchemy(self):
        col_type = sa.String()
        column = fields.Field("test", col_type)

        self.assertEqual(column.name, "test")
        self.assertEqual(column.type, col_type)

    def test_boolean_field(self):
        column = fields.BooleanField()
        self.assertIsInstance(column.type, sa.Boolean)
        self.assertFalse(column.nullable)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.BooleanField)

        column = fields.BooleanField(constraint_name="test")
        self.assertEqual(column.type.name, "test")

    def test_char_field(self):
        with self.assertRaises(TypeError):
            column = fields.CharField()

        column = fields.CharField(max_length=120)
        self.assertEqual(column.type.length, 120)
        self.assertIsInstance(column.info["validators"][-1], django_validators.MaxLengthValidator)
        self.assertEqual(column.info["validators"][-1].limit_value, 120)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.CharField)

    def test_date_field(self):
        column = fields.DateField()
        self.assertIsInstance(column.type, sa.Date)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.DateField)

    def test_datetime_field(self):
        column = fields.DateTimeField()
        self.assertIsInstance(column.type, sa.DateTime)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.DateTimeField)

    def test_duration_field(self):
        column = fields.DurationField()
        self.assertIsInstance(column.type, sa.Interval)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.DurationField)

    def test_decimal_field(self):
        column = fields.DecimalField()
        self.assertIsInstance(column.type, sa.Numeric)
        self.assertTrue(column.type.asdecimal)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.DecimalField)

    def test_email_field(self):
        column = fields.EmailField(length=100)
        self.assertIsInstance(column.type, sa.String)
        self.assertEqual(
            {
                "form_class": djangofields.EmailField,
                "required": False,
                "validators": [django_validators.validate_email, mock.ANY],
            },
            column.info,
        )
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.EmailField)

    def test_enum_field_bad_config(self):
        with self.assertRaises(TypeError):
            fields.EnumField()

        with self.assertRaises(TypeError):
            fields.EnumField(DummyEnum)

    def test_enum_field_plain_choices(self):
        column = fields.EnumField(choices=["a", "b"])
        self.assertIsInstance(column.type, sa.Enum)
        self.assertIsNone(column.type.enum_class)
        self.assertEqual(column.type.enums, ["a", "b"])
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.TypedChoiceField)
        self.assertEqual(form_field.choices, [("a", "a"), ("b", "b")])

    def test_enum_field_enum_choices(self):
        column = fields.EnumField(choices=DummyEnum)
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, formfields.EnumField)

    def test_enum_field_enum_choices_with_constraint_name(self):
        column = fields.EnumField(choices=DummyEnum, constraint_name="dummy")
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)
        self.assertEqual(column.type.name, "dummy")
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, formfields.EnumField)

    def test_enum_field_enum_choices_with_constraint_name_and_no_native_type(self):
        column = fields.EnumField(choices=DummyEnum, constraint_name="dummy", native_enum=False)
        self.assertIsInstance(column.type, sa.Enum)
        self.assertEqual(column.type.enum_class, DummyEnum)
        self.assertEqual(column.type.name, "dummy")
        self.assertFalse(column.type.native_enum)
        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, formfields.EnumField)

    def test_float_field(self):
        column = fields.FloatField()
        self.assertIsInstance(column.type, sa.Float)
        self.assertIsNone(column.type.precision)
        self.assertFalse(column.type.asdecimal)

        column = fields.FloatField(precision=10)
        self.assertEqual(column.type.precision, 10)

        column = fields.FloatField(max_digits=10)
        self.assertEqual(column.type.precision, 10)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.FloatField)

    def test_integer_field(self):
        column = fields.IntegerField()
        self.assertIsInstance(column.type, sa.Integer)
        self.assertIsInstance(column.info["validators"][-2], django_validators.MinValueValidator)
        self.assertEqual(column.info["validators"][-2].limit_value, -2147483648)
        self.assertIsInstance(column.info["validators"][-1], django_validators.MaxValueValidator)
        self.assertEqual(column.info["validators"][-1].limit_value, 2147483647)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.IntegerField)

    def test_biginteger_field(self):
        column = fields.BigIntegerField()
        self.assertIsInstance(column.type, sa.BigInteger)
        self.assertIsInstance(column.info["validators"][-2], django_validators.MinValueValidator)
        self.assertEqual(column.info["validators"][-2].limit_value, -9223372036854775808)
        self.assertIsInstance(column.info["validators"][-1], django_validators.MaxValueValidator)
        self.assertEqual(column.info["validators"][-1].limit_value, 9223372036854775807)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.IntegerField)

    def test_smallinteger_field(self):
        column = fields.SmallIntegerField()
        self.assertIsInstance(column.type, sa.SmallInteger)
        self.assertIsInstance(column.info["validators"][-2], django_validators.MinValueValidator)
        self.assertEqual(column.info["validators"][-2].limit_value, -32768)
        self.assertIsInstance(column.info["validators"][-1], django_validators.MaxValueValidator)
        self.assertEqual(column.info["validators"][-1].limit_value, 32767)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.IntegerField)

    def test_nullboolean_field(self):
        column = fields.NullBooleanField()
        self.assertIsInstance(column.type, sa.Boolean)
        self.assertTrue(column.nullable)

        column = fields.NullBooleanField(constraint_name="test")
        self.assertEqual(column.type.name, "test")

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.NullBooleanField)

    def test_slug_field(self):
        column = fields.SlugField(label="test", length=100)
        self.assertIsInstance(column.type, sa.String)
        self.assertEqual(
            {
                "form_class": djangofields.SlugField,
                "label": "test",
                "required": False,
                "validators": [django_validators.validate_slug, mock.ANY],
            },
            column.info,
        )

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.SlugField)

    def test_text_field(self):
        column = fields.TextField()
        self.assertIsInstance(column.type, sa.Text)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.CharField)
        self.assertIsInstance(form_field.widget, djangoforms.Textarea)

    def test_time_field(self):
        column = fields.TimeField()
        self.assertIsInstance(column.type, sa.Time)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.TimeField)

    def test_timestamp_field(self):
        column = fields.TimestampField()
        self.assertIsInstance(column.type, sa.TIMESTAMP)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.DateTimeField)

    def test_url_field(self):
        column = fields.URLField(length=100)
        self.assertIsInstance(column.type, sa.String)
        self.assertIsInstance(column.info["validators"][0], django_validators.URLValidator)

        form_field = meta.column_info(column).formfield()
        self.assertIsInstance(form_field, djangofields.URLField)

    def test_binary_field(self):
        fields.BinaryField()

    def test_override_form_class(self):
        column = fields.EnumField(choices=["a", "b"], form_class=djangofields.ChoiceField)

        form_field = meta.column_info(column).formfield()
        self.assertIs(type(form_field), djangofields.ChoiceField)
        self.assertIsNot(type(form_field), djangofields.TypedChoiceField)

        column = fields.URLField(form_class=djangofields.CharField, length=100)
        form_field = meta.column_info(column).formfield()
        self.assertIs(type(form_field), djangofields.CharField)
        self.assertIsNot(type(form_field), djangofields.URLField)
