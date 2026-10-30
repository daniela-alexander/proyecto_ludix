from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from .models import (
    BibliotecaJuego,
    Juego,
    PerfilUsuario,
    SesionJuegoPropuesto,
    SesionSugerencia,
)
# este ultimo añadido por daniela para configurar la paginación
from .filters import GameFilter, JuegoFilter
from .models import Category, Game, LibraryGame, Order, OrderLine, Wishlist
from .serializers import GameSerializer, JuegoSerializer
from .pagination import GamePagination, JuegoPagination

from django.contrib.auth.decorators import login_required
from .forms import (
    EDAD_FILTRO_MAYOR_DE_18,
    EDAD_MAYOR_DE_18,
    SugerenciaForm,
)


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


def game_detail(request, game_id):
    game = get_object_or_404(
        Game.objects.prefetch_related("categories", "mechanics"),
        pk=game_id,
    )
    library_entry = None
    is_in_wishlist = False
    if request.user.is_authenticated:
        library_entry = LibraryGame.objects.filter(
            user_profile__user=request.user,
            game=game,
        ).first()
        if library_entry is None:
            is_in_wishlist = Wishlist.objects.filter(
                user_profile__user=request.user,
                game=game,
            ).exists()

    return render(
        request,
        "juegos/game_detail.html",
        {
            "game": game,
            "is_in_library": library_entry is not None,
            "is_favorite": library_entry.favorite if library_entry else False,
            "is_in_wishlist": is_in_wishlist,
        },
    )


def game_shop(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render(request, "juegos/game_shop.html", {"game": game})


def home(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category")
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    game_format = request.GET.get("format", "").strip()
    sort_by = request.GET.get("sort", "title")
    sort_options = (
        ("title", _("Orden alfabético")),
        ("best_selling", _("Más vendidos")),
        ("price_asc", _("Precio: menor a mayor")),
        ("price_desc", _("Precio: mayor a menor")),
        ("favorites", _("Más favoritos")),
        ("shortest", _("Partidas más cortas")),
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

    games = list(games[:12])
    library_game_ids = set()
    favorite_game_ids = set()
    wishlist_game_ids = set()
    if request.user.is_authenticated:
        library_entries = list(
            LibraryGame.objects.filter(
                user_profile__user=request.user,
                game_id__in=[game.id for game in games],
            ).values_list("game_id", "favorite")
        )
        library_game_ids = {game_id for game_id, _ in library_entries}
        favorite_game_ids = {
            game_id for game_id, favorite in library_entries if favorite
        }
        wishlist_game_ids = set(
            Wishlist.objects.filter(
                user_profile__user=request.user,
                game_id__in=[game.id for game in games],
            ).values_list("game_id", flat=True)
        )

    return render(
        request,
        "home.html",
        {
            "query": query,
            "games": games,
            "library_game_ids": library_game_ids,
            "favorite_game_ids": favorite_game_ids,
            "wishlist_game_ids": wishlist_game_ids,
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
    suggestion_session = None
    library_game_ids = set()
    wishlist_game_ids = set()

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
        suggestion_session = session

        edad_participante = criterios["edad_minima_participante"]
        if edad_participante == EDAD_MAYOR_DE_18:
            edad_participante = EDAD_FILTRO_MAYOR_DE_18

        juegos = Juego.objects.filter(
            min_players__lte=criterios["num_jugadores"],
            max_players__gte=criterios["num_jugadores"],
            min_age__lte=edad_participante,
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
    elif request.method == "GET" and request.GET.get("session"):
        suggestion_session = get_object_or_404(
            SesionSugerencia.objects.filter(host__user=request.user),
            pk=request.GET["session"],
        )
        recomendaciones = [
            proposal.game
            for proposal in suggestion_session.proposed_games.select_related(
                "game"
            ).order_by("id")
        ]
        form = SugerenciaForm(
            initial={
                "tipo_sugerencia": suggestion_session.suggestion_type,
                "num_jugadores": suggestion_session.player_count,
                "edad_minima_participante": (
                    suggestion_session.edad_minima_participante
                ),
                "duracion_max": suggestion_session.max_duration,
                "dificultad_preferida": (
                    suggestion_session.dificultad_preferida
                ),
                "tematica": suggestion_session.tematica_id,
            }
        )
        enviado = True

    if recomendaciones:
        recommended_game_ids = [game.id for game in recomendaciones]
        library_game_ids = set(
            LibraryGame.objects.filter(
                user_profile__user=request.user,
                game_id__in=recommended_game_ids,
            ).values_list("game_id", flat=True)
        )
        wishlist_game_ids = set(
            Wishlist.objects.filter(
                user_profile__user=request.user,
                game_id__in=recommended_game_ids,
            ).values_list("game_id", flat=True)
        )

    return render(
        request,
        "juegos/sugerencia_form.html",
        {
            "form": form,
            "enviado": enviado,
            "recomendaciones": recomendaciones,
            "suggestion_session": suggestion_session,
            "library_game_ids": library_game_ids,
            "wishlist_game_ids": wishlist_game_ids,
            "edad_mayor_de_18": EDAD_MAYOR_DE_18,
        },
    )