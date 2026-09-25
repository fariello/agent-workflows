# IPD: Make worktree isolation configurable per action type in repository policy

- Date: 2026-09-25
- Kind: child
- Concern: `aw oc run` / `aw agy run` isolation is one boolean (`--no-isolate-worktree`, dest `isolate_worktree`, frozen into run options) that governs BOTH execute turns and the review sweep lane, with no repository-policy default, so an operator on a disk-constrained host cannot keep isolation for execute turns (where commits need protecting) while dropping it for cheap review turns, and must retype the flag on every run.
- Scope: Add a `run.isolate_worktree` member to `.aw/config/project.json` taking per-action booleans (`execute`, `review`), resolve it once at queue build into frozen run options, and have the launch-site reads in `runner_shared` consult the per-action value; `--no-isolate-worktree` stays a shorthand that disables both. ALSO IN, added at review because the feature is unsafe without them: a route for a NON-ISOLATED review's output to reach the repository rather than being silently discarded (or a refusal of the `review: false` value), and a run-start warning whenever policy disables isolation for either action. Orchestrator retirement is NOT made configurable (see F-3). OUT: adding this key to the closed `RUN_POLICY_FLAGS` table, a per-action CLI flag, sparse or `--no-checkout` worktrees, and the separate `aw oc audit` isolation flag.
- Scope-Paths: agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_isolation_per_action.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- Set: isoperact
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: bzlxn0
- From-Backlog: h2mpru

## Workflow history
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-207, all FIXED, no deferrals; OQ-01 resolved from evidence and built as E-06, new non-blocking OQ-02 raised for the maintainer and escalated with `- Finding: F-6`. THE MATERIAL FINDING: `review: false` as authored would DISCARD the review's output, because the whole review-output path (`commit_review_lane_output` then `integrate_review_lane_branch`) is gated on `if is_review and wt_handle is not None:` and no lane means no handle, leaving the plan edit and review record uncommitted in the shared checkout - exactly the behavior executed plan `ajxr5d` removed after measuring it live, and reached by BYPASSING the existing fail-closed guard rather than tripping it. Added E-05 (land the output or refuse the value) and E-06 (run-start warning). Also: corrected E-04, whose `isolate` assignment feeds FOUR reads not two; corrected E-03, since `isolate_worktree` is not in `RUN_POLICY_FLAGS` so a generic namespace leaves it ABSENT and `args.isolate_worktree` raises, and named all four namespace states; corrected V-01, which asserted against `project_schema.py`, an unrelated module, instead of `config.CONFIG_SCHEMA`; verified the audit subparser is provably unaffected by parsing both; strengthened the CLI-flag deferral with the closed-table contract; and rewrote the gate with a scope fence, honesty rule and two stop conditions. E/V renumbered to E-01..E-08 / V-01..V-08.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog h2mpru; re-measured that only `options["isolate_worktree"]` exists (read in `runner_shared` for the review sweep session and the launch `isolate`), that no project-policy isolation key exists in `config.py`, and that orchestrator retirement already always uses `commit_lock.coordinator_worktree` independent of the flag.

## Goal

Let a repository set per-action isolation defaults (execute / review) in committed policy, defaulting both to isolated so behavior is unchanged, while keeping `--no-isolate-worktree` as the all-off override.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: policy reader

- [ ] E-01 In `agent_workflows/config.py`, beside `RUN_POLICY_KEY` / `read_run_policy` / `policy_retry_budget`, add `RUN_ISOLATE_MEMBER = "isolate_worktree"`, `ISOLATION_ACTIONS = ("execute", "review")`, and `policy_isolation(repo_root, *, warn=None) -> dict[str, bool]`. Shapes: `{"run": {"isolate_worktree": {"execute": true, "review": false}}}`; a bare bool under `run.isolate_worktree` applies to both actions. Missing actions default to `True`. Posture per that section's recorded rule ("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE"): a non-bool value or unknown action name falls back to `True` for that action and warns once. Never raises; not registered in `CONFIG_SCHEMA` (same documented reason as `review_findings_gate`).
  - Depends on: none
  - Expected outcome: `policy_isolation(tmp)` returns `{"execute": True, "review": True}` with no project.json.
  - PRECEDENT VERIFIED AT REVIEW: `read_run_policy` / `policy_retry_budget` read `run.<member>` from `.aw/config/project.json`, tolerate a bare top-level form, never raise, and warn-and-fall-back on a malformed value for the recorded reason that "a per-invocation mistake refuses; a shared-file mistake warns and continues". Confirmed too that `retry_budget`, `on_conflict` and `review_findings_gate` are all ABSENT from `config.CONFIG_SCHEMA` (11 keys, none of them `run.*` beyond `defaults.prune`), so not registering this key follows the established pattern rather than skipping a step. If E-05 takes its refusal route, `review: false` is additionally refused HERE with a warning and coerced to `True`.
  - Execution state: pending

