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
import math
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

    @staticmethod
    def _validate_float(
        val: Any,
        field_name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allow_none: bool = True
    ) -> Optional[float]:
        """Validate numeric float values strictly against types, finiteness, and bounds."""
        if val is None:
            if allow_none:
                return None
            raise ValueError(f"Field '{field_name}' is required and cannot be null.")
        if isinstance(val, bool):
            raise ValueError(f"Field '{field_name}' must be a number, not a boolean ({val}).")
        if not isinstance(val, (int, float)):
            raise ValueError(f"Field '{field_name}' must be numeric (int or float), got {type(val).__name__}: '{val}'.")
        fval = float(val)
        if not math.isfinite(fval):
            raise ValueError(f"Field '{field_name}' must be a finite number (NaN, Infinity, or -Infinity are not permitted).")
        if min_val is not None and fval < min_val:
            raise ValueError(f"Field '{field_name}' ({fval}) cannot be less than {min_val}.")
        if max_val is not None and fval > max_val:
            raise ValueError(f"Field '{field_name}' ({fval}) cannot exceed {max_val}.")
        return fval

    @staticmethod
    def _validate_int(
        val: Any,
        field_name: str,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        allow_none: bool = True
    ) -> Optional[int]:
        """Validate integer values strictly against types and bounds."""
        if val is None:
            if allow_none:
                return None
            raise ValueError(f"Field '{field_name}' is required and cannot be null.")
        if isinstance(val, bool):
            raise ValueError(f"Field '{field_name}' must be an integer, not a boolean ({val}).")
        if not isinstance(val, int):
            raise ValueError(f"Field '{field_name}' must be an integer, got {type(val).__name__}: '{val}'.")
        if min_val is not None and val < min_val:
            raise ValueError(f"Field '{field_name}' ({val}) cannot be less than {min_val}.")
        if max_val is not None and val > max_val:
            raise ValueError(f"Field '{field_name}' ({val}) cannot exceed {max_val}.")
        return val

    @staticmethod
    def _validate_bool(
        val: Any,
        field_name: str,
        allow_none: bool = True
    ) -> Optional[bool]:
        """Validate boolean values strictly; string booleans ('true'/'false') are strictly rejected."""
        if val is None:
            if allow_none:
                return None
            raise ValueError(f"Field '{field_name}' is required and cannot be null.")
        if isinstance(val, str):
            raise ValueError(
                f"Field '{field_name}' must be a strict boolean (true or false), not a string '{val}'. "
                "Coercing strings to booleans is prohibited by safety policy."
            )
        if not isinstance(val, bool):
            raise ValueError(f"Field '{field_name}' must be a strict boolean, got {type(val).__name__}: '{val}'.")
        return val

    def evaluate_delivery_access(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate real-time delivery location, building access barriers, and courier safety.
        Returns a structured advisory recommendation and ergonomic safety assessment.
        """
        if payload is None or not isinstance(payload, dict):
            raise ValueError("Request payload must be a non-null dictionary.")

        raw_weight = payload.get("parcel_weight_kg")
        weight_kg = self._validate_float(raw_weight, "parcel_weight_kg", min_val=0.0, max_val=150.0, allow_none=False)
        assert weight_kg is not None

        raw_volume = payload.get("parcel_volume_liters", 0.0)
        volume_liters = self._validate_float(raw_volume, "parcel_volume_liters", min_val=0.0, max_val=1000.0, allow_none=True) or 0.0

        raw_floor = payload.get("floor_number", 1)
        floor = self._validate_int(raw_floor, "floor_number", min_val=-5, max_val=200, allow_none=False)
        assert floor is not None

        raw_elevator = payload.get("elevator_available", False)
        elevator = self._validate_bool(raw_elevator, "elevator_available", allow_none=False)
        assert elevator is not None

        courier_vehicle = str(payload.get("courier_vehicle", "two_wheeler_motorcycle") or "").lower()

        raw_vicinity = payload.get("customer_vicinity_meters")
        if raw_vicinity is None:
            raw_vicinity = payload.get("courier_distance_meters", 50)
        vicinity_meters = self._validate_float(raw_vicinity, "customer_vicinity_meters", min_val=0.0, max_val=50000.0, allow_none=False)
        assert vicinity_meters is not None

        raw_gate_sec = payload.get("gate_security_required")
        if raw_gate_sec is None:
            raw_gate_sec = payload.get("gate_code_required", False)
        gate_security = self._validate_bool(raw_gate_sec, "gate_security_required", allow_none=False)
        assert gate_security is not None

        gate_code = payload.get("gate_code")
        raw_hazard = payload.get("hazard_reported")
        hazard = None
        if raw_hazard is not None and not isinstance(raw_hazard, bool):
            hazard_str = str(raw_hazard).strip()
            if hazard_str.lower() not in ["none", "null", "false", "", "0"]:
                hazard = hazard_str

        access_notes = str(payload.get("access_notes", "") or "")
        customer_name = str(payload.get("customer_name", "Customer") or "Customer")
        order_id = str(payload.get("order_id", "ORD-UNKNOWN") or "ORD-UNKNOWN")

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
                "decision_reason": f"Hazard reported: '{hazard}'. Courier is instructed to halt at perimeter. Immediate customer coordination triggered.",
                "courier_guidance": "Do not enter private premises. Wait at safe perimeter location. Support desk is contacting customer.",
                "courier_action_brief": "Do not enter private premises. Wait at safe perimeter location. Support desk is contacting customer.",
                "customer_prompt": f"Your delivery partner has reached your vicinity but noted: '{hazard}'. Please assist with safe access.",
                "customer_coordination_message": f"Your delivery partner has reached your vicinity but noted: '{hazard}'. Please assist with safe access.",
                "ergonomic_risk_score": 0.85,
                "is_doorstep_safe": False,
                "ground_floor_handoff_authorized": True,
                "pre_arrival_brief_pushed": False,
                "courier_penalty_protection": True,
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

            reason_str = " ".join(reason)
            guidance_str = "You are NOT expected to carry this heavy load up the staircase. Dispatch has authorized customer ground meetup or two-person support."
            prompt_str = f"Your order contains heavy items ({weight_kg:.1f}kg) with no elevator access to Floor {floor}. Please meet the delivery partner at the ground floor or building entrance."

            return {
                "decision": "UNSAFE_PHYSICAL_TASK_ESCALATION",
                "safety_tier": "CRITICAL_ERGONOMIC_RISK",
                "action_title": "Ergonomic Hazard — Escalated for Coordination / Ground Meetup",
                "instructions_summary": reason_str,
                "decision_reason": reason_str,
                "courier_guidance": guidance_str,
                "courier_action_brief": guidance_str,
                "customer_prompt": prompt_str,
                "customer_coordination_message": prompt_str,
                "ergonomic_risk_score": 0.95,
                "is_doorstep_safe": False,
                "ground_floor_handoff_authorized": True,
                "pre_arrival_brief_pushed": False,
                "courier_penalty_protection": True,
                "recommended_handoff_location": "Ground Floor Entrance / Building Foyer",
                "policy_rule_id": "SAF-BULKY-WALKUP-02",
                "disclaimer": "Safety policy strictly protects couriers from unassisted heavy manual lifting."
            }

        # ---------------------------------------------------------------------
        # 3. Ground-Floor Authorized Protocols (Society / Commercial Rules)
        # ---------------------------------------------------------------------
        notes_lower = access_notes.lower()
        if "reception" in notes_lower or "concierge" in notes_lower or "society ground" in notes_lower or "not allowed on upper" in notes_lower:
            instruction_text = "Building security rules mandate external delivery handoff at ground floor reception or concierge desk."
            guidance_text = "Deliver directly to ground floor desk/concierge. No upper-floor transit required."
            prompt_text = "Your building management requires deliveries to be received at the ground floor concierge."
            return {
                "decision": "GROUND_FLOOR_HANDOFF_AUTHORIZED",
                "safety_tier": "STANDARD_FACILITY_PROTOCOL",
                "action_title": "Facility Policy: Ground Floor / Concierge Handover",
                "instructions_summary": instruction_text,
                "decision_reason": instruction_text,
                "courier_guidance": guidance_text,
                "courier_action_brief": guidance_text,
                "customer_prompt": prompt_text,
                "customer_coordination_message": prompt_text,
                "ergonomic_risk_score": 0.10,
                "is_doorstep_safe": True,
                "ground_floor_handoff_authorized": True,
                "pre_arrival_brief_pushed": False,
                "courier_penalty_protection": True,
                "recommended_handoff_location": "Ground Floor Reception / Security Desk",
                "policy_rule_id": "POL-RECEPTION-HANDOFF-03",
                "disclaimer": "Verified facility access rule honored."
            }

        # ---------------------------------------------------------------------
        # 4. Gated Community Pre-Arrival Access Brief
        # ---------------------------------------------------------------------
        if gate_security or gate_code:
            code_text = f"Entry Code: {gate_code}" if gate_code else "State customer flat number at security gate."
            instruction_text = f"Security verification required. {code_text} Access notes: {access_notes}"
            guidance_text = f"Show security boom guard {code_text}. Proceed to designated tower elevator."
            prompt_text = f"Your delivery partner is approaching the main gate ({vicinity_meters:.0f}m away)."
            return {
                "decision": "PRE_ARRIVAL_ACCESS_BRIEF",
                "safety_tier": "COORDINATED_ACCESS",
                "action_title": "Gated Complex Access Brief Available",
                "instructions_summary": instruction_text,
                "decision_reason": instruction_text,
                "courier_guidance": guidance_text,
                "courier_action_brief": guidance_text,
                "customer_prompt": prompt_text,
                "customer_coordination_message": prompt_text,
                "ergonomic_risk_score": 0.25,
                "is_doorstep_safe": True,
                "ground_floor_handoff_authorized": False,
                "pre_arrival_brief_pushed": True,
                "courier_penalty_protection": True,
                "recommended_handoff_location": f"Doorstep (Floor {floor}) via Elevator",
                "policy_rule_id": "POL-GATE-BRIEF-04",
                "disclaimer": "Pre-arrival access brief eliminates gate wait times."
            }

        # ---------------------------------------------------------------------
        # 5. Standard Safe Doorstep Handover
        # ---------------------------------------------------------------------
        instruction_text = f"Access clear. Parcel ({weight_kg:.1f}kg) is within safe handling thresholds. Floor: {floor}."
        guidance_text = f"Proceed to doorstep on Floor {floor}. Note customer preference: '{access_notes or 'Ring bell once'}'"
        prompt_text = "Your delivery partner has arrived in your vicinity and is proceeding to your doorstep."
        return {
            "decision": "SAFE_DOORSTEP_PROCEED",
            "safety_tier": "OPTIMAL_LOW_FRICTION",
            "action_title": "Clear Doorstep Handover Authorized",
            "instructions_summary": instruction_text,
            "decision_reason": instruction_text,
            "courier_guidance": guidance_text,
            "courier_action_brief": guidance_text,
            "customer_prompt": prompt_text,
            "customer_coordination_message": prompt_text,
            "ergonomic_risk_score": 0.15,
            "is_doorstep_safe": True,
            "ground_floor_handoff_authorized": False,
            "pre_arrival_brief_pushed": False,
            "courier_penalty_protection": False,
            "recommended_handoff_location": f"Customer Doorstep (Floor {floor})",
            "policy_rule_id": "POL-STANDARD-DOORSTEP-05",
            "disclaimer": "Standard low-friction doorstep delivery."
        }

    def diagnose_delivery_exception(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnose last-mile delivery exceptions using structured evidence.

        Strict Safety & Governance Principles:
          1. Distinguishes observed facts, customer-provided information, worker-reported information,
             and model-generated hypotheses.
          2. Reason categories: LOCATION_MISMATCH, RESTRICTED_ACCESS, CUSTOMER_UNAVAILABLE,
             BULKY_ITEM_HANDLING, VEHICLE_CAPACITY_CONSTRAINT, UNKNOWN.
          3. Never infers a confirmed cause solely from GPS proximity or a missing timestamp.
          4. Recommends safe actions: contacting customer, verifying instructions, correcting location pin
             with permission, requesting suitable transport, or escalating unresolved access issues.
          5. Never recommends unsafe manual lifting, penalizes worker based solely on an inferred cause,
             or claims delivery succeeded without appropriate customer confirmation.
          6. Provides explanation, supporting evidence, missing information, and escalation status.
        """
        if payload is None or not isinstance(payload, dict):
            raise ValueError("Request payload must be a non-null dictionary.")

        attempt_id = str(payload.get("delivery_attempt_id", payload.get("attempt_id", "ATT-UNKNOWN")))
        order_id = str(payload.get("order_id", "ORD-UNKNOWN"))
        reported_reason = str(payload.get("failure_reason", "") or "").lower().strip()

        # Telemetry validation: conservative handling of missing or optional fields
        raw_weight = payload.get("parcel_weight_kg")
        parcel_weight_kg = self._validate_float(raw_weight, "parcel_weight_kg", min_val=0.0, max_val=150.0, allow_none=True)

        raw_floor = payload.get("floor_number")
        floor = self._validate_int(raw_floor, "floor_number", min_val=-5, max_val=200, allow_none=True)
        if floor is None:
            floor = 1

        raw_elevator = payload.get("elevator_available")
        elevator = self._validate_bool(raw_elevator, "elevator_available", allow_none=True)
        if elevator is None:
            elevator = False  # Conservative assumption: never assume elevator exists if unconfirmed

        raw_vicinity = payload.get("customer_vicinity_meters", payload.get("courier_vicinity_meters"))
        vicinity_meters = self._validate_float(raw_vicinity, "customer_vicinity_meters", min_val=0.0, max_val=50000.0, allow_none=True)

        location_pin_verified = self._validate_bool(payload.get("location_pin_verified"), "location_pin_verified", allow_none=True)
        access_instructions = self._validate_bool(payload.get("access_instructions_available"), "access_instructions_available", allow_none=True)
        customer_contacted = self._validate_bool(payload.get("customer_contact_attempted"), "customer_contact_attempted", allow_none=True)

        # Society access restricted (support both naming conventions)
        raw_soc = payload.get("society_access_restricted")
        if raw_soc is None:
            raw_soc = payload.get("society_restricted_access")
        society_restricted = self._validate_bool(raw_soc, "society_access_restricted", allow_none=True)

        handover_confirmed = self._validate_bool(payload.get("customer_handover_confirmed", False), "customer_handover_confirmed", allow_none=False)
        vehicle_capacity_verified = self._validate_bool(payload.get("vehicle_capacity_verified"), "vehicle_capacity_verified", allow_none=True)

        evidence_source = str(payload.get("evidence_source", "courier_app_report") or "")
        recorded_at = str(payload.get("recorded_at", "2026-10-25T12:00:00Z") or "")
        courier_vehicle = str(payload.get("courier_vehicle", "two_wheeler") or "").lower()

        # 1. Classify information sources into distinct categories
        observed_facts: List[str] = []
        customer_info: List[str] = []
        worker_info: List[str] = []
        model_hypotheses: List[str] = []
        missing_info: List[str] = []

        # Record physical observed facts
        if parcel_weight_kg is not None and parcel_weight_kg > 0:
            observed_facts.append(f"Measured parcel weight: {parcel_weight_kg:.1f} kg")
        elif parcel_weight_kg is None:
            missing_info.append("Parcel weight telemetry is missing; physical carrying hazard cannot be definitively excluded.")

        if floor > 1:
            observed_facts.append(f"Destination floor: Floor {floor} (Elevator available: {elevator})")
        if vicinity_meters is not None:
            observed_facts.append(f"Recorded GPS proximity: {vicinity_meters:.1f}m from destination pin")

        # Record customer provided information
        if access_instructions:
            customer_info.append("Customer submitted access/entry instructions with order")
        elif access_instructions is False:
            missing_info.append("Customer entrance/gate instructions are missing")

        # Record worker reported information
        if reported_reason:
            worker_info.append(f"Delivery partner reported exception: '{reported_reason}' (source: {evidence_source})")
        if society_restricted:
            worker_info.append("Delivery partner reported society/security gate denied entry")
        if customer_contacted:
            worker_info.append("Delivery partner attempted phone contact with customer")
        elif customer_contacted is False:
            missing_info.append("Delivery partner has not yet attempted direct customer contact")

        # Check location pin verification
        if location_pin_verified is False:
            worker_info.append("Delivery partner reports address location does not match map GPS pin")
            missing_info.append("Customer-verified geolocation pin update required")
        elif location_pin_verified is None:
            model_hypotheses.append("Location pin verification status is unknown (unconfirmed pin accuracy)")

        # Prohibit inferring confirmed cause solely from GPS proximity or missing timestamp
        if vicinity_meters is not None and vicinity_meters > 150 and not reported_reason and location_pin_verified is None:
            model_hypotheses.append(
                f"GPS ping ({vicinity_meters:.0f}m) suggests distance mismatch, but root cause CANNOT be confirmed without worker or customer report."
            )

        # 2. Determine root-cause category and safe intervention
        root_cause_category = "UNKNOWN"
        safe_action = "CONTACT_CUSTOMER"
        escalation_status = "PENDING_INVESTIGATION"
        action_directive = ""
        explanation = ""
        policy_rule = "DIAG-DEF-00"

        # A. Bulky item / Ergonomic limits violation
        is_bulky_limits_violation = (
            parcel_weight_kg is not None
            and parcel_weight_kg > self.MAX_UNASSISTED_WALKUP_WEIGHT_KG
            and not elevator
            and floor > self.MAX_WALKUP_FLOORS_WITHOUT_LIFT
        )
        is_bulky_reported = ("bulky" in reported_reason or "heavy" in reported_reason)

        if is_bulky_limits_violation or is_bulky_reported:
            root_cause_category = "BULKY_ITEM_HANDLING"
            safe_action = "AUTHORIZE_GROUND_FLOOR_HANDOFF"
            escalation_status = "ERGONOMIC_SAFETY_ESCALATED"
            policy_rule = "DIAG-BULKY-ERGONOMIC-01"
            if parcel_weight_kg is not None:
                explanation = (
                    f"Parcel weight ({parcel_weight_kg:.1f} kg) to Floor {floor} without elevator violates solitary manual carry limits. "
                    "Delivery partner must NOT be instructed to carry this up the stairs unassisted."
                )
            else:
                explanation = (
                    f"Delivery partner reported heavy/bulky parcel to Floor {floor} without elevator. "
                    "Safety policy strictly forbids forcing solitary manual carry."
                )
            action_directive = (
                "Authorize ground-floor lobby or entrance handover immediately. "
                "Invite customer to receive item at ground level or dispatch two-person support crew."
            )

        # B. Vehicle capacity constraint
        elif (
            (courier_vehicle == "bicycle" and parcel_weight_kg is not None and parcel_weight_kg > self.MAX_BICYCLE_PAYLOAD_KG)
            or ("vehicle" in reported_reason or "capacity" in reported_reason)
        ):
            root_cause_category = "VEHICLE_CAPACITY_CONSTRAINT"
            safe_action = "REQUEST_SUITABLE_TRANSPORT"
            escalation_status = "DISPATCH_REASSIGNMENT_REQUIRED"
            policy_rule = "DIAG-VEHICLE-CAPACITY-02"
            weight_str = f" ({parcel_weight_kg:.1f} kg)" if parcel_weight_kg is not None else ""
            explanation = (
                f"Vehicle type '{courier_vehicle}' is insufficient for parcel payload{weight_str}. "
                "Dispatch safety guardrail triggered."
            )
            action_directive = "Reassign dispatch to suitable motorized cargo vehicle or authorize split-parcel delivery."

        # C. Restricted access / Society security
        elif society_restricted or "security" in reported_reason or "gate" in reported_reason or "restricted" in reported_reason:
            root_cause_category = "RESTRICTED_ACCESS"
            safe_action = "ESCALATE_UNRESOLVED_ACCESS_ISSUE"
            escalation_status = "ACCESS_DESK_ESCALATED"
            policy_rule = "DIAG-RESTRICTED-ACCESS-03"
            explanation = "Premises security protocol or gated community restrictions prevented delivery partner from reaching doorstep."
            action_directive = (
                "Call customer to issue gate security pass or authorize ground-floor security desk handover. "
                "Delivery partner rating protected from penalty."
            )

        # D. Location mismatch
        elif location_pin_verified is False or "location" in reported_reason or "wrong address" in reported_reason or "pin" in reported_reason:
            root_cause_category = "LOCATION_MISMATCH"
            safe_action = "CORRECT_LOCATION_PIN_WITH_PERMISSION"
            escalation_status = "ADDRESS_VERIFICATION_PENDING"
            policy_rule = "DIAG-LOCATION-MISMATCH-04"
            explanation = "Address description and physical geolocation pin exhibit a verified mismatch."
            action_directive = (
                "Initiate in-app location pin confirmation request to customer. "
                "Update address landmarks with explicit customer consent."
            )

        # E. Customer unavailable
        elif "unavailable" in reported_reason or "unreachable" in reported_reason or "doorbell" in reported_reason or "no response" in reported_reason:
            root_cause_category = "CUSTOMER_UNAVAILABLE"
            safe_action = "CONTACT_CUSTOMER"
            escalation_status = "CUSTOMER_CALLBACK_QUEUED"
            policy_rule = "DIAG-CUSTOMER-UNAVAILABLE-05"
            explanation = "Delivery partner reached destination but customer could not be reached via doorbell or phone."
            action_directive = (
                "Trigger automated IVR call and SMS alert to customer with 5-minute wait window before authorizing return-to-origin."
            )

        # F. Unknown / Missing information
        else:
            root_cause_category = "UNKNOWN"
            safe_action = "VERIFY_INSTRUCTIONS_AND_CONTACT"
            escalation_status = "SUPERVISOR_TRIAGE"
            policy_rule = "DIAG-UNKNOWN-06"
            explanation = (
                "Insufficient structured telemetry to confirm delivery exception cause. "
                "Cannot infer worker fault or customer fault from missing timestamps or raw proximity."
            )
            action_directive = "Contact delivery partner and customer to establish verified ground truth."

        # 3. Compile strict fairness & worker protection guarantees
        worker_penalty_prohibited = True
        worker_protection_rationale = (
            "Under MacroOps fair operations policy, delivery partners are never penalized "
            "based solely on unconfirmed inferred causes, missing GPS pings, or physical safety refusals."
        )

        # False completion safeguard: Never claim success without handover confirmation
        completion_status_verified = bool(handover_confirmed)
        if not completion_status_verified:
            missing_info.append("Customer handover has not been confirmed; delivery cannot be closed as fulfilled.")

        return {
            "attempt_id": attempt_id,
            "order_id": order_id,
            "root_cause_category": root_cause_category,
            "policy_rule_id": policy_rule,
            "diagnosis_summary": explanation,
            "recommended_safe_action": safe_action,
            "action_directive": action_directive,
            "escalation_status": escalation_status,
            "evidence_breakdown": {
                "observed_facts": observed_facts,
                "customer_provided_info": customer_info,
                "worker_reported_info": worker_info,
                "model_generated_hypotheses": model_hypotheses
            },
            "missing_information": missing_info,
            "fairness_and_safety_safeguards": {
                "worker_penalty_prohibited": worker_penalty_prohibited,
                "worker_protection_rationale": worker_protection_rationale,
                "unsafe_manual_lifting_forbidden": True,
                "delivery_success_claimed": completion_status_verified,
                "prohibited_inference_enforced": "No cause inferred solely from GPS proximity or missing timestamps."
            },
            "recorded_at": recorded_at,
            "disclaimer": "Diagnostic intelligence advisory. Governed by courier safety and fair fault attribution policies."
        }
