# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormMixin

from ..db.meta import model_info
from ..forms import modelform_factory
from ..views.base import BaseMultipleObjectMixin, BaseSingleObjectMixin


class ListModelMixin(BaseMultipleObjectMixin):
    """A mixin for views manipulating multiple objects."""

    def list(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_list_context_data()
        return self.render_to_response(context)

    def get_list_context_object_name(self, object_list):
        """Get the name to use for the object."""
        model = self.get_model()
        return "%s_list" % model.__name__.lower()

    def get_list_context_data(self, **kwargs):
        queryset = self.object_list
        page_size = self.get_paginate_by(queryset)
        context_object_name = self.get_list_context_object_name(queryset)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
            context = {"paginator": paginator, "page_obj": page, "is_paginated": is_paginated, "object_list": queryset}
        else:
            context = {"paginator": None, "page_obj": None, "is_paginated": False, "object_list": queryset}
        if context_object_name is not None:
            context[context_object_name] = queryset
        context.update(kwargs)
        return super(ListModelMixin, self).get_context_data(**context)


class RetrieveModelMixin(BaseSingleObjectMixin):
    """
    Provide the ability to retrieve a single object for further manipulation.
    """

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_detail_context_data(object=self.object)
        return self.render_to_response(context)

    def get_url_kwargs(self, obj):
        info = model_info(type(obj))
        return {key: getattr(obj, key) for key in info.primary_keys}

    def get_detail_context_object_name(self, obj):
        """Get the name to use for the object."""
        model = self.get_model()
        return model.__name__.lower()

    def get_detail_context_data(self, **kwargs):
        context = {}
        if self.object:
            context["object"] = self.object
            context_object_name = self.get_detail_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super(RetrieveModelMixin, self).get_context_data(**context)


class ModelFormMixin(FormMixin, RetrieveModelMixin):
    fields = None
    form_class = None
    success_url = None

    def get_form_class(self):
        if self.fields is not None and self.form_class:
            raise ImproperlyConfigured("Specifying both 'fields' and 'form_class' is not permitted.")

        if self.form_class:
            return self.form_class

        model = self.get_model()
        return modelform_factory(model, fields=self.fields, session=self.get_session())

    def get_form_kwargs(self):
        """
        Return the keyword arguments for instantiating the form.
        """
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})

        kwargs["session"] = self.get_session()
        return kwargs

    def get_success_url(self):
        """
        Return the URL to redirect to after processing a valid form.
        """
        if self.success_url:
            return self.success_url.format(**vars(self.object))

        raise ImproperlyConfigured(
            "No URL to redirect to. Either provide a url or override this function to return a url"
        )

    def process_form(self, form):
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return super(ModelFormMixin, self).form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_form_context_data(form=form))

    def get_form_context_data(self, **kwargs):
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        return self.get_detail_context_data(**kwargs)


class CreateModelMixin(ModelFormMixin):
    def new(self, request, *args, **kwargs):
        return self.render_to_response(self.get_create_context_data())

    def create(self, request, *args, **kwargs):
        form = self.get_form()
        return self.process_form(form)

    def get_create_context_data(self, **kwargs):
        return self.get_form_context_data(**kwargs)


class UpdateModelMixin(ModelFormMixin):
    def edit(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_update_context_data())

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        return self.process_form(form)

    def get_update_context_data(self, **kwargs):
        return self.get_form_context_data(**kwargs)


class DeleteModelMixin(RetrieveModelMixin):

    destroy_success_url = None

    def confirm_destroy(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_destroy_context_data())

    def destroy(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.perform_destoy(self.object)
        return HttpResponseRedirect(self.get_destroy_success_url())

    def perform_destoy(self, obj):
        session = self.get_session()
        session.delete(obj)
        session.flush()

    def get_destroy_context_data(self, **kwargs):
        return self.get_detail_context_data(**kwargs)

    def get_destroy_success_url(self):
        if self.destroy_success_url:
            return self.destroy_success_url.format(**vars(self.object))

        raise ImproperlyConfigured(
            "No URL to redirect to. Either provide a url or override this function to return a url"
        )
