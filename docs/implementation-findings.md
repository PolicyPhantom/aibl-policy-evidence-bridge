# Implementation Findings

## IF-001

- Date: 2026-08-22
- Initial assumption: The minimal example's typographic heading would render in the default terminal.
- Observed implementation problem: A Windows console using CP932 could not encode typographic en/em dashes and stopped while printing the heading, after the governed result files had been generated.
- Why it matters: The documented public command must complete without requiring manual terminal-encoding changes.
- Classification: Implementation Bug
- Proposed response: Use an ASCII-only console heading while retaining UTF-8 for repository documents and generated artifacts.
- Design change required: NO

No governance-semantic ambiguity or design change was required during the original v0.1.1 implementation.

## IF-002

- Date: 2026-08-22
- Initial assumption: Normal ACTION evaluation would be governed entirely by current policy, authority, evidence, and operating conditions.
- Observed implementation problem: Post-publication adversarial review found that `SUSPENDED + ACTION` could produce `ALLOW -> EXECUTED` while leaving the operational state `SUSPENDED`.
- Why it matters: Suspension must prevent normal action execution; restoration must pass through REENTRY.
- Classification: Governance Implication
- Proposed response: In v0.1.2, return `HOLD` with `OPERATIONAL_STATE_SUSPENDED_REQUIRES_REENTRY` immediately after input validation for a normal ACTION in SUSPENDED.
- Design change required: YES (authorized for v0.1.2)

No additional implementation ambiguity or unexpected finding was observed while applying the authorized v0.1.2 change.
