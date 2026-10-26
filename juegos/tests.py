from django.test import TestCase
from django.contrib.auth.models import User

from .models import (
    Category,
    Game,
    LibraryGame,
    Mechanic,
    Order,
    OrderLine,
    ProposedGameSession,
    SuggestionSession,
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


class SuggestionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("suggestion_user", password="test")
        self.profile = UserProfile.objects.create(user=self.user)
        self.game = Game.objects.create(
            title="Juego recomendado",
            description="",
            min_players=1,
            max_players=4,
            duration_minutes=60,
            min_age=8,
            difficulty=3,
            price=19.99,
        )
        self.category = Category.objects.create(name="Estrategia")
        self.game.categories.add(self.category)
        self.client.force_login(self.user)

    def test_purchase_suggestion_creates_session_and_proposal(self):
        response = self.client.post(
            "/sugerencia/",
            {
                "tipo_sugerencia": SuggestionSession.SuggestionType.PURCHASE,
                "num_jugadores": 4,
                "edad_minima_participante": 18,
                "duracion_max": 90,
                "dificultad_preferida": 3,
                "tematica": self.category.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["enviado"])
        session = SuggestionSession.objects.get(host=self.profile)
        self.assertEqual(
            session.suggestion_type,
            SuggestionSession.SuggestionType.PURCHASE,
        )
        self.assertEqual(session.player_count, 4)
        self.assertEqual(session.max_duration, 90)
        self.assertEqual(session.edad_minima_participante, 18)
        self.assertEqual(session.tematica, self.category)
        self.assertEqual(
            list(
                ProposedGameSession.objects.filter(session=session).values_list(
                    "game_id", flat=True
                )
            ),
            [self.game.id],
        )

    def test_library_suggestion_only_recommends_games_in_library(self):
        other_game = Game.objects.create(
            title="Otro juego",
            description="",
            min_players=1,
            max_players=4,
            duration_minutes=45,
            min_age=8,
            difficulty=3,
            price=19.99,
        )
        LibraryGame.objects.create(user_profile=self.profile, game=self.game)

        response = self.client.post(
            "/sugerencia/",
            {
                "tipo_sugerencia": SuggestionSession.SuggestionType.LIBRARY,
                "num_jugadores": 4,
                "edad_minima_participante": 18,
                "duracion_max": 90,
                "dificultad_preferida": 3,
                "tematica": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["enviado"])
        session = SuggestionSession.objects.get(host=self.profile)
        self.assertEqual(
            list(
                ProposedGameSession.objects.filter(session=session).values_list(
                    "game_id", flat=True
                )
            ),
            [self.game.id],
        )
        self.assertNotIn(
            other_game.id,
            ProposedGameSession.objects.filter(session=session).values_list(
                "game_id", flat=True
            ),
        )
