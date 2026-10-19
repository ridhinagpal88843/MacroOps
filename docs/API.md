# MacroOps AI — REST API Reference Specification

**Base URL:** `http://127.0.0.1:5000/api`  
**Content-Type:** `application/json`  
**Standard Response Envelope:** JSON object containing domain payloads and mandatory synthetic disclaimer.

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Primary Query / Body Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health, DB state, model status | None |
| `GET` | `/kpis` | Macro volume, SLA compliance, picking/transit KPIs | None |
| `GET` | `/stores` | Store-level summaries across 100 dark stores | `sort_by`, `order`, `limit`, `store_id` |
| `GET` | `/orders` | Paginated orders with Stage A risk indicators | `page`, `page_size`, `store_id`, `status`, `has_telemetry`, `search` |
| `GET` | `/order/<order_id>` | Individual order milestones & Stage A/B1/B2 risk scores | `order_id` (path parameter) |
| `POST`| `/assistant/chat` | Grounded conversational AI assistant dialogue | `{"message": "string"}` |

---

## 2. Endpoint Details

### 2.1 `GET /api/health`
Checks the operational readiness of backend services, SQLite connection mode, and model checkpoints.

#### Response Example (200 OK)
```json
{
  "status": "healthy",
  "service_layer": {
    "data_service": true,
    "inference_service": true,
    "assistant_service": true,
    "feature_cache": true
  },
  "database": {
    "connected": true,
    "mode": "read_only",
    "orders_recorded": 100000,
    "database_file": "macroops_analytics.db"
  },
  "models": {
    "loaded": true,
    "stage_a": {
      "model": "LightGBMClassifier",
      "features_count": 7,
      "threshold": 0.93
    },
    "stage_b1": {
      "model": "LightGBMClassifier",
      "features_count": 23,
      "threshold": 0.93
    },
    "stage_b2": {
      "model": "LightGBMClassifier (Hybrid Deterministic)",
      "features_count": 27,
      "threshold": 0.93,
      "deterministic_rule": "remaining_sla_budget_b2_min <= 0 -> P(breach)=1.0"
    }
  },
  "synthetic_data_disclaimer": "All data, models, and metrics represent an analytical prototype on synthetic quick-commerce operational datasets. Not approved for autonomous physical execution."
}
```

---

### 2.2 `GET /api/kpis`
Retrieves standardized operational KPIs across volume, SLA compliance, warehouse picking, last-mile courier delivery, and network inventory accuracy.

#### Response Example (200 OK)
```json
{
  "generated_at": "2026-09-30T23:59:59Z",
  "cohort_window": "September 1-30, 2026",
  "macro_volume": {
    "total_orders": { "value": 100000, "formatted": "100,000", "source": "v_all_orders" },
    "completed_orders": { "value": 97449, "formatted": "97,449 (97.45%)", "source": "v_completed_orders" },
    "cancelled_orders": { "value": 1795, "formatted": "1,795 (1.79%)" },
    "failed_orders": { "value": 756, "formatted": "756 (0.76%)" }
  },
  "sla_compliance": {
    "sla_breach_rate_pct": {
      "value": 89.68,
      "formatted": "89.68%",
      "denominator": "Completed Orders (97,449)",
      "source": "v_completed_orders (late / completed)"
    },
    "on_time_delivery_rate_pct": {
      "value": 10.32,
      "formatted": "10.32%",
      "denominator": "Completed Orders (97,449)"
    },
    "avg_delivery_delay_min": { "value": 6.43, "formatted": "6.43m" }
  },
  "synthetic_data_disclaimer": "All data, models, and metrics represent an analytical prototype on synthetic quick-commerce operational datasets. Not approved for autonomous physical execution."
}
```

---

### 2.3 `GET /api/stores`
Retrieves store-level operational metrics across all 100 dark stores or looks up an individual store.

#### Query Parameters
- `sort_by` (optional): Column to sort by (`total_orders`, `sla_breach_rate_pct`, `on_time_delivery_rate_pct`, `avg_delivery_delay_min`, `avg_inventory_accuracy`). Default: `total_orders`.
- `order` (optional): Sort direction (`asc` or `desc`). Default: `desc`.
- `limit` (optional): Integer between 1 and 100. Default: `100`.
- `store_id` (optional): Exact store ID lookup (e.g., `ST001`).

#### Error Responses
- `400 Bad Request`: When `sort_by` column is invalid, `order` is not `asc/desc`, or `limit` is out of bounds.
- `404 Not Found`: When `store_id` does not exist in the 100-store network.

