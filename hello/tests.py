from django.test import TestCase
from django.urls import reverse
from hello.models import (
    Customer,
    InboundItem,
    InboundOrderStatus,
    Product,
    CustomerProduct,
    Warehouse,
    InboundOrder,
)
from django.db import IntegrityError, transaction


class InboundItemTest(TestCase):
    # 每个测试方法执行前都会调用setup方法
    def setUp(self):
        # 1. 创建测试客户
        self.customer = Customer.objects.create(name="测试客户")
        self.customerB = Customer.objects.create(name="测试客户B")

        # 2. 创建标准商品
        self.product = Product.objects.create(
            barcode="TEST-BARCODE-001",
            name="测试商品",
            weight=1000,
        )
        self.productB = Product.objects.create(
            barcode="TEST-BARCODE-002",
            name="测试商品B",
            weight=2000,
        )

        # 3. 创建客户商品
        self.customer_product = CustomerProduct.objects.create(
            customer=self.customer,
            product=self.product,
            customer_sku="TEST-SKU-001",
            name="测试客户商品",
        )
        self.customer_productB = CustomerProduct.objects.create(
            customer=self.customerB,
            product=self.productB,
            customer_sku="TEST-SKU-002",
            name="测试客户商品B",
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

    def test_other_customer_product_rejected(self):
        url = reverse(
            "inbound_item_create",
            args=[self.order.id],
        )
        before_count = self.order.items.count()
        response = self.client.post(
            url,
            {
                "customer_product": self.customer_productB.id,
                "quantity": 1,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count)

    # 抽取出方法，注意前缀
    def assert_invalid_quantity(self, quantity):
        url = reverse(
            "inbound_item_create",
            args=[self.order.id],
        )

        before_count = self.order.items.count()

        response = self.client.post(
            url,
            {
                "customer_product": self.customer_product.id,
                "quantity": quantity,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count)

    def test_negative_quantity_rejected(self):
        self.assert_invalid_quantity("-5")

    def test_non_integer_quantity_rejected(self):
        self.assert_invalid_quantity("abc")

    def test_empty_quantity_rejected(self):
        self.assert_invalid_quantity("")

    def test_zero_quantity_rejected(self):
        self.assert_invalid_quantity("0")

    def test_decimal_quantity_rejected(self):
        self.assert_invalid_quantity("2.5")

    def test_valid_quantity_accepted(self):
        url = reverse("inbound_item_create", args=[self.order.id])
        before_count = self.order.items.count()

        response = self.client.post(
            url,
            {
                "customer_product": self.customer_product.id,
                "quantity": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count + 1)

        item = self.order.items.get(customer_product=self.customer_product)
        self.assertEqual(item.quantity, 1)

    # 测试已经收货的订单不能再添加新的入库明细
    def test_received_order_rejects_new_item(self):

        self.order.status = InboundOrderStatus.RECEIVED
        self.order.save()
        # # 6. 创建入库单明细
        # self.item = InboundItem.objects.create(
        #     inbound_order=self.order,
        #     customer_product=self.customer_product,
        #     quantity=1,
        # )
        url = reverse("inbound_item_create", args=[self.order.id])
        before_count = self.order.items.count()
        print("before_count:", before_count)
        response = self.client.post(
            url,
            {
                "customer_product": self.customer_product.id,
                "quantity": "1",
            },
        )

        print("after_count:", self.order.items.count())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count)

    # 检查重复提交，普通post请求提交相同的商品和数量，应该被拒绝
    def test_duplicate_item_rejected(self):
        # 6. 创建入库单明细
        InboundItem.objects.create(
            inbound_order=self.order,
            customer_product=self.customer_product,
            quantity=1,
        )
        before_count = self.order.items.count()
        url = reverse("inbound_item_create", args=[self.order.id])
        response = self.client.post(
            url,
            {
                "customer_product": self.customer_product.id,
                "quantity": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.items.count(), before_count)

    def test_database_rejects_duplicate_item(self):
        # 6. 创建入库单明细
        InboundItem.objects.create(
            inbound_order=self.order,
            customer_product=self.customer_product,
            quantity=1,
        )
        before_count = self.order.items.count()
        # 尝试直接在数据库中创建重复的入库单明细，应该会抛出IntegrityError异常
        with self.assertRaises(IntegrityError):
            # 使用 transaction.atomic() 开启一个数据库事务，保证这个事务块中的数据库操作能够作为一个整体提交或回滚。隔离这次失败的数据库操作。
            with transaction.atomic():
                InboundItem.objects.create(
                    inbound_order=self.order,
                    customer_product=self.customer_product,
                    quantity=1,
                )

        self.assertEqual(self.order.items.count(), before_count)
