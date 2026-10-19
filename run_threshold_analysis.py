"""
MacroOps AI — Phase 2C: Stage A Threshold & Calibration Analysis
================================================================
Performs threshold tuning, probability distribution analysis, and calibration
assessment for Stage A baseline classification models on the Validation partition.

Rules & Governance:
  - Models are NOT retrained; loaded directly from model_artifacts/.
  - Validation set (Sept 22-25) is used for threshold analysis.
  - Final Test set (Sept 26-30) is evaluated ONLY on the selected candidate thresholds.
  - Outputs:
      - reports/plots/pr_curve.png
      - reports/plots/calibration_curve.png
      - reports/plots/probability_distribution.png
      - reports/plots/threshold_tradeoffs.png
      - threshold_analysis.json
      - STAGE_A_THRESHOLD_ANALYSIS.md
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
    confusion_matrix
)
from sklearn.calibration import calibration_curve

# ---------------------------------------------------------
# Paths & Settings
# ---------------------------------------------------------
WORKSPACE_DIR = r"c:\Users\HP\Desktop\MacroOps"
DATA_PATH = os.path.join(WORKSPACE_DIR, "predictive_features", "stage_a_features.csv")
ARTIFACTS_DIR = os.path.join(WORKSPACE_DIR, "model_artifacts")
PLOTS_DIR = os.path.join(WORKSPACE_DIR, "reports", "plots")
JSON_OUT_PATH = os.path.join(WORKSPACE_DIR, "threshold_analysis.json")

NUM_COLS = ["item_count", "order_value", "promised_duration_minutes"]
CAT_COLS = ["store_id", "order_hour", "day_of_week"]
BIN_COLS = ["is_peak_rush_hour"]
ALL_FEATURE_COLS = NUM_COLS + CAT_COLS + BIN_COLS
TARGET_CLS = "sla_breached"


def load_data_and_models():
    """Load dataset partitions and pre-trained model artifacts."""
    print("Loading Stage A dataset and pre-trained artifacts...")
    os.makedirs(PLOTS_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    val_mask = df["split"] == "val"
    test_mask = df["split"] == "test"

    y_val = df.loc[val_mask, TARGET_CLS].values
    y_test = df.loc[test_mask, TARGET_CLS].values

    # Load preprocessors
    lin_preprocessor = joblib.load(os.path.join(ARTIFACTS_DIR, "linear_preprocessor.joblib"))
    lgb_oe = joblib.load(os.path.join(ARTIFACTS_DIR, "lgb_ordinal_encoder.joblib"))

    # Load models
    log_reg = joblib.load(os.path.join(ARTIFACTS_DIR, "logistic_regression.joblib"))
    lgb_cls = joblib.load(os.path.join(ARTIFACTS_DIR, "lightgbm_classifier.joblib"))

    # Transform Validation
    X_val_raw = df.loc[val_mask, ALL_FEATURE_COLS]
    X_val_lin = lin_preprocessor.transform(X_val_raw)
    
    X_val_lgb = X_val_raw.copy()
    X_val_lgb[CAT_COLS] = lgb_oe.transform(X_val_raw[CAT_COLS])
    for c in CAT_COLS:
        X_val_lgb[c] = X_val_lgb[c].astype(int)

    # Transform Test
    X_test_raw = df.loc[test_mask, ALL_FEATURE_COLS]
    X_test_lin = lin_preprocessor.transform(X_test_raw)

    X_test_lgb = X_test_raw.copy()
    X_test_lgb[CAT_COLS] = lgb_oe.transform(X_test_raw[CAT_COLS])
    for c in CAT_COLS:
        X_test_lgb[c] = X_test_lgb[c].astype(int)

    # Generate probabilities for class 1 (SLA Breached)
    proba_val_log = log_reg.predict_proba(X_val_lin)[:, 1]
    proba_val_lgb = lgb_cls.predict_proba(X_val_lgb)[:, 1]

    proba_test_log = log_reg.predict_proba(X_test_lin)[:, 1]
    proba_test_lgb = lgb_cls.predict_proba(X_test_lgb)[:, 1]

    print(f"Validation size: {len(y_val):,} (Breached: {y_val.mean()*100:.2f}%)")
    print(f"Test size:       {len(y_test):,} (Breached: {y_test.mean()*100:.2f}%)")

    return {
        "y_val": y_val,
        "y_test": y_test,
        "proba_val": {"LogisticRegression": proba_val_log, "LightGBM": proba_val_lgb},
        "proba_test": {"LogisticRegression": proba_test_log, "LightGBM": proba_test_lgb}
    }


def compute_metrics_at_threshold(y_true, proba, threshold):
    """Compute detailed classification metrics at a given probability threshold."""
    # Predicted class 1 if proba >= threshold else 0
    y_pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n_total = len(y_true)

    flagged_count = int(tp + fp)
    flagged_pct = float(flagged_count / n_total)

    precision_breached = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall_breached = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1_breached = (
        float(2 * precision_breached * recall_breached / (precision_breached + recall_breached))
        if (precision_breached + recall_breached) > 0 else 0.0
    )

    on_time_precision = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
    on_time_recall = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    accuracy = float((tp + tn) / n_total)

    return {
        "threshold": round(float(threshold), 4),
        "flagged_orders": flagged_count,
        "flagged_pct": round(flagged_pct * 100, 2),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "precision_breached": round(precision_breached, 4),
        "recall_breached": round(recall_breached, 4),
        "f1_breached": round(f1_breached, 4),
        "ontime_precision": round(on_time_precision, 4),
        "ontime_recall": round(on_time_recall, 4),
        "accuracy": round(accuracy, 4)
    }


def scan_threshold_grid(y_val, proba_dict):
    """Scan thresholds across the probability spectrum for both models on Validation."""
    print("Scanning validation threshold grid...")
    thresholds = np.linspace(0.50, 0.98, 49)  # 0.50, 0.51, ..., 0.98

    grid_results = {}
    for model_name, proba in proba_dict.items():
        model_metrics = []
        for t in thresholds:
            res = compute_metrics_at_threshold(y_val, proba, t)
            model_metrics.append(res)
        grid_results[model_name] = model_metrics

    return grid_results


def generate_pr_curve_plot(y_val, proba_dict):
    """Generate and save Precision-Recall curve comparison plot."""
    print("Generating Precision-Recall curve plot...")
    plt.figure(figsize=(8, 6), dpi=300)

    base_rate = np.mean(y_val)
    plt.axhline(
        y=base_rate,
        color="gray",
        linestyle="--",
        linewidth=1.5,
        label=f"Baseline Prevalence (Prior = {base_rate:.4f})"
    )

    colors = {"LogisticRegression": "#1f77b4", "LightGBM": "#2ca02c"}
    styles = {"LogisticRegression": "-", "LightGBM": "-."}

    for model_name, proba in proba_dict.items():
        precision, recall, _ = precision_recall_curve(y_val, proba)
        pr_auc = average_precision_score(y_val, proba)
        plt.plot(
            recall,
            precision,
            label=f"{model_name} (PR-AUC = {pr_auc:.4f})",
            color=colors.get(model_name, "black"),
            linestyle=styles.get(model_name, "-"),
            linewidth=2.2
        )

    plt.title("Stage A Validation: Precision-Recall Curve Comparison\n(Target: sla_breached = 1)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Recall (SLA Breached)", fontsize=11)
    plt.ylabel("Precision (SLA Breached)", fontsize=11)
    plt.xlim([0.0, 1.02])
    plt.ylim([0.80, 1.01])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower left", fontsize=10, frameon=True)
    plt.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "pr_curve.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def generate_calibration_plot(y_val, proba_dict):
    """Generate and save Calibration Curve (Reliability Diagram) plot."""
    print("Generating Calibration Curve plot...")
    plt.figure(figsize=(8, 6), dpi=300)

    # Reference perfectly calibrated line
    plt.plot([0, 1], [0, 1], "k--", label="Perfect Calibration", linewidth=1.5)

    colors = {"LogisticRegression": "#1f77b4", "LightGBM": "#2ca02c"}
    markers = {"LogisticRegression": "o", "LightGBM": "s"}

    for model_name, proba in proba_dict.items():
        brier = brier_score_loss(y_val, proba)
        prob_true, prob_pred = calibration_curve(y_val, proba, n_bins=10, strategy="quantile")
        plt.plot(
            prob_pred,
            prob_true,
            marker=markers.get(model_name, "o"),
            color=colors.get(model_name, "black"),
            label=f"{model_name} (Brier = {brier:.4f})",
            linewidth=2.0,
            markersize=6
        )

    plt.title("Stage A Validation: Probability Calibration Curve\n(Reliability Diagram with Quantile Binning)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Mean Predicted Probability P(sla_breached = 1)", fontsize=11)
    plt.ylabel("Observed Fraction of Positives", fontsize=11)
    plt.xlim([0.65, 1.0])
    plt.ylim([0.65, 1.0])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "calibration_curve.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def generate_probability_distribution_plot(y_val, proba_dict):
    """Generate probability distributions conditioned on actual class."""
    print("Generating Probability Distribution plot...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300, sharey=True)

    bins = np.linspace(0.55, 1.0, 46)

    for idx, (model_name, proba) in enumerate(proba_dict.items()):
        ax = axes[idx]
        proba_ontime = proba[y_val == 0]
        proba_breached = proba[y_val == 1]

        ax.hist(
            proba_ontime,
            bins=bins,
            density=True,
            alpha=0.6,
            color="#2ca02c",
            label=f"Actual On-Time (N={len(proba_ontime):,})",
            edgecolor="black",
            linewidth=0.5
        )
        ax.hist(
            proba_breached,
            bins=bins,
            density=True,
            alpha=0.5,
            color="#d62728",
            label=f"Actual Breached (N={len(proba_breached):,})",
            edgecolor="black",
            linewidth=0.5
        )

        ax.axvline(np.mean(proba_ontime), color="#1b631b", linestyle="--", linewidth=1.8, label=f"On-Time Mean ({np.mean(proba_ontime):.3f})")
        ax.axvline(np.mean(proba_breached), color="#8c1213", linestyle="--", linewidth=1.8, label=f"Breach Mean ({np.mean(proba_breached):.3f})")

        ax.set_title(f"{model_name}: Predicted Probability Distribution", fontsize=11, fontweight="bold")
        ax.set_xlabel("Predicted Probability P(Breach = 1)", fontsize=10)
        ax.set_ylabel("Probability Density", fontsize=10)
        ax.set_xlim([0.60, 1.0])
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper left", fontsize=9, frameon=True)

    fig.suptitle("Stage A Validation: Conditioned Risk Score Distribution", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "probability_distribution.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def generate_threshold_tradeoff_plot(grid_results):
    """Generate plot of operational metrics vs decision threshold."""
    print("Generating Threshold Tradeoffs plot...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=300, sharey=True)

    for idx, (model_name, metrics) in enumerate(grid_results.items()):
        ax = axes[idx]
        df_grid = pd.DataFrame(metrics)

        ax.plot(df_grid["threshold"], df_grid["recall_breached"], label="Breach Recall (Class 1)", color="#d62728", linewidth=2.2)
        ax.plot(df_grid["threshold"], df_grid["ontime_recall"], label="On-Time Recall (Class 0)", color="#2ca02c", linewidth=2.2)
        ax.plot(df_grid["threshold"], df_grid["precision_breached"], label="Breach Precision", color="#ff7f0e", linestyle="--", linewidth=1.8)
        ax.plot(df_grid["threshold"], df_grid["ontime_precision"], label="On-Time Precision", color="#17becf", linestyle="--", linewidth=1.8)
        ax.plot(df_grid["threshold"], df_grid["flagged_pct"] / 100.0, label="Flagged Orders Fraction", color="#7f7f7f", linestyle=":", linewidth=2.0)

        # Reference lines
        ax.axvline(0.8922, color="purple", linestyle=":", linewidth=1.2, label="Base Prevalence (0.8922)")

        ax.set_title(f"{model_name}: Metric Tradeoffs vs Threshold", fontsize=11, fontweight="bold")
        ax.set_xlabel("Decision Threshold (tau)", fontsize=10)
        ax.set_ylabel("Metric Value / Fraction", fontsize=10)
        ax.set_xlim([0.70, 0.98])
        ax.set_ylim([0.0, 1.02])
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="center left", fontsize=8.5, frameon=True)

    fig.suptitle("Stage A Validation: Operational Tradeoffs Across Decision Thresholds", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    out_path = os.path.join(PLOTS_DIR, "threshold_tradeoffs.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def evaluate_candidate_thresholds(y_val, y_test, proba_val_dict, proba_test_dict):
    """
    Define 4 operationally meaningful candidate thresholds derived from Validation,
    and evaluate them on both Validation and final Holdout Test.
    """
    print("\nEvaluating Candidate Thresholds on Validation and Holdout Test...")

    # Candidate definitions based on operational use cases:
    # 1. Default Baseline (tau = 0.50): Conventional classification reference
    # 2. Balanced Prevalence Center (tau = 0.8922): Centered around background breach rate
    # 3. High-Recall On-Time Filter / Fast-Track (tau = 0.8600): Maximizes identification of On-Time orders
    # 4. High-Precision Escalation / Dispatch Alert (tau = 0.9300): Flags high-confidence breach risk (~25-30% volume)
    candidates = [
        {
            "id": "cand_default_50",
            "name": "Default Binary Reference",
            "threshold": 0.50,
            "operational_intent": "Traditional machine learning default baseline (tau = 0.50). Evaluates performance without domain calibration.",
            "operational_tradeoff": "Flags 100% of orders as breached. Captures all breaches (100% recall), but achieves 0% on-time discrimination."
        },
        {
            "id": "cand_prevalence_89",
            "name": "Base-Rate Centered Policy",
            "threshold": 0.8922,
            "operational_intent": "Aligns threshold with the empirical validation breach base rate (89.22%). Separates above-average from below-average risk.",
            "operational_tradeoff": "Flags ~60-65% of orders. Recalls ~68-70% of breaches while capturing ~40-42% of on-time orders."
        },
        {
            "id": "cand_ontime_filter_86",
            "name": "On-Time Fast-Track / Low-Risk Filter",
            "threshold": 0.8600,
            "operational_intent": "Prioritizes identifying genuinely on-time orders (P(breach) < 0.86) to route to expedited or low-touch workflows.",
            "operational_tradeoff": "Requires high breach recall (>85%) while achieving meaningful on-time recall (~22-25%). High breach flagging rate (~85%)."
        },
        {
            "id": "cand_escalation_93",
            "name": "Targeted High-Risk Escalation Alert",
            "threshold": 0.9300,
            "operational_intent": "Actionable intervention tier. Flags only high-confidence breaches so dark store supervisors and dispatchers are not alert-fatigued.",
            "operational_tradeoff": "Flags ~23-28% of highest-risk volume with ~95% breach precision. Trades off breach recall (~26-30%) for high actionability."
        }
    ]

    candidate_results = []
    for cand in candidates:
        t = cand["threshold"]
        cand_entry = {
            "id": cand["id"],
            "name": cand["name"],
            "threshold": t,
            "operational_intent": cand["operational_intent"],
            "operational_tradeoff": cand["operational_tradeoff"],
            "validation_metrics": {},
            "test_metrics": {}
        }

        for model_name in ["LogisticRegression", "LightGBM"]:
            val_metrics = compute_metrics_at_threshold(y_val, proba_val_dict[model_name], t)
            test_metrics = compute_metrics_at_threshold(y_test, proba_test_dict[model_name], t)

            cand_entry["validation_metrics"][model_name] = val_metrics
            cand_entry["test_metrics"][model_name] = test_metrics

        candidate_results.append(cand_entry)

    return candidate_results


def run():
    # 1. Load data and models
    data = load_and_validate = load_data_and_models()
    y_val = data["y_val"]
    y_test = data["y_test"]
    proba_val = data["proba_val"]
    proba_test = data["proba_test"]

    # 2. Probability summary stats
    prob_summary = {}
    for model_name, proba in proba_val.items():
        brier = float(brier_score_loss(y_val, proba))
        pr_auc = float(average_precision_score(y_val, proba))
        roc_auc = float(roc_auc_score(y_val, proba))
        prob_summary[model_name] = {
            "validation_brier_score": round(brier, 4),
            "validation_pr_auc": round(pr_auc, 4),
            "validation_roc_auc": round(roc_auc, 4),
            "distribution": {
                "min": round(float(np.min(proba)), 4),
                "p10": round(float(np.percentile(proba, 10)), 4),
                "p25": round(float(np.percentile(proba, 25)), 4),
                "median": round(float(np.median(proba)), 4),
                "mean": round(float(np.mean(proba)), 4),
                "p75": round(float(np.percentile(proba, 75)), 4),
                "p90": round(float(np.percentile(proba, 90)), 4),
                "max": round(float(np.max(proba)), 4),
                "std": round(float(np.std(proba)), 4)
            }
        }

    # 3. Scan validation grid
    grid_results = scan_threshold_grid(y_val, proba_val)

    # 4. Generate plots
    generate_pr_curve_plot(y_val, proba_val)
    generate_calibration_plot(y_val, proba_val)
    generate_probability_distribution_plot(y_val, proba_val)
    generate_threshold_tradeoff_plot(grid_results)

    # 5. Candidate Threshold Evaluations (Validation + Test)
    candidate_results = evaluate_candidate_thresholds(y_val, y_test, proba_val, proba_test)

    # 6. Save JSON output
    output_payload = {
        "analysis_name": "Stage A Classification Threshold and Calibration Analysis (Phase 2C)",
        "synthetic_data_disclaimer": "All models, thresholds, and metrics represent prototype performance on synthetic data.",
        "sample_sizes": {
            "validation": len(y_val),
            "test": len(y_test)
        },
        "base_rates": {
            "validation_breached_pct": round(float(y_val.mean() * 100), 2),
            "test_breached_pct": round(float(y_test.mean() * 100), 2)
        },
        "model_probability_summaries": prob_summary,
        "candidate_thresholds": candidate_results,
        "validation_threshold_grid_sample": {
            "LogisticRegression": [row for row in grid_results["LogisticRegression"] if int(round(row["threshold"] * 100)) % 2 == 0],
            "LightGBM": [row for row in grid_results["LightGBM"] if int(round(row["threshold"] * 100)) % 2 == 0]
        }
    }

    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\nAll outputs successfully generated and saved:")
    print(f"  - JSON Report: {JSON_OUT_PATH}")
    for p in os.listdir(PLOTS_DIR):
        print(f"  - Plot: reports/plots/{p}")


if __name__ == "__main__":
    run()
