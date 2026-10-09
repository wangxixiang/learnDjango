
import re
from django.shortcuts import render
from django.utils.timezone import datetime
from django.http import HttpResponse

from hello.models import Inventory

print("http://127.0.0.1:8000/hello/VSCode")
print("http://127.0.0.1:8000/admin")

def home(request):
    print("home() called")
    return HttpResponse("Hello, Django!")

def inventory_list(request):
    custommer_sku=request.GET.get("customer_sku","")
    if custommer_sku:
        invnentories = Inventory.objects.filter(customer_product__customer_sku=custommer_sku)
   
    return render(request, "hello/inventory_list.html", 
                  {"inventories": invnentories})

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