# AIBL Policy-Evidence Bridge

> **This repository contains a reference prototype for research and demonstration purposes. It is not a production governance system.**

## 1. What This Is

This is the smallest deterministic implementation of the AIBL Policy-Evidence Bridge v0.1.1 boundary. It turns an explicitly approved executable policy, a request, and a current context snapshot into one of four permission decisions, performs only a mock execution outcome, and records a structured Decision Receipt that can be reconstructed for a human reader.

The prototype keeps the natural-language policy in [`policies/source-policy.txt`](policies/source-policy.txt) separate from its pre-authored executable translation in [`policies/executable-policy.yaml`](policies/executable-policy.yaml). Translation alone does not authorize execution; approval remains explicit policy data.

## 2. Research Question

> Given a policy and a proposed action, can the prototype produce a defensible permission decision and reconstruct the basis for that decision without relying on hidden model reasoning?

This prototype exposes that boundary for inspection. It does not prove that AIBL is effective, safe, compliant, production-ready, or empirically validated.

## 3. Architecture

```text
Natural-language policy
  -> candidate/approved executable policy
  -> request + current context snapshot
  -> Permission Gate
  -> ALLOW / RESTRICT / HOLD / DENY
  -> mock execute / block / wait
  -> structured Decision Receipt
  -> receipt-derived reconstruction
```

All normal execution enters through `run_governed_request`, which evaluates the current Permission Gate before determining an execution outcome. See [`docs/architecture.md`](docs/architecture.md).

## 4. Permission States

| State | Meaning | Mock execution outcome |
|---|---|---|
| `ALLOW` | Current policy, authority, evidence, and conditions support unrestricted execution. | `EXECUTED` |
| `RESTRICT` | Execution is permissible only under an explicit, machine-checkable condition. | `EXECUTED_WITH_RESTRICTIONS` when satisfied; otherwise `NOT_EXECUTED_CONDITION_REQUIRED` |
| `HOLD` | Current information cannot establish a defensible permission decision. | `HELD` |
| `DENY` | Current information establishes that the action is prohibited. | `BLOCKED` |

`HOLD` is not `DENY`. Capability is not permission, and evidence is not permission.

## 5. Quick Start

Python 3.11 or later is required. From the repository root:

```bash
pip install -r requirements.txt
python -m examples.minimal_example
python -m pytest
```

The example and tests run offline and require no API key or external service.

## 6. Minimal Example

`python -m examples.minimal_example` evaluates Scenario 01. It prints the expected and actual decision and execution outcome, writes a JSON receipt to `outputs/receipts/`, and writes its human-readable reconstruction to `outputs/reconstructions/`.

Curated output is available in [`examples/sample_outputs/`](examples/sample_outputs/).

## 7. Frozen Test Scenarios

The acceptance set contains exactly 12 fixtures in [`scenarios/`](scenarios/):

| # | Boundary | Decision | Execution |
|---|---|---|---|
| 01 | Approved current action | ALLOW | EXECUTED |
| 02 | Prohibited destination | DENY | BLOCKED |
| 03 | Unknown destination | HOLD | HELD |
| 04 | Audit storage with enforced encryption restriction | RESTRICT | EXECUTED_WITH_RESTRICTIONS |
| 05 | Candidate, unapproved policy | HOLD | HELD |
| 06 | Invalid authority | DENY | BLOCKED |
| 07 | Stale authority | HOLD | HELD |
| 08 | Stale evidence | HOLD | HELD |
| 09 | Secure channel unavailable | DENY | BLOCKED |
| 10 | Policy-version drift | HOLD | HELD |
| 11 | Re-entry with historical ALLOW and stale current authority | HOLD | HELD |
| 12 | Re-entry after fresh current revalidation | ALLOW | EXECUTED |

Run `python -m pytest -s tests/test_scenarios.py` to display expected-versus-actual lines for all frozen scenarios. Supplemental tests are kept separate in [`tests/test_invariants.py`](tests/test_invariants.py).

## 8. Decision Receipts and Reconstruction

Every valid permission evaluation creates a structured receipt containing the request and policy references, applied rule, authority, evidence references, context snapshot, reason codes, decision, restriction state, execution result, and operational-state transition. Receipts do not contain hidden reasoning or Chain-of-Thought.

The readable reconstruction is derived only from the receipt. It is a presentation, not primary governance evidence.

## 9. Re-entry Example

Scenarios 11 and 12 start from an already `SUSPENDED` state. The prototype does not detect suspension automatically.

- Scenario 11 keeps the state `SUSPENDED` because current authority is stale, even though a historical ALLOW is referenced.
- Scenario 12 evaluates fresh current inputs, issues a new decision ID and receipt, executes, and changes the mock state to `RUNNING`.

The previous receipt is historical evidence only and is never reused as current authorization.

## 10. Limitations

This is a narrow research implementation, not a legal or regulatory compliance determination. It has no UI, API server, database, production IAM, live LLM, real connector, cloud deployment, container orchestration, automatic policy generation, or automatic suspension detection. See [`docs/limitations.md`](docs/limitations.md).

## 11. Feedback Wanted

Feedback is especially welcome on architecture boundaries, permission semantics, HOLD versus DENY behavior, authority and freshness assumptions, evidence reconstruction, re-entry semantics, and unrealistic implementation assumptions. Production-hardening suggestions are useful context but are outside the current v0.1.1 scope.

## 12. AI-Assisted Development Disclosure

**AI-assisted development**  
Development of this reference prototype was assisted by AI coding tools. The conceptual design, governance semantics, scenario definitions, acceptance criteria, and final validation remain under human responsibility.

## 13. License Status

**License:** To be selected by the project owner before public release. No license should be inferred from the absence of a `LICENSE` file.
