from django import forms as django_forms
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

from juegos.models import BibliotecaJuego, PerfilUsuario, Wishlist
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
    perfil, creado = PerfilUsuario.objects.get_or_create(
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

    biblioteca = (
        BibliotecaJuego.objects
        .filter(usuario=perfil)
        .select_related("juego")
        .order_by("-fecha_agregado")
    )

    favoritos = biblioteca.filter(favorito=True)

    wishlist = (
        Wishlist.objects
        .filter(usuario=perfil)
        .select_related("juego")
        .order_by("-agregado_el")
    )

    sesiones = perfil.sesiones_sugerencia.order_by(
        "-creado_el"
    )[:5]

    pedidos = perfil.pedidos.order_by("-creado_el")[:5]

    context = {
        "perfil": perfil,
        "biblioteca": biblioteca[:6],
        "favoritos": favoritos[:6],
        "wishlist": wishlist[:6],
        "sesiones": sesiones,
        "pedidos": pedidos,
        "total_juegos": biblioteca.count(),
        "total_favoritos": favoritos.count(),
        "total_wishlist": wishlist.count(),
        "total_pedidos": perfil.pedidos.count(),
        "email_error": email_error,
        "email_success": email_success,
    }

    return render(request, "accounts/profile.html", context)