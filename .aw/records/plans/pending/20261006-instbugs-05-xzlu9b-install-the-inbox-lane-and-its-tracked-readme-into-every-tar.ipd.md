# IPD: Install the inbox lane and its tracked README into every target

- Date: 2026-10-06
- Kind: child
- Concern: Defect D14 of research report `l6cbbb`, present at HEAD `474b037a9`. A fresh scratch install creates no `.aw/inbox/` and no `.aw/inbox/README.md`, although the managed AGENTS.md block the same install writes has a whole section "The inbox: raw drops awaiting adoption" pointing agents at `.aw/inbox/`, and `aw adopt` reads from it. The downstream user, who knew the lane existed, could not find it and dropped external research into a repo-root `tmp/`. The packaged `_data/.aw/` holds only `system/`, and nothing in the installer writes the README: the engine only adds the `/inbox/` ignore line (`engine._AW_GITIGNORE_TEMPLATE`, back-filled by `engine._ensure_aw_gitignore`). In THIS repository the README exists and is tracked only because it was force-added: `git check-ignore -v --no-index .aw/inbox/README.md` prints `.aw/.gitignore:28:/inbox/` while `git ls-files .aw/inbox` lists it. A directory pattern like `/inbox/` cannot be re-included by a negation, so the README cannot be tracked normally under the current rule.
- Scope: IN: (1) a packaged template `.aw/system/workflows/templates/aw-inbox-README.md` whose content is this repository's `.aw/inbox/README.md` (one source; this repo's copy becomes an installed instance); (2) install (fresh and upgrade) creates `.aw/inbox/` and writes its README with the same no-clobber semantics as the records READMEs, staged and listed; (3) the ignore rule becomes `/inbox/*` followed by `!/inbox/README.md` in the template, and the back-fill rewrites an existing exact `/inbox/` line into the pair, keeping the leading-slash anchoring that protects `records/comms/shared/inbox/`; this repository's own `.aw/.gitignore` is updated the same way; (4) the post-install "next steps" and the `getting-started` workflow name `.aw/inbox/` as where to drop external material for `aw adopt`. OUT: the content of the README beyond what is needed to be target-correct; `aw adopt` itself.
- Scope-Paths: .aw/system/workflows/templates/aw-inbox-README.md, .aw/inbox/README.md, .aw/.gitignore, agent_workflows/engine.py, .aw/system/workflows/getting-started/getting-started.md, tests/test_install_inbox_lane.py
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 5
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: xzlu9b

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 05 of Set `instbugs` after reproducing D14 in a scratch target at HEAD `474b037a9` and confirming the force-added README in this repository.

## Goal

Every installed repository has a visible, documented, tracked `.aw/inbox/` README, while anything dropped beside it stays ignored, so the raw-drop lane the installed instructions describe actually exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: fresh install into a temp git repo (`AW_NO_REEXEC=1`), then `ls -la .aw/inbox`; in this repository `git ls-files .aw/inbox` and `git check-ignore -v --no-index .aw/inbox/README.md`.
  - Depends on: none
  - Expected outcome: pasted evidence that the target has no inbox and that this repository's README is tracked while matched by an ignore rule. STOP and report if either changed.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Add `.aw/system/workflows/templates/aw-inbox-README.md` with the content of `.aw/inbox/README.md`, reviewing it for target-correctness (no citation of a file a target lacks; Order 07's check will enforce this), and make `.aw/inbox/README.md` in this repository identical to the template.
  - Depends on: E-01
  - Expected outcome: the template exists and ships in the wheel through the existing `.aw/system` force-include; the two files are byte-identical.
  - Execution state: pending

- [ ] E-03 Write the README on install: add an ensurer beside `engine.ensure_docs_readmes` (called in both install paths, before `create_setup_artifacts`, per the canonical step order) that creates `.aw/inbox/` and writes `README.md` from the template when absent, appends it to `installed` (or `skipped` when present and unchanged), and stages it.
  - Depends on: E-02
  - Expected outcome: a fresh install lists `.aw/inbox/README.md` as added and stages it; a re-install leaves it untouched.
  - Execution state: pending

