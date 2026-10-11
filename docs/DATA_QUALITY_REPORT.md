# MacroOps AI — Comprehensive Data Quality Report

**Document Version:** 1.0  
**Phase:** Data Understanding & Foundation  
**Reference Document:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Inspection Date:** September 28, 2026  
**Audited Datasets:** `orders.csv`, `inventory.csv`, `picking.csv`, `delivery.csv`, `workforce.csv`  

---

## 1. Executive Summary & Quality Scorecard

Across the 200,000 records examined, the MacroOps AI datasets exhibit **high structural formatting integrity** (no missing values, no corrupt records, valid syntactical formatting, and no negative numbers). 

However, rigorous cross-dataset reconciliation and behavioral audits reveal **critical semantic, temporal, and referential anomalies** inherent to synthetic generation that must be handled prior to production model training, KPI dashboard construction, or AI copilot deployment.

### Quality Scorecard by Dimension:
| Dimension | Rating | Description |
| :--- | :---: | :--- |
| **Completeness** | **A+** (100%) | Zero null, empty, or unparseable fields across all 200,000 records. |
| **Uniqueness** | **A** (99.9%) | Zero exact full-row duplicates. Primary keys in `orders`, `picking`, and `delivery` are 100% unique. Only `workforce` lacks a unique key. |
| **Validity (Syntactic)** | **A+** (100%) | Formats (dates, floats, strings, enums) conform strictly to standard syntaxes. |
| **Consistency (Internal)** | **A-** (92%) | Mathematical formulas (`stock_variance`, `inventory_accuracy_pct`, `pick_duration_minutes`) are 100% consistent with raw inputs. |
| **Consistency (Cross-Dataset)** | **C** (58%) | **Severe temporal discrepancies** between `orders` and `delivery`, and between `picking` and `delivery`. |
| **Referential Completeness** | **B-** (70%) | Strong store-level linkage, but 75% of orders lack fulfillment logs, and workforce/SKU tables are disconnected from orders. |

---

## 2. Missing Values & Duplicate Analysis

### 2.1. Missing Values:
- **Total Null / Empty Cells:** **0 across all 37 columns and 200,000 rows.**
- Every column is 100% populated. No empty strings, `NULL`, `NaN`, or whitespace-only records were detected.

### 2.2. Duplicate Rows:
- **Full Row Duplicates:** **0 across all 5 datasets.**
- **Key Duplication:**
  - `orders.order_id`: 100,000 unique values (0 duplicates) — **Valid PK**.
  - `inventory.(store_id, sku_id)`: 40,000 unique pairs (0 duplicates) — **Valid PK**.
  - `picking.order_id`: 25,000 unique values (0 duplicates) — **Valid PK**.
  - `delivery.order_id`: 25,000 unique values (0 duplicates) — **Valid PK**.
  - `workforce.employee_id`: 2,456 unique IDs across 10,000 rows (Average 4.07 rows per employee).
  - `workforce.(employee_id, store_id, role, shift)`: Contains **17 duplicate composite occurrences** with differing task metrics (e.g., `EMP01304` at `ST054` on `Evening` shift as `Picker` recorded twice: once with 49 completed / 8 pending, and once with 44 completed / 4 pending).

---

## 3. Detailed Inconsistencies & Invalid Values

### 3.1. [CRITICAL] Delivery Timestamp Divergence (`orders` vs `delivery`)
- **Issue:** For 100% of the 25,000 overlapping orders, `orders.actual_delivery_time` **DOES NOT MATCH** `delivery.delivery_time`.
- **Metrics:**
  - Exact matches: **0 out of 25,000 (0.0%)**
  - Minimum difference: **-43.95 minutes** (`delivery.delivery_time` earlier than `orders.actual_delivery_time`)
  - Maximum difference: **+78.08 minutes** (`delivery.delivery_time` later than `orders.actual_delivery_time`)
  - Mean absolute difference: **~11.4 minutes**
- **Impact:** 
  - `orders.delivery_delay_minutes` and `orders.sla_breached` were calculated strictly against `orders.actual_delivery_time`.
  - If an analytics dashboard or AI Copilot calculates SLA breach using `delivery.delivery_time`, the SLA status will contradict `orders.csv` in thousands of cases!

#### Evidence Sample:
| Order ID | Promised Time | Orders Actual Delivery | Delivery CSV Delivery Time | Delta (`Delivery - Orders`) | Orders Delay (Mins) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ORD-029899` | 03:53:24 | 03:55:08 | 04:18:05 | **+22.95 mins** | 1.7 |
| `ORD-062514` | 13:48:41 | 14:04:30 | 13:43:25 | **-21.08 mins** | 15.8 |
| `ORD-022321` | 04:12:16 | 04:14:15 | 04:26:09 | **+11.90 mins** | 2.0 |
| `ORD-079556` | 02:57:02 | 03:06:26 | 02:41:43 | **-24.71 mins** | 9.4 |

---

### 3.2. [CRITICAL] Temporal Pipeline Inversion (`picking` vs `delivery`)
- **Issue:** In **15,480 out of 25,000 orders (61.92%)**, the rider's `pickup_time` at the store occurs **BEFORE** the picker completed the order (`pick_end`).
- **Real-World Anomaly:** In physical operations, a delivery courier cannot pick up and depart with an order that warehouse staff has not yet finished picking.
- **Average Anomaly Extent:** Riders are recorded picking up orders an average of 4.2 minutes before picking ended (with anomalies up to 28 minutes early).

#### Evidence Sample:
| Order ID | Picking Start | Picking End | Rider Assignment | Rider Pickup | Anomaly Delta (`pickup - pick_end`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ORD-062514` | 13:14:00 | **13:33:59** | 13:17:30 | **13:27:31** | **-6.45 mins (Picked up before pick end)** |
| `ORD-008046` | 20:54:00 | **21:11:57** | 20:57:25 | **21:00:09** | **-11.80 mins (Picked up before pick end)** |
| `ORD-079556` | 02:33:00 | **02:39:37** | 02:35:19 | **02:37:19** | **-2.31 mins (Picked up before pick end)** |

