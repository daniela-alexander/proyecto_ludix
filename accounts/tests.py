from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from .forms import RegisterForm


class RegisterFormTests(TestCase):
    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="hola@ludix.test",
            password="Password123!",
        )

        form = RegisterForm(data={
            "username": "newuser",
            "email": "hola@ludix.test",
            "password1": "Password123!",
            "password2": "Password123!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class ProfileUploadTests(TestCase):
    def test_profile_image_can_be_uploaded(self):
        user = User.objects.create_user(
            username="photouser",
            email="photo@ludix.test",
            password="Password123!",
        )

        client = Client()
        client.login(username="photouser", password="Password123!")

        avatar = SimpleUploadedFile(
            "avatar.png",
            b"fake-image-content",
            content_type="image/png",
        )

        response = client.post(
            "/accounts/profile/",
            {"email": "photo@ludix.test", "profile_image": avatar},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.profile.profile_image)
