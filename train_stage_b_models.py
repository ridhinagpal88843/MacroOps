"""
MacroOps AI — Stage B Model Training & Diagnostic Evaluation Pipeline
=====================================================================
Trains and evaluates dynamic in-fulfillment risk models for:
  - Checkpoint B1: Post-picking (picking.pick_end)
  - Checkpoint B2: Post-dispatch proxy (max(picking.pick_end, delivery.pickup_time))

Models:
  1. Dummy Classifier (Prior Baseline)
  2. Logistic Regression (Interpretable Linear Reference)
  3. LightGBM Classifier (Primary Production Candidate)

Comparative Benchmarking:
  - Evaluates Stage A frozen LightGBM model on the identical test cohort (N = 4,095).
  - Measures incremental lift of B1 and B2 over Stage A.

Governance Rules:
  - Fit learned preprocessing STRICTLY on Train split (Sept 1-21).
  - Select operating thresholds STRICTLY on Validation split (Sept 22-25).
  - Evaluate final performance ONCE on untouched Test split (Sept 26-30).
  - Zero modifications to Stage A artifacts or source CSVs.
"""

import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss,
    accuracy_score
)
from lightgbm import LGBMClassifier

WORKSPACE_DIR = r"c:\Users\HP\Desktop\MacroOps"
PRED_DIR = os.path.join(WORKSPACE_DIR, "predictive_features")
ARTIFACTS_DIR = os.path.join(WORKSPACE_DIR, "model_artifacts")

B1_CSV = os.path.join(PRED_DIR, "stage_b1_features.csv")
B2_CSV = os.path.join(PRED_DIR, "stage_b2_features.csv")
STAGE_A_CSV = os.path.join(PRED_DIR, "stage_a_features.csv")

STAGE_A_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "lightgbm_classifier.joblib")
STAGE_A_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "lgb_ordinal_encoder.joblib")

METRICS_OUT = os.path.join(ARTIFACTS_DIR, "stage_b_evaluation_metrics.json")
CONFIG_OUT = os.path.join(WORKSPACE_DIR, "stage_b_final_config.json")

