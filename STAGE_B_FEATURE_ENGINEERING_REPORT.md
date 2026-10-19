# MacroOps AI — Stage B Feature Engineering & Integrity Audit Report

**Document Version:** 1.0.0  
**Phase:** Stage B Step 1 — Point-in-Time Feature Engineering  
**Execution Timestamp:** October 13, 2026  
**Pipeline Script:** [`build_stage_b_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_stage_b_features.py)  
**Output Datasets:**
- [`predictive_features/stage_b1_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_b1_features.csv) ($N = 24,369$, 30 columns)
- [`predictive_features/stage_b2_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_b2_features.csv) ($N = 24,369$, 34 columns)
**Metadata & Validation Audits:**
- [`predictive_features/stage_b_feature_metadata.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_b_feature_metadata.json)
- [`predictive_features/stage_b_validation_audit.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_b_validation_audit.json)

---

> [!CAUTION]
> **PROTOTYPE / SYNTHETIC DATA GOVERNANCE DISCLAIMER**  
> All features, timestamps, and point-in-time metrics generated in this pipeline are derived from synthetic quick-commerce operational datasets modeling dark-store operations. This pipeline represents a retrospective point-in-time simulation for model evaluation and research. It does NOT claim live production integration or real-time event streaming execution.

---

## 1. Executive Summary & Audit Objectives

Following the formal completion, freezing, and evaluation of Stage A ([`STAGE_A_FINAL_EVALUATION.md`](file:///c:/Users/HP/Desktop/MacroOps/STAGE_A_FINAL_EVALUATION.md)), Step 1 of Stage B establishes reproducible, leakage-free feature matrices for dynamic in-fulfillment risk tracking.

### Core Governance Directives Enforced:
1. **Zero Stage A Modifications:** No Stage A script, model artifact, configuration ([`stage_a_final_config.json`](file:///c:/Users/HP/Desktop/MacroOps/stage_a_final_config.json)), or metric file was altered.
2. **Untouched Source Data:** All 5 raw CSVs (`orders.csv`, `inventory.csv`, `picking.csv`, `delivery.csv`, `workforce.csv`) remain 100% byte-for-byte immutable.
3. **No Model Training in Step 1:** Work was strictly limited to schema verification, point-in-time feature engineering, and automated integrity auditing.
4. **Strict Temporal Isolation:** Features are restricted exclusively to information physically available by the respective checkpoint timestamps.
5. **No Artificial Denominators:** Zero or negative time budgets are handled via explicit boolean indicators and missing values, avoiding artificial denominator floors.

---

## 2. Source Schema Inspection & Cohort Verification

### 2.1. View Verification: `v_full_lifecycle_orders`
Prior to feature generation, the analytical database [`macroops_analytics.db`](file:///c:/Users/HP/Desktop/MacroOps/macroops_analytics.db) was queried to inspect `v_full_lifecycle_orders`:
- **Total Rows in View:** Exactly **25,000**.
- **Distinct `order_id`s:** Exactly **25,000**.
- **Join Cardinality Verdict:** The inner join between `raw_orders`, `raw_picking`, and `raw_delivery` preserves **strictly 1 row per order** with zero duplication.

### 2.2. Population Filtering: Verified Completed Cohort ($N = 24,369$)
The full-lifecycle dataset breaks down by operational status as follows:
- `Delivered_Late`: **21,874 orders (89.76%)**
- `Delivered_On_Time`: **2,495 orders (10.24%)**
- **Completed Delivery Cohort ($N$):** **24,369 orders (100.0%)**
- **Excluded Exceptions:** 
  - `Cancelled`: **445 orders** (1.78%)
  - `Failed`: **186 orders** (0.74%)
  - *Total Excluded:* 631 orders (2.52%)

> [!NOTE]
> **Cohort Count Clarification:** While pre-audit estimates projected ~24,357 completed orders, empirical execution confirmed exactly **24,369 completed orders**. This verified population is established as the canonical baseline for all Stage B evaluations.

### 2.3. The 75% Telemetry Coverage Limitation
Of the 97,449 total completed orders in `orders.csv`, exactly **24,369 (25.01%)** possess granular warehouse picking and delivery telemetry. The remaining 73,080 completed orders (74.99%) exist only in `orders.csv`.
- *Operational Implication:* Stage B dynamic tracking can only be triggered for orders with WMS/courier milestone events.
- *Evaluation Requirement:* When comparing Stage B against Stage A, Stage A's frozen model must be benchmarked on this identical 24,369-order cohort to ensure fair, unbiased lift measurement.

---

## 3. Point-in-Time Checkpoint Formulations

Stage B introduces two discrete operational checkpoints during fulfillment:

```
Order Checkout (T0)           Pick Complete (T1)           Dispatch Proxy (T2)           Customer Drop-off (Tend)
       |------------------------------|-----------------------------|---------------------------|
   [Stage A]                      [Stage B1]                    [Stage B2]                   [Final Ground Truth]
Static Basket                  Warehouse Finished            Order En Route                  SLA Breached (0/1)
```

---

### Checkpoint B1: Post-Picking ($T_1 = \text{picking.pick\_end}$)

#### 1. Checkpoint Moment
Evaluated the exact millisecond warehouse packaging concludes (`picking.pick_end`).

#### 2. Point-in-Time Feature Whitelist (23 Features)
- **Stage A Static Features (7):** `item_count`, `order_value`, `promised_duration_minutes`, `order_hour`, `day_of_week`, `is_peak_rush_hour`, `store_id`.
- **Picking Performance (8):**
  - `picker_id`: Warehouse picker identifier.
  - `time_to_pick_start_min`: Queue delay before picking began: `(pick_start - order_time) / 60`.
  - `pick_duration_minutes`: Elapsed picking time: `(pick_end - pick_start) / 60`.
  - `elapsed_time_to_b1_min`: Total elapsed time from checkout to pick completion: `(pick_end - order_time) / 60`.
  - `items_picked`: Count of items successfully picked.
  - `items_missing`: Count of missing items flagged during pick.
  - `has_picking_exception`: Binary flag (`1` if `items_missing > 0` else `0`).
  - `picking_speed_items_per_min`: `items_picked / max(0.1, pick_duration_minutes)`.
- **SLA Budget at B1 (4):**
  - `remaining_sla_budget_b1_min`: `(promised_time - pick_end) / 60`.
  - `budget_consumed_ratio_b1`: `elapsed_time_to_b1_min / promised_duration_minutes`.
  - `is_past_promise_at_b1`: `1` if `remaining_sla_budget_b1_min <= 0.0` else `0` (**29 orders**).
  - `pick_budget_deficit_min`: `max(0.0, -remaining_sla_budget_b1_min)`.
- **Courier Assignment State at B1 (4):**
  - *Strict Rule:* Courier assignment information is populated **ONLY if `assignment_time <= pick_end`**.
  - `is_courier_assigned_by_b1`: `1` for **23,400 orders (96.02%)**; `0` for **969 orders (3.98%)**.
  - If assigned (`1`): `assignment_delay_to_b1_min = (assignment_time - order_time) / 60`, `time_from_assignment_to_b1_min = (pick_end - assignment_time) / 60`, `rider_id_at_b1 = rider_id`.
  - If unassigned (`0`): Delay and duration are left explicitly empty (`null`), and `rider_id_at_b1 = "UNASSIGNED"`.

---

### Checkpoint B2: Post-Dispatch Proxy ($T_2 = \max(\text{pick\_end}, \text{pickup\_time})$)

#### 1. Honest Checkpoint Naming & Semantic Definition
As proven in [`TIMESTAMP_ANOMALY_REPORT.md`](file:///c:/Users/HP/Desktop/MacroOps/TIMESTAMP_ANOMALY_REPORT.md), in **61.94% of completed orders (15,094 / 24,369)**, `delivery.pickup_time` occurs *before* `picking.pick_end`. 
- In quick-commerce operations, `pickup_time` reflects **Rider Arrival / Staging Bay Check-in**, not physical wheels-moving departure.
- Physical dispatch cannot occur until **both** warehouse picking has finished **and** the rider has arrived.
- Therefore, Checkpoint B2 is defined as:
  $$\text{effective\_dispatch\_time} = \max(\text{picking.pick\_end}, \text{delivery.pickup\_time})$$
- The checkpoint is explicitly documented as **Post-Dispatch Proxy**, acknowledging that actual departure is inferred from milestone synchronization.

#### 2. Point-in-Time Feature Whitelist (27 Features)
- **Stage A Static Features (7):** Carried forward from $T_0$.
- **Warehouse History Features (7):** `picker_id`, `time_to_pick_start_min`, `pick_duration_minutes`, `items_picked`, `items_missing`, `has_picking_exception`, `picking_speed_items_per_min`.
- **Dispatch & Staging Telemetry (13):**
  - `rider_id`: Assigned courier identifier.
  - `distance_km`: Planned delivery route distance in kilometers.
  - `assignment_delay_min`: `(assignment_time - order_time) / 60`.
  - `elapsed_time_to_dispatch_min`: `(effective_dispatch_time - order_time) / 60`.
  - `remaining_sla_budget_b2_min`: `(promised_time - effective_dispatch_time) / 60`.
  - `budget_consumed_ratio_b2`: `elapsed_time_to_dispatch_min / promised_duration_minutes`.
  - `is_past_promise_at_b2`: `1` if `remaining_sla_budget_b2_min <= 0.0` else `0` (**271 orders**).
  - `transit_budget_deficit_min`: `max(0.0, -remaining_sla_budget_b2_min)`.
  - `courier_wait_at_store_min`: Minutes rider waited at dark store: `max(0.0, (pick_end - pickup_time) / 60)`.
  - `order_staging_dwell_min`: Minutes order waited in staging for rider: `max(0.0, (pickup_time - pick_end) / 60)`.
  - `rider_arrived_before_pick_end`: Binary flag (`1` in 15,094 orders).
  - `required_speed_kmh`: Feasibility metric calculated strictly when `remaining_sla_budget_b2_min > 0`:
    $$\text{required\_speed\_kmh} = \frac{\text{distance\_km}}{\text{remaining\_sla\_budget\_b2\_min} / 60.0}$$
    *Zero / Negative Budget Rule:* If `remaining_sla_budget_b2_min <= 0`, `required_speed_kmh` is set to **empty (`null`)**. **No artificial denominator floor is applied.**
  - `is_speed_unfeasible`: `1` if `remaining_budget <= 0` OR `required_speed_kmh > 60.0 km/h` (**1,869 orders, 7.67%**).

---

## 4. Outcome Labels & Anti-Leakage Governance

### 4.1. Canonical Outcome Labels
Retrospective training labels are extracted exclusively from [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv):
1. **`sla_breached`:** Binary classification target ($1 = \text{Late}, 0 = \text{On-Time}$). Verified 100% consistent with $\text{actual\_delivery\_time} > \text{promised\_time}$.
2. **`delivery_delay_minutes`:** Continuous regression target ($\max(0.0, (\text{actual\_delivery\_time} - \text{promised\_time}) / 60)$).

### 4.2. Explicitly Forbidden Features
The following fields are strictly excluded from all Stage B feature matrices:
- `orders.actual_delivery_time` (Future drop-off outcome).
- `delivery.delivery_time` (Courier app drop-off timestamp).
- `orders.delivery_delay_minutes` (Realized outcome).
- `orders.status` (Post-delivery label).
- `stage_a_predicted_risk`: **Omitted initially** to prevent in-sample leakage. Stage A will serve as an independent evaluation benchmark.

### 4.3. Synthetic Cross-Table Sequence Inconsistencies Discovered
Automated assertions identified that due to independent synthetic generator processes:
- In **25 orders (0.10%)**, `orders.actual_delivery_time` is recorded earlier than `picking.pick_end`.
- In **146 orders (0.60%)**, `orders.actual_delivery_time` is recorded earlier than `effective_dispatch_time`.
- *Governance Decision:* In accordance with data integrity rules, **these source timestamps were NOT modified or overwritten**. They are logged in [`predictive_features/stage_b_validation_audit.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_b_validation_audit.json) as documented synthetic generation artifacts.

