# MacroOps AI — Phase 03 Part 02: Supervisor-Scenario Coverage Matrix & Architecture Verification

**Project:** MacroOps AI — Fulfillment & Last-Mile Operations Intelligence Platform  
**Phase:** 03 — Operational Expansion & Scenario Prototyping (Part 02)  
**Date:** October 2026  
**Status:** `VERIFIED & OPERATIONAL` (41/41 Automated Tests Passing)

---

## 1. Executive Summary & Architectural Scope

In accordance with the supervisor's directives and the approved `SUPERVISOR-SCENARIO COVERAGE MATRIX & ARCHITECTURE DESIGN`, MacroOps AI has implemented Phase 03 Part 02. All three supervisor scenarios are treated as mandatory, independent operational capabilities:

1. **Delivery Location, Doorstep Access & Courier Safety**
2. **Defective or Poor-Quality Products & Supplier Batch Investigation**
3. **Fair Refund and Compensation Recommendations**

### Architecture Governance Invariants

| Governance Dimension | Policy & Enforcement Guarantee |
| :--- | :--- |
| **Model Invariants** | Frozen Stage A/B models, features, evaluation sets, and decision threshold ($\tau = 0.9300$) remain strictly untouched. |
| **Database Integrity** | Canonical SQLite database (`macroops_analytics.db`) remains read-only (`mode=ro`). Zero new tables or schema changes. |
| **Data Partitioning** | All scenario prototypes and synthetic test records reside strictly within `data/scenario_prototypes/`. |
| **API Contracts** | The 7 baseline API contracts are 100% backward-compatible. 5 new prototype endpoints are exposed under `/api/prototypes/`. |
| **Ava 3D Avatar** | Avatar controls, procedural Three.js skeletal mesh, morph targets, viseme lip-sync, and voice toggle preserved. Phase 3 intents seamlessly incorporated. |
| **Truth in Engineering** | The platform explicitly frames automated outcomes as *policy recommendations* and *investigation advisories*. No claims of real physical courier tracking, live bank fund transfers, or legally proven supplier liability are made. |

---

## 2. Supervisor-Scenario Coverage Matrix

| Scenario Scope | Architectural Module | Calibrated Dataset | Decision Action Tiers | Truth-in-Engineering Guardrail |
| :--- | :--- | :--- | :--- | :--- |
| **Scenario 1: Delivery Location & Courier Safety** | `services/delivery_access_service.py` (`DeliveryAccessService`) | `data/scenario_prototypes/synthetic_access_scenarios.json` (25 Scenarios) | 1. `SAFE_DOORSTEP_PROCEED`<br>2. `PRE_ARRIVAL_ACCESS_BRIEF`<br>3. `GROUND_FLOOR_HANDOFF`<br>4. `UNSAFE_PHYSICAL_TASK_ESCALATION` | Simulated vicinity telemetry (< 500m); ground-floor handoffs authorized on ergonomic hazards; no physical rider reassignment claimed. |
| **Scenario 2: Defective Goods & Batch Investigation** | `services/complaint_service.py` (`ComplaintService`) | `data/scenario_prototypes/synthetic_complaint_scenarios.json` (20 Scenarios) | 1. `RECOMMEND_SUPPLIER_BATCH_INVESTIGATION`<br>2. `NORMAL_MONITORING`<br>Thermal Exposure Latency Curve | Defect clustering aggregated by `(supplier_id, batch_id)`; framed strictly as *advisory batch investigation*, never asserting proven legal fault. |
| **Scenario 3: Fair Refund & Compensation Policy** | `services/complaint_service.py` (`ComplaintService`) | `data/scenario_prototypes/synthetic_complaint_scenarios.json` (20 Scenarios) | 1. `IMMEDIATE_REFUND`<br>2. `PRIORITY_REPLACEMENT`<br>3. `PARTIAL_COMPENSATION` (35%)<br>4. `REQUEST_EVIDENCE`<br>5. `HUMAN_REVIEW` | Zero automated rejections; claim frequency alone never triggers refusal; store shift P&L decoupled from legitimate payouts; no live bank transfer executed. |

---

## 3. Scenario Implementation Details

### Scenario 1: Delivery Location, Doorstep Access & Courier Safety

- **Ergonomic Safety Standard:** Solitary walk-up parcel weights are strictly capped at **15.0 kg** for unassisted staircase ascent. Deliveries exceeding 15.0 kg to upper floors (Floor > 2) without a working elevator automatically trigger `GROUND_FLOOR_HANDOFF` or `UNSAFE_PHYSICAL_TASK_ESCALATION`.
- **Pre-Arrival Briefings:** When couriers enter within 500 meters of a destination requiring gate codes, security passes, or special parking instructions, the system pushes a structured briefing before arrival.
- **Physical Hazard Handling:** Documented hazards (unleashed guard dogs, unlit or broken staircases, severe waterlogging) immediately authorize ground-floor handoff, protecting delivery partner ratings and earnings from punitive cancellations.
- **Customer Coordination:** Generates transparent, respectful coordination messages (e.g. inviting the customer to collect bulky orders in the lobby) to prevent customer friction.

