# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url

from django_sorcery import routers

from . import appviews


router = routers.SimpleRouter()
router.register("owners", appviews.OwnerViewSet)

urlpatterns = [
    # list views
    # r"^(?P<id>[0-9]+)/$"
    url(r"^list/owners/$", appviews.OwnerListView.as_view(), name="owners_list"),
    url(r"^list/owners-tmpl/$", appviews.OwnerListViewWithTemplate.as_view(), name="owners_list_tmpl"),
    url(r"^list/owners-order/$", appviews.OwnerListViewWithOrdering.as_view(), name="owners_list_order"),
    url(r"^list/owners-context-name/$", appviews.OwnerListViewNoContextName.as_view(), name="owners_list_context_name"),
    url(
        r"^list/owners-no-empty-paginate/$",
        appviews.OwnerListViewNoEmptyPaginateBy.as_view(),
        name="owners_list_no_empty_paginate",
    ),
    url(
        r"^list/dummy-no-empty-paginate/$",
        appviews.DummyListViewNoEmptyPaginateBy.as_view(),
        name="dummy_list_no_empty_paginate",
    ),
    # detail views
    url(r"^detail/owners/(?P<id>[0-9]+)/$", appviews.OwnerDetailView.as_view(), name="owner_detail"),
    url(
        r"^detail/owners-tmpl/(?P<id>[0-9]+)/$",
        appviews.OwnerDetailViewWithTemplate.as_view(),
        name="owner_detail_tmpl",
    ),
    url(r"^detail/owners-slug/(?P<slug>\w+)/", appviews.OwnerDetailViewWithSlug.as_view(), name="owner_detail_slug"),
    url(
        r"^detail/owners-context-name/(?P<id>[0-9]+)/$",
        appviews.OwnerDetailViewContextName.as_view(),
        name="owner_detail_context_name",
    ),
    # edit views
    url(r"^edit/owners/create/$", appviews.OwnerCreateView.as_view(), name="owner_create"),
    url(r"^edit/owners/(?P<id>[0-9]+)/$", appviews.OwnerUpdateView.as_view(), name="owner_update"),
    url(
        r"^edit/owners/create-field-form/$",
        appviews.OwnerCreateViewWithFieldsAndForm.as_view(),
        name="owner_create_field_form",
    ),
    url(r"^edit/owners/create-form/$", appviews.OwnerCreateViewWithForm.as_view(), name="owner_create_form"),
    url(r"^edit/vehicles/create/$", appviews.VehicleCreateView.as_view(), name="vehicle_create"),
    # delete views
    url(r"^delete/owners/(?P<id>[0-9]+)/$", appviews.OwnerDeleteView.as_view(), name="owner_delete"),
    url(r"^viewsets/", include(router.urls)),
]
