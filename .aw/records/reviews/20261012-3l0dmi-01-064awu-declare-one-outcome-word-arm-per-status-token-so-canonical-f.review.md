# Review findings: plan 064awu

- Subject-Id: 064awu
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `04ba026c0`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Re-measured with the lane's own package (`PYTHONPATH=.`): `TERMINAL_STATES` has 24 tokens and `TERMINAL_STATUS_ALIASES` 10 pairs exactly as F-02/F-03 list; all 24 no-refusal words reproduce F-02. Confirmed: the ladder literals (`render_stream.render_run_summary_table`, `# Outcome label`); `runner_shared` imports `render_stream` at module level and `render_run_summary_table` imports `canonical_terminal_status` function-locally; `INTENTIONALLY_UNMAPPED_DRIVER_STATUSES` and its quoted comment; both pinning tests in `tests/test_zero_dispatch_outcome.py`; spec `uonrjg` 7.2 rows; `lifecycle_style._RUNNER_ITEM_PAIRS`; `6b94a4d9d` hunks (`return ("fail-verify" if exit_code == 0 else "fail-gate")`, `return "fail-gate"`); BLOCKED renders SGR 36; `tools/dead_status_token_scan.py` prints `Total flagged sites: 0 (1 exempt)`; `79d4ix` exists (graduated); `fr19jr` OQ-05 carrier `3l0dmi`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A / D (evidence accuracy) | Plan F-02 "A recorded refusal changes only `substantially-complete`"; review measurement via `render_stream.record_refusal` | Wrong: a refusal flips EVERY success-class token (`executed`, `approved`, `substantially-complete` -> PARTIAL; `reviewed` -> QUEUED at 0 attempts, PARTIAL at 1). E-04(a)'s expected table authored from F-02 would have been wrong for refusal cases. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 restated with the measured refusal behavior; E-04(a) now covers both refusal states explicitly (four words per token). |
| PR-002 | MEDIUM | IN-SCOPE | E (evidence feasibility) | Plan F-02 / E-04 "attempts=0, attempts=1"; renderer raises `TypeError("'int' object is not iterable")` for an int | Fixture shape stated as ints; `attempts` must be a list. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02, E-04 and V-03 now specify `attempts=[]` / `attempts=[{"number": 1}]`. |
| PR-003 | MEDIUM | IN-SCOPE | E (V-03 validity) | Plan V-03 before/after via `git worktree add`; review: a script outside the tree imported `/.../agent-workflows/agent_workflows` (editable install) unless `PYTHONPATH` was set | The before/after diff could compare the same package twice and pass vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now requires `PYTHONPATH=<tree>`, `AW_NO_REEXEC=1`, and pasted `agent_workflows.__file__` for both runs showing different trees. |
| PR-004 | LOW | IN-SCOPE | A (claim scope) | Plan F-04 "the current ladder already AGREES with the spec"; spec `uonrjg` 7.2 rows put `fail-lane`/`fail-merge` in blocked, `not-run`/`not-attempted` in abandoned | Overgeneralization: ladder words are not a projection of 7.2 stages; agreement holds only for the `fail-gate`/`failed-safely` pair. The `not-attempted` divergence has no spec support. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04, E-02 and OQ-01 now scope the spec claim to that pair and note the `not-attempted` divergence rests on `4po0sc` only. |
| PR-005 | LOW | IN-SCOPE | A (evidence accuracy) | Plan E-02 "whose own comments promise it is already rendered FAILED"; `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS` comment is the only such text; F-07 `rg` returns this plan itself | Quote attributed to all writers; F-07 claimed the `rg` printed nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 attributes the quote to the one comment and names the writers by symbol; F-07 re-measured and reworded. |
| PR-006 | LOW | IN-SCOPE | Project rule (OQ owner, V-04 pattern) | OQ-01 `- Owner: none`; V-04 `rg -n "inspect|import ast|read_text\("` | Resolved question had no owner; V-04 pattern would false-positive on a docstring mentioning "inspect". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Owner: plan author`; V-04 pattern anchored to import statements plus `read_text(`/`getsource`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the review reopen OQ-01 because the ladder disagrees with spec `uonrjg` 7.2 on several tokens beyond the alias pairs? | No; keep OQ-01 resolved (c) and narrow the spec claim. | Reopen OQ-01 as blocking; widen scope to align every word with 7.2. | Plan Scope OUT forbids changing any word; outcome word is a run-level verdict distinct from the stage table; the `fail-gate`/`failed-safely` pairing does agree with 7.2 (`.aw/records/specs/approved/20260913-uonrjg-...spec.md` 7.2). | yes |
