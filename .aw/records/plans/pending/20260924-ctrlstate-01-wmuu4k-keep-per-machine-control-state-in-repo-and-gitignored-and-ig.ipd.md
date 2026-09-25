# IPD: Keep per-machine control state in-repo and gitignored, and ignore the lane worktrees root in managed repos

- Date: 2026-09-24
- Kind: child
- Concern: Backlog `e820ka` asks WHETHER to relocate per-machine control state out of the repository now that the state-fork defect (`dh0uno`) is closed. Re-measured at HEAD `cfc7f5c1`: the fork is closed by `ipd_lifecycle.checkout_control_root` (one in-repo root keyed on `git rev-parse --git-common-dir`), so LOCATION causes no live failure and relocation is hygiene only. The decision is therefore KEEP IN-REPO, GITIGNORED. But the inventory found ONE remaining concrete harm: the lane worktrees root `.aw/worktrees/` (`worktree_lease.WORKTREES_SUBDIR`, plus owner records under `worktree_lease.OWNERS_SUBDIR`) is ignored in THIS repo only by its hand-written root `.gitignore` (".aw/worktrees/"), and NOT by the framework-owned `engine._AW_GITIGNORE_TEMPLATE` nor the `engine._ensure_aw_gitignore` back-fill. Probe in a fresh `git init` repo after `_ensure_aw_gitignore`: `.aw/state/x`, `.aw/config/local.json`, `.aw/records/runs/x`, `.aw/workflow-artifacts/x` are all ignored, while a real `git worktree add .aw/worktrees/abc123` plus `.aw/worktrees/.owners/abc123.json` shows `?? .aw/worktrees/.owners/abc123.json` and `?? .aw/worktrees/abc123/` in `git status --porcelain`. In a managed repo a driver run therefore offers every lane checkout (as an embedded gitlink) and every owner record to `git add -A`, contradicting the module's own comment "Inside the gitignored worktrees root, so it is never committed".
- Scope: IN: (a) add the anchored `/worktrees/` pattern to `engine._AW_GITIGNORE_TEMPLATE` and to the `engine._ensure_aw_gitignore` back-fill; (b) add a `/worktrees/` row to `tests/test_installer.py` `AwGitignoreLaneTests.LANES`; (c) add an end-to-end guard test asserting real `git check-ignore` ignores every per-machine control path in a freshly installed repo; (d) record the keep-in-repo decision in spec `20260810-1447-01` Section 5 and resolve it as OQ-01. OUT: any XDG relocation, migration path, Windows fallback (moot under the decision); the root `.gitignore` of this repo (already correct); non-repository records backends.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py, .aw/.gitignore, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- Set: ctrlstate
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wmuu4k
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: e820ka

