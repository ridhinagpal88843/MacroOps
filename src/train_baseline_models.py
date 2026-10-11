"""
MacroOps AI — Phase 2B: Stage A Baseline Model Training Pipeline
================================================================
Train and evaluate baseline classification and regression models on the
verified Stage A feature matrix (predictive_features/stage_a_features.csv).

Targets:
  - Classification: sla_breached (1 = Late / Breached, 0 = On-Time / Met)
  - Regression:     delivery_delay_minutes (Realized delay >= 0.0)

Population:
  - 97,449 orders with status IN ('Delivered_On_Time', 'Delivered_Late')

Partitions:
  - Train:      2026-09-01 to 2026-09-21 (68,157 rows)
  - Validation: 2026-09-22 to 2026-09-25 (13,082 rows)
  - Test:       2026-09-26 to 2026-09-30 (16,210 rows)

Models:
  - Classification:
      1. DummyClassifier (strategy='prior')
      2. LogisticRegression (max_iter=1000)
      3. LightGBMClassifier (default settings, native categorical handling)
  - Regression:
      1. DummyRegressor (strategy='mean')
      2. Ridge (alpha=1.0)
      3. LightGBMRegressor (default settings, native categorical handling)

Preprocessing:
  - Linear models:
      - Continuous (item_count, order_value, promised_duration_minutes) -> StandardScaler
      - Categorical (store_id, order_hour, day_of_week) -> OneHotEncoder(handle_unknown='ignore')
      - Binary (is_peak_rush_hour) -> passthrough
      - FITTED STRICTLY ON TRAIN ONLY.
  - LightGBM:
      - Categorical features -> OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
      - FITTED STRICTLY ON TRAIN ONLY.
      - Native categorical split optimization enabled.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss,
    accuracy_score,
    mean_absolute_error,
    root_mean_squared_error,
    r2_score
)
import lightgbm as lgb

# ---------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------
WORKSPACE_DIR = r"c:\Users\HP\Desktop\MacroOps"
DATA_PATH = os.path.join(WORKSPACE_DIR, "predictive_features", "stage_a_features.csv")
ARTIFACTS_DIR = os.path.join(WORKSPACE_DIR, "model_artifacts")

NUM_COLS = ["item_count", "order_value", "promised_duration_minutes"]
CAT_COLS = ["store_id", "order_hour", "day_of_week"]
BIN_COLS = ["is_peak_rush_hour"]
ALL_FEATURE_COLS = NUM_COLS + CAT_COLS + BIN_COLS

TARGET_CLS = "sla_breached"
TARGET_REG = "delivery_delay_minutes"

RANDOM_SEED = 42


def load_and_validate_data():
    """Load the verified Stage A feature matrix and partition by split."""
    print("=" * 80)
    print("1. LOADING AND PARTITIONING DATASET")
    print("=" * 80)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Feature dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df):,} total rows and {df.shape[1]} columns.")

    # Validate columns
    required_cols = ALL_FEATURE_COLS + [TARGET_CLS, TARGET_REG, "split"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Chronological splits
    train_mask = df["split"] == "train"
    val_mask = df["split"] == "val"
    test_mask = df["split"] == "test"

    print(f"  - Train Partition:      {train_mask.sum():,} rows ({train_mask.mean()*100:.2f}%)")
    print(f"  - Validation Partition: {val_mask.sum():,} rows ({val_mask.mean()*100:.2f}%)")
    print(f"  - Test Partition:       {test_mask.sum():,} rows ({test_mask.mean()*100:.2f}%)")

    # Split targets
    y_cls_train = df.loc[train_mask, TARGET_CLS].values
    y_cls_val = df.loc[val_mask, TARGET_CLS].values
    y_cls_test = df.loc[test_mask, TARGET_CLS].values

    y_reg_train = df.loc[train_mask, TARGET_REG].values
    y_reg_val = df.loc[val_mask, TARGET_REG].values
    y_reg_test = df.loc[test_mask, TARGET_REG].values

    print("\nTarget Distributions:")
    print(f"  Classification (sla_breached = 1 rate):")
    print(f"    Train: {y_cls_train.mean()*100:.2f}% | Val: {y_cls_val.mean()*100:.2f}% | Test: {y_cls_test.mean()*100:.2f}%")
    print(f"  Regression (delivery_delay_minutes mean +/- std):")
    print(f"    Train: {y_reg_train.mean():.2f} +/- {y_reg_train.std():.2f} mins")
    print(f"    Val:   {y_reg_val.mean():.2f} +/- {y_reg_val.std():.2f} mins")
    print(f"    Test:  {y_reg_test.mean():.2f} +/- {y_reg_test.std():.2f} mins")

    return df, train_mask, val_mask, test_mask


def build_preprocessors(df, train_mask):
    """
    Build and fit preprocessing transformations strictly on the training partition.
    Returns:
      - linear_preprocessor: ColumnTransformer for Logistic Regression and Ridge
      - lgb_ordinal_encoder: OrdinalEncoder for LightGBM categorical features
    """
    print("\n" + "=" * 80)
    print("2. FITTING PREPROCESSING PIPELINES (TRAINING PARTITION ONLY)")
    print("=" * 80)

    X_train_raw = df.loc[train_mask, ALL_FEATURE_COLS]

    # Preprocessing for Linear Models
    linear_preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_COLS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
            ("bin", "passthrough", BIN_COLS),
        ]
    )

    t0 = time.perf_counter()
    linear_preprocessor.fit(X_train_raw)
    lin_fit_time = time.perf_counter() - t0

    feature_names_linear = linear_preprocessor.get_feature_names_out()
    print(f"Linear Preprocessor fitted in {lin_fit_time:.4f}s.")
    print(f"  - Input raw features: {len(ALL_FEATURE_COLS)}")
    print(f"  - Output one-hot encoded features: {len(feature_names_linear)}")

    # Preprocessing for LightGBM: Leakage-safe OrdinalEncoder on categoricals
    lgb_ordinal_encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=-1
    )
    t0 = time.perf_counter()
    lgb_ordinal_encoder.fit(X_train_raw[CAT_COLS])
    lgb_oe_fit_time = time.perf_counter() - t0

    print(f"LightGBM OrdinalEncoder fitted in {lgb_oe_fit_time:.4f}s.")
    print(f"  - Encoded categories: {[len(cats) for cats in lgb_ordinal_encoder.categories_]} "
          f"for {CAT_COLS}")

    return linear_preprocessor, lgb_ordinal_encoder, feature_names_linear


def prepare_datasets(df, train_mask, val_mask, test_mask, linear_preprocessor, lgb_ordinal_encoder):
    """Transform data partitions using the fitted preprocessors."""
    print("\n" + "=" * 80)
    print("3. TRANSFORMING DATA PARTITIONS")
    print("=" * 80)

    # Raw splits
    X_train_raw = df.loc[train_mask, ALL_FEATURE_COLS]
    X_val_raw = df.loc[val_mask, ALL_FEATURE_COLS]
    X_test_raw = df.loc[test_mask, ALL_FEATURE_COLS]

    # Linear model datasets
    X_train_lin = linear_preprocessor.transform(X_train_raw)
    X_val_lin = linear_preprocessor.transform(X_val_raw)
    X_test_lin = linear_preprocessor.transform(X_test_raw)

    # LightGBM datasets: transform categorical columns, keep numeric and binary
    def transform_lgb(X_raw):
        X_out = X_raw.copy()
        X_out[CAT_COLS] = lgb_ordinal_encoder.transform(X_raw[CAT_COLS])
        # Ensure categorical columns are typed as category or integer for LightGBM
        for c in CAT_COLS:
            X_out[c] = X_out[c].astype(int)
        return X_out

    X_train_lgb = transform_lgb(X_train_raw)
    X_val_lgb = transform_lgb(X_val_raw)
    X_test_lgb = transform_lgb(X_test_raw)

    print(f"Linear feature matrix shape:   Train={X_train_lin.shape}, Val={X_val_lin.shape}, Test={X_test_lin.shape}")
    print(f"LightGBM feature matrix shape: Train={X_train_lgb.shape}, Val={X_val_lgb.shape}, Test={X_test_lgb.shape}")

    datasets = {
        "linear": (X_train_lin, X_val_lin, X_test_lin),
        "lgb": (X_train_lgb, X_val_lgb, X_test_lgb),
        "targets_cls": (
            df.loc[train_mask, TARGET_CLS].values,
            df.loc[val_mask, TARGET_CLS].values,
            df.loc[test_mask, TARGET_CLS].values
        ),
        "targets_reg": (
            df.loc[train_mask, TARGET_REG].values,
            df.loc[val_mask, TARGET_REG].values,
            df.loc[test_mask, TARGET_REG].values
        )
    }
    return datasets


def evaluate_classifier(name, model, X_val, y_val, X_test, y_test, num_features, train_time):
    """Evaluate classification model on validation and test partitions."""
    results = {
        "model_name": name,
        "train_time_sec": round(train_time, 4),
        "num_input_features": num_features,
        "validation": {},
        "test": {}
    }

    for split_name, X_split, y_split in [("validation", X_val, y_val), ("test", X_test, y_test)]:
        # Predict probabilities and classes
        prob_exists = hasattr(model, "predict_proba")
        if prob_exists:
            y_proba_all = model.predict_proba(X_split)
            # Probability of class 1 (SLA Breached)
            if y_proba_all.shape[1] == 2:
                y_proba = y_proba_all[:, 1]
            else:
                y_proba = y_proba_all[:, 0]
        else:
            y_proba = None

        y_pred = model.predict(X_split)

        # Metrics calculation
        pr_auc = float(average_precision_score(y_split, y_proba)) if y_proba is not None else float("nan")
        roc_auc = float(roc_auc_score(y_split, y_proba)) if y_proba is not None else float("nan")
        precision = float(precision_score(y_split, y_pred, zero_division=0))
        recall_majority = float(recall_score(y_split, y_pred, zero_division=0))  # Class 1 (Breached)
        recall_minority = float(recall_score(y_split, y_pred, pos_label=0, zero_division=0))  # Class 0 (On-Time)
        f1 = float(f1_score(y_split, y_pred, zero_division=0))
        accuracy = float(accuracy_score(y_split, y_pred))
        brier = float(brier_score_loss(y_split, y_proba)) if y_proba is not None else float("nan")

        cm = confusion_matrix(y_split, y_pred).tolist()  # [[TN, FP], [FN, TP]]

        # Probability distribution stats
        if y_proba is not None:
            prob_stats = {
                "mean": float(np.mean(y_proba)),
                "std": float(np.std(y_proba)),
                "min": float(np.min(y_proba)),
                "p25": float(np.percentile(y_proba, 25)),
                "median": float(np.median(y_proba)),
                "p75": float(np.percentile(y_proba, 75)),
                "max": float(np.max(y_proba)),
            }
        else:
            prob_stats = None

        results[split_name] = {
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "precision": round(precision, 4),
            "recall_breached_class1": round(recall_majority, 4),
            "recall_ontime_class0": round(recall_minority, 4),
            "f1_breached": round(f1, 4),
            "accuracy": round(accuracy, 4),
            "brier_score": round(brier, 4),
            "confusion_matrix": cm,
            "prob_distribution": prob_stats
        }

    return results


def evaluate_regressor(name, model, X_val, y_val, X_test, y_test, num_features, train_time):
    """Evaluate regression model on validation and test partitions."""
    results = {
        "model_name": name,
        "train_time_sec": round(train_time, 4),
        "num_input_features": num_features,
        "validation": {},
        "test": {}
    }

    for split_name, X_split, y_split in [("validation", X_val, y_val), ("test", X_test, y_test)]:
        y_pred = model.predict(X_split)

        mae = float(mean_absolute_error(y_split, y_pred))
        rmse = float(root_mean_squared_error(y_split, y_pred))
        r2 = float(r2_score(y_split, y_pred))

        results[split_name] = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "pred_mean": round(float(np.mean(y_pred)), 4),
            "pred_std": round(float(np.std(y_pred)), 4),
            "actual_mean": round(float(np.mean(y_split)), 4),
            "actual_std": round(float(np.std(y_split)), 4),
        }

    return results


def run_training_pipeline():
    """Main execution orchestrator."""
    print("=" * 80)
    print("MACROOPS AI — STAGE A BASELINE MODEL TRAINING (PHASE 2B)")
    print("=" * 80)

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # 1. Load data
    df, train_mask, val_mask, test_mask = load_and_validate_data()

    # 2. Fit preprocessors
    linear_preprocessor, lgb_ordinal_encoder, feature_names_linear = build_preprocessors(df, train_mask)

    # 3. Transform partitions
    datasets = prepare_datasets(df, train_mask, val_mask, test_mask, linear_preprocessor, lgb_ordinal_encoder)

    X_train_lin, X_val_lin, X_test_lin = datasets["linear"]
    X_train_lgb, X_val_lgb, X_test_lgb = datasets["lgb"]
    y_cls_train, y_cls_val, y_cls_test = datasets["targets_cls"]
    y_reg_train, y_reg_val, y_reg_test = datasets["targets_reg"]

    num_features_lin = X_train_lin.shape[1]
    num_features_lgb = X_train_lgb.shape[1]

    # Containers for all evaluations and diagnostics
    all_metrics = {
        "classification": {},
        "regression": {},
        "diagnostics": {
            "logistic_regression_coefficients": [],
            "ridge_coefficients": [],
            "lgbm_classifier_importance": [],
            "lgbm_regressor_importance": []
        }
    }

    # =========================================================
    # CLASSIFICATION MODELS
    # =========================================================
    print("\n" + "=" * 80)
    print("4. TRAINING & EVALUATING CLASSIFICATION MODELS")
    print("=" * 80)

    # Model 1: DummyClassifier
    print("\n>>> Training 1/3: DummyClassifier (strategy='prior')")
    t0 = time.perf_counter()
    dummy_cls = DummyClassifier(strategy="prior", random_state=RANDOM_SEED)
    dummy_cls.fit(X_train_lin, y_cls_train)
    t_dummy_cls = time.perf_counter() - t0
    res_dummy_cls = evaluate_classifier(
        "DummyClassifier (prior baseline)",
        dummy_cls,
        X_val_lin, y_cls_val,
        X_test_lin, y_cls_test,
        num_features=num_features_lin,
        train_time=t_dummy_cls
    )
    all_metrics["classification"]["dummy_classifier"] = res_dummy_cls
    print(f"  DummyClassifier Val PR-AUC: {res_dummy_cls['validation']['pr_auc']}, "
          f"ROC-AUC: {res_dummy_cls['validation']['roc_auc']}, "
          f"Brier: {res_dummy_cls['validation']['brier_score']}")

    # Model 2: Logistic Regression
    print("\n>>> Training 2/3: LogisticRegression (max_iter=1000)")
    t0 = time.perf_counter()
    log_reg = LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, solver="lbfgs")
    log_reg.fit(X_train_lin, y_cls_train)
    t_log_reg = time.perf_counter() - t0
    res_log_reg = evaluate_classifier(
        "LogisticRegression",
        log_reg,
        X_val_lin, y_cls_val,
        X_test_lin, y_cls_test,
        num_features=num_features_lin,
        train_time=t_log_reg
    )
    all_metrics["classification"]["logistic_regression"] = res_log_reg
    print(f"  LogisticRegression Val PR-AUC: {res_log_reg['validation']['pr_auc']}, "
          f"ROC-AUC: {res_log_reg['validation']['roc_auc']}, "
          f"On-Time (Class 0) Recall: {res_log_reg['validation']['recall_ontime_class0']}")

    # Model 3: LightGBM Classifier
    print("\n>>> Training 3/3: LightGBMClassifier (default baseline settings)")
    t0 = time.perf_counter()
    lgb_cls = lgb.LGBMClassifier(
        random_state=RANDOM_SEED,
        verbose=-1,
        n_jobs=-1
    )
    lgb_cls.fit(
        X_train_lgb,
        y_cls_train,
        categorical_feature=CAT_COLS
    )
    t_lgb_cls = time.perf_counter() - t0
    res_lgb_cls = evaluate_classifier(
        "LightGBMClassifier",
        lgb_cls,
        X_val_lgb, y_cls_val,
        X_test_lgb, y_cls_test,
        num_features=num_features_lgb,
        train_time=t_lgb_cls
    )
    all_metrics["classification"]["lightgbm_classifier"] = res_lgb_cls
    print(f"  LightGBMClassifier Val PR-AUC: {res_lgb_cls['validation']['pr_auc']}, "
          f"ROC-AUC: {res_lgb_cls['validation']['roc_auc']}, "
          f"On-Time (Class 0) Recall: {res_lgb_cls['validation']['recall_ontime_class0']}")

    # =========================================================
    # REGRESSION MODELS
    # =========================================================
    print("\n" + "=" * 80)
    print("5. TRAINING & EVALUATING REGRESSION MODELS")
    print("=" * 80)

    # Model 1: DummyRegressor
    print("\n>>> Training 1/3: DummyRegressor (strategy='mean')")
    t0 = time.perf_counter()
    dummy_reg = DummyRegressor(strategy="mean")
    dummy_reg.fit(X_train_lin, y_reg_train)
    t_dummy_reg = time.perf_counter() - t0
    res_dummy_reg = evaluate_regressor(
        "DummyRegressor (mean baseline)",
        dummy_reg,
        X_val_lin, y_reg_val,
        X_test_lin, y_reg_test,
        num_features=num_features_lin,
        train_time=t_dummy_reg
    )
    all_metrics["regression"]["dummy_regressor"] = res_dummy_reg
    print(f"  DummyRegressor Val MAE: {res_dummy_reg['validation']['mae']}, "
          f"RMSE: {res_dummy_reg['validation']['rmse']}, "
          f"R2: {res_dummy_reg['validation']['r2']}")

    # Model 2: Ridge Regression
    print("\n>>> Training 2/3: Ridge Regression (alpha=1.0)")
    t0 = time.perf_counter()
    ridge_reg = Ridge(alpha=1.0, random_state=RANDOM_SEED)
    ridge_reg.fit(X_train_lin, y_reg_train)
    t_ridge_reg = time.perf_counter() - t0
    res_ridge_reg = evaluate_regressor(
        "Ridge",
        ridge_reg,
        X_val_lin, y_reg_val,
        X_test_lin, y_reg_test,
        num_features=num_features_lin,
        train_time=t_ridge_reg
    )
    all_metrics["regression"]["ridge_regression"] = res_ridge_reg
    print(f"  Ridge Val MAE: {res_ridge_reg['validation']['mae']}, "
          f"RMSE: {res_ridge_reg['validation']['rmse']}, "
          f"R2: {res_ridge_reg['validation']['r2']}")

    # Model 3: LightGBM Regressor
    print("\n>>> Training 3/3: LightGBMRegressor (default baseline settings)")
    t0 = time.perf_counter()
    lgb_reg = lgb.LGBMRegressor(
        random_state=RANDOM_SEED,
        verbose=-1,
        n_jobs=-1
    )
    lgb_reg.fit(
        X_train_lgb,
        y_reg_train,
        categorical_feature=CAT_COLS
    )
    t_lgb_reg = time.perf_counter() - t0
    res_lgb_reg = evaluate_regressor(
        "LightGBMRegressor",
        lgb_reg,
        X_val_lgb, y_reg_val,
        X_test_lgb, y_reg_test,
        num_features=num_features_lgb,
        train_time=t_lgb_reg
    )
    all_metrics["regression"]["lightgbm_regressor"] = res_lgb_reg
    print(f"  LightGBMRegressor Val MAE: {res_lgb_reg['validation']['mae']}, "
          f"RMSE: {res_lgb_reg['validation']['rmse']}, "
          f"R2: {res_lgb_reg['validation']['r2']}")

    # =========================================================
    # MODEL DIAGNOSTICS & FEATURE IMPORTANCE
    # =========================================================
    print("\n" + "=" * 80)
    print("6. EXTRACTING MODEL DIAGNOSTICS & FEATURE IMPORTANCES")
    print("=" * 80)

    # 1. Logistic Regression Coefficients
    log_coefs = log_reg.coef_[0]
    log_df = pd.DataFrame({
        "feature": feature_names_linear,
        "coefficient": log_coefs,
        "odds_ratio": np.exp(log_coefs),
        "abs_coefficient": np.abs(log_coefs)
    }).sort_values("abs_coefficient", ascending=False).reset_index(drop=True)
    all_metrics["diagnostics"]["logistic_regression_coefficients"] = log_df.to_dict(orient="records")

    print("\nTop 10 Logistic Regression Coefficients by Magnitude:")
    for _, row in log_df.head(10).iterrows():
        print(f"  {row['feature']:<35} Coef: {row['coefficient']:+8.4f} | Odds Ratio: {row['odds_ratio']:7.4f}")

    # 2. Ridge Regression Coefficients
    ridge_coefs = ridge_reg.coef_
    ridge_df = pd.DataFrame({
        "feature": feature_names_linear,
        "coefficient": ridge_coefs,
        "abs_coefficient": np.abs(ridge_coefs)
    }).sort_values("abs_coefficient", ascending=False).reset_index(drop=True)
    all_metrics["diagnostics"]["ridge_coefficients"] = ridge_df.to_dict(orient="records")

    print("\nTop 10 Ridge Regression Coefficients by Magnitude:")
    for _, row in ridge_df.head(10).iterrows():
        print(f"  {row['feature']:<35} Coef: {row['coefficient']:+8.4f}")

    # 3. LightGBM Classifier Feature Importance
    lgb_cls_split = lgb_cls.booster_.feature_importance(importance_type="split")
    lgb_cls_gain = lgb_cls.booster_.feature_importance(importance_type="gain")
    lgb_cls_imp_df = pd.DataFrame({
        "feature": ALL_FEATURE_COLS,
        "importance_split": lgb_cls_split,
        "importance_gain": lgb_cls_gain
    }).sort_values("importance_gain", ascending=False).reset_index(drop=True)
    all_metrics["diagnostics"]["lgbm_classifier_importance"] = lgb_cls_imp_df.to_dict(orient="records")

    print("\nLightGBM Classifier Feature Importance (by Gain):")
    for _, row in lgb_cls_imp_df.iterrows():
        print(f"  {row['feature']:<28} Gain: {row['importance_gain']:12.2f} | Split Count: {row['importance_split']:6d}")

    # 4. LightGBM Regressor Feature Importance
    lgb_reg_split = lgb_reg.booster_.feature_importance(importance_type="split")
    lgb_reg_gain = lgb_reg.booster_.feature_importance(importance_type="gain")
    lgb_reg_imp_df = pd.DataFrame({
        "feature": ALL_FEATURE_COLS,
        "importance_split": lgb_reg_split,
        "importance_gain": lgb_reg_gain
    }).sort_values("importance_gain", ascending=False).reset_index(drop=True)
    all_metrics["diagnostics"]["lgbm_regressor_importance"] = lgb_reg_imp_df.to_dict(orient="records")

    print("\nLightGBM Regressor Feature Importance (by Gain):")
    for _, row in lgb_reg_imp_df.iterrows():
        print(f"  {row['feature']:<28} Gain: {row['importance_gain']:12.2f} | Split Count: {row['importance_split']:6d}")

    # =========================================================
    # ARTIFACT SERIALIZATION
    # =========================================================
    print("\n" + "=" * 80)
    print("7. SAVING TRAINED ARTIFACTS TO model_artifacts/")
    print("=" * 80)

    # Save Preprocessors
    joblib.dump(linear_preprocessor, os.path.join(ARTIFACTS_DIR, "linear_preprocessor.joblib"))
    joblib.dump(lgb_ordinal_encoder, os.path.join(ARTIFACTS_DIR, "lgb_ordinal_encoder.joblib"))

    # Save Classification Models
    joblib.dump(dummy_cls, os.path.join(ARTIFACTS_DIR, "dummy_classifier.joblib"))
    joblib.dump(log_reg, os.path.join(ARTIFACTS_DIR, "logistic_regression.joblib"))
    joblib.dump(lgb_cls, os.path.join(ARTIFACTS_DIR, "lightgbm_classifier.joblib"))

    # Save Regression Models
    joblib.dump(dummy_reg, os.path.join(ARTIFACTS_DIR, "dummy_regressor.joblib"))
    joblib.dump(ridge_reg, os.path.join(ARTIFACTS_DIR, "ridge_regressor.joblib"))
    joblib.dump(lgb_reg, os.path.join(ARTIFACTS_DIR, "lightgbm_regressor.joblib"))

    # Save Metrics & Diagnostics JSON
    metrics_path = os.path.join(ARTIFACTS_DIR, "evaluation_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    print("All artifacts successfully saved:")
    for f in os.listdir(ARTIFACTS_DIR):
        fpath = os.path.join(ARTIFACTS_DIR, f)
        print(f"  - {f} ({os.path.getsize(fpath):,} bytes)")

    print("\n" + "=" * 80)
    print("PHASE 2B BASELINE MODEL TRAINING COMPLETED SUCCESSFULLY.")
    print("=" * 80)
    return all_metrics


if __name__ == "__main__":
    run_training_pipeline()
