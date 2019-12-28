# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six

from sqlalchemy.orm.interfaces import MapperOption

from django.core.exceptions import ImproperlyConfigured


def _key_from_query(query):
    """
    Given a Query, create a cache key.

    There are many approaches to this; here we use the simplest, which is to create an md5 hash of the text of the SQL
    statement, combined with stringified versions of all the bound parameters within it. There's a bit of a
    performance hit with compiling out "query.statement" here; other approaches include setting up an explicit cache
    key with a particular Query, then combining that with the bound parameter values.
    """

    stmt = query.with_labels().statement
    compiled = stmt.compile()
    params = compiled.params
    return " ".join([six.text_type(compiled)] + [six.text_type(params[k]) for k in sorted(params)])


class FromCache(MapperOption):
    """Specifies that a Query should load results from a cache."""

    propagate_to_loaders = False

    def __init__(self, region, expiration_time=None, key_maker=_key_from_query):
        """
        Provides caching mechanism for a query
        --------------------------------------

        region: any
            The cache region. Can be a dogpile.cache region object

        expiration_time: int or datetime.timedelta
            The expiration time that will be passed to region.

        keymaker: callable
            A callable that will take the query and generate a cache key out of it.

        Note that this approach does *not* detach the loaded objects from the current session. If the cache backend is
        an in-process cache (like "memory") and lives beyond the scope of the current session's transaction, those
        objects may be expired. The method here can be modified to first expunge() each loaded item from the current
        session before returning the list of items, so that the items in the cache are not the same ones in the
        current Session.
        """
        if region is None:
            raise ImproperlyConfigured("FromCache requires a cache region")
        self.expiration_time = expiration_time
        self.key_maker = key_maker
        self.region = region

    def process_query(self, query):
        """Process a Query during normal loading operation."""
        query.caching_option = self

    def get(self, query, merge=True, createfunc=None):
        """
        Return the value from the cache for this query.
        """
        createfunc = query.__iter__
        cache_key = self.key_maker(query)
        cached_value = self.region.get_or_create(
            cache_key, lambda: list(createfunc()), expiration_time=self.expiration_time
        )
        if merge:
            cached_value = query.merge_result(cached_value, load=False)
        return cached_value

    def invalidate(self, query):
        cache_key = self.key_maker(query)
        self.region.delete(cache_key)
