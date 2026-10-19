from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CLIENT = "CLIENTE", "Cliente"
        ADMIN = "ADMIN", "Administrador"

    class Language(models.TextChoices):
        SPANISH = "es", "Español"
        ENGLISH = "en", "Inglés"
        CATALAN = "ca", "Catalán"
        ITALIAN = "it", "Italiano"

    id = models.BigAutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    preferred_language = models.CharField(
        max_length=5,
        choices=Language.choices,
        default=Language.SPANISH,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "perfil_usuario"

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Category(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "categoria"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Mechanic(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        db_table = "mecanica"
        verbose_name = "Mechanic"
        verbose_name_plural = "Mechanics"

    def __str__(self):
        return self.name


class Game(models.Model):
    id = models.BigAutoField(primary_key=True)

    bgg_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        default="",
        blank=True,
    )

    min_players = models.PositiveIntegerField()

    max_players = models.PositiveIntegerField()

    duration_minutes = models.PositiveIntegerField()

    min_age = models.PositiveIntegerField()

    difficulty = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
    )

    price = models.DecimalField(
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

    referral_link = models.TextField(
        null=True,
        blank=True,
    )

    categories = models.ManyToManyField(
        Category,
        through="GameCategory",
        related_name="games",
        blank=True,
    )

    mechanics = models.ManyToManyField(
        Mechanic,
        through="GameMechanic",
        related_name="games",
        blank=True,
    )

    class Meta:
        db_table = "juego"

    def __str__(self):
        return self.title


class GameCategory(models.Model):
    id = models.BigAutoField(primary_key=True)

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="game_categories",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="game_categories",
    )

    class Meta:
        db_table = "juego_categoria"

        constraints = [
            models.UniqueConstraint(
                fields=["game", "category"],
                name="unique_juego_categoria",
            )
        ]

    def __str__(self):
        return f"{self.game} - {self.category}"


class GameMechanic(models.Model):
    id = models.BigAutoField(primary_key=True)

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="game_mechanics",
    )

    mechanic = models.ForeignKey(
        Mechanic,
        on_delete=models.CASCADE,
        related_name="game_mechanics",
    )

    class Meta:
        db_table = "juego_mecanica"

        constraints = [
            models.UniqueConstraint(
                fields=["game", "mechanic"],
                name="unique_juego_mecanica",
            )
        ]

    def __str__(self):
        return f"{self.game} - {self.mechanic}"


class LibraryGame(models.Model):
    id = models.BigAutoField(primary_key=True)

    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="library",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="libraries",
    )

    favorite = models.BooleanField(
        default=False,
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "biblioteca_juego"

        constraints = [
            models.UniqueConstraint(
                fields=["user_profile", "game"],
                name="unique_usuario_juego_biblioteca",
            )
        ]

    def __str__(self):
        return f"{self.user_profile} - {self.game}"


class Wishlist(models.Model):
    id = models.BigAutoField(primary_key=True)

    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "wishlist"

        constraints = [
            models.UniqueConstraint(
                fields=["user_profile", "game"],
                name="unique_usuario_juego_wishlist",
            )
        ]

    def __str__(self):
        return f"{self.user_profile} - {self.game}"


class SuggestionSession(models.Model):
    class SuggestionType(models.TextChoices):
        LIBRARY = "BIBLIOTECA", "Biblioteca"
        PURCHASE = "COMPRA", "Compra"

    id = models.BigAutoField(primary_key=True)

    host = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="suggestion_sessions",
    )

    suggestion_type = models.CharField(
        max_length=20,
        choices=SuggestionType.choices,
    )

    player_count = models.PositiveIntegerField()

    max_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "sesion_sugerencia"

    def __str__(self):
        return f"Session {self.id} - {self.suggestion_type}"


class ProposedGameSession(models.Model):
    id = models.BigAutoField(primary_key=True)

    session = models.ForeignKey(
        SuggestionSession,
        on_delete=models.CASCADE,
        related_name="proposed_games",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="proposed_sessions",
    )

    class Meta:
        db_table = "sesion_juego_propuesto"

        constraints = [
            models.UniqueConstraint(
                fields=["session", "game"],
                name="unique_sesion_juego_propuesto",
            )
        ]

    def __str__(self):
        return f"{self.session} - {self.game}"


class SuggestionVote(models.Model):
    id = models.BigAutoField(primary_key=True)

    session = models.ForeignKey(
        SuggestionSession,
        on_delete=models.CASCADE,
        related_name="votes",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="votes",
    )

    score = models.IntegerField(
        default=1,
    )

    class Meta:
        db_table = "voto_sugerencia"

    def __str__(self):
        return f"{self.session} - {self.game} - {self.score}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDIENTE", "Pendiente"
        PAID = "PAGADO", "Pagado"
        SHIPPED = "ENVIADO", "Enviado"
        CANCELLED = "CANCELADO", "Cancelado"

    id = models.BigAutoField(primary_key=True)

    customer = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "pedido"

    def __str__(self):
        return f"Order #{self.id}"


class OrderLine(models.Model):
    id = models.BigAutoField(primary_key=True)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    game = models.ForeignKey(
        Game,
        on_delete=models.PROTECT,
        related_name="order_lines",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        db_table = "linea_pedido"

    def __str__(self):
        return f"{self.order} - {self.game}"


PerfilUsuario = UserProfile
Categoria = Category
Mecanica = Mechanic
Juego = Game
BibliotecaJuego = LibraryGame
SesionSugerencia = SuggestionSession
SesionJuegoPropuesto = ProposedGameSession
VotoSugerencia = SuggestionVote
Pedido = Order
LineaPedido = OrderLine
JuegoCategoria = GameCategory
JuegoMecanica = GameMechanic
