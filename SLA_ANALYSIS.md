# MacroOps AI — Deep SLA Breach & Order Latency Analysis

**Document Version:** 1.0  
**Phase:** Data Validation and Anomaly Investigation  
**Authoritative Reference:** [README.txt](file:///c:/Users/HP/Desktop/MacroOps/README.txt)  
**Dataset Analyzed:** [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv) (100,000 records)  
**Inspection Date:** September 28, 2026  

---

## 1. Executive Summary & Core SLA Metrics

In [`orders.csv`](file:///c:/Users/HP/Desktop/MacroOps/orders.csv), exactly **89,674 out of 100,000 orders (89.674%)** are flagged as `sla_breached = 1`. This section provides the rigorous empirical analysis of whether this alarming rate is an operational reality, an artifact of tight promised delivery windows, or driven by specific operational cohorts.

### Headline Performance Indicators:
| Metric | Value | Population | Interpretation |
| :--- | :--- | :--- | :--- |
| **Total Order Volume** | 100,000 | All Orders | 30-day transactional log (Sept 1–30, 2026). |
| **Total SLA Breached** | 89,674 | Orders with `sla_breached = 1` | **89.67% total breach rate.** |
| **Total SLA Compliant** | 10,326 | Orders with `sla_breached = 0` | **10.33% on-time rate.** |
| **Mean Promised Duration** | 29.65 minutes | `promised_time - order_time` | Median: 29.44 min, Std Dev: 4.60 min. |
| **Mean Actual Fulfillment Duration** | 35.90 minutes | `actual_delivery_time - order_time` | Median: 35.34 min, Std Dev: 7.67 min. |
| **Mean Fulfillment Deficit** | **+6.25 minutes** | `actual_duration - promised_duration` | Systemic operational delivery lag. |
| **Mean Delivery Delay** | 6.43 minutes | `delivery_delay_minutes` | Restricted to non-negative delays ($[0, \infty)$). |

---

## 2. Exact Definition of SLA Breach in the Dataset

### Finding: Mathematical Definition
- **OBSERVATION:**  
  The dataset calculates SLA breach strictly via a binary threshold comparing `actual_delivery_time` against `promised_time`.

- **EVIDENCE:**
  ```python
  sla_breached = 1 if (actual_delivery_time > promised_time) else 0
  delivery_delay_minutes = max(0.0, round((actual_delivery_time - promised_time).total_seconds() / 60.0, 1))
  ```
  - For all 100,000 orders, whenever `delivery_delay_minutes > 0.0`, `sla_breached` is strictly `1`.
  - Whenever `delivery_delay_minutes == 0.0` and status is `Delivered_On_Time`, `sla_breached` is strictly `0`.
  - Exactly 100% of orders with `actual_delivery_time <= promised_time` have `sla_breached = 0`.

- **POSSIBLE INTERPRETATIONS:**
  1. The SLA engine evaluates a rigid single-point deadline without any grace period (e.g. even a 6-second delay of 0.1 minutes is classified as a full breach).
  2. The synthetic data generation script evaluated the SLA rule uniformly on the raw timestamps for all orders, including Cancelled and Failed orders.

- **DECISION REQUIRED:**
  - Establish whether MacroOps AI operations should introduce a 2-to-3 minute grace period buffer (standard in quick-commerce) or retain the strict zero-tolerance threshold.

---

## 3. Statistical Distribution of Latencies

### 3.1. Percentile Distribution of Core Durations
All durations in the table below are expressed in **minutes**:

| Metric | Min | p1 | p5 | p25 | Median | Mean | p75 | p90 | p95 | p99 | Max | Std Dev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Promised Duration** | 20.00 | 20.00 | 22.37 | 26.36 | 29.44 | **29.65** | 32.69 | 35.73 | 37.56 | 41.17 | 54.27 | 4.60 |
| **Actual Duration** | 11.93 | 20.63 | 24.24 | 30.44 | 35.34 | **35.90** | 40.77 | 46.04 | 49.42 | 55.95 | 76.60 | 7.67 |
| **Calculated Delay** | -10.87 | -3.69 | -1.40 | 2.46 | 5.76 | **6.25** | 9.46 | 13.28 | 15.71 | 20.73 | 37.26 | 5.27 |
| **Reported Delay (`orders.csv`)** | 0.00 | 0.00 | 0.00 | 2.50 | 5.80 | **6.43** | 9.50 | 13.30 | 15.70 | 20.70 | 37.30 | 5.00 |

### Key Distributional Observations:
1. **Promised Duration Hard Floor:** The minimum promised delivery time is **exactly 20.00 minutes** (1st percentile is also 20.00). This indicates a synthetic generation rule or company policy stating: `promised_time = order_time + max(20.0, base_promise)`.
2. **Systemic Deficit:** The 25th percentile of actual delivery time (30.44 min) is greater than the median promised time (29.44 min). In other words, over 75% of actual deliveries took longer than the average promised SLA!

### 3.2. Delivery Delay Histogram Breakdown
| Delay Bin | Order Count | Percentage | Cumulative % | Operational Severity |
| :--- | :---: | :---: | :---: | :--- |
| **0.0 min (On-Time)** | 10,592 | 10.59% | 10.59% | Compliant |
| **0.1 - 2.0 min** | 11,627 | 11.63% | 22.22% | Minor Delay (Within typical grace period) |
| **2.1 - 5.0 min** | 22,352 | 22.35% | 44.57% | Moderate Delay |
| **5.1 - 10.0 min** | 33,478 | 33.48% | 78.05% | Severe Delay (Highest Concentration) |
| **10.1 - 15.0 min** | 15,890 | 15.89% | 93.94% | Critical Delay |
| **15.1 - 20.0 min** | 4,804 | 4.80% | 98.74% | Extreme Delay |
| **20.0+ min** | 1,257 | 1.26% | 100.00% | Severe Failure (Max 37.3 min) |

> [!IMPORTANT]
> **Grace Period Insight:** Notice that **11,627 orders (11.63%)** breached SLA by less than 2 minutes. If a 2-minute operational grace period were applied, the SLA breach rate would drop from **89.67% to 78.05%**. However, the vast bulk of breaches (67.8% of all orders) exceed 2 minutes.

---

## 4. Cohort & Driver Analysis: Is the Breach Localized or Systemic?

### 4.1. Store-by-Store Analysis (100 Stores)
- **OBSERVATION:**  
  The 89.67% breach rate is **strictly systemic** across all 100 fulfillment stores. There are no "hero" stores and no "rogue" stores.

- **EVIDENCE:**
  - Mean Store Breach Rate: **89.68%**
  - Standard Deviation across stores: **1.39%**
  - Lowest Store Breach Rate: **86.63%** (`ST050` — 875 breached out of 1,010 orders, avg delay: 5.78 min)
  - Highest Store Breach Rate: **92.89%** (`ST012` — 915 breached out of 985 orders, avg delay: 7.44 min)

#### Top 5 Highest & Lowest Breach Stores:
| Store ID | Category | Total Orders | Breached Orders | Breach Rate (%) | Mean Delay (min) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `ST012` | Highest Breach | 985 | 915 | **92.89%** | 7.44 |
| `ST080` | Highest Breach | 977 | 905 | **92.63%** | 7.17 |
| `ST024` | Highest Breach | 989 | 914 | **92.42%** | 7.16 |
| `ST042` | Highest Breach | 972 | 898 | **92.39%** | 7.01 |
| `ST045` | Highest Breach | 989 | 912 | **92.21%** | 7.09 |
| ... | *90 Stores* | ... | ... | ... | ... |
| `ST013` | Lowest Breach | 1,013 | 888 | **87.66%** | 6.19 |
| `ST029` | Lowest Breach | 1,001 | 874 | **87.31%** | 6.17 |
| `ST082` | Lowest Breach | 953 | 830 | **87.09%** | 6.22 |
| `ST071` | Lowest Breach | 1,029 | 895 | **86.98%** | 6.28 |
| `ST050` | Lowest Breach | 1,010 | 875 | **86.63%** | 5.78 |

---

### 4.2. Temporal Analysis: Day of Month & Hour of Day

#### Day-of-Month Stability (September 1–30, 2026):
- Mean daily breach rate: **89.68%** | Min: **88.06%** | Max: **91.02%** | Std Dev: **0.66%**.
- Volume is flat at ~3,333 orders per day. Breach rate does not spike on weekends or end-of-month.

#### Hour-of-Day Dynamics (00:00 to 23:00):
- Orders are distributed evenly across all 24 hours (~4,100 to 4,300 orders per hour).
- **Off-Peak Hours (00:00 - 16:00):** Breach rate remains steady between **88.35% and 89.93%**, with average delay flat at ~6.1 minutes.
- **Peak Evening Hours (17:00 - 21:00):** 
  - Breach rate elevates to **90.91% - 92.32%** (peaking at 21:00 with 92.32%).
  - Average delay jumps from **6.1 minutes to 7.51 minutes** (+23% increase in delay).
  - Demonstrates realistic simulated evening rush congestion.

---

### 4.3. Basket Size & Monetary Value Impact

#### Breach Rate by Item Count (1 to 17 items):
There is a **direct, monotonic relationship** between the number of items in the order and the probability of an SLA breach:

| Item Count | Total Orders | Breached Orders | Breach Rate (%) | Mean Delay (min) | Operational Bottleneck |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | 1,791 | 1,429 | **79.79%** | 4.37 | Fast single-item pick |
| **2** | 7,204 | 6,061 | **84.13%** | 4.96 | Small basket |
| **3** | 14,757 | 12,622 | **85.53%** | 5.35 | Small basket |
| **4** | 19,635 | 17,260 | **87.90%** | 5.80 | Medium basket |
| **5** | 19,586 | 17,662 | **90.18%** | 6.33 | Median basket |
| **6** | 15,803 | 14,540 | **92.01%** | 6.98 | Large basket |
| **7** | 10,316 | 9,642 | **93.47%** | 7.59 | Large basket |
| **8** | 5,800 | 5,508 | **94.97%** | 8.13 | High pick complexity |
| **9** | 3,017 | 2,894 | **95.92%** | 8.60 | High pick complexity |
| **10** | 1,301 | 1,276 | **98.08%** | 9.53 | Bulky basket |
| **11** | 514 | 506 | **98.44%** | 10.53 | Bulky basket |
| **12** | 199 | 197 | **98.99%** | 10.77 | Extreme basket size |
| **13 - 17** | 77 | 77 | **100.00%** | 12.80 | 100% Guaranteed Breach |

#### Breach Rate by Order Value Bins:
- `< $250`: 11,320 orders | **85.36% breach rate** | Avg Delay: 5.29 min
- `$250 - $500`: 34,674 orders | **87.74% breach rate** | Avg Delay: 5.85 min
- `$500 - $750`: 29,687 orders | **90.54% breach rate** | Avg Delay: 6.57 min
- `$750 - $1,000`: 15,491 orders | **92.56% breach rate** | Avg Delay: 7.25 min
- `$1,000+`: 8,828 orders | **94.81% breach rate** | Avg Delay: 8.24 min

---

## 5. Structured Investigation Findings

### Finding 1: Systemic Root Cause of the 89.67% Breach Rate
- **OBSERVATION:**  
  The 89.67% SLA breach rate is not an anomaly of a few failing stores or peak hours, but a structural characteristic of the fulfillment promise model.
- **EVIDENCE:**  
  The promised delivery window has a median of 29.44 minutes, while actual fulfillment has a median of 35.34 minutes. Across all 100 stores, breach rates fall within a narrow band of 86.6% to 92.9% ($\sigma = 1.39\%$).
- **POSSIBLE INTERPRETATIONS:**  
  1. *Unrealistic Customer Promise Engine:* The dispatch algorithm promises ~29-minute delivery, but store operations (picking ~13 mins + rider assignment ~8 mins + transit ~22 mins = ~43 mins total) structurally require ~36 minutes.
  2. *Synthetic Generator Calibration:* The dataset generator was configured with fixed distributions where actual delivery duration was parameterized with a higher mean than promised time.
- **DECISION REQUIRED:**  
  - For AI Operations Copilot and Dashboard: Highlight the **structural promise vs capacity gap** as a primary operational insight.
  - For Predictive SLA Models: Frame the target as predicting *minutes of delay* rather than binary classification, or re-calibrate the target threshold.

---

### Finding 2: Monotonic Picking Bottleneck on Large Baskets
- **OBSERVATION:**  
  Baskets with >6 items have breach rates exceeding 92%, reaching 100% for 13+ items.
- **EVIDENCE:**  
  Average delay scales linearly from 4.37 minutes for 1-item orders to 14.25 minutes for 17-item orders.
- **POSSIBLE INTERPRETATIONS:**  
  1. The promised time formula does not scale proportionately with basket item count (promising similar delivery windows for 1 item and 10 items).
  2. Warehouse picking duration increases with item count, consuming the delivery buffer before the rider even departs.
- **DECISION REQUIRED:**  
  - Build predictive features combining `item_count` with store picking velocity to forecast SLA risk at checkout.
