# IPD: Restore behavioral coverage of aw check findings parity between CI and local invocations

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `crk6wb`: commit `19313eed` deleted `tests/test_ci_check_parity.py`, whose `TestCiLocalParity` class was the only behavioral guard that a CI-shaped `aw check` invocation and a local one on the SAME tree yield the same findings `(rule, location)` and the same exit code. Plan `ev7t1w` (site S-06, verdict RETIRE-UNGUARDED) recorded the hole, and the `check_engine.check_scope_drift` docstring still says "no live guard currently asserts this parity".
- Scope: Add one new outcome test module, `tests/test_check_ci_local_parity.py`, that drives `python -m agent_workflows check <type> --agent` as subprocesses over seeded temporary git repos in the two invocation shapes (CI shape: cwd is the repo, `CI`/`GITHUB_ACTIONS` set, no `--dir`; local shape: `--dir <repo>` from a different cwd, those variables unset) for the four types the CI `attention-check` job gates (`plans`, `releases`, `backlog`, `release-gates`), and asserts equal finding sets and exit codes, a fail-closed exit on a seeded violation, and a zero exit on a clean tree. Update the one stale docstring sentence in `check_engine.check_scope_drift` to name the new guard. DOES NOT restore the deleted workflow-text assertions (`TestCiWorkflowInvokesShippedEngine`, which read `.github/workflows/tests.yml` by substring) or the CODEOWNERS/branch-protection doc substring tests, since those are text pins forbidden by P16; DOES NOT change `check_engine` behavior or `.github/workflows/tests.yml`.
- Scope-Paths: tests/test_check_ci_local_parity.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- From-Spec: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: crk6wb
- Set: crk6wb
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 96qxfz

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-crk6wb-01-96qxfz)
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog crk6wb; review-ready.

## Goal

Re-establish a behavioral, mutation-proven guard that `aw check` produces the same findings and exit code whether invoked the way CI invokes it or the way a developer invokes it locally on the same tree, so the CI gate and a local run cannot silently diverge.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: parity test module

