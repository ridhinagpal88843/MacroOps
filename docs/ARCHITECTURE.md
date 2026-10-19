# MacroOps AI — System Architecture Specification

**Version:** 1.0.0 (Release Candidate)  
**System Classification:** Multi-Stage Quick-Commerce Predictive Risk Governance Platform & Embodied Dialogue Assistant  
**Prototype Governance Status:** Analytical Prototype on 200,000 Synthetic Operational Records

---

## 1. System Overview

MacroOps AI is an end-to-end analytical operations intelligence command platform for quick-commerce fulfillment networks. The architecture addresses the structural fulfillment deficit where 10-minute delivery promises encounter systemic picking and last-mile delays.

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT BROWSER                                     |
|  +---------------------------+  +--------------------------------------------------+  |
|  | Animated Command Centre   |  | 3D Operations Assistant ("Ava")                  |  |
|  | - Orbital Fulfillment Hero|  | - Three.js WebGL Portrait Canvas (60 FPS)        |  |
|  | - Macro KPI Cards         |  | - Procedural Rig State Machine (5 States)        |  |
|  | - Diurnal Volume Wave     |  | - Viseme-Based Morph Target Speech Lip-Sync      |  |
|  | - Dark Store Leaderboard  |  | - Grounded Operational Dialogue Stream           |  |
|  | - Order Lifecycle Dossier |  | - Audio Synthesis / Dictation Controls          |  |
|  +---------------------------+  +--------------------------------------------------+  |
+-------------------------------------------^-------------------------------------------+
                                            | JSON / REST over HTTP
+-------------------------------------------v-------------------------------------------+
|                                  FLASK APPLICATION                                    |
|                                     (app.py)                                          |
|                                                                                       |
|   GET /api/health          GET /api/kpis              GET /api/stores                 |
|   GET /api/orders          GET /api/order/<id>        POST /api/assistant/chat        |
|                                                                                       |
|  +----------------------+  +-----------------------+  +----------------------------+  |
|  |     DataService      |  |   InferenceService    |  |      AssistantService      |  |
|  | (Services/data_svc)  |  | (Services/infer_svc)  |  |   (Services/assist_svc)    |  |
|  +----------+-----------+  +-----------+-----------+  +--------------+-------------+  |
+-------------|--------------------------|-----------------------------|----------------+
              |                          |                             |
              v                          v                             v
