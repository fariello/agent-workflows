- Id: imntrh
- Status: open
- Blocks-Release: next
- Set: researchstate
- Priority: medium
- Work-Kind: bug
- Summary: Research status enum fits only answer docs: split pipeline position (derived, set-level) from shelf disposition, and let the research set own the prompt

## Workflow history
- 2026-09-12 open (aw set): status set to open
- 2026-09-11 created (aw backlog): DECIDED (maintainer 2026-09-11): the research SET owns the prompt as order 00; the duplicate prompts/ staging copy is retired for the research kind. Prompt carries NO typed status; pipeline position is DERIVED from set shape (unrun/partial/synthesized). Measured: STATUSES (research_contract.py:187) is not keyed by kind and research_cmd.py:203,259,267 hard-codes status=todo for all 17 kinds including the order-00 prompt, so one token means 'not yet ingested' on a report and 'never dispatched' on a prompt, and NO state can say a prompt was run (3nlmug reads todo while carrying outcome: adopted, consumed-by: [25kzda]). The parent spec knew and routed around it (:79 'NO new state'), making runnedness structural in derive_unrun_prompts (research_index.py:256), which is why aw research pending is the real authority and not the todo column. Cost observed: aw att --type research showed 14 rows where only 4 (q65sz3, ti73qs, 5ek188, nilw5h) were genuinely open, 8 were stale-status finished artifacts, and 2 (sx0cqv, 8it88r) had answers already delivered. Prompts are also double-homed against their own README: 18 of 44 sets carry an order-00 prompt and 4 (hostprobe, awdeliv, chkplace, wtiso) exist in BOTH trees, with the wtiso staging copy in executed/ still reading Status: pending inline.

DECIDED BY THE MAINTAINER 2026-09-11: the RESEARCH SET owns the research prompt as order `00`; the
duplicate staging copy under `.aw/records/prompts/` is retired for the `research` kind. `prompts/`
keeps only the `run-once` and `session-handoff` kinds. A research prompt carries NO hand-typed
status; its pipeline position is DERIVED from set shape.

## The defect, measured 2026-09-11 at a clean HEAD

ONE STATUS ENUM IS APPLIED TO SEVENTEEN KINDS AND ONLY FITS ANSWER DOCUMENTS.
`research_contract.py:187` defines `STATUSES = {todo, active, reference, archive}` and it is NOT
keyed by kind. `research_cmd.py:203` and `:259` hard-code `status="todo"` at creation for every
kind, including the order-`00` prompt that `new-comparison` scaffolds at `:267`. So one token
carries two unrelated meanings: on a report it means "not yet ingested" (the document is complete;
the pending work is consumption), and on a prompt it means "never dispatched to a model" (the
document is complete as a prompt; the pending work is running it).

THERE IS NO STATE FOR A PROMPT THAT HAS BEEN RUN. `reference` and `archive` are both cold-shelf
dispositions, so a prompt whose reports landed still reads `todo` forever. Live instance: `3nlmug`
reads `status: todo` while carrying `outcome: adopted` and `consumed-by: [25kzda]`; it is prompt
provenance for a spec already written, and the vocabulary cannot say so.

THE SPEC KNEW AND ROUTED AROUND IT. `20260824-2000-01-research-lifecycle-reliability.spec.md:79`
states "`status` stays the four-state vocabulary; NO new state", and §3.1 instead makes runnedness
STRUCTURAL via `derive_unrun_prompts` (`research_index.py:256`): a set is UNRUN when its `NN=00`
member is a `research-prompt` and no `NN>=01` sibling exists. That is why `aw research pending`
exists as a separate query and is the real authority, not the `todo` column.

THE OBSERVABLE COST. `aw att --type research` showed 14 rows; only 4 were genuinely open research
(`q65sz3`, `ti73qs`, `5ek188`, `nilw5h`). Eight were finished artifacts whose status was merely
stale, and two (`sx0cqv`, `8it88r`) had answers already delivered and awaiting adoption. This is
the SAME failure the parent spec §1 documented (11 docs at `intake` though 10 were adopted),
re-introduced because state was made tool-WRITTEN-at-creation but never tool-MAINTAINED.

PROMPTS ARE DOUBLE-HOMED WITH CONTRADICTORY LIFECYCLES. `.aw/records/prompts/README.md` states the
convention: "The PROMPT lives here. Its RESULTS are filed under `.aw/records/research/`", and gives
a prompt a real run lifecycle by directory (`pending/` -> `executed/`, plus `superseded/`,
`not-executed/`, `reusable/`). But the tool writes a prompt into the research set anyway: 18 of 44
research sets carry an order-`00` prompt, and FOUR sets exist in BOTH trees (`hostprobe`, `awdeliv`,
`chkplace`, `wtiso`). The two copies also disagree on their own state: the staging copy of the
`wtiso` prompt sits in `executed/` while its leading metadata comment still reads `Status: pending`.

## The shape to build

TWO AXES, because the current field conflates them.

AXIS 1, PIPELINE POSITION. SET-level, DERIVED, never hand-typed. This models the actual process:
fan out one prompt to several models, then fan in to one synthesis.

| State | Derivation |
|---|---|
| `unrun` | an `NN=00` `research-prompt` exists and no `NN>=01` sibling does |
| `partial` | model reports exist but the declared fan-out width is unmet, or no synthesis member exists |
| `synthesized` | a `reconciliation-report` (or terminal `findings`) member exists |

`unrun` and `synthesized` are already computable today (`derive_unrun_prompts`,
`run_prompt_set_ids`). `partial` is the one currently inexpressible, and it is where this process
spends most of its time: dispatched to three models, two returned. `new-comparison` already knows
the declared model list at scaffold time (`research_cmd.py:210-234`), so the expected width is
available to compare against.

AXIS 2, SHELF DISPOSITION. Per-document, and asked ONLY of answer documents. Keep
`todo`/`active`/`reference`/`archive` unchanged; it models ingestion and coldness correctly.

A PROMPT CARRIES NO TYPED STATUS. Its runnedness is a fact about whether siblings exist, so a typed
`status` on a prompt is a claim the file cannot substantiate. This follows the standing house rule
against hand-writing a field that is an output of a step you are not performing.

DO NOT give each of the 17 kinds its own state machine. Only `research-prompt` and
`reconciliation-report` are structurally special; the other 15 are all answers sharing one axis.

## Known edges the implementation must handle

- `derive_unrun_prompts` keys on kind + order, so it FALSE-POSITIVES on a prompt filed as provenance
  after the fact (`3nlmug`, currently reported by `aw research pending`) and MISSES a prompt filed
  as a singleton outside a set.
- `aw research pending` also lists three legacy prompts already shelved to `reference`/`archive`
  (`jd8qhs`, `g5vhpz`, `2838rp`), so the derivation needs to respect cold dispositions.
- 26 of 44 sets have NO order-`00` prompt at all (externally-authored drops, in-repo findings), so
  the pipeline axis must be absent rather than `unrun` for a set that never had a prompt.
- Retiring the staging copies is a `git mv` to `superseded/` with the required `RETIRED` header per
  `prompts/README.md`, never a delete.

## Follow-on cleanup this item does NOT own

The eight stale rows want `aw research set-outcome` / `aw research promote --to reference`, and
`sx0cqv`'s three delivered reports are sitting unadopted in the gitignored `.aw/inbox/`. Both are
data cleanup, separable from the vocabulary change.
