# -*- coding: utf-8 -*-
"""
Django-esque field metadata and interface providers.
"""
from __future__ import absolute_import, print_function, unicode_literals
import datetime
import decimal
import enum

import six
from dateutil.parser import parse

import sqlalchemy as sa

from django import forms as djangoforms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import fields as djangomodelfields
from django.forms import fields as djangofields
from django.utils import timezone
from django.utils.text import capfirst

from ... import fields as sorceryfields
from ...utils import sanitize_separators, suppress


def _make_naive(value):
    if settings.USE_TZ and timezone.is_aware(value):
        default_timezone = timezone.get_default_timezone()
        value = timezone.make_naive(value, default_timezone)
    return value


class column_info(object):
    """
    A helper class that makes sqlalchemy property and column inspection easier
    """

    default_form_class = None
    default_error_messages = djangomodelfields.Field.default_error_messages

    __slots__ = ("name", "property", "column", "parent", "_coercer", "error_messages")

    def __new__(cls, *args, **kwargs):
        args = list(args)
        column = kwargs.pop("column", None)

        if args:
            column = args.pop(0)

        column_info_mapping = getattr(settings, "DJANGO_SORCERY", {}).get("column_info_mapping", COLUMN_INFO_MAPPING)

        override_cls = None
        for base in column.type.__class__.mro():
            if base in column_info_mapping:
                override_cls = column_info_mapping.get(base, cls)

            enum_class = getattr(column.type, "enum_class", object) or object
            for sub in enum_class.mro():
                if (base, sub) in column_info_mapping:
                    override_cls = column_info_mapping.get((base, sub), cls)
                    break

            if override_cls:
                break

        _cls = override_cls or cls
        instance = super(column_info, _cls).__new__(_cls)
        return instance

    def __init__(self, column, prop=None, parent=None, name=None):
        self.property = prop
        self.column = column
        self.parent = parent
        self._coercer = None
        self.name = name or (self.property.key if self.property is not None else self.column.key)

        self.error_messages = {}
        for c in reversed(self.__class__.mro()):
            self.error_messages.update(getattr(c, "default_error_messages", {}))
        self.error_messages.update(column.info.get("error_messages") or {})

    def __repr__(self):
        return "<{!s}({!s}.{!s}){!s}>".format(
            self.__class__.__name__,
            self.parent.model_class.__name__ if self.parent else "<None>",
            self.name or "<None>",
            " pk" if self.column.primary_key else "",
        )

    @property
    def coercer(self):
        """
        Form field to be used to coerce data types
        """
        if not self._coercer:
            self._coercer = self.formfield(localize=True) or djangofields.Field(localize=True)
        return self._coercer

    @property
    def attribute(self):
        """
        Returns the instrumented attribute itself for buiding query expressions
        """
        return getattr(self.parent_model, self.property.key) if self.parent_model else None

    @property
    def validators(self):
        """
        Returns validators of the field
        """
        return self.column.info.get("validators") or []

    @property
    def null(self):
        """
        Returns if field allows null
        """
        return not self.column.primary_key and self.column.nullable

    @property
    def required(self):
        """
        Returns if the field is required
        """
        return self.column.info.get("required", not self.column.nullable)

    @property
    def parent_model(self):
        """
        Returns the model class the field belongs to
        """
        return self.property.parent.class_ if self.property else None

    @property
    def help_text(self):
        """
        Returns field help text
        """
        return self.column.doc

    @property
    def empty_values(self):
        """
        Returns field empty values
        """
        return self.column.info.get("empty_values") or self.coercer.empty_values

    @property
    def default(self):
        """
        Returns the default for the field
        """
        return getattr(self.column.default, "arg", None)

    @property
    def choices(self):
        """
        Returns the choices for the field, only used in sqlalchemy enum typed columns
        """
        return getattr(self.column.type, "enum_class", None) or getattr(self.column.type, "enums", None)

    @property
    def widget(self):
        """
        Returns the form ui widget for the field
        """
        return self.column.info.get("widget_class")

    @property
    def label(self):
        """
        Returns the ui label for the field
        """
        label = self.column.info.get("label")
        if label:
            return label

        return capfirst(" ".join(self.name.split("_"))) if self.name else None

    @property
    def form_class(self):
        """
        Returns the form class to be used for the field
        """
        return self.column.info.get("form_class") or self.default_form_class

    @property
    def field_kwargs(self):
        """
        Returns form field kwargs for the field
        """
        kwargs = {"required": self.required, "validators": self.validators, "help_text": self.help_text}
        if self.default:
            if not callable(self.default):
                kwargs["initial"] = self.default

        if self.label:
            kwargs["label"] = self.label

        if self.widget:
            kwargs["widget"] = self.widget

        return kwargs

    def formfield(self, form_class=None, **kwargs):
        """
        Returns the form field for the field.
        """
        form_class = form_class or self.form_class

        if form_class is not None:
            field_kwargs = self.field_kwargs
            field_kwargs.update(kwargs)
            return form_class(**field_kwargs)

    def to_python(self, value):
        """
        Convert input value to appropriate python object
        """
        return self.coercer.to_python(value)

    def clean(self, value, instance):
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.
        """
        value = self.to_python(value)
        self.validate(value, instance)
        self.run_validators(value)
        return value

    def validate(self, value, instance):
        """
        Validate value and raise ValidationError if necessary
        """
        getattr(instance, "clean_" + self.name, bool)()

    def run_validators(self, value):
        """
        Run field's validators and raise ValidationError if necessary
        """
        if value in self.empty_values:
            return

        errors = []
        for v in self.validators:
            try:
                v(value)
            except ValidationError as e:
                errors.extend(e.error_list)

        if errors:
            raise ValidationError(errors)


class string_column_info(column_info):
    """
    Provides meta info for string columns
    """

    default_form_class = djangofields.CharField

    @property
    def field_kwargs(self):
        kwargs = super(string_column_info, self).field_kwargs
        kwargs["max_length"] = self.column.type.length
        return kwargs

    def to_python(self, value):
        if value is None:
            return value
        return six.text_type(value).strip()


class text_column_info(string_column_info):
    """
    Provides meta info for text columns
    """

    @property
    def widget(self):
        return super(text_column_info, self).widget or djangoforms.Textarea


class choice_column_info(column_info):
    """
    Provides meta info for enum columns with simple choices
    """

    default_form_class = djangofields.TypedChoiceField

    @property
    def form_choices(self):
        """
        Returns choices for form field
        """
        return [(x, x) for x in self.choices]

    @property
    def field_kwargs(self):
        kwargs = super(choice_column_info, self).field_kwargs
        kwargs["choices"] = self.form_choices

        # Many of the subclass-specific formfield arguments (min_value,
        # max_value) don't apply for choice fields, so be sure to only pass
        # the values that TypedChoiceField will understand.
        for k in list(kwargs):
            if k not in (
                "choices",
                "coerce",
                "disabled",
                "empty_value",
                "enum_class",
                "error_messages",
                "help_text",
                "initial",
                "label",
                "required",
                "show_hidden_initial",
                "validators",
                "widget",
            ):
                del kwargs[k]  # pragma: nocover

        return kwargs

    def to_python(self, value):
        if value is None:
            return value

        with suppress(TypeError, ValueError):
            parsed = type(next(iter(self.choices)))(value)
            if parsed in self.choices:
                return parsed

        parsed = six.text_type(value).strip()
        parsed = self.coercer.to_python(parsed)
        if parsed in self.coercer.empty_values:
            return None

        raise ValidationError("%(value)r is not a valid choice.", code="invalid", params={"value": str(value)})


class enum_column_info(choice_column_info):
    """
    Provides meta info for enum columns with Enum choices
    """

    default_form_class = sorceryfields.EnumField

    @property
    def form_choices(self):
        return self.choices

    def to_python(self, value):
        if value is None:
            return value

        with suppress(TypeError, KeyError, ValueError):
            return self.choices[value]
        with suppress(TypeError, KeyError, ValueError):
            return self.choices(value)
        with suppress(TypeError, AttributeError):
            return getattr(self.choices, value)

        return self.coercer.to_python(value)


class numeric_column_info(column_info):
    """
    Provides meta info for numeric columns
    """

    default_form_class = djangofields.DecimalField

    @property
    def field_kwargs(self):
        kwargs = super(numeric_column_info, self).field_kwargs
        if self.column.type.python_type == decimal.Decimal:
            if self.max_digits is not None:
                kwargs["max_digits"] = self.max_digits
            if self.decimal_places is not None:
                kwargs["decimal_places"] = self.decimal_places
        return kwargs

    @property
    def max_digits(self):
        """
        Return max digits for the column
        """
        return self.column.type.precision

    @property
    def decimal_places(self):
        """
        Return decimal places for the column
        """
        return self.column.type.scale

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, decimal.Decimal):
            return value
        if isinstance(value, float):
            value = decimal.Context(prec=self.max_digits).create_decimal_from_float(value)
            return value.to_integral() if value == value.to_integral() else value.normalize()
        if isinstance(value, six.integer_types):
            return decimal.Decimal(value)

        parsed = sanitize_separators(six.text_type(value).strip())
        return self.coercer.to_python(parsed)


class boolean_column_info(column_info):
    """
    Provides meta info for boolean columns
    """

    @property
    def form_class(self):
        form_class = super(boolean_column_info, self).form_class
        if form_class:
            return form_class

        return djangofields.NullBooleanField if self.null else djangofields.BooleanField

    def to_python(self, value):
        if value is None:
            return value
        if value in (True, False):
            return bool(value)
        if value in ("t", "T"):
            return True
        if value in ("f", "F"):
            return False
        return self.coercer.to_python(value)


class date_column_info(column_info):
    """
    Provides meta info for date columns
    """

    default_form_class = djangofields.DateField

    @property
    def coercer(self):
        coercer = super(date_column_info, self).coercer
        coercer.input_formats = settings.DATE_INPUT_FORMATS
        return coercer

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return _make_naive(value).date()
        if isinstance(value, datetime.date):
            return value

        parsed = six.text_type(value).strip()
        with suppress(ValueError):
            return _make_naive(datetime.datetime.fromtimestamp(float(parsed))).date()
        with suppress(ValueError):
            return _make_naive(parse(parsed)).date()

        return _make_naive(self.coercer.to_python(parsed)).date()


class datetime_column_info(column_info):
    """
    Provides meta info for datetime columns
    """

    default_form_class = djangofields.DateTimeField

    @property
    def coercer(self):
        coercer = super(datetime_column_info, self).coercer
        coercer.input_formats = settings.DATETIME_INPUT_FORMATS
        return coercer

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return _make_naive(value)
        if isinstance(value, datetime.date):
            return _make_naive(datetime.datetime(value.year, value.month, value.day))

        parsed = six.text_type(value).strip()
        with suppress(ValueError):
            return _make_naive(datetime.datetime.fromtimestamp(float(parsed)))

        with suppress(ValueError):
            return _make_naive(parse(parsed))

        return _make_naive(self.coercer.to_python(parsed))


class float_column_info(column_info):
    """
    Provides meta info for float columns
    """

    default_form_class = djangofields.FloatField

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, float):
            return value

        parsed = six.text_type(value).strip()
        return self.coercer.to_python(parsed)


class integer_column_info(column_info):
    """
    Provides meta info for integer columns
    """

    default_form_class = djangofields.IntegerField

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, int):
            return value

        parsed = six.text_type(value).strip()
        return self.coercer.to_python(parsed)


class interval_column_info(column_info):
    """
    Provides meta info for interval columns
    """

    default_form_class = djangofields.DurationField

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.timedelta):
            return value

        parsed = six.text_type(value).strip()
        return self.coercer.to_python(parsed)


class time_column_info(column_info):
    """
    Provides meta info for time columns
    """

    default_form_class = djangofields.TimeField

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, datetime.datetime):
            return value.time()

        parsed = six.text_type(value).strip()
        return self.coercer.to_python(parsed)


COLUMN_INFO_MAPPING = {
    (sa.sql.sqltypes.Enum, enum.Enum): enum_column_info,
    (sa.sql.sqltypes.Enum, object): choice_column_info,
    sa.sql.sqltypes.String: string_column_info,
    sa.sql.sqltypes.Text: text_column_info,
    sa.sql.sqltypes.Numeric: numeric_column_info,
    sa.sql.sqltypes.Float: float_column_info,
    sa.sql.sqltypes.Integer: integer_column_info,
    sa.sql.sqltypes.Boolean: boolean_column_info,
    sa.sql.sqltypes.Date: date_column_info,
    sa.sql.sqltypes.DateTime: datetime_column_info,
    sa.sql.sqltypes.Interval: interval_column_info,
    sa.sql.sqltypes.Time: time_column_info,
}
