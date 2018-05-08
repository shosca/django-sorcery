# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import functools

import six

import sqlalchemy as sa
import sqlalchemy.orm  # noqa
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from django.db import DEFAULT_DB_ALIAS

from ..utils import make_args, setdefaultattr, suppress
from .models import Base
from .query import Query, QueryProperty
from .session import SignallingSession
from .signals import all_signals, engine_created
from .url import apply_engine_hacks, make_url


class TransactionContext(object):
    """
    Transaction context manager for maintaining a transaction or savepoint
    """

    def __init__(self, db, savepoint=True):
        self.db = db
        self.savepoint = savepoint
        self.transaction = None

    def __call__(self, func, *args, **kwargs):

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            with self.db.begin(subtransactions=True, nested=self.savepoint):
                return func(*args, **kwargs)

        return wrapped

    def __enter__(self):
        self.transaction = self.db.begin(subtransactions=True, nested=self.savepoint)
        self.transaction.__enter__()

    def __exit__(self, exception_type, value, traceback):
        self.transaction.__exit__(exception_type, value, traceback)
        self.transaction = None


class _sqla_meta(type):

    def __new__(cls, name, bases, attrs):
        typ = super(_sqla_meta, cls).__new__(cls, name, bases, attrs)

        # figure out all props to be proxied
        props = set([i for i in dir(sa.orm.Session()) if not i.startswith("__")])
        props.update(sa.orm.Session.public_methods)

        for i in props:
            if not hasattr(typ, name):
                if hasattr(sa.orm.Session, i) and callable(getattr(sa.orm.Session, i)):
                    setattr(typ, i, sa.orm.scoping.instrument(i))
                else:
                    setattr(typ, i, sa.orm.scoping.makeprop(i))

        return typ


