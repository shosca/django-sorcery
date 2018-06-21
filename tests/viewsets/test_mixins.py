# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.urls import reverse

from django_sorcery import forms, viewsets

from ..base import TestCase
from ..models import Owner, db


class TestListModelMixin(TestCase):
    def setUp(self):
        super(TestListModelMixin, self).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner 1"),
                Owner(id=2, first_name="Test 2", last_name="Owner 2"),
                Owner(id=3, first_name="Test 3", last_name="Owner 3"),
                Owner(id=4, first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.flush()

    def test_list(self):
        class OwnerViewSet(viewsets.ListModelMixin, viewsets.GenericViewSet):
            model = Owner

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "list"

        response = viewset.list(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.context_data,
            {
                "is_paginated": False,
                "object_list": viewset.object_list,
                "owner_list": viewset.object_list,
                "page_obj": None,
                "paginator": None,
                "view": viewset,
            },
        )

    def test_list_allow_no_empty(self):
        class OwnerViewSet(viewsets.ListModelMixin, viewsets.GenericViewSet):
            model = Owner
            allow_empty = False
            paginate_by = 10

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "list"

        response = viewset.list(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.context_data,
            {
                "is_paginated": False,
                "object_list": viewset.object_list.all(),
                "owner_list": viewset.object_list.all(),
                "page_obj": response.context_data["page_obj"],
                "paginator": response.context_data["paginator"],
                "view": viewset,
            },
        )

    def test_list_allow_no_empty_with_no_owners(self):

        db.rollback()

        class OwnerViewSet(viewsets.ListModelMixin, viewsets.GenericViewSet):
            model = Owner
            allow_empty = False
            paginate_by = 10

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "list"

        with self.assertRaises(Http404):
            viewset.list(viewset.request)


class TestRetieveModelMixin(TestCase):
    def setUp(self):
        super(TestRetieveModelMixin, self).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner 1"),
                Owner(id=2, first_name="Test 2", last_name="Owner 2"),
                Owner(id=3, first_name="Test 3", last_name="Owner 3"),
                Owner(id=4, first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.flush()

    def test_retrieve(self):
        class OwnerViewSet(viewsets.RetrieveModelMixin, viewsets.GenericViewSet):
            model = Owner

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.get("/")
        viewset.action = "retrieve"

        response = viewset.retrieve(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.context_data, {"object": viewset.object, "owner": viewset.object, "view": viewset}
        )

        kwargs = viewset.get_url_kwargs(viewset.object)
        self.assertDictEqual(kwargs, {"id": 1})


class TestCreateModelMixin(TestCase):
    def test_new_require_fields_or_form_class(self):
        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = "__all__"
            form_class = forms.modelform_factory(Owner, fields="__all__", session=db)

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "new"

        with self.assertRaises(ImproperlyConfigured):
            viewset.new(viewset.request)

    def test_new_with_form_class(self):

        form_cls = forms.modelform_factory(Owner, fields="__all__", session=db)

        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            form_class = form_cls

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "new"

        response = viewset.new(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context_data, {"form": response.context_data["form"], "view": viewset})
        self.assertIsInstance(response.context_data["form"], form_cls)

    def test_new(self):
        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = "__all__"

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.get("/")
        viewset.action = "new"

        response = viewset.new(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context_data, {"form": response.context_data["form"], "view": viewset})

    def test_create_bad_config(self):
        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = (Owner.first_name.key, Owner.last_name.key)

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.post("/", data={"first_name": "first_name", "last_name": "last_name"})
        viewset.action = "create"

        with self.assertRaises(ImproperlyConfigured):
            viewset.create(viewset.request)

    def test_create(self):
        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = (Owner.first_name.key, Owner.last_name.key)
            success_url = "/viewsets/owners/{id}/"

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.post("/", data={"first_name": "first_name", "last_name": "last_name"})
        viewset.action = "create"

        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.get("location"), reverse("owner-detail", args=[viewset.object.id]))
        self.assertEqual(viewset.object.first_name, "first_name")
        self.assertEqual(viewset.object.last_name, "last_name")

    def test_create_invalid(self):

        form_cls = forms.modelform_factory(Owner, fields=("first_name", "last_name"), session=db)
        form_cls.base_fields["first_name"].required = True
        form_cls.base_fields["last_name"].required = True

        class OwnerViewSet(viewsets.CreateModelMixin, viewsets.GenericViewSet):
            model = Owner
            form_class = form_cls
            success_url = "/viewsets/owners/{id}/"

        viewset = OwnerViewSet()
        viewset.kwargs = {}
        viewset.request = self.factory.post("/", data={})
        viewset.action = "create"

        response = viewset.create(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data["form"].errors,
            {"first_name": ["This field is required."], "last_name": ["This field is required."]},
        )


class TestUpdateModelMixin(TestCase):
    def setUp(self):
        super(TestUpdateModelMixin, self).setUp()
        db.add(Owner(id=1, first_name="Test 1", last_name="Owner 1"))
        db.flush()

    def test_edit(self):
        class OwnerViewSet(viewsets.UpdateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = ("first_name", "last_name")

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.get("/")
        viewset.action = "edit"

        response = viewset.edit(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.context_data,
            {"form": response.context_data["form"], "owner": viewset.object, "object": viewset.object, "view": viewset},
        )

    def test_update(self):
        class OwnerViewSet(viewsets.UpdateModelMixin, viewsets.GenericViewSet):
            model = Owner
            fields = ("first_name", "last_name")
            success_url = "/viewsets/owners/{id}/"

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.post("/", data={"first_name": "edit first", "last_name": "edit last"})
        viewset.action = "update"

        response = viewset.update(viewset.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.get("location"), "/viewsets/owners/1/")


class TestDeleteModelMixin(TestCase):
    def setUp(self):
        super(TestDeleteModelMixin, self).setUp()
        db.add(Owner(id=1, first_name="Test 1", last_name="Owner 1"))
        db.flush()

    def test_confirm_destroy(self):
        class OwnerViewSet(viewsets.DeleteModelMixin, viewsets.GenericViewSet):
            model = Owner

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.get("/")
        viewset.action = "confirm_destory"

        response = viewset.confirm_destroy(viewset.request)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.context_data, {"owner": viewset.object, "object": viewset.object, "view": viewset}
        )

    def test_destroy(self):
        class OwnerViewSet(viewsets.DeleteModelMixin, viewsets.GenericViewSet):
            model = Owner
            destroy_success_url = "/viewsets/owners/"

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.post("/")
        viewset.action = "destory"

        response = viewset.destroy(viewset.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.get("location"), "/viewsets/owners/")
        self.assertIsNone(Owner.query.get(1))

    def test_destroy_no_success_url(self):
        class OwnerViewSet(viewsets.DeleteModelMixin, viewsets.GenericViewSet):
            model = Owner

        viewset = OwnerViewSet()
        viewset.kwargs = {"id": 1}
        viewset.request = self.factory.post("/")
        viewset.action = "destory"

        with self.assertRaises(ImproperlyConfigured):
            viewset.destroy(viewset.request)
