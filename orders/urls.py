from django.urls import path

from .views import order_detail, order_list

urlpatterns = [
    path("", order_list, name="order_list"),
    path("<int:order_id>/", order_detail, name="order_detail"),
]
