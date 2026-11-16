from django.contrib.auth.models import User
from django.test import TestCase

from juegos.models import Category, Game, LibraryGame, Mechanic, UserProfile
from recommendations.hybrid_prototype import GameFeatures, recommend_for_user
from recommendations.implicit_factor_model import train_implicit_factor_model
from recommendations.offline_evaluation import (
    evaluate_factor_model_holdout,
    evaluate_favorite_holdout,
)


class FavoriteHoldoutEvaluationTests(TestCase):
    def setUp(self):
        strategy = Category.objects.create(name="Strategy", slug="strategy")
        abstract = Category.objects.create(name="Abstract", slug="abstract")
        arcade = Category.objects.create(name="Arcade", slug="arcade")
        cooperation = Category.objects.create(
            name="Cooperation",
            slug="cooperation",
        )
        pattern_building = Mechanic.objects.create(
            name="Pattern building",
            slug="pattern-building",
        )
        area_control = Mechanic.objects.create(
            name="Area control",
            slug="area-control",
        )
        cooperation_mechanic = Mechanic.objects.create(
            name="Cooperation",
            slug="cooperation",
        )

        category_by_title = {
            "pizza": strategy,
            "pasta": strategy,
            "Catan": strategy,
            "Carcassonne": abstract,
            "Love letter": strategy,
            "Dixit": arcade,
            "Lunatic": arcade,
            "Catan 2": strategy,
            "El Ahorcado": strategy,
            "Mahjong": arcade,
            "Monopoly": strategy,
            "Azul": cooperation,
        }
        mechanics_by_title = {
            "El Ahorcado": [pattern_building],
            "Mahjong": [pattern_building],
            "Monopoly": [area_control],
            "Azul": [cooperation_mechanic],
        }
        games_by_title = {}
        for title, category in category_by_title.items():
            game = Game.objects.create(
                title=title,
                min_players=1,
                max_players=4,
                duration_minutes=60,
                min_age=8,
                difficulty=3,
            )
            game.categories.add(category)
            game.mechanics.add(*mechanics_by_title.get(title, []))
            games_by_title[title] = game

        favorites_by_username = {
            "test_estrategia_1": ["Catan", "Carcassonne", "Azul"],
            "test_estrategia_2": ["Catan", "Carcassonne", "Azul", "Dixit"],
            "test_estrategia_3": ["Catan", "Carcassonne", "Azul", "Love letter"],
            "test_arcade_1": ["Dixit", "Lunatic", "Mahjong"],
            "test_arcade_2": [
                "Dixit",
                "Lunatic",
                "Mahjong",
                "El Ahorcado",
            ],
            "test_arcade_3": ["Dixit", "Lunatic", "Mahjong", "Monopoly"],
        }
        self.favorites_by_user = {}
        for username, titles in favorites_by_username.items():
            user = User.objects.create_user(username=username)
            profile = UserProfile.objects.create(user=user)
            favorite_ids = set()
            for title in titles:
                game = games_by_title[title]
                LibraryGame.objects.create(
                    user_profile=profile,
                    game=game,
                    favorite=True,
                )
                favorite_ids.add(game.id)
            self.favorites_by_user[profile.id] = frozenset(favorite_ids)

        self.user = User.objects.get(username="test_estrategia_1")
        self.non_favorite_library_game = games_by_title["pizza"]
        LibraryGame.objects.create(
            user_profile=self.user.profile,
            game=self.non_favorite_library_game,
            favorite=False,
        )

        self.games = {
            game.id: GameFeatures(
                title=game.title,
                categories=frozenset(game.categories.values_list("id", flat=True)),
                mechanics=frozenset(game.mechanics.values_list("id", flat=True)),
            )
            for game in games_by_title.values()
        }

    def test_hybrid_holdout_comparison_is_reproducible(self):
        comparison = evaluate_favorite_holdout(
            favorites_by_user=self.favorites_by_user,
            games=self.games,
        )

        self.assertEqual(comparison.test_cases, 22)
        self.assertEqual(comparison.content.top_k_hits, 8)
        self.assertEqual(comparison.content.candidate_hits, 12)
        self.assertEqual(comparison.content.nonempty_lists, 21)
        self.assertEqual(comparison.collaborative.top_k_hits, 18)
        self.assertEqual(comparison.collaborative.candidate_hits, 18)
        self.assertEqual(comparison.collaborative.nonempty_lists, 22)
        self.assertEqual(comparison.hybrid.top_k_hits, 10)
        self.assertEqual(comparison.hybrid.candidate_hits, 14)
        self.assertEqual(comparison.hybrid.nonempty_lists, 22)
        self.assertEqual(comparison.hybrid_fallback_cases, 7)
        self.assertTrue(comparison.hybrid_preserves_content_top_k)

    def test_holdout_requires_multiple_favorites(self):
        user_id, favorite_ids = next(iter(self.favorites_by_user.items()))
        only_one_favorite = {user_id: frozenset([next(iter(favorite_ids))])}

        with self.assertRaisesMessage(
            ValueError,
            "At least one user must have two or more favorites",
        ):
            evaluate_favorite_holdout(only_one_favorite, self.games)

    def test_top_k_must_be_positive(self):
        with self.assertRaisesMessage(ValueError, "top_k must be at least 1"):
            evaluate_favorite_holdout(self.favorites_by_user, self.games, top_k=0)

    def test_factor_model_trains_and_evaluates_held_out_favorites(self):
        evaluation = evaluate_factor_model_holdout(
            favorites_by_user=self.favorites_by_user,
            games=self.games,
            epochs=10,
        )

        self.assertEqual(evaluation.test_cases, 22)
        self.assertEqual(evaluation.training_runs, 22)
        self.assertGreater(evaluation.training_steps, 0)
        self.assertGreaterEqual(evaluation.top_k_hits, 0)
        self.assertLessEqual(evaluation.top_k_hits, evaluation.test_cases)
        self.assertGreaterEqual(evaluation.candidate_hits, 0)
        self.assertLessEqual(evaluation.candidate_hits, evaluation.test_cases)
        self.assertEqual(evaluation.nonempty_lists, evaluation.test_cases)

    def test_factor_model_is_reproducible_and_excludes_seen_favorites(self):
        first_model = train_implicit_factor_model(
            self.favorites_by_user,
            self.games,
            epochs=10,
            random_seed=29,
        )
        second_model = train_implicit_factor_model(
            self.favorites_by_user,
            self.games,
            epochs=10,
            random_seed=29,
        )
        user_id, favorite_ids = next(iter(self.favorites_by_user.items()))

        first_recommendations = first_model.recommend(
            user_id,
            favorite_ids,
            limit=3,
        )
        second_recommendations = second_model.recommend(
            user_id,
            favorite_ids,
            limit=3,
        )

        self.assertEqual(first_recommendations, second_recommendations)
        self.assertTrue(set(first_recommendations).isdisjoint(favorite_ids))
        self.assertEqual(first_model.training_steps, second_model.training_steps)

    def test_explicit_dislikes_are_trained_as_negative_feedback(self):
        games = {
            1: GameFeatures("Favorite", frozenset(), frozenset()),
            2: GameFeatures("Disliked", frozenset(), frozenset()),
            3: GameFeatures("Unseen", frozenset(), frozenset()),
        }
        model = train_implicit_factor_model(
            favorites_by_user={1: frozenset({1})},
            games=games,
            epochs=100,
            ignored_game_ids_by_user={1: frozenset({3})},
            disliked_game_ids_by_user={1: frozenset({2})},
        )

        self.assertGreater(model.score(1, 3), model.score(1, 2))

    def test_database_prototype_is_read_only_and_excludes_library_games(self):
        library_count = LibraryGame.objects.filter(
            user_profile=self.user.profile,
        ).count()

        recommendations = recommend_for_user(self.user.id)

        self.assertNotIn(self.non_favorite_library_game.id, recommendations)
        self.assertTrue(
            self.favorites_by_user[self.user.profile.id].isdisjoint(
                recommendations
            )
        )
        self.assertEqual(
            LibraryGame.objects.filter(user_profile=self.user.profile).count(),
            library_count,
        )
