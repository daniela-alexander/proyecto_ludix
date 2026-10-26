from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            return email

        normalized_email = email.strip()

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise ValidationError("Ya existe una cuenta con este correo electrónico.")

        return normalized_email

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]