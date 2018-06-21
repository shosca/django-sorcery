# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from ..db.meta import model_info
from ..forms import ModelForm
from .base import BaseModelFormSet, modelformset_factory


class BaseInlineFormSet(BaseModelFormSet):
    def __init__(self, data=None, files=None, instance=None, save_as_new=False, prefix=None, queryset=None, **kwargs):

        self.instance = self.fk.parent_model() if instance is None else instance
        self.save_as_new = save_as_new
        if queryset is None:
            queryset = getattr(self.instance, self.fk.name, [])

        super(BaseInlineFormSet, self).__init__(data, files, prefix=prefix, queryset=queryset, **kwargs)

    @classmethod
    def get_default_prefix(cls):
        return cls.fk.name

    def initial_form_count(self):
        if self.save_as_new:
            return 0

        return super(BaseInlineFormSet, self).initial_form_count()

    def save(self, flush=False, **kwargs):
        instances = super(BaseInlineFormSet, self).save(flush=flush)
        setattr(self.instance, self.fk.name, instances)
        return instances


def _get_relation_info(relation):
    info = model_info(relation.parent)
    rel = info.relationships[relation.key]
    if rel.uselist:
        return rel

    raise ValueError("Relationship '%s' is not one to many or many to many." % (relation))


def _get_foreign_key(relation, parent_model, model, fk_name=None):
    info = model_info(parent_model)
    if fk_name is None:
        relations = [
            relation for relation in info.relationships.values() if relation.related_model == model and relation.uselist
        ]
        if len(relations) == 1:
            return relations[0]

        raise ValueError("Couldn't find a relation from '%s' to '%s'." % (parent_model.__name__, model.__name__))


def inlineformset_factory(
    parent_model=None,
    model=None,
    relation=None,
    form=ModelForm,
    formset=BaseInlineFormSet,
    fk_name=None,
    fields=None,
    exclude=None,
    extra=3,
    can_order=False,
    can_delete=True,
    max_num=None,
    formfield_callback=None,
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
    """
    Return an ``InlineFormSet`` for the given kwargs.

    ``fk_name`` must be provided if ``model`` has more than one ``ForeignKey``
    to ``parent_model``.
    """
    if relation is not None:
        fk = _get_relation_info(relation)
        parent_model = fk.parent_model
        model = fk.related_model
    else:
        fk = _get_foreign_key(relation, parent_model, model, fk_name=fk_name)

    kwargs = {
        "form": form,
        "formfield_callback": formfield_callback,
        "formset": formset,
        "extra": extra,
        "can_delete": can_delete,
        "can_order": can_order,
        "fields": fields,
        "exclude": exclude,
        "min_num": min_num,
        "max_num": max_num,
        "widgets": widgets,
        "validate_min": validate_min,
        "validate_max": validate_max,
        "localized_fields": localized_fields,
        "labels": labels,
        "help_texts": help_texts,
        "error_messages": error_messages,
        "field_classes": field_classes,
        "session": session,
    }
    FormSet = modelformset_factory(model, **kwargs)
    FormSet.fk = fk
    return FormSet
