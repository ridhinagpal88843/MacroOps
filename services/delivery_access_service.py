"""
MacroOps AI — Delivery Location & Doorstep Access Assistance Service
=====================================================================
Models real-world quick-commerce vicinity arrivals, building access barriers,
bulky-item ergonomics, and courier safety protocols.

Core Safety & Policy Invariants:
  1. Courier Safety First: Never assume a delivery partner should always carry items
     farther or that a doorstep delivery is always physically safe or possible.
  2. Solitary Carry Limits: Loads > 15 kg without elevator access above Floor 2
     automatically escalate to prevent ergonomic injury.
  3. Ground-Floor Authorization: Society / office rules prohibiting external couriers
     authorize ground-floor handovers immediately without penalizing the delivery partner.
  4. Truth in Engineering: All locations, access notes, and proximity metrics represent
     simulated analytical scenario prototypes. Does not claim physical courier vehicle reassignment.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("macroops_delivery_access")


class DeliveryAccessService:
    """Service evaluating vicinity arrivals, doorstep accessibility, and courier safety."""

    DEFAULT_SCENARIOS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "scenario_prototypes", "synthetic_access_scenarios.json"
    )

    # Ergonomic & safety thresholds
    MAX_UNASSISTED_WALKUP_WEIGHT_KG = 15.0
    MAX_WALKUP_FLOORS_WITHOUT_LIFT = 2
    MAX_BICYCLE_PAYLOAD_KG = 15.0
    PROXIMITY_VICINITY_THRESHOLD_M = 100

    def __init__(self, scenarios_path: Optional[str] = None):
        self.scenarios_path = scenarios_path or self.DEFAULT_SCENARIOS_PATH
        self._scenarios_cache: List[Dict[str, Any]] = []
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load synthetic access scenarios from the isolated prototype directory."""
        if os.path.exists(self.scenarios_path):
            try:
                with open(self.scenarios_path, "r", encoding="utf-8") as f:
                    self._scenarios_cache = json.load(f)
                logger.info(f"Loaded {len(self._scenarios_cache)} access scenarios from {self.scenarios_path}")
            except Exception as e:
                logger.error(f"Failed to load access scenarios: {e}")
                self._scenarios_cache = []
        else:
            logger.warning(f"Access scenarios file not found at {self.scenarios_path}")
            self._scenarios_cache = []

    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Return all available synthetic access scenarios."""
        return self._scenarios_cache

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Find a scenario by its ID."""
        for sc in self._scenarios_cache:
            if sc.get("scenario_id") == scenario_id:
                return sc
        return None

    def evaluate_delivery_access(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate real-time delivery location, building access barriers, and courier safety.
        Returns a structured advisory recommendation and ergonomic safety assessment.
        """
        weight_kg = float(payload.get("parcel_weight_kg", 0.0))
        volume_liters = float(payload.get("parcel_volume_liters", 0.0))
        floor = int(payload.get("floor_number", 1))
        elevator = bool(payload.get("elevator_available", False))
        courier_vehicle = str(payload.get("courier_vehicle", "two_wheeler_motorcycle")).lower()
        vicinity_meters = int(payload.get("customer_vicinity_meters", 50))
        gate_security = bool(payload.get("gate_security_required", False))
        gate_code = payload.get("gate_code")
        hazard = payload.get("hazard_reported")
        access_notes = payload.get("access_notes", "")
        customer_name = payload.get("customer_name", "Customer")
        order_id = payload.get("order_id", "ORD-UNKNOWN")

        # ---------------------------------------------------------------------
        # 1. Active Physical Hazard Assessment
        # ---------------------------------------------------------------------
        if hazard:
            hazard_clean = str(hazard).lower()
            return {
                "decision": "CUSTOMER_COORDINATION_REQUIRED",
                "safety_tier": "HIGH_HAZARD_ALERT",
                "action_title": "Courier Safety Hazard Detected — Hold Entry",
                "instructions_summary": f"Hazard reported: '{hazard}'. Courier is instructed to halt at perimeter. Immediate customer coordination triggered.",
                "courier_guidance": "Do not enter private premises. Wait at safe perimeter location. Support desk is contacting customer.",
                "customer_prompt": f"Your delivery partner has reached your vicinity but noted: '{hazard}'. Please assist with safe access.",
                "ergonomic_risk_score": 0.85,
                "is_doorstep_safe": False,
                "recommended_handoff_location": "Secured Perimeter / Main Gate",
                "policy_rule_id": "SAF-HAZARD-01",
                "disclaimer": "Simulated vicinity intelligence prototype. Prioritizes worker safety over speed."
            }

        # ---------------------------------------------------------------------
        # 2. Bulky Parcel Ergonomic Safety Evaluation
        # ---------------------------------------------------------------------
        is_heavy_walkup = (weight_kg > self.MAX_UNASSISTED_WALKUP_WEIGHT_KG) and (not elevator) and (floor > self.MAX_WALKUP_FLOORS_WITHOUT_LIFT)
        is_vehicle_overload = (courier_vehicle == "bicycle") and (weight_kg > self.MAX_BICYCLE_PAYLOAD_KG)

        if is_heavy_walkup or is_vehicle_overload:
            reason = []
            if is_heavy_walkup:
                reason.append(f"Parcel weight ({weight_kg:.1f}kg) to Floor {floor} without elevator violates solitary manual carry safety limits.")
            if is_vehicle_overload:
                reason.append(f"Vehicle type '{courier_vehicle}' overloaded by {weight_kg:.1f}kg payload.")

            return {
                "decision": "UNSAFE_PHYSICAL_TASK_ESCALATION",
                "safety_tier": "CRITICAL_ERGONOMIC_RISK",
                "action_title": "Ergonomic Hazard — Escalated for Coordination / Ground Meetup",
                "instructions_summary": " ".join(reason),
                "courier_guidance": "You are NOT expected to carry this heavy load up the staircase. Dispatch has authorized customer ground meetup or two-person support.",
                "customer_prompt": f"Your order contains heavy items ({weight_kg:.1f}kg) with no elevator access to Floor {floor}. Please meet the delivery partner at the ground floor or building entrance.",
                "ergonomic_risk_score": 0.95,
                "is_doorstep_safe": False,
                "recommended_handoff_location": "Ground Floor Entrance / Building Foyer",
                "policy_rule_id": "SAF-BULKY-WALKUP-02",
                "disclaimer": "Safety policy strictly protects couriers from unassisted heavy manual lifting."
            }

        # ---------------------------------------------------------------------
        # 3. Ground-Floor Authorized Protocols (Society / Commercial Rules)
        # ---------------------------------------------------------------------
        notes_lower = access_notes.lower()
        if "reception" in notes_lower or "concierge" in notes_lower or "society ground" in notes_lower or "not allowed on upper" in notes_lower:
            return {
                "decision": "GROUND_FLOOR_HANDOFF_AUTHORIZED",
                "safety_tier": "STANDARD_FACILITY_PROTOCOL",
                "action_title": "Facility Policy: Ground Floor / Concierge Handover",
                "instructions_summary": "Building security rules mandate external delivery handoff at ground floor reception or concierge desk.",
                "courier_guidance": "Deliver directly to ground floor desk/concierge. No upper-floor transit required.",
                "customer_prompt": "Your building management requires deliveries to be received at the ground floor concierge.",
                "ergonomic_risk_score": 0.10,
                "is_doorstep_safe": True,
                "recommended_handoff_location": "Ground Floor Reception / Security Desk",
                "policy_rule_id": "POL-RECEPTION-HANDOFF-03",
                "disclaimer": "Verified facility access rule honored."
            }

        # ---------------------------------------------------------------------
        # 4. Gated Community Pre-Arrival Access Brief
        # ---------------------------------------------------------------------
        if gate_security or gate_code:
            code_text = f"Entry Code: {gate_code}" if gate_code else "State customer flat number at security gate."
            return {
                "decision": "PRE_ARRIVAL_ACCESS_BRIEF",
                "safety_tier": "COORDINATED_ACCESS",
                "action_title": "Gated Complex Access Brief Available",
                "instructions_summary": f"Security verification required. {code_text} Access notes: {access_notes}",
                "courier_guidance": f"Show security boom guard {code_text}. Proceed to designated tower elevator.",
                "customer_prompt": f"Your delivery partner is approaching the main gate ({vicinity_meters}m away).",
                "ergonomic_risk_score": 0.25,
                "is_doorstep_safe": True,
                "recommended_handoff_location": f"Doorstep (Floor {floor}) via Elevator",
                "policy_rule_id": "POL-GATE-BRIEF-04",
                "disclaimer": "Pre-arrival access brief eliminates gate wait times."
            }

        # ---------------------------------------------------------------------
        # 5. Standard Safe Doorstep Handover
        # ---------------------------------------------------------------------
        return {
            "decision": "SAFE_DOORSTEP_PROCEED",
            "safety_tier": "OPTIMAL_LOW_FRICTION",
            "action_title": "Clear Doorstep Handover Authorized",
            "instructions_summary": f"Access clear. Parcel ({weight_kg:.1f}kg) is within safe handling thresholds. Floor: {floor}.",
            "courier_guidance": f"Proceed to doorstep on Floor {floor}. Note customer preference: '{access_notes or 'Ring bell once'}'",
            "customer_prompt": "Your delivery partner has arrived in your vicinity and is proceeding to your doorstep.",
            "ergonomic_risk_score": 0.15,
            "is_doorstep_safe": True,
            "recommended_handoff_location": f"Customer Doorstep (Floor {floor})",
            "policy_rule_id": "POL-STANDARD-DOORSTEP-05",
            "disclaimer": "Standard low-friction doorstep delivery."
        }
