# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.html import escape

from django_sorcery.views.list import MultipleObjectMixin, MultipleObjectTemplateResponseMixin

from ..base import TestCase
from ..models import Owner, db


class TestListView(TestCase):
    def setUp(self):
        super(TestListView, self).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner 1"),
                Owner(id=2, first_name="Test 2", last_name="Owner 2"),
                Owner(id=3, first_name="Test 3", last_name="Owner 3"),
                Owner(id=4, first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.flush()

    def test_paginate_orphans(self):
        view = MultipleObjectMixin()
        self.assertEqual(view.get_paginate_orphans(), view.paginate_orphans)

    def test_get_template_names(self):
        view = MultipleObjectTemplateResponseMixin()

        with self.assertRaises(ImproperlyConfigured):
            view.get_template_names()

    def test_list_generic(self):
        url = reverse("owners_list")

        response = self.client.get(url)

        self.assertEqual(
            response.content.decode().strip(), "owner" + escape("".join([repr(owner) for owner in Owner.query]))
        )

    def test_list_with_template(self):
        url = reverse("owners_list_tmpl")

        response = self.client.get(url)

        self.assertEqual(response.content.decode().strip(), escape("".join([repr(owner) for owner in Owner.query])))

    def test_list_ordering(self):
        url = reverse("owners_list_order")

        response = self.client.get(url)

        owners = Owner.query.order_by(Owner.id.desc())

        self.assertEqual(
            response.content.decode().strip(), "owner" + escape("".join([repr(owner) for owner in owners]))
        )

    def test_list_pagination(self):
        db.add_all([Owner(id=i, first_name="Test {}".format(i), last_name="Owner {}".format(i)) for i in range(5, 50)])
        db.flush()

        url = reverse("owners_list")

        response = self.client.get(url)

        self.assertEqual(
            response.content.decode().strip(),
            "owner" + escape("".join([repr(owner) for owner in Owner.query.order_by(Owner.id)[:20]])),
        )

    def test_list_pagination_last_page(self):
        db.add_all([Owner(id=i, first_name="Test {}".format(i), last_name="Owner {}".format(i)) for i in range(5, 50)])
        db.flush()

        url = reverse("owners_list")

        response = self.client.get("{}?page=last".format(url))

        self.maxDiff = None
        self.assertEqual(
            response.content.decode().strip(),
            "owner" + escape("".join([repr(owner) for owner in Owner.query.order_by(Owner.id)[40:]])),
        )

    def test_list_pagination_bad_page(self):
        db.add_all([Owner(id=i, first_name="Test {}".format(i), last_name="Owner {}".format(i)) for i in range(5, 50)])
        db.flush()

        url = reverse("owners_list")

        response = self.client.get("{}?page=abc".format(url))

        self.assertEqual(response.status_code, 404)

    def test_list_pagination_bad_page_out_of_range(self):
        db.add_all([Owner(id=i, first_name="Test {}".format(i), last_name="Owner {}".format(i)) for i in range(5, 50)])
        db.flush()

        url = reverse("owners_list")

        response = self.client.get("{}?page=100".format(url))

        self.assertEqual(response.status_code, 404)

    def test_list_context_name(self):

        url = reverse("owners_list_context_name")
        response = self.client.get(url)
        self.assertIn("owner_list", response.context_data)
        self.assertIsInstance(response.context_data["owner_list"], sa.orm.Query)

    def test_list_no_empty_paginate(self):
        db.rollback()

        url = reverse("owners_list_no_empty_paginate")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_list_dummy_no_empty_paginate(self):
        db.rollback()

        url = reverse("dummy_list_no_empty_paginate")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
