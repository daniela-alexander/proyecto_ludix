from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils import timezone

from .models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.conversation_id = int(
            self.scope["url_route"]["kwargs"]["conversation_id"]
        )
        if not await self.user_can_access_conversation():
            await self.close(code=4403)
            return

        self.group_name = f"chat-conversation-{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        body = content.get("message") if isinstance(content, dict) else None
        if not isinstance(body, str):
            await self.send_json(
                {"type": "error", "code": "invalid_message"}
            )
            return

        body = body.strip()
        if not body:
            await self.send_json(
                {"type": "error", "code": "empty_message"}
            )
            return
        if len(body) > 4000:
            await self.send_json(
                {"type": "error", "code": "message_too_long"}
            )
            return

        message = await self.save_message(body)
        if message is None:
            await self.close(code=4403)
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message_id": message["id"],
                "sender_id": self.scope["user"].pk,
                "sender_name": self.scope["user"].get_username(),
                "body": message["body"],
                "created_at": message["created_at"],
            },
        )

    async def chat_message(self, event):
        if event["sender_id"] != self.scope["user"].pk:
            await self.mark_message_read(event["message_id"])

        await self.send_json(
            {
                "type": "message",
                "id": event["message_id"],
                "sender_id": event["sender_id"],
                "sender_name": event["sender_name"],
                "body": event["body"],
                "created_at": event["created_at"],
            }
        )

    @database_sync_to_async
    def user_can_access_conversation(self):
        return Conversation.objects.filter(
            Q(user_one=self.scope["user"]) | Q(user_two=self.scope["user"]),
            pk=self.conversation_id,
        ).exists()

    @database_sync_to_async
    def save_message(self, body):
        conversation = Conversation.objects.filter(
            Q(user_one=self.scope["user"]) | Q(user_two=self.scope["user"]),
            pk=self.conversation_id,
        ).first()
        if conversation is None:
            return None

        message = Message.objects.create(
            conversation=conversation,
            sender=self.scope["user"],
            body=body,
        )
        Conversation.objects.filter(pk=conversation.pk).update(
            updated_at=timezone.now()
        )
        return {
            "id": message.pk,
            "body": message.body,
            "created_at": message.created_at.isoformat(),
        }

    @database_sync_to_async
    def mark_message_read(self, message_id):
        Message.objects.filter(
            pk=message_id,
            conversation_id=self.conversation_id,
            read_at__isnull=True,
        ).exclude(sender=self.scope["user"]).update(read_at=timezone.now())