class SQLAlchemy(six.with_metaclass(_sqla_meta, object)):
    """
    This class itself is a scoped session and provides very thin and useful abstractions and conventions for using
    sqlalchemy with django.
    """
    session_class = SignallingSession
    query_class = Query
    registry_class = sa.util.ThreadLocalRegistry
    model_class = Base

    def __init__(self, alias=None, **kwargs):
        self.alias = alias or DEFAULT_DB_ALIAS
        self.url, self.kwargs = self._make_url(alias)
        self.kwargs.update(kwargs)
        self.session_class = kwargs.pop("session_class", None) or self.session_class
        self.query_class = kwargs.pop("query_class", None) or self.query_class
        self.registry_class = kwargs.pop("registry_class", None) or self.registry_class
        self.model_class = kwargs.pop("model_class", None) or self.model_class
        self.engine_options = kwargs.pop("engine_options", {})
        self.session_options = kwargs.pop("session_options", {})

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

    def _get_kwargs_for_relation(self, kwargs, prefix="fk_"):
        opts = {}
        for key in list(kwargs.keys()):
            if key.startswith(prefix):
                opts[key] = kwargs.pop(key)
        return opts

    def OneToMany(self, remote_cls, **kwargs):
        """
        Use an event to build one-to-many relationship on a model and auto generates foreign key relationship from the
        remote table::

            class ModelOne(db.Model):
                pk = db.Column(.., primary_key=True)
                m2 = db.OneToMany("ModelTwo", ...)

            class ModelTwo(db.Model):
                pk = db.Column(.., primary_key=True)
                ...

            will create ModelTwo.m1_pk automatically for the relationship
        """

        @declared_attr
        def o2m(cls):
            """
            one to many relationship attribute for declarative
            """
            rels = setdefaultattr(cls, "_relationships", set())
            kwargs.setdefault("info", {}).update(self._get_kwargs_for_relation(kwargs))
            kwargs["uselist"] = True
            backref = kwargs.get("backref")
            backref_kwargs = None
            if backref:
                if isinstance(backref, tuple):
                    with suppress(Exception):
                        backref, backref_kwargs = backref

                backref_kwargs = backref_kwargs or {}

                backref_kwargs["uselist"] = False
                kwargs["backref"] = (backref, backref_kwargs)

            rel = self.relationship(remote_cls, **kwargs)
            rel.direction = sa.orm.interfaces.ONETOMANY
            rels.add(rel)
            return rel

        return o2m

    def ManyToOne(self, remote_cls, **kwargs):
        """
        Use an event to build many-to-one relationship on a model and auto generates foreign key relationship on the
        remote table::

            class ModelOne(db.Model):
                pk = db.Column(.., primary_key=True)
                m2 = db.ManyToOne("ModelTwo", ...)

            class ModelTwo(db.Model):
                pk = db.Column(.., primary_key=True)
                ...

        will create ModelOne.m2_pk automatically for the relationship
        """

        @declared_attr
        def m2o(cls):
            """
            many to one relationship attribute for declarative
            """
            rels = setdefaultattr(cls, "_relationships", set())
            kwargs.setdefault("info", {}).update(self._get_kwargs_for_relation(kwargs))
            kwargs["uselist"] = False
            backref = kwargs.get("backref")
            if backref:
                backref_kwargs = None
                if isinstance(backref, tuple):
                    with suppress(Exception):
                        backref, backref_kwargs = backref

                backref_kwargs = backref_kwargs or {}

                backref_kwargs["uselist"] = True
                kwargs["backref"] = self.backref(backref, **backref_kwargs)

            rel = self.relationship(remote_cls, **kwargs)
            rel.direction = sa.orm.interfaces.MANYTOONE
            rels.add(rel)
            return rel

        return m2o

    def ManyToMany(self, remote_cls, table_name=None, **kwargs):
        """
        Use an event to build many-to-many relationship on a model and auto generates an association table or if a
        model is provided as secondary argument::

            class ModelOne(db.Model):
                pk = db.Column(.., primary_key=True)
                m2s = db.ManyToMany("ModelTwo", backref="m1s", table_name='m1m2s', ...)

            class ModelTwo(db.Model):
                pk = db.Column(.., primary_key=True)
                ...

        or with back_populates::

            class ModelOne(db.Model):
                pk = db.Column(.., primary_key=True)
                m2s = db.ManyToMany("ModelTwo", back_populates="m1s", table_name='m1m2s', ...)

            class ModelTwo(db.Model):
                pk = db.Column(.., primary_key=True)
                m1s = db.ManyToMany("ModelOne", back_populates="m2s", table_name='m1m2s', ...)

        will create ModelOne.m2s and ModelTwo.m1s relationship thru a provided secondary argument. If no secondary argument
        is provided, table_name is required as it will be used for the autogenerated association table.

        In the case of back_populates you have to provide the same table_name argument on both many-to-many
        declarations
        """

        @declared_attr
        def m2m(cls):
            """
            many to many relationship attribute for declarative
            """
            if "secondary" not in kwargs and table_name is None:
                raise sa.exc.ArgumentError(
                    "You need to provide secondary or table_name for the relation for the association table "
                    "that will be generated"
                )

            rels = setdefaultattr(cls, "_relationships", set())
            info = kwargs.setdefault("info", {})
            info.update(self._get_kwargs_for_relation(kwargs))
            info.update(self._get_kwargs_for_relation(kwargs, "table_"))
            if table_name:
                info["table_name"] = table_name

            kwargs["uselist"] = True

            backref = kwargs.get("backref")
            backref_kwargs = None
            if backref:
                if isinstance(backref, tuple):
                    with suppress(Exception):
                        backref, backref_kwargs = backref

                backref_kwargs = backref_kwargs or {}

                backref_kwargs["uselist"] = True
                kwargs["backref"] = self.backref(backref, **backref_kwargs)

            rel = self.relationship(remote_cls, **kwargs)
            rel.direction = sa.orm.interfaces.MANYTOMANY
            rels.add(rel)
            return rel

        return m2m

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
        apply_engine_hacks(engine)
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
        return TransactionContext(self, savepoint)

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
