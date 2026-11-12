from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from juegos.models import Category, Game, LibraryGame, UserProfile
from recommendations.implicit_factor_model import train_implicit_factor_model


class LiveHybridRecommendationTests(TestCase):
    def setUp(self):
        strategy = Category.objects.create(
            name="Strategy",
            slug="live-strategy",
        )
        arcade = Category.objects.create(
            name="Arcade",
            slug="live-arcade",
        )
        self.favorite = self.create_game("Favorite", strategy)
        self.content_candidate = self.create_game("Content candidate", strategy)
        self.real_collaborative_candidate = self.create_game(
            "Real collaborative candidate",
            arcade,
        )
        self.test_collaborative_candidate = self.create_game(
            "Test collaborative candidate",
            arcade,
        )

        self.user = User.objects.create_user(username="live_target")
        self.profile = UserProfile.objects.create(user=self.user)
        LibraryGame.objects.create(
            user_profile=self.profile,
            game=self.favorite,
            favorite=False,
        )
        self.client.force_login(self.user)

        real_neighbor = User.objects.create_user(username="live_neighbor")
        real_neighbor_profile = UserProfile.objects.create(user=real_neighbor)
        LibraryGame.objects.create(
            user_profile=real_neighbor_profile,
            game=self.favorite,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=real_neighbor_profile,
            game=self.real_collaborative_candidate,
            favorite=True,
        )

        test_neighbor = User.objects.create_user(username="test_synthetic_neighbor")
        test_neighbor_profile = UserProfile.objects.create(user=test_neighbor)
        self.test_neighbor_profile_id = test_neighbor_profile.id
        LibraryGame.objects.create(
            user_profile=test_neighbor_profile,
            game=self.favorite,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=test_neighbor_profile,
            game=self.test_collaborative_candidate,
            favorite=True,
        )

    @staticmethod
    def create_game(title, category):
        game = Game.objects.create(
            title=title,
            min_players=1,
            max_players=4,
            duration_minutes=60,
            min_age=8,
            difficulty=3,
        )
        game.categories.add(category)
        return game

    def test_new_favorite_is_used_on_the_next_home_request(self):
        response = self.client.post(
            reverse("library_favorite", args=[self.favorite.id]),
            {"next": "/"},
        )

        self.assertRedirects(response, "/")
        with patch(
            "juegos.recommendations.train_implicit_factor_model",
            wraps=train_implicit_factor_model,
        ) as train_model:
            home = self.client.get("/")

        recommendations = list(home.context["recomendados"])
        recommendation_ids = [game.id for game in recommendations]

        self.assertIn(self.content_candidate.id, recommendation_ids)
        self.assertIn(self.real_collaborative_candidate.id, recommendation_ids)
        self.assertNotIn(self.favorite.id, recommendation_ids)
        training_favorites = train_model.call_args.kwargs["favorites_by_user"]
        training_game_ids = set().union(*training_favorites.values())
        self.assertIn(self.favorite.id, training_favorites[self.profile.id])
        self.assertNotIn(
            self.test_collaborative_candidate.id,
            training_game_ids,
        )
        self.assertNotIn(
            self.test_neighbor_profile_id,
            training_favorites,
        )

    def test_user_without_profile_gets_an_empty_recommendation_list(self):
        user_without_profile = User.objects.create_user(
            username="live_user_without_profile",
        )
        self.client.force_login(user_without_profile)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["recomendados"]), [])
