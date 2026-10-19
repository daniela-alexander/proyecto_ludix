from juegos.models import BibliotecaJuego


class LibraryEntry(BibliotecaJuego):
    class Meta:
        proxy = True
        verbose_name = "Entrada de biblioteca"
        verbose_name_plural = "Biblioteca"
