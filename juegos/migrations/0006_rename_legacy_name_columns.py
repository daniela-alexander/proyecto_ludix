from django.db import migrations


COLUMN_RENAMES = (
    ("categoria", "nombre", "name"),
    ("categoria", "descripcion", "description"),
    ("mecanica", "nombre", "name"),
)


def rename_legacy_columns(schema_editor, renames):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        for table, old_name, new_name in renames:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, table
                )
            }

            if old_name in columns and new_name in columns:
                raise RuntimeError(
                    f"Both {table}.{old_name} and {table}.{new_name} exist."
                )
            if old_name not in columns and new_name not in columns:
                raise RuntimeError(
                    f"Neither {table}.{old_name} nor {table}.{new_name} exists."
                )
            if old_name in columns:
                schema_editor.execute(
                    f"ALTER TABLE {quote_name(table)} "
                    f"RENAME COLUMN {quote_name(old_name)} "
                    f"TO {quote_name(new_name)}"
                )


def rename_columns_forward(apps, schema_editor):
    rename_legacy_columns(schema_editor, COLUMN_RENAMES)


def rename_columns_backward(apps, schema_editor):
    reverse_renames = tuple(
        (table, new_name, old_name)
        for table, old_name, new_name in reversed(COLUMN_RENAMES)
    )
    rename_legacy_columns(schema_editor, reverse_renames)


class Migration(migrations.Migration):

    dependencies = [
        ("juegos", "0005_merge_20261026_1659"),
    ]

    operations = [
        migrations.RunPython(rename_columns_forward, rename_columns_backward),
    ]
