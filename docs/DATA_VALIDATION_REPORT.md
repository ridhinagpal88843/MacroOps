# MacroOps AI — Comprehensive Data Validation & Anomaly Investigation Report

**Platform:** MacroOps AI — GenAI-Powered Fulfillment & Last-Mile Operations Intelligence  
**Document Version:** 1.0  
**Phase:** Data Validation & Anomaly Investigation  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Supporting Reports:**  
- [SLA_ANALYSIS.md](file:///c:/Users/HP/Desktop/MacroOps/SLA_ANALYSIS.md)  
- [TIMESTAMP_ANOMALY_REPORT.md](file:///c:/Users/HP/Desktop/MacroOps/TIMESTAMP_ANOMALY_REPORT.md)  
- [DATA_DICTIONARY.md](file:///c:/Users/HP/Desktop/MacroOps/DATA_DICTIONARY.md)  
- [DATA_RELATIONSHIPS.md](file:///c:/Users/HP/Desktop/MacroOps/DATA_RELATIONSHIPS.md)  
**Inspection Date:** September 28, 2026  

---

## 1. Executive Summary & Validation Scope

This report provides the consolidated findings from the focused deep-dive investigation into the MacroOps AI operational data assets. 

All 200,000 records across the 5 source CSV files were evaluated without modification. The investigation concentrated on three core systemic anomalies and an audit of terminal order states:
1. **The 89.67% SLA Breach Rate in [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv)**
2. **The Picking vs Delivery Timestamp Sequence Inversion across [`picking.csv`](file:///c:/Users/HP/Desktop/MacroOps/picking.csv) and [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv)**
3. **The Delivery Completion Timestamp Divergence between [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv) and [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv)**
4. **The Ghost Fulfillment of Cancelled and Failed Orders**

---

## 2. Issue 1: SLA Breach Rate Distribution & Behavior

### 2.1. Empirical Findings Summary
- **Overall Breach Rate:** **89.674%** (89,674 out of 100,000 orders).
- **Exact Calculation:** A strict binary threshold: $\text{sla\_breached} = 1 \iff \text{actual\_delivery\_time} > \text{promised\_time}$.
- **Delivery Delay Distribution:** Mean: **6.43 mins**, Median: **5.80 mins**, p75: **9.50 mins**, p95: **15.70 mins**, Max: **37.30 mins**.
- **Promised Delivery Duration (`promised_time - order_time`):** Mean: **29.65 mins**, Median: **29.44 mins**, Min: **exactly 20.00 mins** (rigid synthetic lower bound).
- **Actual Delivery Duration (`actual_delivery_time - order_time`):** Mean: **35.90 mins**, Median: **35.34 mins**.
- **Fulfillment Deficit:** Operations take an average of **+6.25 minutes longer** than the customer promise across the population.

### 2.2. Cohort Uniformity vs Outlier Analysis
- **Store-Level Uniformity:** All 100 dark stores exhibit breach rates within a tight **86.63% to 92.89%** band ($\text{mean} = 89.68\%, \sigma = 1.39\%$). There are no localized outlier stores causing the breach.
- **Daily Uniformity:** Daily breach rates across all 30 days in September 2026 stay within **88.06% to 91.02%** ($\sigma = 0.66\%$).
- **Hourly Rush Dynamic:** Breach rate is flat at ~89.0% from 00:00 to 16:00, then rises to **92.32% during peak evening hours (17:00 to 21:00)** with delay increasing from 6.1 to 7.5 minutes.
- **Basket Size Sensitivity:** Breach rate increases monotonically with item count:
  - 1 item: **79.79%** (avg delay: 4.37 min)
  - 5 items: **90.18%** (avg delay: 6.33 min)
  - 10 items: **98.08%** (avg delay: 9.53 min)
  - 13+ items: **100.00%** (avg delay: 11.5–14.3 min)

### 2.3. Structured Finding: SLA Breach Rate
- **OBSERVATION:**  
  The 89.67% breach rate is a system-wide structural characteristic driven by an operational deficit where actual fulfillment (~35.9 mins) structurally outpaces promised delivery windows (~29.7 mins).
- **EVIDENCE:**  
  Store breach variance is minimal ($\sigma = 1.39\%$), day-to-day variance is minimal ($\sigma = 0.66\%$), and delays scale directly with basket item counts.
- **POSSIBLE INTERPRETATIONS:**  
  1. *Synthetic Parameterization:* The data generator created promised times with a mean of ~29.5 min and actual times with a mean of ~35.9 min, creating an intended scenario of an operation in severe SLA distress.
  2. *Static SLA Promise:* The business promises a ~30-minute delivery SLA regardless of order complexity, creating an unavoidable bottleneck on large baskets.
- **DECISION REQUIRED:**  
  - For analytics and modeling, retain the 89.67% baseline as the legitimate representation of the current operational state.
  - In executive dashboards, highlight that 11.63% of breaches are under 2 minutes (grace period sensitivity).

---

## 3. Issue 2: Picking vs Delivery Timestamp Sequence Inversion

### 3.1. Empirical Findings Summary
- **Population:** 25,000 orders shared across `picking.csv` and `delivery.csv`.
- **Compliant Sequence (`pickup_time >= pick_end`):** **9,520 orders (38.08%)**
- **Inverted Sequence (`pickup_time < pick_end`):** **15,480 orders (61.92%)**
- **Difference Statistics ($\Delta = \text{pickup\_time} - \text{pick\_end}$):**
  - Min: **-24.80 mins** | Median: **-1.78 mins** | Mean: **-1.80 mins** | Max: **+21.08 mins** | Std Dev: **5.88 mins**
  - The difference follows a near-perfect Gaussian distribution centered at -1.8 minutes.
- **Assignment Context:** In 100% of orders, `delivery.assignment_time` occurs **after `picking.pick_start`** (mean: +4.17 minutes after pick start), and riders arrive at the store an average of 7.07 minutes later.

### 3.2. Structured Finding: Sequence Inversion
- **OBSERVATION:**  
  In 61.92% of fulfillment runs, the courier's `pickup_time` is recorded earlier than warehouse `pick_end` (median: 1.78 minutes prior).
- **EVIDENCE:**  
  Internal ordering within `picking.csv` (`pick_start < pick_end`) is 100% valid. Internal ordering within `delivery.csv` (`assignment < pickup < delivery`) is 100% valid. The inversion only appears at the cross-table join.
- **POSSIBLE INTERPRETATIONS:**  
  1. *Independent Generation Artifact (Most Probable Technical Cause):* The synthetic simulator generated picking duration and rider arrival independently without an inter-process dependency lock ($\text{pickup\_time} \ge \text{pick\_end}$).
  2. *Timestamp Definition Ambiguity:* In field operations, `delivery.pickup_time` often denotes **Rider Store Arrival / Check-in Time** (when the rider reaches the dark store bay and waits for the order).
  3. *Staging Overlap:* Progressive bin staging where couriers receive items as picked before digital checkout.
- **DECISION REQUIRED:**  
  - **Do NOT modify original CSV timestamps.**
  - In feature engineering pipelines, treat `pickup_time` as *Rider Arrival / Check-In Time* or construct an effective dispatch timestamp: $\text{dispatch\_time} = \max(\text{pick\_end}, \text{pickup\_time})$.

---

## 4. Issue 3: Orders vs Delivery Delivery-Time Divergence

### 4.1. Empirical Findings Summary
- **Population:** 25,000 shared orders.
- **Exact Matches:** **0 out of 25,000 (0.00%)**
- **Diverging Records:** **25,000 out of 25,000 (100.00%)**
- **Directional Split:**
  - `delivery.delivery_time` > `orders.actual_delivery_time`: **12,293 orders (49.17%)**
  - `delivery.delivery_time` < `orders.actual_delivery_time`: **12,707 orders (50.83%)**
- **Difference Statistics ($\Delta = \text{delivery\_time} - \text{actual\_delivery\_time}$):**
  - Min: **-51.53 mins** | Median: **-0.28 mins (~17 seconds)** | Mean: **+1.64 mins** | Max: **+90.57 mins** | Std Dev: **16.36 mins**
  - The divergence forms a symmetrical bell curve centered at approximately zero (-17 seconds).

### 4.2. SLA Alignment Audit
- **Match with `orders.actual_delivery_time`:** **25,000 out of 25,000 (100.00%)** of reported delay minutes and SLA breach flags match `orders.actual_delivery_time`.
- **Match with `delivery.delivery_time`:** Only **879 out of 25,000 (3.52%)** match.

### 4.3. Structured Finding: Delivery-Time Divergence
- **OBSERVATION:**  
  `orders.actual_delivery_time` and `delivery.delivery_time` diverge across 100% of records as zero-centered symmetric noise ($\text{median} = -0.28\text{ min}, \sigma = 16.36\text{ min}$).
- **EVIDENCE:**  
  The mathematical SLA logic in `orders.csv` was derived 100% from `orders.actual_delivery_time`.
- **POSSIBLE INTERPRETATIONS:**  
  1. *Dual System Telemetry:* `orders.actual_delivery_time` represents the central order management platform event (customer confirmation / OTP / system drop-off), while `delivery.delivery_time` represents mobile driver app telematics (subject to sync latency, GPS drift, or manual courier taps).
  2. *Synthetic Generation Artifact:* Independent simulation of order SLA vs transit legs.
- **DECISION REQUIRED:**  
  - **Do NOT alter original CSV timestamps.**
  - Establish **`orders.actual_delivery_time` as the authoritative Ground Truth for SLA monitoring and customer-facing metrics**.
  - Retain **`delivery.delivery_time` as rider transit telemetry** for measuring road speed and travel times.

---

## 5. Investigation of Cancelled and Failed Orders

A dedicated audit was conducted on non-completed order states in `orders.csv`:
- **Cancelled Orders:** 1,795 records (1.795% of orders)
- **Failed Orders:** 756 records (0.756% of orders)
- **Total Non-Delivered:** 2,551 records (2.551% of orders)

### 5.1. Audit Matrix
| Audit Question | Cancelled Orders (1,795) | Failed Orders (756) | Total / Combined (2,551) |
| :--- | :---: | :---: | :---: |
| **How many have actual delivery timestamps?** | **1,795 (100.0%)** | **756 (100.0%)** | **2,551 (100.0%)** |
| **How many have reported delivery delay minutes?** | **1,795 (100.0%)** | **756 (100.0%)** | **2,551 (100.0%)** |
| **How many are flagged `sla_breached = 1`?** | 1,602 (89.25%) | 680 (89.95%) | 2,282 (89.45%) |
| **How many are flagged `sla_breached = 0`?** | 193 (10.75%) | 76 (10.05%) | 269 (10.55%) |
| **How many exist in `picking.csv`?** | 445 (24.79%) | 186 (24.60%) | 631 (24.74%) |
| **How many exist in `delivery.csv`?** | 445 (24.79%) | 186 (24.60%) | 631 (24.74%) |
| **Average reported delay minutes** | 6.40 mins (max 37.3) | 6.32 mins (max 23.3) | 6.38 mins |

### 5.2. Operational & Data-Quality Evaluation

#### Question 1: Should Cancelled and Failed orders be excluded from operational SLA metrics?
- **EVALUATION:** **YES (Mandatory Exclusion).**
- **RATIONALE:**  
  1. A cancelled or failed order is an order fulfillment defect or customer abandonment, **not a late delivery**.
  2. Assigning a delivery delay (e.g. "Cancelled order delayed by 14.4 minutes") corrupts delivery speed analytics and misrepresents courier performance.
  3. In standard retail/quick-commerce operations, the primary KPI for these orders is **Cancellation Rate (1.80%)** and **Failure Rate (0.76%)**, tracked separately from **On-Time Delivery Rate (OTD)** and **SLA Breach Rate**.

#### Question 2: Should Cancelled and Failed orders be retained for data-quality analysis and exception management?
- **EVALUATION:** **YES (Mandatory Retention).**
- **RATIONALE:**  
  1. In the planned MacroOps AI roadmap, **Module 3 is Exception Management** and **Module 6 is AI Copilot / Analytics**. These 2,551 records constitute the primary operational exception cohort.
  2. For the 631 records with picking and delivery logs, they provide critical data on mid-fulfillment cancellations (e.g. customer cancelled after picking, rider failed to locate address during transit).
  3. They serve as essential training examples for predictive cancellation and risk detection models.

### 5.3. Structured Finding: Cancelled & Failed Orders
- **OBSERVATION:**  
  100% of Cancelled and Failed orders have synthetic delivery timestamps and delay calculations in `orders.csv`, and ~24.7% appear fully executed in `picking.csv` and `delivery.csv`.
- **EVIDENCE:**  
  2,282 Cancelled/Failed orders are flagged `sla_breached = 1` and 269 are flagged `sla_breached = 0` based on dummy delivery timestamps.
- **POSSIBLE INTERPRETATIONS:**  
  1. The data generator executed a blind loop across all 100,000 orders without masking out terminal non-delivered states.
  2. In quick-commerce, "Failed" orders may represent attempted deliveries where the rider arrived at the location but could not complete the drop-off (customer unreachable).
- **DECISION REQUIRED:**  
  - In data modeling, create a clean operational view:
    $$\text{Completed\_Orders} = \text{Orders}[\text{status} \in \{\text{'Delivered\_On\_Time'}, \text{'Delivered\_Late'}\}]$$
    $$\text{Exception\_Orders} = \text{Orders}[\text{status} \in \{\text{'Cancelled'}, \text{'Failed'}\}]$$
  - Filter out `Exception_Orders` when calculating customer fulfillment SLA and transit speed KPIs.
  - Route `Exception_Orders` to the Exception Management and Churn Analytics data mart.

---

## 6. Synthesis of Structured Findings

| Investigation Area | Observation | Evidence | Primary Interpretation | Recommended Decision |
| :--- | :--- | :--- | :--- | :--- |
| **89.67% SLA Breach Rate** | Structural, systemic breach across all stores and days. | $\sigma = 1.39\%$ across stores; delay scales linearly with item count. | Operations structurally require ~36 min vs ~30 min promised window. | Treat as valid baseline; analyze promise-vs-capacity gap. |
| **Picking vs Delivery Inversion** | Rider pickup precedes pick end in 61.92% of shared orders. | Median difference is -1.78 mins; normal bell curve. | Independent simulation of pick vs dispatch; or pickup = arrival. | Treat `pickup_time` as Rider Arrival; construct effective dispatch time. |
| **Delivery Time Divergence** | 100% mismatch between Orders actual and Delivery drop-off. | Zero-centered noise ($\sigma = 16.36$ min); 100% SLA match on Orders actual. | Orders actual is Core System SLA truth; Delivery time is mobile telemetry. | Adopt `orders.actual_delivery_time` as Ground Truth for SLA. |
| **Cancelled / Failed Orders** | Full delivery timestamps and SLA flags populated. | 2,551 records have delays; 631 exist in picking & delivery. | Data generator did not mask terminal unfulfilled states. | Exclude from delivery SLA metrics; retain for Exception Management. |

---

## 7. Recommended Next Data-Modeling Step

Based **strictly on the empirical evidence gathered**, the recommended next step is:

### Step 1: Formalize the MacroOps Canonical Data Model (Semantic Layer / Views)
Create non-destructive, clean analytical views (e.g. using DuckDB, SQLite, or SQL view definitions) that preserve the raw CSVs untouched while establishing:
1. **Authoritative Metric Ground Truth:** Bind SLA delay and compliance calculations strictly to `orders.actual_delivery_time` and `orders.promised_time`.
2. **Operational Cohort Segmentation:**
   - Partition orders into `Fulfillment_Cohort` (97,449 delivered orders) and `Exception_Cohort` (2,551 cancelled/failed orders).
   - Create a clean `Full_Lifecycle_Cohort` for the 25,000 orders containing end-to-end picking and delivery telemetry.
3. **Derived Milestone Pipeline:**
   - Construct derived fields:
     - `picking_duration_min = round((pick_end - pick_start)/60, 1)`
     - `assignment_delay_min = round((assignment_time - order_time)/60, 1)`
     - `rider_wait_time_min = max(0.0, round((pick_end - pickup_time)/60, 1))` (treating `pickup_time` as rider arrival)
     - `transit_duration_min = round((delivery_time - max(pick_end, pickup_time))/60, 1)`
4. **Aggregate Operational Dimensions:**
   - Build store-level and shift-level rollups to bridge the workforce table without attempting invalid employee-level joins.

*We await your approval before establishing this semantic modeling layer.*
