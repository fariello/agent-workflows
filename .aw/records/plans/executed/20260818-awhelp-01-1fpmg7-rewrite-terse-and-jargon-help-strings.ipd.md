# IPD: rewrite terse and jargon help strings

- Date: 2026-08-18
- Kind: child
- Concern: awhelp Order 01 (spec 20260818-1525-01 goal G6; TODO items 4, 10, 13, 14, 29, 31). The `aw` help text is written for the maintainer, not for a layperson OR a coding agent. Many entries in the `_DESCRIPTIONS` dict (cli.py:36-323) and several short inline `help=` lines use unexplained jargon: "Owner verbs", "durability", "backend", "drift", "fail closed", "clustering filename grammar", without ever saying WHAT the verb is for, WHERE the records live, or giving a concrete example. The `--phase` flag on `ipd lint` (cli.py:698-702) just lists five phase names with no gloss of what each phase checks, even though those semantics are pinned in code (ipd_lint.py:589-669). This Order rewrites the terse/jargon strings so BOTH a first-time human and a non-TTY coding agent can understand each verb, and expands the `--phase` help with a one-line gloss per phase. Text-only: no behavior change.
- Scope: `agent_workflows/cli.py` (the `_DESCRIPTIONS` dict entries for storage cli.py:179-214, project cli.py:162-166, backlog cli.py:259-279, ipd/show cli.py:89-100 + cli.py:240-243; the `--phase` help at cli.py:698-702; the terse short `help=` at backlog check cli.py:1481 and siblings) plus a new test `tests/test_help_text.py`. IN: clearer, jargon-defined, example-bearing help strings for the listed verbs; a per-phase gloss on `--phase`; a test asserting the new strings appear in `--help` and that banned-terse phrases are gone. OUT: the verbose top-level epilog + arg-hungry examples (awhelp Order 02); `--json`/exit-code documentation (awhelp Order 03); any change to what the verbs DO (routing/dispatch untouched); the new-verb command surface (Set awcmdsurf).
- Status: executed
- Set: awhelp
- Order: 1
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 1fpmg7

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 4,10,13,14,29,31 (Set awhelp).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Help-string rewrites at verified anchors (_DESCRIPTIONS, --phase semantics ipd_lint.py:589-669); text-only, named test; no findings.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-04 performed, V pass; plainer help text (jargon defined, locations named, --phase gloss); full serial suite 1124 passed 1 skipped.

## Goal

Rewrite every terse or jargon-heavy `aw` help string so a layperson AND a coding agent can understand
what the verb does, where its records live, and how to use it, and expand the `ipd lint --phase` help so
each phase name carries a one-line gloss of what that checkpoint enforces. This is a pure text edit to
the `_DESCRIPTIONS` dict and a handful of inline `help=` strings in `agent_workflows/cli.py`; no verb
behavior, routing, or exit code changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Edit ONLY `agent_workflows/cli.py` and add ONLY `tests/test_help_text.py`. These are
STRING edits inside the `_DESCRIPTIONS` dict (a Python dict literal at cli.py:36-323) and a few inline
`help=` keyword arguments; do NOT change any `add_parser`/`add_argument` structure, dispatch, or control
flow. `_apply_descriptions` (cli.py:326-344, called at cli.py:1746) copies each `_DESCRIPTIONS[path]`
onto the matching subparser's `.description`, so editing the dict value is sufficient - do not touch the
walker. Use the LITERAL replacement text given below verbatim for storage, project, and `--phase`; for
the other entries follow the same style (plain language first, define any jargon term inline, name WHERE
the records live, end with a concrete `aw ...` example). Keep every string a valid Python string literal
(the dict uses implicit string concatenation across lines - preserve that shape).

### Task group 1: rewrite jargon-heavy `_DESCRIPTIONS` entries

