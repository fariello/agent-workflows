# IPD: Make worktree isolation configurable per action type in repository policy

- Date: 2026-09-25
- Kind: child
- Concern: `aw oc run` / `aw agy run` isolation is one boolean (`--no-isolate-worktree`, dest `isolate_worktree`, frozen into run options) that governs BOTH execute turns and the review sweep lane, with no repository-policy default, so an operator on a disk-constrained host cannot keep isolation for execute turns (where commits need protecting) while dropping it for cheap review turns, and must retype the flag on every run.
- Scope: Add a `run.isolate_worktree` member to `.aw/config/project.json` taking per-action booleans (`execute`, `review`), resolve it once at queue build into frozen run options, and have the two launch-site reads in `runner_shared` consult the per-action value; `--no-isolate-worktree` stays a shorthand that disables both. Orchestrator retirement is NOT made configurable (see F-3).
- Scope-Paths: agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_isolation_per_action.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- Set: isoperact
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: bzlxn0
- From-Backlog: h2mpru

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog h2mpru; re-measured that only `options["isolate_worktree"]` exists (read in `runner_shared` for the review sweep session and the launch `isolate`), that no project-policy isolation key exists in `config.py`, and that orchestrator retirement already always uses `commit_lock.coordinator_worktree` independent of the flag.

## Goal

Let a repository set per-action isolation defaults (execute / review) in committed policy, defaulting both to isolated so behavior is unchanged, while keeping `--no-isolate-worktree` as the all-off override.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: policy reader

- [ ] E-01 In `agent_workflows/config.py`, beside `RUN_POLICY_KEY` / `read_run_policy` / `policy_retry_budget`, add `RUN_ISOLATE_MEMBER = "isolate_worktree"`, `ISOLATION_ACTIONS = ("execute", "review")`, and `policy_isolation(repo_root, *, warn=None) -> dict[str, bool]`. Shapes: `{"run": {"isolate_worktree": {"execute": true, "review": false}}}`; a bare bool under `run.isolate_worktree` applies to both actions. Missing actions default to `True`. Posture per that section's recorded rule ("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE"): a non-bool value or unknown action name falls back to `True` for that action and warns once. Never raises; not registered in `CONFIG_SCHEMA` (same documented reason as `review_findings_gate`).
  - Depends on: none
  - Expected outcome: `policy_isolation(tmp)` returns `{"execute": True, "review": True}` with no project.json.
  - Execution state: pending

### Task group 2: resolve and freeze

- [ ] E-02 Change the run-parser `--no-isolate-worktree` registrations in `oc_runipd.py` and `agy_runipd.py` (the `start.add_argument("--no-isolate-worktree", dest="isolate_worktree", action="store_false", default=True, ...)` blocks) to `default=None`, so "not supplied" is distinguishable, and update their help text to name the policy key. Do NOT touch the `audit` parser's `--isolate-worktree` `BooleanOptionalAction` in `runner_shared` (separate verb, separate flag). Audit every `getattr(args, "isolate_worktree", True)` read on the RUN namespace (`runner_shared` "\"isolate_worktree\": getattr(args, \"isolate_worktree\", True)") so `None` is never frozen as falsy.
  - Depends on: none
  - Expected outcome: `python3 -m agent_workflows oc run --help` still lists `--no-isolate-worktree` and mentions `run.isolate_worktree`.
  - Execution state: pending

- [ ] E-03 In `runner_shared.initialize_run_core`, where options are built, add `resolve_isolation(args, repo) -> dict[str, bool]`: if `args.isolate_worktree is False` both are False (CLI wins); else `config.policy_isolation(repo)`. Freeze `options["isolate_execute"]` and `options["isolate_review"]`, and keep writing `options["isolate_worktree"] = isolate_execute` so existing readers and stored fixtures (for example `tests/fixtures/run_summary/stranded-run-state.json`) keep their meaning. Add `isolation_for_action(options, action) -> bool` that reads the per-action key and falls back to `options.get("isolate_worktree", True)` so a run state frozen before this change resumes identically.
  - Depends on: E-01, E-02
  - Expected outcome: a new run with `{"run":{"isolate_worktree":{"review":false}}}` freezes `isolate_execute=True, isolate_review=False`.
  - Execution state: pending

- [ ] E-04 Route the two launch-site reads through `isolation_for_action`: the `review_uses_sweep_session = is_review and bool(state.get("options", {}).get("isolate_worktree", True))` line and the `isolate = state.get("options", {}).get("isolate_worktree", True)` line in the per-item launch function in `runner_shared`, passing `"review"` when `is_review` else `"execute"`. The `evaluate_clean_base_for_launch(repo, shared_tree=not isolate)` call then naturally uses the execute value, and `if is_review and isolate:` uses the review value. Update the comment in `oc_runipd.py` near "`isolate_worktree` defaults True" if it now misstates the source.
  - Depends on: E-03
  - Expected outcome: with review isolation off, a review turn runs without acquiring the sweep lane while execute turns still get lanes.
  - Execution state: pending

### Task group 3: tests and suite

