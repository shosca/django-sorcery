# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import logging

from . import databases
from .signals import all_signals


before_middleware_request = all_signals.signal("before_middleware_request")
after_middleware_response = all_signals.signal("after_middleware_response")

logger = logging.getLogger(__name__)


class BaseMiddleware(object):

    logger = logger

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            return self.return_response(request, response)

        response = self.get_response(request)
        response = self.process_response(request, response)
        return self.return_response(request, response)

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

        else:
            if request.method in {"PUT", "POST", "PATCH", "GET", "DELETE"}:
                try:
                    self.flush(request=request, response=response)
                    self.commit(request=request, response=response)
                except Exception:
                    self.logger.error("Error during flush or commit")
                    self.rollback(request=request, response=response)

            else:
                self.rollback(request=request, response=response)

        return self.return_response(request, response)

    def return_response(self, request, response):
        self.remove(request=request, response=response)

        after_middleware_response.send(self.__class__, middleware=self, request=request, response=response)

        return response


class SQLAlchemyDBMiddleware(BaseMiddleware):

    db = None

    def rollback(self, request, response):
        self.db.rollback()

    def flush(self, request, response):
        self.db.flush()

    def commit(self, request, response):
        self.db.commit()

    def remove(self, request, response):
        self.db.remove()


class SQLAlchemyMiddleware(SQLAlchemyDBMiddleware):

    db = databases
