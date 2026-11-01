"""
MacroOps AI — Phase 03 Part 02: Business Validation & Trade-off Automated Tests
================================================================================
Automated test suite covering:
  1. The 10 canonical business trade-off scenarios in `synthetic_tradeoff_scenarios.json`.
  2. Multi-metric evaluation runner measuring policy compliance, human review escalation,
     false rejection, unnecessary compensation, average cost, missing data, and explanation completeness.
  3. Strict fairness invariants: anti-bias on complaint frequency, zero automated denials,
     untrusted instruction sanitization, and missing-data integrity.
  4. Doorstep delivery exception diagnostic engine covering all 6 reason categories,
     4-way evidence breakdown, and worker protection safeguards.
"""

import sys
import os
import unittest
import json

# Ensure workspace is in sys.path
WORKSPACE_DIR = r"c:\Users\HP\Desktop\MacroOps"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from app import app, COMPLAINT_SERVICE, DELIVERY_ACCESS_SERVICE


class TestBusinessValidationAndTradeoffs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.benchmark_path = os.path.join(
            WORKSPACE_DIR, "data", "scenario_prototypes", "synthetic_tradeoff_scenarios.json"
        )
        with open(cls.benchmark_path, "r", encoding="utf-8") as f:
            cls.benchmark_scenarios = json.load(f)

    # =========================================================================
    # 1. INDIVIDUAL VERIFICATION OF THE 10 CANONICAL BUSINESS TRADE-OFF SCENARIOS
    # =========================================================================

    def test_scenario_01_damaged_perishable(self):
        """Case 1: Clearly documented damaged perishable product receives IMMEDIATE_REFUND."""
        case = self.benchmark_scenarios[0]
        self.assertEqual(case["complaint_id"], "SIM-CMP-01")
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "IMMEDIATE_REFUND")
        self.assertEqual(res["policy_rule_id"], "POL-PERISHABLE-TRANSIT-03")
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], 82.0)
        self.assertEqual(res["uncertainty_status"], "DETERMINISTIC_POLICY_MATCH")
        self.assertFalse(res["human_review_required"])

    def test_scenario_02_contradictory_evidence(self):
        """Case 2: Missing or contradictory evidence escalates to HUMAN_REVIEW without auto-denial."""
        case = self.benchmark_scenarios[1]
        self.assertEqual(case["complaint_id"], "SIM-CMP-02")
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "HUMAN_REVIEW")
        self.assertEqual(res["policy_rule_id"], "POL-CONTRADICTORY-EVIDENCE-08")
        self.assertEqual(res["uncertainty_status"], "CONTRADICTORY_EVIDENCE_HOLD")
        self.assertTrue(res["human_review_required"])
        self.assertGreater(len(res["evidence_assessment"]["conflicting_signals"]), 0)

    def test_scenario_03_incorrect_item_delivered(self):
        """Case 3: Incorrect item delivered with available stock receives PRIORITY_REPLACEMENT."""
        case = self.benchmark_scenarios[2]
        self.assertEqual(case["complaint_id"], "SIM-CMP-03")
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "PRIORITY_REPLACEMENT")
        self.assertEqual(res["policy_rule_id"], "POL-WRONG-ITEM-REPLACE-10")
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], 310.0)

    def test_scenario_04_minor_cosmetic_packaging_damage(self):
        """Case 4: Minor packaging damage with consumable product receives PARTIAL_COMPENSATION."""
        case = self.benchmark_scenarios[3]
        self.assertEqual(case["complaint_id"], "SIM-CMP-04")
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "PARTIAL_COMPENSATION")
        self.assertEqual(res["policy_rule_id"], "POL-COSMETIC-PARTIAL-06")
        expected_payout = round(180.0 * 0.35, 2)  # 63.00 INR
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], expected_payout)

    def test_scenario_05_repeated_complaints_supported_by_evidence(self):
        """Case 5: Repeated complaints nevertheless supported by evidence are NEVER penalized."""
        case = self.benchmark_scenarios[4]
        self.assertEqual(case["complaint_id"], "SIM-CMP-05")
        self.assertGreaterEqual(case["customer_claims_90d"], 6)
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "IMMEDIATE_REFUND")
        self.assertNotEqual(res["recommended_action"], "DENY_CLAIM")
        self.assertFalse(res["fairness_audit"]["complaint_frequency_penalized"])
        self.assertTrue(res["fairness_audit"]["automated_rejection_prohibited"])

    def test_scenario_06_high_value_ambiguous_complaint(self):
        """Case 6: High-value ambiguous complaint (> 1500 INR) escalates to HUMAN_REVIEW."""
        case = self.benchmark_scenarios[5]
        self.assertEqual(case["complaint_id"], "SIM-CMP-06")
        self.assertGreaterEqual(case["item_price_inr"], 1500.0)
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "HUMAN_REVIEW")
        self.assertEqual(res["policy_rule_id"], "POL-DISPUTE-CRITICAL-VALUE-01")
        self.assertEqual(res["uncertainty_status"], "HIGH_VALUE_AMBIGUOUS_REVIEW")

    def test_scenario_07_suspected_supplier_batch_pattern(self):
        """Case 7: Suspected supplier or batch-level pattern flags batch investigation advisory."""
        case = self.benchmark_scenarios[6]
        self.assertEqual(case["complaint_id"], "SIM-CMP-07")
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "IMMEDIATE_REFUND")
        self.assertTrue(res["supplier_intelligence"]["investigation_recommended"])
        self.assertTrue(res["financial_assessment"]["vendor_chargeback_eligible"])

    def test_scenario_08_replacement_unavailable_stockout(self):
        """Case 8: When replacement is unavailable, system falls back automatically to refund."""
        case = self.benchmark_scenarios[7]
        self.assertEqual(case["complaint_id"], "SIM-CMP-08")
        self.assertFalse(case["replacement_available"])
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "IMMEDIATE_REFUND")
        self.assertEqual(res["policy_rule_id"], "POL-REPLACEMENT-UNAVAILABLE-FALLBACK-12")
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], 140.0)

    def test_scenario_09_missing_item_value_or_cost_data(self):
        """Case 9: Missing item-value data returns 'insufficient_data' without guessing prices."""
        case = self.benchmark_scenarios[8]
        self.assertEqual(case["complaint_id"], "SIM-CMP-09")
        self.assertIsNone(case["item_price_inr"])
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        self.assertEqual(res["recommended_action"], "HUMAN_REVIEW")
        self.assertEqual(res["policy_rule_id"], "POL-MISSING-COST-DATA-09")
        self.assertEqual(res["financial_assessment"]["cost_status"], "insufficient_data")
        self.assertIsNone(res["financial_assessment"]["recommended_payout_inr"])
        self.assertEqual(res["uncertainty_status"], "INSUFFICIENT_COST_DATA")

    def test_scenario_10_malicious_prompt_injection_defense(self):
        """Case 10: Malicious or instruction-like text is sanitized and executes zero commands."""
        case = self.benchmark_scenarios[9]
        self.assertEqual(case["complaint_id"], "SIM-CMP-10")
        self.assertIn("IGNORE ALL PREVIOUS INSTRUCTIONS", case["defect_description"])
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        # Should sanitize and adjudicate genuine physical defect (creased box -> 35% partial credit)
        self.assertEqual(res["recommended_action"], "PARTIAL_COMPENSATION")
        self.assertTrue(res["untrusted_input_audit"]["adversarial_instruction_detected"])
        self.assertFalse(res["untrusted_input_audit"]["embedded_instructions_executed"])
        self.assertNotEqual(res["financial_assessment"]["recommended_payout_inr"], 10000.0)

    # =========================================================================
    # 2. SEVEN-DIMENSION BUSINESS TRADE-OFF MEASUREMENT MATRIX
    # =========================================================================

    def test_tradeoff_matrix_metrics(self):
        """Verify the 7 business trade-off dimensions across all benchmark scenarios."""
        report = COMPLAINT_SERVICE.evaluate_tradeoff_scenarios(self.benchmark_scenarios)
        self.assertEqual(report["evaluation_cohort_size"], 10)
        metrics = report["metrics"]

        # 1. Recommendation-policy compliance
        self.assertEqual(metrics["recommendation_policy_compliance_pct"], 100.0)

        # 2. Human review escalation (Cases 2, 6, 9 escalated)
        self.assertEqual(metrics["human_review_escalation_count"], 3)
        self.assertEqual(metrics["human_review_escalation_pct"], 30.0)

        # 3. False rejection rate of substantiated complaints (Must be strictly 0.0%)
        self.assertEqual(metrics["false_rejection_of_substantiated_complaints_count"], 0)
        self.assertEqual(metrics["false_rejection_rate_pct"], 0.0)

        # 4. Unnecessary compensation recommendations (0.0% on unsubstantiated/ambiguous)
        self.assertEqual(metrics["unnecessary_compensation_count"], 0)

        # 5. Average estimated compensation cost (only where calculable)
        self.assertGreater(metrics["average_estimated_compensation_inr"], 0.0)
        self.assertEqual(metrics["total_compensable_claims_count"], 7)

        # 6. Missing-data handling accuracy
        self.assertEqual(metrics["missing_data_handling_accuracy_pct"], 100.0)

        # 7. Explanation completeness
        self.assertEqual(metrics["explanation_completeness_pct"], 100.0)

        # Safeguards check
        self.assertTrue(report["safeguards_audit"]["zero_automated_rejection_enforced"])
        self.assertTrue(report["safeguards_audit"]["untrusted_code_execution_prevented"])

    # =========================================================================
    # 3. DOORSTEP DELIVERY DIAGNOSIS ENGINE TESTS
    # =========================================================================

    def test_diagnosis_bulky_handling(self):
        """Verify bulky item exception triggers BULKY_ITEM_HANDLING with ground handoff."""
        payload = {
            "delivery_attempt_id": "ATT-001",
            "order_id": "ORD-101",
            "failure_reason": "bulky_item_staircase_risk",
            "parcel_weight_kg": 22.0,
            "floor_number": 4,
            "elevator_available": False,
            "courier_vehicle": "motorcycle"
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "BULKY_ITEM_HANDLING")
        self.assertEqual(diag["recommended_safe_action"], "AUTHORIZE_GROUND_FLOOR_HANDOFF")
        self.assertEqual(diag["escalation_status"], "ERGONOMIC_SAFETY_ESCALATED")
        self.assertTrue(diag["fairness_and_safety_safeguards"]["worker_penalty_prohibited"])
        self.assertFalse(diag["fairness_and_safety_safeguards"]["delivery_success_claimed"])

    def test_diagnosis_vehicle_capacity(self):
        """Verify vehicle overload triggers VEHICLE_CAPACITY_CONSTRAINT."""
        payload = {
            "delivery_attempt_id": "ATT-002",
            "order_id": "ORD-102",
            "failure_reason": "vehicle_capacity_exceeded",
            "parcel_weight_kg": 18.0,
            "courier_vehicle": "bicycle"
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "VEHICLE_CAPACITY_CONSTRAINT")
        self.assertEqual(diag["recommended_safe_action"], "REQUEST_SUITABLE_TRANSPORT")
        self.assertEqual(diag["escalation_status"], "DISPATCH_REASSIGNMENT_REQUIRED")

    def test_diagnosis_restricted_access(self):
        """Verify gate refusal triggers RESTRICTED_ACCESS and protects courier rating."""
        payload = {
            "delivery_attempt_id": "ATT-003",
            "order_id": "ORD-103",
            "failure_reason": "security_guard_refused_entry",
            "society_access_restricted": True
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "RESTRICTED_ACCESS")
        self.assertEqual(diag["recommended_safe_action"], "ESCALATE_UNRESOLVED_ACCESS_ISSUE")

    def test_diagnosis_location_mismatch(self):
        """Verify pin discrepancy triggers LOCATION_MISMATCH with permission-based pin update."""
        payload = {
            "delivery_attempt_id": "ATT-004",
            "order_id": "ORD-104",
            "location_pin_verified": False,
            "failure_reason": "location_pin_mismatch"
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "LOCATION_MISMATCH")
        self.assertEqual(diag["recommended_safe_action"], "CORRECT_LOCATION_PIN_WITH_PERMISSION")

    def test_diagnosis_customer_unavailable(self):
        """Verify customer no-response triggers CUSTOMER_UNAVAILABLE with callback window."""
        payload = {
            "delivery_attempt_id": "ATT-005",
            "order_id": "ORD-105",
            "failure_reason": "customer_unavailable_doorbell_unanswered",
            "customer_contact_attempted": True
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "CUSTOMER_UNAVAILABLE")
        self.assertEqual(diag["recommended_safe_action"], "CONTACT_CUSTOMER")

    def test_diagnosis_unknown_safeguard(self):
        """Verify ambiguous event triggers UNKNOWN without inferring worker blame."""
        payload = {
            "delivery_attempt_id": "ATT-006",
            "order_id": "ORD-106",
            "failure_reason": "unspecified_delay",
            "customer_vicinity_meters": 200
        }
        diag = DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception(payload)
        self.assertEqual(diag["root_cause_category"], "UNKNOWN")
        self.assertEqual(diag["recommended_safe_action"], "VERIFY_INSTRUCTIONS_AND_CONTACT")
        # Prohibited inference enforced
        self.assertIn("No cause inferred", diag["fairness_and_safety_safeguards"]["prohibited_inference_enforced"])
        self.assertTrue(diag["fairness_and_safety_safeguards"]["worker_penalty_prohibited"])

    # =========================================================================
    # 4. REST API PROTOTYPE ROUTE TESTS
    # =========================================================================

    def test_api_diagnose_exception_endpoint(self):
        """Verify POST /api/prototypes/delivery-access/diagnose-exception returns structured diagnosis."""
        payload = {
            "delivery_attempt_id": "ATT-API-01",
            "order_id": "ORD-API-01",
            "failure_reason": "security_gate_denied_access",
            "society_access_restricted": True
        }
        res = self.client.post("/api/prototypes/delivery-access/diagnose-exception", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["root_cause_category"], "RESTRICTED_ACCESS")
        self.assertEqual(data["recommended_safe_action"], "ESCALATE_UNRESOLVED_ACCESS_ISSUE")
        self.assertIn("synthetic_data_disclaimer", data)

    def test_api_tradeoff_benchmarks_endpoint(self):
        """Verify GET /api/prototypes/disputes/tradeoff-benchmarks returns 7-dimension scorecard."""
        res = self.client.get("/api/prototypes/disputes/tradeoff-benchmarks")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["evaluation_cohort_size"], 10)
        self.assertEqual(data["metrics"]["recommendation_policy_compliance_pct"], 100.0)
        self.assertEqual(data["metrics"]["false_rejection_rate_pct"], 0.0)
        self.assertIn("synthetic_data_disclaimer", data)

    # =========================================================================
    # 5. INPUT VALIDATION & SAFETY REGRESSION TESTS
    # =========================================================================

    def test_delivery_validation_nan_infinity_negative(self):
        """Verify API rejects NaN, infinity, and negative physical values with HTTP 400."""
        # 1. Negative parcel weight
        payload = {"parcel_weight_kg": -5.0, "floor_number": 2}
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertTrue(data.get("validation_error"))

        # 2. String weight (non-numeric)
        payload = {"parcel_weight_kg": "twenty-two", "floor_number": 2}
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)

        # 3. Direct service call with NaN / Inf
        with self.assertRaises(ValueError):
            DELIVERY_ACCESS_SERVICE.evaluate_delivery_access({"parcel_weight_kg": float("nan")})

        with self.assertRaises(ValueError):
            DELIVERY_ACCESS_SERVICE.evaluate_delivery_access({"parcel_weight_kg": float("inf")})

        with self.assertRaises(ValueError):
            DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception({"parcel_weight_kg": -1.0})

    def test_delivery_validation_string_booleans_rejected(self):
        """Verify string booleans like 'false' or 'true' are strictly rejected with HTTP 400."""
        # String 'false' must NOT evaluate to True
        payload = {
            "parcel_weight_kg": 10.0,
            "floor_number": 2,
            "elevator_available": "false"  # String boolean attempt
        }
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("must be a strict boolean", data["message"])

        # String boolean in diagnose endpoint
        diag_payload = {
            "delivery_attempt_id": "ATT-VAL-01",
            "society_access_restricted": "true"
        }
        res_diag = self.client.post("/api/prototypes/delivery-access/diagnose-exception", json=diag_payload)
        self.assertEqual(res_diag.status_code, 400)

        # Direct service check
        with self.assertRaises(ValueError):
            DELIVERY_ACCESS_SERVICE.diagnose_delivery_exception({"customer_handover_confirmed": "false"})

    def test_delivery_validation_invalid_floor_numbers(self):
        """Verify float floors, non-numeric floors, and extreme out-of-range floors return 400."""
        # Float floor (e.g. 2.5)
        payload = {"parcel_weight_kg": 5.0, "floor_number": 2.5}
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)

        # Extreme out-of-range floor
        payload = {"parcel_weight_kg": 5.0, "floor_number": 9999}
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 400)

    def test_delivery_validation_malformed_payload(self):
        """Verify non-dictionary or empty raw body returns 400 Bad Request."""
        res = self.client.post(
            "/api/prototypes/delivery-access/evaluate",
            data="not a json object",
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)

    # =========================================================================
    # 6. COMPLAINT RECOMMENDATION SEMANTICS TESTS
    # =========================================================================

    def test_complaint_semantics_and_no_executed_payment(self):
        """Verify financial assessment clearly distinguishes recommendation from approval and execution."""
        case = self.benchmark_scenarios[0]  # Damaged perishable -> IMMEDIATE_REFUND
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        fin = res["financial_assessment"]

        # 1. Recommended compensation amount is populated
        self.assertEqual(fin["recommended_compensation_amount"], 82.0)
        self.assertEqual(fin["recommended_payout_inr"], 82.0)

        # 2. Pending human review flag
        self.assertFalse(fin["pending_human_review"])

        # 3. Approved/authorized payout is strictly None (simulation prototype)
        self.assertIsNone(fin["approved_authorized_payout"])

        # 4. Actual payment execution structure confirms NO execution
        self.assertFalse(fin["actual_payment_execution"]["payment_executed"])
        self.assertEqual(fin["actual_payment_execution"]["execution_status"], "NO_LIVE_GATEWAY_INTEGRATED")
        self.assertIsNone(fin["actual_payment_execution"]["transaction_id"])

        # 5. Customer explanation does NOT state that payment was executed or credited
        cust_exp = res["explainability"]["customer_facing_explanation"]
        self.assertNotIn("credited to your account", cust_exp.lower())
        self.assertNotIn("initiated a full refund", cust_exp.lower())
        self.assertNotIn("credited to your wallet", cust_exp.lower())
        self.assertIn("recommend", cust_exp.lower())

    def test_complaint_human_review_semantics(self):
        """Verify human-review cases clearly set pending_human_review and no approved payout."""
        case = self.benchmark_scenarios[1]  # Contradictory evidence -> HUMAN_REVIEW
        res = COMPLAINT_SERVICE.evaluate_complaint(case)
        fin = res["financial_assessment"]

        self.assertTrue(fin["pending_human_review"])
        self.assertIsNone(fin["approved_authorized_payout"])
        self.assertFalse(fin["actual_payment_execution"]["payment_executed"])

    def test_delivery_access_frontend_payload_endpoint(self):
        """Verify API evaluates exact frontend form payload with complete contract parity."""
        # Exact payload sent by getAccessFormPayload() for ACC-001 (22.5kg, Fl 4, No lift, No hazard)
        payload = {
            "parcel_weight_kg": 22.5,
            "floor_number": 4,
            "elevator_available": False,
            "gate_security_required": False,
            "gate_code_required": False,
            "hazard_reported": None,
            "customer_vicinity_meters": 120.0,
            "courier_distance_meters": 120.0
        }
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertEqual(data["decision"], "UNSAFE_PHYSICAL_TASK_ESCALATION")
        self.assertFalse(data["is_doorstep_safe"])
        self.assertTrue(data["ground_floor_handoff_authorized"])
        self.assertTrue(data["courier_penalty_protection"])
        self.assertFalse(data["pre_arrival_brief_pushed"])
        self.assertIn("violates solitary manual carry", data["decision_reason"])
        self.assertIn("NOT expected to carry", data["courier_action_brief"])
        self.assertIn("heavy items", data["customer_coordination_message"])
        self.assertNotIn("undefined", data["customer_coordination_message"])

    def test_adjudication_frontend_spoiled_perishable_contract_parity(self):
        """Verify normal spoiled-perishable complaint returns populated decision, rationale, and customer communication."""
        # Exact payload sent by getAdjudicationFormPayload()
        payload = {
            "item_name": "Organic Farm Fresh Milk 1L",
            "item_category": "dairy_chilled",
            "item_price_inr": 85.0,
            "complaint_category": "spoiled_perishable",
            "evidence_attached": True,
            "customer_claims_90d": 2,
            "delivery_delay_minutes": 22.0,
            "ambient_temp_c": 34.0
        }
        res = self.client.post("/api/prototypes/disputes/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # 1. Main action & status
        self.assertEqual(data["adjudication_status"], "RECOMMENDED_BY_POLICY")
        self.assertEqual(data["recommended_action"], "IMMEDIATE_REFUND")
        self.assertFalse(data["human_review_required"])

        # 2. Policy rationale is populated both top-level and nested
        self.assertIn("policy_rationale", data)
        self.assertIn("decision_reason", data)
        self.assertIn("decision_rationale", data["explainability"])
        self.assertIn("thermal stress", data["policy_rationale"].lower())
        self.assertNotIn("undefined", data["policy_rationale"])

        # 3. Customer communication preview is populated both top-level and nested
        self.assertIn("customer_plain_language_explanation", data)
        self.assertIn("customer_facing_explanation", data["explainability"])
        self.assertIn("refund recommendation", data["customer_plain_language_explanation"].lower())
        self.assertNotIn("undefined", data["customer_plain_language_explanation"])

        # 4. Financial assessment fields
        fin = data["financial_assessment"]
        self.assertEqual(fin["recommended_payout_inr"], 85.0)
        self.assertEqual(fin["payout_percentage"], 100)
        self.assertEqual(fin["settlement_channel"], "ORIGINAL_PAYMENT (RECOMMENDED)")
        self.assertFalse(fin["pending_human_review"])
        self.assertIsNone(fin["approved_authorized_payout"])
        self.assertFalse(fin["actual_payment_execution"]["payment_executed"])

    def test_adjudication_missing_optional_explanation_and_safe_fallback(self):
        """Verify service and responses handle optional or missing text safely without 'undefined'."""
        payload = {
            "item_name": "Fresh Paneer 200g",
            "item_category": "dairy_chilled",
            "item_price_inr": 90.0,
            "complaint_category": "spoiled_perishable",
            "evidence_attached": False,
            "customer_claims_90d": 0,
            "delivery_delay_minutes": 5.0,
            "ambient_temp_c": 28.0
        }
        res = self.client.post("/api/prototypes/disputes/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # Rationale and customer explanation must be valid non-empty strings, never None or 'undefined'
        self.assertIsInstance(data.get("policy_rationale"), str)
        self.assertGreater(len(data["policy_rationale"]), 0)
        self.assertNotIn("undefined", data["policy_rationale"])

        self.assertIsInstance(data.get("customer_plain_language_explanation"), str)
        self.assertGreater(len(data["customer_plain_language_explanation"]), 0)
        self.assertNotIn("undefined", data["customer_plain_language_explanation"])

    def test_adjudication_human_review_not_represented_as_authorized_payout(self):
        """Verify human-review result is not represented as an executed or authorized payment."""
        # Case 2: Contradictory evidence
        payload = {
            "item_name": "Cold-Pressed Mustard Oil 1L",
            "item_category": "packaged_ambient",
            "item_price_inr": 240.0,
            "complaint_category": "broken_glass",
            "evidence_attached": True,
            "contradictory_evidence": True,
            "customer_claims_90d": 0
        }
        res = self.client.post("/api/prototypes/disputes/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertEqual(data["recommended_action"], "HUMAN_REVIEW")
        self.assertTrue(data["human_review_required"])

        fin = data["financial_assessment"]
        self.assertTrue(fin["pending_human_review"])
        self.assertIsNone(fin["approved_authorized_payout"])
        self.assertFalse(fin["actual_payment_execution"]["payment_executed"])
        self.assertEqual(fin["settlement_channel"], "ON_HOLD (HUMAN_REVIEW)")

        # Customer message must explicitly state no payment was authorized or processed
        cust_msg = data["customer_plain_language_explanation"]
        self.assertIn("no refund has been processed", cust_msg.lower())
        self.assertNotIn("credited", cust_msg.lower())
        self.assertNotIn("transferred", cust_msg.lower())

    def test_adjudication_frontend_consumed_field_keys(self):
        """Verify exact field keys consumed by renderAdjudicationDecision are strictly present."""
        payload = {
            "item_name": "Brown Eggs 6-Pack",
            "item_category": "dairy_chilled",
            "item_price_inr": 65.0,
            "complaint_category": "broken_damaged_eggs",
            "evidence_attached": True
        }
        res = self.client.post("/api/prototypes/disputes/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        # Fields accessed by renderAdjudicationDecision in static/js/command_centre.js
        required_keys = [
            "adjudication_status",
            "recommended_action",
            "policy_rationale",
            "decision_reason",
            "customer_plain_language_explanation",
            "financial_assessment",
            "fairness_audit",
            "explainability",
            "human_review_required"
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing required frontend key: {key}")

        fin = data["financial_assessment"]
        self.assertIn("recommended_payout_inr", fin)
        self.assertIn("settlement_channel", fin)
        self.assertIn("payout_percentage", fin)
        self.assertIn("pending_human_review", fin)
        self.assertIn("approved_authorized_payout", fin)
        self.assertIn("actual_payment_execution", fin)

        exp = data["explainability"]
        self.assertIn("decision_rationale", exp)
        self.assertIn("customer_facing_explanation", exp)

    def test_complaint_scenarios_dropdown_contract(self):
        """Verify GET /api/prototypes/disputes/scenarios returns all 20 scenarios matching dropdown option schema."""
        res = self.client.get("/api/prototypes/disputes/scenarios")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)

        self.assertEqual(data.get("total_scenarios"), 20)
        scenarios = data.get("scenarios", [])
        self.assertEqual(len(scenarios), 20)

        # Check unique IDs and all required fields for dropdown label rendering
        scenario_ids = set()
        for s in scenarios:
            self.assertIn("complaint_id", s)
            self.assertIn("item_name", s)
            self.assertIn("item_price_inr", s)
            self.assertIn("complaint_category", s)

            cid = s["complaint_id"]
            self.assertNotIn(cid, scenario_ids, f"Duplicate scenario ID found: {cid}")
            scenario_ids.add(cid)

            # Option format: `${c.complaint_id} — ${c.item_name} (₹${c.item_price_inr}, ${c.complaint_category})`
            label = f"{s['complaint_id']} — {s['item_name']} (₹{s['item_price_inr']}, {s['complaint_category']})"
            self.assertNotIn("undefined", label)
            self.assertNotIn("null", label)

        # Default initial scenario (index 0)
        default_scenario = scenarios[0]
        self.assertEqual(default_scenario["complaint_id"], "CMP-001")
        self.assertEqual(default_scenario["item_name"], "Organic Farm Fresh Milk 1L")
        self.assertEqual(default_scenario["item_price_inr"], 85.0)

    def test_complaint_dropdown_frontend_js_wiring(self):
        """Verify static/js/command_centre.js wiring: bootstrap init, shared promise, and retry handling."""
        js_path = os.path.join(WORKSPACE_DIR, "static", "js", "command_centre.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # 1. loadAdjudicationScenarios must be in init() Promise.allSettled
        self.assertIn("loadAdjudicationScenarios()", js_content)
        self.assertIn("loadDisputeScenarios(),\n      loadAdjudicationScenarios()", js_content)

        # 2. switchTab must check for unpopulated dropdown options <= 1
        self.assertIn("if (!dom.selectAdjudicationScenario || dom.selectAdjudicationScenario.options.length <= 1) loadAdjudicationScenarios();", js_content)

        # 3. Shared fetchComplaintScenarios to prevent duplicate network calls
        self.assertIn("fetchComplaintScenarios()", js_content)
        self.assertIn("complaintScenariosPromise", js_content)

        # 4. Error state must provide __retry__ option
        self.assertIn('__retry__', js_content)
        self.assertIn("⚠️ Error loading scenarios — click to retry", js_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
