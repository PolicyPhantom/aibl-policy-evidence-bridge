"""The only normal public path from current gate evaluation to mock execution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .permission import PermissionDecision, evaluate_permission
from .receipt import build_decision_receipt
from .reconstruction import reconstruct_decision


@dataclass(frozen=True)
class GovernedResult:
    permission: PermissionDecision
    execution_status: str
    receipt: dict[str, Any]
    reconstruction: str
    final_operational_state: str


def _mock_execution_status(permission: PermissionDecision) -> str:
    if permission.decision == "ALLOW":
        return "EXECUTED"
    if permission.decision == "RESTRICT":
        if all(condition["satisfied"] for condition in permission.required_conditions):
            return "EXECUTED_WITH_RESTRICTIONS"
        return "NOT_EXECUTED_CONDITION_REQUIRED"
    if permission.decision == "HOLD":
        return "HELD"
    return "BLOCKED"


def run_governed_request(
    permission_input: dict[str, Any], output_directory: str | Path | None = None
) -> GovernedResult:
    """Evaluate the current gate, then and only then perform mock execution."""
    permission = evaluate_permission(permission_input)
    execution_status = _mock_execution_status(permission)
    initial_state = permission_input["operational_state"]["state"]
    final_state = initial_state
    if (
        permission_input["request"]["request_type"] == "REENTRY"
        and execution_status in {"EXECUTED", "EXECUTED_WITH_RESTRICTIONS"}
    ):
        final_state = "RUNNING"
    receipt = build_decision_receipt(
        permission_input, permission, execution_status, final_state
    )
    reconstruction = reconstruct_decision(receipt)

    if output_directory is not None:
        root = Path(output_directory)
        receipts = root / "receipts"
        reconstructions = root / "reconstructions"
        receipts.mkdir(parents=True, exist_ok=True)
        reconstructions.mkdir(parents=True, exist_ok=True)
        request_id = permission_input["request"]["request_id"]
        (receipts / f"{request_id}.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (reconstructions / f"{request_id}.txt").write_text(
            reconstruction + "\n", encoding="utf-8"
        )

    return GovernedResult(
        permission,
        execution_status,
        receipt,
        reconstruction,
        final_state,
    )
