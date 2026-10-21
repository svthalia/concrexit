from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from activemembers.models import Committee
from events.models.event import Event
from events.models.event_registration import EventRegistration
from members.models import Member
from moneybirdsynchronization import services
from moneybirdsynchronization.models import (
    MoneybirdCostCentre,
    MoneybirdExternalInvoice,
    MoneybirdProject,
    cost_centre_id_for_payable_model,
    reference_for_payable,
)
from pizzas.models import FoodEvent, FoodOrder
from payments.payables import payables
from pizzas.models import Product as FoodProduct
from sales.models.order import Order, OrderItem
from sales.models.product import ProductList
from sales.models.shift import Shift


@override_settings(
    MONEYBIRD_DEFAULT_COST_CENTRE_ID="216", MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID="1"
)
class CostCentreTest(TestCase):
    fixtures = ["members.json", "products.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)
        cls.borrel_cost_centre = MoneybirdProject.objects.create(
            name="C101 - Borrel Drink costs", moneybird_id="101"
        )
        cls.weekend_cost_centre = MoneybirdProject.objects.create(
            name="C207 - Thalia Weekend", moneybird_id="207"
        )
        cls.borrel_committee = Committee.objects.create(name="Borrel committee")
        cls.weekend_committee = Committee.objects.create(name="Weekend committee")
        cls.other_committee = Committee.objects.create(name="Another committee")
        MoneybirdCostCentre.objects.create(
            group=cls.borrel_committee, project=cls.borrel_cost_centre
        )
        MoneybirdCostCentre.objects.create(
            group=cls.weekend_committee, project=cls.weekend_cost_centre
        )

        cls.event = Event.objects.create(
            title="Thalia Weekend",
            description="desc",
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            location="test location",
            map_location="test map location",
            price=10.00,
            fine=0.00,
        )
        cls.event.organisers.add(cls.weekend_committee)

    def _create_shift(self, event=None):
        shift = Shift.objects.create(
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            product_list=ProductList.objects.get(name="normal"),
            event=event,
        )
        shift.managers.add(self.borrel_committee)
        return shift

    def test_event_registration_uses_main_organiser(self):
        registration = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        self.assertEqual(cost_centre_id_for_payable_model(registration), "207")

        # With several organisers, the first one by name is the main organiser.
        self.event.organisers.add(self.borrel_committee)
        self.assertEqual(cost_centre_id_for_payable_model(registration), "101")

    def test_sales_order_in_shift_with_event_uses_event_organiser(self):
        order = Order.objects.create(shift=self._create_shift(event=self.event))
        self.assertEqual(cost_centre_id_for_payable_model(order), "207")

    def test_sales_order_in_shift_without_event_has_no_project(self):
        shift = self._create_shift()
        order = Order.objects.create(shift=shift)
        OrderItem.objects.create(
            order=order,
            product=shift.product_list.product_items.get(product__name="beer"),
            amount=1,
        )
        self.assertIsNone(cost_centre_id_for_payable_model(order))

        external_invoice = MoneybirdExternalInvoice.create_for_object(order)
        with mock.patch(
            "moneybirdsynchronization.models.get_moneybird_api_service"
        ) as mock_api:
            data = external_invoice.to_moneybird()
        mock_api.return_value.create_project.assert_not_called()
        details = data["external_sales_invoice"]["details_attributes"]
        self.assertEqual(len(details), 1)
        self.assertNotIn("project_id", details[0])

    def test_group_without_cost_centre_uses_default(self):
        self.event.organisers.set([self.other_committee])
        registration = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        self.assertEqual(cost_centre_id_for_payable_model(registration), "216")

    def test_inactive_cost_centre_uses_default(self):
        self.weekend_cost_centre.active = False
        self.weekend_cost_centre.save()
        registration = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        self.assertEqual(cost_centre_id_for_payable_model(registration), "216")

    def test_food_orders_are_not_booked_on_a_cost_centre(self):
        food_event = FoodEvent.objects.create(
            event=self.event,
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
        )
        product = FoodProduct.objects.create(name="foo", description="bar", price=1)
        order = FoodOrder.objects.create(
            member=self.member, food_event=food_event, product=product
        )
        self.assertIsNone(cost_centre_id_for_payable_model(order))

    def test_references_end_with_event_label(self):
        label = f" [E{self.event.pk}]"
        registration = EventRegistration.objects.create(
            event=self.event, member=self.member
        )
        food_event = FoodEvent.objects.create(
            event=self.event,
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
        )
        food_order = FoodOrder.objects.create(
            member=self.member,
            food_event=food_event,
            product=FoodProduct.objects.create(name="foo", description="bar", price=1),
        )
        order = Order.objects.create(shift=self._create_shift(event=self.event))
        for obj in (registration, food_order, order):
            with self.subTest(obj=obj):
                reference = reference_for_payable(payables.get_payable(obj))
                self.assertTrue(reference.endswith(f"[{obj.pk}]{label}"), reference)

        no_event_order = Order.objects.create(shift=self._create_shift())
        reference = reference_for_payable(payables.get_payable(no_event_order))
        self.assertTrue(reference.endswith(f"[{no_event_order.pk}]"), reference)


@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
)
class ImportProjectsTest(TestCase):
    def test_import_projects(self, mock_api):
        """Projects are created or updated by Moneybird ID, or else by name."""
        existing_by_id = MoneybirdProject.objects.create(
            name="Old name", moneybird_id="1"
        )
        existing_by_name = MoneybirdProject.objects.create(
            name="C202 - Turing Committee"
        )

        first_page = [{"id": "1", "name": "C101 - Borrel Drink costs"}] + [
            {"id": str(1000 + i), "name": f"Project {i}"} for i in range(99)
        ]
        second_page = [{"id": "2", "name": "C202 - Turing Committee"}]
        mock_api.return_value.get_projects.side_effect = [first_page, second_page]

        services.import_projects()

        self.assertEqual(mock_api.return_value.get_projects.call_count, 2)
        existing_by_id.refresh_from_db()
        self.assertEqual(existing_by_id.name, "C101 - Borrel Drink costs")
        existing_by_name.refresh_from_db()
        self.assertEqual(existing_by_name.moneybird_id, "2")
        self.assertEqual(MoneybirdProject.objects.count(), 101)

    def test_import_marks_deactivated_projects_inactive(self, mock_api):
        deactivated = MoneybirdProject.objects.create(
            name="C105 - Constitutieborrel", moneybird_id="105"
        )
        reactivated = MoneybirdProject.objects.create(
            name="C101 - Borrel Drink costs", moneybird_id="101", active=False
        )
        not_pushed = MoneybirdProject.objects.create(name="Food event [2026-10-21]")
        mock_api.return_value.get_projects.return_value = [
            {"id": "101", "name": "C101 - Borrel Drink costs"}
        ]

        services.import_projects()

        deactivated.refresh_from_db()
        self.assertFalse(deactivated.active)
        reactivated.refresh_from_db()
        self.assertTrue(reactivated.active)
        not_pushed.refresh_from_db()
        self.assertTrue(not_pushed.active)
