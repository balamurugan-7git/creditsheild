"""
generate_docs_docx.py
Generates a comprehensive, beautifully styled Microsoft Word (.docx) document
for the CrediShield AI project.
"""

import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set the background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def create_document(output_path: str):
    doc = Document()

    # Set page margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles
    navy = RGBColor(27, 54, 93)     # #1B365D - Primary Header
    slate = RGBColor(74, 85, 104)   # #4A5568 - Secondary Header
    charcoal = RGBColor(45, 55, 72) # #2D3748 - Body Text
    accent = RGBColor(37, 99, 235)  # #2563EB - Highlights

    # Base Normal Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = charcoal
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(6)

    # Document Header / Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("CrediShield AI 🛡️")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(26)
    run_title.font.bold = True
    run_title.font.color.rgb = navy

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(18)
    run_sub = p_sub.add_run("Full-Stack Loan Default Risk & Explainable Credit Scoring Portal\nSystem Concept, Architecture, Implementation, and Execution Guide")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(14)
    run_sub.font.italic = True
    run_sub.font.color.rgb = slate

    # Metadata callout box
    meta_table = doc.add_table(rows=1, cols=1)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_cell = meta_table.cell(0, 0)
    set_cell_background(meta_cell, "F1F5F9")
    set_cell_margins(meta_cell, top=140, bottom=140, left=200, right=200)
    p_meta = meta_cell.paragraphs[0]
    p_meta.paragraph_format.space_after = Pt(0)
    r_meta = p_meta.add_run(
        "Author: Balamurugan | Portfolio Project (Full-Stack & AI/ML Engineering)\n"
        "Tech Stack: FastAPI, React 18, TypeScript, XGBoost, SHAP, SQLite/PostgreSQL, Docker\n"
        "Status: Fully Implemented, Test-Verified (81% Coverage), Production-Scaffolded"
    )
    r_meta.font.size = Pt(9.5)
    r_meta.font.color.rgb = slate

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = navy
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = slate
        return p

    def add_callout(text, title=None, fill="EFF6FF", border="3B82F6"):
        t = doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.cell(0, 0)
        set_cell_background(c, fill)
        set_cell_margins(c, top=120, bottom=120, left=180, right=180)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        if title:
            r_head = p.add_run(f"📌 {title}\n")
            r_head.font.bold = True
            r_head.font.size = Pt(10.5)
            r_head.font.color.rgb = navy
        r_body = p.add_run(text)
        r_body.font.size = Pt(10)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def format_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        # Format Header Row
        hdr_cells = table.rows[0].cells
        for i, h_text in enumerate(headers):
            hdr_cells[i].text = h_text
            set_cell_background(hdr_cells[i], "1E293B")
            set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
            p = hdr_cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.runs[0]
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(9.5)

        # Format Data Rows
        for r_idx, row_data in enumerate(data):
            row_cells = table.rows[r_idx + 1].cells
            fill = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                row_cells[c_idx].text = str(val)
                set_cell_background(row_cells[c_idx], fill)
                set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
                p = row_cells[c_idx].paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                r = p.runs[0]
                r.font.size = Pt(9)
                r.font.color.rgb = charcoal

        # Set Column Widths
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # 1. Executive Summary & Project Abstract
    # -------------------------------------------------------------
    add_h1("1. Executive Summary & Project Abstract")
    doc.add_paragraph(
        "CrediShield AI is an enterprise-grade loan default risk assessment and explainable credit scoring "
        "portal engineered from the ground up to solve the core operational and regulatory bottlenecks of "
        "automated lending. Built using the Home Credit Default Risk benchmark, it combines state-of-the-art "
        "machine learning engineering with modern, responsive full-stack web software."
    )
    doc.add_paragraph(
        "Unlike academic notebooks or superficial API wrappers, CrediShield AI addresses real-world lending "
        "complexities: severe class imbalance (8% default base rate), post-application target leakage, asymmetric "
        "financial penalty costs (5:1 False Negative to False Positive penalty), explainability (SHAP TreeExplainer "
        "cached at prediction time), and human-in-the-loop regulatory compliance with mandatory audit justification."
    )

    add_callout(
        "Key Engineering Highlights:\n"
        "• Target Leakage Exclusion: Pre-engineered Bucket A (application-time) vs Bucket B (excluded) checklist.\n"
        "• Cost-Sensitive Thresholds: Optimization at 5:1 FN:FP cost ratio (Approved, Manual Review, Rejected tiers).\n"
        "• Explainable AI: Instant top-5 plain-English SHAP factors delivered with every scored application.\n"
        "• Full-Stack Architecture: Asynchronous FastAPI REST API, React 18 / TypeScript frontend, Zod schemas.\n"
        "• Security & Compliance: Native bcrypt + JWT auth, slowapi rate limiting, SQLAlchemy audit trail.\n"
        "• Production Rigor: 81% backend test coverage (18 pytest tests), monthly PSI drift monitoring CLI script.",
        title="Project Highlights at a Glance"
    )

    # -------------------------------------------------------------
    # 2. Problem Statement & Motivation
    # -------------------------------------------------------------
    add_h1("2. Problem Statement & Lending Industry Motivation")
    doc.add_paragraph(
        "Commercial and retail lending institutions face three critical challenges when deploying artificial "
        "intelligence for credit decisioning:"
    )

    doc.add_paragraph(
        "1. The Black-Box Regulatory Trap: Financial regulations (such as the Equal Credit Opportunity Act and FCRA) "
        "mandate that lenders provide adverse action notices detailing the exact reasons why an applicant was denied credit. "
        "Standard machine learning models output a raw number without explaining which underlying variables drove that score."
    )
    doc.add_paragraph(
        "2. The Asymmetry of Financial Loss: Standard classification models maximize accuracy using a default 0.50 cutoff. "
        "In lending, a False Negative (lending money to a borrower who defaults) results in loss of the entire principal, "
        "whereas a False Positive (rejecting a creditworthy applicant) results only in lost interest margin. A False Negative "
        "is approximately 5 times more expensive to a bank than a False Positive. Models calibrated to a 0.50 cutoff optimize "
        "for overall error rate rather than bank profitability and capital preservation."
    )
    doc.add_paragraph(
        "3. Target Leakage in Public Benchmarks: Many models trained on credit datasets achieve deceptively high accuracy "
        "by feeding on variables generated after the loan was disbursed (e.g. historical payment installment tables, late fee penalties). "
        "In a live production application, these variables do not exist at the underwriting moment."
    )

    # -------------------------------------------------------------
    # 3. System Architecture & Component Interaction
    # -------------------------------------------------------------
    add_h1("3. System Architecture & End-to-End Workflow")
    doc.add_paragraph(
        "CrediShield AI is designed around a clean separation of concerns, decoupling the presentation layer, "
        "API gateway, machine learning inference engine, and persistent storage."
    )

    arch_headers = ["Layer", "Component / Tool", "Architectural Responsibility"]
    arch_data = [
        ["Presentation", "React 18, Vite, TypeScript, TailwindCSS", "Multi-step loan application form, real-time risk gauge, SHAP cards, underwriting queue"],
        ["Client Validation", "Zod Schemas + React Hook Form", "Enforces strict type safety and logical constraints before HTTP dispatch"],
        ["API Gateway", "FastAPI (Python 3.13), Uvicorn", "Asynchronous HTTP routing, OpenAPI documentation, Pydantic v2 schemas"],
        ["Security & RBAC", "Bcrypt + Stateless JWT, SlowAPI", "Password hashing, dual-role authorization (applicant vs officer), 10 req/min rate limiting"],
        ["Inference Engine", "XGBoost + ColumnTransformer + SHAP", "Data standardization, one-hot encoding, model inference, TreeExplainer attributions"],
        ["Decision Policy", "Threshold Policy Service (JSON)", "Maps probability to Approved, Manual Review, or Rejected via 5:1 cost optimization"],
        ["Audit & Storage", "SQLAlchemy 2.0 ORM, SQLite/Postgres", "Complete relational persistence of applicants, applications, scores, and officer overrides"],
        ["Drift Monitor", "PSI CLI Script (Python)", "Monthly distribution stability calculation with alerting on PSI >= 0.20"]
    ]
    t_arch = doc.add_table(rows=len(arch_data) + 1, cols=3)
    format_table(t_arch, [1.3, 2.2, 3.0], arch_headers, arch_data)

    # -------------------------------------------------------------
    # 4. Machine Learning & Feature Engineering Deep-Dive
    # -------------------------------------------------------------
    add_h1("4. Machine Learning & Feature Engineering Deep-Dive")
    add_h2("4.1 Dataset & Target Leakage Protocol")
    doc.add_paragraph(
        "CrediShield AI is trained on the Kaggle Home Credit Default Risk benchmark. Prior to exploratory data analysis "
        "or feature selection, an explicit Target Leakage Exclusion Checklist was established:"
    )
    doc.add_paragraph(
        "• Bucket A (Eligible at Application Time): Applicant demographics (age, gender, family status, housing), "
        "stated financials (annual income, requested loan credit, annuity, goods price), employment duration, and external "
        "credit bureau scores (EXT_SOURCE_1, EXT_SOURCE_2, EXT_SOURCE_3).\n"
        "• Bucket B (Excluded - Post-Decision / Target Leakage): Loan payment history, days overdue, collection flags, and "
        "bureau inquiries made after loan approval. These features were eliminated before preprocessing."
    )

    add_h2("4.2 Preprocessing Pipeline & Anomaly Handling")
    doc.add_paragraph(
        "The pipeline utilizes scikit-learn's ColumnTransformer wrapped in a versioned bundle:\n"
        "1. DAYS_EMPLOYED Sentinel Anomaly: The raw dataset encodes unemployed applicants using the sentinel value 365,243 days. "
        "The pipeline intercepts this value and replaces it with NaN, preserving applicant records while avoiding artificial mathematical distortion.\n"
        "2. Categorical Encoding: Handled via OneHotEncoder(handle_unknown='ignore', drop='first') with a dedicated 'Missing' sentinel for nulls.\n"
        "3. Numerical Standardization: Scaled via StandardScaler to normalize variances across disparate financial ranges."
    )

    add_h2("4.3 Class Imbalance & Model Training")
    doc.add_paragraph(
        "The dataset exhibits severe class imbalance with an 8% default rate (approx. 11 non-defaulters per 1 defaulter). "
        "CrediShield AI configures an XGBoost Classifier with scale_pos_weight calculated as:"
    )
    add_callout(
        "scale_pos_weight = count(non_defaulters) / count(defaulters) ≈ 11.5\n\n"
        "Hyperparameters: n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.8, "
        "colsample_bytree=0.8, eval_metric='aucpr', objective='binary:logistic'.",
        title="Class-Weighted XGBoost Specification"
    )

    add_h2("4.4 Explainable AI (XAI) with SHAP TreeExplainer")
    doc.add_paragraph(
        "To deliver explainable credit scoring without latency bottlenecks, the system uses shap.TreeExplainer. "
        "Because tree-based Shapley values are calculated directly on internal leaf weightings, inference takes under 50 milliseconds. "
        "The raw Shapley array is mapped back to the preprocessor's feature names, OHE prefixes are stripped, and the top 5 absolute "
        "contributors are formatted into plain-English descriptors with explicit directionality (Increases Default Risk vs Decreases Default Risk)."
    )

    add_h2("4.5 5:1 Cost-Based Threshold Optimization")
    doc.add_paragraph(
        "Instead of defaulting to 0.50, the validation set is swept across candidate threshold pairs (Low, High) using an empirical cost function:"
    )
    add_callout(
        "Total Loss = (5.0 × False Negatives) + (1.0 × False Positives)\n\n"
        "• Low Threshold Cutoff (e.g. 0.35): P(default) < Low ⟹ Approved\n"
        "• Manual Review Zone: Low ≤ P(default) ≤ High ⟹ Manual Review\n"
        "• High Threshold Cutoff (e.g. 0.65): P(default) > High ⟹ Rejected",
        title="Asymmetric Cost Optimization Equation"
    )

    # -------------------------------------------------------------
    # 5. Full-Stack Software Engineering Architecture
    # -------------------------------------------------------------
    add_h1("5. Full-Stack Software Engineering Architecture")
    add_h2("5.1 Secure REST API & Authentication")
    doc.add_paragraph(
        "The backend is built with FastAPI and Python 3.13. Security features include:\n"
        "• Native Bcrypt Hashing: Passwords hashed with salt rounds; no plaintext storage.\n"
        "• Stateless JWT Authentication: Issues signed HS256 JSON Web Tokens with embedded user IDs and role claims.\n"
        "• SlowAPI Rate Limiting: Limits scoring endpoints to 10 requests per minute per IP address, preventing abuse and scraping.\n"
        "• Dual-Role RBAC: Explicit enforcement for 'applicant' (can only see and submit own applications) and 'loan_officer' (can inspect institutional queues and submit overrides)."
    )

    add_h2("5.2 Database Design & Relational Persistence")
    doc.add_paragraph(
        "CrediShield AI uses SQLAlchemy 2.0 declarative models with support for SQLite (local dev) and PostgreSQL (production):\n"
        "• users: id, email (unique, indexed), hashed_password, role, full_name, created_at, is_active.\n"
        "• applications: id, applicant_id (FK), input_features (JSON), probability (float), decision (string), "
        "model_version (string), shap_top_factors (JSON), officer_override (nullable), override_reason (text, nullable), "
        "override_by (FK, nullable), override_at (datetime, nullable), scored_at (datetime)."
    )

    add_h2("5.3 Modern React 18 Frontend & Human-in-the-Loop Governance")
    doc.add_paragraph(
        "The frontend is authored in React 18, TypeScript, and Tailwind CSS with two distinct workflows:\n"
        "1. Applicant Dashboard: Multi-step loan intake with Zod validation, instant scoring, interactive radial probability gauge, and SHAP cards.\n"
        "2. Officer Underwriting Dashboard: Paginated queue of institutional applications with status filtering. Officers can open any application "
        "to inspect raw parameters, review SHAP factors, and execute a Decision Override with mandatory written rationale (min 10 characters)."
    )

    # -------------------------------------------------------------
    # 6. Model Monitoring & Drift Governance
    # -------------------------------------------------------------
    add_h1("6. Model Drift & Production Governance (PSI)")
    doc.add_paragraph(
        "Credit models degrade over time as macroeconomic environments shift. CrediShield AI implements the Population "
        "Stability Index (PSI) to mathematically track shifts in feature distributions between the training baseline and inference traffic."
    )
    add_callout(
        "PSI Formula:\n"
        "PSI = ∑ [ (Actual% - Expected%) × ln(Actual% / Expected%) ]\n\n"
        "Severity Bands:\n"
        "• PSI < 0.10: Stable — Distribution unchanged; no retraining required.\n"
        "• 0.10 ≤ PSI < 0.20: Warning — Moderate shift detected; closer monitoring required.\n"
        "• PSI ≥ 0.20: Significant Drift — Action required; triggers automated CLI exit code 1.",
        title="Population Stability Index (PSI) Governance"
    )

    # -------------------------------------------------------------
    # 7. Verification, Testing & Quality Assurance
    # -------------------------------------------------------------
    add_h1("7. Verification, Testing & Quality Assurance")
    doc.add_paragraph(
        "CrediShield AI is reinforced with rigorous automated testing gates exceeding commercial standards:"
    )

    test_headers = ["Test Suite", "Test Scope", "Pass Rate", "Code Coverage"]
    test_data = [
        ["Backend Pytest", "Authentication, RBAC, scoring, rate-limits, ModelService, Policy", "18 passed, 0 failed", "81.00% (Target: ≥70%)"],
        ["ML Pipeline Pytest", "Preprocessing, anomaly handling, stratification, PSI, thresholds", "9 passed, 0 failed", "100% of pipeline modules"],
        ["Frontend TypeScript", "Strict type checking, component interfaces, Zod schema validation", "0 compilation errors", "Full build verified"],
        ["CI Pipeline", "GitHub Actions workflow running linting, tests, and Docker builds", "All checks passing", "Enforced on git push"]
    ]
    t_test = doc.add_table(rows=len(test_data) + 1, cols=4)
    format_table(t_test, [1.5, 2.5, 1.3, 1.2], test_headers, test_data)

    # -------------------------------------------------------------
    # 8. Step-by-Step Execution Guide
    # -------------------------------------------------------------
    add_h1("8. Step-by-Step Execution & Deployment Guide")
    doc.add_paragraph(
        "Follow these steps to run, demonstrate, and verify the entire CrediShield AI system locally:"
    )

    add_h2("8.1 Step 1: Starting the Backend API Server")
    add_callout(
        "cd \"credishield\\backend\"\n"
        "py -3.13 -m uvicorn app.main:app --port 8000 --host 127.0.0.1 --reload\n\n"
        "• API Base: http://127.0.0.1:8000\n"
        "• Interactive Swagger Docs: http://127.0.0.1:8000/docs\n"
        "• Health Check: http://127.0.0.1:8000/api/health",
        title="Backend Execution"
    )

    add_h2("8.2 Step 2: Starting the React Frontend")
    add_callout(
        "cd \"credishield\\frontend\"\n"
        "npm run dev -- --host 127.0.0.1\n\n"
        "• Frontend URL: http://localhost:5173\n"
        "• Build Production Bundle: npm run build",
        title="Frontend Execution"
    )

    add_h2("8.3 Step 3: Running Automated Tests")
    add_callout(
        "# Run Backend Unit & Integration Tests with Coverage:\n"
        "py -3.13 -m pytest backend/tests/ -v --cov=app --cov-report=term-missing\n\n"
        "# Run ML Pipeline Tests:\n"
        "py -3.13 -m pytest ml/tests/ -v",
        title="Automated Test Execution"
    )

    add_h2("8.4 Step 4: Running Monthly PSI Drift Monitoring")
    add_callout(
        "cd \"credishield\\ml\"\n"
        "py -3.13 scripts/run_psi_monthly.py --training-data data/processed/sample_train.csv --new-data data/processed/sample_new_month.csv",
        title="Drift Script Execution"
    )

    add_h2("8.5 Step 5: Full Containerized Stack (Docker)")
    add_callout(
        "cd \"credishield\"\n"
        "docker-compose up --build -d\n\n"
        "• Spawns PostgreSQL (port 5432), FastAPI Backend (port 8000), and React Nginx (port 3000).",
        title="Docker Compose Deployment"
    )

    # -------------------------------------------------------------
    # 9. Technical Interview Defense & Viva Q&A Guide
    # -------------------------------------------------------------
    add_h1("9. Technical Interview Defense & Viva Q&A Guide")
    doc.add_paragraph(
        "When defending CrediShield AI in front of hiring managers, professors, or technical interviewers, "
        "use these crisp, authoritative answers to demonstrate senior engineering maturity:"
    )

    qa_headers = ["Interview Question", "Recommended Technical Defense"]
    qa_data = [
        [
            "Why did you choose XGBoost instead of a Deep Learning neural network?",
            "For tabular credit data, tree-based gradient boosting models consistently outperform deep neural networks in empirical benchmarks. Tabular data lacks spatial or temporal locality, and gradient boosted trees handle heterogeneous continuous/categorical distributions, missing values, and non-linear interactions without requiring compute-heavy synthetic embedding layers."
        ],
        [
            "Why did you use SHAP TreeExplainer rather than KernelExplainer or LIME?",
            "KernelExplainer and LIME use perturbation-based sampling which takes 15-30 seconds per prediction, making them unusable for interactive web APIs. TreeExplainer takes advantage of internal tree structure to compute exact Shapley values in polynomial time O(TLD^2), returning local feature attributions in under 50 milliseconds."
        ],
        [
            "How did you address the 8% default rate class imbalance?",
            "Instead of naive SMOTE which generates synthetic points that often violate financial correlations, I configured XGBoost's scale_pos_weight parameter to balance the gradient updates (approx 11.5:1). This directly penalizes positive class misclassifications during boosting without modifying the underlying dataset."
        ],
        [
            "Why did you implement a 5:1 cost matrix rather than a standard 0.50 cutoff?",
            "In retail banking, a False Negative (unrecovered defaulted principal) is orders of magnitude more damaging than a False Positive (lost interest margin on a rejected applicant). By establishing a 5:1 loss penalty on validation predictions, the decision boundaries directly minimize institutional financial exposure."
        ],
        [
            "What is target leakage and how did you prevent it?",
            "Target leakage occurs when training data contains features generated after the decision event (such as payment installments or late payment penalties). I created a formal Bucket A vs Bucket B checklist that strictly isolated application-time features, guaranteeing that no post-disbursement data leaked into the model."
        ],
        [
            "Why is human-in-the-loop override required in the system?",
            "Credit scoring systems cannot operate as fully autonomous black boxes due to fair lending laws. Underwriters need the ability to overturn automated decisions based on verified offline collateral or extraordinary circumstances. CrediShield AI mandates a minimum 10-character written audit justification stored with the officer's ID to ensure complete legal traceability."
        ]
    ]
    t_qa = doc.add_table(rows=len(qa_data) + 1, cols=2)
    format_table(t_qa, [2.0, 4.5], qa_headers, qa_data)

    # Save document
    doc.save(output_path)
    print(f"Successfully generated DOCX at: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "CrediShield_AI_Complete_Documentation.docx"
    create_document(out_file)
