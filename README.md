# ML Experiment Dashboard

CS50 Web Programming with Python and JavaScript — Capstone Project

## Overview

ML Experiment Dashboard is a Django web application that lets a user upload a
CSV dataset, receive an AI-generated summary of what the dataset contains and
whether it looks fit for machine learning, browse a paginated history of
their past uploads, and then actually train a machine learning model against
the dataset — automatically choosing between regression and classification,
cleaning and scaling the data, evaluating on a held-out test split, and
receiving a second AI-generated explanation of what the results mean. It
combines a traditional authenticated CRUD application with a generative-AI
integration (Google's Gemini, via LangChain) and real, local machine
learning (scikit-learn).

## Distinctiveness and Complexity

This project is not a social network, not an e-commerce storefront, and not
a variation of the course's own Pizza project — the closest CS50W project in
spirit is Project 2 (Commerce), but the two share no functional overlap.
Commerce is a marketplace with listings, bids, and watchlists; this
application accepts a user-supplied dataset and does something no other
project in the course does: it interprets, summarizes, and trains models
against arbitrary tabular data supplied at runtime.

The complexity comes from three areas that don't appear elsewhere in the
course's projects:

**A generative-AI integration with real fallback behavior.** Two separate
LangChain/Gemini calls exist in this project — one to describe an uploaded
dataset (`dataset_commentary.py`) and one to explain a trained model's
results in plain language (`result_commentary.py`). Both are grounded in
facts computed locally (column types, missing-value counts, duplicate rows,
per-column min/max/mean, or the model name and metric) rather than asking
the LLM to guess from raw data, and both are wrapped so that a network
failure or API error degrades to a friendly "Commentary unavailable."
message instead of crashing the page. Because these calls are non-
deterministic and require network access, the test suite mocks them
explicitly rather than skipping coverage of the surrounding view logic.

**Real machine learning, not a canned demo.** `model_training.py` inspects
the uploaded dataset's target column at request time, decides whether the
problem is regression or classification based on its dtype, discards
non-numeric feature columns and any leftover index columns (`Unnamed: *`,
a common artifact of poorly-exported CSVs), imputes missing numeric values
with the column mean, scales features with `StandardScaler`, splits the
data 80/20, and trains either a `LinearRegression` or a `LogisticRegression`
with scikit-learn — reporting R² or accuracy on the held-out test set. This
logic was verified against a real 21,000-row real-estate dataset during
development, not just synthetic test fixtures.

**A genuinely multi-request architecture, not a single form.** Uploading a
file and running an experiment on it are two separate HTTP requests, days
or minutes apart, that both need the *full* dataset — not just the 5-row
preview persisted to the database. Rather than permanently storing every
uploaded file, the full parsed dataset is cached server-side (Django's
cache framework) keyed to the user's session for a short window after
upload. This was a deliberate architectural choice made after weighing
permanent file storage against session-scoped caching, and it shapes real,
user-visible behavior: an experiment must be run shortly after upload, in
the same browser session, or the app tells the user their data has expired
rather than silently failing.

Beyond those three areas, the app also uses Django's pagination framework
for upload history, a login-required section distinct from the public
login/register pages, a custom `AbstractUser`-based user model, three
migrations evolving the schema as the feature set grew, a `JSONField`-backed
`ExperimentResult` model designed to flexibly hold whatever shape of metrics
a given model type produces, and hand-rolled vanilla JavaScript (no
framework) for drag-and-drop file upload and a commentary show/hide toggle.
The test suite has 26 tests covering registration, authentication, upload
validation, dataset persistence, paginated history (including per-user
isolation, so one user can never see another's uploads), and the full
train-and-evaluate flow for both regression and classification.

## What's in each file

- **`capstone/capstone/settings.py`** — Django settings. Loads `GOOGLE_API_KEY`
  from a local `.env` file via `python-dotenv`, and sets `LOGIN_URL` for the
  login-required views.
- **`capstone/capstone/urls.py`** — root URL configuration; includes the app's URLs.
- **`capstone/ml_experiment_dashboard/models.py`** — `User` (custom auth
  model), `Experiment` (one uploaded dataset: its name, columns, row count, a
  5-row preview, and its AI commentary), `ExperimentResult` (the outcome of
  training a model against an `Experiment`, stored as flexible JSON since
  different model types produce different metrics).
- **`capstone/ml_experiment_dashboard/views.py`** — `index` (upload and
  validate a CSV, generate its AI commentary, cache the full dataset,
  display it); `history` (paginated, per-user list of past uploads);
  `run_experiment` (GET shows a target-column picker with no side effects;
  POST trains a model on the cached dataset and shows the results plus an AI
  explanation); `register`, `login`, `logout`.
- **`capstone/ml_experiment_dashboard/urls.py`** — the app's routes.
- **`capstone/ml_experiment_dashboard/dataset_commentary.py`** —
  `generate_dataset_commentary(df)`: computes real facts about the uploaded
  dataset and asks Gemini to summarize it and suggest a likely prediction
  target.
- **`capstone/ml_experiment_dashboard/model_training.py`** —
  `train_model(df, target_column)`: the actual ML training logic described
  above.
- **`capstone/ml_experiment_dashboard/result_commentary.py`** —
  `generate_result_commentary(result_data)`: asks Gemini to explain a
  trained model's results in plain language.
- **`capstone/ml_experiment_dashboard/admin.py`, `apps.py`** — standard
  Django app configuration.
- **`capstone/ml_experiment_dashboard/migrations/`** — `0001_initial.py`
  (base `User`/`Experiment`/`ExperimentResult` schema), `0002_*.py` (adds
  `columns`, `row_count`, `preview_rows`, `commentary` to `Experiment`),
  `0003_*.py` (adds `commentary` to `ExperimentResult`).
- **`capstone/ml_experiment_dashboard/templates/ml_experiment_dashboard/`**
  — `layout.html` (shared navigation and page shell), `index.html` (upload
  form, dataset preview, commentary, and the "Run Experiment" entry point),
  `history.html` (paginated past uploads), `run_experiment.html`
  (target-column picker and training results), `login.html`, `register.html`.
- **`capstone/ml_experiment_dashboard/static/ml_experiment_dashboard/`** —
  `scripts.js` (drag-and-drop upload handling, AI-commentary show/hide
  toggle), `styles.css`.
- **`capstone/ml_experiment_dashboard/test_files/`** — small CSV/TXT
  fixtures used only by the automated test suite.
- **`capstone/ml_experiment_dashboard/tests.py`** — 26 tests covering every
  view and the full upload-to-training flow.
- **`requirements.txt`** — Python dependencies: `pandas`, `langchain`,
  `langchain-google-genai`, `python-dotenv`, `scikit-learn`.

## How to run the application

1. Clone this repository and `cd` into `capstone/capstone` (the folder
   containing `manage.py`).
2. Install dependencies: `pip install -r ../requirements.txt`.
3. Create a file named `.env` in `capstone/capstone` (the same folder as
   `manage.py`) containing:
   ```
   GOOGLE_API_KEY=your-key-from-google-ai-studio
   ```
   This is optional but recommended — without it, uploads and experiments
   still work, but the AI commentary will show "Commentary unavailable."
   Google AI Studio issues free-tier API keys.
4. Apply migrations: `python manage.py migrate`.
5. Start the server: `python manage.py runserver`.
6. Visit `http://127.0.0.1:8000`, register an account, and upload a CSV
   file with a header row and at least 5 rows of data to try it out.

To run the automated test suite (from the same directory):
`python manage.py test`. All 26 tests run without any API key or network
access, since the Gemini calls are mocked in tests that don't need to
exercise them.

## Additional information for graders

- The full uploaded dataset is intentionally **not** stored permanently —
  only a 5-row preview and derived stats are saved to the database. The
  complete dataset lives in a short-lived server-side cache tied to the
  browser session, so running an experiment only works shortly after
  uploading, in the same session. This is a deliberate scope decision, not
  a bug: visiting an old entry in the upload history will show its stats and
  commentary, but not offer a "Run Experiment" action, since the data that
  action needs is no longer available.
- Model training currently only uses numeric feature columns automatically
  (categorical features are excluded rather than encoded) and chooses
  between exactly two algorithms based on the target column's type. This
  keeps the feature auto-selection simple and predictable; adding
  categorical encoding or letting a user choose the algorithm manually would
  be natural next steps.
