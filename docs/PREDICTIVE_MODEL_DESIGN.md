# MacroOps AI — Predictive Intelligence Design Review (Revised)
## Use Case: SLA Breach Risk Prediction & Delay Estimation for Incoming Orders

**Document Version:** 2.0 (Revised Design Review)  
**Phase:** Predictive Intelligence Architecture & Design  
**Author:** Lead Software Engineer & Data/AI Architect, MacroOps AI  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Database Reference:** [`macroops_analytics.db`](file:///c:/Users/HP/Desktop/MacroOps/macroops_analytics.db)  
**Status:** Approved Design Specification — Model Training Frozen Pending Next Phase  
**Date:** September 28, 2026  

---

> [!IMPORTANT]
> **SYNTHETIC DATA PROTOTYPE DISCLAIMER:**  
> **All model performance is prototype performance on synthetic data and must not be interpreted as real-world operational performance.**  
> The datasets utilized were synthetically generated for prototype evaluation, architecture validation, and platform demonstration purposes.

---

## 1. Problem Formulation & Prediction Contract

### 1.1. Core Business Objective
In quick-commerce and instant retail operations, identifying orders at risk of breaching customer SLA commitments at the earliest possible milestone allows the dispatch engine to take proactive corrective interventions:
- Re-routing orders to less congested dark stores.
- Elevating picking queue priority for bulky baskets.
- Dynamically adjusting customer delivery promises before payment confirmation.

### 1.2. Prediction Timestamp Specification
The primary prediction point is strictly defined as **ORDER CREATION / CHECKOUT TIMESTAMP** ($T_0 = \text{orders.order\_time}$):
- **Decision Moment:** The exact millisecond the customer places the order and checkout is confirmed.
- **Strict Isolation Rule:** **NO field, milestone, duration, or telemetry generated at $T > T_0$ may be utilized in the Stage A model.**
- **Temporal Integrity Rule:** Any feature whose temporal availability at $T_0$ cannot be proven from timestamps in the source files is strictly excluded.

### 1.3. Target Variable Definitions

#### Target 1: Binary SLA Breach Risk (`sla_breached`) — Classification
$$y_{\text{clf}} \in \{0, 1\}$$
- **Class 1 (SLA Breached / Positive Class):** Order delivery exceeded promised deadline ($\text{actual\_delivery\_time} > \text{promised\_time}$).
- **Class 0 (SLA Met / Negative Class):** Order delivery fulfilled on or before promised deadline ($\text{actual\_delivery\_time} \le \text{promised\_time}$).
- **Population Prevalence:** **89.68% Class 1** vs. **10.32% Class 0** (evaluated on completed deliveries in `v_completed_orders`).

#### Target 2: Realized Delivery Delay in Minutes (`delivery_delay_minutes`) — Regression
$$y_{\text{reg}} \in [0.0, \infty)$$
$$y_{\text{reg}} = \max\left(0.0, \frac{\text{actual\_delivery\_time} - \text{promised\_time}}{60.0}\right)$$
- **Explicit Definition:** **Predict realized delivery delay in minutes for completed orders.**
- **Scope Restriction:** **This regression model predicts delivery latency for orders that reach delivery drop-off. It must NOT be interpreted as an order completion or failure prediction model.**

### 1.4. Operational Population Filtering
- **Included Population:** Strictly **Completed Orders** (`status IN ('Delivered_On_Time', 'Delivered_Late')`, 97,449 orders).
- **Excluded Population:** **Cancelled Orders** (1,795 orders, 1.79%) and **Failed Orders** (756 orders, 0.76%).
- **Rationale for Exclusion:** Cancelled and Failed orders represent customer churn or drop-off failures, not delayed deliveries. The synthetic delivery timestamps populated on these orders introduce false delay signals that distort both SLA classification and delay regression.

---

## 2. Temporal Availability Audit & Feature Governance

### 2.1. Investigation: Workforce & Inventory Temporal Availability
During initial design, aggregated store-level inventory accuracy and shift-level workforce task metrics were considered as potential checkout-time features. We conducted a strict audit of their temporal legitimacy:

1. **Workforce Temporal Audit:**
   - [`workforce.csv`](file:///c:/Users/HP/Desktop/MacroOps/workforce.csv) contains `employee_id, role, store_id, shift, tasks_completed, tasks_pending`.
   - **Crucial Finding:** There is **NO date or timestamp column** in `workforce.csv`.
   - An order placed on September 14 at 19:30 belongs to the `Evening` shift. However, there are multiple unanchored records for `(store_id, 'Evening')` with differing task counts and no log dates.
   - **Verdict:** Because temporal alignment with incoming orders cannot be proven, mapping workforce metrics to checkout orders requires inventing dates or unproven assumptions. **EXCLUDED FROM STAGE A.**

2. **Inventory Temporal Audit:**
   - [`inventory.csv`](file:///c:/Users/HP/Desktop/MacroOps/inventory.csv) contains a single static snapshot of 40,000 store-SKU records.
   - **Crucial Finding:** There is **NO audit timestamp** indicating whether this represents beginning-of-month, end-of-month, or an unanchored average.
   - Furthermore, orders have no SKU-level line items, preventing dynamic stock decrementing.
   - **Verdict:** Using a static snapshot to predict orders across 30 days introduces lookahead bias or unproven temporal alignment. **EXCLUDED FROM STAGE A.**

3. **Delivery Distance Audit:**
   - `distance_km` resides exclusively in [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv).
   - In this prototype dataset, `delivery.csv` is populated for only 25,000 out of 100,000 orders.
   - **Verdict:** Using `distance_km` at Stage A would cause a 75% data loss on the full order population. **EXCLUDED FROM STAGE A (Deferred to Stage B).**

---

### 2.2. Final Stage A Approved Feature Set (Strictly 7 Features)

All 7 approved features are 100% populated in [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv), have zero nulls, and are proven to be known at the exact second of checkout:

| # | Feature Name | Source Column | Data Type | Feature Type | Operational Definition & Rationale |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | `item_count` | `orders.item_count` | Integer | Numerical (Discrete) | Total number of units in customer basket (1 to 17). Strongest proven monotonic driver of warehouse pick latency and SLA breach probability. |
| **2** | `order_value` | `orders.order_value` | Float | Numerical (Financial) | Gross order transaction value in currency units ($80 to $2,744). Proxy for basket density, item price tiers, and order complexity. |
| **3** | `promised_duration_minutes` | `promised_time - order_time` | Float | Numerical (Duration) | Customer-facing delivery window generated by the dispatch engine at checkout: `(promised_time - order_time) / 60`. Range: 20.0 to 54.3 mins. |
| **4** | `order_hour` | `substr(order_time, 12, 2)` | Integer | Categorical (Temporal) | Hour of the day (0 to 23). Captures cyclical intra-day store workload and courier congestion. |
| **5** | `day_of_week` | `strftime('%w', order_time)` | String / Int | Categorical (Temporal) | Day of the week (Monday through Sunday). Captures weekly ordering patterns and weekend traffic. |
| **6** | `is_peak_rush_hour` | Derived from `order_hour` | Integer (Binary) | Binary Flag | Indicator flag: `1` if `order_hour` $\in [17, 18, 19, 20, 21]$ (5 PM to 9 PM evening rush), else `0`. Empirically verified +23% delay surge during this window. |
| **7** | `store_id` | `orders.store_id` | String | Categorical (Spatial) | Dark store identifier (`ST001` to `ST100`). Encodes localized dark-store baseline velocity and micro-fulfillment capacity. |

---

### 2.3. Excluded Features & Leakage Blocklist

The following fields must be **strictly excluded** from Stage A feature matrices:

| Field Name | Category | Reason for Exclusion |
| :--- | :---: | :--- |
| `actual_delivery_time` | **Category C** | **Fatal Target Leakage.** Directly defines the ground-truth target. |
| `delivery_delay_minutes` | **Category C** | **Fatal Target Leakage.** Exact continuous target variable (when evaluating classification). |
| `status` | **Category C** | **Fatal Label Leakage.** Contains `Delivered_Late` vs `Delivered_On_Time`. |
| `sla_breached` | **Category C** | **Fatal Label Leakage.** Exact binary classification target. |
| `pick_start`, `pick_end` | **Category B** | Occur 4 to 17 minutes after checkout. |
| `pick_duration_minutes` | **Category B** | Picking elapsed duration; known only after picking finishes. |
| `picker_id` | **Category B** | Picker assignment occurs post-checkout. |
| `items_picked`, `items_missing` | **Category B** | Warehouse retrieval results; known only after picking completes. |
| `assignment_time`, `assignment_delay_minutes` | **Category B** | Dispatch milestones; generated ~8.17 minutes after checkout. |
| `rider_id`, `pickup_time`, `delivery_time` | **Category B** | Courier transit milestones; occur 8 to 35 minutes after checkout. |
| `distance_km` | **Category B\*** | Resides in `delivery.csv`; missing for 75,000 orders in the full population. |
| `store_shift_task_completion_rate` | **Category D** | Unanchored workforce snapshot; no date/timestamp exists to prove temporal alignment. |
| `store_shift_backlog_rate` | **Category D** | Unanchored workforce snapshot; no date/timestamp exists to prove temporal alignment. |
| `store_avg_inventory_accuracy` | **Category D** | Unanchored static inventory snapshot; audit date cannot be demonstrated. |
| `store_physical_stockout_count` | **Category D** | Unanchored static inventory snapshot; audit date cannot be demonstrated. |
| `sku_id` | **Category D** | Disconnected from `orders.csv`; no order line-item table provided. |

---

## 3. Three-Stage Progressive Modeling Architecture

MacroOps AI maintains a progressive three-stage intelligence pipeline to serve distinct operational intervention moments:

```
[Order Checkout] ─────> STAGE A: Checkout-Time SLA Risk (100,000 Orders)
       │                Approved Features: Exactly 7 Category A Features
       │                Primary Model: LightGBM Classifier & Regressor
       │                Action: Proactive Promise Adjustment / Queue Priority
       ▼
[Warehouse Staging] ──> STAGE B: In-Fulfillment Dynamic Risk Update (25,000 Orders)
       │                Incremental Features: Pick Duration, Missing Items, Assignment Delay, Distance
       │                Action: Dynamic Courier Expediting / Order Rerouting
       ▼
[Customer Drop-Off] ──> STAGE C: Post-Event Root-Cause Explanation (25,000 Orders)
                        Full Telemetry: Complete Pipeline Milestones & Courier Speed
                        Output: Automated TreeSHAP Incident Diagnostics for Copilot
```

### Stage Summary:
- **STAGE A (Checkout-Time SLA Risk):**
  - *Data Scope:* Full completed order population (**97,449 orders**).
  - *Feature Scope:* Exactly the **7 approved Category A features**.
  - *Use Case:* Predict breach risk and expected delay the instant the customer checks out.
- **STAGE B (In-Fulfillment Dynamic Risk Update):**
  - *Data Scope:* Co-indexed fulfillment cohort (**25,000 orders**).
  - *Feature Scope:* 7 Stage A features + `pick_duration_minutes`, `has_picking_exception`, `calc_assignment_delay_min`, and `distance_km`.
  - *Use Case:* Re-score risk mid-flight once warehouse picking and courier assignment telemetry arrive.
- **STAGE C (Post-Event Root-Cause Explanation):**
  - *Data Scope:* Completed orders with full telemetry (**25,000 orders**).
  - *Feature Scope:* Full end-to-end telemetry.
  - *Use Case:* Explain *why* a breach occurred (e.g. 55% picking bottleneck, 35% courier transit delay, 10% distance) to feed the AI Operations Copilot (Module 5).

---

## 4. Train / Validation / Test Splitting Strategy

### 4.1. Chronological Time-Series Partitioning
A random split allows future data to leak into past predictions. In operational logistics, models must always predict future performance from past data. Therefore, a **strict chronological partition** along the September 2026 calendar timeline is enforced:

```
[ September 1 ------------------- September 21 ] [ Sept 22 ------ Sept 25 ] [ Sept 26 ------ Sept 30 ]
             TRAIN SET (70.0%)                          VAL SET (13.3%)                 TEST SET (16.7%)
           ~68,223 Delivered Orders                 ~12,987 Delivered Orders        ~16,239 Delivered Orders
```

| Partition | Date Window (Sept 2026) | Days | Order Volume (Delivered) | Share (%) | Primary Function |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Train Set** | Sept 01 00:00:00 to Sept 21 23:59:00 | 21 | ~68,223 | **70.0%** | Model fitting, parameter estimation, feature transformations. |
| **Validation Set** | Sept 22 00:00:00 to Sept 25 23:59:00 | 4 | ~12,987 | **13.3%** | Hyperparameter tuning, probability calibration, threshold selection. |
| **Test Set (Holdout)** | Sept 26 00:00:00 to Sept 30 23:59:00 | 5 | ~16,239 | **16.7%** | Final unbiased performance benchmarking and reporting. |

### 4.2. Target-Encoding Safeguard
When encoding high-cardinality categorical variables (`store_id`):
- Encoding statistics must be computed **strictly on the Train Set (Sept 1–21)**.
- Train statistics are then mapped onto Validation and Test sets. Unseen stores fallback to global train statistics.

---

## 5. Evaluation Metrics & Class Imbalance Strategy

### 5.1. Handling the 89.68% Class Skew (The Accuracy Paradox)
- **Problem:** Because 89.68% of delivered orders are breached, a naive dummy model predicting `y = 1` for every order achieves **89.68% raw accuracy**.
- **Governance Rule:** **Raw accuracy is disqualified as a primary success metric.**
- **Operational Focus:** The critical business value lies in accurately identifying the **10.32% on-time compliant orders** and ranking orders by risk probability.

### 5.2. Approved Classification Metrics
1. **Precision-Recall AUC (PR-AUC):** Primary benchmark. Quantifies precision-recall trade-offs under heavy class imbalance.
2. **ROC-AUC:** Measures ranking discrimination across all possible decision thresholds.
3. **Minority-Class (On-Time) Recall & F1:** Measures how effectively the model detects compliant deliveries.
4. **Macro F1-Score:** Unweighted average of F1 across both classes.
5. **Calibrated Brier Score:** Measures the reliability of predicted breach probabilities.
6. **Confusion Matrix at Cost-Tuned Threshold:** Evaluated at a threshold optimized for operational cost rather than default 0.50.

### 5.3. Approved Regression Metrics (Delay in Minutes)
1. **Mean Absolute Error (MAE):** Average error magnitude in minutes. Primary benchmark.
2. **Root Mean Squared Error (RMSE):** Penalizes large latency prediction errors.
3. **$R^2$ (Coefficient of Determination):** Quantifies variance explained by checkout inputs.

---

## 6. Recommended Baseline Models for Implementation

| Model Track | Candidate Architecture | Primary Libraries | Purpose & Justification |
| :--- | :--- | :--- | :--- |
| **Stage A Classification** | **Baseline 1:** Logistic Regression (L2 penalty)<br>**Baseline 2:** LightGBM Classifier | `scikit-learn`<br>`lightgbm` | Logistic Regression provides a linear benchmark. LightGBM captures non-linear basket interactions and natively handles store categorical features with high speed on 100k rows. |
| **Stage A Delay Regression** | **Baseline 1:** Ridge Linear Regression<br>**Baseline 2:** LightGBM Regressor (Huber loss) | `scikit-learn`<br>`lightgbm` | Huber loss makes the LightGBM regressor robust against extreme delay outliers (up to 37.3 mins). |
| **Stage B Dynamic Update** | LightGBM Classifier with Monotonic Constraints | `lightgbm` | Enforces monotonic risk increases with picking duration and missing items. |
| **Stage C Root Cause** | TreeSHAP Attribution Engine | `shap` | Generates transparent factor attributions for AI Copilot explanations. |

---

## 7. Review Checklist & Implementation Roadmap

- [x] **Target Variables Defined:** Binary `sla_breached` and continuous `delivery_delay_minutes` (for completed orders).
- [x] **Prediction Point Enforced:** Strictly $T_0 = \text{order\_time}$ (Checkout).
- [x] **Stage A Feature List Finalized:** Exactly 7 approved Category A features.
- [x] **Workforce & Inventory Excluded:** Excluded due to unproven temporal availability.
- [x] **Distance Excluded from Stage A:** Excluded due to 75% telemetry subsampling.
- [x] **Cancelled/Failed Orders Excluded:** Excluded from training to eliminate synthetic dummy delay signals.
- [x] **Chronological Split Approved:** Sept 1–21 (Train), Sept 22–25 (Val), Sept 26–30 (Test).
- [x] **Prototype Disclaimer Formally Added:** Explicitly declared in header.
- [x] **Model Training Frozen:** No training executed pending user sign-off.
