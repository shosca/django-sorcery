# -*- coding: utf-8 -*-
import json

from django.core.exceptions import ValidationError

from django_sorcery import fields
from django_sorcery.forms import apply_limit_choices_to_form_field, modelform_factory

from .base import TestCase
from .testapp.models import CompositePkModel, Owner, Vehicle, VehicleType, db


class TestEnumField(TestCase):
    def test_field(self):
        field = fields.EnumField(enum_class=VehicleType)

        with self.assertRaises(ValidationError) as ctx:
            value = field.clean(None)
        self.assertEqual(ctx.exception.code, "required")

        with self.assertRaises(ValidationError) as ctx:
            value = field.clean("")
        self.assertEqual(ctx.exception.code, "required")
        value = field.to_python("")

        value = field.clean("car")
        self.assertEqual(value, VehicleType.car)

        value = field.clean("Car")
        self.assertEqual(value, VehicleType.car)

        value = field.to_python(VehicleType.car)
        self.assertEqual(value, VehicleType.car)

        with self.assertRaises(ValidationError):
            field.clean("blue")

        value = field.valid_value(None)
        self.assertFalse(value)

        value = field.prepare_value(VehicleType.car)
        self.assertEqual(value, "car")

        value = field.bound_data(VehicleType.car, None)
        self.assertEqual(value, "car")

        value = field.bound_data(None, None)
        self.assertIsNone(value)

        value = field.bound_data(None, VehicleType.car)
        self.assertIsNone(value, "car")

        value = field.prepare_value(None)
        self.assertFalse(value)

    def test_field_not_required(self):
        field = fields.EnumField(enum_class=VehicleType, required=False)

        value = field.clean(None)
        self.assertIsNone(value)

        value = field.clean("")
        self.assertIsNone(value)

        value = field.clean("car")
        self.assertEqual(value, VehicleType.car)

        value = field.clean("Car")
        self.assertEqual(value, VehicleType.car)

        with self.assertRaises(ValidationError):
            field.to_python("blue")

        value = field.bound_data(VehicleType.car, None)
        self.assertEqual(value, "car")

        value = field.bound_data(None, None)
        self.assertIsNone(value)

        value = field.bound_data(None, VehicleType.car)
        self.assertIsNone(value, "car")


class TestModelChoiceField(TestCase):
    def setUp(self):
        super().setUp()
        db.add_all([Owner(first_name="first_name {}".format(i), last_name="last_name {}".format(i)) for i in range(10)])
        db.flush()

    def test_apply_limit_value(self):

        field = fields.ModelChoiceField(Owner, db, limit_choices_to=[Owner.first_name == "first_name 1"])
        apply_limit_choices_to_form_field(field)
        self.assertEqual(field.queryset.count(), 1)

    def test_apply_limit_callable(self):
        def limit_choices_to():
            return [Owner.first_name == "first_name 1"]

        field = fields.ModelChoiceField(Owner, db, required=True, limit_choices_to=limit_choices_to)
        apply_limit_choices_to_form_field(field)
        self.assertEqual(field.queryset.count(), 1)

    def test_choices(self):

        field = fields.ModelChoiceField(Owner, db)

        self.assertListEqual(
            list(field.choices), [("", field.empty_label)] + [(owner.id, str(owner)) for owner in Owner.query]
        )

        field = fields.ModelChoiceField(Owner, db, required=True, initial=1)
        self.assertListEqual(list(field.choices), [(owner.id, str(owner)) for owner in Owner.query])

    def test_get_object(self):

        owner = Owner.objects.first()

        field = fields.ModelChoiceField(Owner, db)

        self.assertIsNone(field.get_object(None))

        owner = field.get_object(owner.id)
        self.assertIsNotNone(owner)
        self.assertIsInstance(owner, Owner)

        with self.assertRaises(ValidationError) as ctx:
            field.get_object(0)

        self.assertEqual(
            ctx.exception.args,
            ("Select a valid choice. That choice is not one of the available choices.", "invalid_choice", None),
        )

    def test_get_object_composite_pk(self):
        instance = CompositePkModel(id=1, pk=2)
        db.add(instance)
        db.flush()

        field = fields.ModelChoiceField(CompositePkModel, db)
        pks = field.prepare_value(instance)

        obj = field.get_object(json.dumps(pks))
        self.assertIsNotNone(obj)
        self.assertIs(obj, instance)

    def test_to_python(self):
        owner = Owner.objects.first()
        field = fields.ModelChoiceField(Owner, db)
        owner = field.to_python(owner.id)
        self.assertIsNotNone(owner)
        self.assertIsInstance(owner, Owner)

    def test_label_from_instance(self):
        owner = Owner.objects.first()

        field = fields.ModelChoiceField(Owner, db)

        self.assertEqual(field.label_from_instance(Owner.query.get(owner.id)), repr(owner))

    def test_prepare_instance_value(self):
        field = fields.ModelChoiceField(Owner, db)
        owner = Owner.objects.first()

        pks = field.prepare_instance_value(Owner.query.get(owner.id))
        self.assertEqual(pks, owner.id)

    def test_prepare_instance_value_composite(self):
        field = fields.ModelChoiceField(CompositePkModel, db)

        pks = field.prepare_instance_value(CompositePkModel(id=1, pk="a"))
        self.assertDictEqual(pks, {"id": 1, "pk": "a"})

    def test_prepare_value(self):
        field = fields.ModelChoiceField(CompositePkModel, db)
        pks = field.prepare_value(CompositePkModel(id=1, pk="a"))
        self.assertDictEqual(pks, {"id": 1, "pk": "a"})

    def test_validate(self):
        field = fields.ModelChoiceField(Owner, db, required=True)

        self.assertIsNone(field.validate(1))

        with self.assertRaises(ValidationError):
            field.validate(None)

    def test_get_bound_field(self):
        db.rollback()
        form = modelform_factory(Vehicle, fields=("owner",), session=db)()
        field = form.fields["owner"]
        bf = field.get_bound_field(form, "owner")
        self.assertHTMLEqual(
            str(bf), '<select name="owner" id="id_owner"><option value="" selected>---------</option></select>'
        )


class TestModelMultipleChoiceField(TestCase):
    def setUp(self):
        super().setUp()
        db.add_all([Owner(first_name="first_name {}".format(i), last_name="last_name {}".format(i)) for i in range(10)])
        db.flush()

    def test_to_python(self):
        field = fields.ModelMultipleChoiceField(Owner, db)
        owner1, owner2, owner3 = Owner.objects[:3]

        self.assertEqual(field.to_python(None), [])

        self.assertEqual(field.to_python([owner1.id, owner2.id, owner3.id]), [owner1, owner2, owner3])

    def test_prepare_value(self):
        field = fields.ModelMultipleChoiceField(Owner, db)
        owner1, owner2, owner3 = Owner.objects[:3]

        self.assertIsNone(field.prepare_value(None))

        self.assertEqual(field.prepare_value([owner1, owner2, owner3]), [owner1.id, owner2.id, owner3.id])
