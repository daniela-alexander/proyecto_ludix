from juegos.models import BibliotecaJuego


class LibraryEntry(BibliotecaJuego):
    class Meta:
        proxy = True
        app_label = "library"
        verbose_name = "Library entry"
        verbose_name_plural = "Library"
