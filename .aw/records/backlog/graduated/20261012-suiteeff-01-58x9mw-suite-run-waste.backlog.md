- Id: 58x9mw
- Status: graduated
- Graduated-To: z3cqvz
- Blocks-Release: next
- Set: suiteeff
- Priority: high
- Work-Kind: bug
- Summary: Full pytest suites are run wastefully and concurrently: 322 runner baselines never collected, 1,258 agent full-suite runs (91.5h) with no reuse, oversubscribed -n auto, and no machine-wide serialization

## Workflow history
- 2026-10-12 graduated (aw set): graduated to Set suiteeff (z3cqvz, 9ec94f, 0o0wt2, xvm6no, 1qut7y; all to-review, lint clean, coverage pass)
- 2026-10-12 created (aw backlog): filed from operator investigation of 2026-10-12 stalls

## Measured (2026-10-12, October run records `.aw/records/runs/run-202610*`)

- The runner's pre-work SUITE BASELINE (`runner_shared.start_suite_baseline`, a full `python3 -m pytest` in a detached checkout per execute attempt) STARTED 322 times and was COLLECTED 0 times (`suite-baseline-collected` events: 0; `attempt["suite_baseline"]` present on 0 of 318 attempts). Its collection is inside `if integration_gate_relevant and not validate:` in `execute_item_core`, and 318 of 320 baseline-bearing attempts ran with validation ON (`options.validate` absent, `no_verify` False, so `validate = not (no_verify or no_audit)` is True). Every one of those baselines burned a full 12-core suite for nothing, then was abandoned in the turn's `finally`.
- `post_merge_revalidation` on 269 items: every record `skipped: true`, reason "validation is ON, so the VERIFIER's verdict is this item's trust signal". So the runner's own suite paths are OFF in the default mode; the suites that actually run are the AGENTS'.
- Agent turns ran 1,258 FULL-suite pytest invocations (1,047 executor, 211 verifier; plus 4,194 narrowed), median 216s, p90 622s, 91.5 hours of wall time total, each at `-n auto` (12 workers on a 12-core host).
- Under seven concurrent drivers (load average 75-88 on 12 cores, 2026-10-12) full suites ran past the 900s stall watchdog and three runs lost 9 of 11 turns to `ipd-stalled`.
- Exact-tree reuse is modest: the 322 baselines span 284 distinct whole trees and 261 distinct code trees (agent_workflows, tests, conftest.py, pyproject.toml, tools), i.e. 61 (19%) were exact repeats. Per-test-FILE selection by static import closure does not help: the median test file transitively imports 154 of 186 package modules, so a typical one-file step invalidates 92% of test files. Consecutive base commits differ by a median of 1 package file and 1 test file, which is what makes per-TEST (coverage-based) selection promising and unmeasured.

## Ask

One Set: remove the wasted baseline, route full-suite runs through one shared tree-keyed result cache with a bounded worker count, serialize full suites machine-wide with watchdog-visible waiting, and measure (then possibly adopt) coverage-based test selection for agent iteration while keeping the full suite as the integration authority.
