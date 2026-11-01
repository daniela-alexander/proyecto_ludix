from django import forms
from django.utils.translation import gettext, gettext_lazy as _

from .models import Category, SuggestionSession

EDAD_MAYOR_DE_18 = 19
EDAD_FILTRO_MAYOR_DE_18 = 100


class SugerenciaForm(forms.Form):

    tipo_sugerencia = forms.ChoiceField(
        help_text=_(
            "La biblioteca muestra juegos que ya tienes. "
            "El catálogo puede incluir juegos no disponibles actualmente."
        ),
    )

    num_jugadores = forms.IntegerField(
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
        initial=3,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "min": "1",
            "max": "5",
            "step": "1",
        }),
    )

    tematica = forms.ModelChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Asignamos los labels dinámicamente para que respeten el idioma del request
        self.fields["tipo_sugerencia"].label = _("🎮 ¿De dónde quieres que salgan las recomendaciones?")
        self.fields["num_jugadores"].label = _("👥 Número de jugadores")
        self.fields["edad_minima_participante"].label = _("👶 Edad de la persona más joven")
        self.fields["duracion_max"].label = _("⏱️ Duración máxima en minutos")
        self.fields["dificultad_preferida"].label = _("🎯 Dificultad (1 = muy fácil, 5 = muy difícil)")
        self.fields["tematica"].label = _("🏷️ Temática")

        # Opciones y empty_label también de forma dinámica
        self.fields["tipo_sugerencia"].choices = [
            (
                SuggestionSession.SuggestionType.LIBRARY,
                _("De mi biblioteca"),
            ),
            (
                SuggestionSession.SuggestionType.PURCHASE,
                _("Del catálogo de Ludix"),
            ),
        ]
        
        self.fields["tematica"].empty_label = _("Cualquiera")
        self.fields["tematica"].label_from_instance = (
            lambda category: gettext(category.get_name())
        )