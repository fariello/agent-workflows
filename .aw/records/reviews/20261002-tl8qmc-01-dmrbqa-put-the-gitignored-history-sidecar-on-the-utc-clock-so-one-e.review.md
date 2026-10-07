# Review findings: plan dmrbqa

- Subject-Id: dmrbqa
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review-sweep lane. Plan committed and byte-identical to the lane input, so
no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize`
clean after revision (one intermediate `IPD-I305` from prose in a `Depends on:` field, repaired).

Measured (gitignored probe `.aw/state/review-probe-dmrbqa/probe.sh`, `mktemp` repos, real CLI, no production edit), at
03:42 UTC 2026-10-07:
- `TZ=XXX-20` (local 2026-10-07 = UTC): inline `- 2026-10-07 same-status (aw backlog): probe msg`, sidecar
  `"date": "20261007"`; agree because no skew.
- `TZ=Pacific/Honolulu` (local 2026-10-06, UTC 2026-10-07): inline `- 2026-10-07 same-status (aw backlog): probe msg`,
  sidecar `"date": "20261006"`; `aw record-history` -> `- 20261006 [backlog] aw backlog set (aw backlog): probe msg`.
  The divergence the plan predicts is LIVE.
- `record_history.append` / `append_rename` still `date = _date.today().strftime("%Y%m%d")`
  (`agent_workflows/record_history.py:64`, `:228`); `artifact_core.utc_history_date()` returns UTC `YYYY-MM-DD`
  (`agent_workflows/artifact_core.py:221`), no compact variant.
- `5ivkdh` executed; its E-01 says "DO NOT ADD A COMPACT (`YYYYMMDD`) VARIANT ... `dmrbqa` ... can derive it as
  `<helper>().replace("-", "")`" (`.aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-...ipd.md:48`).
- `tests/test_history_date_clock.py` (subprocess `TZ`) and `tests/test_scaffold_history_clock.py` (`XXX-24`/`XXX+23:59`,
  tzset with restore) exist; neither reads `history.jsonl`.
- No CLI path passes `date=` to the sidecar: `aw backlog set` has no `--date`; `specs._sidecar_append`
  (`agent_workflows/specs.py:250`) omits it.
- `tests/test_history_provenance.py tests/test_history_label_parity.py tests/test_backlog.py`: `59 passed in 5.78s`.
- `TZ=XXX-24` local 2026-10-08, `TZ=XXX+23:59` local 2026-10-06, UTC 2026-10-07.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C. Architecture / G. premise currency | `5ivkdh` E-01 (executed) "DO NOT ADD A COMPACT ... VARIANT"; `artifact_core.py:221`; plan Scope-Paths excludes `artifact_core.py` | E-01 instructed "if `5ivkdh` did not add [a compact variant], ADD IT THERE", i.e. edit undeclared `artifact_core.py` and contradict the sibling's shipped, reviewed decision naming this plan as the caller that should derive it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now derives `_core.utc_history_date().replace("-", "")` and removes the conditional add; V-01 confirms no variant added; Concern records the now-live divergence. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (vacuous-pass risk) | probe: `XXX-20` local == UTC at 03:42 UTC; `tests/test_history_date_clock.py`, `tests/test_scaffold_history_clock.py` | E-02 rested on a stale "zero tests set TZ" premise and recommended zones that are each skewed only part of the day, so a run outside the window passes vacuously for that zone. The existing tests already establish safe patterns. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 cites both shipped patterns, prefers `XXX-24`/`XXX+23:59` (always one zone skewed), requires failing if neither zone skews, tolerates crossing midnight, and notes the existing clock test never reads the sidecar. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Reachability | `specs.py:250`; `aw backlog set --help` has no `--date` | V-01 and Required test 4 demanded explicit-`date` precedence by observable output, but no CLI surface passes `date` to these functions, so the plan did not say how to observe it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names the observation: call `record_history.append(..., date=...)` and `record_rename(..., date=...)` directly and assert the written sidecar line. |
| PR-004 | MEDIUM | IN-SCOPE | B/G. Shared-checkout safety, sequencing | Required tests 1 "stash or revert the production edit"; E-02 `Depends on: E-01` | Pre-fix evidence was to come from stash or revert (forbidden in a shared checkout), and the dependency order put the fix before the test, so the red observation could be forfeited. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Test-first ordering made machine-visible (E-01 depends on E-02); run-before-edit or a `git show HEAD:` scratch import replaces stash/revert. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criterion | commit `8c460a9a1` fixed the three authoring-time failures | V-02 and Required test 7 pinned "the same three pre-existing failures" as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline re-derived at execution HEAD and compared by node id. |
| PR-006 | LOW | IN-SCOPE | Honest documentation | `CHANGELOG.md:31` "across all history writers" | The plan relied on `5ivkdh`'s CHANGELOG entry without noting that entry is currently false for the sidecar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec/doc sync notes this plan makes that entry true; no CHANGELOG edit (undeclared). |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | gate item 9 "Finalize with `aw ipd finalize ...`" unconditionally | Gate instructed the executor to finalize unconditionally and limited commits to the two Scope-Paths, excluding the plan file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize ownership conditional on runner vs hand execution; plan file included in commit set. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Add a compact UTC helper to `artifact_core`, or derive locally from the shipped one? | Derive `_core.utc_history_date().replace("-", "")` | Add `utc_history_date_compact()` to `artifact_core` | `5ivkdh` E-01 shipped decision; `artifact_core.py` not in Scope-Paths; `specs.run_new` precedent | yes |
| D-2 | Which skew zones should the test use? | `XXX-24` and `XXX+23:59` | `XXX-20` / `Pacific/Honolulu` as authored | probe at 03:42 UTC: `XXX-20` unskewed; `tests/test_scaffold_history_clock.py` precedent | yes |
| D-3 | How should explicit-`date` precedence be observed? | Direct calls to `append` / `record_rename` asserting the written line | Add a CLI `--date` to backlog set (out of scope, `fcnz1r` area) | No CLI path reaches the parameter (probe and `specs.py:250`) | yes |
