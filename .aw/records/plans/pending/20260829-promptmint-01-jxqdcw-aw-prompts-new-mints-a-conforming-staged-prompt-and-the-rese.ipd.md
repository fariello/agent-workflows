# IPD: aw prompts new mints a conforming staged prompt, and the research producer workflow calls it

- Date: 2026-08-29
- Kind: child
- Concern: There is no `aw` verb that creates a file in the operational prompt STAGING lane `.aw/records/prompts/pending/`, so the `/aw research` producer workflow instructs the agent to HAND-NAME the file and HAND-WRITE its metadata comment. That violates the house rule that conforming artifacts are created by verbs, and it does not merely risk drift, it has already produced it: only 7 of the 13 prompts in `executed/` carry the leading `aw-prompt` metadata comment at all, and the staging README and the workflow disagree about whether the filename ends `.md` or `.prompt.md`.
- Scope: Add `aw prompts new` to mint a conforming staged prompt file (correct clustered/legacy name, leading `aw-prompt` metadata comment, `Status: pending`, landing in `.aw/records/prompts/pending/`, dry-run by default, never auto-staged), and change the `research-prompt` workflow to call it instead of hand-writing. Excludes `aw prompts check` (the prompt-purity lint, already specified separately and still unimplemented), excludes any change to the prompt LIFECYCLE verbs, and excludes touching `.aw/records/research/` or the `aw research` verb family.
- Scope-Paths: agent_workflows/prompts.py, agent_workflows/cli.py, agent_workflows/artifact_types.py, .aw/system/workflows/research-prompt/research-prompt.md, tests/test_prompts_new.py
- Item-Dependencies: none
- Status: to-review
- Set: promptmint
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: jxqdcw
- Blocks-Release: next
- From-Backlog: i97baj

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `i97baj` during the blocking-backlog graduation sweep. The item's OPEN DESIGN QUESTION (a standalone `aw prompt` noun versus extending `aw research`) is RESOLVED from repository evidence rather than left to the maintainer: an APPROVED spec already establishes the `aw prompts <verb>` namespace by name, and `prompts` is already a registered artifact type with a `prompt` facet and working `rename`/`group` verbs, so the namespace is settled and this plan only adds the missing `new`. See F1 and OQ-01. Two facts the item did not record were measured and change the work: the metadata comment is missing from 6 of 13 executed prompts (F3), and the documented filename grammar is self-contradictory across two authoritative files (F4).

## Goal

Make a staged prompt a tooled artifact like every other record in this repo. One verb mints it with the right name and the right metadata, the producer workflow calls that verb, and the naming contradiction that made hand-writing ambiguous is resolved rather than perpetuated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: settle the name, then mint it

- [ ] E-01 RESOLVE THE FILENAME CONTRADICTION FIRST, because the verb cannot emit a conforming name until the repo agrees what one is, and this must be decided in the plan rather than improvised by the executor. Measured conflict (F4): `.aw/records/prompts/README.md` documents `YYYYMMDD-HHMM-NN-<slug>.md`, while the `research-prompt` workflow's Step 4 and exit gate specify `YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`, and separately the uniform artifact grammar registers a `prompt` facet with `prompts` in `TYPE_FACET`, which points at a THIRD possibility (a clustered `YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md` name). On-disk evidence: every file in `executed/` uses the legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` shape, i.e. the facet IS present in practice while the README omits it. RECOMMENDED RESOLUTION for the approver: emit the legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` shape, matching what is actually on disk and what `artifact_naming` documents for the id6-less types, and CORRECT the README to include the `.prompt.md` facet. Do NOT mint an id6-clustered name in this plan: `artifact_naming`'s own docstring states prompts are among the types it does NOT add an id6 to, and doing so would be a corpus-wide naming change well beyond this item. If the approver prefers the clustered id6 form, this plan needs re-scoping.
  - Depends on: none
  - Expected outcome: ONE documented filename grammar for a staged prompt, recorded in the plan with the decision and its rationale; the README no longer contradicts the workflow; and the choice is consistent with the existing on-disk corpus.
  - Execution state: pending

