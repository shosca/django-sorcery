# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url

from django_sorcery import routers

from .testapp import views


router = routers.SimpleRouter()
router.register("owners", views.OwnerViewSet)

urlpatterns = [
    # list views
    # r"^(?P<id>[0-9]+)/$"
    url(r"^list/owners/$", views.OwnerListView.as_view(), name="owners_list"),
    url(r"^list/owners-tmpl/$", views.OwnerListViewWithTemplate.as_view(), name="owners_list_tmpl"),
    url(r"^list/owners-order/$", views.OwnerListViewWithOrdering.as_view(), name="owners_list_order"),
    url(r"^list/owners-context-name/$", views.OwnerListViewNoContextName.as_view(), name="owners_list_context_name"),
    url(
        r"^list/owners-no-empty-paginate/$",
        views.OwnerListViewNoEmptyPaginateBy.as_view(),
        name="owners_list_no_empty_paginate",
    ),
    url(
        r"^list/dummy-no-empty-paginate/$",
        views.DummyListViewNoEmptyPaginateBy.as_view(),
        name="dummy_list_no_empty_paginate",
    ),
    # detail views
    url(r"^detail/owners/(?P<id>[0-9]+)/$", views.OwnerDetailView.as_view(), name="owner_detail"),
    url(r"^detail/owners-tmpl/(?P<id>[0-9]+)/$", views.OwnerDetailViewWithTemplate.as_view(), name="owner_detail_tmpl"),
    url(r"^detail/owners-slug/(?P<slug>\w+)/", views.OwnerDetailViewWithSlug.as_view(), name="owner_detail_slug"),
    url(
        r"^detail/owners-context-name/(?P<id>[0-9]+)/$",
        views.OwnerDetailViewContextName.as_view(),
        name="owner_detail_context_name",
    ),
    # edit views
    url(r"^edit/owners/create/$", views.OwnerCreateView.as_view(), name="owner_create"),
    url(r"^edit/owners/(?P<id>[0-9]+)/$", views.OwnerUpdateView.as_view(), name="owner_update"),
    url(
        r"^edit/owners/create-field-form/$",
        views.OwnerCreateViewWithFieldsAndForm.as_view(),
        name="owner_create_field_form",
    ),
    url(r"^edit/owners/create-form/$", views.OwnerCreateViewWithForm.as_view(), name="owner_create_form"),
    url(r"^edit/vehicles/create/$", views.VehicleCreateView.as_view(), name="vehicle_create"),
    # delete views
    url(r"^delete/owners/(?P<id>[0-9]+)/$", views.OwnerDeleteView.as_view(), name="owner_delete"),
    url(r"^viewsets/", include(router.urls)),
]
