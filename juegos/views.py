from django.shortcuts import render
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .filters import JuegoFilter
from .models import (
    BibliotecaJuego,
    Juego,
    PerfilUsuario,
    SesionJuegoPropuesto,
    SesionSugerencia,
)
from .serializers import JuegoSerializer
from .pagination import JuegoPagination

# este ultimo añadido por daniela para configurar la paginación

from django.contrib.auth.decorators import login_required
from .forms import SugerenciaForm


class JuegoListView(ListAPIView):
    queryset = Juego.objects.all()
    serializer_class = JuegoSerializer
    pagination_class = JuegoPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = JuegoFilter


def home(request):
    return render(request, "home.html")


@login_required
def sugerencia_view(request):
    form = SugerenciaForm(
        request.POST if request.method == "POST" else None
    )
    enviado = False
    recomendaciones = []

    if request.method == "POST" and form.is_valid():
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
        criterios = form.cleaned_data

        sesion = SesionSugerencia.objects.create(
            anfitrion=perfil,
            tipo_sugerencia=criterios["tipo_sugerencia"],
            num_jugadores=criterios["num_jugadores"],
            edad_minima_participante=criterios[
                "edad_minima_participante"
            ],
            dificultad_preferida=criterios["dificultad_preferida"],
            duracion_max=criterios["duracion_max"],
            tematica=criterios["tematica"],
        )

        juegos = Juego.objects.filter(
            num_jugadores_min__lte=criterios["num_jugadores"],
            num_jugadores_max__gte=criterios["num_jugadores"],
            edad_minima__lte=criterios["edad_minima_participante"],
            duracion_minutos__lte=criterios["duracion_max"],
        )

        if criterios["tipo_sugerencia"] == SesionSugerencia.TipoSugerencia.BIBLIOTECA:
            juegos = juegos.filter(bibliotecas__usuario=perfil)

        if criterios["tematica"]:
            juegos = juegos.filter(categorias=criterios["tematica"])

        candidatos = list(juegos.distinct())
        candidatos.sort(
            key=lambda juego: (
                abs(
                    juego.dificultad
                    - criterios["dificultad_preferida"]
                ),
                juego.duracion_minutos,
                juego.titulo.lower(),
            )
        )
        recomendaciones = candidatos[:3]

        SesionJuegoPropuesto.objects.bulk_create(
            [
                SesionJuegoPropuesto(sesion=sesion, juego=juego)
                for juego in recomendaciones
            ]
        )

        enviado = True

    return render(
        request,
        "juegos/sugerencia_form.html",
        {
            "form": form,
            "enviado": enviado,
            "recomendaciones": recomendaciones,
        },
    )