def evaluate_predictions(y_true, y_prob, threshold):
    """Compute comprehensive diagnostic metrics at a decision threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    
    total = len(y_true)
    flagged = tp + fp
    alert_rate = flagged / total
    
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # Specificity / On-time recall
    ontime_rec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ontime_prec = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    
    pr_auc = average_precision_score(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)
    brier = brier_score_loss(y_true, y_prob)
    acc = accuracy_score(y_true, y_pred)
    
    return {
        "threshold": round(float(threshold), 4),
        "total_orders": int(total),
        "flagged_orders": int(flagged),
        "alert_rate_pct": round(float(alert_rate * 100), 2),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "precision_pct": round(float(prec * 100), 2),
        "recall_pct": round(float(rec * 100), 2),
        "f1": round(float(f1), 4),
        "ontime_recall_pct": round(float(ontime_rec * 100), 2),
        "ontime_precision_pct": round(float(ontime_prec * 100), 2),
        "pr_auc": round(float(pr_auc), 4),
        "roc_auc": round(float(roc_auc), 4),
        "brier_score": round(float(brier), 4),
        "accuracy_pct": round(float(acc * 100), 2)
    }

def scan_thresholds(y_true, y_prob, thresholds=None):
    if thresholds is None:
        thresholds = np.linspace(0.50, 0.99, 50)
    results = []
    for t in thresholds:
        results.append(evaluate_predictions(y_true, y_prob, t))
    return results

def run_stage_b_training():
    print("=" * 80)
    print("MacroOps AI — Stage B Model Training & Diagnostic Evaluation")
    print("=" * 80)
    
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    # 1. Load Data
    print(f"Loading Stage B1 features from: {B1_CSV}")
    df_b1 = pd.read_csv(B1_CSV)
    print(f"Loading Stage B2 features from: {B2_CSV}")
    df_b2 = pd.read_csv(B2_CSV)
    print(f"Loading Stage A features from: {STAGE_A_CSV}")
    df_a = pd.read_csv(STAGE_A_CSV)
    
    # Checkpoint B1 feature subsets
    b1_num_cols = [
        'item_count', 'order_value', 'promised_duration_minutes',
        'time_to_pick_start_min', 'pick_duration_minutes', 'elapsed_time_to_b1_min',
        'items_picked', 'items_missing', 'picking_speed_items_per_min',
        'remaining_sla_budget_b1_min', 'budget_consumed_ratio_b1', 'pick_budget_deficit_min',
        'assignment_delay_to_b1_min', 'time_from_assignment_to_b1_min'
    ]
    b1_bin_cols = [
        'is_peak_rush_hour', 'has_picking_exception', 'is_past_promise_at_b1',
        'is_courier_assigned_by_b1'
    ]
    b1_cat_cols = ['store_id', 'order_hour', 'day_of_week', 'picker_id', 'rider_id_at_b1']
    b1_all_features = b1_num_cols + b1_bin_cols + b1_cat_cols
    
    # Checkpoint B2 feature subsets
    b2_num_cols = [
        'item_count', 'order_value', 'promised_duration_minutes',
        'time_to_pick_start_min', 'pick_duration_minutes', 'items_picked',
        'items_missing', 'picking_speed_items_per_min', 'distance_km',
        'assignment_delay_min', 'elapsed_time_to_dispatch_min',
        'remaining_sla_budget_b2_min', 'budget_consumed_ratio_b2',
        'transit_budget_deficit_min', 'courier_wait_at_store_min',
        'order_staging_dwell_min', 'required_speed_kmh'
    ]
    b2_bin_cols = [
        'is_peak_rush_hour', 'has_picking_exception', 'is_past_promise_at_b2',
        'rider_arrived_before_pick_end', 'is_speed_unfeasible'
    ]
    b2_cat_cols = ['store_id', 'order_hour', 'day_of_week', 'picker_id', 'rider_id']
    b2_all_features = b2_num_cols + b2_bin_cols + b2_cat_cols
    
    # Splits for B1
    train_mask = df_b1['split'] == 'train'
    val_mask = df_b1['split'] == 'val'
    test_mask = df_b1['split'] == 'test'
    
    y_b1_train = df_b1.loc[train_mask, 'sla_breached'].values
    y_b1_val = df_b1.loc[val_mask, 'sla_breached'].values
    y_b1_test = df_b1.loc[test_mask, 'sla_breached'].values
    
    # Splits for B2
    y_b2_train = df_b2.loc[train_mask, 'sla_breached'].values
    y_b2_val = df_b2.loc[val_mask, 'sla_breached'].values
    y_b2_test = df_b2.loc[test_mask, 'sla_breached'].values
    
    print(f"\nCohort Sizes: Train={train_mask.sum():,}, Val={val_mask.sum():,}, Test={test_mask.sum():,}")
    print(f"Test Positive Prevalence (Breach Baseline): {y_b1_test.mean()*100:.2f}%\n")
    
    # -------------------------------------------------------------
    # STAGE A BENCHMARK ON IDENTICAL TEST COHORT (N = 4,095)
    # -------------------------------------------------------------
    print("=" * 70)
    print("EVALUATING STAGE A BENCHMARK ON IDENTICAL TEST COHORT (N = 4,095)")
    print("=" * 70)
    test_order_ids = df_b1.loc[test_mask, 'order_id'].values
    df_a_matched = df_a[df_a['order_id'].isin(test_order_ids)].set_index('order_id').reindex(test_order_ids).reset_index()
    
    stage_a_lgb = joblib.load(STAGE_A_MODEL_PATH)
    stage_a_enc = joblib.load(STAGE_A_ENCODER_PATH)
    
    stage_a_cat_cols = ['store_id', 'order_hour', 'day_of_week']
    stage_a_feature_order = [
        'item_count', 'order_value', 'promised_duration_minutes',
        'order_hour', 'day_of_week', 'is_peak_rush_hour', 'store_id'
    ]
    
    X_a_test = df_a_matched[stage_a_feature_order].copy()
    X_a_test[stage_a_cat_cols] = stage_a_enc.transform(X_a_test[stage_a_cat_cols])
    y_a_test_prob = stage_a_lgb.predict_proba(X_a_test)[:, 1]
    
    stage_a_test_metrics_tau93 = evaluate_predictions(y_b1_test, y_a_test_prob, threshold=0.9300)
    stage_a_test_metrics_tau50 = evaluate_predictions(y_b1_test, y_a_test_prob, threshold=0.5000)
    print(f"Stage A Frozen Policy (tau = 0.9300) on Identical Test Cohort:")
    print(f"  PR-AUC: {stage_a_test_metrics_tau93['pr_auc']:.4f} | ROC-AUC: {stage_a_test_metrics_tau93['roc_auc']:.4f} | Brier: {stage_a_test_metrics_tau93['brier_score']:.4f}")
    print(f"  Alert Rate: {stage_a_test_metrics_tau93['alert_rate_pct']:.2f}% | Precision: {stage_a_test_metrics_tau93['precision_pct']:.2f}% | Recall: {stage_a_test_metrics_tau93['recall_pct']:.2f}%")
    
    # -------------------------------------------------------------
    # CHECKPOINT B1: MODEL TRAINING & EVALUATION
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TRAINING CHECKPOINT B1 MODELS (Post-Picking, T1 = pick_end)")
    print("=" * 70)
    
    # 1. B1 Preprocessing Pipelines (Fitted strictly on Train)
    # Linear Preprocessor
    b1_num_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    b1_bin_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent'))
    ])
    b1_cat_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='MISSING')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    b1_linear_preprocessor = ColumnTransformer(
        transformers=[
            ('num', b1_num_transformer, b1_num_cols),
            ('bin', b1_bin_transformer, b1_bin_cols),
            ('cat', b1_cat_transformer, b1_cat_cols)
        ]
    )
    
    # Fit linear preprocessor on Train
    X_b1_train_raw = df_b1.loc[train_mask, b1_all_features].copy()
    X_b1_val_raw = df_b1.loc[val_mask, b1_all_features].copy()
    X_b1_test_raw = df_b1.loc[test_mask, b1_all_features].copy()
    
    b1_linear_preprocessor.fit(X_b1_train_raw)
    X_b1_train_lin = b1_linear_preprocessor.transform(X_b1_train_raw)
    X_b1_val_lin = b1_linear_preprocessor.transform(X_b1_val_raw)
    X_b1_test_lin = b1_linear_preprocessor.transform(X_b1_test_raw)
    
    # LightGBM Ordinal Encoder for Categoricals (Fitted strictly on Train)
    b1_ordinal_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    # Fill NAs in categoricals prior to ordinal encoding
    for df in [X_b1_train_raw, X_b1_val_raw, X_b1_test_raw]:
        for c in b1_cat_cols:
            df[c] = df[c].fillna('MISSING').astype(str)
            
    b1_ordinal_encoder.fit(X_b1_train_raw[b1_cat_cols])
    
    X_b1_train_lgb = X_b1_train_raw.copy()
    X_b1_val_lgb = X_b1_val_raw.copy()
    X_b1_test_lgb = X_b1_test_raw.copy()
    
    X_b1_train_lgb[b1_cat_cols] = b1_ordinal_encoder.transform(X_b1_train_raw[b1_cat_cols])
    X_b1_val_lgb[b1_cat_cols] = b1_ordinal_encoder.transform(X_b1_val_raw[b1_cat_cols])
    X_b1_test_lgb[b1_cat_cols] = b1_ordinal_encoder.transform(X_b1_test_raw[b1_cat_cols])
    
    # Models B1
    # 1. Dummy
    b1_dummy = DummyClassifier(strategy='prior')
    b1_dummy.fit(X_b1_train_lgb, y_b1_train)
    b1_dummy_val_prob = b1_dummy.predict_proba(X_b1_val_lgb)[:, 1]
    b1_dummy_test_prob = b1_dummy.predict_proba(X_b1_test_lgb)[:, 1]
    
    # 2. Logistic Regression
    b1_logistic = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs')
    b1_logistic.fit(X_b1_train_lin, y_b1_train)
    b1_logistic_val_prob = b1_logistic.predict_proba(X_b1_val_lin)[:, 1]
    b1_logistic_test_prob = b1_logistic.predict_proba(X_b1_test_lin)[:, 1]
    
    # 3. LightGBM Classifier
    b1_lgb = LGBMClassifier(
        random_state=42,
        n_estimators=150,
        learning_rate=0.05,
        min_child_samples=25,
        verbose=-1
    )
    b1_lgb.fit(X_b1_train_lgb, y_b1_train, categorical_feature=b1_cat_cols)
    b1_lgb_val_prob = b1_lgb.predict_proba(X_b1_val_lgb)[:, 1]
    b1_lgb_test_prob = b1_lgb.predict_proba(X_b1_test_lgb)[:, 1]
    
    print(f"Checkpoint B1 Validation PR-AUC:")
    print(f"  Dummy: {average_precision_score(y_b1_val, b1_dummy_val_prob):.4f}")
    print(f"  Logistic Regression: {average_precision_score(y_b1_val, b1_logistic_val_prob):.4f}")
    print(f"  LightGBM Classifier: {average_precision_score(y_b1_val, b1_lgb_val_prob):.4f}")
    
    # -------------------------------------------------------------
    # CHECKPOINT B2: MODEL TRAINING & EVALUATION
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TRAINING CHECKPOINT B2 MODELS (Post-Dispatch Proxy, T2 = effective_dispatch)")
    print("=" * 70)
    
    # Linear Preprocessor for B2
    b2_num_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    b2_bin_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent'))
    ])
    b2_cat_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='MISSING')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    b2_linear_preprocessor = ColumnTransformer(
        transformers=[
            ('num', b2_num_transformer, b2_num_cols),
            ('bin', b2_bin_transformer, b2_bin_cols),
            ('cat', b2_cat_transformer, b2_cat_cols)
        ]
    )
    
    X_b2_train_raw = df_b2.loc[train_mask, b2_all_features].copy()
    X_b2_val_raw = df_b2.loc[val_mask, b2_all_features].copy()
    X_b2_test_raw = df_b2.loc[test_mask, b2_all_features].copy()
    
    b2_linear_preprocessor.fit(X_b2_train_raw)
    X_b2_train_lin = b2_linear_preprocessor.transform(X_b2_train_raw)
    X_b2_val_lin = b2_linear_preprocessor.transform(X_b2_val_raw)
    X_b2_test_lin = b2_linear_preprocessor.transform(X_b2_test_raw)
    
    # LightGBM Ordinal Encoder for B2 Categoricals
    b2_ordinal_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    for df in [X_b2_train_raw, X_b2_val_raw, X_b2_test_raw]:
        for c in b2_cat_cols:
            df[c] = df[c].fillna('MISSING').astype(str)
            
    b2_ordinal_encoder.fit(X_b2_train_raw[b2_cat_cols])
    
    X_b2_train_lgb = X_b2_train_raw.copy()
    X_b2_val_lgb = X_b2_val_raw.copy()
    X_b2_test_lgb = X_b2_test_raw.copy()
    
    X_b2_train_lgb[b2_cat_cols] = b2_ordinal_encoder.transform(X_b2_train_raw[b2_cat_cols])
    X_b2_val_lgb[b2_cat_cols] = b2_ordinal_encoder.transform(X_b2_val_raw[b2_cat_cols])
    X_b2_test_lgb[b2_cat_cols] = b2_ordinal_encoder.transform(X_b2_test_raw[b2_cat_cols])
    
    # Models B2
    # 1. Dummy
    b2_dummy = DummyClassifier(strategy='prior')
    b2_dummy.fit(X_b2_train_lgb, y_b2_train)
    b2_dummy_val_prob = b2_dummy.predict_proba(X_b2_val_lgb)[:, 1]
    b2_dummy_test_prob = b2_dummy.predict_proba(X_b2_test_lgb)[:, 1]
    
    # 2. Logistic Regression
    b2_logistic = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs')
    b2_logistic.fit(X_b2_train_lin, y_b2_train)
    b2_logistic_val_prob = b2_logistic.predict_proba(X_b2_lin := X_b2_val_lin)[:, 1]
    b2_logistic_test_prob = b2_logistic.predict_proba(X_b2_test_lin)[:, 1]
    
    # 3. LightGBM Classifier
    b2_lgb = LGBMClassifier(
        random_state=42,
        n_estimators=150,
        learning_rate=0.05,
        min_child_samples=25,
        verbose=-1
    )
    b2_lgb.fit(X_b2_train_lgb, y_b2_train, categorical_feature=b2_cat_cols)
    b2_lgb_val_prob = b2_lgb.predict_proba(X_b2_val_lgb)[:, 1]
    b2_lgb_test_prob = b2_lgb.predict_proba(X_b2_test_lgb)[:, 1]
    
    # Hybrid Deterministic Policy Probabilities for B2:
    # If is_past_promise_at_b2 == 1, probability = 1.0
    val_b2_deterministic_flags = df_b2.loc[val_mask, 'is_past_promise_at_b2'].values
    test_b2_deterministic_flags = df_b2.loc[test_mask, 'is_past_promise_at_b2'].values
    
    b2_lgb_val_prob_hybrid = np.where(val_b2_deterministic_flags == 1, 1.0, b2_lgb_val_prob)
    b2_lgb_test_prob_hybrid = np.where(test_b2_deterministic_flags == 1, 1.0, b2_lgb_test_prob)
    
    print(f"Checkpoint B2 Validation PR-AUC:")
    print(f"  Dummy: {average_precision_score(y_b2_val, b2_dummy_val_prob):.4f}")
    print(f"  Logistic Regression: {average_precision_score(y_b2_val, b2_logistic_val_prob):.4f}")
    print(f"  LightGBM Classifier (Pure): {average_precision_score(y_b2_val, b2_lgb_val_prob):.4f}")
    print(f"  LightGBM Classifier (Hybrid): {average_precision_score(y_b2_val, b2_lgb_val_prob_hybrid):.4f}")
    
    # -------------------------------------------------------------
    # THRESHOLD SELECTION ON VALIDATION SET (B1 & B2)
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("OPERATING THRESHOLD SELECTION ON VALIDATION SET")
    print("=" * 70)
    
    # Scan B1 thresholds
    b1_grid = np.linspace(0.80, 0.98, 91)
    b1_val_scan = scan_thresholds(y_b1_val, b1_lgb_val_prob, b1_grid)
    
    # Scan B2 thresholds
    b2_grid = np.linspace(0.80, 0.98, 91)
    b2_val_scan = scan_thresholds(y_b2_val, b2_lgb_val_prob_hybrid, b2_grid)
    
    # Strategy 1: Targeted Escalation under 30% Workload Budget
    # Find highest threshold where alert_rate <= 30.0% and precision >= 94.0%
    b1_target_policy = [s for s in b1_val_scan if s['alert_rate_pct'] <= 30.0 and s['precision_pct'] >= 93.5]
    b1_chosen_t = b1_target_policy[0]['threshold'] if b1_target_policy else 0.9300
    
    b2_target_policy = [s for s in b2_val_scan if s['alert_rate_pct'] <= 30.0 and s['precision_pct'] >= 93.5]
    b2_chosen_t = b2_target_policy[0]['threshold'] if b2_target_policy else 0.9300
    
    print(f"Selected Candidate Thresholds on Validation:")
    print(f"  B1 Selected Threshold: tau = {b1_chosen_t:.4f}")
    print(f"  B2 Selected Threshold: tau = {b2_chosen_t:.4f}")
    
    # -------------------------------------------------------------
    # FINAL HOLDOUT TEST EVALUATION (TOUCHED ONLY ONCE)
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL HOLDOUT TEST EVALUATION (September 26–30, N = 4,095)")
    print("=" * 70)
    
    # Checkpoint B1 Test Results
    b1_test_tau_frozen = evaluate_predictions(y_b1_test, b1_lgb_test_prob, threshold=0.9300)
    b1_test_tau_selected = evaluate_predictions(y_b1_test, b1_lgb_test_prob, threshold=b1_chosen_t)
    b1_test_logreg = evaluate_predictions(y_b1_test, b1_logistic_test_prob, threshold=0.9300)
    
    # Checkpoint B2 Test Results
    b2_test_tau_frozen = evaluate_predictions(y_b2_test, b2_lgb_test_prob_hybrid, threshold=0.9300)
    b2_test_tau_selected = evaluate_predictions(y_b2_test, b2_lgb_test_prob_hybrid, threshold=b2_chosen_t)
    b2_test_logreg = evaluate_predictions(y_b2_test, b2_logistic_test_prob, threshold=0.9300)
    
    print("\n--- TEST SUMMARY TABLE (tau = 0.9300 Standard Escalation Benchmark) ---")
    print(f"{'Metric':<25} | {'Stage A (Frozen)':<18} | {'Stage B1 (Pick End)':<20} | {'Stage B2 (Dispatch)':<20}")
    print("-" * 90)
    print(f"{'PR-AUC':<25} | {stage_a_test_metrics_tau93['pr_auc']:<18.4f} | {b1_test_tau_frozen['pr_auc']:<20.4f} | {b2_test_tau_frozen['pr_auc']:<20.4f}")
    print(f"{'ROC-AUC':<25} | {stage_a_test_metrics_tau93['roc_auc']:<18.4f} | {b1_test_tau_frozen['roc_auc']:<20.4f} | {b2_test_tau_frozen['roc_auc']:<20.4f}")
    print(f"{'Brier Score':<25} | {stage_a_test_metrics_tau93['brier_score']:<18.4f} | {b1_test_tau_frozen['brier_score']:<20.4f} | {b2_test_tau_frozen['brier_score']:<20.4f}")
    print(f"{'Alert Workload %':<25} | {stage_a_test_metrics_tau93['alert_rate_pct']:<18.2f}% | {b1_test_tau_frozen['alert_rate_pct']:<20.2f}% | {b2_test_tau_frozen['alert_rate_pct']:<20.2f}%")
    print(f"{'Breach Precision %':<25} | {stage_a_test_metrics_tau93['precision_pct']:<18.2f}% | {b1_test_tau_frozen['precision_pct']:<20.2f}% | {b2_test_tau_frozen['precision_pct']:<20.2f}%")
    print(f"{'Breach Recall %':<25} | {stage_a_test_metrics_tau93['recall_pct']:<18.2f}% | {b1_test_tau_frozen['recall_pct']:<20.2f}% | {b2_test_tau_frozen['recall_pct']:<20.2f}%")
    print(f"{'Breaches Captured (TP)':<25} | {stage_a_test_metrics_tau93['tp']:<18} | {b1_test_tau_frozen['tp']:<20} | {b2_test_tau_frozen['tp']:<20}")
    print(f"{'F1-Score':<25} | {stage_a_test_metrics_tau93['f1']:<18.4f} | {b1_test_tau_frozen['f1']:<20.4f} | {b2_test_tau_frozen['f1']:<20.4f}")
    print("-" * 90)
    
    # Deterministic counts in test set
    test_deterministic_breaches_b2 = int((test_b2_deterministic_flags == 1).sum())
    test_deterministic_actual_breaches_b2 = int(y_b2_test[test_b2_deterministic_flags == 1].sum())
    print(f"\nDeterministic Breaches at B2 Test Set: {test_deterministic_breaches_b2} orders flagged (Actual breaches: {test_deterministic_actual_breaches_b2})")
    
    # -------------------------------------------------------------
    # SAVE MODEL ARTIFACTS
    # -------------------------------------------------------------
    print("\nSaving Stage B model artifacts...")
    # B1 Artifacts
    joblib.dump(b1_lgb, os.path.join(ARTIFACTS_DIR, "stage_b1_lightgbm.joblib"))
    joblib.dump(b1_logistic, os.path.join(ARTIFACTS_DIR, "stage_b1_logistic.joblib"))
    joblib.dump(b1_dummy, os.path.join(ARTIFACTS_DIR, "stage_b1_dummy.joblib"))
    joblib.dump(b1_ordinal_encoder, os.path.join(ARTIFACTS_DIR, "stage_b1_ordinal_encoder.joblib"))
    joblib.dump(b1_linear_preprocessor, os.path.join(ARTIFACTS_DIR, "stage_b1_linear_preprocessor.joblib"))
    
    # B2 Artifacts
    joblib.dump(b2_lgb, os.path.join(ARTIFACTS_DIR, "stage_b2_lightgbm.joblib"))
    joblib.dump(b2_logistic, os.path.join(ARTIFACTS_DIR, "stage_b2_logistic.joblib"))
    joblib.dump(b2_dummy, os.path.join(ARTIFACTS_DIR, "stage_b2_dummy.joblib"))
    joblib.dump(b2_ordinal_encoder, os.path.join(ARTIFACTS_DIR, "stage_b2_ordinal_encoder.joblib"))
    joblib.dump(b2_linear_preprocessor, os.path.join(ARTIFACTS_DIR, "stage_b2_linear_preprocessor.joblib"))
    
    # -------------------------------------------------------------
    # SAVE MACHINE-READABLE METRICS & CONFIG
    # -------------------------------------------------------------
    metrics_payload = {
        "pipeline_name": "MacroOps AI Stage B Model Training & Evaluation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "test_cohort_size": int(len(y_b1_test)),
        "test_base_rate_breaches_pct": round(float(y_b1_test.mean() * 100), 2),
        "stage_a_identical_cohort_benchmark": {
            "tau_0_9300_frozen": stage_a_test_metrics_tau93,
            "tau_0_5000_default": stage_a_test_metrics_tau50
        },
        "checkpoint_b1_post_picking": {
            "validation_pr_auc": {
                "dummy": round(float(average_precision_score(y_b1_val, b1_dummy_val_prob)), 4),
                "logistic_regression": round(float(average_precision_score(y_b1_val, b1_logistic_val_prob)), 4),
                "lightgbm": round(float(average_precision_score(y_b1_val, b1_lgb_val_prob)), 4)
            },
            "test_evaluation": {
                "tau_0_9300_frozen": b1_test_tau_frozen,
                "tau_selected_val": b1_test_tau_selected,
                "logistic_regression_tau_0_9300": b1_test_logreg
            }
        },
        "checkpoint_b2_post_dispatch_proxy": {
            "validation_pr_auc": {
                "dummy": round(float(average_precision_score(y_b2_val, b2_dummy_val_prob)), 4),
                "logistic_regression": round(float(average_precision_score(y_b2_val, b2_logistic_val_prob)), 4),
                "lightgbm_pure": round(float(average_precision_score(y_b2_val, b2_lgb_val_prob)), 4),
                "lightgbm_hybrid": round(float(average_precision_score(y_b2_val, b2_lgb_val_prob_hybrid)), 4)
            },
            "test_evaluation": {
                "tau_0_9300_frozen": b2_test_tau_frozen,
                "tau_selected_val": b2_test_tau_selected,
                "logistic_regression_tau_0_9300": b2_test_logreg,
                "deterministic_breach_count": test_deterministic_breaches_b2,
                "deterministic_actual_breaches": test_deterministic_actual_breaches_b2
            }
        },
        "incremental_lift_over_stage_a": {
            "b1_vs_stage_a": {
                "delta_pr_auc": round(float(b1_test_tau_frozen['pr_auc'] - stage_a_test_metrics_tau93['pr_auc']), 4),
                "delta_roc_auc": round(float(b1_test_tau_frozen['roc_auc'] - stage_a_test_metrics_tau93['roc_auc']), 4),
                "delta_breach_recall_pct": round(float(b1_test_tau_frozen['recall_pct'] - stage_a_test_metrics_tau93['recall_pct']), 2),
                "delta_tp_breaches_captured": int(b1_test_tau_frozen['tp'] - stage_a_test_metrics_tau93['tp']),
                "delta_precision_pct": round(float(b1_test_tau_frozen['precision_pct'] - stage_a_test_metrics_tau93['precision_pct']), 2)
            },
            "b2_vs_stage_a": {
                "delta_pr_auc": round(float(b2_test_tau_frozen['pr_auc'] - stage_a_test_metrics_tau93['pr_auc']), 4),
                "delta_roc_auc": round(float(b2_test_tau_frozen['roc_auc'] - stage_a_test_metrics_tau93['roc_auc']), 4),
                "delta_breach_recall_pct": round(float(b2_test_tau_frozen['recall_pct'] - stage_a_test_metrics_tau93['recall_pct']), 2),
                "delta_tp_breaches_captured": int(b2_test_tau_frozen['tp'] - stage_a_test_metrics_tau93['tp']),
                "delta_precision_pct": round(float(b2_test_tau_frozen['precision_pct'] - stage_a_test_metrics_tau93['precision_pct']), 2)
            }
        }
    }
    
    with open(METRICS_OUT, 'w', encoding='utf-8') as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved evaluation metrics to: {METRICS_OUT}")
    
    # Save Stage B Configuration JSON
    config_payload = {
        "stage": "Stage B (Dynamic In-Fulfillment SLA Risk Tracking)",
        "governance_status": "EVALUATED_PROTOTYPE_FROZEN",
        "cohort_definition": "orders.status IN ('Delivered_On_Time', 'Delivered_Late') WITH full picking and delivery telemetry (N = 24,369)",
        "split_dates": {
            "train": "2026-09-01 to 2026-09-21 (N = 17,031)",
            "val": "2026-09-22 to 2026-09-25 (N = 3,243)",
            "test": "2026-09-26 to 2026-09-30 (N = 4,095)"
        },
        "target_definition": {
            "name": "sla_breached",
            "type": "binary classification",
            "ground_truth_rule": "1 if actual_delivery_time > promised_time else 0 (canonical from orders.csv)"
        },
        "checkpoints": {
            "B1_PICK_END": {
                "checkpoint_event": "picking.pick_end",
                "features": b1_all_features,
                "primary_model": "LightGBMClassifier",
                "linear_reference": "LogisticRegression",
                "operating_threshold": float(b1_chosen_t),
                "model_artifact": "model_artifacts/stage_b1_lightgbm.joblib",
                "preprocessor_artifact": "model_artifacts/stage_b1_ordinal_encoder.joblib",
                "linear_reference_model_artifact": "model_artifacts/stage_b1_logistic.joblib",
                "linear_reference_preprocessor_artifact": "model_artifacts/stage_b1_linear_preprocessor.joblib"
            },
            "B2_DISPATCH_PROXY": {
                "checkpoint_event": "max(picking.pick_end, delivery.pickup_time)",
                "features": b2_all_features,
                "primary_model": "LightGBMClassifier (Hybrid Deterministic)",
                "deterministic_rule": "Orders with remaining_sla_budget_b2_min <= 0 are classified deterministically as P(breach) = 1.0",
                "linear_reference": "LogisticRegression",
                "operating_threshold": float(b2_chosen_t),
                "model_artifact": "model_artifacts/stage_b2_lightgbm.joblib",
                "preprocessor_artifact": "model_artifacts/stage_b2_ordinal_encoder.joblib",
                "linear_reference_model_artifact": "model_artifacts/stage_b2_logistic.joblib",
                "linear_reference_preprocessor_artifact": "model_artifacts/stage_b2_linear_preprocessor.joblib"
            }
        },
        "telemetry_limitations": "Applicable exclusively to orders with dark store picking and delivery records (25.01% of total orders). 74.99% of orders lack granular fulfillment events and remain governed by Stage A checkout predictions."
    }
    
    with open(CONFIG_OUT, 'w', encoding='utf-8') as f:
        json.dump(config_payload, f, indent=2)
    print(f"Saved Stage B configuration to: {CONFIG_OUT}")
    print("\nStage B Model Training Pipeline Complete!")

if __name__ == "__main__":
    run_stage_b_training()
