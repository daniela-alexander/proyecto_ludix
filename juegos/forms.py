from django import forms

from .models import Category, SuggestionSession

EDAD_MAYOR_DE_18 = 19
EDAD_FILTRO_MAYOR_DE_18 = 100


class SugerenciaForm(forms.Form):
    tipo_sugerencia = forms.ChoiceField(
        label="¿De dónde quieres que salgan las recomendaciones?",
        choices=[
            (
                SuggestionSession.SuggestionType.LIBRARY,
                "De mi biblioteca",
            ),
            (
                SuggestionSession.SuggestionType.PURCHASE,
                "Del catálogo de Ludix",
            ),
        ],
        help_text=(
            "La biblioteca muestra juegos que ya tienes. "
            "El catálogo puede incluir juegos no disponibles actualmente."
        ),
    )

    num_jugadores = forms.IntegerField(
        label="Número de jugadores",
        min_value=1,
        max_value=10,
        initial=4,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "min": "1",
            "max": "10",
            "step": "1",
        }),
    )

    edad_minima_participante = forms.IntegerField(
        label="Edad de la persona más joven",
        min_value=3,
        max_value=EDAD_MAYOR_DE_18,
        initial=18,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "min": "3",
            "max": str(EDAD_MAYOR_DE_18),
            "step": "1",
        }),
    )

    duracion_max = forms.IntegerField(
        label="Duración máxima en minutos",
        min_value=15,
        max_value=240,
        initial=90,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "min": "15",
            "max": "240",
            "step": "15",
        }),
    )

    dificultad_preferida = forms.DecimalField(
        label="Dificultad (1 = muy fácil, 5 = muy difícil)",
        initial=3,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(
            attrs={
                "type": "range",
                "min": "1",
                "max": "5",
                "step": "1",
            }
        )
    )   

    tematica = forms.ModelChoiceField(
        label="Temática",
        queryset=Category.objects.order_by("name"),
        required=False,
        empty_label="Cualquiera",
    )
