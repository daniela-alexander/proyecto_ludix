from django.shortcuts import render
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .filters import GameFilter
from .models import Game
from .serializers import GameSerializer
from .pagination import GamePagination


class GameListView(ListAPIView):
    queryset = Game.objects.all().order_by("id")
    serializer_class = GameSerializer
    pagination_class = GamePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = GameFilter


JuegoListView = GameListView


def home(request):
    return render(request, "home.html")