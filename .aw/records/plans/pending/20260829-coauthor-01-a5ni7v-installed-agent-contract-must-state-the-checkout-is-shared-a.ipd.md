# IPD: Installed agent contract must state the checkout is shared and require verifying the staged set before committing

- Date: 2026-08-29
- Kind: child
- From-Backlog: suugsf
- Concern: An interactive `agy` session committed `bd3fed1` and SWEPT another session's uncommitted `run_viewer.py`/`cli.py` edits into it, with a one-line message that never mentioned the swept work. Root cause: the `AGENTS.md` block installed by `engine.py:1137` (`### Agent execution contract`) says "commit ONLY files you changed... never `git add -A`" but NEVER states that other agents or humans may be working in the same checkout. Verified absent from that block: `concurrent`, `other agent`, `another agent`, `shared checkout`, `unrelated`, `sweep`, `git status`, `staged`. The `## Concurrent Work` warning that DOES say this lives only in the driver prompt (`agy_runipd.py:1573-1579` + `oc` twin), and `host_adapters.py:83` maps the `antigravity` host's pointer file to `AGENTS.md`, so for an interactive session the rule does not exist anywhere it can be read. Second, host-independent gap: nothing tells an agent HOW to check what it is about to commit, so "stage only your files" is unactionable; prose alone demonstrably failed, since the driver prompt already forbade `git add -A` and a sweep still happened.
- Scope: Add a shared-checkout section plus a MANDATORY pre-commit verification step to the INSTALLED `AGENTS.md` block in `engine.py`, so every managed repo receives it on install/update; align both driver prompts (`oc_runipd.py`, `agy_runipd.py`) with the same rule so runner and interactive sessions agree; fix the curly apostrophe in the delivered prompt text; and regenerate this repo's own `AGENTS.md` block from `engine.py` so source and delivered copy do not drift. Documentation/prose only. Does NOT add a pre-commit hook, does NOT change git behavior, and does NOT attempt to attribute file edits to a session (rejected: a hook is local, uncloned, `--no-verify`-skippable, and cannot reliably know which agent edited a file, so it would produce false refusals).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, AGENTS.md, tests/test_shared_checkout_contract.py
- Item-Dependencies: none
- Status: approved
- Set: coauthor
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: a5ni7v
- Approval: 2026-08-29, human ("approved"): Maintainer directed this fix (update the agent-workflows files so it installs).

## Workflow history
- 2026-08-29 approved (aw set, --by-human): Maintainer directed this fix (update the agent-workflows files so it installs).
- 2026-08-29 to-review (aw set): Authored review-ready from backlog suugsf.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the shared-checkout rule reach EVERY agent (not just runner turns) by stating it in the installed `AGENTS.md` contract, and make it actionable by requiring the agent to enumerate the staged set and refuse any path it did not itself modify before committing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the installed contract

- [x] E-01 Add a `### Shared checkout: you are not alone in this repo` section to the installed AGENTS block in `engine.py` (beside `### Agent execution contract`, which begins at `engine.py:1137`). It MUST state: other agents and humans may be working in this same checkout concurrently; uncommitted changes and untracked files you did not create are NOT yours; never revert, stage, commit, or "clean up" another party's work; and if a file you must edit is being changed under you and the changes cannot be safely combined, STOP and report rather than overwriting. Because this block is what `install`/`update` writes into every managed repo, this is the only place the rule reaches a non-runner session.
  - Depends on: none
  - Expected outcome: `engine.agents_managed_block(target_layout="aw")` contains the new heading and the four rules; a test asserts the previously-absent terms (`concurrent`, `another agent`, `staged`) are now present.
  - Execution state: performed
- [x] E-02 Add the MANDATORY verification step to the same installed block: before every commit, run `git diff --cached --name-only` (or `git status --porcelain`) and confirm EVERY staged path is one you personally modified for the task at hand; unstage anything else (`git restore --staged <path>`) rather than committing it. State plainly that a path-scoped `git commit -- <paths>` still commits whatever is already staged for those paths, so scoping the command is NOT by itself sufficient. This closes the gap that made "stage only your files" unactionable.
  - Depends on: E-01
  - Expected outcome: the block names the exact verification command and the unstage remedy; a test asserts `git diff --cached --name-only` appears in the generated block.
  - Execution state: performed

