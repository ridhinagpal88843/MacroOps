# MacroOps AI — Synthetic Data Governance, Empirical Validation & Pilot Deployment Plan

**Document Version:** 1.0.0<br>
**Phase:** Phase 03 Part 02 — Data Governance & Field Validation<br>
**System Classification:** Governance Framework, Ethical Telemetry & Pilot Trial Architecture<br>
**Execution Guarantee:** Non-destructive analytical extension. Preserves frozen model baselines and historical database views.

---

## 1. Executive Summary & Governance Objective

MacroOps AI was initially developed and evaluated over a canonical synthetic dataset of 200,000 quick-commerce events and 100 dark stores across September 2026. While synthetic operational data enables safe rapid prototyping, rigorous regression testing, and stress-testing of anti-bias policies, real-world deployment requires an honest accounting of synthetic limitations, empirical validation, and a controlled pilot roadmap.

This document establishes the **data validation and governance plan** required prior to physical deployment, ensuring strict compliance with worker safety, customer privacy, algorithmic fairness, and commercial accountability.

> [!CAUTION]
> **Truth-in-Engineering Protocol:** This document outlines proposed empirical validation protocols and a pilot design. No real-world customers, couriers, or employees have been contacted, and no unauthorized personal data collection has taken place.

---

## 2. Telemetry Field Audit: Real vs. Proposed Schema Extensions

To maintain architectural transparency, the table below delineates which data fields exist in the active analytical database (`macroops_analytics.db`) and which are proposed extensions for future operational collection:

| Domain | Field Name | Status in Workspace | Data Source / Operational Meaning |
| :--- | :--- | :---: | :--- |
| **Orders** | `order_id`, `store_id`, `order_time`, `item_count`, `order_value`, `promised_time`, `actual_delivery_time`, `status`, `sla_breached`, `delivery_delay_minutes` | **EXISTING (Canonical)** | Ingested into `raw_orders` and exposed via canonical view `v_all_orders` ($N=100,000$). |
| **Inventory** | `store_id`, `sku_id`, `system_stock`, `physical_stock`, `stockout`, `stock_variance`, `inventory_accuracy_pct` | **EXISTING (Canonical)** | Ingested into `raw_inventory` and exposed via view `v_store_inventory` ($N=40,000$). |
| **Picking** | `order_id`, `picker_id`, `pick_start`, `pick_end`, `items_picked`, `items_missing`, `exception_flag` | **EXISTING (Canonical)** | Ingested into `raw_picking` ($N=24,369$; 25.01% telemetry coverage). |
| **Delivery** | `order_id`, `rider_id`, `pickup_time`, `delivery_time`, `distance_km` | **EXISTING (Canonical)** | Ingested into `raw_delivery` ($N=24,369$; 25.01% telemetry coverage). |
| **Workforce** | `employee_id`, `name`, `role`, `assigned_store`, `shift`, `performance_rating` | **EXISTING (Canonical)** | Ingested into `raw_workforce` ($N=10,000$). |
| **Doorstep Telemetry** | `delivery_attempt_id`, `failure_reason`, `location_pin_verified`, `access_instructions_available`, `customer_contact_attempted`, `society_access_restricted`, `parcel_weight_kg`, `parcel_dimensions`, `vehicle_capacity_verified`, `customer_handover_confirmed`, `evidence_source`, `recorded_at` | **PROPOSED EXTENSION** | Modeled in prototype service `DeliveryAccessService` and calibrated in `synthetic_access_scenarios.json` ($N=25$). |
| **Dispute Adjudication**| `complaint_id`, `sku_id`, `complaint_category`, `defect_description`, `evidence_attached`, `evidence_confidence_score`, `contradictory_evidence`, `batch_id`, `supplier_id`, `ambient_temp_c`, `replacement_available`, `item_price_inr` | **PROPOSED EXTENSION** | Modeled in prototype service `ComplaintService` and calibrated in `synthetic_tradeoff_scenarios.json` ($N=10$) and `synthetic_complaint_scenarios.json` ($N=20$). |

---

## 3. Synthetic Data Assumptions & Telemetry Limitations

