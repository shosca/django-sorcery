# -*- coding: utf-8 -*-
"""
Django REST Framework like viewset mixins for common model sqlalchemy actions
"""

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormMixin

from ..db import meta
from ..forms import modelform_factory
from ..views.base import BaseMultipleObjectMixin, BaseSingleObjectMixin


class ListModelMixin(BaseMultipleObjectMixin):
    """
    A mixin for displaying a list of objects

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /                        list            <resource name>-list
    ====== ======================== =============== ======================
    """

    def list(self, request, *args, **kwargs):
        """List action for displaying a list of objects"""
        self.object_list = self.get_queryset()
        context = self.get_list_context_data()
        return self.render_to_response(context)

    def get_list_context_object_name(self, object_list):
        """Get the name to use for the object."""
        model = self.get_model()
        return "%s_list" % model.__name__.lower()

    def get_list_context_data(self, **kwargs):
        """Returns context data for list action"""
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
        return super().get_context_data(**context)


class RetrieveModelMixin(BaseSingleObjectMixin):
    """
    A mixin for displaying a single object

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /<pk>/                   retrieve        <resource name>-detail
    ====== ======================== =============== ======================
    """

    def retrieve(self, request, *args, **kwargs):
        """List action for displaying a single object"""
        self.object = self.get_object()
        context = self.get_detail_context_data(object=self.object)
        return self.render_to_response(context)

    def get_url_kwargs(self, obj):
        info = meta.model_info(type(obj))
        return {key: getattr(obj, key) for key in info.primary_keys}

    def get_detail_context_object_name(self, obj):
        """Get the name to use for the object."""
        model = self.get_model()
        return model.__name__.lower()

    def get_detail_context_data(self, **kwargs):
        """
        Returns detail context data for template rendering
        """
        context = {}
        if self.object:
            context["object"] = self.object
            context_object_name = self.get_detail_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)


class ModelFormMixin(FormMixin, RetrieveModelMixin):
    """
    Common mixin for handling sqlalchemy model forms in viewsets
    """

    fields = None
    form_class = None
    success_url = None

    def get_form_class(self):
        """
        Returns the form class to be used
        """
        if self.fields is not None and self.form_class:
            raise ImproperlyConfigured("Specifying both 'fields' and 'form_class' is not permitted.")

        if self.form_class:
            return self.form_class

        model = self.get_model()
        return modelform_factory(model, fields=self.fields, session=self.get_session())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form
        """
        kwargs = super().get_form_kwargs()
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
        """
        Checks if form is valid and processes accordingly
        """
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        """
        Processes a valid form
        """
        self.object = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handles invalid form
        """
        return self.render_to_response(self.get_form_context_data(form=form))

    def get_form_context_data(self, **kwargs):
        """
        Return form context data for template rendering
        """
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        return self.get_detail_context_data(**kwargs)


class CreateModelMixin(ModelFormMixin):
    """
    A mixin for supporting creating objects

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    POST   /                        create          <resource name>-list
    GET    /new/                    new             <resource name>-new
    ====== ======================== =============== ======================
    """

    def new(self, request, *args, **kwargs):
        """New action for displaying a form for creating an object"""
        return self.render_to_response(self.get_create_context_data())

    def create(self, request, *args, **kwargs):
        """Create action for creating an object"""
        form = self.get_form()
        return self.process_form(form)

    def get_create_context_data(self, **kwargs):
        """
        Returns new context data for template rendering
        """
        return self.get_form_context_data(**kwargs)


class UpdateModelMixin(ModelFormMixin):
    """
    A mixin for supporting updating objects

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /<pk>/edit/              edit            <resource name>-edit
    POST   /<pk>/                   update          <resource name>-detail
    PUT    /<pk>/                   update          <resource name>-detail
    PATCH  /<pk>/                   update          <resource name>-detail
    ====== ======================== =============== ======================
    """

    def edit(self, request, *args, **kwargs):
        """Edit action for displaying a form for editing an object"""
        self.object = self.get_object()
        return self.render_to_response(self.get_update_context_data())

    def update(self, request, *args, **kwargs):
        """Update action for updating an object"""
        self.object = self.get_object()
        form = self.get_form()
        return self.process_form(form)

    def get_update_context_data(self, **kwargs):
        """
        Returns edit context data for template rendering
        """
        return self.get_form_context_data(**kwargs)


class DeleteModelMixin(RetrieveModelMixin):
    """
    A mixin for supporting deleting objects

    When used with router, it will map the following operations to actions on the viewset

    ====== ======================== =============== ======================
    Method Path                     Action          Route Name
    ====== ======================== =============== ======================
    GET    /<pk>/delete/            confirm_destoy  <resource name>-delete
    POST   /<pk>/delete/            destroy         <resource name>-delete
    DELETE /<pk>/                   destroy         <resource name>-detail
    ====== ======================== =============== ======================
    """

    destroy_success_url = None

    def confirm_destroy(self, request, *args, **kwargs):
        """Confirm_destory action for displaying deletion confirmation for an object"""
        self.object = self.get_object()
        return self.render_to_response(self.get_destroy_context_data())

    def destroy(self, request, *args, **kwargs):
        """Destroy action for deletion of an object"""
        self.object = self.get_object()
        self.perform_destoy(self.object)
        return HttpResponseRedirect(self.get_destroy_success_url())

    def perform_destoy(self, obj):
        """
        Performs the deletion operation
        """
        session = self.get_session()
        session.delete(obj)
        session.flush()

    def get_destroy_context_data(self, **kwargs):
        """
        Returns destory context data for rendering deletion confirmation page
        """
        return self.get_detail_context_data(**kwargs)

    def get_destroy_success_url(self):
        """
        Return the url to redirect to after successful deletion of an object
        """
        if self.destroy_success_url:
            return self.destroy_success_url.format(**vars(self.object))

        raise ImproperlyConfigured(
            "No URL to redirect to. Either provide a url or override this function to return a url"
        )
