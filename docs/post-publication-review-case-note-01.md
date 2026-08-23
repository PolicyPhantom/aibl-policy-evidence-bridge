# AIBL Policy–Evidence Bridge
## Post-Publication Review Case Note 01

### From Implicit Permission Expansion to Explicit State/Request Governance

**Status:** Final Draft — Supplementary Case Note  
**Prototype versions covered:** v0.1.1 → v0.1.3  
**Date:** 2026-08-23

---

## 1. Purpose

This Case Note documents a governance-relevant implementation gap discovered after the initial public release of the **AIBL Policy–Evidence Bridge — Reference Prototype**, the subsequent correction process, and the design lessons that emerged from it.

The prototype was originally designed to examine a narrow execution-governance bridge:

> **Policy → Permission → Execution Decision → Evidence → Reconstruction**

It was not intended to prove the correctness or completeness of AIBL, nor to provide production-ready governance infrastructure.

The post-publication correction history described here was **not a pre-designed experiment**. It emerged unexpectedly through adversarial review of the published prototype.

Retrospectively, however, the correction process provides a useful worked example of a broader governance problem:

> A system may pass all predefined tests while still containing an uncovered state combination that silently expands effective permission.

---

## 2. Initial Baseline — v0.1.1

The initial public release, **v0.1.1**, passed all predefined tests:

- 12 Frozen Acceptance Scenarios
- 10 Supplemental Tests
- **22 / 22 PASS**

The prototype already enforced several explicit governance boundaries, including:

- `Capability ≠ Permission`
- `Evidence ≠ Permission`
- `Translation ≠ Authorization`
- `Unknown ≠ Allow`
- `HOLD ≠ DENY`
- Historical `ALLOW` does not automatically authorize current execution or re-entry
- Execution requires a current Permission Gate decision

The original re-entry scenarios tested:

- `SUSPENDED + REENTRY` with stale current authority → `HOLD`
- `SUSPENDED + REENTRY` after fresh revalidation → `ALLOW`

However, one reachable combination of two already-existing inputs had not been explicitly specified or tested:

