# 🎲 Ludix — Plataforma de juegos de mesa

**Ludix** es una aplicación web que ayuda a responder a una pregunta habitual:
**¿a qué jugamos?**. Su objetivo es facilitar el descubrimiento y la elección
de juegos de mesa y cartas mediante un catálogo, filtros y sugerencias basadas
en las preferencias del grupo.

La aplicación también permite organizar una biblioteca personal, guardar
favoritos y crear una lista de deseos.

## Equipo de desarrollo 🧑‍💻
- Angelo Musso: Scrum Master y backend developer.
- Daniela Alexander: Backend developer.
- Cristofer Picado: Frontend developer.
- Diego Llontop Vásques: Frontend developer.


## 🎯 Funcionalidades

- Catálogo con búsqueda, filtros y fichas de juegos.
- Búsqueda por títulos traducidos y títulos originales.
- Sugerencias para jugar con juegos de la biblioteca o descubrir juegos del
  catálogo.
- Filtros de sugerencias por número de jugadores, edad, duración, dificultad y
  categoría.
- Biblioteca personal, favoritos y lista de deseos.
- Cuentas y perfiles de usuario.
- Mensajería privada en tiempo real.
- Interfaz traducida al español, catalán, inglés e italiano.
- API REST para consultar y filtrar juegos.
- Herramienta interna, restringida al personal, para comparar recomendaciones.

## 🛠️ Tecnologías y herramientas

### Backend y API

- **Python 3.14**
- **Django 6**
- **Django REST Framework**
- **django-filter**

### Interfaz

- Plantillas de Django
- HTML, CSS y JavaScript

### Datos y servicios

- **PostgreSQL** para desarrollo local; **SQLite** también está soportado.
- **Redis** para las capas de comunicación en tiempo real y el broker de Celery.
- **Django Channels** y **Daphne** para WebSockets.
- **Celery** y **Celery Beat** están incluidos y configurados; actualmente no
  hay tareas periódicas activas.

### Herramientas de desarrollo

- `pip` y `requirements.txt` para dependencias Python.
- Docker Compose para PostgreSQL y Redis locales.
- Git para control de versiones.

## 🏗️ Arquitectura

Ludix utiliza Django para servir las páginas y la API. La interfaz se construye
con plantillas, estilos y JavaScript.

```text
Navegador
   │
   ├── páginas HTML, CSS y JavaScript
   ├── API HTTP / JSON
   └── WebSockets
          │
          ▼
   Django / Django REST Framework
          │
          ├── PostgreSQL o SQLite
          └── Redis (Channels y broker de Celery)
```

## 📁 Estructura del proyecto

```text
Ludix/
├── accounts/          # Cuentas y perfiles
├── chat/              # Conversaciones y mensajería
├── juegos/            # Juegos, catálogo y sugerencias
├── library/           # Biblioteca y favoritos
├── orders/            # Consultas de pedidos
├── recommendations/   # Recomendaciones y preferencias
├── wishlist/          # Lista de deseos
├── ludix/             # Configuración, rutas y ASGI
├── templates/         # Plantillas HTML
├── static/            # CSS, JavaScript e imágenes
├── locale/            # Traducciones de Django
├── requirements.txt   # Dependencias Python
├── docker-compose.yaml
└── manage.py
```

Los fixtures de juegos están en `juegos/fixtures/`. Los archivos subidos o
descargados por la aplicación se guardan bajo `media/`.

## 🗄️ Datos principales

El proyecto usa el modelo `User` de Django y lo relaciona con `UserProfile`,
que almacena el rol, el idioma preferido, la fecha de nacimiento y, si existe,
la imagen de perfil.

### Juegos, categorías y mecánicas

`Game` contiene, entre otros datos, el título, descripción, número de
jugadores, duración, edad mínima, dificultad, precio, stock, imagen y si el
juego es en línea. Los títulos y descripciones tienen campos opcionales para
inglés, catalán e italiano. Cada juego puede relacionarse con varias categorías
y mecánicas.

### Biblioteca y lista de deseos

- `LibraryGame` vincula un perfil con un juego y permite marcarlo como favorito.
- `Wishlist` vincula un perfil con los juegos que quiere guardar para más
  adelante.

Ambas relaciones impiden que el mismo usuario añada dos veces el mismo juego.

### Sugerencias

`SuggestionSession` guarda las preferencias seleccionadas: tipo de sugerencia,
número de jugadores y, opcionalmente, duración, edad, dificultad y categoría.
El tipo permite buscar en la biblioteca o en el catálogo. También existen
modelos para juegos propuestos y votos asociados a una sesión.

