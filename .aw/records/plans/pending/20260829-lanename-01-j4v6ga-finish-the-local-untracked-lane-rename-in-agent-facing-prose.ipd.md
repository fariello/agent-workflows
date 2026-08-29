# IPD: finish the local->untracked lane rename in agent-facing prose, shipped templates, and constant names

- Date: 2026-08-29
- Kind: child
- Concern: The `local/` -> `untracked/` quarantine-lane rename shipped in CODE but not in the PROSE that instructs agents, so `/handoff` still recreates `.aw/records/prompts/local/` on every run and adopter repos are still shipped a README documenting the old name.
- Scope: Retire the last live `local/` lane references in agent-facing workflow instructions, shipped templates/READMEs, and the misleading `*_LOCAL_SUBDIR` constant names. Prose, templates, and identifier renames only; no lane behavior change (the runtime values are already `untracked`). Also delete a hand-written stale `.aw/records/prompts/.gitignore` that reasserts the old convention. Immutable history (executed IPDs, research reports, DECISIONS.md, CHANGELOG) is explicitly NOT rewritten.
- Scope-Paths: .aw/system/workflows/handoff/handoff.md, .aw/system/workflows/handoff/README.md, .aw/system/workflows/whatnext/whatnext.md, .aw/system/workflows/index.md, .aw/system/workflows/templates/prompts-README.md, .aw/records/prompts/README.md, .aw/records/comms/README.md, agent_workflows/engine.py, agent_workflows/comms.py, tests/test_untracked_lane_migration.py, tests/test_dir_readmes.py
- Item-Dependencies: none
- Status: to-review
- Set: lanename
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: j4v6ga
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored as a CORRECTIVE plan after the maintainer observed remnant `local/` references, including a recently re-added `.aw/records/prompts/.gitignore`. Per the execution contract, the already-executed rename IPDs (`20260818-awuntracked-01-c32roo`, and the `awuntrackedfix`/`awgitignore` orders) are NOT edited in place; this new plan closes the post-execution gap.

## Goal

Make the repository's instructions agree with its already-correct code. The lane is named `untracked/` at runtime, but six agent-facing documents still instruct agents to write to `local/`, and the template shipped to adopter repos still documents `local/` as the quarantine lane. Because `.aw/system/workflows/handoff/handoff.md:109` literally tells the agent to `mkdir -p .aw/records/prompts/local`, every `/handoff` run RECREATES the retired lane, which is why the drift keeps reappearing after each migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the regeneration loop

- [ ] E-01 In `.aw/system/workflows/handoff/handoff.md`, replace all five `.aw/records/prompts/local/` references (lines 16, 30, 108, 109, 134) with `.aw/records/prompts/untracked/`, including the `mkdir -p .aw/records/prompts/local` on line 109 which becomes `mkdir -p .aw/records/prompts/untracked`. Do not otherwise reword the workflow.
  - Depends on: none
  - Expected outcome: `grep -c "prompts/local" .aw/system/workflows/handoff/handoff.md` returns 0; `grep -c "prompts/untracked"` returns 5; the `mkdir -p` targets `untracked`.
  - Execution state: pending

### Task group 2: stop shipping the retired name

- [ ] E-02 In BOTH `.aw/system/workflows/templates/prompts-README.md` and `.aw/records/prompts/README.md`, rename the quarantine-lane section and all 7 references each from `local/` to `untracked/` (heading at :44, the D94 note, the bullet at :51, and the `git mv` promotion command at :58-59). Keep the D94 citation and the "the directory you write to IS the privilege level" rationale intact; only the lane NAME changes. Add one sentence stating explicitly that the lane is named `untracked/` and that `local/` is the retired name, so a reader of an older repo can map the two.
  - Depends on: E-01
  - Expected outcome: both files have 0 matches for `local/` as a lane path and document `untracked/`; both mention the retired name exactly once, as history; the two files remain consistent with each other (diff of their lane sections is empty except for paths that legitimately differ).
  - Execution state: pending

### Task group 3: fix the generated-shim source

- [ ] E-03 In `.aw/system/workflows/index.md`, update the `handoff` manifest row (line 41) and the narrative mention (line 219) to say `untracked/`. Then REGENERATE the slash-command shims through the normal installer path so `.opencode/commands/handoff.md:2` and `.claude/commands/handoff.md:2` pick up the corrected `workflow.description`. Do NOT hand-edit either shim.
  - Depends on: E-02
  - Expected outcome: `index.md` has 0 `local/` matches; both shims contain `untracked/` and 0 `local/`; the shim diff shows ONLY the description string changing, proving they were regenerated rather than rewritten.
  - Execution state: pending

