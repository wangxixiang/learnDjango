from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("hello/<name>", views.hello_there, name="hello_there"),
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inbound/", views.inbound_list, name="inbound_list"),
    path("inbound/create/", views.inbound_create, name="inbound_create"),
    path(
        "inbound/<int:order_id>/items/create/",
        views.inbound_item_create,
        name="inbound_item_create",
    ),
    path(
        "inbound/<int:order_id>/",
        views.inbound_detail,
        name="inbound_detail",
    ),
    path(
        "inbound/<int:order_id>/receive/",
        views.inbound_receive,
        name="inbound_receive",
    ),
]
