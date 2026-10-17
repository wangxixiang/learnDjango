from django.test import TestCase
from django.urls import reverse
from hello.models import (
    Customer,
    InboundItem,
    InboundOrderStatus,
    Inventory,
    InventoryStatus,
    InventoryTransaction,
    Location,
    Product,
    CustomerProduct,
    Warehouse,
    InboundOrder,
)


class InboundReceiveTest(TestCase):
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

        # 6. 创建入库单明细
        self.item = InboundItem.objects.create(
            inbound_order=self.order,
            customer_product=self.customer_product,
            quantity=1,
        )

        # 7. 创建库位
        self.location = Location.objects.create(
            warehouse=self.warehouse,
            code="RECEIVING-01",
        )

    def test_regular_receive(self):

        beforeInventoryTransactionCount = InventoryTransaction.objects.all().count()
        # 1. 发送收货请求
        response = self.client.post(reverse("inbound_receive", args=[self.order.id]))
        afterInventoryCount = Inventory.objects.get(
            location=self.location,
            customer_product=self.order.items.first().customer_product,
            status=InventoryStatus.AVAILABLE,
        ).quantity

        afterInventoryTransactionCount = InventoryTransaction.objects.all().count()
        # 从数据库重新读取数据，更新当前 self.order 对象的字段值
        self.order.refresh_from_db()

        # 2. 检查响应状态码是否为302（重定向）
        self.assertEqual(response.status_code, 302)
        # 3. 检查入库单状态是否已更新为已收货
        self.assertEqual(
            self.order.items.first().quantity,
            afterInventoryCount,
        )
        self.assertEqual(1, afterInventoryTransactionCount)
        self.assertEqual(self.order.status, InboundOrderStatus.RECEIVED)

    def test_receive_with_duplicate(self):
        # 1. 发送第一次收货请求
        response1 = self.client.post(reverse("inbound_receive", args=[self.order.id]))
        # 2. 发送第二次收货请求
        response2 = self.client.post(reverse("inbound_receive", args=[self.order.id]))

        # 从数据库重新读取数据，更新当前 self.order 对象的字段值
        self.order.refresh_from_db()
        afterInventoryTransactionCount = InventoryTransaction.objects.all().count()
        self.assertEqual(1, afterInventoryTransactionCount)
        afterInventoryCount = Inventory.objects.get(
            location=self.location,
            customer_product=self.order.items.first().customer_product,
            status=InventoryStatus.AVAILABLE,
        ).quantity
        self.assertEqual(1, afterInventoryCount)

        # 3. 检查第一次响应状态码是否为302（重定向）
        self.assertEqual(response1.status_code, 302)
        # 4. 检查第二次响应状态码是否为400（错误请求）,代码里捕获异常了。
        self.assertEqual(response2.status_code, 302)
        # 5. 检查入库单状态是否仍为已收货
        self.assertEqual(self.order.status, InboundOrderStatus.RECEIVED)
