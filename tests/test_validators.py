# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple

from django.core.exceptions import ValidationError

from django_sorcery.validators import (
    ValidateCantRemove,
    ValidateEmptyWhen,
    ValidateNotEmptyWhen,
    ValidateOnlyOneOf,
    ValidateTogetherModelFields,
    ValidateValue,
)

from .base import TestCase
from .testapp.models import ValidateUniqueModel, db


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


class TestValidateValue(TestCase):
    def setUp(self):
        super(TestValidateValue, self).setUp()
        self.validator = ValidateValue("right", lambda n: n.left != "left" or "right" in n.right)

    def test_valid(self):
        self.assertIsNone(self.validator(Node("left", "right")))
        self.assertIsNone(self.validator(Node("notleft", "notRight")))
        self.assertIsNone(self.validator(Node("notleft", "right")))

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            self.validator(Node("left", "left"))

    def test_error(self):
        with self.assertRaises(ValidationError):
            self.validator(Node("left", None))


class TestValidateEmptyWhen(TestCase):
    def setUp(self):
        super(TestValidateEmptyWhen, self).setUp()
        self.validator = ValidateEmptyWhen("right", lambda n: not n.left)

    def test_valid(self):
        self.assertIsNone(self.validator(Node(None, None)))
        self.assertIsNone(self.validator(Node("left", "right")))

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            self.validator(Node(None, "right"))


class TestValidateNotEmptyWhen(TestCase):
    def setUp(self):
        super(TestValidateNotEmptyWhen, self).setUp()
        self.validator = ValidateNotEmptyWhen("right", lambda n: n.left)

    def test_valid(self):
        self.assertIsNone(self.validator(Node(None, None)))
        self.assertIsNone(self.validator(Node("left", "right")))

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            self.validator(Node("left", None))


class TestValidateOnlyOneOf(TestCase):
    def test_valid_required(self):
        validator = ValidateOnlyOneOf(["left", "right"])

        self.assertIsNone(validator(Node(None, "right")))
        self.assertIsNone(validator(Node("left", None)))

    def test_invalid_required(self):
        validator = ValidateOnlyOneOf(["left", "right"])

        with self.assertRaises(ValidationError):
            validator(Node("left", "right"))
        with self.assertRaises(ValidationError):
            validator(Node(None, None))

    def test_valid_not_required(self):
        validator = ValidateOnlyOneOf(["left", "right"], required=False)

        self.assertIsNone(validator(Node(None, "right")))
        self.assertIsNone(validator(Node("left", None)))
        self.assertIsNone(validator(Node(None, None)))

    def test_invalid_not_required(self):
        validator = ValidateOnlyOneOf(["left", "right"], required=False)

        with self.assertRaises(ValidationError):
            validator(Node("left", "right"))


class TestValidateCantRemove(TestCase):
    def setUp(self):
        super(TestValidateCantRemove, self).setUp()
        self.validator = ValidateCantRemove("name")

    def test_no_changes(self):
        m = ValidateUniqueModel(name="Test")
        db.add(m)
        db.flush()

        self.assertIsNone(self.validator(m))

    def test_not_removed(self):
        m = ValidateUniqueModel(name="Test")
        db.add(m)
        db.flush()
        m.name = "Test2"

        self.assertIsNone(self.validator(m))

    def test_removed(self):
        m = ValidateUniqueModel(name="Test")
        db.add(m)
        db.flush()
        m.name = None

        with self.assertRaises(ValidationError):
            self.validator(m)
