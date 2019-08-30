# -*- coding: utf-8 -*-

from django import forms as djangoforms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms import fields as djangofields

from django_sorcery import fields as sorceryfields, forms

from .base import TestCase
from .testapp.models import (
    ClassicModel,
    ModelFullCleanFail,
    ModelOne,
    ModelTwo,
    Option,
    Owner,
    Part,
    Vehicle,
    VehicleType,
    db,
)


class TestFieldsForModel(TestCase):
    def test_default_case(self):
        fields = forms.fields_for_model(Vehicle, db)

        checks = [
            ("name", djangofields.CharField),
            ("type", sorceryfields.EnumField),
            ("created_at", djangofields.DateTimeField),
            ("paint", djangofields.TypedChoiceField),
            ("is_used", djangofields.BooleanField),
            ("msrp", djangofields.DecimalField),
            ("owner", sorceryfields.ModelChoiceField),
            ("parts", sorceryfields.ModelMultipleChoiceField),
            ("options", sorceryfields.ModelMultipleChoiceField),
        ]
        self.assertEqual(len(fields), len(checks))
        for name, fieldtype in checks:
            self.assertIsInstance(fields[name], fieldtype)

    def test_fields(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",))
        checks = [("name", djangofields.CharField)]
        self.assertEqual(len(fields), len(checks))
        for name, fieldtype in checks:
            self.assertIsInstance(fields[name], fieldtype)

    def test_exclude(self):
        fields = forms.fields_for_model(Vehicle, db, exclude=("name",))
        checks = [
            ("type", sorceryfields.EnumField),
            ("created_at", djangofields.DateTimeField),
            ("paint", djangofields.TypedChoiceField),
            ("is_used", djangofields.BooleanField),
            ("msrp", djangofields.DecimalField),
            ("owner", sorceryfields.ModelChoiceField),
            ("parts", sorceryfields.ModelMultipleChoiceField),
            ("options", sorceryfields.ModelMultipleChoiceField),
        ]
        self.assertEqual(len(fields), len(checks))
        for name, fieldtype in checks:
            self.assertIsInstance(fields[name], fieldtype)

    def test_widgets(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",), widgets={"name": djangoforms.Textarea})

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertIsInstance(fields["name"].widget, djangoforms.Textarea)

    def test_localized_fields(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",), localized_fields=("name",))

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertTrue(fields["name"].localize)

        fields = forms.fields_for_model(Vehicle, db, fields=("name",), localized_fields=djangoforms.ALL_FIELDS)

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertTrue(fields["name"].localize)

    def test_labels(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",), labels={"name": "dummy"})

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertEqual(fields["name"].label, "dummy")

    def test_help_texts(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",), help_texts={"name": "dummy"})

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertEqual(fields["name"].help_text, "dummy")

    def test_error_messages(self):
        fields = forms.fields_for_model(Vehicle, db, fields=("name",), error_messages={"name": {"required": "dummy"}})

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.CharField)
        self.assertEqual(fields["name"].error_messages, {"required": "dummy"})

    def test_field_classes(self):
        fields = forms.fields_for_model(
            Vehicle, db, fields=("name",), help_texts={"name": None}, field_classes={"name": djangofields.FileField}
        )

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.FileField)

    def test_formfield_callback(self):
        def callback(*args, **kwargs):
            return djangofields.FileField()

        fields = forms.fields_for_model(Vehicle, db, fields=("name",), formfield_callback=callback)

        self.assertEqual(len(fields), 1)
        self.assertIsInstance(fields["name"], djangofields.FileField)

        with self.assertRaises(TypeError):
            fields = forms.fields_for_model(Vehicle, db, fields=("name",), formfield_callback=[])


class TestApplyLimitChoicesTo(TestCase):
    def test_apply_limit(self):
        db.add_all([Owner(first_name="one"), Owner(first_name="one_more"), Owner(first_name="two")])
        field = sorceryfields.ModelChoiceField(Owner, db, limit_choices_to=[Owner.first_name.startswith("one")])
        forms.apply_limit_choices_to_form_field(field)
        self.assertEqual(field.queryset.count(), 2)


class TestModelToDict(TestCase):
    def test_model_to_dict(self):
        vehicle = Vehicle(
            id=1,
            name="vehicle",
            owner=Owner(id=2, first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(id=3, name="option 1"), Option(id=4, name="option 2")],
            parts=[Part(id=5, name="part 1"), Part(id=6, name="part 2")],
        )

        self.assertEqual(
            {
                "created_at": None,
                "is_used": True,
                "msrp": None,
                "name": "vehicle",
                "options": [3, 4],
                "owner": 2,
                "paint": "red",
                "parts": [5, 6],
                "type": VehicleType.car,
            },
            forms.model_to_dict(vehicle),
        )

    def test_model_to_dict_exclude(self):
        vehicle = Vehicle(
            id=1,
            name="vehicle",
            owner=Owner(id=2, first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(id=3, name="option 1"), Option(id=4, name="option 2")],
            parts=[Part(id=5, name="part 1"), Part(id=6, name="part 2")],
        )

        self.assertEqual(
            {
                "created_at": None,
                "is_used": True,
                "msrp": None,
                "name": "vehicle",
                "options": [3, 4],
                "paint": "red",
                "parts": [5, 6],
            },
            forms.model_to_dict(vehicle, exclude=["type", "owner"]),
        )

    def test_model_to_dict_fields(self):
        vehicle = Vehicle(
            name="vehicle",
            owner=Owner(first_name="first_name", last_name="last_name"),
            is_used=True,
            paint="red",
            type=VehicleType.car,
            options=[Option(name="option 1"), Option(name="option 2")],
            parts=[Part(name="part 1"), Part(name="part 2")],
        )

        self.assertEqual(
            {"is_used": True, "name": "vehicle", "paint": "red"},
            forms.model_to_dict(vehicle, fields=["name", "is_used", "paint"]),
        )

    def test_model_to_dict_private_relation(self):
        obj = ModelTwo(pk=2, name="two", _model_one=ModelOne(pk=1, name="one"))

        self.assertEqual({"name": "two"}, forms.model_to_dict(obj))


class TestModelForm(TestCase):
    def setUp(self):
        super().setUp()
        self.owner = Owner(first_name="Test", last_name="Owner")
        db.add(self.owner)

        self.options = [
            Option(id=1, name="Option 1"),
            Option(id=2, name="Option 2"),
            Option(id=3, name="Option 3"),
            Option(id=4, name="Option 4"),
        ]
        db.add_all(self.options)
        db.flush()

    def test_modelform_factory_fields(self):
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        form = form_class()
        self.assertListEqual(
            sorted(form.fields.keys()),
            ["created_at", "is_used", "msrp", "name", "options", "owner", "paint", "parts", "type"],
        )

    def test_modelform_factory_instance_validate(self):
        vehicle = Vehicle(owner=self.owner)
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        form = form_class(instance=vehicle, data={"name": "testing"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"type": ["This field is required."], "is_used": ["This field is required."]})

    def test_modelform_factory_instance_save(self):
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        data = {"name": "testing", "type": "car", "owner": self.owner.id, "is_used": True}
        form = form_class(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

    def test_modelform_factory_modelchoicefield_choices(self):
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        data = {"name": "testing", "type": "car", "owner": 1}
        form = form_class(data=data)

        owner_choices = form.fields["owner"].choices
        option_choices = form.fields["options"].choices
        self.assertEqual(len(owner_choices), 2)
        self.assertEqual(len(option_choices), 4)

    def test_modelform_factory_new_render(self):
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        form = form_class(data={})

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {"type": ["This field is required."], "is_used": ["This field is required."]})
        self.assertEqual(
            form.initial,
            {"paint": None, "created_at": None, "type": None, "msrp": None, "name": None, "is_used": False},
        )
        self.assertEqual(
            form.cleaned_data,
            {"paint": "", "created_at": None, "options": [], "parts": [], "msrp": None, "name": "", "owner": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = self.get_soup(form.as_p())
        expected_soup = self.get_soup(
            "".join(
                [
                    "<p>",
                    '  <label for="id_created_at">Created at:</label>',
                    '  <input type="text" name="created_at" id="id_created_at" />',
                    "</p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    "<p>",
                    '  <label for="id_is_used">Is used:</label>',
                    '  <input id="id_is_used" name="is_used" required="" type="checkbox"/>',
                    "</p>",
                    "<p>",
                    '  <label for="id_msrp">Msrp:</label>',
                    '  <input id="id_msrp" name="msrp" step="0.01" type="number"/>',
                    "</p>",
                    "<p>",
                    '  <label for="id_name">Name:</label>',
                    '  <input id="id_name" maxlength="50" name="name" type="text" />',
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
                    "<p>",
                    '  <label for="id_owner">Owner:</label>',
                    '  <select id="id_owner" name="owner">',
                    "    <option selected value>---------</option>",
                    '    <option value="{}">{}</option>'.format(self.owner.id, self.owner),
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
            )
        )
        self.assertEqual(soup.prettify(), expected_soup.prettify())

    def test_modelform_factory_instance_render(self):
        form_class = forms.modelform_factory(Vehicle, fields=forms.ALL_FIELDS, session=db)
        vehicle = Vehicle(owner=self.owner, type=VehicleType.car)
        form = form_class(instance=vehicle, data={})

        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {"type": ["This field is required."], "is_used": ["This field is required."]})
        self.assertEqual(
            form.initial,
            {
                "created_at": None,
                "is_used": False,
                "msrp": None,
                "name": None,
                "owner": self.owner.id,
                "paint": None,
                "type": VehicleType.car,
            },
        )
        self.assertEqual(
            form.cleaned_data,
            {"paint": "", "msrp": None, "created_at": None, "options": [], "parts": [], "name": "", "owner": None},
        )

        form.order_fields(sorted(form.fields.keys()))

        soup = self.get_soup(form.as_p())
        expected_soup = self.get_soup(
            "".join(
                [
                    "<p>",
                    '  <label for="id_created_at">Created at:</label>',
                    '  <input type="text" name="created_at" id="id_created_at" />',
                    "</p>",
                    '<ul class="errorlist"><li>This field is required.</li></ul>',
                    "<p>",
                    '  <label for="id_is_used">Is used:</label>',
                    '  <input id="id_is_used" name="is_used" required type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_msrp">Msrp:</label>',
                    '  <input id="id_msrp" name="msrp" step="0.01" type="number" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_name">Name:</label>',
                    '  <input id="id_name" maxlength="50" name="name" type="text" />',
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
                    "<p>",
                    '  <label for="id_owner">Owner:</label>',
                    '  <select id="id_owner" name="owner">',
                    "    <option selected value>---------</option>",
                    '    <option value="{}">{}</option>'.format(self.owner.id, self.owner),
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
            )
        )

        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_form_field_callback_in_base_meta(self):

        self.callback_called = False

        def callback(*args, **kwargs):
            self.callback_called = True

        class OwnerBaseForm(forms.ModelForm):
            class Meta:
                model = Owner
                session = db
                fields = forms.ALL_FIELDS
                formfield_callback = staticmethod(callback)

        class OwnerForm(OwnerBaseForm):
            pass

        self.assertTrue(self.callback_called)

    def test_fields_bad_value(self):

        with self.assertRaises(TypeError) as ctx:
            forms.modelform_factory(Owner, forms.ModelForm, fields="abc1234")

        self.assertEqual(
            ctx.exception.args, ("OwnerForm.Meta.fields cannot be a string. Did you mean to type: ('abc1234',)?",)
        )

    def test_empty_fields_and_exclude(self):

        with self.assertRaises(ImproperlyConfigured) as ctx:

            class OwnerForm(forms.ModelForm):
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
        class OwnerForm(forms.ModelForm):
            pass

        with self.assertRaises(ValueError) as ctx:
            OwnerForm()

        self.assertEqual(ctx.exception.args, ("ModelForm has no model class specified.",))

    def test_modelform_no_session(self):
        class OwnerForm(forms.ModelForm):
            class Meta:
                model = Owner
                fields = forms.ALL_FIELDS

        with self.assertRaises(ValueError) as ctx:
            OwnerForm()

        self.assertEqual(ctx.exception.args, ("ModelForm has no session specified.",))

    def test_modelform_custom_setter(self):
        class OwnerForm(forms.ModelForm):
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
        class VehicleForm(forms.ModelForm):
            class Meta:
                model = Vehicle
                session = db
                fields = ("paint", "name")

        form = VehicleForm(data={"name": "Bad Vehicle"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"__all__": ["Name cannot be `Bad Value`"]})

    def test_modelform_validation_with_field_clean(self):
        class VehicleForm(forms.ModelForm):
            class Meta:
                model = Vehicle
                session = db
                fields = ("paint", "name")

        form = VehicleForm(data={"name": "Vehicle", "paint": "pink"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"paint": ["Can't have a pink car"]})

    def test_modelform_save_with_errors(self):
        class VehicleForm(forms.ModelForm):
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
        class BadModelForm(forms.ModelForm):
            class Meta:
                model = ModelFullCleanFail
                session = db
                fields = ("name",)

        form = BadModelForm(data={"name": "bad"})
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {"__all__": ["bad model"]})

    def test_modelform_clean_with_classic_model(self):
        class ClassicModelForm(forms.ModelForm):
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

        forms.modelform_factory(Owner, fields=forms.ALL_FIELDS, formfield_callback=callback, session=db)

        self.assertTrue(self.callback_called)

    def test_modelform_factory_with_no_fields_exclude(self):

        with self.assertRaises(ImproperlyConfigured) as ctx:
            forms.modelform_factory(Owner, session=db)

        self.assertEqual(
            ctx.exception.args,
            ("Calling modelform_factory without defining 'fields' or 'exclude' explicitly is prohibited.",),
        )

    def test_update_errors(self):
        class OwnerForm(forms.ModelForm):
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
