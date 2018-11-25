# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django import forms as djangoforms
from django.core import validators as django_validators
from django.forms import fields as djangofields

from django_sorcery.db import fields as dbfields, meta  # noqa

from ...base import TestCase
from ...testapp.models import COLORS, AllKindsOfFields, Business, Vehicle, VehicleType


class TestColumnMeta(TestCase):
    def test_deprecated_init(self):
        col = dbfields.CharField()
        info = meta.column_info(None, col)

        self.assertIs(info.column, col)
        self.assertEqual(repr(info), "<string_column_info(<None>.None)>")

    def test_column_info(self):
        info = meta.model_info(Vehicle)

        col = info.primary_keys["id"]
        self.assertEqual(col.name, "id")
        self.assertDictEqual(
            {
                "help_text": "The primary key",
                "label": "Id",
                "required": True,
                "validators": [django_validators.validate_integer],
            },
            col.field_kwargs,
        )
        self.assertIs(col.validators, col.column.info["validators"])
        self.assertTrue(col.required)

    def test_default_initial(self):
        info = meta.model_info(Business)

        col = info.employees
        self.assertDictEqual(
            {
                "help_text": None,
                "initial": 5,
                "label": "Employees",
                "required": True,
                "validators": [django_validators.validate_integer],
            },
            col.field_kwargs,
        )

    def test_column_info_enum(self):
        info = meta.model_info(Vehicle)
        col = info.type
        self.assertDictEqual(
            {"choices": VehicleType, "help_text": None, "label": "Type", "required": True, "validators": []},
            col.field_kwargs,
        )
        self.assertTrue(col.required)

    def test_column_info_enum_from_class_from_info(self):
        info = meta.column_info(sa.Column(sa.Enum(VehicleType), info={"form_class": djangofields.IntegerField}))
        self.assertIsInstance(info, meta.enum_column_info)
        self.assertEqual(info.form_class, djangofields.IntegerField)

    def test_column_info_boolean_from_class_from_info(self):
        info = meta.column_info(sa.Column(sa.Boolean(), info={"form_class": djangofields.IntegerField}))
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
        column = meta.column_info(dbfields.TextField(label="dummy"))
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
        self.assertEqual(repr(col), "<enum_column_info(Vehicle.paint)>")

    def test_plain_sqla(self):
        info = meta.model_info(AllKindsOfFields)
        col = info.decimal
        self.assertDictEqual(
            {"help_text": None, "label": "Decimal", "required": False, "validators": []}, col.field_kwargs
        )