### Task group 2: resolve and freeze

- [ ] E-02 Change the run-parser `--no-isolate-worktree` registrations in `oc_runipd.py` and `agy_runipd.py` (the `start.add_argument("--no-isolate-worktree", dest="isolate_worktree", action="store_false", default=True, ...)` blocks) to `default=None`, so "not supplied" is distinguishable, and update their help text to name the policy key. Do NOT touch the `audit` parser's `--isolate-worktree` `BooleanOptionalAction` in `runner_shared` (separate verb, separate flag). Audit every `getattr(args, "isolate_worktree", True)` read on the RUN namespace (`runner_shared` "\"isolate_worktree\": getattr(args, \"isolate_worktree\", True)") so `None` is never frozen as falsy.
  - Depends on: none
  - Expected outcome: `python3 -m agent_workflows oc run --help` still lists `--no-isolate-worktree` and mentions `run.isolate_worktree`.
  - THE AUDIT PARSER IS PROVABLY UNAFFECTED, so the plan's caution is correct and can be stated as a measurement rather than a hope: `start` and `audit` are separate subparsers with separate namespaces, verified by parsing both (`start abc123` -> `True`, `start --no-isolate-worktree` -> `False`, `audit abc123` -> `True`, `audit --no-isolate-worktree` -> `False`, the last because `BooleanOptionalAction` generates the `--no-` form itself). `resume` leaves the attribute ABSENT entirely, which is why E-03's fallback must treat absent and `None` alike. ALSO AUDIT `oc_runipd.audit`'s own `if getattr(args, "isolate_worktree", True):` read, which the authored item does not name: it runs on the AUDIT namespace and must keep its `True` default, so it must NOT be changed to a policy read in this plan.
  - Execution state: pending

- [ ] E-03 In `runner_shared.initialize_run_core`, where options are built, add `resolve_isolation(args, repo) -> dict[str, bool]`: if `args.isolate_worktree is False` both are False (CLI wins); else `config.policy_isolation(repo)`. Freeze `options["isolate_execute"]` and `options["isolate_review"]`, and keep writing `options["isolate_worktree"] = isolate_execute` so existing readers and stored fixtures (for example `tests/fixtures/run_summary/stranded-run-state.json`) keep their meaning. Add `isolation_for_action(options, action) -> bool` that reads the per-action key and falls back to `options.get("isolate_worktree", True)` so a run state frozen before this change resumes identically.
  - Depends on: E-01, E-02
  - Expected outcome: a new run with `{"run":{"isolate_worktree":{"review":false}}}` freezes `isolate_execute=True, isolate_review=False`.
  - FOUR NAMESPACE STATES, NOT TWO, and the authored `if args.isolate_worktree is False` test handles only one of them safely. Because `isolate_worktree` is NOT a member of `RUN_POLICY_FLAGS` (verified: the table's 16 flags do not include it), a generically built contract namespace leaves the attribute ABSENT, not `False`, so `args.isolate_worktree` would raise `AttributeError`; use `getattr(args, "isolate_worktree", None)`. The four states are: `False` (typed flag, CLI wins, both off), `None` (E-02's new default, defer to policy), ABSENT (defer to policy, same as `None`), and `True` (what every existing fixture namespace passes explicitly). DECIDE AND STATE what `True` means: treating it as an override would let those fixtures defeat a repository policy silently, while treating it as "not supplied" makes the flag unable to force isolation ON against a policy that disables it. Prefer "defer to policy", matching `freeze_run_policy_flags._supplied`'s recorded rule that a placeholder `bool` on a generically filled namespace "can only mean ... ABSENT", and note that no CLI form currently produces an explicit `True` since the only registered flag is `--no-isolate-worktree`. Do NOT add this key to `RUN_POLICY_FLAGS`: that table is the closed spec-2.1 flag list and registering a non-spec flag there is documented as failing the surface contract.
  - Execution state: pending