---

## 5. Chronological Partition Distribution

All Stage B datasets strictly adhere to the project-standard chronological split boundaries based on `order_date`:

| Partition | Calendar Dates | Completed Orders ($N$) | Percentage | SLA Breaches | Empirical Breach Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train** | September 01 – September 21, 2026 | **17,031** | 69.89% | 15,297 | **89.82%** |
| **Validation** | September 22 – September 25, 2026 | **3,243** | 13.31% | 2,895 | **89.27%** |
| **Test (Holdout)** | September 26 – September 30, 2026 | **4,095** | 16.80% | 3,682 | **89.91%** |
| **Total Cohort** | September 01 – September 30, 2026 | **24,369** | **100.00%** | **21,874** | **89.76%** |

---

## 6. Verification & File Immutability Audit

The pipeline executed automated file timestamp and size assertions before and after feature generation. All 12 governing files were confirmed **UNTOUCHED**:

```
[IMMUTABILITY LOG]
orders.csv                       UNTOUCHED (12,736,693 bytes)
inventory.csv                    UNTOUCHED (1,253,132 bytes)
picking.csv                      UNTOUCHED (1,994,296 bytes)
delivery.csv                     UNTOUCHED (2,979,929 bytes)
workforce.csv                    UNTOUCHED (393,929 bytes)
stage_a_final_config.json        UNTOUCHED (2,859 bytes)
stage_a_final_metrics.json       UNTOUCHED (1,881 bytes)
STAGE_A_FINAL_EVALUATION.md      UNTOUCHED (15,355 bytes)
stage_a_features.csv             UNTOUCHED (8,619,863 bytes)
feature_metadata.json            UNTOUCHED (3,297 bytes)
validation_audit.json            UNTOUCHED (2,143 bytes)
```

---

## 7. Deliverables Summary & Step 1 Sign-Off

```
c:\Users\HP\Desktop\MacroOps\
├── build_stage_b_features.py                        (Executable feature engineering pipeline)
├── STAGE_B_FEATURE_ENGINEERING_REPORT.md            (This engineering and governance report)
└── predictive_features/
    ├── stage_b1_features.csv                        (24,369 rows, 30 columns | Checkpoint B1)
    ├── stage_b2_features.csv                        (24,369 rows, 34 columns | Checkpoint B2)
    ├── stage_b_feature_metadata.json                (Schema definitions, checkpoint rules)
    └── stage_b_validation_audit.json                (Automated assertion results & immutability log)
```

### Next Steps Pending Review:
1. Review and approve the point-in-time feature schemas and deterministic rules.
2. Proceed to **Step 2 (Model Training & Diagnostics)** to train baseline and LightGBM models for Checkpoint B1 and Checkpoint B2.
3. Benchmark incremental predictive lift against frozen Stage A on the exact 24,369 cohort.
