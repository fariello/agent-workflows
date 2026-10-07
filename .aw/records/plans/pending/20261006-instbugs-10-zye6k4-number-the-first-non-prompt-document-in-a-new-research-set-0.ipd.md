# IPD: Number the first non-prompt document in a new research set 01, keeping 00 for the originating prompt

- Date: 2026-10-06
- Kind: child
- Concern: Defect D12 of research report `l6cbbb`, present at HEAD `474b037a9`. `research_cmd.plan_new` takes the order from `research_cmd._next_order_for_set`, whose docstring is "Return the next NN for an existing set (max existing + 1), or 0 for a new set." So the FIRST document of a new set is numbered `00` whatever its kind; in the scratch target `aw research new --kind research-report --apply` and `aw adopt --apply` (which derives names through `research_cmd.plan_new`) both produced `...-00-<id6>-...research-report.md`. The naming contract reserves `00` for the originating prompt: spec `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md` says "`00` is the originating prompt (Section 4.6); `01..NN` are members", the installed research README says "(`00` is the originating prompt)", and `research_cmd.plan_new_comparison` already scaffolds "# 00 = originating prompt". But the same spec's Section 5.1 says `aw research new` should "create a new set at `NN=00`", which is the contradiction the code implemented. There is also no way to choose an order explicitly.
- Scope: IN: when a NEW set's first document is not a `research-prompt`, number it `01` (a `research-prompt` opening a new set stays `00`); existing sets keep max+1; add `--order NN` to `aw research new` and `aw adopt` (refused if that order is already taken in the set); amend spec Section 5.1 to match Section 4.6 and record the amendment with `aw specs note`; adjust the research README template line if wording needs it; tests. OUT: renaming existing files numbered `00` that are not prompts (maintainer ruling: existing files are not renamed); the comparison scaffold (already correct); companion files (backlog `bh1cy5`).
- Scope-Paths: agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/cli.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/system/workflows/templates/agents-docs-research-README.md, tests/test_research_first_order.py, tests/test_research_cmd_create.py, tests/test_artifact_adopt.py, tests/test_research_date_containment.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 10
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: zye6k4

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Reviewed at lane HEAD `24891c7c0`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced D12 for new-set report, prompt, singleton and adopt in a scratch target (F-05); a throwaway-copy mutation of exactly the proposed rule failed five existing tests (F-06). Fixed: the five tests pinning the old `00` rule are named in E-02 and their files added to Scope-Paths (PR-001); singleton path probed and tested (PR-002); `--order` threading, exit 2, range, refusal before mint or write, and `--order 00` into an existing set specified (PR-003); spec 5.1 Inputs list gains `--order`, `aw specs check` and the spec-edit rationale added (PR-004); `Carrier-Declined:` replaces the malformed carrier failing `check.ipd-uncarried-obligation`, `- Blocks-Release: next` added (PR-005); gate gains honesty rule, scope fence, spec-edit declaration, temp HOME and conditional finalize ownership (PR-006).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 10 of Set `instbugs` after reproducing `00` on a new-set `research-report` from both `aw research new --apply` and `aw adopt --apply`, and recording the maintainer's 2026-10-06 ruling (OQ-01).

## Goal

