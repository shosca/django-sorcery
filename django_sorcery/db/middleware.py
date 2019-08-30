# -*- coding: utf-8 -*-
"""
Django middleware support for sqlalchemy
"""
import logging

from . import databases
from .signals import all_signals


before_middleware_request = all_signals.signal("before_middleware_request")
after_middleware_response = all_signals.signal("after_middleware_response")

logger = logging.getLogger(__name__)


class BaseMiddleware(object):
    """
    Base middleware implementation that supports unit of work per request for django
    """

    logger = logger

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            return self.return_response(request, response)

        response = self.get_response(request)
        return self.process_response(request, response)

    def process_request(self, request):
        """
        Hook for adding arbitrary logic to request processing
        """
        before_middleware_request.send(self.__class__, middleware=self, request=request)

    def process_response(self, request, response):
        """
        Commits or rollbacks scoped sessions depending on status code then removes them
        """
        if response.status_code >= 400:
            self.rollback(request=request, response=response)
            return self.return_response(request, response)

        if request.method not in {"PUT", "POST", "PATCH", "GET", "DELETE"}:
            self.rollback(request=request, response=response)
            return self.return_response(request, response)

        try:
            self.flush(request=request, response=response)
            self.commit(request=request, response=response)
        except Exception:
            self.logger.error("Error during flush or commit")
            self.rollback(request=request, response=response)
            self.return_response(request, response)
            raise

        return self.return_response(request, response)

    def return_response(self, request, response):
        """
        Hook for adding arbitrary logic to response processing
        """
        self.remove(request=request, response=response)

        after_middleware_response.send(self.__class__, middleware=self, request=request, response=response)

        return response


class SQLAlchemyDBMiddleware(BaseMiddleware):
    """
    A base SQLAlchemy db middleware.

    Used by SQLAlchemy to provide a default middleware for a single db, it will first try to flush
    and if successfull, proceed with commit. If there are any errors during flush, will issue a rollback.
    """

    db = None

    def rollback(self, request, response):
        """
        Rolls back current scoped session
        """
        self.db.rollback()

    def flush(self, request, response):
        """
        Flushes current scoped session
        """
        self.db.flush()

    def commit(self, request, response):
        """
        Commits current scoped session
        """
        self.db.commit()

    def remove(self, request, response):
        """
        Removes current scoped session
        """
        self.db.remove()


class SQLAlchemyMiddleware(SQLAlchemyDBMiddleware):
    """
    A sqlalchemy middleware that manages all the dbs configured and initialized.

    it will first try to flush all the configured and initialized SQLAlchemy instances and if
    successfull, proceed with commit. If there are any errors during flush, all transactions
    will be rolled back.
    """

    db = databases
