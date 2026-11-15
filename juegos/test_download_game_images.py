from io import BytesIO
from pathlib import Path
import ssl
import tempfile
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from PIL import Image

from juegos.management.commands.download_game_images import download_image
from juegos.models import Game


class DownloadGameImagesTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            title="Juego de prueba",
            description="Prueba de descarga",
            min_players=2,
            max_players=4,
            duration_minutes=30,
            min_age=8,
            difficulty="2.00",
            image="https://placehold.co/test.png",
        )
        image_buffer = BytesIO()
        Image.new("RGB", (4, 4), "blue").save(image_buffer, format="PNG")
        self.image_content = image_buffer.getvalue()
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)

    def mock_opener(self, content=None, error=None):
        response = BytesIO(content if content is not None else self.image_content)
        response.headers = {"Content-Length": str(len(response.getvalue()))}
        opener = Mock()
        if error:
            opener.open.side_effect = error
        else:
            opener.open.return_value = response
        return patch(
            "juegos.management.commands.download_game_images.build_opener",
            return_value=opener,
        )

    def test_command_downloads_image_and_saves_local_media_path(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with self.mock_opener():
                    call_command("download_game_images", verbosity=0)

                self.game.refresh_from_db()
                self.assertEqual(self.game.image.name, "games/juego-de-prueba-1.png")
                self.assertTrue(self.game.image.storage.exists(self.game.image.name))

    def test_dry_run_does_not_change_image_or_create_media_file(self):
        with override_settings(MEDIA_ROOT=self.media_dir.name):
            with self.mock_opener():
                call_command("download_game_images", "--dry-run", verbosity=0)

            self.game.refresh_from_db()
            self.assertEqual(self.game.image.name, "https://placehold.co/test.png")
            self.assertEqual(list(Path(self.media_dir.name).iterdir()), [])

    def test_rejects_hosts_outside_allowlist(self):
        self.game.image = "https://example.com/image.png"
        self.game.save(update_fields=["image"])

        with self.mock_opener() as opener:
            with self.assertRaises(CommandError):
                call_command("download_game_images", verbosity=0)

        opener.return_value.open.assert_not_called()
        self.game.refresh_from_db()
        self.assertEqual(self.game.image.name, "https://example.com/image.png")

    def test_invalid_image_does_not_replace_url(self):
        with override_settings(MEDIA_ROOT=self.media_dir.name):
            with self.mock_opener(content=b"not an image"):
                with self.assertRaises(CommandError):
                    call_command("download_game_images", verbosity=0)

            self.game.refresh_from_db()
            self.assertEqual(self.game.image.name, "https://placehold.co/test.png")

    def test_https_uses_certificate_verification_with_certifi_bundle(self):
        with self.mock_opener() as opener_patch:
            download_image(self.game.image.name)

        handlers = opener_patch.call_args.args
        https_handler = next(
            handler
            for handler in handlers
            if handler.__class__.__name__ == "HTTPSHandler"
        )
        self.assertTrue(https_handler._context.check_hostname)
        self.assertEqual(https_handler._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(https_handler._context.get_ca_certs())

    def test_waits_between_image_requests(self):
        Game.objects.create(
            title="Segundo juego",
            description="Otra prueba",
            min_players=2,
            max_players=4,
            duration_minutes=30,
            min_age=8,
            difficulty="2.00",
            image="https://placehold.co/second.png",
        )

        with patch(
            "juegos.management.commands.download_game_images.download_image",
            return_value=(self.image_content, ".png"),
        ), patch("juegos.management.commands.download_game_images.time.sleep") as sleep:
            call_command("download_game_images", "--dry-run", verbosity=0)

        sleep.assert_called_once_with(3)

    def test_stops_immediately_when_server_returns_rate_limit(self):
        rate_limit = HTTPError(
            "https://placehold.co/test.png",
            429,
            "Too Many Requests",
            {},
            None,
        )
        with patch(
            "juegos.management.commands.download_game_images.download_image",
            side_effect=rate_limit,
        ) as download, patch(
            "juegos.management.commands.download_game_images.time.sleep"
        ) as sleep:
            with self.assertRaisesMessage(CommandError, "HTTP 429"):
                call_command("download_game_images", verbosity=0)

        download.assert_called_once()
        sleep.assert_not_called()
