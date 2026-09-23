# CrediShield AI

> **Full-Stack Loan Default Risk & Credit-Scoring Application**  
> Final Year Project · Portfolio / Proof-of-Concept

[![CI](https://github.com/your-org/credishield/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/credishield/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Tech Stack](#3-tech-stack)
4. [ML Model](#4-ml-model)
5. [Quick Start — Local Development](#5-quick-start--local-development)
6. [Docker Deployment](#6-docker-deployment)
7. [User Roles](#7-user-roles)
8. [API Endpoints](#8-api-endpoints)
9. [Testing](#9-testing)
10. [Drift Monitoring](#10-drift-monitoring)
11. [Project Structure](#11-project-structure)
12. [Out of Scope](#12-out-of-scope)
13. [Interview Summary](#13-interview-summary)
14. [License](#14-license)

---

## 1. Project Overview

**CrediShield AI** is a production-style, full-stack loan default risk and credit-scoring application built as a final-year capstone / portfolio piece. It demonstrates an end-to-end machine-learning system that ingests a loan application, scores it with an XGBoost model trained on the [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) Kaggle dataset, explains the decision with SHAP values, and persists everything to a PostgreSQL database — all served through a FastAPI backend and a React frontend.

### Purpose

This project is designed as a **portfolio and proof-of-concept** to showcase:

- Responsible ML engineering (leakage prevention, cost-based thresholds, explainability)
- Production-style API design (JWT auth, rate limiting, audit logging, two user roles)
- Modern full-stack web development (React 18 + TypeScript, Tailwind CSS)
- DevOps fundamentals (Docker Compose, GitHub Actions CI, Alembic migrations)
- Observational monitoring strategy (PSI-based drift detection)

### Key Features

| Feature | Details |
|---|---|
| 🔐 **JWT Authentication** | Secure register / login with role-based access control |
| 📊 **ML Risk Scoring** | XGBoost pipeline, ROC-AUC ≥ 0.77 on held-out validation set |
| 🔍 **SHAP Explainability** | Per-application feature-importance waterfall, cached at prediction time |
| ⚖️ **Cost-Based Thresholds** | Approved / Manual Review / Rejected bands set by cost optimisation, not guesswork |
| 📝 **Audit Logging** | Every prediction, override, and user action is logged in PostgreSQL |
| 🚦 **Rate Limiting** | Submission endpoint protected against abuse |
| 📈 **Drift Monitoring** | Monthly PSI script to detect covariate shift in production data |
| 🐳 **Docker Compose** | Single-command spin-up of all services |
| ✅ **CI Pipeline** | GitHub Actions runs lint + unit tests on every push |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                               │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                 React 18 + TypeScript SPA                   │   │
│   │   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │   │
│   │   │  Applicant   │  │ Loan Officer │  │  SHAP Waterfall │  │   │
│   │   │  Dashboard   │  │  Dashboard   │  │  Chart (D3.js)  │  │   │
│   │   └──────────────┘  └──────────────┘  └─────────────────┘  │   │
│   └──────────────────────────┬──────────────────────────────────┘   │
│                              │  HTTPS / REST JSON                   │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                       FASTAPI BACKEND                               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Auth Router │  │  App Router  │  │     Health Router        │  │
│  │  /api/auth/  │  │  /api/       │  │     /api/health          │  │
│  │              │  │  applications│  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘  │
│         │                 │                                         │
│  ┌──────▼─────────────────▼──────────────────────────────────────┐  │
│  │                   Services Layer                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │  │
│  │  │  AuthService │  │  ScoreService│  │   AuditService     │  │  │
│  │  │  JWT tokens  │  │  SHAP cache  │  │   Postgres log     │  │  │
│  │  └──────────────┘  └──────┬───────┘  └────────────────────┘  │  │
│  └───────────────────────────┼───────────────────────────────────┘  │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │  In-process model call
┌──────────────────────────────▼──────────────────────────────────────┐
│                         ML LAYER                                    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │   Scikit-learn Pipeline  →  XGBoost Classifier              │    │
│  │   • Imputer → OrdinalEncoder → XGBClassifier                │    │
│  │   • Class-weighted training (imbalanced TARGET)             │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                      │
│  ┌────────────────────────────▼────────────────────────────────┐    │
│  │   SHAP TreeExplainer  →  shap_values cached per application │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                      │
│  ┌────────────────────────────▼────────────────────────────────┐    │
│  │   Cost-Based Threshold Optimizer  →  thresholds.json        │    │
│  │   Bands: APPROVED | MANUAL REVIEW | REJECTED                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      DATA LAYER                                     │
│                                                                     │
│  ┌──────────────────────────┐    ┌──────────────────────────────┐   │
│  │     PostgreSQL DB        │    │   ML Artifacts (disk)        │   │
│  │  • users                 │    │  • pipeline.pkl              │   │
│  │  • applications          │    │  • thresholds.json           │   │
│  │  • audit_logs            │    │  • feature_names.json        │   │
│  └──────────────────────────┘    └──────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    MONITORING (OFFLINE)                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │   scripts/run_psi_monthly.py                                │    │
│  │   • Computes PSI between training baseline & production     │    │
│  │   • Flags features with PSI > 0.2 for review               │    │
│  │   • Outputs HTML drift report                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

### Machine Learning

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.11 |
| Pipeline | Scikit-learn | 1.4 |
| Classifier | XGBoost | 2.0 |
| Explainability | SHAP | 0.44 |
| Data manipulation | Pandas, NumPy | 2.x / 1.26 |
| Notebooks | Jupyter Lab | 4.x |
| Model serialisation | Joblib | 1.3 |

### Backend

| Component | Technology | Version |
|---|---|---|
| Framework | FastAPI | 0.111 |
| ASGI server | Uvicorn | 0.29 |
| ORM | SQLAlchemy | 2.0 |
| Migrations | Alembic | 1.13 |
| Database | PostgreSQL | 16 |
| Auth | Python-JOSE (JWT) | 3.3 |
| Password hashing | Passlib (bcrypt) | 1.7 |
| Rate limiting | SlowAPI | 0.1 |
| Validation | Pydantic | 2.x |
| Policy engine | OPA (optional) / custom | — |

### Frontend

| Component | Technology | Version |
|---|---|---|
| Framework | React | 18 |
| Language | TypeScript | 5.x |
| Build tool | Vite | 5.x |
| Styling | Tailwind CSS | 3.x |
| HTTP client | Axios | 1.x |
| Charts | Recharts + D3.js | — |
| Forms | React Hook Form | 7.x |
| State | React Context + useReducer | — |

### DevOps

| Component | Technology |
|---|---|
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |
| Linting (Python) | Ruff + Black |
| Linting (JS) | ESLint + Prettier |
| Type-checking | mypy (Python) / tsc (TS) |

---

## 4. ML Model

### Dataset — Home Credit Default Risk

The model is trained on the [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) Kaggle dataset (`application_train.csv` / `application_test.csv`).  
The binary target column `TARGET` indicates whether a client defaulted (`1`) or repaid (`0`). The dataset is heavily imbalanced (~8 % default rate).

### Leakage Exclusion Checklist

Before any feature engineering, an explicit **leakage-exclusion checklist** (`notebooks/02_leakage_checklist.ipynb`) was built to ensure that only **application-time** features are used in training.  
The following categories of columns are dropped or flagged:

| Category | Rule |
|---|---|
| Post-origination fields | Any column that is populated only after the loan is issued (e.g. repayment records) |
| Data-entry helpers | Internal IDs, surrogate keys (`SK_ID_CURR` used only as index) |
| Near-zero variance | Columns with > 80 % single value after imputation |
| Future-leaking aggregates | Bureau / previous-application columns that reference events post-application date |

### Preprocessing Pipeline

The Scikit-learn `Pipeline` object stored in `ml/artifacts/pipeline.pkl` consists of:

```
Pipeline([
    ('imputer',  ColumnTransformer([
                    ('num', SimpleImputer(strategy='median'), num_cols),
                    ('cat', SimpleImputer(strategy='most_frequent'), cat_cols),
                ])),
    ('encoder',  OrdinalEncoder(handle_unknown='use_encoded_value',
                                unknown_value=-1)),
    ('model',    XGBClassifier(
                    n_estimators=500,
                    learning_rate=0.05,
                    max_depth=6,
                    scale_pos_weight=<computed from class ratio>,
                    eval_metric='auc',
                    early_stopping_rounds=30,
                    use_label_encoder=False,
                    random_state=42,
                )),
])
```

`scale_pos_weight` is computed as `(count of negatives) / (count of positives)` to handle class imbalance explicitly.

### Validation Strategy

- **Stratified 5-fold cross-validation** on `application_train.csv`
- Final evaluation on a held-out 20 % stratified split
- Metrics reported: **Precision, Recall, F1-score, ROC-AUC**
- Threshold optimisation is performed on the validation fold only — never on the test fold

### SHAP Explainability

```python
explainer = shap.TreeExplainer(pipeline.named_steps['model'])
shap_values = explainer.shap_values(X_transformed)
```

- `TreeExplainer` is used (no sampling, exact Shapley values for tree models)
- SHAP values are **cached in the database** alongside each prediction to avoid recomputation at display time
- The frontend renders a waterfall chart showing the top-10 positive and negative feature contributions for each application

### Cost-Based Decision Thresholds

Rather than defaulting to 0.5, thresholds are derived by minimising a **business cost function** on the validation set:

```
Cost(threshold) = FN_cost × FN(threshold) + FP_cost × FP(threshold)
```

where:
- **FN (False Negative)** = approving a defaulter — assumed high cost (e.g. 5×)
- **FP (False Positive)** = rejecting a good applicant — assumed lower cost (e.g. 1×)

This produces **two threshold values** (t_low, t_high) that define three decision bands:

| Band | Condition | Action |
|---|---|---|
| **APPROVED** | P(default) < t_low | Auto-approve |
| **MANUAL REVIEW** | t_low ≤ P(default) < t_high | Route to loan officer |
| **REJECTED** | P(default) ≥ t_high | Auto-reject |

Thresholds are persisted to `ml/artifacts/thresholds.json` and loaded by the backend at startup.

---

## 5. Quick Start — Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 running locally
- A Kaggle account (to download dataset)

---

### Step 1 — Download the Dataset

```bash
# Create the data directories
mkdir -p ml/data/raw

# Option A: Kaggle CLI (recommended)
pip install kaggle
kaggle competitions download -c home-credit-default-risk -p ml/data/raw/
unzip ml/data/raw/home-credit-default-risk.zip -d ml/data/raw/

# Option B: Manual download
# Go to https://www.kaggle.com/c/home-credit-default-risk/data
# Download application_train.csv and application_test.csv
# Place them in ml/data/raw/
```

Required files in `ml/data/raw/`:
- `application_train.csv`
- `application_test.csv`

---

### Step 2 — ML Setup (Train the Model)

```bash
# Navigate to the ml directory
cd ml

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch Jupyter Lab
jupyter lab

# Run notebooks IN ORDER:
#   notebooks/01_eda.ipynb              - Exploratory data analysis
#   notebooks/02_leakage_checklist.ipynb - Feature leakage audit
#   notebooks/03_training.ipynb         - Train, validate, serialise model

# After running notebook 03, verify these artifacts exist:
ls artifacts/
# pipeline.pkl
# thresholds.json
# feature_names.json
```

---

### Step 3 — Backend Setup

```bash
# Navigate to the backend directory
cd ../backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your local PostgreSQL credentials and secret key:
#   DATABASE_URL=postgresql://user:password@localhost:5432/credishield
#   SECRET_KEY=your-very-long-random-secret-key
#   ALGORITHM=HS256
#   ACCESS_TOKEN_EXPIRE_MINUTES=60
#   MODEL_PATH=../ml/artifacts/pipeline.pkl
#   THRESHOLDS_PATH=../ml/artifacts/thresholds.json
#   FEATURE_NAMES_PATH=../ml/artifacts/feature_names.json

# Create the database (if it does not exist)
psql -U postgres -c "CREATE DATABASE credishield;"

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API docs available at:
#   http://localhost:8000/docs       (Swagger UI)
#   http://localhost:8000/redoc      (ReDoc)
```

---

### Step 4 — Frontend Setup

```bash
# Navigate to the frontend directory
cd ../frontend

# Install Node dependencies
npm install

# Configure the API base URL (optional — defaults to http://localhost:8000)
cp .env.example .env.local
# Edit .env.local:
#   VITE_API_BASE_URL=http://localhost:8000

# Start the development server
npm run dev

# App available at:
#   http://localhost:5173
```

---

## 6. Docker Deployment

Docker Compose orchestrates **four services**: `db` (PostgreSQL), `backend` (FastAPI), `frontend` (React via Nginx), and `ml-init` (one-shot container that runs Alembic migrations on first boot).

### Prerequisites

- Docker Desktop (Windows / macOS) or Docker Engine + Compose plugin (Linux)
- ML artifacts already generated (run Step 2 from Quick Start first)

### One-Command Spin-Up

```bash
# Clone the repository (if not already done)
git clone https://github.com/your-org/credishield.git
cd credishield

# Copy and configure root-level environment file
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SECRET_KEY, etc.

# Build images and start all services in detached mode
docker compose up --build -d

# Check service health
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs for a specific service
docker compose logs -f backend

# Run database migrations (handled automatically by ml-init service,
# but can be run manually if needed)
docker compose exec backend alembic upgrade head
```

### Service URLs

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### Stopping and Cleaning Up

```bash
# Stop all services (preserves volumes)
docker compose down

# Stop and remove all volumes (WARNING: deletes database data)
docker compose down -v

# Rebuild a single service without restarting others
docker compose up --build -d backend
```

### Docker Compose Environment Variables

| Variable | Description | Required |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `POSTGRES_DB` | Database name (default: `credishield`) | Yes |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | Yes |
| `ALGORITHM` | JWT algorithm (default: `HS256`) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL (default: `60`) | No |
| `RATE_LIMIT_PER_MINUTE` | Submissions per minute per IP (default: `5`) | No |

---

## 7. User Roles

CrediShield AI has **two scoped roles**. There is deliberately no super-admin role (see [Out of Scope](#12-out-of-scope)).

### Applicant (`role: applicant`)

An individual who wants to apply for a loan.

| Capability | Details |
|---|---|
| Register & log in | Create an account with email + password |
| Submit an application | POST to `/api/applications/` (rate-limited) |
| View own applications | GET list and detail of their own submissions only |
| See risk score & decision | View probability score, decision band, and SHAP explanation |
| Cannot | Access other applicants' data, override decisions, or view audit logs |

### Loan Officer (`role: officer`)

An employee of the lending institution.

| Capability | Details |
|---|---|
| Log in | Standard JWT login (account created by seeding / admin script) |
| View all applications | Full paginated list across all applicants |
| Search & filter | Filter by status, date range, risk band |
| Override decisions | PATCH `/api/applications/{id}/override` with a reason (logged) |
| View SHAP explanations | Inspect feature contributions for any application |
| View audit trail | See full history of status changes and overrides |
| Cannot | Create applications, modify user accounts, or access ML artifacts directly |

---

## 8. API Endpoints

All endpoints are prefixed with `/api`. Authentication uses **Bearer JWT** tokens.

| Method | Endpoint | Auth Required | Role | Description |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | No | — | Register a new applicant account |
| `POST` | `/api/auth/login` | No | — | Log in, receive JWT access token |
| `GET` | `/api/auth/me` | Yes | Any | Get current authenticated user's profile |
| `POST` | `/api/applications/` | Yes | Applicant | Submit a new loan application (rate-limited: 5 req/min) |
| `GET` | `/api/applications/` | Yes | Any | List applications (applicants see own; officers see all) |
| `GET` | `/api/applications/{id}` | Yes | Any | Get application detail including SHAP values |
| `PATCH` | `/api/applications/{id}/override` | Yes | Officer | Override the ML decision with a manual decision + reason |
| `GET` | `/api/health` | No | — | Health check — returns service status and model version |

### Request / Response Examples

#### `POST /api/auth/register`

```json
// Request
{
  "email": "alice@example.com",
  "password": "SecurePass123!",
  "full_name": "Alice Smith"
}

// Response 201
{
  "id": "uuid-here",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "role": "applicant",
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### `POST /api/applications/`

```json
// Request (subset of Home Credit features)
{
  "amt_income_total": 135000.0,
  "amt_credit": 450000.0,
  "amt_annuity": 22500.0,
  "name_contract_type": "Cash loans",
  "code_gender": "F",
  "flag_own_car": "N",
  "flag_own_realty": "Y",
  "cnt_children": 0,
  "name_income_type": "Working",
  "name_education_type": "Higher education",
  "name_family_status": "Single / not married",
  "days_birth": -12000,
  "days_employed": -2000,
  "region_population_relative": 0.035
}

// Response 201
{
  "id": "uuid-here",
  "status": "MANUAL_REVIEW",
  "default_probability": 0.31,
  "decision_band": "MANUAL_REVIEW",
  "shap_values": {
    "days_employed": -0.12,
    "amt_credit": 0.09,
    "amt_income_total": -0.07,
    "...": "..."
  },
  "created_at": "2025-01-15T10:05:00Z"
}
```

#### `PATCH /api/applications/{id}/override`

```json
// Request (officer only)
{
  "decision": "APPROVED",
  "reason": "Verified additional income documentation in person."
}

// Response 200
{
  "id": "uuid-here",
  "status": "APPROVED",
  "overridden_by": "officer@bank.com",
  "override_reason": "Verified additional income documentation in person.",
  "overridden_at": "2025-01-15T11:00:00Z"
}
```

#### `GET /api/health`

```json
// Response 200
{
  "status": "ok",
  "model_version": "v1.2.0",
  "thresholds": {
    "t_low": 0.18,
    "t_high": 0.42
  },
  "db": "connected",
  "uptime_seconds": 3600
}
```

---

## 9. Testing

### ML Tests

```bash
cd ml

# Activate virtual environment
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Run all ML unit tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_pipeline.py -v
pytest tests/test_thresholds.py -v
pytest tests/test_psi.py -v
```

### Backend Tests

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Run all backend tests (uses a separate test SQLite DB by default)
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test modules
pytest tests/test_auth.py -v
pytest tests/test_applications.py -v
pytest tests/test_scoring.py -v

# Run only fast unit tests (exclude integration tests)
pytest tests/ -v -m "not integration"
```

### Frontend Tests

```bash
cd frontend

# Run unit and component tests (Vitest)
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Type-check without building
npx tsc --noEmit

# Lint
npm run lint
```

### Full CI Run (local simulation)

```bash
# From the repo root — mimics what GitHub Actions runs
cd ml     && pytest tests/ -q && cd ..
cd backend && pytest tests/ -q && cd ..
cd frontend && npm run lint && npm run test -- --run && cd ..
echo "All checks passed."
```

---

## 10. Drift Monitoring

### Why Drift Monitoring?

A model trained on historical Home Credit data will degrade over time as the population of loan applicants changes — due to economic shifts, new credit products, or changes in data collection. CrediShield AI implements **Population Stability Index (PSI)** based drift monitoring as an offline, scheduled job.

### What is PSI?

PSI measures how much the distribution of a feature has shifted between a **baseline** (training data) and a **current** (production data) window:

```
PSI = Σ (Actual% − Expected%) × ln(Actual% / Expected%)
```

Interpretation:

| PSI Value | Interpretation | Action |
|---|---|---|
| < 0.10 | No significant shift | Monitor normally |
| 0.10 – 0.20 | Moderate shift | Investigate feature |
| > 0.20 | Significant shift | Flag for retraining review |

### Running the PSI Script

```bash
cd ml

# Activate virtual environment
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Run monthly drift check
# Compares training baseline (ml/data/processed/train_baseline.parquet)
# against production data exported from PostgreSQL
python scripts/run_psi_monthly.py \
  --baseline data/processed/train_baseline.parquet \
  --production data/processed/production_month.parquet \
  --output reports/drift_report_$(date +%Y_%m).html \
  --threshold 0.2

# The script will:
# 1. Load baseline feature distributions (saved during notebook 03)
# 2. Load current month's production data
# 3. Compute PSI for each feature
# 4. Print a summary table to stdout
# 5. Save an HTML report with plots to the specified output path
# 6. Exit with code 1 if any feature exceeds --threshold (useful for CI alerting)
```

### Scheduling

In production, this script would be scheduled via **cron** (Linux) or **Task Scheduler** (Windows):

```bash
# Example cron entry: run on the 1st of every month at 08:00
0 8 1 * * cd /app/ml && python scripts/run_psi_monthly.py \
  --baseline data/processed/train_baseline.parquet \
  --production data/processed/production_$(date +\%Y_\%m).parquet \
  --output reports/drift_$(date +\%Y_\%m).html >> logs/psi_cron.log 2>&1
```

### PSI Module

The core PSI logic lives in [`ml/src/monitoring/psi.py`](ml/src/monitoring/psi.py):

```python
def compute_psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    """
    Compute the Population Stability Index between two distributions.

    Parameters
    ----------
    expected : pd.Series  - baseline (training) distribution
    actual   : pd.Series  - current (production) distribution
    bins     : int        - number of bins for continuous features

    Returns
    -------
    float : PSI score
    """
```

### Triggering Retraining

This project does **not** implement automatic retraining (see [Out of Scope](#12-out-of-scope)).  
When PSI exceeds 0.2 on one or more features, the recommended manual workflow is:

1. Review the HTML drift report to identify which features shifted
2. Collect fresh labelled data (if available)
3. Re-run notebooks `01 → 02 → 03` with updated data
4. Evaluate new model vs. champion model on held-out set
5. Promote new `pipeline.pkl` via a pull request and redeploy

---

## 11. Project Structure

```
credishield/
│
├── ml/                                  # Machine Learning
│   ├── src/
│   │   ├── pipeline.py                  # Builds and trains the Scikit-learn pipeline
│   │   ├── thresholds.py                # Cost-based threshold optimisation
│   │   ├── serialize.py                 # Saves/loads pipeline.pkl & feature_names.json
│   │   └── monitoring/
│   │       └── psi.py                   # Population Stability Index computation
│   │
│   ├── notebooks/
│   │   ├── 01_eda.ipynb                 # Exploratory data analysis & visualisations
│   │   ├── 02_leakage_checklist.ipynb   # Explicit leakage audit & feature selection
│   │   └── 03_training.ipynb            # Training, validation, SHAP, serialisation
│   │
│   ├── data/
│   │   ├── raw/                         # Downloaded Kaggle CSVs (git-ignored)
│   │   │   ├── application_train.csv
│   │   │   └── application_test.csv
│   │   └── processed/                   # Cleaned parquet files (git-ignored)
│   │       ├── train_baseline.parquet
│   │       └── val.parquet
│   │
│   ├── scripts/
│   │   └── run_psi_monthly.py           # CLI script for scheduled drift monitoring
│   │
│   ├── tests/
│   │   ├── test_pipeline.py             # Unit tests for pipeline construction
│   │   ├── test_thresholds.py           # Unit tests for threshold optimiser
│   │   └── test_psi.py                  # Unit tests for PSI computation
│   │
│   ├── artifacts/                       # Serialised model artifacts (git-ignored)
│   │   ├── pipeline.pkl
│   │   ├── thresholds.json
│   │   └── feature_names.json
│   │
│   └── requirements.txt
│
├── backend/                             # FastAPI Backend
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory, CORS, lifespan hooks
│   │   ├── config.py                    # Pydantic Settings (reads from .env)
│   │   ├── database.py                  # SQLAlchemy engine & session factory
│   │   │
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── application.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/                     # Pydantic request / response schemas
│   │   │   ├── user.py
│   │   │   ├── application.py
│   │   │   └── health.py
│   │   │
│   │   ├── auth/
│   │   │   ├── jwt.py                   # Token creation & verification
│   │   │   ├── password.py              # Bcrypt hashing helpers
│   │   │   └── dependencies.py          # FastAPI Depends() for current user / role
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.py                  # /api/auth/* endpoints
│   │   │   ├── applications.py          # /api/applications/* endpoints
│   │   │   └── health.py                # /api/health endpoint
│   │   │
│   │   └── services/
│   │       ├── scoring.py               # Loads model, runs prediction, caches SHAP
│   │       └── audit.py                 # Writes to audit_logs table
│   │
│   ├── alembic/                         # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0001_create_users.py
│   │       ├── 0002_create_applications.py
│   │       └── 0003_create_audit_logs.py
│   │
│   ├── policy/
│   │   └── authz.py                     # Lightweight role-permission checks
│   │
│   ├── tests/
│   │   ├── conftest.py                  # Pytest fixtures (test client, test DB)
│   │   ├── test_auth.py
│   │   ├── test_applications.py
│   │   └── test_scoring.py
│   │
│   ├── .env.example                     # Template environment file
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                            # React 18 + TypeScript SPA
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── ApplicantDashboard.tsx
│   │   │   ├── OfficerDashboard.tsx
│   │   │   ├── ApplicationDetail.tsx
│   │   │   └── NewApplicationPage.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── NavBar.tsx
│   │   │   ├── ApplicationCard.tsx
│   │   │   ├── DecisionBadge.tsx
│   │   │   ├── ShapWaterfall.tsx        # D3.js SHAP waterfall chart
│   │   │   ├── OverrideModal.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   │
│   │   ├── api/
│   │   │   ├── axios.ts                 # Axios instance with JWT interceptor
│   │   │   ├── auth.ts                  # Auth API calls
│   │   │   └── applications.ts          # Applications API calls
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.tsx          # Global auth state via React Context
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useApplications.ts
│   │   │
│   │   ├── types/
│   │   │   ├── user.ts
│   │   │   └── application.ts
│   │   │
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   │   └── credishield-logo.svg
│   │
│   ├── .env.example
│   ├── Dockerfile
│   ├── nginx.conf                       # Nginx config for production SPA serving
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions: lint + test on push / PR
│
├── docker-compose.yml                   # Orchestrates db, backend, frontend services
├── .env.example                         # Root-level env template for Docker Compose
├── .gitignore
└── README.md
```

---

## 12. Out of Scope

The following items were deliberately **not built** as part of this project. They are documented here to demonstrate conscious scoping decisions rather than oversight.

| Item | Reason Not Included |
|---|---|
| **Admin role** | Two clearly scoped roles (applicant, officer) are sufficient for the proof-of-concept. A third role would add complexity without demonstrating new concepts. |
| **Live drift dashboard** | A real-time drift UI requires production traffic and a feature store. The offline PSI script is the appropriate first step. |
| **Automatic retraining pipeline** | Auto-retraining (MLflow, Airflow, Kubeflow) is a significant infrastructure concern beyond the scope of a final-year project. The monthly PSI script defines the trigger; retraining is manual. |
| **LLM / GenAI features** | No GPT-based explanation generation or chatbot. SHAP is sufficient and more interpretable for a regulated financial context. |
| **Fraud detection module** | Fraud is a separate ML problem requiring different labels and data sources. |
| **Multi-bureau data** | Only `application_train.csv` / `application_test.csv` are used. Bureau, POS, and instalment tables from Home Credit are excluded to keep the pipeline tractable. |
| **Mobile application** | A responsive React web app is sufficient for the target users. |
| **A/B testing framework** | Champion/challenger model comparison is noted as a future step but not implemented. |

---

## 13. Interview Summary

I built CrediShield AI, a full-stack loan default risk and credit-scoring application, using the Home Credit Kaggle dataset. Before modeling, I built an explicit leakage-exclusion checklist so only application-time features were used. The model is a Scikit-learn preprocessing pipeline with class-weighted XGBoost, validated with stratified cross-validation and evaluated on precision, recall, F1, and ROC-AUC. Decisions are explained per-application using SHAP's TreeExplainer, cached at prediction time for performance. Business thresholds for Approved, Manual Review, and Rejected are set by a cost-based optimization on the validation set rather than a guessed cutoff. The system is served through a FastAPI backend with JWT auth, two clearly scoped roles, rate limiting, and PostgreSQL persistence with full audit logging, and a React dashboard for applicants and loan officers. I also scoped out what I deliberately did not build — an admin role, a live drift dashboard, automatic retraining, and any LLM features — and documented monthly PSI-based drift monitoring as the next production step.

---

## 14. License

```
MIT License

Copyright (c) 2025 CrediShield AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Built with ❤️ as a Final Year Project · CrediShield AI · MIT License
</p>
