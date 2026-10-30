from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from juegos.models import Game, LibraryGame, UserProfile, Wishlist


@login_required
def wishlist_list(request):
    items = (
        Wishlist.objects.filter(user_profile__user=request.user)
        .select_related("user_profile__user", "game")
        .order_by("-added_at")
    )

    payload = {
        "count": items.count(),
        "items": [
            {
                "id": item.id,
                "juego_id": item.game.id,
                "titulo": item.game.title,
                "agregado_el": item.added_at.isoformat(),
            }
            for item in items
        ],
    }
    return JsonResponse(payload)


@login_required
@require_POST
def add_to_wishlist(request, game_id):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    game = get_object_or_404(Game, id=game_id)

    if LibraryGame.objects.filter(user_profile=user_profile, game=game).exists():
        Wishlist.objects.filter(user_profile=user_profile, game=game).delete()
        created = False
    else:
        _, created = Wishlist.objects.get_or_create(
            user_profile=user_profile,
            game=game,
        )

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseRedirect(next_url)

    return JsonResponse({
        "created": created,
        "game_id": game.id,
        "titulo": game.title,
    })


@login_required
@require_POST
def remove_from_wishlist(request, game_id):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    game = get_object_or_404(Game, id=game_id)

    if not LibraryGame.objects.filter(user_profile=user_profile, game=game).exists():
        Wishlist.objects.filter(user_profile=user_profile, game=game).delete()

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseRedirect(next_url)

    return HttpResponseRedirect(
        reverse("game_detail", kwargs={"game_id": game.id})
    )
