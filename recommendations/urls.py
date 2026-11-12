from django.urls import path

from .views import recommendation_dashboard, recommendation_preview

urlpatterns = [
    path("preview/", recommendation_preview, name="recommendation_preview"),
    path("", recommendation_dashboard, name="recommendation_dashboard"),
]
