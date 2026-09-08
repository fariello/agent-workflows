# IPD: Give aw backlog set the --work-kind and --priority setters its plan twin already has

- Date: 2026-09-08
- Kind: child
- Concern: `aw backlog set` cannot correct an item's `Work-Kind` or `Priority`, although `aw ipd set` and `aw specs set` can both set both fields on their record types. An agent asked to reclassify a mislabeled backlog item must therefore hand-edit frontmatter the tool otherwise owns, which is exactly what the noun-verb grammar exists to prevent. The measured consequence is not cosmetic: the 2026-09-03 all-bugs-block-release audit selects on `Work-Kind: bug`, so three items (`cnwy8g`, `fjs11i`, `a8eufb`) whose labels could not be corrected with the owner verb were invisible to the audit that existed to find them.
- Scope: Register `--work-kind` and `--priority` on the `aw backlog set` subparser, validate both against the single shared vocabularies in `backlog.py` (`KINDS`, `PRIORITIES`) rather than a second literal list, make both persist on a NO-OP transition (a pure reclassification changes no status), and make both work on BOTH of the verb's two spellings (the positional `<status> <selector>` form and the `<path> --status` form, which dispatch to two different code paths). Update the declared command surface so the flags are not merely present but declared, and pin all of it with tests including the no-op case this defect was hit on.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/backlog.py, agent_workflows/command_surface.py, tests/test_work_kind.py, tests/test_backlog_work_kind_rename.py
- Item-Dependencies: none
- Status: to-review
- Set: bklgkind
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: b5sfwm
- From-Backlog: a220ap
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `a220ap`, inheriting its `Blocks-Release: next` gate. Every claim below was re-measured at HEAD `44d4950d` by reading the files, not by recalling line numbers. ONE CORRECTION TO THE ITEM, which widens the plan: the item asserts "only `Priority` is reachable on a BACKLOG item", and that is FALSE. `aw backlog set --help` lists neither `--priority` nor `--work-kind`, and `--priority` exists only on `aw backlog new` (`cli.py:3914-3916`). So NEITHER classification field is tool-settable on an existing item, and fixing only `--work-kind` would leave the identical hole one field over. Both are in scope. ONE MATERIAL DISCOVERY that shrinks the work: `aw backlog set` on its POSITIONAL spelling already routes through `status_set.apply_status_change` (`cli.py:11140-11149`, `scoped_type="backlog"`), whose Work-Kind and Priority writers are record-type-agnostic and already hoisted out of every status branch, so that spelling needs a parser change only. The `--status` spelling forks to `backlog.run_set` (`cli.py:11150-11156`) and does need its own handling; that asymmetry is the real risk in this plan and E-03 exists for it.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a backlog item's classification correctable with the verb that owns it, so a mislabeled `Work-Kind` stops being a label that stays wrong. The release-facing point is narrow and measured: an audit that selects on `Work-Kind: bug` is only as good as the repository's ability to fix a wrong `Work-Kind`, and today that ability requires a hand edit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: register the two flags

- [ ] E-01 Register `--work-kind` on the `aw backlog set` subparser `p_backlog_set` (created at `cli.py:3966-3971`; its existing flags run `--dir` `:3975`, `--status` `:3978`, `--message` `:3981`, `--gate-kind` `:3982`, `--gate-ref` `:3988`, `--blocks-release` `:3994`, `--evidence` `:4000`, `--dry-run` `:4010`, `--yes` `:4013`, `_add_commit_flags` `:4016`). Mirror the `aw ipd set` registration at `cli.py:1293-1300` exactly: `dest="work_kind"`, `choices` covering the vocabulary plus `-` to clear, and help text that states the `-` clears semantics and the persists-on-a-no-op-transition behavior. DERIVE THE CHOICES LIST FROM `backlog.KINDS` (`backlog.py:70`) RATHER THAN TYPING A THIRD LITERAL. Both existing registrations hardcode the five values (`cli.py:1297` for `ipd set`, `cli.py:4247` for `specs set`) and are pinned to the shared vocabulary only by a test (`tests/test_work_kind.py:212-236`); adding a third hand-written copy widens a known drift surface, and the sorted vocabulary plus `"-"` is a one-expression substitute.
  - Depends on: none
  - Expected outcome: `aw backlog set --help` lists `--work-kind` with the same vocabulary `aw ipd set --help` shows, and an out-of-vocabulary value is rejected by argparse before any file is touched.
  - Execution state: pending

