from django.contrib import admin
from django.urls import include, path
from juegos.views import JuegoListView, home
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/juegos/", JuegoListView.as_view()),
    path("", home, name="home"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("accounts/", include("accounts.urls")),
]
