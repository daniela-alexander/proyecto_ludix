from django.contrib.auth.models import User
from django.conf import settings
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import re_path, reverse

from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from .consumers import ChatConsumer
from .models import Conversation, Message
from ludix.asgi import application


class ChatViewsTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="test-pass")
        self.bob = User.objects.create_user(username="bob", password="test-pass")
        self.client.force_login(self.alice)

    def test_inbox_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("chat:inbox"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_user_can_start_conversation(self):
        response = self.client.post(
            reverse("chat:new"),
            {"recipient": self.bob.pk},
        )

        conversation = Conversation.objects.get()
        self.assertRedirects(
            response,
            reverse(
                "chat:conversation",
                kwargs={"conversation_id": conversation.pk},
            ),
        )
        self.assertTrue(conversation.includes(self.alice))
        self.assertTrue(conversation.includes(self.bob))

    def test_existing_conversation_is_reused_and_cannot_be_opened_by_others(self):
        conversation = Conversation.objects.create(
            user_one=self.alice,
            user_two=self.bob,
        )
        self.client.post(reverse("chat:new"), {"recipient": self.bob.pk})
        self.assertEqual(Conversation.objects.count(), 1)

        stranger = User.objects.create_user(
            username="stranger",
            password="test-pass",
        )
        self.client.force_login(stranger)
        response = self.client.get(
            reverse(
                "chat:conversation",
                kwargs={"conversation_id": conversation.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_inbox_shows_unread_count_and_opening_marks_messages_read(self):
        conversation = Conversation.objects.create(
            user_one=self.alice,
            user_two=self.bob,
        )
        message = Message.objects.create(
            conversation=conversation,
            sender=self.bob,
            body="Hola, Alice",
        )

        inbox_response = self.client.get(reverse("chat:inbox"))
        self.assertEqual(inbox_response.context["conversations"][0].unread_count, 1)

        self.client.get(
            reverse(
                "chat:conversation",
                kwargs={"conversation_id": conversation.pk},
            )
        )

        message.refresh_from_db()
        self.assertIsNotNone(message.read_at)

    def test_chat_sections_follow_the_selected_language(self):
        translations = {
            "en": (
                "Messages",
                "Your private conversations.",
                "New conversation",
                "Choose who you want to talk to.",
                "Select a user",
                "Open conversation",
            ),
            "ca": (
                "Missatges",
                "Les teves converses privades.",
                "Nova conversa",
                "Tria amb qui vols parlar.",
                "Selecciona un usuari",
                "Obre la conversa",
            ),
            "it": (
                "Messaggi",
                "Le tue conversazioni private.",
                "Nuova conversazione",
                "Scegli con chi vuoi parlare.",
                "Seleziona un utente",
                "Apri la conversazione",
            ),
        }

        for language, expected_strings in translations.items():
            with self.subTest(language=language):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
                inbox_response = self.client.get(reverse("chat:inbox"))
                new_chat_response = self.client.get(reverse("chat:new"))

                for expected in expected_strings[:2]:
                    self.assertContains(inbox_response, expected)
                for expected in expected_strings[2:]:
                    self.assertContains(new_chat_response, expected)


@override_settings(
    CHANNEL_LAYERS={
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
)
class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="test-pass")
        self.bob = User.objects.create_user(username="bob", password="test-pass")
        self.stranger = User.objects.create_user(
            username="stranger",
            password="test-pass",
        )
        self.session_client = Client()
        self.session_client.force_login(self.alice)
        self.stranger_client = Client()
        self.stranger_client.force_login(self.stranger)
        self.conversation = Conversation.objects.create(
            user_one=self.alice,
            user_two=self.bob,
        )

    def communicator_for(self, user):
        application = URLRouter(
            [
                re_path(
                    r"ws/chat/(?P<conversation_id>\d+)/$",
                    ChatConsumer.as_asgi(),
                )
            ]
        )

        async def authenticated_consumer(scope, receive, send):
            scope = {**scope, "user": user}
            await application(scope, receive, send)

        return WebsocketCommunicator(
            authenticated_consumer,
            f"/ws/chat/{self.conversation.pk}/",
        )

    async def test_participants_exchange_and_persist_messages(self):
        alice_socket = self.communicator_for(self.alice)
        bob_socket = self.communicator_for(self.bob)
        alice_connected = bob_connected = False

        try:
            connected, _ = await alice_socket.connect()
            self.assertTrue(connected)
            alice_connected = True
            connected, _ = await bob_socket.connect()
            self.assertTrue(connected)
            bob_connected = True

            await alice_socket.send_json_to({"message": "Hola, Bob"})
            alice_event = await alice_socket.receive_json_from()
            bob_event = await bob_socket.receive_json_from()

            self.assertEqual(alice_event["body"], "Hola, Bob")
            self.assertEqual(bob_event["sender_name"], "alice")
            message = await database_sync_to_async(Message.objects.get)()
            self.assertEqual(message.sender_id, self.alice.pk)
            self.assertIsNotNone(message.read_at)
        finally:
            if alice_connected:
                await alice_socket.disconnect()
            if bob_connected:
                await bob_socket.disconnect()

    async def test_asgi_websocket_authenticates_the_django_session(self):
        session_cookie = self.session_client.cookies[
            settings.SESSION_COOKIE_NAME
        ].value
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{self.conversation.pk}/",
            headers=[
                (b"cookie", f"{settings.SESSION_COOKIE_NAME}={session_cookie}".encode()),
                (b"origin", b"http://testserver"),
            ],
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        try:
            await communicator.send_json_to({"message": "Sesión validada"})
            event = await communicator.receive_json_from()
            self.assertEqual(event["body"], "Sesión validada")
            self.assertEqual(event["sender_name"], "alice")
        finally:
            await communicator.disconnect()

    async def test_asgi_websocket_rejects_anonymous_and_unrelated_users(self):
        path = f"/ws/chat/{self.conversation.pk}/"
        origin = (b"origin", b"http://testserver")
        anonymous_socket = WebsocketCommunicator(
            application,
            path,
            headers=[origin],
        )
        connected, close_code = await anonymous_socket.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

        session_cookie = self.stranger_client.cookies[
            settings.SESSION_COOKIE_NAME
        ].value
        stranger_socket = WebsocketCommunicator(
            application,
            path,
            headers=[
                (b"cookie", f"{settings.SESSION_COOKIE_NAME}={session_cookie}".encode()),
                origin,
            ],
        )
        connected, close_code = await stranger_socket.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)
