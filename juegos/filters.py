import django_filters
from django import forms

from .models import Category, Game, Mechanic


class GameFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        range_pairs = (
            ("price_min", "price_max"),
            ("difficulty_min", "difficulty_max"),
            ("duration_min", "duration_max"),
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


class GameFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
    )
    price_max = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
    )
    difficulty_min = django_filters.NumberFilter(
        field_name="difficulty",
        lookup_expr="gte",
    )
    difficulty_max = django_filters.NumberFilter(
        field_name="difficulty",
        lookup_expr="lte",
    )
    duration_min = django_filters.NumberFilter(
        field_name="duration_minutes",
        lookup_expr="gte",
    )
    duration_max = django_filters.NumberFilter(
        field_name="duration_minutes",
        lookup_expr="lte",
    )
    category = django_filters.ModelChoiceFilter(
        field_name="categories",
        queryset=Category.objects.order_by("name"),
        distinct=True,
    )
    mechanic = django_filters.ModelChoiceFilter(
        field_name="mechanics",
        queryset=Mechanic.objects.order_by("name"),
        distinct=True,
    )

    class Meta:
        model = Game
        form = GameFilterForm
        fields = [
            "price_min",
            "price_max",
            "difficulty_min",
            "difficulty_max",
            "duration_min",
            "duration_max",
            "category",
            "mechanic",
        ]


JuegoFilterForm = GameFilterForm
JuegoFilter = GameFilter