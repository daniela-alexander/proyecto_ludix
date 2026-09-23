import django_filters
from django import forms

from .models import Categoria, Juego, Mecanica


class JuegoFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        range_pairs = (
            ("precio_min", "precio_max"),
            ("dificultad_min", "dificultad_max"),
            ("duracion_min", "duracion_max"),
        )

        for minimum_name, maximum_name in range_pairs:
            minimum = cleaned_data.get(minimum_name)
            maximum = cleaned_data.get(maximum_name)
            if minimum is not None and maximum is not None and minimum > maximum:
                self.add_error(
                    minimum_name,
                    f"No puede ser mayor que {maximum_name.replace('_', ' ')}.",
                )

        return cleaned_data


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
        queryset=Categoria.objects.order_by("nombre"),
        distinct=True,
    )
    mecanica = django_filters.ModelChoiceFilter(
        field_name="mecanicas",
        queryset=Mecanica.objects.order_by("nombre"),
        distinct=True,
    )

    class Meta:
        model = Juego
        form = JuegoFilterForm
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