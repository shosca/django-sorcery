# -*- coding: utf-8 -*-
"""
Default alembic signal configuration
"""

from ...db import signals


def include_object(obj, name, type_, reflected, compare_to):
    """
    The default include_object handler for alembic, delegates to alembic_include_object signal

    The return value will be considered True if all the signal handlers return True for the
    object to be included in migration.
    """
    results = signals.alembic_include_object.send(
        obj, name=name, type_=type_, reflected=reflected, compare_to=compare_to
    )
    if results:
        return all(res[1] for res in results)

    return True


def process_revision_directives(context, revision, directives):
    """
    The default process_revision_directives handler for alembic, delegates to
    alembic_process_revision_directives
    """
    signals.alembic_process_revision_directives.send(context, revision=revision, directives=directives)
