"""Field mapping from SQLAlchemy type's to form fields."""
import json
from contextlib import suppress

from django.core.exceptions import ValidationError
from django.forms import fields as djangofields
from django.utils.translation import gettext_lazy


class EnumField(djangofields.ChoiceField):
    """Form field for using an Enum as choices."""

    empty_value = None

    def __init__(self, enum_class=None, choices=None, **kwargs):
        self.enum_class = enum_class or choices

        kwargs["choices"] = [(e.name, e.value) for e in self.enum_class]
        if not kwargs.get("required", True):
            empty_label = kwargs.pop("empty_label", "")
            kwargs["choices"] = [(self.empty_value, empty_label)] + kwargs["choices"]

        kwargs.pop("max_length", None)
        super().__init__(**kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            value = None

        if value is None:
            return

        with suppress(TypeError, KeyError, ValueError):
            return self.enum_class[value]
        with suppress(TypeError, KeyError, ValueError):
            return self.enum_class(value)
        with suppress(TypeError, AttributeError):
            return getattr(self.enum_class, value)

        raise ValidationError(self.error_messages["invalid_choice"], code="invalid", params={"value": str(value)})

    def valid_value(self, value):
        if value is None:
            return not self.required

        return value in self.enum_class

    def prepare_value(self, value):
        return value if value is None else value.name

    def bound_data(self, data, initial):
        value = super().bound_data(data, initial)
        return self.prepare_value(value)


class ModelChoiceIterator:
    """Iterator for sqlalchemy query for model choice fields."""

    def __init__(self, field):
        self.field = field

    def __iter__(self):

        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)

        for obj in self.field.queryset:
            yield self.choice(obj)

    def __len__(self):
        return self.field.queryset.count() + (1 if self.field.empty_label is not None else 0)

    def choice(self, obj):
        """Returns choice item for django choice field."""
        return (self.field.prepare_value(obj), self.field.label_from_instance(obj))


class ModelChoiceField(djangofields.ChoiceField):
    """A ChoiceField whose choices are a sqlalchemy model relationship."""

    default_error_messages = {
        "invalid_choice": "Select a valid choice. That choice is not one of the available choices."
    }

    iterator = ModelChoiceIterator

    def __init__(
        self,
        model,
        session,
        empty_label="---------",
        required=True,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        to_field_name=None,
        limit_choices_to=None,
        **kwargs,
    ):
        if required and (initial is not None):
            self.empty_label = None
        else:
            self.empty_label = empty_label

        djangofields.Field.__init__(
            self, required=required, widget=widget, label=label, initial=initial, help_text=help_text, **kwargs
        )

        self._choices = None
        self.model = model
        from .db import meta

        self.model_info = meta.model_info(model)
        self.session = session
        self._queryset = None
        self.limit_choices_to = limit_choices_to  # limit the queryset later.
        self.to_field_name = to_field_name

    def _get_queryset(self):
        return self._queryset or self.session.query(self.model)

    def _set_queryset(self, queryset):
        self._queryset = None if queryset is None else queryset

    queryset = property(_get_queryset, _set_queryset)

    def _get_choices(self):
        return self.iterator(self)

    choices = property(_get_choices, djangofields.ChoiceField._set_choices)

    def get_object(self, value):
        """Returns model instance."""
        if value in self.empty_values:
            return None

        pk = None
        try:
            pk = json.loads(value)
            if isinstance(pk, dict):
                pk = self.model_info.primary_keys_from_dict(pk)
        except TypeError:
            pk = value

        obj = self.session.query(self.model).get(pk)
        if obj is None:
            raise ValidationError(self.error_messages["invalid_choice"], code="invalid_choice")

        return obj

    def to_python(self, value):
        return self.get_object(value)

    def label_from_instance(self, obj):
        """Returns label from model instance."""
        return str(obj)

    def prepare_instance_value(self, obj):
        """Returns primary key from instance."""
        return self.model_info.primary_keys_from_instance(obj)

    def prepare_value(self, obj):
        if isinstance(obj, self.model):
            return self.prepare_instance_value(obj)

        return super().prepare_value(obj)

    def validate(self, value):
        return djangofields.Field.validate(self, value)

    def get_bound_field(self, form, field_name):
        self.widget.choices = self.choices
        return super().get_bound_field(form, field_name)

    def get_limit_choices_to(self):
        """Returns limit_choices_to for this model.

        If it is a callable, invoke it and return the result
        """
        if callable(self.limit_choices_to):
            return self.limit_choices_to()
        return self.limit_choices_to


class ModelMultipleChoiceField(ModelChoiceField):
    """A ChoiceField whose choices are a sqlalchemy model list relationship."""

    widget = djangofields.SelectMultiple
    hidden_widget = djangofields.MultipleHiddenInput
    default_error_messages = {
        "list": gettext_lazy("Enter a list of values."),
        "invalid_choice": gettext_lazy("Select a valid choice. %(value)s is not one of the available choices."),
    }

    def __init__(self, *args, **kwargs):
        kwargs["empty_label"] = None
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return []

        return list(self._check_values(value))

    def _check_values(self, value):
        return [self.get_object(pk) for pk in value]

    def prepare_value(self, value):
        try:
            return [self.prepare_instance_value(v) for v in value if not isinstance(v, str)]

        except Exception:
            return super().prepare_value(value)
