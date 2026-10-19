from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import LibraryGame, Game, UserProfile


def _build_filters(request):
    players = int(request.GET.get("players", 2))
    duration = int(request.GET.get("duration", 120))
    age = int(request.GET.get("age", 8))
    difficulty = Decimal(request.GET.get("difficulty", "4.00"))

    filters = {
        "min_players__lte": players,
        "max_players__gte": players,
        "duration_minutes__lte": duration,
        "min_age__lte": age,
        "difficulty__lte": difficulty,
    }
    return filters


@login_required
def recommendation_dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    excluded_ids = set(
        LibraryGame.objects.filter(user_profile=user_profile).values_list("game_id", flat=True)
    )

    queryset = Game.objects.filter(**_build_filters(request)).exclude(id__in=excluded_ids)[:10]

    payload = {
        "user": request.user.username,
        "recommendations": [
            {
                "id": game.id,
                "titulo": game.title,
                "descripcion": game.description,
                "jugadores": f"{game.min_players}-{game.max_players}",
                "duracion_minutos": game.duration_minutes,
                "edad_minima": game.min_age,
                "dificultad": str(game.difficulty),
                "precio": str(game.price),
            }
            for game in queryset
        ],
    }
    return JsonResponse(payload)
