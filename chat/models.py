from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):
    user_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user_one",
    )
    user_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user_two",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_one", "user_two"],
                name="unique_chat_participant_pair",
            ),
            models.CheckConstraint(
                condition=~Q(user_one=F("user_two")),
                name="chat_participants_must_differ",
            ),
        ]

    def includes(self, user):
        return user.pk in (self.user_one_id, self.user_two_id)

    def other_user(self, user):
        return self.user_two if user.pk == self.user_one_id else self.user_one


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    body = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"],
                name="chat_msg_convo_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.sender}: {self.body[:40]}"
