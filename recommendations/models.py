from django.conf import settings
from django.db import models

from juegos.models import PerfilUsuario, Juego


class RecommendationPreference(models.Model):
    user = models.OneToOneField(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="recommendation_preferences",
    )
    jugadores_min = models.PositiveIntegerField(default=1)
    jugadores_max = models.PositiveIntegerField(default=6)
    duracion_maxima = models.PositiveIntegerField(default=120)
    edad_minima = models.PositiveIntegerField(default=8)
    dificultad_maxima = models.DecimalField(max_digits=3, decimal_places=2, default=4.00)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "recommendation_preference"

    def __str__(self):
        return f"Preferencias de {self.user.user.username}"


class RecommendationHistory(models.Model):
    user = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="recommendation_history",
    )
    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="recommendation_history",
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_history"

    def __str__(self):
        return f"{self.user.user.username} -> {self.juego.titulo}"
