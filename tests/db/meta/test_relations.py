# -*- coding: utf-8 -*-

import sqlalchemy as sa

from django.core.exceptions import ImproperlyConfigured

from django_sorcery import fields
from django_sorcery.db import meta

from ...base import TestCase
from ...models_terrible_relations import Foo
from ...testapp.models import Owner, Part, Vehicle


class TestRelationshipMeta(TestCase):
    def test_relationship_meta(self):
        info = meta.model_info(Vehicle)

        rel = info.relationships["owner"]

        self.assertEqual(rel.related_model, Owner)
        self.assertEqual(rel.related_table, Owner.__table__)
        self.assertEqual(rel.parent_mapper, Vehicle.__mapper__)
        self.assertEqual(rel.related_mapper, Owner.__mapper__)
        self.assertEqual(rel.name, "owner")
        self.assertEqual(rel.direction, sa.orm.relationships.MANYTOONE)
        self.assertEqual(rel.foreign_keys, [Vehicle._owner_id.property.columns[0]])
        self.assertEqual(
            rel.local_remote_pairs, [(Vehicle._owner_id.property.columns[0], Owner.id.property.columns[0])]
        )
        self.assertEqual(
            rel.local_remote_pairs_for_identity_key,
            [(Vehicle._owner_id.property.columns[0], Owner.id.property.columns[0])],
        )
        self.assertFalse(rel.uselist)
        self.assertEqual(repr(rel), "<relation_info(Vehicle.owner)>")

    def test_relationship_meta_backref(self):
        info = meta.model_info(Owner)

        rel = info.relationships["vehicles"]

        self.assertEqual(rel.related_model, Vehicle)
        self.assertEqual(rel.related_table, Vehicle.__table__)
        self.assertEqual(rel.parent_mapper, Owner.__mapper__)
        self.assertEqual(rel.related_mapper, Vehicle.__mapper__)
        self.assertEqual(rel.name, "vehicles")
        self.assertEqual(rel.direction, sa.orm.relationships.ONETOMANY)
        self.assertEqual(rel.foreign_keys, [Vehicle._owner_id.property.columns[0]])
        self.assertEqual(
            rel.local_remote_pairs, [(Owner.id.property.columns[0], Vehicle._owner_id.property.columns[0])]
        )
        self.assertEqual(
            rel.local_remote_pairs_for_identity_key,
            [(Owner.id.property.columns[0], Vehicle._owner_id.property.columns[0])],
        )
        self.assertTrue(rel.uselist)
        self.assertEqual(repr(rel), "<relation_info(Owner.vehicles)>")

    def test_terrible_relationship_meta(self):
        info = meta.model_info(Foo)

        rel = info.relationships["partial_parent"]

        self.assertEqual(rel.related_model, Foo)
        self.assertEqual(rel.related_table, Foo.__table__)
        self.assertEqual(rel.name, "partial_parent")
        self.assertEqual(rel.direction, sa.orm.relationships.MANYTOONE)
        self.assertEqual(rel.foreign_keys, [Foo.parent_id2.property.columns[0]])
        self.assertEqual(rel.local_remote_pairs, [(Foo.parent_id2.property.columns[0], Foo.id2.property.columns[0])])
        self.assertEqual(
            rel.local_remote_pairs_for_identity_key,
            [
                (Foo.id1.property.columns[0], Foo.id1.property.columns[0]),
                (Foo.parent_id2.property.columns[0], Foo.id2.property.columns[0]),
            ],
        )
        self.assertFalse(rel.uselist)
        self.assertEqual(repr(rel), "<relation_info(Foo.partial_parent)>")

    def test_formfield(self):
        info = meta.model_info(Vehicle)

        with self.assertRaises(ImproperlyConfigured):
            info.owner.formfield()

        formfield = info.owner.formfield(session=Owner.query.session)
        self.assertIsInstance(formfield, fields.ModelChoiceField)

        formfield = info.parts.formfield(session=Part.query.session)
        self.assertIsInstance(formfield, fields.ModelMultipleChoiceField)

    def test_get_form_class(self):
        info = meta.model_info(Vehicle)

        self.assertEqual(info.parts.get_form_class(), fields.ModelMultipleChoiceField)
        self.assertEqual(info.owner.get_form_class(), fields.ModelChoiceField)

    def test_field_kwargs(self):
        info = meta.model_info(Vehicle)

        self.assertDictEqual(info.parts.field_kwargs, {"required": False})
        self.assertDictEqual(info.owner.field_kwargs, {"required": False})
