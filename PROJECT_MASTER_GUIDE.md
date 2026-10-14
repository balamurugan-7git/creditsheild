# CrediShield AI: Complete Master Technical Guide & System Documentation
> **Comprehensive System Specification, Architecture, Codebase Breakdown, Machine Learning Pipeline, Backend APIs, Security, and Cloud Deployment Guide.**  
> *Designed for Project Defense, Technical Interviews, and LLM-assisted learning.*

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [High-Level Architecture & Tech Stack](#2-high-level-architecture--tech-stack)
3. [Complete Codebase Directory & File-by-File Breakdown](#3-complete-codebase-directory--file-by-file-breakdown)
4. [Machine Learning Pipeline & Explainable AI (XAI) Deep Dive](#4-machine-learning-pipeline--explainable-ai-xai-deep-dive)
5. [Backend Architecture, Database & Security Engine](#5-backend-architecture-database--security-engine)
6. [Frontend Architecture & Explainability Visualizations](#6-frontend-architecture--explainability-visualizations)
7. [End-to-End Runtime Data Flow](#7-end-to-end-runtime-data-flow)
8. [DevOps, Infrastructure-as-Code & Render Cloud Deployment](#8-devops-infrastructure-as-code--render-cloud-deployment)
9. [Comprehensive Technical Interview & Viva Q&A Guide](#9-comprehensive-technical-interview--viva-qa-guide)

---

## 1. Executive Summary & Problem Statement

### 1.1 The Industry Problem
In commercial lending and retail banking, credit assessment has historically relied on static credit bureau scorecards (e.g., FICO) or manual underwriting. With the advent of machine learning, financial institutions can leverage high-dimensional tabular datasets (such as the **Home Credit Default Risk** dataset) to predict the likelihood of default with far greater statistical power than classical logistic regression.

However, deploying ML models in banking introduces three critical challenges:
1. **The "Black Box" Problem:** High-performing models (such as XGBoost or ensemble gradient boosted trees) are non-linear and opaque. Regulatory frameworks—including the **U.S. Equal Credit Opportunity Act (ECOA)**, the **Fair Credit Reporting Act (FCRA)**, and the **EU Artificial Intelligence Act**—strictly mandate that financial institutions must provide clear, actionable reasons when adverse actions (rejections) are taken against an applicant.
2. **Target Leakage:** Training models on features recorded *after* loan approval (e.g., historical repayment status or post-disbursement telemetry) artificially inflates accuracy during training but causes catastrophic failure in live production.
3. **Rigid Binary Cutoffs:** Traditional classification uses an arbitrary 0.50 probability cutoff. In credit underwriting, the cost of a **False Negative** (approving a borrower who defaults, losing 100% of the loan principal) is significantly higher than the cost of a **False Positive** (rejecting a creditworthy borrower, forfeiting only marginal interest revenue).

### 1.2 The CrediShield AI Solution
**CrediShield AI** is an enterprise-grade, full-stack credit risk scoring platform built to solve these industry challenges:
* **XGBoost Classifier:** Trained exclusively on pre-decision application features (Bucket A) with class-weight optimization for extreme data imbalance.
* **SHAP (SHapley Additive exPlanations) TreeExplainer:** Computes game-theoretic local feature attributions for every loan scoring request in real-time, explaining precisely *why* an applicant was categorized into their risk tier.
* **Three-Tier Cost-Optimized Decision Policy:** Replaces naive binary classification with an optimized 3-zone system:
  * **Approved** ($p < 0.35$): Automated low-risk fast-track.
  * **Manual Review** ($0.35 \le p \le 0.65$): Uncertain risk requiring human underwriter scrutiny.
  * **Rejected** ($p > 0.65$): Automated high-risk rejection.
* **Human-in-the-Loop (HITL) Governance:** A dedicated loan officer portal where credit underwriters can inspect SHAP waterfall explanations, review applicant features, and apply audit-logged decision overrides with mandatory regulatory justification.
* **Modern Cloud Native Microservice Architecture:** Python 3.11, FastAPI, SQLAlchemy ORM with MySQL/SQLite support, JWT authentication, Bcrypt password hashing, React 18, TypeScript, TailwindCSS, and automated Infrastructure-as-Code deployment via Render.

---

## 2. High-Level Architecture & Tech Stack

```
                              ┌───────────────────────────────────────────────┐
                              │            CLIENT BROWSER (User)              │
                              │  React 18 + TypeScript + Vite + TailwindCSS   │
                              └──────────────────────┬────────────────────────┘
                                                     │ HTTPS (REST / JSON)
                                                     ▼
                              ┌───────────────────────────────────────────────┐
                              │           FASTAPI BACKEND ENGINE              │
                              │             (Uvicorn / Python 3.11)           │
                              ├───────────────────────────────────────────────┤
                              │ • SlowAPI Rate Limiter (10 req/min)           │
                              │ • CORS Security Middleware (Regex matching)   │
                              │ • OAuth2 Password Bearer & JWT Token Handler  │
                              │ • Pydantic v2 Request / Response Validation   │
                              └───────┬───────────────────────────────┬───────┘
                                      │                               │
             ┌────────────────────────┴────────┐      ┌───────────────┴───────────────┐
             │                                 │      │                               │
             ▼                                 ▼      ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│     SQLAlchemy ORM        │   │    ModelService (ML)      │   │   Drift Monitor (PSI)     │
│   (Relational Database)   │   │  • XGBoost Classifier     │   │ • Population Stability    │
├───────────────────────────┤   │  • SHAP TreeExplainer     │   │   Index Engine            │
│ • Users Table (Auth/RBAC) │   │  • Cost Policy Engine     │   │ • Baseline vs Production  │
│ • Applications Table      │   │  • Preprocessing Pipeline │   │   Distribution Comparison │
│   (Payloads & Overrides)  │   └──────────────┬────────────┘   └───────────────────────────┘
└────────────┬──────────────┘                  │
             │                                 ▼
             ▼                   ┌───────────────────────────┐
┌───────────────────────────┐    │    Serialized Artifacts   │
│  MySQL / SQLite Database  │    │ • model_v1.joblib         │
│  (credishield.db / MySQL) │    │ • model_v1_meta.json      │
└───────────────────────────┘    └───────────────────────────┘
```

### 2.1 Technology Stack Matrix

| Layer | Technology | Version | Purpose in CrediShield AI |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | `>=0.111.0` | Asynchronous high-performance REST API routing, dependency injection, and OpenAPI Swagger documentation generation. |
| **ASGI Server** | **Uvicorn** | `>=0.29.0` | Production lightning-fast ASGI web server worker for Python. |
| **Data Validation** | **Pydantic v2** | `>=2.7.0` | Strict data parsing, type coercion, and schema enforcement with `email-validator`. |
| **Database ORM** | **SQLAlchemy** | `>=2.0.0` | Object Relational Mapping connecting Python classes to relational database tables. |
| **Database Drivers** | **PyMySQL / SQLite** | `>=1.1.0` | MySQL database connection driver and built-in SQLite engine for local/production persistence. |
| **Security & Auth** | **python-jose & bcrypt**| `>=3.3.0` | Cryptographic JWT token generation/validation (HS256) and one-way salted password hashing. |
| **Rate Limiting** | **SlowAPI** | `>=0.1.9` | IP-based rate limiting protecting machine learning endpoints against denial-of-service (DoS) bursts. |
| **Machine Learning** | **XGBoost** | `>=2.0.0` | Gradient-boosted decision trees optimized with class weighting for default risk classification. |
| **Explainable AI** | **SHAP** | `>=0.44.0` | Game-theoretic feature attribution calculating exact local Shapley values for model transparency. |
| **Data Processing** | **Scikit-Learn / Pandas**| `>=1.4.0` | `ColumnTransformer`, `StandardScaler`, `OneHotEncoder`, and tabular dataframe transformations. |
| **Model Packaging** | **Joblib** | `>=1.3.0` | High-efficiency compression and disk serialization of trained pipelines and transformers. |
| **Frontend Framework**| **React 18** | `^18.3.1` | Declarative component UI library for reactive single-page application (SPA) rendering. |
| **Programming Lang** | **TypeScript** | `^5.4.0` | Compile-time type safety preventing frontend runtime exceptions across API models. |
| **Styling & Icons** | **TailwindCSS & Lucide**| `^3.4.0` | Utility-first responsive CSS styling paired with clean financial UI iconography. |
| **Data Visualization**| **Recharts** | `^2.12.0` | SVG-based responsive data visualization rendering the interactive semi-circular risk gauge. |
| **State & Querying** | **TanStack React Query**| `^5.40.0` | Asynchronous server-state management, automated cache invalidation, and mutation handling. |
| **Cloud Hosting** | **Render** | Cloud Native| Automated Git-backed continuous deployment for Web Service and Static Site using `render.yaml`. |

---

## 3. Complete Codebase Directory & File-by-File Breakdown

```text
credishield/
├── ml/                                 # MACHINE LEARNING ENGINE
│   ├── artifacts/                      # Compiled ML models & metadata
│   │   ├── model_v1.joblib             # Serialized preprocessor + XGBoost pipeline
│   │   └── model_v1_meta.json          # Pipeline metadata (features, metrics, timestamps)
│   ├── notebooks/                      # Exploratory Data Analysis & experiments
│   │   ├── 01_eda.ipynb                # Feature distribution & correlation analysis
│   │   ├── 02_leakage_checklist.ipynb  # Bucket A vs Bucket B leakage exclusion logic
│   │   └── 03_training.ipynb           # Model training, threshold sweep & SHAP validation
│   ├── scripts/                        # Production operations & batch processing
│   │   └── run_psi_monthly.py          # CLI script for monthly PSI data drift reports
│   ├── src/                            # Production ML source code
│   │   ├── monitoring/                 # Drift monitoring
│   │   │   ├── __init__.py
│   │   │   └── psi.py                  # Population Stability Index computation engine
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # Core ETL, ColumnTransformer, XGBoost & SHAP code
│   │   ├── serialize.py                # Joblib serialization & artifact dataclass
│   │   └── thresholds.py               # Cost-based sweeps & Youden's J statistic
│   ├── tests/                          # Pytest test suite for ML logic
│   │   ├── test_pipeline.py            # Unit tests for preprocessing & leakage
│   │   ├── test_psi.py                 # Tests for PSI drift calculation
│   │   └── test_thresholds.py          # Tests for risk cutoffs and cost matrix
│   └── requirements.txt                # ML standalone dependencies
│
├── backend/                            # FASTAPI BACKEND SERVICE
│   ├── alembic/                        # Database migration scripts
│   ├── app/
│   │   ├── routes/                     # REST API Endpoint Routers
│   │   │   ├── __init__.py
│   │   │   ├── applications.py         # /applications (scoring, listing, detail, overrides)
│   │   │   ├── auth.py                 # /auth (register, token login, me)
│   │   │   └── health.py               # /health (database & model liveness check)
│   │   ├── services/                   # Business Logic & Model Serving Singletons
│   │   │   ├── __init__.py
│   │   │   ├── policy.py               # Threshold evaluation & classification service
│   │   │   └── prediction.py           # ModelService singleton (XGBoost + SHAP inference)
│   │   ├── __init__.py
│   │   ├── auth.py                     # Bcrypt hashing, JWT generation, get_current_user
│   │   ├── config.py                   # Pydantic BaseSettings loading .env
│   │   ├── database.py                 # SQLAlchemy engine, session maker, create_tables
│   │   ├── main.py                     # FastAPI application factory, CORS, Lifespan, RateLimit
│   │   ├── models.py                   # SQLAlchemy ORM models (User, Application)
│   │   └── schemas.py                  # Pydantic request/response validation schemas
│   ├── policy/
│   │   └── thresholds.json             # Runtime threshold configuration
│   ├── tests/                          # Backend Pytest suite
│   ├── .env.example                    # Sample environment variable template (MySQL & SQLite)
│   ├── pytest.ini                      # Pytest configuration
│   └── requirements.txt                # Python backend dependencies
│
├── frontend/                           # REACT + TYPESCRIPT WEB APPLICATION
│   ├── public/                         # Static assets & favicon
│   ├── src/
│   │   ├── api/                        # HTTP Networking layer
│   │   │   ├── applications.ts         # Application submission, query, and override API calls
│   │   │   ├── auth.ts                 # Login, register, and profile API calls
│   │   │   └── client.ts               # Pre-configured Axios instance, interceptors, dynamic URL
│   │   ├── components/                 # Reusable UI widgets
│   │   │   ├── ui/                     # Base design system (Button, Input, Badge, Card)
│   │   │   ├── ApplicationForm.tsx     # Multi-step credit application form with Zod validation
│   │   │   ├── ApplicationTable.tsx    # Paginated data table for applications
│   │   │   ├── Navbar.tsx              # Top navigation bar with user profile & logout
│   │   │   ├── OverrideModal.tsx       # Loan Officer decision override modal dialog
│   │   │   └── RiskResultCard.tsx      # Half-donut gauge chart & SHAP factor explanation list
│   │   ├── context/
│   │   │   └── AuthContext.tsx         # React Context managing JWT, user profile & session
│   │   ├── hooks/
│   │   │   └── usePrediction.ts        # TanStack Query mutation & query custom hooks
│   │   ├── pages/                      # Application route views
│   │   │   ├── ApplicantDashboard.tsx  # Applicant view: apply for loan & review personal history
│   │   │   ├── ApplicationDetail.tsx   # Detailed audit view: raw payload, gauge, SHAP, override
│   │   │   ├── Login.tsx               # User sign-in page
│   │   │   ├── OfficerDashboard.tsx    # Loan officer queue: KPI metrics, filterable review table
│   │   │   └── Register.tsx            # New account creation page with role selection
│   │   ├── types/
│   │   │   └── index.ts                # TypeScript interfaces matching backend Pydantic schemas
│   │   ├── App.tsx                     # React Router v6 setup & ProtectedRoute guards
│   │   ├── index.css                   # TailwindCSS root styling directives
│   │   └── main.tsx                    # React application root entrypoint
│   ├── package.json                    # Node.js dependencies & build scripts
│   ├── tsconfig.json                   # TypeScript compiler configuration
│   └── vite.config.ts                  # Vite build tool configuration & local dev proxy
│
├── .python-version                     # Runtime Python version lock (3.11.9)
├── README.md                           # Project documentation overview
└── render.yaml                         # Render Infrastructure-as-Code Blueprint configuration
```

---

## 4. Machine Learning Pipeline & Explainable AI (XAI) Deep Dive

### 4.1 Dataset & Target Leakage Prevention
The modeling engine is built around the **Home Credit Default Risk** benchmark dataset.
* **Target Variable:** `TARGET` (Binary: `0` = Borrower repaid loan on time, `1` = Borrower experienced payment default / delinquency).
* **Class Imbalance:** In real-world banking and in this dataset, only ~8% of applicants default ($1:11$ positive-to-negative ratio). A naive model predicting all `0` would achieve 92% accuracy while completely failing to detect credit risk.

#### The Bucket Separation Principle:
To guarantee production integrity, all dataset columns were partitioned into two strict buckets:
* **Bucket A (Permitted Pre-Decision Features):** Information known at the exact second the borrower submits the application.
  * *Demographics:* `CODE_GENDER`, `DAYS_BIRTH` (age), `NAME_EDUCATION_TYPE`, `NAME_FAMILY_STATUS`, `NAME_HOUSING_TYPE`, `CNT_CHILDREN`.
  * *Financials:* `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `NAME_INCOME_TYPE`, `DAYS_EMPLOYED`.
  * *External Bureau Proxies:* `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3` (normalized normalized scores from external rating agencies).
* **Bucket B (Strictly Excluded Post-Decision Features - Leakage):** Features generated after approval or during loan servicing (e.g., historical delinquency days on current credit, repayment installment records, closure timestamps). Using these in training causes **target leakage**, rendering the model useless on live applicants.

### 4.2 Data Cleaning & Scikit-Learn Pipeline (`pipeline.py`)
```python
# 1. Handling the employment anomaly:
# In Home Credit data, unemployed/retired individuals have DAYS_EMPLOYED = 365243 (~1000 years).
# We map 365243 -> NaN so the imputer can treat it as missing data.
df['DAYS_EMPLOYED'] = df['DAYS_EMPLOYED'].replace(365243, np.nan)

# 2. Scikit-Learn ColumnTransformer:
preprocessor = ColumnTransformer(
    transformers=[
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), numerical_cols),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]), categorical_cols)
    ]
)
```

### 4.3 XGBoost Classifier Training
* **Algorithm:** Extreme Gradient Boosting (`xgboost.XGBClassifier`).
* **Objective Function:** `binary:logistic`.
* **Handling Imbalance:** Set `scale_pos_weight = sum(negative_instances) / sum(positive_instances)` (~11.3). This penalizes the loss function heavily when a defaulting applicant is misclassified as non-defaulting.
* **Evaluation Metrics:**
  * **ROC-AUC (Receiver Operating Characteristic Area Under Curve):** Measures discrimination ability across all thresholds ($\approx 0.76 - 0.78$ on Bucket A features).
  * **PR-AUC (Precision-Recall AUC):** Evaluates performance specifically on the rare minority default class.
  * **F1-Score, Precision, and Recall.**

### 4.4 Explainable AI (XAI) via SHAP TreeExplainer
Traditional feature importance (e.g., Gini gain) gives global importance across the entire dataset, but **cannot explain an individual borrower's decision**. CrediShield AI uses **SHAP (SHapley Additive exPlanations)** based on cooperative game theory:

$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{i\}) - f_x(S) \right]$$

Where:
* $F$ is the complete set of all features.
* $S$ is a subset of features excluding feature $i$.
* $\phi_i(x)$ is the marginal contribution (Shapley value) of feature $i$ to applicant $x$'s default probability.

#### Implementation in CrediShield AI:
```python
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_transformed)

# Top factors extraction:
# If shap_value > 0 -> pushes probability UP -> 'increases_risk' (Red flag)
# If shap_value < 0 -> pushes probability DOWN -> 'decreases_risk' (Green flag)
```
For every application scored, CrediShield extracts the **Top 5 SHAP factors**, translates technical feature keys into human-readable labels (e.g., `EXT_SOURCE_2` $\rightarrow$ *"External Credit Score 2"*), and displays them with directional arrows in the UI.

### 4.5 Decision Policy Optimization (`thresholds.py`)
Rather than using a fixed 0.50 cutoff, CrediShield uses a dual optimization strategy:
1. **Youden's J Statistic:**
   $$J = \text{Sensitivity} + \text{Specificity} - 1 = \text{TPR} - \text{FPR}$$
   Finds the point on the ROC curve that maximizes separation between classes.
2. **Cost-Based Threshold Sweep:**
   $$\text{Total Cost} = C_{\text{FN}} \cdot \text{False Negatives} + C_{\text{FP}} \cdot \text{False Positives}$$
   Setting the cost ratio $\frac{C_{\text{FN}}}{C_{\text{FP}}} = 5.0$ reflects that loan defaults cost ~5x more than rejecting a good applicant.

This establishes our **3-Tier Decision Policy**:
* $p < 0.35 \implies$ **APPROVED** (Low default risk)
* $0.35 \le p \le 0.65 \implies$ **MANUAL REVIEW** (Human underwriter evaluation required)
* $p > 0.65 \implies$ **REJECTED** (High default risk)

### 4.6 Population Stability Index (PSI) Data Drift Monitoring (`psi.py`)
Over time, economic changes (inflation, interest rates) cause the distribution of new loan applicants to drift away from the training distribution. The PSI engine calculates:

$$\text{PSI} = \sum_{b=1}^{B} \left( \% \text{ Actual}_b - \% \text{ Expected}_b \right) \times \ln\left( \frac{\% \text{ Actual}_b}{\% \text{ Expected}_b} \right)$$

* $\text{PSI} < 0.1$: **Stable** (No change in applicant distribution).
* $0.1 \le \text{PSI} \le 0.2$: **Warning** (Moderate shift; schedule model review).
* $\text{PSI} > 0.2$: **Significant Drift** (Significant population shift; trigger automated retraining alerts).

---

## 5. Backend Architecture, Database & Security Engine

### 5.1 Relational Database Architecture (`models.py`)
The system supports both **MySQL** (production/scalable) and **SQLite** (local development/zero-config) seamlessly via SQLAlchemy ORM.

#### 1. `users` Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'applicant', -- 'applicant' | 'loan_officer'
    full_name VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX ix_users_email ON users(email);
```

#### 2. `applications` Table
```sql
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    input_features JSON NOT NULL,            -- Raw 120+ feature input payload
    probability FLOAT NOT NULL,              -- Predicted default probability (0.0 to 1.0)
    decision VARCHAR(50) NOT NULL,           -- 'approved' | 'manual_review' | 'rejected'
    model_version VARCHAR(50) NOT NULL,      -- e.g. 'v1'
    shap_top_factors JSON NOT NULL,          -- Top 5 SHAP factors with impact & direction
    officer_override VARCHAR(50) NULL,       -- 'approved' | 'rejected' (if overridden)
    override_reason TEXT NULL,               -- Mandatory justification text (min 10 chars)
    override_by INT NULL,                    -- Foreign key to users(id) of loan officer
    override_at DATETIME NULL,               -- Timestamp when override was recorded
    scored_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES users(id),
    FOREIGN KEY (override_by) REFERENCES users(id)
);
```

### 5.2 Password Security & JWT Authentication (`auth.py`)
* **Password Hashing:** Passwords are never stored in plaintext. They are processed through **Bcrypt** with unique cryptographic salt:
  ```python
  def hash_password(password: str) -> str:
      pwd_bytes = password.encode("utf-8")[:72]
      return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")
  ```
* **JWT Token Issuance (OAuth2 Password Bearer):**
  When a user logs in, the `/api/auth/token` endpoint validates credentials and signs an **HS256 JSON Web Token** containing:
  ```json
  {
    "sub": "user@example.com",
    "role": "loan_officer",
    "exp": 1790203535
  }
  ```
* **Role-Based Access Control (RBAC):**
  FastAPI dependency injection enforces permissions before executing route handlers:
  ```python
  def require_role(role: str):
      def role_checker(current_user: User = Depends(get_current_user)) -> User:
          if current_user.role != role:
              raise HTTPException(status_code=403, detail="Forbidden")
          return current_user
      return role_checker
  ```

### 5.3 Model Service Singleton (`services/prediction.py`)
To prevent loading large machine learning models from disk on every HTTP request (which causes high latency and memory spikes), CrediShield initializes a **Singleton `ModelService`** during application startup inside FastAPI's **Lifespan** context manager:
* Loads `model_v1.joblib` and metadata into RAM once.
* Caches pre-computed transformers and the `shap.TreeExplainer`.
* Handles concurrent prediction requests efficiently with sub-100ms response times.

### 5.4 REST API Endpoint Inventory

| Method | Endpoint | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Registers a new user account with role selection. |
| `POST` | `/api/auth/token` | Public | Authenticates credentials and returns a Bearer JWT. |
| `GET` | `/api/auth/me` | Authenticated | Returns currently authenticated user profile. |
| `POST` | `/api/applications/` | Applicant / Officer | Submits application, triggers XGBoost & SHAP scoring, saves to DB. Rate-limited to 10 req/min. |
| `GET` | `/api/applications/` | Authenticated | Paginated application list. Automatically filtered: applicants see only their own, officers see all. |
| `GET` | `/api/applications/{id}` | Authenticated | Retrieves single application details, feature payload, and SHAP factors. |
| `PATCH` | `/api/applications/{id}/override` | **Loan Officer Only** | Records an underwriter decision override with mandatory audit justification. |
| `GET` | `/api/health` | Public | Returns database connectivity, timestamp, and model loaded status. |

---

## 6. Frontend Architecture & Explainability Visualizations

### 6.1 State Management & React Query Architecture
* **`AuthContext.tsx`:** Manages user authentication state, stores the JWT in `localStorage`, and validates session tokens against `/api/auth/me` on initial page load.
* **`client.ts`:** Pre-configured Axios instance. Injects `Authorization: Bearer <token>` dynamically. Intercepts `401 Unauthorized` responses to purge corrupted tokens and redirect cleanly to `/login`.
* **`usePrediction.ts`:** Uses **TanStack Query** (`useQuery` and `useMutation`). Features automatic cache invalidation: when an application is scored or overridden, the list query key is invalidated, causing the UI table to refresh automatically without a manual page reload.

### 6.2 Key UI Components
1. **`RiskResultCard.tsx` (The Explainability Engine):**
   * Uses **Recharts** to render an SVG half-donut gauge chart reflecting default risk percentage ($0\% - 100\%$).
   * Color-coded dynamically based on the 3 policy thresholds:
     * 🟢 Green ($< 35\%$): Low Risk / Approved
     * 🟡 Amber ($35\% - 65\%$): Medium Risk / Manual Review
     * 🔴 Red ($> 65\%$): High Risk / Rejected
   * Renders the **Top 5 SHAP factors** with directional badges (`increases risk` in red vs `decreases risk` in green) and numerical contribution weights.
2. **`OverrideModal.tsx` (Human-in-the-Loop Dialog):**
   * Accessible only to users with the `loan_officer` role.
   * Prompts the officer to select a new decision (`approved` or `rejected`) and enter an audit reason.
   * Validates reason length ($\ge 10$ characters) to prevent empty or uninformative audit logs.
3. **`ApplicationForm.tsx`:**
   * Multi-step loan submission form with field validation.
   * Captures demographic, employment, asset, and credit features.

---

## 7. End-to-End Runtime Data Flow

### Step-by-Step Scenario: Submitting and Overriding a Loan Application

```
[Borrower / Applicant]               [FastAPI Backend]                 [Database & ML Engine]
          │                                  │                                    │
          ├──── 1. POST /applications/ ─────►│                                    │
          │    (JSON Payload + Bearer JWT)   ├──── 2. Verify JWT & Rate Limit ───►│
          │                                  ├──── 3. Send to ModelService ──────►│
          │                                  │                                    ├─ Transform features
          │                                  │                                    ├─ XGBoost predict_proba
          │                                  │                                    ├─ SHAP TreeExplainer
          │                                  │                                    └─ Apply Thresholds
          │                                  │◄─── 4. Return Prediction + SHAP ───┤
          │                                  ├──── 5. INSERT INTO applications ──►│ (Save record)
          │◄─── 6. HTTP 201 Created ─────────┤                                    │
          │    (Probability, Decision, SHAP) │                                    │
          ▼                                  ▼                                    ▼
[Display Gauge (48%)]                                                              
[Status: MANUAL REVIEW]                                                            
          │                                                                        
          ▼                                                                        
[Loan Officer Logs In]                                                             
          │                                                                        
          ├──── 7. GET /applications/ ──────►│                                    │
          │                                  ├──── 8. SELECT * WHERE status... ──►│
          │◄─── 9. Return Applications List ─┤                                    │
          │                                  │                                    │
          ├──── 10. PATCH /override ────────►│ (Decision: Approved, Reason: "...")│
          │                                  ├──── 11. Enforce Role: loan_officer │
          │                                  ├──── 12. UPDATE applications ──────►│ (Save override)
          │◄─── 13. HTTP 200 OK ─────────────┤                                    │
          ▼                                  ▼                                    ▼
[Display Purple Audit Banner:                                                      
 "Overridden by Officer #2 on [Date] - Reason: Verified stable secondary income"]  
```

---

## 8. DevOps, Infrastructure-as-Code & Render Cloud Deployment

The entire stack is configured for automated cloud deployment using a declarative **Render Blueprint (`render.yaml`)**.

### 8.1 Blueprint Specification (`render.yaml`)
```yaml
services:
  # ─── 1. FastAPI Python Backend Web Service ─────────────────────────────────
  - type: web
    name: credishield-api
    runtime: python
    plan: free
    region: oregon
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /api/health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: APP_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        value: "http://localhost:5173,https://credishield-web.onrender.com"
      - key: RATE_LIMIT
        value: "60/minute"
      - key: DATABASE_URL
        value: "sqlite:///./credishield.db"

  # ─── 2. React + Vite Frontend Static Site ──────────────────────────────────
  - type: web
    name: credishield-web
    runtime: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: "./frontend/dist"
    routes:
      - type: rewrite
        source: "/*"
        destination: "/index.html"
    envVars:
      - key: VITE_API_URL
        value: "https://credishield-api.onrender.com"
```

### 8.2 Key Deployment Problem-Solving Log
During deployment, two real-world architectural issues were resolved:
1. **Pydantic v2 Email Validator Missing Dependency:**
   * *Issue:* The backend build failed during startup with `ImportError: email-validator is not installed, run pip install 'pydantic[email]'`.
   * *Resolution:* Added `email-validator>=2.0.0` and `pydantic[email]>=2.7.0` to `backend/requirements.txt`.
2. **Python Version Pinning:**
   * *Issue:* Render defaulted to Python 3.14.3 preview which lacked pre-compiled binary wheels for heavy scientific packages (`xgboost`, `scipy`), triggering lengthy compilation timeouts.
   * *Resolution:* Pinned stable Python `3.11.9` via `.python-version` and `PYTHON_VERSION: 3.11.9` in `render.yaml`.
3. **Internal vs. Public API URL Resolution:**
   * *Issue:* Render’s `fromService: property: host` injected the private container hostname (`credishield-api`), which external browser clients could not resolve, causing white screen failures.
   * *Resolution:* Explicitly configured `VITE_API_URL: https://credishield-api.onrender.com` and implemented dynamic client-side hostname detection in `client.ts`.

---

## 9. Comprehensive Technical Interview & Viva Q&A Guide

### Q1: What is the core business problem CrediShield AI solves?
**Answer:** In retail lending, evaluating loan applications requires balancing default risk against business revenue. Most machine learning solutions act as "black boxes," which violates financial regulations (such as FCRA and the EU AI Act) requiring institutions to explain adverse credit decisions. CrediShield AI pairs an XGBoost classification model with SHAP (SHapley Additive exPlanations) to provide real-time, feature-level transparency for every credit decision, while implementing a cost-optimized 3-tier threshold policy with human underwriter decision overrides.

### Q2: What is target leakage and how did you prevent it?
**Answer:** Target leakage occurs when features that are only generated *after* a loan has been approved or serviced (e.g., late payment counts, transaction logs during the loan term) are included in training. This yields unrealistically high accuracy during training but causes catastrophic failure on live applications where those values cannot exist. We prevented this by establishing a strict Bucket Separation: **Bucket A** features (demographics, income, requested credit, external bureau ratings known at application time) were allowed; **Bucket B** features (post-decision repayment metrics) were strictly excluded.

### Q3: Why did you choose XGBoost over traditional Logistic Regression?
**Answer:** While Logistic Regression is natively interpretable, it assumes linear relationships between features and the log-odds of default, missing complex feature interactions (such as the interaction between debt-to-income ratio and external credit scores). XGBoost handles non-linearities, missing values, and complex interactions automatically. By combining XGBoost with SHAP, we obtain the predictive performance of gradient boosted decision trees alongside the interpretability of linear models.

### Q4: How does SHAP work mathematically and why is it superior to feature importances?
**Answer:** Standard tree feature importances (e.g., Gini impurity decrease) compute global feature importance across the entire dataset, but cannot explain why a *specific individual* was rejected. SHAP is grounded in cooperative game theory (Shapley values). It evaluates a feature's marginal contribution across all possible feature subsets. In CrediShield, SHAP produces exact positive and negative attributions summing from the base expected value of the population to the applicant’s final log-odds of default.

### Q5: Why did you avoid a 0.50 probability decision cutoff?
**Answer:** A naive 0.50 threshold assumes equal misclassification costs. In lending, a False Negative (approving a borrower who defaults) costs the institution the full loan principal, whereas a False Positive (rejecting a good borrower) only costs the lost marginal interest revenue. We performed a cost-based optimization sweep setting the cost ratio $C_{\text{FN}} / C_{\text{FP}} = 5.0$, combined with Youden’s J statistic ($\text{TPR} - \text{FPR}$). This established our three tiers: Approved ($< 0.35$), Manual Review ($0.35 - 0.65$), and Rejected ($> 0.65$).

### Q6: What is Human-in-the-Loop (HITL) and how is it implemented?
**Answer:** HITL ensures critical automated decisions can be audited and revised by human experts. When an applicant falls in the "Manual Review" range, the application is queued on the Loan Officer Dashboard. A loan officer reviews the SHAP risk attributions alongside any external mitigating documentation (e.g., verified co-signers, collateral). If an exception is warranted, the officer uses the `/override` endpoint, which mandates a 10+ character written justification and permanently records their officer ID, timestamp, and reasoning in the database for compliance auditing.

### Q7: How does JWT authentication work in this application?
**Answer:** When a user logs in via `POST /api/auth/token`, the backend checks the email and verifies the password using Bcrypt. If valid, it signs an HS256 JWT containing the user's email (`sub`) and role (`role`). The client stores this token in `localStorage` and attaches it as a `Bearer` token in the `Authorization` header for subsequent requests. FastAPI dependencies (`get_current_user`, `require_role`) decode and validate the token signature on each protected route.

### Q8: How is the database designed and how does it support MySQL?
**Answer:** We designed our data layer using SQLAlchemy ORM with two primary models: `User` and `Application`. We wrote database-agnostic models using standard SQLAlchemy types (`Integer`, `String`, `DateTime`, `JSON`). The application connects to SQLite locally (`sqlite:///./credishield.db`) and to MySQL in enterprise production (`mysql+pymysql://user:password@host:3306/db`) simply by updating the `DATABASE_URL` environment variable, requiring zero changes to business logic code.

### Q9: What is Population Stability Index (PSI) and why is it included?
**Answer:** PSI measures how much a categorical or continuous distribution has shifted between a reference baseline (training data) and a target dataset (production applications over the past month). In credit risk, macro-economic shifts (such as inflation spikes) change applicant distributions, leading to concept drift and model decay. A $\text{PSI} > 0.2$ indicates significant drift, alerting our engineering team to retrain the model.

### Q10: How did you handle high concurrency and model loading in FastAPI?
**Answer:** Loading an ML model from disk on every incoming HTTP request causes severe latency spikes and memory fragmentation. We implemented the **Singleton Pattern** via FastAPI's `lifespan` context manager. During application startup, `ModelService` loads the XGBoost model, the preprocessor, and the SHAP explainer into memory once. Incoming requests share this pre-loaded instance, achieving sub-100ms response times.
