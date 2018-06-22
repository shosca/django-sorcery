# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateResponseMixin, View

from .base import BaseMultipleObjectMixin


class MultipleObjectMixin(BaseMultipleObjectMixin):
    """A mixin for views manipulating multiple objects."""

    context_object_name = "object_list"

    def get_context_object_name(self, object_list):
        """Get the name to use for the object."""
        if self.context_object_name:
            return self.context_object_name

        model = self.get_model()
        return "%s_list" % model.__name__.lower()

    def get_context_data(self, object_list=None, **kwargs):
        """Get the context for this view."""
        queryset = object_list if object_list is not None else self.object_list
        page_size = self.get_paginate_by(queryset)
        context_object_name = self.get_context_object_name(queryset)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
            context = {"paginator": paginator, "page_obj": page, "is_paginated": is_paginated, "object_list": queryset}
        else:
            context = {"paginator": None, "page_obj": None, "is_paginated": False, "object_list": queryset}
        if context_object_name is not None:
            context[context_object_name] = queryset
        context.update(kwargs)
        return super(MultipleObjectMixin, self).get_context_data(**context)


class BaseListView(MultipleObjectMixin, View):
    """A base view for displaying a list of objects."""

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


class MultipleObjectTemplateResponseMixin(TemplateResponseMixin):
    """Mixin for responding with a template and list of objects."""

    template_name_suffix = "_list"

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return a list. May not be called if
        render_to_response is overridden.
        """
        try:
            names = super(MultipleObjectTemplateResponseMixin, self).get_template_names()
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # we just start with an empty list.
            names = []

            # If the list is a queryset, we'll invent a template name based on the
            # app and model name. This name gets put at the end of the template
            # name list so that user-supplied names override the automatically-
            # generated ones.

            if hasattr(self, "get_model_template_name"):
                names.append(self.get_model_template_name())
            elif not names:
                raise ImproperlyConfigured(
                    "%(cls)s requires either a 'template_name' attribute or a get_queryset() method that returns a "
                    "QuerySet." % {"cls": self.__class__.__name__}
                )

        return names


class ListView(MultipleObjectTemplateResponseMixin, BaseListView):
    """
    Render some list of objects, set by `self.model` or `self.queryset`.
    `self.queryset` can actually be any iterable of items, not just a queryset.
    """
