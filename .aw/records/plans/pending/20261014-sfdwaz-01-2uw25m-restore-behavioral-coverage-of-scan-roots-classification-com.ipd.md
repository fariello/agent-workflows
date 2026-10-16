# IPD: Restore behavioral coverage of SCAN_ROOTS classification completeness

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_artifact_core.py`, and with it `ScanRootClassificationInvariantTests`, the only guard that no `artifact_core.SCAN_ROOTS` entry is scanned and then silently dropped because `attention._classify_tree` returns `None` for it (the `TODO.md` trap closed by `diof9n`). The comment above `SCAN_ROOTS` now says "no live guard currently asserts this" (left so by `ev7t1w` S-02, RETIRE-UNGUARDED). `rg -n "SCAN_ROOTS" tests/` finds only `tests/test_attention_blind_spot.py` and `tests/test_attention_contract.py`, and neither asserts the scanned-then-dropped property: `TrackedTreeScanCoverageTests` is deliberately one-directional (tracked tree -> scan root) and says so.
- Scope: IN: a new behavioral test module `tests/test_scan_root_classification.py` that exercises `artifact_core.iter_scan_files`, `attention._classify_tree` and `attention.scan` on synthesized temp repositories and asserts their outputs; repointing the one comment above `artifact_core.SCAN_ROOTS` from "no live guard currently asserts this" to the new test. OUT: any change to `SCAN_ROOTS`, `TREE_POLICY`, `attention._classify_tree`, `attention.scan` or `attention_contract.is_exempt_unclassified` behavior; restoring any other deleted test; any source-reading assertion (P16).
- Scope-Paths: tests/test_scan_root_classification.py, agent_workflows/artifact_core.py, .aw/records/plans/pending/20261014-sfdwaz-01-2uw25m-restore-behavioral-coverage-of-scan-roots-classification-com.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: sfdwaz
- Set: sfdwaz
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 2uw25m
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved

- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): plan-review complete; PR-001..PR-005 fixed
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (E-03 split into E-03/E-05 with corrected sort order, E-02 mechanism clarified, V-* bars re-based on behavior); review record `.aw/records/reviews/20261014-sfdwaz-01-2uw25m-restore-behavioral-coverage-of-scan-roots-classification-com.review.md`.
- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog `sfdwaz`; review-ready.

## Goal

Restore, as behavior-exercising tests, the guarantee that every `artifact_core.SCAN_ROOTS` entry either classifies to a `TreePolicy` through `attention._classify_tree` or is a member of a closed, named, separately justified exemption set, so a future root that is scanned and silently dropped (the `TODO.md` defect) fails the suite again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Restore the invariant as behavioral tests

- [ ] E-01 Create `tests/test_scan_root_classification.py` with a `ScanRootClassificationTests` class whose `test_no_scan_root_is_scanned_then_silently_dropped` calls `attention._classify_tree(root)` for every entry of `artifact_core.SCAN_ROOTS` and asserts the list of roots that return `None` and are not in the closed exemption set (`CITATION_ONLY_ROOT_DOCS = {"DECISIONS.md", "README.md", "ARCHITECTURE.md"}`, `LEGACY_CONTAINER_ROOTS = {".agents/docs"}`) is empty, with a failure message naming the offenders and the two remedies.
  - Depends on: none
  - Expected outcome: the test passes at HEAD; it reports `[]` offenders.
  - Execution state: pending
- [ ] E-02 In the same module add `test_the_exemptions_are_live_and_justified`: build a temp repo in which every exempted root exists (each of the three root docs as a file; `.agents/docs` as a directory holding one `.md` child), call `artifact_core.iter_scan_files(repo)` with its default roots, and assert that for each exempted name at least one returned repo-relative path equals that name or lies under `<name>/` (`iter_scan_files` returns FILES, not roots, so a directory root is observed through its child). Also assert `attention._classify_tree` returns a non-`None` policy for `.agents/docs/specs/x.spec.md` and `.agents/docs/research/y.md` (the children that justify the container exemption).
  - Depends on: E-01
  - Expected outcome: test passes; a stale exemption (a name no longer scanned) would fail it.
  - Execution state: pending
- [ ] E-03 In the same module add `test_todo_md_is_not_scanned`: build a temp repo containing `TODO.md` plus one `DECISIONS.md`, call `artifact_core.iter_scan_files(repo)` with its default roots, and assert `TODO.md` is absent from the returned relative paths while `DECISIONS.md` is present (this `iter_scan_files` assertion is the load-bearing one); then call `attention.scan(repo)` and assert no returned item or drift row names `TODO.md`.
  - Depends on: E-01
  - Expected outcome: test passes.
  - Execution state: pending
- [ ] E-05 In the same module add `test_the_invariant_detects_an_unclassified_root`: factor the E-01 offender computation into a module-level helper taking a roots iterable, run it over `artifact_core.SCAN_ROOTS + ("TODO.md", ".aw/records/no-such-tree")`, and assert it returns exactly the two appended roots (proves the guard is not vacuous).
  - Depends on: E-01
  - Expected outcome: test passes; the helper returns `[".aw/records/no-such-tree", "TODO.md"]` (Python `sorted` order: `.` sorts before `T`; measured at review HEAD `de5c53233`).
  - Execution state: pending

### Task group 2: Repoint the comment

- [ ] E-04 Edit the comment above `artifact_core.SCAN_ROOTS` (the sentence "former invariant `tests/test_artifact_core.py::ScanRootClassificationInvariantTests` was deleted in `19313eed`; no live guard currently asserts this.") so it names the restored guard `tests/test_scan_root_classification.py::ScanRootClassificationTests` and keeps the `19313eed` history. Comment-only edit; no executable change.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/artifact_core.py` touches only comment lines.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must call code and assert outputs; no `inspect`/`ast`/regex over source. Every assertion here calls `iter_scan_files`, `_classify_tree` or `scan`. Iterating the `SCAN_ROOTS` tuple as INPUT to those calls is data, not source reading.
- Test style: stdlib `unittest` classes with `tempfile.mkdtemp()` repos, as in `tests/test_attention_contract.py` (`TrackedTreeReachabilityTests`) and `tests/test_attention_blind_spot.py`.
- Run the suite bare: `python3 -m pytest` (repo-local contract); narrowed runs use `python3 -m pytest -o addopts="" <file>`.
- Commit through `aw commit 2uw25m -- <paths>`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| F | Finding | Evidence |
|---|---|---|
| F-01 | The backlog item says `classify_rel`; no such symbol exists. The classifier the deleted test exercised is `attention._classify_tree`. | `rg -n "classify_rel" --type py .` returns empty; `git show 19313eed7^:tests/test_artifact_core.py` calls `attention._classify_tree(root)` in `test_no_scan_root_is_scanned_then_silently_dropped`. |
| F-02 | At authoring HEAD `b8a40fdf4`, the roots classifying to `None` are exactly `DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, `.agents/docs`, which equals the deleted test's exemption set, so the restored test passes without behavior change. | One-off `python3 -c` over `C.SCAN_ROOTS` printing `_classify_tree(r)` name: all other 13 roots map to `plans`, `backlog`, `specs`, `research`, `walkthroughs`, `roadmaps`, `docs-prompts`, `releases`, `prompts`. |
| F-03 | The deleted module's four tests: `test_no_scan_root_is_scanned_then_silently_dropped`, `test_todo_md_is_not_a_scan_root` (`assertNotIn` on the tuple), `test_the_exemption_is_a_closed_named_set_not_a_predicate`, `test_the_legacy_container_exemption_is_justified_by_its_children`. E-03 replaces the tuple-membership assertion with an observed `iter_scan_files`/`scan` outcome. | `git show 19313eed7^:tests/test_artifact_core.py`, class `ScanRootClassificationInvariantTests`. |
| F-04 | Existing coverage does not overlap: `TrackedTreeScanCoverageTests` docstring states "THE CHECK IS DELIBERATELY ONE-DIRECTIONAL (tracked tree -> scan root, never the reverse)". | `tests/test_attention_contract.py`, class `TrackedTreeScanCoverageTests`. |

## Proposed changes (ordered, validatable)

1. E-01..E-03, E-05: add `tests/test_scan_root_classification.py` (four behavioral tests).
2. E-04: repoint the `SCAN_ROOTS` comment in `agent_workflows/artifact_core.py`.

## Deferred / out of scope (with reason)

- The other deleted `tests/test_artifact_core.py` classes (e.g. `DanglingTests`) belong to other backlog carriers filed by `ellenm` and are not this item's property.
  - Carrier: ellenm
  - Carrier-Evidence: .aw/records/plans/executed/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md
- Making `attention.scan` report root-level unclassified files: a behavior change, not coverage restoration.
  - Carrier-Declined: behavior change, not coverage restoration

## Scope check

- Over-scope: none.
- Under-scope: none; the one comment that names the missing guard is in Scope-Paths.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_scan_root_classification.py -v` shows every test in the module passing (V-01..V-03, V-05).
- Full suite bare `python3 -m pytest` passes (V-04).

