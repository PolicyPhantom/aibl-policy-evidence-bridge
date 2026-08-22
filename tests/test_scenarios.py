"""Exactly the 13 frozen v0.1.2 acceptance scenarios."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.context import load_scenario
from src.execution import run_governed_request


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FILES = sorted((ROOT / "scenarios").glob("*.yaml"))
if len(SCENARIO_FILES) != 13:
    raise RuntimeError(f"Frozen scenario set must contain exactly 13 files, found {len(SCENARIO_FILES)}")


@pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=lambda path: path.stem)
def test_frozen_acceptance_scenario(scenario_path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(scenario_path)
    expected = scenario["expected"]
    result = run_governed_request(scenario["permission_input"], tmp_path)
    actual_condition_codes = [
        condition["code"] for condition in result.permission.required_conditions
    ]
    receipt = result.receipt.get("decision_receipt")

    print(
        f"{scenario['scenario']['id']} {scenario['scenario']['name']} | "
        f"decision expected={expected['decision']} actual={result.permission.decision} | "
        f"execution expected={expected['execution_status']} actual={result.execution_status}"
    )
    assert result.permission.decision == expected["decision"]
    assert set(expected["reason_codes"]).issubset(result.permission.reason_codes)
    assert actual_condition_codes == expected["required_conditions"]
    assert receipt is not None
    assert receipt["decision"] == result.permission.decision
    assert result.reconstruction.strip()
    assert result.execution_status == expected["execution_status"]
    assert result.final_operational_state == expected["final_operational_state"]
    assert (tmp_path / "receipts" / f"{scenario['request']['request_id']}.json").is_file()
    assert (tmp_path / "reconstructions" / f"{scenario['request']['request_id']}.txt").is_file()

    if scenario["request"]["request_type"] == "REENTRY":
        previous_id = scenario["historical_previous_decision"]["decision_id"]
        assert scenario["historical_previous_decision"]["decision"] == "ALLOW"
        assert receipt["previous_decision_id"] == previous_id
        assert receipt["decision_id"] != previous_id