### Task group 4: remaining agent-facing prose

- [ ] E-04 Update `.aw/system/workflows/handoff/README.md:6` and `.aw/system/workflows/whatnext/whatnext.md:61` to `untracked/`. Note that `whatnext.md:61` currently names `.aw/records/comms/local/inbox/`, a path that does not exist, so this also fixes a silently-empty instruction.
  - Depends on: none
  - Expected outcome: both files have 0 `local/` matches; the comms inbox path in `whatnext.md` resolves to a directory that exists on disk.
  - Execution state: pending

- [ ] E-05 Update `.aw/records/comms/README.md:9,15` to document `untracked/` as the ephemeral lane, matching what `AGENTS.md` already tells agents (engine.py:1134). Keep the `shared/` half unchanged.
  - Depends on: none
  - Expected outcome: 0 `local/` matches; the README's lane names agree with the installed AGENTS.md block and with the dirs present under `.aw/records/comms/`.
  - Execution state: pending

### Task group 5: names that contradict their values, then remove the stale artifact and guard the invariant

- [ ] E-06 Rename `PROMPTS_LOCAL_SUBDIR` -> `PROMPTS_UNTRACKED_SUBDIR` and `COMMS_LOCAL_SUBDIRS` -> `COMMS_UNTRACKED_SUBDIRS` in `agent_workflows/engine.py` (definitions at :4126, :4182; uses at :5113, :5116) and update every reference repo-wide, including tests. Fix the stale docstring path in `agent_workflows/comms.py:230` (`.agents/comms/local/acks/` -> `untracked`). Values are unchanged, so this is a pure rename.
  - Depends on: none
  - Expected outcome: `grep -rn "LOCAL_SUBDIR" --include=*.py .` returns 0 matches outside `.aw/worktrees/` and `tmp/`; the runtime values are still `"untracked"` and `("inbox","sent","archive","scheduled","acks")`; the full suite passes.
  - Execution state: pending

- [ ] E-07 Delete the untracked `.aw/records/prompts/.gitignore`. Under the canonical `.aw/` layout the lane is ignored by `.aw/.gitignore` (`records/*/untracked/`), no per-lane file is emitted (engine.py:5085-5090), and `migrate_local_lanes_to_untracked` deletes exactly this file (engine.py:5265-5269). Then add a regression guard asserting that no TRACKED, non-historical file instructs an agent to use a `local/` lane: a test that greps the workflow/template/README surface for `prompts/local` or `comms/local` and fails if found, with the historical trees (`.aw/records/plans/**`, `.aw/records/research/**`, `DECISIONS.md`, `CHANGELOG*`) explicitly exempt. The guard MUST be proven to fail on an injected violation.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: the file is gone; the new test passes on the fixed tree AND fails when a `local/` lane reference is injected into any in-scope file (both directions demonstrated); the historical exemption is asserted so the test does not demand rewriting immutable records.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The rename is DONE in code and on disk. `engine.PROMPTS_LOCAL_SUBDIR == "untracked"` (engine.py:4126, value verified at runtime), the emitted template body is `untracked/` (`_PROMPTS_GITIGNORE_TEMPLATE`, engine.py:4127-4133), the comms lane is created at `comms/untracked/<sub>` (engine.py:5117-5119), and on disk `.aw/records/comms/` contains `shared/` + `untracked/` with no `local/`. So this plan must NOT change lane behavior; it aligns names and prose only.
- The canonical `.aw/` layout is ignored by ONE framework-owned `.aw/.gitignore` (`records/*/untracked/`, engine.py:4136-4143). A per-lane `.gitignore` is emitted ONLY for the legacy `.agents/` layout: `create_setup_artifacts` branches on `_canonical_aw` and appends `AW_GITIGNORE_PATH` for canonical vs `{prompts}/.gitignore` for legacy (engine.py:5085-5090). `migrate_local_lanes_to_untracked` additionally DELETES a stale per-lane `.gitignore` under `.aw/records/` (engine.py:5265-5269).
- Therefore the `.aw/records/prompts/.gitignore` currently on disk is doubly wrong: commit `6ebee73` deleted it, and the migration function deletes it on sight. It is UNTRACKED, its exact wording ("`local/` quarantine lane is NEVER committed (DECISIONS D94)") appears in NO template and NO git revision (verified: `git grep -S` finds no such source; a repo-wide grep matches only this one file), so it was HAND-WRITTEN today from the stale prose. It must be deleted, not edited.
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
| F8 | MED | `.aw/records/prompts/.gitignore` (untracked, on disk) | A hand-written file reasserting `local/`, deleted by `6ebee73` and deleted-on-sight by `migrate_local_lanes_to_untracked`. Its wording exists in no template and no git revision. Under the canonical `.aw/` layout no per-lane ignore should exist at all. | `git log --oneline -- <path>` shows the delete; wording is unique to this file |

