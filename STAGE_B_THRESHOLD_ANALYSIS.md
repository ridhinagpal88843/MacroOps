# MacroOps AI — Stage B Threshold & Operational Policy Analysis

**Document Version:** 1.0.0  
**Phase:** Stage B Step 2 — Operating Threshold Selection & Capacity Trade-offs  
**Execution Timestamp:** October 14, 2026  
**Pipeline Reference:** [`train_stage_b_models.py`](file:///c:/Users/HP/Desktop/MacroOps/train_stage_b_models.py)  
**Machine-Readable Metrics:** [`model_artifacts/stage_b_evaluation_metrics.json`](file:///c:/Users/HP/Desktop/MacroOps/model_artifacts/stage_b_evaluation_metrics.json)  
**Configuration File:** [`stage_b_final_config.json`](file:///c:/Users/HP/Desktop/MacroOps/stage_b_final_config.json)  

---

> [!CAUTION]
> **PROTOTYPE / SYNTHETIC DATA GOVERNANCE DISCLAIMER**  
> All thresholds, alert rates, and operational trade-offs evaluated in this report are based on models trained on synthetic quick-commerce operational datasets. **No threshold in this report is declared globally "optimal" or production-ready.** Operating cutoffs represent business trade-offs between dispatcher alert burden and SLA breach exposure under capacity-constrained staffing.

---

## 1. Executive Summary & Core Policy Findings

In Stage A ([`STAGE_A_THRESHOLD_ANALYSIS.md`](file:///c:/Users/HP/Desktop/MacroOps/STAGE_A_THRESHOLD_ANALYSIS.md)), an operating threshold of **$\tau = 0.9300$** was frozen based on validation data to constrain alert volume to the top ~28–43% highest-risk orders while achieving $>92\%$ precision.

In Stage B, because orders have already consumed physical warehouse picking time, the posterior risk probabilities shift substantially upward toward 1.0. Consequently:
1. **Direct Policy Comparison ($\tau = 0.9300$):** Using the frozen Stage A cutoff flags **~65% of orders** at Checkpoints B1 and B2, capturing **+814 additional breaches (+50.1% more breach volume)** than Stage A at **90.98% precision**.
2. **Capacity-Matched Policy ($\tau = 0.9800$):** If dispatch operations cannot review >40% of volume, raising the threshold to **$\tau = 0.9800$** constrains alert volume to **38.07%** at B2 while capturing 1,394 breaches with **89.42% precision**.

---

## 2. Probability Distribution Shift Between Stages

The predicted probability distributions illustrate the physical progression of fulfillment:

| Metric / Quantile | Stage A ($T_0$ Checkout) | Stage B1 ($T_1$ Pick End) | Stage B2 ($T_2$ Dispatch Proxy) | Operational Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Minimum** | 0.5893 | 0.4404 | 0.4125 | All stages identify a small cohort of fast, low-risk deliveries. |
| **25th Percentile ($P_{25}$)** | 0.8638 | 0.9422 | 0.9482 | By B1, 75% of orders have predicted breach probability $>94\%$. |
| **Median ($P_{50}$)** | **0.8994** | **0.9824** | **0.9753** | **Median risk shifts upward by +8.3%** as pick time accumulates. |
| **75th Percentile ($P_{75}$)** | 0.9369 | 0.9859 | 0.9842 | Upper quartile risk boundary. |
| **90th Percentile ($P_{90}$)** | 0.9673 | 0.9877 | 0.9880 | Top decile near certainty ($>98.7\%$). |
| **Maximum** | 0.9991 | 0.9942 | 0.9966 (1.0000 Hybrid) | Orders past promised deadline reach $P = 1.0$. |

---

## 3. Threshold Scan & Capacity Trade-offs

### 3.1. Checkpoint B1 (Post-Picking) Threshold Grid

#### Validation Set ($N = 3,243$, 2,895 Breaches)
| Threshold ($\tau$) | Alert Rate % | Breach Precision % | Breach Recall % | F1-Score | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.88** | 87.63% | 89.66% | 88.01% | 0.8883 | 2,548 | 294 | 54 | 347 |
| **0.90** | 84.09% | 89.73% | 84.53% | 0.8705 | 2,447 | 280 | 68 | 448 |
| **0.92** | 80.23% | 89.70% | 80.62% | 0.8492 | 2,334 | 268 | 80 | 561 |
| **0.93 (Frozen Ref)** | **78.42%** | **89.78%** | **78.86%** | **0.8396** | **2,283** | **260** | **88** | **612** |
| **0.94** | 75.64% | 89.89% | 76.17% | 0.8246 | 2,205 | 248 | 100 | 690 |
| **0.95** | 72.65% | 89.98% | 73.23% | 0.8075 | 2,120 | 236 | 112 | 775 |
| **0.96** | 67.96% | 89.88% | 68.43% | 0.7770 | 1,981 | 223 | 125 | 914 |
| **0.97** | 63.58% | 89.72% | 63.90% | 0.7464 | 1,850 | 212 | 136 | 1,045 |
| **0.98** | **54.95%** | **89.28%** | **54.96%** | **0.6804** | **1,591** | **191** | **157** | **1,304** |

#### Holdout Test Set ($N = 4,095$, 3,682 Breaches)
| Threshold ($\tau$) | Alert Rate % | Breach Precision % | Breach Recall % | F1-Score | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.88** | 88.21% | 90.34% | 88.62% | 0.8947 | 3,263 | 349 | 64 | 419 |
| **0.90** | 83.83% | 90.53% | 84.41% | 0.8736 | 3,108 | 325 | 88 | 574 |
| **0.92** | 79.66% | 90.68% | 80.34% | 0.8520 | 2,958 | 304 | 109 | 724 |
| **0.93 (Frozen Ref)** | **77.46%** | **90.67%** | **78.11%** | **0.8392** | **2,876** | **296** | **117** | **806** |
| **0.94** | 75.56% | 90.56% | 76.10% | 0.8270 | 2,802 | 292 | 121 | 880 |
| **0.95** | 72.70% | 90.56% | 73.22% | 0.8097 | 2,696 | 281 | 132 | 986 |
| **0.96** | 67.91% | 90.47% | 68.33% | 0.7786 | 2,516 | 265 | 148 | 1,166 |
| **0.97** | 63.91% | 90.26% | 64.15 | 0.7500 | 2,362 | 255 | 158 | 1,320 |
| **0.98** | **55.75%** | **89.97%** | **55.78%** | **0.6887** | **2,054** | **229** | **184** | **1,628** |

---

### 3.2. Checkpoint B2 (Post-Dispatch Proxy) Threshold Grid

#### Validation Set ($N = 3,243$, 2,895 Breaches)
| Threshold ($\tau$) | Alert Rate % | Breach Precision % | Breach Recall % | F1-Score | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.88** | 93.15% | 89.61% | 93.51% | 0.9151 | 2,707 | 314 | 34 | 188 |
| **0.90** | 90.87% | 89.62% | 91.23% | 0.9041 | 2,641 | 306 | 42 | 254 |
| **0.92** | 86.96% | 89.65% | 87.32% | 0.8847 | 2,528 | 292 | 56 | 367 |
| **0.93 (Frozen Ref)** | **84.09%** | **89.62%** | **84.42%** | **0.8694** | **2,444** | **283** | **65** | **451** |
| **0.94** | 79.49% | 89.72% | 79.90% | 0.8452 | 2,313 | 265 | 83 | 582 |
| **0.95** | 73.97% | 89.54% | 74.20% | 0.8115 | 2,148 | 251 | 97 | 747 |
| **0.96** | 65.53% | 89.84% | 65.94% | 0.7606 | 1,909 | 216 | 132 | 986 |
| **0.97** | 56.31% | 89.92% | 56.72% | 0.6956 | 1,642 | 184 | 164 | 1,253 |
| **0.98 (Capacity-Matched)** | **40.18%** | **89.87%** | **40.45%** | **0.5579** | **1,171** | **132** | **216** | **1,724** |

#### Holdout Test Set ($N = 4,095$, 3,682 Breaches)
| Threshold ($\tau$) | Alert Rate % | Breach Precision % | Breach Recall % | F1-Score | True Positives (TP) | False Positives (FP) | True Negatives (TN) | False Negatives (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.88** | 93.80% | 89.95% | 93.83% | 0.9185 | 3,455 | 386 | 27 | 227 |
| **0.90** | 91.62% | 89.93% | 91.63% | 0.9077 | 3,374 | 378 | 35 | 308 |
| **0.92** | 87.37% | 89.85% | 87.32% | 0.8857 | 3,215 | 363 | 50 | 467 |
| **0.93 (Frozen Ref)** | **84.08%** | **90.01%** | **84.17%** | **0.8699** | **3,099** | **344** | **69** | **583** |
| **0.94** | 78.56% | 90.18% | 78.79% | 0.8410 | 2,901 | 316 | 97 | 781 |
| **0.95** | 72.23% | 90.33% | 72.57% | 0.8048 | 2,672 | 286 | 127 | 1,010 |
| **0.96** | 64.13% | 90.33% | 64.42% | 0.7521 | 2,372 | 254 | 159 | 1,310 |
| **0.97** | 54.77% | 90.55% | 55.16% | 0.6856 | 2,031 | 212 | 201 | 1,651 |
| **0.98 (Capacity-Matched)** | **38.07%** | **89.42%** | **37.86%** | **0.5320** | **1,394** | **165** | **248** | **2,288** |

---

## 4. Operational Policy Trade-offs & Recommendations

Operations leadership must choose between two distinct operational strategies:

```
POLICY OPTION A: FIXED THRESHOLD BENCHMARK (tau = 0.9300)
- Operating Stance: Dynamic In-Fulfillment Safety Net
- Checkpoint B2 Workload: 65.49% of volume alerted
- Breach Capture: 2,440 breaches captured (66.27% recall)
- Operational Meaning: Captures +814 more breaches than Stage A (+50.1% lift) with high precision (90.98%).
  Requires automated dispatch actions (e.g., dynamic promise adjustments or courier re-routing) rather than pure human intervention.

POLICY OPTION B: CAPACITY-MATCHED WORKLOAD (tau = 0.9800)
- Operating Stance: Constrained Supervisor Manual Review (< 40% budget)
- Checkpoint B2 Workload: 38.07% of volume alerted (1,559 orders)
- Breach Capture: 1,394 breaches captured (37.86% recall)
- Operational Meaning: Matches Stage A's human capacity constraint while identifying only the absolute highest-certainty breaches.
```

### Recommendation
For production architecture:
1. **Automated Interventions:** Apply Policy Option A ($\tau = 0.9300$) to trigger automated customer promise adjustments and dispatch re-routes.
2. **Supervisor Escalations:** Apply Policy Option B ($\tau = 0.9800$) to trigger manual dark store supervisor paging, preventing alert fatigue.
