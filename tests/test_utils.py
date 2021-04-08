from django.test import TestCase
from django_sorcery import utils


class TestUtils(TestCase):
    def test_setdefaultattr(self):
        class Dummy:
            pass

        obj = Dummy()

        default = set()

        utils.setdefaultattr(obj, "test", default)

        self.assertTrue(hasattr(obj, "test"))
        self.assertEqual(obj.test, default)

        utils.setdefaultattr(obj, "test", set())

        self.assertTrue(hasattr(obj, "test"))
        self.assertEqual(obj.test, default)

    def test_make_args(self):

        value = utils.make_args("abc", kw="something")

        self.assertEqual(value, ("abc", {"kw": "something"}))

    def test_lower(self):
        self.assertEqual(utils.lower("HELLO"), "hello")
        self.assertEqual(utils.lower(5), 5)