Root cause: the rename IPDs migrated the MECHANISM (constants, emitted templates, on-disk dirs, a migration function) and the enforcement (`.aw/.gitignore`), but not the INSTRUCTIONS. Nothing in the repo fails when prose and code disagree, so the divergence was invisible to CI and reproduced itself through `/handoff`.

## Proposed changes (ordered, validatable)

1. Fix the self-regenerating source first (F1), since it is the only reference that WRITES to disk.
2. Fix the shipped template and this repo's instance together (F2, F3) so an install cannot reintroduce the old text.
3. Fix the manifest row, then REGENERATE the shims rather than hand-editing them (F4).
4. Fix the remaining agent-facing docs (F5, F6).
5. Rename the misleading constants (F7), mechanical and behavior-free.
6. Delete the stale hand-written ignore file (F8).
7. Add a guard so this specific divergence cannot recur silently.

## Deferred / out of scope (with reason)

- Rewriting immutable history: executed IPDs under `.aw/records/plans/executed/**`, research reports, `DECISIONS.md`, and `CHANGELOG` entries legitimately describe the `local/` era and MUST keep saying `local/`. Roughly 30 files. Editing them would falsify the record; the E-07 guard exempts them explicitly.
- The stale in-repo clones `tmp/awclone/` and `tmp/cutclone/` carry the old `local/` engine template. `tmp/` is gitignored, so they are invisible to `git grep` but NOT to an agent grepping the filesystem, making them a live source of wrong answers. Out of scope here because they are untracked working material belonging to whoever created them (shared-checkout rule); flagged for the maintainer to delete.
- The missing `aw prompts` minting verb (backlog `i97baj`, open, `Blocks-Release: next`). That is the deeper fix: with no tool, agents re-derive the path from prose, which is exactly how this drift propagates. This plan corrects the prose; `i97baj` removes the need to read it.
- Any change to lane BEHAVIOR, the `.aw/.gitignore` patterns, or the `UNTRACKED_PATTERNS` catch-all convention. All already correct.

## Scope check

- Over-scope: none. Every path in Scope-Paths carries at least one finding above, plus the two test files E-06/E-07 must touch.
- Under-scope: the two `tmp/` clones and `i97baj` are named under Deferred with reasons rather than silently dropped.

## Required tests / validation

