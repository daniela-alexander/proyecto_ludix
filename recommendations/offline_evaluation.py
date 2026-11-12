"""Offline strategies for repeatable holdout evaluation.

This module is intentionally not used by the live recommendation view.
"""

from dataclasses import dataclass
from typing import AbstractSet, Mapping

from recommendations.hybrid_prototype import (
    GameFeatures,
    rank_content_candidates,
    rank_collaborative_candidates,
    recommend_hybrid_candidates,
)
from recommendations.implicit_factor_model import train_implicit_factor_model


@dataclass(frozen=True)
class RecommendationMetrics:
    top_k_hits: int
    candidate_hits: int
    nonempty_lists: int


@dataclass(frozen=True)
class OfflineComparison:
    test_cases: int
    content: RecommendationMetrics
    collaborative: RecommendationMetrics
    hybrid: RecommendationMetrics
    hybrid_fallback_cases: int
    hybrid_preserves_content_top_k: bool


@dataclass(frozen=True)
class FactorModelEvaluation:
    test_cases: int
    top_k_hits: int
    candidate_hits: int
    nonempty_lists: int
    training_runs: int
    training_steps: int


def evaluate_factor_model_holdout(
    favorites_by_user: Mapping[int, AbstractSet[int]],
    games: Mapping[int, GameFeatures],
    top_k: int = 3,
    factors: int = 4,
    epochs: int = 100,
    random_seed: int = 17,
) -> FactorModelEvaluation:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    heldout_cases = [
        (user_id, favorite_game_id)
        for user_id, favorite_game_ids in favorites_by_user.items()
        if len(favorite_game_ids) >= 2
        for favorite_game_id in favorite_game_ids
    ]
    if not heldout_cases:
        raise ValueError("At least one user must have two or more favorites")

    top_k_hits = 0
    candidate_hits = 0
    nonempty_lists = 0
    training_steps = 0

    for user_id, heldout_game_id in heldout_cases:
        known_favorites = favorites_by_user[user_id] - {heldout_game_id}
        model = train_implicit_factor_model(
            favorites_by_user={
                other_user_id: (
                    other_favorites - {heldout_game_id}
                    if other_user_id == user_id
                    else other_favorites
                )
                for other_user_id, other_favorites in favorites_by_user.items()
            },
            games=games,
            factors=factors,
            epochs=epochs,
            random_seed=random_seed,
            ignored_game_ids_by_user={
                user_id: {heldout_game_id},
            },
        )
        recommendations = model.recommend(
            user_id,
            seen_game_ids=known_favorites,
            limit=len(games),
        )
        top_k_hits += heldout_game_id in recommendations[:top_k]
        candidate_hits += heldout_game_id in recommendations
        nonempty_lists += bool(recommendations)
        training_steps += model.training_steps

    return FactorModelEvaluation(
        test_cases=len(heldout_cases),
        top_k_hits=top_k_hits,
        candidate_hits=candidate_hits,
        nonempty_lists=nonempty_lists,
        training_runs=len(heldout_cases),
        training_steps=training_steps,
    )


def evaluate_favorite_holdout(
    favorites_by_user: Mapping[int, AbstractSet[int]],
    games: Mapping[int, GameFeatures],
    top_k: int = 3,
) -> OfflineComparison:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    heldout_cases = [
        (user_id, favorite_game_id)
        for user_id, favorite_game_ids in favorites_by_user.items()
        if len(favorite_game_ids) >= 2
        for favorite_game_id in favorite_game_ids
    ]
    if not heldout_cases:
        raise ValueError("At least one user must have two or more favorites")

    recommendations = {"content": [], "collaborative": [], "hybrid": []}
    targets = []
    fallback_cases = 0
    preserves_content_top_k = True

    for user_id, heldout_game_id in heldout_cases:
        known_favorites = favorites_by_user[user_id] - {heldout_game_id}
        targets.append(heldout_game_id)

        content = rank_content_candidates(known_favorites, games)
        collaborative = rank_collaborative_candidates(
            user_id,
            known_favorites,
            favorites_by_user,
            games,
        )
        hybrid, used_fallback = recommend_hybrid_candidates(
            user_id,
            known_favorites,
            favorites_by_user,
            games,
            minimum_results=top_k,
        )
        fallback_cases += used_fallback
        preserved_count = min(top_k, len(content))
        preserves_content_top_k &= hybrid[:preserved_count] == content[:preserved_count]

        recommendations["content"].append(content)
        recommendations["collaborative"].append(collaborative)
        recommendations["hybrid"].append(hybrid)

    def measure(strategy: str) -> RecommendationMetrics:
        results = recommendations[strategy]
        return RecommendationMetrics(
            top_k_hits=sum(
                target in result[:top_k]
                for target, result in zip(targets, results)
            ),
            candidate_hits=sum(
                target in result
                for target, result in zip(targets, results)
            ),
            nonempty_lists=sum(bool(result) for result in results),
        )

    return OfflineComparison(
        test_cases=len(heldout_cases),
        content=measure("content"),
        collaborative=measure("collaborative"),
        hybrid=measure("hybrid"),
        hybrid_fallback_cases=fallback_cases,
        hybrid_preserves_content_top_k=preserves_content_top_k,
    )
