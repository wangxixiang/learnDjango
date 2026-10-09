
import re
from django.shortcuts import render
from django.utils.timezone import datetime
from django.http import HttpResponse, request

from hello.models import Inventory,Warehouse, InventoryStatus
from django.db.models import Sum

print("http://127.0.0.1:8000/hello/VSCode")
print("http://127.0.0.1:8000/admin")

def home(request):
    print("home() called")
    return HttpResponse("Hello, Django!")

def inventory_list(request):
    custommer_sku=request.GET.get("customer_sku","")
    product_name=request.GET.get("product_name","")
    warehouse_id=request.GET.get("warehouse_id","")
    status = request.GET.get("status", "")

    inventories=Inventory.objects.all()
    warehouses = Warehouse.objects.all()

    if custommer_sku:
        inventories = inventories.filter(customer_product__customer_sku=custommer_sku)
    if product_name:
        inventories = inventories.filter(customer_product__name__icontains=product_name)
    if warehouse_id:
        inventories = inventories.filter(location__warehouse_id=warehouse_id        )
    if status:
        inventories = inventories.filter(status=status)

    total_quantity = inventories.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    return render(request, "hello/inventory_list.html", 
                  {"inventories": inventories,
                    "customer_sku": custommer_sku, 
                    "product_name": product_name,
                    "warehouse_id": warehouse_id,
                    "warehouses": warehouses,
                    "status": status,
                    "status_choices": InventoryStatus.choices,
                    "total_quantity": total_quantity
                    })

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