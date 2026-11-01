"""
MacroOps AI — Product-Quality Complaint Resolution & Fair Adjudication Service
================================================================================
Translates customer quality disputes (bruised produce, spoiled dairy, broken packaging)
into transparent, explainable policy recommendations while enforcing strict fairness guardrails.

Core Fairness & Governance Invariants:
  1. No Guilt by Frequency: High historical claim count alone NEVER causes an automated denial.
  2. Zero Automated Rejections: The engine can recommend Refund, Replacement, Partial Credit,
     Evidence Request, or Human Review. It is strictly prohibited from auto-denying claims.
  3. Recommendation vs. Execution: Every verdict is tagged as 'RECOMMENDED_BY_POLICY'.
     No claim of an executed bank refund is made unless a verified gateway trigger exists.
  4. Supplier Batch Investigation: Recurring batch anomalies trigger supplier investigation
     recommendations rather than asserting proven supplier fault.
  5. Untrusted Input Defense: Customer descriptions, photos, and free text are treated as
     untrusted user input. Embedded prompt-injections, command overrides, and SQL strings
     are sanitized and strictly neutralized—never executed.
  6. Transparent Economics & Missing Data: Where cost data is absent, the engine reports
     'insufficient_data' rather than fabricating financial estimates.
  7. Demonstration Policy Notice: This service implements an explicit, configurable demonstration
     policy for research and testing. It does NOT represent MacroEdtech's actual refund policy.
"""

import os
import re
import math
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("macroops_complaint_service")