- [ ] E-02 Register `--priority` on the same subparser, mirroring `aw ipd set --priority` (`cli.py:1282-1289`), validated against `backlog.PRIORITIES` (`backlog.py:69`). THIS ITEM EXISTS BECAUSE THE BACKLOG ITEM'S PREMISE WAS WRONG IN THE PLAN'S FAVOUR: the item says `Priority` is already reachable, and it is not. Measured at HEAD `44d4950d`: `aw backlog set --help` lists exactly `--no-color --agent --json --dir --status --message --gate-kind --gate-ref --blocks-release --evidence --dry-run --yes --commit/--no-commit`, and `--priority` appears only on `aw backlog new` (`cli.py:3914-3916`). Leaving it out would ship a fix whose own justification ("the tool must own the frontmatter") still fails one field over, and would guarantee a duplicate item.
  - Depends on: none
  - Expected outcome: `aw backlog set --help` lists `--priority`; both classification fields are now reachable on an existing item.
  - Execution state: pending

### Task group 2: make both spellings honor the flags

- [ ] E-03 Handle the `--status` spelling, which does NOT share the plan/spec write path and is the only place new write code is needed. `aw backlog set` forks on whether a status was given as a positional: the positional form dispatches to `status_set.run_set_command(..., scoped_type="backlog")` (`cli.py:11140-11149`), whose `apply_status_change` (`status_set.py:590`) already writes Work-Kind at `:762-773` and Priority at `:749-760` for ANY record type; the `<path> --status` form instead dispatches to `backlog.run_set` (`cli.py:11150-11156`), which has no such writer. Apply the two fields inside `backlog.run_set` (`backlog.py:473-607`) by setting them on the parsed item BEFORE the render at `:536`, so `_render_item` (`:317-337`, the `- Work-Kind:` line at `:324`) emits the new values. Reuse `backlog.KINDS`/`PRIORITIES` for validation and refuse with the same exit-2 shape `backlog new` uses (`:374-378`); do NOT reimplement the regex line-rewrite, since the render already round-trips the field from the parsed item. VERIFY THE FORK EMPIRICALLY BEFORE CODING: run both spellings under a debugger or with a print to confirm which function receives each, because a fix applied to only one spelling is invisible until a user picks the other.
  - Depends on: E-01, E-02
  - Expected outcome: both `aw backlog set open <selector> --work-kind bug` and `aw backlog set <path> --status open --work-kind bug` persist the change; the same holds for `--priority`.
  - Execution state: pending

- [ ] E-04 Make a PURE RECLASSIFICATION work, i.e. a call that changes no status. This is the exact case the defect was hit on (the item records reclassifying `cnwy8g`, `fjs11i`, `a8eufb` from `followup` to `bug` with no status change) and it is the one most likely to be missed, because the verb is named for transitions. On the positional spelling this already holds by construction and must be CONFIRMED not assumed: the Work-Kind write at `status_set.py:762-773` and the Priority write at `:749-760` are hoisted out of every status branch and keyed only on the flag being present, and `apply_status_change` has no same-status early return, which is precisely how `aw ipd set` earns its "persists on a no-op transition" claim (pinned by `tests/test_work_kind.py:337-377`, no-op assertion at `:357-361`). On the `--status` spelling, confirm a same-status call is not short-circuited before the render at `backlog.py:536`. A history record MUST be appended for the reclassification (`backlog._reattach_history`, `:628-649`, record format `:635`), because an untracked classification change is an unauditable one, and the item's own history is the precedent: the deviation was recorded by hand so it would be auditable.
  - Depends on: E-03
  - Expected outcome: setting an item's current status again while passing `--work-kind bug` persists the new kind AND appends a history record naming the change; no file move occurs.
  - Execution state: pending

