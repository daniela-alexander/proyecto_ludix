from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("new/", views.new_conversation, name="new"),
    path("<int:conversation_id>/", views.conversation_detail, name="conversation"),
]
