from juegos.models import Pedido


class Order(Pedido):
    class Meta:
        proxy = True
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
