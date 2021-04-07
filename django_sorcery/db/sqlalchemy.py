"""SQLAlchemy goodies that provides a nice interface to using sqlalchemy with
django."""
import functools
import inspect

import sqlalchemy as sa
import sqlalchemy.orm  # noqa
from sqlalchemy.ext.declarative import declarative_base

from ..utils import make_args
from . import fields, signals
from .composites import BaseComposite, CompositeField
from .models import Base, BaseMeta
from .query import Query, QueryProperty
from .relations import RelationsMixin
from .session import SignallingSession
from .transaction import TransactionContext


def instrument(name):
    def do(self, *args, **kwargs):
        return getattr(self.registry(), name)(*args, **kwargs)

    return do


def makeprop(name):
    def get(self):
        return getattr(self.registry(), name)

    return property(get)


class _sqla_meta(type):
    def __new__(mcs, name, bases, attrs):
        typ = super().__new__(mcs, name, bases, attrs)

        # figure out all props to be proxied
        dummy = sa.orm.Session()
        props = {i for i in dir(dummy) if not i.startswith("__")}
        props.update(
            [
                "__contains__",
                "__iter__",
                "add",
                "add_all",
                "autocommit",
                "autoflush",
                "begin",
                "begin_nested",
                "bind",
                "bulk_insert_mappings",
                "bulk_save_objects",
                "bulk_update_mappings",
                "close",
                "commit",
                "connection",
                "delete",
                "deleted",
                "dirty",
                "execute",
                "expire",
                "expire_all",
                "expunge",
                "expunge_all",
                "flush",
                "get_bind",
                "identity_map",
                "info",
                "is_active",
                "is_modified",
                "merge",
                "new",
                "no_autoflush",
                "query",
                "refresh",
                "rollback",
                "scalar",
            ]
        )

        for i in props:
            if not hasattr(typ, name):
                if hasattr(dummy, i) and inspect.isroutine(getattr(dummy, i)):
                    setattr(typ, i, instrument(i))
                else:
                    setattr(typ, i, makeprop(i))

        return typ


class SQLAlchemy(RelationsMixin, metaclass=_sqla_meta):
    """This class itself is a scoped session and provides very thin and useful
    abstractions and conventions for using sqlalchemy with django."""

    session_class = SignallingSession
    query_class = Query
    registry_class = sa.util.ThreadLocalRegistry
    metadata_class = sa.MetaData
    model_class = Base

    BaseComposite = BaseComposite
    CompositeField = CompositeField

    def __init__(self, url, **kwargs):
        self.url, self.kwargs = url, kwargs
        self.alias = kwargs.get("alias")
        self.session_class = self.kwargs.get("session_class", None) or self.session_class
        self.query_class = self.kwargs.get("query_class", None) or self.query_class
        self.registry_class = self.kwargs.get("registry_class", None) or self.registry_class
        self.metadata_class = self.kwargs.get("metadata_class", None) or self.metadata_class
        self.model_class = self.kwargs.get("model_class", None) or self.model_class
        self.engine_options = self.kwargs.get("engine_options", {})
        self.session_options = self.kwargs.get("session_options", {})

        self.session_options.setdefault("query_cls", self.query_class)
        self.session_options.setdefault("class_", self.session_class)

        self.middleware = self.make_middleware()
        self.models_registry = []
        self.metadata = self.metadata_class(**self.kwargs.get("metadata_kwargs", {}))
        self.Model = self._make_declarative(self.model_class)

        for module, is_partial in [(sa, False), (sa.sql, False), (sa.orm, False), (fields, True)]:
            for key in module.__all__:
                if not hasattr(self, key) and not hasattr(type(self), key):
                    value = getattr(module, key)
                    setattr(
                        self, key, functools.wraps(value)(functools.partial(value, db=self)) if is_partial else value
                    )

        self.collections = sa.orm.collections
        self.event = sa.event
        self.relationship = self._wrap(self.relationship)
        self.relation = self._wrap(self.relation)
        self.dynamic_loader = self._wrap(self.dynamic_loader)
        self._registry = None

    def __call__(self, **kwargs):
        return self.session(**kwargs)

    @property
    def registry(self):
        """Returns scoped registry instance."""
        if not self._registry:
            engine = self._create_engine(self.url, **self.engine_options)
            self._registry = self.registry_class(sa.orm.sessionmaker(bind=engine, **self.session_options))

        return self._registry

    @property
    def inspector(self):
        """Returns engine inspector.

        Useful for querying for db schema info.
        """
        return sa.inspect(self.engine)

    def session(self, **kwargs):
        """Return the current session, creating it if necessary using
        session_factory for the current scope Any kwargs provided will be
        passed on to the session_factory.

        If there's already a session in current scope, will raise
        InvalidRequestError
        """
        if not kwargs:
            return self.registry()

        if self.registry.has():
            raise sa.exc.InvalidRequestError("Scoped session is already present; " "no new arguments may be specified.")

        session = self.session_factory(**kwargs)
        self.registry.set(session)
        return session

    def Table(self, name, *args, **kwargs):
        """Returns a sqlalchemy table that is automatically added to
        metadata."""
        assert name is not None, "Table requires `name` argument"
        assert args, "Table at least takes one column argument"
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
        """Wrapper that sets the 'query_class' argument from the model's
        query_class attribute."""

        @functools.wraps(fn)
        def func(cls, *args, **kwargs):
            """Wraps a function setting default `query_class` argument."""
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
        signals.engine_created.send(engine)
        return engine

    def _make_declarative(self, model):
        """
        Creates the base class that the models should inherit from
        ----------------------------------------------------------
        model: class
            The base class for the declarative_base to be inherited from
        """
        base = declarative_base(
            cls=model, metadata=self.metadata, metaclass=type("BaseMeta", (BaseMeta,), {"db": self})
        )

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
        """Current engine."""
        return self.bind

    @property
    def session_factory(self):
        """Current session factory to create sessions."""
        return self.registry.createfunc

    def __repr__(self):
        return "<{} engine={!r}>".format(self.__class__.__name__, self.url)

    def queryproperty(self, *args, **kwargs):
        """Generate a query property for a model."""
        model = None
        if args and isinstance(args[0], type) and issubclass(args[0], self.Model):
            model = args[0]
            args = args[1:]

        return QueryProperty(self, model, *args, **kwargs)

    def atomic(self, savepoint=True):
        """Create a savepoint or transaction scope."""
        return TransactionContext(self, savepoint=savepoint)

    def make_middleware(self):
        """Creates a middleware to be used in a django application."""
        from .middleware import SQLAlchemyDBMiddleware

        return type("SQLAlchemyMiddleware", (SQLAlchemyDBMiddleware,), {"db": self})

    def args(self, *args, **kwargs):
        """Useful for setting table args and mapper args on models."""
        return make_args(*args, **kwargs)

    def remove(self):
        """Remove the current scoped session."""
        if self.registry.has():
            self.registry().close()
        self.registry.clear()
        for signal in signals.all_signals.scoped_signals:
            signal.cleanup()

    def create_all(self):
        """Create the schema in db."""
        result = signals.before_create_all.send(db=self, bind=self.engine)
        if all(i[1] in [True, None] for i in result):
            self.metadata.create_all(bind=self.engine)
            signals.after_create_all.send(self, db=self, bind=self.engine)

    def drop_all(self):
        """Drop the schema in db."""
        result = signals.before_drop_all.send(db=self, bind=self.engine)
        if all(i[1] in [True, None] for i in result):
            self.metadata.drop_all(bind=self.engine)
            signals.after_drop_all.send(self, db=self, bind=self.engine)
