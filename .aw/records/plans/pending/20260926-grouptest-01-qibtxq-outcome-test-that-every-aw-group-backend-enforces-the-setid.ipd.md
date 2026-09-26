# IPD: Outcome test that every aw group backend enforces the setid length policy

- Date: 2026-09-26
- Kind: child
- Concern: `aw group` routes per type (`artifact_types.TYPE_BACKENDS`: plans -> `plans_refs.run_set_assign`, research -> `research_refs.run_set_assign`, everything else -> `artifact_rename.run_group_*` -> `run_group_generic`). The setid-length guard was added to all three backends by plan x75obw, but NO test covers it: `tests/test_artifact_group.py` was deleted in commit `19313eed` (test trim). The next verb-wide policy, or a regression that drops the guard from one backend, would go undetected, which is exactly how the original defect (guard on the generic backend only) happened.
- Scope: IN: one new outcome test file `tests/test_group_verb_policy.py`, parametrized over every type in `artifact_types.TYPE_BACKENDS` that has a `group` verb, asserting the refusal (over 24 chars) and the warning (15 to 24 chars). OUT: any production code change (the guards exist and work, measured); a shared pre-dispatch validation seam (the backlog's other suggested direction; a refactor this plan does not need); restoring the deleted `test_artifact_group.py`.
- Scope-Paths: tests/test_group_verb_policy.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 8gwpjy
- Blocks-Release: next
- Set: grouptest
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: qibtxq

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 8gwpjy: Registry-driven outcome test that every aw group backend enforces the setid length policy.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A regression test that fails if ANY `aw group` backend stops enforcing the setid-length policy, and that covers a newly registered type automatically because it iterates the routing registry rather than a hand-written list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm current behavior

- [ ] E-01 Confirm the guard fires on every backend at HEAD: in a temp `git init` dir, for each type `t` in `[t for t, v in artifact_types.TYPE_BACKENDS.items() if "group" in v]`, run `aw group $t zzzzzz --set abcdefghijklmnopqrstuvwxyz` (26 chars) and `aw group $t zzzzzz --set abcdefghijklmnop` (16 chars) and record rc and output.
  - Depends on: none
  - Expected outcome (measured at authoring for all 9 types: plans, research, specs, prompts, backlog, walkthroughs, roadmaps, releases, other): the 26-char case exits 2 with `error: aw group <t>: --set 'abc...z' is 26 characters, over the 24-character maximum`; the 16-char case prints `note: aw group <t>: --set 'abcdefghijklmnop' is 16 characters; a setid of <= 14 characters is strongly preferred` and then fails on the unmatched selector (`error: no ... zzzzzz`), exit 2. If any type does not, stop and report: that is a live bug, not a missing test.
  - Execution state: pending

### Task group 2: The test file

- [ ] E-02 Create `tests/test_group_verb_policy.py`. Build the type list from the registry: `GROUP_TYPES = sorted(t for t, verbs in artifact_types.TYPE_BACKENDS.items() if "group" in verbs)`, plus a sanity assertion that it is non-empty and contains `plans` and `research` (so an accidental empty parametrization cannot pass vacuously). For each type, in a temp git repo, run the real CLI (`tests.support.run_cli("group", t, "zzzzzz", "--set", <setid>, "--dir", <tmp>)`, or in-process `cli.main` with captured stdout if subprocess cost is excessive; justify the choice in evidence) and assert:
    (a) REFUSAL: a 25-character setid (the smallest refused length, so the boundary is covered) exits `2` and the output contains `is 25 characters` and `24-character maximum` (so the refusal is the length guard, not the unmatched-selector error);
    (b) WARNING: a 15-character setid (smallest warned length) prints a line containing `is 15 characters` and `strongly preferred`, and does NOT contain `maximum for a setid` (not refused by the guard). The command still exits 2 because the selector matches nothing; assert the warning, not the rc, and say so in a comment, since the warning must be emitted before resolution fails.
    Use `pytest.mark.parametrize` (or `subTest`) keyed by type name so a failure names the backend's type.
  - Depends on: E-01
  - Expected outcome: 2 assertions x 9 types all pass at HEAD.
  - Execution state: pending
- [ ] E-03 Prove each assertion bites per backend WITHOUT committing a mutation and without touching the shared checkout: create a throwaway worktree `git worktree add --detach /tmp/opencode/qibtxq-mut HEAD`, copy the new test file into it, and for EACH of the three backends in turn (a) `plans_refs.run_set_assign`, (b) `research_refs.run_set_assign`, (c) `artifact_rename.run_group_generic`, disable only that backend's `validate_setid_length_for_authoring` call (replace its result with `(None, None)`), run `python3 -m pytest -o addopts="" -q tests/test_group_verb_policy.py` inside the worktree (its `tests/support.py` pins `PYTHONPATH` to the worktree root), record which parametrized cases fail, then restore the backend with `git -C /tmp/opencode/qibtxq-mut checkout -- <file>` before the next. Finally `git worktree remove --force /tmp/opencode/qibtxq-mut`.
  - Depends on: E-02
  - Expected outcome: mutating (a) fails exactly the `plans` refusal and warning cases; (b) exactly the `research` cases; (c) the refusal and warning cases for all seven generic types (specs, prompts, backlog, walkthroughs, roadmaps, releases, other). No other case fails in each run.
  - Execution state: pending

### Task group 3: Full suite

- [ ] E-04 Run the bare suite `python3 -m pytest` in the real checkout and confirm the worktree from E-03 is gone (`git worktree list`).
  - Depends on: E-03
  - Expected outcome: suite green; no leftover worktree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Setid policy: `config.SETID_WARN_LENGTH_DEFAULT = 14`, `config.SETID_MAX_LENGTH_DEFAULT = 24`; one validator `config.validate_setid_length_for_authoring` returns `(error, warning)` (AGENTS.md; plans README "KEEP A SETID SHORT").
- Tests run the CLI through `tests.support.run_cli`, pinned to the tree by `PYTHONPATH`.
- The shared checkout must not be used for mutation experiments; a detached throwaway worktree under `/tmp/opencode` keeps the mutation out of everyone else's tree.
- Commits via `aw commit qibtxq -- tests/test_group_verb_policy.py`; suite run bare.

## Findings

| # | Evidence (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `artifact_types.TYPE_BACKENDS` (~:74-118): plans `"group": "plans_refs.run_set_assign"`, research `"group": "research_refs.run_set_assign"`, seven others `"group": "artifact_rename.run_group_<type>"` | Routing confirmed; 9 types have a `group` verb. |
| F-2 | `artifact_rename.run_group_generic` "setidlen x75obw E-06 (catalog I-17): the ONE shared setid-length guard" (~:830-845); `plans_refs.run_set_assign` (~:450-470); `research_refs.run_set_assign` (~:310-330) | Guard present on all three backends, as the brief says. |
| F-3 | `git show --stat 19313eed` lists `tests/test_artifact_group.py | 270 --` | Deleted; `git grep validate_setid_length_for_authoring tests/` hits only `tests/test_config.py` and `tests/test_check_engine.py`, neither of which drives `aw group`. No `aw group` coverage exists. Confirmed. |
| F-4 | measured (E-01 shape) | All 9 types refuse 26 chars with rc 2 and warn at 16 chars. The warn case also exits 2 (selector `zzzzzz` unmatched), so the test must assert the warning text, not rc 0; the brief's "15-24 chars warns" is correct but does not imply success exit. |
| F-5 | `aw group --help` lists `comms` as a type | `comms` is not in `TYPE_BACKENDS`, so it has no `group` backend; iterating the registry correctly excludes it. |

## Proposed changes (ordered, validatable)

1. E-01 confirm behavior.
2. E-02 the registry-driven test.
3. E-03 per-backend mutation proof in a throwaway worktree.
4. E-04 suite.

## Deferred / out of scope (with reason)

- A single pre-dispatch validation seam for `aw group`: a refactor the backlog offered as an alternative; the test is the cheaper option the backlog itself recommends and closes the detection gap.
  - Carrier-Declined: not needed; the parametrized test covers every current and future backend through the registry, so no refactor is outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

The maintainer's standing rule is to test OUTCOMES only: the test drives the real `aw group` command and asserts its exit status and emitted message, never the guard's source or its presence in a file. One test file, two assertions per type, parametrized from the registry so a new type is covered with no edit. E-03 proves each assertion is load-bearing per backend.

## Spec / documentation sync

N/A: test-only; no spec or doc changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste, for all 9 types, rc and the first output line of the 26-char and 16-char runs (expected: rc 2 plus the length error; the `note:` warning line).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_group_verb_policy.py` output listing every parametrized case by type name (18 cases plus the sanity check) as PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: for each of the three mutations, paste the diff applied in the worktree and the pytest output showing exactly which cases FAILED (plans only; research only; the seven generic types only), then `git worktree list` showing the throwaway worktree removed.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures) and `git status --short tests/` showing only the new file as this plan's change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: one new test file; no production code. The bug being closed is the missing detection (8gwpjy), not a live guard failure (all 9 backends measured enforcing at authoring).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `tests/test_group_verb_policy.py` only. The E-03 mutations happen in a throwaway worktree and are never committed; the shared checkout's `plans_refs.py`, `research_refs.py`, `artifact_rename.py` must not be edited. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. Genuine stop condition: E-01 shows a backend NOT enforcing the policy (live bug; report before writing a test that would fail).

HONESTY RULE (hard MUST): paste the ACTUAL runner output; V-03 failures must be real runs.

Commit ONLY `tests/test_group_verb_policy.py` through `aw commit qibtxq -- tests/test_group_verb_policy.py`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize qibtxq --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from backlog `8gwpjy`; then set that item `done` with `--evidence` citing the executed plan.
