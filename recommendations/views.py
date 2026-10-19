from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import BibliotecaJuego, Juego, PerfilUsuario


def _build_filters(request):
    players = int(request.GET.get("players", 2))
    duration = int(request.GET.get("duration", 120))
    age = int(request.GET.get("age", 8))
    difficulty = Decimal(request.GET.get("difficulty", "4.00"))

    filters = {
        "num_jugadores_min__lte": players,
        "num_jugadores_max__gte": players,
        "duracion_minutos__lte": duration,
        "edad_minima__lte": age,
        "dificultad__lte": difficulty,
    }
    return filters


@login_required
def recommendation_dashboard(request):
    user_profile = PerfilUsuario.objects.get(user=request.user)
    excluded_ids = set(
        BibliotecaJuego.objects.filter(usuario=user_profile).values_list("juego_id", flat=True)
    )

    queryset = Juego.objects.filter(**_build_filters(request)).exclude(id__in=excluded_ids)[:10]

    payload = {
        "user": request.user.username,
        "recommendations": [
            {
                "id": juego.id,
                "titulo": juego.titulo,
                "descripcion": juego.descripcion,
                "jugadores": f"{juego.num_jugadores_min}-{juego.num_jugadores_max}",
                "duracion_minutos": juego.duracion_minutos,
                "edad_minima": juego.edad_minima,
                "dificultad": str(juego.dificultad),
                "precio": str(juego.precio),
            }
            for juego in queryset
        ],
    }
    return JsonResponse(payload)
