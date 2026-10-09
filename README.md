# 🎲 Sobre Ludix

Ludix nace con una idea sencilla:

**¿No sabes qué juego jugar? Ludix te ayuda a elegirlo**.

El objetivo es crear una plataforma que combine un catálogo de juegos de mesa con un sistema de recomendaciones que facilite la elección tanto para jugar como para comprar.

La aplicación busca solucionar el problema de perder tiempo decidiendo qué juego escoger durante una reunión. Para ello, el usuario podrá introducir diferentes criterios y obtener recomendaciones adaptadas a sus necesidades.


Los criterios contemplados incluyen:

- Número de jugadores.
- Edad.
- Dificultad.
- Duración.
- Temática.

Ludix contempla dos modos principales de sugerencia:

- **Sugerencia de compra:** para recomendar juegos que el usuario podría comprar.
- **Sugerencia de biblioteca:** para recomendar juegos que el usuario ya posee.

---

## 🎯 Objetivos

El objetivo principal de Ludix es facilitar la elección de un juego de mesa.

Entre los objetivos del proyecto se encuentran:

- Permitir el registro de usuarios.
- Permitir la autenticación.
- Mostrar un catálogo de juegos.
- Permitir realizar búsquedas.
- Recomendar juegos según diferentes criterios.
- Gestionar la biblioteca personal de los usuarios.
- Consultar juegos favoritos.
- Gestionar una lista de deseos (*wishlist*).
- Crear sesiones de sugerencias.
- Permitir votar entre juegos propuestos.
- Gestionar un carrito de compras.
- Crear pedidos.
- Gestionar el stock.
- Administrar productos.
- Consultar el historial de juegos jugados.
- Consultar el historial de pedidos.
- Soportar diferentes idiomas.

Los objetivos técnicos contemplan un diseño responsive y una arquitectura basada en una API REST.

---

## 🛠️ Tecnologías

### Backend

- **Python 3.14**
- **Django 6.1.1**
- **Django REST Framework 3.18.1**
- **django-filter 26.1**

### Base de datos

- **SQLite** para el desarrollo inicial.

### Control de versiones

- **Git**

### Frontend previsto

- **React**

La arquitectura prevista separa el frontend del backend mediante una API REST.

---

## 🏗️ Arquitectura

La arquitectura prevista para Ludix sigue una separación entre frontend, backend y base de datos:

```
┌─────────────────────┐
│      FRONTEND       │
│        React        │
└──────────┬──────────┘
           │
           │ HTTP / JSON
           ▼
┌─────────────────────┐
│       BACKEND       │
│   Django REST API   │
└──────────┬──────────┘
           │
           │ ORM
           ▼
┌─────────────────────┐
│      DATABASE       │
│       SQLite        │
└─────────────────────┘
```

Durante el desarrollo inicial se utiliza SQLite. Posteriormente se contempla la posibilidad de utilizar PostgreSQL.

# 📁 Estructura del proyecto

La estructura principal del backend es:

    Ludix/
    │
    ├── manage.py
    ├── db.sqlite3
    ├── .gitignore
    │
    ├── ludix/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    │
    └── juegos/
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models.py
        ├── pagination.py
        ├── serializers.py
        ├── tests.py
        ├── views.py
        ├── readme.md
        │
        └── migrations/
            ├── __init__.py
            └── 0001_initial.py

El entorno virtual no debe incluirse en el repositorio. Se recomienda utilizar ```.venv/``` y añadirlo al ```.gitignore```.

# 🗄️ Modelo de datos

Ludix cuenta con diferentes modelos destinados a representar usuarios, juegos, biblioteca, wishlist, sugerencias y pedidos.

# 👥 Usuarios

El proyecto utiliza el sistema de usuarios de Django y cuenta con un modelo ```PerfilUsuario``` asociado al usuario.

El perfil permite almacenar información adicional como:

* Rol.
* Idioma preferido.
* Fecha de nacimiento.

#  Roles

Los roles contemplados son:

* Clientes.
* Admin.

# 🗣️ Idiomas

* Español (```es```)
* Inglés (```en```)
* Catalán (```ca```)
* Italiano (```it```)

# 🎲 Juegos

El modelo ```Juego``` representa los juegos de mesa disponibles en la aplicación.

Entre sus principales atributos se encuentran:

* Título.
* Descripción.
* ID de BoardGameGeek.
* Número mínimo de jugadores.
* Número máximo de jugadores.
* Duración.
* Edad mínima.
* Dificultad.
* Precio.
* Stock.
* Enlace de referido.

Los juegos pueden pertenecer a diferentes categorías y mecánicas.

# 🏷️ Categorías

Las categorías permiten clasificar los juegos de mesa.

Un juego puede estar asociado a varias categorías.

Por ejemplo:

