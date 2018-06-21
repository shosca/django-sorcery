# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.html import escape

from django_sorcery.views.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin

from ..base import TestCase
from ..models import Owner, db


class TestDetailView(TestCase):
    def setUp(self):
        super(TestDetailView, self).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner1"),
                Owner(id=2, first_name="Test 2", last_name="Owner2"),
                Owner(id=3, first_name="Test 3", last_name="Owner3"),
                Owner(id=4, first_name="Test 4", last_name="Owner4"),
            ]
        )
        db.flush()

    def test_get_object_fail_no_kwargs(self):
        class DummyView(SingleObjectMixin):
            model = Owner

        view = DummyView()
        view.kwargs = {}

        with self.assertRaises(AttributeError) as ctx:
            view.get_object(queryset=[Owner()])

        self.assertEqual(
            str(ctx.exception),
            "Generic detail view DummyView must be called with either an object pk or a slug in the URLconf.",
        )

    def test_detail_generic(self):

        url = reverse("owner_detail", kwargs={"id": 1})

        response = self.client.get(url)

        self.assertEqual(response.content.decode().strip(), "owner" + escape(repr(Owner.query.get(1))))

    def test_detail_generic_with_template(self):

        url = reverse("owner_detail_tmpl", kwargs={"id": 1})

        response = self.client.get(url)

        self.assertEqual(response.content.decode().strip(), escape(repr(Owner.query.get(1))))

    def test_detail_generic_with_slug(self):

        url = reverse("owner_detail_slug", kwargs={"slug": "Owner1"})

        response = self.client.get(url)

        self.assertEqual(response.content.decode().strip(), "owner" + escape(repr(Owner.query.get(1))))

    def test_detail_generic_404(self):

        url = reverse("owner_detail", kwargs={"id": 99})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_detail_generic_context_name(self):

        url = reverse("owner_detail_context_name", kwargs={"id": 1})

        response = self.client.get(url)

        self.assertIn("item", response.context_data)
        self.assertIsInstance(response.context_data["item"], Owner)

    def test_detail_get_template_name_field_from_object(self):

        view = SingleObjectTemplateResponseMixin()
        view.object = Owner(last_name="owner_template")
        view.template_name_field = "last_name"

        template_names = view.get_template_names()

        self.assertEqual(template_names, [view.object.last_name])

    def test_detail_get_template_name_fail(self):

        view = SingleObjectTemplateResponseMixin()
        view.object = Owner(last_name="owner_template")

        with self.assertRaises(ImproperlyConfigured):
            view.get_template_names()
