# Review findings: ipd z6wodh

- Subject-Id: z6wodh
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed `.aw/records/plans/pending/20261121-rryabb-01-z6wodh-scrub-driver-restart-env-vars-and-ignore-stale-aw-invocation.ipd.md` against backlog `rryabb`, `agent_workflows/runner_shared.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/attended_session.py`, `agent_workflows/runner_stop.py`, `conftest.py`, `tests/test_runner_resume_clears_stop.py`, `tests/test_statusline_behavior.py`, `tests/test_runner_startup_timings.py`, `tests/test_commit_run_trailers_env.py`, and spec `25kzda`. The diagnosis is correct and was reproduced at review. Six findings (`PR-001` to `PR-006`), all fixed in place.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | Right-sizing (R4) | plan E-04 (original text) | E-04 bundled four independent test surfaces (fixture refactor plus resume regression, three agent-launch child-env assertions, a pytest-subprocess probe, and implicit `resolve_invocation_start` unit coverage) in one item, failing diagnostics (a) through (c) of the conceptual-density check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-04 (fixture helper, resume regression (a), resolver and scrub regression (b)) and new E-06 (child-env regression (c), pytest-session regression (d)); added V-06; E-05 now depends on E-04 and E-06; diagrams, proposed changes, V-01 to V-03, and Scope updated to cite the new letters. |
| PR-002 | HIGH | IN-SCOPE | Executability, unbounded recursion (R2) | plan E-04 (c) original: "a pytest subprocess launched with both variables set sees neither variable and passes `tests/test_runner_resume_clears_stop.py`" | A test inside `tests/test_runner_resume_clears_stop.py` that launches pytest on that same whole file re-collects itself and recurses without bound; the item also did not say how the subprocess observes `os.environ`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 (d) now specifies a marker-gated probe test plus a launcher that targets only the probe node id with `-o addopts=` and asserts exit 0 and `1 passed`, and states the no-whole-file rule explicitly. |
| PR-003 | MEDIUM | UNDER-SCOPE | Validation evidence (R2) | plan E-04 Expected outcome "fail against unpatched code"; V-04 original | E-04 promised regressions that fail on unpatched code, but no V-item demanded RED evidence; V-01 cited "new runner_shared regression assertions from E-04" that E-04 never defined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (b) now defines direct `scrub_driver_restart_env` and `resolve_invocation_start(require_restart_env=True)` assertions; V-04 and V-06 demand RED output, obtained before the production edits or in a temporary base-commit worktree, and forbid `git stash` or reverting files in the checkout. |
| PR-004 | MEDIUM | IN-SCOPE | Live-artifact success criteria (R2 G) | plan E-05 Expected outcome; V-05 original | E-05 required `aw check all --agent` and `aw sanitize --agent` to "pass with zero failures" and V-05 demanded "N passed" lines from both, which neither command prints (both emit `aw.agent/v1` records), and the repository-wide outcome may carry findings this plan does not own. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and V-05 now require no failure or finding introduced by this change, with any pre-existing one shown to reproduce on the base commit (re-derived at execution), and demand the agent result records for those two commands. |
| PR-005 | LOW | IN-SCOPE | Spec sync truthfulness (R4) | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` "An operator `resume` (when `AW_DRIVER_RESTART` is not set) clears any recorded `driver_restart_refusal`" | The N/A claim did not name the one spec that describes this behavior; the spec already defines a run without `AW_DRIVER_RESTART` as an operator resume, so no edit is needed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec / documentation sync now cites spec `25kzda` and states why no amendment is needed. |
| PR-006 | LOW | IN-SCOPE | Precision and scope completeness (R1, P) | `agent_workflows/work_cmd.py` "env=att.child_env()"; `agent_workflows/runner_shared.py::pinned_child_env`; plan E-01 "read only when `AW_DRIVER_RESTART` is truthy when `require_restart_env=True`"; plan E-04 "repeated `env_manual` comprehensions" | E-01's conditional was hard to parse; E-04 named only `env_manual` while `ClearStopRequestHelperTests` uses `env`; the Scope check did not say why `work_cmd`'s interactive session and the driver's short-lived `pinned_child_env()` helper subprocesses are left unscrubbed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded E-01 (keyword-only parameter, explicit condition); E-04 names both variable spellings; Scope check records the deliberately unscrubbed paths and why. Added a cohesion rationale for the six-item count (advisory `IPD-Z603`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the extra test surfaces become a separate child plan or a sixth E-item in this plan? | A sixth E-item (E-06) in this plan, with a cohesion rationale. | A second child plan in Set `rryabb` (rejected: it would leave E-01 to E-03 without the regressions that prove them, and the whole change is five files with one root cause). | `aw ipd lint` reports only advisory `IPD-Z603` for six items; plan Scope-Paths lists five files | yes |
| D-2 | Should `work_cmd`'s interactive session and `pinned_child_env()` helper subprocesses also scrub the two variables? | No; leave them unscrubbed and record why in the Scope check. | Scrub inside `pinned_child_env` itself (rejected: it changes every caller, including non-agent helpers, beyond the bug's reach). | `agent_workflows/work_cmd.py` "env=att.child_env()" runs from a human shell; helper subprocesses never call `resolve_invocation_start`; the suite-baseline pytest child is covered by the E-03 `conftest.py` scrub | yes |
| D-3 | How should V-04 and V-06 obtain RED evidence without disturbing a shared checkout? | Run the new tests before applying the production edits, or in a temporary base-commit `git worktree`; never stash or revert. | Require `git stash` of production edits (rejected: AGENTS.md forbids stashing in a shared checkout). | AGENTS.md "Never 'fix' a polluted index with a bare `git reset` or `git stash`" | yes |

### Step T

1. No; no public CLI option, output format, or spec changes; `resolve_invocation_start` gains a keyword-only parameter with a backward-compatible default.
2. No; the plan touches runner environment construction, not commit, merge, worktree-isolation, or sandbox guards.
3. Moderately; six E-items in two task groups across five files sharing one root cause.
4. Yes; `- Scope-Paths:` names five files, no `.spec.md`.
5. Yes, moderately; a wrong gate could make a self-restart clear a live stop request or lose elapsed-time continuity, which other runner code depends on.

### Step R1

- Checked: every symbol cited in the plan. `runner_shared.restart_on_new_code_if_needed` sets `AW_DRIVER_RESTART` and `AW_INVOCATION_START_WALL`; `runner_shared.resolve_invocation_start` reads `AW_INVOCATION_START_WALL` first with no `AW_DRIVER_RESTART` check; `runner_shared.track_startup_timings` calls `resolve_invocation_start()`; `runner_shared.run_attended_turn` passes `att.child_env(extra_env)` (a plain `os.environ` copy); `agy_runipd.run_agy_turn` and `oc_runipd.run_opencode` call `pinned_child_env()` and pop other inherited keys but not these two; `agy_runipd.main` and `oc_runipd.main` call `runner_shared.resolve_invocation_start()`; `runner_stop.reset_deferred_request` exists; `conftest.py` pops the listed session keys and defines `_restore_home_sandbox`; `TestCwdBadgeAndOptionARunId.test_resolve_invocation_start_mono_preserves_script_start` calls `resolve_invocation_start_mono` with an explicit dict. Commits `a166b272c` and `b61073951` resolve. F-04 reproduced: `AW_DRIVER_RESTART=1 AW_INVOCATION_START_WALL=<now-300> python3 -m pytest tests/test_runner_resume_clears_stop.py -o addopts="" -p no:randomly -q --no-cov` gave `3 failed, 10 passed`, the same three tests.

### Step R2

- Checked: E/V bijection (now six to six), Scope-Paths against every edited file, dependencies (none external), concrete evidence in every V-item, and reachability. V-02 and V-03 demand observed runtime behavior: manual resume clearing is produced by `agy_runipd.main`/`oc_runipd.main` through `runner_shared.clear_stale_stop_request_on_manual_resume`, and the pytest-session observation is produced by the E-06 (d) probe. Execution contract present: scope fence without a stop clause, honesty rule, `aw commit z6wodh`, never push, conditional finalize ownership.

### Step R3

- Checked: the change removes two variables from child environments and narrows when one is trusted; no secrets, auth, or new inputs. Trust-boundary note: `AW_INVOCATION_START_WALL` is parsed with `float()` inside a `try`; unchanged. No finding.

### Step R4

- Checked: invariants. Self-restart must preserve `stop-request.json` and elapsed time (covered by regression (a) and by `tests/test_driver_restart.py` in E-05); manual resume must clear an older stop file (regression (a)); explicit-env callers of `resolve_invocation_start_mono` keep current behavior (default `require_restart_env=False`, `tests/test_statusline_behavior.py` in E-05). Reuses existing pop-before-spawn pattern in both drivers. The suite-cache exclusion is justified. Spec sync addressed in `PR-005`.

### Step S5

- Checked: the plan has no open questions; review-created questions were resolved from repository evidence and recorded as `D-1` to `D-3`, all reversible. No finding at or above `HIGH` is left open.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 | "read only when `AW_DRIVER_RESTART` is truthy when `require_restart_env=True`" | keyword-only parameter; when `True`, read only if `AW_DRIVER_RESTART` is non-empty | Double "when" was ambiguous |
| E-04 | "repeated `env_manual` comprehensions" | names both `env` and `env_manual` comprehensions by class | Incomplete identifier list |
| E-05 / V-05 | "pass with zero failures"; "N passed" from `aw check`/`aw sanitize` | no introduced failure or finding; agent result records | Unsatisfiable evidence demand |
| Spec / documentation sync | bare N/A | N/A citing spec `25kzda` rule | Substantiate the claim |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
