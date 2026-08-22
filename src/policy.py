"""Loading and validation for the frozen v0.1.2 executable policy shape."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class InputValidationError(ValueError):
    """Raised before permission evaluation when mandatory input is malformed."""


def load_yaml_document(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from disk without consulting any external source."""
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise InputValidationError(f"{path}: expected a YAML mapping")
    return data


def _require(mapping: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if field not in mapping or mapping[field] is None:
            raise InputValidationError(f"Missing field: {label}.{field}")


def validate_policy(policy: dict[str, Any]) -> None:
    """Validate only the narrow executable policy schema frozen for v0.1.2."""
    if not isinstance(policy, dict):
        raise InputValidationError("policy must be a mapping")
    _require(
        policy,
        (
            "policy_id",
            "version",
            "source_ref",
            "status",
            "approved_by_role",
            "approved_at",
            "effective_from",
            "freshness",
            "rules",
        ),
        "policy",
    )
    if policy["status"] not in {"APPROVED", "CANDIDATE"}:
        raise InputValidationError("policy.status must be APPROVED or CANDIDATE")
    freshness = policy["freshness"]
    if not isinstance(freshness, dict):
        raise InputValidationError("policy.freshness must be a mapping")
    _require(
        freshness,
        ("authority_max_age_seconds", "evidence_max_age_seconds"),
        "policy.freshness",
    )
    if not isinstance(policy["rules"], list) or not policy["rules"]:
        raise InputValidationError("policy.rules must be a non-empty list")
    for index, rule in enumerate(policy["rules"]):
        label = f"policy.rules[{index}]"
        if not isinstance(rule, dict):
            raise InputValidationError(f"{label} must be a mapping")
        _require(rule, ("rule_id", "action", "destination"), label)
        destination = rule["destination"]
        if not isinstance(destination, dict):
            raise InputValidationError(f"{label}.destination must be a mapping")
        _require(
            destination,
            ("evidence_type", "allow_values", "unknown_decision"),
            f"{label}.destination",
        )
        if destination["unknown_decision"] != "HOLD":
            raise InputValidationError(
                f"{label}.destination.unknown_decision must be HOLD"
            )


def load_executable_policy(path: str | Path) -> dict[str, Any]:
    document = load_yaml_document(path)
    policy = document.get("policy")
    validate_policy(policy)
    return policy


def is_policy_approved(policy: dict[str, Any]) -> bool:
    return policy["status"] == "APPROVED"


def is_policy_effective(policy: dict[str, Any], evaluation_time: datetime) -> bool:
    from .context import parse_datetime

    return parse_datetime(policy["effective_from"]) <= evaluation_time


def policy_ref_matches(request_ref: dict[str, Any], policy: dict[str, Any]) -> bool:
    return (
        request_ref.get("policy_id") == policy["policy_id"]
        and str(request_ref.get("version")) == str(policy["version"])
    )


def get_applicable_rule(policy: dict[str, Any], action: str) -> dict[str, Any] | None:
    return next((rule for rule in policy["rules"] if rule["action"] == action), None)


def freshness_thresholds(policy: dict[str, Any]) -> tuple[int, int]:
    freshness = policy["freshness"]
    return (
        int(freshness["authority_max_age_seconds"]),
        int(freshness["evidence_max_age_seconds"]),
    )
