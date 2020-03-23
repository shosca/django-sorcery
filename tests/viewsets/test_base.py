from ..base import TestCase
from ..testapp.views import OwnerViewSet


class TestViewSet(TestCase):
    def test_as_view_without_action_map(self):

        with self.assertRaises(TypeError):
            OwnerViewSet.as_view()

    def test_as_view_with_verb_initkwargs(self):

        with self.assertRaises(TypeError):
            OwnerViewSet.as_view(actions={"get": "list"}, get="test")

    def test_as_view_with_bad_initkwargs(self):

        with self.assertRaises(TypeError):
            OwnerViewSet.as_view(actions={"get": "list"}, foo="test")

    def test_as_view(self):

        view = OwnerViewSet.as_view(actions={"get": "list"})

        self.assertEqual(view.cls, OwnerViewSet)
        self.assertEqual(view.actions, {"get": "list"})
        self.assertEqual(view.initkwargs, {})
        self.assertIsNone(view.suffix)

        request = self.factory.get("/")
        response = view(request)
        self.assertEqual(response.status_code, 200)
