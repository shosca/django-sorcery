# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.test import TestCase

from django_sorcery.exceptions import NestedValidationError


class TestNestedValidationError(TestCase):
    def test_string(self):
        error = NestedValidationError("error")
        self.assertEqual(error.messages, ["error"])

        error = NestedValidationError("error %s", params=("here",))
        self.assertEqual(error.messages, ["error here"])

    def test_list(self):
        error = NestedValidationError(["error"])
        self.assertEqual(error.messages, ["error"])

    def test_dict(self):
        error = NestedValidationError({"some": "error"})
        self.assertEqual(error.message_dict, {"some": ["error"]})

    def test_nested(self):
        error = NestedValidationError(NestedValidationError({"some": {"field": ["error"]}}))
        self.assertEqual(error.message_dict, {"some": {"field": ["error"]}})

    def test_update_error_dict(self):
        error = NestedValidationError("error")
        self.assertDictEqual(
            {"some": "other error", "__all__": [error]}, error.update_error_dict({"some": "other error"})
        )

        other = ValidationError("other error")
        error2 = NestedValidationError({"some": error})
        self.assertDictEqual({"some": [other, error]}, error2.update_error_dict({"some": [other]}))

    def test_dict_nested(self):
        error = NestedValidationError({"some": {"field": "error", "list": ["errors"], "object": {"field": "error"}}})
        self.assertEqual(
            error.message_dict, {"some": {"field": ["error"], "list": ["errors"], "object": {"field": ["error"]}}}
        )

    def test_list_nested(self):
        error = NestedValidationError(
            {
                "some": {
                    "field": "error",
                    "list": ["error1", "error2"],
                    "object": {"field": "error"},
                    "nested": [{"field": "error", "list": ["errors"]}],
                }
            }
        )
        self.assertEqual(
            error.message_dict,
            {
                "some": {
                    "field": ["error"],
                    "list": ["error1", "error2"],
                    "object": {"field": ["error"]},
                    "nested": [{"field": ["error"], "list": ["errors"]}],
                }
            },
        )

    def test_nested_error(self):
        error = NestedValidationError({"some": ValidationError("error")})
        self.assertEqual(error.message_dict, {"some": ["error"]})

        inner = NestedValidationError("error")
        error = NestedValidationError({"some": inner})
        self.assertEqual(error.message_dict, {"some": ["error"]})

    def test_repr(self):
        self.assertTrue(repr(NestedValidationError("error")).startswith("NestedValidationError"))
