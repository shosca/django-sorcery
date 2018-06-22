# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError
from django.test import TestCase

from django_sorcery.exceptions import NestedValidationError


class TestNestedValidationError(TestCase):
    def test_string_message(self):
        error = NestedValidationError("error")

        self.assertEqual(error.message, "error")
        self.assertIsNone(error.params)

        self.assertIsInstance(error.error_list, list)
        self.assertEqual(len(error.error_list), 1)
        self.assertEqual(error.error_list, [error])

        error_dict = error.update_error_dict({"some": "other error"})

        self.assertDictEqual({"some": "other error", "__all__": [error]}, error_dict)

    def test_dict_message(self):
        error = NestedValidationError({"some": "error"})

        self.assertIsInstance(error.error_dict, dict)
        self.assertIn("some", error.error_dict)

        errors = error.error_dict["some"]

        self.assertIsInstance(errors, list)

        other = [ValidationError("other error")]
        error_dict = error.update_error_dict({"some": other})

        self.assertDictEqual({"some": [other[0], errors[0]]}, error_dict)

        error = errors[0]

        self.assertEqual(error.message, "error")
        self.assertIsNone(error.params)

        self.assertIsInstance(error.error_list, list)
        self.assertEqual(len(error.error_list), 1)
        self.assertEqual(error.error_list, [error])

    def test_dict_nested(self):
        error = NestedValidationError({"some": {"field": "error", "list": ["errors"], "object": {"field": "error"}}})
        self.assertEqual(
            error.message_dict, {"some": {"field": ["error"], "list": ["errors"], "object": {"field": ["error"]}}}
        )

    def test_nested_error(self):
        error = NestedValidationError({"some": ValidationError("error")})

        self.assertIsInstance(error.error_dict, dict)
        self.assertIn("some", error.error_dict)

        errors = error.error_dict["some"]

        self.assertIsInstance(errors, list)

        error = errors[0]

        self.assertEqual(error.message, "error")
        self.assertIsNone(error.params)

        self.assertIsInstance(error.error_list, list)
        self.assertEqual(len(error.error_list), 1)
        self.assertEqual(error.error_list, [error])

    def test_nested_error_error(self):
        inner = NestedValidationError("error")
        error = NestedValidationError({"some": inner})

        self.assertIsInstance(error.error_dict, dict)
        self.assertIn("some", error.error_dict)

        errors = error.error_dict["some"]

        self.assertIsInstance(errors, list)

        error = errors[0]

        self.assertEqual(error.message, "error")
        self.assertIsNone(error.params)

        self.assertIsInstance(error.error_list, list)
        self.assertEqual(len(error.error_list), 1)
        self.assertEqual(error.error_list, [error])