- [ ] E-02 Add a new `agent_workflows/prompts.py` module with a `run_new(args)` following the ESTABLISHED owner-verb shape rather than a new one. Copy the structure of `specs.run_new` (locate by symbol), which is the closest sibling: resolve the repo root through `project_context.resolve_verb_repo_root`, derive the slug through `artifact_core.kebab` with a length bound, build the destination path, render the file, honor dry-run as the DEFAULT with `--apply` to write, write via `artifact_core.atomic_write`, and emit through the `CommandResult`/`select_output`/`get_renderer` pipeline so `--agent` and `--json` work like every other verb. Do NOT invent a bespoke output path or a bare `print`. Compute the `NN` per-minute sequence by inspecting existing files for that `YYYYMMDD-HHMM` prefix so a second prompt in the same minute gets `02`, and note the sequence must consider the WHOLE prompts tree, not only `pending/`, or a prompt minted after an earlier one moved to `executed/` can collide.
  - Depends on: E-01
  - Expected outcome: `aw prompts new --kind research --slug x` previews a conforming path and body and writes NOTHING; with `--apply` it writes exactly that file; `--agent` emits the standard JSONL result; a second call in the same minute yields `NN=02`; the sequence does not collide with a file already moved out of `pending/`.
  - Execution state: pending

- [ ] E-03 Emit the leading metadata comment as a SINGLE line, exactly as the purity contract requires. The line takes the documented form `<!-- aw-prompt: Kind: <kind> | Status: pending | Created: <date> | Author: <agent> | Targets: ... | Concerns: ... -->` and must be the FIRST line of the file. Two properties are load-bearing and must not be broken by rendering convenience: it is an HTML comment so it is invisible when the prompt is pasted into a chat, and it is ONE line so nothing before the prompt body can be mistaken for prompt content. Accept `--kind` (default `research`), plus optional `--targets`, `--concerns`, `--author`, and `--status` (defaulting to `pending`), and validate `--kind` against the recognized kinds documented in the staging README (`run-once`, `research`, and `session-handoff` are the ones actually in use; enumerate from the README rather than inventing a set). Emit NO body boilerplate beyond what the caller supplies, because the prompt-purity contract forbids any content in the file that is not the prompt itself, and a helpful template comment would violate it.
  - Depends on: E-02
  - Expected outcome: the minted file's first line is a single-line `aw-prompt` HTML comment carrying the supplied fields; an unrecognized `--kind` is rejected with a nonzero exit; the file contains no user-facing scaffolding or placeholder prose that would breach prompt purity.
  - Execution state: pending

- [ ] E-04 Register the verb so it is discoverable and dispatchable: add the `prompts` subparser with a `new` subcommand at the two CLI edit points in `cli.py` (the parser builder and the dispatcher; locate them by how `specs` is registered), and add `"new": "prompts.run_new"` to the `prompts` entry in `artifact_types.TYPE_BACKENDS`, which today lists only `rename` and `group`. Note that `prompts` is currently NOT a valid top-level `aw` command at all (measured: `aw prompts check` errors with `invalid choice: 'prompts'`), so this E-item CREATES the namespace the approved prompt-purity spec already assumes. Leave room for that spec's `check` verb rather than designing it: register the noun and the one verb this plan owns, and do not stub `check`.
  - Depends on: E-02, E-03
  - Expected outcome: `aw prompts new --help` works, `aw prompts --help` lists `new`, `python3 -m agent_workflows prompts new` reaches the same code path, and the backend registry resolves `("prompts", "new")`; no `check` stub is added.
  - Execution state: pending

### Task group 2: make the workflow use it, and prove the whole thing

- [ ] E-05 Rewrite the `research-prompt` workflow so it CALLS the verb instead of hand-naming and hand-writing. Concretely, Step 4 currently instructs the agent to "Determine the timestamp and sequence number" and "Write the file", which is precisely the untooled behavior the backlog item objects to; replace that with an `aw prompts new` invocation supplying `--kind research` and the metadata fields, then have the agent write only the PROMPT BODY into the minted file. Update the exit gate accordingly, and keep the two existing requirements that must survive: run `aw check-local-leaks` on the finished file, and NEVER auto-stage or commit it. Also fix the naming line in this file to match E-01's resolution. Keep all prose free of em and en dashes per the execution contract, since this is an agent-facing workflow file that a human also reads.
  - Depends on: E-01, E-04
  - Expected outcome: the workflow no longer tells an agent to compute a filename or hand-write metadata; it names the exact `aw prompts new` invocation; the leak-scan and no-auto-commit requirements are intact; the exit gate checks the verb was used.
  - Execution state: pending

