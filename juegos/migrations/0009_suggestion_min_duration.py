from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("juegos", "0008_game_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="suggestionsession",
            name="min_duration",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