### Scenario 2: Defective Products & Supplier Batch Investigation

- **Cold-Chain Latency Correlation:** Correlates delivery delay minutes and ambient temperature (°C) against perishable categories (dairy and fresh produce). When delays exceed 15 minutes in ambient temperatures > 30°C, product degradation is attributed to fulfillment latency, automatically exonerating the customer.
- **Photo Evidence Tagging:** Inspects visual tags (e.g., `PHOTO_ATTACHED`, `BRUISED_SKIN`, `CURDLED_MILK`, `LEAKING_SEAL`) attached to dispute records to substantiate genuine claims.
- **Supplier Batch Clustering:** Analyzes recurring defect patterns across dark store intake batches. When a batch exhibits $\ge 2$ complaints or a defect rate $> 4.0\%$, the system issues an advisory `RECOMMEND_SUPPLIER_BATCH_INVESTIGATION` ticket, triggering physical warehouse quarantine and supplier QA audits.

### Scenario 3: Fair Refund and Compensation Recommendations

- **5-Tier Transparent Adjudication:**
  1. `IMMEDIATE_REFUND`: 100% refund to original payment channel for spoiled perishables with verified transit delays or severe food safety defects.
  2. `PRIORITY_REPLACEMENT`: Expedited replacement dispatch for damaged essential household staples and groceries.
  3. `PARTIAL_COMPENSATION`: 35% store credit compensation for minor cosmetic packaging dents where the food seal remains intact.
  4. `REQUEST_EVIDENCE`: Friendly, non-accusatory prompt requesting photo evidence for claims on high-value items without documentation.
  5. `HUMAN_REVIEW`: Escalation to human customer support leads for complex, high-value disputes (> ₹1,500 INR) or repeated ambiguous claims.
- **Anti-Bias Charter:**
  - **Zero Automated Rejections:** The system possesses no automated denial pathway (`DENY_CLAIM` is structurally prohibited).
  - **No Guilt by Frequency:** Customer claim frequency in the past 90 days is never used as sole grounds for rejection or reduced compensation.
  - **Margin Decoupling:** Shift manager P&L metrics are decoupled from customer resolution costs, eliminating incentives to suppress legitimate claims.

---

## 4. Enterprise Command Centre Views

The Command Centre interface features three dedicated views accessible via top-level cyber-navy navigation tabs:

```
[ Executive Overview ] [ Order Explorer ] [ Model Governance ] [ 🚪 Access & Safety ] [ 🔍 Dispute Inspector ] [ ⚖️ Fair Adjudication ]
```

### 1. Access & Safety Monitor (`#tab-access-safety`)
- **Key Metrics Row:** Ergonomic Walk-up Limit (15.0 kg), Vertical Staircase Limit (2 Floors), Pre-Arrival Briefing Rate (100%), Ground Handoff Escalation (Active).
- **Interactive Simulation Suite:** Interactive scenario picker loading 25 calibrated access scenarios with real-time parameter adjusters (parcel weight, drop-off floor, elevator availability, gate code requirement, hazard type, vicinity distance).
- **Safety Assessment Console:** Displays real-time decision badges, doorstep safety status, ground handoff authorization, courier action directive, and customer coordination message preview.

### 2. Quality Dispute Inspector (`#tab-dispute-inspector`)
- **Key Metrics Row:** Cold-Chain Delay Limit (15.0 min), Batch Anomaly Trigger ($\ge 2$ Claims), Photo Evidence Tagging (100%), Investigation Governance (Advisory).
- **Emerging Supplier Batch Defect Clusters Table:** Live leaderboard displaying monitored batches, affected SKUs, complaint-to-unit ratios, defect rates, defect signatures, and advisory investigation recommendations.
- **Defect Inspection & Thermal Correlator:** Side-by-side inspection console displaying photo evidence tags, item details, defect descriptions, and an animated thermal exposure progress meter correlating transit delays with product degradation.

### 3. Fair Adjudication Console (`#tab-adjudication-console`)
- **Key Metrics Row:** Automated Rejections (0.00% Prohibited), Frequency Bias Protection (Active), Margin Decoupling (Enforced), Policy Tiers (5 Tiers).
- **Complaint Parameters & Evidence Dossier:** Scenario selector loading 20 calibrated complaint scenarios with granular form controls to simulate custom claim conditions.
- **Adjudication Outcome Dossier:** Visual recommendation hero badge (`tier-refund`, `tier-replacement`, `tier-partial`, `tier-evidence`, `tier-review`), payout amount, settlement channel, anti-bias audit badge, plain-language customer communication preview, and fairness charter checklist.

---

## 5. Ava 3D Operations Assistant Integration

Ava's conversational intelligence engine (`services/assistant_service.py`) natively supports Phase 3 supervisor inquiries with grounded dialogue responses and explicit denominators:

