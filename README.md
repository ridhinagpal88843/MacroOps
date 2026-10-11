# MacroOps AI — Quick-Commerce Fulfillment Intelligence & SLA Risk Prediction

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Stage%20A%20Frozen-success.svg)](#project-status)
[![License](https://img.shields.io/badge/license-Proprietary%20%2F%20Prototype-lightgrey.svg)](#data-access-note)

MacroOps AI is an end-to-end operational analytics and predictive intelligence platform designed for quick-commerce fulfillment networks and dark-store operations. The platform enables proactive fulfillment exception management by predicting Service Level Agreement (SLA) delivery breach risk at the exact moment of order placement (**Stage A**), allowing dispatchers and store supervisors to intervene before delivery deadlines are compromised.

---

## Table of Contents

- [Project Description](#project-description)
- [Project Status](#project-status)
- [Repository Structure](#repository-structure)
- [Data Access Note](#data-access-note)
- [Setup & Quickstart](#setup--quickstart)
- [Core Models & Governance](#core-models--governance)
- [Analytical Data Layer](#analytical-data-layer)

---

## Project Description

Quick-commerce fulfillment promises 10-to-30-minute delivery windows across dense urban dark-store networks. Managing operational latency across rapid fulfillment stages (order placement, picking, rider assignment, and transit) requires early detection of order risk.

MacroOps AI solves this through a multi-tiered intelligence pipeline:
1. **Analytical Data Layer (ADL):** Centralized semantic model and relational views built on SQLite (`macroops_analytics.db`) standardizing 15+ core operational KPIs across 200,000 synthetic operational events.
2. **Stage A Risk Classification:** Predicts SLA breach risk at the instant of order checkout ($t = 0$) using lightweight, pre-picking store and dispatch signals.
3. **Capacity-Constrained Operating Policy:** Implements an operationally constrained decision threshold ($\tau = 0.9300$) achieving $\ge 94\%$ breach precision while capping alert volume to the top ~25–29% highest-risk orders to eliminate alert fatigue.
4. **Operations Copilot & Dashboards:** Decision support tools providing dark-store supervisors with root-cause diagnostics and re-routing recommendations.

---

## Project Status

| Milestone / Component | Phase | Status | Key Deliverables & Artifacts |
| :--- | :--- | :---: | :--- |
| **Data Ingestion & Profiling** | Phase 1A | `COMPLETE` | `docs/DATA_PROFILING_REPORT.md`, `docs/DATA_QUALITY_REPORT.md` |
| **Analytical Data Layer & KPIs** | Phase 1B | `COMPLETE` | `macroops_analytics.db`, `docs/KPI_DEFINITIONS.md`, `docs/ANALYTICAL_DATA_LAYER.md` |
| **Feature Engineering (Stage A)** | Phase 2A | `COMPLETE` | `src/build_predictive_features.py`, `data/predictive_features/` |
| **Baseline Modeling & Benchmarking** | Phase 2B | `COMPLETE` | `src/train_baseline_models.py`, `models/` (LightGBM, Logistic Regression) |
| **Threshold Analysis & Policy Freezing** | Phase 2C | `FROZEN` | `reports/stage_a_final_config.json`, `reports/stage_a_final_metrics.json`, `reports/plots/` |
| **Operational Copilot & Web App** | Phase 3A | `IN PROGRESS` | `app/` (Dashboard & Dispatcher Interface) |
| **Automated Test Suite & CI** | Phase 3B | `PLANNED` | `tests/` |

---

## Repository Structure

```text
MacroOps/
├── .gitignore                    # Exclusion rules (data, binaries, media, environments)
├── README.md                     # Project documentation, status, structure, and quickstart
├── app/                          # Web application services & dashboard interfaces
├── data/                         # Local dataset directory (excluded from git)
│   ├── raw/                      # Raw incoming transaction and event CSVs
│   ├── predictive_features/      # Engineered feature tables and metadata
│   ├── orders.csv                # Orders transactional dataset (100k records)
│   ├── inventory.csv             # Dark-store inventory and SKU stock records
│   ├── picking.csv               # Warehouse picking timestamps and item logs
│   ├── delivery.csv              # Dispatch and rider transit performance
│   ├── workforce.csv             # Shift allocation and staffing logs
│   └── macroops_analytics.db     # SQLite analytical data layer & KPI views
├── docs/                         # Architecture, KPI, and governance documentation
│   ├── ANALYTICAL_DATA_LAYER.md  # Relational schema and view definitions
│   ├── DATA_DICTIONARY.md        # Comprehensive entity-attribute specifications
│   ├── DATA_PROFILING_REPORT.md  # Data distribution and column profile analysis
│   ├── DATA_QUALITY_REPORT.md    # Integrity, anomaly, and constraint audit
│   ├── DATA_RELATIONSHIPS.md     # Cross-entity foreign keys and ER relationships
│   ├── DATA_VALIDATION_REPORT.md # Data consistency verification report
│   ├── FEATURE_ENGINEERING_REPORT.md # Mathematical definitions for Stage A features
│   ├── KPI_DEFINITIONS.md        # Operational KPI formulas and benchmark values
│   ├── MODEL_PERFORMANCE_REPORT.md   # Model comparison and cross-validation metrics
│   ├── PREDICTIVE_MODEL_DESIGN.md    # Problem framing and Stage A system design
│   ├── SLA_ANALYSIS.md           # SLA breach baseline dynamics and root-cause analysis
│   ├── STAGE_A_FINAL_EVALUATION.md   # Final holdout evaluation and policy audit
│   ├── STAGE_A_MODEL_SELECTION.md    # Pre-freezing model selection report
│   ├── STAGE_A_THRESHOLD_ANALYSIS.md # Decision threshold optimization analysis
│   └── TIMESTAMP_ANOMALY_REPORT.md   # Chronological audit of operational timestamps
├── models/                       # Serialized model binaries & evaluation metadata
│   ├── dummy_classifier.joblib   # Heuristic prior baseline
│   ├── dummy_regressor.joblib    # Mean target baseline
│   ├── evaluation_metrics.json   # Benchmark metrics across models
│   ├── lgb_ordinal_encoder.joblib# Ordinal encoder for categorical features
│   ├── lightgbm_classifier.joblib# Primary Stage A classification model
│   ├── lightgbm_regressor.joblib # Continuous delay regression model
│   ├── linear_preprocessor.joblib# One-hot scaler pipeline for linear models
│   ├── logistic_regression.joblib# Baseline linear classifier
│   └── ridge_regressor.joblib    # Baseline linear regressor
├── notebooks/                    # Exploratory analysis & prototyping notebooks
├── reports/                      # Evaluation reports, frozen configs, and visual plots
│   ├── plots/                    # Calibration curves, PR curves, and trade-off charts
│   ├── stage_a_final_config.json # Frozen decision threshold and feature config
│   ├── stage_a_final_metrics.json# Machine-readable holdout verification metrics
│   └── threshold_analysis.json   # Threshold sweep data across candidate operating points
├── src/                          # Production pipeline scripts and execution modules
│   ├── build_predictive_features.py # Feature extraction and validation pipeline
│   ├── run_threshold_analysis.py    # Operating policy evaluation and plotting script
│   └── train_baseline_models.py     # Training and evaluation runner for baseline models
└── tests/                        # Unit tests, data contract checks, and model tests
```

---

## Data Access Note

> [!IMPORTANT]
> **Synthetic Prototype Governance & Data Access Protocol**
> - **Synthetic Dataset:** All operational data in this repository comprises 200,000 synthetic operational events (orders, inventory, picking, deliveries, workforce) generated to mirror realistic quick-commerce dark-store dynamics without exposing sensitive proprietary business information.
> - **Version Control Exclusions:** In accordance with `.gitignore`, large datasets (`data/`), SQLite database files (`*.db`), media (`*.mp4`), and slide decks (`*.pptx`, `*.pdf`) are excluded from Git commits to ensure high repository hygiene and prevent binary bloat.
> - **Data Availability:** To run feature engineering and training pipelines locally, place the primary CSV datasets (`orders.csv`, `inventory.csv`, `picking.csv`, `delivery.csv`, `workforce.csv`) and/or `macroops_analytics.db` in the `data/` folder.

---

## Setup & Quickstart

### 1. Prerequisites
- Python 3.10 or higher
- Git installed on your local environment

### 2. Environment Setup

Clone the repository and set up a Python virtual environment:

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
```

### 3. Install Dependencies

Install the core data science and machine learning packages:

```bash
pip install --upgrade pip
pip install numpy pandas scikit-learn lightgbm joblib matplotlib seaborn
```

### 4. Running the Pipelines

#### A. Generate Stage A Predictive Features
Processes raw operational orders and constructs the clean, validated feature dataset:
```bash
python src/build_predictive_features.py
```
*Outputs: `data/predictive_features/stage_a_features.csv`, `feature_metadata.json`, `validation_audit.json`*

#### B. Train and Evaluate Baseline Models
Fits baseline models (Dummy, Logistic Regression, LightGBM) across chronological train/validation/test partitions:
```bash
python src/train_baseline_models.py
```
*Outputs: Serialized `.joblib` binaries and `models/evaluation_metrics.json`*

#### C. Run Threshold Sweeps and Policy Validation
Sweeps classification thresholds ($\tau \in [0.5, 0.99]$) and evaluates operating policy constraints:
```bash
python src/run_threshold_analysis.py
```
*Outputs: `reports/threshold_analysis.json` and diagnostic curves in `reports/plots/`*

---

## Core Models & Governance

### Decision Policy Freezing Protocol
The operating decision threshold was frozen based strictly on the Validation partition (Sept 22–25, $N = 13,082$) prior to evaluating the untouched holdout test set (Sept 26–30, $N = 16,210$).

| Model Architecture | Selected Operating Threshold ($\tau$) | Validation PR-AUC | Breach Precision | Flagged Alert Volume |
| :--- | :---: | :---: | :---: | :---: |
| **LightGBM Classifier** *(Primary MVP)* | **0.9300** | **0.9252** | **94.00%** | **28.94% (3,786 orders)** |
| **Logistic Regression** *(Linear Baseline)* | 0.9300 | 0.9254 | 93.61% | 25.10% (3,284 orders) |

**Key Engineering Advantage:** The selected LightGBM classifier requires only **7 native features** compared to 135 one-hot encoded features for Logistic Regression, reducing pipeline complexity by **19x** while delivering superior precision and robustness.

---

## Analytical Data Layer

The analytical backbone is organized into standardized views within `macroops_analytics.db`:
- `v_all_orders`: Complete transaction catalog across all store locations.
- `v_completed_orders`: Delivered orders with validated end-to-end SLA delivery latency.
- `v_picking_performance`: Dark-store warehouse picking duration and exception tracking.
- `v_delivery_performance`: Rider assignment, transit velocity, and last-mile distances.
- `v_store_inventory`: SKU availability, stockout ratios, and catalog health.
- `v_workforce_performance`: Picker and rider shift completion and backlog rates.

For detailed KPI formulas and data contracts, refer to [`docs/KPI_DEFINITIONS.md`](docs/KPI_DEFINITIONS.md) and [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).
