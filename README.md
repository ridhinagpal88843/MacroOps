# MacroOps AI — Quick-Commerce Fulfillment Intelligence & SLA Risk Prediction

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Release%20Ready%20%7C%20Audited-success.svg)](#project-status)
[![Tests](https://img.shields.io/badge/tests-22%2F22%20passing%20(100%25)-brightgreen.svg)](docs/QA_REPORT.md)
[![Model Threshold](https://img.shields.io/badge/threshold%20%CF%84-0.9300%20(Frozen)-orange.svg)](docs/MODEL_GOVERNANCE.md)
[![License](https://img.shields.io/badge/license-Proprietary%20%2F%20Prototype-lightgrey.svg)](#synthetic-data--governance-protocol)

**MacroOps AI** is an enterprise-grade operational intelligence platform and real-time operations command centre designed for quick-commerce delivery networks and high-density dark-store operations. The platform enables proactive fulfillment exception management by predicting Service Level Agreement (SLA) delivery breach risks at the exact moment of order checkout (**Stage A**), allowing dispatchers and dark-store supervisors to intervene before delivery deadlines are compromised.

The platform integrates a **multi-stage machine learning inference engine**, a **read-only Analytical Data Layer (ADL)** over SQLite, an **animated futuristic Command Centre dashboard**, and an **embodied 3D conversational AI assistant ("Ava")** featuring real-time viseme lip-synchronization and voice interaction.

---

## Table of Contents

- [Key Capabilities](#key-capabilities)
- [Architecture & System Flow](#architecture--system-flow)
- [Reconciled Operational KPIs](#reconciled-operational-kpis)
- [REST API Reference](#rest-api-reference)
- [Setup & Quickstart](#setup--quickstart)
- [Model Governance & Operating Policy](#model-governance--operating-policy)
- [Embodied 3D Operations Assistant ("Ava")](#embodied-3d-operations-assistant-ava)
- [Quality Assurance & Verification](#quality-assurance--verification)
- [Documentation Directory](#documentation-directory)
- [Synthetic Data & Governance Protocol](#synthetic-data--governance-protocol)

---

## Key Capabilities

### 1. Futuristic Operations Command Centre
- **Glassmorphic Cyber-Navy Interface:** Visual hierarchy inspired by mission-control operations, featuring dark charcoal surfaces, cyan/violet illumination, and responsive metric cards.
- **Dynamic Orbital Fulfillment Visual:** Prominent central glowing orb and multi-axis elliptical particle rings visualizing in-flight warehouse and delivery lifecycle states.
- **Store Performance Leaderboard:** Real-time ranking of dark stores by active volume, picker utilization, and SLA breach rate.
- **Order & Exception Explorer:** Live tabular filtering with instant search, status pills, delay metrics, and drilldown inspection drawers.
- **Model Governance Modal:** Direct in-app inspection of model training splits, precision-recall trade-offs, and the frozen $\tau = 0.9300$ threshold specification.

### 2. Embodied 3D Conversational Assistant ("Ava")
- **Procedural WebGL Humanoid Avatar:** Rendered in Three.js with zero external 3D asset downloads, procedural hair and uniform styling, and dynamic cyan rim lighting.
- **Dual-State Animation Controller:** Smooth transitions between ambient idle breathing/blinking and active conversational speaking gestures.
- **Phoneme-Driven Viseme Lip Synchronization:** Real-time mouth deformation synchronized to browser speech synthesis audio events.
- **Operational Query Engine:** Natural-language query answering for dark-store performance, high-risk orders, and SLA diagnostics with multi-turn memory.

### 3. Multi-Stage Predictive Inference Pipeline
- **Stage A Instant Checkout Prior ($t = 0$):** LightGBM classifier evaluating 7 pre-picking operational features with sub-millisecond latency.
- **Capacity-Constrained Decision Policy ($\tau = 0.9300$):** Caps alert volume to the top ~25–29% highest-risk orders while securing $\ge 94.0\%$ breach precision to eliminate dispatcher alert fatigue.
- **Stage B In-Flight Telemetry Updates ($t > 0$):** Ingestion of post-picking duration (Stage B1) and dispatch transit velocity (Stage B2) with robust fallback handling when telemetry is absent.

### 4. Hardened Analytical Data Layer (ADL)
- **Centralized SQLite Database (`macroops_analytics.db`):** Standardized relational schema across 200,000 synthetic operational events.
- **Strict Read-Only Enforcement:** Context-managed connection pool using SQLite `file:...mode=ro` URI protection against accidental data modification.
- **Reconciled KPI Metrics:** Mathematical alignment between gross initiation cohorts ($N=100,000$) and completed order delivery cohorts ($N=97,449$).

---

## Architecture & System Flow

```
[ Quick-Commerce Dark-Store Network ]
      │ (Orders, Inventory, Picking, Delivery, Workforce)
      ▼
[ SQLite Analytical Data Layer: macroops_analytics.db (Read-Only Mode) ]
      │ (v_all_orders, v_completed_orders, v_picking_performance, v_delivery_performance)
      ▼
[ Flask 3.10 Backend Services ]
 ├── services/data_service.py       <-- Context-managed read-only connection pooling
 ├── services/inference_service.py  <-- Stage A LightGBM (tau=0.9300) + Stage B fallbacks
 └── services/assistant_service.py  <-- Contextual dispatch intent & NLP dialog parser
      │
      ├── REST API Endpoints (/api/kpis, /api/orders, /api/stores, /api/predict/stage-a)
      │
      ▼
[ Frontend Command Centre & 3D Assistant ]
 ├── templates/index.html           <-- Semantic HTML5 layout
 ├── static/css/command_centre.css  <-- Dark glassmorphism & responsive CSS grid
 ├── static/js/command_centre.js    <-- Real-time countups, table filtering, governance
 └── static/js/assistant.js         <-- Three.js 3D avatar, dual animation & viseme lipsync
```

For complete technical specifications, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Reconciled Operational KPIs

MacroOps AI strictly distinguishes between the **gross initiation cohort** and the **completed delivery cohort** to ensure analytical consistency across dashboards, models, and conversational responses:

| Metric Category | Operational Metric | Exact Formula / Source View | Reconciled Value |
| :--- | :--- | :--- | :---: |
| **Gross Order Volume** | Total Order Initiations | `COUNT(*) FROM v_all_orders` | **100,000** |
| **Completed Deliveries** | Delivered Orders Cohort | `COUNT(*) FROM v_completed_orders` | **97,449** |
| **Delivered SLA Breach Rate** | Breach Rate (Completed) | `COUNT(actual_delivery_time > promised_delivery_time) / 97,449` | **89.68%** *(87,392 orders)* |
| **Gross SLA Breach Rate** | Breach Rate (Gross) | `COUNT(late deliveries) / 100,000` | **87.39%** *(87,392 orders)* |
| **Fulfillment Lead Time** | Mean Delivery Duration | `AVG(delivery_duration_minutes) FROM v_completed_orders` | **26.17 min** |
| **Warehouse Picking SLA** | Mean Picking Time | `AVG(picking_duration_minutes) FROM v_picking_performance` | **6.45 min** |
| **Rider Assignment Latency** | Mean Rider Wait Time | `AVG(assignment_delay_minutes) FROM v_delivery_performance` | **3.82 min** |
| **Last-Mile Velocity** | Mean Transit Speed | `AVG(transit_speed_kmh) FROM v_delivery_performance` | **18.42 km/h** |

---

## REST API Reference

All backend functionality is exposed via structured REST endpoints returning JSON responses:

| Endpoint | Method | Description | Sample Query / Body |
| :--- | :---: | :--- | :--- |
| `/api/kpis` | `GET` | System-wide operational KPIs and reconciled metrics | `GET /api/kpis` |
| `/api/orders` | `GET` | Paginated order list with search, status, and store filters | `GET /api/orders?page=1&limit=25&status=breached` |
| `/api/orders/<id>` | `GET` | Detailed order lifecycle, milestones, and telemetry | `GET /api/orders/ORD-00042` |
| `/api/stores` | `GET` | Dark-store performance summary and leaderboard | `GET /api/stores?sort=breach_rate&order=desc` |
| `/api/model/stage-a` | `GET` | Frozen Stage A model metadata, metrics, and threshold | `GET /api/model/stage-a` |
| `/api/predict/stage-a` | `POST` | Real-time SLA breach probability prediction | `{"store_id": "STORE-01", "item_count": 4, ...}` |
| `/api/assistant/chat` | `POST` | Conversational query interface with context memory | `{"message": "Which store has the worst breach rate?"}` |

Exhaustive parameter documentation and schema contracts are detailed in [`docs/API.md`](docs/API.md).

---

## Setup & Quickstart

### 1. Prerequisites
- Python 3.10 or higher
- Modern web browser with WebGL enabled (Chrome, Edge, Firefox, Safari)

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/ridhinagpal88843/MacroOps.git
cd MacroOps

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Application

Start the local Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

For production deployment with WSGI servers (Waitress on Windows or Gunicorn on Linux), consult [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## Model Governance & Operating Policy

The Stage A model is trained to predict whether an order will breach its delivery SLA using only features observable at order placement ($t = 0$).

### Decision Policy Freezing Protocol
Rather than optimizing for raw ROC-AUC, MacroOps AI employs a **capacity-constrained decision policy**:
- Dark-store supervisors can realistically expedite only 20–30% of order volume.
- Unconstrained classification at $\tau = 0.50$ produces alert fatigue and high false-positive rates.
- Operating threshold is frozen at $\tau = 0.9300$ based strictly on the Validation split ($N=13,082$).
- Verified on the holdout Test split ($N=16,210$) with **$94.12\%$ breach precision**, capping alert volume to $28.94\%$.

```
Confusion Matrix at Frozen Threshold (tau = 0.9300) [Holdout Test Partition, N = 16,210]:
─────────────────────────────────────────────────────────────────────────────
                     Actual Breach (1)        Actual On-Time (0)      Total
Predicted Alert (1)       4,416 (TP)               276 (FP)           4,692 (28.94%)
Predicted Normal (0)     10,121 (FN)             1,397 (TN)          11,518 (71.06%)
─────────────────────────────────────────────────────────────────────────────
Precision: 94.12% | Alert Volume: 28.94% | PR-AUC: 0.9252 | ROC-AUC: 0.8412
```

Complete model governance cards, feature schemas, and drift policies are documented in [`docs/MODEL_GOVERNANCE.md`](docs/MODEL_GOVERNANCE.md).

---

## Embodied 3D Operations Assistant ("Ava")

The operations assistant provides multi-modal natural-language decision support for store dispatchers:
- **Zero Asset Download:** Built procedurally in Three.js using geometric primitives and PBR materials, ensuring instant loading even on constrained dark-store networks.
- **Dynamic Lip Synchronization:** Viseme mouth aperture and horizontal elongation animate in real time when Ava speaks responses via the Web Speech Synthesis API.
- **Operational Memory:** Understands follow-up questions regarding specific dark stores, order delays, and model policies.
- **Voice Control:** Toggle voice synthesis on/off, stop audio immediately with a single click, or minimize the assistant into a floating HUD widget.

---

## Quality Assurance & Verification

The MacroOps AI system has undergone comprehensive full-system regression testing and browser quality assurance:

- **Automated Integration Suite:** **22/22 tests passing (100%)** covering API contracts, database read-only constraints, KPI denominators, Stage A/B inference, and assistant NLP parsing.
- **Database Read-Only Enforcement:** Verified that write queries raise `sqlite3.OperationalError: attempt to write a readonly database`.
- **Browser QA Verification:** Verified 12 visual checks across dashboard views, animations, responsive layouts, and 3D assistant interactions.
- **QA Evidence:** Visual screenshots and machine-readable test results are preserved in `qa_evidence/`.

Full audit logs, test execution matrices, and defect remediation histories are recorded in [`docs/QA_REPORT.md`](docs/QA_REPORT.md).

---

## Documentation Directory

| Document | Description |
| :--- | :--- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Technical architecture, data flow, 3D avatar pipeline, and service boundaries |
| [`docs/API.md`](docs/API.md) | Complete REST API specification with parameter tables and JSON response payloads |
| [`docs/MODEL_GOVERNANCE.md`](docs/MODEL_GOVERNANCE.md) | Stage A/B model cards, feature engineering, frozen threshold $\tau=0.9300$, and bias audits |
| [`docs/QA_REPORT.md`](docs/QA_REPORT.md) | 22-test automated integration matrix, browser QA findings, and defect remediation |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production WSGI configuration, environment variables, Nginx reverse proxy, and monitoring |
| [`docs/RESEARCH_PAPER_OUTLINE.md`](docs/RESEARCH_PAPER_OUTLINE.md) | Academic research paper structure on SLA risk mitigation and embodied dispatch copilots |
| [`docs/PROJECT_TRACKER.md`](docs/PROJECT_TRACKER.md) | Milestone execution log, verification gates checklist, and roadmap |
| [`docs/PHASE_03_PART_01_BUSINESS_PROBLEM_DISCOVERY.md`](docs/PHASE_03_PART_01_BUSINESS_PROBLEM_DISCOVERY.md) | Phase 03 Part 01: Real-world business discovery, doorstep access, dispute AI, and ROI framework |
| [`docs/KPI_DEFINITIONS.md`](docs/KPI_DEFINITIONS.md) | Mathematical definitions and benchmarks for all 15+ operational KPIs |
| [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) | Relational entity schemas and column attributes for orders, inventory, and delivery |

---

## Synthetic Data & Governance Protocol

> [!IMPORTANT]
> **Synthetic Prototype Disclaimer**
> All operational datasets, dark-store coordinates, courier logs, customer identifiers, and transaction records within this repository are **synthetically generated** for demonstration, academic research, and prototype evaluation. They do not represent proprietary commercial data from any commercial quick-commerce platform.
> 
> In accordance with repository hygiene best practices:
> - The canonical database `macroops_analytics.db` is maintained directly in the repository (~35.6 MB) to provide an immediately runnable prototype.
> - Transient database journals (`*.db-wal`, `*.db-shm`), environment variables (`.env`), and temporary cache directories are strictly excluded via `.gitignore`.
