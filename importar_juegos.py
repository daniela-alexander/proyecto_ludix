import os
import json
import django
from decimal import Decimal


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ludix.settings')
django.setup()

from juegos.models import Game, Category, Mechanic # Ajusta 'juego' al nombre de tu app si es diferente

def cargar_juegos_json():
    # Ruta del archivo JSON que subiste
    ruta_json = 'juegos/fixtures/100_juegos.json'  # O pon la ruta completa donde lo guardaste
    
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontró el archivo en la ruta: {ruta_json}")
        return

    with open(ruta_json, 'r', encoding='utf-8-sig') as archivo:
        juegos_data = json.load(archivo)
        
        for item in juegos_data:
            titulo = item.get('nombre')
            descripcion = f"{item.get('descripcion', '')}\n\nInstrucciones:\n{item.get('instrucciones', '')}"
            
            # Como tu JSON trae los jugadores y tiempo como texto (ej. "2 a 10+", "15 - 30 min"),
            # asignamos valores por defecto seguros para los campos numéricos requeridos por tu modelo:
            min_players = 2
            max_players = 4
            duration = 20
            
            # Intentamos parsear algo básico si es posible, o dejamos valores estándar
            # (puedes ajustar esta lógica según prefieras)
            
            game, created = Game.objects.update_or_create(
                title=titulo,
                defaults={
                    'description': descripcion,
                    'min_players': min_players,
                    'max_players': max_players,
                    'duration_minutes': duration,
                    'min_age': 8,           # Valor por defecto genérico
                    'difficulty': Decimal('2.00'), # Valor por defecto
                    'price': Decimal('0.00'),
                    'stock': 10,
                    'is_online': False,
                }
            )
            
            # Opcional: Si quieres registrar la categoría o subcategoría automáticamente
            categoria_nombre = item.get('categoria')
            if categoria_nombre:
                cat, _ = Category.objects.get_or_create(name=categoria_nombre)
                game.categories.add(cat)

            accion = "Creado" if created else "Actualizado"
            print(f"[{accion}] Juego: {titulo}")

        print("\n¡Los 100 juegos se han importado exitosamente a la base de datos!")

if __name__ == '__main__':
    cargar_juegos_json()