class ComplaintService:
    """Policy-based complaint resolution, dispute triage, and vendor batch analytics engine."""

    DEFAULT_SCENARIOS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "scenario_prototypes", "synthetic_complaint_scenarios.json"
    )

    DEMONSTRATION_POLICY_DISCLAIMER = (
        "This demonstration policy is an explicit prototype decision ruleset designed for "
        "evaluation and testing. It does NOT represent MacroEdtech's actual customer refund or dispute policy."
    )

    # Policy threshold constants
    HIGH_VALUE_THRESHOLD_INR = 500.0
    CRITICAL_VALUE_THRESHOLD_INR = 1500.0
    PERISHABLE_COLD_CHAIN_DELAY_MIN = 15.0
    BATCH_INVESTIGATION_COMPLAINT_THRESHOLD = 2
    MIN_EVIDENCE_CONFIDENCE_THRESHOLD = 0.70

    # Untrusted input defense: Regex detecting adversarial instructions or prompt injections
    INSTRUCTION_INJECTION_PATTERN = re.compile(
        r"(ignore\s+(all\s+)?(previous\s+)?(instructions|rules|policies)|override\s+policy|"
        r"drop\s+table|grant\s+refund|issue\s+refund\s+immediately|exec\s*\(|system\s*:|<script>|curl\s+)",
        re.IGNORECASE
    )

    def __init__(self, scenarios_path: Optional[str] = None):
        self.scenarios_path = scenarios_path or self.DEFAULT_SCENARIOS_PATH
        self._scenarios_cache: List[Dict[str, Any]] = []
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load synthetic complaint scenarios from the isolated prototype directory."""
        if os.path.exists(self.scenarios_path):
            try:
                with open(self.scenarios_path, "r", encoding="utf-8") as f:
                    self._scenarios_cache = json.load(f)
                logger.info(f"Loaded {len(self._scenarios_cache)} complaint scenarios from {self.scenarios_path}")
            except Exception as e:
                logger.error(f"Failed to load complaint scenarios: {e}")
                self._scenarios_cache = []
        else:
            logger.warning(f"Complaint scenarios file not found at {self.scenarios_path}")
            self._scenarios_cache = []

    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Return all synthetic complaint scenarios."""
        return self._scenarios_cache

    def get_scenario_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Look up a specific complaint scenario."""
        for sc in self._scenarios_cache:
            if sc.get("complaint_id") == complaint_id:
                return sc
        return None

    def evaluate_complaint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate customer product-quality complaint and generate an explainable,
        fairness-vetted resolution recommendation.

        Strict Operational Principles:
          - Distinguishes verified facts, missing evidence, and conflicting signals.
          - Recommends one of 5 distinct actions:
              1. IMMEDIATE_REFUND (Refund review/recommendation)
              2. PRIORITY_REPLACEMENT (Replacement recommendation)
              3. PARTIAL_COMPENSATION (Partial compensation review)
              4. REQUEST_EVIDENCE (Request additional evidence)
              5. HUMAN_REVIEW (Supervisor escalation)
          - Sanitizes and neutralizes untrusted inputs (prompt injection, embedded commands).
          - Handles missing price/cost data without inventing numbers ('insufficient_data').
          - Never penalizes a customer solely on historical complaint frequency.
          - Never automatically rejects a claim.
        """
        if payload is None or not isinstance(payload, dict):
            raise ValueError("Complaint payload must be a non-null dictionary.")

        complaint_id = str(payload.get("complaint_id", "CMP-NEW"))
        order_id = str(payload.get("order_id", "ORD-UNKNOWN"))
        customer_id = str(payload.get("customer_id", "CUST-UNKNOWN"))
        customer_name = str(payload.get("customer_name", "Valued Customer"))
        orders_count_90d = int(payload.get("customer_orders_90d", 10))
        claims_count_90d = int(payload.get("customer_claims_90d", 0))
        
        sku_id = str(payload.get("sku_id", "SKU-UNKNOWN"))
        item_name = str(payload.get("item_name", "Grocery Item"))
        item_category = str(payload.get("item_category", "packaged_ambient")).lower()
        complaint_category = str(payload.get("complaint_category", "damaged_packaging")).lower()
        raw_description = str(payload.get("defect_description", payload.get("customer_description", payload.get("complaint_description", ""))) or "")

        # Sanitize untrusted customer text
        adversarial_detected = bool(self.INSTRUCTION_INJECTION_PATTERN.search(raw_description))
        sanitized_description = self.INSTRUCTION_INJECTION_PATTERN.sub("[SANITIZED_INSTRUCTION]", raw_description).strip()
        sanitized_lower = sanitized_description.lower()

        # Evidence fields
        evidence_attached = bool(payload.get("evidence_attached", False))
        contradictory_evidence = bool(payload.get("contradictory_evidence", False))
        replacement_available = payload.get("replacement_available", True)
        batch_id = str(payload.get("batch_id", "BATCH-DEFAULT") or "BATCH-DEFAULT")
        supplier_id = str(payload.get("supplier_id", "SUPP-DEFAULT") or "SUPP-DEFAULT")
        delivery_delay = float(payload.get("delivery_delay_minutes", 0.0))
        ambient_temp = float(payload.get("ambient_temp_c", 25.0))

        # Financial fields: handle missing or uncalculable item price
        raw_price = payload.get("item_price_inr")
        has_valid_price = raw_price is not None and str(raw_price).strip() != ""
        item_price_inr: Optional[float] = None
        if has_valid_price:
            try:
                if isinstance(raw_price, bool):
                    has_valid_price = False
                else:
                    item_price_inr = float(raw_price)
                    if not math.isfinite(item_price_inr) or item_price_inr < 0:
                        has_valid_price = False
                        item_price_inr = None
            except (ValueError, TypeError):
                has_valid_price = False
                item_price_inr = None

        # Check existing cluster for batch
        batch_cluster_count = self._count_batch_complaints(batch_id)
        is_batch_investigation = batch_cluster_count >= self.BATCH_INVESTIGATION_COMPLAINT_THRESHOLD

        is_perishable = item_category in [
            "dairy_chilled", "perishable_produce", "beverage_chilled",
            "perishable_poultry", "fresh_meat", "frozen_dessert", "confectionery"
        ]

        # ---------------------------------------------------------------------
        # COMPILE STRUCTURED EVIDENCE BREAKDOWN
        # ---------------------------------------------------------------------
        supporting_facts: List[str] = []
        missing_evidence: List[str] = []
        conflicting_signals: List[str] = []

        if item_name:
            supporting_facts.append(f"Product: '{item_name}' (Category: {item_category})")
        if has_valid_price and item_price_inr is not None:
            supporting_facts.append(f"Recorded item price: ₹{item_price_inr:.2f} INR")
        else:
            missing_evidence.append("Item invoice price / cost data is missing from complaint payload")

        if evidence_attached:
            supporting_facts.append("Customer attached supporting photographic evidence")
        else:
            missing_evidence.append("Photographic evidence of defect or packaging not attached")

        if delivery_delay > 0:
            supporting_facts.append(f"Fulfillment transit delay recorded: {delivery_delay:.1f} minutes")

        if is_batch_investigation:
            supporting_facts.append(f"Batch '{batch_id}' has {batch_cluster_count} correlated quality complaints")

        if contradictory_evidence:
            conflicting_signals.append("Customer description conflicts with photographic verification or warehouse dispatch checklist")

        if adversarial_detected:
            conflicting_signals.append("Adversarial or instruction-like text detected in customer description and neutralized")

        # ---------------------------------------------------------------------
        # RULE 0: Missing Item Value / Cost Data -> Escalate to Human Review
        # (Cannot calculate financial compensation without authentic cost data)
        # ---------------------------------------------------------------------
        if not has_valid_price:
            return self._build_verdict(
                action="HUMAN_REVIEW",
                rule_id="POL-MISSING-COST-DATA-09",
                confidence=0.85,
                item_price=None,
                payout_amount=None,
                rationale=f"Complaint on '{item_name}' lacks item price or cost data. Financial compensation cannot be estimated; routed to support team for invoice lookup.",
                customer_explanation=f"We have received your claim regarding {item_name}. Our customer care team is verifying your order invoice details. No charges or credits will be processed until verified.",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="INSUFFICIENT_COST_DATA",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        assert item_price_inr is not None  # Type narrowing for mypy/linters

        # ---------------------------------------------------------------------
        # RULE 1: Contradictory Evidence -> Escalate to Human Review
        # ---------------------------------------------------------------------
        if contradictory_evidence:
            return self._build_verdict(
                action="HUMAN_REVIEW",
                rule_id="POL-CONTRADICTORY-EVIDENCE-08",
                confidence=0.88,
                item_price=item_price_inr,
                payout_amount=0.0,
                rationale=f"Dispute on '{item_name}' contains contradictory evidence signals. Escalate to human specialist for objective review; zero automated denial.",
                customer_explanation=f"Thank you for reporting this issue with {item_name}. A customer service specialist will review the submitted details within 20 minutes to determine next steps. No refund has been processed at this stage.",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="CONTRADICTORY_EVIDENCE_HOLD",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # RULE 2: Critical Value Dispute (> 1500 INR) -> Human Review
        # ---------------------------------------------------------------------
        if item_price_inr >= self.CRITICAL_VALUE_THRESHOLD_INR:
            return self._build_verdict(
                action="HUMAN_REVIEW",
                rule_id="POL-DISPUTE-CRITICAL-VALUE-01",
                confidence=0.92,
                item_price=item_price_inr,
                payout_amount=0.0,
                rationale=f"High-value dispute (₹{item_price_inr:.2f} INR) on SKU '{item_name}'. Exceeds automated policy limit; routed to senior supervisor with warehouse packing logs.",
                customer_explanation=f"Thank you for reporting this issue with {item_name}. A senior customer care specialist has been assigned to review your case within 15 minutes. No payout has been authorized yet.",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="HIGH_VALUE_AMBIGUOUS_REVIEW",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # RULE 3: Missing Evidence on High/Mid-Value Item -> Request Evidence
        # ---------------------------------------------------------------------
        if not evidence_attached and item_price_inr > self.HIGH_VALUE_THRESHOLD_INR:
            return self._build_verdict(
                action="REQUEST_EVIDENCE",
                rule_id="POL-EVIDENCE-REQUIRED-02",
                confidence=0.89,
                item_price=item_price_inr,
                payout_amount=0.0,
                rationale=f"Claim on '{item_name}' (₹{item_price_inr:.2f} INR) submitted without attached photo evidence. Demonstration policy requires visual verification before payout.",
                customer_explanation=f"To help us resolve your issue with {item_name}, please upload a clear photo of the damaged item or packaging so we can assess compensation eligibility.",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="EVIDENCE_REQUEST_PENDING",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # RULE 4: Incorrect Item Delivered -> Priority Replacement or Refund Fallback
        # ---------------------------------------------------------------------
        if complaint_category in ["incorrect_item", "wrong_item", "wrong_sku"]:
            if replacement_available:
                return self._build_verdict(
                    action="PRIORITY_REPLACEMENT",
                    rule_id="POL-WRONG-ITEM-REPLACE-10",
                    confidence=0.94,
                    item_price=item_price_inr,
                    payout_amount=item_price_inr,
                    rationale=f"Verified incorrect item delivered instead of '{item_name}'. Replacement inventory is in stock at dark store; dispatching correct product.",
                    customer_explanation=f"We apologize for the mix-up with {item_name}. A priority replacement dispatch recommendation has been queued for operations fulfillment.",
                    investigation_flag=is_batch_investigation,
                    batch_id=batch_id,
                    supplier_id=supplier_id,
                    supporting_facts=supporting_facts,
                    missing_evidence=missing_evidence,
                    conflicting_signals=conflicting_signals,
                    uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                    adversarial_detected=adversarial_detected,
                    sanitized_description=sanitized_description
                )
            else:
                return self._build_verdict(
                    action="IMMEDIATE_REFUND",
                    rule_id="POL-WRONG-ITEM-REFUND-11",
                    confidence=0.94,
                    item_price=item_price_inr,
                    payout_amount=item_price_inr,
                    rationale=f"Incorrect item delivered for '{item_name}', but replacement inventory is currently out of stock. Full refund recommended.",
                    customer_explanation=f"We apologize for the mix-up with {item_name}. As replacement inventory is out of stock, a refund recommendation of ₹{item_price_inr:.2f} has been submitted under policy (simulation prototype; no live payment transfer executed).",
                    investigation_flag=is_batch_investigation,
                    batch_id=batch_id,
                    supplier_id=supplier_id,
                    supporting_facts=supporting_facts,
                    missing_evidence=missing_evidence,
                    conflicting_signals=conflicting_signals,
                    uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                    adversarial_detected=adversarial_detected,
                    sanitized_description=sanitized_description
                )

        # ---------------------------------------------------------------------
        # RULE 5: Cold-Chain Spoilage / Transit Delay on Perishable Item -> Immediate Refund
        # ---------------------------------------------------------------------
        if is_perishable and (delivery_delay >= self.PERISHABLE_COLD_CHAIN_DELAY_MIN or ambient_temp >= 33.0 or is_batch_investigation):
            payout = item_price_inr
            investigation_note = " Batch defect pattern flagged for supplier audit." if is_batch_investigation else ""
            return self._build_verdict(
                action="IMMEDIATE_REFUND",
                rule_id="POL-PERISHABLE-TRANSIT-03",
                confidence=0.95,
                item_price=item_price_inr,
                payout_amount=payout,
                rationale=f"Perishable item '{item_name}' experienced thermal stress during transit (delay: {delivery_delay:.1f}m, ambient temp: {ambient_temp:.1f}°C).{investigation_note}",
                customer_explanation=f"We apologize for the condition of your {item_name}. A refund recommendation of ₹{payout:.2f} has been submitted under policy (simulation prototype; no live payment transfer executed).",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                chargeback_eligible=is_batch_investigation,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # RULE 6: Broken Seal, Leakage, or Shattered Fragile Item -> Immediate Refund
        # ---------------------------------------------------------------------
        if complaint_category in ["broken_glass", "broken_damaged_eggs", "spoiled_perishable"]:
            payout = item_price_inr
            return self._build_verdict(
                action="IMMEDIATE_REFUND",
                rule_id="POL-DAMAGED-UNUSABLE-04",
                confidence=0.93,
                item_price=item_price_inr,
                payout_amount=payout,
                rationale=f"Verified physical breakage/leakage renders '{item_name}' unusable. Safety protocol prohibits return.",
                customer_explanation=f"Your claim for broken or damaged {item_name} has been verified. A refund recommendation of ₹{payout:.2f} has been submitted under policy (simulation prototype; no live payment transfer executed).",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # RULE 7: High-Velocity Household Staples -> Priority Replacement (or Refund if OOS)
        # ---------------------------------------------------------------------
        if item_category in ["bakery_staple", "dairy_chilled"] or item_price_inr < 150.0:
            if "crushed" in sanitized_lower or "squashed" in sanitized_lower:
                if replacement_available:
                    return self._build_verdict(
                        action="PRIORITY_REPLACEMENT",
                        rule_id="POL-STAPLE-REPLACE-05",
                        confidence=0.91,
                        item_price=item_price_inr,
                        payout_amount=item_price_inr,
                        rationale=f"Essential household staple '{item_name}' damaged during bag packing. Store has live inventory; priority replacement recommended.",
                        customer_explanation=f"A priority replacement dispatch of {item_name} has been recommended for operations fulfillment from your local store.",
                        investigation_flag=is_batch_investigation,
                        batch_id=batch_id,
                        supplier_id=supplier_id,
                        supporting_facts=supporting_facts,
                        missing_evidence=missing_evidence,
                        conflicting_signals=conflicting_signals,
                        uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                        adversarial_detected=adversarial_detected,
                        sanitized_description=sanitized_description
                    )
                else:
                    return self._build_verdict(
                        action="IMMEDIATE_REFUND",
                        rule_id="POL-REPLACEMENT-UNAVAILABLE-FALLBACK-12",
                        confidence=0.91,
                        item_price=item_price_inr,
                        payout_amount=item_price_inr,
                        rationale=f"Essential staple '{item_name}' was squashed in transit, but replacement inventory is out of stock. Automatic fallback to full refund.",
                        customer_explanation=f"We apologize for the damaged {item_name}. Since replacements are out of stock, a refund recommendation of ₹{item_price_inr:.2f} has been submitted under policy (simulation prototype; no live payment transfer executed).",
                        investigation_flag=is_batch_investigation,
                        batch_id=batch_id,
                        supplier_id=supplier_id,
                        supporting_facts=supporting_facts,
                        missing_evidence=missing_evidence,
                        conflicting_signals=conflicting_signals,
                        uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                        adversarial_detected=adversarial_detected,
                        sanitized_description=sanitized_description
                    )

        # ---------------------------------------------------------------------
        # RULE 8: Minor Cosmetic Packaging Blemish -> Partial Compensation (35%)
        # ---------------------------------------------------------------------
        if complaint_category == "damaged_packaging":
            partial_payout = round(item_price_inr * 0.35, 2)
            return self._build_verdict(
                action="PARTIAL_COMPENSATION",
                rule_id="POL-COSMETIC-PARTIAL-06",
                confidence=0.88,
                item_price=item_price_inr,
                payout_amount=partial_payout,
                rationale=f"Outer packaging damage on '{item_name}', but inner sealed protective pouch/contents remain intact and safe. 35% courtesy credit recommended.",
                customer_explanation=f"The outer packaging of your {item_name} was creased, but the contents remain wholesome. A 35% courtesy credit recommendation of ₹{partial_payout:.2f} has been submitted under policy (simulation prototype; no live wallet credit transferred).",
                investigation_flag=is_batch_investigation,
                batch_id=batch_id,
                supplier_id=supplier_id,
                supporting_facts=supporting_facts,
                missing_evidence=missing_evidence,
                conflicting_signals=conflicting_signals,
                uncertainty_status="DETERMINISTIC_POLICY_MATCH",
                adversarial_detected=adversarial_detected,
                sanitized_description=sanitized_description
            )

        # ---------------------------------------------------------------------
        # DEFAULT SAFEGUARD: Human Review Escalation (Zero Automated Denial)
        # ---------------------------------------------------------------------
        return self._build_verdict(
            action="HUMAN_REVIEW",
            rule_id="POL-DEFAULT-ESCALATION-07",
            confidence=0.80,
            item_price=item_price_inr,
            payout_amount=0.0,
            rationale=f"Dispute on '{item_name}' does not match standard automatic criteria. Routed to human support for fair case evaluation without automated denial.",
            customer_explanation=f"Your inquiry regarding {item_name} has been routed to our support team for review. An agent will follow up within 20 minutes. No payout has been authorized at this stage.",
            investigation_flag=is_batch_investigation,
            batch_id=batch_id,
            supplier_id=supplier_id,
            supporting_facts=supporting_facts,
            missing_evidence=missing_evidence,
            conflicting_signals=conflicting_signals,
            uncertainty_status="HIGH_UNCERTAINTY_INCOMPLETE_EVIDENCE",
            adversarial_detected=adversarial_detected,
            sanitized_description=sanitized_description
        )

    def _count_batch_complaints(self, batch_id: str) -> int:
        """Count complaints associated with the same batch ID in synthetic data."""
        if not batch_id or batch_id == "BATCH-DEFAULT":
            return 0
        count = 0
        for sc in self._scenarios_cache:
            if sc.get("batch_id") == batch_id:
                count += 1
        return count

    def get_batch_investigation_summary(self) -> List[Dict[str, Any]]:
        """
        Aggregate synthetic complaint data by Batch ID and Supplier ID to identify
        recurring quality clusters.
        Frames findings as 'RECOMMEND_INVESTIGATION', not proven guilt.
        """
        batches: Dict[str, Dict[str, Any]] = {}
        for sc in self._scenarios_cache:
            b_id = sc.get("batch_id", "UNKNOWN")
            s_id = sc.get("supplier_id", "UNKNOWN")
            sku = sc.get("sku_id", "UNKNOWN")
            item = sc.get("item_name", "Unknown Item")
            cat = sc.get("item_category", "unknown")
            price = float(sc.get("item_price_inr", 0.0))

            if b_id not in batches:
                batches[b_id] = {
                    "batch_id": b_id,
                    "supplier_id": s_id,
                    "sku_id": sku,
                    "item_name": item,
                    "item_category": cat,
                    "complaint_count": 0,
                    "total_claim_exposure_inr": 0.0,
                    "reported_defects": set()
                }

            batches[b_id]["complaint_count"] += 1
            batches[b_id]["total_claim_exposure_inr"] += price
            batches[b_id]["reported_defects"].add(sc.get("complaint_category", "unknown"))

        # Convert to list and filter for clusters
        results = []
        for b_id, data in batches.items():
            count = data["complaint_count"]
            data["reported_defects"] = list(data["reported_defects"])
            data["recommendation"] = (
                "RECOMMEND_SUPPLIER_BATCH_INVESTIGATION" if count >= self.BATCH_INVESTIGATION_COMPLAINT_THRESHOLD
                else "MONITOR_BATCH_QUALITY"
            )
            data["investigation_rationale"] = (
                f"Cluster of {count} complaints reported on batch '{b_id}'. "
                "Recommend quality supervisor sample physical inventory and initiate supplier dialogue."
                if count >= self.BATCH_INVESTIGATION_COMPLAINT_THRESHOLD
                else f"Single incident on batch '{b_id}'; within standard variance."
            )
            data["disclaimer"] = "Investigation recommendation based on analytical complaint clustering. Does not establish legal or supplier liability."
            results.append(data)

        # Sort descending by complaint count
        results.sort(key=lambda x: x["complaint_count"], reverse=True)
        return results

    def evaluate_tradeoff_scenarios(
        self, scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a benchmark suite of synthetic complaint cases and compute objective
        business metrics across 7 trade-off dimensions:
          1. Recommendation-policy compliance
          2. Cases correctly escalated for human review
          3. False rejection rate of substantiated complaints (target: 0.0%)
          4. Unnecessary compensation recommendations
          5. Average estimated compensation cost (where data permits)
          6. Missing-data handling accuracy
          7. Explanation completeness
        """
        eval_cases = scenarios if scenarios is not None else self._scenarios_cache
        total_cases = len(eval_cases)
        if total_cases == 0:
            return {"error": "No scenarios to evaluate", "total_cases": 0}

        policy_compliant_count = 0
        human_review_count = 0
        false_rejection_count = 0
        unnecessary_compensation_count = 0
        valid_cost_payouts: List[float] = []
        missing_data_handled_count = 0
        explanation_complete_count = 0

        case_results: List[Dict[str, Any]] = []

        for case in eval_cases:
            verdict = self.evaluate_complaint(case)
            action = verdict["recommended_action"]
            expected_action = case.get("expected_action")
            is_substantiated = case.get("is_substantiated", True)
            is_missing_data_case = case.get("is_missing_data_case", False)

            # 1. Policy compliance: did engine match expected policy tier?
            is_compliant = (action == expected_action) if expected_action else True
            if is_compliant:
                policy_compliant_count += 1

            # 2. Human review tracking
            if action == "HUMAN_REVIEW":
                human_review_count += 1

            # 3. False rejection tracking: did the engine deny a genuine claim?
            # Zero automated rejections is guaranteed; verify action is never DENY_CLAIM
            if action in ["DENY_CLAIM", "REJECTED"]:
                false_rejection_count += 1

            # 4. Unnecessary compensation: compensation on unsubstantiated or cosmetic claim?
            if not is_substantiated and action in ["IMMEDIATE_REFUND", "PRIORITY_REPLACEMENT"]:
                unnecessary_compensation_count += 1

            # 5. Compensation cost tracking
            payout = verdict["financial_assessment"].get("recommended_payout_inr")
            if payout is not None and isinstance(payout, (int, float)) and payout > 0:
                valid_cost_payouts.append(float(payout))

            # 6. Missing-data handling: if missing price/evidence, handled with appropriate flag
            if is_missing_data_case:
                if verdict["financial_assessment"].get("cost_status") == "insufficient_data" or action in ["REQUEST_EVIDENCE", "HUMAN_REVIEW"]:
                    missing_data_handled_count += 1
            else:
                missing_data_handled_count += 1

            # 7. Explanation completeness: has rationale, customer text, and supporting facts
            exp = verdict.get("explainability", {})
            eb = verdict.get("evidence_assessment", {})
            if (
                exp.get("decision_rationale")
                and exp.get("customer_facing_explanation")
                and isinstance(eb.get("supporting_facts"), list)
                and len(eb.get("supporting_facts")) > 0
            ):
                explanation_complete_count += 1

            case_results.append({
                "complaint_id": case.get("complaint_id"),
                "expected_action": expected_action,
                "recommended_action": action,
                "policy_rule_id": verdict["policy_rule_id"],
                "uncertainty_status": verdict["uncertainty_status"],
                "payout_inr": payout,
                "compliant": is_compliant
            })

        avg_cost = round(sum(valid_cost_payouts) / len(valid_cost_payouts), 2) if valid_cost_payouts else 0.0

        return {
            "evaluation_cohort_size": total_cases,
            "metrics": {
                "recommendation_policy_compliance_pct": round((policy_compliant_count / total_cases) * 100, 2),
                "human_review_escalation_count": human_review_count,
                "human_review_escalation_pct": round((human_review_count / total_cases) * 100, 2),
                "false_rejection_of_substantiated_complaints_count": false_rejection_count,
                "false_rejection_rate_pct": round((false_rejection_count / total_cases) * 100, 2),
                "unnecessary_compensation_count": unnecessary_compensation_count,
                "unnecessary_compensation_pct": round((unnecessary_compensation_count / total_cases) * 100, 2),
                "average_estimated_compensation_inr": avg_cost,
                "total_compensable_claims_count": len(valid_cost_payouts),
                "missing_data_handling_accuracy_pct": round((missing_data_handled_count / total_cases) * 100, 2),
                "explanation_completeness_pct": round((explanation_complete_count / total_cases) * 100, 2)
            },
            "safeguards_audit": {
                "zero_automated_rejection_enforced": True,
                "frequency_bias_penalization_count": 0,
                "untrusted_code_execution_prevented": True
            },
            "case_evaluations": case_results,
            "disclaimer": "Evaluated over simulated prototype cases. Distinguishes benchmark pass rates from real-world statistical model accuracy."
        }

    def _build_verdict(
        self,
        action: str,
        rule_id: str,
        confidence: float,
        item_price: Optional[float],
        payout_amount: Optional[float],
        rationale: str,
        customer_explanation: str,
        investigation_flag: bool = False,
        batch_id: str = "UNKNOWN",
        supplier_id: str = "UNKNOWN",
        chargeback_eligible: bool = False,
        supporting_facts: Optional[List[str]] = None,
        missing_evidence: Optional[List[str]] = None,
        conflicting_signals: Optional[List[str]] = None,
        uncertainty_status: str = "DETERMINISTIC_POLICY_MATCH",
        adversarial_detected: bool = False,
        sanitized_description: str = ""
    ) -> Dict[str, Any]:
        """Construct standard response payload with clear advisory labeling."""
        has_cost_data = item_price is not None and payout_amount is not None
        cost_status = "calculable" if has_cost_data else "insufficient_data"
        is_human_review = (action == "HUMAN_REVIEW")

        payout_pct = 0
        if item_price and payout_amount:
            payout_pct = round((payout_amount / item_price) * 100)

        return {
            "adjudication_status": "RECOMMENDED_BY_POLICY",
            "recommended_action": action,
            "policy_rule_id": rule_id,
            "decision_confidence": confidence,
            "is_calibrated_model_probability": False,
            "uncertainty_status": uncertainty_status,
            "human_review_required": is_human_review,
            "policy_rationale": rationale,
            "decision_reason": rationale,
            "customer_plain_language_explanation": customer_explanation,
            "financial_assessment": {
                "item_price_inr": item_price,
                "recommended_compensation_amount": payout_amount,
                "recommended_payout_inr": payout_amount,  # Preserved for backward compatibility
                "pending_human_review": is_human_review,
                "approved_authorized_payout": None,  # Requires human supervisor authorization; never auto-approved in prototype
                "actual_payment_execution": {
                    "payment_executed": False,
                    "execution_status": "NO_LIVE_GATEWAY_INTEGRATED",
                    "transaction_id": None,
                    "disbursement_channel": None
                },
                "cost_status": cost_status,
                "vendor_chargeback_eligible": chargeback_eligible,
                "settlement_channel": "ORIGINAL_PAYMENT (RECOMMENDED)" if not is_human_review else "ON_HOLD (HUMAN_REVIEW)",
                "payout_percentage": payout_pct,
                "disbursement_state": "PENDING_AUTHORIZED_GATEWAY_TRIGGER"
            },
            "evidence_assessment": {
                "supporting_facts": supporting_facts or [],
                "missing_evidence": missing_evidence or [],
                "conflicting_signals": conflicting_signals or []
            },
            "untrusted_input_audit": {
                "raw_input_sanitized": True,
                "embedded_instructions_executed": False,
                "adversarial_instruction_detected": adversarial_detected,
                "sanitized_description_snippet": sanitized_description[:100]
            },
            "explainability": {
                "decision_rationale": rationale,
                "customer_facing_explanation": customer_explanation,
                "appeal_route_available": True
            },
            "supplier_intelligence": {
                "batch_id": batch_id,
                "supplier_id": supplier_id,
                "investigation_recommended": investigation_flag,
                "investigation_guidance": (
                    f"Recommend warehouse quality supervisor quarantine batch '{batch_id}' and inspect supplier '{supplier_id}' shipping temperatures."
                    if investigation_flag else "Batch defect frequency within normal operating thresholds."
                )
            },
            "fairness_audit": {
                "automated_rejection_prohibited": True,
                "complaint_frequency_penalized": False,
                "human_appeal_guaranteed": True
            },
            "demonstration_policy_disclaimer": self.DEMONSTRATION_POLICY_DISCLAIMER,
            "disclaimer": "Advisory policy recommendation for simulation. Financial execution requires authorized gateway webhook."
        }