- [ ] E-06 Add `tests/test_prompts_new.py` covering: dry-run writes NOTHING (assert the directory is unchanged) while printing the intended path; `--apply` writes exactly one file at the resolved path; the first line is a single-line `aw-prompt` comment with the supplied `Kind`, `Status: pending`, and `Created`; the per-minute sequence increments to `02` on a second call in the same minute; the sequence does NOT collide with a same-minute file that already sits in `executed/` (the E-02 whole-tree requirement); an unrecognized `--kind` exits nonzero and writes nothing; `--agent` output is parseable as the standard result envelope; and the minted file passes a purity property, namely that nothing precedes the comment and the comment occupies exactly one line. Pin the clock rather than depending on wall time, so the sequence tests are deterministic and parallel-safe under `xdist`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the module passes deterministically under the default parallel invocation; the dry-run, collision, and rejection cases each fail against a naive implementation that writes eagerly, sequences within `pending/` only, or accepts any kind.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The `aw prompts <verb>` NAMESPACE IS ALREADY SANCTIONED, which is what resolves the item's open design question. The APPROVED spec `prompt-purity lint` names `aw prompts check` throughout and states explicitly that its implementation "also establishes the `aw prompts <verb>` namespace for future prompt tooling". This plan adds `new` into a namespace the repo already decided on, rather than choosing between competing nouns.
- `prompts` is ALREADY a first-class artifact type. It appears in `artifact_types.ARTIFACT_TYPES`, maps `prompt` to `prompts` in the singular alias table, carries a `prompt` facet in `artifact_naming.TYPE_FACET` and `ARTIFACT_TYPE_FACETS`, and already has working `rename` and `group` backends. The ONLY missing verb is `new`, which is exactly the gap the backlog item describes.
- Nothing in the package writes to `.aw/records/prompts/` today. A grep for `prompts/pending` across `agent_workflows/` finds only a docstring EXAMPLE in `agy_run.py`, confirming the tree is currently maintained entirely by hand.
- `aw specs new` is the model to copy, and copying it is the point. It mints, previews by default, writes atomically, and emits through the shared result renderer. It is also the precedent for a verb creating a conforming artifact in a tree that was previously hand-maintained.
- The two prompt homes are DELIBERATELY distinct and this plan must not merge them: `.aw/records/prompts/` is operational staging ("what prompt is queued to run?") whose lifecycle is encoded by moving the file between buckets, while `.aw/records/research/` holds the durable RESULTS. The staging README states this explicitly as the prompt-to-results convention, and the workflow file restates the division of labor. So extending `aw research` would have been the wrong answer regardless of the namespace evidence.
- Prompt purity is a CONTRACT, not a preference: the emitted file contains only the prompt addressed to the target AI, with pipeline metadata confined to the single leading HTML comment precisely because that is invisible when pasted. This constrains E-03 to emit no template body.
- The staging tree has a gitignored `local/` quarantine lane for raw or sensitive drafts, and promotion out of it is described as a deliberate human act, never automatic. This plan's verb targets `pending/` only and must not write to or promote from `local/`.
- The suite is invoked BARE and runs under `xdist`, so any test asserting a per-minute sequence must pin the clock rather than race real time.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | approved spec `prompt-purity lint`; `artifact_types.py`; `artifact_naming.py` | THE ITEM'S OPEN DESIGN QUESTION IS ALREADY ANSWERED BY THE REPO. The item asks whether to extend `aw research` or create a new noun. An APPROVED spec already names `aw prompts check` and says its implementation establishes the `aw prompts <verb>` namespace; `prompts` is already a registered artifact type with a `prompt` facet and working `rename`/`group` verbs. So the noun is `prompts`, and this plan adds the missing `new`. No maintainer decision is needed. | spec `- Status: approved`, with `aw prompts check` named in its title, G1, G5, G6, and design section; `TYPE_BACKENDS["prompts"]` currently lists exactly `rename` and `group` |
| F2 | HIGH | `agent_workflows/` | The gap is total, not partial: NO code in the package creates a staged prompt. The only match for the staging path is a docstring example. So there is nothing to extend and the verb is genuinely net-new. | grep for `prompts/pending` across `agent_workflows/*.py` returns only `agy_run.py`'s docstring example |
| F3 | HIGH | `.aw/records/prompts/executed/` | THE DRIFT IS ALREADY REAL, which the item asserts as a risk but does not measure. Only 7 of 13 executed prompts begin with the `aw-prompt` metadata comment; 6 have NONE. Hand-written metadata is therefore not merely untooled, it is unreliably applied, and the verb is the fix rather than a tidiness improvement. | measured at `d4c4a0a`: first-line `aw-prompt` present in 7 files, absent in 6 |
| F4 | HIGH | `.aw/records/prompts/README.md` versus `research-prompt.md` versus `artifact_naming.py` | THE DOCUMENTED FILENAME IS SELF-CONTRADICTORY THREE WAYS, so "write a conforming name" was underdetermined for any hand-authoring agent. The README says `YYYYMMDD-HHMM-NN-<slug>.md`; the workflow says `YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`; the uniform grammar registers a `prompt` FACET and a clustered id6 form. On-disk reality matches the workflow's faceted legacy shape. E-01 must settle this before the verb can emit anything. | README naming paragraph; workflow Step 4 and exit gate; `TYPE_FACET["prompts"] = "prompt"`; every `executed/` filename ends `.prompt.md` |
| F5 | MED | `artifact_naming.py` docstring | The clustered id6 form is NOT available to prompts today by design. The module states that prompts, roadmaps, releases, and walkthroughs "do not yet carry an id6 in most on-disk names" and that it "does NOT add an id6 to those types (out of scope)". So minting an id6-clustered prompt name would contradict the naming authority itself and is correctly out of this plan's scope (E-01). | module docstring, id6-less legacy types paragraph |
| F6 | MED | `cli.py` | `prompts` is not a top-level command at all today, so E-04 CREATES the namespace rather than extending it. This also means the approved purity spec's `aw prompts check` has nowhere to attach yet, which is worth stating so a reviewer does not assume half of it already exists. | measured: `aw prompts check` fails with `invalid choice: 'prompts'` and lists the valid commands; no `agent_workflows/prompts_lint.py` exists |
| F7 | LOW | `.aw/records/prompts/pending/` | The staging lane currently holds exactly ONE prompt plus a README, so this verb's blast radius on existing content is nil and the end-to-end check can be performed without disturbing a queue. | directory listing at `d4c4a0a` |

