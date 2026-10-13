from django.test import TestCase
from django.urls import reverse
from hello.models import (
    Customer,
    Product,
    CustomerProduct,
    Warehouse,
    InboundOrder,
)


class InboundItemTest(TestCase):
    def setUp(self):
        # 1. 创建测试客户
        self.customer = Customer.objects.create(name="测试客户")

        # 2. 创建标准商品
        self.product = Product.objects.create(
            barcode="TEST-BARCODE-001",
            name="测试商品",
            weight=1000,
        )

        # 3. 创建客户商品
        self.customer_product = CustomerProduct.objects.create(
            customer=self.customer,
            product=self.product,
            customer_sku="TEST-SKU-001",
            name="测试客户商品",
        )

        # 4. 创建仓库
        self.warehouse = Warehouse.objects.create(name="测试仓库")

        # 5. 创建入库单
        self.order = InboundOrder.objects.create(
            code="TEST-IN-001",
            customer=self.customer,
            warehouse=self.warehouse,
        )

    def test_customer_created(self):
        # 验证测试数据是否创建成功
        self.assertEqual(self.customer.name, "测试客户")
        self.assertEqual(self.product.name, "测试商品")
        self.assertEqual(self.customer_product.customer_sku, "TEST-SKU-001")
        self.assertEqual(self.warehouse.name, "测试仓库")
        self.assertEqual(self.order.code, "TEST-IN-001")

    def test_zero_quantity_rejected(self):
        url = reverse(
            "inbound_item_create",
            args=[self.order.id],
        )

        before_count = self.order.items.count()

        response = self.client.post(
            url,
            {
                "customer_product": self.customer_product.id,
                "quantity": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count)
