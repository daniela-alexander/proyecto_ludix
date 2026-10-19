from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import Pedido


@login_required
def order_list(request):
    pedidos = (
        Pedido.objects.filter(cliente__user=request.user)
        .select_related("cliente__user")
        .order_by("-creado_el")
    )

    return JsonResponse({
        "count": pedidos.count(),
        "items": [
            {
                "id": pedido.id,
                "estado": pedido.estado,
                "total": str(pedido.total),
                "creado_el": pedido.creado_el.isoformat(),
            }
            for pedido in pedidos
        ],
    })


@login_required
def order_detail(request, pedido_id):
    pedido = Pedido.objects.filter(id=pedido_id, cliente__user=request.user).first()
    if not pedido:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)

    return JsonResponse({
        "id": pedido.id,
        "estado": pedido.estado,
        "total": str(pedido.total),
        "creado_el": pedido.creado_el.isoformat(),
    })
