# -*- coding: utf-8 -*-
"""
sqlalchemy profiling things
"""
import logging
import time
from collections import defaultdict, namedtuple
from functools import partial
from threading import local

import sqlalchemy as sa

from django.conf import settings


logger = logging.getLogger(__name__)
STATEMENT_TYPES = {"SELECT": "select", "INSERT INTO": "insert", "UPDATE": "update", "DELETE": "delete"}


Query = namedtuple("Query", ["timestamp", "statement", "parameters", "duration"])


class SQLAlchemyProfiler(object):
    """
    A sqlalchemy profiler that hooks into sqlalchemy engine and pool events and generate stats. Can also capture
    executed sql statements. Useful for profiling or testing sql statements.
    """

    def __init__(self, exclude=None, record_queries=True):
        self.local = local()
        self.exclude = exclude or []
        self.record_queries = record_queries

        self._events = [
            ("before_cursor_execute", sa.engine.Engine, self._before_cursor_execute),
            ("after_cursor_execute", sa.engine.Engine, self._after_cursor_execute),
            ("begin", sa.engine.Engine, partial(self._event_counter, count_event="begin")),
            ("begin_twophase", sa.engine.Engine, partial(self._event_counter, count_event="begin_twophase")),
            ("commit", sa.engine.Engine, partial(self._event_counter, count_event="commit")),
            ("commit_twophase", sa.engine.Engine, partial(self._event_counter, count_event="commit_twophase")),
            ("prepare_twophase", sa.engine.Engine, partial(self._event_counter, count_event="prepare_twophase")),
            ("release_savepoint", sa.engine.Engine, partial(self._event_counter, count_event="prepare_twophase")),
            ("rollback", sa.engine.Engine, partial(self._event_counter, count_event="rollback")),
            ("rollback_savepoint", sa.engine.Engine, partial(self._event_counter, count_event="rollback_savepoint")),
            ("rollback_twophase", sa.engine.Engine, partial(self._event_counter, count_event="rollback_twophase")),
            ("savepoint", sa.engine.Engine, partial(self._event_counter, count_event="savepoint")),
            ("dbapi_error", sa.engine.Engine, partial(self._event_counter, count_event="dbapi_error")),
            ("engine_connect", sa.engine.Engine, partial(self._event_counter, count_event="engine_connect")),
            ("engine_disposed", sa.engine.Engine, partial(self._event_counter, count_event="engine_disposed")),
            ("checkin", sa.pool.Pool, partial(self._event_counter, count_event="pool_checkin")),
            ("checkout", sa.pool.Pool, partial(self._event_counter, count_event="pool_checkout")),
            ("close", sa.pool.Pool, partial(self._event_counter, count_event="pool_close")),
            ("close_detached", sa.pool.Pool, partial(self._event_counter, count_event="pool_close_detached")),
            ("connect", sa.pool.Pool, partial(self._event_counter, count_event="pool_connect")),
            ("detach", sa.pool.Pool, partial(self._event_counter, count_event="pool_detach")),
            ("first_connect", sa.pool.Pool, partial(self._event_counter, count_event="pool_first_connect")),
            ("invalidate", sa.pool.Pool, partial(self._event_counter, count_event="pool_invalidate")),
            ("reset", sa.pool.Pool, partial(self._event_counter, count_event="pool_reset")),
            ("soft_invalidate", sa.pool.Pool, partial(self._event_counter, count_event="pool_soft_invalidate")),
        ]

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        # stop all listeners when profiler gets garbage collected
        # py2 does not collect coverage on this
        self.stop()  # pragma: nocover

    def start(self):
        """
        Starts profiling by wiring up sqlalchemy events
        """
        self.clear()
        for ev, target, handler in self._events:
            try:
                if not sa.event.contains(target, ev, handler):
                    sa.event.listen(target, ev, handler)
            except Exception:  # pragma: nocover
                # Gets raised when pool doesnt support the event, so ignore it
                pass  # pragma: nocover

    def stop(self):
        """
        Stops profiling by detaching wired up sqlalchemy events
        """
        for ev, target, handler in self._events:
            try:
                if sa.event.contains(target, ev, handler):
                    sa.event.remove(target, ev, handler)
            except Exception:  # pragma: nocover
                # Gets raised when pool doesnt support the event, so ignore it
                pass  # pragma: nocover

    def clear(self):
        """
        Clears collected stats
        """
        self.local.__dict__.clear()

    @property
    def duration(self):
        """
        Return total statement execution duration
        """
        return self.local.__dict__.setdefault("duration", 0)

    @duration.setter
    def duration(self, value):
        """
        Sets total statement execution duration
        """
        self.local.duration = value

    @property
    def counts(self):
        """
        Returns a dict of counts per sqlalchemy event operation like executed statements, commits, rollbacks, etc..
        """
        return self.local.__dict__.setdefault("counts", defaultdict(lambda: 0))

    @property
    def queries(self):
        """
        Returns executed statements
        """
        return self.local.__dict__.setdefault("queries", [])

    @property
    def stats(self):
        """
        Returns profiling stats
        """
        stats = self.counts.copy()
        stats["duration"] = self.duration
        return stats

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        self.local._profiler_query_start_time = time.time()

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        end_time = time.time()
        start_time = self.local._profiler_query_start_time
        duration = end_time - start_time

        for e in self.exclude:
            if e in statement:
                return

        params = getattr(context, "compiled_parameters", [])
        if self.record_queries:
            self.queries.append(Query(int(round(time.time() * 1000)), statement, params, duration))

        self.duration += duration
        self.counts["execute"] += 1

        for start, event in STATEMENT_TYPES.items():
            if statement.startswith(start):
                self.counts[event] += 1
                break

    def _event_counter(self, *args, **kwargs):
        count_event = kwargs.get("count_event")
        self.counts[count_event] += 1


class SQLAlchemyProfilingMiddleware(object):
    """
    Django middleware that provides sqlalchemy statistics
    """

    logger = logger

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.profiler = SQLAlchemyProfiler(record_queries=False)

    @property
    def log_results(self):
        """
        Determines if stats should be logged or not
        """
        return settings.DEBUG

    @property
    def header_results(self):
        """
        Determines if stats should be returned as headers or not
        """
        return settings.DEBUG

    def start(self):
        """
        Starts profiling and disables restarts
        """
        self.profiler.start()
        self.start = lambda: None

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_request(self, request):
        """
        Starts profiling and resets stats doe the request
        """
        self.start()
        self.profiler.clear()

    def process_response(self, request, response):
        """
        Logs current request stats and also returns stats as headers
        """
        try:
            stats = self.profiler.stats
            if stats["duration"] or self.log_results:
                self.log(**{"sa_{}".format(k): v for k, v in stats.items()})
        except Exception:  # pragma: nocover
            # The show must go on...
            pass  # pragma: nocover
        else:
            if self.header_results:
                for k, v in stats.items():
                    response["X-SA-{}".format("".join(i.title() for i in k.split("_")))] = v
        self.profiler.clear()
        return response

    def log(self, **kwargs):
        """
        Log sqlalchemy stats for current request
        """
        self.logger.info("SQLAlchemy profiler %s", " ".join("{}={}".format(k, v) for k, v in kwargs.items()))
