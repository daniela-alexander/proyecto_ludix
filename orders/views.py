from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from juegos.models import Order


@login_required
def order_list(request):
    orders = (
        Order.objects.filter(customer__user=request.user)
        .select_related("customer__user")
        .order_by("-created_at")
    )

    return JsonResponse({
        "count": orders.count(),
        "items": [
            {
                "id": order.id,
                "estado": order.status,
                "total": str(order.total),
                "creado_el": order.created_at.isoformat(),
            }
            for order in orders
        ],
    })


@login_required
def order_detail(request, order_id):
    order = Order.objects.filter(id=order_id, customer__user=request.user).first()
    if not order:
        return JsonResponse({"error": "Pedido no encontrado"}, status=404)

    return JsonResponse({
        "id": order.id,
        "estado": order.status,
        "total": str(order.total),
        "creado_el": order.created_at.isoformat(),
    })
