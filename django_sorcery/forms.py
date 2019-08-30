# -*- coding: utf-8 -*-
"""
Helper functions for creating Form classes from SQLAlchemy models.
"""
from collections import OrderedDict
from itertools import chain

import six

from django.core.exceptions import NON_FIELD_ERRORS, ImproperlyConfigured, ValidationError
from django.forms import ALL_FIELDS
from django.forms.forms import BaseForm as DjangoBaseForm, DeclarativeFieldsMetaclass
from django.forms.models import BaseModelForm as DjangoBaseModelForm, ModelFormOptions
from django.forms.utils import ErrorList

from .db import meta
from .utils import suppress


def _get_default_kwargs(
    info,
    session,
    fields=None,
    exclude=None,
    widgets=None,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None,
    field_classes=None,
):
    kwargs = {}
    if widgets and info.name in widgets:
        kwargs["widget"] = widgets[info.name]
    if labels and info.name in labels:
        kwargs["label"] = labels[info.name]
    if help_texts and info.name in help_texts:
        kwargs["help_text"] = help_texts[info.name]
    if error_messages and info.name in error_messages:
        kwargs["error_messages"] = error_messages[info.name]
    if field_classes and info.name in field_classes:
        kwargs["form_class"] = field_classes[info.name]

    if localized_fields == ALL_FIELDS:
        kwargs["localize"] = True
    if localized_fields and info.name in localized_fields:
        kwargs["localize"] = True

    if session is None:
        with suppress(AttributeError):
            session = info.related_model.query.session

    if isinstance(info, meta.relation_info):
        kwargs["session"] = session
    return kwargs


def fields_for_model(
    model,
    session,
    fields=None,
    exclude=None,
    widgets=None,
    formfield_callback=None,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None,
    field_classes=None,
    apply_limit_choices_to=True,
    **kwargs,
):
    """
    Returns a dictionary containing form fields for a given model
    """

    field_list = []
    info = meta.model_info(model)

    for name, attr in chain(info.properties.items(), info.relationships.items()):

        if name.startswith("_"):
            continue

        if fields and name not in fields:
            continue

        if exclude and name in exclude:
            continue

        kwargs = _get_default_kwargs(
            attr,
            session,
            fields=fields,
            exclude=exclude,
            widgets=widgets,
            localized_fields=localized_fields,
            labels=labels,
            help_texts=help_texts,
            error_messages=error_messages,
            field_classes=field_classes,
        )
        if formfield_callback is None:
            formfield = attr.formfield(**kwargs)
        elif not callable(formfield_callback):
            raise TypeError("formfield_callback must be a function or callable")
        else:
            formfield = formfield_callback(attr, **kwargs)

        if formfield is not None:
            if apply_limit_choices_to:
                apply_limit_choices_to_form_field(formfield)
            field_list.append((name, formfield))

    return OrderedDict(field_list)


def apply_limit_choices_to_form_field(formfield):
    """Apply limit_choices_to to the formfield's query if needed."""
    if hasattr(formfield, "queryset") and hasattr(formfield, "get_limit_choices_to"):
        limit_choices_to = formfield.get_limit_choices_to()
        if limit_choices_to is not None:
            formfield.queryset = formfield.queryset.filter(*limit_choices_to)


def model_to_dict(instance, fields=None, exclude=None):
    """
    Return a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """
    info = meta.model_info(type(instance))

    fields = set(
        fields or list(info.properties.keys()) + list(info.primary_keys.keys()) + list(info.relationships.keys())
    )
    exclude = set(exclude or [])
    data = {}
    for name in info.properties:

        if name.startswith("_"):
            continue

        if name not in fields:
            continue

        if name in exclude:
            continue

        data[name] = getattr(instance, name)

    for name, rel in info.relationships.items():
        related_info = meta.model_info(rel.related_model)

        if name.startswith("_"):
            continue

        if name not in fields:
            continue

        if name in exclude:
            continue

        if rel.uselist:
            for obj in getattr(instance, name):
                pks = related_info.primary_keys_from_instance(obj)
                if pks:
                    data.setdefault(name, []).append(pks)
        else:
            obj = getattr(instance, name)
            pks = related_info.primary_keys_from_instance(obj)
            if pks:
                data[name] = pks

    return data


class SQLAModelFormOptions(ModelFormOptions):
    """
    Model form options for sqlalchemy
    """

    def __init__(self, options=None):
        super().__init__(options=options)
        self.session = getattr(options, "session", None)


