# -*- coding: utf-8 -*-
"""
Django REST Framework like model viewsets
"""
from functools import update_wrapper
from inspect import getmembers

from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import classonlymethod
from django.views.generic.base import TemplateResponseMixin, View

from . import mixins


class GenericViewSet(TemplateResponseMixin, View):
    """
    Base class for all sqlalchemy model generic viewsets.
    """

    def get_template_names(self):

        self.template_name_suffix = "_" + self.action
        names = []

        try:
            names.extend(super().get_template_names())
        except ImproperlyConfigured:
            pass

        if hasattr(self, "get_model_template_name"):
            names.append(self.get_model_template_name())

        return names

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        # The suffix initkwarg is reserved for displaying the viewset type.
        # eg. 'List' or 'Instance'.
        cls.suffix = None

        # The detail initkwarg is reserved for introspecting the viewset type.
        cls.detail = None

        # Setting a basename allows a view to reverse its action urls. This
        # value is provided by the router through the initkwargs.
        cls.basename = None

        # actions must not be empty
        if not actions:
            raise TypeError(
                "The `actions` argument must be provided when "
                "calling `.as_view()` on a ViewSet. For example "
                "`.as_view({'get': 'list'})`"
            )

        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(
                    "You tried to pass in the %s method name as a "
                    "keyword argument to %s(). Don't do that." % (key, cls.__name__)
                )

            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r" % (cls.__name__, key))

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            # We also store the mapping of request methods to actions,
            # so that we can later set the action attribute.
            # eg. `self.action = 'list'` on an incoming GET request.
            self.action_map = actions
            method = request.method.lower()
            self.action = self.action_map.get(method, "metadata")

            # Bind methods to actions
            # This is the bit that's different to a standard view
            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method, handler)

            if hasattr(self, "get") and not hasattr(self, "head"):
                self.head = self.get

            self.request = request
            self.args = args
            self.kwargs = kwargs

            # And continue as usual
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())

        # We need to set these on the view function, so that breadcrumb
        # generation can pick out these bits of information from a
        # resolved URL.
        view.cls = cls
        view.initkwargs = initkwargs
        view.suffix = initkwargs.get("suffix", None)
        view.actions = actions
        return view

    @classmethod
    def get_extra_actions(cls):
        """
        Get the methods that are marked as an extra ViewSet `@action`.
        """
        return [method for _, method in getmembers(cls, lambda attr: hasattr(attr, "bind_to_methods"))]


class ReadOnlyModelViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /                        list            <resource name>-list
    GET    /<pk>/                   retrieve        <resource name>-detail
    ====== ======================== =============== ======================
    """


class ModelViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DeleteModelMixin, ReadOnlyModelViewSet):
    """
    A viewset that provides default `new()`, `create()`, `retrieve()`, `edit()`, update()`,
    `confirm_destroy())`, `destroy()` and `list()` actions.

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /                        list            <resource name>-list
    POST   /                        create          <resource name>-list
    GET    /new/                    new             <resource name>-new
    GET    /<pk>/                   retrieve        <resource name>-detail
    POST   /<pk>/                   update          <resource name>-detail
    PUT    /<pk>/                   update          <resource name>-detail
    PATCH  /<pk>/                   update          <resource name>-detail
    DELETE /<pk>/                   destroy         <resource name>-detail
    GET    /<pk>/edit/              edit            <resource name>-edit
    GET    /<pk>/delete/            confirm_destoy  <resource name>-delete
    POST   /<pk>/delete/            destroy         <resource name>-delete
    ====== ======================== =============== ======================
    """
