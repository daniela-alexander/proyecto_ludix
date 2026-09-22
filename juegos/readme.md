# Hito 1

## Relaciones

**Relaciones Uno a Muchos (ForeignKey)**
•	Usuario → BibliotecaJuego / Wishlist / Pedido / VotoSugerencia: Un usuario puede poseer múltiples juegos en su biblioteca personal, guardar varias peticiones en su wishlist, realizar distintos pedidos de compra y emitir múltiples votos en las sesiones grupales de sugerencia.

•	**Categoria / Mecanica / Editorial → Juego:** Un juego pertenece primariamente a una editorial o categoría principal para simplificar filtros rápidos en el motor de recomendación.

•	**Usuario (Cliente) → Pedido:** Un cliente puede realizar varios pedidos en la tienda a lo largo del tiempo, pero cada pedido pertenece a un único usuario.

•	**Pedido → LineaPedido:** Un pedido de compra se compone de múltiples líneas/ítems (detalles de pedido).

•	**Juego → LineaPedido:** Un producto/juego puede figurar en múltiples líneas de pedidos realizados por distintos clientes.
Relaciones Muchos a Muchos (ManyToManyField)

•	**Juego ↔ Categoria:** Un juego de mesa puede clasificarse en varias categorías (ej. Estrategia, Familiar, Fantasía) y una categoría engloba múltiples juegos.

•	**Juego ↔ Mecanica:** Un juego utiliza distintas mecánicas (Colocación de trabajadores, Gestión de mano, Drafting) y una mecánica está presente en muchos juegos.

•	**SesionSugerencia ↔ Juego:** En una sesión grupal para elegir qué jugar se filtran y proponen múltiples juegos candidatos, y un mismo juego puede ser sugerido en distintas sesiones.
Relaciones Uno a Uno (OneToOneField)

• **User (Django Auth) ↔ PerfilUsuario:** Extiende el modelo por defecto de autenticación de Django (django.contrib.auth.models.User) para almacenar preferencias del usuario (edad, idioma preferido, nivel de experiencia) y su tipo de rol (Visitante/Cliente, Administrador).

![Mi foto](./Ludixjpg.jpg)
