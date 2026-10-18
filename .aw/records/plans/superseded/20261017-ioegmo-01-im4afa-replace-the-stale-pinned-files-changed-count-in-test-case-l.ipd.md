# IPD: Replace the stale pinned files-changed count in test_case_l with a derived oracle

- Date: 2026-10-17
- Kind: child
- Concern: `TestCleanTargetConfigHome.test_case_l_tracked_install_still_writes_target` asserts a hard-coded `git show --stat` total ("358 files changed") for a private-target install, so every new file added to the installed payload (most recently `.aw/system/workflows/askme/rationale.md`) breaks the suite even though install behavior is correct.
- Scope: Replace the literal count with an assertion derived from the installer's own observable outputs, so the test still proves that the commit contains exactly what the install wrote and nothing else, without pinning a payload size.
- Scope-Paths: tests/test_clean_target_config_home.py
- Item-Dependencies: none
- Status: superseded
- Readiness: no-go
- Work-Kind: bug
- Priority: high
- From-Backlog: ioegmo
- Blocks-Release: next
- Set: ioegmo
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: im4afa

## Workflow history
- 2026-10-18 superseded (aw set): Superseded by 84cba788c and executed plan 3nczai
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (HIGH, open, OQ-02 blocking), PR-002 (MEDIUM, open)
- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored from backlog ioegmo; reproduced the failure in the lane (363 actual vs 358 pinned).

## Goal

Make `test_case_l_tracked_install_still_writes_target` assert an outcome (the install commit contains exactly the files the installer reports it created and staged) instead of a magic number, so adding a workflow file to the payload no longer turns the release gate red while a real over- or under-commit still fails it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Establish the oracle empirically

- [ ] E-01 In a scratch run of the test body (or a temporary debug print inside the test, removed before commit), capture for the private-target install: (a) `git diff --name-only HEAD~1 HEAD` in the target, (b) the JSON list in `<target>/.agent-workflows-installer-backups/<ts>/.created-files.json` (written by `engine.save_created_files_record`), and (c) which of (b) are git-ignored per `git check-ignore`. Record whether set(a) equals set(b) minus ignored paths, and if not, which paths differ and why.
  - Depends on: none
  - Expected outcome: A written comparison (pasted into the V-01 evidence) that states whether the created-files record, filtered to non-ignored paths, is an exact oracle for the commit's file set, with any discrepancy explained by source (`engine.prompt_and_run_commit` / `engine._stage_installed_file`).
  - Execution state: pending

### Task group 2: Replace the pin

- [ ] E-02 In `tests/test_clean_target_config_home.py`, `test_case_l_tracked_install_still_writes_target`, replace `self.assertIn("358 files changed", tail)` with: (1) the set of paths changed by the install commit (`git diff --name-only HEAD~1 HEAD`) equals the oracle chosen in E-01 (preferred: the `.created-files.json` record filtered to non-ignored paths; if E-01 shows a principled, explained difference, apply exactly that adjustment in code with a comment citing the reason); (2) the `--stat` tail still matches `^\s*N files? changed` where N equals the length of that set; (3) the set is non-empty and contains `AGENTS.md` and `.aw/.gitignore`. No literal file count may remain.
  - Depends on: E-01
  - Expected outcome: The test passes on the current payload, contains no hard-coded file total, and asserts equality between the committed set and an installer-produced record.
  - Execution state: pending

- [ ] E-03 Prove the new assertion is not vacuous: temporarily (not committed) make the oracle disagree, e.g. by creating and `git add`-ing an extra untracked file in the target before the install so it is swept into the commit, or by dropping one entry from the oracle set in the test, and confirm the test fails; then revert the temporary change.
  - Depends on: E-02
  - Expected outcome: A captured failing run showing the assertion detects an over-commit or a mismatch, followed by the reverted file showing no residue in `git diff`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests must assert observable outputs; a derived set equality between the commit and the installer's own record is an outcome assertion, while a payload size literal is a coupling to unrelated source files.