### Task group 2: driver prompt parity

- [x] E-03 Align BOTH driver prompts with the installed contract so a runner turn and an interactive session are told the same thing: extend the existing `## Concurrent Work` section (`agy_runipd.py:1573-1579` and the `oc_runipd.py` twin) with the same verification requirement from E-02, since that section currently contains no `git status`/`git diff --cached` instruction at all.
  - Depends on: E-02
  - Expected outcome: both prompts instruct the agent to verify the staged set before committing; a test asserts the verification command appears in each driver's prompt text.
  - Execution state: performed
- [x] E-04 Replace the curly apostrophe in the delivered prompt text (`agy_runipd.py:1577`, "another agent's") with a plain ASCII apostrophe, matching the repo's plain-ASCII posture for delivered artifacts, and check the `oc` twin for the same character.
  - Depends on: none
  - Expected outcome: no U+2019 remains in either driver's `## Concurrent Work` text; a test asserts the delivered prompt strings are pure ASCII.
  - Execution state: performed

### Task group 3: no drift between source and delivered copy

- [x] E-05 Regenerate this repo's own `AGENTS.md` managed block from `engine.py` so the source of truth and this repo's delivered copy agree (verified they currently differ: generated 8868 chars vs in-repo 9068, because the graduation contract was added to `AGENTS.md` directly). Preserve the hand-authored content that belongs in the block by moving it into `engine.py` first, so regeneration LOSES NOTHING.
  - Depends on: E-01, E-02
  - Expected outcome: this repo's `<!-- aw:block -->...<!-- /aw:block -->` equals `engine.agents_managed_block(target_layout="aw")` exactly, and the graduate/implement/execute contract added earlier is still present (nothing dropped).
  - Execution state: performed

## Project conventions discovered (Step 0)

- The installed agent-facing rules are assembled IN CODE by `engine.agents_managed_block(style, target_layout)` / `agents_managed_sections()` (`engine.py`, contract section at `:1137`) and written into each managed repo's pointer file between `<!-- aw:block -->` markers. Editing a repo's `AGENTS.md` by hand fixes ONE repo; editing `engine.py` fixes every adopter on install/update. `host_adapters.py:761` records the same posture ("AGENTS.md is not hand-edited here").
- `host_adapters.py:78-83` maps each host to its pointer file: `opencode`/`codex`/`kiro`/`antigravity` -> `AGENTS.md`, `gemini_cli` -> `GEMINI.md`, `claude_code` -> `CLAUDE.md`. So the `antigravity` host (the one that swept the work) reads `AGENTS.md`, which is why the installed block is the load-bearing artifact here.
- Both drivers already inject a `## Concurrent Work` prompt section (`agy_runipd.py:1573-1579`; `oc_runipd.py` twin) with the right SPIRIT but no verification step, and it reaches ONLY runner turns.
- VERIFIED the generated block and this repo's copy have already drifted (8868 vs 9068 chars), so E-05 must move hand-added content into `engine.py` rather than regenerate blindly.
- Delivered prose in this repo avoids em/en dashes and should be plain ASCII; the existing prompt text violates that with a curly apostrophe (`agy_runipd.py:1577`).

## Findings

The incident, verified from git and the run ledgers:

| Fact | Evidence |
|---|---|
| the sweeping commit | `bd3fed1` "feat(run_viewer): add pid liveness, runtime, and multi-line run header" |
| it was NOT a runner turn | no `.aw/records/runs/*/state.json` references `bd3fed1` |
| the host reads AGENTS.md | `host_adapters.py:83` maps `antigravity` -> `AGENTS.md` |
| the contract is silent | `concurrent`/`other agent`/`another agent`/`shared checkout`/`unrelated`/`sweep`/`git status`/`staged` all ABSENT from the installed contract block |
| the warning exists elsewhere | `agy_runipd.py:1573-1579`, driver prompt only |
| no verification anywhere | `git status`, `git diff --cached`, `verify` all absent from the `## Concurrent Work` block |

