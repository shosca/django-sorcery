"""
Signals
-------

Implements some basic signals using blinker
"""
from threading import local

import blinker
from blinker._utilities import defaultdict


class ScopedSignal(blinker.NamedSignal):
    """Same as ``NamedSignal`` but signal is scoped to a thread.

    In other words, if a receiver is attached within a specific thread,
    even if signal is sent in another thread, in that other thread no
    receivers will be present and hence nothing will execute. Useful for
    adding one-off signal handlers for example to be executed at the end
    of unit-of-work (e.g. request) without adding a possibility that
    another thread might start executing the receiver.
    """

    def __init__(self, name, doc=None):
        self.name = name
        self.__doc__ = doc
        self.local = local()
        self.cleanup()

    @property
    def receivers(self):
        """Return all thread scoped receivers."""
        return self.local.__dict__.setdefault("receivers", {})

    @property
    def _by_receiver(self):
        return self.local.__dict__.setdefault("_by_receiver", defaultdict(set))

    @property
    def _by_sender(self):
        return self.local.__dict__.setdefault("_by_sender", defaultdict(set))

    @property
    def _weak_senders(self):
        return self.local.__dict__.setdefault("_weak_senders", {})

    def cleanup(self):
        """Cleans up signal for the current thread scope."""
        self._clear_state()


class Namespace(blinker.Namespace):
    """A signal namespace that also manages scoped signals."""

    def scopedsignal(self, name, doc=None):
        """Returns the scoped signal for a given name."""
        try:
            return self[name]

        except KeyError:
            return self.setdefault(name, ScopedSignal(name, doc))

    @property
    def scoped_signals(self):
        """Returns all scoped signals."""
        for signal in self.values():
            if isinstance(signal, ScopedSignal):
                yield signal


all_signals = Namespace()

before_flush = all_signals.signal("before_flush")
after_flush = all_signals.signal("after_flush")

before_commit = all_signals.signal("before_commit")
before_scoped_commit = all_signals.scopedsignal("before_scoped_commit")

after_commit = all_signals.signal("after_commit")
after_scoped_commit = all_signals.scopedsignal("after_scoped_commit")

after_rollback = all_signals.signal("after_rollback")
after_scoped_rollback = all_signals.scopedsignal("after_scoped_rollback")

engine_created = all_signals.signal("engine_created")

before_middleware_request = all_signals.signal("before_middleware_request")
after_middleware_response = all_signals.signal("after_middleware_response")

declare_first = all_signals.signal("declare_first")
declare_last = all_signals.signal("declare_last")

before_create_all = all_signals.signal("before_create_all")
after_create_all = all_signals.signal("after_create_all")

before_drop_all = all_signals.signal("before_drop_all")
after_drop_all = all_signals.signal("after_drop_all")

alembic_app_created = all_signals.signal("alembic_app_created")
alembic_config_created = all_signals.signal("alembic_config_created")
alembic_include_object = all_signals.signal("alembic_include_object")
alembic_process_revision_directives = all_signals.signal("alembic_process_revision_directives")
