from django.contrib import admin

from .models import (
    Customer,
    Product,
    CustomerProduct,
    Warehouse,
    Location,
    Inventory,
    InboundOrder,
    InboundItem,
    OutboundOrder,
    OutboundItem,
    InventoryTransaction,
)


admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(CustomerProduct)
admin.site.register(Warehouse)
admin.site.register(Location)
admin.site.register(Inventory)
admin.site.register(InboundOrder)
admin.site.register(InboundItem)
admin.site.register(OutboundOrder)
admin.site.register(OutboundItem)
admin.site.register(InventoryTransaction)