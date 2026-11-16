from django.urls import path

from .views import (
    dislike_recommendation,
    remove_recommendation_feedback,
    recommendation_dashboard,
    recommendation_preview,
)

urlpatterns = [
    path("preview/", recommendation_preview, name="recommendation_preview"),
    path("dislike/<int:game_id>/", dislike_recommendation, name="recommendation_dislike"),
    path(
        "dislike/<int:game_id>/remove/",
        remove_recommendation_feedback,
        name="recommendation_feedback_remove",
    ),
    path("", recommendation_dashboard, name="recommendation_dashboard"),
]
