# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import functools
import inspect

import six

import sqlalchemy as sa
import sqlalchemy.orm  # noqa
from sqlalchemy.ext.declarative import declarative_base

from django.db import DEFAULT_DB_ALIAS

from ..utils import make_args
from .composites import BaseComposite, CompositeField
from .models import Base
from .query import Query, QueryProperty
from .relations import RelationsMixin
from .session import SignallingSession
from .signals import all_signals, engine_created
from .transaction import TransactionContext
from .url import make_url


class _sqla_meta(type):
    def __new__(cls, name, bases, attrs):
        typ = super(_sqla_meta, cls).__new__(cls, name, bases, attrs)

        # figure out all props to be proxied
        dummy = sa.orm.Session()
        props = {i for i in dir(dummy) if not i.startswith("__")}
        props.update(sa.orm.Session.public_methods)

        for i in props:
            if not hasattr(typ, name):
                if hasattr(dummy, i) and inspect.isroutine(getattr(dummy, i)):
                    setattr(typ, i, sa.orm.scoping.instrument(i))
                else:
                    setattr(typ, i, sa.orm.scoping.makeprop(i))

        return typ


class SQLAlchemy(six.with_metaclass(_sqla_meta, RelationsMixin)):
    """
    This class itself is a scoped session and provides very thin and useful abstractions and conventions for using
    sqlalchemy with django.
    """

    session_class = SignallingSession
    query_class = Query
    registry_class = sa.util.ThreadLocalRegistry
    model_class = Base

    BaseComposite = BaseComposite
    CompositeField = CompositeField

    def __init__(self, alias=None, **kwargs):
        self.alias = alias or DEFAULT_DB_ALIAS
        self.url, self.kwargs = self._make_url(alias)
        self.kwargs.update(kwargs)
        self.session_class = self.kwargs.get("session_class", None) or self.session_class
        self.query_class = self.kwargs.get("query_class", None) or self.query_class
        self.registry_class = self.kwargs.get("registry_class", None) or self.registry_class
        self.model_class = self.kwargs.get("model_class", None) or self.model_class
        self.engine_options = self.kwargs.get("engine_options", {})
        self.session_options = self.kwargs.get("session_options", {})

        self.session_options.setdefault("query_cls", self.query_class)
        self.session_options.setdefault("class_", self.session_class)

        self.middleware = self.make_middleware()
        self.Model = self._make_declarative(self.model_class)

        for module in sa, sa.sql, sa.orm:
            for key in module.__all__:
                if not hasattr(self, key):
                    setattr(self, key, getattr(module, key))

        self.collections = sa.orm.collections
        self.event = sa.event
        self.relationship = self._wrap(self.relationship)
        self.relation = self._wrap(self.relation)
        self.dynamic_loader = self._wrap(self.dynamic_loader)

    def __call__(self, **kwargs):
        return self.session(**kwargs)

    @property
    def registry(self):
        if not hasattr(self, "_registry"):
            engine = self._create_engine(self.url, **self.engine_options)
            self._registry = self.registry_class(sa.orm.sessionmaker(bind=engine, **self.session_options))

        return self._registry

    @property
    def inspector(self):
        return self.inspect(self.engine)

    def session(self, **kwargs):
        """
        Return the current session, creating it if necessary using session_factory for the current scope
        Any kwargs provided will be passed on to the session_factory. If there's already a session in
        current scope, will raise InvalidRequestError
        """
        if kwargs:
            if self.registry.has():
                raise sa.exc.InvalidRequestError(
                    "Scoped session is already present; " "no new arguments may be specified."
                )

            else:
                session = self.session_factory(**kwargs)
                self.registry.set(session)
                return session

        else:
            return self.registry()

    def Table(self, name, *args, **kwargs):
        assert name is not None, "Table requires `name` argument"
        assert len(args) > 0, "Table at least takes one column argument"
        for arg in args:
            assert not isinstance(arg, sa.MetaData), "Passing a `metadata` is not allowed"

        return sa.Table(name, self.metadata, *args, **kwargs)

    def _set_query_class(self, cls, kwargs):
        query_class = self.query_class
        try:
            query_class = cls.query_class
        except AttributeError:
            pass

        kwargs["query_class"] = query_class

    def _wrap(self, fn):
        """
        Wrapper that sets the 'query_class' argument from the model's
        query_class attribute
        """

        @functools.wraps(fn)
        def func(cls, *args, **kwargs):
            """
            Wraps a function setting default `query_class` argument
            """
            self._set_query_class(cls, kwargs)

            if "backref" in kwargs:
                backref = kwargs["backref"]
                backref_kwargs = {}
                if isinstance(backref, tuple):
                    backref, backref_kwargs = backref
                    self._set_query_class(backref, backref_kwargs)

                kwargs["backref"] = (backref, backref_kwargs)

            return fn(cls, *args, **kwargs)

        return func

    def _create_engine(self, url, **kwargs):
        engine = sa.create_engine(url, **kwargs)
        engine_created.send(engine)
        return engine

    def _make_url(self, alias):
        """
        Makes a url out of alias or url string
        ----------------------------------------------------------
        alias: str
            a config alias or url string
        """
        return make_url(alias)

    def _make_declarative(self, model):
        """
        Creates the base class that the models should inherit from
        ----------------------------------------------------------
        model: class
            The base class for the declarative_base to be inherited from
        """
        base = declarative_base(cls=model)

        # allow to customize things in custom base model
        if not hasattr(base, "query_class"):
            base.query_class = self.query_class
        if not hasattr(base, "query"):
            base.query = self.queryproperty()
        if not hasattr(base, "objects"):
            base.objects = self.queryproperty()

        return base

    @property
    def engine(self):
        """
        Current engine
        """
        return self.bind

    @property
    def metadata(self):
        """
        Current metadata
        """
        return self.Model.metadata

    @property
    def session_factory(self):
        """
        Current session factory to create sessions
        """
        return self.registry.createfunc

    def __repr__(self):
        return "<{} engine={!r}>".format(self.__class__.__name__, self.url)

    def queryproperty(self, *args, **kwargs):
        """
        Generate a query property for a model
        """
        model = None
        if args and isinstance(args[0], type) and issubclass(args[0], self.Model):
            model = args[0]
            args = args[1:]

        return QueryProperty(self, model, *args, **kwargs)

    def atomic(self, savepoint=True):
        """
        Create a savepoint or transaction scope
        """
        return TransactionContext(self, savepoint=savepoint)

    def make_middleware(self):
        """
        Creates a middleware to be used in a django application
        """
        from .middleware import SQLAlchemyDBMiddleware

        return type(str("{}SQLAlchemyMiddleware".format(self.alias)), (SQLAlchemyDBMiddleware,), {"db": self})

    def args(self, *args, **kwargs):
        """
        Useful for setting table args and mapper args on models
        """
        return make_args(*args, **kwargs)

    def remove(self):
        """
        Remove the current scoped session
        """
        if self.registry.has():
            self.registry().close()
        self.registry.clear()
        for signal in all_signals.scoped_signals:
            signal.cleanup()

    def create_all(self):
        """
        Create the schema in db
        """
        self.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """
        Drop the schema in db
        """
        self.metadata.drop_all(bind=self.engine)