## Proposed changes (ordered, validatable)

1. Settle the one filename grammar and correct the README that contradicts it (E-01).
2. Add `prompts.run_new` in the established owner-verb shape, previewing by default (E-02).
3. Emit the single-line metadata comment with validated fields and no body boilerplate (E-03).
4. Register the `prompts` noun and its `new` verb in the CLI and the backend registry (E-04).
5. Make the research producer workflow call the verb instead of hand-writing (E-05).
6. Prove dry-run, sequencing, collision, rejection, and purity behavior deterministically (E-06).

## Deferred / out of scope (with reason)

- `aw prompts check`, the prompt-purity lint, is owned by its own APPROVED spec and is NOT implemented here. This plan deliberately registers the namespace without stubbing `check`, so that spec can land its verb cleanly. Note honestly that after this plan the purity contract is still unenforced by tooling; only minting is tooled.
- Adding an id6 to prompt names, or moving prompts onto the clustered grammar, is out of scope per F5 and would be a corpus-wide change.
- Prompt LIFECYCLE movement (pending to executed/superseded/not-executed) stays a `git mv` per the staging README. This plan does not add a `set`-style transition verb, and does not bring prompts into the attention view (they are explicitly deferred there).
- The `local/` quarantine lane and its deliberate human promotion step are untouched.
- `aw research` and `.aw/records/research/` are untouched, since the two homes are deliberately distinct.

## Scope check

