from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    BibliotecaJuego,
    Juego,
    PerfilUsuario,
    SesionJuegoPropuesto,
    SesionSugerencia,
)
# este ultimo añadido por daniela para configurar la paginación
from .filters import GameFilter, JuegoFilter
from .models import Category, Game, Order, OrderLine
from .serializers import GameSerializer, JuegoSerializer
from .pagination import GamePagination, JuegoPagination

from django.contrib.auth.decorators import login_required
from .forms import SugerenciaForm


class GameListView(ListAPIView):
    queryset = Game.objects.all().order_by("id")
    serializer_class = GameSerializer
    pagination_class = GamePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = GameFilter
    search_fields = [
        "title",
        "description",
        "categories__name",
        "mechanics__name",
    ]
    ordering_fields = ["id", "title", "price", "difficulty", "duration_minutes"]
    ordering = ["id"]


JuegoListView = GameListView

def home(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category")
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    game_format = request.GET.get("format", "").strip()
    sort_by = request.GET.get("sort", "title")
    sort_options = (
        ("title", "Orden alfabético"),
        ("best_selling", "Más vendidos"),
        ("price_asc", "Precio: menor a mayor"),
        ("price_desc", "Precio: mayor a menor"),
        ("favorites", "Más favoritos"),
        ("shortest", "Partidas más cortas"),
    )
    if sort_by not in {value for value, _ in sort_options}:
        sort_by = "title"

    games = Game.objects.all()

    if query:
        games = games.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(mechanics__name__icontains=query)
        ).distinct()

    if category_id:
        games = games.filter(categories__id=category_id).distinct()

    if price_min:
        try:
            games = games.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            games = games.filter(price__lte=float(price_max))
        except ValueError:
            pass

    if game_format == "mesa":
        games = games.filter(is_online=False)
    elif game_format == "online":
        games = games.filter(is_online=True)

    if sort_by == "best_selling":
        sales = (
            OrderLine.objects
            .filter(
                game_id=OuterRef("pk"),
                order__status__in=(Order.Status.PAID, Order.Status.SHIPPED),
            )
            .order_by()
            .values("game_id")
            .annotate(total=Sum("quantity"))
            .values("total")
        )
        games = games.annotate(
            sales_count=Coalesce(
                Subquery(sales, output_field=IntegerField()),
                Value(0),
            )
        ).order_by("-sales_count", "title")
    elif sort_by == "price_asc":
        games = games.order_by("price", "title")
    elif sort_by == "price_desc":
        games = games.order_by("-price", "title")
    elif sort_by == "favorites":
        games = games.annotate(
            favorite_count=Count(
                "libraries",
                filter=Q(libraries__favorite=True),
                distinct=True,
            )
        ).order_by("-favorite_count", "title")
    elif sort_by == "shortest":
        games = games.order_by("duration_minutes", "title")
    else:
        games = games.order_by("title")

    games = games[:12]

    return render(
        request,
        "home.html",
        {
            "query": query,
            "games": games,
            "categories": Category.objects.order_by("name"),
            "selected_category": category_id,
            "price_min": price_min,
            "price_max": price_max,
            "selected_format": game_format,
            "selected_sort": sort_by,
            "sort_options": sort_options,
        },
    )
  
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

        session = SesionSugerencia.objects.create(
            host=perfil,
            suggestion_type=criterios["tipo_sugerencia"],
            player_count=criterios["num_jugadores"],
            edad_minima_participante=criterios[
                "edad_minima_participante"
            ],
            dificultad_preferida=criterios["dificultad_preferida"],
            max_duration=criterios["duracion_max"],
            tematica=criterios["tematica"],
        )

        juegos = Juego.objects.filter(
            min_players__lte=criterios["num_jugadores"],
            max_players__gte=criterios["num_jugadores"],
            min_age__lte=criterios["edad_minima_participante"],
            duration_minutes__lte=criterios["duracion_max"],
        )

        if (
            criterios["tipo_sugerencia"]
            == SesionSugerencia.SuggestionType.LIBRARY
        ):
            juegos = juegos.filter(libraries__user_profile=perfil)

        if criterios["tematica"]:
            juegos = juegos.filter(categories=criterios["tematica"])

        candidatos = list(juegos.distinct())
        candidatos.sort(
            key=lambda juego: (
                abs(
                    juego.difficulty
                    - criterios["dificultad_preferida"]
                ),
                juego.duration_minutes,
                juego.title.lower(),
            )
        )
        recomendaciones = candidatos[:3]

        SesionJuegoPropuesto.objects.bulk_create(
            [
                SesionJuegoPropuesto(session=session, game=game)
                for game in recomendaciones
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