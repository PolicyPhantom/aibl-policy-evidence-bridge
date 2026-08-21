"""Scenario loading, input validation, and deterministic freshness helpers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .policy import InputValidationError, load_yaml_document, validate_policy


PERMISSION_INPUT_KEYS = (
    "request",
    "policy",
    "authority",
    "evidence",
    "operating_conditions",
    "operational_state",
    "evaluation_time",
)


def parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InputValidationError(f"Invalid timestamp: {value}") from exc
    else:
        raise InputValidationError(f"Invalid timestamp: {value!r}")
    if parsed.tzinfo is None:
        raise InputValidationError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def format_datetime(value: str | datetime) -> str:
    return parse_datetime(value).isoformat().replace("+00:00", "Z")


def is_fresh(
    record_time: str | datetime,
    evaluation_time: str | datetime,
    max_age_seconds: int,
    valid_until: str | datetime | None = None,
) -> bool:
    """Apply the frozen inclusive freshness boundary deterministically."""
    evaluated_at = parse_datetime(evaluation_time)
    age = (evaluated_at - parse_datetime(record_time)).total_seconds()
    within_age = age <= max_age_seconds
    within_validity = valid_until is None or evaluated_at <= parse_datetime(valid_until)
    return within_age and within_validity


def _require(mapping: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    if not isinstance(mapping, dict):
        raise InputValidationError(f"{label} must be a mapping")
    for field in fields:
        if field not in mapping or mapping[field] is None:
            raise InputValidationError(f"Missing field: {label}.{field}")


def validate_permission_input(permission_input: dict[str, Any]) -> None:
    """Reject malformed input before any permission decision is produced."""
    _require(permission_input, PERMISSION_INPUT_KEYS, "permission_input")
    request = permission_input["request"]
    _require(
        request,
        (
            "request_id",
            "request_type",
            "actor_id",
            "action",
            "target",
            "purpose",
            "requested_at",
            "policy_ref",
        ),
        "request",
    )
    if request["request_type"] not in {"ACTION", "REENTRY"}:
        raise InputValidationError("request.request_type must be ACTION or REENTRY")
    if request["request_type"] == "REENTRY" and not request.get("previous_decision_id"):
        raise InputValidationError("Missing field: request.previous_decision_id")
    _require(request["policy_ref"], ("policy_id", "version"), "request.policy_ref")
    parse_datetime(request["requested_at"])

    validate_policy(permission_input["policy"])
    parse_datetime(permission_input["policy"]["approved_at"])
    parse_datetime(permission_input["policy"]["effective_from"])

    authority = permission_input["authority"]
    _require(
        authority,
        ("authority_id", "actor_id", "scope", "status", "checked_at", "valid_until", "evidence_ref"),
        "authority",
    )
    if authority["status"] not in {"VALID", "INVALID"}:
        raise InputValidationError("authority.status must be VALID or INVALID")
    if not isinstance(authority["scope"], list):
        raise InputValidationError("authority.scope must be a list")
    parse_datetime(authority["checked_at"])
    parse_datetime(authority["valid_until"])

    evidence = permission_input["evidence"]
    if not isinstance(evidence, list):
        raise InputValidationError("evidence must be a list")
    for index, record in enumerate(evidence):
        _require(
            record,
            ("evidence_id", "type", "subject", "value", "observed_at", "source"),
            f"evidence[{index}]",
        )
        parse_datetime(record["observed_at"])

    conditions = permission_input["operating_conditions"]
    _require(conditions, ("snapshot_id", "observed_at"), "operating_conditions")
    parse_datetime(conditions["observed_at"])

    operational_state = permission_input["operational_state"]
    _require(operational_state, ("state", "changed_at", "reason"), "operational_state")
    if operational_state["state"] not in {"RUNNING", "SUSPENDED"}:
        raise InputValidationError("operational_state.state must be RUNNING or SUSPENDED")
    parse_datetime(operational_state["changed_at"])
    parse_datetime(permission_input["evaluation_time"])


def assemble_permission_input(document: dict[str, Any]) -> dict[str, Any]:
    permission_input = {key: deepcopy(document.get(key)) for key in PERMISSION_INPUT_KEYS}
    validate_permission_input(permission_input)
    return permission_input


def load_scenario(path: str | Path) -> dict[str, Any]:
    document = load_yaml_document(path)
    document["permission_input"] = assemble_permission_input(document)
    return document
