# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bs4 import BeautifulSoup

from django.core.exceptions import ImproperlyConfigured, ValidationError

from django_sorcery.forms import ALL_FIELDS, ModelForm, modelform_factory

from .base import TestCase
from .models import ClassicModel, ModelFullCleanFail, Option, Owner, Vehicle, VehicleType, db


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
            {"paint": "", "created_at": None, "options": [], "parts": [], "name": "", "is_used": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(form.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    "<p>",
                    '  <label for="id_created_at">Created at:</label>',
                    '  <input type="text" name="created_at" id="id_created_at" />' "</p>",
                    "<p>",
                    '  <label for="id_is_used">Is used:</label>',
                    '  <select name="is_used" id="id_is_used">',
                    '    <option value="1" selected>Unknown</option>',
                    '    <option value="2">Yes</option>',
                    '    <option value="3">No</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_name">Name:</label>',
                    '  <input id="id_name" name="name" type="text" />',
                    '  <span class="helptext">' "    The name of the vehicle",
                    "  </span>",
                    "</p>",
                    "<p>",
                    '  <label for="id_options">Options:</label>',
                    '  <select id="id_options" multiple="multiple" name="options">',
                    "    <option value=\"1\">Option(id=1, name='Option 1')</option>",
                    "    <option value=\"2\">Option(id=2, name='Option 2')</option>",
                    "    <option value=\"3\">Option(id=3, name='Option 3')</option>",
                    "    <option value=\"4\">Option(id=4, name='Option 4')</option>",
                    "  </select>",
                    "</p>",
                    '<ul class="errorlist">',
                    "  <li>",
                    "    This field is required.",
                    "  </li>",
                    "</ul>",
                    "<p>",
                    '  <label for="id_owner">Owner:</label>',
                    '  <select id="id_owner" name="owner" required>',
                    "    <option selected value>---------</option>",
                    "    <option value=\"1\">Owner(id=1, first_name='Test', last_name='Owner')</option>",
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_paint">Paint:</label>',
                    '  <select id="id_paint" name="paint">',
                    "    <option selected value></option>",
                    '    <option value="red">red</option>',
                    '    <option value="green">green</option>',
                    '    <option value="blue">blue</option>',
                    '    <option value="silver">silver</option>',
                    '    <option value="pink">pink</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_parts">Parts:</label>',
                    '  <select id="id_parts" multiple="multiple" name="parts">',
                    "  </select>",
                    "</p>",
                    '<ul class="errorlist">',
                    "  <li>",
                    "    This field is required.",
                    "  </li>",
                    "</ul>",
                    "<p>",
                    '  <label for="id_type">Type:</label>',
                    '  <select id="id_type" name="type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                ]
            ),
            "html.parser",
        )

        self.assertEqual(soup.prettify(), expected_soup.prettify())

    def test_modelform_factory_instance_render(self):
        form_class = modelform_factory(Vehicle, fields=ALL_FIELDS, session=db)
        vehicle = Vehicle(owner=Owner.query.get(1), type=VehicleType.car)
        form = form_class(instance=vehicle, data={})

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {"owner": ["This field is required."], "type": ["This field is required."]})
        self.assertEqual(
            form.initial,
            {"paint": None, "created_at": None, "type": VehicleType.car, "name": None, "is_used": None, "owner": 1},
        )
        self.assertEqual(
            form.cleaned_data,
            {"paint": "", "created_at": None, "options": [], "parts": [], "name": "", "is_used": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(form.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    "<p>",
                    '  <label for="id_created_at">Created at:</label>',
                    '  <input type="text" name="created_at" id="id_created_at" />' "</p>",
                    "<p>",
                    '  <label for="id_is_used">Is used:</label>',
                    '  <select name="is_used" id="id_is_used">',
                    '    <option value="1" selected>Unknown</option>',
                    '    <option value="2">Yes</option>',
                    '    <option value="3">No</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_name">Name:</label>',
                    '  <input id="id_name" name="name" type="text" />',
                    '  <span class="helptext">' "    The name of the vehicle",
                    "  </span>",
                    "</p>",
                    "<p>",
                    '  <label for="id_options">Options:</label>',
                    '  <select id="id_options" multiple="multiple" name="options">',
                    "    <option value=\"1\">Option(id=1, name='Option 1')</option>",
                    "    <option value=\"2\">Option(id=2, name='Option 2')</option>",
                    "    <option value=\"3\">Option(id=3, name='Option 3')</option>",
                    "    <option value=\"4\">Option(id=4, name='Option 4')</option>",
                    "  </select>",
                    "</p>",
                    '<ul class="errorlist">',
                    "  <li>",
                    "    This field is required.",
                    "  </li>",
                    "</ul>",
                    "<p>",
                    '  <label for="id_owner">Owner:</label>',
                    '  <select id="id_owner" name="owner" required>',
                    "    <option selected value>---------</option>",
                    "    <option value=\"1\">Owner(id=1, first_name='Test', last_name='Owner')</option>",
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_paint">Paint:</label>',
                    '  <select id="id_paint" name="paint">',
                    "    <option selected value></option>",
                    '    <option value="red">red</option>',
                    '    <option value="green">green</option>',
                    '    <option value="blue">blue</option>',
                    '    <option value="silver">silver</option>',
                    '    <option value="pink">pink</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_parts">Parts:</label>',
                    '  <select id="id_parts" multiple="multiple" name="parts">',
                    "  </select>",
                    "</p>",
                    '<ul class="errorlist">',
                    "  <li>",
                    "    This field is required.",
                    "  </li>",
                    "</ul>",
                    "<p>",
                    '  <label for="id_type">Type:</label>',
                    '  <select id="id_type" name="type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                ]
            ),
            "html.parser",
        )

        self.maxDiff = None
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_form_field_callback_in_base_meta(self):

        self.callback_called = False

        def callback(*args, **kwargs):
            self.callback_called = True

        class OwnerBaseForm(ModelForm):
            class Meta:
                model = Owner
                session = db
                fields = ALL_FIELDS
                formfield_callback = staticmethod(callback)

        class OwnerForm(OwnerBaseForm):
            pass

        self.assertTrue(self.callback_called)

    def test_fields_bad_value(self):

        with self.assertRaises(TypeError) as ctx:
            modelform_factory(Owner, ModelForm, fields="abc1234")

        self.assertEqual(
            ctx.exception.args, ("OwnerForm.Meta.fields cannot be a string. Did you mean to type: ('abc1234',)?",)
        )

    def test_empty_fields_and_exclude(self):

        with self.assertRaises(ImproperlyConfigured) as ctx:

            class OwnerForm(ModelForm):
                class Meta:
                    model = Owner

        self.assertEqual(
            ctx.exception.args,
            (
                "Creating a ModelForm without either the 'fields' attribute or the 'exclude' attribute is prohibited; "
                "form OwnerForm needs updating.",
            ),
        )

    def test_modelform_no_model(self):
        class OwnerForm(ModelForm):
            pass

        with self.assertRaises(ValueError) as ctx:
            OwnerForm()

        self.assertEqual(ctx.exception.args, ("ModelForm has no model class specified.",))

    def test_modelform_no_session(self):
        class OwnerForm(ModelForm):
            class Meta:
                model = Owner
                fields = ALL_FIELDS

        with self.assertRaises(ValueError) as ctx:
            OwnerForm()

        self.assertEqual(ctx.exception.args, ("ModelForm has no session specified.",))

    def test_modelform_custom_setter(self):
        class OwnerForm(ModelForm):
            class Meta:
                model = Owner
                session = db
                fields = ("first_name",)

            def set_first_name(self, instance, name, field, value):
                instance.first_name = "other"

        form = OwnerForm(data={"first_name": "something"})

        instance = form.save()

        self.assertEqual(instance.first_name, "other")

    def test_modelform_validation_with_model_clean(self):
        class VehicleForm(ModelForm):
            class Meta:
                model = Vehicle
                session = db
                fields = ("paint", "name")

        form = VehicleForm(data={"name": "Bad Vehicle"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"__all__": ["Name cannot be `Bad Value`"]})

    def test_modelform_validation_with_field_clean(self):
        class VehicleForm(ModelForm):
            class Meta:
                model = Vehicle
                session = db
                fields = ("paint", "name")

        form = VehicleForm(data={"name": "Vehicle", "paint": "pink"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"paint": ["Can't have a pink car"]})

    def test_modelform_save_with_errors(self):
        class VehicleForm(ModelForm):
            class Meta:
                model = Vehicle
                session = db
                fields = ("type", "name")

        form = VehicleForm(data={"name": "something"})

        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError) as ctx:
            form.save()

        self.assertEqual(ctx.exception.args, ("The Vehicle could not be saved because the data didn't validate.",))

    def test_modelform_model_full_clean_validate(self):
        class BadModelForm(ModelForm):
            class Meta:
                model = ModelFullCleanFail
                session = db
                fields = ("name",)

        form = BadModelForm(data={"name": "bad"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"__all__": ["bad model"]})

    def test_modelform_clean_with_classic_model(self):
        class ClassicModelForm(ModelForm):
            class Meta:
                model = ClassicModel
                session = db
                fields = ("name",)

        form = ClassicModelForm(data={"name": "classic"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.instance.name, "classic")

    def test_modelform_factory_with_formfield_callback(self):

        self.callback_called = False

        def callback(*args, **kwargs):
            self.callback_called = True

        modelform_factory(Owner, fields=ALL_FIELDS, formfield_callback=callback, session=db)

        self.assertTrue(self.callback_called)

    def test_modelform_factory_with_no_fields_exclude(self):

        with self.assertRaises(ImproperlyConfigured) as ctx:
            modelform_factory(Owner, session=db)

        self.assertEqual(
            ctx.exception.args,
            ("Calling modelform_factory without defining 'fields' or 'exclude' explicitly is prohibited.",),
        )

    def test_update_errors(self):
        class OwnerForm(ModelForm):
            class Meta:
                model = Owner
                session = db
                fields = ("first_name", "last_name")
                error_messages = {"__all__": {"required": "Last name is required"}}

        form = OwnerForm(data={"first_name": "name"})
        self.assertTrue(form.is_valid())

        form = OwnerForm(data={"first_name": "name"})
        form._update_errors("error")
        self.assertDictEqual(form.errors, {"__all__": ["error"]})

        form = OwnerForm(data={"first_name": "name"})
        form._update_errors({"first_name": "name error"})
        self.assertDictEqual(form.errors, {"first_name": ["name error"]})

        form = OwnerForm(data={"first_name": "name"})
        error = ValidationError({"first_name": "name error"})
        form._update_errors(error)
        self.assertDictEqual(form.errors, {"first_name": ["name error"]})

        form = OwnerForm(data={"first_name": "name"})
        error = ValidationError({"dummy": ValidationError("error")})
        with self.assertRaises(ValueError):
            form._update_errors(error)

        form = OwnerForm(data={"first_name": "name"})
        error = ValidationError({"first_name": [ValidationError("first_name", code="required")]})
        form._update_errors(error)
        self.assertDictEqual(form.errors, {"first_name": ["This field is required."]})

        form = OwnerForm(data={"last_name": "name"})
        error = ValidationError(ValidationError("Last name is required."))
        form._update_errors(error)
        self.assertDictEqual(form.errors, {"__all__": ["Last name is required."]})
