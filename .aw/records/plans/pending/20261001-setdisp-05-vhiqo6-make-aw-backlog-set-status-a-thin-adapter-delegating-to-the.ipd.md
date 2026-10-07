# IPD: Make aw backlog set status a thin adapter delegating to the shared status set engine

- Date: 2026-10-01
- Kind: child
- Concern: `aw backlog set` is the original subject of backlog `fcnz1r` and the harder of the two migrations. `backlog.run_set` re-implements transition validation, the metadata write (via a full `_strip_metadata_and_history` plus `_render_item` round trip rather than the shared engine's line-by-line rewrite), relocation (via `atomic_write` plus `unlink`, which git sees as a delete plus an untracked file where the shared engine stages a single `git mv` rename), history assembly, and the sidecar append. It carries `--gate-dir`, which `runner_shared.close_backlog_item` depends on and which exists on no other verb. It also still contains a dead read of a nonexistent `apply` flag in its dry-run guard. Three release-blocking defects (`43p53n`, `mawwlc`, and the gate default) were each fixed by duplicating behavior into this function, and two more bypasses were measured on its sibling path while authoring this Set, so this is the function whose removal from the dispatch fork actually closes the recurring class.
- Scope: IN: reduce `backlog.run_set` to an argument-normalizing adapter delegating to `status_set.run_set_command`, preserving its name and callable signature and keeping `--gate-dir` working as an engine parameter; adopt the shared engine's `git mv` relocation per spec `wy9aru` 4.2; adopt the shared engine's ambiguous-selector refusal per 4.5; carry the backlog-only validations into the shared engine per 4.7; verify `runner_shared.close_backlog_item` still works. OUT, each with a reason recorded under "Deferred": the specs path (child 04, which must land first); every axis `wy9aru` Section 7 assigns elsewhere, each with its own carrier; closing any of the carriers whose defects this migration incidentally removes, except where the plan's own evidence proves the fix complete.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_backlog_set_adapter.py, CHANGELOG.md
- Item-Dependencies: executed:m94eht
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- From-Spec: wy9aru
- Set: setdisp
- Order: 5
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vhiqo6

## Workflow history
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The bare suite pytest after the final child compared by name against baseline

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r` under spec `wy9aru`. This is the Set's terminal child and the one that actually closes the recurring class for the verb `fcnz1r` names. It inherits child 04's sidecar ruling (`wy9aru` OQ-1) rather than re-deciding it. The two engines were read in full at HEAD `ec857565a`; the base suite measured bare (`3512 passed, 2 skipped`).
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave `aw backlog set` with ONE implementation of transition validation, the metadata write and
relocation, reached by both spellings, so that the next release-gated gate added to it cannot be
bypassed by choosing the other spelling, which is what happened three times before this Set.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: carry the backlog-only validations into the shared engine

- [ ] E-01 Carry the UNSAFE-DESCRIPTIVE refusals into the shared engine. `backlog.run_set` refuses an unsafe `--message` via `_refuse_unsafe_descriptive(..., bound_length=False)` and an unsafe `--gate-ref` with `bound_length=True`; the shared engine validates neither, so the positional spelling accepts a control-character-bearing message into an artifact's permanent history.

    PRESERVE THE TWO DIFFERENT LENGTH POLICIES EXACTLY. `--message` is unbounded and `--gate-ref` is bounded, and that asymmetry is deliberate: a history message is prose and a gate ref is an identifier. Collapsing them to one policy would either truncate legitimate prose or admit an unbounded identifier.

    APPLY THE REFUSAL TO EVERY RECORD TYPE, not to backlog only, and state why in the code: an unsafe message is unsafe in a plan's history exactly as in a backlog item's, and the shared engine writes history for all of them. If applying it broadly breaks an existing test, that test is asserting that an unsafe value is accepted somewhere; report it rather than narrowing the fix to make it pass.
  - Depends on: none
  - Expected outcome: an unsafe `--message` is refused on both spellings for backlog items and for every other record type the shared engine serves; an unsafe `--gate-ref` is refused with the bounded-length policy; a legitimate long prose message is still accepted.
  - Execution state: pending

- [ ] E-02 Carry the ENUM VALIDATION of `--work-kind` and `--priority` into the shared engine. `backlog.run_set` validates both against its vocabularies and exits 2 before any resolution; the shared engine performs no function-level validation and relies on argparse `choices` alone, so a direct call (and `aw ipd set`, whose own flags are declared with `choices`) can write an out-of-vocabulary value.

    DERIVE THE VOCABULARIES, NEVER RE-LIST THEM. `backlog.PRIORITIES` and `backlog.KINDS` already exist and are already imported by the shared engine for other purposes; a second hardcoded copy is the exact defect GUIDING_PRINCIPLES P8 names and that `ipd_schema`'s own comment records having been bitten by when `graduated` was added to the backlog status vocabulary and a duplicated set went stale.

    NOTE THIS ASYMMETRY IS NOT CLI-REACHABLE and say so where you test it: argparse `choices` rejects an invalid value before dispatch, so the function-level hole is observable only via a direct call. That is still an outcome assertion (return code plus written file), so GUIDING_PRINCIPLES P16 holds.
  - Depends on: none
  - Expected outcome: a direct call with an invalid `--work-kind` or `--priority` is refused with a nonzero exit and writes nothing, on both paths; the vocabularies are derived from `backlog.PRIORITIES`/`backlog.KINDS` with no second copy; valid values still write.
  - Execution state: pending

### Task group 2: the delegation

- [ ] E-03 Make `--gate-dir` an engine parameter, keeping `runner_shared.close_backlog_item` working. Today `--gate-dir` is declared on `aw backlog set` only and read only by `backlog.run_set`, which validates it as a project root and evaluates the release-gate close predicate against it while writing to `repo_root`. The shared engine always evaluates against `repo_root`.

    THIS FLAG CANNOT BE DROPPED AND THE REASON IS IN THE CODE: `runner_shared.close_backlog_item` documents that it uses the `--status` spelling specifically "because only it honors `--gate-dir`", so dropping it breaks the runner's own backlog-close path. `BacklogGateDirSplitTests` plus `test_backlog_set_declared_flag_surface_matches_parser` pin both the behavior and the DECLARATION, so the flag must remain declared on `aw backlog set` as well as honored.

    PER `wy9aru` 4.4, THE ENGINE TAKES AN OPTIONAL GATE ROOT DEFAULTING TO THE REPO ROOT, and the flag stays declared on `aw backlog set` only, because that is the only verb where it is meaningful. Do not add it to `aw set` or `aw ipd set`; `wy9aru` C5 asks for convergence only where a flag is MEANINGFUL, and a gate root on a plan setter is not.
  - Depends on: none
  - Expected outcome: `aw backlog set <item> --status done --gate-dir <other-root>` evaluates the close predicate against the other root and writes to the repo root, exactly as today; `BacklogGateDirSplitTests` and `test_backlog_set_declared_flag_surface_matches_parser` pass unchanged; `runner_shared.close_backlog_item` is driven end to end and works.
  - Execution state: pending

- [ ] E-04 Reduce `backlog.run_set` to an adapter delegating to `status_set.run_set_command` with `scoped_type="backlog"`, KEEPING ITS NAME AND CALLABLE SIGNATURE (spec `wy9aru` S2). It must accept both the `path` attribute its direct callers set and the `args` list `cli.main` supplies, as `cli.main` mutates `args.path` before calling.

    THREE AXES FLIP HERE AND EACH IS A DELIBERATE RULING, NOT A SIDE EFFECT. State each in the evidence with its before and after.

    (1) RELOCATION BECOMES A SINGLE STAGED RENAME (`wy9aru` 4.2). `backlog.run_set`'s `atomic_write` plus `unlink` makes git see a delete plus an untracked file; the shared engine stages one `git mv`. This is not a style preference: `status_set`'s own comment records that it USED to do the write-then-unlink and changed BECAUSE git saw two changes, and `test_staged_rename_moves_and_duplicate_prevention` exists because that shape produced 36 duplicate ids in a measured incident. Verify the porcelain output changes from a delete plus untracked file to a single `R` line.

    (2) THE HISTORY WRITER CHANGES, AND WITH IT THE CLOCK, THE LABEL AND THE DEDUP. The shared engine stamps UTC where `backlog._reattach_history` stamps the local date; it consults `same_status_message_is_duplicate` where `run_set` consults nothing; and its label is the target status or `same-status`. These are three axes with three separate owners (`2wae2x`/`fnb8pl`/`lq2w86`, `r74211`, `jbipfa`), and this delegation RESOLVES all three for this path as a consequence of the ruling in `wy9aru` 4.6. MEASURE each before and after and record it. Do NOT close those carriers from here unless the measured evidence proves the fix COMPLETE across every writer each item names; a partial fix closed as done is exactly the false record the close-legitimacy gate exists to prevent.

    (3) AMBIGUOUS SELECTORS NOW REFUSE (`wy9aru` 4.5). `backlog.run_set` acts on `res.paths[0]` when a selector matches many and says nothing, which is a silent wrong-target write; the shared engine refuses unless `--force`. Replacing a silent partial action with a refusal raises the floor, which is what `wy9aru` C2 requires, but it IS a behavior change for any caller that relied on the first-match behavior. Search for one before assuming none exists.

    THE DEAD `apply` READ DISAPPEARS WITH THIS FUNCTION. `backlog.run_set`'s dry-run guard reads `not getattr(args, "apply", True)` and `--apply` is not declared on `aw backlog set`; that dead read is the residue of release-gated item `19lmbe`, whose symptom was already repaired. Deleting the guard removes it, so E-06 must decide whether `19lmbe` can be closed with evidence or must stay open, and must NOT close it silently.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `backlog.run_set` contains no transition validation, no metadata render, no relocation and no history assembly of its own; both spellings produce identical observable results on every axis child 02's harness pins; the three flipped axes measured before and after; every existing direct caller still works.
  - Execution state: pending

### Task group 3: prove it, and reconcile the carriers honestly

- [ ] E-05 Author `tests/test_backlog_set_adapter.py` and re-run child 02's differential harness. The harness is the primary evidence: every backlog AGREEMENT assertion must still pass unchanged. FLIP the expected-difference assertions this plan closes, naming each individually with its old and new value: the relocation shape (c), the sidecar row (d) if the ruling makes both sides agree, and the multi-selector behavior (e).

    The new module covers what the harness does not: that `backlog.run_set` is still callable with each hand-built `Namespace` shape its existing tests use; that `--gate-dir` still splits the gate root from the write root; that `runner_shared.close_backlog_item` still closes an item end to end; and that a `git mv` relocation appears as a single `R` in porcelain.

    RUN THE THREE RETROSPECTIVE PARITY FILES EXPLICITLY AND PASTE EACH: `tests/test_backlog_positional_close_gate.py` (nineteen tests), `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`. Each exists because an asymmetry on that axis caused a release-blocking defect, so they are the regression surface that matters most here. A failure in any of them means this migration reintroduced one of the three defects the Set exists to prevent.

    NO TEST MAY READ PRODUCTION SOURCE with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Pass `--no-commit` on every CLI invocation.
  - Depends on: E-04
  - Expected outcome: every backlog agreement assertion in the harness passing unchanged; the flipped expected-difference assertions named with old and new values; the three retrospective parity files each passing with output pasted; the new module's cases passing.
  - Execution state: pending

- [ ] E-06 Reconcile the carriers whose defects this migration removes, and record the user-visible change. For EACH of `19lmbe` (the dead `apply` read, release-gated), `2wae2x`/`fnb8pl`/`lq2w86` (the clock), `r74211` (the same-status dedup) and `jbipfa`'s label axis, state explicitly whether this migration COMPLETELY satisfies the item as the item itself defines its scope, and close it with cited evidence ONLY where it does.

    THE DEFAULT IS NOT TO CLOSE, and the reason is mechanical rather than cautious. Several of these items name EVERY writer, not only `backlog.run_set`: the clock items name five local-clock call sites in `backlog.py`, of which this migration removes only the one inside `run_set`; `backlog.run_note`, `_render_item`'s created line and `set_records.close_on_answer` still read the local clock afterwards. Closing such an item would assert a repository-wide fix that did not happen. `19lmbe` is the likeliest genuine close (its subject is the dry-run guard that ceases to exist), and it is RELEASE-GATED, so closing it must go through `aw backlog set done <item> --evidence <this plan's executed path>` rather than by clearing the gate, and only after this plan is in `executed/` so the citation resolves.

    The `CHANGELOG.md` entry names what a USER observes: a backlog item's status change is now recorded as a single file rename in git rather than a delete plus a new file; an ambiguous selector is now refused instead of silently acting on one match; and the history record now carries the same date and label whichever spelling was used. Write no em or en dashes (user-facing prose, `AGENTS.md`), and do not describe the delegation.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: a per-item verdict for all six named carriers, each stating COMPLETE or PARTIAL against the item's own scope with the measurement supporting it; closes performed only for the COMPLETE ones, via the evidence route, with pasted output; one CHANGELOG entry naming the three user-visible changes, with no em or en dash.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Unification is proven by identical observable behavior across both spellings, never by asserting that one implementation exists.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- A release-blocking backlog item CANNOT be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF, SATISFIED with a resolvable in-tree citation, or explicitly DE-GATED. E-06 uses SATISFIED where it closes anything, which is why those closes run after this plan reaches `executed/`.
- DERIVE A VOCABULARY, NEVER RE-LIST IT (GUIDING_PRINCIPLES P8). `ipd_schema`'s own comment records that a second hardcoded copy of the backlog status set made `state:backlog:graduated:<id6>` unparseable when `graduated` was added, which is why E-02 derives from `backlog.PRIORITIES`/`backlog.KINDS`.
- The inline history block's boundary is a measured subtlety documented in `backlog._prior_history_records`: the block ends at the first line that is neither blank nor a column-zero `- ` bullet, because an unbounded scan once promoted five indented prose-quoted example lines into an item's provenance. Read history through that helper or `attention._history_section_lines`.

## Findings

Established by reading `backlog.run_set` and the shared engine in full at HEAD `ec857565a`.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE SET'S THESIS) | Three release-blocking defects were each fixed by duplicating behavior into `backlog.run_set` or its sibling: `43p53n` (gate-field clearing, whose `status_set` comment records the fix was "unreachable" from the positional form), `gatefollows`/`vsgd48` (the gate default, wired into BOTH paths deliberately), `mawwlc`/`47ttnv` (the close predicate, which the positional spelling skipped at exit 0). Two more were MEASURED while authoring this Set (`h4fiwa`, `fv4b6s`). | **FIVE INSTANCES OF ONE CLASS, ALL ON THIS FORK, AND EVERY PRIOR FIX LEFT THE FORK INTACT.** This child is the one that removes the mechanism for the verb `fcnz1r` names. It is also why its regression surface is the three retrospective parity files rather than the new harness alone: a failure there means the migration reintroduced one of the three defects. |
| F-02 | HIGH (DATA-LOSS PRECEDENT) | `status_set.apply_status_change`'s comment records that it USED to `atomic_write` then `unlink` and that git saw that as TWO changes; `tests/test_git_commit_helper.py::test_staged_rename_moves_and_duplicate_prevention` asserts the porcelain line starts with `R` and its comment block records a measured 36-duplicate-id incident. `backlog.run_set` still does `atomic_write` then `unlink`. | **THE RELOCATION DIFFERENCE IS NOT COSMETIC: ONE SIDE HAS A PINNED REGRESSION TEST AND A RECORDED DATA-LOSS INCIDENT, AND THE OTHER IS THE SHAPE THAT CAUSED IT.** `wy9aru` 4.2 rules `git mv` canonical on exactly this evidence. Migrating this path is therefore a defect fix wearing a refactor's clothes, which is worth stating so a reviewer does not treat the porcelain change as incidental churn. |
| F-03 | HIGH (CARRIER DISCIPLINE) | The clock items name FIVE local-clock call sites in `backlog.py`; this migration removes only the one reached through `run_set`. `backlog.run_note`, `_render_item`'s created line and `set_records.close_on_answer` still read the local clock afterwards. | **MOST OF THE CARRIERS THIS MIGRATION TOUCHES ARE ONLY PARTIALLY SATISFIED BY IT, SO THE DEFAULT MUST BE NOT TO CLOSE.** `AGENTS.md`'s close-legitimacy rule exists because closing a release-gated item without the gate being satisfied is a false record. E-06 therefore requires a per-item COMPLETE-or-PARTIAL verdict measured against the ITEM's own scope, not against this plan's diff. |
| F-04 | MEDIUM (RUNNER DEPENDENCY) | `runner_shared.close_backlog_item` builds argv with an explicit `--status done` and documents choosing that spelling "because only it honors `--gate-dir`". `BacklogGateDirSplitTests` (five tests) plus `test_backlog_set_declared_flag_surface_matches_parser` pin the behavior and the declaration. | **THE RUNNER'S OWN BACKLOG-CLOSE PATH DEPENDS ON THE SPELLING THIS PLAN MIGRATES**, so the adapter is not optional and `--gate-dir` must survive as both a declaration and a behavior. E-03 makes it an engine parameter and E-05 drives `close_backlog_item` end to end rather than inferring it still works. |
| F-05 | MEDIUM (SILENT WRONG TARGET) | `backlog.run_set` on a multi-match selector acts on `res.paths[0]`, documented as "act on the first deterministically". The shared engine refuses an ambiguous selector unless `--force`. | **TODAY ONE SPELLING SILENTLY WRITES TO AN ARBITRARY MATCH**, which is worse than a refusal and is the strongest argument for `wy9aru` 4.5's widening: the migration replaces a silent partial action with a refusal, raising the floor `wy9aru` C2 defines. It IS a behavior change for a caller relying on first-match, so E-04 requires searching for one. |
| F-06 | MEDIUM (DEAD READ) | `backlog.run_set`'s dry-run guard reads `not getattr(args, "apply", True)`, and `--apply` is not declared on `aw backlog set`. Item `19lmbe` (`open`, release-gated) is the carrier; its symptom was already repaired, leaving the dead read. | **THE DEAD READ DISAPPEARS WITH THE FUNCTION, SO THIS MIGRATION PLAUSIBLY COMPLETES A RELEASE-GATED ITEM.** `19lmbe` is the likeliest genuine close among the carriers, because its subject IS the guard that ceases to exist. E-06 must verify that against the item's own text and close it through the evidence route, never silently. |
| F-07 | MEDIUM (THREE AXES AT ONCE) | Delegation replaces `backlog._reattach_history` with the shared engine's writer, changing the clock (local to UTC), the label (`set` to the target status or `same-status`) and the dedup (none to `same_status_message_is_duplicate`). | **ONE CHANGE FLIPS THREE SEPARATELY-OWNED AXES SIMULTANEOUSLY**, which is the single most likely place for this plan to be reviewed as having smuggled in other people's work. E-04 therefore requires measuring each before and after and recording it, and E-06 requires a per-item verdict. The axes are resolved for THIS PATH by `wy9aru` 4.6; the ITEMS remain open unless proven complete. |
| F-08 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **THE BASE IS GREEN AT THIS HEAD AND THAT IS TIME-DEPENDENT**: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` is red whenever local and UTC dates differ, and this plan makes both spellings use UTC, which should make it time-INDEPENDENT. Note that as an expected improvement and verify it under both timezones. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/status_set.py`: the unsafe-descriptive refusals for `--message` and `--gate-ref`, with their two different length policies (E-01).
2. `agent_workflows/status_set.py`: function-level enum validation of `--work-kind`/`--priority`, derived from `backlog.PRIORITIES`/`backlog.KINDS` (E-02).
3. `agent_workflows/status_set.py`: an optional gate root parameter, so `--gate-dir` survives (E-03).
4. `agent_workflows/backlog.py` + `agent_workflows/cli.py`: `backlog.run_set` becomes an argument-normalizing adapter delegating to the shared engine (E-04).
5. `tests/test_backlog_set_adapter.py`: the adapter's own cases; plus child 02's harness re-run with its flipped expected-difference assertions named, and the three retrospective parity files run explicitly (E-05).
6. `CHANGELOG.md`: one entry naming the three user-visible changes; per-carrier verdicts, with closes only where COMPLETE (E-06).

## Deferred / out of scope (with reason)

- THE SPECS PATH IS NOT MIGRATED HERE. Spec `wy9aru` S4 requires the migration to be incremental and per-verb, each with its harness green before the next starts, and child 04 does specs first because it is the simpler path (no `--gate-dir`, no `_render_item` round trip, no relocation divergence). This plan depends on it having executed.
  - Carrier: m94eht
- THE CLOCK CARRIERS ARE ADVANCED, NOT CLOSED, unless E-06's measurement proves otherwise (F-03). They name every writer; this migration fixes the one reached through `run_set`, leaving `backlog.run_note`, `_render_item`'s created line and `set_records.close_on_answer` on the local clock.
  - Carrier: 2wae2x
- THE SAME-STATUS DEDUP AND THE HISTORY LABEL are resolved for this path as a consequence of adopting the shared writer, but their items name behavior beyond it. E-06 gives each a measured COMPLETE-or-PARTIAL verdict rather than assuming either.
  - Carrier: r74211
- THE BACKLOG TRANSITION TABLE IS NOT DESIGNED HERE. `t1gbwg` observes that NEITHER path validates a transition ORDER and that no `BACKLOG_TRANSITIONS` constant exists. That is a vocabulary design question; this migration's contribution is leaving ONE enforcement site for it to land in instead of two, which is exactly the benefit it confers.
  - Carrier: t1gbwg
- THE AUDIT OF ITEMS ALREADY CLOSED THROUGH THE UNGATED SPELLING is untouched. It is a report over committed history, explicitly "AN AUDIT, NOT A BACKFILL", and no code change reaches it.
  - Carrier: mbjuv5
- `aw prompts set` IS NOT REGISTERED OR REMOVED. Dispatched in `cli.main` and advertised in help but rejected by the parser; fixing it is a scope decision unrelated to backlog items.
  - Carrier: 68sur3
- `--gate-dir` IS NOT ADDED TO ANY OTHER VERB. `wy9aru` C5 asks for flag convergence only where a flag is MEANINGFUL, and a gate root on a plan or prompt setter is not. It stays declared on `aw backlog set` alone.
  - Carrier-Declined: not a defect; the flag is verb-specific by design and `wy9aru` 4.4 rules it stays where it is

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-01, E-02, E-03), `agent_workflows/backlog.py` (E-04), `agent_workflows/cli.py` (E-04), `tests/test_backlog_set_adapter.py` (E-05), `CHANGELOG.md` (E-06).
- Under-scope: E-05 flips assertions in `tests/test_set_dispatch_parity.py`, which child 02 authors and which is not declared here, to avoid a scope-reconciliation conflict over another plan's file; declare it at execution if the finalize gate requires it and record the widening in the transition message, which this note authorizes. E-01's broad application of the unsafe-descriptive refusal may require repairing a test asserting that an unsafe value is accepted; the path is not knowable at authoring time (F-01 establishes the risk, not its target), so declare it at execution if it materializes. E-06 writes to backlog items under `.aw/records/backlog/` through `aw backlog set`, a tooled lifecycle transition rather than a hand edit. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, not counts (F-08).
- `tests/test_set_dispatch_parity.py` (child 02's harness) run alone under BOTH the machine's local timezone and `TZ=UTC`, with every backlog AGREEMENT assertion passing UNCHANGED. A changed agreement assertion is a regression unless this plan named it in advance.
- THE THREE RETROSPECTIVE PARITY FILES, run individually and pasted: `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py`, and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`. These are the surfaces that caught the three release-blocking defects; a failure means this migration reintroduced one.
- `tests/test_backlog_handoff_close.py` (including `BacklogGateDirSplitTests` and the declared-flag-surface test), `tests/test_backlog.py`, `tests/test_history_provenance.py` and `tests/test_git_commit_helper.py`, each run individually with its result pasted.
- `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` run under BOTH timezones: it is red at base for part of each day, and this plan should make it time-INDEPENDENT. Report both runs.
- The new `tests/test_backlog_set_adapter.py` run alone with `-o addopts=""`, every case named, including the end-to-end `runner_shared.close_backlog_item` drive and the single-`R`-rename porcelain assertion.
- `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0, and `AW_NO_REEXEC=1 aw check release-gates` pasted, since E-06 may close a release-gated item.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET plus any expected change from a carrier E-06 legitimately closed. Re-derive before and after. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing. Per `wy9aru` S5, no commit may both unify a path and fix an axis Section 7 defers.

## Spec / documentation sync

Spec `wy9aru` (`to-review`) governs this Set and is NOT edited by this child: it implements 4.2 (the
`git mv` relocation), 4.4 (`--gate-dir` as a parameter), 4.5 (the ambiguous-selector refusal), 4.6
(inherit the record shape) and 4.7 (union the refusals), and decides nothing on the spec's behalf.

NO SPEC AMENDMENT IS OWED BY THIS CHILD, and the reason is worth stating because its sibling owes one.
The `1525-02` R2 amendment (the sidecar writer's site) is carried by child 04 (`m94eht`), which lands
first and amends it there. By the time this plan runs, R2 already describes the shared engine as the
writer, so migrating the second verb onto that engine conforms to the amended text without changing it.
If child 04's amendment somehow did not land, STOP and report rather than amending the spec here: the
amendment and the behavior must travel together (`wy9aru` S5), and splitting them across two plans is
how a spec comes to describe a routing that does not exist.

`CHANGELOG.md` records the three user-visible changes (E-06). No other user-facing documentation
describes `backlog.run_set`'s internals.

## Open questions

### OQ-01: does anything rely on `backlog.run_set`'s current first-match behavior for an ambiguous selector?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: F-05 establishes the behavior change: the migration replaces "act on `res.paths[0]` silently" with "refuse unless `--force`". That raises the floor `wy9aru` C2 defines, so the design does not change either way; the question is only whether an in-tree caller (notably `runner_shared.close_backlog_item`, the hosts, or a workflow body) passes a selector that can match several and relies on the first. Answerable by searching those callers at execution time. If one exists, it must pass `--force` or a unique selector, and that fix belongs in the same change.

### OQ-02: does this migration COMPLETELY satisfy release-gated item `19lmbe`, or only partially?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: F-06 establishes that `19lmbe`'s subject is the dry-run guard's dead `apply` read, and that the guard ceases to exist when `run_set` becomes an adapter, which makes this the likeliest genuine close among the six carriers. But the item is RELEASE-GATED, so closing it wrongly writes a false record, and the verdict must be measured against the ITEM's own text rather than against this plan's diff. E-06 requires a COMPLETE-or-PARTIAL verdict with the measurement, and a close only via `aw backlog set done --evidence` after this plan reaches `executed/`. Non-blocking because either verdict has a defined action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted rc and the file read back for an unsafe `--message` on BOTH spellings showing refusal and no write; the same for an unsafe `--gate-ref`; a legitimate long prose message accepted; a demonstration that the refusal applies to a non-backlog record type too; and, if any existing test broke, its name with the explanation rather than a narrowed fix.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted rc and the file read back for a direct call with an invalid `--work-kind` and with an invalid `--priority`, both refused with nothing written; valid values shown writing; and a statement that the vocabularies are derived from `backlog.PRIORITIES`/`backlog.KINDS` with the derivation quoted, not re-listed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output of `aw backlog set <item> --status done --gate-dir <other-root>` showing the predicate evaluated against the other root and the write landing in the repo root; pasted results for `BacklogGateDirSplitTests` and `test_backlog_set_declared_flag_surface_matches_parser`; and pasted evidence of `runner_shared.close_backlog_item` driven end to end successfully.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `git status --porcelain` after a status change through BOTH spellings, each showing a single `R` rename line (the before state, a delete plus untracked file, measured first for contrast); the three flipped axes (clock, label, dedup) each measured before and after with the records pasted; the ambiguous-selector refusal demonstrated; the answer to OQ-01 with the search that produced it; and pasted proof that every existing direct caller of `backlog.run_set` still works.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted harness run under both the local timezone and `TZ=UTC` with every backlog agreement assertion passing UNCHANGED; the flipped expected-difference assertions named with old and new values; pasted individual results for the three retrospective parity files; pasted result for `test_release_exempt_setter_roundtrip_and_parity` under BOTH timezones showing it now time-independent; and pasted results for the new adapter module.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: a per-item COMPLETE-or-PARTIAL verdict for all six carriers (`19lmbe`, `2wae2x`, `fnb8pl`, `lq2w86`, `r74211`, and `jbipfa`'s label axis), each with the measurement supporting it against the item's own scope; pasted `aw backlog set done ... --evidence` output for each item closed, showing the SATISFIED route rather than a cleared gate; pasted `aw check release-gates`; the `CHANGELOG.md` hunk diffed; and a grep over that hunk for em and en dashes returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It is the Set's TERMINAL child and depends on child 04 (`m94eht`) having EXECUTED, which in
turn is gated on spec `wy9aru` OQ-1 (the sidecar ruling, owned by the maintainer). It therefore cannot
run before that question is answered, and it inherits the answer rather than re-deciding it.

It is also the child with the widest blast radius: it flips three separately-owned axes at once (F-07)
and changes the git shape of every backlog status transition (F-02). Review should concentrate there,
and on E-06's carrier verdicts, where the failure mode is closing a release-gated item that this
migration only partly satisfied.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any widening declared at execution time, through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for
every test claim; a claim of success without pasted output is a contract violation regardless of
whether the tests passed. Verify the staged set with `git diff --cached --name-only` before committing,
and re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index
that you never staged.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. E-06's carrier closes run AFTER that move, because each evidence
citation must resolve. The orchestrator `63zo2f` owns the disposition of the backlog item `fcnz1r`
itself; do not set it from here.
