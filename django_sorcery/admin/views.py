# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sqlalchemy as sa

from django.contrib.admin.views import main
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect


csrf_protect_m = method_decorator(csrf_protect)


class ChangeList(main.ChangeList):
    def get_queryset(self, request):
        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params, filters_use_distinct) = self.get_filters(request)

        qs = self.root_queryset
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_use_distinct = self.model_admin.get_search_results(request, qs, self.query)

        # Remove duplicates from results, if necessary
        if filters_use_distinct | search_use_distinct:
            return qs.distinct()
        else:
            return qs

    def translate_order_bys(self, orders):
        expressions = []
        for order in orders:
            direction = sa.asc
            if order[0] == "-":
                order = order[1:]
                direction = sa.desc

            col_info = self.model.primary_keys.get(order) or self.model.properties(order)
            expressions.append(direction(col_info.attribute))

        return expressions

    def apply_select_related(self, qs):
        # TODO (serkan): return eager optioned query here
        return qs

    def get_ordering(self, request, queryset):
        """
        Return the list of ordering fields for the change list.
        First check the get_ordering() method in model admin, then check
        the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by calling _get_deterministic_ordering() with the
        constructed ordering.
        """
        params = self.params
        ordering = list(self.model_admin.get_ordering(request) or self._get_default_ordering())
        if main.ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[main.ORDER_VAR].split(".")
            for p in order_params:
                try:
                    none, pfx, idx = p.rpartition("-")
                    field_name = self.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue  # No 'admin_order_field', skip it
                    if hasattr(order_field, "as_sql"):
                        # order_field is an expression.
                        ordering.append(order_field.desc() if pfx == "-" else order_field.asc())
                    # reverse order if order_field has already "-" as prefix
                    elif order_field.startswith("-") and pfx == "-":
                        ordering.append(order_field[1:])
                    else:
                        ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        return self._get_deterministic_ordering(ordering)
