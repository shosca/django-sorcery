# -*- coding: utf-8 -*-
"""
Helper functions for creating Form classes from SQLAlchemy models.
"""
from __future__ import absolute_import, print_function, unicode_literals

import six

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.models import ModelFormOptions
from django.forms.utils import ErrorList
from django.utils.module_loading import import_string

from .db.models import model_to_dict
from .field_mapping import ALL_FIELDS, ModelFieldMapper, apply_limit_choices_to_form_field


class SQLAModelFormOptions(ModelFormOptions):

    def __init__(self, options=None):
        super(SQLAModelFormOptions, self).__init__(options=options)
        self.session = getattr(options, "session", None)


class ModelFormMetaclass(DeclarativeFieldsMetaclass):

    def __new__(cls, name, bases, attrs):
        mcs = super(ModelFormMetaclass, cls).__new__(cls, name, bases, attrs)

        base_formfield_callback = None
        for base in bases:
            if hasattr(base, "Meta") and hasattr(base.Meta, "formfield_callback"):
                base_formfield_callback = base.Meta.formfield_callback
                break

        formfield_callback = attrs.pop("formfield_callback", base_formfield_callback)

        if bases == (BaseModelForm,):
            return mcs

        opts = mcs._meta = SQLAModelFormOptions(getattr(mcs, "Meta", None))

        for opt in ["fields", "exclude", "localized_fields"]:
            value = getattr(opts, opt)
            if isinstance(value, six.string_types) and value != ALL_FIELDS:
                raise TypeError(
                    "%(model)s.Meta.%(opt)s cannot be a string. Did you mean to type: ('%(value)s',)?"
                    % {"model": mcs.__name__, "opt": opt, "value": value}
                )

        if opts.model:
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelForm without either the 'fields' attribute or the 'exclude' attribute is "
                    "prohibited; form %s needs updating." % name
                )

            if opts.fields == ALL_FIELDS:
                opts.fields = None

            mapper = import_string(settings.SQLALCHEMY_FORM_MAPPER) if hasattr(
                settings, "SQLALCHEMY_FORM_MAPPER"
            ) else ModelFieldMapper

            mcs.base_fields = mapper(opts, formfield_callback, apply_limit_choices_to=False).get_fields()

        else:
            mcs.base_fields = mcs.declared_fields

        return mcs


class BaseModelForm(BaseForm):

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        instance=None,
        use_required_attribute=None,
        renderer=None,
        session=None,
    ):
        opts = self._meta
        opts.session = opts.session or session
        if opts.model is None:
            raise ValueError("ModelForm has no model class specified.")

        if opts.session is None:
            raise ValueError("ModelForm has no session specified.")

        self.instance = opts.model() if instance is None else instance
        object_data = self.model_to_dict()
        object_data.update(initial or {})
        self._validate_unique = False
        super(BaseModelForm, self).__init__(
            data,
            files,
            auto_id,
            prefix,
            object_data,
            error_class,
            label_suffix,
            empty_permitted,
            use_required_attribute=use_required_attribute,
            renderer=renderer,
        )
        for field in self.fields.values():
            apply_limit_choices_to_form_field(field)

    def model_to_dict(self):
        opts = self._meta
        return model_to_dict(self.instance, opts.fields, opts.exclude)

    def update_attribute(self, instance, name, field, value):
        field_setter = getattr(self, "set_" + name, None)
        if field_setter:
            field_setter(instance, name, field, value)
        else:
            setattr(instance, name, value)

    def save(self, flush=True, **kwargs):
        opts = self._meta

        if self.errors:
            raise ValueError(
                "The %s could not be saved because the data didn't validate." % (self.instance.__class__.__name__,)
            )

        self.instance = self.save_instance()

        if flush:
            opts.session.flush()

        return self.instance

    def save_instance(self, instance=None, cleaned_data=None):

        instance = instance or self.instance
        cleaned_data = cleaned_data or self.cleaned_data

        for name, field in self.fields.items():
            if name in cleaned_data:
                self.update_attribute(self.instance, name, field, cleaned_data[name])

        if instance not in self._meta.session:
            self._meta.session.add(instance)
        return instance


class ModelForm(six.with_metaclass(ModelFormMetaclass, BaseModelForm)):
    pass


def modelform_factory(model, form=ModelForm, formfield_callback=None, **kwargs):
    defaults = [
        "fields",
        "exclude",
        "widgets",
        "localized_fields",
        "labels",
        "help_texts",
        "error_messages",
        "field_classes",
        "session",
    ]

    attrs = {"model": model}
    for key in defaults:
        value = kwargs.get(key)
        if value is not None:
            attrs[key] = value

    bases = (form.Meta,) if hasattr(form, "Meta") else tuple()
    meta = type(str("Meta"), bases, attrs)
    if formfield_callback:
        meta.formfield_callback = staticmethod(formfield_callback)

    class_name = model.__name__ + "Form"

    if getattr(meta, "fields", None) is None and getattr(meta, "exclude", None) is None:
        raise ImproperlyConfigured(
            "Calling modelform_factory without defining 'fields' or 'exclude' explicitly is prohibited."
        )

    return type(form)(str(class_name), (form,), {"Meta": meta, "formfield_callback": formfield_callback})