```
Juego
 ├── Estrategia
 ├── Familiar
 └── Competitivo
```

# ⚙️ Mecánicas

Las mecánicas permiten describir cómo funciona un juego.

Un juego puede tener varias mecánicas asociadas.

Por ejemplo:

```
Juego
 ├── Gestión de recursos
 ├── Colocación de trabajadores
 └── Construcción de mazos
```

# 📚 Biblioteca

La biblioteca permite relacionar usuarios con los juegos que poseen.

El modelo utilizado es:

``` BibliotecaJuego ```

Además, permite marcar determinados juegos como favoritos.

La relación puede representarse de la siguiente manera:

```
Usuario
   │
   ▼
Biblioteca
   │
   ├── Juego
   ├── Juego
   ├── Juego
   └── Juego favorito
```

# ❤️ Wishlist

La wishlist permite que un usuario guarde juegos que le gustaría comprar.

```
Usuario
   │
   ▼
Wishlist
   │
   ├── Juego
   ├── Juego
   └── Juego
```

# 💡 Sistema de sugerencias

Una de las funcionalidades principales de Ludix es el sistema de sugerencias.

El proyecto contempla los siguientes modelos:

* ```SesionSugerencia```
* ```SesionJuegoPropuesto```
* ```VotoSugerencia```

Las sesiones de sugerencia pueden ser de dos tipos:

```
BIBLIOTECA
COMPRA
```

El objetivo es que los usuarios puedan obtener recomendaciones de juegos según diferentes criterios.

# 🔄 Funcionamiento previsto

El flujo básico será:

```
Usuario
   │
   ▼
Selecciona criterios
   │
   ├── Número de jugadores
   ├── Edad
   ├── Dificultad
   ├── Duración
   └── Temática
   │
   ▼
Sistema de recomendación
   │
   ▼
Juegos recomendados
```

Por ejemplo: 

```
Número de jugadores: 4
Edad: 18+
Dificultad: Media
Duración: 60 minutos
Temática: Estrategia

             ↓

        RECOMENDACIONES

             ↓

          Catan
       Carcassonne
            Azul
```

# 🛒 Sistema de compras

Ludix también contempla una parte de ecommerce.

El proyecto cuenta con modelos relacionados con los pedidos:

* ```Pedido```
* ```LineaPedido```

Los pedidos pueden encontrarse en diferentes estados:

```
PENDIENTE
PAGADO
ENVIADO
CANCELADO
```

El objetivo final es permitir:

* Consultar juegos disponibles para comprar.
* Añadir productos al carrito.
* Crear pedidos.
* Consultar pedidos.
* Gestionar stock.

# 🔗 Relaciones principales

La estructura de relaciones puede representarse de la siguiente manera:

```
User
 │
 └── 1:1 ── PerfilUsuario
                │
                ├── 1:N ── BibliotecaJuego ── N:1 ── Juego
                │
                ├── 1:N ── Wishlist ───────── N:1 ── Juego
                │
                ├── 1:N ── Pedido
                │
                └── 1:N ── SesionSugerencia
                                  │
                                  ├── 1:N ── SesionJuegoPropuesto
                                  │                  │
                                  │                  └── Juego
                                  │
                                  └── 1:N ── VotoSugerencia
                                                     │
                                                     └── Juego


Juego
 ├── N:M ── Categoria
 └── N:M ── Mecanica


Pedido
 │
 └── 1:N ── LineaPedido
                 │
                 └── N:1 ── Juego
```

# Instalación 

**1. Clonar el repositorio**

```git clone <URL_DEL_REPOSITORIO>```

Entrar en la carpeta: 

```cd Ludix```

**2. Crear un entorno virtual**

 <small>**Windows**</small>

``` python -m venv .venv ```

Activar el entorno: 

```.venv\Scripts\activate```

 <small>**macOS / Linux</small>

```python3 -m venv .venv```

Activar el entorno: 

```source .venv/bin/activate```

# 📦 Instalación de dependencias
Si existe un archivo ```requirements.txt```:

```pip install -r requirements.txt```

En caso contrario: 

```
pip install Django==6.1.1
pip install djangorestframework==3.18.1
pip install django-filter==26.1
```

# 🗄️ Configurar base de datos
Aplicar las migraciones:

```python manage.py migrate```

Esto creará y actualizará la base de datos SQLite. 

# ▶️ Ejecutar el proyecto

Para iniciar el servidor de desarrollo:

```python manage.py runserver```

El proyecto estará disponible en:

```http://127.0.0.1:8000/```

# 🔌 API

El backend utiliza Django REST Framework para proporcionar una API REST.

Actualmente existe un endpoint para consultar los juegos:

```GET /api/juegos/```

Por ejemplo:

```curl http://127.0.0.1:8000/api/juegos/```

# 📄 Paginación

