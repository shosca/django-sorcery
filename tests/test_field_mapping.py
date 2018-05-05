# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import forms as djangoforms
from django.forms import fields as djangofields

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

    def test_build_boolean_field_not_nullable(self):

        class Meta:
            model = AllKindsOfFields
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()
        self.assertIn("isit", fields)

        field = fields["isit"]
        self.assertIsInstance(field, djangofields.BooleanField)

    def test_build_integer_field(self):

        class Meta:
            model = AllKindsOfFields
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()
        self.assertIn("integer", fields)

        field = fields["integer"]
        self.assertIsInstance(field, djangofields.IntegerField)

    def test_build_text_field(self):

        class Meta:
            model = AllKindsOfFields
            session = db

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()
        self.assertIn("text", fields)

        field = fields["text"]
        self.assertIsInstance(field, djangofields.CharField)
        self.assertIsInstance(field.widget, djangoforms.Textarea)
