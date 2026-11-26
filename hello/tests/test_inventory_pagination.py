from django.test import TestCase
from django.urls import reverse

from hello.models import (
    Customer,
    CustomerProduct,
    Inventory,
    InventoryStatus,
    Location,
    Product,
    Warehouse,
)


class InventoryPaginationTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Pagination customer")
        self.warehouse = Warehouse.objects.create(name="Pagination warehouse")
        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code="RECEIVING-01",
        )
        for index in range(21):
            product = Product.objects.create(
                barcode=f"PAGE-{index}", name=f"Page product {index}", weight=1
            )
            customer_product = CustomerProduct.objects.create(
                customer=self.customer,
                product=product,
                customer_sku=f"PAGE-SKU-{index}",
                name=f"Page product {index}",
            )
            Inventory.objects.create(
                location=self.location,
                customer_product=customer_product,
                quantity=1,
                status=InventoryStatus.AVAILABLE,
            )

    def test_default_page_contains_twenty_records_and_navigation(self):
        response = self.client.get(reverse("inventory_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inventories"]), 20)
        self.assertEqual(response.context["paginator"].count, 21)
        self.assertContains(response, "第 1 页 / 共 2 页")
        self.assertContains(response, "总记录数：21")
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, 'aria-disabled="true">上一页</span>')
        self.assertContains(response, "page=2")

    def test_filters_are_preserved_in_pagination_links(self):
        filters = {
            "customer_sku": "",
            "product_name": "Page product",
            "customer_id": str(self.customer.id),
            "warehouse_id": str(self.warehouse.id),
            "location_code": "RECEIVING-01",
            "status": str(InventoryStatus.AVAILABLE),
        }
        response = self.client.get(reverse("inventory_list"), filters)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inventories"]), 20)
        next_link = (
            "?customer_sku=&amp;product_name=Page+product"
            f"&amp;customer_id={self.customer.id}&amp;warehouse_id={self.warehouse.id}"
            "&amp;location_code=RECEIVING-01&amp;status=1&amp;page=2"
        )
        self.assertContains(response, next_link)

    def test_out_of_range_and_invalid_pages_are_handled(self):
        out_of_range = self.client.get(reverse("inventory_list"), {"page": "99"})
        invalid = self.client.get(reverse("inventory_list"), {"page": "invalid"})

        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(out_of_range.context["page_obj"].number, 2)
        self.assertEqual(len(out_of_range.context["inventories"]), 1)
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context["page_obj"].number, 1)