A new research set's first non-prompt document is numbered `01`, so `00` reliably means "the originating prompt" everywhere, the spec says one thing instead of two, and a user can pick an order explicitly when they need to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: in a temp git repo installed with `AW_NO_REEXEC=1 HOME=<tmp> aw install . -y --preset private-target`, run `aw research new --set probe1 --kind research-report --slug a --apply`, `aw research new --set probe2 --kind research-prompt --slug b --apply`, `aw research new --kind findings --slug single --apply` (singleton), and `aw adopt .aw/inbox/ext.md --kind findings --slug ext --set probe3 --apply` of a dropped inbox file; paste the resulting filenames. If the non-prompt files are already `01`, record that and drop E-02.
  - Depends on: none
  - Expected outcome: `00` on all four pasted with the HEAD sha (reproduced at review, F-05).
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Change the new-set order rule in `research_cmd.plan_new`: an empty set yields `0` only when the (already normalized) kind is `research-prompt`, otherwise `1`; a non-empty set still yields max+1 (so a prompt added to an existing set is NOT moved to `00`; that is what `--order 00` in E-03 is for). Keep the rule in one place (`_next_order_for_set` gains the kind, and its docstring is updated) so `artifact_adopt.plan_adoption`, which derives names through `plan_new`, inherits it without its own copy. Update the existing tests that pin the old `00` behavior to the new rule, re-derived at execution by running the research and adopt test files after the change; at review a mutation of exactly this rule failed five: `tests/test_research_cmd_create.py` `test_nn_increments_on_second_same_set_call` and `test_singleton_derives_set_from_slug`, `tests/test_artifact_adopt.py` `test_the_same_set_groups_successive_adoptions`, and `tests/test_research_date_containment.py` `test_conforming_dry_run_previews_and_exits_zero` and `test_conforming_date_byte_identical`. Change each expectation from `00`-first to `01`-first; do not weaken or delete any.
  - Depends on: E-01
  - Expected outcome: the E-01 probes yield `01` for the report, the singleton and the adopted file and `00` for the prompt; every previously failing pinned test passes with its updated expectation.
  - Execution state: pending

