from django.test import TestCase
from django.urls import reverse
from hello.models import (
    Customer,
    InboundItem,
    InboundOrderStatus,
    Location,
    Product,
    CustomerProduct,
    Warehouse,
    InboundOrder,
)
from django.db import IntegrityError, transaction


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
