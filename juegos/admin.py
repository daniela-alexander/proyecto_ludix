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
        "titulo",
        "num_jugadores_min",
        "num_jugadores_max",
        "duracion_minutos",
        "edad_minima",
        "dificultad",
        "stock",
    )
    search_fields = ("titulo",)
    inlines = (JuegoCategoriaInline, JuegoMecanicaInline)


admin.site.register(Categoria)
admin.site.register(Mecanica)