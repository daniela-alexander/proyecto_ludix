from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import UserProfile, Wishlist


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
def add_to_wishlist(request, juego_id):
    from juegos.models import Game

    user_profile = UserProfile.objects.get(user=request.user)
    game = Game.objects.get(id=juego_id)

    item, created = Wishlist.objects.get_or_create(user_profile=user_profile, game=game)
    return JsonResponse({
        "created": created,
        "juego_id": game.id,
        "titulo": game.title,
    })
