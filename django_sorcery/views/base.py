# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import literal
from sqlalchemy.exc import InvalidRequestError

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.translation import gettext
from django.views.generic.base import ContextMixin

from ..db.models import get_primary_keys
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
        query = None
        if model:

            query = getattr(model, "query", None) or getattr(model, "objects", None)

            if query is None and self.session:
                query = self.session.query(model)

        if query and self.query_options:
            query = query.options(*self.query_options)

        if not query:

            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define %(cls)s.model and %(cls)s.session, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )

        return query

    def get_session(self):
        if self.session is None:
            self.session = self.get_queryset().session

        return self.session

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


class BaseMultipleObjectMixin(SQLAlchemyMixin):

    allow_empty = True
    paginate_by = None
    paginate_orphans = 0
    paginator_class = Paginator
    page_kwarg = "page"
    ordering = None

    def get_queryset(self):
        """
        Return the list of items for this view.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        queryset = super(BaseMultipleObjectMixin, self).get_queryset()

        ordering = self.get_ordering()
        if ordering is not None:
            queryset = queryset.order_by(*ordering)

        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            is_empty = True
            if self.get_paginate_by(queryset) is not None:

                if hasattr(queryset, "session"):
                    session = queryset.session
                    is_empty = not session.query(literal(True)).filter(queryset.exists()).scalar()

                else:
                    is_empty = not next(iter(queryset), None)

            if is_empty:
                raise Http404(
                    gettext("Empty list and '%(class_name)s.allow_empty' is False.")
                    % {"class_name": self.__class__.__name__}
                )

        return queryset

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.ordering

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        return self.paginate_by

    def get_paginate_orphans(self):
        """
        Return the maximum number of orphans extend the last page by when
        paginating.
        """
        return self.paginate_orphans

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        """Return an instance of the paginator for this view."""
        return self.paginator_class(
            queryset, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page, **kwargs
        )

    def paginate_queryset(self, queryset, page_size):
        """
        Paginate queryset
        """
        paginator = self.get_paginator(
            queryset, page_size, orphans=self.get_paginate_orphans(), allow_empty_first_page=self.get_allow_empty()
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == "last":
                page_number = paginator.num_pages
            else:
                raise Http404(gettext("Page is not 'last', nor can it be converted to an int."))

        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())

        except InvalidPage as e:
            raise Http404(
                gettext("Invalid page (%(page_number)s): %(message)s") % {"page_number": page_number, "message": str(e)}
            )

    def get_allow_empty(self):
        """
        Return ``True`` if the view should display empty lists and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty


class BaseSingleObjectMixin(SQLAlchemyMixin):

    object = None
    slug_field = "slug"
    slug_url_kwarg = "slug"
    query_pkg_and_slug = False

    def get_object(self, queryset=None):
        """
        Return the object the view is displaying

        Require `self.queryset` and the primary key attributes or the slug attributes in the URLconf.
        Subclasses can override this to return any object
        """

        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        model = self.get_model()
        pk = get_primary_keys(model, self.kwargs)
        obj = None

        if pk is not None:
            obj = queryset.get(pk)

        if slug is not None and (pk is None and self.query_pkg_and_slug):
            slug_field = self.get_slug_field()
            obj = next(iter(queryset.filter_by(**{slug_field: slug})), None)

        if pk is None and slug is None:
            raise AttributeError(
                "Generic detail view %s must be called with either an object "
                "pk or a slug in the URLconf." % self.__class__.__name__
            )

        if obj is None:
            raise Http404(gettext("No %(cls)s instance found matching the query" % {"cls": model.__name__}))

        return obj

    def get_slug_field(self):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.slug_field
