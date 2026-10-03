# Review findings: plan 840y6i

- Subject-Id: 840y6i
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `63ad100b8` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Re-verified (scratch under gitignored `.aw/state/`, deleted after):
- `attention._age_marker` uses `date.today()`; docstring ends "Deterministic: compares ISO dates only."; two callers
  (`attention._render_item_row`, `cli.py` board renderer), neither passing a date.
- Real corpus replay (`aw attention --all --format json`, 2358 items) at 20:50 UTC: `XXX-20 flips 10`, `XXX+12 flips 0`.
- `workflow_artifacts_prune._parse_run_date`: `run-20261002T110915Z-830789 None`, `20261002-110915 2026-10-02`.
  Under `TZ=XXX-20` the runner-shaped id goes through the local mtime fallback: `(0, 2026-10-03)`, consistent.
- `00-run-protocol.md`: workflow-artifacts run ids are "a timestamp run ID ... YYYYMMDD-HHMMSS". `DECISIONS.md` D55:
  "all human-facing timestamp NAMES use the creating machine's LOCAL time ... AND `workflow-artifacts/` RUN_IDs
  (`YYYYMMDD-HHMMSS`)". `engine.py` mints `datetime.now().strftime("%Y%m%d-%H%M%S")` (local).
- Spec `2vev8j` approved; Section 4.4 heading "One timezone for every writer". OQ-02 carrier `6ly144` is an open backlog item.
- Sibling writer plans `5ivkdh` (reviewed), `9wcei0`, `rfyrvp`, `dmrbqa` all pending; none executed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | A. Correctness / D. Invariants | `workflow_artifacts_prune._parse_run_date` (leading `YYYYMMDD` only); probe `run-20261002T110915Z-830789 None`; `DECISIONS.md` D55 "AND `workflow-artifacts/` RUN_IDs (`YYYYMMDD-HHMMSS`)" | F-02/E-03 claimed the prune reader compares a UTC run id against a local today. The cited runner id does not parse (falls back to local mtime vs local today, consistent); the ids that do parse are workflow-artifacts RUN_IDs that D55 rules LOCAL. Converting today to UTC would have introduced a mixed-clock error into a DELETION planner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed E-03/V-03 and `workflow_artifacts_prune.py` from Scope-Paths; corrected Concern, Scope, Goal, F-02, F-03, F-06, OQ-01, Proposed changes, Required tests, gate paragraph; E-04/V-04 now carry the prune reader as a fourth correctly-LOCAL row. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (vacuous-pass) | Review probe: `XXX-20 flips 10`, `XXX+12 flips 0` at 20:50 UTC | E-01 asked for one east and one west zone but did not guarantee either is skewed at the hour the test runs, so the guard could pass vacuously at some hours. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires a pair covering all 24 UTC hours (`XXX-20` from 04 UTC, `XXX+12` before 12 UTC) and a test-side assertion that a skew window was hit; V-01 updated. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (xdist isolation) | E-01 "SET `TZ` FOR THE CODE UNDER TEST ONLY, restoring it afterwards"; `pyproject.toml` addopts `-n auto` | An in-process `os.environ['TZ']` plus `time.tzset()` changes the clock for every later test in the same xdist worker. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now drives `_age_marker` in a subprocess with `TZ` in its env (pattern demonstrated at review); V-01 confirms no in-worker `tzset`. |
| PR-004 | LOW | IN-SCOPE | E. Testing (RED-at-base validity) | E-01/E-02 injectable `today` | If the RED-at-base cases passed `today=`, they would fail at base with a `TypeError` rather than on the verdict, which proves nothing about the clock. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Timezone cases call `_age_marker` without `today`; a separate GREEN-after-only case pins the seam. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract / live-artifact bar | Post-gate lifecycle "move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition"; "ten flipping items"; "Baseline is `3 failed, 4624 passed, 2 skipped`" | Missing `aw ipd begin`, conditional runner/executor finalize ownership and scope-justification wording; live counts (ten flips, suite counts) used as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lifecycle paragraph rewritten; the bars are now "nonzero re-derived count to zero" and a pre-edit bare-suite failure set captured at execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the prune reader stay in scope? | No: remove it; it is correctly LOCAL | Keep E-03 (introduces a UTC-vs-local error on D55 local RUN_IDs); re-scope E-03 to parse `run-...Z` ids as UTC (a new feature, not this bug, and the prune tree does not use that shape) | D55; `00-run-protocol.md`; `_parse_run_date` probe | yes |
| D-2 | How does the test vary the timezone? | Subprocess with `TZ` in env, fixed-offset pair `XXX-20`/`XXX+12`, test asserts a skew window was hit | In-worker `tzset` (leaks across xdist tests); a single zone (vacuous at some hours) | Review probe; `pyproject.toml` `-n auto` | yes |
