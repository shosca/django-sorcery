# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import namedtuple

from django.core.exceptions import ValidationError
from django.test import TestCase

from django_sorcery.validators import ValidateTogetherModelFields


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
