from django.db.models import Q

from .models import Category, Game, LibraryGame, Mechanic, UserProfile
from recommendations.implicit_factor_model import (
    train_implicit_factor_model,
)
from recommendations.hybrid_prototype import GameFeatures


def build_content_recommendations(user):
    favorites = Game.objects.filter(
        libraries__user_profile__user=user,
        libraries__favorite=True,
    )
    categories = Category.objects.filter(
        games__in=favorites,
    ).distinct()
    mechanics = Mechanic.objects.filter(
        games__in=favorites,
    ).distinct()

    return (
        Game.objects.filter(
            Q(categories__in=categories) |
            Q(mechanics__in=mechanics),
        )
        .exclude(
            id__in=favorites.values_list("id", flat=True),
        )
        .exclude(
            id__in=LibraryGame.objects.filter(
                user_profile__user=user,
            ).values_list("game_id", flat=True),
        )
        .distinct()
    )


def build_factor_model_recommendations(
    user,
    collaborative_profile_ids=None,
):
    profile = UserProfile.objects.filter(user=user).first()
    if profile is None:
        return []

    favorite_rows = LibraryGame.objects.filter(favorite=True)
    if collaborative_profile_ids is None:
        favorite_rows = favorite_rows.exclude(
            user_profile__user__username__startswith="test_",
        )
    else:
        favorite_rows = favorite_rows.filter(
            user_profile_id__in=collaborative_profile_ids,
        )

    favorites_by_user = {}
    for profile_id, game_id in favorite_rows.values_list(
        "user_profile_id",
        "game_id",
    ):
        favorites_by_user.setdefault(profile_id, set()).add(game_id)

    user_favorites = favorites_by_user.get(profile.id, set())
    if not user_favorites or len(favorites_by_user) < 2:
        return []

    games = Game.objects.prefetch_related("categories", "mechanics")
    game_features = {
        game.id: GameFeatures(
            title=game.title,
            categories=frozenset(category.id for category in game.categories.all()),
            mechanics=frozenset(mechanic.id for mechanic in game.mechanics.all()),
        )
        for game in games
    }
    if not game_features:
        return []
    all_game_ids = set(game_features)
    if not any(all_game_ids - favorite_ids for favorite_ids in favorites_by_user.values()):
        return []

    model = train_implicit_factor_model(
        favorites_by_user=favorites_by_user,
        games=game_features,
    )
    excluded_game_ids = set(
        LibraryGame.objects.filter(
            user_profile=profile,
        ).values_list("game_id", flat=True)
    )
    return model.recommend(
        profile.id,
        seen_game_ids=excluded_game_ids,
        limit=len(game_features),
    )


def build_personalised_recommendations(
    user,
    collaborative_profile_ids=None,
):
    content_recommendations = list(build_content_recommendations(user))
    if len(content_recommendations) >= 3:
        return content_recommendations

    if user.username.startswith("test_") and collaborative_profile_ids is None:
        return content_recommendations

    model_recommendations = build_factor_model_recommendations(
        user,
        collaborative_profile_ids=collaborative_profile_ids,
    )
    recommended_ids = {game.id for game in content_recommendations}
    games_by_id = Game.objects.in_bulk(model_recommendations)
    for game_id in model_recommendations:
        game = games_by_id.get(game_id)
        if game is None:
            continue
        if game.id not in recommended_ids:
            content_recommendations.append(game)
            recommended_ids.add(game.id)
            if len(content_recommendations) >= 3:
                break

    return content_recommendations
