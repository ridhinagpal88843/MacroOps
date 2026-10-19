# MacroOps AI — Stage A Feature Engineering & Validation Audit Report (Revised)

**Platform:** MacroOps AI — Fulfillment & Operations Intelligence Platform  
**Document Version:** 2.0 (Target-Free Raw Feature Matrix)  
**Phase:** Phase 2A — Stage A Feature Engineering  
**Pipeline Script:** [`build_predictive_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_predictive_features.py)  
**Output Dataset:** [`predictive_features/stage_a_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_a_features.csv)  
**Metadata:** [`predictive_features/feature_metadata.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/feature_metadata.json)  
**Audit Source:** [`predictive_features/validation_audit.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/validation_audit.json)  
**Date:** September 28, 2026  

---

> [!IMPORTANT]
> **SYNTHETIC DATA PROTOTYPE DISCLAIMER:**  
> **All model performance is prototype performance on synthetic data and must not be interpreted as real-world operational performance.**

---

## 1. Executive Summary & Architecture Revision

Following review, Phase 2A (Stage A Feature Engineering) has been updated to produce a **100% target-free raw feature matrix**. 

### Revisions Enacted:
1. **Target Encoding Removal:** `store_target_encoded` was **completely removed** from the saved feature matrix [`stage_a_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_a_features.csv). The original raw categorical `store_id` is preserved directly.
2. **Model Preprocessing Strategy Standardized:** For the baseline Logistic Regression model, a scikit-learn `ColumnTransformer` pipeline is specified:
   - `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` applied to `store_id`, `order_hour`, and `day_of_week`.
   - `StandardScaler()` applied to continuous numerical features (`item_count`, `order_value`, `promised_duration_minutes`).
   - `passthrough` applied to binary flag `is_peak_rush_hour`.
   - **Zero Target Encoding.**
3. **Partition-Only Fitting Rule:** All preprocessing transformers (`OneHotEncoder`, `StandardScaler`) must be fitted **strictly on the training partition (`split == 'train'`)**, and applied unchanged to validation and test partitions without re-fitting.
4. **Code-Level Leakage Audit:** Inspection of [`build_predictive_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_predictive_features.py) confirms that **zero features are derived from target labels**.
5. **Model Training Frozen:** No ML models have been trained.

---

## 2. Final Approved Feature Schema (7 Conceptual Features)