---

### 3.3. [HIGH] Cancelled and Failed Orders Fully Processed in Logistics Logs
- **Issue:** In `orders.csv`, there are **1,795 Cancelled** orders and **756 Failed** orders.
- **Anomalies Identified:**
  1. **Delivery timestamps populated:** Every single Cancelled and Failed order has an `actual_delivery_time` and `delivery_delay_minutes` populated in `orders.csv`.
  2. **Inclusion in Picking & Delivery:** Exactly 445 Cancelled orders and 186 Failed orders exist in both `picking.csv` and `delivery.csv`, showing completed pick cycles, picker IDs, rider assignments, pickup times, delivery drop-off times, and travel distances.
  3. **Inconsistent SLA Assignment:**
     - 1,602 Cancelled orders are flagged `sla_breached = 1`, and 193 are flagged `sla_breached = 0`.
     - 680 Failed orders are flagged `sla_breached = 1`, and 76 are flagged `sla_breached = 0`.
     - Standard logistics logic dictates that Cancelled/Failed orders represent customer churn or fulfillment failures, not on-time vs late deliveries.

---

### 3.4. [HIGH] Workforce Data Disconnect & Ambiguity
- **Issue:**
  1. **Missing Temporal Anchor:** `workforce.csv` contains no date, timestamp, or day-of-week. It is impossible to determine whether records represent daily logs, monthly totals, or shift averages across September 2026.
  2. **Disconnected Identifiers:** `workforce.employee_id` (`EMPxxxxx`) does not correlate with `picking.picker_id` (`PICKxxxxx`) or `delivery.rider_id` (`RIDxxxxx`). There is zero referential bridge.
  3. **High Employee Mobility/Volatility:** 92.9% of employees (2,282 out of 2,456) appear assigned across multiple different stores, and 86.8% appear under multiple operational roles (e.g. working as a Packer in one shift and a Rider Coordinator in another). Without date stamps, this suggests multi-skilling or synthetic noise.

---

### 3.5. [MEDIUM] Operational Coverage Skew (75% Missing Fulfillment Data)
- **Issue:** Out of 100,000 orders in `orders.csv`, exactly 25,000 exist in `picking.csv` and `delivery.csv`.
- **Status Distribution Comparison:**
  - In 25,000 subset: 87.50% Delivered_Late, 9.98% Delivered_On_Time, 1.78% Cancelled, 0.74% Failed.
  - In 75,000 remainder: 87.36% Delivered_Late, 10.08% Delivered_On_Time, 1.80% Cancelled, 0.76% Failed.
- **Finding:** The 25,000 sample is a **stratified uniform random sample** (distribution across statuses is statistically identical). However, full-pipeline analysis is restricted to 25% of orders.

---

### 3.6. [MEDIUM] Extreme Late Delivery Operational Skew
- **Issue:** In `orders.csv`, **87,392 orders (87.39%)** are marked `Delivered_Late`, and total SLA breaches reach **89,674 (89.67%)**.
- **Context:** In quick-commerce operations, an 89.7% SLA breach rate is catastrophic. This high baseline rate means predictive models will encounter extreme class imbalance in reverse (on-time orders are the rare minority at ~10%).

---

### 3.7. [LOW] Extreme Stockout Rarity in Inventory
- **Issue:** Out of 40,000 store-SKU inventory records, only **3 records (0.0075%)** have `stockout = 'Yes'` and `physical_stock = 0`.
- **Finding:** Conversely, in `picking.csv`, **2,920 orders (11.68%)** encountered missing items during picking. Since inventory is a single static snapshot without SKU links to orders, inventory stockouts cannot be directly reconciled with picking item stockouts.

---

## 4. Potential Data-Quality Risks & Mitigation Recommendations

| Risk Category | Potential Operational / Technical Failure | Mitigation Strategy for MacroOps AI |
| :--- | :--- | :--- |
| **Model Training Risk (SLA Prediction)** | Predictive models trained on `delivery.delivery_time` vs `orders.actual_delivery_time` will learn conflicting ground-truth targets. | Establish `orders.actual_delivery_time` as the single authoritative source of truth for SLA breach labeling; treat `delivery.csv` as transit telemetry. |
| **Feature Leakage / Chronology Inversion** | If an ML pipeline uses `delivery.pickup_time` to predict picking delays, it will use future information due to the 61.9% `pickup_time < pick_end` anomaly. | Enforce strict chronological feature engineering: only use order creation and early assignment features when predicting picking bottlenecks. |
| **RAG / GenAI Copilot Hallucination** | When operations managers ask the AI Copilot "Why did Order ORD-029899 breach SLA?", the LLM could see conflicting delivery timestamps (03:55 vs 04:18) and report erroneous facts. | In RAG ingestion prompts and tool definitions, explicitly document the timestamp semantics (e.g. "orders.actual_delivery_time is system SLA delivery time; delivery.delivery_time is driver app completion time"). |
| **Executive Reporting Distortions** | Reporting Cancelled and Failed orders as "Delivered Late with 15 mins delay" will corrupt fulfillment metrics. | Create cleaned reporting views where Cancelled and Failed orders are partitioned out from fulfillment duration and transit calculations. |
| **Worker Productivity Metrics** | Trying to compute individual picker speed by joining `workforce.employee_id` with `picking.picker_id` will fail. | Aggregate workforce productivity strictly at the `store_id` and `shift` level; do not attempt employee-level operational attribution. |
