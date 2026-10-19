from django.urls import path

from .views import add_to_wishlist, wishlist_list

urlpatterns = [
    path("", wishlist_list, name="wishlist_list"),
    path("add/<int:juego_id>/", add_to_wishlist, name="wishlist_add"),
]
