# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from ...db import signals


def include_object(obj, name, type_, reflected, compare_to):
    results = signals.alembic_include_object.send(
        obj, name=name, type_=type_, reflected=reflected, compare_to=compare_to
    )
    if len(results) > 0:
        return all([res[1] for res in results])

    return True


def process_revision_directives(context, revision, directives):
    signals.alembic_process_revision_directives.send(context, revision=revision, directives=directives)