- [ ] E-05 Update the DECLARED command surface so the flags are declared and not merely present. `command_surface.COMMAND_INVENTORY` carries an entry for `command="backlog set"` at `command_surface.py:1197-1215` whose `legacy_flags` (`:1204-1213`) list neither field, while the `backlog new` entry (`:1181`, `:1190-1194`) does list its `--work-kind`. Add both flags to the `backlog set` declaration. This matters because the repo already enforces declaration/parser agreement for the sibling verb (`tests/test_backlog_work_kind_rename.py:424-434` for `backlog new`), so an undeclared flag is an inconsistency the next audit of this surface would report.
  - Depends on: E-01, E-02
  - Expected outcome: the `backlog set` inventory entry declares `--work-kind` and `--priority`, matching what the parser accepts.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Add the test the backlog item explicitly requires, plus its siblings. The item's stated requirement is verbatim: "a test asserting a reclassification with NO status change is persisted and appends a history record, because that no-op case is the one this defect was hit on." Follow the existing template rather than inventing a shape: `tests/test_work_kind.py::PlanSetterTests::test_set_writes_persists_on_noop_and_clears` (`:337-377`) is the plan-side twin, and its `-`-clears half is at `:362-377`. Cover, for BOTH spellings from E-03: (a) a no-op reclassification persists and appends history; (b) `-` clears; (c) an out-of-vocabulary value is refused and NOTHING is written; (d) the same three for `--priority`. Note `tests/test_backlog_work_kind_rename.py` already calls `backlog.run_set` twice (`:212`, `:324`) but only for rename/gate preservation, and its `_SetArgs` namespace (`:492-508`) has NO `work_kind` attribute, so that namespace needs extending rather than a new fixture being written.
  - Depends on: E-03, E-04
  - Expected outcome: the no-op reclassification case is pinned by a test that fails against HEAD `44d4950d` and passes after E-03/E-04; the clear and refusal cases are pinned too.
  - Execution state: pending

- [ ] E-07 Extend the anti-drift test that pins the argparse choices to the shared vocabulary. `tests/test_work_kind.py:212-236` (`test_the_cli_choices_match_the_shared_vocab`) currently asserts `set(backlog.KINDS) | {"-"}` for the `("ipd","set")` and `("specs","set")` paths only. Add `("backlog","set")` to it, so the third registration cannot drift from `backlog.KINDS`. If E-01 derived the choices from the vocabulary rather than typing them, this test becomes a cheap regression fence rather than the only defense; keep it either way, because it is what makes the "one vocabulary" property checkable.
  - Depends on: E-01
  - Expected outcome: the vocabulary-agreement test covers all three `set` verbs and fails if any registration diverges from `backlog.KINDS`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The vocabularies are single-sourced in `backlog.py`: `PRIORITIES` at `:69`, `KINDS` at `:70`. The plan and spec CHECKERS honor that (`check_engine.check_plan_work_kind` at `:2671`, comparing against `sorted(_backlog.KINDS)` at `:2712`/`:2715`; `specs.py:317` validating `work_kind not in _backlog.KINDS`), but the argparse `choices` lists do NOT: they are hand-written literals at `cli.py:1297` and `cli.py:4247`.
