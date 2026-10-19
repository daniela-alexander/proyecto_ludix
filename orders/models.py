from juegos.models import Pedido


class Order(Pedido):
    class Meta:
        proxy = True
        app_label = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
