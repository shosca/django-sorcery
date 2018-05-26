# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateResponseMixin, View

from .base import BaseSingleObjectMixin


class SingleObjectMixin(BaseSingleObjectMixin):
    """
    Provide the ability to retrieve a single object for further manipulation.
    """

    def get_context_object_name(self, obj):
        """Get the name to use for the object."""
        if self.context_object_name:
            return self.context_object_name

        model = self.get_model()
        return model.__name__.lower()

    def get_context_data(self, **kwargs):
        """Insert the single object into the context dict."""
        context = {}
        if self.object:
            context["object"] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super(SingleObjectMixin, self).get_context_data(**context)


class BaseDetailView(SingleObjectMixin, View):
    """A base view for displaying a single object."""

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class SingleObjectTemplateResponseMixin(TemplateResponseMixin):
    """
    Provide the ability to retrieve template names
    """

    template_name_field = None
    template_name_suffix = "_detail"

    def get_template_names(self):
        """
        """
        try:
            names = super(SingleObjectTemplateResponseMixin, self).get_template_names()
        except ImproperlyConfigured as e:

            names = []

            if self.object and self.template_name_field:
                name = getattr(self.object, self.template_name_field, None)
                if name:
                    names.insert(0, name)

            if hasattr(self, "get_model_template_name"):
                names.append(self.get_model_template_name())

            if not names:
                six.reraise(ImproperlyConfigured, e)

        return names


class DetailView(SingleObjectTemplateResponseMixin, BaseDetailView):
    """
    Render a "detail" view of an object.
    By default this is a model instance looked up from `self.queryset`, but the
    view will support display of *any* object by overriding `self.get_object()`.
    """
