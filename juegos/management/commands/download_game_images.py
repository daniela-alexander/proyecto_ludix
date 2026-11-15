import ssl
import time
import warnings
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import certifi
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from PIL import Image, UnidentifiedImageError

from juegos.models import Game


ALLOWED_IMAGE_HOSTS = {"placehold.co", "upload.wikimedia.org"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
REQUEST_DELAY_SECONDS = 3
IMAGE_EXTENSIONS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
}


def validate_image_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_IMAGE_HOSTS
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(f"URL no permitida: {url}")


class AllowedImageRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        validate_image_url(new_url)
        return super().redirect_request(
            request,
            response,
            code,
            message,
            headers,
            new_url,
        )


def download_image(url):
    validate_image_url(url)
    request = Request(url, headers={"User-Agent": "Ludix image downloader"})
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    opener = build_opener(
        AllowedImageRedirectHandler(),
        HTTPSHandler(context=ssl_context),
    )

    with opener.open(request, timeout=20) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_IMAGE_BYTES:
            raise ValueError("La imagen supera el límite de tamaño de 12 MB.")

        content = response.read(MAX_IMAGE_BYTES + 1)

    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen supera el límite de tamaño de 12 MB.")

    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(content)) as image:
            image.verify()
            image_format = image.format
            width, height = image.size

    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError("La imagen supera el límite de resolución permitido.")

    extension = IMAGE_EXTENSIONS.get(image_format)
    if not extension:
        raise ValueError(f"Formato de imagen no admitido: {image_format}")

    return content, extension


class Command(BaseCommand):
    help = "Descarga a media/ las imágenes HTTP(S) guardadas en los juegos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida las descargas sin guardar archivos ni actualizar la base de datos.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        games = [
            game
            for game in Game.objects.exclude(image__isnull=True).exclude(image="")
            if game.image.name.startswith(("http://", "https://"))
        ]
        if not games:
            self.stdout.write("No hay URLs de imagen pendientes de descargar.")
            return

        downloaded = 0
        failures = []
        for index, game in enumerate(games):
            try:
                content, extension = download_image(game.image.name)
                if not dry_run:
                    filename = f"{slugify(game.title)[:100]}-{game.pk}{extension}"
                    game.image.save(filename, ContentFile(content), save=False)
                    game.save(update_fields=["image"])
                downloaded += 1
                action = "Validada" if dry_run else "Descargada"
                self.stdout.write(f"{action}: {game.title}")
            except HTTPError as error:
                failures.append(game.title)
                self.stderr.write(
                    self.style.WARNING(
                        f"No se pudo descargar {game.title}: HTTP {error.code}."
                    )
                )
                if error.code in {403, 429}:
                    raise CommandError(
                        f"El servidor respondió HTTP {error.code}; se detiene la "
                        "descarga para respetar el bloqueo o límite del servidor."
                    ) from error
            except (
                Image.DecompressionBombError,
                Image.DecompressionBombWarning,
                OSError,
                TimeoutError,
                UnidentifiedImageError,
                URLError,
                ValueError,
            ) as error:
                failures.append(game.title)
                self.stderr.write(
                    self.style.WARNING(f"No se pudo descargar {game.title}: {error}")
                )

            if index < len(games) - 1:
                time.sleep(REQUEST_DELAY_SECONDS)

        action = "validadas" if dry_run else "descargadas"
        self.stdout.write(f"Imágenes {action}: {downloaded}; fallidas: {len(failures)}.")
        if failures:
            raise CommandError(
                f"Falló la descarga de {len(failures)} imagen(es). "
                "Consulta los avisos anteriores."
            )
