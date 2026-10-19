"""
MacroOps AI — Production Web Application & Core REST API
=======================================================
RESTful backend exposing operational KPI summaries, store analytics,
paginated order lifecycle milestones, and multi-stage risk scoring (Stage A, B1, B2).

Strict Engineering & Governance Guarantees:
  1. Read-only database access via DataService (SQLite URI mode=ro).
  2. Single-load inference engine via InferenceService (zero retraining, frozen threshold 0.9300).
  3. Safe parameter validation, strict column whitelisting, and bounded pagination.
  4. Zero leakage: post-outcome fields never enter prediction feature vectors.
  5. Deterministic B2 overdue rule isolated from learned tree probabilities.
  6. Dispatch proxy explicitly identified as a fulfillment synchronization proxy, not physical departure.
  7. Safe error responses: stack traces and sensitive local filesystem paths are never returned to clients.
  8. Synthetic data disclaimer attached to API responses.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request, Response, render_template
import pandas as pd

# Add workspace directory to path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from services.data_service import DataService
from services.inference_service import InferenceService
from services.assistant_service import AssistantService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger("macroops_api")

# -----------------------------------------------------------------------------
# APPLICATION FACTORY & SERVICE INITIALIZATION
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Global singletons
DATA_SERVICE: Optional[DataService] = None
INFERENCE_SERVICE: Optional[InferenceService] = None
ASSISTANT_SERVICE: Optional[AssistantService] = None
FEATURE_CACHE: Dict[str, pd.DataFrame] = {}

SERVICE_STATUS = {
    "data_service": False,
    "inference_service": False,
    "assistant_service": False,
    "feature_cache": False,
    "init_error": None
}

SYNTHETIC_DATA_DISCLAIMER = (
    "All data, models, and metrics represent an analytical prototype on synthetic "
    "quick-commerce operational datasets. Not approved for autonomous physical execution."
)

try:
    logger.info("Initializing DataService...")
    DATA_SERVICE = DataService()
    SERVICE_STATUS["data_service"] = True

    logger.info("Initializing InferenceService and loading frozen models...")
    INFERENCE_SERVICE = InferenceService()
    SERVICE_STATUS["inference_service"] = True

    logger.info("Initializing AssistantService...")
    ASSISTANT_SERVICE = AssistantService(DATA_SERVICE, INFERENCE_SERVICE)
    SERVICE_STATUS["assistant_service"] = True

    logger.info("Indexing point-in-time feature tables for sub-millisecond scoring...")
    pred_dir = os.path.join(WORKSPACE_DIR, "predictive_features")
    b1_path = os.path.join(pred_dir, "stage_b1_features.csv")
    b2_path = os.path.join(pred_dir, "stage_b2_features.csv")

    if os.path.exists(b1_path):
        FEATURE_CACHE["b1"] = pd.read_csv(b1_path).set_index("order_id")
    if os.path.exists(b2_path):
        FEATURE_CACHE["b2"] = pd.read_csv(b2_path).set_index("order_id")

    SERVICE_STATUS["feature_cache"] = True
    logger.info("Services and feature indexes initialized successfully.")
except Exception as e:
    logger.critical(f"Service initialization error: {e}")
    SERVICE_STATUS["init_error"] = str(e)


# -----------------------------------------------------------------------------
# GLOBAL ERROR HANDLERS (Safe error reporting, zero stack traces/paths exposed)
# -----------------------------------------------------------------------------
@app.errorhandler(400)
def handle_bad_request(e) -> Response:
    return jsonify({
        "error": "Bad Request",
        "message": str(e.description if hasattr(e, 'description') else "Invalid request parameters."),
        "status_code": 400
    }), 400


@app.errorhandler(404)
def handle_not_found(e) -> Response:
    return jsonify({
        "error": "Not Found",
        "message": str(e.description if hasattr(e, 'description') else "Requested resource was not found."),
        "status_code": 404
    }), 404


@app.errorhandler(405)
def handle_method_not_allowed(e) -> Response:
    return jsonify({
        "error": "Method Not Allowed",
        "message": "The HTTP method is not supported for this endpoint.",
        "status_code": 405
    }), 405


@app.errorhandler(500)
def handle_internal_error(e) -> Response:
    logger.error(f"Internal 500 error: {e}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal operational error occurred while processing the request.",
        "status_code": 500
    }), 500


@app.route("/", methods=["GET"])
def index() -> Response:
    """Serve the animated Operations Command Centre frontend."""
    return render_template("index.html")


# -----------------------------------------------------------------------------
# 1. GET /api/health
# -----------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check() -> Response:
    """
    Application health and service status endpoint.
    Reports operational state of database and ML models without exposing local paths.
    """
    is_healthy = SERVICE_STATUS["data_service"] and SERVICE_STATUS["inference_service"]
    status_str = "healthy" if is_healthy else "degraded"

    db_info: Dict[str, Any] = {"connected": False, "mode": "read_only"}
    if DATA_SERVICE:
        try:
            with DATA_SERVICE.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM raw_orders")
                total_orders = int(cur.fetchone()[0])
                db_info.update({
                    "connected": True,
                    "orders_recorded": total_orders,
                    "database_file": "macroops_analytics.db"
                })
        except Exception as e:
            db_info["error"] = "Database connection check failed"

    model_info: Dict[str, Any] = {"loaded": False}
    if INFERENCE_SERVICE and INFERENCE_SERVICE.models_loaded:
        model_info = {
            "loaded": True,
            "stage_a": {
                "model": "LightGBMClassifier",
                "features_count": len(INFERENCE_SERVICE.features_a),
                "threshold": INFERENCE_SERVICE.STAGE_A_THRESHOLD
            },
            "stage_b1": {
                "model": "LightGBMClassifier",
                "features_count": len(INFERENCE_SERVICE.features_b1),
                "threshold": INFERENCE_SERVICE.STAGE_B1_THRESHOLD
            },
            "stage_b2": {
                "model": "LightGBMClassifier (Hybrid Deterministic)",
                "features_count": len(INFERENCE_SERVICE.features_b2),
                "threshold": INFERENCE_SERVICE.STAGE_B2_THRESHOLD,
                "deterministic_rule": "remaining_sla_budget_b2_min <= 0 -> P(breach)=1.0"
            }
        }

    status_code = 200 if is_healthy else 503
    return jsonify({
        "status": status_str,
        "service_layer": {
            "data_service": SERVICE_STATUS["data_service"],
            "inference_service": SERVICE_STATUS["inference_service"],
            "assistant_service": SERVICE_STATUS["assistant_service"],
            "feature_cache": SERVICE_STATUS["feature_cache"]
        },
        "database": db_info,
        "models": model_info,
        "synthetic_data_disclaimer": SYNTHETIC_DATA_DISCLAIMER
    }), status_code


# -----------------------------------------------------------------------------
# 2. GET /api/kpis
# -----------------------------------------------------------------------------
@app.route("/api/kpis", methods=["GET"])
def get_kpis() -> Response:
    """
    Retrieve standardized operational KPIs across volume, SLA compliance,
    dark store picking, last-mile transit, and inventory accuracy.
    """
    if not DATA_SERVICE:
        return jsonify({"error": "Service Unavailable", "message": "Data service uninitialized"}), 503

    try:
        kpi_payload = DATA_SERVICE.get_global_kpis()
        kpi_payload["synthetic_data_disclaimer"] = SYNTHETIC_DATA_DISCLAIMER
        return jsonify(kpi_payload), 200
    except Exception as e:
        logger.error(f"Error fetching global KPIs: {e}")
        return jsonify({"error": "Failed to compute KPIs", "message": "Analytical query failure"}), 500


# -----------------------------------------------------------------------------
# 3. GET /api/stores
# -----------------------------------------------------------------------------
@app.route("/api/stores", methods=["GET"])
def get_stores() -> Response:
    """
    Retrieve store-level operational metrics across all 100 dark stores.
    Supports parameterized sorting and limits; prevents SQL injection via whitelisting.

    Query Parameters:
      - sort_by: Column to sort by (default: 'total_orders')
      - order: Sort direction ('desc' or 'asc', default: 'desc')
      - limit: Maximum number of stores to return (1-100, default: 100)
      - store_id: Optional exact store lookup (e.g., 'ST001')
    """
    if not DATA_SERVICE:
        return jsonify({"error": "Service Unavailable", "message": "Data service uninitialized"}), 503

    # Check for single store detail request
    store_id_param = request.args.get("store_id")
    if store_id_param:
        store_detail = DATA_SERVICE.get_store_detail(store_id_param.strip().upper())
        if not store_detail:
            return jsonify({
                "error": "Store Not Found",
                "store_id": store_id_param.strip().upper(),
                "message": f"Store ID '{store_id_param}' was not found in the 100-store network."
            }), 404
        return jsonify({"store": store_detail}), 200

    # Parse and validate sort parameters
    sort_by = request.args.get("sort_by", "total_orders").strip().lower()
    order_param = request.args.get("order", "desc").strip().lower()

    if order_param not in ("asc", "desc"):
        return jsonify({
            "error": "Bad Request",
            "message": f"Invalid order parameter '{order_param}'. Allowed values are 'asc' or 'desc'."
        }), 400

    # Parse and validate limit parameter
    limit_raw = request.args.get("limit", "100")
    try:
        limit_val = int(limit_raw)
        if limit_val < 1 or limit_val > 100:
            return jsonify({
                "error": "Bad Request",
                "message": "Limit must be an integer between 1 and 100."
            }), 400
    except ValueError:
        return jsonify({
            "error": "Bad Request",
            "message": f"Invalid limit '{limit_raw}'. Expected an integer between 1 and 100."
        }), 400

    allowed_sort_columns = [
        "store_id", "total_orders", "on_time_orders", "late_orders",
        "cancelled_orders", "failed_orders", "on_time_delivery_rate_pct",
        "sla_breach_rate_pct", "avg_delivery_delay_min", "total_revenue",
        "active_skus", "avg_inventory_accuracy", "total_physical_units",
        "physical_stockout_count", "total_workforce_shifts", "total_completed_tasks",
        "total_pending_tasks", "avg_task_completion_rate_pct"
    ]

    if sort_by not in allowed_sort_columns:
        return jsonify({
            "error": "Bad Request",
            "message": f"Invalid sort_by column '{sort_by}'. Allowed columns: {allowed_sort_columns}"
        }), 400

    try:
        ascending = (order_param == "asc")
        stores = DATA_SERVICE.get_store_summaries(sort_by=sort_by, ascending=ascending, limit=limit_val)
        return jsonify({
            "stores": stores,
            "count": len(stores),
            "sorted_by": sort_by,
            "order": order_param,
            "synthetic_data_disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }), 200
    except Exception as e:
        logger.error(f"Error fetching store summaries: {e}")
        return jsonify({"error": "Failed to fetch stores", "message": "Database query failure"}), 500


# -----------------------------------------------------------------------------
# 4. GET /api/orders
# -----------------------------------------------------------------------------
@app.route("/api/orders", methods=["GET"])
def get_orders() -> Response:
    """
    Retrieve paginated order records with joined picking and delivery milestones.
    Attaches lightweight Stage A risk indicators strictly to the requested page slice
    without re-scoring the entire 100,000-order database.

    Query Parameters:
      - page: 1-indexed page number (default: 1)
      - page_size: Orders per page (1-100, default: 50)
      - store_id: Filter by dark store ID (e.g., 'ST001')
      - status: Filter by order status (e.g., 'Delivered_Late')
      - has_telemetry: Filter by telemetry availability ('true' or 'false')
      - search: Search order ID substring
    """
    if not DATA_SERVICE:
        return jsonify({"error": "Service Unavailable", "message": "Data service uninitialized"}), 503

    # Parse and validate pagination
    page_raw = request.args.get("page", "1")
    page_size_raw = request.args.get("page_size", "50")

    try:
        page = int(page_raw)
        if page < 1:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Bad Request", "message": "Page must be a positive integer >= 1."}), 400

    try:
        page_size = int(page_size_raw)
        if page_size < 1 or page_size > 100:
            raise ValueError()
    except ValueError:
        return jsonify({"error": "Bad Request", "message": "Page size must be an integer between 1 and 100."}), 400

    # Parse optional filters
    store_id = request.args.get("store_id")
    if store_id:
        store_id = store_id.strip().upper()

    status = request.args.get("status")
    if status:
        status = status.strip()
        allowed_statuses = ["Delivered_On_Time", "Delivered_Late", "Cancelled", "Failed"]
        if status not in allowed_statuses:
            return jsonify({
                "error": "Bad Request",
                "message": f"Invalid status '{status}'. Allowed statuses: {allowed_statuses}"
            }), 400

    has_telemetry_raw = request.args.get("has_telemetry")
    has_telemetry = None
    if has_telemetry_raw is not None:
        val = has_telemetry_raw.strip().lower()
        if val in ("true", "1", "yes"):
            has_telemetry = True
        elif val in ("false", "0", "no"):
            has_telemetry = False
        else:
            return jsonify({
                "error": "Bad Request",
                "message": "has_telemetry must be a boolean ('true' or 'false')."
            }), 400

    search = request.args.get("search")
    if search:
        search = search.strip()

    try:
        order_page = DATA_SERVICE.get_orders(
            page=page,
            page_size=page_size,
            store_id=store_id,
            status=status,
            has_telemetry=has_telemetry,
            search_order_id=search
        )

        # Attach lightweight Stage A checkout risk indicator for the page slice
        orders = order_page.get("orders", [])
        if INFERENCE_SERVICE and INFERENCE_SERVICE.models_loaded and orders:
            try:
                # Prepare Stage A feature dataframe for this page slice
                slice_records = []
                valid_indices = []
                for idx, ord_dict in enumerate(orders):
                    if all(k in ord_dict and ord_dict[k] is not None for k in ["item_count", "order_value", "promised_duration_minutes", "store_id", "order_hour", "day_of_week"]):
                        slice_records.append({
                            "item_count": int(ord_dict["item_count"]),
                            "order_value": float(ord_dict["order_value"]),
                            "promised_duration_minutes": float(ord_dict["promised_duration_minutes"]),
                            "store_id": str(ord_dict["store_id"]),
                            "order_hour": int(ord_dict["order_hour"]),
                            "day_of_week": str(ord_dict["day_of_week"]),
                            "is_peak_rush_hour": 1 if int(ord_dict["order_hour"]) in (12, 13, 19, 20, 21) else 0
                        })
                        valid_indices.append(idx)

                if slice_records:
                    df_slice = pd.DataFrame(slice_records)
                    probs_slice = INFERENCE_SERVICE.predict_stage_a(df_slice)
                    for i, real_idx in enumerate(valid_indices):
                        prob_val = float(probs_slice[i])
                        orders[real_idx]["stage_a_risk_score"] = round(prob_val, 4)
                        orders[real_idx]["stage_a_alert"] = bool(prob_val >= INFERENCE_SERVICE.STAGE_A_THRESHOLD)
            except Exception as scoring_err:
                logger.warning(f"Could not compute Stage A indicators for order slice: {scoring_err}")

        return jsonify({
            "orders": orders,
            "pagination": order_page.get("pagination", {}),
            "filters_applied": {
                "store_id": store_id,
                "status": status,
                "has_telemetry": has_telemetry,
                "search": search
            },
            "synthetic_data_disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }), 200

    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return jsonify({"error": "Failed to fetch orders", "message": "Database query failure"}), 500


# -----------------------------------------------------------------------------
# 5. GET /api/order/<order_id>
# -----------------------------------------------------------------------------
@app.route("/api/order/<order_id>", methods=["GET"])
def get_order_detail(order_id: str) -> Response:
    """
    Retrieve full lifecycle milestones and multi-stage risk assessment for an individual order.

    Governance Rules Enforced:
      1. Stage A checkout risk is evaluated for all completed orders.
      2. Stage B1 risk is evaluated ONLY if picking telemetry exists; else explicitly marked unavailable.
      3. Stage B2 risk is evaluated ONLY if dispatch proxy telemetry exists; else explicitly marked unavailable.
      4. B2 deterministic overdue override (remaining SLA budget <= 0) is isolated from tree probabilities.
      5. B2 dispatch proxy is explicitly identified as an effective fulfillment synchronization point,
         not confirmed physical courier transit departure.
      6. Post-delivery outcomes are strictly prevented from entering feature vectors.
    """
    if not DATA_SERVICE:
        return jsonify({"error": "Service Unavailable", "message": "Data service uninitialized"}), 503

    clean_order_id = order_id.strip()

    try:
        # Retrieve lifecycle from DataService
        lifecycle = DATA_SERVICE.get_order_lifecycle(clean_order_id)
        if not lifecycle:
            return jsonify({
                "error": "Order Not Found",
                "order_id": clean_order_id,
                "message": f"Order ID '{clean_order_id}' was not found in the orders database."
            }), 404

        # Merge with cached feature stores if present
        order_payload = dict(lifecycle)

        if "b1" in FEATURE_CACHE and clean_order_id in FEATURE_CACHE["b1"].index:
            b1_features = FEATURE_CACHE["b1"].loc[clean_order_id].to_dict()
            order_payload.update(b1_features)

        if "b2" in FEATURE_CACHE and clean_order_id in FEATURE_CACHE["b2"].index:
            b2_features = FEATURE_CACHE["b2"].loc[clean_order_id].to_dict()
            order_payload.update(b2_features)

        # Run multi-stage scoring
        risk_assessment: Dict[str, Any] = {}
        if INFERENCE_SERVICE and INFERENCE_SERVICE.models_loaded:
            risk_assessment = INFERENCE_SERVICE.score_order(order_payload)

        return jsonify({
            "order_id": clean_order_id,
            "lifecycle_milestones": lifecycle,
            "risk_assessment": risk_assessment.get("checkpoints", {}),
            "governance_and_coverage": {
                "has_stage_b_telemetry": lifecycle.get("has_stage_b_telemetry", False),
                "telemetry_note": lifecycle.get("telemetry_coverage_note", ""),
                "dispatch_proxy_clarification": (
                    "Checkpoint B2 represents max(pick_end, pickup_time), serving as an effective "
                    "operational synchronization milestone. It does not represent confirmed physical departure."
                ),
                "frozen_decision_threshold": INFERENCE_SERVICE.STAGE_A_THRESHOLD if INFERENCE_SERVICE else 0.9300
            },
            "synthetic_data_disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }), 200

    except Exception as e:
        logger.error(f"Error fetching order detail for {clean_order_id}: {e}")
        return jsonify({
            "error": "Failed to retrieve order",
            "order_id": clean_order_id,
            "message": "Internal query or scoring failure"
        }), 500


# -----------------------------------------------------------------------------
# 6. POST /api/assistant/chat
# -----------------------------------------------------------------------------
@app.route("/api/assistant/chat", methods=["POST"])
def assistant_chat() -> Response:
    """
    Grounded Operations AI Assistant conversation endpoint.
    Processes natural language queries against verified analytical database views
    and frozen multi-stage risk models without hallucination.
    """
    if not ASSISTANT_SERVICE:
        return jsonify({
            "error": "Service Unavailable",
            "message": "Assistant intelligence service is uninitialized."
        }), 503

    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({
            "error": "Bad Request",
            "message": "Message parameter is required and cannot be empty."
        }), 400

    if len(message) > 1000:
        return jsonify({
            "error": "Bad Request",
            "message": "Message exceeds maximum permitted length of 1,000 characters."
        }), 400

    try:
        response_payload = ASSISTANT_SERVICE.process_query(message)
        return jsonify(response_payload), 200
    except Exception as e:
        logger.error(f"Assistant processing error: {e}")
        return jsonify({
            "error": "Internal Error",
            "message": "Failed to process operational query."
        }), 500


# -----------------------------------------------------------------------------
# MAIN LOCAL ENTRY POINT (Debug mode disabled by default)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("MACROOPS_PORT", 5000))
    logger.info(f"Starting MacroOps Operations Platform on http://127.0.0.1:{port} (debug=False)...")
    app.run(host="127.0.0.1", port=port, debug=False)