1. **`DELIVERY_ACCESS_INTELLIGENCE`**: Responds to queries regarding doorstep access, staircase walk-up limits, gate access, and courier ergonomic safety.
2. **`COMPLAINT_ADJUDICATION_POLICY`**: Explains the 5-tier fair compensation policy, anti-bias protections, and cold-chain delay correlations.
3. **`SUPPLIER_BATCH_INVESTIGATION`**: Reports active supplier defect clusters, quarantine thresholds, and batch investigation recommendations.

Quick operational prompt chips have been added to the assistant UI for single-click access to all three supervisor scenario topics.

---

## 6. REST API Prototype Endpoints

The Flask application exposes 5 dedicated prototype endpoints:

| Method | Endpoint | Description | Request / Query Params |
| :---: | :--- | :--- | :--- |
| `GET` | `/api/prototypes/delivery-access/scenarios` | Lists all 25 calibrated access scenarios | None |
| `POST` | `/api/prototypes/delivery-access/evaluate` | Evaluates physical access and courier safety | JSON payload: `parcel_weight_kg`, `floor_number`, `elevator_available`, etc. |
| `GET` | `/api/prototypes/disputes/scenarios` | Lists all 20 calibrated complaint scenarios | Optional `category` filter |
| `POST` | `/api/prototypes/disputes/evaluate` | Computes 5-tier fair adjudication recommendation | JSON payload: `item_name`, `item_category`, `item_price_inr`, `evidence_attached`, etc. |
| `GET` | `/api/prototypes/disputes/batch-investigations` | Aggregates supplier batch defect clusters | None |

All baseline API contracts (`/api/health`, `/api/kpis`, `/api/stores`, `/api/orders`, `/api/orders/<id>`, `/api/model/stage-a`, `/api/predict/stage-a`, `/api/assistant/chat`) remain fully functional and backward-compatible.

---

## 7. Verification & Automated Test Results

System stability and scenario coverage have been verified through automated regression suites:

### Test Suite Execution Summary

```
======================================================================
1. tests/test_full_system_integration.py (Baseline System Regression)
----------------------------------------------------------------------
Ran 22 tests in 10.695s
Status: OK (22/22 Passing - 100%)

2. tests/test_phase03_scenarios.py (Phase 03 Supervisor Scenarios)
----------------------------------------------------------------------
Ran 19 tests in 0.057s
Status: OK (19/19 Passing - 100%)

Total Verified Automated Tests: 41 / 41 PASSING (100%)
======================================================================
```

### Detailed Breakdown of Phase 03 Tests (`tests/test_phase03_scenarios.py`)

- `test_01_synthetic_access_scenarios_dataset`: Verifies 25 access scenarios with valid schemas.
- `test_02_synthetic_complaint_scenarios_dataset`: Verifies 20 complaint scenarios with valid schemas.
- `test_03_bulky_weight_walkup_escalation`: Verifies bulky loads (>15kg) trigger handoff escalation.
- `test_04_gated_community_pre_arrival_brief`: Verifies gate access triggers pre-arrival briefing.
- `test_05_ground_floor_safe_delivery`: Verifies standard ground delivery allows safe doorstep proceed.
- `test_06_perishable_coldchain_refund`: Verifies spoiled milk with transit delay receives `IMMEDIATE_REFUND`.
- `test_07_cosmetic_damaged_packaging_partial_credit`: Verifies dented box receives `PARTIAL_COMPENSATION` (35%).
- `test_08_missing_evidence_request`: Verifies missing photo prompts `REQUEST_EVIDENCE`.
- `test_09_high_value_item_human_review`: Verifies high-value dispute triggers `HUMAN_REVIEW`.
- `test_10_fairness_invariant_anti_bias`: Verifies complaint frequency alone never triggers refusal.
- `test_11_supplier_batch_investigation_aggregation`: Verifies defect clusters trigger batch investigation.
- `test_12_api_delivery_access_scenarios`: Verifies GET endpoint returns 25 scenarios.
- `test_13_api_delivery_access_evaluate`: Verifies POST evaluation returns safety decisions.
- `test_14_api_disputes_scenarios`: Verifies GET endpoint returns 20 complaint scenarios.
- `test_15_api_disputes_evaluate`: Verifies POST evaluation returns 5-tier recommendations.
- `test_16_api_disputes_batch_investigations`: Verifies GET endpoint returns supplier defect clusters.
- `test_17_assistant_doorstep_access_query`: Verifies Ava responds to doorstep access queries.
- `test_18_assistant_quality_dispute_query`: Verifies Ava explains fair dispute resolution policy.
- `test_19_assistant_batch_investigation_query`: Verifies Ava reports batch investigation alerts.

---

## 8. Truth in Engineering Declarations

1. **Simulated Telemetry:** Vicinity detection (< 500m) and courier positioning represent simulated algorithms. No real-world GPS trackers or mobile app background locations are queried.
2. **Advisory Payouts:** Financial refund amounts and store credits are policy proposals for support supervisors. No live banking, UPI, or payment gateway APIs are invoked.
3. **Courier Ergonomics:** The platform recommends ground-floor handovers and task halts; no physical delivery partners are reassigned in real time.
4. **Supplier Quality:** Defect clusters generate advisory tickets for dark store intake auditors; synthetic data does not constitute legal proof of supplier breach of contract.