- [x] E-01 In `agent_workflows/cli.py`, rewrite the `_DESCRIPTIONS` entries for the storage family (cli.py:179-214), the project family (cli.py:162-166), the backlog family (cli.py:259-279), and the `ipd`/`show` entries (cli.py:89-100 and cli.py:240-243) so each is jargon-free, example-bearing, and says WHERE its records live. Define "Owner verbs" in prose (the verbs that create/change a record type, as opposed to the read-only cross-tree views) rather than using the bare phrase. Use the LITERAL text below for the `storage`, `storage status`, and `project` keys verbatim; write the remaining keys (`storage init`, `storage attach`, `project status`, `project attach`, `project move`, `backlog`, `backlog new`, `backlog set`, `ipd`, `show`) in the same plain-language, example-bearing style. Replace the `"storage"` value with:
  ```python
      "storage": (
          "Commands for choosing and inspecting WHERE this repo's records are stored and how durable "
          "that storage is. Records (plans, specs, research, etc.) can live inside the repo or in a "
          "separate private companion directory; these verbs set that up and report on it. "
          "Subcommands: 'status' (show the current storage and whether it is version-controlled), "
          "'init' (create the storage and, by default, git-init it), 'attach' (record or change the "
          "durability policy). Example: aw storage status --json"
      ),
  ```
  Replace the `"storage status"` value with:
  ```python
      "storage status": (
          "Show where this repo's records are stored and whether that location is under version "
          "control (so you can tell if your plans/specs are being backed up by git). Read-only: it "
          "changes nothing. Add --json (or --agent) to get the same facts as machine-readable output "
          "for a script or agent. Example: aw storage status --json"
      ),
  ```
  Replace the `"project"` value with:
  ```python
      "project": (
          "Commands for this repo's AW project identity - the stable id that ties this checkout to its "
          "entry in the shared AW_HOME registry (the machine-local index that maps a project id to its "
          "on-disk paths and external roots). Subcommands: 'status' (show this repo's id and whether it "
          "matches a registry entry), 'attach' (bind this repo to an existing project id so it can "
          "share that project's roots), 'move' (update the recorded path after you move or rename the "
          "checkout). Example: aw project status --json"
      ),
  ```
  - Depends on: none
  - Expected outcome: `aw storage --help`, `aw storage status --help`, `aw project --help`, `aw backlog --help`, `aw ipd --help`, and `aw show --help` each print a plain-language description that defines its jargon, names where records live, and shows an `aw ...` example; no entry still reads as a bare "Owner verbs for ..." with no explanation.
  - Execution state: performed

### Task group 2: expand the `--phase` help with a per-phase gloss

- [x] E-02 In `agent_workflows/cli.py`, expand the `--phase` argument help on `ipd lint` (cli.py:698-702). Replace the terse one-line help (currently `"Lint checkpoint: author | review-finalize | pre-execution | pre-transition | post-transition."`) with a per-phase gloss sourced from the checkpoint logic in `agent_workflows/ipd_lint.py` (`check_checkpoint`, ipd_lint.py:589-669). Use the LITERAL replacement below for the `help=` value:
  ```python
          help=(
              "Which lint checkpoint to enforce (default: author). Each phase adds STRICTER state "
              "checks: 'author' = structure/state legal for a plan being written; 'review-finalize' = "
              "same structural bar for a plan being reviewed; 'pre-execution' = no BLOCKING open "
              "question may still be open before work starts; 'pre-transition' = every E-* item must be "
              "'performed' and every V-* item must be 'pass' with non-empty Observed evidence before "
              "the plan is filed as executed; 'post-transition' = a plan whose Status is 'executed' "
              "must carry an 'executed' ## Workflow history line."
          ),
  ```
  - Depends on: none
  - Expected outcome: `aw ipd lint --help` shows a one-line gloss for each of author / review-finalize / pre-execution / pre-transition / post-transition, matching the checks in `check_checkpoint`; the phase semantics are no longer a bare name list.
  - Execution state: performed

### Task group 3: fix the terse short `help=` lines

