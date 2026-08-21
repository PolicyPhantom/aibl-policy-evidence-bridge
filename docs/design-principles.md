# Design Principles

## Core boundaries

- Capability is not permission. `encryption_available` says a capability exists; `encryption_enabled` says the required control is applied.
- Evidence is not permission. Evidence records facts used by the gate but cannot authorize execution by themselves.
- Translation is not authorization. A candidate executable policy remains unable to authorize until its status is explicitly `APPROVED`.
- Unknown is not ALLOW. Unknown, incomplete, ambiguous, or stale current information produces HOLD where permission cannot be established.
- Historical ALLOW is not current permission. REENTRY always performs a fresh evaluation and creates a new receipt.
- Hidden reasoning is not governance evidence. Decisions use only validated fields, controlled reason codes, and explicit references.
- Execution requires a current Permission Gate decision. The normal execution interface contains no independent public mock-execute entry point.

## Mandatory invariants

1. Unapproved policy cannot authorize execution.
2. Unknown or ambiguous conditions must not silently become ALLOW.
3. Every valid permission decision produces a structured Decision Receipt.
4. Execution occurs only after a current Permission Gate decision.
5. Human-readable explanation is derived from structured evidence and is not primary evidence itself.
6. Hidden model reasoning or Chain-of-Thought is not governance evidence.
7. Previous ALLOW does not automatically authorize REENTRY.
8. REENTRY requires fresh evaluation of current governance conditions.
9. Permission Gate must not be bypassed by execution code.
10. Invalid or malformed input fails before a permission decision and never defaults to ALLOW.

## HOLD versus DENY

HOLD means the system cannot currently establish a defensible decision, such as for stale authority or unknown destination classification. DENY means current information establishes a prohibition, such as an invalid authority, prohibited destination, or unavailable mandatory secure channel. The two states are never merged.
