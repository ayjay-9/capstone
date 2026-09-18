import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ml_experiment_dashboard.models import Experiment, ExperimentResult

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

    def test_history_pagination(self):
        user = User.objects.create_user(username="hannah", password="testpass123")
        self.client.force_login(user)
        # Create 12 dummy experiments for this user
        for i in range(12):
            Experiment.objects.create(
                user=user,
                name=f"dataset_{i}.csv",
                row_count=5,
                commentary=f"This is dataset {i}."
            )
        response = self.client.get(reverse("history"))
        self.assertEqual(response.status_code, 200)
        # Check that only 5 experiments are shown on the first page
        for i in range(7, 12):
            self.assertContains(response, f"dataset_{i}.csv")
        for i in range(0, 7):
            self.assertNotContains(response, f"dataset_{i}.csv")

        # Check the second page
        response_page_2 = self.client.get(reverse("history") + "?page=2")
        self.assertEqual(response_page_2.status_code, 200)
        for i in range(2, 7):
            self.assertContains(response_page_2, f"dataset_{i}.csv")

class RunExperimentViewTests(TestCase):
    def test_run_experiment_requires_login(self):
        response = self.client.get(reverse("run_experiment", args=[1]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_run_experiment_with_invalid_experiment_id(self):
        user = User.objects.create_user(username="ian", password="testpass123")
        self.client.force_login(user)
        response = self.client.get(reverse("run_experiment", args=[999]))  # Non-existent ID
        self.assertEqual(response.status_code, 404)

    def test_run_experiment_get_shows_target_column_picker(self):
        user = User.objects.create_user(username="jane", password="testpass123")
        self.client.force_login(user)
        experiment = Experiment.objects.create(
            user=user,
            name="valid_dataset.csv",
            row_count=10,
            columns=["brand", "price", "ram"],
            commentary="This dataset contains laptop specs and prices."
        )
        response = self.client.get(reverse("run_experiment", args=[experiment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="target_column"')
        self.assertContains(response, '<option value="price">price</option>')
        # GET must not have side effects - no result yet, no ExperimentResult created
        self.assertNotContains(response, "Experiment Results for valid_dataset.csv")
        self.assertFalse(ExperimentResult.objects.filter(experiment=experiment).exists())

    def test_run_experiment_rejects_another_users_experiment(self):
        owner = User.objects.create_user(username="owner2", password="testpass123")
        intruder = User.objects.create_user(username="intruder", password="testpass123")
        experiment = Experiment.objects.create(user=owner, name="not_yours.csv", row_count=5)

        self.client.force_login(intruder)
        response = self.client.get(reverse("run_experiment", args=[experiment.id]))
        self.assertEqual(response.status_code, 404)

    @patch("ml_experiment_dashboard.views.generate_dataset_commentary")
    def test_run_experiment_post_runs_regression(self, mock_commentary):
        mock_commentary.return_value = "Test commentary."
        user = User.objects.create_user(username="karl", password="testpass123")
        self.client.force_login(user)
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/valid_dataset.csv")
        with open(CSV_PATH, "rb") as csv_file:
            self.client.post(reverse("index"), {"dataset": csv_file}, format="multipart")
        experiment = Experiment.objects.get(user=user, name="valid_dataset.csv")

        response = self.client.post(
            reverse("run_experiment", args=[experiment.id]),
            {"target_column": "price"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Experiment Results for valid_dataset.csv")
        self.assertContains(response, "regression")
        self.assertContains(response, "LinearRegression")
        result = ExperimentResult.objects.filter(experiment=experiment).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.result_data["problem_type"], "regression")
        self.assertEqual(result.result_data["feature_columns"], ["ram"])

    @patch("ml_experiment_dashboard.views.generate_dataset_commentary")
    def test_run_experiment_post_runs_classification(self, mock_commentary):
        mock_commentary.return_value = "Test commentary."
        user = User.objects.create_user(username="lena", password="testpass123")
        self.client.force_login(user)
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/valid_dataset.csv")
        with open(CSV_PATH, "rb") as csv_file:
            self.client.post(reverse("index"), {"dataset": csv_file}, format="multipart")
        experiment = Experiment.objects.get(user=user, name="valid_dataset.csv")

        response = self.client.post(
            reverse("run_experiment", args=[experiment.id]),
            {"target_column": "brand"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "classification")
        self.assertContains(response, "LogisticRegression")
        result = ExperimentResult.objects.filter(experiment=experiment).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.result_data["problem_type"], "classification")
        self.assertEqual(sorted(result.result_data["feature_columns"]), ["price", "ram"])

    def test_run_experiment_post_without_cached_dataset_shows_friendly_message(self):
        user = User.objects.create_user(username="mona", password="testpass123")
        self.client.force_login(user)
        experiment = Experiment.objects.create(
            user=user, name="old.csv", row_count=5, columns=["price", "ram"]
        )

        response = self.client.post(
            reverse("run_experiment", args=[experiment.id]),
            {"target_column": "price"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your uploaded data has expired.")
        self.assertFalse(ExperimentResult.objects.filter(experiment=experiment).exists())

    @patch("ml_experiment_dashboard.views.generate_dataset_commentary")
    def test_run_experiment_post_with_invalid_target_column_shows_friendly_message(self, mock_commentary):
        mock_commentary.return_value = "Test commentary."
        user = User.objects.create_user(username="nate", password="testpass123")
        self.client.force_login(user)
        CSV_PATH = os.path.join(os.path.dirname(__file__), "test_files/valid_dataset.csv")
        with open(CSV_PATH, "rb") as csv_file:
            self.client.post(reverse("index"), {"dataset": csv_file}, format="multipart")
        experiment = Experiment.objects.get(user=user, name="valid_dataset.csv")

        response = self.client.post(
            reverse("run_experiment", args=[experiment.id]),
            {"target_column": "does_not_exist"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Could not run an experiment with that column.")
        self.assertFalse(ExperimentResult.objects.filter(experiment=experiment).exists())