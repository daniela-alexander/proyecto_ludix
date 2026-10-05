from django.contrib import admin
from django.urls import path
from juegos.views import JuegoListView, inicio

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/juegos/", JuegoListView.as_view()),
    path("", inicio, name="inicio"),
]
