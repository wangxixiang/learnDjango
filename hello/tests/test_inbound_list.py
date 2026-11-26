from django.test import TestCase
from django.urls import reverse

from hello.models import Customer, InboundOrder, InboundStatus, Warehouse


class InboundListTest(TestCase):
    def setUp(self):
        self.customer_a = Customer.objects.create(name="Customer A")
        self.customer_b = Customer.objects.create(name="Customer B")
        self.warehouse_a = Warehouse.objects.create(name="Warehouse A")
        self.warehouse_b = Warehouse.objects.create(name="Warehouse B")

        self.orders_a = []
        for index in range(6):
            self.orders_a.append(
                InboundOrder.objects.create(
                    code=f"INB-A-{index:03}",
                    customer=self.customer_a,
                    warehouse=self.warehouse_a,
                    status=InboundStatus.DRAFT,
                )
            )
        for index in range(6):
            InboundOrder.objects.create(
                code=f"INB-B-{index:03}",
                customer=self.customer_b,
                warehouse=self.warehouse_b,
                status=InboundStatus.RECEIVED,
            )

    def get_list(self, params=None):
        return self.client.get(reverse("inbound_list"), params or {})

    def test_first_page_has_at_most_five_records(self):
        response = self.get_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inbound_orders"]), 5)
        self.assertEqual(response.context["paginator"].count, 12)

    def test_second_page_shows_next_distinct_batch(self):
        first = self.get_list()
        second = self.get_list({"page": "2"})
        first_ids = {order.id for order in first.context["inbound_orders"]}
        second_ids = {order.id for order in second.context["inbound_orders"]}

        self.assertEqual(len(second_ids), 5)
        self.assertFalse(first_ids & second_ids)

    def test_inbound_number_uses_contains_match(self):
        response = self.get_list({"inbound_number": "A-002"})
        self.assertEqual(response.context["paginator"].count, 1)
        self.assertEqual(response.context["inbound_orders"][0].code, "INB-A-002")

    def test_customer_filter(self):
        response = self.get_list({"customer_id": self.customer_a.id})
        self.assertEqual(response.context["paginator"].count, 6)
        self.assertTrue(all(o.customer_id == self.customer_a.id for o in response.context["inbound_orders"]))

    def test_warehouse_filter(self):
        response = self.get_list({"warehouse_id": self.warehouse_b.id})
        self.assertEqual(response.context["paginator"].count, 6)
        self.assertTrue(all(o.warehouse_id == self.warehouse_b.id for o in response.context["inbound_orders"]))

    def test_status_filter(self):
        response = self.get_list({"status": InboundStatus.RECEIVED})
        self.assertEqual(response.context["paginator"].count, 6)
        self.assertTrue(all(o.status == InboundStatus.RECEIVED for o in response.context["inbound_orders"]))

    def test_filters_combine_with_and_logic(self):
        response = self.get_list({
            "inbound_number": "INB-A",
            "customer_id": self.customer_a.id,
            "warehouse_id": self.warehouse_a.id,
            "status": InboundStatus.DRAFT,
        })
        self.assertEqual(response.context["paginator"].count, 6)
        self.assertTrue(all(o.code.startswith("INB-A") for o in response.context["inbound_orders"]))

    def test_pagination_links_preserve_all_filters(self):
        response = self.get_list({
            "inbound_number": "INB-A",
            "customer_id": self.customer_a.id,
            "warehouse_id": self.warehouse_a.id,
            "status": InboundStatus.DRAFT,
        })
        expected = (
            f"?inbound_number=INB-A&amp;customer_id={self.customer_a.id}"
            f"&amp;warehouse_id={self.warehouse_a.id}&amp;status=1&amp;page=2"
        )
        self.assertContains(response, expected)

    def test_invalid_and_out_of_range_pages_are_handled(self):
        invalid = self.get_list({"page": "abc"})
        out_of_range = self.get_list({"page": "9999"})
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context["page_obj"].number, 1)
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(out_of_range.context["page_obj"].number, 3)

    def test_empty_results_show_friendly_message(self):
        response = self.get_list({"inbound_number": "DOES-NOT-EXIST"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginator"].count, 0)
        self.assertContains(response, "没有找到符合条件的入库单")