class ModelFormMetaclass(DeclarativeFieldsMetaclass):
    """
    ModelForm metaclass for sqlalchemy models
    """

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)

        base_formfield_callback = None
        for base in bases:
            if hasattr(base, "Meta") and hasattr(base.Meta, "formfield_callback"):
                base_formfield_callback = base.Meta.formfield_callback
                break

        formfield_callback = attrs.pop("formfield_callback", base_formfield_callback)

        if bases == (BaseModelForm,):
            return cls

        opts = cls._meta = SQLAModelFormOptions(getattr(cls, "Meta", None))

        for opt in ["fields", "exclude", "localized_fields"]:
            value = getattr(opts, opt)
            if isinstance(value, six.string_types) and value != ALL_FIELDS:
                raise TypeError(
                    "%(model)s.Meta.%(opt)s cannot be a string. Did you mean to type: ('%(value)s',)?"
                    % {"model": cls.__name__, "opt": opt, "value": value}
                )

        if opts.model:
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelForm without either the 'fields' attribute or the 'exclude' attribute is "
                    "prohibited; form %s needs updating." % name
                )

            if opts.fields == ALL_FIELDS:
                opts.fields = None

            cls.base_fields = fields_for_model(
                opts.model,
                opts.session,
                error_messages=opts.error_messages,
                exclude=opts.exclude,
                field_classes=opts.field_classes,
                fields=opts.fields,
                help_texts=opts.help_texts,
                labels=opts.labels,
                localized_fields=opts.localized_fields,
                widgets=opts.widgets,
                formfield_callback=formfield_callback,
                apply_limit_choices_to=False,
            )
            cls.base_fields.update(cls.declared_fields)
        else:
            cls.base_fields = cls.declared_fields

        return cls


class BaseModelForm(DjangoBaseModelForm):
    """
    Base ModelForm for sqlalchemy models
    """

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
        DjangoBaseForm.__init__(
            self,
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=object_data,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=empty_permitted,
            use_required_attribute=use_required_attribute,
            renderer=renderer,
        )
        for field in self.fields.values():
            apply_limit_choices_to_form_field(field)

    def model_to_dict(self):
        """
        Returns a dict containing the data in ``instance`` suitable for passing as forms ``initial`` keyword argument.
        """
        opts = self._meta
        return model_to_dict(self.instance, opts.fields, opts.exclude)

    def _update_errors(self, errors):
        custom_errors = self._meta.error_messages or {}
        error_dict = getattr(errors, "error_dict", None) or {NON_FIELD_ERRORS: errors}

        for field, messages in error_dict.items():
            error_messages = {}
            if field == NON_FIELD_ERRORS and NON_FIELD_ERRORS in custom_errors:
                error_messages = custom_errors[NON_FIELD_ERRORS]
            elif field in self.fields:
                error_messages = self.fields[field].error_messages

            for message in messages:
                if isinstance(message, ValidationError) and message.code in error_messages:
                    message.message = error_messages[message.code]

        self.add_error(None, errors)

    def is_valid(self, rollback=True):
        """
        Return True if the form has no errors, or False otherwise. Will also rollback the session transaction.
        """
        is_valid = super().is_valid()

        if not is_valid and rollback:
            self._meta.session.rollback()

        return is_valid

    def save(self, flush=True, **kwargs):
        """
        Makes form's self.instance model persistent and flushes the session.
        """
        opts = self._meta

        if self.errors:
            raise ValueError(
                "The %s could not be saved because the data didn't validate." % (self.instance.__class__.__name__,)
            )

        if self.instance not in opts.session:
            opts.session.add(self.instance)

        if flush:
            opts.session.flush()

        return self.instance

    def _post_clean(self):
        """
        Hook for performing additional cleaning after form cleaning is complete. Used for model validation in model
        forms.
        """
        try:
            self.instance = self.save_instance()
        except ValidationError as e:
            self._update_errors(e)

        try:
            getattr(self.instance, "full_clean", bool)()
        except ValidationError as e:
            self._update_errors(e)

    def save_instance(self, instance=None, cleaned_data=None):
        """
        Updates form's instance with cleaned data.
        """
        instance = instance or self.instance
        cleaned_data = cleaned_data or self.cleaned_data

        for name, field in self.fields.items():
            if name in cleaned_data:
                self.update_attribute(self.instance, name, field, cleaned_data[name])

        return instance

    def update_attribute(self, instance, name, field, value):
        """
        Provides hooks for updating form instance's attribute for a field with value.
        """
        field_setter = getattr(self, "set_" + name, None)
        if field_setter:
            field_setter(instance, name, field, value)
        else:
            setattr(instance, name, value)


class ModelForm(six.with_metaclass(ModelFormMetaclass, BaseModelForm)):
    """
    ModelForm base class for sqlalchemy models
    """


def modelform_factory(model, form=ModelForm, formfield_callback=None, **kwargs):
    """
    Return a ModelForm class containing form fields for the given model.
    """
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

    bases = (form.Meta,) if hasattr(form, "Meta") else ()
    meta_ = type(str("Meta"), bases, attrs)
    if formfield_callback:
        meta_.formfield_callback = staticmethod(formfield_callback)

    class_name = model.__name__ + "Form"

    if getattr(meta_, "fields", None) is None and getattr(meta_, "exclude", None) is None:
        raise ImproperlyConfigured(
            "Calling modelform_factory without defining 'fields' or 'exclude' explicitly is prohibited."
        )

    return type(form)(str(class_name), (form,), {"Meta": meta_, "formfield_callback": formfield_callback})