- `python3 -m pytest -n auto` (default fast subset) and `python3 -m pytest -m "" -n auto` (full, including slow) must pass. NOTE a known-good baseline: 4 tests currently fail in the slow suite (`test_command_surface_declarations`, `test_cli_conformance_matrix` x2, `test_cli` subparser descriptions). These are PRE-EXISTING and unrelated (undeclared CLI parser leaves from concurrent `run_cli` work); verified by stashing unrelated edits and reproducing them on a clean tree. The executor MUST re-establish this baseline before and after, and must not claim them as caused or fixed here.
- `tests/test_dir_readmes.py` and `tests/test_setup_artifacts.py` guard README/artifact shape; both must still pass. `test_setup_artifacts.py:347` asserts the default artifact count is 24, which must NOT change (this plan emits no new artifact).
- `tests/test_untracked_lane_migration.py` must still pass unchanged in BEHAVIOR (it deliberately creates `local/` dirs as migration INPUT, which is correct and must not be renamed away).
- A temp install must generate shims containing `untracked/`, proving E-03 flows through the generator.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec changes. The convention is unchanged; only the lane's name in prose is corrected to match the code that already implements it.
- `.aw/records/prompts/README.md` and `.aw/records/comms/README.md` are themselves documentation being corrected here.
- Consider a `DECISIONS.md` note recording that `untracked/` is the sole lane name and `local/` is retired, so a future reader does not re-derive the old convention. Left to the executor's judgment; if added it must be a NEW numbered decision, not an edit to the existing D94/D81 entries.

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
- Resolution or deferral rationale: NO. `tmp/` is gitignored and its contents belong to another party under the shared-checkout rule, so a test that fails on them would fail for reasons the executor may not fix. The guard scans the TRACKED surface only. The clones are flagged to the maintainer under Deferred instead.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "prompts/local\|prompts/untracked" .aw/system/workflows/handoff/handoff.md` showing 0 `local` and 5 `untracked` hits, and the full line 109 showing `mkdir -p .aw/records/prompts/untracked`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -c "prompts/local" ` for both README files (expect 0 each) and `grep -n "untracked/" ` for both (expect the lane section). Additionally paste a `diff` of the two files' lane sections demonstrating they remain mutually consistent, and the one sentence that names `local/` as retired.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -n "local/" .aw/system/workflows/index.md` (expect no output) and `grep -n "untracked/" .opencode/commands/handoff.md .claude/commands/handoff.md` showing both shims updated. Paste `git diff` for both shims showing ONLY the description string changed, which proves regeneration rather than hand-editing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n "local/" .aw/system/workflows/handoff/README.md .aw/system/workflows/whatnext/whatnext.md` (expect no output), plus `ls -d` of the comms inbox path now named in `whatnext.md` proving it EXISTS (the pre-fix path did not).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "local/\|untracked/" .aw/records/comms/README.md` showing the ephemeral lane is `untracked/`, and the corresponding `AGENTS.md` line showing the two now agree.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -rn "LOCAL_SUBDIR" --include=*.py . | grep -v ".aw/worktrees\|tmp/"` (expect no output), plus a python one-liner printing `PROMPTS_UNTRACKED_SUBDIR` and `COMMS_UNTRACKED_SUBDIRS` showing values UNCHANGED (`untracked`, and the 5-tuple). Paste the `comms.py` docstring line showing the corrected ack path.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: (a) `ls .aw/records/prompts/.gitignore` showing it is absent; (b) the new guard test passing; (c) PROOF OF FALSIFIABILITY: inject a `local/` lane reference into one in-scope file, paste the test FAILING, revert, paste it passing again. A guard that cannot fail is not evidence. (d) paste an assertion that a historical file (e.g. an executed IPD containing `local/`) does NOT trip the guard. (e) WHOLE-PLAN GATE, required here because E-07 is the last item and its guard depends on E-01..E-05: paste actual runner output for `python3 -m pytest -n auto` AND `python3 -m pytest -m "" -n auto`, showing the pass counts and showing the failure set is EXACTLY the 4 pre-existing CLI-surface failures named under Required tests (no new failures, and none of the 4 silently "fixed"); paste `test_setup_artifacts.py` count assertion still at 24; paste a temp-install shim containing `untracked/`; paste `aw check-local-leaks . --agent` clean and `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is a single cohesive concern (finish one rename across the prose surface) and is deliberately NOT split into a Set: the changes are individually trivial, mutually consistent, and must land together or the shipped template and this repo's README disagree. E-03's regeneration step depends on E-02's wording, and E-07's guard can only pass once E-01 through E-05 are done, so serial execution in one pass is correct.

Execution contract: the executor commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never pushes. Before every commit it MUST run `git diff --cached --name-only` and unstage anything it did not modify: this repository is a SHARED CHECKOUT with other agents and humans working concurrently, and at least one concurrent session currently has uncommitted work in `agent_workflows/` and `tests/`. Path-scoping alone is NOT sufficient, since a path-scoped commit still commits what is already staged for those paths.

The executor MUST NOT hand-edit `.opencode/commands/handoff.md` or `.claude/commands/handoff.md` (generated; fix `index.md` and regenerate), MUST NOT rewrite historical records under `.aw/records/plans/executed/**`, `.aw/records/research/**`, `DECISIONS.md`, or `CHANGELOG`, and MUST NOT touch the `tmp/` clones or any other party's uncommitted work.

Post-gate lifecycle: after every `V-*` item is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, transition with `aw ipd finalize` (which owns the plan move to `.aw/records/plans/executed/`). Do not hand-move the file and do not mark this plan executed on the strength of the execution checkmarks alone.
