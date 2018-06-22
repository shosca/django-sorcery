# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError

from django_sorcery import fields
from django_sorcery.forms import modelform_factory

from .base import TestCase
from .models import CompositePkModel, Owner, Vehicle, VehicleType, db


class TestEnumField(TestCase):
    def test_field(self):
        field = fields.EnumField(enum_class=VehicleType)

        value = field.to_python(None)
        self.assertIsNone(value)

        value = field.to_python("car")
        self.assertEqual(value, VehicleType.car)

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

        value = field.valid_value(None)
        self.assertTrue(value)

        value = field.valid_value("car")
        self.assertFalse(value)

        value = field.valid_value(VehicleType.car)
        self.assertTrue(value)

        value = field.valid_value(VehicleType.car)
        self.assertTrue(value)

        value = field.bound_data(VehicleType.car, None)
        self.assertEqual(value, "car")

        value = field.bound_data(None, None)
        self.assertIsNone(value)

        value = field.bound_data(None, VehicleType.car)
        self.assertIsNone(value, "car")


class TestModelChoiceField(TestCase):
    def setUp(self):
        super(TestModelChoiceField, self).setUp()
        db.add_all([Owner(first_name="first_name {}".format(i), last_name="last_name {}".format(i)) for i in range(10)])
        db.flush()

    def test_apply_limit(self):

        field = fields.ModelChoiceField(Owner, db, limit_choices_to=[Owner.id == 1])
        fields.apply_limit_choices_to_form_field(field)
        self.assertEqual(field.queryset.count(), 1)

    def test_choices(self):

        field = fields.ModelChoiceField(Owner, db)

        self.assertListEqual(
            list(field.choices), [("", field.empty_label)] + [(owner.id, str(owner)) for owner in Owner.query]
        )

        field = fields.ModelChoiceField(Owner, db, required=True, initial=1)
        self.assertListEqual(list(field.choices), [(owner.id, str(owner)) for owner in Owner.query])

    def test_get_object(self):

        field = fields.ModelChoiceField(Owner, db)

        self.assertIsNone(field.get_object(None))

        owner = field.get_object(1)
        self.assertIsNotNone(owner)
        self.assertIsInstance(owner, Owner)

        with self.assertRaises(ValidationError) as ctx:
            field.get_object(100)

        self.assertEqual(
            ctx.exception.args,
            ("Select a valid choice. That choice is not one of the available choices.", "invalid_choice", None),
        )

    def test_to_python(self):

        field = fields.ModelChoiceField(Owner, db)
        owner = field.to_python(1)
        self.assertIsNotNone(owner)
        self.assertIsInstance(owner, Owner)

    def test_label_from_instance(self):
        field = fields.ModelChoiceField(Owner, db)

        self.assertEqual(
            field.label_from_instance(Owner.query.get(1)),
            "Owner(id=1, first_name='first_name 0', last_name='last_name 0')",
        )

    def test_prepare_instance_value(self):
        field = fields.ModelChoiceField(Owner, db)

        pks = field.prepare_instance_value(Owner.query.get(1))
        self.assertEqual(pks, 1)

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
            str(bf), '<select name="owner" required id="id_owner"><option value="" selected>---------</option></select>'
        )


class TestModelMultipleChoiceField(TestCase):
    def setUp(self):
        super(TestModelMultipleChoiceField, self).setUp()
        db.add_all([Owner(first_name="first_name {}".format(i), last_name="last_name {}".format(i)) for i in range(10)])
        db.flush()

    def test_to_python(self):
        field = fields.ModelMultipleChoiceField(Owner, db)

        self.assertEqual(field.to_python(None), [])

        self.assertEqual(field.to_python([1, 2, 3]), [Owner.query.get(1), Owner.query.get(2), Owner.query.get(3)])

    def test_prepare_value(self):
        field = fields.ModelMultipleChoiceField(Owner, db)

        self.assertIsNone(field.prepare_value(None))

        self.assertEqual(field.prepare_value([Owner.query.get(1), Owner.query.get(2), Owner.query.get(3)]), [1, 2, 3])
