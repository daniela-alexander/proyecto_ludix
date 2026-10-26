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
    )
    search_fields = ("title",)
    inlines = (JuegoCategoriaInline, JuegoMecanicaInline)


admin.site.register(Categoria)
admin.site.register(Mecanica)