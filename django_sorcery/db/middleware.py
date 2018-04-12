# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from . import databases


class BaseMiddleware(object):

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            self.remove(request, response)
            return response

        response = self.get_response(request)

        return self.process_response(request, response)

    def process_request(self, request):
        """
        Hook for adding arbitrary logic to request processing
        """

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
                    self.rollback(request=request, response=response)

            else:
                self.rollback(request=request, response=response)

        self.remove(request=request, response=response)

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

    def rollback(self, request, response):
        for db in databases.values():
            db.rollback()

    def flush(self, request, response):
        for db in databases.values():
            db.flush()

    def commit(self, request, response):
        for db in databases.values():
            db.commit()

    def remove(self, request, response):
        for db in databases.values():
            db.remove()
