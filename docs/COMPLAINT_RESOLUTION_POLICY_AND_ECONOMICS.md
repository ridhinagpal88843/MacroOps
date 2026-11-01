# MacroOps AI — Complaint Resolution Policy & Business Economics

**Document Version:** 1.0.0<br>
**Phase:** Phase 03 Part 02 — Business Economics & Decision Engine<br>
**System Classification:** Transparent Cost Governance, Decision Theory & Trade-Off Modeling<br>
**Policy Status:** Demonstration & Research Policy (Prototype Evaluation)

---

## 1. Executive Summary & Policy Scope

A common failure mode in automated customer dispute systems is the myopic optimization for the lowest possible refund rate. While aggressive claim rejections may artificially reduce short-term accounting refund spend, they cause catastrophic long-term business damage:
- Erosion of customer trust and collapse of Customer Lifetime Value (LTV).
- Delivery partner demoralization when couriers are wrongly blamed for upstream transit or vendor defects.
- Supplier moral hazard when dark-store intake teams repeatedly absorb the cost of damaged or spoiled vendor shipments.

This specification articulates a **transparent, cost-aware complaint resolution model** that balances financial prudence, fair customer treatment, courier safety, and vendor accountability.

> [!IMPORTANT]
> **Demonstration Policy Notice:** The decision rules, compensation thresholds, and economic parameters documented herein represent an explicit, configurable demonstration policy developed for research, simulation, and benchmark testing. They do **not** represent MacroEdtech's actual customer refund or dispute policy, which requires legal, merchant, and executive finance approval.

---

## 2. Mathematical Cost Model

Every customer dispute resolution introduces direct financial outflows, operational labor overhead, and probabilistic downstream risks. The expected total cost of resolving a complaint under an action $a \in \{\text{Refund}, \text{Replace}, \text{Partial}, \text{Evidence}, \text{Review}\}$ is modeled as:

$$\mathbb{E}[\text{Cost}(a)] = P_{\text{refund}}(a) \cdot C_{\text{refund}} + P_{\text{replace}}(a) \cdot C_{\text{replace}} + C_{\text{support\_handling}}(a) + P_{\text{repeat}}(a) \cdot C_{\text{repeat\_contact}} - C_{\text{vendor\_chargeback}}(a)$$

> [!WARNING]
> **Unvalidated Financial Modeling Assumptions:** All financial parameters listed below (e.g., assumed ₹4,200 LTV, ₹3,200 monthly spend, ₹28 human triage cost, ₹35 delivery slot cost) and behavioral claims (e.g., 82% churn probability) are **illustrative modeling assumptions** adopted from general quick-commerce research heuristics. They are **not** empirical measurements from MacroEdtech's operational data (`macroops_analytics.db` contains operational order telemetry but zero historical customer dispute logs or churn tracking cohorts).

### Component Definitions & Baseline Assumptions

| Parameter | Notation | Baseline Value (INR) | Operational Explanation & Assumption Status |
| :--- | :--- | :--- | :--- |
| **Item Invoice Price** | $P_{\text{item}}$ | Dynamic (Observed) | Price paid by the customer for the specific SKU (observed from order telemetry). |
| **Direct Refund Outflow** | $C_{\text{refund}}$ | $P_{\text{item}}$ or $0.35 \cdot P_{\text{item}}$ | 100% of item value for refunds; 35% for partial cosmetic compensation (prototype policy). |
| **Replacement COGS** | $C_{\text{cogs}}$ | $0.65 \cdot P_{\text{item}}$ | Illustrative assumption: wholesale procurement cost estimated at 65% of retail price. |
| **Replacement Delivery** | $C_{\text{transit}}$ | ₹35.00 | Illustrative assumption: estimated last-mile dispatch slot cost (not empirically verified). |
| **Support Handling Time** | $C_{\text{support}}$ | Automated: ₹1.50<br>Human Review: ₹28.00 | Illustrative assumption: compute cost vs. 4 minutes of human agent triage at an assumed ₹420/hr labor rate. |
| **Repeat Contact Risk** | $C_{\text{repeat}}$ | ₹45.00 | Illustrative assumption: estimated labor cost of handling secondary escalation. |
| **Vendor Chargeback** | $C_{\text{chargeback}}$ | $P_{\text{item}}$ (when applicable) | Recovery of defective goods cost from supplier when batch anomaly threshold ($\ge 2$) is met. |

### Missing Data Governance Rule
$$\text{If } P_{\text{item}} \text{ is missing or unverified, } \mathbb{E}[\text{Cost}(a)] = \text{"insufficient\_data"}$$

The engine strictly refuses to invent surrogate price figures or guess financial exposure. Missing cost parameters immediately trigger manual triage with explicit audit flags.

---

## 3. Alternative Action Cost & Experience Comparison