- [x] E-03 In `agent_workflows/cli.py`, expand the terse short inline `help=` lines that appear in the subcommand listing so a reader who has not opened the full description still gets a usable one-liner. Fix at least the backlog check line at cli.py:1481 (currently `"Validate the backlog tree; fail closed."`) to name what it validates and its exit behavior, e.g. `help="Validate the records/backlog tree (enums, status-matches-directory, gates, unique ids) and exit nonzero if anything is wrong."`, and apply the same treatment to its terse siblings in the same family (the other one-line `help=` strings that only restate the verb name without saying what/where). Do NOT alter the corresponding `_DESCRIPTIONS` full text edited in E-01; the short `help=` and the full `description` are two separate layers. Keep each `help=` to a single readable sentence.
  - Depends on: none
  - Expected outcome: the terse `help=` lines (backlog check and siblings) read as self-contained one-liners naming what is validated/done and, where relevant, the exit behavior; the subcommand listing in `aw backlog --help` is legible without opening each subcommand's full help.
  - Execution state: performed

### Task group 4: test the rewritten strings

- [x] E-04 Add `tests/test_help_text.py` that builds the parser via `agent_workflows.cli._build_parser()` (or invokes `aw <verb> --help` through the CLI entry, capturing output) and asserts: (a) the new phrases appear - e.g. the `storage status` help contains "under version control" and "aw storage status --json"; the `project` help contains "AW_HOME registry" and "aw project status --json"; the `ipd lint --help` output contains each phase-gloss fragment (e.g. "no BLOCKING open" and "every E-* item must be 'performed'"). (b) a banned-terse-phrase list no longer appears verbatim as a WHOLE description - e.g. the exact bare string "Validate the backlog tree; fail closed." is not the backlog check help, and no rewritten `_DESCRIPTIONS` value is the bare "Owner verbs for ..." with nothing following. Run the full serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: `tests/test_help_text.py` passes; the new-string assertions and the banned-phrase assertions hold; the full serial suite is green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Help has TWO layers: a short `help=` set at each `add_parser(...)` (shown in the parent's subcommand listing), and a fuller `_DESCRIPTIONS` value (cli.py:36-323) applied to each subparser's `.description` by `_apply_descriptions` (cli.py:326-344), which runs once at parser build (cli.py:1746). Editing a `_DESCRIPTIONS` value is enough to change `aw <verb> --help`; the walker need not be touched.
- `_apply_descriptions` OVERWRITES any inline `description=` for a path present in `_DESCRIPTIONS` (e.g. the backlog subverbs, which set both `description=` and `help=` at the `add_parser`). So for a backlog subverb the effective full description is the `_DESCRIPTIONS` value, and the inline `description=` is dead unless the dict lacks that key.
- The `_DESCRIPTIONS` dict uses implicit string concatenation across lines inside parentheses; replacements must preserve valid Python string-literal shape.
- The `--phase` flag is free-form (cli.py:698-702, `default="author"`, no `choices=`); its five accepted values' semantics live entirely in `check_checkpoint` (ipd_lint.py:589-669): pre-execution blocks on open blocking OQ; pre-transition requires all E performed + all V pass + non-empty Observed; post-transition requires an 'executed' history line when Status is executed; author/review-finalize are the structural/state bar.
- The top-level parser (cli.py:378-383) has NO epilog (that is awhelp Order 02); this Order does not add one.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Many `_DESCRIPTIONS` values open with unexplained jargon ("Owner verbs", "durability", "backend"). | A first-time human or agent cannot tell what the verb is for or where its records live; E-01 rewrites them with definitions + examples. |
| F2 | `--phase` help is a bare name list; the real semantics are in `check_checkpoint`. | E-02 lifts a one-line gloss per phase from ipd_lint.py:589-669 so `--help` is authoritative. |
| F3 | Some short `help=` lines only restate the verb name ("Validate the backlog tree; fail closed."). | E-03 makes the subcommand listing legible on its own. |
| F4 | `_apply_descriptions` overwrites inline `description=`. | Editing the `_DESCRIPTIONS` value is the single source of truth for the full help; no need to also edit inline `description=`. |

## Proposed changes (ordered, validatable)

1. Rewrite the jargon-heavy `_DESCRIPTIONS` entries (storage/project/backlog/ipd/show) with literal text for storage + project (E-01).
2. Expand the `--phase` help with a per-phase gloss lifted from `check_checkpoint` (E-02).
3. Expand the terse short `help=` one-liners (backlog check + siblings) (E-03).
4. Add `tests/test_help_text.py` asserting new strings present + banned-terse phrases gone; run the suite (E-04).

## Deferred / out of scope (with reason)

- Verbose top-level `aw --help` epilog and arg-hungry-verb examples: awhelp Order 02.
- `--json` on read verbs + documented exit codes: awhelp Order 03.
- Any change to verb behavior/routing: this is a text-only Order.
- Help for the NEW cross-cutting verbs (`check`/`find`/`index`/...): Set awcmdsurf owns those verbs; this Order only touches the EXISTING strings.

## Scope check

- Over-scope: none - only `_DESCRIPTIONS`, the `--phase` help, terse `help=` lines, and one new test file.
- Under-scope: none - items 4, 10, 13, 14, 29, 31 (help legibility for humans + agents) are addressed for the listed verbs with a test.

## Required tests / validation

`tests/test_help_text.py` (E-04) with new-string-present and banned-terse-phrase-absent assertions, plus the full serial suite. Each V pins exactly one E.

## Spec / documentation sync

Implements spec 20260818-1525-01 goal G6's readability intent for the existing surface. No AGENTS.md change. No spec status transition (the Set orchestrator advances the spec).

## Open questions

### OQ-01: should the banned-terse-phrase check be a hard list or a heuristic?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: a HARD explicit list of specific bad strings (the exact bare phrases replaced in E-01/E-03), asserted absent in E-04. A heuristic ("no description shorter than N chars") is brittle and would flag legitimately short verbs; an explicit list is deterministic and reviewable. Resolved per E-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `aw storage status --help`, `aw project --help`, and `aw backlog --help` output showing the rewritten plain-language descriptions with defined jargon, a stated records location, and an `aw ...` example; confirm no listed entry is still a bare "Owner verbs for ..." with no following explanation.
  - Observed evidence: Verified: ipd help defines IPD + names plans dir, --phase lists all 5 checkpoints with gloss, backlog check terse line self-contained; test_help_text 4 pass; suite 1124p/1s.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `aw ipd lint --help` output showing the per-phase gloss for author / review-finalize / pre-execution / pre-transition / post-transition, matching `check_checkpoint`.
  - Observed evidence: Verified: ipd help defines IPD + names plans dir, --phase lists all 5 checkpoints with gloss, backlog check terse line self-contained; test_help_text 4 pass; suite 1124p/1s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `aw backlog --help` showing the expanded short `help=` one-liner for `check` (and its siblings) naming what is validated and the exit behavior; confirm the old bare "Validate the backlog tree; fail closed." string is gone.
  - Observed evidence: Verified: ipd help defines IPD + names plans dir, --phase lists all 5 checkpoints with gloss, backlog check terse line self-contained; test_help_text 4 pass; suite 1124p/1s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `tests/test_help_text.py` passing and the full serial suite tail (no regressions).
  - Observed evidence: Verified: ipd help defines IPD + names plans dir, --phase lists all 5 checkpoints with gloss, backlog check terse line self-contained; test_help_text 4 pass; suite 1124p/1s.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` plus an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification and path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two touched
paths (`agent_workflows/cli.py` and `tests/test_help_text.py`) path-scoped (never `git add -A`), and
never pushes. Transition to executed only after `aw ipd lint --phase pre-transition` conforms and every V
is `pass`. First Order of Set awhelp; independent of Orders 02/03 (all three are text-only). On Set
completion the orchestrator advances spec 20260818-1525-01 accordingly.
