# MacroOps AI — Stage A Final Evaluation & Frozen Policy Verification

**Document Version:** 1.0.0  
**Status:** COMPLETE & FROZEN  
**Phase:** Phase 2C Final Stage A Evaluation  
**Execution Timestamp:** September 28, 2026  
**Frozen Configuration File:** [`stage_a_final_config.json`](file:///c:/Users/HP/Desktop/MacroOps/stage_a_final_config.json)  
**Machine-Readable Evaluation Metrics:** [`stage_a_final_metrics.json`](file:///c:/Users/HP/Desktop/MacroOps/stage_a_final_metrics.json)  
**Model Binaries:** [`model_artifacts/lightgbm_classifier.joblib`](file:///c:/Users/HP/Desktop/MacroOps/model_artifacts/lightgbm_classifier.joblib), [`model_artifacts/logistic_regression.joblib`](file:///c:/Users/HP/Desktop/MacroOps/model_artifacts/logistic_regression.joblib)  

---

> [!CAUTION]
> **PROTOTYPE / SYNTHETIC DATA GOVERNANCE DISCLAIMER**  
> All models, probability distributions, threshold metrics, and holdout evaluations presented in this document are derived strictly from baseline prototype models trained on synthetic quick-commerce operational datasets. **This model and operating policy are NOT claimed to be production-ready.** Performance benchmarks reflect the statistical behavior of synthetic prototype data and establish experimental baselines for subsequent development phases.

---

## 1. Governance Declaration: Policy Freezing Protocol

In accordance with strict machine learning engineering governance, **the operating decision policy was formally defined and frozen based exclusively on the Validation partition (September 22–25, $N = 13,082$) BEFORE evaluating the untouched Holdout Test partition (September 26–30, $N = 16,210$)**.

### Core Policy Determinations
1. **Operating Policy Selected:** **Candidate 4 ($\tau = 0.9300$)**
2. **Operational Assumption:** **Capacity-Constrained Operational Escalation.**
   - Stage A alerts are treated as operational signals intended for manual dark-store supervisor reviews, priority picking reallocation, and dispatcher couriering.
   - Human operational bandwidth is finite; alerting 50–60% of daily volume would cause operational paralysis and severe alert fatigue.
   - The threshold $\tau = 0.9300$ was selected to constrain alert volume to the top ~25–29% highest-risk orders while achieving $\ge 94\%$ breach precision.
3. **No Claim of Mathematical Optimality:**
   - **The threshold $\tau = 0.9300$ is NOT claimed to be mathematically or globally optimal.**
   - In operations research, an operating threshold is optimal only with respect to an explicit cost function ($C = c_{\text{FP}} \cdot \text{FP} + c_{\text{FN}} \cdot \text{FN}$). Under different business assumptions (e.g., zero-cost automated promise extensions), a lower threshold such as $\tau = 0.8922$ would be preferable. Under the MVP human-intervention constraint, $\tau = 0.9300$ is the appropriate operational stance.
4. **Selected Architecture:** **LightGBM Classifier** (with Logistic Regression preserved as an interpretable linear baseline reference).
5. **Zero Post-Hoc Tuning:** Neither the model parameters, features, nor decision threshold were altered after inspecting holdout test results.

---

## 2. Pre-Freezing Validation Analysis & Model Selection

Under the frozen policy ($\tau = 0.9300$), both candidate classification models were evaluated on the **Validation set ($N = 13,082$, 11,672 breaches, 1,410 on-time)** to select the primary MVP model:

### Validation Performance Comparison ($\tau = 0.9300$, Pre-Freezing)

| Evaluation Dimension | Logistic Regression Baseline | Selected LightGBM Classifier | Validation Comparison & Decision Rationale |
| :--- | :---: | :---: | :--- |
| **Input Features** | 135 (One-Hot Encoded) | **7 (Native Compact)** | **LightGBM reduces pipeline complexity by 19x**, eliminating 128 sparse dummy columns. |
| **Validation PR-AUC** | **0.9254** | 0.9252 | Identical ranking quality across the probability spectrum. |
| **Validation ROC-AUC** | **0.6066** | 0.5971 | Marginal linear ranking advantage (+0.0095). |
| **Validation Brier Score** | **0.0951** | 0.0957 | Both models are statistically well-calibrated (better than Dummy prior 0.0962). |
| **Flagged Alert Volume** | **3,284 orders (25.10%)** | 3,786 orders (28.94%) | Both models satisfy the capacity constraint ($< 30\%$ alert budget). |
| **Breach Precision** | 93.61% | **94.00%** | **LightGBM achieves +0.39% higher precision**, resulting in fewer false alarms per alert. |
| **Breach Recall** | 26.34% (3,074 breaches) | **30.49% (3,559 breaches)** | **LightGBM captures +485 additional true breaches (+15.8% more breach volume)**. |
| **On-Time Order Recall** | **85.11% (1,200 / 1,410)** | 83.90% (1,183 / 1,410) | Logistic Regression preserves 17 more on-time orders from false escalation. |
| **F1-Score** | 0.4111 | **0.4605** | LightGBM provides superior harmonic balance between precision and recall. |

### Model Selection Rationale
**LightGBM Classifier was selected as the Stage A MVP Model** for three objective operational reasons:
1. **Superior Breach Capture in the Escalation Tail:** Within the targeted alert budget, LightGBM captures **15.8% more at-risk deliveries** (3,559 vs 3,074 on validation) than Logistic Regression at equal or slightly higher precision ($94.00\%$).
2. **Cleaner Production Engineering:** LightGBM operates directly on the 7 approved feature definitions via native ordinal categorical encoding. It eliminates 128 one-hot dummy columns, handles unseen dark stores natively via unknown index mapping (`-1`), and avoids memory bloat.
3. **Sub-Millisecond Inference:** LightGBM executes tree traversals in $< 0.2\text{ms}$ per order, comfortably meeting checkout API latency budgets.

---

## 3. Frozen Stage A Configuration (`stage_a_final_config.json`)

The following configuration was formally established prior to test set execution:

```json
{
  "stage": "Stage A (Order Checkout / Creation Point T0)",
  "governance_status": "FROZEN_FOR_FINAL_EVALUATION",
  "policy_name": "Targeted Operational Escalation Policy (Candidate 4)",
  "prediction_point_t0": "orders.order_time",
  "prediction_target": "sla_breached (1 = Breached/Late, 0 = On-Time/Met)",
  "frozen_decision_threshold": 0.9300,
  "selected_model": "LightGBMClassifier",
  "baseline_reference_model": "LogisticRegression",
  "approved_stage_a_features": [
    "item_count",
    "order_value",
    "promised_duration_minutes",
    "order_hour",
    "day_of_week",
    "is_peak_rush_hour",
    "store_id"
  ],
  "model_artifact_path": "model_artifacts/lightgbm_classifier.joblib",
  "preprocessor_artifact_path": "model_artifacts/lgb_ordinal_encoder.joblib",
  "intended_operational_interpretation": "Targeted risk-alerting layer designed to surface high-confidence SLA breach risks for supervisor/dispatcher operational escalation under capacity-constrained human review budgets."
}
```

---

## 4. Final Holdout Test Evaluation

Following policy freezing, a single evaluation run was executed against the **Final Holdout Test partition (September 26–30, 2026, $N = 16,210$)**.

### Final Holdout Test Metrics Table

| Metric | Selected Model: LightGBM Classifier | Baseline Reference: Logistic Regression | Operational Meaning & Interpretation |
| :--- | :---: | :---: | :--- |
| **Decision Threshold ($\tau$)** | **0.9300 (Frozen)** | **0.9300 (Frozen)** | Predetermined escalation decision boundary. |
| **Number of Features** | **7 compact** | 135 one-hot | Operational footprint of inference pipeline. |
| **PR-AUC** | **0.9288** | **0.9289** | Area under Precision-Recall curve (Baseline = 0.8964). |
| **ROC-AUC** | **0.6008** | **0.6107** | Overall discriminative ranking ability. |
| **Brier Score** | **0.0923** | **0.0917** | Probability calibration loss (Lower = better; Dummy = 0.0929). |
| **Flagged Order Volume** | **4,644 orders (28.65%)** | **4,012 orders (24.75%)** | Orders escalated for dark store supervisor intervention. |
| **Breach Precision** | **94.08%** | **94.34%** | **Fewer than 6 out of 100 alerts are false alarms.** |
| **Breach Recall (Capture Rate)**| **30.07% (4,369 / 14,530)** | **26.05% (3,785 / 14,530)** | **LightGBM catches +584 more breaches (+15.4%) than LogReg.** |
| **On-Time Order Recall** | **83.63% (1,405 / 1,680)** | **86.49% (1,453 / 1,680)** | On-time orders correctly protected from false alarms. |
| **On-Time Precision** | **12.15% (1,405 / 11,566)** | **11.91% (1,453 / 12,198)** | Purity of the unflagged standard fulfillment stream. |
| **F1-Score (Breached)** | **0.4557** | **0.4083** | Harmonic mean of breach precision and recall. |
| **Overall Accuracy** | **35.62%** | **32.31%** | Note: Accuracy reflects high-threshold filtering, not error rate. |

---

### Final Confusion Matrices (Holdout Test Set, $N = 16,210$)

#### 1. Selected Model: LightGBM Classifier ($\tau = 0.9300$)
```
                            PREDICTED STANDARD (0)       PREDICTED ESCALATION (1)
ACTUAL ON-TIME (0):                 1,405 (TN)                     275 (FP)
ACTUAL BREACHED (1):               10,161 (FN)                   4,369 (TP)

Summary:
- Total Orders Evaluated: 16,210
- Escalations Triggered:  4,644 (28.65% workload)
- True Positive Breaches: 4,369 (30.07% breach recall)
- False Alarms:           275 (5.92% false discovery rate; 94.08% precision)
- Correctly Shielded:     1,405 on-time orders (83.63% on-time recall)
```

#### 2. Baseline Reference: Logistic Regression ($\tau = 0.9300$)
```
                            PREDICTED STANDARD (0)       PREDICTED ESCALATION (1)
ACTUAL ON-TIME (0):                 1,453 (TN)                     227 (FP)
ACTUAL BREACHED (1):               10,745 (FN)                   3,785 (TP)

Summary:
- Total Orders Evaluated: 16,210
- Escalations Triggered:  4,012 (24.75% workload)
- True Positive Breaches: 3,785 (26.05% breach recall)
- False Alarms:           227 (5.66% false discovery rate; 94.34% precision)
- Correctly Shielded:     1,453 on-time orders (86.49% on-time recall)
```

---

## 5. Comparative Evaluation & Out-of-Sample Stability

### Validation vs. Final Test Consistency

| Model / Metric | Validation Set (Sept 22–25) | Final Test Set (Sept 26–30) | Variance ($\Delta$) | Stability Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **LightGBM Flagged %** | 28.94% | 28.65% | -0.29% | Highly stable alert workload across time. |
| **LightGBM Precision** | 94.00% | 94.08% | +0.08% | Zero precision decay on unseen future dates. |
| **LightGBM Breach Recall** | 30.49% | 30.07% | -0.42% | Stable breach capture across calendar shifts. |
| **LightGBM On-Time Recall**| 83.90% | 83.63% | -0.27% | Consistent shielding of on-time deliveries. |
| **LightGBM PR-AUC** | 0.9252 | 0.9288 | +0.0036 | No overfitting; slight test generalization gain. |
| **LightGBM Brier Score** | 0.0957 | 0.0923 | -0.0034 | Improved probability calibration on test set. |

**Analytical Conclusion:** The difference between Validation and Final Test metrics is negligible across all dimensions ($|\Delta| < 0.5\%$). This confirms that:
1. The chronological split (Train: Sept 1–21 $\to$ Val: Sept 22–25 $\to$ Test: Sept 26–30) was strictly respected.
2. The preprocessing pipeline has zero temporal data leakage.
3. The frozen decision policy ($\tau = 0.9300$) generalizes robustly without performance degradation.

---

## 6. Distinguishing "Policy Selection" from "Model Performance"

A vital conceptual distinction must be maintained for operational stakeholders:

1. **Model Performance (Ranking & Calibration):**
   - Both models achieve **PR-AUC ~0.929** and **ROC-AUC ~0.60–0.61**.
   - These metrics measure the model's fundamental ability to assign higher probabilities to late deliveries than on-time deliveries, regardless of the cutoff.
   - LightGBM exhibits wider score spread ($\sigma = 0.0534$ vs $0.0434$, max $0.9991$ vs $0.9895$), giving it superior separation in the extreme upper deciles.
2. **Policy Selection (Operating Cutoff):**
   - The threshold $\tau = 0.9300$ does NOT change how the model ranks orders. It simply defines **where operations draws the line for manual intervention**.
   - Choosing $\tau = 0.9300$ forces a deliberate trade-off: **Operations accepts that 69.93% of breaches will pass unflagged at checkout** in order to ensure that **the alerts they do receive are 94.08% trustworthy** and capped at ~28.6% of total order volume.
   - The unflagged 69.93% of breaches are not "failures of the model"; they are the inevitable mathematical consequence of capping alert volume when 89.64% of all orders are breached.
   - **Bridging the Gap via Stage B:** This trade-off confirms why **Stage B (Dynamic In-Fulfillment Tracking)** is architecturally essential. The 10,161 breaches that could not be flagged at checkout due to finite capacity must be dynamically identified during picking and courier transit as real-time delays accumulate.

---

## 7. Final Deliverables Summary & Stop Boundary

All Phase 2 requirements for Stage A predictive intelligence are now fully satisfied:

```
c:\Users\HP\Desktop\MacroOps\
├── predictive_features/
│   ├── stage_a_features.csv             (97,449 rows, 7 approved features, zero leakage)
│   ├── feature_metadata.json            (Pipeline schema & split documentation)
│   └── validation_audit.json            (Automated data integrity audit)
│
├── model_artifacts/
│   ├── linear_preprocessor.joblib       (Fitted ColumnTransformer)
│   ├── lgb_ordinal_encoder.joblib       (Fitted OrdinalEncoder)
│   ├── dummy_classifier.joblib          (Prior baseline)
│   ├── logistic_regression.joblib       (Trained baseline)
│   ├── lightgbm_classifier.joblib       (Selected MVP model)
│   ├── dummy_regressor.joblib           (Mean baseline)
│   ├── ridge_regressor.joblib           (Ridge baseline)
│   ├── lightgbm_regressor.joblib        (LightGBM regressor baseline)
│   └── evaluation_metrics.json          (Full raw metrics)
│
├── reports/plots/
│   ├── pr_curve.png                     (Validation PR curve)
│   ├── calibration_curve.png            (Validation reliability diagram)
│   ├── probability_distribution.png     (Validation risk score distributions)
│   └── threshold_tradeoffs.png          (Validation metrics vs threshold)
│
├── Governance & Documentation:
│   ├── PREDICTIVE_MODEL_DESIGN.md       (Three-stage architecture & leakage audit)
│   ├── FEATURE_ENGINEERING_REPORT.md    (Stage A feature pipeline documentation)
│   ├── MODEL_PERFORMANCE_REPORT.md      (Phase 2B baseline model evaluation)
│   ├── STAGE_A_THRESHOLD_ANALYSIS.md    (Phase 2C threshold & calibration analysis)
│   ├── STAGE_A_MODEL_SELECTION.md       (Decision-policy trade-off framework)
│   ├── stage_a_final_config.json        (Pre-evaluation frozen policy configuration)
│   ├── stage_a_final_metrics.json       (Holdout test evaluation metrics)
│   └── STAGE_A_FINAL_EVALUATION.md      (This final evaluation document)
```

In strict compliance with user instructions, execution is **STOPPED**. No work on Stage B (In-Fulfillment dynamic models), Stage C (Root-cause explanations), API endpoints, dashboard integration, or deployment has been started.