- [ ] E-04 Route the launch-site reads through `isolation_for_action`: the `review_uses_sweep_session = is_review and bool(state.get("options", {}).get("isolate_worktree", True))` line and the `isolate = state.get("options", {}).get("isolate_worktree", True)` line in the per-item launch function in `runner_shared`, passing `"review"` when `is_review` else `"execute"`. NOTE THE SECOND ASSIGNMENT FEEDS FOUR READS, NOT TWO, so the substitution must be made deliberately rather than by replacing one line: `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)`, `if is_review and isolate:` (the sweep lane), and TWO MORE at `if isolate:` inside `if self_finalize and not is_review:` (the `driver_begin(..., isolated=True)` choice and `allocate_isolation_worktree`). The three non-sweep reads are all reached only when `not is_review`, so binding `isolate = isolation_for_action(options, "review" if is_review else "execute")` preserves each one's meaning; VERIFY that by reading the enclosing guards rather than assuming it, because a future edit that removes a `not is_review` guard would silently hand an execute-only site the review value. Update the comment in `oc_runipd.py` near "`isolate_worktree` defaults True" if it now misstates the source.
  - Depends on: E-03
  - Expected outcome: with review isolation off, a review turn runs without acquiring the sweep lane while execute turns still get lanes; the three execute-only reads are unchanged in behavior.
  - Execution state: pending

- [ ] E-05 MAKE A NON-ISOLATED REVIEW STILL LAND ITS OUTPUT, which is the gap that otherwise makes `review: false` destructive rather than merely cheaper. MEASURED AT REVIEW: the entire review-output path is gated on `if is_review and wt_handle is not None:`, which calls `commit_review_lane_output` and then `integrate_review_lane_branch`. With review isolation off, `if is_review and isolate:` never allocates, `wt_handle` stays `None`, and that whole block is SKIPPED, so the review's two outputs (the plan edit and the review record) are left UNCOMMITTED in the shared checkout. That is precisely the pre-`ajxr5d` behavior executed plan `ajxr5d` removed after it was measured live on 2026-09-13: a review commit in main held five files, three of them sibling child plans still `queued` in the same run, and the files sat uncommitted for ~36 minutes while a concurrent run had items refused against them. Note the existing lane path FAILS CLOSED (an allocation failure sets `fail-lane` and never launches, so no turn silently falls back to the shared checkout); a policy switch would bypass that guard rather than trip it. SO: add a shared-checkout branch beside the lane branch that path-scopes a commit of exactly what `git status --porcelain` reports for the plan under review and its review record, reusing `commit_review_lane_output`'s discipline (never `git add -A`, hooks run normally with no `--no-verify`, a hook rejection reported as nothing-committed rather than a silent loss). If that branch cannot be written within this plan's declared Scope-Paths, then REFUSE the `review: false` policy value in E-01 instead, warning that review isolation cannot be disabled, and record which route was taken.
  - Depends on: E-04
  - Expected outcome: with `review: false`, a review's plan edit and review record are committed to the shared checkout (or the policy value is refused with a warning); in neither case is review output left uncommitted or discarded.
  - Execution state: pending

- [ ] E-06 ADD THE RUN-START WARNING FOR ANY POLICY THAT DISABLES ISOLATION, resolving OQ-01 as its own default already proposed and extending it to the review action for the reason E-05 measures. Print one line at run start naming the key and the action(s) it disabled, for example `run.isolate_worktree.execute=false` and `run.isolate_worktree.review=false`. This is the visibility half of the same argument the `config.py` run-policy section already records for `retry_budget` ("a silent fallback would override a repository that believes it set a policy with no signal anywhere"), applied in the opposite direction: a committed policy that disables a safety property is easier to forget than a typed flag, and `--no-isolate-worktree` at least appears in the operator's own scrollback. Emit nothing when both actions are isolated, so a default run's output is byte-identical.
  - Depends on: E-03
  - Expected outcome: a run with `{"run":{"isolate_worktree":{"review":false}}}` prints one warning naming `run.isolate_worktree.review=false`; a default run prints nothing new.
  - Execution state: pending

### Task group 3: tests and suite