---

### 2.4 `GET /api/orders`
Retrieves paginated order records with joined picking and delivery milestones. Attaches lightweight Stage A risk indicators strictly to the requested page slice.

#### Query Parameters
- `page` (optional): Positive integer $\ge 1$. Default: `1`.
- `page_size` (optional): Integer between 1 and 100. Default: `50`.
- `store_id` (optional): Filter by dark store ID (e.g., `ST001`).
- `status` (optional): Filter by order status (`Delivered_On_Time`, `Delivered_Late`, `Cancelled`, `Failed`).
- `has_telemetry` (optional): Filter by telemetry availability (`true` or `false`).
- `search` (optional): Search order ID substring.

#### Response Structure
```json
{
  "orders": [
    {
      "order_id": "ORD-000001",
      "store_id": "ST001",
      "order_time": "2026-09-01 08:14:22",
      "status": "Delivered_Late",
      "sla_breached": 1,
      "delivery_delay_minutes": 5.4,
      "stage_a_risk_score": 0.9412,
      "stage_a_alert": true,
      "has_picking_telemetry": 1,
      "has_delivery_telemetry": 1
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_orders": 100000,
    "total_pages": 2000,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### 2.5 `GET /api/order/<order_id>`
Retrieves full lifecycle milestones and multi-stage risk assessment for an individual order across Stage A, Stage B1, and Stage B2.

#### Path Parameter
- `order_id`: Canonical order identifier (e.g., `ORD-000001`).

#### Response Example (200 OK)
```json
{
  "order_id": "ORD-000001",
  "lifecycle_milestones": {
    "order_time": "2026-09-01 08:14:22",
    "pick_start": "2026-09-01 08:16:10",
    "pick_end": "2026-09-01 08:21:45",
    "pickup_time": "2026-09-01 08:22:10",
    "delivery_time": "2026-09-01 08:35:12",
    "has_stage_b_telemetry": true
  },
  "risk_assessment": {
    "stage_a": {
      "checkpoint_name": "T0: Order Checkout",
      "risk_probability": 0.9412,
      "operating_threshold": 0.93,
      "alert_triggered": true,
      "status_label": "CRITICAL RISK ESCALATION"
    },
    "stage_b1": {
      "checkpoint_name": "T1: Post-Picking",
      "risk_probability": 0.9620,
      "operating_threshold": 0.93,
      "alert_triggered": true,
      "checkpoint_available": true
    },
    "stage_b2": {
      "checkpoint_name": "T2: Post-Dispatch Proxy",
      "risk_probability": 1.0,
      "is_deterministic_override": true,
      "checkpoint_available": true
    }
  },
  "governance_and_coverage": {
    "has_stage_b_telemetry": true,
    "dispatch_proxy_clarification": "Checkpoint B2 represents max(pick_end, pickup_time), serving as an effective operational synchronization milestone. It does not represent confirmed physical departure.",
    "frozen_decision_threshold": 0.93
  }
}
```

---

### 2.6 `POST /api/assistant/chat`
Processes conversational inquiries against analytical database views and multi-stage models without hallucination.

#### Request Payload
```json
{
  "message": "What is our overall SLA breach rate?"
}
```

#### Validation Rules
- `message` cannot be empty or whitespace only (HTTP 400).
- `message` maximum length: 1,000 characters (HTTP 400).

#### Response Example (200 OK)
```json
{
  "reply": "Across our 100 dark stores, we have recorded 100,000 gross orders. Of the 97,449 completed orders, our SLA breach rate stands at 89.68% with an average delivery delay of 6.43m. On-time delivery is currently 10.32%.",
  "intent": "GLOBAL_KPIS",
  "evidence": {
    "gross_orders": 100000,
    "completed_orders": 97449,
    "sla_breach_rate": 89.68,
    "on_time_delivery_rate": 10.32,
    "avg_delay_min": 6.43,
    "source_view": "v_completed_orders and v_all_orders",
    "denominator": "Completed Orders (97,449)"
  },
  "recommendation": "Recommendation: High breach rates are systemic across stores due to structural 6.25m delivery deficits. Dispatchers should prioritize Stage A high-risk checkout orders (P >= 0.9300) to fast-track picking lines.",
  "denominator": "Completed Orders (97,449)",
  "synthetic_data_disclaimer": "All data, metrics, and models represent an analytical prototype on 200,000 synthetic quick-commerce records. Not approved for autonomous physical execution."
}
```
