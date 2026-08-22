# Architecture

## End-to-end boundary

```text
Policy source
  -> pre-authored executable translation
  -> schema validation and explicit approval status
  -> action or re-entry request
  -> authority + evidence + operating conditions + operational state
  -> deterministic Permission Gate
  -> ALLOW / RESTRICT / HOLD / DENY
  -> mock execution outcome
  -> structured Decision Receipt
  -> human-readable reconstruction
```

`src/policy.py` loads and validates the frozen policy shape. `src/context.py` validates scenario inputs and calculates timestamp freshness against the fixture's explicit `evaluation_time`. Neither module grants permission.

`src/permission.py` is the single decision entry point. It first rejects malformed input. Immediately afterward, a normal `ACTION` in `SUSPENDED` is held with `OPERATIONAL_STATE_SUSPENDED_REQUIRES_REENTRY`. Only then does normal evaluation check current policy approval/effectiveness and version, authority validity/scope/freshness, destination evidence freshness/classification, and required operating conditions or restrictions.

`src/execution.py` exposes the normal public path `run_governed_request`. That path always calls the Permission Gate before its private mock execution mapping. It then calls `src/receipt.py` and derives text through `src/reconstruction.py`.

## Re-entry

```text
SUSPENDED state + REENTRY request + historical decision reference
  -> fresh evaluation of current policy, authority, evidence, and conditions
  -> new current permission decision
  -> new decision ID and Decision Receipt
  -> remain SUSPENDED, or become RUNNING after permitted mock execution
```

The historical ALLOW is retained only as a reference. It never restores permission by itself. v0.1.2 starts its re-entry scenarios in `SUSPENDED`; automatic suspension detection is not implemented. Restoring action capability from `SUSPENDED` requires a `REENTRY` request; a normal `ACTION` remains held in `SUSPENDED`.

## Determinism

Frozen fixtures specify `evaluation_time`. Freshness is inclusive at the configured boundary: an age equal to the maximum age is fresh; a larger age is stale. Receipt IDs are deterministically derived from the current request, evaluation time, and applied policy identity. They use a 12-hex-character prefix of SHA-256 and are prototype identifiers, not audit-grade globally collision-resistant identifiers. No wall-clock lookup or external data source participates in a frozen decision.
