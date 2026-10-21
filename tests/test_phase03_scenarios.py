"""
MacroOps AI — Phase 03 Part 02: Supervisor Scenario QA Test Suite
==================================================================
Automated regression tests covering:
1. Scenario 1: Delivery location, doorstep access, bulky-item weight limits, and courier safety.
2. Scenario 2: Defective products, bruised fruits, perishable cold-chain, and supplier batch investigation.
3. Scenario 3: Transparent 5-tier fair compensation policy, anti-bias invariants, and zero automated denials.
4. Prototype REST API endpoints and Ava AI Copilot intent routing.
"""

import sys
import os
import unittest
import json

# Ensure workspace is in sys.path
WORKSPACE_DIR = r"c:\Users\HP\Desktop\MacroOps"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from app import app, DELIVERY_ACCESS_SERVICE, COMPLAINT_SERVICE, ASSISTANT_SERVICE


class TestPhase03SupervisorScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    # =========================================================================
    # 1. SCENARIO 1: DELIVERY LOCATION & COURIER SAFETY SERVICE TESTS
    # =========================================================================
    def test_01_bulky_walkup_escalation(self):
        """Verify bulky item (>15kg) to upper floor walkup triggers UNSAFE_PHYSICAL_TASK_ESCALATION."""
        payload = {
            "parcel_weight_kg": 22.5,
            "floor_number": 4,
            "elevator_available": False,
            "courier_vehicle": "two_wheeler_motorcycle"
        }
        res = DELIVERY_ACCESS_SERVICE.evaluate_delivery_access(payload)
        self.assertEqual(res["decision"], "UNSAFE_PHYSICAL_TASK_ESCALATION")
        self.assertFalse(res["is_doorstep_safe"])
        self.assertGreaterEqual(res["ergonomic_risk_score"], 0.8)
        self.assertEqual(res["policy_rule_id"], "SAF-BULKY-WALKUP-02")
        self.assertIn("violates solitary manual carry", res["instructions_summary"])

    def test_02_physical_hazard_coordination(self):
        """Verify courier physical hazard reports trigger CUSTOMER_COORDINATION_REQUIRED."""
        payload = {
            "parcel_weight_kg": 3.0,
            "floor_number": 1,
            "elevator_available": False,
            "hazard_reported": "aggressive_dog_in_courtyard"
        }
        res = DELIVERY_ACCESS_SERVICE.evaluate_delivery_access(payload)
        self.assertEqual(res["decision"], "CUSTOMER_COORDINATION_REQUIRED")
        self.assertFalse(res["is_doorstep_safe"])
        self.assertIn("aggressive_dog_in_courtyard", res["instructions_summary"])

    def test_03_facility_ground_floor_handoff(self):
        """Verify commercial concierge / society rules authorize GROUND_FLOOR_HANDOFF."""
        payload = {
            "parcel_weight_kg": 5.0,
            "floor_number": 12,
            "elevator_available": True,
            "access_notes": "Drop at ground floor reception; couriers not allowed on upper floors."
        }
        res = DELIVERY_ACCESS_SERVICE.evaluate_delivery_access(payload)
        self.assertEqual(res["decision"], "GROUND_FLOOR_HANDOFF_AUTHORIZED")
        self.assertTrue(res["is_doorstep_safe"])

    def test_04_gated_community_access_brief(self):
        """Verify gated community with pass code triggers PRE_ARRIVAL_ACCESS_BRIEF."""
        payload = {
            "parcel_weight_kg": 4.0,
            "floor_number": 5,
            "elevator_available": True,
            "gate_security_required": True,
            "gate_code": "GATE-9912"
        }
        res = DELIVERY_ACCESS_SERVICE.evaluate_delivery_access(payload)
        self.assertEqual(res["decision"], "PRE_ARRIVAL_ACCESS_BRIEF")
        self.assertIn("GATE-9912", res["instructions_summary"])

    def test_05_standard_safe_doorstep_delivery(self):
        """Verify standard delivery within ergonomic limits triggers SAFE_DOORSTEP_PROCEED."""
        payload = {
            "parcel_weight_kg": 2.5,
            "floor_number": 2,
            "elevator_available": True,
            "gate_security_required": False
        }
        res = DELIVERY_ACCESS_SERVICE.evaluate_delivery_access(payload)
        self.assertEqual(res["decision"], "SAFE_DOORSTEP_PROCEED")
        self.assertTrue(res["is_doorstep_safe"])

    # =========================================================================
    # 2. SCENARIO 2 & 3: QUALITY DISPUTES & FAIR COMPENSATION TESTS
    # =========================================================================
    def test_06_perishable_coldchain_refund(self):
        """Verify spoiled perishable with delivery delay receives IMMEDIATE_REFUND."""
        payload = {
            "sku_id": "SKU-PROD-019",
            "item_name": "Organic Farm Fresh Milk 1L",
            "item_category": "dairy_chilled",
            "item_price_inr": 85.0,
            "complaint_category": "spoiled_perishable",
            "evidence_attached": True,
            "delivery_delay_minutes": 22.0,
            "ambient_temp_c": 34.0
        }
        res = COMPLAINT_SERVICE.evaluate_complaint(payload)
        self.assertEqual(res["recommended_action"], "IMMEDIATE_REFUND")
        self.assertEqual(res["adjudication_status"], "RECOMMENDED_BY_POLICY")
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], 85.0)

    def test_07_cosmetic_damaged_packaging_partial_credit(self):
        """Verify minor packaging dent on ambient goods receives PARTIAL_COMPENSATION."""
        payload = {
            "sku_id": "SKU-CEREAL-012",
            "item_name": "Multi-Grain Corn Flakes 750g",
            "item_category": "packaged_ambient",
            "item_price_inr": 200.0,
            "complaint_category": "damaged_packaging",
            "defect_description": "Cardboard box slightly dented, pouch sealed",
            "evidence_attached": True
        }
        res = COMPLAINT_SERVICE.evaluate_complaint(payload)
        self.assertEqual(res["recommended_action"], "PARTIAL_COMPENSATION")
        self.assertGreater(res["financial_assessment"]["recommended_payout_inr"], 0.0)
        self.assertLess(res["financial_assessment"]["recommended_payout_inr"], 200.0)

    def test_08_missing_evidence_on_high_value_item(self):
        """Verify unverified claim on goods > 500 INR triggers REQUEST_EVIDENCE."""
        payload = {
            "sku_id": "SKU-OIL-008",
            "item_name": "Extra Virgin Olive Oil 1L",
            "item_category": "packaged_ambient",
            "item_price_inr": 850.0,
            "evidence_attached": False
        }
        res = COMPLAINT_SERVICE.evaluate_complaint(payload)
        self.assertEqual(res["recommended_action"], "REQUEST_EVIDENCE")
        self.assertEqual(res["financial_assessment"]["recommended_payout_inr"], 0.0)

    def test_09_critical_value_dispute_human_review(self):
        """Verify dispute on critical item (> 1500 INR) triggers HUMAN_REVIEW."""
        payload = {
            "sku_id": "SKU-ELEC-002",
            "item_name": "Wireless Earbuds Quick-Commerce Exclusive",
            "item_category": "electronics",
            "item_price_inr": 2499.0,
            "evidence_attached": True
        }
        res = COMPLAINT_SERVICE.evaluate_complaint(payload)
        self.assertEqual(res["recommended_action"], "HUMAN_REVIEW")

    def test_10_fairness_invariant_anti_bias(self):
        """Verify high complaint frequency alone NEVER triggers automated rejection."""
        payload = {
            "customer_id": "CUST-FREQ-01",
            "customer_orders_90d": 20,
            "customer_claims_90d": 6,  # 30% claim frequency
            "sku_id": "SKU-FRUIT-004",
            "item_name": "Alphonso Mangoes (Pack of 3)",
            "item_category": "perishable_produce",
            "item_price_inr": 340.0,
            "complaint_category": "spoiled_perishable",
            "evidence_attached": True,
            "delivery_delay_minutes": 25.0
        }
        res = COMPLAINT_SERVICE.evaluate_complaint(payload)
        # Must approve valid perishable or escalate to human review; NEVER deny automatically
        self.assertIn(res["recommended_action"], ["IMMEDIATE_REFUND", "HUMAN_REVIEW"])
        self.assertNotEqual(res["recommended_action"], "DENY_CLAIM")
        self.assertTrue(res["fairness_audit"]["automated_rejection_prohibited"])

    def test_11_supplier_batch_investigation_aggregation(self):
        """Verify supplier batch cluster analysis triggers RECOMMEND_SUPPLIER_BATCH_INVESTIGATION."""
        investigations = COMPLAINT_SERVICE.get_batch_investigation_summary()
        self.assertIsInstance(investigations, list)
        self.assertGreater(len(investigations), 0)
        
        # Batch BATCH-DAIRY-B102 has 3 synthetic complaints
        dairy_batch = next((b for b in investigations if b["batch_id"] == "BATCH-DAIRY-B102"), None)
        self.assertIsNotNone(dairy_batch)
        self.assertEqual(dairy_batch["recommendation"], "RECOMMEND_SUPPLIER_BATCH_INVESTIGATION")
        self.assertGreaterEqual(dairy_batch["complaint_count"], 2)

    # =========================================================================
    # 3. REST API PROTOTYPE ENDPOINT TESTS
    # =========================================================================
    def test_12_api_delivery_access_scenarios(self):
        """Verify GET /api/prototypes/delivery-access/scenarios returns all 25 scenarios."""
        res = self.client.get("/api/prototypes/delivery-access/scenarios")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["total_scenarios"], 25)
        self.assertEqual(len(data["scenarios"]), 25)

    def test_13_api_delivery_access_evaluate(self):
        """Verify POST /api/prototypes/delivery-access/evaluate returns structured safety assessment."""
        payload = {
            "parcel_weight_kg": 20.0,
            "floor_number": 4,
            "elevator_available": False
        }
        res = self.client.post("/api/prototypes/delivery-access/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["decision"], "UNSAFE_PHYSICAL_TASK_ESCALATION")

    def test_14_api_disputes_scenarios(self):
        """Verify GET /api/prototypes/disputes/scenarios returns all 20 complaint scenarios."""
        res = self.client.get("/api/prototypes/disputes/scenarios")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["total_scenarios"], 20)
        self.assertEqual(len(data["scenarios"]), 20)

    def test_15_api_disputes_evaluate(self):
        """Verify POST /api/prototypes/disputes/evaluate returns explainable 5-tier recommendation."""
        payload = {
            "sku_id": "SKU-PROD-019",
            "item_name": "Organic Milk 1L",
            "item_category": "dairy_chilled",
            "item_price_inr": 85.0,
            "complaint_category": "spoiled_perishable",
            "evidence_attached": True,
            "delivery_delay_minutes": 20.0
        }
        res = self.client.post("/api/prototypes/disputes/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["recommended_action"], "IMMEDIATE_REFUND")
        self.assertEqual(data["adjudication_status"], "RECOMMENDED_BY_POLICY")

    def test_16_api_disputes_batch_investigations(self):
        """Verify GET /api/prototypes/disputes/batch-investigations returns supplier clusters."""
        res = self.client.get("/api/prototypes/disputes/batch-investigations")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertGreater(data["total_batches_monitored"], 0)
        self.assertIn("batch_investigations", data)

    # =========================================================================
    # 4. AVA AI COPILOT INTENT ROUTING TESTS
    # =========================================================================
    def test_17_assistant_doorstep_access_query(self):
        """Verify Ava responds with grounded courier safety policy on doorstep access queries."""
        res = self.client.post("/api/assistant/chat", json={"message": "What is our policy on doorstep access and courier safety?"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["intent"], "DELIVERY_ACCESS_INTELLIGENCE")
        self.assertIn("15.0 kg", data["evidence"]["max_unassisted_walkup_weight"])

    def test_18_assistant_quality_dispute_query(self):
        """Verify Ava explains the 5-tier fair compensation policy and anti-bias rules."""
        res = self.client.post("/api/assistant/chat", json={"message": "Explain our fair compensation policy for quality disputes and bruised fruit"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["intent"], "COMPLAINT_ADJUDICATION_POLICY")
        self.assertIn("IMMEDIATE_REFUND", data["evidence"]["policy_actions"])

    def test_19_assistant_batch_investigation_query(self):
        """Verify Ava reports supplier batch defect clusters when asked about batch investigations."""
        res = self.client.post("/api/assistant/chat", json={"message": "Show supplier batch investigations and defective batch reports"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["intent"], "SUPPLIER_BATCH_INVESTIGATION")


if __name__ == "__main__":
    unittest.main()