- `aw backlog set` has TWO dispatch paths, and this is the single most important fact for this plan. Positional `<status> <selector>` goes to `status_set.run_set_command` with `scoped_type="backlog"` (`cli.py:11140-11149`); `<path> --status` goes to `backlog.run_set` (`cli.py:11150-11156`). They do not share a write path.
- `status_set.apply_status_change` (`:590`) is record-type-agnostic and writes the optional fields UNCONDITIONALLY on flag presence, outside every status branch: `--blocks-release` `:709-721`, `--from-backlog` `:723-733`, `--item-dependencies` `:735-747`, `--priority` `:749-760`, `--work-kind` `:762-773`. That hoisting IS the "persists on a no-op transition" mechanism; there is no same-status early return.
- The shared line writer is `releases.set_work_kind_line` (`releases.py:455-468`) with a full-line-anchored regex `_WORK_KIND_LINE_RE` (`:452`). Use it rather than a new rewrite if a regex path is needed at all.
- `backlog._render_item` (`:317-337`) re-emits `item.kind` (`:324`) as parsed, so `run_set` already round-trips the field; only a settable override is missing. Validation lives in `backlog.validate_item` (`:170`) with the kind check at `:207-214` emitting `backlog.kind-invalid`.
- `tests/test_work_kind.py` contains a deliberate `BacklogAsymmetryTests` class (`:567-594`) asserting the backlog side REQUIRES its field and reports through its own rule. Read it before touching backlog validation, so this plan's change is recognized as adding a setter rather than relaxing a requirement.
- `aw backlog new` already accepts `--work-kind` (`cli.py:3921-3926`) with a retained `--kind` alias (`:3927-3932`), applied at `backlog.py:363-365` with the preferred spelling winning. Match that spelling precedent; do NOT add a `--kind` alias to `set`, since nothing has ever shipped one there and a new alias is a new deprecation obligation.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | `aw backlog set` registers no classification setter at all. Its full flag list is `--dir --status --message --gate-kind --gate-ref --blocks-release --evidence --dry-run --yes --commit/--no-commit`. | `cli.py:3966-4016`; measured `python3 -m agent_workflows backlog set --help` at `44d4950d` |
| F-2 | THE ITEM'S PREMISE IS PARTLY WRONG, and the correction widens the fix: `--priority` is NOT reachable on `backlog set` either. It exists only on `backlog new`. So neither field is settable on an existing item. | `cli.py:3914-3916` (`new`); absent from `:3966-4016` (`set`) |
| F-3 | The plan twin does have both: `aw ipd set --priority` at `cli.py:1282-1289` and `--work-kind` at `:1293-1300`, whose help text states "Persists on a no-op transition." | `cli.py:1282-1300` |
| F-4 | The gate half of the same operation is already tooled on backlog, which is what makes the classification half's absence an inconsistency rather than a uniform limitation: `--blocks-release` IS registered. | `cli.py:3994-3999` |
| F-5 | The positional spelling needs NO new write code: it already routes through `apply_status_change`, whose Work-Kind/Priority writers are record-type-agnostic and hoisted out of every status branch. | `cli.py:11140-11149`; `status_set.py:749-760`, `:762-773` |
| F-6 | The `--status` spelling DOES need new write code: it forks to `backlog.run_set`, which has no Work-Kind or Priority writer. This asymmetry is the plan's main risk. | `cli.py:11150-11156`; `backlog.py:473-607` |
| F-7 | There is no existing test anywhere in `tests/` that exercises a Work-Kind change through `backlog set`. The rename suite calls `run_set` twice but only for rename/gate preservation, and its `_SetArgs` namespace has no `work_kind` attribute. | `tests/test_backlog_work_kind_rename.py:212`, `:324`, `:492-508` |
| F-8 | The no-op-persistence template already exists on the plan side and is directly reusable as the shape for E-06. | `tests/test_work_kind.py:337-377`, no-op assertion `:357-361` |
| F-9 | The argparse choices are pinned to the shared vocabulary only by a test, and that test enumerates exactly two verbs, so a third hand-written literal would be unguarded until E-07 extends it. | `tests/test_work_kind.py:212-236`; literals at `cli.py:1297`, `cli.py:4247` |
| F-10 | The declared surface is stale for this verb: the `backlog set` inventory entry lists neither field while the `backlog new` entry lists its `--work-kind`. | `command_surface.py:1197-1215` (`legacy_flags` `:1204-1213`) vs `:1181`, `:1190-1194` |
| F-11 | The measured harm is an audit miss, not developer inconvenience: the 2026-09-03 all-bugs-block-release audit selected on `Work-Kind: bug` and skipped `cnwy8g`, `fjs11i`, `a8eufb`, whose labels could not be corrected with the owner verb. | backlog item `a220ap` body and its `2026-09-03 set` history record |

## Proposed changes (ordered, validatable)

1. Register `--work-kind` on `p_backlog_set`, deriving choices from `backlog.KINDS` (E-01).
2. Register `--priority` on the same subparser against `backlog.PRIORITIES` (E-02).
3. Apply both fields in `backlog.run_set` so the `--status` spelling honors them too (E-03).
4. Confirm and pin the pure-reclassification (no status change) path, including its history record (E-04).
5. Declare both flags in the `backlog set` command-surface entry (E-05).
6. Test the no-op reclassification, the `-` clear, and the refusal, on both spellings (E-06).
7. Extend the vocabulary-agreement test to cover the third `set` verb (E-07).

## Deferred / out of scope (with reason)