- Over-scope: none. The new module holds the verb, `cli.py` registers it, `artifact_types.py` adds the one registry entry, the workflow file is the caller this item exists to fix, and the test module is new.
- `.aw/records/prompts/README.md` IS EDITED under E-01 but is NOT in `Scope-Paths`. This is a deliberate under-scope declaration rather than an oversight: the README is the file carrying the contradictory naming claim (F4), so leaving it wrong would mean shipping a verb that disagrees with its own documentation. RECOMMENDED RESOLUTION for the approver: add `.aw/records/prompts/README.md` to `Scope-Paths`. If the approver declines, E-01 must record that the README remains contradictory and a follow-up is required, and the executor must NOT edit it silently.
- Under-scope otherwise: none outstanding. `cli.py` is frequently dirty from concurrent work and is the subject of several pre-existing CLI-conformance test failures in this repo; expect contention and re-read before editing.
- Note that CLI-surface conformance tests exist in this repo (locate `test_command_surface_declarations` and `test_cli_conformance_matrix`) and have been observed FAILING for undeclared parser leaves during concurrent CLI work. Adding a new subparser may require a declaration in whatever surface manifest those tests consult. Find that requirement BEFORE adding the parser, and if satisfying it means editing a file outside `Scope-Paths`, STOP and report rather than expanding the fence.

## Required tests / validation

- `tests/test_prompts_new.py` must pass with every case in E-06, deterministically under the default parallel invocation. Falsifiability: the dry-run case must fail against an implementation that writes eagerly; the collision case must fail against one that sequences within `pending/` only; the rejection case must fail against one that accepts any `--kind`.
- The CLI-surface conformance tests must pass, since this plan adds a parser leaf. Run them explicitly and paste the result. If they were already failing at your baseline for unrelated undeclared leaves, ATTRIBUTE that by name rather than fixing it, and prove your leaf is not among the offenders.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during this sweep at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Take your own before/after readings with their HEAD; concurrent agents are committing to `cli.py`.
- End-to-end, the property the item asks for: run `aw prompts new` for real, paste the minted path and the file's first line, run `aw check-local-leaks` on it, and confirm it was NOT staged or committed (`git status --porcelain` showing it untracked). Then delete or retire your test artifact so the staging queue is not polluted; the lane currently holds exactly one real prompt (F7).
- Also validate the WORKFLOW change by reading it back: paste the rewritten Step 4 and exit gate, and confirm no instruction to compute a filename or hand-write metadata survives anywhere in the file.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- `.aw/records/prompts/README.md` naming paragraph must be corrected to the E-01 grammar (see the Scope check for the fence question this raises).
- `.aw/system/workflows/research-prompt/research-prompt.md` is rewritten by E-05, including its Step 4, its exit gate, and its naming references.
- The approved `prompt-purity lint` spec should NOT be edited by this plan, but the executor should record in the terminal history that the `aw prompts` namespace it assumed now EXISTS, so whoever implements `check` knows the attachment point is ready.
- AGENTS.md's "Writing prompts for another AI" section governs prompt content, not staging mechanics, and needs no change. Do not edit the managed block.

## Open questions

### OQ-01: Is the verb a standalone `aw prompts` noun or an extension of `aw research`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: STANDALONE `aw prompts new`. Resolved from repository evidence, not preference, which is why this item needs no maintainer round trip despite carrying an explicit open question. Three facts decide it. First, an APPROVED spec already names `aw prompts check` and states that implementing it "establishes the `aw prompts <verb>` namespace for future prompt tooling", so the noun is already sanctioned policy. Second, `prompts` is ALREADY a registered artifact type with a `prompt` facet and working `rename`/`group` backends whose registry entry is simply missing `new`, so this is filling a hole in an existing surface rather than choosing a new shape. Third, the two homes are deliberately distinct: `.aw/records/prompts/` is operational staging whose lifecycle is its directory, while `.aw/records/research/` holds durable results, and both the staging README and the workflow file state that division explicitly. Folding staging into `aw research` would collapse a separation the repo maintains on purpose.

### OQ-02: Which filename grammar should the verb emit?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE LEGACY FACETED FORM `YYYYMMDD-HHMM-NN-<slug>.prompt.md`, and correct the README to match. Resolved from on-disk evidence plus the naming authority's own scope statement. Every file in `executed/` uses that shape, so it is what the corpus actually is; the workflow already specifies it; and `artifact_naming`'s docstring explicitly places prompts among the types it does NOT give an id6, so emitting a clustered id6 name would contradict the module that owns naming (F5). The README's bare `.md` claim is the outlier and is simply wrong against the corpus. NOTE for the approver: this resolution is a documented recommendation rather than a fait accompli, because it entails editing a file outside `Scope-Paths`; see the Scope check.

