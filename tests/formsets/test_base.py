# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bs4 import BeautifulSoup

from django.core.exceptions import ImproperlyConfigured

from django_sorcery.forms import ALL_FIELDS
from django_sorcery.formsets import modelformset_factory

from ..base import TestCase
from ..models import Owner, db


class TestModelFormSet(TestCase):
    def setUp(cls):
        super(TestModelFormSet, cls).setUp()
        db.add_all(
            [
                Owner(first_name="Test 1", last_name="Owner 1"),
                Owner(first_name="Test 2", last_name="Owner 2"),
                Owner(first_name="Test 3", last_name="Owner 3"),
                Owner(first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.flush()

    def test_factory(self):
        formset_class = modelformset_factory(Owner, fields=ALL_FIELDS, session=db)
        formset = formset_class()

        self.assertEqual(formset.model, Owner)
        self.assertEqual(formset.session, db)

    def test_render(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db)
        query = Owner.query

        formset = formset_class(queryset=query)

        self.assertEqual(len(formset.forms), 5)

        for form in formset.forms:
            form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(formset.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    '<input type="hidden" name="form-TOTAL_FORMS" value="5" id="id_form-TOTAL_FORMS" />',
                    '<input type="hidden" name="form-INITIAL_FORMS" value="4" id="id_form-INITIAL_FORMS" />',
                    '<input type="hidden" name="form-MIN_NUM_FORMS" value="0" id="id_form-MIN_NUM_FORMS" />',
                    '<input type="hidden" name="form-MAX_NUM_FORMS" value="1000" id="id_form-MAX_NUM_FORMS" />',
                    "<p>",
                    '  <label for="id_form-0-first_name">First name:</label>',
                    '  <input type="text" name="form-0-first_name" id="id_form-0-first_name" value="Test 1" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-0-last_name">Last name:</label>',
                    '  <input type="text" name="form-0-last_name" id="id_form-0-last_name" value="Owner 1" />',
                    '  <input type="text" name="form-0-id" id="id_form-0-id" type="hidden" value="1" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-1-first_name">First name:</label>',
                    '  <input type="text" name="form-1-first_name" id="id_form-1-first_name" value="Test 2" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-1-last_name">Last name:</label>',
                    '  <input type="text" name="form-1-last_name" id="id_form-1-last_name" value="Owner 2" />',
                    '  <input type="text" name="form-1-id" id="id_form-1-id" type="hidden" value="2" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-2-first_name">First name:</label>',
                    '  <input type="text" name="form-2-first_name" id="id_form-2-first_name" value="Test 3" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-2-last_name">Last name:</label>',
                    '  <input type="text" name="form-2-last_name" id="id_form-2-last_name" value="Owner 3" />',
                    '  <input type="text" name="form-2-id" id="id_form-2-id" type="hidden" value="3" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-3-first_name">First name:</label>',
                    '  <input type="text" name="form-3-first_name" id="id_form-3-first_name" value="Test 4" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-3-last_name">Last name:</label>',
                    '  <input type="text" name="form-3-last_name" id="id_form-3-last_name" value="Owner 4" />',
                    '  <input type="text" name="form-3-id" id="id_form-3-id" type="hidden" value="4" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-4-first_name">First name:</label>',
                    '  <input type="text" name="form-4-first_name" id="id_form-4-first_name" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-4-last_name">Last name:</label>',
                    '  <input type="text" name="form-4-last_name" id="id_form-4-last_name" />',
                    "</p>",
                ]
            ),
            "html.parser",
        )
        self.maxDiff = None
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_edit(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db)
        query = Owner.query

        data = {
            "form-TOTAL_FORMS": "5",
            "form-INITIAL_FORMS": "4",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-first_name": "Edited first name 1",
            "form-0-last_name": "Edited last name 1",
            "form-1-id": "2",
            "form-1-first_name": "Edited first name 2",
            "form-1-last_name": "Edited last name 2",
            "form-2-id": "3",
            "form-2-first_name": "Edited first name 3",
            "form-2-last_name": "Edited last name 3",
            "form-3-id": "4",
            "form-3-first_name": "Edited first name 4",
            "form-3-last_name": "Edited last name 4",
            "form-4-id": "",
            "form-4-first_name": "Edited first name 5",
            "form-4-last_name": "Edited last name 5",
        }

        formset = formset_class(queryset=query, data=data)
        self.assertTrue(formset.is_valid())
        instances = formset.save()
        db.expire_all()

        for owner in instances:
            self.assertEqual(owner.first_name, "Edited first name {}".format(owner.id))
            self.assertEqual(owner.last_name, "Edited last name {}".format(owner.id))

    def test_edit_new_delete_ignore(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db, can_delete=True)

        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-first_name": "Edited first name 1",
            "form-0-last_name": "Edited last name 1",
            "form-0-DELETE": "on",
        }

        formset = formset_class(queryset=[], data=data)
        self.assertTrue(formset.is_valid())
        instances = formset.save()
        self.assertEqual(instances, [])
        self.assertEqual(formset.new_objects, [])
        self.assertEqual(formset.changed_objects, [])
        self.assertEqual(formset.deleted_objects, [])

    def test_delete_render(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db, can_delete=True)
        formset = formset_class(queryset=Owner.query)

        self.assertEqual(len(formset.forms), 5)

        for form in formset.forms:
            form.order_fields(sorted(form.fields.keys()))

        soup = BeautifulSoup(formset.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    '<input type="hidden" name="form-TOTAL_FORMS" value="5" id="id_form-TOTAL_FORMS" />',
                    '<input type="hidden" name="form-INITIAL_FORMS" value="4" id="id_form-INITIAL_FORMS" />',
                    '<input type="hidden" name="form-MIN_NUM_FORMS" value="0" id="id_form-MIN_NUM_FORMS" />',
                    '<input type="hidden" name="form-MAX_NUM_FORMS" value="1000" id="id_form-MAX_NUM_FORMS" />',
                    "<p>",
                    '  <label for="id_form-0-DELETE">Delete:</label>',
                    '  <input id="id_form-0-DELETE" name="form-0-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-0-first_name">First name:</label>',
                    '  <input type="text" name="form-0-first_name" id="id_form-0-first_name" value="Test 1" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-0-last_name">Last name:</label>',
                    '  <input type="text" name="form-0-last_name" id="id_form-0-last_name" value="Owner 1" />',
                    '  <input type="text" name="form-0-id" id="id_form-0-id" type="hidden" value="1" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-1-DELETE">Delete:</label>',
                    '  <input id="id_form-1-DELETE" name="form-1-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-1-first_name">First name:</label>',
                    '  <input type="text" name="form-1-first_name" id="id_form-1-first_name" value="Test 2" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-1-last_name">Last name:</label>',
                    '  <input type="text" name="form-1-last_name" id="id_form-1-last_name" value="Owner 2" />',
                    '  <input type="text" name="form-1-id" id="id_form-1-id" type="hidden" value="2" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-2-DELETE">Delete:</label>',
                    '  <input id="id_form-2-DELETE" name="form-2-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-2-first_name">First name:</label>',
                    '  <input type="text" name="form-2-first_name" id="id_form-2-first_name" value="Test 3" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-2-last_name">Last name:</label>',
                    '  <input type="text" name="form-2-last_name" id="id_form-2-last_name" value="Owner 3" />',
                    '  <input type="text" name="form-2-id" id="id_form-2-id" type="hidden" value="3" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-3-DELETE">Delete:</label>',
                    '  <input id="id_form-3-DELETE" name="form-3-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-3-first_name">First name:</label>',
                    '  <input type="text" name="form-3-first_name" id="id_form-3-first_name" value="Test 4" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-3-last_name">Last name:</label>',
                    '  <input type="text" name="form-3-last_name" id="id_form-3-last_name" value="Owner 4" />',
                    '  <input type="text" name="form-3-id" id="id_form-3-id" type="hidden" value="4" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-4-DELETE">Delete:</label>',
                    '  <input id="id_form-4-DELETE" name="form-4-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-4-first_name">First name:</label>',
                    '  <input type="text" name="form-4-first_name" id="id_form-4-first_name" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_form-4-last_name">Last name:</label>',
                    '  <input type="text" name="form-4-last_name" id="id_form-4-last_name" />',
                    "</p>",
                ]
            ),
            "html.parser",
        )
        self.maxDiff = None
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_delete(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db, can_delete=True)
        query = Owner.query

        data = {
            "form-TOTAL_FORMS": "5",
            "form-INITIAL_FORMS": "4",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": "1",
            "form-0-first_name": "Edited first name 1",
            "form-0-last_name": "Edited last name 1",
            "form-1-id": "2",
            "form-1-first_name": "Edited first name 2",
            "form-1-last_name": "Edited last name 2",
            "form-2-id": "3",
            "form-2-first_name": "Edited first name 3",
            "form-2-last_name": "Edited last name 3",
            "form-3-id": "4",
            "form-3-first_name": "Edited first name 4",
            "form-3-last_name": "Edited last name 4",
            "form-3-DELETE": "on",
            "form-4-id": "",
            "form-4-first_name": "",
            "form-4-last_name": "",
        }

        formset = formset_class(queryset=query, data=data)
        self.assertTrue(formset.is_valid())
        instances = formset.save()

        self.assertEqual(len(instances), 3)
        self.assertEqual(len(formset.deleted_objects), 1)
        self.assertEqual(Owner.query.count(), 3)

    def test_initial_extra(self):
        formset_class = modelformset_factory(Owner, fields="__all__", session=db)

        initial = [{"last_name": "test"}, None]

        formset = formset_class(queryset=Owner.query, initial=initial)
        extra_form = formset.forms[formset.initial_form_count()]

        self.assertEqual(extra_form.initial["last_name"], "test")

    def test_bad_initial(self):
        formset_class = modelformset_factory(Owner, fields="__all__", session=db, extra=2)

        initial = [None]

        formset = formset_class(queryset=Owner.query, initial=initial)
        extra_form = formset.forms[formset.initial_form_count() + 1]

        self.assertEqual(extra_form.initial["first_name"], None)
        self.assertEqual(extra_form.initial["last_name"], None)

    def test_no_queryset(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db)
        formset = formset_class()

        self.assertIsNone(formset.queryset)
        self.assertListEqual(formset.get_queryset(), Owner.query.all())

    def test_save_no_initial_forms(self):
        formset_class = modelformset_factory(Owner, fields=("first_name", "last_name"), session=db, extra=0)
        formset = formset_class(queryset=Owner.query.filter_by(id=99))
        self.assertEqual(formset.save(), [])

    def test_formset_factory_no_fields_exclude(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            modelformset_factory(Owner, fields=None, exclude=None, session=db)

        self.assertEqual(
            ctx.exception.args,
            ("Calling modelformset_factory without defining 'fields' or " "'exclude' explicitly is prohibited.",),
        )
