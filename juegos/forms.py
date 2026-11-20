from decimal import Decimal

from django import forms
from django.utils.translation import gettext, gettext_lazy as _

from .models import Category, SuggestionSession

EDAD_MAYOR_DE_18 = 19
EDAD_FILTRO_MAYOR_DE_18 = 100


class SugerenciaForm(forms.Form):

    tipo_sugerencia = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={"class": "recommend-source-options"}),
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

    duracion_preferencia = forms.ChoiceField(
        required=False,
        choices=(),
        initial="max60",
        widget=forms.RadioSelect(
            attrs={"class": "recommend-option-cards duration-options"}
        ),
    )

    edad_minima_participante = forms.TypedChoiceField(
        required=False,
        choices=(),
        coerce=int,
        empty_value=None,
        initial="",
        widget=forms.RadioSelect(
            attrs={"class": "recommend-option-cards age-options"}
        ),
    )

    dificultad_preferida = forms.TypedChoiceField(
        required=False,
        choices=(),
        coerce=Decimal,
        empty_value=None,
        initial="",
        widget=forms.RadioSelect(
            attrs={"class": "recommend-option-cards difficulty-options"}
        ),
    )

    tematica = forms.ModelChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Asignamos los labels dinámicamente para que respeten el idioma del request
        self.fields["tipo_sugerencia"].label = _("¿Dónde buscar?")
        self.fields["duracion_preferencia"].label = _("Tiempo de partida")
        self.fields["duracion_preferencia"].choices = [
            ("", _("♾️ Cualquiera")),
            ("max15", _("⚡ Hasta 15m")),
            ("max30", _("☕ Hasta 30m")),
            ("max60", _("🎯 Hasta 60m")),
            ("max120", _("🎲 Hasta 120m")),
            ("min120", _("🕰️ 120 y más")),
        ]
        self.fields["duracion_preferencia"].help_text = ""
        self.fields["num_jugadores"].label = _("👥 Número de jugadores")
        self.fields["num_jugadores"].help_text = ""
        self.fields["edad_minima_participante"].label = _(
            "Edad"
        )
        self.fields["edad_minima_participante"].choices = [
            ("", _("Cualquier edad")),
            (3, "🧸 3+"),
            (6, "🚀 6+"),
            (10, "🎲 10+"),
            (14, "⚔️ 14+"),
            (EDAD_MAYOR_DE_18, "🍷 18+"),
        ]
        self.fields["dificultad_preferida"].label = _("Dificultad")
        self.fields["dificultad_preferida"].choices = [
            ("", _("Cualquier dificultad")),
            (Decimal("1"), _("🌱 Muy fácil")),
            (Decimal("2"), _("🙂 Fácil")),
            (Decimal("3"), _("⚖️ Intermedio")),
            (Decimal("4"), _("🔥 Difícil")),
            (Decimal("5"), _("🏆 Muy difícil")),
        ]
        self.fields["dificultad_preferida"].help_text = _(
            "La dificultad solo influye en el orden de las recomendaciones."
        )
        self.fields["tematica"].label = _("🏷️ Categoría")
        self.fields["tematica"].help_text = ""

        # Opciones y empty_label también de forma dinámica
        self.fields["tipo_sugerencia"].choices = [
            (
                SuggestionSession.SuggestionType.LIBRARY,
                _("Mis juegos"),
            ),
            (
                SuggestionSession.SuggestionType.PURCHASE,
                _("Catálogo de Ludix"),
            ),
        ]
        
        self.fields["tematica"].empty_label = _("Cualquiera")
        self.fields["tematica"].label_from_instance = (
            lambda category: gettext(category.get_name())
        )