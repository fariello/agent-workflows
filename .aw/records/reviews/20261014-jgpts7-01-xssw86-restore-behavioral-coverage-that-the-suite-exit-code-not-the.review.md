# Review findings: plan xssw86

- Subject-Id: xssw86
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `52011db5e`. The plan was committed and unchanged (sha256 matched the sealed lane input `e005f214...`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase review-finalize` is clean after the revisions. `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`; only the expected `IPD-S404` not-yet-performed errors remain.

Re-measured with a prototype of exactly the planned tests under the gitignored `.aw/state/` (deleted afterwards). Mutations were applied through a `-p` plugin with no production edit:

| Run | Result |
|---|---|
| unmutated | `6 passed` |
| mutant A (`integration_is_earned` forced `passing=True` on an empty list, rebound on `runner_shared`, `oc_runipd`, `agy_runipd`) | `1 failed, 5 passed` (red-empty test) |
| mutant B (`new_failures_since_baseline` / `unattributed_merged_failures` forced `suite_passed=True`) | `2 failed, 4 passed` (E-03, E-04) |

The cited history resolves: `19313eed7^:tests/test_suite_adjudication.py:273` holds `class TheExitCodeIsTheAuthorityAndNotTheList`, and its `_suite_result` / `_asks_the_agent` helpers match E-01. `oc_runipd.integration_is_earned` and `agy_runipd.integration_is_earned` are both the re-exported `runner_shared.integration_is_earned`. No test references `new_failures_since_baseline` or `unattributed_merged_failures`, which confirms F-4.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | pre-transition lint: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3` | None of the three Deferred rows had a carrier, so the plan could never finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row 1 is now in scope as E-05 (see PR-002). Rows 2 and 3 carry a reasoned `Carrier-Declined`. The rule is cleared. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Docs honesty | `agent_workflows/runner_shared.py:28128`, `:28594`, `:28726`, `:28919` each say "`TheExitCodeIsTheAuthorityAndNotTheList` ... no live guard currently asserts this" | Once the guard lands, four production comments would falsely say the property is unguarded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 for a comment-only repoint and added `runner_shared.py` to Scope-Paths. The bare suite now runs last, after E-05. Same remedy as sibling `tosnwd` PR-002. |
| PR-003 | MEDIUM | IN-SCOPE | E. Evidence feasibility | `pip list` has no `pytest-subtests` | V-01 demanded `-v` output showing PASSED "for both host subtests". Without the plugin, pytest prints one line per method, so that evidence cannot be produced. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands the per-method PASSED line plus the source excerpt of the host loop. |
| PR-004 | MEDIUM | IN-SCOPE | E. Mutation mechanism | `oc_runipd.py:449` / `agy_runipd.py:606` `integration_is_earned as integration_is_earned` | The mutation check was ambiguous ("patch `integration_is_earned`'s suite input"). It did not say that both host aliases must be rebound, or that V-04 needs mutation evidence for E-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified mutants A and B as a `-p` plugin with the measured results. V-04 now requires mutant-B output. |
| PR-005 | LOW | IN-SCOPE | E. Control strength | `runner_shared.gate_answer_is_warranted` returns `False` when `earned` | The passing control did not assert that a green suite is never escalated, which was the deleted `AGreenSuiteIsNeverTaxedWithAQuestion` intent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(d) now also asserts `warranted is False`. The note on the host loop clarifies it is a re-binding guard, not an identity pin. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | old gate paragraph; OQ-01 `Owner: none` | The gate lacked the hard-MUST paste rule, the scope fence, `aw ipd begin`, and the runner/hand finalize split. It also said "Move the plan to `executed/`". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the standard contract (no stop-on-scope wording). The owner is set to the plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the stale comments be fixed in this plan or in a filed follow-up? | In this plan (E-05), comment-only. | File a backlog follow-up (rejected: it leaves four false comments live in the interim, and the sibling `tosnwd` precedent took the in-plan route) | `.aw/records/reviews/20261014-xhrpeg-01-tosnwd-...review.md` PR-002; `runner_shared.py:28128` | yes |
| D-2 | Should the per-host loop remain, given that both hosts alias one function? | Keep it, without an identity assertion. | Drop the loop; assert identity (rejected as a P16 structure pin) | `python3 -c` check: `oc_runipd.integration_is_earned is runner_shared.integration_is_earned` and the agy equivalent both `True` | yes |
