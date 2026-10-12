# IPD: Add a worktree-isolated mutation probe that reports whether a test selection kills a named mutant

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to MUTATION-PROVE surviving coverage, and `GUIDING_PRINCIPLES.md` Section 16 names mutation as the validity test for a test ("A test is only valid if breaking the underlying behavior makes the test fail"). The repo has no mutation tool: `mutmut` is not installed (`python3 -c "import mutmut"` -> `ModuleNotFoundError` at authoring) and no `tools/` script mutates code. Plan `oyh28b` mutated in memory with a `pytest -p` plugin; that cannot reach behavior exercised through a SUBPROCESS (`aw ...` CLI invocations a large share of the suite uses), where an in-memory patch is invisible, so a CLI-only guard would be scored `survived` falsely. It also cannot be shared with a co-worker's checkout safely if done on disk (`oyh28b` approval gate: "mutation proofs are staged IN MEMORY, never by editing a tracked file in this shared checkout"). A DISPOSABLE git worktree outside the repo satisfies both: the mutation is a real on-disk edit visible to subprocesses, and no tracked file of the shared checkout is touched. Measured cost basis: one bare suite run is `201.44s` at authoring (`38 failed, 7181 passed, 2 skipped` at `fca848304`), so a full-suite mutant costs about 3.5 minutes and baseline failures must be subtracted, not ignored.
- Scope: IN: a new `tools/mutation_probe.py` that, given a production target `agent_workflows/<module>.py::<qualname>`, a mutation operator, and a test selection (pytest args; default the bare suite's own selection, `-m 'not slow and not livecorpus'`), creates a detached worktree of `HEAD` under a temp dir, runs the selection UNMUTATED to record the baseline failing node set, applies the mutant, reruns, and reports `killed` (a node that passed at baseline now fails or errors), `survived` (no such node), or `invalid` (mutant did not apply, or the mutated module fails to import so that every test errors, reported separately as `killed-by-import` and not counted as a guard); optional `--extra-test <commit>:<path>` writes a historical test blob into the worktree's `tests/` so a replayed deleted test can serve as the POSITIVE CONTROL; always removes the worktree (`git worktree remove --force` plus `git worktree prune`). Operators: `return-none`, `return-true`, `return-false`, `negate-return` (wrap each `return <expr>` as `return not (<expr>)`), `raise` (body becomes `raise RuntimeError("mutant")`), `noop` (body becomes `pass`/`return None`). Behavioral tests over a synthesized repo. `tools/README.md` section. OUT: choosing which targets to mutate (Order 07); a general mutation framework; any change to production code.
- Scope-Paths: tools/mutation_probe.py, tests/test_mutation_probe.py, tools/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g55j1e

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Provide a reproducible yes/no answer to "does this test selection fail when this production function is broken this way?", baseline-corrected and isolated from the shared checkout, so Order 07 can mutation-prove properties without hand-patching files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Probe

- [ ] E-01 Create `tools/mutation_probe.py` with `probe(repo_root, target, operator, pytest_args, extra_tests=(), timeout_s=1800) -> ProbeResult` and `main(argv)` (`<target> --op <operator> [--extra-test COMMIT:PATH ...] [--format text|json] [-- <pytest args>]`). Steps: `git worktree add --detach <tmp>/wt HEAD`; write each `--extra-test` blob from `git show <COMMIT>^:<PATH>` to `<wt>/<PATH>`; run `sys.executable -m pytest -o addopts="" -q -p no:randomly -p no:cacheprovider --junitxml <tmp>/base.xml <pytest args or default "-n auto -m 'not slow and not livecorpus'">` with `cwd=<wt>` and `PYTHONPATH=<wt>`; parse failing/erroring nodeids; locate `<qualname>` in `<wt>/agent_workflows/<module>.py` with `ast` (lineno/end_lineno of the function body; this is the TOOL editing a disposable copy, not a test reading source), splice the operator's replacement body at the body's indentation, `py_compile` it; rerun into `<tmp>/mut.xml`; compute `newly_failing = mut_fail - base_fail`; verdict `killed` if non-empty, `killed-by-import` if every collected node errors with an import/syntax error naming the mutated module, `survived` if empty, `invalid` if the qualname is absent or the operator does not apply (for example `negate-return` on a function with no `return <expr>`). Report target, operator, baseline fail count, mutated fail count, up to 20 `newly_failing` nodeids, wall time. Remove the worktree in a `finally`, then `git worktree prune`. Refuse (exit 2) if the main checkout's `git status --porcelain` changed during the probe.
  - Depends on: none
  - Expected outcome: `python3 tools/mutation_probe.py agent_workflows/run_freeze.py::freeze_requirements --op raise -- tests/` reports `killed` or `survived` with baseline counts, and the shared checkout's `git status --short` and `git worktree list` are identical before and after.
  - Execution state: pending

### Task group 2: Tests and docs

- [ ] E-02 Create `tests/test_mutation_probe.py` that builds a throwaway git repo under `tmp_path` with `agent_workflows/m.py` defining `def is_even(n): return n % 2 == 0` and `def unused(): return 1`, `tests/test_m.py` asserting `is_even(2)` and `not is_even(3)`, and one test that fails at baseline regardless; commit; drive `probe` and assert: `is_even` + `negate-return` -> `killed` with the two assertion nodes in `newly_failing` and the always-failing node excluded; `unused` + `return-none` -> `survived`; a missing qualname -> `invalid`; an `--extra-test` historical blob that is the only test asserting `unused() == 1` turns `unused` + `return-none` into `killed`; after each call the fixture repo's `git worktree list` has only the main worktree and `git status --porcelain` is empty. Drive `main([..., "--format", "json"])` once and assert exit code and JSON keys. No `livecorpus` marker; no real trim sha.
  - Depends on: E-01
  - Expected outcome: the new file passes in the default bare run and exercises every verdict except `killed-by-import`, plus a `killed-by-import` case using an operator splice that makes the module unimportable (for example a target whose replacement is forced to an invalid indent via a test-only operator hook, or a module-level function the tests import at collection whose mutant raises at import).
  - Execution state: pending

- [ ] E-03 Add a `mutation_probe.py` section to `tools/README.md`: purpose, the disposable-worktree isolation rule and why in-memory patching is insufficient for subprocess-driven tests, the operator list, the verdict classes including baseline subtraction, the positive-control use of `--extra-test`, and the measured cost (one bare-suite selection is about 200 s here).
  - Depends on: E-01
  - Expected outcome: README section with those points.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Mutation is P16's own validity test (`GUIDING_PRINCIPLES.md` Section 16, bullet "Verify test sensitivity with mutation").
- Never edit a tracked file of the shared checkout for an experiment (`AGENTS.md` "Shared checkout"; `oyh28b` approval gate). A detached worktree outside the repo is a separate working tree and is torn down afterwards.
- Narrowed pytest runs use `-o addopts=""` (repo-local development contract in `AGENTS.md`); this tool passes the default marker selection explicitly so its default equals what a bare run selects.
- Bare suite at authoring HEAD `fca848304`: `38 failed, 7181 passed, 2 skipped, 3 warnings in 201.44s`, so baseline subtraction is mandatory: a mutant cannot be credited for a node that already fails.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | No mutation tooling exists in the repo or environment. | `python3 -c "import mutmut"` -> `ModuleNotFoundError: No module named 'mutmut'`; no `tools/*.py` mutates code (`ls tools`). |
| F-02 | In-memory mutation cannot see subprocess-driven behavior. | Plan `oyh28b` E-05 prescribes a `-p` plugin patching in `pytest_configure`; a subprocess `aw ...` imports a fresh interpreter that never loads that plugin. |
| F-03 | The bare suite currently has 38 failing nodes, so raw "any failure" is not a kill signal. | Bare `python3 -m pytest` at `fca848304`: `38 failed, 7181 passed, 2 skipped, 3 warnings in 201.44s (0:03:21)`. |
| F-04 | A disposable worktree is the repo's established isolation unit. | `git worktree list` shows the runner's own lanes under `.aw/worktrees/`; the runner isolates each item in one (`AGENTS.md` "each execute item gets its own ISOLATED WORKTREE"). This probe uses a temp dir outside the repo instead, so it never collides with lane leases. |

## Proposed changes (ordered, validatable)

1. Probe with baseline subtraction and worktree isolation (E-01).
2. Synthesized-repo tests for every verdict (E-02).
3. README section (E-03).

## Deferred / out of scope (with reason)

- Selecting targets and operators per property, and running the probes: Order 07 (`rq3q7v`).
  - Carrier: rq3q7v
- Automatic operator enumeration (mutating every statement): not needed; the audit mutates named properties, and per-statement enumeration multiplies the 200 s cost by orders of magnitude.
  - Carrier-Declined: Won't-fix for this Set by measured cost (F-03 suite time); a property-level operator answers the item's question.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_mutation_probe.py` passes.
- One live probe on the real tree with `git status --short` and `git worktree list` identical before and after.
- Bare `python3 -m pytest`, actual summary pasted, no new failures versus an execution-start baseline.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs `tools/` audit scripts. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Where should the disposable worktree live?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Under `tempfile.mkdtemp()`, outside the repo, so it is never mistaken for a runner lane under `.aw/worktrees/` and never leased. `git worktree prune` after removal keeps `.git/worktrees` clean.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git status --short` and `git worktree list` before and after one live run of `python3 tools/mutation_probe.py agent_workflows/run_freeze.py::freeze_requirements --op raise --format json -- tests/` (produced by E-01's `main`), and that run's pasted JSON showing verdict, baseline fail count and mutated fail count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" -q tests/test_mutation_probe.py` summary line, and a mapping of each verdict class (`killed`, `survived`, `invalid`, `killed-by-import`, positive-control `--extra-test`) to the test node that asserts it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md`; pasted bare `python3 -m pytest` summary line with no new failures versus the execution-start baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: commit only the declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`; never `git add -A`, never `--no-verify`, never push. The probe must never edit a tracked file of the invoking checkout; if a run leaves a worktree or a dirty path behind, fix the tool, do not hand-clean. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
