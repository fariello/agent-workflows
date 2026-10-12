# Review findings: plan anzu8q

- Subject-Id: anzu8q
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2f4c97052`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
Upstream interfaces were taken from the reviewed text of `8d0qsg` (Order 05, reviewed earlier in this sweep),
`sk2rbf` (Order 04) and `g55j1e` (Order 03); none of their tools exist at this HEAD yet.

Demonstrations (temp dirs only, worktrees removed, `git worktree list` count unchanged):
- Detached worktree of `19313eed^`, `tests/test_run_freeze.py` with `nzzu8n`'s pytest flags: `12 passed in 0.36s`.
- Context-to-nodeid longest-prefix rule on a real collected id:
  `tests.test_lost_guard_census.LostGuardCensusBehavioralTests.test_classifier_bidirectional_and_mixed` ->
  `tests/test_lost_guard_census.py::LostGuardCensusBehavioralTests::test_classifier_bidirectional_and_mixed`;
  an unknown module maps to none.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G executability (data provenance) | `8d0qsg` E-02 ("All tool output (JSON) goes under a temp dir"), E-03/E-04 row contents; this plan E-01 original ("baseline reaching-test count and `subprocess_only` flag from Order 04's data") | The reaching tests and `subprocess_only` flags, which E-01 and E-03 need and which Order 07 uses as its narrowed selection, are not in any committed record by the time this plan runs, so the executor could not produce them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-04 (run first) re-measures `baseline` at this HEAD, records counts and flags by key, and converts contexts to nodeids by a demonstrated rule. E-03 records each row's selection. V-04 added. |
| PR-002 | HIGH | IN-SCOPE | A correctness (operators) | `g55j1e` E-04 "Scope note: `noop` is DROPPED"; Operators list | E-01 offered `noop`, which the probe does not accept, and claimed an operator "breaks exactly that property", which whole-function replacement cannot do for a multi-behavior function. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Operator list set to the five; wording changed to "which assertion it makes fail", with the whole-function limit and the positive control named. F-05 added. |
| PR-003 | MEDIUM | IN-SCOPE | A correctness (regression verdict) | E-02 original; review replay at `19313eed^` (F-06) | A deleted test already failing at the trim would be labelled `regression` ("no explaining commit is `regression`"), and `git log -- <module path>` misses a symbol that moved module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 first re-runs each nodeid at `19313eed^` in a throwaway worktree (`stale-at-trim` if it fails there) and adds `git log -S<symbol>`. |
| PR-004 | MEDIUM | IN-SCOPE | C cost model | E-03 original; `g55j1e` E-01 (baseline plus mutant plus flaky re-run); `rq3q7v` Scope (survivor plus control) | Cost "estimated from their count" was undefined, and a probe costs at least two selection runs, with two probes per property. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cost = 2 x S + 2 x C from timed unmutated runs, pasted; cap applies to summed cost. |
| PR-005 | MEDIUM | IN-SCOPE | A (one row per group vs per property) | Concern ("one function can carry several behaviors"); E-01 original "one row" | E-01 forced one property per function key, contradicting its own Concern. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | One row per distinct property; V-01 checks key-set equality instead of row-count equality. |
| PR-006 | MEDIUM | IN-SCOPE | C operability (index) | `.aw/.gitignore:50-51`; `8d0qsg` PR-003/F-07 | E-03 and V-03 demanded the gitignored index be committed and `--check` conform, which it cannot at this HEAD. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Commit the doc only; evidence via `aw research find --id` and no `--check` line naming the doc. |
| PR-007 | LOW | UNDER-SCOPE | Traceability (deferrals) | Deferred section original (`pass-shared` carried by `rq3q7v`); `8d0qsg` E-04 lists only `pass-exclusive` and `fail-investigate` | `pass-shared` files never reach this plan's input, so "listed in `triaged-not-mutated` if they do not fit the cap" was not executable; the carrier was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 lists every `pass-shared` file from `## Verdicts` as `triaged-not-mutated` (`no exclusive reach`); carrier set to `xmr5qj`. `stale-at-trim` deferral added with a cross-reference: `xmr5qj` E-03 (d)'s no-carrier list should gain `stale-at-trim` (that plan is `to-review`; its reviewer owns the edit). |
| PR-008 | LOW | IN-SCOPE | Gate / OQ owner | Gate original; OQ-01 `Owner: none` | Gate lacked the paste-actual-output rule, fence wording, temp-dir rule, ordering and prerequisite; OQ owner `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate itemized; owner `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where do reaching tests come from, given Order 05 did not keep them? | Re-run `baseline` here (E-04). | Amend `8d0qsg` to commit the JSON, rejected because that plan is `reviewed` with a doc-only commit and the JSON is large; re-run `8d0qsg`'s diff, rejected because only the baseline side is needed. | `8d0qsg` E-02; `sk2rbf` E-01 (~6 min). | yes |
| D-2 | How to treat a deleted test that fails at the trim's own parent? | New verdict `stale-at-trim`, no carrier. | Call it `regression`, rejected because nothing changed after the trim. | F-06 replay. | yes |
| D-3 | Keep the 40 / 3 h cap? | Keep, applied to the defined summed cost. | Raise it, rejected: no evidence the cost model is wrong yet. | OQ-01; `oyh28b` F-06. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
