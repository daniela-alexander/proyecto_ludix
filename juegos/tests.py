from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from channels.testing import WebsocketCommunicator

from .forms import SugerenciaForm
from .consumers import UsuariosConsumer
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
    Wishlist,
)


class UsuariosConsumerTests(SimpleTestCase):
    def setUp(self):
        UsuariosConsumer.usuarios_conectados.clear()

    async def test_connected_count_decreases_when_socket_disconnects(self):
        first = WebsocketCommunicator(
            UsuariosConsumer.as_asgi(),
            "/ws/usuarios/",
        )
        second = WebsocketCommunicator(
            UsuariosConsumer.as_asgi(),
            "/ws/usuarios/",
        )
        first_connected = False
        second_connected = False

        try:
            connected, _ = await first.connect()
            self.assertTrue(connected)
            first_connected = True
            self.assertEqual(await first.receive_json_from(), {"usuarios": 1})

            connected, _ = await second.connect()
            self.assertTrue(connected)
            second_connected = True
            self.assertEqual(await first.receive_json_from(), {"usuarios": 2})
            self.assertEqual(await second.receive_json_from(), {"usuarios": 2})

            await first.disconnect()
            first_connected = False
            self.assertEqual(await second.receive_json_from(), {"usuarios": 1})

            await second.disconnect()
            second_connected = False
            self.assertEqual(UsuariosConsumer.usuarios_conectados, set())
        finally:
            if first_connected:
                await first.disconnect()
            if second_connected:
                await second.disconnect()


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

    def test_home_shows_library_state_for_current_user(self):
        user = User.objects.create_user(username="library_card_user")
        profile = UserProfile.objects.create(user=user)
        LibraryGame.objects.create(user_profile=profile, game=self.game_one)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertEqual(response.context["library_game_ids"], {self.game_one.id})
        self.assertContains(response, 'class="game-card-library-button is-in-library"')
        self.assertContains(response, 'data-remove-label="Quitar de mi biblioteca"')
        self.assertContains(response, f'action="/library/add/{self.game_two.id}/"')

    def test_remove_from_library_only_removes_current_users_game(self):
        user = User.objects.create_user(username="library_remove_user")
        other_user = User.objects.create_user(username="other_library_user")
        user_profile = UserProfile.objects.create(user=user)
        other_profile = UserProfile.objects.create(user=other_user)
        LibraryGame.objects.create(user_profile=user_profile, game=self.game_one)
        LibraryGame.objects.create(user_profile=other_profile, game=self.game_one)
        self.client.force_login(user)

        response = self.client.post(
            reverse("library_remove", kwargs={"game_id": self.game_one.id}),
            {"next": "/?q=Prueba"},
        )

        self.assertRedirects(response, "/?q=Prueba")
        self.assertFalse(
            LibraryGame.objects.filter(
                user_profile=user_profile,
                game=self.game_one,
            ).exists()
        )
        self.assertTrue(
            LibraryGame.objects.filter(
                user_profile=other_profile,
                game=self.game_one,
            ).exists()
        )

    def test_home_shows_favorite_and_wishlist_controls_only_in_allowed_states(self):
        user = User.objects.create_user(username="game_controls_user")
        profile = UserProfile.objects.create(user=user)
        LibraryGame.objects.create(
            user_profile=profile,
            game=self.game_one,
            favorite=True,
        )
        Wishlist.objects.create(user_profile=profile, game=self.game_two)
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertEqual(response.context["favorite_game_ids"], {self.game_one.id})
        self.assertEqual(response.context["wishlist_game_ids"], {self.game_two.id})
        self.assertContains(response, 'action="/library/favorite/1/"')
        self.assertContains(response, 'action="/wishlist/remove/2/"')
        self.assertNotContains(response, 'action="/wishlist/add/1/"')
        self.assertNotContains(response, 'action="/library/favorite/2/"')

    def test_favorite_toggle_only_changes_games_in_current_users_library(self):
        user = User.objects.create_user(username="favorite_toggle_user")
        profile = UserProfile.objects.create(user=user)
        library_entry = LibraryGame.objects.create(
            user_profile=profile,
            game=self.game_one,
        )
        self.client.force_login(user)

        favorite_url = reverse(
            "library_favorite",
            kwargs={"game_id": self.game_one.id},
        )
        response = self.client.post(favorite_url, {"next": "/"})

        self.assertRedirects(response, "/")
        library_entry.refresh_from_db()
        self.assertTrue(library_entry.favorite)

        self.client.post(favorite_url, {"next": "/"})
        library_entry.refresh_from_db()
        self.assertFalse(library_entry.favorite)

        self.client.post(
            reverse("library_favorite", kwargs={"game_id": self.game_two.id}),
            {"next": "/"},
        )
        self.assertFalse(
            LibraryGame.objects.filter(
                user_profile=profile,
                game=self.game_two,
            ).exists()
        )

    def test_wishlist_can_only_be_changed_while_game_is_outside_library(self):
        user = User.objects.create_user(username="wishlist_controls_user")
        profile = UserProfile.objects.create(user=user)
        self.client.force_login(user)
        add_url = reverse("wishlist_add", kwargs={"game_id": self.game_two.id})
        remove_url = reverse("wishlist_remove", kwargs={"game_id": self.game_two.id})

        response = self.client.post(add_url, {"next": "/"})

        self.assertRedirects(response, "/")
        self.assertTrue(
            Wishlist.objects.filter(
                user_profile=profile,
                game=self.game_two,
            ).exists()
        )

        self.client.post(remove_url, {"next": "/"})
        self.assertFalse(
            Wishlist.objects.filter(
                user_profile=profile,
                game=self.game_two,
            ).exists()
        )

        LibraryGame.objects.create(user_profile=profile, game=self.game_two)
        self.client.post(add_url, {"next": "/"})
        self.assertFalse(
            Wishlist.objects.filter(
                user_profile=profile,
                game=self.game_two,
            ).exists()
        )

    def test_adding_game_to_library_removes_it_from_wishlist(self):
        user = User.objects.create_user(username="library_clears_wishlist")
        profile = UserProfile.objects.create(user=user)
        Wishlist.objects.create(user_profile=profile, game=self.game_one)
        self.client.force_login(user)

        self.client.post(
            reverse("library_add", kwargs={"game_id": self.game_one.id}),
            {"next": "/"},
        )

        self.assertTrue(
            LibraryGame.objects.filter(
                user_profile=profile,
                game=self.game_one,
            ).exists()
        )
        self.assertFalse(
            Wishlist.objects.filter(
                user_profile=profile,
                game=self.game_one,
            ).exists()
        )

class GameDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="detail_user")
        self.game = Game.objects.create(
            title="Juego detallado",
            description="Descripción completa del juego.",
            min_players=2,
            max_players=5,
            duration_minutes=45,
            min_age=10,
            difficulty=3.5,
            price=24.99,
            stock=3,
        )
        self.category = Category.objects.create(name="Aventura")
        self.mechanic = Mechanic.objects.create(name="Cooperación")
        self.game.categories.add(self.category)
        self.game.mechanics.add(self.mechanic)

    def test_detail_page_shows_game_information(self):
        response = self.client.get(
            reverse("game_detail", kwargs={"game_id": self.game.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Descripción completa del juego.")
        self.assertContains(response, "Aventura")
        self.assertContains(response, "Cooperación")
        self.assertContains(response, "Inicia sesión para añadirlo")
        self.assertContains(
            response,
            reverse("game_shop", kwargs={"game_id": self.game.id}),
        )

    def test_game_shop_page_shows_coming_soon_and_returns_to_game(self):
        response = self.client.get(
            reverse("game_shop", kwargs={"game_id": self.game.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Muy pronto podrás comprar tus juegos favoritos.")
        self.assertContains(response, "Juego detallado")
        self.assertContains(
            response,
            f'href="{reverse("game_detail", kwargs={"game_id": self.game.id})}"',
        )

    def test_detail_page_uses_translations(self):
        detail_url = reverse("game_detail", kwargs={"game_id": self.game.id})
        self.client.post(
            reverse("set_language"),
            {"language": "en", "next": detail_url},
        )

        response = self.client.get(detail_url)

        self.assertContains(response, "Catalog")
        self.assertContains(response, "Game details")
        self.assertContains(response, "Players")
        self.assertContains(response, "Log in to add it")

    def test_detail_page_shows_controls_based_on_library_state(self):
        profile = UserProfile.objects.create(user=self.user)
        LibraryGame.objects.create(user_profile=profile, game=self.game, favorite=True)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("game_detail", kwargs={"game_id": self.game.id})
        )

        self.assertContains(response, 'action="/library/favorite/1/"')
        self.assertContains(response, 'aria-pressed="true"')
        self.assertNotContains(response, 'action="/wishlist/add/1/"')

        LibraryGame.objects.filter(user_profile=profile, game=self.game).delete()
        response = self.client.get(
            reverse("game_detail", kwargs={"game_id": self.game.id})
        )
        self.assertContains(response, 'action="/wishlist/add/1/"')
        self.assertNotContains(response, 'action="/library/favorite/1/"')

    def test_user_can_add_game_from_detail_and_return_to_detail(self):
        self.client.force_login(self.user)
        detail_url = reverse("game_detail", kwargs={"game_id": self.game.id})

        response = self.client.post(
            reverse("library_add", kwargs={"game_id": self.game.id}),
            {"next": detail_url},
        )

        self.assertRedirects(response, detail_url)
        self.assertTrue(
            LibraryGame.objects.filter(
                user_profile__user=self.user,
                game=self.game,
            ).exists()
        )
        self.assertContains(self.client.get(detail_url), "ya está en tu biblioteca")

        self.client.post(
            reverse("library_add", kwargs={"game_id": self.game.id}),
            {"next": detail_url},
        )
        self.assertEqual(
            LibraryGame.objects.filter(
                user_profile__user=self.user,
                game=self.game,
            ).count(),
            1,
        )

    def test_profile_library_has_remove_button_and_removes_game(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        LibraryGame.objects.create(user_profile=profile, game=self.game)
        self.client.force_login(self.user)
        profile_url = reverse("profile")
        remove_url = reverse("library_remove", kwargs={"game_id": self.game.id})

        response = self.client.get(profile_url)

        self.assertContains(response, f'action="{remove_url}"')
        self.assertContains(response, 'class="profile-library-remove-button"')
        self.assertContains(response, 'aria-label="Quitar de mi biblioteca"')

        response = self.client.post(
            remove_url,
            {"next": profile_url},
        )

        self.assertRedirects(response, profile_url)
        self.assertFalse(
            LibraryGame.objects.filter(
                user_profile=profile,
                game=self.game,
            ).exists()
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

    def test_age_and_duration_controls_use_sensible_ranges_and_steps(self):
        response = self.client.get("/sugerencia/")
        age_widget = SugerenciaForm.base_fields[
            "edad_minima_participante"
        ].widget
        duration_widget = SugerenciaForm.base_fields["duracion_max"].widget

        self.assertEqual(int(age_widget.attrs["min"]), 3)
        self.assertEqual(int(age_widget.attrs["max"]), 19)
        self.assertEqual(duration_widget.attrs["step"], "15")
        self.assertContains(response, "Mayor de 18")

    def test_over_18_age_option_includes_games_for_adults(self):
        adult_game = Game.objects.create(
            title="Juego para adultos",
            description="",
            min_players=1,
            max_players=4,
            duration_minutes=60,
            min_age=40,
            difficulty=3,
            price=19.99,
        )

        response = self.client.post(
            "/sugerencia/",
            {
                "tipo_sugerencia": SuggestionSession.SuggestionType.PURCHASE,
                "num_jugadores": 4,
                "edad_minima_participante": 19,
                "duracion_max": 90,
                "dificultad_preferida": 3,
                "tematica": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["enviado"])
        self.assertIn(adult_game, response.context["recomendaciones"])

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

    def test_recommendation_results_show_library_and_wishlist_actions(self):
        owned_game = Game.objects.create(
            title="Juego en biblioteca",
            description="",
            min_players=1,
            max_players=4,
            duration_minutes=45,
            min_age=8,
            difficulty=3,
            price=19.99,
        )
        LibraryGame.objects.create(user_profile=self.profile, game=owned_game)
        Wishlist.objects.create(user_profile=self.profile, game=self.game)

        response = self.client.post(
            "/sugerencia/",
            {
                "tipo_sugerencia": SuggestionSession.SuggestionType.PURCHASE,
                "num_jugadores": 4,
                "edad_minima_participante": 18,
                "duracion_max": 90,
                "dificultad_preferida": 3,
                "tematica": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["library_game_ids"],
            {owned_game.id},
        )
        self.assertEqual(response.context["wishlist_game_ids"], {self.game.id})
        self.assertContains(
            response,
            f'href="{reverse("game_shop", kwargs={"game_id": self.game.id})}"',
        )
        suggestion_url = (
            f'{reverse("sugerencia")}?session='
            f'{response.context["suggestion_session"].id}'
        )
        self.assertContains(response, f'value="{suggestion_url}"')
        self.assertContains(
            response,
            f'action="{reverse("library_add", kwargs={"game_id": self.game.id})}"',
        )
        self.assertContains(
            response,
            f'action="{reverse("wishlist_remove", kwargs={"game_id": self.game.id})}"',
        )
        self.assertContains(
            response,
            f'action="{reverse("library_remove", kwargs={"game_id": owned_game.id})}"',
        )

        add_to_library_response = self.client.post(
            reverse("library_add", kwargs={"game_id": self.game.id}),
            {"next": suggestion_url},
        )
        self.assertRedirects(add_to_library_response, suggestion_url)
        restored_response = self.client.get(suggestion_url)
        self.assertContains(restored_response, self.game.title)
        self.assertContains(
            restored_response,
            f'action="{reverse("library_remove", kwargs={"game_id": self.game.id})}"',
        )
        self.assertNotContains(
            restored_response,
            f'action="{reverse("wishlist_add", kwargs={"game_id": self.game.id})}"',
        )
