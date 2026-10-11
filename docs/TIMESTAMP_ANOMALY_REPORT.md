# MacroOps AI — Timestamp Anomaly & Cross-Table Divergence Report

**Document Version:** 1.0  
**Phase:** Data Validation and Anomaly Investigation  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Datasets Analyzed:** [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv), [`picking.csv`](file:///c:/Users/HP/Desktop/MacroOps/picking.csv), [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv)  
**Population Analyzed:** 25,000 co-indexed orders shared across picking and delivery  
**Inspection Date:** September 28, 2026  

---

## 1. Executive Summary

This report delivers a deep empirical investigation into the two primary temporal anomalies identified in the MacroOps AI operational data foundation:
1. **Picking vs Delivery Pipeline Anomaly:** In **61.92% of orders**, the courier's `pickup_time` is recorded *prior* to warehouse `pick_end`.
2. **Delivery Drop-Off Time Divergence:** For **100% of orders**, `orders.actual_delivery_time` deviates from `delivery.delivery_time` by an average absolute delta of ~11.4 minutes.

Each finding is dissected into **OBSERVATION**, **EVIDENCE**, **POSSIBLE INTERPRETATIONS**, and **DECISION REQUIRED**.

---

## 2. Investigation 1: Picking vs Delivery Sequence Inversion

### 2.1. The Sequence Issue
In a physical store fulfillment workflow, the chronological expectation is:
$$\text{order\_time} \le \text{pick\_start} < \text{pick\_end} \le \text{pickup\_time} < \text{delivery\_time}$$

While internal sequences within each individual file are 100% valid, the cross-table join between `picking.csv` and `delivery.csv` reveals a massive sequence inversion:

| Sequence Condition | Order Count | Percentage | Operational Meaning |
| :--- | :---: | :---: | :--- |
| **`pickup_time >= pick_end`** | 9,520 | **38.08%** | **Standard Flow:** Order picked and staged before rider pickup. |
| **`pickup_time < pick_end`** | 15,480 | **61.92%** | **Inverted Flow:** Rider recorded picking up before picking ended. |
| **Total Shared Orders** | 25,000 | 100.00% | Exact co-indexed subset. |

---

### 2.2. Distribution of Delta ($\Delta = \text{pickup\_time} - \text{pick\_end}$)

When subtracting `pick_end` from `pickup_time` (expressed in minutes):

| Statistic | Value (Minutes) | Notes |
| :--- | :---: | :--- |
| **Minimum** | **-24.80 min** | Extreme inversion (rider left 24.8 mins before picking ended). |
| **1st Percentile (p1)** | -15.62 min | Severe sequence gap. |
| **5th Percentile (p5)** | -11.44 min | Severe sequence gap. |
| **25th Percentile (p25)** | -5.73 min | 1 in 4 orders has pickup >5.7 mins before pick end. |
| **Median** | **-1.78 min** | Typical order shows pickup ~1.8 mins before pick end. |
| **Mean** | **-1.80 min** | Symmetrical negative offset. |
| **75th Percentile (p75)** | +2.18 min | 25% of orders show normal sequence with >2.2 mins buffer. |
| **90th Percentile (p90)** | +5.67 min | Normal sequence buffer. |
| **95th Percentile (p95)** | +7.78 min | Normal sequence buffer. |
| **99th Percentile (p99)** | +11.91 min | Long staging buffer before rider departure. |
| **Maximum** | **+21.08 min** | Longest normal buffer. |
| **Standard Deviation** | **5.88 min** | High variance across the process handoff. |

#### Histogram Distribution of Delta ($\Delta = \text{pickup\_time} - \text{pick\_end}$):
```
[ < -15 min ]  ██ (329)
[-15 to -10 ]  █████████ (1,747)
[-10 to -5  ]  ███████████████████████████ (5,184)
[ -5 to 0   ]  ██████████████████████████████████████████ (8,220)  <-- Mode / Median
[  0 to 5   ]  █████████████████████████████████ (6,451)
[  5 to 10  ]  █████████████ (2,526)
[ 10 to 15  ]  ███ (489)
[ > 15 min  ]  █ (54)
```
The delta follows a clean **Gaussian distribution centered at -1.8 minutes with $\sigma \approx 5.88$ minutes**.

---

### 2.3. Surrounding Milestone Timings
To understand what occurs during this handoff, we examined dispatch assignment milestones:
- **`assignment_time - pick_start`:**
  - Range: **+0.50 to +16.84 minutes** (Mean: **+4.17 mins**, Median: **+3.99 mins**).
  - In **100.0% of orders**, rider assignment occurs **after picking has begun** (typically ~4 minutes into the pick).
- **`assignment_time - pick_end`:**
  - Mean: **-8.87 minutes** (Median: **-8.78 mins**).
  - In 96.2% of orders, riders are assigned before picking is completed.
- **`pickup_time - assignment_time`:**
  - Riders arrive/pick up an average of **7.07 minutes** after assignment.

---

### 2.4. Representative Case Studies

#### Case A: Typical Inverted Record (`ORD-062514`)
```csv
pick_start:      2026-09-09 13:14:00
assignment_time: 2026-09-09 13:17:30  (+3.5 min after pick start)
pickup_time:     2026-09-09 13:27:31  (+10.0 min after assignment)
pick_end:        2026-09-09 13:33:59  (+6.5 min AFTER rider pickup!)
delivery_time:   2026-09-09 13:43:25  (+15.9 min transit)
```
*Anomaly:* Rider `RID00695` is recorded departing at `13:27:31`, but picker `PICK00982` did not record completion until `13:33:59` (6.45 minutes later).

#### Case B: Standard Compliant Record (`ORD-029899`)
```csv
pick_start:      2026-09-02 03:34:00
assignment_time: 2026-09-02 03:40:28  (+6.5 min after pick start)
pick_end:        2026-09-02 03:42:22  (Picking completes)
pickup_time:     2026-09-02 03:46:37  (+4.25 min AFTER pick end - Normal handoff)
delivery_time:   2026-09-02 04:18:05  (+31.5 min transit)
```

---

### 2.5. Structured Findings: Picking vs Delivery

- **OBSERVATION:**  
  For 15,480 orders (61.92%), `delivery.pickup_time` is earlier than `picking.pick_end`, with an average discrepancy of 1.8 minutes and a normal distribution spanning -24.8 to +21.1 minutes.

- **EVIDENCE:**  
  - 100% of internal timelines (`pick_start < pick_end` and `assignment_time < pickup_time < delivery_time`) are strictly valid.
  - The cross-table difference $(\text{pickup\_time} - \text{pick\_end})$ is negative in 61.92% of cases, with median -1.78 minutes.
  - The distribution is completely smooth without discrete step-function artifacts.

- **POSSIBLE INTERPRETATIONS:**  
  1. **Interpretation A (Systematic Data-Generation Artifact):**  
     The synthetic dataset generator likely simulated the picking lifecycle and delivery dispatch lifecycle using two independent stochastic processes:
     - Process 1 (Picking): `pick_end = pick_start + normal(13.0, 5.0)`
     - Process 2 (Delivery): `assignment_time = pick_start + uniform(0.5, 8.0)` and `pickup_time = assignment_time + normal(7.0, 3.0)`
     Because these two equations were evaluated independently without an explicit constraint enforcement ($\text{pickup\_time} \ge \text{pick\_end}$), whenever pick duration took longer than average, the rider's arrival fell before pick completion.
  2. **Interpretation B (Timestamp Semantic Definition):**  
     In dark-store WMS terminology, `delivery.pickup_time` may actually represent **Rider Arrival / Store Check-In Time** (when the rider taps "Arrived at Dark Store" in the courier app) rather than physical departure. In this operational model, riders routinely arrive 1 to 5 minutes before packaging finishes and wait in the dispatch bay.
  3. **Interpretation C (Operational Staging / Multi-item handoff):**  
     In quick-commerce, large orders (e.g. 10+ items) might undergo progressive handover or bag pre-sealing before the digital pick-list is formally closed.

- **DECISION REQUIRED:**  
  - **Do NOT alter original CSV timestamps.**
  - For analytics and modeling, document whether `pickup_time` should be treated semantically as *Rider Arrival at Store* or whether downstream feature engineering should derive an effective departure time: $\text{effective\_departure} = \max(\text{pick\_end}, \text{pickup\_time})$.

---

## 3. Investigation 2: Orders vs Delivery Delivery-Time Divergence

### 3.1. Divergence Extent
[`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv) and [`delivery.csv`](file:///c:/Users/HP/Desktop/MacroOps/delivery.csv) both contain a delivery completion timestamp:
- `orders.actual_delivery_time`
- `delivery.delivery_time`

When comparing these two fields across all 25,000 shared orders:

| Metric | Count | Percentage |
| :--- | :---: | :---: |
| **Total Shared Orders** | 25,000 | 100.00% |
| **Exact Matching Records** | **0** | **0.00%** |
| **Differing Records** | **25,000** | **100.00%** |
| `delivery.delivery_time` > `orders.actual_delivery_time` | 12,293 | **49.17%** |
| `delivery.delivery_time` < `orders.actual_delivery_time` | 12,707 | **50.83%** |

---

### 3.2. Statistical Distribution of Difference ($\Delta = \text{delivery\_time} - \text{actual\_delivery\_time}$)

All metrics expressed in **minutes**:

| Statistic | Value (Minutes) | Notes |
| :--- | :---: | :--- |
| **Minimum** | **-51.53 min** | Delivery CSV is 51.5 mins earlier than Orders actual. |
| **1st Percentile (p1)** | -29.97 min | Substantial negative divergence. |
| **5th Percentile (p5)** | -21.61 min | Substantial negative divergence. |
| **25th Percentile (p25)** | -9.56 min | 1 in 4 orders has Delivery CSV >9.5 mins earlier. |
| **Median** | **-0.28 min** | **Virtually zero median divergence (~17 seconds).** |
| **Mean** | **+1.64 min** | Minor positive mean bias. |
| **75th Percentile (p75)** | +10.79 min | 25% of orders have Delivery CSV >10.8 mins later. |
| **90th Percentile (p90)** | +22.81 min | Substantial positive divergence. |
| **95th Percentile (p95)** | +31.38 min | Substantial positive divergence. |
| **99th Percentile (p99)** | +50.50 min | Substantial positive divergence. |
| **Maximum** | **+90.57 min** | Delivery CSV is 90.6 mins later than Orders actual. |
| **Standard Deviation** | **16.36 min** | High spread ($\sigma \approx 16.4$ min). |

#### Histogram of Difference:
```
[ < -30 min  ]  █ (245)
[-30 to -15  ]  ███████████ (3,078)
[-15 to -5   ]  ██████████████████████ (5,982)
[ -5 to 0    ]  ████████████ (3,402)
[ 0 (exact)  ]  (0)
[  0 to 5    ]  ███████████ (3,068)
[  5 to 15   ]  █████████████████ (4,634)
[ 15 to 30   ]  ███████████ (3,182)
[ > 30 min   ]  █████ (1,409)
```
The divergence is **near-perfect symmetric noise centered right at zero (-0.28 min)**. 49.17% of orders show `delivery.delivery_time` after `orders.actual_delivery_time`, while 50.83% show it before.

---

### 3.3. SLA Calculation Alignment Audit: Which Timestamp Governs SLA?

We conducted a mathematical audit comparing both timestamps against the reported `orders.delivery_delay_minutes` and `orders.sla_breached`:

$$\text{calc\_delay\_orders} = \max(0.0, \text{round}((\text{orders.actual\_delivery\_time} - \text{promised\_time}) / 60, 1))$$
$$\text{calc\_delay\_delivery} = \max(0.0, \text{round}((\text{delivery.delivery\_time} - \text{promised\_time}) / 60, 1))$$

| Candidate Source | Reconciled Exact Matches | Match Rate (%) | Ground Truth Audit Verdict |
| :--- | :---: | :---: | :--- |
| **`orders.actual_delivery_time`** | **25,000 out of 25,000** | **100.00%** | **PROVEN MATHEMATICAL GROUND TRUTH** for SLA calculations. |
| **`delivery.delivery_time`** | **879 out of 25,000** | **3.52%** | Uncorrelated with SLA delay numbers (only incidental matches). |

---

### 3.4. Structured Findings: Delivery-Time Divergence

- **OBSERVATION:**  
  `orders.actual_delivery_time` and `delivery.delivery_time` differ in 100% of shared orders, distributed symmetrically around zero (median: -0.28 min, std dev: 16.36 min).

- **EVIDENCE:**  
  - 100% of reported delays and SLA breaches in `orders.csv` match `orders.actual_delivery_time` to within 0.1 minutes.
  - Only 3.52% of delays match `delivery.delivery_time`.
  - The divergence has a 49.17% / 50.83% positive/negative split.

- **POSSIBLE INTERPRETATIONS:**  
  1. **Dual System Semantics (Real-World Architecture):**  
     In production logistics architectures, two separate timestamps frequently exist:
     - `orders.actual_delivery_time`: The **Core Order Service / Customer Confirmation Timestamp** (system OTP entry, automated geofence checkout, or customer confirmation), which binds the SLA guarantee.
     - `delivery.delivery_time`: The **Rider Mobile App Client Timestamp**, recorded by the courier's device. Differences arise from mobile app sync delay, offline caching, GPS drift, or manual completion taps after leaving the customer doorstep.
  2. **Independent Synthetic Generation Artifact:**  
     The data generator created `orders.csv` delivery times based on promised time and target SLA breach rates, while separately generating `delivery.csv` transit times based on distance and rider speed, without harmonizing the final timestamps.

- **DECISION REQUIRED:**  
  - **Do NOT modify original CSVs.**
  - **Adopt `orders.actual_delivery_time` as the authoritative Ground Truth for SLA evaluation and customer promises.**
  - **Adopt `delivery.delivery_time` as Rider Telemetry** for analyzing transit duration and courier mobility behavior.
