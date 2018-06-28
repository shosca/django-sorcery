# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple

from django.core.exceptions import ValidationError

from django_sorcery.validators import ValidateTogetherModelFields

from .base import TestCase
from .models import ValidateUniqueModel, db


Node = namedtuple("Node", ["left", "right", "value"])
Node.__new__.__defaults__ = (None, None, None)


class TestValidateTogetherModelFields(TestCase):
    def test_success_all_none(self):
        node = Node()

        validator = ValidateTogetherModelFields(["left", "right", "value"])

        self.assertIsNone(validator(node))

    def test_success_all_full(self):
        node = Node("left", "right", "value")

        validator = ValidateTogetherModelFields(["left", "right", "value"])

        self.assertIsNone(validator(node))

    def test_success_fail(self):
        node = Node("left", "right")

        validator = ValidateTogetherModelFields(["left", "right", "value"])

        with self.assertRaises(ValidationError):
            self.assertIsNone(validator(node))


class TestValidateUnique(TestCase):
    def test_validate_on_insert(self):
        model = ValidateUniqueModel(name="Test")
        db.add(model)
        db.flush()

        model = ValidateUniqueModel(name="Test")
        db.add(model)
        with self.assertRaises(ValidationError) as ctx:
            db.flush()

        self.assertEqual(
            ctx.exception.message_dict,
            {"__all__": ["name must make a unique set.", "bar, foo must make a unique set."]},
        )

    def test_validate_on_update(self):
        model = ValidateUniqueModel(name="Name", foo="Test", bar="Test")
        db.add(model)
        db.flush()

        model.foo = "foo"
        db.flush()