- [ ] E-03 Add `--order NN` to `aw research new` and `aw adopt` (argparse in `cli.py` beside each verb's `--date`, `type=int`, default `None`; threaded through `research_cmd.run_new` and `artifact_adopt.run_adopt`/`plan_adoption` into a new `plan_new(order=...)` keyword): accepts 0-99 (refuse others with exit 2), formats as two digits, and refuses with exit 2 and a message naming the occupying file when that order is already taken in the set (scan with the same `parse_name` walk `_next_order_for_set` uses). The refusal must come before an id6 is minted or anything is written, in both preview and `--apply`.
  - Depends on: E-02
  - Expected outcome: `--order 03` on a new set yields `03`; `--order 00` adds a `research-prompt` to an existing set whose `00` is free; `--order` on an occupied slot exits 2 naming the occupant and writes nothing; `--order 100` exits 2.
  - Execution state: pending

- [ ] E-04 Amend spec `20260730-2152-01` Section 5.1: replace "or create a new set at `NN=00`" with wording that a new set starts at `NN=01` unless the document is a `research-prompt` (Section 4.6), and add `--order` to that section's "Inputs" list as an explicit override refused on an occupied slot; record it with `aw specs note .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md --message "..."` citing this plan and the maintainer ruling. Check the research README template's "`00` is the originating prompt" line still reads correctly and adjust only if needed (expected: unchanged, since the rule now matches it).
  - Depends on: E-03
  - Expected outcome: the naming list ("`00` is the originating prompt (Section 4.6)"), Section 4.6 ("the prompt is `NN=00` of its research set") and Section 5.1 agree; the spec's workflow history carries the note; `aw specs check` reports no new finding on the spec.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_research_first_order.py`: through the real CLI in a temp repo (subprocess or `cli.main`, with `HOME`/`XDG_CONFIG_HOME` isolated as in `tests/test_research_date_containment.py` `setUp`), assert (a) a new-set `research-report` is `01`; (b) a new-set `research-prompt` is `00`; (c) a second document in an existing set is max+1; (d) `aw adopt --apply` into a new set is `01`; (e) `--order 03` yields `03`; (f) `--order` on an occupied slot exits 2, names the occupant, and writes no file; (g) a singleton (no `--set`) non-prompt is `01`; (h) `--order 00` adds a prompt to an existing set. Prove (a) can fail by reverting the rule and pasting the failure, then restore it.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails; assertions are on created filenames and exit codes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_adopt` "DERIVES the conforming name by CALLING ``research_cmd.plan_new``", so fixing `plan_new` fixes adopt.
- Only kind `research-prompt` is a prompt in the research kind vocabulary; `plan_new` normalizes `kind` through `research_contract.normalize_kind` before it computes the order, so the rule compares the canonical value.
- `aw research set-assign --order` already exists and renumbers sequentially (`research_refs.plan_set_assign` `start_order`); it is a different verb and unchanged here.
- The installer writes each research README from `.aw/system/workflows/templates/agents-docs-<bucket>-README.md` (`engine.py` `f"agents-docs-{tmpl_bucket}-README.md"`); this repo's own `.aw/records/research/README.md` carries the same "`00` is the originating prompt" line.
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
| F-05 | Reproduced at review HEAD `24891c7c0`. | scratch `private-target` install: `aw research new` report in new set `zprobe1` -> `-zprobe1-00-`; prompt in `zprobe2` -> `-00-`; second doc in `zprobe1` -> `-01-`; singleton findings -> `-zsingle-00-`; `aw adopt --set zprobe3 --apply` -> `-zprobe3-00-`; neither `research new --help` nor `adopt --help` mentions `--order` |
| F-06 | Five existing tests pin the old rule. | in a throwaway copy, `if order_n == 0 and kind != "research-prompt": order_n = 1` after `_next_order_for_set` in `plan_new`, then the research and adopt test files: "5 failed, 182 passed" (the five named in E-02) |
| F-07 | The spec also states the prompt rule in Section 4.6. | "the prompt is `NN=00` of its research set (it joins the cohort as the read-order-0 member)" |

## Proposed changes (ordered, validatable)

1. Kind-aware new-set order rule (E-02).
2. `--order` override on both verbs (E-03).
3. Spec 5.1 amendment with history note (E-04).
4. Behavior tests with mutation proof (E-05).

## Deferred / out of scope (with reason)

- Renaming existing non-prompt `00` files: maintainer ruling 2026-10-06 (OQ-01) is not to rename.
  - Carrier-Declined: deliberately not done per the maintainer ruling recorded in OQ-01; no follow-up obligation exists.
- Companion files for research documents (D13).
  - Carrier: bh1cy5
- The whole-Set regression asserting `01` numbering after composed research verbs.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: none. The five pinned tests (F-06) are updated in E-02 because they encode the old rule, not an invariant.

## Required tests / validation

- `tests/test_research_first_order.py` (E-05) with the mutation proof; narrowed run as `python3 -m pytest -o addopts="" tests/test_research_first_order.py`.
- The research and adopt test files (`tests/test_research*.py`, `tests/test_artifact_adopt.py`) pass after E-02's expectation updates.
- Bare `python3 -m pytest` summary line pasted, before the edit and after.

## Spec / documentation sync

- Spec `20260730-2152-01` Section 5.1 amended and noted (E-04); research README template checked (E-04). WHY a plan edits an implemented spec: Section 5.1 contradicts the same spec's naming list and Section 4.6, the code implemented the contradicting sentence, and the maintainer ruled for the naming-list reading (OQ-01); leaving 5.1 unedited would make the spec contradict the shipped code instead.

## Open questions

### OQ-01: What number should the first non-prompt document of a new set get?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by the maintainer on 2026-10-06, choosing the recommended option when asked: a non-prompt document that opens a new set gets `01` (`00` stays reserved for a prompt); add `--order` to `aw research new` and `aw adopt`; amend spec `20260730-2152-01` Section 5.1; existing files are not renamed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the four pre-edit filenames with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same four probes post-edit (`01`, `00`, `01`, `01`), the `git diff` of `agent_workflows/research_cmd.py`, and the run of the five previously pinned tests passing with the diff of their changed expectations.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `--order 03` filename, the `--order 00` prompt-into-existing-set filename, the occupied-slot refusal with its exit status and a directory listing showing nothing was written, and the `--order 100` refusal, for both `aw research new` and `aw adopt`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the amended Section 5.1 sentence and Inputs list, the new `## Workflow history` line from the spec, and the `aw specs check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file (cases (a) to (h) passing), the mutation failure output for case (a), and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the numbering rule, its override, and the spec sentence that states it are one contract change.

EXECUTION CONTRACT. OQ-01 is resolved (maintainer, 2026-10-06); no question is open. Execute E-items in order (E-01 to E-05). Commit only files changed for this plan through `aw commit zye6k4 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SPEC EDIT: this plan amends implemented spec `20260730-2152-01` (declared in `- Scope-Paths:`, reason in the spec-sync section). SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example another test found pinning the old rule) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize zye6k4`, never by a hand `git mv`.
