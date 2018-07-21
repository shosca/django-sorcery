# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.urls import reverse_lazy

from django_sorcery import forms, views, viewsets
from django_sorcery.routers import action

from .models import Owner, Vehicle, db


class OwnerListView(views.ListView):
    queryset = Owner.query
    paginate_by = 20


class OwnerListViewWithTemplate(views.ListView):
    template_name = "views/list.html"
    queryset = Owner.query


class OwnerListViewWithOrdering(views.ListView):
    queryset = Owner.query
    ordering = (Owner.id.desc(),)


class OwnerListViewNoContextName(views.ListView):
    queryset = Owner.query
    context_object_name = None


class OwnerListViewNoEmptyPaginateBy(views.ListView):
    queryset = Owner.query
    paginate_by = 20
    allow_empty = False


class DummyListViewNoEmptyPaginateBy(views.ListView):
    queryset = []
    paginate_by = 20
    allow_empty = False


class OwnerDetailView(views.DetailView):
    queryset = Owner.query


class OwnerDetailViewWithTemplate(views.DetailView):
    template_name = "views/edit.html"
    queryset = Owner.query


class OwnerDetailViewWithSlug(views.DetailView):
    queryset = Owner.query
    query_pkg_and_slug = True
    slug_field = Owner.last_name.key


class OwnerDetailViewContextName(views.DetailView):
    queryset = Owner.query
    context_object_name = "item"


class OwnerCreateView(views.CreateView):
    model = Owner
    fields = "__all__"
    session = db
    success_url = reverse_lazy("owners_list")


class OwnerUpdateView(views.UpdateView):
    model = Owner
    fields = "__all__"
    session = db
    success_url = reverse_lazy("owners_list")


class OwnerCreateViewWithFieldsAndForm(views.CreateView):
    model = Owner
    session = db
    fields = "__all__"
    form_class = forms.modelform_factory(Owner, fields="__all__", session=db)


class OwnerCreateViewWithForm(views.CreateView):
    model = Owner
    session = db
    form_class = forms.modelform_factory(Owner, fields="__all__", session=db)


class VehicleCreateView(views.CreateView):
    model = Vehicle
    session = db
    fields = "__all__"


class OwnerDeleteView(views.DeleteView):
    model = Owner
    session = db
    success_url = reverse_lazy("owners_list")


class OwnerViewSet(viewsets.ModelViewSet):
    model = Owner

    @action(detail=True)
    def custom(self, request, *args, **kwargs):
        return self.detail(request, *args, **kwargs)
