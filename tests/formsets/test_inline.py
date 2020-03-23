from django_sorcery.db import meta
from django_sorcery.forms import ALL_FIELDS
from django_sorcery.formsets import inlineformset_factory

from ..base import TestCase
from ..testapp.models import Owner, Vehicle, VehicleType, db


class TestInlineFormSet(TestCase):
    def setUp(self):
        super().setUp()
        self.owner = Owner(first_name="Test 1", last_name="Owner 1")
        db.add(self.owner)
        db.flush()

    def test_factory(self):
        info = meta.model_info(Owner)
        formset_class = inlineformset_factory(Owner, Vehicle, fields=ALL_FIELDS, session=db)

        self.assertEqual(formset_class.fk, info.relationships["vehicles"])

    def test_factory_with_relation(self):
        info = meta.model_info(Owner)
        formset_class = inlineformset_factory(relation=Owner.vehicles, fields=ALL_FIELDS, session=db)

        self.assertEqual(formset_class.fk, info.relationships["vehicles"])

    def test_factory_with_bad_relation(self):

        with self.assertRaises(ValueError):
            inlineformset_factory(relation=Vehicle.owner, fields=ALL_FIELDS, session=db)

    def test_factory_for_non_existant_relation(self):

        with self.assertRaises(ValueError):
            inlineformset_factory(Vehicle, Owner, fields=ALL_FIELDS, session=db)

    def test_initial_form_count(self):
        formset_class = inlineformset_factory(relation=Owner.vehicles, fields=("type",), session=db)
        formset = formset_class(save_as_new=True)
        self.assertEqual(formset.initial_form_count(), 0)

    def test_inline_form_create_render(self):
        formset_class = inlineformset_factory(relation=Owner.vehicles, fields=("type",), session=db)
        formset = formset_class()

        soup = self.get_soup(formset.as_p())
        expected_soup = self.get_soup(
            "".join(
                [
                    '<input type="hidden" name="vehicles-TOTAL_FORMS" value="3" id="id_vehicles-TOTAL_FORMS" />',
                    '<input type="hidden" name="vehicles-INITIAL_FORMS" value="0" id="id_vehicles-INITIAL_FORMS" />',
                    '<input type="hidden" name="vehicles-MIN_NUM_FORMS" value="0" id="id_vehicles-MIN_NUM_FORMS" />',
                    '<input type="hidden" name="vehicles-MAX_NUM_FORMS" value="1000" id="id_vehicles-MAX_NUM_FORMS" />',
                    "<p>",
                    '  <label for="id_vehicles-0-type">Type:</label>',
                    '  <select id="id_vehicles-0-type" name="vehicles-0-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-0-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-0-DELETE" name="vehicles-0-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-1-type">Type:</label>',
                    '  <select id="id_vehicles-1-type" name="vehicles-1-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-1-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-1-DELETE" name="vehicles-1-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-2-type">Type:</label>',
                    '  <select id="id_vehicles-2-type" name="vehicles-2-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-2-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-2-DELETE" name="vehicles-2-DELETE" type="checkbox" />',
                    "</p>",
                ]
            )
        )
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())

    def test_inline_form_create(self):
        formset_class = inlineformset_factory(relation=Owner.vehicles, fields=("type",), session=db)
        data = {
            "vehicles-TOTAL_FORMS": "3",
            "vehicles-INITIAL_FORMS": "3",
            "vehicles-MIN_NUM_FORMS": "0",
            "vehicles-MAX_NUM_FORMS": "1000",
            "vehicles-0-type": "car",
            "vehicles-1-type": "bus",
            "vehicles-2-type": "car",
        }
        formset = formset_class(instance=self.owner, data=data)
        values = formset.save()

        self.assertEqual(values[0].owner, self.owner)
        self.assertEqual(values[0].type, VehicleType.car)

        self.assertEqual(values[1].owner, self.owner)
        self.assertEqual(values[1].type, VehicleType.bus)

        self.assertEqual(values[2].owner, self.owner)
        self.assertEqual(values[2].type, VehicleType.car)

    def test_inline_form_update_render(self):
        self.owner.vehicles = [Vehicle(type=VehicleType.car), Vehicle(type=VehicleType.bus)]
        db.flush()

        formset_class = inlineformset_factory(relation=Owner.vehicles, fields=("type",), session=db)
        formset = formset_class(instance=self.owner)

        soup = self.get_soup(formset.as_p())
        expected_soup = self.get_soup(
            "".join(
                [
                    '<input type="hidden" name="vehicles-TOTAL_FORMS" value="5" id="id_vehicles-TOTAL_FORMS" />',
                    '<input type="hidden" name="vehicles-INITIAL_FORMS" value="2" id="id_vehicles-INITIAL_FORMS" />',
                    '<input type="hidden" name="vehicles-MIN_NUM_FORMS" value="0" id="id_vehicles-MIN_NUM_FORMS" />',
                    '<input type="hidden" name="vehicles-MAX_NUM_FORMS" value="1000" id="id_vehicles-MAX_NUM_FORMS" />',
                    "<p>",
                    '  <label for="id_vehicles-0-type">Type:</label>',
                    '  <select id="id_vehicles-0-type" name="vehicles-0-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car" selected>Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-0-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-0-DELETE" name="vehicles-0-DELETE" type="checkbox" />',
                    '  <input id="id_vehicles-0-id" name="vehicles-0-id" type="hidden" value="{}" />'.format(
                        self.owner.vehicles[0].id
                    ),
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-1-type">Type:</label>',
                    '  <select id="id_vehicles-1-type" name="vehicles-1-type">',
                    '    <option value="bus" selected>Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-1-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-1-DELETE" name="vehicles-1-DELETE" type="checkbox" />',
                    '  <input id="id_vehicles-1-id" name="vehicles-1-id" type="hidden" value="{}" />'.format(
                        self.owner.vehicles[1].id
                    ),
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-2-type">Type:</label>',
                    '  <select id="id_vehicles-2-type" name="vehicles-2-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-2-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-2-DELETE" name="vehicles-2-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-3-type">Type:</label>',
                    '  <select id="id_vehicles-3-type" name="vehicles-3-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-3-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-3-DELETE" name="vehicles-3-DELETE" type="checkbox" />',
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-4-type">Type:</label>',
                    '  <select id="id_vehicles-4-type" name="vehicles-4-type">',
                    '    <option value="bus">Bus</option>',
                    '    <option value="car">Car</option>',
                    "  </select>",
                    "</p>",
                    "<p>",
                    '  <label for="id_vehicles-4-DELETE">Delete:</label>',
                    '  <input id="id_vehicles-4-DELETE" name="vehicles-4-DELETE" type="checkbox" />',
                    "</p>",
                ]
            )
        )
        self.assertHTMLEqual(soup.prettify(), expected_soup.prettify())
