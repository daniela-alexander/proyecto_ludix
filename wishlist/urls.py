from django.urls import path

from .views import add_to_wishlist, remove_from_wishlist, wishlist_list

urlpatterns = [
    path("", wishlist_list, name="wishlist_list"),
    path("add/<int:game_id>/", add_to_wishlist, name="wishlist_add"),
    path("remove/<int:game_id>/", remove_from_wishlist, name="wishlist_remove"),
]