- [ ] E-01 Create `tests/test_check_ci_local_parity.py` with a helper that builds a temporary `git init`ed repo and a helper `_run(repo, rtype, shape)` that runs `check <rtype> --agent` through `tests.support.run_cli` (which prepends this checkout to `PYTHONPATH` via `support.pinned_env`; a bare `subprocess.run([sys.executable, "-m", "agent_workflows", ...])` from the temp-repo cwd imports `agent_workflows` from whatever editable install site-packages points at, NOT this tree, while the local shape's cwd would import this tree, so the two shapes would run DIFFERENT code and the E-04 mutations would be invisible to the CI shape; plan-review probe) in either the CI shape (cwd=`repo`, env with `CI=true` and `GITHUB_ACTIONS=true`, no `--dir`) or the local shape (cwd = the repository root of this checkout, `--dir <repo>`, env with `CI` and `GITHUB_ACTIONS` removed), returning `(returncode, sorted({(d["rule"], d["location"]) for d in diagnostics}))` parsed from the last `aw.agent/v1` JSON line of stdout. The repo helper uses `tests.support.init_repo` and creates it under `tempfile.TemporaryDirectory()` (cleaned up), never under this checkout.
  - Depends on: none
  - Expected outcome: the module imports and the helpers return parsed finding sets for both shapes; both shapes demonstrably import this checkout's package (the E-04 mutations reaching the CI shape is the proof).
  - Execution state: pending
- [ ] E-02 Add a seeded-violation parity test parameterized over `plans`, `releases`, `backlog`, `release-gates`: seed one nonconforming artifact for the type (for `plans` a `.aw/records/plans/pending/badname.ipd.md` as in `19313eed^:tests/test_ci_check_parity.py`; for `backlog` a misnamed `.aw/records/backlog/open/bad.backlog.md` missing required fields; for `releases` a misnamed release record; for `release-gates` a CONFORMING backlog item, e.g. `.aw/records/backlog/open/20261014-zprobe-01-zprobe-probe-item.backlog.md` with `- Id: zprobe`, `- Status: open`, `- Set: zprobe`, `- Priority: low`, `- Work-Kind: chore`, `- Summary: probe item`, `- Blocks-Release: zzzzzz`, and a one-line `## Workflow history`, with no release record, so `check.blocks-release-dangling` is the only finding; plan-review probe: both shapes exit 1 with exactly that finding), then assert the two shapes return EQUAL finding sets, EQUAL exit codes, exit code `1`, and that the finding set is NON-EMPTY and contains the specific rule the seed targets (`check.name-nonconformant` for `plans`, `releases`, and `backlog`; `check.blocks-release-dangling` for `release-gates`; all four reproduced at review), so an empty-vs-empty or cannot-run-vs-cannot-run (exit 2) comparison cannot pass vacuously.
  - Depends on: E-01
  - Expected outcome: four parity cases pass on the current tree.
  - Execution state: pending
- [ ] E-03 Add a clean-tree test: for a temporary git repo containing only an empty `.aw/records/` directory, assert both shapes exit `0` for each of the four types and return equal finding sets. Do NOT reproduce the deleted `test_clean_tree_passes` recipe (`index plans --dir <repo>` on a bare `git init` repo): at review it raised `FileNotFoundError` on the AW_HOME `records/plans/INDEX.json` path, and `check` on a repo with no `.aw/records/` exits `2` (`cannot-run`, `next: aw install .`) in BOTH shapes, which would make a parity assertion pass while the exit-0 assertion fails. With `.aw/records/` present, review measured exit `0` in both shapes for all four types (findings: an info-level `check.collisions-not-checked` for three types, none for `release-gates`).
  - Depends on: E-01
  - Expected outcome: clean-tree cases pass on the current tree.
  - Execution state: pending

### Task group 2: sensitivity proof and docstring

- [ ] E-04 Mutation-prove sensitivity in a scratch edit to `agent_workflows/check_engine.py` that is reverted before commit (the edit reaches both subprocess shapes only because E-01 pins `PYTHONPATH`): (a) in `check_engine.check_type`, before it returns, drop the first element of the drift list when `os.environ.get("CI")` is set; (b) in the same place, when `Path.cwd().resolve() == Path(repo_root).resolve()`, replace each Drift's `location` with the absolute `str(Path(repo_root) / location)` via `_replace`; run the new module under each mutation and record that it FAILS, then revert and confirm `git diff agent_workflows/check_engine.py` shows only the E-05 docstring change (or nothing yet).
  - Depends on: E-02
  - Expected outcome: each mutation turns at least one parity test red; reverted tree is green.
  - Execution state: pending
- [ ] E-05 Replace the sentence in the `check_engine.check_scope_drift` docstring reading "which is what ``tests/test_ci_check_parity.py`` (deleted in ``19313eed``; no live guard currently asserts this parity) compared" with one naming `tests/test_check_ci_local_parity.py` as the live parity guard.
  - Depends on: E-02
  - Expected outcome: the docstring no longer claims the parity is unguarded.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite bare: `python3 -m pytest` (AGENTS.md repository development contract); narrowed runs use `python3 -m pytest -o addopts="" tests/test_check_ci_local_parity.py`.
- P16 (GUIDING_PRINCIPLES): tests assert observable outcomes only; never read production source or workflow YAML text. The new module therefore drives the CLI by subprocess and never opens `.github/workflows/tests.yml`.
- P16 "Verify test sensitivity with mutation" and the "Never weaken an assertion" bullet: hence the non-empty, rule-specific assertion in E-02 and the mutation proof in E-04.
- The CI `attention-check` job in `.github/workflows/tests.yml` runs `python -m agent_workflows check plans --agent`, `check releases --agent`, `check backlog --agent`, and `check release-gates --agent` from the repo root with no `--dir` (quoted step strings "aw check plans (plan conformance; fail closed)" etc.); that is the CI shape E-01 reproduces.
- Precedent behavioral module for the same deletion commit: `tests/test_check_scope_drift.py` (plan `qqg41f`, backlog `caf5ed`) states its bound and its mutation proofs in the module docstring; follow that shape.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The deleted `TestCiLocalParity.test_ci_and_local_identical_on_same_tree` ran the SAME invocation twice, so it proved determinism, not CI-vs-local parity; the restored test must vary the invocation shape to test the stated property. | `git show 19313eed^:tests/test_ci_check_parity.py`: both calls use `_run_check(repo, "plans")` with identical cwd/args/env. |
| F-2 | The two shapes currently agree. | Authoring probe: a seeded misnamed backlog item checked with cwd=repo and `CI=true GITHUB_ACTIONS=true` versus `--dir <repo>` from another cwd with those variables unset produced byte-identical `--agent` output (`IDENTICAL`), exit 1, first rule `check.name-nonconformant`. A clean `git init` repo with `index plans` run returned exit 0 for all four types in both shapes. Seed probes: a misnamed `bad.release.md` makes `check releases` exit 1; a conforming backlog item with `- Blocks-Release: zzzzzz` and no release record makes `check release-gates` emit `check.blocks-release-dangling`. |
| F-3 | The deleted workflow-text and doc-substring tests are not restorable. | They assert `assertIn("python -m agent_workflows check plans", text)` on YAML text and on `docs/branch-protection.md`; P16 forbids text pins. The backlog item itself says "only behavioral outcomes may be restored, never a source-reading pin (P16)". |
| F-4 | A stale docstring claims no guard exists. | `check_engine.check_scope_drift` docstring: "``tests/test_ci_check_parity.py`` (deleted in ``19313eed``; no live guard currently asserts this parity)". |
| F-6 | (plan-review) No code in `agent_workflows/` reads `CI` or `GITHUB_ACTIONS` today, so the observable shape difference is cwd-discovery vs `--dir`; the env limb still models CI and is what mutation (a) keys on. The other real difference is WHICH package each shape imports unless the subprocess is pinned (E-01). | `rg -n "GITHUB_ACTIONS|environ.get\(\"CI\"\)" agent_workflows/` -> no hit; review probe: unpinned `python -c "import agent_workflows"` from a temp cwd resolved to a different checkout's editable install. |
| F-5 | The `ev7t1w` audit attributed S-06 to `check_scope_drift`, but the property is the whole `aw check` surface; the parity test covers every finding the four gated types emit, which includes drift findings when present. | `ev7t1w` site table row S-06. |

## Proposed changes (ordered, validatable)

1. New module `tests/test_check_ci_local_parity.py` (E-01..E-03).
2. Mutation proof, scratch only (E-04).
3. Docstring sentence update in `agent_workflows/check_engine.py` (E-05).

## Deferred / out of scope (with reason)

- Workflow-YAML and CODEOWNERS / `docs/branch-protection.md` substring assertions: text pins, forbidden by P16 (F-3).
  - Carrier-Declined: P16 forbids the assertion shape itself; there is no behavioral property left to carry.
- Comparing the advisory `next` hint field: the deleted test excluded it as nondeterministic ordering; parity is defined on findings and exit code.
  - Carrier-Declined: `next` is an advisory hint, not a finding; excluding it is the definition of the property, not deferred work.
- Scope-drift-specific parity (seeding a live begin receipt in a lane worktree): drift behavior is already covered by `tests/test_check_scope_drift.py`; this plan guards invocation-shape parity, which is type-agnostic.
  - Carrier-Declined: already covered by live `tests/test_check_scope_drift.py`; nothing is left unowned.

## Scope check

- Over-scope: none.
- Under-scope: none; the four types are exactly those the CI `attention-check` job runs through `aw check`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_check_ci_local_parity.py -v` passes (E-01..E-03).
- Each E-04 mutation turns the module red; reverted tree green. (Each `check` subprocess took about 0.55s at review, so the 16 invocations cost roughly 9s; no `slow` marker is warranted.)
- Full bare suite `python3 -m pytest` passes with no new failures.
- `aw ipd lint` on this plan conforms at `--phase pre-transition` before finalize.

## Spec / documentation sync

N/A: no spec governs this test-only change, and the only prose touched is one code docstring (E-05). No user-facing docs change.

## Open questions

### OQ-01: Should the restored module also re-pin the CI workflow invoking the shipped entry point?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. That assertion read `.github/workflows/tests.yml` by substring, a text pin P16 forbids, and the backlog item restricts restoration to behavioral outcomes. Invocation-shape parity is the behavioral property.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git status --short` showing `tests/test_check_ci_local_parity.py` as a new file, a pasted excerpt of `_run` showing both shapes go through `tests.support.run_cli` (PYTHONPATH-pinned), plus pasted output of `python3 -m pytest -o addopts="" tests/test_check_ci_local_parity.py -v` showing collection succeeded and test names listed.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the four seeded-violation parity cases (`plans`, `releases`, `backlog`, `release-gates`) PASSED, and a pasted excerpt of the test source showing the non-empty and rule-specific assertions.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the clean-tree case(s) PASSED for all four types, plus a pasted excerpt of the test source showing the seed is a repo with `.aw/records/` present and the assertion is exit `0` (not merely equal exit codes) in both shapes.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: for each of mutations (a) and (b), the pasted mutation diff and the pasted pytest output showing at least one FAILED test; then pasted `git diff agent_workflows/check_engine.py` after revert showing no mutation residue, and a pasted green rerun.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff agent_workflows/check_engine.py` showing only the docstring sentence change naming `tests/test_check_ci_local_parity.py`, plus the pasted `N passed` summary line of a bare `python3 -m pytest` run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Low-risk test-only chore: one new test module and one docstring sentence; no behavior change. The reviewer should check that F-1's correction (varying the invocation shape rather than repeating one invocation) matches the intended property, and that the four seeds each exercise a real finding.

Execute only after human approval (`aw ipd set approved 96qxfz --by-human`). Open questions: OQ-01 is resolved; none remain. Begin with `aw ipd begin 96qxfz`.

Scope fence: `- Scope-Paths:` is a DECLARATION reconciled at finalize. If an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`; acknowledge a declared-but-unmodified path with `--scope-ack`. The E-04 mutations are scratch edits and MUST be reverted before any commit; V-04 demands the empty residue diff.

Honesty rule: every `V-*` item MUST paste the ACTUAL runner output; never claim a result you did not run.

Commits: commit only through `aw commit 96qxfz -- tests/test_check_ci_local_parity.py agent_workflows/check_engine.py <this plan path>` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` first, and never push.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize 96qxfz` once `aw ipd lint --phase pre-transition` conforms and V-01..V-05 hold pasted evidence with `Result: pass`. Never hand-roll a `git mv` into `executed/`. Backlog `crk6wb` closes through the handoff route (this plan carries `- From-Backlog: crk6wb`).
