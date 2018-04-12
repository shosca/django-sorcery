# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from bs4 import BeautifulSoup

from django_sorcery.forms import ALL_FIELDS
from django_sorcery.formsets import modelformset_factory

from .base import TestCase
from .models import Owner, db


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

    def test_modelformset_factory(self):
        formset_class = modelformset_factory(Owner, fields=ALL_FIELDS, session=db)
        formset = formset_class()

        self.assertEqual(formset.model, Owner)
        self.assertEqual(formset.session, db)

    def test_modelformset_factory_render(self):
        formset_class = modelformset_factory(Owner, fields="__all__", session=db)
        query = Owner.query

        formset = formset_class(queryset=query)

        self.assertEqual(len(formset.forms), 5)

        soup = BeautifulSoup(formset.as_p(), "html.parser")
        expected_soup = BeautifulSoup(
            "".join(
                [
                    '<input type="hidden" name="form-TOTAL_FORMS" value="5" id="id_form-TOTAL_FORMS" /><input type="hidden" name="form-INITIAL_FORMS" value="4" id="id_form-INITIAL_FORMS" /><input type="hidden" name="form-MIN_NUM_FORMS" value="0" id="id_form-MIN_NUM_FORMS" /><input type="hidden" name="form-MAX_NUM_FORMS" value="1000" id="id_form-MAX_NUM_FORMS" />',
                    '<p><label for="id_form-0-first_name">First name:</label> <input type="text" name="form-0-first_name" value="Test 1" id="id_form-0-first_name" /></p>',
                    '<p><label for="id_form-0-last_name">Last name:</label> <input type="text" name="form-0-last_name" value="Owner 1" id="id_form-0-last_name" /></p>',
                    '<p><label for="id_form-0-vehicles">Vehicles:</label> <select name="form-0-vehicles" multiple="multiple" id="id_form-0-vehicles">',
                    "</select></p>",
                    '<p><label for="id_form-0-id">Id:</label> <input type="text" name="form-0-id" value="1" id="id_form-0-id" /></p> <p><label for="id_form-1-first_name">First name:</label> <input type="text" name="form-1-first_name" value="Test 2" id="id_form-1-first_name" /></p>',
                    '<p><label for="id_form-1-last_name">Last name:</label> <input type="text" name="form-1-last_name" value="Owner 2" id="id_form-1-last_name" /></p>',
                    '<p><label for="id_form-1-vehicles">Vehicles:</label> <select name="form-1-vehicles" multiple="multiple" id="id_form-1-vehicles">',
                    "</select></p>",
                    '<p><label for="id_form-1-id">Id:</label> <input type="text" name="form-1-id" value="2" id="id_form-1-id" /></p> <p><label for="id_form-2-first_name">First name:</label> <input type="text" name="form-2-first_name" value="Test 3" id="id_form-2-first_name" /></p>',
                    '<p><label for="id_form-2-last_name">Last name:</label> <input type="text" name="form-2-last_name" value="Owner 3" id="id_form-2-last_name" /></p>',
                    '<p><label for="id_form-2-vehicles">Vehicles:</label> <select name="form-2-vehicles" multiple="multiple" id="id_form-2-vehicles">',
                    "</select></p>",
                    '<p><label for="id_form-2-id">Id:</label> <input type="text" name="form-2-id" value="3" id="id_form-2-id" /></p> <p><label for="id_form-3-first_name">First name:</label> <input type="text" name="form-3-first_name" value="Test 4" id="id_form-3-first_name" /></p>',
                    '<p><label for="id_form-3-last_name">Last name:</label> <input type="text" name="form-3-last_name" value="Owner 4" id="id_form-3-last_name" /></p>',
                    '<p><label for="id_form-3-vehicles">Vehicles:</label> <select name="form-3-vehicles" multiple="multiple" id="id_form-3-vehicles">',
                    "</select></p>",
                    '<p><label for="id_form-3-id">Id:</label> <input type="text" name="form-3-id" value="4" id="id_form-3-id" /></p> <p><label for="id_form-4-first_name">First name:</label> <input type="text" name="form-4-first_name" id="id_form-4-first_name" /></p>',
                    '<p><label for="id_form-4-last_name">Last name:</label> <input type="text" name="form-4-last_name" id="id_form-4-last_name" /></p>',
                    '<p><label for="id_form-4-vehicles">Vehicles:</label> <select name="form-4-vehicles" multiple="multiple" id="id_form-4-vehicles">',
                    "</select></p>",
                    '<p><label for="id_form-4-id">Id:</label> <input type="text" name="form-4-id" id="id_form-4-id" /></p>',
                ]
            ),
            "html.parser",
        )
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_modelformset_factory_edit(self):
        formset_class = modelformset_factory(Owner, fields="__all__", session=db)
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
            "form-4-first_name": "",
            "form-4-last_name": "",
        }

        formset = formset_class(queryset=query, data=data)
        instances = formset.save()
        db.expire_all()

        for owner in instances:
            self.assertEqual(owner.first_name, "Edited first name {}".format(owner.id))
            self.assertEqual(owner.last_name, "Edited last name {}".format(owner.id))
