from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework import filters  #Cristofer

from .models import Juego
from .serializers import JuegoSerializer
from .pagination import JuegoPagination 
# este ultimo añadido por daniela para configurar la paginación


class JuegoListView(ListAPIView):
    queryset = Juego.objects.all()
    serializer_class = JuegoSerializer
    pagination_class = JuegoPagination

# Ordenación Cristofer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
      "titulo",
      "num_jugadores_min",
      "num_jugadores_max",
      "duracion_minutos",
      "edad_minima",
      "dificultad",
      "precio",
      "stock",
]
ordering = ["titulo"]

# Create your views here.