| Action Tier | Direct Financial Cost | Operational Overhead | Customer Satisfaction (CSAT) Impact | Expected Repeat Contact Rate ($P_{\text{repeat}}$) | Recommended Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`IMMEDIATE_REFUND`** | $1.00 \cdot P_{\text{item}}$ | Low (₹1.50 assumed) | High (+18% NPS retention assumed) | Very Low (< 3% assumed) | Spoiled perishables, food safety risks, broken glass, transit delays > 15m. |
| **`PRIORITY_REPLACEMENT`** | $0.65 \cdot P_{\text{item}} + ₹35.00$ | Medium (₹5.00 assumed) | Highest (+24% NPS retention assumed) | Very Low (< 2% assumed) | Crushed bread/staples, incorrect item delivered, where replacement inventory is in stock. |
| **`PARTIAL_COMPENSATION`** | $0.35 \cdot P_{\text{item}}$ | Low (₹1.50 assumed) | Moderate-High (+8% NPS assumed) | Moderate (8–12% assumed) | Cosmetic packaging scuffs or dents where consumable food seal remains intact. |
| **`REQUEST_EVIDENCE`** | ₹0.00 (Pending) | Low (₹1.50 assumed) | Neutral to Slight Friction (-4% NPS assumed) | High (25–35% assumed) | Unverified claims on items > ₹500 without initial photographic documentation. |
| **`HUMAN_REVIEW`** | Variable (Escalated) | High (₹28.00 assumed) | Neutral (+2% NPS post-resolution assumed) | Low (< 5% assumed) | Critical-value items (> ₹1,500), contradictory evidence, or missing cost data. |

---

## 4. Analysis of Core Business Trade-Offs

### 4.1 Incorrectly Rejecting a Genuine Complaint (Type I Error)
- **Direct Financial Consequence:** Saves a one-time refund of ₹80–₹350.
- **True Economic Consequence (Illustrative Model):** Under illustrative churn heuristic assumptions (unvalidated against empirical cohort data), average monthly customer spend is modeled at ₹3,200 with an annual gross margin of ₹1,150. A customer who experiences an unjustified rejection of a genuine ₹85 milk defect is modeled with an **82% churn probability within 45 days**, destroying an estimated ₹1,150–₹4,200 in assumed annual customer lifetime value.
- **Evidence Status:** This 82% churn figure is an **unvalidated modeling assumption** for decision trade-off simulation; it is not a measured company metric.
- **Fairness Policy Invariant:** Automated rejections are structurally prohibited. If evidence is ambiguous, the case must be escalated to a human reviewer or prompted for additional evidence—never summarily dismissed.

### 4.2 Providing Unnecessary Compensation (Type II Error)
- **Direct Financial Consequence:** Unwarranted payout on unsubstantiated or cosmetic claims creates direct margin shrinkage.
- **Operational Consequence:** Unchecked automated full refunds incentivize repeat fraudulent claims and systemic exploitation.
- **MacroOps Mitigation:** Graduated tiered response. Minor outer box dents receive **35% courtesy wallet credit** rather than a full refund, preserving the customer relationship while eliminating incentives to claim non-defective items as total losses.

### 4.3 Replacement vs. Cash Refund
- **Economic Mechanics:**
  - For a ₹200 grocery item, a cash refund costs the business **₹200**.
  - A replacement dispatch costs **COGS (₹130) + Dispatch (₹35) = ₹165**.
  - The business saves ₹35 while the customer receives the exact item required for their dinner preparation, eliminating the frustration of having to re-order and wait.
- **Operational Guardrail:** Replacements are offered **only when live dark-store inventory is verified**. If replacement stock is zero, the engine automatically falls back to an immediate cash refund (`POL-REPLACEMENT-UNAVAILABLE-FALLBACK-12`).

### 4.4 Automated Decisioning vs. Human Support Labor
- **Automated Processing:** Sub-second latency, ₹1.50 compute cost. Highly effective for clear evidence and standardized low-friction policies.
- **Human Review:** Requires 3–5 minutes of skilled support agent time (₹28.00–₹45.00 labor cost).
- **Optimization Principle:** Human review must be reserved for high-value claims (> ₹1,500), contradictory evidence, or edge cases. Routing every ₹40 item to human review is economically unviable, while automating ₹2,500 electronics claims introduces uncontrolled financial exposure.

---

## 5. Multi-Dimensional Performance Scorecard

MacroOps AI evaluates operational success across five balanced dimensions, ensuring the organization never optimizes for cost at the expense of fairness or supplier integrity:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MACROOPS 5-DIMENSIONAL SCORECARD                     │
├────────────────────────────────────────────────────────────────────────┤
│  1. FAIRNESS & ANTI-BIAS                                               │
│     - 0% Automated Rejections (Hard Governance Guarantee)              │
│     - 0% Frequency Penalization (Claims evaluated on merits)          │
│     - 100% Appeal Route Availability                                   │
├────────────────────────────────────────────────────────────────────────┤
│  2. RESOLUTION VELOCITY & EFFICIENCY                                   │
│     - Median automated adjudication time: < 100 milliseconds           │
│     - Automated resolution rate: 70% of low/medium risk claims         │
│     - Human review triage rate: Bounded to 25–30% of cohort            │
├────────────────────────────────────────────────────────────────────────┤
│  3. ECONOMIC ACCURACY & COST CONTROL                                   │
│     - 0% Fabricated Financial Estimates (Missing data -> Insufficient) │
│     - 35% Tiered Partial Credit for cosmetic blemishes                 │
│     - Intelligent replacement dispatch saving 15–20% vs. cash refund   │
├────────────────────────────────────────────────────────────────────────┤
│  4. UPSTREAM SUPPLIER ACCOUNTABILITY                                   │
│     - Automated cluster detection on recurring batch anomalies (>= 2)  │
│     - Chargeback recovery routing to offset retailer margin loss       │
│     - Quarantine advisories for warehouse intake QA inspections        │
├────────────────────────────────────────────────────────────────────────┤
│  5. CUSTOMER TRUST & RETENTION                                         │
│     - Post-dispute NPS recovery tracking                               │
│     - Repeat contact rate minimization (< 5% on resolved claims)       │
│     - Transparent, empathetic plain-language resolution explanations   │
└────────────────────────────────────────────────────────────────────────┘
```
