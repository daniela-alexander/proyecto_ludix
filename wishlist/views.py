from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import PerfilUsuario, Wishlist


@login_required
def wishlist_list(request):
    items = (
        Wishlist.objects.filter(usuario__user=request.user)
        .select_related("usuario__user", "juego")
        .order_by("-agregado_el")
    )

    payload = {
        "count": items.count(),
        "items": [
            {
                "id": item.id,
                "juego_id": item.juego.id,
                "titulo": item.juego.titulo,
                "agregado_el": item.agregado_el.isoformat(),
            }
            for item in items
        ],
    }
    return JsonResponse(payload)


@login_required
def add_to_wishlist(request, juego_id):
    from juegos.models import Juego

    usuario = PerfilUsuario.objects.get(user=request.user)
    juego = Juego.objects.get(id=juego_id)

    item, created = Wishlist.objects.get_or_create(usuario=usuario, juego=juego)
    return JsonResponse({
        "created": created,
        "juego_id": juego.id,
        "titulo": juego.titulo,
    })