- The routine gate is bare `python3 -m pytest`; narrowed per-test runs use `python3 -m pytest -o addopts="" <path> -k <name>` (repo-local development contract in AGENTS.md).
- The installer writes its created-files list in `engine.save_created_files_record` (`record_path = backup_dir / ".created-files.json"`), and `engine.run_rollback` consumes that same record, so it is an existing, contract-bearing artifact rather than test-only scaffolding.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The pin has already drifted twice: commit `9ca816dba` introduced "357 files changed", `a75488af5` bumped it to "358", and the backlog item records the askme `rationale.md` addition (`37d37ee4e`) breaking it again. | `git log -L574,574:tests/test_clean_target_config_home.py` |
| F2 | The test currently fails in this lane: `AssertionError: '358 files changed' not found in ' 363 files changed, 20528 insertions(+)'`. | `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` |
| F3 | The only `files changed` literal in the test tree is this one, so the fix is single-site. | `grep -rn "files changed" tests/` (other hit is a comment in `tests/test_status_set.py`) |
| F4 | The other assertions in case (l) (HEAD moved, `AGENTS.md`, `.aw/.gitignore`, backups dir exist, "Git: changes staged; commit offered below") are outcome assertions and stay unchanged. | test body |

## Proposed changes (ordered, validatable)

1. E-01: measure the commit set against the `.created-files.json` record to pick an exact oracle.
2. E-02: replace the literal with set equality plus a consistent `--stat` count derived from that set.
3. E-03: demonstrate the new assertion fails on a deliberate mismatch.

## Deferred / out of scope (with reason)

- Changing installer behavior or payload: the install is correct; only the test is stale.
  - Carrier-Declined: installer behavior is correct; only the test is stale
- Auditing other tests for different pinned payload counts (e.g. installed-item counts not phrased as "files changed"): not evidenced by this item; file a separate backlog item if found during execution.
  - Carrier-Declined: not evidenced by this item; will file a separate backlog item if found during execution

## Scope check

- Over-scope: none.
- Under-scope: none; the single failing assertion is the whole defect (F3).

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py` passes in full (all cases, not only case l).
- The E-03 negative run fails as expected.
- Bare `python3 -m pytest` core tier passes (or any failure shown to be pre-existing and unrelated, with output pasted).
- `grep -n "files changed" tests/test_clean_target_config_home.py` shows no numeric literal.

## Spec / documentation sync

N/A: test-only change; no spec or user-facing doc describes the installed file count.

## Open questions

### OQ-01: Is the created-files record an exact oracle for the commit set?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: Resolved by procedure rather than assumption: E-01 measures it, and E-02 either uses it directly or applies only an explained, coded adjustment. If E-01 shows no principled oracle exists, the fallback is still pin-free: assert the commit set equals the set of non-ignored files present in the target after install minus the pre-existing `README.md` (computed via `git ls-files` + filesystem walk excluding `.git`), which still detects a swept-in foreign file.

### OQ-02: Retire this plan as superseded, or rescope it?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: Resolved: retired as superseded by commit 84cba788c and executed plan 3nczai (Set 6i9viq), which derived the private-target install commit expectation and proved test sensitivity.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted comparison output from E-01 listing the commit path count, the record path count, the ignored-path count, and the symmetric difference (empty, or each differing path with its explained cause).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The `git diff` of `tests/test_clean_target_config_home.py` showing the literal removed and the derived assertions added, plus pasted output of `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py` showing all tests passed, plus pasted output of bare `python3 -m pytest` showing its `N passed` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted failing pytest output from the deliberate mismatch run (produced by the temporary change E-03 creates) naming the mismatched path(s), followed by `git status --porcelain` / `git diff` showing the temporary change is gone.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Commit only `tests/test_clean_target_config_home.py` and this plan via `aw commit im4afa -- <paths>`; never push. Move to `.aw/records/plans/executed/` through the lifecycle tooling only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
