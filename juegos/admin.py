from django.contrib import admin
from .models import Game, Category


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "id")
    search_fields = ("title",)

    fields = (
        "title",
        "description",
        "title_en",
        "description_en",
        "title_ca",
        "description_ca",
        "title_it",
        "description_it",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "id")
    search_fields = ("name",)

    fields = (
        "name",
        "name_en",
        "name_ca",
        "name_it",
        "slug",
        "description",
    )