Why prose alone is insufficient but still worth writing: the driver prompt ALREADY says "never use `git add .` or `git add -A`" and a sweep still occurred, which is why E-02 adds an executable CHECK (enumerate the staged set, compare against what you edited) rather than another prohibition. The subtle trap E-02 must name explicitly: a path-scoped `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, so an agent that believes path-scoping protects it can still sweep a co-worker's edits to the same file. That is precisely what happened to `run_viewer.py`.

Why a hook was rejected rather than deferred: a pre-commit hook is local, is not cloned by default, is skippable with `--no-verify`, and above all cannot reliably determine WHICH session edited a file, so it would refuse legitimate commits. The honest enforcement boundary here is an instruction plus a verification command the agent can actually run.

## Proposed changes (ordered, validatable)

1. `engine.py`: new `### Shared checkout` section in the installed AGENTS block.
2. `engine.py`: mandatory staged-set verification step in the same block.
3. `oc_runipd.py` + `agy_runipd.py`: extend `## Concurrent Work` with the verification requirement.
4. `agy_runipd.py` (+ `oc` twin if present): ASCII apostrophe.
5. `AGENTS.md`: regenerate the managed block from `engine.py`, losing no hand-added content.
6. `tests/test_shared_checkout_contract.py`: assert the installed block and both prompts carry the rule and the command, and that delivered prompt text is ASCII.

## Deferred / out of scope (with reason)

- A pre-commit hook that refuses foreign staged paths: REJECTED (not merely deferred). Local, uncloned, `--no-verify`-skippable, and unable to attribute an edit to a session, so it would produce false refusals. Recorded so it is not re-proposed as an easy win.
- Per-agent identity/attribution in commits (e.g. a trailer naming the session): a larger design touching every commit path; file separately if wanted.
- Teaching agents to coordinate (locks, leases) rather than merely avoid: `wtiso`/`worktree_lease` territory, not a documentation fix.
- Changing `GEMINI.md`/`CLAUDE.md` handling: those hosts already resolve their own pointer file via `host_adapters.py`; the block content is shared, so no per-host text is needed.

## Scope check

- Over-scope: none. Prose and its tests only; no git behavior changes and no new hook.
- Under-scope: none. The silent contract (E-01), the missing verification (E-02), prompt parity (E-03), the ASCII defect (E-04), and source/delivered drift (E-05) each have a 1:1 validation item.

## Required tests / validation

- `python -m pytest tests/test_shared_checkout_contract.py -q` passes.
- Assertions are made against the GENERATED block (`engine.agents_managed_block(target_layout="aw")`), not against this repo's `AGENTS.md`, so they prove what ADOPTERS receive.
- A regression assertion pins the specific terms verified absent today (`concurrent`, `another agent`, `staged`, `git diff --cached --name-only`).
- A test asserts this repo's `AGENTS.md` managed block equals the generated block (E-05), so the two cannot drift again.
- `make test-all` remains green.

## Spec / documentation sync

- The installed `AGENTS.md` block is itself the documentation being changed; no separate spec is needed.
- This repo's `AGENTS.md` is regenerated from `engine.py` (E-05) so the source of truth is unambiguous.
- No CHANGELOG entry is claimed here; the release-notes workflow owns that.

## Open questions

