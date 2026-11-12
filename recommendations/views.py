from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from juegos.models import Game, LibraryGame, UserProfile
from juegos.recommendations import (
    build_content_recommendations,
    build_personalised_recommendations,
)


def _build_filters(request):
    players = int(request.GET.get("players", 2))
    duration = int(request.GET.get("duration", 120))
    age = int(request.GET.get("age", 8))
    difficulty = Decimal(request.GET.get("difficulty", "4.00"))

    filters = {
        "min_players__lte": players,
        "max_players__gte": players,
        "duration_minutes__lte": duration,
        "min_age__lte": age,
        "difficulty__lte": difficulty,
    }
    return filters


@login_required
def recommendation_dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    excluded_ids = set(
        LibraryGame.objects.filter(user_profile=user_profile).values_list("game_id", flat=True)
    )

    queryset = Game.objects.filter(**_build_filters(request)).exclude(id__in=excluded_ids)[:10]

    payload = {
        "user": request.user.username,
        "recommendations": [
            {
                "id": game.id,
                "titulo": game.title,
                "descripcion": game.description,
                "jugadores": f"{game.min_players}-{game.max_players}",
                "duracion_minutos": game.duration_minutes,
                "edad_minima": game.min_age,
                "dificultad": str(game.difficulty),
                "precio": str(game.price),
            }
            for game in queryset
        ],
    }
    return JsonResponse(payload)


@staff_member_required
def recommendation_preview(request):
    profiles = UserProfile.objects.filter(
        user__username__startswith="test_",
    ).select_related("user").order_by("user__username")
    collaborative_profile_ids = set(profiles.values_list("id", flat=True))
    selected_profile_id = request.GET.get("profile")

    if selected_profile_id:
        try:
            profile_id = int(selected_profile_id)
        except ValueError:
            profile_id = None

        selected_profile = (
            profiles.filter(pk=profile_id).first()
            if profile_id is not None
            else None
        )
        if selected_profile is None:
            return render(
                request,
                "recommendations/preview.html",
                {
                    "profiles": profiles,
                    "selected_profile": None,
                    "current_recommendations": [],
                    "hybrid_recommendations": [],
                    "invalid_profile": True,
                },
                status=404,
            )
    else:
        selected_profile = profiles.filter(
            user=request.user,
            library__favorite=True,
        ).first()
        if selected_profile is None:
            selected_profile = profiles.filter(library__favorite=True).first()
        if selected_profile is None:
            selected_profile = profiles.filter(user=request.user).first()

    current_recommendations = []
    ml_recommendations = []
    if selected_profile is not None:
        current_recommendations = list(
            build_content_recommendations(selected_profile.user)
        )
        ml_recommendations = build_personalised_recommendations(
            selected_profile.user,
            collaborative_profile_ids=collaborative_profile_ids,
        )

    return render(
        request,
        "recommendations/preview.html",
        {
            "profiles": profiles,
            "selected_profile": selected_profile,
            "current_recommendations": current_recommendations,
            "ml_recommendations": ml_recommendations,
            "invalid_profile": False,
        },
    )
