from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

class RegisterViewTests(TestCase):
    def test_get_register_page(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_valid_registration_logs_in_and_redirects(self):
        response = self.client.post(
            reverse("register"),
            {
                "first": "John",
                "last": "Doe",
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "a-very-uncommon-pass9",
                "confirmation": "a-very-uncommon-pass9",
            },
        )

        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_password_mismatch_does_not_create_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "first": "Jane",
                "last": "Doe",
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password": "a-very-uncommon-pass9",
                "confirmation": "different-pass9",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser2").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="testpass123")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "testpass123"}
        )
        self.assertRedirects(response, reverse("index"))

    def test_invalid_login_shows_error(self):
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username and/or password.")

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

class IndexViewTests(TestCase):
    def test_logged_out_users_cannot_upload_data(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please log in or register to upload a dataset.")

    def test_logged_in_user_can_upload_data(self):
        user = User.objects.create_user(username="bob", password="testpass123")
        self.client.force_login(user)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload Dataset (CSV):") 