### OQ-01: Should the shared-checkout rule be its own section or folded into the existing execution contract?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: its OWN section. The existing `### Agent execution contract` paragraph is already a dense run-on covering commits, test honesty, dash style, review posture, and tagging; appending a fifth concern would bury the rule an agent most needs to see before its first commit. GUIDING_PRINCIPLES P9 (design instructions for the model that will run them) favors a discrete, scannable heading over more prose in a crowded paragraph.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output asserting the GENERATED block (not this repo's file) contains the new heading and each of the four rules, plus pasted before/after term scans showing `concurrent`/`another agent`/`shared checkout` went from ABSENT to PRESENT.
  - Observed evidence: `python3 -m pytest tests/test_shared_checkout_contract.py` -> `19 passed`. Assertions run against `engine.agents_managed_block(target_layout="aw")`, i.e. what ADOPTERS receive, not this repo's file. Term scan before vs after:
    ```
    BEFORE: concurrent MISSING | other agent MISSING | another agent MISSING | shared checkout MISSING
            unrelated MISSING  | sweep MISSING       | git status MISSING    | staged MISSING
    AFTER : CONCURRENTLY PRESENT | another party PRESENT | staged PRESENT | git diff --cached --name-only PRESENT
    ```
    The section and all four rules are present (`SharedCheckoutSectionTests`, 6/6): heading, CONCURRENTLY, "you did not create are NOT yours", the six forbidden verbs (revert/stage/commit/discard/reformat/clean up), and "STOP and report".
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output asserting `git diff --cached --name-only` and the unstage remedy appear in the generated block, and that the block states path-scoping a commit is not by itself sufficient. A prose claim that "verification was added" fails this item.
  - Observed evidence: `VerificationStepTests` 4/4 pass, asserting the generated block contains `git diff --cached --name-only`, `git restore --staged`, `ALREADY STAGED`, and `BEFORE EVERY COMMIT`. The installed text states the trap that caused the incident verbatim:
    ```
    Path-scoping the command is NOT by itself sufficient: `git commit -- <paths>` still commits
    whatever is ALREADY STAGED for those paths, including edits a co-worker made to the same file.
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted test output showing the verification instruction is present in BOTH drivers' `## Concurrent Work` prompt text, plus the actual prompt excerpt from each driver.
  - Observed evidence: `DriverPromptParityTests` 4/4 pass. All FOUR `## Concurrent Work` blocks (two per driver, exec + verifier) now carry the verification step:
    ```
    oc_runipd.py     block1  ascii-clean=True  has-verify=True
    oc_runipd.py     block2  ascii-clean=True  has-verify=True
    agy_runipd.py    block1  ascii-clean=True  has-verify=True
    agy_runipd.py    block2  ascii-clean=True  has-verify=True
    ```
    Also updated the pre-existing `test_concurrent_work_statement_in_prompts` (tests/test_oc_runipd.py), which pinned the exact old prose INCLUDING the curly apostrophe, to assert the required PROPERTIES instead, so a future wording change does not break it for no substantive reason.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted output of an ASCII check over both drivers' concurrent-work prompt strings showing no U+2019 (or any non-ASCII) remains.
  - Observed evidence: the curly apostrophe (U+2019) was present in FOUR delivered prompt blocks (both drivers, both exec and verifier paths):
    ```
    BEFORE: oc_runipd.py non-ascii: {'\u2019'} x2 ; agy_runipd.py non-ascii: {'\u2019'} x2
    AFTER : all four blocks ascii-clean=True
    ```
    Pinned by `test_every_block_is_pure_ascii` and `test_no_curly_apostrophe_remains`, which scan for ANY codepoint > 127 rather than only that character.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted output showing this repo's `<!-- aw:block -->` content EQUALS `engine.agents_managed_block(target_layout="aw")` (they differ today: 8868 vs 9068 chars), plus a grep proving the previously hand-added graduate/implement/execute contract survives the regeneration.
  - Observed evidence: the generated block and this repo's copy had drifted (8868 vs 9068 chars). A diff BEFORE regenerating showed blind regeneration would have REGRESSED three things, so `engine.py` was corrected to reality first rather than overwriting the better text:
    ```
    - repo said `aw index plans`/`aw find plans` (verified: `aw index plans --help` EXISTS)
    + engine said `aw plans` verbs           (verified: `aw plans --help` MISSING -> engine was stale)
    - repo said `aw spec set approved <id6> --by-human`   (correct)
    + engine said `aw specs set --status approved`        (stale)
    - repo documented `graduated`->`active`  (engine did not; drift I introduced earlier)
    + engine said comms/untracked/inbox      (correct; repo said comms/local -> repo was stale here)
    ```
    After fixing `engine.py` the only remaining diff was the intended additions plus the comms correction. Post-regeneration:
    ```
    block == generated: True
    graduation contract (outside block) survived: True
    graduation contract now ALSO in block: True
    ```
    The duplicate outside the block was then replaced with a pointer to the managed block (P8), leaving the `From-Backlog` mechanics paragraph intact. Pinned by `NoDriftTests` (3/3): block equality, no duplicated contract body, and `host_adapters.HOST_POINTER_FILE["antigravity"] == "AGENTS.md"` (the reason the installed block is load-bearing for the observed incident).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
