"""Structured, deterministic Decision Receipt generation."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

from .context import format_datetime
from .permission import PermissionDecision


def _decision_id(permission_input: dict[str, Any]) -> str:
    request = permission_input["request"]
    seed = "|".join(
        (
            request["request_id"],
            format_datetime(permission_input["evaluation_time"]),
            permission_input["policy"]["policy_id"],
            str(permission_input["policy"]["version"]),
        )
    )
    return "dec-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def build_decision_receipt(
    permission_input: dict[str, Any],
    permission: PermissionDecision,
    execution_status: str,
    final_operational_state: str,
) -> dict[str, Any]:
    request = permission_input["request"]
    policy = permission_input["policy"]
    authority = permission_input["authority"]
    conditions = permission_input["operating_conditions"]
    receipt = {
        "decision_id": _decision_id(permission_input),
        "decided_at": format_datetime(permission_input["evaluation_time"]),
        "request_id": request["request_id"],
        "request_type": request["request_type"],
        "request": {
            "actor_id": request["actor_id"],
            "action": request["action"],
            "target": request["target"],
            "purpose": request["purpose"],
        },
        "request_policy_ref": deepcopy(request["policy_ref"]),
        "applied_policy": {
            "policy_id": policy["policy_id"],
            "version": str(policy["version"]),
            "rule_ids": list(permission.rule_ids),
        },
        "authority": {
            "authority_id": authority["authority_id"],
            "status": authority["status"],
            "checked_at": format_datetime(authority["checked_at"]),
            "evidence_ref": authority["evidence_ref"],
        },
        "evidence_refs": [record["evidence_id"] for record in permission_input["evidence"]],
        "context_snapshot_id": conditions["snapshot_id"],
        "operating_conditions": {
            key: deepcopy(value)
            for key, value in conditions.items()
            if key not in {"snapshot_id", "observed_at"}
        },
        "operational_state": {
            "initial": permission_input["operational_state"]["state"],
            "final": final_operational_state,
        },
        "previous_decision_id": request.get("previous_decision_id"),
        "decision": permission.decision,
        "required_conditions": [deepcopy(item) for item in permission.required_conditions],
        "reason_codes": list(permission.reason_codes),
        "execution_status": execution_status,
    }
    return {"decision_receipt": receipt}
