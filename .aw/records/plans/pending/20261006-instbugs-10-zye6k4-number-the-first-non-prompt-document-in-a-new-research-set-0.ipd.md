# IPD: Number the first non-prompt document in a new research set 01, keeping 00 for the originating prompt

- Date: 2026-10-06
- Kind: child
- Concern: Defect D12 of research report `l6cbbb`, present at HEAD `474b037a9`. `research_cmd.plan_new` takes the order from `research_cmd._next_order_for_set`, whose docstring is "Return the next NN for an existing set (max existing + 1), or 0 for a new set." So the FIRST document of a new set is numbered `00` whatever its kind; in the scratch target `aw research new --kind research-report --apply` and `aw adopt --apply` (which derives names through `research_cmd.plan_new`) both produced `...-00-<id6>-...research-report.md`. The naming contract reserves `00` for the originating prompt: spec `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md` says "`00` is the originating prompt (Section 4.6); `01..NN` are members", the installed research README says "(`00` is the originating prompt)", and `research_cmd.plan_new_comparison` already scaffolds "# 00 = originating prompt". But the same spec's Section 5.1 says `aw research new` should "create a new set at `NN=00`", which is the contradiction the code implemented. There is also no way to choose an order explicitly.
- Scope: IN: when a NEW set's first document is not a `research-prompt`, number it `01` (a `research-prompt` opening a new set stays `00`); existing sets keep max+1; add `--order NN` to `aw research new` and `aw adopt` (refused if that order is already taken in the set); amend spec Section 5.1 to match Section 4.6 and record the amendment with `aw specs note`; adjust the research README template line if wording needs it; tests. OUT: renaming existing files numbered `00` that are not prompts (maintainer ruling: existing files are not renamed); the comparison scaffold (already correct); companion files (backlog `bh1cy5`).
- Scope-Paths: agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/cli.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/system/workflows/templates/agents-docs-research-README.md, tests/test_research_first_order.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 10
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: zye6k4

## Workflow history

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 10 of Set `instbugs` after reproducing `00` on a new-set `research-report` from both `aw research new --apply` and `aw adopt --apply`, and recording the maintainer's 2026-10-06 ruling (OQ-01).

## Goal

A new research set's first non-prompt document is numbered `01`, so `00` reliably means "the originating prompt" everywhere, the spec says one thing instead of two, and a user can pick an order explicitly when they need to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: in a temp repo with an installed `.aw` layout, run `aw research new --set probe1 --kind research-report --slug a --apply`, `aw research new --set probe2 --kind research-prompt --slug b --apply`, and `aw adopt --apply` of an inbox file into a new set; paste the resulting filenames. STOP and report if the report and adopted file are already `01`.
  - Depends on: none
  - Expected outcome: `00` on all three pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Change the new-set order rule used by `research_cmd.plan_new`: an empty set yields `0` only when the requested kind is `research-prompt`, otherwise `1`; a non-empty set still yields max+1. Keep the rule in one place (`_next_order_for_set` gains the kind, or `plan_new` applies it) so `artifact_adopt`, which derives names through `plan_new`, inherits it without its own copy.
  - Depends on: E-01
  - Expected outcome: the E-01 probes yield `01` for the report and the adopted file and `00` for the prompt.
  - Execution state: pending

- [ ] E-03 Add `--order NN` to `aw research new` and `aw adopt` (argparse in `cli.py`, threaded into `plan_new`): accepts 0-99, formats as two digits, and refuses with a clear message naming the occupying file when that order already exists in the set.
  - Depends on: E-02
  - Expected outcome: `--order 03` on a new set yields `03`; `--order` on an occupied slot exits non-zero naming the occupant.
  - Execution state: pending

- [ ] E-04 Amend spec `20260730-2152-01` Section 5.1: replace "or create a new set at `NN=00`" with wording that a new set starts at `NN=01` unless the document is a `research-prompt` (Section 4.6), and that `--order` overrides; record it with `aw specs note <spec> --message "..."` citing this plan. Check the research README template's "`00` is the originating prompt" line still reads correctly and adjust only if needed.
  - Depends on: E-03
  - Expected outcome: Sections 4.6, the naming list, and 5.1 agree; the spec's workflow history carries the note.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_research_first_order.py`: through the real CLI in a temp repo, assert (a) a new-set `research-report` is `01`; (b) a new-set `research-prompt` is `00`; (c) a second document in an existing set is max+1; (d) `aw adopt --apply` into a new set is `01`; (e) `--order 03` yields `03`; (f) `--order` on an occupied slot exits non-zero and names the occupant. Prove (a) can fail by reverting the rule and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails; assertions are on created filenames and exit codes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_adopt` "DERIVES the conforming name by CALLING ``research_cmd.plan_new``", so fixing `plan_new` fixes adopt.
- Only kind `research-prompt` is a prompt in the research kind vocabulary.
- Spec status and history are owned by `aw specs` (`note` adds a history line); an implemented spec may receive a dated amendment note.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | A new set always starts at 0. | `research_cmd._next_order_for_set` docstring "or 0 for a new set" and `return (max(orders) + 1) if orders else 0` |
| F-02 | Both verbs produce `00` reports. | scratch target: `aw research new --kind research-report --apply` and `aw adopt --apply` both wrote `-00-` names |
| F-03 | The spec contradicts itself. | spec `20260730-2152-01` naming list "`00` is the originating prompt (Section 4.6)" versus Section 5.1 "create a new set at `NN=00`" |
| F-04 | The comparison scaffold is already right. | `research_cmd.plan_new_comparison` "# 00 = originating prompt" then "# 01..N = one report per model" |

## Proposed changes (ordered, validatable)

1. Kind-aware new-set order rule (E-02).
2. `--order` override on both verbs (E-03).
3. Spec 5.1 amendment with history note (E-04).
4. Behavior tests with mutation proof (E-05).

## Deferred / out of scope (with reason)

- Renaming existing non-prompt `00` files: maintainer ruling 2026-10-06 (OQ-01) is not to rename.
  - Carrier: none (ruled out)
- Companion files for research documents (D13).
  - Carrier: bh1cy5
- The whole-Set regression asserting `01` numbering after composed research verbs.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `tests/test_research_first_order.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- Spec `20260730-2152-01` Section 5.1 amended and noted (E-04); research README template checked (E-04).

## Open questions

### OQ-01: What number should the first non-prompt document of a new set get?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by the maintainer on 2026-10-06, choosing the recommended option when asked: a non-prompt document that opens a new set gets `01` (`00` stays reserved for a prompt); add `--order` to `aw research new` and `aw adopt`; amend spec `20260730-2152-01` Section 5.1; existing files are not renamed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the three pre-edit filenames with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same three probes post-edit (`01`, `00`, `01`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `--order 03` filename and the occupied-slot refusal with its exit status.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the amended Section 5.1 sentence and the new `## Workflow history` line from the spec.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the numbering rule, its override, and the spec sentence that states it are one contract change.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit zye6k4 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed zye6k4`.
