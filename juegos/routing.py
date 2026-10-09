from django.urls import re_path

from .consumers import UsuariosConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/usuarios/$",
        UsuariosConsumer.as_asgi(),
    ),
]