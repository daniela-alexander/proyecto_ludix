from django.urls import path

from .views import recommendation_dashboard

urlpatterns = [
    path("", recommendation_dashboard, name="recommendation_dashboard"),
]
