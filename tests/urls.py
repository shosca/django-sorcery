from django_sorcery import routers

from .testapp import views


try:
    from django.conf.urls import url as re_path
    from django.conf.urls import include
except ImportError:  # pragma: no cover
    from django.urls import re_path, include


router = routers.SimpleRouter()
router.register("owners", views.OwnerViewSet)

urlpatterns = [
    # list views
    # r"^(?P<id>[0-9]+)/$"
    re_path(r"^list/owners/$", views.OwnerListView.as_view(), name="owners_list"),
    re_path(r"^list/owners-tmpl/$", views.OwnerListViewWithTemplate.as_view(), name="owners_list_tmpl"),
    re_path(r"^list/owners-order/$", views.OwnerListViewWithOrdering.as_view(), name="owners_list_order"),
    re_path(
        r"^list/owners-context-name/$", views.OwnerListViewNoContextName.as_view(), name="owners_list_context_name"
    ),
    re_path(
        r"^list/owners-no-empty-paginate/$",
        views.OwnerListViewNoEmptyPaginateBy.as_view(),
        name="owners_list_no_empty_paginate",
    ),
    re_path(
        r"^list/dummy-no-empty-paginate/$",
        views.DummyListViewNoEmptyPaginateBy.as_view(),
        name="dummy_list_no_empty_paginate",
    ),
    # detail views
    re_path(r"^detail/owners/(?P<id>[0-9]+)/$", views.OwnerDetailView.as_view(), name="owner_detail"),
    re_path(
        r"^detail/owners-tmpl/(?P<id>[0-9]+)/$", views.OwnerDetailViewWithTemplate.as_view(), name="owner_detail_tmpl"
    ),
    re_path(r"^detail/owners-slug/(?P<slug>\w+)/", views.OwnerDetailViewWithSlug.as_view(), name="owner_detail_slug"),
    re_path(
        r"^detail/owners-context-name/(?P<id>[0-9]+)/$",
        views.OwnerDetailViewContextName.as_view(),
        name="owner_detail_context_name",
    ),
    # edit views
    re_path(r"^edit/owners/create/$", views.OwnerCreateView.as_view(), name="owner_create"),
    re_path(r"^edit/owners/(?P<id>[0-9]+)/$", views.OwnerUpdateView.as_view(), name="owner_update"),
    re_path(
        r"^edit/owners/create-field-form/$",
        views.OwnerCreateViewWithFieldsAndForm.as_view(),
        name="owner_create_field_form",
    ),
    re_path(r"^edit/owners/create-form/$", views.OwnerCreateViewWithForm.as_view(), name="owner_create_form"),
    re_path(r"^edit/vehicles/create/$", views.VehicleCreateView.as_view(), name="vehicle_create"),
    # delete views
    re_path(r"^delete/owners/(?P<id>[0-9]+)/$", views.OwnerDeleteView.as_view(), name="owner_delete"),
    re_path(r"^viewsets/", include(router.urls)),
]