- [ ] E-04 Change the ignore rule: in `engine._AW_GITIGNORE_TEMPLATE` replace `/inbox/` with `/inbox/*` and `!/inbox/README.md` (keeping the explanatory comment and adding one sentence on why a directory pattern cannot be negated); in `engine._ensure_aw_gitignore` rewrite an exact `/inbox/` line into the pair and add the pair when neither form is present; apply the same edit to this repository's `.aw/.gitignore`. Add `.aw/inbox/` to the post-install next-steps text and to `getting-started` as the drop zone for `aw adopt`.
  - Depends on: E-03
  - Expected outcome: `git check-ignore` reports the README not ignored and any other file in `.aw/inbox/` ignored, in a fresh target, in an upgraded target that had `/inbox/`, and in this repository; `.aw/records/comms/shared/inbox/.gitkeep` stays tracked.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_inbox_lane.py` with real installs into temp git repos: (a) fresh: `.aw/inbox/README.md` exists, `git check-ignore -q .aw/inbox/README.md` exits 1, `git check-ignore -q .aw/inbox/some-drop.md` exits 0, `git check-ignore -q .aw/records/comms/shared/inbox/.gitkeep` exits 1, and the README is in `git ls-files` after a `-y` install; (b) upgrade: seed a `.aw/.gitignore` with the old `/inbox/` line, reinstall, assert the same four outcomes and that the file now contains `!/inbox/README.md` once; (c) `aw attention --format json` in a target whose inbox holds only the README reports no waiting inbox drops, and reports one after a drop is added. Prove (a) can fail by restoring the bare `/inbox/` template line and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Records READMEs are installed from `.aw/system/workflows/templates/*-README.md` by the `ensure_*_readmes` family in `engine.py`, no-clobber, and appear in the install listing.
- Every `.aw/.gitignore` pattern is ANCHORED with a leading slash because an unanchored `inbox/` once swallowed the tracked `records/comms/shared/inbox/` lane (template comment beginning "ANCHORED with a leading slash so it matches ONLY `.aw/inbox/`").
- `attention.py` already excludes the inbox's own `README.md` and `.gitkeep` from the waiting-drops count ("`.aw/inbox/README.md` is committed scaffolding that documents the lane").
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | No inbox after a fresh install. | scratch target: `.aw/inbox` absent from `find` output; `aw adopt` worked there only after a manual `mkdir -p .aw/inbox` |
| F-02 | This repo's README is force-tracked inside an ignored directory. | `git ls-files .aw/inbox` -> `.aw/inbox/README.md`; `git check-ignore -v --no-index .aw/inbox/README.md` -> `.aw/.gitignore:28:/inbox/` |
| F-03 | The installed AGENTS.md block describes the lane. | scratch `AGENTS.md` line 35 mentions `.aw/inbox/` five times |

## Proposed changes (ordered, validatable)

1. Template plus identical repo copy (E-02).
2. Install-time ensurer (E-03).
3. Negatable ignore pair with back-fill, plus pointers (E-04).
4. Tests (E-05).

## Deferred / out of scope (with reason)

- none.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `tests/test_install_inbox_lane.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- `getting-started` names the inbox (E-04). No spec states the `/inbox/` ignore pattern (measured: `grep -rln "/inbox/" .aw/records/specs/` matches only the comms convention spec, about the comms lane, and a history note in the artifact-organization spec unrelated to this lane), so no spec amendment is needed.

## Open questions

### OQ-01: Should the inbox README be tracked at all, given the inbox is for untrusted text?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes. The README is framework-authored scaffolding, not dropped content, and `attention.py` already calls it "committed scaffolding that documents the lane". Only the drops must stay untracked, which the `/inbox/*` rule preserves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `ls -la .aw/inbox` failure in a fresh target and the two commands from this repository, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `cmp .aw/system/workflows/templates/aw-inbox-README.md .aw/inbox/README.md && echo identical` and a listing of the built wheel (or `_data` tree) showing the template.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the fresh-install listing line for `.aw/inbox/README.md` and a re-install showing it unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the four `git check-ignore` results in a fresh target, in an upgraded target, and in this repository (README not ignored; drop ignored; comms `.gitkeep` not ignored), plus the new next-steps line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit xzlu9b -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed xzlu9b`.
