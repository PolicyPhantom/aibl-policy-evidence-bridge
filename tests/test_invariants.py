"""Supplemental validation and invariant tests outside the frozen set."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

import src.execution as execution_module
from src.context import is_fresh, load_scenario
from src.execution import run_governed_request
from src.permission import PERMISSION_STATES, evaluate_permission
from src.policy import InputValidationError
from src.reconstruction import reconstruct_decision


ROOT = Path(__file__).resolve().parents[1]


def scenario_input(name: str) -> dict:
    return load_scenario(ROOT / "scenarios" / name)["permission_input"]


def test_missing_mandatory_input_fails_before_decision_or_output(tmp_path: Path) -> None:
    permission_input = scenario_input("01_allow.yaml")
    del permission_input["request"]["actor_id"]
    with pytest.raises(InputValidationError, match="actor_id"):
        run_governed_request(permission_input, tmp_path)
    assert not (tmp_path / "receipts").exists()
    assert not (tmp_path / "reconstructions").exists()


def test_freshness_boundary_is_inclusive_and_deterministic() -> None:
    assert is_fresh("2026-08-21T11:00:00Z", "2026-08-21T12:00:00Z", 3600)
    assert not is_fresh("2026-08-21T10:59:59Z", "2026-08-21T12:00:00Z", 3600)


def test_missing_evidence_holds_and_does_not_execute() -> None:
    permission_input = scenario_input("01_allow.yaml")
    permission_input["evidence"] = []
    result = run_governed_request(permission_input)
    assert result.permission.decision == "HOLD"
    assert "CURRENT_CONTEXT_INCOMPLETE" in result.permission.reason_codes
    assert result.execution_status == "HELD"


def test_unsatisfied_restriction_does_not_execute() -> None:
    permission_input = scenario_input("04_restrict_encryption.yaml")
    permission_input["operating_conditions"]["encryption_enabled"] = False
    result = run_governed_request(permission_input)
    assert result.permission.decision == "RESTRICT"
    assert "CONDITION_UNSATISFIED" in result.permission.reason_codes
    assert result.execution_status == "NOT_EXECUTED_CONDITION_REQUIRED"


def test_normal_execution_module_exposes_only_governed_public_path() -> None:
    public_callables = {
        name
        for name, value in vars(execution_module).items()
        if callable(value) and not name.startswith("_") and getattr(value, "__module__", None) == execution_module.__name__
    }
    assert public_callables == {"GovernedResult", "run_governed_request"}


def test_previous_allow_is_referenced_but_not_reused() -> None:
    permission_input = scenario_input("12_allow_reentry_revalidated.yaml")
    result = run_governed_request(permission_input)
    receipt = result.receipt["decision_receipt"]
    assert receipt["previous_decision_id"] == permission_input["request"]["previous_decision_id"]
    assert receipt["decision_id"] != receipt["previous_decision_id"]
    assert "PREVIOUS_ALLOW_NOT_SUFFICIENT_FOR_REENTRY" in receipt["reason_codes"]


def test_receipt_id_is_deterministic_for_the_same_current_input() -> None:
    permission_input = scenario_input("01_allow.yaml")
    first = run_governed_request(deepcopy(permission_input))
    second = run_governed_request(deepcopy(permission_input))
    assert first.receipt["decision_receipt"]["decision_id"] == second.receipt["decision_receipt"]["decision_id"]


def test_reconstruction_uses_structured_receipt_content() -> None:
    result = run_governed_request(scenario_input("01_allow.yaml"))
    receipt = deepcopy(result.receipt)
    receipt["decision_receipt"]["reason_codes"] = ["DESTINATION_APPROVED"]
    text = reconstruct_decision(receipt)
    assert "DESTINATION_APPROVED" in text
    assert "AUTHORITY_VALID" not in text


def test_only_four_permission_states_exist_and_are_represented() -> None:
    decisions = {
        evaluate_permission(scenario_input(name)).decision
        for name in (
            "01_allow.yaml",
            "02_deny_prohibited_destination.yaml",
            "03_hold_unknown_destination.yaml",
            "04_restrict_encryption.yaml",
        )
    }
    assert decisions == PERMISSION_STATES == {"ALLOW", "RESTRICT", "HOLD", "DENY"}


def test_invalid_timestamp_fails_validation() -> None:
    permission_input = scenario_input("01_allow.yaml")
    permission_input["evaluation_time"] = "not-a-time"
    with pytest.raises(InputValidationError, match="Invalid timestamp"):
        evaluate_permission(permission_input)