+-----------------------------+  +-------------------------+  +-------------------------+
|     CANONICAL DATABASE      |  |  FROZEN ML CHECKPOINTS  |  |    FEATURE CACHE STORE  |
|   macroops_analytics.db     |  |     model_artifacts/    |  |   predictive_features/  |
|   (SQLite URI: mode=ro)     |  |                         |  |                         |
|                             |  | - Stage A (LightGBM)    |  | - stage_b1_features.csv |
| - v_all_orders (100k)       |  |   tau = 0.9300 (T0)     |  | - stage_b2_features.csv |
| - v_completed_orders (97.4k)|  | - Stage B1 (LightGBM)   |  |   (Indexed by order_id  |
| - v_picking_performance     |  |   tau = 0.9300 (T1)     |  |    for sub-ms lookup)   |
| - v_delivery_performance    |  | - Stage B2 (Hybrid)     |  |                         |
| - v_store_ops_summary       |  |   tau = 0.9300 (T2)     |  |                         |
+-----------------------------+  +-------------------------+  +-------------------------+
```

---

## 2. Core Architectural Components

### 2.1 Web Application & API Layer (`app.py`)
- **Runtime:** Flask WSGI application configured with strict parameter validation and zero stack-trace leakage.
- **Singletons:** Initializes `DataService`, `InferenceService`, and `AssistantService` as shared singletons during startup.
- **In-Memory Feature Indexing:** Pre-loads and indexes `stage_b1_features.csv` and `stage_b2_features.csv` into hash tables (`FEATURE_CACHE`) keyed by `order_id` for sub-millisecond multi-stage scoring.

### 2.2 Analytical Data Service (`services/data_service.py`)
- **Strict Read-Only Enforcement:** Connects exclusively using SQLite URI `file:{path}?mode=ro`.
- **Resource Management:** Wraps connection acquisition in `@contextmanager` with guaranteed `conn.close()` on context exit to eliminate connection leakage and lock contention.
- **SQL Parameterization:** Strictly whitelists sort columns and uses parameterized `?` placeholders across all queries.
- **Canonical Views:**
  - `v_all_orders`: 100,000 gross records across September 1–30, 2026.
  - `v_completed_orders`: 97,449 fulfilled orders (`Delivered_On_Time` or `Delivered_Late`).
  - `v_store_ops_summary`: Store-level aggregates across all 100 dark stores with completed order denominators.

### 2.3 Multi-Stage Inference Engine (`services/inference_service.py`)
- **Lifecycle Checkpoints:**
  - **T0 Checkout (`Stage A`):** Evaluates risk at order creation using 7 features (`item_count`, `order_value`, `promised_duration_minutes`, `order_hour`, `day_of_week`, `is_peak_rush_hour`, `store_id`). Operating threshold frozen at $\tau = 0.9300$.
  - **T1 Post-Picking (`Stage B1`):** Dynamic re-assessment upon pick completion (`picking.pick_end`). Available exclusively for orders with dark store picking telemetry (25.01% of cohort). Operating threshold frozen at $\tau = 0.9300$.
  - **T2 Post-Dispatch Proxy (`Stage B2`):** Synchronization point defined as $\max(\text{pick\_end}, \text{pickup\_time})$. Employs a hybrid deterministic rule: if remaining SLA budget $\le 0$, breach probability is deterministically set to $1.0000$; otherwise predicted by LightGBM.
- **Zero Leakage:** Strict temporal feature separation ensures post-outcome timestamps never enter feature vectors.

### 2.4 Grounded Assistant Engine (`services/assistant_service.py`)
- **Empirical Grounding:** Translates user operational inquiries into parameterized `DataService` queries.
- **Evidence Boxes:** Strictly isolates empirical database statistics from actionable dispatch recommendations.
- **Explicit Denominators:** Distinguishes between completed order denominators ($97,449$) and gross initiation volume ($100,000$).
- **Safety & Injection Defense:** Sanitizes queries via regex patterns; neutralizes prompt injection and SQL injection payloads.

### 2.5 3D Embodied Operations Assistant (`static/js/operations_assistant.js`)
- **Renderer:** Localized Three.js r128 WebGL renderer with high-definition portrait framing and operations rim lighting.
- **Asset:** Fully rigged GLB humanoid model (`brunette.glb`) containing 67 skeletal joints and 72 facial morph targets.
- **State Machine:** Governs 5 discrete animation states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`) at 60 FPS using exponential rotation smoothing.
- **Speech & Viseme Lip-Sync:** Browser `speechSynthesis` API paired with a procedural syllable cadence generator that drives mouth blendshapes (`viseme_aa`, `viseme_O`, `viseme_E`, `jawOpen`, `mouthOpen`).

---

## 3. Data Flow & Request Lifecycles

### 3.1 Order Inspection & Multi-Stage Scoring Flow
```
User clicks order in UI
       │
       ▼
GET /api/order/<order_id>
       │
       ├──> DataService.get_order_lifecycle(order_id)
       │       └── Queries v_full_lifecycle_orders / raw tables
       │
       ├──> Merge cached Stage B1/B2 feature vectors from FEATURE_CACHE
       │
       └──> InferenceService.score_order(order_payload)
               ├── Score Stage A: LightGBM (T0 Checkout)
               ├── Score Stage B1: LightGBM (if picking telemetry exists)
               └── Score Stage B2: Hybrid Deterministic (if dispatch proxy exists)
       │
       ▼
Return JSON with milestones, Stage A/B1/B2 probabilities, and telemetry coverage note
```

### 3.2 Grounded Assistant Dialogue Flow
```
User types query or clicks chip
       │
       ▼
POST /api/assistant/chat {"message": "..."}
       │
       ├──> AssistantService.process_query(message)
       │       ├── Regex intent routing (KPI, Store Ranking, Order Audit, Model Governance)
       │       ├── DataService query execution against canonical SQLite view
       │       └── Assemble response payload (reply, evidence box, recommendation, denominator)
       │
       ▼
Client receives JSON:
       ├── Renders text bubble + evidence box + recommendation + disclaimer
       ├── Triggers Web Speech synthesis (TTS)
       └── Character transitions to SPEAKING with viseme lip-sync and body gestures
```

---

## 4. Security & Safety Architecture

1. **Database Protection:** Read-only SQLite URI prevents database modification, SQL injection attacks, and data tampering.
2. **Zero Client Credentials:** No API keys, tokens, or environment credentials exist in frontend code or API responses.
3. **Safe Error Handling:** 400, 404, and 500 error handlers sanitize error output; local server filesystem paths and stack traces are suppressed.
4. **Permanent Prototype Labeling:** All API responses and UI cards carry the mandatory synthetic prototype disclaimer.
