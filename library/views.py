from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import BibliotecaJuego


@login_required
def library_list(request):
    entries = (
        BibliotecaJuego.objects.filter(usuario__user=request.user)
        .select_related("usuario__user", "juego")
        .order_by("-fecha_agregado")
    )

    payload = {
        "count": entries.count(),
        "items": [
            {
                "id": item.id,
                "juego_id": item.juego.id,
                "titulo": item.juego.titulo,
                "favorito": item.favorito,
                "fecha_agregado": item.fecha_agregado.isoformat(),
            }
            for item in entries
        ],
    }
    return JsonResponse(payload)


@login_required
def add_to_library(request, juego_id):
    from juegos.models import Juego, PerfilUsuario

    usuario = PerfilUsuario.objects.get(user=request.user)
    juego = Juego.objects.get(id=juego_id)

    item, created = BibliotecaJuego.objects.get_or_create(usuario=usuario, juego=juego)
    if request.method == "POST":
        item.favorito = request.POST.get("favorito") in {"true", "1", "True"}
        item.save()

    return JsonResponse({
        "created": created,
        "juego_id": juego.id,
        "titulo": juego.titulo,
        "favorito": item.favorito,
    })
