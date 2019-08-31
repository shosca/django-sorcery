# -*- coding: utf-8 -*-
"""
Common mixins used in models
"""

from . import meta


class CleanMixin(object):
    """
    Mixin for adding django-style ``full_clean`` validation to any object.

    Base model in :py:class:`..sqlalchemy.SQLAlchemy` already uses this mixin applied.

    For example::

        class Address(db.Model):
            city = db.Column(db.String(20))
            state = db.Column(db.String(2))
            date = db.Column(db.Date())

            validators = [
                ValidateTogetherModelFields(["city", "state"]),
            ]

            def clean_date(self):
                if self.date > datetime.date.today():
                    raise ValidationError("Cant pick future date")

            def clean(self):
                if self.date.year < 1776 and self.state == "NY":
                    raise ValidationError("NY state did not exist before 1776")
    """

    def clean(self, **kwargs):
        """
        Hook for adding custom model validations before model is flushed.

        Should raise ``ValidationError`` if any errors are found.
        """

    def clean_fields(self, exclude=None, **kwargs):
        """
        Clean all fields on object
        """
        meta.model_info(self).clean_fields(self, exclude=exclude, **kwargs)

    def _get_properties_for_validation(self):
        """
        Needs to be implemented to return all properties for the object
        """

    def clean_nested_fields(self, exclude=None, **kwargs):
        """
        Clean all nested fields which includes composites
        """
        meta.model_info(self).clean_nested_fields(self, exclude=exclude, **kwargs)

    def _get_nested_objects_for_validation(self):
        """
        Needs to be implemented to return all nested objects
        """

    def clean_relation_fields(self, exclude, **kwargs):
        """
        Clean all relation fields
        """
        meta.model_info(self).clean_relation_fields(self, exclude=exclude, **kwargs)

    def _get_relation_objects_for_validation(self):
        """
        Needs to be implemented to return all relation objects
        """

    def run_validators(self, **kwargs):
        """
        Check all model validators registered on ``validators`` attribute
        """
        meta.model_info(self).run_validators(self, **kwargs)

    def full_clean(self, exclude=None, **kwargs):
        """
        Run model's full clean chain

        This will run all of these in this order:

        * will validate all columns by using ``clean_<column>`` methods
        * will validate all nested objects (e.g. composites) with ``full_clean``
        * will run through all registered validators on ``validators`` attribute
        * will run full model validation with ``self.clean()``
        * if ``recursive`` kwarg is provided, will recursively clean all relations.
          Useful when all models need to be explicitly cleaned without flushing to DB.
        """
        meta.model_info(self).full_clean(self, exclude=exclude, **kwargs)
