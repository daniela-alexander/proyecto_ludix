from django import forms as django_forms
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

from juegos.models import LibraryGame, UserProfile, Wishlist
from .forms import RegisterForm


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {
        "form": form
    })


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    email_error = ""
    email_success = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        try:
            email = django_forms.EmailField(
                required=False
            ).clean(email)

            request.user.email = email
            request.user.save(update_fields=["email"])

            email_success = "Email actualizado correctamente."

        except ValidationError:
            email_error = "Introduce una dirección de email válida."

    library = (
        LibraryGame.objects
        .filter(user_profile=profile)
        .select_related("game")
        .order_by("-added_at")
    )

    favorites = library.filter(favorite=True)

    wishlist = (
        Wishlist.objects
        .filter(user_profile=profile)
        .select_related("game")
        .order_by("-added_at")
    )

    sessions = profile.suggestion_sessions.order_by(
        "-created_at"
    )[:5]

    orders = profile.orders.order_by("-created_at")[:5]

    context = {
        "profile": profile,
        "perfil": profile,
        "library": library[:6],
        "biblioteca": library[:6],
        "favorites": favorites[:6],
        "favoritos": favorites[:6],
        "wishlist": wishlist[:6],
        "sessions": sessions,
        "sesiones": sessions,
        "orders": orders,
        "pedidos": orders,
        "total_games": library.count(),
        "total_juegos": library.count(),
        "total_favorites": favorites.count(),
        "total_favoritos": favorites.count(),
        "total_wishlist": wishlist.count(),
        "total_orders": profile.orders.count(),
        "total_pedidos": profile.orders.count(),
        "email_error": email_error,
        "email_success": email_success,
    }

    return render(request, "accounts/profile.html", context)