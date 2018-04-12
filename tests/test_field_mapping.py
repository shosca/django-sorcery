# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.forms.fields import CharField

from django_sorcery.field_mapping import ModelFieldMapper
from django_sorcery.forms import SQLAModelFormOptions

from .base import TestCase
from .models import Owner, Vehicle, db


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

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(sorted(list(fields.keys())), ["first_name", "last_name", "vehicles"])

    def test_get_fields_with_include(self):

        class Meta:
            model = Owner
            fields = ["first_name"]

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(list(fields.keys()), ["first_name"])

    def test_get_fields_with_exclude(self):

        class Meta:
            model = Owner
            exclude = ["first_name", "vehicles"]

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertListEqual(list(fields.keys()), ["last_name"])

    def test_get_fields_formfield_callback(self):

        self.callback_called = False

        def callback(attr, **kwargs):
            self.callback_called = True
            return CharField()

        class Meta:
            model = Owner
            fields = ["first_name"]

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta), formfield_callback=callback)

        fields = mapper.get_fields()

        self.assertTrue(self.callback_called)
        self.assertListEqual(list(fields.keys()), ["first_name"])

    def test_get_fields_no_private(self):

        class Meta:
            model = Vehicle

        mapper = ModelFieldMapper(SQLAModelFormOptions(Meta))

        fields = mapper.get_fields()

        self.assertEqual(
            list(sorted(fields.keys())), ["created_at", "is_used", "name", "options", "owner", "paint", "parts", "type"]
        )
        self.assertNotIn(Vehicle._owner_id.key, fields)