```text
Operational State = SUSPENDED
Request Type      = ACTION

All predefined tests passed, but this state/request combination remained outside the tested semantic space.

This distinction became important later:

Test success did not imply semantic completeness.

3. Unexpected Finding — Implicit Permission Expansion

A post-publication adversarial review exercised the untested combination:

SUSPENDED + ACTION

Using an otherwise valid request that would normally produce ALLOW, the prototype could produce:

Decision:          ALLOW
Execution Result:   EXECUTED
Operational State: SUSPENDED

The problem was not that an explicit policy rule authorized execution from a suspended state.

The problem was that no state/request compatibility check existed at that boundary.

As a result, the normal permission-evaluation path remained reachable even though restoration of action capability from SUSPENDED was intended to occur through the explicit REENTRY path.

For the purposes of this Case Note, this behavior is described as an implicit permission expansion:

Execution became effectively available because the relevant governance boundary had not been defined, rather than because permission had been explicitly granted.

The phrase implicit permission expansion is used here as descriptive language for this specific implementation finding. It is not introduced as a new formal AIBL risk category.

The finding also demonstrated an important distinction between a wrong answer and a missing question.

The prototype had not answered a defined governance question incorrectly.

Instead:

The question itself had not been explicitly defined for one reachable combination of operational state and request type.

4. v0.1.2 Correction — Making the Missing Boundary Explicit

The first correction was released as v0.1.2.

Relevant commit:

183a4e6 Fix suspended action bypass in v0.1.2

An explicit rule was introduced:

SUSPENDED + ACTION
        ↓
HOLD

with the reason code:

OPERATIONAL_STATE_SUSPENDED_REQUIRES_REENTRY

Expected behavior became:

Decision:          HOLD
Execution Result:   HELD
Operational State: SUSPENDED

A new acceptance scenario was added while preserving the original twelve scenarios unchanged.

The test result after the correction was:

13 Acceptance Scenarios
10 Supplemental Tests
23 / 23 PASS

The v0.1.2 correction closed the reported SUSPENDED + ACTION bypass.

After that correction, the same review method was applied more systematically by enumerating the full combination space of:

Request Type × Operational State

That second review pass surfaced another previously undefined combination:

RUNNING + REENTRY

The second issue was therefore not simply an automatic consequence of the first code change. It was identified by extending the review from the reported defect to the complete 2 × 2 state/request space.

5. v0.1.3 — Closing the Full State/Request Matrix

The second correction made the full relationship between operational state and request type explicit.

Relevant commit:

d6886d1 Close re-entry state semantics in v0.1.3

The resulting compatibility matrix was:

Operational State	ACTION	REENTRY
RUNNING	Normal permission evaluation	HOLD — re-entry not applicable
SUSPENDED	HOLD — re-entry required	Fresh re-entry evaluation

For:

RUNNING + REENTRY

the prototype now returns:

Decision: HOLD
Reason:   REENTRY_NOT_APPLICABLE_WHILE_RUNNING

The request is held because re-entry is not meaningful while the system is already in the RUNNING state.

This is treated as HOLD, rather than DENY, because the underlying action is not necessarily prohibited. The request/state combination itself is semantically inapplicable.

After adding the final acceptance scenario:

14 Acceptance Scenarios
10 Supplemental Tests
24 / 24 PASS

All four combinations of Request Type × Operational State were now explicitly defined.

5.1 An Open Question About HOLD

The v0.1.3 correction also introduced a distinction that this Case Note does not attempt to resolve.

In the original prototype scenarios, HOLD primarily represented situations in which current information was insufficient, ambiguous, stale, or otherwise inadequate to justify either permission or prohibition.

For RUNNING + REENTRY, however, the relevant information may be complete. The reason for HOLD is instead that the requested transition is semantically inapplicable in the current operational state.

The prototype therefore now uses HOLD for at least two distinguishable situations:

Epistemic HOLD — the system lacks sufficiently current or complete information to make a defensible permission decision.
Applicability HOLD — the request/state combination itself is not meaningful for normal permission evaluation.

Whether these situations should remain under a single HOLD state or be distinguished more explicitly is left as an open design question for future work.

The v0.1.3 implementation should therefore be understood as making the state/request matrix explicit, not as resolving every semantic question created by that matrix.

6. What the Correction Process Revealed
6.1 Test Success Is Not Semantic Completeness

v0.1.1 passed 22 / 22 predefined tests.

The implementation gap nevertheless remained reachable because the relevant state combination had not been represented in the original test space.

This demonstrates a familiar but important distinction:

Passing all specified tests does not establish that the specification itself is complete.

The defect was not hidden inside a failing requirement.

It existed outside the boundary of what had been explicitly asked.

6.2 Undefined Governance States Can Behave Like Permission

The original implementation contained no explicit rule authorizing normal execution while suspended.

Yet the absence of a compatibility check allowed the ordinary permission path to proceed.

In operational governance, therefore:

Absence of an explicit authorization boundary may have executable consequences.

If an undefined state silently falls through to an execution-capable path, missing governance semantics may become effective permission in practice.

The issue was therefore not simply a software branching error.

It was a governance-boundary error expressed through software.

6.3 Transition Semantics Are Part of the Permission Boundary

The correction process also showed that runtime permission cannot always be determined solely by examining:

actor
requested action
policy
current authority
evidence
operating conditions

The meaning of the request may also depend on the system's current operational state.

For example, REENTRY has a meaningful governance role when the system is SUSPENDED, but not when it is already RUNNING.

The valid relationship between state and requested transition therefore forms part of the runtime governance boundary itself.

This led to an additional design invariant:

Request type and operational state must form a valid transition pair. A semantically incompatible pair must not silently proceed to normal permission evaluation.

7. Relationship to the Prototype's Design Principles

The correction history was not intentionally constructed as an AIBL demonstration.

However, retrospectively, it resembles the same design concern already present in the prototype:

Missing, ambiguous, stale, or otherwise unresolved governance conditions should not silently become ALLOW.

The v0.1.1 design already applied that principle to matters such as policy approval, authority freshness, evidence freshness, and unknown destinations.

The post-publication findings showed that an analogous problem could also occur at the level of state/request compatibility.

In v0.1.1, the SUSPENDED + ACTION combination had no explicit interpretation.

Because the missing interpretation did not produce an explicit non-execution state, the ordinary execution path remained available.

The later versions changed this from an implicit outcome into an explicit governance decision:

Undefined compatibility
        ↓
Explicit evaluation
        ↓
HOLD + inspectable reason code

The value of this observation is not that the development process "proved" AIBL.

Rather:

A post-publication implementation defect happened to reproduce, at the development-process level, a structurally similar ambiguity to the kind of ambiguity the prototype was intended to expose at runtime.

That interpretation is retrospective and should be treated as such.

8. Review Method Note

The initial defect was identified through an AI-assisted adversarial review that included executable reproduction, rather than textual code inspection alone.

The AI-assisted review did more than identify the defect.

It also generated specific candidate resolutions, including proposed semantics and reason-code naming.

For the later RUNNING + REENTRY finding, the reviewer identified the untested state/request combination and proposed alternative treatments rather than only reporting that the case was undefined.

Other AI-assisted discussion also contributed to evaluating those alternatives and their governance meaning.

The project owner did not independently originate every correction or semantic option described in this Case Note.

Instead, the process was closer to:

Observed implementation behavior
        ↓
AI-assisted defect discovery
        ↓
AI-generated candidate interpretation / correction
        ↓
Project-side evaluation
        ↓
Human acceptance or rejection
        ↓
Implementation
        ↓
Executable testing
        ↓
Commit / versioned specification

The project owner retained final acceptance authority over whether a proposed interpretation or correction would become part of the prototype.

A candidate proposal therefore did not acquire specification authority merely because an AI reviewer generated it.

It had to be evaluated, accepted, implemented, tested, and incorporated into the versioned project.

Retrospectively, this creates a small parallel with another principle already present in the prototype:

Candidate ≠ Approved

This parallel was not intentionally designed into the review process and should not be interpreted as a planned governance experiment.

AI-assisted review functioned here as both:

a defect-discovery mechanism; and
a source of candidate resolutions.

It should not be interpreted as independent assurance, certification, or proof of correctness.

Likewise, the use of multiple AI systems may expose different assumptions or reviewer blind spots, but it does not by itself establish reviewer independence or eliminate the possibility of correlated model failure.

9. Case Summary

The correction history can be summarized as:

v0.1.1
22 / 22 PASS
        ↓
Untested SUSPENDED × ACTION combination discovered
        ↓
Implicit execution path reproduced
        ↓
v0.1.2
SUSPENDED + ACTION → HOLD
23 / 23 PASS
        ↓
Full Request Type × Operational State space enumerated
        ↓
RUNNING × REENTRY found undefined
        ↓
Full 2 × 2 compatibility matrix defined
        ↓
v0.1.3
24 / 24 PASS

The central lesson is:

The important failure was not that the system chose the wrong answer to a defined question. The question itself had not been defined for one reachable combination of state and request.

For governance-oriented systems, this suggests that review should examine not only whether expected cases return expected decisions, but also whether relevant combinations of state, request, authority, evidence, and transition semantics have been explicitly defined.

A second lesson emerged from the review process itself:

A proposed correction can be technically plausible without yet being authoritative.

Candidate resolutions still require explicit evaluation and acceptance before they become part of the governed specification.

10. Scope Boundary

This Case Note does not establish:

production readiness;
system safety;
legal or regulatory compliance;
completeness of the AIBL framework;
completeness of the prototype's remaining state space;
effectiveness of AI-assisted review as an assurance method;
independence of multiple AI reviewers;
superiority of the prototype over existing authorization, policy, IAM, or runtime-control systems; or
that the post-publication correction process was an intentionally designed AIBL experiment.

It documents one concrete implementation finding, the review path that exposed it, and the governance semantics introduced to address it.

The prototype remains a small reference implementation intended to make assumptions inspectable, executable, testable, and open to criticism.