- [ ] E-07 Add `tests/test_isolation_per_action.py`: (a) `policy_isolation` shapes (absent, bare bool, object, partial object, bad value warns); (b) `resolve_isolation` precedence over all FOUR namespace states, because `isolate_worktree` is NOT in `RUN_POLICY_FLAGS` and so a generically built namespace leaves it ABSENT rather than `False` (verified at review): CLI `False` beats policy `True`; `None` defers to policy; `True` (which every existing fixture namespace passes, e.g. `tests/test_hostdedup_third_host.py`, `tests/test_runner_active_conflict.py`, `tests/test_orchestrator_retirement.py`) must NOT be read as an override that defeats policy unless that is the deliberate choice, so assert whichever semantics E-03 implements and state it; ABSENT defers to policy. (c) `isolation_for_action` falls back to legacy `isolate_worktree` when per-action keys are absent, driven against the REAL stored fixture `tests/fixtures/run_summary/stranded-run-state.json` (which carries `"isolate_worktree": true` and no per-action key) rather than a hand-built dict, so the resume-compatibility claim is tested against a shape that actually exists on disk. (d) the launch-site wiring: a structural assertion that neither launch-site read in `runner_shared` still reads `options.get("isolate_worktree"` directly (grep the function source via `inspect.getsource`), which FAILS before E-04. (e) THE BEHAVIORAL CASE THAT MATTERS: with `review: false`, drive a review item and assert its two output files are COMMITTED (or that the policy value was refused per E-05's fallback route), never left uncommitted in the shared checkout. A structural grep alone cannot catch that regression, which is the one this plan can actually cause.
  - Depends on: E-05, E-06
  - Expected outcome: new module passes, with (e) failing if E-05's branch is removed.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest` (no added flags; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection, so do NOT pass `-n0`, a second `-q`, or `-p no:randomly`).
  - Depends on: E-07
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run policy lives under the `run` object in `.aw/config/project.json` (`config.RUN_POLICY_KEY = "run"`, spec 25kzda 5.5 path for `run.retry_budget`); precedence CLI > repository policy > default, frozen at queue build (`runner_shared.freeze_run_policy_flags` docstring: "resume use 'the original host, queue, and options'").
- Both hosts share one launch implementation in `runner_shared` (re-homed by `cnwy8g`), so the launch change is made once; only the parser registrations exist per host.
- `RUN_POLICY_FLAGS` is a CLOSED table asserted against spec `25kzda` 2.1, and `register_display_flags`'s docstring records that adding a non-spec flag to it fails the surface contract. `isolate_worktree` is not a member, so it must stay out, and a namespace built generically over that table leaves the attribute ABSENT rather than falsy.
- `freeze_run_policy_flags._supplied` records the rule for a generically filled namespace: a placeholder `bool` "can only mean ... ABSENT". Any new resolver reading a bool off `args` should follow it rather than inventing a fourth convention.
- `apply_run_policy_flags_on_resume` is the shipped precedent for `default=None`-means-absent: "a value of `None` means the flag was ABSENT, so the frozen value stands". E-02's change adopts exactly that convention for this flag.
- A review turn's OUTPUT reaches main only through `commit_review_lane_output` then `integrate_review_lane_branch`, both inside `if is_review and wt_handle is not None:`. Any change that can leave a review without a lane must supply another route for those two files or refuse; there is no third existing path.
- `aw oc audit` has its OWN `--isolate-worktree` (`BooleanOptionalAction`, `default=True`) on a separate subparser sharing the `isolate_worktree` dest name. Verified independent: changing the `start` default cannot affect it. It must not be re-pointed at the policy key by this plan.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | Not already built: one boolean, no per-action key, no policy default. | `grep -rn isolate_worktree agent_workflows/*.py`: parser dests in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py` (audit); frozen once as `"isolate_worktree": getattr(args, "isolate_worktree", True)`; read twice in `runner_shared`. `grep -n -i isolat agent_workflows/config.py` returns nothing. |
| F-2 | The one flag already governs two action types. | `runner_shared`: `review_uses_sweep_session = is_review and bool(...get("isolate_worktree", True))` and `if is_review and isolate:` -> `acquire_review_sweep_lane`; the same `isolate` drives execute lanes. |
| F-3 | "Orchestrate" is not governed by the flag at all. | Orchestrator retirement commits via `commit_lock.coordinator_worktree` inside `ipd_lifecycle` finalize unconditionally (dirtygates `u23gbn`, executed); no `isolate` check guards it. It is a short-lived coordinator-owned tree, not an agent turn, so a toggle adds nothing and risks re-opening the shared-checkout write the Set closed. |
| F-4 | Still wanted, at low priority. | Maintainer resolved dirtygates `8lfoum` OQ-01 to KEEP `--no-isolate-worktree` (escape hatch retained), so selective control remains meaningful; h2mpru's measured cost (0.31s / 46M per worktree here) confirms low urgency, not moot. |
| F-5 | THE `isolate` ASSIGNMENT FEEDS FOUR READS, NOT TWO, so E-04's "route the two launch-site reads" understates the edit. The three beyond the sweep lane are all reached only when `not is_review`, so the substitution is safe today, but that safety rests on guards the plan never states. | In the per-item launch function: `isolate = state.get("options", {}).get("isolate_worktree", True)`, then `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)` and two `if isolate:` reads, all three inside `if self_finalize and not is_review:`, plus `if is_review and isolate:` for the sweep lane |
| F-6 | TURNING REVIEW ISOLATION OFF DISCARDS THE REVIEW'S OUTPUT, which no item addressed and which makes `review: false` destructive rather than merely cheaper. The whole review-output path is gated on the lane handle, so with no lane the plan edit and the review record are left UNCOMMITTED in the shared checkout. | `if is_review and isolate:` is the only writer of `wt_handle` on the review path; the output block is `if is_review and wt_handle is not None:` -> `commit_review_lane_output(...)` then `integrate_review_lane_branch(...)`. With `isolate` false the first never runs, so `wt_handle` stays `None` and the second is skipped entirely |
| F-7 | That discarded-output state is EXACTLY the behavior executed plan `ajxr5d` removed after measuring it live, so `review: false` re-enables a closed defect by configuration. | `ajxr5d` Concern: "A review turn runs in the SHARED checkout with NO lane ... Measured live 2026-09-13: reviewing the orchestrator `8lfoum` produced commit `59cdc718` holding five files, three of them sibling child plans ... still `queued` in the same run ... uncommitted for the turn's duration (~36 minutes) ... a concurrent `runanalytics` execute run had its items refused against them. This is not a theoretical concurrency risk; it happened while the maintainer watched." Its E-02 record adds "FAIL-CLOSED: a review whose lane allocation fails is marked `blocked` and never falls back to the shared checkout, because that fallback is the behavior this plan removes and would be invisible" |
| F-8 | The existing lane path FAILS CLOSED on allocation failure, so a policy switch does not trip that guard, it BYPASSES it. This is why the risk is invisible rather than loud. | The sweep-lane `except Exception` sets `attempt["disposition"] = "fail-lane"`, `item["status"] = "fail-lane"`, emits `review-sweep-lane-alloc-failed`, prints "not launching" and `return`s. A false `isolate` never enters that `try` at all |
| F-9 | Spec `7ckptx` R5.4 keeps a NORMATIVE refusal for a shared-tree turn with dirty tracked paths, but a review never reaches the evaluation, so disabling review isolation puts a turn in the shared tree outside that obligation's reach. | R5.4: "SHARED TREE (`--no-isolate-worktree`): the turn MUST be REFUSED, and the refusal MUST name the dirty paths"; the only caller is `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)`, guarded by `if self_finalize and not is_review:`. The "reviews were exempt" phrase in the 2026-09-16 amendment note is a measured cost observation, not a normative carve-out |
| F-10 | `isolate_worktree` is NOT in `RUN_POLICY_FLAGS`, which has two consequences the plan does not account for: a generically built namespace leaves it ABSENT (so `args.isolate_worktree` raises), and the key must not be added to that table. | `[row.flag for row in RUN_POLICY_FLAGS]` returns 16 flags, none of them `--no-isolate-worktree`; `hasattr(Namespace(**{row.dest: False for row in RUN_POLICY_FLAGS}), "isolate_worktree")` is False; `register_display_flags`' docstring: "DELIBERATELY NOT IN `RUN_POLICY_FLAGS`: that table is the closed flag list spec `25kzda` 2.1 declares" |

## Proposed changes (ordered, validatable)

1. Policy reader (E-01).
2. Distinguish unsupplied CLI flag (E-02), resolve and freeze per-action values with legacy fallback over all four namespace states (E-03).
3. Launch sites consult per-action value, all four reads accounted for (E-04).
4. Make a non-isolated review still land its output, or refuse the policy value (E-05) - the item without which `review: false` re-enables the defect `ajxr5d` closed.
5. Warn at run start whenever policy disables isolation (E-06).
6. Tests including the behavioral review-output case (E-07), suite (E-08).

## Deferred / out of scope (with reason)

- Per-action toggle for orchestrator retirement (F-3).
  - Carrier-Declined: retirement is not agent-executed and already always uses a throwaway coordinator worktree; making it optional only re-enables shared-checkout writes.
- Sparse-checkout or `--no-checkout` worktrees for very large repositories (h2mpru suggested-shape item 4).
  - Carrier-Declined: h2mpru records the undeclared-path read risk as unresolved and the measured cost here is negligible; re-file when a large or disk-constrained repository is an actual case.
- A per-action CLI flag (e.g. `--no-isolate-review`).
  - Carrier-Declined: h2mpru asks for configuration so operators need not retype flags; the policy key covers it, and the reason not to widen the flag surface is STRONGER than the authored "no demonstrated need": `RUN_POLICY_FLAGS` is a CLOSED table asserted against spec `25kzda` 2.1, and `register_display_flags`'s docstring records that registering a non-spec flag there fails the surface contract. So a new CLI flag would either fail that contract or require a spec amendment this plan does not declare.
- Making the `aw oc audit` turn read the policy key (it has its own `--isolate-worktree` on a separate subparser sharing the dest name).
  - Carrier-Declined: verified independent at review, so leaving it alone is safe rather than merely untidy; unifying the two is its own decision about whether an audit is an "action type" in this vocabulary at all.

## Scope check

- Over-scope: none.
- Under-scope: CLOSED BY E-05 AND E-06, which the authored plan lacked. `review: false` as originally specified would have left a review's plan edit and review record uncommitted in the shared checkout (F-6), re-enabling the defect executed plan `ajxr5d` measured live and removed (F-7), and it would have done so SILENTLY because the existing fail-closed guard is bypassed rather than tripped (F-8). A configuration surface that can turn a safety property off must land the output another way or refuse the value, and must say so at run start. `aw oc audit` keeps its own `--isolate-worktree` and does not read the policy key; that remains a separate choice (now recorded under Deferred).

## Required tests / validation

New `tests/test_isolation_per_action.py`, including the structural test shown failing before E-04 AND the behavioral review-output case from E-07(e), which is the only test that can catch the F-6 regression; the resume-compatibility case driven against the real `tests/fixtures/run_summary/stranded-run-state.json`; existing `tests/test_oc_runipd.py` isolation tests (`test_isolated_prompt_states_the_lane_requirement`, `test_non_isolated_prompt_is_unchanged_by_the_lane_feature`) must still pass; bare suite. Note that many existing fixtures set `"isolate_worktree"` alone with no per-action key (for example `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_reaskscore_composed.py`, `tests/test_defect_report.py`), so the legacy fallback is load-bearing for the existing suite and not only for stored run state.

## Spec / documentation sync

No `.spec.md` names `isolate_worktree` defaults as a contract beyond the flag, which survives unchanged, and no `.spec.md` appears in `- Scope-Paths:` so the runners will announce no declared spec edit. BUT ONE SPEC INTERACTION MUST BE STATED RATHER THAN CALLED N/A (F-9): spec `7ckptx` R5.4 keeps a NORMATIVE refusal for a shared-tree turn with dirty tracked paths, and its only caller is guarded by `not is_review`, so a review running in the shared tree sits outside that obligation's reach. This plan does not amend R5.4 and does not need to, because E-05 keeps the review's output accounted for and E-06 makes the posture visible; but an executor must not read "N/A for specs" as "no containment contract is nearby". If a future item wants R5.4's refusal to cover a non-isolated review, that is a spec amendment and a different plan. The AGENTS.md runner paragraph ("opt out with `--no-isolate-worktree`") remains true; no edit required.

## Open questions

### OQ-01: Should a policy that disables isolation print a run-start warning?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: RESOLVED AT REVIEW AS YES, for BOTH actions, and built as E-06. The question's own default was already yes for `execute`; review evidence extends it to `review` and removes the need to ask. The deciding facts are in-repo rather than a matter of taste: `config.py`'s run-policy section already records the principle for exactly this situation ("a silent fallback would override a repository that believes it set a policy with no signal anywhere"), and F-8 measures that a policy disabling isolation BYPASSES the existing fail-closed guard instead of tripping it, so nothing else in the run would say anything. A committed, shared policy is also harder to notice than a typed flag, which at least appears in the operator's own scrollback. Scope of the warning is deliberately narrow: one line naming the key and the disabled action(s), and nothing at all when both are isolated, so a default run's output is byte-identical.

### OQ-02: Is `review: false` a policy value this repository should offer at all?

- Blocking: no
- Status: open
- Owner: maintainer
- Finding: F-6
- Resolution or deferral rationale: RAISED AT REVIEW. E-05 makes the value SAFE either way (it lands the review output in the shared checkout, or it refuses the value with a warning), so this question does not block execution: whichever route E-05 takes, no review output is lost. What remains is a judgement only the maintainer can make, because it is about appetite rather than mechanism. Offering `review: false` re-admits a review turn to the shared checkout, and executed plan `ajxr5d` removed that after measuring it live on 2026-09-13 (a review commit in main holding five files, three of them sibling child plans still `queued` in the same run; files uncommitted for ~36 minutes; a concurrent run's items refused against them). E-05's shared-checkout commit addresses the LOST-OUTPUT half of that incident but NOT the mid-run-dirty-tree half, and F-9 notes spec `7ckptx` R5.4's shared-tree refusal does not reach a review turn. Against that, `h2mpru`'s motivation is real but narrow: disk is linear in parallelism (1.5G per worktree on a 1.5GB repository), while this repository measures 46M and 0.31s. So the honest options are (a) ship `review: false` with E-05's commit path and accept a dirty shared tree during review turns, (b) accept `execute` per-action control only and have E-01 refuse `review: false` with a warning, which still satisfies h2mpru's disk motivation for the expensive action type since execute lanes are the parallel ones, or (c) defer the whole plan until a disk-constrained repository is an actual case, which `h2mpru` itself says is not the current situation. Default if unanswered: (b), the conservative route, because it keeps a closed defect closed and still delivers the configuration surface the backlog item asked for.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import tempfile; from agent_workflows import config; print(config.policy_isolation(tempfile.mkdtemp()))"` printing `{'execute': True, 'review': True}`, plus the malformed-value case showing the warning text naming the key and the bad value. Assert the schema claim against the RIGHT file: paste `python3 -c "from agent_workflows import config; print([k for k in config.CONFIG_SCHEMA if 'isolat' in k])"` returning `[]`. The authored `grep -c isolate agent_workflows/project_schema.py` is a check on an UNRELATED module (that file governs placements and presets and contains no `run.*` key at all; the schema this key is deliberately absent from is `config.CONFIG_SCHEMA`), so it would pass no matter what E-01 did.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m agent_workflows oc run --help | grep -A3 no-isolate-worktree` and the same for `agy run`, both mentioning `run.isolate_worktree`; `git diff -- agent_workflows/runner_shared.py | grep -c BooleanOptionalAction` = 0 (audit flag untouched). ALSO paste the four parsed namespaces proving the audit subparser is unaffected and that absent-versus-None is distinguishable: `start <id6>` (expect `None` after this change), `start <id6> --no-isolate-worktree` (`False`), `audit <id6>` (`True`), `audit <id6> --no-isolate-worktree` (`False`), and `resume <run>` (attribute ABSENT). Measured at review before the change: `True/False/True/False/ABSENT`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing output of the E-07 precedence and legacy-fallback tests by name (`python3 -m pytest -o addopts="" -q tests/test_isolation_per_action.py -k "precedence or legacy"`), showing a case for EACH of the four namespace states (`False`, `None`, ABSENT, `True`) and stating in the item what `True` was implemented to mean. Also paste the `stranded-run-state.json`-driven fallback case, since that is a real on-disk shape rather than a constructed dict.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n 'get("isolate_worktree"' agent_workflows/runner_shared.py` showing only the fallback inside `isolation_for_action` (and the options writer), plus the structural test from E-07(d) FAILING when run before E-04 is applied and passing after. ALSO paste `grep -n '\bisolate\b' agent_workflows/runner_shared.py` for the launch function with each of the FOUR reads annotated by its enclosing guard, so the claim that three of them are execute-only is shown rather than assumed (measured at review: `shared_tree=not isolate`, two `if isolate:` inside `if self_finalize and not is_review:`, and `if is_review and isolate:`).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: THE ONE VALIDATION THAT DISCRIMINATES. With `{"run":{"isolate_worktree":{"review":false}}}`, drive a review item and paste the resulting `git status --porcelain` for the shared checkout plus the commit that carries the plan edit and the review record; OR, if E-05 took the refusal route, paste the warning and `policy_isolation` returning `review: True`. In EITHER case also paste the negative control: the same run with E-05's branch removed, showing the two files left UNCOMMITTED, which is the F-6 regression. A pass without that control cannot distinguish "the output landed" from "the test never checked".
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the run-start output for a policy disabling `review` (one line naming `run.isolate_worktree.review=false`), for one disabling `execute`, and for a DEFAULT run showing no new line at all. The last is what proves the warning is scoped and did not become noise on every run.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_isolation_per_action.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` summary line, 0 failed. The two host driver files are included deliberately: both carry state fixtures writing `isolate_worktree` alone with no per-action key, so they are the existing suite's exercise of E-03's legacy fallback.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `N passed` and 0 failed, plus the pre-change baseline count as `<before> -> <after>` so a pre-existing failure is not read as caused by this change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval.

WHAT A HUMAN IS APPROVING, AND THE ONE THING TO DECIDE FIRST. A new `run.isolate_worktree` policy member with per-action booleans, resolved and frozen at queue build, consulted at the launch sites, plus a run-start warning and one new test module. Behavior with no policy and no flag is unchanged by construction (both actions default isolated). THE PART THAT NEEDS A HUMAN JUDGEMENT IS `review: false`, raised as OQ-02: it re-admits a review turn to the shared checkout, which executed plan `ajxr5d` removed after measuring it live on 2026-09-13 (a review commit in main holding five files, three of them sibling child plans still `queued` in the same run; uncommitted for ~36 minutes; a concurrent run's items refused against them). E-05 makes the value safe either way (land the output, or refuse the value), so execution is not blocked; what the maintainer is choosing is whether the option should exist. OQ-02 records the three options and defaults to the conservative one.

WHY `execute: false` IS THE LESS ALARMING HALF, stated so the two are not judged together: the shared-tree execute path already exists and is already reachable by `--no-isolate-worktree`, spec `7ckptx` R5.4 keeps its dirty-tracked-path REFUSAL in force for it, and `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)` is that refusal's live caller. A review turn reaches none of that (F-9), which is the asymmetry that makes the review half the one worth pausing on.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `agent_workflows/config.py`, only the new `RUN_ISOLATE_MEMBER` / `ISOLATION_ACTIONS` / `policy_isolation` additions beside the existing run-policy accessors. In `agent_workflows/runner_shared.py`, `resolve_isolation`, `isolation_for_action`, the options freeze, the launch-site binding, E-05's review-output branch, and E-06's warning. In `oc_runipd.py` and `agy_runipd.py`, ONLY the `start` parser's `--no-isolate-worktree` default and help text. `tests/test_isolation_per_action.py` is new. Expected to need NO edit: `RUN_POLICY_FLAGS` (a closed spec-asserted table this key must stay out of), the `audit` subparser's own `--isolate-worktree` and `oc_runipd.audit`'s `getattr(args, "isolate_worktree", True)` read, `agent_workflows/project_schema.py`, `config.CONFIG_SCHEMA`, and every existing test fixture writing `isolate_worktree` alone. No `.spec.md`, backlog, or release record is edited. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be. V-05's NEGATIVE CONTROL, because a passing review-output test cannot be distinguished from a test that never checked unless the same test is shown failing with E-05's branch removed. V-01's schema assertion, because the authored `grep -c isolate agent_workflows/project_schema.py` interrogates an unrelated module and would pass regardless. And V-06's DEFAULT-run line, because a warning that fires on every run is noise, and only the silent case proves it is scoped.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if E-05 can neither commit a non-isolated review's output within the declared Scope-Paths nor refuse the policy value, stop and report, because shipping `review: false` without one of those two routes silently discards review output. If routing the launch-site binding changes the behavior of any of the three execute-only `isolate` reads (F-5), stop and report, since that would hand an execute turn a review policy value.

Commit ONLY the Scope-Paths via `aw commit bzlxn0 -- <Scope-Paths>`, never `git add -A`, never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. On execution, close backlog `h2mpru` with `--evidence` citing the executed plan; it carries no `- Blocks-Release:`, so no gate is handed off.
