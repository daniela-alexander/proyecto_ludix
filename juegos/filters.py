import django_filters

from .models import Categoria, Juego, Mecanica


class JuegoFilter(django_filters.FilterSet):
    precio_min = django_filters.NumberFilter(
        field_name="precio",
        lookup_expr="gte",
    )
    precio_max = django_filters.NumberFilter(
        field_name="precio",
        lookup_expr="lte",
    )
    dificultad_min = django_filters.NumberFilter(
        field_name="dificultad",
        lookup_expr="gte",
    )
    dificultad_max = django_filters.NumberFilter(
        field_name="dificultad",
        lookup_expr="lte",
    )
    duracion_min = django_filters.NumberFilter(
        field_name="duracion_minutos",
        lookup_expr="gte",
    )
    duracion_max = django_filters.NumberFilter(
        field_name="duracion_minutos",
        lookup_expr="lte",
    )
    categoria = django_filters.ModelChoiceFilter(
        field_name="categorias",
        queryset=Categoria.objects.all(),
    )
    mecanica = django_filters.ModelChoiceFilter(
        field_name="mecanicas",
        queryset=Mecanica.objects.all(),
    )

    class Meta:
        model = Juego
        fields = [
            "precio_min",
            "precio_max",
            "dificultad_min",
            "dificultad_max",
            "duracion_min",
            "duracion_max",
            "categoria",
            "mecanica",
        ]