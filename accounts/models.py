from juegos.models import PerfilUsuario


class UserProfile(PerfilUsuario):
    class Meta:
        proxy = True
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self):
        return super().__str__()
