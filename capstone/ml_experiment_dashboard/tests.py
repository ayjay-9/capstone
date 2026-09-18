import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ml_experiment_dashboard.models import Experiment

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
        self.assertContains(response, "Drag &amp; drop a CSV here, or click to browse")

    def test_logged_in_user_uploads_non_csv_file(self):
        user = User.objects.create_user(username="dave", password="testpass123")
        self.client.force_login(user)
        # Simulate file upload with a non-CSV file
        TXT_PATH = os.path.join(os.path.dirname(__file__), "test_files/empty.txt")
        with open(TXT_PATH, "rb") as txt_file:
            response = self.client.post(
                reverse("index"),
                {"dataset": txt_file},
                format="multipart",
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please upload a CSV file.")

    def test_upload_with_no_data(self):
        user = User.objects.create_user(username="charlie", password="testpass123")
        self.client.force_login(user)
        # Simulate file upload
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/empty.csv")
        with open(CSV_PATH, "rb") as csv_file:
            response = self.client.post(
                reverse("index"),
                {"dataset": csv_file},
                format="multipart",
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The uploaded CSV file should not be empty and must contain valid data headers.")

    def test_csv_upload_with_fewer_than_five_rows_is_rejected(self):
        user = User.objects.create_user(username="frank", password="testpass123")
        self.client.force_login(user)
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/csv_with_headers.csv")
        with open(CSV_PATH, "rb") as csv_file:
            response = self.client.post(
                reverse("index"),
                {"dataset": csv_file},
                format="multipart",
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The uploaded CSV file must contain at least 5 rows of data.")

    # Simulate a successful CSV upload and check that the Experiment is saved in the database to rreduce the calls to the API 
    @patch("ml_experiment_dashboard.views.generate_dataset_commentary")
    def test_csv_upload_with_valid_data_saves_experiment(self, mock_commentary):
        mock_commentary.return_value = "This dataset contains laptop specs and prices."
        user = User.objects.create_user(username="eve", password="testpass123")
        self.client.force_login(user)
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/valid_dataset.csv")
        with open(CSV_PATH, "rb") as csv_file:
            response = self.client.post(
                reverse("index"),
                {"dataset": csv_file},
                format="multipart",
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Successfully uploaded valid_dataset.csv.")
        mock_commentary.assert_called_once()
        # Check that the Experiment was created in the database
        experiment = Experiment.objects.filter(user=user, name="valid_dataset.csv").first()
        self.assertIsNotNone(experiment)
        self.assertEqual(experiment.row_count, 10)  # Assuming valid_dataset.csv has 10 rows
        self.assertEqual(experiment.commentary, "This dataset contains laptop specs and prices.")


class HistoryViewTests(TestCase):
    def test_history_requires_login(self):
        response = self.client.get(reverse("history"))
        self.assertEqual(response.status_code, 302)

    def test_user_upload_history_is_displayed(self):
        user = User.objects.create_user(username="grace", password="testpass123")
        self.client.force_login(user)
        # Create a dummy experiment for this user
        Experiment.objects.create(
            user=user,
            name="test_dataset.csv",
            row_count=5,
            commentary="This is a test dataset."
        )
        response = self.client.get(reverse("history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test_dataset.csv")

    def test_history_shows_only_current_users_experiments(self):
        owner = User.objects.create_user(username="owner", password="testpass123")
        other = User.objects.create_user(username="other", password="testpass123")
        Experiment.objects.create(user=owner, name="mine.csv", row_count=5)
        Experiment.objects.create(user=other, name="not_mine.csv", row_count=5)

        self.client.force_login(owner)
        response = self.client.get(reverse("history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mine.csv")
        self.assertNotContains(response, "not_mine.csv")