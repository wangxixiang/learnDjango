import re
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.timezone import datetime
from django.http import HttpResponse, request
from django.db import transaction
from django.db.models import Count, Sum

from hello.models import (
    Inventory,
    InventoryTransactionSource,
    InventoryTransactionType,
    Warehouse,
    InventoryStatus,
    InboundOrderStatus,
    InboundOrder,
    Customer,
    CustomerProduct,
    InboundItem,
    InventoryTransaction,
)
from django.db.models import Sum

print("http://127.0.0.1:8000/hello/VSCode")
print("http://127.0.0.1:8000/admin")


def home(request):
    print("home() called")
    return render(
        request,
        "hello/home.html",
        {},
    )


@transaction.atomic
def inbound_receive(request, order_id):

    order = InboundOrder.objects.get(id=order_id)

    if request.method != "POST":
        return redirect("inbound_detail", order_id=order.id)
    # 防止重复收货，只有草稿状态的订单才能收货
    if order.status != InboundOrderStatus.DRAFT:
        messages.warning(request, "该入库单已处理，不能重复收货。")
        return redirect("inbound_detail", order_id=order.id)

    items = order.items.all()

    for item in items:
        # 查询或者新增
        inventory, created = Inventory.objects.get_or_create(
            location_id=1,
            customer_product=item.customer_product,
            status=InventoryStatus.AVAILABLE,
            defaults={
                "quantity": 0,
            },
        )

        inventory.quantity += item.quantity
        inventory.save()

        InventoryTransaction.objects.create(
            customer_product=item.customer_product,
            quantity=item.quantity,
            # 使用枚举类型，避免魔法数字
            type=InventoryTransactionType.INBOUND,
            source=InventoryTransactionSource.INBOUND_ORDER,
            source_foreign_id=order.id,
            location_id=1,
        )

    order.status = InboundOrderStatus.RECEIVED
    order.save()
    messages.success(
        request,
        f"入库单 {order.code} 已收货成功！",
    )
    return redirect("inbound_detail", order_id=order.id)


# List all inbound orders
def inbound_list(request):
    # Retrieve all inbound orders and order them by ID in descending order
    inbound_orders = InboundOrder.objects.all().order_by("-id")
    inbound_orders = InboundOrder.objects.annotate(
        # 好简洁呀，这么简单就加了两个字段，一个是从表的条数，一个是从表某个字段的求和
        item_count=Count("items"),
        total_quantity=Sum("items__quantity"),
    )
    return render(
        request,
        "hello/inbound_list.html",
        {
            "inbound_orders": inbound_orders,
        },
    )


def inbound_create(request):

    if request.method == "POST":

        code = request.POST.get("code")
        customer_id = request.POST.get("customer")
        warehouse_id = request.POST.get("warehouse")

        InboundOrder.objects.create(
            code=code,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
        )

        return redirect("inbound_list")

    customers = Customer.objects.all()
    warehouses = Warehouse.objects.all()

    return render(
        request,
        "hello/inbound_create.html",
        {
            "customers": customers,
            "warehouses": warehouses,
        },
    )


def inbound_item_create(request, order_id):
    # 上来先获取是哪个order
    order = InboundOrder.objects.get(id=order_id)

    print("进入此页面的方法: " + request.method)
    # 保存的逻辑
    if request.method == "POST":

        customer_product_id = request.POST.get("customer_product")
        quantity = request.POST.get("quantity")

        InboundItem.objects.create(
            inbound_order=order,
            customer_product_id=customer_product_id,
            quantity=quantity,
        )

        return redirect("inbound_list")
    # 加载新页面的逻辑
    customer_products = CustomerProduct.objects.filter(customer=order.customer)

    return render(
        request,
        "hello/inbound_item_create.html",
        {
            "order": order,
            "customer_products": customer_products,
        },
    )


def inbound_detail(request, order_id):

    order = InboundOrder.objects.get(id=order_id)

    items = order.items.all()
    can_receive = order.status == InboundOrderStatus.DRAFT
    return render(
        request,
        "hello/inbound_detail.html",
        {
            "order": order,
            "items": items,
            "can_receive": can_receive,
        },
    )


def inventory_list(request):
    custommer_sku = request.GET.get("customer_sku", "")
    product_name = request.GET.get("product_name", "")
    warehouse_id = request.GET.get("warehouse_id", "")
    status = request.GET.get("status", "")

    inventories = Inventory.objects.all()
    warehouses = Warehouse.objects.all()

    if custommer_sku:
        inventories = inventories.filter(customer_product__customer_sku=custommer_sku)
    if product_name:
        inventories = inventories.filter(customer_product__name__icontains=product_name)
    if warehouse_id:
        inventories = inventories.filter(location__warehouse_id=warehouse_id)
    if status:
        inventories = inventories.filter(status=status)

    total_quantity = inventories.aggregate(total=Sum("quantity"))["total"] or 0

    return render(
        request,
        "hello/inventory_list.html",
        {
            "inventories": inventories,
            "customer_sku": custommer_sku,
            "product_name": product_name,
            "warehouse_id": warehouse_id,
            "warehouses": warehouses,
            "status": status,
            "status_choices": InventoryStatus.choices,
            "total_quantity": total_quantity,
        },
    )


def hello_there(request, name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")

    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    match_object = re.match("[a-zA-Z]+", name)

    if match_object:
        clean_name = match_object.group(0)
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return HttpResponse(content)
