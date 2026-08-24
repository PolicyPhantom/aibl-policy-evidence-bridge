# AIBL Policy–Evidence Bridge
## Post-Publication Review Case Note 01

### From Implicit Permission Expansion to Explicit State/Request Governance

**Status:** Final Draft — Supplementary Case Note  
**Prototype versions covered:** v0.1.1 → v0.1.3  
**Date:** 2026-08-23

---

## 1. Purpose

This Case Note documents a governance-relevant implementation gap discovered after the initial public release of the **AIBL Policy–Evidence Bridge — Reference Prototype**, the subsequent correction process, and the design lessons that emerged from it.

### Prototype focus

The prototype was designed to examine a narrow execution-governance bridge:

> **Policy → Permission → Execution Decision → Evidence → Reconstruction**

It was **not** intended to prove the correctness or completeness of AIBL, nor to provide production-ready governance infrastructure.

### Why this Case Note exists

The post-publication correction history described here was **not a pre-designed experiment**. It emerged unexpectedly through adversarial review of the published prototype.

Retrospectively, the correction process provides a useful worked example of a broader governance problem:

> **A system may pass all predefined tests while still containing an uncovered state combination that silently expands effective permission.**

---

## 2. Initial Baseline — v0.1.1

### Test baseline

The initial public release, **v0.1.1**, passed all predefined tests:

| Test set | Result |
|---|---:|
| Frozen Acceptance Scenarios | 12 / 12 PASS |
| Supplemental Tests | 10 / 10 PASS |
| **Total** | **22 / 22 PASS** |

### Governance boundaries already present

The prototype already enforced several explicit governance boundaries:

- `Capability ≠ Permission`
- `Evidence ≠ Permission`
- `Translation ≠ Authorization`
- `Unknown ≠ Allow`
- `HOLD ≠ DENY`
- Historical `ALLOW` does not automatically authorize current execution or re-entry
- Execution requires a current Permission Gate decision

### Re-entry cases already tested

The original re-entry scenarios covered:

| Operational State | Request | Current condition | Expected |
|---|---|---|---|
| `SUSPENDED` | `REENTRY` | stale current authority | `HOLD` |
| `SUSPENDED` | `REENTRY` | fresh revalidation | `ALLOW` |

### The uncovered combination

One reachable combination of two already-existing inputs had **not** been explicitly specified or tested:

| Input | Value |
|---|---|
| Operational State | `SUSPENDED` |
| Request Type | `ACTION` |

All predefined tests passed, but this combination remained outside the tested semantic space.

> **Test success did not imply semantic completeness.**

---

## 3. Unexpected Finding — Implicit Permission Expansion

A post-publication adversarial review exercised the untested combination:

| Input | Value |
|---|---|
| Operational State | `SUSPENDED` |
| Request Type | `ACTION` |

Despite the suspended state, an otherwise valid request could reach:

| Result | Observed behavior |
|---|---|
| Permission Decision | `ALLOW` |
| Execution Result | `EXECUTED` |
| Operational State | `SUSPENDED` |

### Why this mattered

No policy explicitly authorized execution from `SUSPENDED`.

The normal permission path remained reachable because **no compatibility rule existed for `SUSPENDED + ACTION`**.

For this Case Note, this behavior is described as **implicit permission expansion**:

> **Execution became effectively available because the relevant governance boundary had not been defined, rather than because permission had been explicitly granted.**

### Wrong answer vs. missing question

The prototype had not answered a defined governance question incorrectly.

> **The system did not give the wrong answer to a defined question.  
> The question itself had not been defined for one reachable state/request combination.**

*“Implicit permission expansion” is descriptive language used in this Case Note. It is not introduced as a formal AIBL risk category.*

---

## 4. v0.1.2 — Closing the Suspended-Action Bypass

**Commit:** `183a4e6 Fix suspended action bypass in v0.1.2`

v0.1.2 made the previously missing boundary explicit.

### Before / after

| | v0.1.1 | v0.1.2 |
|---|---|---|
| State / Request | `SUSPENDED + ACTION` | `SUSPENDED + ACTION` |
| Decision | `ALLOW` possible | `HOLD` |
| Execution | `EXECUTED` possible | `HELD` |
| Final State | `SUSPENDED` | `SUSPENDED` |
| Reason | No compatibility rule | `OPERATIONAL_STATE_SUSPENDED_REQUIRES_REENTRY` |

The original twelve acceptance scenarios were preserved unchanged, and one new scenario was added.

