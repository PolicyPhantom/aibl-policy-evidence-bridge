"""Run one frozen scenario through the complete governed execution path."""

from __future__ import annotations

from pathlib import Path

from src.context import load_scenario
from src.execution import run_governed_request


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    scenario = load_scenario(repository_root / "scenarios" / "01_allow.yaml")
    result = run_governed_request(
        scenario["permission_input"], repository_root / "outputs"
    )
    expected = scenario["expected"]
    receipt_path = repository_root / "outputs" / "receipts" / "req-001.json"
    reconstruction_path = (
        repository_root / "outputs" / "reconstructions" / "req-001.txt"
    )

    print("AIBL Policy-Evidence Bridge - Minimal Example")
    print(f"Scenario: {scenario['scenario']['id']} {scenario['scenario']['name']}")
    print(f"Expected decision:  {expected['decision']}")
    print(f"Actual decision:    {result.permission.decision}")
    print(f"Reason codes:       {', '.join(result.permission.reason_codes)}")
    print(f"Expected execution: {expected['execution_status']}")
    print(f"Actual execution:   {result.execution_status}")
    print(f"Receipt:            {receipt_path.relative_to(repository_root)}")
    print(f"Reconstruction:     {reconstruction_path.relative_to(repository_root)}")
    print()
    print(result.reconstruction)


if __name__ == "__main__":
    main()
