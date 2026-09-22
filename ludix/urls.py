from django.contrib import admin
from django.urls import path
from juegos.views import JuegoListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/juegos/", JuegoListView.as_view()),
]