> **Test status: 13 Acceptance Scenarios + 10 Supplemental Tests = 23 / 23 PASS**

### What happened next

The correction closed the reported `SUSPENDED + ACTION` bypass.

The review then moved from the individual defect to the complete combination space:

> **`Request Type × Operational State`**

That second pass exposed another previously undefined combination:

> **`RUNNING + REENTRY`**

This second issue was not simply an automatic consequence of the first code change. It was found by applying the same review method more systematically across the full 2 × 2 state/request space.

---

## 5. v0.1.3 — Closing the Full State/Request Matrix

**Commit:** `d6886d1 Close re-entry state semantics in v0.1.3`

The second correction explicitly defined all four combinations.

### State/request compatibility matrix

| Operational State | `ACTION` | `REENTRY` |
|---|---|---|
| `RUNNING` | Normal permission evaluation | `HOLD` — re-entry not applicable |
| `SUSPENDED` | `HOLD` — re-entry required | Fresh re-entry evaluation |

### `RUNNING + REENTRY`

For `RUNNING + REENTRY`, the prototype now returns:

- **Decision:** `HOLD`
- **Reason:** `REENTRY_NOT_APPLICABLE_WHILE_RUNNING`
- **Execution:** `HELD`
- **Operational State:** remains `RUNNING`

> **Test status: 14 Acceptance Scenarios + 10 Supplemental Tests = 24 / 24 PASS**

All four `Request Type × Operational State` combinations were now explicitly defined.

### 5.1 An Open Question About `HOLD`

The v0.1.3 correction revealed that `HOLD` is now used for two distinguishable situations:

| HOLD type | Meaning | Example recovery path |
|---|---|---|
| **Epistemic HOLD** | Information is missing, stale, ambiguous, or insufficient | Refresh evidence / authority |
| **Applicability HOLD** | The request is not meaningful in the current operational state | Change request or operational state |

In the original scenarios, `HOLD` primarily represented insufficient or stale information.

For `RUNNING + REENTRY`, the relevant information may be complete; the issue is that the requested transition is semantically inapplicable in the current state.

> **Open design question:** Should `HOLD` remain a unified governance state, or should different recovery paths be represented more explicitly?

This Case Note leaves that question unresolved.

---

## 6. What the Correction Process Revealed

The post-publication correction process produced three broader observations.

### 6.1 Test Success Is Not Semantic Completeness

v0.1.1 passed **22 / 22 predefined tests**.

The implementation gap nevertheless remained reachable because the relevant state/request combination had not been represented in the original test space.

> **Passing all specified tests does not establish that the specification itself is complete.**

The defect was not hidden inside a failing requirement. It existed outside the boundary of what had been explicitly specified and tested.

### 6.2 Undefined Governance Semantics Can Have Executable Consequences

The original implementation contained no explicit rule authorizing normal execution while the system was `SUSPENDED`.

Yet the absence of a compatibility check allowed the ordinary permission path to remain reachable.

> **Absence of an explicit authorization boundary may have executable consequences.**

If an undefined state/request combination silently falls through to an execution-capable path, missing governance semantics may become effective permission in practice.

**Interpretation:** this was not simply a software branching error. It was a **governance-boundary error expressed through software**.

### 6.3 Transition Semantics Are Part of the Permission Boundary

Runtime permission cannot always be determined solely from:

- actor
- requested action
- policy
- current authority
- evidence
- operating conditions

The meaning of a request may also depend on the system's current operational state.

For example:

| Request | State | Meaning |
|---|---|---|
| `REENTRY` | `SUSPENDED` | Meaningful governance transition |
| `REENTRY` | `RUNNING` | Semantically inapplicable |

This led to an additional design invariant:

> **Request type and operational state must form a valid transition pair. A semantically incompatible pair must not silently proceed to normal permission evaluation.**

---

## 7. Relationship to the Prototype's Design Principles

### What this does *not* show

The correction history was **not intentionally constructed as an AIBL demonstration**.

It does not show that the development process “proved” AIBL.

### What it does resemble

Retrospectively, the correction history resembles a design concern already present in the prototype:

> **Missing, ambiguous, stale, or otherwise unresolved governance conditions should not silently become `ALLOW`.**

The v0.1.1 design already applied this principle to:

- policy approval
- authority freshness
- evidence freshness
- unknown destinations

The post-publication findings showed that an analogous problem could also occur at the level of **state/request compatibility**.

### Before the correction

`SUSPENDED + ACTION` had no explicit interpretation.

