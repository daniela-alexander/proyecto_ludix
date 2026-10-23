from django import forms

from .models import Categoria, SesionSugerencia


class SugerenciaForm(forms.Form):
    tipo_sugerencia = forms.ChoiceField(
        label="¿De dónde quieres que salgan las recomendaciones?",
        choices=[
            (
                SesionSugerencia.TipoSugerencia.BIBLIOTECA,
                "De mi biblioteca",
            ),
            (
                SesionSugerencia.TipoSugerencia.COMPRA,
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
        min_value=0,
        max_value=100,
        initial=18,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "min": "0",
            "max": "100",
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
            "step": "1",
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
        queryset=Categoria.objects.order_by("nombre"),
        required=False,
        empty_label="Cualquiera",
    )
