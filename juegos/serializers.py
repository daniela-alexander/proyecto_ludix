from rest_framework import serializers
from .models import Game


class GameSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, game):
        return game.get_title()

    class Meta:
        model = Game
        fields = "__all__"


JuegoSerializer = GameSerializer