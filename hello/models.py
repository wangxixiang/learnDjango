from django.db import models


# =========================
# 1. Customer 客户
# =========================

class Customer(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# =========================
# 2. Product 标准商品
# =========================

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    barcode = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)
    weight = models.BigIntegerField(help_text="单位：g")

    def __str__(self):
        return self.name


# =========================
# 3. CustomerProduct 客户商品
# =========================

class CustomerProduct(models.Model):
    id = models.BigAutoField(primary_key=True)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="products"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="customer_products"
    )

    customer_sku = models.CharField(max_length=100)
    name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "customer_sku"],
                name="unique_customer_sku"
            )
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.customer_sku}"


# =========================
# 4. Warehouse 仓库
# =========================

class Warehouse(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# =========================
# 5. Location 库位
# =========================

class Location(models.Model):
    id = models.BigAutoField(primary_key=True)

    code = models.CharField(max_length=100)

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="locations"
    )

    priority = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"],
                name="unique_warehouse_location"
            )
        ]

    def __str__(self):
        return f"{self.warehouse.name} - {self.code}"


# =========================
# 6. Inventory 库存
# =========================

class InventoryStatus(models.IntegerChoices):
    AVAILABLE = 1, "可用"
    HOLD = 2, "冻结"
    DAMAGED = 3, "损坏"


class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="inventories"
    )

    customer_product = models.ForeignKey(
        CustomerProduct,
        on_delete=models.PROTECT,
        related_name="inventories"
    )

    quantity = models.PositiveIntegerField(default=0)

    status = models.SmallIntegerField(
        choices=InventoryStatus.choices,
        default=InventoryStatus.AVAILABLE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "location",
                    "customer_product",
                    "status"
                ],
                name="unique_inventory"
            )
        ]

    def __str__(self):
        return f"{self.customer_product.customer_sku} - {self.location.code}"


# =========================
# 7. InboundOrder 入库单
# =========================

class InboundStatus(models.IntegerChoices):
    DRAFT = 1, "草稿"
    EXPECTED = 2, "预计到货"
    RECEIVING = 3, "收货中"
    RECEIVED = 4, "已收货"
    CLOSED = 5, "已关闭"
    CANCELLED = 6, "已取消"


class InboundOrder(models.Model):
    id = models.BigAutoField(primary_key=True)

    code = models.CharField(max_length=100)

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="inbound_orders"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="inbound_orders"
    )

    status = models.SmallIntegerField(
        choices=InboundStatus.choices,
        default=InboundStatus.DRAFT
    )

    def __str__(self):
        return self.code


# =========================
# 8. InboundItem 入库明细
# =========================

class InboundItem(models.Model):
    id = models.BigAutoField(primary_key=True)

    inbound_order = models.ForeignKey(
        InboundOrder,
        on_delete=models.CASCADE,
        related_name="items"
    )

    customer_product = models.ForeignKey(
        CustomerProduct,
        on_delete=models.PROTECT,
        related_name="inbound_items"
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.inbound_order.code} - {self.customer_product.customer_sku}"


# =========================
# 9. OutboundOrder 出库单
# =========================

class OutboundStatus(models.IntegerChoices):
    DRAFT = 1, "草稿"
    RELEASED = 2, "已释放"
    PICKING = 3, "拣货中"
    PICKED = 4, "已拣货"
    PACKING = 5, "打包中"
    SHIPPED = 6, "已发货"
    CANCELLED = 7, "已取消"


class OutboundOrder(models.Model):
    id = models.BigAutoField(primary_key=True)

    code = models.CharField(max_length=100)

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="outbound_orders"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="outbound_orders"
    )

    status = models.SmallIntegerField(
        choices=OutboundStatus.choices,
        default=OutboundStatus.DRAFT
    )

    def __str__(self):
        return self.code


# =========================
# 10. OutboundItem 出库明细
# =========================

class OutboundItem(models.Model):
    id = models.BigAutoField(primary_key=True)

    outbound_order = models.ForeignKey(
        OutboundOrder,
        on_delete=models.CASCADE,
        related_name="items"
    )

    customer_product = models.ForeignKey(
        CustomerProduct,
        on_delete=models.PROTECT,
        related_name="outbound_items"
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.outbound_order.code} - {self.customer_product.customer_sku}"


# =========================
# 11. InventoryTransaction 库存流水
# =========================

class InventoryTransactionType(models.IntegerChoices):
    INBOUND = 1, "入库增加"
    OUTBOUND = 2, "出库减少"
    STOCK_LOSS = 3, "盘亏"
    STOCK_GAIN = 4, "盘盈"


class InventoryTransactionSource(models.IntegerChoices):
    INBOUND_ORDER = 1, "入库单"
    OUTBOUND_ORDER = 2, "出库单"
    STOCKTAKE = 3, "盘点"


class InventoryTransaction(models.Model):
    id = models.BigAutoField(primary_key=True)

    customer_product = models.ForeignKey(
        CustomerProduct,
        on_delete=models.PROTECT,
        related_name="inventory_transactions"
    )

    quantity = models.IntegerField(
        help_text="正数表示增加，负数表示减少"
    )

    type = models.SmallIntegerField(
        choices=InventoryTransactionType.choices
    )

    source = models.SmallIntegerField(
        choices=InventoryTransactionSource.choices
    )

    source_foreign_id = models.BigIntegerField()

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="inventory_transactions"
    )

    def __str__(self):
        return f"{self.customer_product.customer_sku} - {self.quantity}"