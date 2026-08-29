# IPD: finish the local->untracked lane rename in agent-facing prose, shipped templates, and constant names

- Date: 2026-08-29
- Kind: child
- Concern: The `local/` -> `untracked/` quarantine-lane rename shipped in CODE but not in the PROSE that instructs agents, so `/handoff` still recreates `.aw/records/prompts/local/` on every run and adopter repos are still shipped a README documenting the old name.
- Scope: Retire the last live `local/` lane references in agent-facing workflow instructions, shipped templates/READMEs, user-facing docs, and the misleading `*_LOCAL_SUBDIR` constant names. Prose, templates, and identifier renames only; no lane behavior change (the runtime values are already `untracked`). Also normalize the stale on-disk `local/` lane and its hand-written `.gitignore` through the EXISTING `aw normalize-lanes` verb rather than a raw delete. Immutable history (executed IPDs, research reports, DECISIONS.md, CHANGELOG) is explicitly NOT rewritten.
- Scope-Paths: .aw/system/workflows/handoff/handoff.md, .aw/system/workflows/handoff/README.md, .aw/system/workflows/whatnext/whatnext.md, .aw/system/workflows/index.md, .aw/system/workflows/templates/prompts-README.md, .aw/records/prompts/README.md, .aw/records/comms/README.md, README.md, ARCHITECTURE.md, tools/README.md, agent_workflows/engine.py, agent_workflows/comms.py, tests/test_untracked_lane_migration.py, tests/test_dir_readmes.py
- Item-Dependencies: none
- Status: approved
- Set: lanename
- Order: 1
- Highest E allocated: 09
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: j4v6ga
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-29 approved (aw set): status set to approved

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored as a CORRECTIVE plan after the maintainer observed remnant `local/` references, including a recently re-added `.aw/records/prompts/.gitignore`. Per the execution contract, the already-executed rename IPDs (`20260818-awuntracked-01-c32roo`, and the `awuntrackedfix`/`awgitignore` orders) are NOT edited in place; this new plan closes the post-execution gap.
- 2026-08-29 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review; APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Raised F8 from MED to BLOCKER after REPRODUCING the exposure (the stale lane's only protection is a hand-written ignore the framework deletes on sight, and it currently shields an unscrubbed handoff draft). Replaced E-07's raw delete with the existing `aw normalize-lanes` verb to preserve that draft, and split the guard out as E-09. Added E-08 for three user-facing docs (`README.md`, `ARCHITECTURE.md`, `tools/README.md`) that were live but unscoped. Corrected the artifact-count claim (25, not 24) and replaced the unverified test baseline with a measured one (1 fast / 5 full failures, not 4 slow-only). Added a hard prohibition on running `aw install .` here after measuring a 157-path, 270-file, auto-staged side effect during this review; also added deprecated aliases for the renamed constants and resolved OQ-03.

## Goal

Make the repository's instructions agree with its already-correct code. The lane is named `untracked/` at runtime, but nine agent-facing and user-facing documents still name `local/`, and the template shipped to adopter repos still documents `local/` as the quarantine lane. Because `.aw/system/workflows/handoff/handoff.md:109` literally tells the agent to `mkdir -p .aw/records/prompts/local`, every `/handoff` run RECREATES the retired lane, which is why the drift keeps reappearing after each migration.

The drift is not merely cosmetic. It has a CONFIDENTIALITY consequence, which is the real reason this plan blocks the release. The guarantee D94 sells is "the directory you write to IS the privilege level": an agent that follows the stale prose writes a raw session handoff, containing exactly the unscrubbed context D94 exists to quarantine, into a lane whose ignore rule is a hand-written file that no installer emits and that the framework's own migration DELETES ON SIGHT (`engine.py:5265-5269`). The moment that file is removed by the normal tooling path, the raw draft becomes a normal untracked file, one `git add -A` away from being committed to a public repo. This was reproduced on this checkout, not reasoned about: with the stale `.gitignore` temporarily moved aside, `git status` reported `?? .aw/records/prompts/local/` (see F8 evidence). So the stale prose does not just use an old name; it routes sensitive content into a lane whose protection is an accident.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the regeneration loop

- [ ] E-01 In `.aw/system/workflows/handoff/handoff.md`, replace all five `.aw/records/prompts/local/` references (lines 16, 30, 108, 109, 134) with `.aw/records/prompts/untracked/`, including the `mkdir -p .aw/records/prompts/local` on line 109 which becomes `mkdir -p .aw/records/prompts/untracked`. Do not otherwise reword the workflow.
  - Depends on: none
  - Expected outcome: `grep -c "prompts/local" .aw/system/workflows/handoff/handoff.md` returns 0; `grep -c "prompts/untracked"` returns 5; the `mkdir -p` targets `untracked`.
  - Execution state: pending

### Task group 2: stop shipping the retired name

- [ ] E-02 In BOTH `.aw/system/workflows/templates/prompts-README.md` and `.aw/records/prompts/README.md`, rename the quarantine-lane section and all 7 references each from `local/` to `untracked/` (the `local/` mention at :10, the heading at :44, the D94 note at :46 and :48, the bullet at :51, and the `git mv` promotion command at :58-59). Keep the D94 citation and the "the directory you write to IS the privilege level" rationale intact; only the lane NAME changes. Add one sentence stating explicitly that the lane is named `untracked/` and that `local/` is the retired name, so a reader of an older repo can map the two. NOTE these two files are currently BYTE-IDENTICAL (`diff` exits 0, verified in review), so the correct execution is to edit one and copy it to the other, and the validation is a `diff` that still exits 0.
  - Depends on: E-01
  - Expected outcome: both files have 0 matches for `local/` as a lane path and document `untracked/`; both mention the retired name exactly once, as history; `diff` of the two files still exits 0 (they remain byte-identical, which is how the installer avoids reintroducing a stale copy).
  - Execution state: pending

### Task group 3: fix the generated-shim source

- [ ] E-03 In `.aw/system/workflows/index.md`, update the `handoff` manifest row (line 41) and the narrative mention (line 219) to say `untracked/`. Then REGENERATE the slash-command shims so `.opencode/commands/handoff.md:2` and `.claude/commands/handoff.md:2` pick up the corrected `workflow.description`. Do NOT hand-edit either shim.

  REGENERATION HAZARD (measured in review, do not skip): running the full `aw install .` in THIS repo to regenerate two shims is NOT a safe surgical action. A review run of `python3 -m agent_workflows install . --yes` produced 157 changed paths, created an entire untracked `.agents/skills/` tree (270 files), added two unrelated `exec-set` shims, rewrote `.aw/system/managed-sections.json` (+810 lines), stripped the trailing newline from `.aw/config/project.json`, AND auto-staged all of it, in a SHARED CHECKOUT with concurrent work present. It also silently ran `migrate_local_lanes_to_untracked` as a side effect. The executor MUST therefore regenerate WITHOUT a whole-repo install: call the shim generator directly for the `handoff` command only (the manifest parse at `engine.py:640-691` plus the shim writer at `engine.py:826-829`), then verify the two shim files are the only changed paths. If no such narrow entry point can be invoked, STOP and report rather than running the full installer; a two-line description fix must not be bought with a 157-path diff.
  - Depends on: E-02
  - Expected outcome: `index.md` has 0 `local/` matches; both shims contain `untracked/` and 0 `local/`; `git status --porcelain` after regeneration shows ONLY the two shim files plus `index.md` as changed (no `.agents/`, no `managed-sections.json`, no `project.json`, no `exec-set` shims, and nothing auto-staged); the shim diff shows ONLY the description string changing, proving they were regenerated rather than rewritten.
  - Execution state: pending

### Task group 4: remaining agent-facing prose

- [ ] E-04 Update `.aw/system/workflows/handoff/README.md:6` and `.aw/system/workflows/whatnext/whatnext.md:61` to `untracked/`. Note that `whatnext.md:61` currently names `.aw/records/comms/local/inbox/`, a path that does not exist, so this also fixes a silently-empty instruction.
  - Depends on: none
  - Expected outcome: both files have 0 `local/` matches; the comms inbox path in `whatnext.md` resolves to a directory that exists on disk.
  - Execution state: pending

- [ ] E-05 Update `.aw/records/comms/README.md:9,15` to document `untracked/` as the ephemeral lane, matching what `AGENTS.md:32` already tells agents (emitted from `engine.py:1134`). Keep the `shared/` half unchanged. NOTE the SHIPPED template `engine._COMMS_README_TEMPLATE` is ALREADY correct (it says `untracked/` at both sites, verified in review by diffing the rendered template against this file), so unlike E-02 this is a one-sided fix: this repo's stale INSTANCE only. Do NOT "fix" the template; it needs no change, and the only other differences (`.agents/comms/` vs `.aw/records/comms/` in the title, `.agents/docs/specs/` vs `.aw/records/specs/`) are legitimate layout differences that must be PRESERVED.
  - Depends on: none
  - Expected outcome: 0 `local/` matches; the README's lane names agree with the installed AGENTS.md block and with the dirs present under `.aw/records/comms/`; a diff of this file against the rendered `_COMMS_README_TEMPLATE` shows ONLY the two legitimate layout-path differences and no lane-name difference.
  - Execution state: pending

- [ ] E-08 Update the three USER-FACING docs the original scope missed, all of which describe the lane to a human evaluating or adopting the toolkit: `README.md:296` (the `.aw/records/` tree listing says `comms/` contains `shared/`, `local/`), `ARCHITECTURE.md:216` (says the installer scaffolds "a gitignored `local/` lane"), and `tools/README.md:28-29` (two `aw agy exec` examples pointing at `.agents/prompts/local/brief.md`). These are the FIRST thing a prospective adopter reads, so they teach the retired name before any workflow file is ever opened. For `tools/README.md` keep the legacy `.agents/` prefix (that example is about the legacy layout) and change only the lane segment to `untracked/`. Keep these dash-free per the prose convention.
  - Depends on: none
  - Expected outcome: `grep -n "prompts/local\|comms/local\|\`local/\`" README.md ARCHITECTURE.md tools/README.md` returns no output; the `.aw/` tree listing in `README.md` names `untracked/`; `tools/README.md` still says `.agents/` (layout preserved) with the lane segment now `untracked/`.
  - Execution state: pending

### Task group 5: names that contradict their values, then normalize the stale artifact and guard the invariant

- [ ] E-06 Rename `PROMPTS_LOCAL_SUBDIR` -> `PROMPTS_UNTRACKED_SUBDIR` and `COMMS_LOCAL_SUBDIRS` -> `COMMS_UNTRACKED_SUBDIRS` in `agent_workflows/engine.py` (definitions at :4126, :4182; uses at :5113, :5116). Fix the stale docstring path in `agent_workflows/comms.py:230` (`.agents/comms/local/acks/` -> `untracked`). Values are unchanged, so this is a pure rename.

  COMPATIBILITY: verified in review that these two names have exactly FOUR references in the whole live tree, all four inside `engine.py` itself (`grep -rn` over `agent_workflows/` + `tests/` + `tools/`; no test and no other module names them), and that `engine.py` declares no `__all__`. So the blast radius is one file. `engine` is nonetheless an importable module of a published package, so a third-party caller could reference the old name. Because that is unverifiable from inside this repo, keep a backward-compatible alias at each old name (`PROMPTS_LOCAL_SUBDIR = PROMPTS_UNTRACKED_SUBDIR`) with a comment naming this IPD and marking it a deprecated alias retained for external callers. That preserves the readability win with zero compatibility risk. If the maintainer prefers a hard rename (see OQ-03), drop the aliases and say so in the workflow history.
  - Depends on: none
  - Expected outcome: `grep -rn "LOCAL_SUBDIR" --include=*.py agent_workflows/ tests/ tools/` matches ONLY the two deprecated-alias lines; the new names resolve; the runtime values are still `"untracked"` and `("inbox","sent","archive","scheduled","acks")` under BOTH the new and the aliased old name; the full suite passes.
  - Execution state: pending

- [ ] E-07 Normalize the stale on-disk lane using the EXISTING verb, not a raw delete: run `aw normalize-lanes` (`python3 -m agent_workflows normalize-lanes`) at the repo root. This is the canonical, idempotent, retroactive entry point for exactly this drift (`cli.py:8244-8256` -> `engine.migrate_local_lanes_to_untracked`), and it does the whole job in the right ORDER: it recursively MERGES `prompts/local/` into `prompts/untracked/` without clobbering (`_merge_tree`, engine.py:5123-5138), then deletes the stale per-lane `.gitignore` (engine.py:5265-5269), then ensures `.aw/.gitignore` carries `records/*/untracked/` (engine.py:5271-5272).

  DO NOT delete the `.gitignore` by hand and DO NOT delete the `local/` directory. As of this review that directory holds a real, unscrubbed session-handoff draft (`20260829-1422-01-session-handoff-run-ledger-defects.md`, 14453 bytes) that is NOT tracked and therefore NOT recoverable from git. `rm` on the ignore file first would leave that draft exposed as a plain untracked file; `rm` on the directory would destroy a colleague's only copy. Reusing the shipped verb preserves the content, keeps the ordering safe, and exercises the very code path that is supposed to prevent this drift (KISS: no new mechanism for a job the tool already does). VERIFY the draft survived, by name and byte size, in `untracked/` before continuing.
  - Depends on: none
  - Expected outcome: `.aw/records/prompts/local/` no longer exists; `.aw/records/prompts/.gitignore` no longer exists; the handoff draft is present at `.aw/records/prompts/untracked/20260829-1422-01-session-handoff-run-ledger-defects.md` with its byte size and checksum unchanged; `git check-ignore -v` on that file now cites `.aw/.gitignore:6:records/*/untracked/` (the framework-owned rule) rather than the hand-written per-lane file; a second `aw normalize-lanes` reports nothing to do (idempotent).
  - Execution state: pending

- [ ] E-09 Add the regression guard that makes this divergence impossible to reintroduce silently: a test asserting that no TRACKED, non-historical file instructs an agent to use a `local/` lane. Scan the tracked surface via `git ls-files` (NOT a filesystem walk, so gitignored working material and the `tmp/` clones are structurally out of scope per OQ-02) for `prompts/local` or `comms/local`, and fail with the offending `path:line`. Exempt the historical trees explicitly: `.aw/records/plans/**`, `.aw/records/research/**`, `.aw/records/prompts/{executed,superseded,not-executed}/**`, `.aw/records/specs/**`, `DECISIONS.md`, `CHANGELOG*`, and `opencode-recovery/**` (verified in review to contain many legitimate historical mentions). Follow the house test style (stdlib `unittest`, as in `tests/test_untracked_lane_migration.py`).

  The guard MUST be proven falsifiable: inject a violation, watch it fail, revert, watch it pass. A guard that cannot fail is not evidence. It must ALSO be proven not to fire on the exempt historical set, so it never pressures a future agent into rewriting immutable records.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-08
  - Expected outcome: the new test passes on the fixed tree; it FAILS when a `local/` lane reference is injected into any in-scope file (both directions demonstrated with pasted output); it does NOT fail with the historical files present, asserted directly (e.g. by confirming a known executed IPD containing `local/` is excluded from the scanned set).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The rename is DONE in code and on disk. `engine.PROMPTS_LOCAL_SUBDIR == "untracked"` (engine.py:4126, value verified at runtime), the emitted template body is `untracked/` (`_PROMPTS_GITIGNORE_TEMPLATE`, engine.py:4127-4133), the comms lane is created at `comms/untracked/<sub>` (engine.py:5117-5119), and on disk `.aw/records/comms/` contains `shared/` + `untracked/` with no `local/`. So this plan must NOT change lane behavior; it aligns names and prose only.
- The canonical `.aw/` layout is ignored by ONE framework-owned `.aw/.gitignore` (`records/*/untracked/`, engine.py:4136-4143). A per-lane `.gitignore` is emitted ONLY for the legacy `.agents/` layout: `create_setup_artifacts` branches on `_canonical_aw` and appends `AW_GITIGNORE_PATH` for canonical vs `{prompts}/.gitignore` for legacy (engine.py:5085-5090). `migrate_local_lanes_to_untracked` additionally DELETES a stale per-lane `.gitignore` under `.aw/records/` (engine.py:5265-5269).
- Therefore the `.aw/records/prompts/.gitignore` currently on disk is doubly wrong: commit `6ebee73` deleted it, and the migration function deletes it on sight. It is UNTRACKED, its exact wording ("`local/` quarantine lane is NEVER committed (DECISIONS D94)") appears in NO template and NO git revision (verified: `git log --all -S` on the distinctive sentence returns nothing), so it was HAND-WRITTEN from the stale prose. It must be retired, not edited.
- There is ALREADY a shipped verb for exactly this drift: `aw normalize-lanes` (`cli.py:8244-8256`), whose help text reads "Rename any prompts/comms 'local/' quarantine lane to 'untracked/' across both layouts, preserving contents ... Retroactive + idempotent; needs no reinstall." Reusing it is the KISS path and avoids inventing a hand-rolled delete for a job the tool already does safely and in the correct order (merge contents first, then drop the stale ignore, then ensure the framework-owned ignore).
- The prompts README template and this repo's instance are currently BYTE-IDENTICAL (`diff` exits 0). The comms README is the OPPOSITE case: its shipped template (`engine._COMMS_README_TEMPLATE`) is already correct and only this repo's instance is stale. The two READMEs therefore need opposite treatment, which is why they are separate E-items.
- `aw install .` in this repo is NOT a surgical operation. Measured in review: 157 changed paths, a new untracked `.agents/skills/` tree (270 files), two unrelated `exec-set` shims, a +810-line rewrite of `.aw/system/managed-sections.json`, a trailing-newline strip on `.aw/config/project.json`, all AUTO-STAGED, plus an implicit `migrate_local_lanes_to_untracked` side effect. Any step that says "regenerate through the installer" must be scoped narrowly or it will sweep a shared checkout.
- Slash-command shims are GENERATED, not authored: `parse_manifest` reads the `index.md` manifest table (engine.py:640-691) and the shim writer emits `description: {workflow.description}` into `.opencode/commands/<cmd>.md` and `.claude/commands/<cmd>.md` (engine.py:826-829). So `.opencode/commands/handoff.md:2` and `.claude/commands/handoff.md:2` must NOT be hand-edited; fixing `index.md:41` and regenerating is the correct action, and hand-editing them would be undone on the next install.
- `.aw/records/prompts/README.md` is this repo's INSTANCE of the shipped template `.aw/system/workflows/templates/prompts-README.md`. Both carry the same 7 `local/` references and must be fixed together, or the next install re-introduces the stale copy.
- Prose convention: user-facing prose in this repo uses no em/en dashes (execution contract). The files in scope are user-facing docs, so keep them dash-free.

## Findings

| # | Sev | File:line | Finding | Evidence |
|---|-----|-----------|---------|----------|
| F1 | HIGH | `.aw/system/workflows/handoff/handoff.md:16,30,108,109,134` | Five instructions tell the agent to write to `.aw/records/prompts/local/`, and :109 says `mkdir -p .aw/records/prompts/local`. This ACTIVELY RECREATES the retired lane on every `/handoff` run, so the drift is self-regenerating rather than a static leftover. | `grep -n "local/"` yields exactly those 5 lines |
| F2 | HIGH | `.aw/system/workflows/templates/prompts-README.md:10,44,46,48,51,58,59` | The template SHIPPED to adopter repos documents `local/` as the quarantine lane, including a `## The local/ quarantine lane (gitignored)` heading and a `git mv .aw/records/prompts/local/<file>` promotion command. New installs are therefore still taught the retired name. | 7 matches; heading at :44 |
| F3 | HIGH | `.aw/records/prompts/README.md:10,44,46,48,51,58,59` | This repo's own copy has the same 7 references. This is the file that misled THIS session into filing a research prompt into the gitignored lane; the README documents `local/` and never mentions `untracked/`, while BOTH dirs exist on disk and both are ignored. | 7 matches; `grep -n untracked` finds none |
| F4 | MED | `.aw/system/workflows/index.md:41,219` | The manifest row and narrative say the handoff writes to the `local/` lane. Because `parse_manifest` feeds `workflow.description` into the generated shims, this single row propagates the stale name into `.opencode/commands/handoff.md:2` and `.claude/commands/handoff.md:2`. | engine.py:640-691, :826-829; both shims carry the identical string |
| F5 | MED | `.aw/system/workflows/handoff/README.md:6`, `.aw/system/workflows/whatnext/whatnext.md:61` | Two more agent-facing docs cite `local/`. `whatnext.md:61` tells the agent to list `.aw/records/comms/local/inbox/`, a path that NO LONGER EXISTS on disk, so that instruction silently finds nothing. | `ls .aw/records/comms/` shows only `README.md`, `shared`, `untracked` |
| F6 | MED | `.aw/records/comms/README.md:9,15` | The comms README still documents `local/` as the ephemeral lane, contradicting `AGENTS.md:32` (installed from engine.py:1134), which correctly directs agents to `comms/untracked/inbox/`. The always-loaded context is right and the README is stale, so an agent that reads the README regresses. | engine.py:1134 emits `untracked/inbox/` |
| F7 | LOW | `agent_workflows/engine.py:4126,4182`, `agent_workflows/comms.py:230` | `PROMPTS_LOCAL_SUBDIR = "untracked"` and `COMMS_LOCAL_SUBDIRS` are names that contradict their own values; `comms.py:230` documents an ack path as `.agents/comms/local/acks/`. A reader (human or agent) sees both names and cannot tell which is current. Naming only, no behavior. | value verified at runtime as `untracked` |
| F8 | **BLOCKER** | `.aw/records/prompts/.gitignore` + `.aw/records/prompts/local/` (both untracked, on disk) | The stale lane's ONLY confidentiality protection is a hand-written ignore file that no installer emits, that commit `6ebee73` deleted, and that the framework's own migration DELETES ON SIGHT (engine.py:5265-5269). It currently shields a real unscrubbed session-handoff draft (14453 bytes). REPRODUCED in review: move that file aside and `git status` immediately reports `?? .aw/records/prompts/local/`, i.e. the raw draft becomes a normal untracked file, one `git add -A` from a public commit. This is the exact failure D94 exists to prevent, and it is live right now, so it is a BLOCKER, not a cleanup. It also means E-07 must NOT be a raw `rm`: the content must be merged forward first. | `git check-ignore -v` cites `.aw/records/prompts/.gitignore:9`; with it moved aside, `git status --porcelain` = `?? .aw/records/prompts/local/`; `git log --all -S` finds the wording in no revision |
| F9 | MED | `README.md:296`, `ARCHITECTURE.md:216`, `tools/README.md:28-29` | Three USER-FACING docs omitted from the original scope still name `local/`: the `.aw/` tree listing a prospective adopter reads first, the architecture description of the comms convention, and two runnable `aw agy exec` examples. A reader is taught the retired name before opening any workflow file, and the `tools/README.md` examples are copy-pasteable into a path that no longer exists. | `git grep -n` on the tracked surface; the plan's Scope-Paths named none of the three |
| F10 | LOW | plan `:124` | The plan asserts `test_setup_artifacts.py:347` "asserts the default artifact count is 24, which must NOT change". The live assertion is `assertEqual(len(created), 25)` (the test NAME still says 24, a pre-existing naming lag). An executor validating against "24" would either chase a nonexistent regression or, worse, "fix" the passing assertion. | `tests/test_setup_artifacts.py:347-350` |

Root cause: the rename IPDs migrated the MECHANISM (constants, emitted templates, on-disk dirs, a migration function) and the enforcement (`.aw/.gitignore`), but not the INSTRUCTIONS. Nothing in the repo fails when prose and code disagree, so the divergence was invisible to CI and reproduced itself through `/handoff`. E-09's guard is the missing feedback loop: it converts "prose and code disagree" from an invisible condition into a test failure.

## Proposed changes (ordered, validatable)

1. Fix the self-regenerating source first (F1), since it is the only reference that WRITES to disk.
2. Fix the shipped template and this repo's instance together (F2, F3) so an install cannot reintroduce the old text.
3. Fix the manifest row, then regenerate the shims NARROWLY rather than hand-editing them or running a full install (F4).
4. Fix the remaining agent-facing docs (F5, F6) and the user-facing docs (F9).
5. Rename the misleading constants behind deprecated aliases (F7), mechanical and behavior-free.
6. Normalize the stale lane and its hand-written ignore through `aw normalize-lanes`, preserving the draft it currently shields (F8).
7. Add a guard so this specific divergence cannot recur silently, and prove it can fail.

Ordering note: E-07 (F8) is the live confidentiality exposure and carries no dependencies, so an executor who must stop early should do E-07 FIRST. It is listed later only to keep the prose fixes contiguous.

## Deferred / out of scope (with reason)

- Rewriting immutable history: executed IPDs under `.aw/records/plans/executed/**`, research reports, `DECISIONS.md`, and `CHANGELOG` entries legitimately describe the `local/` era and MUST keep saying `local/`. Roughly 30 files. Editing them would falsify the record; the E-07 guard exempts them explicitly.
- The stale in-repo clones `tmp/awclone/` and `tmp/cutclone/` carry the old `local/` engine template. `tmp/` is gitignored, so they are invisible to `git grep` but NOT to an agent grepping the filesystem, making them a live source of wrong answers. Out of scope here because they are untracked working material belonging to whoever created them (shared-checkout rule); flagged for the maintainer to delete.
- `opencode-recovery/**` contains many `local/`-era mentions in recovered session transcripts. These are historical records of what was true at the time, so they are exempt from E-09's guard and are not rewritten.
- `test_run_viewer_cli_issues_flag`, one of the pre-existing failures in the measured baseline, fails because it asserts against LIVE repo state. It is already owned by the separate pending plan `testinvoke-02` (`i79rgh`) and must NOT be fixed here; doing so would silently absorb another plan's scope.
- The missing `aw prompts` minting verb (backlog `i97baj`, open, `Blocks-Release: next`). That is the deeper fix: with no tool, agents re-derive the path from prose, which is exactly how this drift propagates. This plan corrects the prose; `i97baj` removes the need to read it.
- Any change to lane BEHAVIOR, the `.aw/.gitignore` patterns, or the `UNTRACKED_PATTERNS` catch-all convention. All already correct.

## Scope check

- Over-scope: none. Every path in Scope-Paths carries at least one finding above, plus the test file E-09 adds.
- Under-scope: closed in review. `README.md`, `ARCHITECTURE.md`, and `tools/README.md` carried live `local/` references but were absent from Scope-Paths; they are now E-08 (F9). The two `tmp/` clones and `i97baj` remain named under Deferred with reasons rather than silently dropped.
- Deliberately NOT in scope though they match a `local/` grep: `.aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md:82` (an `implemented` spec that documents the `local/`-era ack path and already annotates the rename at :28, so it is history) and `agent_workflows/layout_migration.py:501` (a docstring that must keep naming `local/` because it describes migrating FROM it). Renaming either would falsify a record or break a migration comment.

## Required tests / validation

- Invoke the suite BARE (`python3 -m pytest`): `pyproject.toml:122` already sets `addopts = "-q -n auto --dist=worksteal -m 'not slow'"`. Do NOT pass `-n0` (it disables the configured parallelism and is ~5x slower) and do NOT add a second `-q` (it compounds to `-qq` and SUPPRESSES the "N passed" summary line this contract requires you to paste).
- MEASURED BASELINE, re-established in this review on the current tree (paste your own equivalents, before and after):
  - Fast subset, `python3 -m pytest --no-header --tb=no -rN`: `1 failed, 2875 passed, 3 skipped, 4 xfailed in 29.41s`. The single failure is `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag`.
  - Full suite, `python3 -m pytest -m "" -n auto --no-header --tb=no -rN`: `5 failed, 3202 passed, 3 skipped, 4 xfailed in 154.54s`. The five are `test_run_viewer_cli_issues_flag`, `test_command_surface_declarations::test_zero_undeclared_parser_leaves`, `test_cli::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, and `test_cli_conformance_matrix::UndeclaredLeafGuardTests` x2.
  - All five are PRE-EXISTING and unrelated to this plan. `test_run_viewer_cli_issues_flag` asserts against LIVE repo state and is already covered by a separate pending plan (`testinvoke-02` / `i79rgh`); the other four are undeclared CLI parser leaves from concurrent work. The plan's earlier claim of "4 failures, slow suite only" UNDERCOUNTED: one of them also fails in the fast subset, so an executor expecting a green fast run would have been misled. Do not claim any of the five as caused or fixed here; if the set CHANGES, investigate before proceeding.
- `tests/test_dir_readmes.py` and `tests/test_setup_artifacts.py` guard README/artifact shape; both must still pass. The default-artifact-count assertion is `assertEqual(len(created), 25)` at `tests/test_setup_artifacts.py:350` (the test is still NAMED `test_default_setup_artifacts_unchanged_count_24`, a pre-existing naming lag; the number that matters is 25). It must NOT change, since this plan emits no new artifact. Do not "correct" the count to match the stale test name.
- `tests/test_untracked_lane_migration.py` and `tests/test_untracked_lane_both_layouts.py` must still pass unchanged in BEHAVIOR (both deliberately create `local/` dirs as migration INPUT, which is correct and must not be renamed away). E-09's guard scans `git ls-files`, and these fixtures are constructed at runtime in a temp dir, so they cannot trip it.
- A TEMP-repo install (into a throwaway directory, never this repo) must generate a `handoff` shim containing `untracked/`, proving E-03's correction flows through the generator rather than only through the two hand-verified files.
- `aw check-local-leaks . --agent` must report no finding attributable to this plan's paths. NOTE the current tree already reports 2 findings (`home-path`, `handle`) in another agent's pending plan, `20260829-testinvoke-01-uyd3lw...ipd.md:172`; that is NOT this plan's to fix and must not be swept in.
- `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec changes. The convention is unchanged; only the lane's name in prose is corrected to match the code that already implements it.
- `.aw/records/prompts/README.md` and `.aw/records/comms/README.md` are themselves documentation being corrected here.
- Consider a `DECISIONS.md` note recording that `untracked/` is the sole lane name and `local/` is retired, so a future reader does not re-derive the old convention. Left to the executor's judgment; if added it must be a NEW numbered decision, not an edit to the existing D94/D81 entries.
- `.aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md` is `Status: implemented` and already annotates the rename at :28 (`untracked/ ... (was `local/`)`), while :82 still shows the `local/`-era ack path. That is a historical record of an implemented spec, so it is NOT edited here (see Scope check). If the maintainer wants the spec's ack path modernized, that is a separate `aw specs` change, not a prose fix smuggled into this plan.

## Open questions

### OQ-01: Should the retired `local/` name be mentioned at all in the corrected READMEs?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, exactly once, as history. Evidence: the maintainer's stated reason for the rename is that "local" did not convey to the user that the files were untracked, so silently dropping the old name would leave anyone with an older checkout or an older adopter repo unable to map `local/` to `untracked/`. E-02 therefore requires one explicit sentence naming `local/` as retired, while every INSTRUCTION uses `untracked/`.

### OQ-02: Should the E-07 guard also fail on the `tmp/` clones?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. `tmp/` is gitignored and its contents belong to another party under the shared-checkout rule, so a test that fails on them would fail for reasons the executor may not fix. E-09 therefore enumerates via `git ls-files`, which makes the exclusion STRUCTURAL rather than a maintained ignore list. The clones are flagged to the maintainer under Deferred instead.

### OQ-03: Keep deprecated aliases for the renamed constants, or hard-rename?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP ALIASES (the plan now specifies this in E-06). Evidence: the two names have exactly four references in the live tree, all inside `engine.py`, and no test or other module names them (`grep -rn` over `agent_workflows/`, `tests/`, `tools/`), so a hard rename is safe INSIDE the repo. But `engine` is an importable module of a published package and declares no `__all__`, so an external caller cannot be ruled out from here. A two-line alias buys full compatibility at no cost, and the readability goal (a name that does not contradict its value) is achieved either way. The maintainer may prefer a hard rename for cleanliness; that is a judgment call about public surface, not a correctness question, so E-06 states the default and allows the override.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "prompts/local\|prompts/untracked" .aw/system/workflows/handoff/handoff.md` showing 0 `local` and 5 `untracked` hits, and the full line 109 showing `mkdir -p .aw/records/prompts/untracked`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -c "prompts/local" ` for both README files (expect 0 each) and `grep -n "untracked/" ` for both (expect the lane section). Paste `diff .aw/system/workflows/templates/prompts-README.md .aw/records/prompts/README.md; echo "exit=$?"` showing exit 0 (still byte-identical, so the next install cannot reintroduce the stale copy). Paste the one sentence that names `local/` as retired.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -n "local/" .aw/system/workflows/index.md` (expect no output) and `grep -n "untracked/" .opencode/commands/handoff.md .claude/commands/handoff.md` showing both shims updated. Paste `git diff` for both shims showing ONLY the description string changed, which proves regeneration rather than hand-editing. CONTAINMENT EVIDENCE (required, because a full install was measured at 157 paths): paste `git status --porcelain` immediately after regeneration showing no `.agents/` tree, no `managed-sections.json` change, no `project.json` change, no `exec-set` shims, and an EMPTY `git diff --cached --name-only` (nothing auto-staged).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n "local/" .aw/system/workflows/handoff/README.md .aw/system/workflows/whatnext/whatnext.md` (expect no output), plus `ls -d` of the comms inbox path now named in `whatnext.md` proving it EXISTS (the pre-fix path did not).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "local/\|untracked/" .aw/records/comms/README.md` showing the ephemeral lane is `untracked/`, and the corresponding `AGENTS.md:32` line showing the two now agree. Paste a diff of this README against the rendered `engine._COMMS_README_TEMPLATE` showing the ONLY remaining differences are the two legitimate layout paths (`.agents/comms/` vs `.aw/records/comms/`, `.agents/docs/specs/` vs `.aw/records/specs/`) and NO lane-name difference, proving the instance was brought into line with an already-correct template.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -rn "LOCAL_SUBDIR" --include=*.py agent_workflows/ tests/ tools/` showing ONLY the two deprecated-alias lines. Paste a python one-liner printing `PROMPTS_UNTRACKED_SUBDIR`, `COMMS_UNTRACKED_SUBDIRS`, AND the two aliases, showing all four resolve and the values are UNCHANGED (`untracked`, and the 5-tuple `('inbox','sent','archive','scheduled','acks')`). Paste the `comms.py` docstring line showing the corrected ack path.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: (a) paste the `aw normalize-lanes` output; (b) `ls -la .aw/records/prompts/` showing `local/` absent and no `.gitignore`; (c) CONTENT-PRESERVATION PROOF, the point of using the verb instead of `rm`: paste `ls -l` and `md5sum` for `.aw/records/prompts/untracked/20260829-1422-01-session-handoff-run-ledger-defects.md` showing size 14453 and the checksum recorded pre-change, proving the unscrubbed draft was merged forward and not destroyed; (d) paste `git check-ignore -v` on that file showing the rule is now `.aw/.gitignore:6:records/*/untracked/` (framework-owned) rather than a hand-written per-lane file, which is the actual closure of the F8 exposure; (e) paste a second `aw normalize-lanes` run reporting nothing to do (idempotent).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `git grep -n "prompts/local\|comms/local\|\`local/\`" -- README.md ARCHITECTURE.md tools/README.md` (expect no output), plus the corrected `README.md` tree line and the two `tools/README.md` example lines showing the `.agents/` prefix PRESERVED with only the lane segment changed.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: (a) the new guard test passing; (b) PROOF OF FALSIFIABILITY: inject a `local/` lane reference into one in-scope file, paste the test FAILING with the injected `path:line`, revert, paste it passing again. A guard that cannot fail is not evidence. (c) paste evidence that the historical set does NOT trip it (e.g. show a known executed IPD containing `local/` is excluded from the scanned set, and that the test is green with those files present unchanged). (d) WHOLE-PLAN GATE, required here because E-09 depends on E-01..E-05 and E-08: paste actual runner output for BARE `python3 -m pytest` AND `python3 -m pytest -m "" -n auto`, showing the pass counts and showing the failure set is EXACTLY the pre-existing set named under Required tests (1 in the fast subset, 5 in the full suite; no new failures, and none silently "fixed"); paste the `test_setup_artifacts.py` count assertion still reading 25; paste a TEMP-repo install shim containing `untracked/`; paste `aw check-local-leaks . --agent` showing no finding in this plan's paths; paste `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a single cohesive concern (finish one rename across the prose surface) and is deliberately NOT split into a Set: the changes are individually trivial, mutually consistent, and must land together or the shipped template and this repo's README disagree. E-03's regeneration step depends on E-02's wording, and E-09's guard can only pass once E-01 through E-05 and E-08 are done, so serial execution in one pass is correct. Right-sizing was re-checked in review: each E-item now names one deliverable on one surface with one validation surface, and the original E-07 (which bundled a filesystem mutation with authoring a new test) was SPLIT into E-07 (normalize the lane) and E-09 (the guard) because those are independent passes with unrelated evidence.

Execution contract: the executor commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never pushes. Before every commit it MUST run `git diff --cached --name-only` and unstage anything it did not modify: this repository is a SHARED CHECKOUT with other agents and humans working concurrently, and at review time another session had uncommitted work across `.aw/records/backlog/`, `.aw/records/plans/pending/`, and the research indexes. Path-scoping alone is NOT sufficient, since a path-scoped commit still commits what is already staged for those paths.

The executor MUST NOT hand-edit `.opencode/commands/handoff.md` or `.claude/commands/handoff.md` (generated; fix `index.md` and regenerate narrowly), MUST NOT rewrite historical records under `.aw/records/plans/executed/**`, `.aw/records/research/**`, `.aw/records/specs/**`, `opencode-recovery/**`, `DECISIONS.md`, or `CHANGELOG`, and MUST NOT touch the `tmp/` clones or any other party's uncommitted work.

Two hard prohibitions specific to this plan, both learned from a measured incident during its review:

1. DO NOT run `aw install .` (or `python3 -m agent_workflows install .`) against THIS repository to satisfy E-03. It touched 157 paths, created 270 untracked files, rewrote two tracked config/state files, and AUTO-STAGED everything, in a shared checkout. Regenerate the two shims narrowly, or STOP and report.
2. DO NOT `rm` the stale `.gitignore` or the `local/` directory to satisfy E-07. That directory holds an untracked, unrecoverable session-handoff draft belonging to another session. Use `aw normalize-lanes`, which merges content forward before retiring the ignore file, and verify the draft's checksum survived.

Honesty rule (hard MUST): when reporting tests, paste the ACTUAL runner output including the summary line. Never claim a pass you did not run. If the pre-existing failure set changes in either direction, say so explicitly rather than rounding to "tests pass".

Post-gate lifecycle: after every `V-*` item is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, transition with `aw ipd finalize` (which owns the plan move to `.aw/records/plans/executed/`). Do not hand-move the file and do not mark this plan executed on the strength of the execution checkmarks alone.
