from django.contrib import admin
from .models import (
    Categoria,
    Juego,
    JuegoCategoria,
    JuegoMecanica,
    Mecanica,
)


class JuegoCategoriaInline(admin.TabularInline):
    model = JuegoCategoria
    extra = 1


class JuegoMecanicaInline(admin.TabularInline):
    model = JuegoMecanica
    extra = 1

@admin.register(Juego)
class JuegoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "min_players",
        "max_players",
        "duration_minutes",
        "min_age",
        "difficulty",
        "stock",
        "id",
    )
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
    
    inlines = (JuegoCategoriaInline, JuegoMecanicaInline)


@admin.register(Categoria)
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
    
    
admin.site.register(Categoria)
admin.site.register(Mecanica)