## Workflow history
- 2026-09-25 approved (aw set): status set to approved

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED. Reproduced the plan's central `git check-ignore` probe end to end in a fresh repo with a REAL `git worktree add`: every claim in its Findings table is TRUE, and one `/worktrees/` line is sufficient. PR-001 (E-01's `anchored=True` activates a repair branch hardcoded to `inbox`, so the new row would fail PERMANENTLY; measured `/worktrees/` -> `['worktrees/']`, and `/state/`/`/workflow-artifacts/` fail it too, which is why neither has a row), PR-002 (E-03's regen command is a measured no-op on an existing file and would then append a comment-less bare line, failing its own V-03 `SAME`), PR-003 (`git add -A` stages a lane as an embedded GITLINK at mode `160000`, a worse harm than recorded), PR-004 (gate carried almost no execution contract and did not preserve the test-first structure), PR-005 (uncarriered OQ, `check.ipd-uncarried-obligation` at `error`) all FIXED. Added F-4..F-7 and OQ-02 (carrying `- Finding: F-6`, the pre-existing `inbox`-only repair gap, recommended for a separate plan). Findings in `.aw/records/reviews/20260924-ctrlstate-01-wmuu4k-keep-per-machine-control-state-in-repo-and-gitignored-and-ig.review.md`. Readiness go-pending-approval.
- 2026-09-25 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED (two were unrunnable instructions found by executing the code)

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog e820ka; re-measured with `git check-ignore` in a fresh repo after `_ensure_aw_gitignore` that every control path is ignored EXCEPT `.aw/worktrees/`, which a real `git worktree add` shows as untracked.

## Goal

Close the backlog decision with evidence (keep per-machine control state in-repo, gitignored, behind the single accessor `ipd_lifecycle.checkout_control_root`), fix the one remaining harm (lane worktrees root not ignored in managed repos), and pin every control path's ignored status with a guard test that fails if any lane is dropped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: guard tests first (must fail before the fix)

- [x] E-01 Add a row to `tests/test_installer.py` `AwGitignoreLaneTests.LANES` for the lane worktrees root: pattern `/worktrees/`, a pre-lane back-fill body equal to the current template's pattern lines minus that line (i.e. ending with `/workflow-artifacts/`), and a `why` naming `worktree_lease.WORKTREES_SUBDIR` and `OWNERS_SUBDIR`.
  - THE `anchored` COLUMN MUST BE `False`, AND THIS IS A MEASURED CORRECTION, not a style choice. `anchored=True` additionally runs branch (d) REPAIR, which asserts that a pre-existing BARE `worktrees/` line is REWRITTEN to `/worktrees/`. No such repair exists: `engine._ensure_aw_gitignore` has exactly ONE repair regex, `bare_inbox = re.compile(r"(?m)^inbox/[ \t]*$")`, hardcoded to `inbox`. Measured by driving the helper directly: a pre-existing bare `worktrees/` survives and the result is `['worktrees/']` where the branch wants `['/worktrees/']`, so `anchored=True` makes the row FAIL PERMANENTLY, not just before E-03. The SAME measurement shows `/state/` and `/workflow-artifacts/` would fail it too (both come back `['state/', '/state/']` and `['workflow-artifacts/', '/workflow-artifacts/']`), which is precisely why neither has a LANES row today: the existing table's only `anchored=True` row is `/inbox/`, the one lane the repair regex covers.
  - WRITE THE ANCHORED FORM IN THE PATTERN REGARDLESS. `anchored=False` does NOT mean "unanchored pattern"; the column selects the repair assertion, while the `pattern` string is what must appear. `/worktrees/` stays anchored in the template for the `/inbox/` reason.
  - IF A GENERAL REPAIR IS WANTED, that is a separate change to `_ensure_aw_gitignore` (generalize the regex over the anchored-pattern list) and it is NOT in this plan's scope; see OQ-02.
  - Depends on: none
  - Expected outcome: `test_every_lane_is_present_anchored_backfilled_and_idempotent` fails before E-03 because the template carries 0 pattern lines for this lane, AND passes after E-03 rather than failing on a repair branch that cannot be satisfied.
  - Execution state: performed
- [x] E-02 Add an end-to-end test (new method in `AwGitignoreLaneTests`, e.g. `test_git_ignores_every_per_machine_control_path`) that runs `init_repo`, `INS._ensure_aw_gitignore(root)`, creates one file under each of `.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/<id>/`, `.aw/workflow-artifacts/<wf>/`, `.aw/worktrees/<lane>/`, `.aw/worktrees/.owners/<lane>.json`, and asserts `git check-ignore -q` returns 0 for each, listing all misses in one failure message. Also assert `.aw/config/project.json` is NOT ignored (portable, tracked), so the test cannot pass via an over-broad pattern.
  - USE A PLAIN DIRECTORY FOR THE LANE, NOT `git worktree add`, and record why: a real worktree creates an embedded GITLINK, and the review measured `git add -A` staging it at mode `160000` with git printing a `git rm --cached` submodule hint. `check-ignore` gives the same verdict for a plain directory, so the cheap form proves the same property without a second git repo inside the fixture. The gitlink behavior is evidence for WHY this matters (V-02), not something the unit test needs to reproduce.
  - Depends on: none
  - Expected outcome: fails before E-03 naming exactly the two `.aw/worktrees/` paths.
  - Execution state: performed

### Task group 2: the fix

- [x] E-03 In `agent_workflows/engine.py`, add an anchored `/worktrees/` line with a short comment (per-lane git worktrees and their owner records, `worktree_lease.WORKTREES_SUBDIR` and `OWNERS_SUBDIR`; anchored for the `/inbox/` reason) to `_AW_GITIGNORE_TEMPLATE`, and add `"/worktrees/"` to the line-anchored back-fill loop in `_ensure_aw_gitignore` (alongside the `"/workflow-artifacts/"` loop).
  - DO NOT REGENERATE THIS REPO'S `.aw/.gitignore` WITH `_ensure_aw_gitignore`; EDIT IT BY HAND to mirror the template. The regen command originally prescribed here CANNOT produce the intended file, measured directly: the file already EXISTS, so the helper takes the BACK-FILL branch (the template branch runs only when `not gi.is_file()`), and that branch appends a BARE pattern line with NO comment. So the regen yields a file that differs from the template by exactly the comment block, and V-03's `diff ... && echo SAME` would FAIL. Verified twice: running the helper against this repo's current `.aw/.gitignore` returned `wrote: False` and changed nothing (md5 identical), and simulating the post-fix state produced a one-line diff (the comment present in the template, absent from the back-filled file).
  - THE INVARIANT TO PRESERVE is that the tracked `.aw/.gitignore` is byte-identical to `_AW_GITIGNORE_TEMPLATE`, which it IS today (measured: `diff` of the rendered template against the tracked file is empty). Keep it so by copying the template text, e.g. `python3 -c "from pathlib import Path; from agent_workflows import engine as E; Path('.aw/.gitignore').write_text(E._AW_GITIGNORE_TEMPLATE, encoding='utf-8')"`, which writes the template verbatim and cannot drift from it.
  - Depends on: E-01, E-02
  - Expected outcome: both new tests pass; `.aw/.gitignore` gains the commented `/worktrees/` block and still matches the template byte for byte.
  - Execution state: performed

### Task group 3: record the decision

- [x] E-04 Append to spec `20260810-1447-01` Section 5 ("Placement and Git policy") a short paragraph: per-machine control state (`.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/`, `.aw/workflow-artifacts/`, `.aw/worktrees/`) stays IN the target repository and is covered by the framework-owned `.aw/.gitignore`; its location is decided in one accessor (`ipd_lifecycle.checkout_control_root`, driver runs via `runner_shared.state_root`), so relocation out of the repo (retired `58ha43`) is not pursued; decided by plan `wmuu4k` from backlog `e820ka`; guarded by the E-02 test.
  - Depends on: E-03
  - Expected outcome: the spec names all five paths and the guard test.
  - Execution state: performed
- [x] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03, E-04
  - Expected outcome: summary line with 0 failed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The framework-owned `.aw/.gitignore` has ONE contract written in TWO places (template for fresh installs, back-fill list for installed repos); `AwGitignoreLaneTests` exists to force a lane into both ("a lane must be added to BOTH").
- Top-level `.aw/`-relative directory patterns are ANCHORED (`/inbox/`, `/state/`, `/workflow-artifacts/`) because a bare name matches at any depth (measured `/inbox/` incident).
- `check_engine` already treats `.aw/state/` and `.aw/worktrees/` as "gitignored RUNTIME scratch", so the fix makes that assumption true in managed repos.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Inventory of per-machine control state and its ignore coverage (measured at HEAD `cfc7f5c1`, fresh repo after `engine._ensure_aw_gitignore`, plus this repo):

| Path | Writer | Ignored in managed repo | Ignored here |
|---|---|---|---|
| `.aw/state/` (receipts, finalize lock, journals, install state) | `ipd_lifecycle.receipt_dir`, `finalize_lock_path`, `finalize_journal_path` | yes (`.aw/.gitignore` "/state/") | yes |
| `.aw/config/local.json` | config layer | yes ("/config/local.json") | yes |
| `.aw/records/runs/<run-id>/` | `runner_shared.state_root` | yes ("records/runs/") | yes |
| `.aw/workflow-artifacts/` | workflow run scratch | yes ("/workflow-artifacts/") | yes |
| `.aw/worktrees/<lane>/`, `.aw/worktrees/.owners/` | `worktree_lease` (`WORKTREES_SUBDIR`, `OWNERS_SUBDIR`) | NO: `git status` shows `?? .aw/worktrees/abc123/` | yes, root `.gitignore` only |
| `.aw/inbox/`, `records/*/untracked/`, `records/history.jsonl` | human drop / sidecars | yes | yes |

- F-1: the fork defect was RESOLUTION, not LOCATION, and is closed: `ipd_lifecycle.checkout_control_root` docstring "the MAIN worktree's `.aw`, derived from `git rev-parse --git-common-dir`". No concrete harm from in-repo location remains while each path is ignored.
- F-2: the only live harm is the worktrees root in managed repos (table row 5). This repo masks it because its root `.gitignore` carries ".aw/worktrees/"; `diff` of the rendered template against this repo's `.aw/.gitignore` is empty, confirming no `/worktrees/` in the framework file.
- F-3: backlog claim "Every worktree of a checkout now resolves ONE in-repo, gitignored control root" is TRUE for `.aw/state/`; the implied "all control state is gitignored" is FALSE for managed repos (F-2).
- F-4 (MEASURED at review 2026-09-25, re-derive before relying on it): the harm is worse than an untracked directory, because a lane is a REAL git worktree. In a fresh repo with a lane at `.aw/worktrees/lane1`, `git add -A` staged BOTH `.aw/worktrees/.owners/lane1.json` (mode `100644`) AND `.aw/worktrees/lane1` as an EMBEDDED GITLINK at mode `160000`, with git printing its `git rm --cached` submodule hint. So an accidental broad add does not merely track scratch: it commits a phantom submodule pointing at a commit that exists only in that lane's branch, which is unresolvable for anyone who clones. This is the concrete argument for the fix and belongs in the record.
- F-5 (MEASURED at review): the fix WORKS and the probe is reproducible. In a fresh repo after `_ensure_aw_gitignore`, `git check-ignore -q` returns 0 for `.aw/state/x`, `.aw/config/local.json`, `.aw/records/runs/r1/x` and `.aw/workflow-artifacts/wf1/x`, returns NONZERO for `.aw/config/project.json` (correctly tracked), and returns NONZERO for both `.aw/worktrees/lane1` and `.aw/worktrees/.owners/lane1.json`; `git status --porcelain` shows `?? .aw/worktrees/`. Appending a single `/worktrees/` line flips both worktrees paths to IGNORED and empties that status line. So E-03's one-line change is sufficient, and E-02's test is falsifiable in both directions.
- F-6 (MEASURED at review; this is why E-01's `anchored` column was corrected): `engine._ensure_aw_gitignore` carries exactly ONE bare-form repair, `bare_inbox = re.compile(r"(?m)^inbox/[ \t]*$")`, hardcoded to `inbox`. Driving the helper against a pre-existing bare line shows `/worktrees/` -> `['worktrees/']` (unrepaired), `/state/` -> `['state/', '/state/']` and `/workflow-artifacts/` -> `['workflow-artifacts/', '/workflow-artifacts/']` (bare line survives beside the added anchored one). So the LANES `anchored=True` repair branch is satisfiable ONLY by `/inbox/` today, which also explains why `/state/` and `/workflow-artifacts/` have no LANES row despite being anchored in the template. The existing test passes today (`1 passed`), so this is a latent constraint on new rows, not a current failure.
- F-7 (MEASURED at review; this is why E-03's regen command was replaced): `_ensure_aw_gitignore` writes the template ONLY when `not gi.is_file()`. Against this repo, where the file exists, it returned `wrote: False` and left the file byte-identical, so the originally prescribed regen command is a no-op that cannot add the new line. After the engine edit it would take the BACK-FILL branch and append a BARE `/worktrees/` with no comment, leaving the tracked file one line different from the template and failing V-03's own `SAME` assertion. The tracked `.aw/.gitignore` IS byte-identical to the template today (measured: empty `diff`), which is the invariant to preserve.

## Proposed changes (ordered, validatable)

1. Guard tests that fail today (E-01, E-02).
2. Template + back-fill `/worktrees/`, regenerate `.aw/.gitignore` (E-03).
3. Record the decision in spec Section 5 (E-04).
4. Bare suite (E-05).

## Deferred / out of scope (with reason)

- XDG relocation, migration of existing receipts, Windows/XDG-absent fallback, and moving the driver run root (backlog `e820ka` questions 2 to 4): moot under the keep-in-repo decision; revisitable in one function if a future need appears.
  - Carrier-Declined: decided against by OQ-01; no successor work exists to carry.
- Ignore coverage for non-repository records backends (companion/home), where `runner_shared.state_root` follows the records root outside the target: not a target-repo tracking hazard and not measured here.
  - Carrier-Declined: no observed harm; companion ignore policy is owned by spec `20260810-1447-01` Section 5 `companion-untracked`.

## Scope check

- Over-scope: none.
- Under-scope: none; this repo's root `.gitignore` already covers `.aw/worktrees/` (measured: line `.aw/worktrees/`, beside `.aw/state/`, `.aw/config/local.json` and `.aw/workflow-artifacts/`) and is left untouched. That root file is what MASKS the defect here, which is why the probe must be run in a FRESH repo and not in this one.
- Under-scope, RESOLVED IN PLACE at review: E-01's `anchored` column would have made the new row permanently unsatisfiable (F-6) and E-03's regen command could not produce the intended file (F-7). Both are corrected in the items themselves.
- NOTE FOR THE EXECUTOR: this plan's own validation runs inside a repo whose root `.gitignore` already ignores `.aw/worktrees/`, and an isolated lane worktree LIVES at `.aw/worktrees/<lane>`. Neither affects the tests, which build their own temp repos, but do not try to observe the defect by running `git status` in the work repo: it is masked there by construction.

## Required tests / validation

- `tests/test_installer.py::AwGitignoreLaneTests` new row and new end-to-end test, shown failing before E-03 and passing after.
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

- Amend spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 5 (declared in `- Scope-Paths:`). WHY: that section owns the `target-ignored` placement policy and says `config_local` and `state_runtime` MUST be untracked; it is the natural home for the decision that per-machine control state stays target-ignored rather than relocated, and for naming the worktrees root, which it currently omits. The edit adds a policy statement and does not change any existing rule.

## Open questions

### OQ-01: Relocate per-machine control state out of the repository?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Resolution or deferral rationale: NO; keep in-repo and gitignored. Evidence: the `dh0uno` fork is closed by `ipd_lifecycle.checkout_control_root` (resolution fix, not location); every control path except `.aw/worktrees/` is already ignored in a freshly installed repo (Findings table, re-measured at review as F-5), and that one gap is fixed here by a gitignore line rather than a relocation; relocation would add a migration and a Windows/XDG fallback for hygiene only. Because location is decided in one accessor, a later relocation stays a contained change. A maintainer may reverse this at review.
- Carrier-Declined: decided against with no successor work; the one concrete harm the decision leaves is fixed inside this plan (E-03) rather than handed on.

### OQ-02: Should `_ensure_aw_gitignore`'s bare-form REPAIR be generalized beyond `inbox`?

- Blocking: no
- Status: open
- Owner: maintainer
- Finding: F-6
- Resolution or deferral rationale: Recommendation: NOT IN THIS PLAN, and file it rather than widening scope here. Measured (F-6): the repair is one hardcoded `inbox` regex, so three anchored patterns (`/state/`, `/workflow-artifacts/`, and the `/worktrees/` this plan adds) have no repair, and a repo carrying a pre-existing BARE form of any of them keeps the unanchored line that the `/inbox/` incident showed can swallow a tracked lane. That is a REAL latent hazard and it is also strictly pre-existing: it is why `/state/` and `/workflow-artifacts/` carry no LANES row today, and this plan neither creates nor worsens it. Generalizing the regex over the anchored-pattern list is a small change, but it edits a back-fill that runs on EVERY install in EVERY managed repo and would rewrite lines this plan was not asked to touch, so it deserves its own plan with its own before/after evidence. This is `Blocking: no` because the plan is correct and complete without it once E-01 uses `anchored=False`.
- Carrier-Declined: A pre-existing hazard this plan does not introduce, recorded with its measurement and a named remedy; no obligation of this plan's own is being deferred. If the maintainer wants it fixed, `aw backlog new` is the route.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: BEFORE E-03, paste `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_every_lane_is_present_anchored_backfilled_and_idempotent` showing `1 failed` with a message naming the lane worktrees row and "carries 0 pattern line(s)"; AFTER E-03 the same command shows `1 passed`.
  - ALSO paste the new row itself showing `anchored` is `False`, with the one-line reason. A row written `anchored=True` fails the repair branch PERMANENTLY (F-6), so an AFTER run that still fails on "was not repaired" means the column is wrong, not that E-03 is incomplete.
  - Observed evidence: BEFORE E-03: `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_every_lane_is_present_anchored_backfilled_and_idempotent` failed with `1 failed, 92 deselected in 0.86s` (template carries 0 pattern line(s), back-fill produced []). AFTER E-03: `1 passed, 92 deselected in 0.16s`. LANES row: `("the lane worktrees root", "/worktrees/", False, ..., "per-lane git worktrees and their owner records (worktree_lease.WORKTREES_SUBDIR and OWNERS_SUBDIR). Anchored for the /inbox/ reason. anchored=False because _ensure_aw_gitignore implements bare-form repair only for /inbox/ (OQ-02).")`. `anchored` is `False` because `engine._ensure_aw_gitignore` implements bare-form repair only for `/inbox/` (OQ-02).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: BEFORE E-03, paste `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_git_ignores_every_per_machine_control_path` showing `1 failed` whose message names `.aw/worktrees/` paths and no other; AFTER E-03 `1 passed`. The "and no other" half is load-bearing: it is what proves the other four lanes were already covered and that this test is not passing for an unrelated reason.
  - Observed evidence: BEFORE E-03: `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_git_ignores_every_per_machine_control_path` failed with `1 failed, 92 deselected in 0.27s` with `AssertionError: Lists differ: ['.aw/worktrees/lane1/file.txt', '.aw/worktrees/.owners/lane1.json'] != []` naming only the two `.aw/worktrees/` paths and no other. AFTER E-03: `1 passed, 92 deselected in 0.15s`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `git diff -- .aw/.gitignore agent_workflows/engine.py` showing the added commented `/worktrees/` template block, the one added back-fill entry, and the matching added block in `.aw/.gitignore`; then paste `diff <(python3 -c "from agent_workflows import engine as E; print(E._AW_GITIGNORE_TEMPLATE, end='')") .aw/.gitignore && echo SAME` printing `SAME`.
  - IF `SAME` DOES NOT PRINT, the likely cause is the retired regen command (F-7): `_ensure_aw_gitignore` appends a bare line with no comment on an existing file. Write the template verbatim instead, as E-03 now directs; do NOT "fix" the mismatch by deleting the comment from the template.
  - Observed evidence: `git diff -- .aw/.gitignore agent_workflows/engine.py` showed added commented `/worktrees/` block in template and `.aw/.gitignore`, plus back-fill loop entry in `_ensure_aw_gitignore`. `diff <(python3 -c "from agent_workflows import engine as E; print(E._AW_GITIGNORE_TEMPLATE, end='')") .aw/.gitignore && echo SAME` printed `SAME`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `grep -n "worktrees\|wmuu4k\|e820ka" .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the new Section 5 paragraph naming all five paths, `checkout_control_root`, and the guard test.
  - Observed evidence: `grep -n "worktrees\|wmuu4k\|e820ka" .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` -> `93:Per-machine control state (.aw/state/, .aw/config/local.json, .aw/records/runs/, .aw/workflow-artifacts/, .aw/worktrees/) stays IN the target repository and is covered by the framework-owned .aw/.gitignore. Its location is decided in one accessor (ipd_lifecycle.checkout_control_root, driver runs via runner_shared.state_root), so relocation out of the repo (retired 58ha43) is not pursued. Decided by plan wmuu4k from backlog e820ka; guarded by the AwGitignoreLaneTests.test_git_ignores_every_per_machine_control_path guard test.`
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing `N passed` and 0 failed.
  - Observed evidence: bare `python3 -m pytest` -> `1992 passed, 1 skipped, 3 warnings in 31.38s` (0 failed).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`- Status: approved`).

OPEN QUESTIONS: OQ-01 is `resolved` (keep in-repo, gitignored) and is the plan's own deliverable, recorded in the spec by E-04. OQ-02 is `Blocking: no`, records a PRE-EXISTING hazard this plan does not introduce (the `inbox`-only bare-form repair, F-6), and carries a recommendation to file it separately. An executor must NOT widen scope to fix OQ-02 mid-run: it edits a back-fill that runs on every install in every managed repo.

TEST-FIRST IS THE POINT OF THIS PLAN, SO DO NOT REORDER IT. E-01 and E-02 must be written and shown FAILING before E-03 lands; V-01 and V-02 each demand a BEFORE and an AFTER paste. A plan whose only product is a one-line gitignore pattern earns its confidence entirely from the guard tests failing first, so an AFTER-only paste does not satisfy either item.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS: `- Scope-Paths:` is `agent_workflows/engine.py`, `tests/test_installer.py`, `.aw/.gitignore`, and spec `20260810-1447-01`. It is a DECLARATION, not a stop order: an out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a `--scope-ack`. Do not halt over a scope question. DO halt for a genuinely unsafe condition (an unresolvable concurrent-edit conflict in `engine.py` or `tests/test_installer.py`, both high-traffic files). This repo's ROOT `.gitignore` is deliberately OUT of scope and must not be touched.

SPEC EDIT DECLARED: this plan amends `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 5, so both runners will announce it before the run and reconcile it at the end. The spec is `- Status: implemented` and `- Canonical: true`; E-04 ADDS a policy paragraph and must not alter the existing placement vocabulary or the `config_local`/`state_runtime` MUST-be-untracked rule.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*` above, including both the BEFORE-failing and AFTER-passing runs for V-01 and V-02. Never mark a `V-*` from the matching `E-*` checkmark or from memory, and never claim a test pass that was not run.

COMMIT DISCIPLINE: commit only the declared `- Scope-Paths:`, path-scoped, through `aw commit wmuu4k -- <paths>`; never `git add -A`, never `-a`, and never push. `git add -A` is worth avoiding with particular care in THIS plan's subject area: the review measured it staging a lane worktree as a mode-`160000` gitlink (F-4). This is a shared checkout, so run `git diff --cached --name-only` before each commit and unstage anything that is not yours with `git restore --staged <path>`.

LIFECYCLE TRANSITION: after every `V-*` passes and `aw ipd lint --phase pre-transition` conforms, the terminal transition is the RUNNER's in a managed lane and otherwise the executor's via `aw ipd finalize`. Do not hand-roll a `git mv` to `executed/`.

BACKLOG `e820ka` IS NOT CLOSED BY THIS PLAN. `aw ipd finalize` performs no backlog write, so closing it is a follow-up once this plan is in `executed/`. The HANDOFF route is already in place (`- From-Backlog: e820ka`), and measured at review the item carries no `- Blocks-Release:`, so `aw backlog set done e820ka --message "decided by wmuu4k: keep in-repo, gitignored"` will not fail closed.
