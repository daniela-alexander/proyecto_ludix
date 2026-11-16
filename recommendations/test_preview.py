from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from juegos.models import Category, Game, LibraryGame, UserProfile
from recommendations.implicit_factor_model import train_implicit_factor_model


class RecommendationPreviewTests(TestCase):
    def setUp(self):
        self.shared_category = Category.objects.create(
            name="Strategy",
            slug="strategy-preview",
        )
        self.other_category = Category.objects.create(
            name="Arcade",
            slug="arcade-preview",
        )
        self.favorite = self.create_game("Favorite", self.shared_category)
        self.content_candidate = self.create_game(
            "Content candidate",
            self.shared_category,
        )
        self.collaborative_candidate = self.create_game(
            "Collaborative candidate",
            self.other_category,
        )
        self.outside_cohort_candidate = self.create_game(
            "Outside cohort candidate",
            Category.objects.create(
                name="Outside cohort",
                slug="outside-cohort-preview",
            ),
        )

        self.staff_user = User.objects.create_user(
            username="test_preview_staff",
            is_staff=True,
        )
        self.profile = UserProfile.objects.create(user=self.staff_user)
        LibraryGame.objects.create(
            user_profile=self.profile,
            game=self.favorite,
            favorite=True,
        )

        neighbor = User.objects.create_user(username="test_preview_neighbor")
        neighbor_profile = UserProfile.objects.create(user=neighbor)
        self.test_neighbor_profile = neighbor_profile
        LibraryGame.objects.create(
            user_profile=neighbor_profile,
            game=self.favorite,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=neighbor_profile,
            game=self.collaborative_candidate,
            favorite=True,
        )

        outside_user = User.objects.create_user(username="outside_preview_user")
        self.outside_profile = UserProfile.objects.create(user=outside_user)
        LibraryGame.objects.create(
            user_profile=self.outside_profile,
            game=self.favorite,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=self.outside_profile,
            game=self.outside_cohort_candidate,
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

    def test_staff_can_compare_current_and_hybrid_recommendations(self):
        self.client.force_login(self.staff_user)
        url = reverse("recommendation_preview")
        library_count = LibraryGame.objects.count()

        with patch(
            "juegos.recommendations.train_implicit_factor_model",
            wraps=train_implicit_factor_model,
        ) as train_model:
            response = self.client.get(url, {"profile": self.profile.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Content candidate")
        self.assertContains(response, "Collaborative candidate")
        self.assertNotContains(response, "outside_preview_user")
        trained_profile_ids = set(
            train_model.call_args.kwargs["favorites_by_user"]
        )
        self.assertEqual(
            trained_profile_ids,
            {self.profile.id, self.test_neighbor_profile.id},
        )
        self.assertEqual(
            [game.id for game in response.context["current_recommendations"]],
            [self.content_candidate.id],
        )
        ml_recommendation_ids = [
            game.id for game in response.context["ml_recommendations"]
        ]
        self.assertEqual(
            ml_recommendation_ids[:2],
            [self.content_candidate.id, self.collaborative_candidate.id],
        )
        self.assertEqual(LibraryGame.objects.count(), library_count)

    def test_non_staff_users_cannot_open_preview(self):
        user = User.objects.create_user(username="preview_regular_user")
        self.client.force_login(user)

        response = self.client.get(reverse("recommendation_preview"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))

    def test_invalid_profile_id_returns_not_found(self):
        self.client.force_login(self.staff_user)

        for profile_id in (
            "999999",
            "not-a-number",
            str(self.outside_profile.id),
        ):
            with self.subTest(profile_id=profile_id):
                response = self.client.get(
                    reverse("recommendation_preview"),
                    {"profile": profile_id},
                )
                self.assertEqual(response.status_code, 404)
