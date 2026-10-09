from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import register_view, profile_view

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", LoginView.as_view(template_name="accounts/login.html", next_page="profile"), name="login"),
    path("profile/", profile_view, name="profile"),
]
