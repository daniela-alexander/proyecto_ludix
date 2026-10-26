from juegos.models import Wishlist


class WishlistEntry(Wishlist):
    class Meta:
        proxy = True
        app_label = "wishlist"
        verbose_name = "Wishlist item"
        verbose_name_plural = "Wishlist"