- A `--kind` ALIAS on `backlog set`. `backlog new` carries one for backward compatibility (`cli.py:3927-3932`), but `set` has never accepted any spelling, so there is nothing to be compatible with and a new alias would create a deprecation obligation for free.
- REPLACING the two existing hand-written `choices` literals at `cli.py:1297` and `cli.py:4247` with a vocabulary-derived expression. It is the same drift smell and the fix is mechanical, but it changes two verbs this plan is not otherwise touching, and E-07's extended test covers the risk. Worth a follow-up, not worth widening this fence.
- BULK RECLASSIFICATION (setting Work-Kind across many items in one call). Not requested, and a bulk classification change is exactly the kind of sweep that should be deliberate per item.
- The all-bugs-block-release AUDIT itself. This plan makes labels correctable; whether the three named items are re-audited afterwards is a separate act on items outside this plan's ownership.

## Scope check

- Over-scope: `--priority` (E-02) is not named by the backlog item, which wrongly believed it already worked. It is included because the item's own stated principle (the tool owns the frontmatter) fails identically on that field, and shipping without it guarantees a duplicate item. Called out here so a reviewer can reject it deliberately rather than discover it.
- Under-scope: the two pre-existing hardcoded `choices` literals are left alone (see Deferred). The `Work-Kind` values themselves are not re-audited on any item.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the actual summary line. Baseline on `main` at the time of authoring is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and note a lane worktree may show additional failures from tests that read live repo state.
- `python3 -m pytest tests/test_work_kind.py tests/test_backlog_work_kind_rename.py` for the focused surface.
- Manual, on a scratch item in a fixture repo, with the exit code measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`): a no-op reclassification on each spelling; a `-` clear; an out-of-vocabulary refusal that writes nothing.
- `python3 -m agent_workflows check backlog` must not gain a diagnostic.

## Spec / documentation sync

No spec governs the `backlog set` flag surface, so no `.spec.md` file is touched and none is declared in `Scope-Paths`. The authoritative declaration for this verb is `command_surface.COMMAND_INVENTORY` (`command_surface.py:1197-1215`), which E-05 updates; that is the in-repo contract a reviewer should check against. `--help` text is generated from the parser, so E-01/E-02 update it by construction. AGENTS.md needs no change: it already states that the tool owns the frontmatter, and this plan makes that true for one more field pair rather than changing the rule.

## Open questions

### OQ-01: Should the two pre-existing hardcoded choices literals be replaced in this plan?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: DEFERRED, and the plan proceeds either way. E-01 derives the new registration from `backlog.KINDS` and E-07 extends the agreement test to cover all three verbs, so the drift risk is fenced whatever is decided. Converting `cli.py:1297` and `cli.py:4247` as well would touch two verbs outside this plan's concern; a reviewer who wants them folded in can say so, since the edit is mechanical.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full `python3 -m agent_workflows backlog set --help` output showing `--work-kind` with its choices, AND paste the output of a rejected out-of-vocabulary call (`backlog set open <sel> --work-kind bogus`) with its exit code measured unpiped. Paste the source lines added to `cli.py` showing the choices are derived from `backlog.KINDS` rather than typed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same `--help` output showing `--priority` with the `backlog.PRIORITIES` vocabulary, and paste a rejected out-of-vocabulary `--priority` call with its unpiped exit code.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: on a scratch fixture item, run BOTH spellings and paste, for each, the command, its exit code, and a `grep '^- Work-Kind:\|^- Priority:'` of the resulting file showing the new values. The two spellings must be shown separately, because they traverse different code (`cli.py:11140-11149` vs `:11150-11156`); a single demonstration does not validate this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a same-status reclassification call (item already `open`, run with target status `open` plus `--work-kind bug`), its exit code, the resulting `- Work-Kind:` line, the appended `## Workflow history` record, and a `git status --short` or `ls` showing the file did NOT move directories. Do this for both spellings.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of the `backlog set` entry in `command_surface.py` and the output of whatever declaration-agreement assertion covers it, showing declared flags match the parser's accepted flags.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new tests' names and the actual `python3 -m pytest tests/test_work_kind.py tests/test_backlog_work_kind_rename.py` summary line. ALSO paste proof the no-op test is meaningful: its failure output when run against the pre-change code (for example via `git stash` of the source change, or a recorded run before the fix landed). A test that passes both before and after validates nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the extended `test_the_cli_choices_match_the_shared_vocab` source showing `("backlog","set")` in its enumeration, its passing result, and the failure message produced when one registration is temporarily perturbed (prove the fence bites).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
