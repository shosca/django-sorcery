# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bs4 import BeautifulSoup

from django_sorcery.forms import ALL_FIELDS, modelform_factory

from .base import TestCase
from .models import Option, Owner, Vehicle, db


class TestModelForm(TestCase):

    def setUp(cls):
        super(TestModelForm, cls).setUp()
        db.add(Owner(id=1, first_name="Test", last_name="Owner"))
        db.add_all(
            [
                Option(id=1, name="Option 1"),
                Option(id=2, name="Option 2"),
                Option(id=3, name="Option 3"),
                Option(id=4, name="Option 4"),
            ]
        )
        db.flush()

    def test_modelform_factory_fields(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        form = form_class()
        self.assertListEqual(
            sorted(form.fields.keys()), ["created_at", "is_used", "name", "options", "owner", "paint", "parts", "type"]
        )

    def test_modelform_factory_instance_validate(self):
        vehicle = Vehicle(owner=Owner.query.get(1))
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        form = form_class(instance=vehicle, data={"name": "testing"})
        self.assertFalse(form.is_valid())
        self.assertEqual({"type": ["This field is required."], "owner": ["This field is required."]}, form.errors)

    def test_modelform_factory_instance_save(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        data = {"name": "testing", "type": "car", "owner": 1}
        form = form_class(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

    def test_modelform_factory_modelchoicefield_choices(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        data = {"name": "testing", "type": "car", "owner": 1}
        form = form_class(data=data)

        owner_choices = form.fields["owner"].choices
        option_choices = form.fields["options"].choices
        self.assertEqual(len(owner_choices), 2)
        self.assertEqual(len(option_choices), 4)

    def test_modelform_factory_new_render(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        form = form_class(data={})

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {"owner": ["This field is required."], "type": ["This field is required."]})
        self.assertEqual(form.initial, {"paint": None, "created_at": None, "type": None, "name": None, "is_used": None})
        self.assertEqual(
            form.cleaned_data,
            {"paint": "", "created_at": None, "options": [], "parts": [], "name": u"", "is_used": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(form.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    '<p><label for="id_created_at">Created at:</label> <input type="text" name="created_at" id="id_created_at" /></p>',
                    '<p><label for="id_is_used">Is used:</label> <select name="is_used" id="id_is_used">',
                    '  <option value="1" selected>Unknown</option>',
                    '  <option value="2">Yes</option>',
                    '  <option value="3">No</option>',
                    "</select></p>",
                    '<p><label for="id_name">Name:</label> <input type="text" name="name" id="id_name" /> <span class="helptext">The name of the vehicle</span></p>',
                    '<p><label for="id_options">Options:</label> <select name="options" multiple="multiple" id="id_options">',
                    "</select></p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    '<p><label for="id_owner">Owner:</label> <select name="owner" id="id_owner">',
                    "</select></p>",
                    '<p><label for="id_paint">Paint:</label> <select name="paint" id="id_paint">',
                    '  <option value="" selected></option>',
                    '  <option value="red">red</option>',
                    '  <option value="green">green</option>',
                    '  <option value="blue">blue</option>',
                    '  <option value="silver">silver</option>',
                    "</select></p>",
                    '<p><label for="id_parts">Parts:</label> <select name="parts" multiple="multiple" id="id_parts">',
                    "</select></p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    '<p><label for="id_type">Type:</label> <select name="type" id="id_type">',
                    '  <option value="bus">Bus</option>',
                    '  <option value="car">Car</option>',
                    "</select></p>",
                ]
            ),
            "html.parser",
        )
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_modelform_factory_instance_render(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        vehicle = Vehicle(owner=Owner.query.get(1))
        form = form_class(instance=vehicle, data={})

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {"owner": ["This field is required."], "type": ["This field is required."]})
        self.assertEqual(form.initial, {"paint": None, "created_at": None, "type": None, "name": None, "is_used": None})
        self.assertEqual(
            form.cleaned_data,
            {"paint": "", "created_at": None, "options": [], "parts": [], "name": u"", "is_used": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(form.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    '<p><label for="id_created_at">Created at:</label> <input type="text" name="created_at" id="id_created_at" /></p>',
                    '<p><label for="id_is_used">Is used:</label> <select name="is_used" id="id_is_used">',
                    '  <option value="1" selected>Unknown</option>',
                    '  <option value="2">Yes</option>',
                    '  <option value="3">No</option>',
                    "</select></p>",
                    '<p><label for="id_name">Name:</label> <input type="text" name="name" id="id_name" /> <span class="helptext">The name of the vehicle</span></p>',
                    '<p><label for="id_options">Options:</label> <select name="options" multiple="multiple" id="id_options">',
                    "</select></p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    '<p><label for="id_owner">Owner:</label> <select name="owner" id="id_owner">',
                    "</select></p>",
                    '<p><label for="id_paint">Paint:</label> <select name="paint" id="id_paint">',
                    '  <option value="" selected></option>',
                    '  <option value="red">red</option>',
                    '  <option value="green">green</option>',
                    '  <option value="blue">blue</option>',
                    '  <option value="silver">silver</option>',
                    "</select></p>",
                    '<p><label for="id_parts">Parts:</label> <select name="parts" multiple="multiple" id="id_parts">',
                    "</select></p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    '<p><label for="id_type">Type:</label> <select name="type" id="id_type">',
                    '  <option value="bus">Bus</option>',
                    '  <option value="car">Car</option>',
                    "</select></p>",
                ]
            ),
            "html.parser",
        )

        self.maxDiff = None
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())
