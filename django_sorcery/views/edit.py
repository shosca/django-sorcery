# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import FormMixin

from .. import forms
from .detail import BaseDetailView, SingleObjectMixin, SingleObjectTemplateResponseMixin


class ModelFormMixin(FormMixin, SingleObjectMixin):
    fields = None

    def get_form_class(self):
        if self.fields is not None and self.form_class:
            raise ImproperlyConfigured("Specifying both 'fields' and 'form_class' is not permitted.")

        if self.form_class:
            return self.form_class

        model = self.get_model()
        return forms.modelform_factory(model, fields=self.fields, session=self.session)

    def get_form_kwargs(self):
        """
        Return the keyword arguments for instantiating the form.
        """
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})

        kwargs["session"] = self.session
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

    def form_valid(self, form):
        self.object = form.save()
        return super(ModelFormMixin, self).form_valid(form)


class ProcessFormView(View):
    """Render a form on GET and processes it on POST."""

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    put = post


class BaseFormView(FormMixin, ProcessFormView):
    """A base view for displaying a form."""


class FormView(TemplateResponseMixin, BaseFormView):
    """A view for displaying a form and rendering a template response."""


class BaseCreateView(ModelFormMixin, ProcessFormView):
    """
    Base view for creating a new object instance.
    Using this base class requires subclassing to provide a response mixin.
    """

    def get(self, request, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(BaseCreateView, self).post(request, *args, **kwargs)


class CreateView(SingleObjectTemplateResponseMixin, BaseCreateView):
    """
    View for creating a new object, with a response rendered by a template.
    """

    template_name_suffix = "_form"


class BaseUpdateView(ModelFormMixin, ProcessFormView):
    """
    Base view for updating an existing object.
    Using this base class requires subclassing to provide a response mixin.
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(BaseUpdateView, self).post(request, *args, **kwargs)


class UpdateView(SingleObjectTemplateResponseMixin, BaseUpdateView):
    """View for updating an object, with a response rendered by a template."""

    template_name_suffix = "_form"


class DeletionMixin:
    """Provide the ability to delete objects."""

    success_url = None

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.session.delete(self.object)
        self.session.flush()
        return HttpResponseRedirect(success_url)

    # Add support for browsers which only accept GET and POST for now.

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.success_url:
            return self.success_url.format(**self.object.__dict__)

        else:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")


class BaseDeleteView(DeletionMixin, BaseDetailView):
    """
    Base view for deleting an object.
    Using this base class requires subclassing to provide a response mixin.
    """


class DeleteView(SingleObjectTemplateResponseMixin, BaseDeleteView):
    """
    View for deleting an object retrieved with self.get_object(), with a
    response rendered by a template.
    """

    template_name_suffix = "_confirm_delete"
