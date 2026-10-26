from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import (
    Category,
    Game,
    LibraryGame,
    Mechanic,
    Order,
    OrderLine,
    UserProfile,
)


class GameApiSearchTests(TestCase):
    def setUp(self):
        self.category_action = Category.objects.create(name="Acción", slug="accion")
        self.category_strategy = Category.objects.create(name="Estrategia", slug="estrategia")
        self.mechanic_exploration = Mechanic.objects.create(name="Exploración", slug="exploracion")

        self.game_one = Game.objects.create(
            title="Prueba Ludix",
            description="Un juego de acción con mucha exploración.",
            min_players=1,
            max_players=4,
            duration_minutes=60,
            min_age=8,
            difficulty=4.5,
            price=19.99,
            stock=10,
            is_online=False,
        )
        self.game_one.categories.add(self.category_action)
        self.game_one.mechanics.add(self.mechanic_exploration)

        self.game_two = Game.objects.create(
            title="Cartas del reino",
            description="Juego de estrategia para partidas largas.",
            min_players=2,
            max_players=6,
            duration_minutes=90,
            min_age=12,
            difficulty=3.2,
            price=29.99,
            stock=5,
            is_online=True,
        )
        self.game_two.categories.add(self.category_strategy)

    def test_search_returns_matching_title(self):
        response = self.client.get("/api/games/?search=ludix")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Prueba Ludix")

    def test_category_filter_returns_only_matching_games(self):
        response = self.client.get(f"/api/games/?category={self.category_action.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Prueba Ludix")

    def test_home_filter_by_online_type(self):
        response = self.client.get("/?format=online")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cartas del reino")
        self.assertNotContains(response, "Prueba Ludix")

    def test_home_sorts_by_price(self):
        ascending = self.client.get("/?sort=price_asc")
        descending = self.client.get("/?sort=price_desc")

        self.assertEqual(
            [game.title for game in ascending.context["games"]],
            ["Prueba Ludix", "Cartas del reino"],
        )
        self.assertEqual(
            [game.title for game in descending.context["games"]],
            ["Cartas del reino", "Prueba Ludix"],
        )

    def test_home_sorts_by_paid_sales_quantity(self):
        profile = UserProfile.objects.create(user=User.objects.create_user("buyer"))
        paid_order = Order.objects.create(
            customer=profile,
            status=Order.Status.PAID,
            total=100,
        )
        pending_order = Order.objects.create(
            customer=profile,
            status=Order.Status.PENDING,
            total=100,
        )
        OrderLine.objects.create(
            order=paid_order,
            game=self.game_one,
            quantity=2,
            unit_price=self.game_one.price,
        )
        OrderLine.objects.create(
            order=paid_order,
            game=self.game_two,
            quantity=5,
            unit_price=self.game_two.price,
        )
        OrderLine.objects.create(
            order=pending_order,
            game=self.game_one,
            quantity=50,
            unit_price=self.game_one.price,
        )

        response = self.client.get("/?sort=best_selling")

        self.assertEqual(
            [game.title for game in response.context["games"]],
            ["Cartas del reino", "Prueba Ludix"],
        )

    def test_home_sorts_by_favorite_count(self):
        first_profile = UserProfile.objects.create(
            user=User.objects.create_user("first_fan")
        )
        second_profile = UserProfile.objects.create(
            user=User.objects.create_user("second_fan")
        )
        LibraryGame.objects.create(
            user_profile=first_profile,
            game=self.game_one,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=second_profile,
            game=self.game_one,
            favorite=True,
        )
        LibraryGame.objects.create(
            user_profile=first_profile,
            game=self.game_two,
            favorite=True,
        )

        response = self.client.get("/?sort=favorites")

        self.assertEqual(
            [game.title for game in response.context["games"]],
            ["Prueba Ludix", "Cartas del reino"],
        )


class LanguageSelectionTests(TestCase):
    def test_selected_language_is_applied_across_pages(self):
        self.client.post(
            "/i18n/setlang/",
            {"language": "en", "next": "/"},
        )

        home_response = self.client.get("/")
        websocket_response = self.client.get("/websocket-test/")

        self.assertContains(home_response, "Welcome to Ludix")
        self.assertContains(home_response, '<html lang="en">')
        self.assertContains(home_response, 'name="language"')
        self.assertContains(websocket_response, "Users online")
        self.assertContains(websocket_response, '<html lang="en">')
        self.assertContains(websocket_response, 'name="language"')

    def test_auth_and_profile_pages_follow_the_selected_language(self):
        self.client.post(
            reverse("set_language"),
            {"language": "ca", "next": "/"},
        )

        self.assertContains(
            self.client.get(reverse("login")),
            "Inicia la sessió a Ludix",
        )
        self.assertContains(
            self.client.get(reverse("register")),
            "Uneix-te a Ludix",
        )

        user = User.objects.create_user(username="languageuser")
        self.client.force_login(user)
        self.assertContains(
            self.client.get(reverse("profile")),
            "EL TEU ESPAI PERSONAL",
        )

    def test_language_switcher_offers_all_requested_languages(self):
        response = self.client.get("/")

        for language in ("es", "ca", "en", "it"):
            with self.subTest(language=language):
                self.assertContains(response, f'value="{language}"')
