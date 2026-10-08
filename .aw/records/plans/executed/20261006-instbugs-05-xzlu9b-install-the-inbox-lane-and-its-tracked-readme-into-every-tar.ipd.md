# IPD: Install the inbox lane and its tracked README into every target

- Date: 2026-10-06
- Kind: child
- Concern: Defect D14 of research report `l6cbbb`, present at HEAD `474b037a9`. A fresh scratch install creates no `.aw/inbox/` and no `.aw/inbox/README.md`, although the managed AGENTS.md block the same install writes has a whole section "The inbox: raw drops awaiting adoption" pointing agents at `.aw/inbox/`, and `aw adopt` reads from it. The downstream user, who knew the lane existed, could not find it and dropped external research into a repo-root `tmp/`. The packaged `_data/.aw/` holds only `system/`, and nothing in the installer writes the README: the engine only adds the `/inbox/` ignore line (`engine._AW_GITIGNORE_TEMPLATE`, back-filled by `engine._ensure_aw_gitignore`). In THIS repository the README exists and is tracked only because it was force-added: `git check-ignore -v --no-index .aw/inbox/README.md` prints `.aw/.gitignore:28:/inbox/` while `git ls-files .aw/inbox` lists it. A directory pattern like `/inbox/` cannot be re-included by a negation, so the README cannot be tracked normally under the current rule.
- Scope: IN: (1) a packaged template `.aw/system/workflows/templates/aw-inbox-README.md` whose content is this repository's `.aw/inbox/README.md` (one source; this repo's copy becomes an installed instance); (2) install (fresh and upgrade) creates `.aw/inbox/` and writes its README with the same no-clobber semantics as the records READMEs, staged and listed; (3) the ignore rule becomes `/inbox/*` followed by `!/inbox/README.md` in the template, and the back-fill rewrites an existing exact `/inbox/` line into the pair, keeping the leading-slash anchoring that protects `records/comms/shared/inbox/`; this repository's own `.aw/.gitignore` is updated the same way; (4) the post-install "next steps" and the `getting-started` workflow name `.aw/inbox/` as where to drop external material for `aw adopt`. OUT: the content of the README beyond what is needed to be target-correct; `aw adopt` itself.
- Scope-Paths: .aw/system/workflows/templates/aw-inbox-README.md, .aw/inbox/README.md, .aw/.gitignore, agent_workflows/engine.py, agent_workflows/cli.py, .aw/system/workflows/getting-started/getting-started.md, tests/test_install_inbox_lane.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: f33nrj
- Set: instbugs
- Order: 5
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: xzlu9b

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: xzlu9b verified (set instbugs, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Reviewed at lane HEAD `01ad8b2ae`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Demonstrated the `/inbox/*` + `!/inbox/README.md` pair in a scratch repo (F-04) and re-measured D14 with a scratch install (F-06). Fixed: README's own gitignore section argues against this change and instructs `git add -f`, now rewritten in E-02 (PR-001); upgrade would leave the README unstaged because the old `/inbox/` rule is still live when the ensurer runs, now ordered in E-03 (PR-002); E-05(c) asserted an inbox count in `--format json` that does not exist (PR-003); ensurer routed through `collect_scaffold_members` so `--diff` and layout gating come for free (PR-004); post-install pointer site named and `cli.py` added to Scope-Paths (PR-005); `- Blocks-Release: next` (PR-006); gate gains honesty rule, scope fence, temp HOME, inbox-safety note and conditional finalize ownership (PR-007).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 05 of Set `instbugs` after reproducing D14 in a scratch target at HEAD `474b037a9` and confirming the force-added README in this repository.

## Goal

Every installed repository has a visible, documented, tracked `.aw/inbox/` README, while anything dropped beside it stays ignored, so the raw-drop lane the installed instructions describe actually exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [x] E-01 Re-measure at the execution HEAD: fresh install into a temp git repo (`AW_NO_REEXEC=1`), then `ls -la .aw/inbox`; in this repository `git ls-files .aw/inbox` and `git check-ignore -v --no-index .aw/inbox/README.md`.
  - Depends on: none
  - Expected outcome: pasted evidence that the target has no inbox and that this repository's README is tracked while matched by an ignore rule. STOP and report if either changed.
  - Execution state: performed

### Task group 2: fix

- [x] E-02 Add `.aw/system/workflows/templates/aw-inbox-README.md` with the content of `.aw/inbox/README.md`, reviewing it for target-correctness (no citation of a file a target lacks; Order 07's check will enforce this), and make `.aw/inbox/README.md` in this repository identical to the template. REWRITE the README's closing section "Why this directory is gitignored" (it currently says the ignore is `/inbox/`, instructs `git add -f .aw/inbox/README.md`, and argues AGAINST narrowing the pattern) so it states the new rule: `/inbox/*` ignores every drop, `!/inbox/README.md` re-includes exactly this one file, and the default for a NEW drop stays IGNORED, so the containment that paragraph defended is preserved (see Findings F-04/F-05). No em or en dashes (user-facing prose).
  - Depends on: E-01
  - Expected outcome: the template exists and ships in the wheel through the existing `.aw/system` force-include; the two files are byte-identical; neither mentions `git add -f` or claims the ignore pattern is `/inbox/`.
  - Execution state: performed

- [x] E-03 Write the README on install through the EXISTING scaffold machinery rather than a bespoke writer: add an `inbox` category to `engine.collect_scaffold_members` mapping `.aw/inbox/README.md` to template `aw-inbox-README.md` (aw layout only; a legacy `.agents/` layout has no inbox and gets nothing), and an `ensure_inbox_readme(plan, use_git, installed, skipped)` modeled on `engine.ensure_docs_readmes` (no-clobber, dry-run aware, `git_add_optional`), called from `engine.install_into_repo` beside the other `ensure_*_readmes` calls (the single shared install chokepoint, before `create_setup_artifacts`). Because `collect_scaffold_members(category=None)` feeds the `--diff` preview in `engine.run`, the preview then shows the README for free. STAGING ORDER HAZARD: on a FRESH install `.aw/.gitignore` does not yet exist when the ensurer runs (it is created later by `create_setup_artifacts`), so `git add` succeeds; on an UPGRADE the old `/inbox/` rule exists, so `git_add_optional` returns False ('ignored by') and the README is written but silently unstaged. So E-04's `_ensure_aw_gitignore` rewrite must run BEFORE this ensurer: call `_ensure_aw_gitignore(repo_root)` immediately before `ensure_inbox_readme` when `.aw/.gitignore` already exists, and if `git_add_optional` still returns False, record the README under `skipped` with the reason rather than `installed`.
  - Depends on: E-02
  - Expected outcome: a fresh install and an upgrade from a `/inbox/`-only `.aw/.gitignore` both list `.aw/inbox/README.md` as added AND have it in `git diff --cached --name-only`; a re-install lists it `[already current]` and changes nothing.
  - Execution state: performed

- [x] E-04 Change the ignore rule: in `engine._AW_GITIGNORE_TEMPLATE` replace `/inbox/` with `/inbox/*` and `!/inbox/README.md` (keeping the explanatory comment and adding one sentence on why a directory pattern cannot be negated); in `engine._ensure_aw_gitignore` (which every install reaches through `write_setup_marker` and `migrate_local_lanes_to_untracked`, and which E-03 now also calls before the inbox ensurer) rewrite an exact `/inbox/` line into the pair, keep the existing bare-`inbox/` repair but make it produce the pair, and add the pair when neither form is present; the presence test must match the two pattern LINES, never the substring in the comment. Return True when it rewrote, so the caller's commit set includes `.aw/.gitignore`. Apply the same edit to this repository's `.aw/.gitignore`. POINTERS: add one line naming `.aw/inbox/` as the drop zone for `aw adopt` to the closing guidance `cli._install_one` prints after a successful install (the block that ends "Changes are STAGED but NOT committed"), and add the same pointer to `.aw/system/workflows/getting-started/getting-started.md` (it mentions the inbox nowhere today).
  - Depends on: E-03
  - Expected outcome: `git check-ignore` reports the README not ignored, `drop.md` and `sub/README.md` inside `.aw/inbox/` ignored, in a fresh target, in an upgraded target that had `/inbox/`, and in this repository; `.aw/records/comms/shared/inbox/.gitkeep` stays not ignored; the `.aw/.gitignore` contains `!/inbox/README.md` exactly once after two installs.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_install_inbox_lane.py` with real installs into temp git repos: (a) fresh: `.aw/inbox/README.md` exists, `git check-ignore -q .aw/inbox/README.md` exits 1, `git check-ignore -q .aw/inbox/some-drop.md` exits 0, `git check-ignore -q .aw/records/comms/shared/inbox/.gitkeep` exits 1, and the README is in `git ls-files` after a `-y` install; (b) upgrade: seed a `.aw/.gitignore` with the old `/inbox/` line, reinstall, assert the same four outcomes and that the file now contains `!/inbox/README.md` once; (c) the human `aw attention` board in a target whose inbox holds only the README prints no `waiting in `.aw/inbox/`` TODO line, and prints `TODO: 1 file waiting` after a drop is added (the count is rendered only in the human board footer, not in `--format json`; measured: `attention.inbox_waiting` has one caller, the footer); (d) a nested `.aw/inbox/sub/README.md` is ignored (the re-include must not leak into subdirectories). Prove (a) can fail by restoring the bare `/inbox/` template line and pasting the failure, and prove (b) can fail by removing the E-03 pre-ensurer `_ensure_aw_gitignore` call and pasting the 'not staged' failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: performed

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
| F-04 | (review) The ignore pair behaves as the plan claims. Scratch repo with `/inbox/*` + `!/inbox/README.md`: `check-ignore` rc `1 .aw/inbox/README.md`, `0 .aw/inbox/drop.md`, `0 .aw/inbox/sub/README.md`, `1 .aw/records/comms/shared/inbox/.gitkeep`; plain `git add .aw/inbox/README.md` succeeds; `git status --ignored` shows `!! .aw/inbox/drop.md`, `!! .aw/inbox/sub/`. Under the old `/inbox/`, `git add .aw/inbox/README.md` prints "The following paths are ignored by one of your .gitignore files: .aw/inbox". | review probe, lane HEAD `01ad8b2ae` |
| F-05 | (review) The current README documents the OPPOSITE design: "Force-adding this single file is preferred over narrowing the ignore pattern (for example to `/inbox/*.md` with an exception), because narrowing would make the default for a NEW drop 'tracked unless something excludes it'". That argument applied to `/inbox/*.md`; `/inbox/*` plus a single-file negation keeps every new drop IGNORED by default (F-04), so the stated objection does not apply, but the README must be rewritten or the shipped template contradicts itself. Origin: plan `lznpv6` E-06 "Decide which and say so", resolved there by force-add. | `.aw/inbox/README.md` section "Why this directory is gitignored"; `.aw/records/plans/executed/20260908-awinbox-01-lznpv6-...ipd.md` E-06 |
| F-06 | (review) Re-measured at lane HEAD: fresh `aw install --preset private-target -y --no-interactive` (temp HOME) leaves no `.aw/inbox/`; install output names `.aw/records/comms/shared/inbox/.gitkeep` but nothing for `.aw/inbox/`. | scratch install |
| F-07 | (review) Staging order: `ensure_*_readmes` run inside `install_into_repo` BEFORE `create_setup_artifacts` writes `.aw/.gitignore`, while an UPGRADED target already has `/inbox/`; `engine.git_add_optional` returns False on 'ignored by', so without a prior gitignore rewrite the upgraded README would be written but never staged. | `engine.install_into_repo` step order; `engine.git_add_optional` |
| F-08 | (review) The `--format json` attention output carries no inbox count; `attention.inbox_waiting` is called only from the human board footer (`TODO: {waiting} {noun} waiting in .aw/inbox/`). The original E-05(c) asserted on JSON and was unsatisfiable. | `grep inbox_waiting agent_workflows/*.py` -> one call site in `attention.py` |

## Proposed changes (ordered, validatable)

1. Template plus identical repo copy, with the gitignore section rewritten to the new rule (E-02).
2. Install-time ensurer through `collect_scaffold_members`, with the gitignore rewrite run first so upgrades stage the README (E-03).
3. Negatable ignore pair with back-fill, plus pointers (E-04).
4. Tests (E-05).

## Deferred / out of scope (with reason)

- `aw uninstall --deep` does not list `.aw/inbox` in `engine._DEEP_CLEANUP_ROOTS`, so after this plan a deep uninstall leaves the installed README behind. Not added here: the inbox may hold unadopted user drops, and deleting a user's raw material is a separate decision.
  - Carrier-Declined: a normal `aw uninstall` already preserves scaffolding by design, and the leftover is one framework-authored README in a user-owned drop zone; removing it is not required for correctness.

## Scope check

- Over-scope: none.
- Under-scope: none after review (F-05 README rewrite, F-07 staging order and the `cli.py` pointer were added).

## Required tests / validation

- `tests/test_install_inbox_lane.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- `getting-started` names the inbox (E-04). The inbox README is rewritten to the new ignore rule (E-02). No spec states the `/inbox/` ignore pattern (measured: `grep -rln "/inbox/" .aw/records/specs/` matches only the comms convention spec, about the comms lane, and a history note in the artifact-organization spec unrelated to this lane), so no spec amendment is needed.

## Open questions

### OQ-01: Should the inbox README be tracked at all, given the inbox is for untrusted text?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes. The README is framework-authored scaffolding, not dropped content, and `attention.py` already calls it "committed scaffolding that documents the lane". Only the drops must stay untracked, which the `/inbox/*` rule preserves (demonstrated F-04, including a nested `sub/README.md` staying ignored). This reverses `lznpv6` E-06's force-add choice; that choice's only stated objection was to a `/inbox/*.md` narrowing that would track new non-matching drops by default, which `/inbox/*` does not do (F-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `ls -la .aw/inbox` failure in a fresh target and the two commands from this repository, with the HEAD sha.
  - Observed evidence:
    Execution starting HEAD: ccc66aadf93c9c9aa168b97ba9879e59ef02c06d

    Fresh target pre-edit:
    $ ls -la .aw/inbox
    ls: cannot access '.aw/inbox': No such file or directory

    This repository pre-edit:
    $ git ls-files .aw/inbox
    .aw/inbox/README.md

    $ git check-ignore -v --no-index .aw/inbox/README.md
    .aw/.gitignore:28:/inbox/	.aw/inbox/README.md
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `cmp .aw/system/workflows/templates/aw-inbox-README.md .aw/inbox/README.md && echo identical`, `grep -n 'add -f\|ignores `/inbox/`' .aw/inbox/README.md` returning nothing, the rewritten gitignore section, and a listing of the built wheel (or `_data` tree) showing the template.
  - Observed evidence:
    $ cmp .aw/system/workflows/templates/aw-inbox-README.md .aw/inbox/README.md && echo identical
    identical

    $ grep -n 'add -f\|ignores `/inbox/`' .aw/inbox/README.md
    (no output, exit code 1)

    Rewritten gitignore section in .aw/inbox/README.md:
    ```markdown
    ## Why this directory is gitignored

    The `.aw/.gitignore` configuration applies `/inbox/*` followed by `!/inbox/README.md`, and that is
    deliberate on two counts. The content is unvetted third-party text that has not passed the leak
    sanitizer, and git history is permanent. And the directory sits OUTSIDE `.aw/records/` so the
    record sweep cannot enumerate a drop as an artifact.
    ```

    Built wheel listing:
    $ python3 -m build --wheel --outdir /tmp/whl_test && unzip -l /tmp/whl_test/*.whl | grep aw-inbox-README.md
    Successfully built agent_workflows-1.3.0rc2.dev8830+gccc66aadf.d20261008-py3-none-any.whl
         3833  2020-02-02 00:00   agent_workflows/_data/.aw/system/workflows/templates/aw-inbox-README.md
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the fresh-install listing line for `.aw/inbox/README.md` plus `git diff --cached --name-only | grep inbox`; the same two for an upgrade over a seeded `/inbox/`-only `.aw/.gitignore`; and a re-install showing `[already current]`.
  - Observed evidence:
    Fresh install:
    [added    ] .aw/inbox/README.md
    $ git diff --cached --name-only | grep inbox
    .aw/inbox/README.md
    .aw/records/comms/shared/inbox/.gitkeep
    .aw/system/workflows/templates/aw-inbox-README.md

    Upgrade over seeded /inbox/-only .aw/.gitignore:
    [added    ] .aw/inbox/README.md
    $ git diff --cached --name-only | grep inbox
    .aw/inbox/README.md
    .aw/records/comms/shared/inbox/.gitkeep
    .aw/system/workflows/templates/aw-inbox-README.md

    Re-install:
    [no change] .aw/inbox/README.md
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the four `git check-ignore` results in a fresh target, in an upgraded target, and in this repository (README not ignored; drop ignored; comms `.gitkeep` not ignored), plus `.aw/inbox/sub/README.md` ignored, `grep -c '^!/inbox/README.md$' .aw/.gitignore` = 1 after a second install, the new post-install pointer line, and the `getting-started` diff.
  - Observed evidence:
    Fresh target:
    .aw/inbox/README.md: rc=0 out=.aw/.gitignore:31:!/inbox/README.md	.aw/inbox/README.md
    .aw/inbox/some-drop.md: rc=0 out=.aw/.gitignore:30:/inbox/*	.aw/inbox/some-drop.md
    .aw/records/comms/shared/inbox/.gitkeep: rc=1 out=
    .aw/inbox/sub/README.md: rc=0 out=.aw/.gitignore:30:/inbox/*	.aw/inbox/sub/README.md
    Count of '!/inbox/README.md' after second install: 1

    Upgraded target:
    .aw/inbox/README.md: rc=0 out=.aw/.gitignore:3:!/inbox/README.md	.aw/inbox/README.md
    .aw/inbox/some-drop.md: rc=0 out=.aw/.gitignore:2:/inbox/*	.aw/inbox/some-drop.md
    .aw/records/comms/shared/inbox/.gitkeep: rc=1 out=
    .aw/inbox/sub/README.md: rc=0 out=.aw/.gitignore:2:/inbox/*	.aw/inbox/sub/README.md
    Count of '!/inbox/README.md' after second install (upgraded): 1

    This repository:
    .aw/inbox/README.md: rc=0 out=.aw/.gitignore:31:!/inbox/README.md	.aw/inbox/README.md
    .aw/inbox/some-drop.md: rc=0 out=.aw/.gitignore:30:/inbox/*	.aw/inbox/some-drop.md
    .aw/records/comms/shared/inbox/.gitkeep: rc=1 out=
    .aw/inbox/sub/README.md: rc=0 out=.aw/.gitignore:30:/inbox/*	.aw/inbox/sub/README.md

    Post-install pointer line:
    Inbox drop zone: drop raw external material into .aw/inbox/ for 'aw adopt'.

    getting-started diff:
    ```diff
    diff --git a/.aw/system/workflows/getting-started/getting-started.md b/.aw/system/workflows/getting-started/getting-started.md
    --- a/.aw/system/workflows/getting-started/getting-started.md
    +++ b/.aw/system/workflows/getting-started/getting-started.md
    @@ -40,7 +40,8 @@ In a few sentences, not a lecture:
     - **Guided/meta** workflows change files with your confirmation (`setup-repo`, `scaffold`);
       `verify` produces evidence; `list-workflows` shows everything.
     - Where things land: assessment/plan proposals as IPDs in `.aw/records/plans/pending/`; durable
    -  run records under `.aw/workflow-artifacts/<workflow>/<RUN_ID>/`.
    +  run records under `.aw/workflow-artifacts/<workflow>/<RUN_ID>/`; raw external research or
    +  notes awaiting adoption in `.aw/inbox/` (adopted with `aw adopt`).

     ## Step 3: Ask the goal and route

    @@ -63,6 +64,7 @@ inside the prompt itself so it is decidable from the prompt alone (GUIDING_PRINC
     - "Write release notes / bump the version" -> `release-notes`
     - "Do a post-mortem" -> `incident`
     - "Add a new workflow/lens/persona to the toolkit" -> `scaffold`
    +- "Adopt external research or raw notes into records" -> drop files into `.aw/inbox/` and run `aw adopt`
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
    Narrowed test run:
    $ python3 -m pytest tests/test_install_inbox_lane.py
    ....                                                                     [100%]
    4 passed in 12.68s

    Mutation failure (a) (restoring bare /inbox/ without negation rewrite):
    FAILED tests/test_install_inbox_lane.py::test_fresh_install_inbox_lane - AssertionError: assert 0 == 1
    where 0 = CompletedProcess(args=['git', 'check-ignore', '-q', '--no-index', '.aw/inbox/README.md'], returncode=0).returncode

    Mutation failure (b) (omitting _ensure_aw_gitignore pre-call before ensure_inbox_readme):
    FAILED tests/test_install_inbox_lane.py::test_upgrade_from_seeded_inbox_gitignore
    AssertionError: assert '.aw/inbox/README.md' in []

    Bare test suite against baseline:
    Baseline: 6693 passed, 2 skipped, 3 warnings in 825.97s
    Current:  6697 passed, 2 skipped, 3 warnings in 355.98s (0:05:55)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in order. Commit only files changed for this plan through `aw commit xzlu9b -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. In THIS repository the README is already tracked, so after the `.aw/.gitignore` edit it stays tracked with no `git rm --cached`; do not touch any other file in this repository's `.aw/inbox/` (it may hold another party's drops). HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize xzlu9b`, never by a hand `git mv`.