Because the missing interpretation did not produce an explicit non-execution state, the ordinary permission path remained available.

### After the correction

| Stage | Outcome |
|---|---|
| Undefined compatibility | No explicit state/request rule |
| Explicit evaluation | Compatibility checked |
| Governance result | `HOLD` + inspectable reason code |

### Retrospective interpretation

> **A post-publication implementation defect happened to reproduce, at the development-process level, a structurally similar ambiguity to the kind of ambiguity the prototype was intended to expose at runtime.**

This interpretation is retrospective and should be treated as such.

---

## 8. Review Method Note

The initial defect was identified through an **AI-assisted adversarial review that included executable reproduction**, rather than textual code inspection alone.

### What the AI-assisted review contributed

The review did more than identify the defect. It also generated specific **candidate resolutions**, including:

- proposed semantics
- reason-code naming
- alternative treatments for the remaining undefined state/request combination

For the later `RUNNING + REENTRY` finding, the reviewer identified the untested combination and proposed alternative treatments rather than only reporting that the case was undefined.

Other AI-assisted discussion also contributed to evaluating those alternatives and their governance meaning.

### Division of roles

The project owner did **not** independently originate every correction or semantic option described in this Case Note.

The actual process was closer to:

| Stage | Role |
|---|---|
| Observed implementation behavior | Existing prototype |
| Defect discovery | AI-assisted adversarial review |
| Candidate interpretation / correction | AI-assisted proposal generation |
| Semantic evaluation | Project-side review |
| Acceptance authority | Human project owner |
| Implementation | Coding workflow |
| Verification | Executable tests and re-review |
| Record | Git commit and versioned specification |

### Candidate proposal vs. specification authority

The project owner retained final acceptance authority over whether a proposed interpretation or correction would become part of the prototype.

A candidate proposal did **not** acquire specification authority merely because an AI reviewer generated it.

It had to be:

1. evaluated;
2. accepted or rejected;
3. implemented;
4. tested; and
5. incorporated into the versioned project.

Retrospectively, this creates a small parallel with another principle already present in the prototype:

> **Candidate ≠ Approved**

This parallel was **not intentionally designed into the review process** and should not be interpreted as a planned governance experiment.

### Methodological boundary

AI-assisted review functioned here as both:

- a defect-discovery mechanism; and
- a source of candidate resolutions.

It should **not** be interpreted as:

- independent assurance;
- certification;
- proof of correctness; or
- a substitute for independent human review.

Likewise, the use of multiple AI systems may expose different assumptions or reviewer blind spots, but it does not by itself establish reviewer independence or eliminate the possibility of correlated model failure.

---

## 9. Case Summary

### Correction timeline

| Version | Observation / Change | Test Status |
|---|---|---:|
| **v0.1.1** | Original public baseline | **22 / 22 PASS** |
|  | `SUSPENDED × ACTION` found undefined |  |
|  | Implicit execution path reproduced |  |
| **v0.1.2** | `SUSPENDED + ACTION → HOLD` | **23 / 23 PASS** |
|  | Full `Request Type × Operational State` space enumerated |  |
|  | `RUNNING × REENTRY` found undefined |  |
| **v0.1.3** | Full 2 × 2 compatibility matrix defined | **24 / 24 PASS** |

### Central lesson

> **The important failure was not that the system chose the wrong answer to a defined question. The question itself had not been defined for one reachable combination of state and request.**

For governance-oriented systems, review should examine not only whether expected cases return expected decisions, but also whether relevant combinations of:

- state
- request
- authority
- evidence
- transition semantics

have been explicitly defined.

### Second lesson

> **A proposed correction can be technically plausible without yet being authoritative.**

Candidate resolutions still require explicit evaluation and acceptance before they become part of the governed specification.

---

## 10. Scope Boundary

### What this Case Note documents

This Case Note documents:

- one concrete implementation finding;
- the review path that exposed it; and
- the governance semantics introduced to address it.

### What it does *not* establish

This Case Note does **not** establish:

- production readiness;
- system safety;
- legal or regulatory compliance;
- completeness of the AIBL framework;
- completeness of the prototype's remaining state space;
- effectiveness of AI-assisted review as an assurance method;
- independence of multiple AI reviewers;
- superiority of the prototype over existing authorization, policy, IAM, or runtime-control systems; or
- that the post-publication correction process was an intentionally designed AIBL experiment.

### Prototype status

The prototype remains a small reference implementation intended to make assumptions:

- **inspectable**
- **executable**
- **testable**
- **open to criticism**
