from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from juegos.models import Game, LibraryGame, UserProfile


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
@require_POST
def add_to_library(request, game_id):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    game = get_object_or_404(Game, id=game_id)

    item, created = LibraryGame.objects.get_or_create(user_profile=user_profile, game=game)
    if "favorito" in request.POST:
        item.favorite = request.POST.get("favorito") in {"true", "1", "True"}
        item.save()

    next_url = request.POST.get("next")
    if next_url is not None:
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return HttpResponseRedirect(next_url)
        return HttpResponseRedirect(
            reverse("game_detail", kwargs={"game_id": game.id})
        )

    return JsonResponse({
        "created": created,
        "game_id": game.id,
        "titulo": game.title,
        "favorito": item.favorite,
    })