The saved feature dataset [`predictive_features/stage_a_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_a_features.csv) contains exclusively the 7 approved Stage A features alongside tracking identifiers and targets:

| Column Name | Inferred Type | Feature Classification | Category | Description | Model Transformation |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `order_id` | String | Identifier | — | Unique order identifier (`ORD-000001` to `ORD-100000`). | Dropped from $X$ |
| `prediction_timestamp_t0` | Timestamp | Temporal Anchor | — | Order checkout timestamp ($T_0 = \text{order\_time}$). | Dropped from $X$ |
| `order_date` | String | Date Partition | — | Calendar date formatted as `YYYY-MM-DD`. | Dropped from $X$ |
| `split` | String | Dataset Partition | — | Chronological partition: `'train'`, `'val'`, or `'test'`. | Partition Selector |
| **`item_count`** | Integer | Feature 1 (Numerical) | **A** | Number of items in basket (1 to 17). | `StandardScaler()` |
| **`order_value`** | Float | Feature 2 (Numerical) | **A** | Gross order monetary value ($80.00 to $2,744.18). | `StandardScaler()` |
| **`promised_duration_minutes`**| Float | Feature 3 (Numerical) | **A** | Customer delivery window: `(promised_time - order_time) / 60` (20.0 to 54.3 mins). | `StandardScaler()` |
| **`order_hour`** | Integer | Feature 4 (Categorical) | **A** | Hour of checkout (0 to 23). | `OneHotEncoder()` |
| **`day_of_week`** | String | Feature 5 (Categorical) | **A** | Day of the week (Monday through Sunday). | `OneHotEncoder()` |
| **`is_peak_rush_hour`** | Binary Flag | Feature 6 (Flag) | **A** | 1 if `order_hour` $\in [17, 18, 19, 20, 21]$, else 0. | `passthrough` |
| **`store_id`** | String | Feature 7 (Categorical) | **A** | Dark store identifier (`ST001` to `ST100`). | `OneHotEncoder(handle_unknown='ignore')` |
| **`sla_breached`** | Binary Integer | Target 1 (Classification) | **Target** | 1 if `actual_delivery_time > promised_time`, else 0. | Supervised Label $y_{\text{clf}}$ |
| **`delivery_delay_minutes`** | Float | Target 2 (Regression) | **Target** | Realized delivery delay in minutes: $\max(0.0, (\text{actual} - \text{promised})/60)$. | Supervised Label $y_{\text{reg}}$ |

---

## 3. Preprocessing Pipeline Specification (Zero Target Encoding)

For the baseline Logistic Regression classifier and Ridge/Linear delay regressor, feature transformation is governed by the following scikit-learn pipeline specification:

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Define feature groups strictly from Stage A approved inputs
CATEGORICAL_FEATURES = ['store_id', 'order_hour', 'day_of_week']
NUMERICAL_FEATURES   = ['item_count', 'order_value', 'promised_duration_minutes']
BINARY_FEATURES      = ['is_peak_rush_hour']

# Model Preprocessing Engine (Fitted strictly on Train partition)
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
        ('num', StandardScaler(), NUMERICAL_FEATURES),
        ('bin', 'passthrough', BINARY_FEATURES)
    ],
    remainder='drop'
)

# STRICT FITTING RULE:
# X_train_trans = preprocessor.fit_transform(X_train)
# X_val_trans   = preprocessor.transform(X_val)
# X_test_trans  = preprocessor.transform(X_test)
```

### Preprocessing Safeguards:
1. **Zero Target Information:** Neither `store_id`, `order_hour`, nor `day_of_week` uses target labels for encoding.
2. **Train-Only Scaling:** Means and standard deviations for `StandardScaler` are fitted exclusively on `train` (Sept 1–21).
3. **Out-of-Vocabulary Resilience:** `OneHotEncoder(handle_unknown='ignore')` guarantees that any previously unseen category in future sets maps safely to all zeros.

---

## 4. Re-Validated Data Audit Results

Following the re-execution of [`build_predictive_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_predictive_features.py), the audit results from [`predictive_features/validation_audit.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/validation_audit.json) are summarized below:

### 4.1. Row Counts & Split Boundaries
- **Total Population:** **97,449 rows** (`status IN ('Delivered_On_Time', 'Delivered_Late')`).
- **Excluded Non-Delivered:** 1,795 Cancelled (1.79%) and 756 Failed (0.76%).
- **Duplicate Order IDs:** **0** (100% unique primary keys).
- **Missing Values:** **0** across all 13 columns.

| Split Partition | Calendar Date Range | Calendar Days | Order Count | Population Share (%) |
| :--- | :--- | :---: | :---: | :---: |
| **`train`** | **2026-09-01** 00:00:00 to **2026-09-21** 23:59:00 | 21 Days | **68,157** | **69.94%** |
| **`val`** | **2026-09-22** 00:00:00 to **2026-09-25** 23:59:00 | 4 Days | **13,082** | **13.42%** |
| **`test`** | **2026-09-26** 00:00:00 to **2026-09-30** 23:59:00 | 5 Days | **16,210** | **16.63%** |
| **Total Completed** | **2026-09-01** to **2026-09-30** | **30 Days** | **97,449** | **100.00%** |

---

### 4.2. Target Distributions Across Splits

#### Binary Classification Target (`sla_breached`):
| Split | Total Orders | Breached (1) | On-Time Met (0) | Breach Rate (%) | On-Time Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`train`** | 68,157 | 61,190 | 6,967 | **89.78%** | 10.22% |
| **`val`** | 13,082 | 11,672 | 1,410 | **89.22%** | 10.78% |
| **`test`** | 16,210 | 14,530 | 1,680 | **89.64%** | 10.36% |
| **Combined** | **97,449** | **87,392** | **10,057** | **89.68%** | **10.32%** |

#### Continuous Regression Target (`delivery_delay_minutes`):
| Split | Mean Delay (All) | Min Delay | Max Delay |
| :--- | :---: | :---: | :---: |
| **`train`** | **6.44 mins** | 0.0 min | 36.4 mins |
| **`val`** | **6.41 mins** | 0.0 min | 29.1 mins |
| **`test`** | **6.41 mins** | 0.0 min | 32.9 mins |
| **Combined** | **6.43 mins** | **0.0 min** | **36.4 mins** |

---

### 4.3. Feature Statistics & Ranges
- `item_count`: Min **1**, Max **17**, Mean **5.00**
- `order_value`: Min **$80.00**, Max **$2,744.18**, Mean **$574.64**
- `promised_duration_minutes`: Min **20.00 min**, Max **54.27 min**, Mean **29.65 min**
- `order_hour`: Min **0**, Max **23**, Mean **11.46**
- `is_peak_rush_hour`: Exactly **20,363 orders (20.90%)** flagged as 1 (5 PM to 9 PM)
- `store_id`: Evenly balanced across all 100 stores (~950 to 1,020 orders per store)

---

### 4.4. Unseen Store Audit
- Unique stores in `train`: **100**
- Unique stores in `val`: **100**
- Unique stores in `test`: **100**
- **Unseen stores in `val` / `test`:** **0** (All 100 stores are fully represented in training).

---

## 5. Target Leakage Confirmation

A line-by-line inspection of [`build_predictive_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_predictive_features.py) confirms:
1. `item_count` is read directly from customer basket checkout units.
2. `order_value` is read directly from checkout transaction value.
3. `promised_duration_minutes` is calculated exclusively from checkout timestamps (`promised_time - order_time`).
4. `order_hour` is extracted from checkout timestamp `order_time`.
5. `day_of_week` is extracted from checkout timestamp `order_time`.
6. `is_peak_rush_hour` is derived exclusively from `order_hour`.
7. `store_id` is the raw alphanumeric dark-store identifier.
8. **ZERO features depend on `actual_delivery_time`, `status`, `delivery_delay_minutes`, or `sla_breached`.**
9. **ZERO picking or delivery telemetry is present in the feature matrix.**

---

## 6. Current Implementation Status

- [x] Feature pipeline revised: [`build_predictive_features.py`](file:///c:/Users/HP/Desktop/MacroOps/build_predictive_features.py).
- [x] Feature dataset re-generated: [`predictive_features/stage_a_features.csv`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/stage_a_features.csv) (97,449 rows, 13 columns).
- [x] Feature metadata updated: [`predictive_features/feature_metadata.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/feature_metadata.json).
- [x] Re-audit completed: [`predictive_features/validation_audit.json`](file:///c:/Users/HP/Desktop/MacroOps/predictive_features/validation_audit.json).
- [x] Report updated: [`FEATURE_ENGINEERING_REPORT.md`](file:///c:/Users/HP/Desktop/MacroOps/FEATURE_ENGINEERING_REPORT.md).
- [x] **Model training frozen.** No training executed.

*The Stage A feature matrix is verified, target-free, and ready for baseline model training upon your approval.*
