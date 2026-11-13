from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from juegos.models import Category, Game, LibraryGame, Mechanic, UserProfile
from juegos.models import Wishlist
from recommendations.models import RecommendationFeedback
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
        self.second_content_candidate = self.create_game(
            "Another content candidate",
            strategy,
        )
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

    def test_content_candidates_are_ranked_by_shared_attributes_then_title(self):
        cooperative = Mechanic.objects.create(name="Cooperative")
        self.favorite.mechanics.add(cooperative)
        self.content_candidate.mechanics.add(cooperative)
        mechanic_candidate = Game.objects.create(
            title="Mechanic candidate",
            min_players=1,
            max_players=4,
            duration_minutes=60,
            min_age=8,
            difficulty=3,
        )
        mechanic_candidate.mechanics.add(cooperative)

        response = self.client.post(
            reverse("library_favorite", args=[self.favorite.id]),
            {"next": "/"},
        )

        self.assertRedirects(response, "/")
        recommendations = list(
            self.client.get("/").context["recomendados"]
        )
        recommendation_ids = [game.id for game in recommendations]

        self.assertEqual(
            recommendation_ids[:3],
            [
                self.content_candidate.id,
                self.second_content_candidate.id,
                mechanic_candidate.id,
            ],
        )

    def test_user_without_profile_gets_an_empty_recommendation_list(self):
        user_without_profile = User.objects.create_user(
            username="live_user_without_profile",
        )
        self.client.force_login(user_without_profile)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["recomendados"]), [])

    def test_dislike_is_saved_and_removed_from_recommendations_and_training(self):
        self.client.post(
            reverse("library_favorite", args=[self.favorite.id]),
            {"next": "/"},
        )
        dislike_response = self.client.post(
            reverse(
                "recommendation_dislike",
                args=[self.content_candidate.id],
            ),
            {"next": "/"},
        )

        self.assertRedirects(dislike_response, "/")
        self.assertTrue(
            RecommendationFeedback.objects.filter(
                user=self.user,
                game=self.content_candidate,
            ).exists()
        )

        with patch(
            "juegos.recommendations.train_implicit_factor_model",
            wraps=train_implicit_factor_model,
        ) as train_model:
            home = self.client.get("/")

        recommendations = list(home.context["recomendados"])
        self.assertNotIn(self.content_candidate, recommendations)
        disliked_ids = train_model.call_args.kwargs[
            "disliked_game_ids_by_user"
        ]
        self.assertIn(
            self.content_candidate.id,
            disliked_ids[self.profile.id],
        )

    def test_dislike_supports_the_existing_ajax_card_action(self):
        response = self.client.post(
            reverse(
                "recommendation_dislike",
                args=[self.content_candidate.id],
            ),
            {"next": "/"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"game_id": self.content_candidate.id})

    def test_favoriting_a_disliked_game_clears_its_negative_feedback(self):
        RecommendationFeedback.objects.create(
            user=self.user,
            game=self.content_candidate,
        )
        LibraryGame.objects.create(
            user_profile=self.profile,
            game=self.content_candidate,
            favorite=False,
        )

        self.client.post(
            reverse("library_favorite", args=[self.content_candidate.id]),
            {"next": "/"},
        )

        self.assertFalse(
            RecommendationFeedback.objects.filter(
                user=self.user,
                game=self.content_candidate,
            ).exists()
        )

    def test_recommendation_cards_show_a_round_dislike_button(self):
        self.client.post(
            reverse("library_favorite", args=[self.favorite.id]),
            {"next": "/"},
        )
        response = self.client.get("/")

        self.assertContains(
            response,
            'class="game-card-icon-button game-card-dislike-button"',
        )
        self.assertContains(response, 'aria-label="No me gusta"')
        self.assertContains(
            response,
            f'action="{reverse("wishlist_add", args=[self.content_candidate.id])}"',
        )
        self.assertContains(response, 'class="game-card-icon-button game-card-wishlist-button"')

    def test_recommendation_wishlist_button_saves_and_updates_its_state(self):
        self.client.post(
            reverse("library_favorite", args=[self.favorite.id]),
            {"next": "/"},
        )
        add_response = self.client.post(
            reverse("wishlist_add", args=[self.content_candidate.id]),
            {"next": "/"},
        )
        self.assertRedirects(add_response, "/")
        self.assertTrue(
            Wishlist.objects.filter(
                user_profile=self.profile,
                game=self.content_candidate,
            ).exists()
        )

        response = self.client.get("/")

        self.assertEqual(
            response.context["wishlist_game_ids"],
            {self.content_candidate.id},
        )
        self.assertContains(
            response,
            f'action="{reverse("wishlist_remove", args=[self.content_candidate.id])}"',
        )
        self.assertContains(response, 'aria-pressed="true"')

    def test_game_detail_can_set_and_clear_dislike(self):
        LibraryGame.objects.create(
            user_profile=self.profile,
            game=self.content_candidate,
            favorite=False,
        )
        detail_url = reverse("game_detail", args=[self.content_candidate.id])
        dislike_url = reverse(
            "recommendation_dislike",
            args=[self.content_candidate.id],
        )
        remove_url = reverse(
            "recommendation_feedback_remove",
            args=[self.content_candidate.id],
        )

        response = self.client.get(detail_url)
        self.assertContains(response, f'action="{dislike_url}"')
        self.assertContains(response, 'aria-label="No me gusta"')
        self.assertContains(response, 'aria-pressed="false"')

        self.client.post(dislike_url, {"next": detail_url})
        response = self.client.get(detail_url)
        self.assertContains(response, f'action="{remove_url}"')
        self.assertContains(response, 'aria-label="Quitar de No me gusta"')
        self.assertContains(response, 'aria-pressed="true"')

        remove_response = self.client.post(
            remove_url,
            {"next": detail_url},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(
            remove_response.json(),
            {"game_id": self.content_candidate.id},
        )
        self.assertFalse(
            RecommendationFeedback.objects.filter(
                user=self.user,
                game=self.content_candidate,
            ).exists()
        )
        self.assertContains(self.client.get(detail_url), f'action="{dislike_url}"')

    def test_profile_lists_disliked_games_and_can_remove_feedback(self):
        RecommendationFeedback.objects.create(
            user=self.user,
            game=self.content_candidate,
        )
        profile_url = reverse("profile")
        remove_url = reverse(
            "recommendation_feedback_remove",
            args=[self.content_candidate.id],
        )

        response = self.client.get(profile_url)
        self.assertContains(response, "Juegos que no me gustan")
        self.assertContains(response, self.content_candidate.title)
        self.assertContains(response, f'action="{remove_url}"')

        remove_response = self.client.post(
            remove_url,
            {"next": profile_url},
        )

        self.assertRedirects(remove_response, profile_url)
        self.assertFalse(
            RecommendationFeedback.objects.filter(
                user=self.user,
                game=self.content_candidate,
            ).exists()
        )
        self.assertContains(
            self.client.get(profile_url),
            "Todavía no has marcado juegos que no te gusten.",
        )
