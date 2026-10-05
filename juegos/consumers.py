import json

from channels.generic.websocket import AsyncWebsocketConsumer


class UsuariosConsumer(AsyncWebsocketConsumer):
    usuarios_conectados = set()

    async def connect(self):
        self.usuarios_conectados.add(self.channel_name)

        await self.accept()
        await self.channel_layer.group_add(
            "usuarios_conectados",
            self.channel_name,
        )

        await self.actualizar_contador()

    async def disconnect(self, close_code):
        self.usuarios_conectados.discard(self.channel_name)

        await self.channel_layer.group_discard(
            "usuarios_conectados",
            self.channel_name,
        )

        await self.actualizar_contador()

    async def actualizar_contador(self):
        await self.channel_layer.group_send(
            "usuarios_conectados",
            {
                "type": "enviar_contador",
                "cantidad": len(self.usuarios_conectados),
            },
        )

    async def enviar_contador(self, evento):
        await self.send(
            text_data=json.dumps(
                {
                    "usuarios": evento["cantidad"],
                }
            )
        )