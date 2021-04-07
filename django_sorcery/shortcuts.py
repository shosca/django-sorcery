"""Some Django like shortcuts that support sqlalchemy models."""
from contextlib import suppress

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from sqlalchemy.exc import InvalidRequestError


def _get_query(klass):

    query = getattr(klass, "query", None) or getattr(klass, "objects", None)

    if query:
        return query

    with suppress(AttributeError, InvalidRequestError):
        klass._only_full_mapper_zero("get")
        return klass

    raise ImproperlyConfigured("Couldn't figure out the query for model {cls}".format(cls=klass.__name__))


def get_object_or_404(klass, *args, **kwargs):
    """Use session.get() to return an object, or raise a Http404 exception if
    the object does not exist.

    klass may be a Model, or Query object. All other passed arguments
    and keyword arguments are used in the get() query.
    """
    query = _get_query(klass)

    instance = query.get(*args, **kwargs)

    if instance is None:
        raise Http404("No %s matches the given query." % query)

    return instance


def get_list_or_404(klass, *args, **kwargs):
    """Use filter() to return a list of objects, or raise a Http404 exception
    if the count is 0.

    klass may be a Model or Query object. All other passed arguments
    used in filter() and keyword arguments are used in filter_by().
    """
    query = _get_query(klass)

    if args:
        query = query.filter(*args)

    if kwargs:
        query = query.filter_by(**kwargs)

    if not query.count():
        raise Http404("No %s matches the given query." % query)

    return query