## Spec / documentation sync

N/A: no behavior or contract changes; only a test module and a code comment.

## Open questions

### OQ-01: Should the restored test target `classify_rel` as named in the backlog item?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No such symbol exists (F-01); the property the deleted test guarded is expressed through `attention._classify_tree`, which is what the backlog's cited site `ev7t1w` S-02 describes. The item's requirement (restore behavioral coverage of the property) is unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_scan_root_classification.py -v` output showing the test that pins "every `SCAN_ROOTS` entry classifies via `attention._classify_tree` or is in the closed exemption set" PASSED (the E-01 name is a pointer, not the bar), plus pasted `rg -n "\binspect\b|\bimport ast\b|\bast\.|getsource|read_text\(" tests/test_scan_root_classification.py` output (expected: no match, or only matches that read a temp-repo fixture and never a package module), showing no source-reading (P16).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the test that pins "every exempted name is still yielded by `iter_scan_files` over a temp repo, and `.agents/docs` children classify non-`None`" PASSED, plus a one-off pasted demonstration that the exemption guard is live: rerun the E-02 assertion with an extra non-scanned name (for example `NOT-A-ROOT.md`) added to the exemption set and paste the resulting assertion failure.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the test that pins "`TODO.md` is absent from `iter_scan_files` output and from every `attention.scan` item and drift row, while `DECISIONS.md` is present" PASSED, and the module run's summary line showing zero failed and zero errors (re-derive the count at execution; do not compare against a number written here).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff agent_workflows/artifact_core.py` showing only `#` comment lines changed, naming `tests/test_scan_root_classification.py::ScanRootClassificationTests`, and still carrying `19313eed` and the "Do not re-add `TODO.md`" instruction, plus the pasted summary line of a bare `python3 -m pytest` run with zero failures.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output showing the test that pins "the offender helper reports both appended unclassified roots and nothing else" PASSED, plus the pasted value of a one-off `python3 -c` call of the helper over `SCAN_ROOTS + ("TODO.md", ".aw/records/no-such-tree")` showing exactly those two roots.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths through `aw commit 2uw25m -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. Paste actual runner output for every test claim.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `sfdwaz` carries no `- Blocks-Release:` to inherit.
