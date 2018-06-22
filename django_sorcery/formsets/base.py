# -*- coding: utf-8 -*-
"""
Helper functions for creating FormSet classes from SQLAlchemy models.
"""
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.forms import fields as djangofields
from django.forms.formsets import BaseFormSet, formset_factory
from django.forms.widgets import HiddenInput

from ..db.meta import model_info
from ..db.models import get_primary_keys
from ..forms import ModelForm, modelform_factory


class BaseModelFormSet(BaseFormSet):
    """
    A ``FormSet`` for editing a queryset and/or adding new objects to it.
    """

    model = None
    session = None
    absolute_max = 2000

    # Set of fields that must be unique among forms of this set.
    unique_fields = set()

    def __init__(self, data=None, files=None, auto_id="id_%s", prefix=None, queryset=None, initial=None, **kwargs):
        self.session = kwargs.pop("session", self.session)
        self.queryset = queryset
        self.initial_extra = initial
        kwargs.update({"data": data, "files": files, "auto_id": auto_id, "prefix": prefix})
        super(BaseModelFormSet, self).__init__(**kwargs)

    def initial_form_count(self):
        """Return the number of forms that are required in this FormSet."""
        if not (self.data or self.files):
            return len(self.get_queryset())

        return super(BaseModelFormSet, self).initial_form_count()

    def _existing_object(self, pk):
        info = model_info(self.model)

        if not isinstance(pk, tuple):
            pk = (pk,)

        if not hasattr(self, "_object_dict"):
            self._object_dict = {info.mapper.primary_key_from_instance(o): o for o in self.get_queryset()}

        return self._object_dict.get(pk)

    def _construct_form(self, i, **kwargs):
        pk_required = i < self.initial_form_count()
        if pk_required:
            if self.is_bound:

                info = model_info(self.model)
                pks = {}
                for name, pk_info in info.primary_keys.items():
                    pk_key = "%s-%s" % (self.add_prefix(i), name)
                    pk_val = self.data.get(pk_key)
                    pks[name] = pk_info.column.type.python_type(pk_val) if pk_val else None

                pk = get_primary_keys(self.model, pks)

                kwargs["instance"] = self._existing_object(pk)
            else:
                kwargs["instance"] = self.get_queryset()[i]
        elif self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs["initial"] = self.initial_extra[i - self.initial_form_count()]
            except IndexError:
                pass
        kwargs["session"] = self.session
        form = super(BaseModelFormSet, self)._construct_form(i, **kwargs)
        return form

    def add_fields(self, form, index):
        info = model_info(self.model)

        if form.instance in self.session:
            for name in info.primary_keys:
                pk_field = djangofields.Field(initial=getattr(form.instance, name, None), widget=HiddenInput)
                form.fields[name] = pk_field

        super(BaseModelFormSet, self).add_fields(form, index)

    def get_queryset(self):
        if not hasattr(self, "_queryset"):
            if self.queryset is not None:
                qs = self.queryset
            else:
                qs = self.session.query(self.model)[: self.absolute_max]

            if hasattr(qs, "all"):
                qs = qs.all()

            self._queryset = qs

        return self._queryset

    def delete_existing(self, obj, **kwargs):
        """Deletes an existing model instance."""
        self.session.delete(obj)

    def save(self, flush=True, **kwargs):
        """
        Save model instances for every form, adding and changing instances
        as necessary, and return the list of instances.
        """
        self.new_objects = []
        self.changed_objects = []
        self.deleted_objects = []
        saved_instances = []

        for form in self.extra_forms:
            if not form.has_changed():
                continue

            if self.can_delete and self._should_delete_form(form):
                continue

            obj = form.save(flush=flush)
            self.new_objects.append(obj)
            saved_instances.append(obj)

        for form in self.initial_forms:
            if form in self.deleted_forms:
                self.deleted_objects.append(form.instance)
                self.delete_existing(form.instance)
                continue

            elif form.has_changed():
                self.changed_objects.append(form.instance)

            obj = form.save(flush=flush)
            saved_instances.append(obj)

        return saved_instances

    save.alters_data = True


def modelformset_factory(
    model,
    form=ModelForm,
    formfield_callback=None,
    formset=BaseModelFormSet,
    extra=1,
    can_delete=False,
    can_order=False,
    max_num=None,
    fields=None,
    exclude=None,
    widgets=None,
    validate_max=False,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None,
    min_num=None,
    validate_min=False,
    field_classes=None,
    session=None,
):
    meta = getattr(form, "Meta", None)
    fields = getattr(meta, "fields", fields)
    exclude = getattr(meta, "exclude", exclude)
    if fields is None and exclude is None:
        raise ImproperlyConfigured(
            "Calling modelformset_factory without defining 'fields' or " "'exclude' explicitly is prohibited."
        )

    form = modelform_factory(
        model,
        form=form,
        fields=fields,
        exclude=exclude,
        formfield_callback=formfield_callback,
        widgets=widgets,
        localized_fields=localized_fields,
        labels=labels,
        help_texts=help_texts,
        error_messages=error_messages,
        field_classes=field_classes,
        session=session,
    )

    FormSet = formset_factory(
        form,
        formset,
        extra=extra,
        min_num=min_num,
        max_num=max_num,
        can_order=can_order,
        can_delete=can_delete,
        validate_min=validate_min,
        validate_max=validate_max,
    )
    class_name = model.__name__ + "FormSet"
    return type(form)(str(class_name), (FormSet,), {"model": model, "session": session})
