# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from django_sorcery import forms
from django_sorcery.views import edit

from ..appviews import OwnerCreateViewWithForm
from ..base import TestCase
from ..models import Owner, db


class TestCreateView(TestCase):
    def test_create(self):

        url = reverse("owner_create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context_data["view"], edit.CreateView)
        self.assertIsInstance(response.context_data["form"], forms.ModelForm)

        response = self.client.post(url, {"first_name": "Randall", "last_name": "Munroe"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owners_list"))

    def test_create_with_form_class(self):

        url = reverse("owner_create_form")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context_data["view"], edit.CreateView)
        self.assertTrue(type(response.context_data["form"]) is OwnerCreateViewWithForm.form_class)

    def test_create_bad_field_form_config(self):

        url = reverse("owner_create_field_form")

        with self.assertRaises(ImproperlyConfigured) as ctx:
            self.client.get(url)

        self.assertEqual(str(ctx.exception), "Specifying both 'fields' and 'form_class' is not permitted.")

    def test_create_get_success_url_bad_config(self):

        view = OwnerCreateViewWithForm()

        with self.assertRaises(ImproperlyConfigured) as ctx:
            view.get_success_url()

        self.assertEqual(
            str(ctx.exception), "No URL to redirect to. Either provide a url or override this function to return a url"
        )

    def test_create_form_invalid(self):

        url = reverse("vehicle_create")

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 200)

        form = response.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"type": ["This field is required."], "owner": ["This field is required."]})
        self.assertHTMLEqual(response.content.decode(), form.as_p())


class TestUpdateView(TestCase):
    def test_update(self):
        owner = Owner(first_name="Radnall", last_name="Munroe")
        db.add(owner)
        db.flush()

        url = reverse("owner_update", kwargs={"id": owner.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context_data["view"], edit.UpdateView)
        self.assertIsInstance(response.context_data["form"], forms.ModelForm)
        form = response.context_data["form"]
        view = response.context_data["view"]
        self.assertHTMLEqual(response.content.decode(), form.as_p())
        self.assertEqual(view.object, owner)

        response = self.client.post(url, {"first_name": "Patrick", "last_name": "Bateman"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owners_list"))

        self.assertEqual(owner.first_name, "Patrick")
        self.assertEqual(owner.last_name, "Bateman")


class TestDeleteView(TestCase):
    def test_delete(self):
        owner = Owner(first_name="Radnall", last_name="Munroe")
        db.add(owner)
        db.flush()

        url = reverse("owner_delete", kwargs={"id": owner.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context_data["view"], edit.DeleteView)
        self.assertEqual(response.context_data["object"], owner)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owners_list"))

        state = db.inspect(owner)
        self.assertTrue(state.deleted)

    def test_delete_get_success_url(self):

        view = edit.DeletionMixin()

        with self.assertRaises(ImproperlyConfigured):
            view.get_success_url()