### 3.1 Assumptions Underlying Synthetic Scenario Construction
1. **Urban Density Modeling:** Dark stores are assumed to operate in dense metropolitan corridors where 40% of deliveries involve multi-story apartment complexes or gated high-rises.
2. **Cold-Chain Exposure Function:** Perishable quality degradation is assumed to correlate strongly with transit delays exceeding 15 minutes when ambient urban temperatures exceed 30°C.
3. **Packaging Failure Modes:** Secondary packaging creases during motorcycle backpack transit are assumed to represent 70% of packaging complaints, with inner food barrier integrity preserved in the majority of cases.
4. **Batch Defect Clustering:** Vendor manufacturing defects (e.g., spoiled milk batches) are modeled as concentrated clusters sharing identical `(supplier_id, batch_id)` tuples.

### 3.2 Known Telemetry Limitations in Current State
- **Telemetry Coverage Boundary:** In-store warehouse picking logs and courier GPS transit records are captured for exactly 25.01% of completed orders (24,369 orders). 74.99% of network orders possess checkout timestamps only.
- **Urban GPS Multipath Drift:** Raw satellite GPS signals in high-density urban canyons reflect off concrete buildings, causing horizontal positional drift of 50–150 meters. Raw GPS proximity alone **cannot** verify doorstep presence.
- **Visual Evidence Ambiguity:** Smartphone photos submitted by customers may be poorly lit, out of focus, or framed ambiguously, necessitating human review guardrails rather than autonomous claim denials.

---

## 4. Evidence Required for Real-World Validation

Before transitioning from prototype decision logic to autonomous or semi-automated execution, the following empirical evidence must be gathered and verified:

