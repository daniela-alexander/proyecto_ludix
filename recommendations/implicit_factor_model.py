"""Small, in-memory BPR model for recommendation experiments.

Unobserved games are sampled as ranking negatives; this does not mean users
explicitly disliked them. This model is experimental; the web flow trains it
when content-based recommendations do not provide enough candidates.
"""

import math
import random
from dataclasses import dataclass
from typing import AbstractSet, Mapping

from recommendations.hybrid_prototype import GameFeatures


@dataclass(frozen=True)
class ImplicitFactorModel:
    user_factors: Mapping[int, tuple[float, ...]]
    game_factors: Mapping[int, tuple[float, ...]]
    games: Mapping[int, GameFeatures]
    training_steps: int

    def score(self, user_id: int, game_id: int) -> float:
        user_vector = self.user_factors.get(user_id)
        game_vector = self.game_factors.get(game_id)
        if user_vector is None or game_vector is None:
            return 0.0
        return sum(user_value * game_value for user_value, game_value in zip(
            user_vector,
            game_vector,
        ))

    def recommend(
        self,
        user_id: int,
        seen_game_ids: AbstractSet[int],
        limit: int = 3,
    ) -> list[int]:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if user_id not in self.user_factors:
            return []

        candidates = (
            game_id
            for game_id in self.game_factors
            if game_id not in seen_game_ids
        )
        return sorted(
            candidates,
            key=lambda game_id: (
                -self.score(user_id, game_id),
                self.games[game_id].title.casefold(),
                game_id,
            ),
        )[:limit]


def train_implicit_factor_model(
    favorites_by_user: Mapping[int, AbstractSet[int]],
    games: Mapping[int, GameFeatures],
    factors: int = 4,
    epochs: int = 100,
    learning_rate: float = 0.03,
    regularization: float = 0.02,
    random_seed: int = 17,
    ignored_game_ids_by_user: Mapping[int, AbstractSet[int]] | None = None,
    disliked_game_ids_by_user: Mapping[int, AbstractSet[int]] | None = None,
) -> ImplicitFactorModel:
    if factors < 1:
        raise ValueError("factors must be at least 1")
    if epochs < 1:
        raise ValueError("epochs must be at least 1")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if regularization < 0:
        raise ValueError("regularization cannot be negative")

    unknown_games = set().union(*favorites_by_user.values()) - games.keys()
    if unknown_games:
        raise ValueError(f"Unknown game IDs in favorites: {sorted(unknown_games)}")

    randomizer = random.Random(random_seed)
    all_game_ids = tuple(games)
    user_factors = {
        user_id: [
            randomizer.uniform(-0.05, 0.05)
            for _ in range(factors)
        ]
        for user_id in favorites_by_user
    }
    game_factors = {
        game_id: [
            randomizer.uniform(-0.05, 0.05)
            for _ in range(factors)
        ]
        for game_id in all_game_ids
    }

    ignored_by_user = ignored_game_ids_by_user or {}
    disliked_by_user = disliked_game_ids_by_user or {}
    training_pairs = []
    for user_id, favorite_ids in favorites_by_user.items():
        negatives = tuple(
            game_id
            for game_id in all_game_ids
            if game_id not in favorite_ids
            and game_id not in ignored_by_user.get(user_id, frozenset())
        )
        if negatives:
            explicit_negatives = (
                disliked_by_user.get(user_id, frozenset())
                & set(negatives)
            )
            for favorite_id in favorite_ids:
                training_pairs.append((user_id, favorite_id, negatives))
                training_pairs.extend(
                    (user_id, favorite_id, (disliked_id,))
                    for disliked_id in explicit_negatives
                )
    if not training_pairs:
        raise ValueError(
            "Training requires at least one favorite and one unobserved game"
        )

    training_steps = 0
    for _ in range(epochs):
        randomizer.shuffle(training_pairs)
        for user_id, positive_id, negatives in training_pairs:
            negative_id = randomizer.choice(negatives)
            user_vector = user_factors[user_id]
            positive_vector = game_factors[positive_id]
            negative_vector = game_factors[negative_id]
            margin = sum(
                user_value * (positive_value - negative_value)
                for user_value, positive_value, negative_value in zip(
                    user_vector,
                    positive_vector,
                    negative_vector,
                )
            )
            pairwise_gradient = 1 / (
                1 + math.exp(max(-60.0, min(60.0, margin)))
            )
            previous_user_vector = tuple(user_vector)
            for index in range(factors):
                user_vector[index] += learning_rate * (
                    pairwise_gradient
                    * (positive_vector[index] - negative_vector[index])
                    - regularization * user_vector[index]
                )
                positive_vector[index] += learning_rate * (
                    pairwise_gradient * previous_user_vector[index]
                    - regularization * positive_vector[index]
                )
                negative_vector[index] += learning_rate * (
                    -pairwise_gradient * previous_user_vector[index]
                    - regularization * negative_vector[index]
                )
            training_steps += 1

    return ImplicitFactorModel(
        user_factors={
            user_id: tuple(vector)
            for user_id, vector in user_factors.items()
        },
        game_factors={
            game_id: tuple(vector)
            for game_id, vector in game_factors.items()
        },
        games=games,
        training_steps=training_steps,
    )
