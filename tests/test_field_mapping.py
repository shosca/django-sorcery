# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import forms as djangoforms
from django.forms import fields as djangofields

from django_sorcery import fields
from django_sorcery.db.meta import model_info
from django_sorcery.field_mapping import ModelFieldMapper
from django_sorcery.forms import SQLAModelFormOptions

from .base import TestCase
from .models import AllKindsOfFields, Owner, Vehicle, db


class TestFieldMapping(TestCase):
    def test_get_default_kwargs(self):
        class Meta:
            model = Owner
            session = db.session
            widgets = {"test": "widget"}
            labels = {"test": "label"}
            help_texts = {"test": "help_text"}
            error_messages = {"test": "error_message"}
            field_classes = {"test": "field_class"}
            localized_fields = ("test",)

        opts = SQLAModelFormOptions(Meta)
        mapper = ModelFieldMapper(opts)

        self.assertDictEqual({}, mapper.get_default_kwargs("none"))

        self.assertDictEqual(
            {
                "error_messages": "error_message",
                "form_class": "field_class",
                "help_text": "help_text",
                "label": "label",
                "localize": True,
                "widget": "widget",
            },
            mapper.get_default_kwargs("test"),
        )

        mapper.opts.localized_fields = "__all__"
        self.assertDictEqual(
            {
                "error_messages": "error_message",
                "form_class": "field_class",
                "help_text": "help_text",
                "label": "label",
                "localize": True,
                "widget": "widget",
            },
            mapper.get_default_kwargs("test"),
        )

    def test_get_fields(self):
        class Meta:
            model = Owner
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(sorted(list(fields.keys())), ["first_name", "last_name", "vehicles"])

    def test_get_fields_with_include(self):
        class Meta:
            model = Owner
            fields = ["first_name"]
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(list(fields.keys()), ["first_name"])

    def test_get_fields_with_exclude(self):
        class Meta:
            model = Owner
            exclude = ["first_name", "vehicles"]
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(list(fields.keys()), ["last_name"])

    def test_get_fields_formfield_callback(self):

        info = model_info(Owner)
        self.called_with = []

        def callback(attr, **kwargs):
            self.called_with.append(attr)
            return djangofields.CharField()

        class Meta:
            model = Owner
            fields = ["first_name", "vehicles"]

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta), formfield_callback=callback)

        fields = mapper.get_fields()

        self.assertListEqual(list(fields.keys()), ["first_name", "vehicles"])
        self.assertEqual(self.called_with, [info.properties["first_name"], info.relationships["vehicles"]])

    def test_get_fields_no_private(self):
        class Meta:
            model = Vehicle
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertEqual(
            list(sorted(fields.keys())), ["created_at", "is_used", "name", "options", "owner", "paint", "parts", "type"]
        )
        self.assertNotIn(Vehicle._owner_id.key, fields)


class TestTypeMap(TestCase):
    def setUp(self):
        super(TestTypeMap, self).setUp()

        class Meta:
            model = AllKindsOfFields
            session = db

        self.mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))
        self.fields = self.mapper.get_fields()

    def test_boolean_field_not_nullable(self):
        self.assertIn("boolean_notnull", self.fields)
        field = self.fields["boolean_notnull"]
        self.assertIsInstance(field, djangofields.BooleanField)

    def test_boolean_field(self):
        self.assertIn("boolean", self.fields)
        field = self.fields["boolean"]
        self.assertIsInstance(field, djangofields.NullBooleanField)

    def test_enum_field(self):
        self.assertIn("enum", self.fields)
        field = self.fields["enum"]
        self.assertIsInstance(field, fields.EnumField)

    def test_enum_choice_field(self):
        self.assertIn("enum_choice", self.fields)
        field = self.fields["enum_choice"]
        self.assertIsInstance(field, djangofields.TypedChoiceField)

    def test_bigint_field(self):
        self.assertIn("bigint", self.fields)
        field = self.fields["bigint"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_biginteger_field(self):
        self.assertIn("biginteger", self.fields)
        field = self.fields["biginteger"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_decimal_field(self):
        self.assertIn("decimal", self.fields)
        field = self.fields["decimal"]
        self.assertIsInstance(field, djangofields.DecimalField)

    def test_float_field(self):
        self.assertIn("float", self.fields)
        field = self.fields["float"]
        self.assertIsInstance(field, djangofields.FloatField)

    def test_int_field(self):
        self.assertIn("int", self.fields)
        field = self.fields["int"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_integer_field(self):
        self.assertIn("integer", self.fields)
        field = self.fields["integer"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_numeric_field(self):
        self.assertIn("numeric", self.fields)
        field = self.fields["numeric"]
        self.assertIsInstance(field, djangofields.DecimalField)

    def test_real_field(self):
        self.assertIn("real", self.fields)
        field = self.fields["real"]
        self.assertIsInstance(field, djangofields.FloatField)

    def test_smallint_field(self):
        self.assertIn("smallint", self.fields)
        field = self.fields["smallint"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_smallinteger_field(self):
        self.assertIn("smallinteger", self.fields)
        field = self.fields["smallinteger"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_char_field(self):
        self.assertIn("char", self.fields)
        field = self.fields["char"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_clob_field(self):
        self.assertIn("clob", self.fields)
        field = self.fields["clob"]
        self.assertIsInstance(field, djangofields.CharField)
        self.assertIsInstance(field.widget, djangoforms.Textarea)

    def test_nchar_field(self):
        self.assertIn("nchar", self.fields)
        field = self.fields["nchar"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_nvarchar_field(self):
        self.assertIn("nvarchar", self.fields)
        field = self.fields["nvarchar"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_string_field(self):
        self.assertIn("string", self.fields)
        field = self.fields["string"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_text_field(self):
        self.assertIn("text", self.fields)
        field = self.fields["text"]
        self.assertIsInstance(field, djangofields.CharField)
        self.assertIsInstance(field.widget, djangoforms.Textarea)

    def test_unicode_field(self):
        self.assertIn("unicode", self.fields)
        field = self.fields["unicode"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_unicodetext_field(self):
        self.assertIn("unicodetext", self.fields)
        field = self.fields["unicodetext"]
        self.assertIsInstance(field, djangofields.CharField)
        self.assertIsInstance(field.widget, djangoforms.Textarea)

    def test_varchar_field(self):
        self.assertIn("varchar", self.fields)
        field = self.fields["varchar"]
        self.assertIsInstance(field, djangofields.CharField)

    def test_date_field(self):
        self.assertIn("date", self.fields)
        field = self.fields["date"]
        self.assertIsInstance(field, djangofields.DateField)

    def test_datetime_field(self):
        self.assertIn("datetime", self.fields)
        field = self.fields["datetime"]
        self.assertIsInstance(field, djangofields.DateTimeField)

    def test_interval_field(self):
        self.assertIn("interval", self.fields)
        field = self.fields["interval"]
        self.assertIsInstance(field, djangofields.DurationField)

    def test_time_field(self):
        self.assertIn("time", self.fields)
        field = self.fields["time"]
        self.assertIsInstance(field, djangofields.TimeField)

    def test_timestamp_field(self):
        self.assertIn("timestamp", self.fields)
        field = self.fields["timestamp"]
        self.assertIsInstance(field, djangofields.DateTimeField)

    def test_binary_field(self):
        self.assertNotIn("binary", self.fields)

    def test_blob_field(self):
        self.assertNotIn("blob", self.fields)

    def test_largebinary_field(self):
        self.assertNotIn("largebinary", self.fields)

    def test_varbinary_field(self):
        self.assertNotIn("varbinary", self.fields)
