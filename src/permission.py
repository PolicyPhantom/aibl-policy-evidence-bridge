"""The single deterministic Permission Gate for v0.1.3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import is_fresh, parse_datetime, validate_permission_input
from .policy import (
    freshness_thresholds,
    get_applicable_rule,
    is_policy_approved,
    is_policy_effective,
    policy_ref_matches,
)


PERMISSION_STATES = frozenset({"ALLOW", "RESTRICT", "HOLD", "DENY"})


@dataclass(frozen=True)
class PermissionDecision:
    decision: str
    reason_codes: tuple[str, ...]
    required_conditions: tuple[dict[str, Any], ...] = ()
    rule_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.decision not in PERMISSION_STATES:
            raise ValueError(f"Invalid permission state: {self.decision}")


def evaluate_permission(permission_input: dict[str, Any]) -> PermissionDecision:
    """Evaluate current inputs; malformed inputs raise before returning a decision."""
    validate_permission_input(permission_input)
    request = permission_input["request"]

    if (
        request["request_type"] == "ACTION"
        and permission_input["operational_state"]["state"] == "SUSPENDED"
    ):
        return PermissionDecision(
            "HOLD", ("OPERATIONAL_STATE_SUSPENDED_REQUIRES_REENTRY",)
        )

    if (
        request["request_type"] == "REENTRY"
        and permission_input["operational_state"]["state"] == "RUNNING"
    ):
        return PermissionDecision(
            "HOLD", ("REENTRY_NOT_APPLICABLE_WHILE_RUNNING",)
        )

    policy = permission_input["policy"]
    authority = permission_input["authority"]
    evidence_records = permission_input["evidence"]
    conditions = permission_input["operating_conditions"]
    evaluation_time = parse_datetime(permission_input["evaluation_time"])
    reasons: list[str] = []

    if request["request_type"] == "REENTRY":
        reasons.append("PREVIOUS_ALLOW_NOT_SUFFICIENT_FOR_REENTRY")

    if not is_policy_approved(policy):
        return PermissionDecision("HOLD", tuple(reasons + ["POLICY_NOT_APPROVED"]))
    if not is_policy_effective(policy, evaluation_time):
        return PermissionDecision("HOLD", tuple(reasons + ["POLICY_AMBIGUOUS"]))
    reasons.append("POLICY_APPROVED")

    if not policy_ref_matches(request["policy_ref"], policy):
        return PermissionDecision("HOLD", tuple(reasons + ["POLICY_VERSION_STALE"]))

    rule = get_applicable_rule(policy, request["action"])
    if rule is None:
        return PermissionDecision("HOLD", tuple(reasons + ["POLICY_AMBIGUOUS"]))
    rule_ids = (str(rule["rule_id"]),)

    if (
        authority["status"] != "VALID"
        or authority["actor_id"] != request["actor_id"]
        or request["action"] not in authority["scope"]
    ):
        return PermissionDecision(
            "DENY", tuple(reasons + ["AUTHORITY_INVALID"]), rule_ids=rule_ids
        )

    authority_max_age, evidence_max_age = freshness_thresholds(policy)
    if not is_fresh(
        authority["checked_at"],
        evaluation_time,
        authority_max_age,
        authority["valid_until"],
    ):
        return PermissionDecision(
            "HOLD", tuple(reasons + ["AUTHORITY_STALE"]), rule_ids=rule_ids
        )
    reasons.append("AUTHORITY_VALID")

    destination_rule = rule["destination"]
    destination_evidence = next(
        (
            record
            for record in evidence_records
            if record["type"] == destination_rule["evidence_type"]
            and record["subject"] == request["target"]
        ),
        None,
    )
    if destination_evidence is None:
        return PermissionDecision(
            "HOLD",
            tuple(reasons + ["DESTINATION_UNKNOWN", "CURRENT_CONTEXT_INCOMPLETE"]),
            rule_ids=rule_ids,
        )
    if not is_fresh(
        destination_evidence["observed_at"], evaluation_time, evidence_max_age
    ):
        return PermissionDecision(
            "HOLD", tuple(reasons + ["EVIDENCE_STALE"]), rule_ids=rule_ids
        )

    destination_value = destination_evidence["value"]
    if destination_value in destination_rule.get("deny_values", []):
        return PermissionDecision(
            "DENY", tuple(reasons + ["DESTINATION_PROHIBITED"]), rule_ids=rule_ids
        )
    if destination_value not in destination_rule["allow_values"]:
        return PermissionDecision(
            destination_rule["unknown_decision"],
            tuple(reasons + ["DESTINATION_UNKNOWN"]),
            rule_ids=rule_ids,
        )
    reasons.append("DESTINATION_APPROVED")

    for name, required_value in rule.get("required_operating_conditions", {}).items():
        if name not in conditions:
            return PermissionDecision(
                "HOLD",
                tuple(reasons + ["CONDITION_UNKNOWN", "CURRENT_CONTEXT_INCOMPLETE"]),
                rule_ids=rule_ids,
            )
        if conditions[name] != required_value:
            return PermissionDecision(
                rule.get("on_operating_condition_failure", "DENY"),
                tuple(reasons + ["OPERATING_CONDITION_PROHIBITED"]),
                rule_ids=rule_ids,
            )
        reasons.append("CONDITION_SATISFIED")

    required_conditions: list[dict[str, Any]] = []
    for restriction in rule.get("required_restrictions", []):
        name = restriction["condition"]
        present = name in conditions
        satisfied = present and conditions[name] == restriction["required_value"]
        required_conditions.append(
            {
                "code": restriction["restriction_code"],
                "condition": name,
                "required_value": restriction["required_value"],
                "satisfied": satisfied,
            }
        )
        reasons.append(
            "CONDITION_SATISFIED"
            if satisfied
            else ("CONDITION_UNSATISFIED" if present else "CONDITION_UNKNOWN")
        )

    reasons.append("CURRENT_CONTEXT_VALID")
    if required_conditions:
        return PermissionDecision(
            "RESTRICT", tuple(reasons), tuple(required_conditions), rule_ids
        )
    return PermissionDecision("ALLOW", tuple(reasons), rule_ids=rule_ids)
