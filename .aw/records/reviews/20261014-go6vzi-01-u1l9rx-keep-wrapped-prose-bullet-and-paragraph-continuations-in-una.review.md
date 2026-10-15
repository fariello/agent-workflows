# Review findings: plan u1l9rx

- Subject-Id: u1l9rx
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`90ac6c2fc`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review; `--phase review-finalize` conforms after the revisions, and `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

The plan's thesis and its measurements were REPRODUCED at review, with the proposed `in_prose` extractor implemented as a scratch function under gitignored `.aw/state/` and monkeypatched over `ipd_lint.unattached_section_prose`. The scratch was then deleted.

- `ipd_lint.unattached_section_prose` does drop every indented line (`if raw[:1].isspace(): continue`), and `runner_shared.probe_cache_payload` is its only production caller.
- Commit `592bfbf0b` ("put each completion criterion's OWNER on the probed first line") unwrapped exactly the three `m0kl28` bullets F-01 quotes.
- Corpus: 91 orchestrators. 21 payloads moved (20 `executed`, 1 `superseded`). The only pending orchestrator, `k93w2g`, kept digest `d726a52a...51af` under both extractors. There were 0 shared prose lines over 40 characters and 0 shared cells over 25 characters. F-02 and F-03 are confirmed.
- With the scratch extractor patched in, the existing default suites (`test_orchestrator_probe_payload.py`, `..._shape_composed.py`, `..._shape_gate.py`) gave `34 passed`, and the livecorpus Groups A/B/C gave `3 passed`. The `c3` subfield-continuation pin still holds.
- A synthetic wrapped `OWNER: syn002 (executed).` bullet FAILED its assertion under the current extractor. It PASSED under the proposed one, with the E-01 leaf continuation present only in `e_items`. So the new test is falsifiable.
- The `coverage_record.py` freshness check compares `rec.fingerprint == probe_cache_digest(plan_text)`, so a moved digest re-probes; it does not wrongly pass a plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 1 obligation(s) name no durable carrier: deferred row 1` | Deferred was written as the bullet `- None.`, which the carrier rule parses as an uncarried obligation, so the plan would fail its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote it as bare `None.` (the convention in executed plans such as `mcbph5`). The rule is cleared. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Honest documentation | `runner_shared.probe_cache_payload` docstring "Indented non-sub-field lines inside allowlisted sections leave 476 lines (74,625 characters) invisible to both extractors, carrying 14 hazard hits" | E-02 updated the prose but did not address this measured figure, which becomes false once wrapped continuations are joined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 must re-measure with a date or go qualitative, and must not leave the old numbers. V-02 checks for it. |
| PR-003 | MEDIUM | IN-SCOPE | G. Re-derivation convention | F-03 "single pending orchestrator `k93w2g` ... retains its exact digest"; V-items demanded no impact evidence | The fingerprint impact on pending orchestrators is a live-artifact count measured at authoring. No V-item re-derived it at execution, so a new pending orchestrator could re-probe without anyone being told. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires the old-vs-new digest for every pending orchestrator, re-derived at execution, with any moved digest named. |
| PR-004 | LOW | IN-SCOPE | E. Evidence specificity | V-03 listed commands only | V-03 did not say which behaviors its pasted output had to show. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now names the four new behaviors and that `c3` still passes. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; Scope-Paths | The gate lacked the honesty rule, never-push/tag, `aw ipd begin`, conditional finalize ownership, the Blocks-Release note, and an unsafe-condition stop. It also told the executor unconditionally to `aw ipd finalize`. The plan file was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract, with finalize conditional on runner ownership, and the plan path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01 (blank line terminates a continuation)? | Yes, as authored | Let continuation span blank lines | `ipd_lint.leaf_action_blocks` `if not stripped: break`; review reproduction of 0 Group A movers | yes |
| D-2 | Is a spec amendment needed? | No | Amend r07vma Section 3a | Neither approved spec mentions indented-line exclusion (`rg -i indented` over both specs is empty); the change fixes an extractor bug inside the specified contract | yes |
| D-3 | Re-measure or drop the docstring figures? | Executor's choice of either, old numbers forbidden | Mandate re-measurement only | Both are honest; the forbidden case is stale numbers | yes |