- [ ] E-05 Add `tests/test_isolation_per_action.py`: (a) `policy_isolation` shapes (absent, bare bool, object, partial object, bad value warns); (b) `resolve_isolation` precedence: CLI `False` beats policy `True`; `None` defers to policy; (c) `isolation_for_action` falls back to legacy `isolate_worktree` when per-action keys are absent (resume of an old state); (d) the launch-site wiring: a structural assertion that neither launch-site read in `runner_shared` still reads `options.get("isolate_worktree"` directly (grep the function source via `inspect.getsource`), which FAILS before E-04.
  - Depends on: E-04
  - Expected outcome: new module passes.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run policy lives under the `run` object in `.aw/config/project.json` (`config.RUN_POLICY_KEY = "run"`, spec 25kzda 5.5 path for `run.retry_budget`); precedence CLI > repository policy > default, frozen at queue build (`runner_shared.freeze_run_policy_flags` docstring: "resume use 'the original host, queue, and options'").
- Both hosts share one launch implementation in `runner_shared` (re-homed by `cnwy8g`), so the launch change is made once; only the parser registrations exist per host.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-1 | Not already built: one boolean, no per-action key, no policy default. | `grep -rn isolate_worktree agent_workflows/*.py`: parser dests in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py` (audit); frozen once as `"isolate_worktree": getattr(args, "isolate_worktree", True)`; read twice in `runner_shared`. `grep -n -i isolat agent_workflows/config.py` returns nothing. |
| F-2 | The one flag already governs two action types. | `runner_shared`: `review_uses_sweep_session = is_review and bool(...get("isolate_worktree", True))` and `if is_review and isolate:` -> `acquire_review_sweep_lane`; the same `isolate` drives execute lanes. |
| F-3 | "Orchestrate" is not governed by the flag at all. | Orchestrator retirement commits via `commit_lock.coordinator_worktree` inside `ipd_lifecycle` finalize unconditionally (dirtygates `u23gbn`, executed); no `isolate` check guards it. It is a short-lived coordinator-owned tree, not an agent turn, so a toggle adds nothing and risks re-opening the shared-checkout write the Set closed. |
| F-4 | Still wanted, at low priority. | Maintainer resolved dirtygates `8lfoum` OQ-01 to KEEP `--no-isolate-worktree` (escape hatch retained), so selective control remains meaningful; h2mpru's measured cost (0.31s / 46M per worktree here) confirms low urgency, not moot. |

## Proposed changes (ordered, validatable)

1. Policy reader (E-01).
2. Distinguish unsupplied CLI flag (E-02), resolve and freeze per-action values with legacy fallback (E-03).
3. Launch sites consult per-action value (E-04).
4. Tests (E-05), suite (E-06).

## Deferred / out of scope (with reason)

- Per-action toggle for orchestrator retirement (F-3).
  - Carrier-Declined: retirement is not agent-executed and already always uses a throwaway coordinator worktree; making it optional only re-enables shared-checkout writes.
- Sparse-checkout or `--no-checkout` worktrees for very large repositories (h2mpru suggested-shape item 4).
  - Carrier-Declined: h2mpru records the undeclared-path read risk as unresolved and the measured cost here is negligible; re-file when a large or disk-constrained repository is an actual case.
- A per-action CLI flag (e.g. `--no-isolate-review`).
  - Carrier-Declined: h2mpru asks for configuration so operators need not retype flags; the policy key covers it and adding flags widens the frozen `RUN_POLICY_FLAGS` contract for no demonstrated need.

## Scope check

- Over-scope: none.
- Under-scope: `aw oc audit` keeps its own `--isolate-worktree` and does not read the policy key; unifying it is a separate choice.

## Required tests / validation

New `tests/test_isolation_per_action.py`, including a structural test shown failing before E-04; existing `tests/test_oc_runipd.py` isolation tests (`test_isolated_prompt_states_the_lane_requirement`, `test_non_isolated_prompt_is_unchanged_by_the_lane_feature`) must still pass; bare suite.

## Spec / documentation sync

N/A for specs: no `.spec.md` names `isolate_worktree` defaults as a contract beyond the flag, which survives unchanged. The AGENTS.md runner paragraph ("opt out with `--no-isolate-worktree`") remains true; no edit required.

## Open questions

### OQ-01: Should a policy that disables execute isolation print a run-start warning?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: yes, one line at run start naming `run.isolate_worktree.execute=false`, because dirtygates `8lfoum` OQ-01 records the non-isolated path as the one remaining route to mid-run shared-checkout writes, and a committed policy is easier to forget than a typed flag.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import tempfile; from agent_workflows import config; print(config.policy_isolation(tempfile.mkdtemp()))"` printing `{'execute': True, 'review': True}`; `grep -c isolate agent_workflows/project_schema.py` unchanged from before.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m agent_workflows oc run --help | grep -A3 no-isolate-worktree` and the same for `agy run`, both mentioning `run.isolate_worktree`; `git diff -- agent_workflows/runner_shared.py | grep -c BooleanOptionalAction` = 0 (audit flag untouched).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing output of the E-05 precedence and legacy-fallback tests by name (`python3 -m pytest -o addopts="" -q tests/test_isolation_per_action.py -k "precedence or legacy"`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n 'get("isolate_worktree"' agent_workflows/runner_shared.py` showing only the fallback inside `isolation_for_action` (and the options writer), plus the structural test from E-05(d) FAILING when run before E-04 is applied and passing after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_isolation_per_action.py tests/test_oc_runipd.py` summary line, 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit through `aw commit <plan> -- <Scope-Paths>`, never push. After every V-* item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` via `aw ipd finalize`.
