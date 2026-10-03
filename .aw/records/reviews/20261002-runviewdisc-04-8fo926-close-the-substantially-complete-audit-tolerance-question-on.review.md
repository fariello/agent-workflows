# Review: Close the substantially-complete audit tolerance question on measurement

- Subject-Id: 8fo926
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits and `--phase review-finalize` was clean after them. The `pre-transition` phase reported only the expected not-yet-executed findings (S404).

I re-measured at lane HEAD `fbb729c65`, in memory, with no repository change. The sweep used `audit_artifact` against a temporary git repo, `build_finalize_evidence_index`, and RETIRED banners. Results:

- `hasattr(aa,'_status_disagrees')` is `False`.
- `_RUN_SUCCESS_STATUSES` is `frozenset({'executed'})`.
- The fail-gate aliases are `blocked`, `failed-safely`, `substantially-complete`.
- `canonical_terminal_status('complete')` is `complete`, and `complete` is not in `TERMINAL_STATES`.
- `tests/test_artifact_audit.py`: `24 passed`.

Sweep table (270 combinations each):

| sweep | mutation | differing |
|---|---|---|
| substantially-complete vs complete | none | 0 |
| fail-gate family, members vs each other | none | 0 |
| substantially-complete vs complete | `+fail-gate` | 168 |
| fail-gate family, members vs each other | `+fail-gate` | **0** |
| substantially-complete vs complete | `+substantially-complete` (legacy spelling) | 0 |
| each family member vs complete | `+fail-gate` | 168 each |

The classes I observed were `retired`, `unchanged`, `unknown`, and `regressed` (the last only under mutation).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Testing / fence falsifiability (E) | plan E-03 "the four ... ALL indistinguishable"; measured family-vs-each-other under `frozenset({'executed','fail-gate'})`: 270 compared, 0 differing | As authored, E-03 compares family members to EACH OTHER. All four canonicalize to `fail-gate`, so the `fail-gate` mutation moves them together and the test CANNOT fail. E-03, V-03, and the plan's central "enforceable rather than merely written" claim all depended on that failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now compares each member to the non-success reference `complete` and collects every member that diverges into one message. Measured: 0 divergences at HEAD and 168 per member under the mutation. |
| PR-002 | MEDIUM | IN-SCOPE | Decision honesty | plan OQ-02 "A future change that deliberately tolerates the whole family stays green" | OQ-02 says a family-wide tolerance passes the fence. That statement is the PR-001 defect worded as a feature, and it contradicts the plan's goal of making the `fail-gate` one-liner visible. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 now says a family-wide tolerance turns the fence RED by design, and explains why that cost is intended. Owner set to `plan author`. |
| PR-003 | LOW | UNDER-SCOPE | Validation (E) | plan E-01(2) | E-01 shows the sweep finds 0 differences at HEAD, but never shows that the sweep CAN detect a difference. A broken harness would also report 0. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(2) now also requires the `fail-gate` mutation to make the sweep distinguish the pair (168 of 270 at review). |
| PR-004 | LOW | IN-SCOPE | Execution contract (G) | plan gate "STOP and report"; "finalize through the tooled lifecycle" | The defect-found clause said STOP rather than file it. The lifecycle transition did not say who owns it, the runner or the executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The clause now says file with `aw backlog new` and report. The gate now states conditional finalize ownership. The E-01 stop is labelled a premise-invalidation stop, which is legitimate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should the fail-gate family fence compare against? | Each member against `complete` | Members against each other (cannot fail, measured 270/0); members against `executed` (would also pin `executed`'s tolerance, so over-rigid) | in-memory sweep at `fbb729c65`; `canonical_terminal_status('complete') == 'complete'`, which is outside `_RUN_SUCCESS_STATUSES` | yes |
| D-2 | Should a deliberate family-wide tolerance turn the fence red? | Yes | Stay green (the authoring OQ-02) | `artifact_audit` refusal precedent cited in the plan's Step 0 conventions; F-05 `blocked` hazard | yes |
