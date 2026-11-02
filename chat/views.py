from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import NewConversationForm
from .models import Conversation, Message

User = get_user_model()


@login_required
def inbox(request):
    latest_message = Message.objects.filter(
        conversation=OuterRef("pk")
    ).order_by("-created_at", "-pk")
    conversations = (
        Conversation.objects.filter(
            Q(user_one=request.user) | Q(user_two=request.user)
        )
        .select_related("user_one", "user_two")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__read_at__isnull=True)
                & ~Q(messages__sender=request.user),
            ),
            last_message=Subquery(latest_message.values("body")[:1]),
            last_message_at=Subquery(
                latest_message.values("created_at")[:1]
            ),
        )
        .order_by(F("last_message_at").desc(nulls_last=True), "-updated_at")
    )

    return render(
        request,
        "chat/inbox.html",
        {"conversations": conversations},
    )


@login_required
def new_conversation(request):
    form = NewConversationForm(
        request.POST or None,
        current_user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        recipient = form.cleaned_data["recipient"]
        user_one_id, user_two_id = sorted((request.user.pk, recipient.pk))
        try:
            with transaction.atomic():
                conversation, _ = Conversation.objects.get_or_create(
                    user_one_id=user_one_id,
                    user_two_id=user_two_id,
                )
        except IntegrityError:
            conversation = Conversation.objects.get(
                user_one_id=user_one_id,
                user_two_id=user_two_id,
            )
        return redirect(
            "chat:conversation",
            conversation_id=conversation.pk,
        )

    return render(request, "chat/new_conversation.html", {"form": form})


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(
            Q(user_one=request.user) | Q(user_two=request.user)
        ).select_related("user_one", "user_two"),
        pk=conversation_id,
    )
    Message.objects.filter(
        conversation=conversation,
        read_at__isnull=True,
    ).exclude(sender=request.user).update(read_at=timezone.now())

    messages = conversation.messages.select_related("sender").order_by(
        "created_at",
        "pk",
    )
    return render(
        request,
        "chat/conversation.html",
        {
            "conversation": conversation,
            "messages": messages,
            "recipient": conversation.other_user(request.user),
        },
    )
