# IPD: Make aw backlog set status a thin adapter delegating to the shared status set engine

- Date: 2026-10-01
- Kind: child
- Concern: `aw backlog set` is the original subject of backlog `fcnz1r` and the harder of the two migrations. `backlog.run_set` re-implements transition validation, the metadata write (via a full `_strip_metadata_and_history` plus `_render_item` round trip rather than the shared engine's line-by-line rewrite), relocation (via `atomic_write` plus `unlink`, which git sees as a delete plus an untracked file where the shared engine stages a single `git mv` rename), history assembly, and the sidecar append. It carries `--gate-dir`, which `runner_shared.close_backlog_item` depends on and which exists on no other verb. It also still contains a dead read of a nonexistent `apply` flag in its dry-run guard. Three release-blocking defects (`43p53n`, `mawwlc`, and the gate default) were each fixed by duplicating behavior into this function, and two more bypasses were measured on its sibling path while authoring this Set, so this is the function whose removal from the dispatch fork actually closes the recurring class.
- Scope: IN: reduce `backlog.run_set` to an argument-normalizing adapter delegating to `status_set.run_set_command`, preserving its name and callable signature and keeping `--gate-dir` and the lane-carrier override working as engine parameters and the `(aw backlog)` actor preserved; adopt the shared engine's `git mv` relocation per spec `wy9aru` 4.2; adopt the shared engine's selector semantics per 4.5 (a setid acts on every match; an ambiguous substring refuses); carry the backlog-only validations the engine still lacks (`--work-kind`/`--priority` enum, `--gate-dir`, the lane-carrier pair) into the shared engine per 4.7, confirming those `4gwgo3` already carried; verify `runner_shared.close_backlog_item` still works. OUT, each with a reason recorded under "Deferred": the specs path (child 04, which must land first); every axis `wy9aru` Section 7 assigns elsewhere, each with its own carrier; closing any of the carriers whose defects this migration incidentally removes, except where the plan's own evidence proves the fix complete.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_backlog_set_adapter.py, CHANGELOG.md
- Item-Dependencies: executed:m94eht
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- From-Spec: wy9aru
- Set: setdisp
- Order: 5
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vhiqo6
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed
- 2026-10-07 /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (all fixed; record `.aw/records/reviews/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.review.md`). Execution remains gated on `m94eht` executing, which is gated on `wy9aru` OQ-1 (BLOCKING, maintainer).
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

- [ ] E-01 CONFIRM, DO NOT RE-IMPLEMENT, the UNSAFE-DESCRIPTIVE refusals in the shared engine. CORRECTED AT REVIEW 2026-10-07: the premise that the shared engine "validates neither" is false at HEAD `072b6f640`. `status_set.run_set_command` already loops over `--message` (`bound_length=False`), `--actor`, `--gate-ref`, `--gate-summary`, `--blocks-release` and `--gate-kind` (all bounded) under the comment "IPD 4gwgo3 E-02, E-03", for EVERY record type, before resolving anything. MEASURED: `aw backlog set done aaa111 --message 'a\nb' --yes --no-commit` is rc 2 `FAIL aw set: --message must not contain embedded newlines`, file untouched. Perform NO production edit for this item: re-measure both spellings for an unsafe `--message`, an unsafe `--gate-ref`, a long legitimate message, and one non-backlog type, and record the result. If any case does NOT refuse, that is a regression of `4gwgo3` to fix by consuming `_refuse_unsafe_descriptive`, never a second copy. The one remaining difference is the message PREFIX (`aw backlog set:` versus `aw set:`), which E-07 decides. The original authoring text follows for context. `backlog.run_set` refuses an unsafe `--message` via `_refuse_unsafe_descriptive(..., bound_length=False)` and an unsafe `--gate-ref` with `bound_length=True`.

    PRESERVE THE TWO DIFFERENT LENGTH POLICIES EXACTLY. `--message` is unbounded and `--gate-ref` is bounded, and that asymmetry is deliberate: a history message is prose and a gate ref is an identifier. Collapsing them to one policy would either truncate legitimate prose or admit an unbounded identifier.

    APPLY THE REFUSAL TO EVERY RECORD TYPE, not to backlog only, and state why in the code: an unsafe message is unsafe in a plan's history exactly as in a backlog item's, and the shared engine writes history for all of them. If applying it broadly breaks an existing test, that test is asserting that an unsafe value is accepted somewhere; report it rather than narrowing the fix to make it pass.
  - Depends on: none
  - Expected outcome: an unsafe `--message` is refused on both spellings for backlog items and for one other record type, with no production edit made by this item; an unsafe `--gate-ref` is refused with the bounded-length policy; a legitimate long prose message is still accepted; the evidence names `4gwgo3` as the installing plan.
  - Execution state: pending

- [ ] E-02 Carry the ENUM VALIDATION of `--work-kind` and `--priority` into the shared engine. `backlog.run_set` validates both against its vocabularies and exits 2 before any resolution; the shared engine performs no function-level validation and relies on argparse `choices` alone, so a direct call (and `aw ipd set`, whose own flags are declared with `choices`) can write an out-of-vocabulary value. CONFIRMED AT REVIEW: `status_set.run_set_command(["done", "aaa111"], scoped_type="backlog", repo_root=<tmp>, args=Namespace(work_kind="bogus", ...))` is rc 0 and writes `- Work-Kind: bogus`; the same with `priority="bogus"` writes `- Priority: bogus`.

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
    THE RUNNER PASSES TWO MORE FLAGS THE ENGINE DOES NOT READ (found at review). `runner_shared.close_backlog_item` builds argv with `--gate-dir` AND `--lane-carrier-ref`/`--lane-carrier-path` (which override the lane's one finalized carrier during the gate evaluation), and `backlog.run_set` validates that the two are given together and passes them to the close predicate. `status_set` reads neither. Carry them as engine parameters beside the gate root, with the paired-flag refusal preserved, or delegation silently drops the override the runner's isolated-turn close depends on.
  - Expected outcome: `aw backlog set <item> --status done --gate-dir <other-root>` evaluates the close predicate against the other root and writes to the repo root, exactly as today; `--lane-carrier-ref`/`--lane-carrier-path` reach the predicate after delegation and the one-without-the-other refusal still fires; `BacklogGateDirSplitTests` and `test_backlog_set_declared_flag_surface_matches_parser` pass unchanged; `runner_shared.close_backlog_item` is driven end to end and works.
  - Execution state: pending

- [ ] E-07 SPIKE, BEFORE THE ADAPTER: measure every observable the delegation would change, and decide each one. Added at review (`.aw/records/reviews/20261001-setdisp-05-vhiqo6-make-aw-backlog-set-status-a-thin-adapter-delegating-to-the.review.md`, round 1), mirroring sibling `m94eht` E-07.

    (a) THE RECORDED ACTOR. `backlog._reattach_history` writes `(aw backlog)`; the shared engine writes `(aw set)` unless `args.actor` is set (MEASURED: status spelling `- 2026-10-07 done (aw backlog): m`, positional `- 2026-10-07 done (aw set): m`). 52 assertions in 12 test modules pin `(aw backlog)`. Preserve it by passing `actor="aw backlog"` when none was given, as `m94eht` does for `(aw specs)`; record before and after.

    (b) THE REFUSAL TABLE. For every refusal `backlog.run_set` performs (`--gate-dir` not a project root, the paired lane-carrier flags, `--work-kind`/`--priority` enum, release-exempt pair, `--graduated-to`, `--message`, `--gate-ref`, no such item, ambiguous selector, illegal transition, gate pair on `blocked`, the release-gate close predicate), record rc and message on BOTH spellings before any edit, and mark each row `preserved` or `changed` after. Pinned today: `tests/test_status_set_descriptive_safety.py` asserts `aw backlog set: --message must not contain embedded newlines` on the `--status` spelling.

    (c) THE CONFIRMATION GATE. MEASURED: `aw backlog set aaa111 --status done --agent` (no `--yes`) is rc 0 and writes today; the shared engine returns 2 for an agent/JSON caller without `--yes`. `runner_shared.close_backlog_item` passes neither `--agent` nor `--json`, so it is unaffected; record that with the argv quoted, and name the change in the CHANGELOG.

    (d) THE SIDECAR. MEASURED: the `--status` spelling writes `.aw/records/history.jsonl`, the positional spelling does not. Whatever child 04 implemented for `wy9aru` OQ-1 already governs backlog through the shared engine once this adapter lands; measure that the backlog adapter inherits it and record the result.
  - Depends on: none
  - Expected outcome: the actor read back after delegation equal to the actor before it; a pasted refusal table with every row `preserved` or `changed` and each `changed` row's pinning test named; the confirmation-gate and sidecar observations pasted; E-04 does not start until every row is decided.
  - Execution state: pending

- [ ] E-04 Reduce `backlog.run_set` to an adapter delegating to `status_set.run_set_command` with `scoped_type="backlog"`, KEEPING ITS NAME AND CALLABLE SIGNATURE (spec `wy9aru` S2). It must accept both the `path` attribute its direct callers set and the `args` list `cli.main` supplies, as `cli.main` mutates `args.path` before calling.

    THREE AXES FLIP HERE AND EACH IS A DELIBERATE RULING, NOT A SIDE EFFECT. State each in the evidence with its before and after.

    (1) RELOCATION GOES THROUGH `git mv` (`wy9aru` 4.2), BUT THE PORCELAIN DOES NOT BECOME A SINGLE `R` UNDER `--no-commit`. CORRECTED AT REVIEW: MEASURED in a scratch repo, BOTH spellings end in ` D <src>` plus `?? <dest dir>` after `--no-commit`, because `status_set._offer_self_commit` runs `git reset --quiet HEAD -- <paths>` on the touched paths and unstages the rename (the same cause sibling `afdmn6`'s review recorded for its axis (c)). So the observable relocation shape already AGREES between spellings and will not flip here; `wy9aru` AC-5 is met by neither. Record the shape before and after (it should be unchanged), and do NOT claim a single-rename improvement. The committing path (`--commit`/`--yes` with self-commit) may record a rename in the COMMIT; measure that with `git show --stat --find-renames` and record it if so.

    (2) THE HISTORY WRITER CHANGES, BUT THE CLOCK, THE LABEL AND THE DEDUP ALREADY AGREE. CORRECTED AT REVIEW: `backlog.run_set` already stamps `core.utc_history_date()` (plan `5ivkdh`, commit `3c55295a3`), already labels the record with the target status or `same-status` (plan `jbipfa`, executed), and already consults `same_status_message_is_duplicate` (histdedup, backlog `r74211` `done`). So none of the three axes flips here. MEASURE each on both spellings before and after and record that it is unchanged; this plan closes no carrier for them.

    (3) A MULTI-MATCH SETID NOW ACTS ON EVERY MATCH (`wy9aru` 4.5). CORRECTED AT REVIEW: the shared engine does NOT refuse a setid. MEASURED with two items sharing a setid: `aw backlog set sharedset --status done` is rc 0 and moves ONLY the first (`res.paths[0]`); `aw backlog set done sharedset --yes` is rc 0 and moves BOTH. An ambiguous SUBSTRING refuses at rc 2 on both spellings already (sibling `afdmn6` axis (e)). So the change on the `--status` spelling is one-to-all for a setid, which is what `wy9aru` 4.5 rules canonical; it is a behavior change for a caller relying on first-match, and OQ-01 records that no in-tree caller does.

    APPLY E-07's DECISIONS: `actor="aw backlog"` when none was given, every `preserved` refusal row kept, and the lane-carrier parameters from E-03 passed through.

    THE DEAD `apply` READ DISAPPEARS WITH THIS FUNCTION. `backlog.run_set`'s dry-run guard reads `not getattr(args, "apply", True)` and `--apply` is not declared on `aw backlog set`. Its carrier `19lmbe` is ALREADY `done` (closed citing commit `23ec426df`), so there is nothing to close; record only that the residue is gone.
  - Depends on: E-01, E-02, E-03, E-07
  - Expected outcome: `backlog.run_set` contains no transition validation, no metadata render, no relocation and no history assembly of its own; both spellings produce identical observable results on every axis child 02's harness pins; the relocation shape, clock, label and dedup each measured unchanged; the setid one-to-all change measured; every existing direct caller (`tests/test_backlog.py`, `tests/test_backlog_descriptive_safety.py`, `tests/test_support_section.py`) still works.
  - Execution state: pending

### Task group 3: prove it, and reconcile the carriers honestly

- [ ] E-05 Author `tests/test_backlog_set_adapter.py` and re-run child 02's differential harness. The harness is the primary evidence: every backlog AGREEMENT assertion must still pass unchanged. FLIP the expected-difference assertions this plan closes, naming each individually with its old and new value: the sidecar row (d) if the ruling makes both sides agree, and the setid multi-selector behavior (e). The relocation shape (c) is ALREADY an agreement axis in the harness (reclassified at `afdmn6` review) and must stay unchanged.

    The new module covers what the harness does not: that `backlog.run_set` is still callable with each hand-built `Namespace` shape its existing tests use; that `--gate-dir` still splits the gate root from the write root; that `runner_shared.close_backlog_item` still closes an item end to end, including with `--lane-carrier-ref`/`--lane-carrier-path`; and that the recorded actor is still `(aw backlog)`.

    RUN THE THREE RETROSPECTIVE PARITY FILES EXPLICITLY AND PASTE EACH: `tests/test_backlog_positional_close_gate.py` (nineteen tests), `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`. Each exists because an asymmetry on that axis caused a release-blocking defect, so they are the regression surface that matters most here. A failure in any of them means this migration reintroduced one of the three defects the Set exists to prevent.

    NO TEST MAY READ PRODUCTION SOURCE with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Pass `--no-commit` on every CLI invocation.
  - Depends on: E-04
  - Expected outcome: every backlog agreement assertion in the harness passing unchanged; the flipped expected-difference assertions named with old and new values; the three retrospective parity files each passing with output pasted; the new module's cases passing.
  - Execution state: pending

- [ ] E-06 Record the carrier state and the user-visible change. CORRECTED AT REVIEW: of the six carriers authoring named, `19lmbe` and `r74211` are already `done`, `jbipfa` is `executed`, and `fnb8pl`/`lq2w86` are `graduated` to their own plans (`qjm4bg` pending; `9wcei0` executed / `rfyrvp` superseded), so this plan closes NONE of them and must not touch their status. Re-read each `- Status:` at execution and record it before and after, unchanged.

    `2wae2x` (`open`, `Blocks-Release: next`) is the one live item. Its own text scopes it to "backlog.run_set formats history dates using local date ... while status_set uses UTC", which plan `5ivkdh` fixed BEFORE this plan. Do NOT close it from here: the fix is not this plan's work and closing another plan's carrier is the maintainer's call. Record the measured verdict (both spellings stamp UTC; `test_release_exempt_setter_roundtrip_and_parity` passes under a skewed `TZ`) in the evidence and in the final report, naming `5ivkdh`'s executed plan as the citation a maintainer would use with `aw backlog set done 2wae2x --evidence <path>`.

    FILE ONE BACKLOG ITEM with `aw backlog new` for the relocation finding E-04 (1) measured (`_offer_self_commit`'s reset unstages the `git mv`, so `wy9aru` AC-5 is met by neither spelling), unless one already exists, and cite its id6 in the evidence. `Work-Kind: bug`, so it carries `- Blocks-Release: next` by default.

    The `CHANGELOG.md` entry names what a USER observes: `aw backlog set <setid> --status <s>` now updates every item in the set rather than only the first; it now requires `--yes` with `--agent` or `--json`; and each E-07 row marked `changed`. Write no em or en dashes (user-facing prose, `AGENTS.md`), do not describe the delegation, and make no claim about git renames, dates or history labels (none changed).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07
  - Expected outcome: the five settled carriers' statuses unchanged; a pasted `2wae2x` verdict with its measurement and no status change; one new backlog item id6 for the AC-5 relocation finding (or the existing one cited); one CHANGELOG entry naming the user-visible changes listed above, with no em or en dash.
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
| F-02 | HIGH (DATA-LOSS PRECEDENT; OBSERVABLE CLAIM CORRECTED AT REVIEW, see F-09) | `status_set.apply_status_change`'s comment records that it USED to `atomic_write` then `unlink` and that git saw that as TWO changes; `tests/test_git_commit_helper.py::test_staged_rename_moves_and_duplicate_prevention` asserts the porcelain line starts with `R` and its comment block records a measured 36-duplicate-id incident. `backlog.run_set` still does `atomic_write` then `unlink`. | **THE RELOCATION DIFFERENCE IS NOT COSMETIC: ONE SIDE HAS A PINNED REGRESSION TEST AND A RECORDED DATA-LOSS INCIDENT, AND THE OTHER IS THE SHAPE THAT CAUSED IT.** `wy9aru` 4.2 rules `git mv` canonical on exactly this evidence. Migrating this path is therefore a defect fix wearing a refactor's clothes, which is worth stating so a reviewer does not treat the porcelain change as incidental churn. |
| F-03 | MEDIUM (CARRIER DISCIPLINE; RE-MEASURED AT REVIEW) | At HEAD `072b6f640`: `backlog.run_set`, `backlog.run_note` and `_reattach_history` stamp `core.utc_history_date()` (`5ivkdh`); `19lmbe`, `r74211`, `t1gbwg`, `mbjuv5`, `68sur3` are `done`; `fnb8pl`/`lq2w86` `graduated`; `2wae2x` `open`. Local-clock reads remain only in non-history sites (`backlog.py` filename date, `set_records`). | **NO CARRIER IS THIS PLAN'S TO CLOSE.** The clock, dedup and label axes were closed by other plans before this one runs. E-06 records statuses unchanged and a verdict for the one live item, `2wae2x`, without closing it. |
| F-04 | MEDIUM (RUNNER DEPENDENCY) | `runner_shared.close_backlog_item` builds argv with an explicit `--status done` and documents choosing that spelling "because only it honors `--gate-dir`". `BacklogGateDirSplitTests` (five tests) plus `test_backlog_set_declared_flag_surface_matches_parser` pin the behavior and the declaration. | **THE RUNNER'S OWN BACKLOG-CLOSE PATH DEPENDS ON THE SPELLING THIS PLAN MIGRATES**, so the adapter is not optional and `--gate-dir` must survive as both a declaration and a behavior. E-03 makes it an engine parameter and E-05 drives `close_backlog_item` end to end rather than inferring it still works. |
| F-05 | MEDIUM (SILENT PARTIAL TARGET; CORRECTED AT REVIEW) | `backlog.run_set` on a multi-match setid acts on `res.paths[0]`, documented as "act on the first deterministically". MEASURED: the shared engine acts on EVERY setid match (rc 0, both items moved); an ambiguous substring refuses on both spellings already. | **TODAY ONE SPELLING SILENTLY WRITES ONLY THE FIRST OF A SET**, while the other writes all of them. Delegation makes the `--status` spelling write all, which is `wy9aru` 4.5's ruling. It is not a new refusal, as authoring claimed. OQ-01 records that no in-tree caller relies on first-match. |
| F-06 | LOW (DEAD READ) | `backlog.run_set`'s dry-run guard reads `not getattr(args, "apply", True)`, and `--apply` is not declared on `aw backlog set`. Item `19lmbe` is `done` at review (closed citing commit `23ec426df`). | **THE DEAD READ DISAPPEARS WITH THE FUNCTION; THERE IS NO CARRIER LEFT TO CLOSE.** |
| F-07 | LOW (THREE AXES; CORRECTED AT REVIEW) | `backlog.run_set` already uses `core.utc_history_date()`, passes `label=` (`jbipfa`) and consults `same_status_message_is_duplicate` (histdedup). | **NONE OF THE THREE AXES FLIPS.** What DOES change is the actor and the refusal prefix (F-10). E-04 measures the three axes unchanged. |
| F-08 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **RE-DERIVE; COMPARE FAILURE SETS BY NAME.** `test_release_exempt_setter_roundtrip_and_parity` should already be time-independent since `5ivkdh`; verify under both timezones as a non-regression, not as an improvement this plan delivers. |
| F-09 | HIGH (UNREACHABLE EVIDENCE, MEASURED AT REVIEW) | Scratch repo, `--no-commit`: `--status` spelling porcelain ` D .../open/<item>` + `?? .../done/`; positional spelling the SAME. Cause: `status_set._offer_self_commit` `git reset --quiet HEAD -- <paths>`. | **V-04's demand for "a single `R` rename line" on both spellings was not reachable**, and the CHANGELOG claim "recorded as a single file rename" would have been false. E-04 (1), E-05, E-06 and V-04 are rewritten to the observable agreement, and E-06 files the AC-5 gap. |
| F-10 | HIGH (CALLER-BREAKING CHANGES NOT NAMED, MEASURED AT REVIEW) | Actor `(aw backlog)` vs `(aw set)` (52 pinned assertions, 12 modules); refusal prefix `aw backlog set:` vs `aw set:` (pinned in `tests/test_status_set_descriptive_safety.py`); `--agent` without `--yes` rc 0 vs rc 2; `runner_shared.close_backlog_item` passes `--lane-carrier-ref`/`--lane-carrier-path`, which `status_set` never reads. | **DELEGATION AS WRITTEN WOULD REWRITE THE ACTOR, CHANGE PINNED MESSAGES, AND DROP THE RUNNER'S LANE-CARRIER OVERRIDE.** E-07 spike added; E-03 carries the lane-carrier flags. |

## Proposed changes (ordered, validatable)

1. No production edit: confirm the unsafe-descriptive refusals `4gwgo3` already installed in the shared engine (E-01).
2. `agent_workflows/status_set.py`: function-level enum validation of `--work-kind`/`--priority`, derived from `backlog.PRIORITIES`/`backlog.KINDS` (E-02).
3. `agent_workflows/status_set.py`: an optional gate root parameter plus the lane-carrier ref/path pair, so `--gate-dir` and the runner's override survive (E-03).
3a. No production file: the E-07 spike measures actor, refusal table, confirmation gate and sidecar on both spellings and decides each row (E-07).
4. `agent_workflows/backlog.py` + `agent_workflows/cli.py`: `backlog.run_set` becomes an argument-normalizing adapter delegating to the shared engine (E-04).
5. `tests/test_backlog_set_adapter.py`: the adapter's own cases; plus child 02's harness re-run with its flipped expected-difference assertions named, and the three retrospective parity files run explicitly (E-05).
6. `CHANGELOG.md`: one entry naming the user-visible changes; carrier statuses recorded unchanged; one backlog item filed for the AC-5 relocation gap (E-06).

## Deferred / out of scope (with reason)

- THE SPECS PATH IS NOT MIGRATED HERE. Spec `wy9aru` S4 requires the migration to be incremental and per-verb, each with its harness green before the next starts, and child 04 does specs first because it is the simpler path (no `--gate-dir`, no `_render_item` round trip, no relocation divergence). This plan depends on it having executed.
  - Carrier: m94eht
- THE CLOCK CARRIERS ARE NOT THIS PLAN'S (F-03, corrected at review). The `run_set` history clock was fixed by `5ivkdh` before this plan; `2wae2x` is left for the maintainer to close with that plan's citation.
  - Carrier: 2wae2x
- THE SAME-STATUS DEDUP AND THE HISTORY LABEL were already unified by histdedup and `jbipfa`; `r74211` is `done`. Nothing remains here.
  - Carrier: r74211
- THE BACKLOG TRANSITION TABLE IS NOT DESIGNED HERE. `t1gbwg` is `done` at review; both spellings now consult `attention_contract.backlog_transition_allowed`, and delegation leaves one call site for it.
  - Carrier: t1gbwg
- THE AUDIT OF ITEMS ALREADY CLOSED THROUGH THE UNGATED SPELLING is untouched (`mbjuv5`, `done` at review).
  - Carrier: mbjuv5
- `aw prompts set` registration is not this plan's concern (`68sur3`, `done` at review via executed plan `gm9baj`).
  - Carrier: 68sur3
- THE `git mv` RENAME IS UNSTAGED BY `_offer_self_commit`'S RESET UNDER `--no-commit`, so `wy9aru` AC-5 is met by neither spelling (F-09). Fixing the reset changes the self-commit contract for every record type and is not a dispatch change; E-06 files a backlog item for it.
  - Carrier: filed by E-06 at execution (`aw backlog new`), id6 recorded in V-06
- `--gate-dir` IS NOT ADDED TO ANY OTHER VERB. `wy9aru` C5 asks for flag convergence only where a flag is MEANINGFUL, and a gate root on a plan or prompt setter is not. It stays declared on `aw backlog set` alone.
  - Carrier-Declined: not a defect; the flag is verb-specific by design and `wy9aru` 4.4 rules it stays where it is

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-01, E-02, E-03), `agent_workflows/backlog.py` (E-04), `agent_workflows/cli.py` (E-04), `tests/test_backlog_set_adapter.py` (E-05), `CHANGELOG.md` (E-06).
- Under-scope: E-05 flips assertions in `tests/test_set_dispatch_parity.py`, which child 02 authors and which is not declared here, to avoid a scope-reconciliation conflict over another plan's file; declare it at execution if the finalize gate requires it and record the widening in the transition message, which this note authorizes. E-01's broad application of the unsafe-descriptive refusal may require repairing a test asserting that an unsafe value is accepted; the path is not knowable at authoring time (F-01 establishes the risk, not its target), so declare it at execution if it materializes. E-06 creates one backlog item under `.aw/records/backlog/` through `aw backlog new`, a tooled authoring verb rather than a hand edit; justify it at finalize with a `--scope-reason`. E-07 (b) may edit `tests/test_status_set_descriptive_safety.py` and any of the twelve modules pinning `(aw backlog)` ONLY for a row it marks `changed`. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, not counts (F-08).
- `tests/test_set_dispatch_parity.py` (child 02's harness) run alone under BOTH the machine's local timezone and `TZ=UTC`, with every backlog AGREEMENT assertion passing UNCHANGED. A changed agreement assertion is a regression unless this plan named it in advance.
- THE THREE RETROSPECTIVE PARITY FILES, run individually and pasted: `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py`, and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange`. These are the surfaces that caught the three release-blocking defects; a failure means this migration reintroduced one.
- `tests/test_backlog_handoff_close.py` (including `BacklogGateDirSplitTests` and the declared-flag-surface test), `tests/test_backlog.py`, `tests/test_history_provenance.py` and `tests/test_git_commit_helper.py`, each run individually with its result pasted.
- `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` run under BOTH timezones as a non-regression (it should already be time-independent since `5ivkdh`). Report both runs.
- The new `tests/test_backlog_set_adapter.py` run alone with `-o addopts=""`, every case named, including the end-to-end `runner_shared.close_backlog_item` drive (with and without the lane-carrier pair) and the `(aw backlog)` actor read-back.
- `AW_NO_REEXEC=1 aw backlog check`, `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0, and `AW_NO_REEXEC=1 aw check release-gates` pasted, since E-06 files a `bug` item that defaults to `Blocks-Release: next`.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET plus the one new backlog item E-06 files. Re-derive before and after. Do not "fix" another plan's finding or another lane's state.
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

`CHANGELOG.md` records the user-visible changes E-06 lists. No other user-facing documentation
describes `backlog.run_set`'s internals.

## Open questions

### OQ-01: does anything rely on `backlog.run_set`'s current first-match behavior for an ambiguous selector?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-10-07 FROM THE CODE: the only in-tree production caller of the `--status` spelling is `runner_shared.close_backlog_item`, whose argv is `["backlog", "set", item_id6, "--status", "done", ...]`, a single id6 that cannot match several items. No other production module builds `backlog set` argv. So no caller relies on first-match; E-04 re-runs the search at execution. Original rationale: F-05 establishes the behavior change: the migration replaces "act on `res.paths[0]` silently" with "refuse unless `--force`". That raises the floor `wy9aru` C2 defines, so the design does not change either way; the question is only whether an in-tree caller (notably `runner_shared.close_backlog_item`, the hosts, or a workflow body) passes a selector that can match several and relies on the first. Answerable by searching those callers at execution time. If one exists, it must pass `--force` or a unique selector, and that fix belongs in the same change.

### OQ-02: does this migration COMPLETELY satisfy release-gated item `19lmbe`, or only partially?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-10-07: MOOT. `19lmbe` is already `done` (history: "Fixed in commit 23ec426df7: dry_run honored in backlog.py"), so this plan neither closes nor reopens it; E-04 records only that the residual dead read disappears. Original rationale: F-06 establishes that `19lmbe`'s subject is the dry-run guard's dead `apply` read, and that the guard ceases to exist when `run_set` becomes an adapter, which makes this the likeliest genuine close among the six carriers. But the item is RELEASE-GATED, so closing it wrongly writes a false record, and the verdict must be measured against the ITEM's own text rather than against this plan's diff. E-06 requires a COMPLETE-or-PARTIAL verdict with the measurement, and a close only via `aw backlog set done --evidence` after this plan reaches `executed/`. Non-blocking because either verdict has a defined action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted rc and the file read back for an unsafe `--message` on BOTH spellings showing refusal and no write; the same for an unsafe `--gate-ref`; a legitimate long prose message accepted; a demonstration that the refusal applies to a non-backlog record type too; and `git diff` showing no production edit made by this item.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted rc and the file read back for a direct call with an invalid `--work-kind` and with an invalid `--priority`, both refused with nothing written; valid values shown writing; and a statement that the vocabularies are derived from `backlog.PRIORITIES`/`backlog.KINDS` with the derivation quoted, not re-listed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output of `aw backlog set <item> --status done --gate-dir <other-root>` showing the predicate evaluated against the other root and the write landing in the repo root; pasted output showing `--lane-carrier-ref`/`--lane-carrier-path` change the predicate's verdict after delegation and the one-without-the-other refusal; pasted results for `BacklogGateDirSplitTests` and `test_backlog_set_declared_flag_surface_matches_parser`; and pasted evidence of `runner_shared.close_backlog_item` driven end to end successfully.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `git status --porcelain` after a `--no-commit` status change through BOTH spellings, before and after delegation, showing the shape unchanged and identical across spellings; the clock, label and dedup each measured before and after with the records pasted, unchanged; the setid one-to-all change demonstrated with two items (before: one moved; after: both moved) and the substring refusal unchanged; the answer to OQ-01 with the search that produced it; and pasted proof that every existing direct caller of `backlog.run_set` still works.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted harness run under both the local timezone and `TZ=UTC` with every backlog agreement assertion passing UNCHANGED; the flipped expected-difference assertions named with old and new values; pasted individual results for the three retrospective parity files; pasted result for `test_release_exempt_setter_roundtrip_and_parity` under BOTH timezones, passing; and pasted results for the new adapter module.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the `- Status:` of `19lmbe`, `2wae2x`, `fnb8pl`, `lq2w86`, `r74211` before and after, unchanged; the `2wae2x` verdict with both spellings' UTC records pasted; the `aw backlog new` output (or the existing item) for the AC-5 relocation gap with its id6; pasted `aw check release-gates`; the `CHANGELOG.md` hunk diffed; and a grep over that hunk for em and en dashes returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: a pasted history line after delegation on both spellings showing `(aw backlog)`; the pasted refusal table with rc and message on both spellings before and after, every row `preserved` or `changed`, and each `changed` row's edited test path; the pasted `runner_shared.close_backlog_item` argv showing no `--agent`/`--json`; and the sidecar observation on both spellings after delegation.
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

Scope fence: the declared `Scope-Paths` plus the conditional paths named in "Scope check" are a
DECLARATION, not a stop condition; an out-of-scope edit is made and then justified with a
`--scope-reason`, and a declared path left untouched takes a `--scope-ack`. The spec-sync STOP (child
04's amendment absent) is a missing-prerequisite stop and remains correct.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the runner performs that transition;
when executed by hand, the executor runs `aw ipd finalize` for it. Never hand-`git mv` the file. No
step of this plan runs after the transition (E-06 closes nothing). The orchestrator `63zo2f` owns the disposition of the backlog item `fcnz1r`
itself; do not set it from here.
