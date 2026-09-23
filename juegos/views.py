from django.shortcuts import render
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

from .filters import JuegoFilter
from .models import Juego
from .serializers import JuegoSerializer
from .pagination import JuegoPagination 
# este ultimo añadido por daniela para configurar la paginación


class JuegoListView(ListAPIView):
    queryset = Juego.objects.all()
    serializer_class = JuegoSerializer
    pagination_class = JuegoPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = JuegoFilter

# Create your views here.
