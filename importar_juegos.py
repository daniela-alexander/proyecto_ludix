import argparse
import json
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ludix.settings")

import django

django.setup()

from django.db import transaction
from django.utils.text import slugify

from juegos.models import Category, Game


RUTA_JSON = Path(__file__).resolve().parent / "juegos/fixtures/juegos_de_mesa.json"
VALORES_NUMERICOS = re.compile(r"\d+")


def extraer_rango(valor, predeterminado):
    numeros = [int(numero) for numero in VALORES_NUMERICOS.findall(str(valor))]
    if not numeros:
        return predeterminado
    if len(numeros) == 1:
        return numeros[0], numeros[0]
    return min(numeros), max(numeros)


def obtener_slug_categoria(nombre):
    base_slug = slugify(nombre)[:150] or "categoria"
    slug = base_slug
    indice = 2
    while Category.objects.filter(slug=slug).exclude(name=nombre).exists():
        sufijo = f"-{indice}"
        slug = f"{base_slug[:150 - len(sufijo)]}{sufijo}"
        indice += 1
    return slug


def descripcion_completa(item):
    secciones = [
        item.get("descripcion", "").strip(),
        f"Subcategoría: {item['subcategoria']}"
        if item.get("subcategoria")
        else "",
        f"Procedencia: {item['pais_procedencia']}"
        if item.get("pais_procedencia")
        else "",
        f"Instrucciones:\n{item['instrucciones']}"
        if item.get("instrucciones")
        else "",
        item.get("creador", "").strip(),
    ]
    return "\n\n".join(seccion for seccion in secciones if seccion)


def cargar_juegos_json(ruta_json=RUTA_JSON):
    try:
        with Path(ruta_json).open(encoding="utf-8-sig") as archivo:
            juegos_data = json.load(archivo)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No se pudo leer el JSON de juegos: {error}") from error

    if not isinstance(juegos_data, list):
        raise ValueError("El archivo JSON debe contener una lista de juegos.")

    creados = 0
    actualizados = 0
    with transaction.atomic():
        for indice, item in enumerate(juegos_data, start=1):
            if not isinstance(item, dict) or not item.get("nombre", "").strip():
                raise ValueError(f"El juego número {indice} no tiene un nombre válido.")

            min_players, max_players = extraer_rango(
                item.get("numero_jugadores"),
                (2, 4),
            )
            min_players = max(1, min_players)
            max_players = max(min_players, max_players)

            duracion_minima, duracion_maxima = extraer_rango(
                item.get("tiempo_estimado"),
                (20, 20),
            )
            duration = max(1, round((duracion_minima + duracion_maxima) / 2))
            titulo = item["nombre"].strip()
            defaults = {
                "description": descripcion_completa(item),
                "min_players": min_players,
                "max_players": max_players,
                "duration_minutes": duration,
                "min_age": 8,
                "difficulty": Decimal("2.00"),
                "is_online": False,
            }
            if "precio" in item:
                try:
                    precio = Decimal(str(item["precio"]))
                except (InvalidOperation, TypeError, ValueError) as error:
                    raise ValueError(
                        f"El precio del juego «{titulo}» no es un número válido."
                    ) from error
                if not precio.is_finite() or precio < 0:
                    raise ValueError(
                        f"El precio del juego «{titulo}» debe ser un número no negativo."
                    )
                defaults["price"] = precio

            imagen_url = (
                item.get("imagen_juego") or item.get("imagen_ilustrativa") or ""
            ).strip()
            game, created = Game.objects.update_or_create(
                title=titulo,
                defaults=defaults,
            )
            if imagen_url and (
                not game.image
                or game.image.name.startswith(("games/illustrations","http://", "https://"))
            ):
                game.image = imagen_url
                game.save(update_fields=["image"])

            categoria_nombre = item.get("categoria", "").strip()
            if categoria_nombre:
                category, _ = Category.objects.get_or_create(
                    name=categoria_nombre,
                    defaults={"slug": obtener_slug_categoria(categoria_nombre)},
                )
                game.categories.add(category)

            if created:
                creados += 1
            else:
                actualizados += 1

    print(
        f"Importación completada: {creados} juegos creados, "
        f"{actualizados} actualizados."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Importa juegos desde un archivo JSON."
    )
    parser.add_argument(
        "archivo_json",
        nargs="?",
        type=Path,
        default=RUTA_JSON,
        help=f"Archivo JSON a importar (por defecto: {RUTA_JSON}).",
    )
    argumentos = parser.parse_args()

    print(f"Importando juegos desde: {argumentos.archivo_json}")

    try:
        cargar_juegos_json(argumentos.archivo_json)
    except ValueError as error:
        raise SystemExit(str(error)) from error
