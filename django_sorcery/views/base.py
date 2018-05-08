# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy.exc import InvalidRequestError

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import ContextMixin

from ..utils import suppress


class SQLAlchemyMixin(ContextMixin):
    queryset = None
    model = None
    session = None
    context_object_name = None
    query_options = None

    @classmethod
    def get_model(cls):
        """
        Returns the model class
        """
        if cls.model is not None:
            return cls.model

        with suppress(AttributeError, InvalidRequestError):
            return cls.queryset._only_entity_zero().class_

        raise ImproperlyConfigured(
            "Couldn't figure out the model for %(cls)s, either provide a queryset or set the model "
            "and the session attribute" % {"cls": cls.__name__}
        )

    def get_queryset(self):
        """
        Return the `QuerySet` that will be used to look up the object.
        This method is called by the default implementation of get_object() and
        may not be called if get_object() is overridden.
        """
        if self.queryset is not None:
            return self.queryset

        model = self.get_model()
        if model and self.session:
            query = self.session.query(model)
            if self.query_options:
                query = query.options(*self.query_options)

            return query

        raise ImproperlyConfigured(
            "%(cls)s is missing a QuerySet. Define %(cls)s.model and %(cls)s.session, %(cls)s.queryset, or override "
            "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
        )

    def get_model_template_name(self):
        """
        Returns the base template path
        """
        model = self.get_model()
        app_config = apps.get_containing_app_config(model.__module__)
        return "%s/%s%s.html" % (
            model.__name__.lower() if app_config is None else app_config.label,
            model.__name__.lower(),
            self.template_name_suffix,
        )
