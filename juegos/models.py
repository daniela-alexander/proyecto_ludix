from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class PerfilUsuario(models.Model):
    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        ADMIN = "ADMIN", "Administrador"

    class Idioma(models.TextChoices):
        ESPANOL = "es", "Español"
        INGLES = "en", "Inglés"
        CATALAN = "ca", "Catalán"
        ITALIANO = "it", "Italiano"

    id = models.BigAutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil",
    )

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )

    idioma_preferido = models.CharField(
        max_length=5,
        choices=Idioma.choices,
        default=Idioma.ESPANOL,
    )

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "perfil_usuario"

    def __str__(self):
        return f"{self.user.username} - {self.rol}"


class Categoria(models.Model):
    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "categoria"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Mecanica(models.Model):
    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        db_table = "mecanica"
        verbose_name = "Mecánica"
        verbose_name_plural = "Mecánicas"

    def __str__(self):
        return self.nombre


class Juego(models.Model):
    id = models.BigAutoField(primary_key=True)

    bgg_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
    )

    titulo = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField(
        default="",
        blank=True,
    )

    num_jugadores_min = models.PositiveIntegerField()

    num_jugadores_max = models.PositiveIntegerField()

    duracion_minutos = models.PositiveIntegerField()

    edad_minima = models.PositiveIntegerField()

    dificultad = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[
            MinValueValidator(0),
        ],
    )

    stock = models.PositiveIntegerField(
        default=0,
    )

    link_referido = models.TextField(
        null=True,
        blank=True,
    )

    categorias = models.ManyToManyField(
        Categoria,
        through="JuegoCategoria",
        related_name="juegos",
        blank=True,
    )

    mecanicas = models.ManyToManyField(
        Mecanica,
        through="JuegoMecanica",
        related_name="juegos",
        blank=True,
    )

    class Meta:
        db_table = "juego"

    def __str__(self):
        return self.titulo


class JuegoCategoria(models.Model):
    id = models.BigAutoField(primary_key=True)

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="juego_categorias",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="juego_categorias",
    )

    class Meta:
        db_table = "juego_categoria"

        constraints = [
            models.UniqueConstraint(
                fields=["juego", "categoria"],
                name="unique_juego_categoria",
            )
        ]

    def __str__(self):
        return f"{self.juego} - {self.categoria}"


class JuegoMecanica(models.Model):
    id = models.BigAutoField(primary_key=True)

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="juego_mecanicas",
    )

    mecanica = models.ForeignKey(
        Mecanica,
        on_delete=models.CASCADE,
        related_name="juego_mecanicas",
    )

    class Meta:
        db_table = "juego_mecanica"

        constraints = [
            models.UniqueConstraint(
                fields=["juego", "mecanica"],
                name="unique_juego_mecanica",
            )
        ]

    def __str__(self):
        return f"{self.juego} - {self.mecanica}"


class BibliotecaJuego(models.Model):
    id = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="biblioteca",
    )

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="bibliotecas",
    )

    favorito = models.BooleanField(
        default=False,
    )

    fecha_agregado = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "biblioteca_juego"

        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "juego"],
                name="unique_usuario_juego_biblioteca",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.juego}"


class Wishlist(models.Model):
    id = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )

    agregado_el = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "wishlist"

        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "juego"],
                name="unique_usuario_juego_wishlist",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.juego}"


class SesionSugerencia(models.Model):
    class TipoSugerencia(models.TextChoices):
        BIBLIOTECA = "BIBLIOTECA", "Biblioteca"
        COMPRA = "COMPRA", "Compra"

    id = models.BigAutoField(primary_key=True)

    anfitrion = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="sesiones_sugerencia",
    )

    tipo_sugerencia = models.CharField(
        max_length=20,
        choices=TipoSugerencia.choices,
    )

    num_jugadores = models.PositiveIntegerField()

    duracion_max = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    creado_el = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "sesion_sugerencia"

    def __str__(self):
        return f"Sesión {self.id} - {self.tipo_sugerencia}"


class SesionJuegoPropuesto(models.Model):
    id = models.BigAutoField(primary_key=True)

    sesion = models.ForeignKey(
        SesionSugerencia,
        on_delete=models.CASCADE,
        related_name="juegos_propuestos",
    )

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="sesiones_propuesto",
    )

    class Meta:
        db_table = "sesion_juego_propuesto"

        constraints = [
            models.UniqueConstraint(
                fields=["sesion", "juego"],
                name="unique_sesion_juego_propuesto",
            )
        ]

    def __str__(self):
        return f"{self.sesion} - {self.juego}"


class VotoSugerencia(models.Model):
    id = models.BigAutoField(primary_key=True)

    sesion = models.ForeignKey(
        SesionSugerencia,
        on_delete=models.CASCADE,
        related_name="votos",
    )

    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name="votos",
    )

    puntuacion = models.IntegerField(
        default=1,
    )

    class Meta:
        db_table = "voto_sugerencia"

    def __str__(self):
        return f"{self.sesion} - {self.juego} - {self.puntuacion}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        ENVIADO = "ENVIADO", "Enviado"
        CANCELADO = "CANCELADO", "Cancelado"

    id = models.BigAutoField(primary_key=True)

    cliente = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    creado_el = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "pedido"

    def __str__(self):
        return f"Pedido #{self.id}"


class LineaPedido(models.Model):
    id = models.BigAutoField(primary_key=True)

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="lineas",
    )

    juego = models.ForeignKey(
        Juego,
        on_delete=models.PROTECT,
        related_name="lineas_pedido",
    )

    cantidad = models.PositiveIntegerField(
        default=1,
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        db_table = "linea_pedido"

    def __str__(self):
        return f"{self.pedido} - {self.juego}"