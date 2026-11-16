"""Hybrid recommendation prototype based on content and user similarities."""

from collections import defaultdict
from dataclasses import dataclass
from typing import AbstractSet, Mapping

from juegos.models import Game, LibraryGame, UserProfile


@dataclass(frozen=True)
class GameFeatures:
    title: str
    categories: AbstractSet[int]
    mechanics: AbstractSet[int]


def rank_content_candidates(
    favorite_game_ids: AbstractSet[int],
    games: Mapping[int, GameFeatures],
    excluded_game_ids: AbstractSet[int] = frozenset(),
) -> list[int]:
    favorite_categories = set()
    favorite_mechanics = set()
    for game_id in favorite_game_ids:
        favorite_categories.update(games[game_id].categories)
        favorite_mechanics.update(games[game_id].mechanics)

    excluded_ids = favorite_game_ids | excluded_game_ids
    scored_candidates = []
    for game_id, features in games.items():
        if game_id in excluded_ids:
            continue

        score = len(features.categories & favorite_categories)
        score += len(features.mechanics & favorite_mechanics)
        if score:
            scored_candidates.append((game_id, score, features.title.casefold()))

    scored_candidates.sort(key=lambda candidate: (-candidate[1], candidate[2], candidate[0]))
    return [game_id for game_id, _, _ in scored_candidates]


def rank_collaborative_candidates(
    user_id: int,
    favorite_game_ids: AbstractSet[int],
    favorites_by_user: Mapping[int, AbstractSet[int]],
    games: Mapping[int, GameFeatures],
    excluded_game_ids: AbstractSet[int] = frozenset(),
) -> list[int]:
    support = defaultdict(float)
    for other_user_id, other_favorites in favorites_by_user.items():
        if other_user_id == user_id:
            continue

        intersection = favorite_game_ids & other_favorites
        if not intersection:
            continue

        similarity = len(intersection) / len(favorite_game_ids | other_favorites)
        for game_id in other_favorites - favorite_game_ids - excluded_game_ids:
            support[game_id] += similarity

    return sorted(
        support,
        key=lambda game_id: (
            -support[game_id],
            games[game_id].title.casefold(),
            game_id,
        ),
    )


def recommend_hybrid_candidates(
    user_id: int,
    favorite_game_ids: AbstractSet[int],
    favorites_by_user: Mapping[int, AbstractSet[int]],
    games: Mapping[int, GameFeatures],
    minimum_results: int = 3,
    excluded_game_ids: AbstractSet[int] = frozenset(),
) -> tuple[list[int], bool]:
    if minimum_results < 1:
        raise ValueError("minimum_results must be at least 1")

    content = rank_content_candidates(
        favorite_game_ids,
        games,
        excluded_game_ids,
    )
    if len(content) >= minimum_results:
        return content, False

    hybrid = list(content)
    hybrid_ids = set(hybrid)
    collaborative = rank_collaborative_candidates(
        user_id,
        favorite_game_ids,
        favorites_by_user,
        games,
        excluded_game_ids,
    )
    for game_id in collaborative:
        if game_id not in hybrid_ids:
            hybrid.append(game_id)
            hybrid_ids.add(game_id)
            if len(hybrid) >= minimum_results:
                break

    return hybrid, True


def recommend_for_user(
    user_id: int,
    minimum_results: int = 3,
    collaborative_profile_ids: AbstractSet[int] | None = None,
) -> list[int]:
    """Calculate recommendations for a Django auth user without writing data."""
    if minimum_results < 1:
        raise ValueError("minimum_results must be at least 1")

    profile = UserProfile.objects.get(user_id=user_id)
    favorite_rows = LibraryGame.objects.filter(favorite=True)
    if collaborative_profile_ids is not None:
        favorite_rows = favorite_rows.filter(
            user_profile_id__in=collaborative_profile_ids,
        )
    favorite_rows = favorite_rows.values_list(
        "user_profile_id",
        "game_id",
    )
    favorites_by_user = defaultdict(set)
    for profile_id, game_id in favorite_rows:
        favorites_by_user[profile_id].add(game_id)

    user_favorites = set(
        LibraryGame.objects.filter(
            user_profile=profile,
            favorite=True,
        ).values_list("game_id", flat=True)
    )
    if not user_favorites:
        return []
    favorites_by_user[profile.id] = user_favorites

    games = Game.objects.prefetch_related("categories", "mechanics")
    game_features = {
        game.id: GameFeatures(
            title=game.title,
            categories=frozenset(category.id for category in game.categories.all()),
            mechanics=frozenset(mechanic.id for mechanic in game.mechanics.all()),
        )
        for game in games
    }
    excluded_game_ids = set(
        LibraryGame.objects.filter(user_profile=profile).values_list(
            "game_id",
            flat=True,
        )
    )
    recommendations, _ = recommend_hybrid_candidates(
        user_id=profile.id,
        favorite_game_ids=user_favorites,
        favorites_by_user=favorites_by_user,
        games=game_features,
        minimum_results=minimum_results,
        excluded_game_ids=excluded_game_ids,
    )
    return recommendations
