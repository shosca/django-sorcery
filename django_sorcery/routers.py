# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import itertools
from collections import namedtuple

from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured

from django_sorcery.db.meta import model_info


Route = namedtuple("Route", ["url", "mapping", "name", "detail", "initkwargs"])
DynamicRoute = namedtuple("DynamicRoute", ["url", "name", "detail", "initkwargs"])


def escape_curly_brackets(url_path):
    """
    Double brackets in regex of url_path for escape string formatting
    """
    if ("{" and "}") in url_path:
        url_path = url_path.replace("{", "{{").replace("}", "}}")
    return url_path


def action(methods=None, detail=None, url_path=None, url_name=None, **kwargs):
    """
    Mark a ViewSet method as a routable action.

    Set the `detail` boolean to determine if this action should apply to
    instance/detail requests or collection/list requests.
    """
    methods = ["get"] if (methods is None) else methods
    methods = [method.lower() for method in methods]

    assert detail is not None, "@action() missing required argument: 'detail'"

    def decorator(func):
        func.bind_to_methods = methods
        func.detail = detail
        func.url_path = url_path if url_path else func.__name__
        func.url_name = url_name if url_name else func.__name__.replace("_", "-")
        func.kwargs = kwargs
        return func

    return decorator


class BaseRouter(object):
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, base_name=None):
        if base_name is None:
            base_name = self.get_default_base_name(viewset)
        self.registry.append((prefix, viewset, base_name))

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        raise NotImplementedError("get_default_base_name must be overridden")

    def get_urls(self):
        """
        Return a list of URL patterns, given the registered viewsets.
        """
        raise NotImplementedError("get_urls must be overridden")

    @property
    def urls(self):
        if not hasattr(self, "_urls"):
            self._urls = self.get_urls()
        return self._urls


class SimpleRouter(BaseRouter):
    """
    Generates url patterns that map requests to a viewset's action functions.

    It will map the following operations to following actions on the viewset:

    ====== ======================== =============== =================
    Method Path                     Action          Route Name
    ====== ======================== =============== =================
    GET    /<resource>/             list            <resource>-list
    POST   /<resource>/             create          <resource>-list
    GET    /<resource>/new/         new             <resource>-new
    GET    /<resource>/<pk>/        retrieve        <resource>-detail
    POST   /<resource>/<pk>/        update          <resource>-detail
    PUT    /<resource>/<pk>/        update          <resource>-detail
    PATCH  /<resource>/<pk>/        update          <resource>-detail
    DELETE /<resource>/<pk>/        destroy         <resource>-detail
    GET    /<resource>/<pk>/edit/   edit            <resource>-edit
    GET    /<resource>/<pk>/delete/ confirm_destoy  <resource>-delete
    POST   /<resource>/<pk>/delete/ destroy         <resource>-delete
    ====== ======================== =============== =================
    """

    routes = [
        # List route.
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={"get": "list", "post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        Route(
            url=r"^{prefix}/new{trailing_slash}$",
            mapping={"get": "new"},
            name="{basename}-new",
            detail=False,
            initkwargs={"suffix": "New"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{url_path}{trailing_slash}$", name="{basename}-{url_name}", detail=False, initkwargs={}
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={"get": "retrieve", "post": "update", "put": "update", "patch": "update", "delete": "destroy"},
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        Route(
            url=r"^{prefix}/{lookup}/edit{trailing_slash}$",
            mapping={"get": "edit"},
            name="{basename}-edit",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        Route(
            url=r"^{prefix}/{lookup}/delete{trailing_slash}$",
            mapping={"get": "confirm_destroy", "post": "destroy"},
            name="{basename}-destroy",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        DynamicRoute(
            url=r"^{prefix}/{lookup}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=True,
            initkwargs={},
        ),
    ]

    def __init__(self, trailing_slash=True):
        self.trailing_slash = "/" if trailing_slash else ""
        super(SimpleRouter, self).__init__()

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        model = getattr(viewset, "get_model", lambda: None)()

        assert model is not None, (
            "`base_name` argument not specified, and could not automatically determine the name from the viewset, "
            "as either queryset is is missing or is not a sqlalchemy query, or the serializer_class is not a "
            "sqlalchemy model serializer"
        )

        return model.__name__.lower()

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known host needs to be checked again and again for
        # different functions.
        known_actions = itertools.chain(*[route.mapping.values() for route in self.routes if isinstance(route, Route)])
        extra_actions = viewset.get_extra_actions()

        # checking action names against the known actions list
        not_allowed = [action.__name__ for action in extra_actions if action.__name__ in known_actions]
        if not_allowed:
            msg = "Cannot use the @action decorator on the following methods, as they are existing routes: %s"
            raise ImproperlyConfigured(msg % ", ".join(not_allowed))

        # partition detail and list actions
        detail_actions = [action for action in extra_actions if action.detail]
        list_actions = [action for action in extra_actions if not action.detail]

        routes = []
        for route in self.routes:
            if isinstance(route, DynamicRoute) and route.detail:
                routes += [self._get_dynamic_route(route, action) for action in detail_actions]
            elif isinstance(route, DynamicRoute) and not route.detail:
                routes += [self._get_dynamic_route(route, action) for action in list_actions]
            else:
                routes.append(route)

        return routes

    def _get_dynamic_route(self, route, action):
        initkwargs = route.initkwargs.copy()
        initkwargs.update(action.kwargs)

        url_path = escape_curly_brackets(action.url_path)

        return Route(
            url=route.url.replace("{url_path}", url_path),
            mapping={http_method: action.__name__ for http_method in action.bind_to_methods},
            name=route.name.replace("{url_name}", action.url_name),
            detail=route.detail,
            initkwargs=initkwargs,
        )

    def get_method_map(self, viewset, method_map):
        """
        Given a viewset, and a mapping of http methods to actions,
        return a new mapping which only includes any mappings that
        are actually implemented by the viewset.
        """
        bound_methods = {}
        for method, action in method_map.items():
            if hasattr(viewset, action):
                bound_methods[method] = action
        return bound_methods

    def get_lookup_regex(self, viewset, lookup_prefix=""):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers
        """
        lookup_url_regex = getattr(viewset, "lookup_url_regex", None)
        if lookup_url_regex:
            return lookup_url_regex

        base_regex = "(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})"

        model = getattr(viewset, "get_model", lambda: None)()
        if model:
            info = model_info(model)

            regexes = []
            for key, _ in info.primary_keys.items():
                regexes.append(
                    base_regex.format(lookup_prefix=lookup_prefix, lookup_url_kwarg=key, lookup_value="[^/.]+")
                )

            return "/".join(regexes)

        lookup_field = getattr(viewset, "lookup_field", "pk")
        lookup_url_kwarg = getattr(viewset, "lookup_url_kwarg", None) or lookup_field
        lookup_value = getattr(viewset, "lookup_value_regex", "[^/.]+")
        return base_regex.format(
            lookup_prefix=lookup_prefix, lookup_url_kwarg=lookup_url_kwarg, lookup_value=lookup_value
        )

    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = []

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                regex = route.url.format(prefix=prefix, lookup=lookup, trailing_slash=self.trailing_slash)

                # If there is no prefix, the first part of the url is probably
                #   controlled by project's urls.py and the router is in an app,
                #   so a slash in the beginning will (A) cause Django to give
                #   warnings and (B) generate URLS that will require using '//'.
                if not prefix and regex[:2] == "^/":
                    regex = "^" + regex[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update({"basename": basename, "detail": route.detail})

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename=basename)
                ret.append(url(regex, view, name=name))

        return ret