### OQ-03: Should the verb also write a prompt BODY template?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, emit no body boilerplate. The prompt-purity contract requires the file to contain ONLY the prompt addressed to the target AI, with no user-facing instructions and nothing to strip before uploading, and it confines pipeline metadata to the single leading HTML comment precisely because that is invisible when pasted. A template body or placeholder prose would be content that is not the prompt, i.e. exactly what the contract forbids and what the still-unimplemented purity lint would flag. The verb therefore mints the metadata line and the file; the agent writes the prompt.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: state the chosen grammar and paste the three conflicting sources side by side (the README line, the workflow Step 4 line, and the `TYPE_FACET`/`ARTIFACT_TYPE_FACETS` entries) with the on-disk evidence that decides it (a listing of `executed/` showing the `.prompt.md` suffix). Then paste the README diff, OR, if the approver declined the `Scope-Paths` addition, paste the recorded statement that the README remains contradictory plus the follow-up you filed. Silently leaving it unfixed and unrecorded FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the dry-run invocation showing the intended path and NO file written (a directory listing before and after). Paste the `--apply` run and the resulting file. Paste the same-minute second call yielding `NN=02`. Paste the COLLISION proof: a same-minute prompt already in `executed/` and a new mint that does not reuse its `NN`. Paste the `--agent` output showing the standard envelope. Name the sibling verb you copied.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the minted file's first TWO lines, showing the `aw-prompt` comment is exactly one line and that the prompt body (or nothing) follows. Paste an unrecognized `--kind` being rejected with a nonzero exit and no file written. Paste the recognized-kind list and the README lines you derived it from. Confirm the file contains no template or placeholder prose.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw prompts --help` and `aw prompts new --help`. Paste `python3 -m agent_workflows prompts new` reaching the same path. Paste the `TYPE_BACKENDS["prompts"]` entry showing `new` alongside `rename` and `group`. Paste the CLI-surface conformance tests passing, or, if they were already failing at your baseline, paste the failure NAMES from your baseline and prove your new leaf is not among them. Confirm no `check` stub was added.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the rewritten Step 4 and exit gate. Paste a grep over the workflow file proving no instruction to compute a timestamp/sequence or hand-write metadata remains. Confirm the leak-scan and never-auto-commit requirements are still present. Confirm no em or en dash was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full test module output passing under the DEFAULT parallel invocation (not a serialized run), proving the clock was pinned rather than raced. Paste falsifiability evidence as actual failures: the dry-run case against an eager writer, the collision case against a `pending/`-only sequencer, and the rejection case against a permissive `--kind`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. Right-sizing checked per leaf: E-01 the naming decision, E-02 the verb, E-03 the metadata line, E-04 the registration, E-05 the workflow caller, E-06 the tests. Each has its own falsifiable surface.

Open questions: ALL RESOLVED, and notably the item's own OPEN DESIGN QUESTION is resolved from repository evidence (an approved spec already sanctions the `aw prompts` namespace, and `prompts` is already a registered artifact type missing only `new`), so no maintainer decision is required on the design. TWO fence questions DO need the approver, and both are recorded in the Scope check rather than buried: whether to add `.aw/records/prompts/README.md` to `Scope-Paths` so E-01 can fix the contradictory naming paragraph, and whether satisfying the CLI-surface conformance manifest requires a file this plan does not declare. The executor must not resolve either by silently editing an undeclared file.

Scope fence: touch ONLY `agent_workflows/prompts.py` (new), `agent_workflows/cli.py`, `agent_workflows/artifact_types.py`, `.aw/system/workflows/research-prompt/research-prompt.md`, and the new `tests/test_prompts_new.py`, plus `.aw/records/prompts/README.md` IF the approver grants it. Do NOT implement `aw prompts check` (owned by the approved purity spec), do NOT add an id6 to prompt names, do NOT add a lifecycle transition verb, do NOT touch `aw research` or `.aw/records/research/`, do NOT write to or promote from the gitignored `local/` lane, and do NOT edit AGENTS.md managed blocks. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with concurrent agents and `cli.py` is one of the most contended files in it, so re-read it immediately before editing and locate insertion points by how `specs` is registered rather than by line number. Line numbers are deliberately omitted from this plan.

Cleanup obligation specific to this plan: your end-to-end check MINTS A REAL PROMPT into the tracked staging lane. That lane currently holds exactly one genuine prompt, so remove or retire your artifact when done rather than leaving test residue in a queue other people read.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
