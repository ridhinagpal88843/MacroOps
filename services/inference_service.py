"""
MacroOps AI — Production Inference Service
=========================================
Unified multi-stage risk scoring engine for:
  - Stage A (Order Checkout / T0)
  - Stage B1 (Post-Picking / T1 = picking.pick_end)
  - Stage B2 (Post-Dispatch Proxy / T2 = max(pick_end, pickup_time))

Strict ML Engineering & Governance Guarantees:
  1. Models and encoders are loaded once into memory (singleton pattern).
  2. Zero retraining, zero modifications to saved model binaries.
  3. Strict feature ordering, explicit categorical handling ('MISSING' fill + OrdinalEncoder).
  4. Hybrid deterministic rule at B2 is isolated and labeled separately from tree probabilities.
  5. Leakage protection: post-outcome fields (actual_delivery_time, sla_breached, delivery_delay_minutes)
     are strictly prevented from entering feature matrices.
  6. Dispatch proxy is documented as an effective synchronization point, never physical departure.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Tuple


class InferenceService:
    """Singleton inference service managing Stage A, B1, and B2 models."""

    WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ARTIFACTS_DIR = os.path.join(WORKSPACE_DIR, "model_artifacts")

    # Frozen Operational Decision Thresholds
    STAGE_A_THRESHOLD = 0.9300
    STAGE_B1_THRESHOLD = 0.9300
    STAGE_B2_THRESHOLD = 0.9300

    # Leakage blacklist: forbidden in feature inputs
    OUTCOME_BLACKLIST = {
        "actual_delivery_time",
        "delivery_time",
        "sla_breached",
        "delivery_delay_minutes",
        "actual_duration_minutes",
        "order_outcome"
    }

    def __init__(self, artifacts_dir: Optional[str] = None):
        """Initialize the inference service and load all model/preprocessor binaries."""
        self.artifacts_dir = os.path.abspath(artifacts_dir or self.ARTIFACTS_DIR)
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load all saved Stage A, B1, and B2 models and encoders once."""
        try:
            # 1. Stage A
            self.model_a = joblib.load(os.path.join(self.artifacts_dir, "lightgbm_classifier.joblib"))
            self.encoder_a = joblib.load(os.path.join(self.artifacts_dir, "lgb_ordinal_encoder.joblib"))
            self.features_a = list(self.model_a.feature_name_)
            self.cats_a = ["store_id", "order_hour", "day_of_week"]

            # 2. Stage B1
            self.model_b1 = joblib.load(os.path.join(self.artifacts_dir, "stage_b1_lightgbm.joblib"))
            self.encoder_b1 = joblib.load(os.path.join(self.artifacts_dir, "stage_b1_ordinal_encoder.joblib"))
            self.features_b1 = list(self.model_b1.feature_name_)
            self.cats_b1 = ["store_id", "order_hour", "day_of_week", "picker_id", "rider_id_at_b1"]

            # 3. Stage B2
            self.model_b2 = joblib.load(os.path.join(self.artifacts_dir, "stage_b2_lightgbm.joblib"))
            self.encoder_b2 = joblib.load(os.path.join(self.artifacts_dir, "stage_b2_ordinal_encoder.joblib"))
            self.features_b2 = list(self.model_b2.feature_name_)
            self.cats_b2 = ["store_id", "order_hour", "day_of_week", "picker_id", "rider_id"]

            self.models_loaded = True
        except Exception as e:
            self.models_loaded = False
            raise RuntimeError(f"Critical error loading model artifacts from {self.artifacts_dir}: {e}")

    # -------------------------------------------------------------------------
    # Preprocessing Helpers
    # -------------------------------------------------------------------------
    def _sanitize_features(self, df: pd.DataFrame, expected_features: List[str]) -> pd.DataFrame:
        """Check for and remove any outcome leakage columns before inference."""
        for forbidden in self.OUTCOME_BLACKLIST:
            if forbidden in df.columns:
                df = df.drop(columns=[forbidden])
        
        missing = [f for f in expected_features if f not in df.columns]
        if missing:
            raise ValueError(f"Missing required input features for inference: {missing}")

        return df[expected_features].copy()

    # -------------------------------------------------------------------------
    # Batch Scoring Methods
    # -------------------------------------------------------------------------
    def predict_stage_a(self, df: pd.DataFrame) -> np.ndarray:
        """
        Compute Stage A SLA breach risk probabilities for order checkout.

        Args:
            df: DataFrame containing the 7 Stage A features.
        Returns:
            np.ndarray of risk probabilities [0.0, 1.0].
        """
        X = self._sanitize_features(df, self.features_a)
        
        # Apply fitted OrdinalEncoder strictly on the 3 categoricals
        X[self.cats_a] = self.encoder_a.transform(X[self.cats_a])
        return self.model_a.predict_proba(X)[:, 1]

    def predict_stage_b1(self, df: pd.DataFrame) -> np.ndarray:
        """
        Compute Stage B1 SLA breach risk probabilities post-picking (pick_end).

        Args:
            df: DataFrame containing the 23 Stage B1 features.
        Returns:
            np.ndarray of risk probabilities [0.0, 1.0].
        """
        X = self._sanitize_features(df, self.features_b1)

        # Handle missing string categoricals identically to training pipeline
        for c in self.cats_b1:
            X[c] = X[c].fillna("MISSING").astype(str)

        X[self.cats_b1] = self.encoder_b1.transform(X[self.cats_b1])
        return self.model_b1.predict_proba(X)[:, 1]

    def predict_stage_b2(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Stage B2 SLA breach risk probabilities post-dispatch proxy
        (T2 = max(pick_end, pickup_time)) with hybrid deterministic clock override.

        Args:
            df: DataFrame containing the 27 Stage B2 features.
        Returns:
            Tuple of:
              - final_probabilities (np.ndarray): combined probabilities
              - raw_model_probabilities (np.ndarray): pure tree probabilities
              - deterministic_mask (np.ndarray): boolean flags where override was applied
        """
        X = self._sanitize_features(df, self.features_b2)

        # Identify deterministic overdue condition prior to encoding
        # (orders that have already consumed 100% of SLA budget before dispatch)
        is_overdue = np.zeros(len(df), dtype=bool)
        if "is_past_promise_at_b2" in df.columns:
            is_overdue = is_overdue | (df["is_past_promise_at_b2"].values == 1)
        if "remaining_sla_budget_b2_min" in df.columns:
            is_overdue = is_overdue | (df["remaining_sla_budget_b2_min"].values <= 0.0)

        # Handle missing string categoricals identically to training pipeline
        for c in self.cats_b2:
            X[c] = X[c].fillna("MISSING").astype(str)

        X[self.cats_b2] = self.encoder_b2.transform(X[self.cats_b2])
        raw_probs = self.model_b2.predict_proba(X)[:, 1]

        # Apply hybrid deterministic override: overdue orders receive P=1.0
        final_probs = np.where(is_overdue, 1.0, raw_probs)

        return final_probs, raw_probs, is_overdue

    # -------------------------------------------------------------------------
    # Single-Order Scoring & Multi-Stage Progression
    # -------------------------------------------------------------------------
    def score_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate full lifecycle risk progression for an individual order across
        all eligible fulfillment checkpoints.

        Args:
            order_data: Dictionary of order attributes and milestones.
        Returns:
            Structured risk assessment across Stage A, B1, and B2.
        """
        results: Dict[str, Any] = {
            "order_id": order_data.get("order_id", "UNKNOWN"),
            "checkpoints": {}
        }

        # -------------------------------------------------------------
        # 1. Stage A: Checkout Point (T0)
        # -------------------------------------------------------------
        has_stage_a = all(f in order_data for f in ["item_count", "order_value", "promised_duration_minutes", "store_id", "order_hour", "day_of_week"])
        if has_stage_a:
            try:
                row_a = {
                    "item_count": int(order_data["item_count"]),
                    "order_value": float(order_data["order_value"]),
                    "promised_duration_minutes": float(order_data["promised_duration_minutes"]),
                    "store_id": str(order_data["store_id"]),
                    "order_hour": int(order_data["order_hour"]),
                    "day_of_week": str(order_data["day_of_week"]),
                    "is_peak_rush_hour": int(order_data.get("is_peak_rush_hour", 1 if int(order_data["order_hour"]) in (12, 13, 19, 20, 21) else 0))
                }
                df_a = pd.DataFrame([row_a])
                prob_a = float(self.predict_stage_a(df_a)[0])
                alert_a = bool(prob_a >= self.STAGE_A_THRESHOLD)

                results["checkpoints"]["stage_a"] = {
                    "checkpoint_available": True,
                    "checkpoint_name": "T0: Order Checkout",
                    "checkpoint_event": "orders.order_time",
                    "checkpoint_timestamp": order_data.get("order_time"),
                    "risk_probability": round(prob_a, 4),
                    "operating_threshold": self.STAGE_A_THRESHOLD,
                    "alert_triggered": alert_a,
                    "prediction_type": "LEARNED_PROBABILITY",
                    "status_label": "CRITICAL RISK ESCALATION" if alert_a else "STANDARD FULFILLMENT"
                }
            except Exception as e:
                results["checkpoints"]["stage_a"] = {
                    "checkpoint_available": False,
                    "error": f"Failed Stage A scoring: {str(e)}"
                }
        else:
            results["checkpoints"]["stage_a"] = {
                "checkpoint_available": False,
                "reason": "Missing required checkout fields."
            }

        # -------------------------------------------------------------
        # 2. Stage B1: Post-Picking Point (T1)
        # -------------------------------------------------------------
        has_b1_telemetry = (
            ("pick_end" in order_data or "checkpoint_timestamp" in order_data)
            and all(f in order_data and order_data[f] is not None for f in ["items_picked", "pick_duration_minutes"])
        )
        if has_b1_telemetry:
            try:
                # Build B1 feature payload if available
                b1_payload = {f: order_data[f] for f in self.features_b1 if f in order_data}
                if len(b1_payload) == len(self.features_b1):
                    df_b1 = pd.DataFrame([b1_payload])
                    prob_b1 = float(self.predict_stage_b1(df_b1)[0])
                    alert_b1 = bool(prob_b1 >= self.STAGE_B1_THRESHOLD)

                    # Compute lift vs Stage A
                    prob_a_val = results["checkpoints"].get("stage_a", {}).get("risk_probability")
                    delta_b1 = round(prob_b1 - prob_a_val, 4) if prob_a_val is not None else None
                    ts_b1 = order_data.get("pick_end") or order_data.get("checkpoint_timestamp")

                    results["checkpoints"]["stage_b1"] = {
                        "checkpoint_available": True,
                        "checkpoint_name": "T1: Post-Picking",
                        "checkpoint_event": "picking.pick_end",
                        "checkpoint_timestamp": ts_b1,
                        "risk_probability": round(prob_b1, 4),
                        "operating_threshold": self.STAGE_B1_THRESHOLD,
                        "alert_triggered": alert_b1,
                        "delta_vs_stage_a": delta_b1,
                        "prediction_type": "LEARNED_PROBABILITY",
                        "status_label": "HIGH BREACH RISK" if alert_b1 else "ON TRACK POST-PICK"
                    }
                else:
                    results["checkpoints"]["stage_b1"] = {
                        "checkpoint_available": False,
                        "reason": "Incomplete B1 feature vector in input row."
                    }
            except Exception as e:
                results["checkpoints"]["stage_b1"] = {
                    "checkpoint_available": False,
                    "error": f"Failed Stage B1 scoring: {str(e)}"
                }
        else:
            results["checkpoints"]["stage_b1"] = {
                "checkpoint_available": False,
                "reason": "Picking telemetry not yet completed or not recorded."
            }

        # -------------------------------------------------------------
        # 3. Stage B2: Post-Dispatch Proxy (T2)
        # -------------------------------------------------------------
        has_b2_telemetry = (
            ("pickup_time" in order_data or "effective_dispatch_time" in order_data or "checkpoint_timestamp" in order_data)
            and ("distance_km" in order_data or "elapsed_time_to_dispatch_min" in order_data)
        )
        if has_b2_telemetry:
            try:
                b2_payload = {f: order_data[f] for f in self.features_b2 if f in order_data}
                # Map column name variations if necessary
                if "assignment_delay_min" not in b2_payload and "assignment_delay_minutes" in order_data:
                    b2_payload["assignment_delay_min"] = order_data["assignment_delay_minutes"]

                if len(b2_payload) == len(self.features_b2):
                    df_b2 = pd.DataFrame([b2_payload])
                    final_p, raw_p, is_det = self.predict_stage_b2(df_b2)
                    prob_b2 = float(final_p[0])
                    raw_prob_b2 = float(raw_p[0])
                    det_override = bool(is_det[0])
                    alert_b2 = bool(prob_b2 >= self.STAGE_B2_THRESHOLD)

                    prob_a_val = results["checkpoints"].get("stage_a", {}).get("risk_probability")
                    delta_b2 = round(prob_b2 - prob_a_val, 4) if prob_a_val is not None else None

                    dispatch_timestamp = (
                        order_data.get("effective_dispatch_time")
                        or order_data.get("checkpoint_timestamp")
                        or (max(str(order_data.get("pick_end", "")), str(order_data.get("pickup_time", ""))) if order_data.get("pick_end") and order_data.get("pickup_time") else None)
                        or order_data.get("pickup_time")
                    )

                    results["checkpoints"]["stage_b2"] = {
                        "checkpoint_available": True,
                        "checkpoint_name": "T2: Post-Dispatch Proxy",
                        "checkpoint_event": "max(picking.pick_end, delivery.pickup_time)",
                        "checkpoint_event_clarification": (
                            "Fulfillment synchronization proxy between picking completion and courier pickup. "
                            "Does not represent confirmed physical transit departure."
                        ),
                        "checkpoint_timestamp": dispatch_timestamp,
                        "risk_probability": round(prob_b2, 4),
                        "raw_model_probability": round(raw_prob_b2, 4),
                        "is_deterministic_override": det_override,
                        "prediction_type": "DETERMINISTIC_CLOCK_EXPIRY" if det_override else "LEARNED_PROBABILITY",
                        "operating_threshold": self.STAGE_B2_THRESHOLD,
                        "alert_triggered": alert_b2,
                        "delta_vs_stage_a": delta_b2,
                        "status_label": "CERTAIN BREACH (OVERDUE)" if det_override else ("HIGH TRANSIT RISK" if alert_b2 else "ON TRACK IN TRANSIT")
                    }
                else:
                    results["checkpoints"]["stage_b2"] = {
                        "checkpoint_available": False,
                        "reason": "Incomplete B2 feature vector in input row."
                    }
            except Exception as e:
                results["checkpoints"]["stage_b2"] = {
                    "checkpoint_available": False,
                    "error": f"Failed Stage B2 scoring: {str(e)}"
                }
        else:
            results["checkpoints"]["stage_b2"] = {
                "checkpoint_available": False,
                "reason": "Dispatch telemetry not yet recorded or order not in dark store telemetry cohort."
            }

        return results
