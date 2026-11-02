from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NewConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label=_("Usuario"),
        empty_label=_("Selecciona un usuario"),
    )

    def __init__(self, *args, current_user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = User.objects.exclude(
            pk=current_user.pk
        ).order_by("username")
