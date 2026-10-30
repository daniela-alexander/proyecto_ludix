from django.urls import path

from .views import add_to_library, library_list, remove_from_library, toggle_favorite

urlpatterns = [
    path("", library_list, name="library_list"),
    path("add/<int:game_id>/", add_to_library, name="library_add"),
    path("remove/<int:game_id>/", remove_from_library, name="library_remove"),
    path("favorite/<int:game_id>/", toggle_favorite, name="library_favorite"),
]