El módulo de recomendaciones incluye sugerencias basadas en contenido y una
herramienta de comparación con un modelo colaborativo. La vista de comparación
es una herramienta interna para usuarios del personal, no una pantalla pública
del catálogo.

### Pedidos

El proyecto cuenta con modelos de pedido y líneas de pedido, y con endpoints
autenticados para consultar los pedidos propios. El flujo de checkout y el
procesamiento de pagos no forman parte de las funcionalidades actuales.

## 🌐 Idiomas

La interfaz está configurada para:

- Español (`es`)
- Catalán (`ca`)
- Inglés (`en`)
- Italiano (`it`)

Los títulos y descripciones de juegos y las categorías también admiten campos
de traducción. Para actualizar los archivos de traducción de Django se puede
usar:

```bash
python manage.py makemessages -l ca -l en -l it
python manage.py compilemessages
```

## 🚀 Instalación y ejecución

### Requisitos

- Python 3.14
- Git
- Docker Desktop o Docker Engine con Docker Compose

Docker Compose inicia PostgreSQL y Redis para el entorno de desarrollo.

### 1. Clonar el repositorio

```bash
git clone https://github.com/daniela-alexander/proyecto_ludix.git
cd proyecto_ludix
```

### 2. Crear y activar un entorno virtual

```bash
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configurar el entorno y los servicios

Copia `.env.example` a `.env` y arranca PostgreSQL y Redis:

```bash
cp .env.example .env
docker compose up -d
```

En Windows PowerShell, copia el archivo con:

```powershell
Copy-Item .env.example .env
```

El ejemplo configura PostgreSQL y direcciones locales para Redis. Si no se
define `DATABASE_ENGINE`, Django usa SQLite (`db.sqlite3`).

### 5. Aplicar migraciones e iniciar Django

```bash
python manage.py migrate
python manage.py runserver
```

Abre <http://127.0.0.1:8000/>.

Las credenciales de `.env.example` son solo para desarrollo local. No subas
`.env`, claves ni credenciales al repositorio.

## ⚙️ Configuración de la base de datos

El proyecto admite:

- **PostgreSQL:** configura `DATABASE_ENGINE=postgresql` y las variables
  `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT` en `.env`.
- **SQLite:** configura `DATABASE_ENGINE=sqlite` o deja la variable sin
  definir.

Para arrancar o detener los servicios locales:

```bash
docker compose up -d
docker compose down
```

## ⏰ Celery y Redis

Celery está configurado para utilizar Redis como broker, y Celery Beat usa el
planificador de Django. Si añades tareas Celery, inicia el worker y Beat en
terminales separadas:

```bash
celery -A ludix worker -l INFO
celery -A ludix beat -l INFO
```

## 💬 Chat en tiempo real

El chat usa Django Channels y Redis para la comunicación en tiempo real. Los
usuarios autenticados pueden abrir conversaciones; el acceso a cada
conversación está limitado a sus participantes. Para probarlo localmente,
arranca PostgreSQL y Redis con Docker Compose y ejecuta:

```bash
python manage.py runserver
```

## 🔌 API de juegos

El catálogo está disponible en:

- `GET /api/games/`
- `GET /api/juegos/` (ruta alternativa)

La API permite búsqueda, filtros por categoría, mecánica, precio, dificultad,
duración o modalidad en línea, y ordenamiento por campos configurados.

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/games/?search=ajedrez"
```

La respuesta se pagina: el tamaño predeterminado es 10 y se puede configurar
`page_size` hasta un máximo de 100.

```text
/api/games/?page=1&page_size=20
```

## 🧪 Pruebas

Las pruebas están en los módulos `tests.py` de las aplicaciones. Para ejecutar
toda la suite:

```bash
python manage.py test
```

Para ejecutar solo las pruebas de juegos:

```bash
python manage.py test juegos.tests
```

## 🔮 Mejoras futuras

- Seguir mejorando la interfaz y la experiencia de uso.
- Añadir notificaciones para mantener informados a los usuarios.
- Incorporar una sección de reseñas y valoraciones en la ficha de cada juego.

## 🔐 Notas de seguridad

La configuración del repositorio está orientada al desarrollo local. Antes de
un despliegue hay que configurar una `SECRET_KEY` privada, desactivar `DEBUG`,
definir `ALLOWED_HOSTS`, proteger las credenciales de base de datos y aplicar
la configuración de HTTPS y seguridad recomendada por Django.

## LICENCIA 📄
El proyecto Ludix está bajo la licencia MIT. Consulta el archivo `LICENSE` para
más detalles.

## Agradecimientos 🙏
A todos los participantes del proyecto.
Fundació Esplai, por la enseñanza y el apoyo en el desarrollo del proyecto.