from collections import Counter

from django.db import migrations, models
from django.utils.text import slugify


SLUG_FIELDS = (
    ("Category", "slug", 150, ("name", "nombre"), "category"),
    ("Game", "slug", 220, ("title", "titulo"), "game"),
    ("Mechanic", "slug", 150, ("name", "nombre"), "mechanic"),
)


def add_and_populate_slugs(apps, schema_editor):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        for model_name, field_name, max_length, source_fields, fallback in SLUG_FIELDS:
            model = apps.get_model("juegos", model_name)
            table = model._meta.db_table
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, table
                )
            }

            if field_name not in columns:
                schema_editor.execute(
                    f"ALTER TABLE {quote_name(table)} "
                    f"ADD COLUMN {quote_name(field_name)} "
                    f"varchar({max_length}) NOT NULL DEFAULT ''"
                )
                columns.add(field_name)

            source_field = next(
                (field for field in source_fields if field in columns),
                None,
            )
            if source_field is None:
                raise RuntimeError(
                    f"Cannot find a source name column for {table}."
                )

            cursor.execute(
                f"SELECT {quote_name('id')}, {quote_name(source_field)}, "
                f"{quote_name(field_name)} FROM {quote_name(table)} "
                f"ORDER BY {quote_name('id')}"
            )
            rows = cursor.fetchall()
            slug_counts = Counter(row[2] for row in rows if row[2])
            reserved = {
                row[2]
                for row in rows
                if row[2] and slug_counts[row[2]] == 1
            }
            used = set()

            for object_id, source_name, current_slug in rows:
                if current_slug and current_slug not in used:
                    slug = current_slug
                else:
                    base_slug = slugify(source_name or "") or f"{fallback}-{object_id}"
                    base_slug = base_slug[:max_length]
                    slug = base_slug
                    suffix_number = 2
                    while slug in used or slug in reserved:
                        suffix = f"-{suffix_number}"
                        slug = f"{base_slug[:max_length - len(suffix)]}{suffix}"
                        suffix_number += 1

                used.add(slug)
                if slug != current_slug:
                    cursor.execute(
                        f"UPDATE {quote_name(table)} "
                        f"SET {quote_name(field_name)} = %s "
                        f"WHERE {quote_name('id')} = %s",
                        [slug, object_id],
                    )

            index_name = f"juegos_{table}_slug_uniq"
            schema_editor.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS {quote_name(index_name)} "
                f"ON {quote_name(table)} ({quote_name(field_name)})"
            )


def remove_slugs(apps, schema_editor):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        for model_name, field_name, _, _, _ in reversed(SLUG_FIELDS):
            model = apps.get_model("juegos", model_name)
            table = model._meta.db_table
            index_name = f"juegos_{table}_slug_uniq"
            schema_editor.execute(
                f"DROP INDEX IF EXISTS {quote_name(index_name)}"
            )
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, table
                )
            }
            if field_name in columns:
                schema_editor.execute(
                    f"ALTER TABLE {quote_name(table)} "
                    f"DROP COLUMN {quote_name(field_name)}"
                )


class Migration(migrations.Migration):

    dependencies = [
        ("juegos", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_and_populate_slugs, remove_slugs),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="category",
                    name="slug",
                    field=models.SlugField(
                        blank=True,
                        max_length=150,
                        unique=True,
                    ),
                ),
                migrations.AddField(
                    model_name="game",
                    name="slug",
                    field=models.SlugField(
                        blank=True,
                        max_length=220,
                        unique=True,
                    ),
                ),
                migrations.AddField(
                    model_name="mechanic",
                    name="slug",
                    field=models.SlugField(
                        blank=True,
                        max_length=150,
                        unique=True,
                    ),
                ),
            ],
        ),
    ]
