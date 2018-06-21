# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured

from django_sorcery import viewsets
from django_sorcery.routers import BaseRouter, Route, SimpleRouter, action

from .appviews import OwnerViewSet
from .base import TestCase
from .models import Owner


class TestBaseRouter(TestCase):
    def test_router(self):
        router = BaseRouter()

        self.assertEqual(router.registry, [])

        router.register("prefix", OwnerViewSet, base_name="base_name")

        self.assertEqual(router.registry, [("prefix", OwnerViewSet, "base_name")])

        with self.assertRaises(NotImplementedError):
            router.register("prefix", OwnerViewSet)

        with self.assertRaises(NotImplementedError):
            router.get_default_base_name(OwnerViewSet)

        with self.assertRaises(NotImplementedError):
            router.get_urls()

        with self.assertRaises(NotImplementedError):
            router.urls

        router._urls = "test"
        self.assertEqual(router.urls, "test")


class TestSimpleRouter(TestCase):
    def get_regex(self, pattern):
        try:
            return pattern.pattern._regex

        except AttributeError:
            return pattern._regex

    def test_router(self):

        router = SimpleRouter()

        router.register("prefix", OwnerViewSet)

        self.assertEqual(router.registry, [("prefix", OwnerViewSet, "owner")])

        self.assertEqual(
            router.get_routes(OwnerViewSet),
            [
                Route(
                    url="^{prefix}{trailing_slash}$",
                    mapping={"get": "list", "post": "create"},
                    name="{basename}-list",
                    detail=False,
                    initkwargs={"suffix": "List"},
                ),
                Route(
                    url="^{prefix}/new{trailing_slash}$",
                    mapping={"get": "new"},
                    name="{basename}-new",
                    detail=False,
                    initkwargs={"suffix": "New"},
                ),
                Route(
                    url="^{prefix}/{lookup}{trailing_slash}$",
                    mapping={
                        "get": "retrieve",
                        "post": "update",
                        "put": "update",
                        "patch": "update",
                        "delete": "destroy",
                    },
                    name="{basename}-detail",
                    detail=True,
                    initkwargs={"suffix": "Instance"},
                ),
                Route(
                    url="^{prefix}/{lookup}/edit{trailing_slash}$",
                    mapping={"get": "edit"},
                    name="{basename}-edit",
                    detail=True,
                    initkwargs={"suffix": "Instance"},
                ),
                Route(
                    url="^{prefix}/{lookup}/delete{trailing_slash}$",
                    mapping={"get": "confirm_destroy", "post": "destroy"},
                    name="{basename}-destroy",
                    detail=True,
                    initkwargs={"suffix": "Instance"},
                ),
                Route(
                    url="^{prefix}/{lookup}/custom{trailing_slash}$",
                    mapping={"get": "custom"},
                    name="{basename}-custom",
                    detail=True,
                    initkwargs={},
                ),
            ],
        )

        urls = {url.name: url for url in router.urls}

        self.assertEqual(self.get_regex(urls["owner-custom"]), "^prefix/(?P<id>[^/.]+)/custom/$")
        self.assertEqual(self.get_regex(urls["owner-destroy"]), "^prefix/(?P<id>[^/.]+)/delete/$")
        self.assertEqual(self.get_regex(urls["owner-detail"]), "^prefix/(?P<id>[^/.]+)/$")
        self.assertEqual(self.get_regex(urls["owner-edit"]), "^prefix/(?P<id>[^/.]+)/edit/$")
        self.assertEqual(self.get_regex(urls["owner-list"]), "^prefix/$")
        self.assertEqual(self.get_regex(urls["owner-new"]), "^prefix/new/$")

    def test_action_on_existing_action(self):
        class OwnerViewSet(viewsets.ListModelMixin, viewsets.GenericViewSet):
            model = Owner

            @action(detail=False)
            def list(self, request, *args, **kwargs):
                pass

        router = SimpleRouter()

        with self.assertRaises(ImproperlyConfigured):
            router.get_routes(OwnerViewSet)

    def test_custom_lookup_regex(self):
        class OwnerViewSet(viewsets.RetrieveModelMixin, viewsets.GenericViewSet):
            model = Owner
            lookup_url_regex = "lookup_regex"

        router = SimpleRouter()

        self.assertEqual(router.get_lookup_regex(OwnerViewSet), "lookup_regex")

    def test_lookup_regex_no_model(self):
        class OwnerViewSet(viewsets.GenericViewSet):
            pass

        router = SimpleRouter()
        self.assertEqual(router.get_lookup_regex(OwnerViewSet), "(?P<pk>[^/.]+)")

    def test_path_with_mustaches(self):
        class OwnerViewSet(viewsets.GenericViewSet):
            @action(detail=False, url_path="{dummy}")
            def dummy(self, request, *args, **kwargs):
                pass

        router = SimpleRouter()
        routes = router.get_routes(OwnerViewSet)
        dummy_route = next(iter(filter(lambda r: "dummy" in r.url, routes)), None)
        self.assertIsNotNone(dummy_route)
        self.assertEqual(dummy_route.url, "^{prefix}/{{dummy}}{trailing_slash}$")

    def test_get_url_with_empty_prefix(self):
        class OwnerViewSet(viewsets.ListModelMixin, viewsets.GenericViewSet):
            model = Owner

        router = SimpleRouter()
        router.register("", OwnerViewSet, "")
        urlpattern = router.get_urls()[0]
        self.assertEqual(self.get_regex(urlpattern), "^$")