El endpoint de juegos utiliza paginación.

Para consultar la primera página:

```/api/juegos/?page=1```

También se puede especificar el tamaño de la página:

```/api/juegos/?page=1&page_size=20```

El tamaño predeterminado es:

```10```

El tamaño máximo configurado es:

```100```

# 🧪 Test

Los test del proyecto se encuentran en:

```juegos/test.py```

Para ejecutar todos los test:

```python manage.py test```

# ⚙️ Configuración de Django

La configuración principal del proyecto se encuentra en:

```ludix/settings.py```

La base de datos utilizada actualmente es:

```SQLite```

y el archivo de base de datos es:

```db.squlite3```

La configuración actual está orientada al desarrollo. Antes de desplegar la aplicación en producción deben revisarse aspectos como ```DEBUG```, ```SECRET_KEY```, ```ALLOWED_HOSTS```, seguridad y configuración de la base de datos.

# 🔐 Seguridad

Para un entorno de producción se deberán revisar, entre otros, los siguientes aspectos:

* SECRET_KEY
* DEBUG
* ALLOWED_HOSTS
* Autenticación.
* Permisos de la API.
* Variables de entorno.
* Protección de contraseñas.
* Configuración HTTPS.
* Configuración de la base de datos.
* CORS.

Las contraseñas de los usuarios deben gestionarse utilizando el sistema de autenticación de Django y nunca deben almacenarse en texto plano.

# 🌐 Frontend

El proyecto contempla un frontend desarrollado con React.

La comunicación entre React y Django se realizará mediante HTTP y JSON:

```
React
  │
  │ HTTP / JSON
  ▼
Django REST API
  │
  ▼
SQLite
```

Entre las pantallas previstas se encuentran: 

```
/register
/login
```

# 🌳 Git y trabajo en equipo

Para organizar el trabajo se propone utilizar ramas de funcionalidad.

La rama principal será:


```main```

Y las funcionalidades se desarrollarán en ramas:

```
feature/setup
feature/auth
feature/database
feature/frontend-auth
```

Por ejemplo: 

```git switch -c feature/frontend-auth```

Después de finalizar una funcionalidad:

```
feature/frontend-auth
        │
        ▼
   Pull Request
        │
        ▼
       main
```

📋 Flujo de desarrollo

El flujo recomendado es:

```
1. Crear una rama
        ↓
2. Desarrollar la funcionalidad
        ↓
3. Realizar pruebas
        ↓
4. Crear commits
        ↓
5. Crear Pull Request
        ↓
6. Revisar
        ↓
7. Integrar en main
```

Ejemplo de commmits: 

```
git add .
git commit -m "Create React project"
git commit -m "Add register page"
git commit -m "Add login page"
git commit -m "Connect register API"
```

# 🗺️ Roadmap
**Sprint 1**

El primer sprint se centra en preparar la base técnica del proyecto.

**Backend**
 * ✅ Crear proyecto Django.
 * ✅ Configurar Django REST Framework.
 * ✅ Configurar SQLite.
 * ✅ Crear migraciones.
 * ✅ Crear aplicación juegos.
 * ✅ Crear modelos.
 * ✅ Crear serializer de juegos.
 * ✅ Crear endpoint de juegos.
 * ✅ Añadir paginación.

**Usuarios**
* 🔲 Registro.
* 🔲 Login.
* 🔲 Autenticación.
* 🔲 Permisos.

**Frontend**
* 🔲 Crear proyecto en React.
* 🔲 Crear página de registro.
* 🔲 Crear página de login.
* 🔲 Conectar React con la API.

# 🔮 Próximas funcionalidades

Después del primer sprint se contempla implementar:

* 🔲 Sistema completo de autenticación.
* 🔲 Catálogo de juegos.
* 🔲 Búsqueda.
* 🔲 Filtros.
* 🔲 Sistema de recomendaciones.
* 🔲 Biblioteca personal.
* 🔲 Favoritos.
* 🔲 Wishlist.
* 🔲 Sesiones de sugerencia.
* 🔲 Votación.
* 🔲 Carrito de compra.
* 🔲 Pedidos.
* 🔲 Gestión de stock.
* 🔲 Administración.
* 🔲 Historial de juegos.
* 🔲 Historial de pedidos.
* 🔲 Soporte multidioma.
* 🔲 Frontend completo en React.

# 👥 Equipo

Ludix es un proyecto colaborativo desarrollado por un equipo de estudiantes.

La planificación inicial divide el trabajo en diferentes áreas:

| Área          | Responsabilidades                     |
| ------------- | ------------------------------------- |
| Django        | Configuración del proyecto y backend  |
| Usuarios      | Registro, login y autenticación       |
| Base de datos | Migraciones, modelos y testing        |
| Frontend      | React, formularios y conexión con API |













































