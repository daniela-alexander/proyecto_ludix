from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import LibraryGame


@login_required
def library_list(request):
    entries = (
        LibraryGame.objects.filter(user_profile__user=request.user)
        .select_related("user_profile__user", "game")
        .order_by("-added_at")
    )

    payload = {
        "count": entries.count(),
        "items": [
            {
                "id": item.id,
                "juego_id": item.game.id,
                "titulo": item.game.title,
                "favorito": item.favorite,
                "fecha_agregado": item.added_at.isoformat(),
            }
            for item in entries
        ],
    }
    return JsonResponse(payload)


@login_required
def add_to_library(request, juego_id):
    from juegos.models import Game, UserProfile

    user_profile = UserProfile.objects.get(user=request.user)
    game = Game.objects.get(id=juego_id)

    item, created = LibraryGame.objects.get_or_create(user_profile=user_profile, game=game)
    if request.method == "POST":
        item.favorite = request.POST.get("favorito") in {"true", "1", "True"}
        item.save()

    return JsonResponse({
        "created": created,
        "juego_id": game.id,
        "titulo": game.title,
        "favorito": item.favorite,
    })