```
┌────────────────────────────────────────────────────────────────────────┐
│               EMPIRICAL EVIDENCE VERIFICATION STANDARDS                │
├────────────────────────────────────────────────────────────────────────┤
│  1. DOORSTEP EXCEPTION VALIDATION                                      │
│     - Hardware scale weight verification at dark-store packing bench.  │
│     - Timestamped courier arrival confirmation within geofence.        │
│     - Telephony server logs proving >= 1 outgoing call/SMS attempt.    │
│     - Optical character recognition (OCR) on building entry signages.  │
├────────────────────────────────────────────────────────────────────────┤
│  2. PRODUCT QUALITY VALIDATION                                         │
│     - Customer photographic evidence showing readable SKU batch stamp. │
│     - Thermal sensor telemetry from insulated courier cargo bags.      │
│     - Corroborating complaints on identical SKU/Batch within 24 hours. │
│     - Dark-store physical inventory audit of remaining batch units.    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Stakeholder Interview & User-Research Methodology

A structured qualitative discovery study is proposed to validate operational assumptions across all fulfillment roles:

### 5.1 Delivery Partners ($N = 40$ Target Cohort)
- **Focus Areas:** Physical fatigue, staircase walk-up ergonomics, heavy liquid packaging (detergents, water cartons), gated community security delays, and perceptions of algorithmic penalty systems.
- **Safety Protocol:** Semi-structured interviews conducted at dark-store rest hubs during shift breaks, compensated at standard hourly bonus rates.

### 5.2 Customers ($N = 30$ Target Cohort)
- **Focus Areas:** Frustrations with delivery location drops (lobby vs. doorstep), clarity of address entry in mobile apps, transparency of complaint outcomes, and willingness to accept replacements vs. refunds.
- **Sampling Strategy:** Stratified across high-frequency urban grocery shoppers, gated community residents, and customers who filed quality disputes in the past 60 days.

### 5.3 Dark-Store Supervisors & Pickers ($N = 15$ Target Cohort)
- **Focus Areas:** Packing station bottlenecks, packaging material resilience, inventory stockout substitution protocols, and vendor intake quality screening.

### 5.4 Customer Care & Dispute Specialists ($N = 15$ Target Cohort)
- **Focus Areas:** Case triage duration, recurring ambiguous claim patterns, customer de-escalation scripts, and pain points in manual invoice lookup.

---

## 6. Privacy, Ethics, Retention & Fairness Safeguards

### 6.1 Data Privacy & Consent Architecture (DPDP & GDPR Alignment)
- **Purpose Limitation:** Customer-uploaded photos and address entrance notes are restricted exclusively to delivery facilitation and claim adjudication. Commercial marketing or third-party profiling is strictly prohibited.
- **Data Minimization:** Customer phone numbers and full names are masked in supervisor-facing consoles (e.g., `CUST-***-101`). Only tokenized customer IDs are logged in audit tables.
- **Retention & Automatic Purging:** Customer dispute photographs and courier audio notes are retained in encrypted cold storage for **90 days** post-resolution, after which they are permanently purged.

### 6.2 Algorithmic Fairness & Labor Safeguards
- **Zero Algorithmic Penalties on Inferred Causes:** Delivery partners cannot suffer platform deactivations, performance rating deductions, or wage withholdings based on unverified exception codes.
- **Anti-Bias Charter:** Customer claim adjudication evaluates the physical evidence of the specific order. Historical claim frequency in the past 90 days **never** constitutes sole grounds for claim denial.
- **Human Review Guarantee:** Any dispute involving high financial value (> ₹1,500), contradictory evidence, or potential abuse is routed to human specialists. The platform contains **zero automated rejection code paths**.

---

## 7. Controlled Pilot Trial Design

To validate business impact, operational velocity, and customer retention empirically, a phased pilot protocol is defined:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PILOT TIMELINE & PHASES                         │
├────────────────────────────────────────────────────────────────────────┤
│  PHASE 1: BASELINE OBSERVATION (Weeks 1–4)                             │
│  - Deploy telemetry logging across 6 pilot dark stores (No AI actions).│
│  - Measure baseline refund spend, SLA breach rate, and rider churn.    │
├────────────────────────────────────────────────────────────────────────┤
│  PHASE 2: SHADOW ADJUDICATION (Weeks 5–8)                              │
│  - Engine runs in background; generates policy recommendations.       │
│  - Human supervisors resolve claims manually; recommendations logged.  │
│  - Compare supervisor decisions vs. policy recommendations.            │
├────────────────────────────────────────────────────────────────────────┤
│  PHASE 3: ASSISTED PILOT (Weeks 9–16)                                  │
│  - 3 Test Dark Stores: Supervisors view AI recommendations & 1-click.  │
│  - 3 Control Dark Stores: Traditional manual dispute process.          │
│  - Difference-in-Differences (DiD) statistical comparison.             │
└────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Key Success Metrics (Target vs. Baseline)

| Evaluation Dimension | Primary Metric | Baseline Estimate | Pilot Target | Verification Method |
| :--- | :--- | :---: | :---: | :--- |
| **Doorstep Delivery** | First-attempt delivery success rate | 91.2% | $\ge 94.5\%$ | Dispatch milestone logs |
| **Courier Safety** | Solitary $>15\text{kg}$ staircase climb incidents | Unmonitored | **0 incidents** | Incident tracking & rider audits |
| **Dispute Velocity** | Average resolution turnaround time | 8.5 minutes | $< 60$ seconds | Customer support ticketing system |
| **Financial Accuracy** | Avoidable compensation spend per order | ₹4.20 | $\le ₹3.40$ | Retail P&L accounting audits |
| **Customer Trust** | Post-dispute 60-day customer retention | 64.0% | $\ge 76.0\%$ | Cohort repurchase analysis |

### 7.2 Safety Stopping Criteria (Circuit Breakers)
The pilot must be immediately halted and reverted to manual protocols if any of the following threshold breaches occur:
1. **False Rejection Spike:** Documented customer appeals revealing justified claims wrongly blocked exceeding $1.0\%$ of resolved volume.
2. **Customer Dissatisfaction Surge:** Post-resolution CSAT dropping by $> 5.0$ percentage points compared to control stores.
3. **Worker Safety Hazard:** Any courier physical injury or unsafe manual handling incident resulting from platform assignment.
4. **Financial Variance Discrepancy:** Net compensation spend exceeding $+10\%$ of budgeted historical run rates due to policy miscalibration.
