from juegos.models import Wishlist


class WishlistEntry(Wishlist):
    class Meta:
        proxy = True
        verbose_name = "Juego en wishlist"
        verbose_name_plural = "Wishlist"
