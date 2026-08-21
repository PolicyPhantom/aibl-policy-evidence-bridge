"""Human-readable reconstruction derived only from a structured receipt."""

from __future__ import annotations

from typing import Any

from .policy import InputValidationError


def reconstruct_decision(receipt_document: dict[str, Any]) -> str:
    receipt = receipt_document.get("decision_receipt")
    if not isinstance(receipt, dict):
        raise InputValidationError("Missing field: decision_receipt")
    request = receipt["request"]
    applied = receipt["applied_policy"]
    authority = receipt["authority"]
    condition_text = ", ".join(
        f"{key}={str(value).lower() if isinstance(value, bool) else value}"
        for key, value in receipt["operating_conditions"].items()
    ) or "none recorded"
    evidence_text = ", ".join(receipt["evidence_refs"]) or "none"
    reasons = ", ".join(receipt["reason_codes"])
    restrictions = ", ".join(
        condition["code"] for condition in receipt["required_conditions"]
    ) or "none"
    state = receipt["operational_state"]
    return "\n".join(
        (
            f"Decision {receipt['decision_id']} at {receipt['decided_at']}",
            f"Request: {receipt['request_type']} {request['action']} for target {request['target']} (request {receipt['request_id']}).",
            f"Policy: {applied['policy_id']} v{applied['version']}; rules: {', '.join(applied['rule_ids']) or 'none' }.",
            f"Authority: {authority['authority_id']} status {authority['status']} checked at {authority['checked_at']}.",
            f"Evidence references: {evidence_text}; context {receipt['context_snapshot_id']}: {condition_text}.",
            f"Permission: {receipt['decision']}; required conditions: {restrictions}; reasons: {reasons}.",
            f"Execution: {receipt['execution_status']}; operational state: {state['initial']} -> {state['final']}.",
        )
    )
