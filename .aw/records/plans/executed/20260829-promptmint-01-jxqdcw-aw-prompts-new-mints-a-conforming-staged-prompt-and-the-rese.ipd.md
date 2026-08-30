# IPD: aw prompts new mints a conforming staged prompt, and the research producer workflow calls it

- Date: 2026-08-29
- Kind: child
- Concern: There is no `aw` verb that creates a file in the operational prompt STAGING lane `.aw/records/prompts/pending/`, so the `/aw research` producer workflow instructs the agent to HAND-NAME the file and HAND-WRITE its metadata comment. That violates the house rule that conforming artifacts are created by verbs, and it does not merely risk drift, it has already produced it: only 7 of the 13 prompts in `executed/` carry the leading `aw-prompt` metadata comment at all, and the staging README and the workflow disagree about whether the filename ends `.md` or `.prompt.md`.
- Scope: Add `aw prompts new` to mint a conforming staged prompt file (correct clustered/legacy name, leading `aw-prompt` metadata comment, `Status: pending`, landing in `.aw/records/prompts/pending/`, dry-run by default, never auto-staged), and change the `research-prompt` workflow to call it instead of hand-writing. Excludes `aw prompts check` (the prompt-purity lint, already specified separately and still unimplemented), excludes any change to the prompt LIFECYCLE verbs, and excludes touching `.aw/records/research/` or the `aw research` verb family.
- Scope-Paths: agent_workflows/prompts.py, agent_workflows/cli.py, agent_workflows/artifact_types.py, agent_workflows/command_surface.py, .aw/records/prompts/README.md, .aw/system/workflows/research-prompt/research-prompt.md, tests/test_prompts_new.py
- Item-Dependencies: none
- Status: executed
- Set: promptmint
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: jxqdcw
- Blocks-Release: next
- From-Backlog: i97baj

## Workflow history
- 2026-08-30 executed (opencode (its_direct/pt3-claude-opus-5-1m-us)): Implemented aw prompts new: the staging lane now has a creating verb, so a prompt is a tooled artifact instead of a hand-named file with hand-written metadata. E-01 settled the filename on the legacy faceted YYYYMMDD-HHMM-NN-<slug>.prompt.md (what all 13 executed prompts already use; artifact_naming excludes prompts from id6 clustering) and fixed BOTH README contradictions, including replacing the YAML front-matter Kind: language that approved spec P4 forbids with the leading aw-prompt HTML comment convention. E-02/E-03 added prompts.run_new modeled on specs.run_new (dry-run default, atomic write, standard result renderer), sequencing NN across the WHOLE prompts tree so a mint cannot collide with a same-minute prompt already moved to executed/, emitting the single-line comment as the first line and NO body per purity P4/P5, with the measured kind set (run-once/research/session-handoff) closed and an omitted --author omitted rather than placeholdered. E-04 registered the leaf in cli.py, TYPE_BACKENDS, and command_surface (modeled on specs new); no check stub, since that verb belongs to the approved purity spec whose namespace this establishes. E-05 rewrote the research-prompt workflow to CALL the verb. E-06 added 15 tests with a pinned clock. RETROACTIVE ACKNOWLEDGMENT (ipd-lifecycle recovery path 1): the begin receipt was created AFTER the implementation commit, so finalize's scope gate is ADVISORY here and verified nothing; the scope equality was verified BY HAND instead and is exact, 7 declared Scope-Paths == the 7 paths changed in 42ec759. The --scope-ack notes say modified-but-receipt-postdates-work rather than not-needed, because every declared path WAS modified. See run decision 05-jxqdcw-D1. NOT DONE HERE, recorded for the purity-lint implementer: aw prompts check is still unimplemented, so the purity contract remains untooled-enforced (only minting is tooled); this verb IS the aw prompts scaffold contemplated by that spec OQ5, named new for consistency with aw specs new, so no second overlapping verb should be added; and the handoff workflow still instructs YAML front-matter for session-handoff prompts (handoff.md:110, gate :134) with one such file in the gitignored untracked/ lane, a whole prompt KIND currently disagreeing with the contract, deliberately untouched as out of scope. Pre-existing and not fixed: test_zero_undeclared_parser_leaves is red at baseline with 59 undeclared leaves; prompts new is not among them and the count did not grow. [Scope reconciliation - in-scope-unmodified .aw/records/prompts/README.md: modified-but-receipt-postdates-work; in-scope-unmodified .aw/system/workflows/research-prompt/research-prompt.md: modified-but-receipt-postdates-work; in-scope-unmodified agent_workflows/artifact_types.py: modified-but-receipt-postdates-work; in-scope-unmodified agent_workflows/cli.py: modified-but-receipt-postdates-work; in-scope-unmodified agent_workflows/command_surface.py: modified-but-receipt-postdates-work; in-scope-unmodified agent_workflows/prompts.py: modified-but-receipt-postdates-work; in-scope-unmodified tests/test_prompts_new.py: modified-but-receipt-postdates-work]
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (aw set): /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-106. Verified every finding independently at f02c64e: F3 exact (7 of 13 executed prompts carry the aw-prompt comment, 6 do not, named), F4 three-way naming conflict confirmed (README:4 bare .md, workflow:9/:98/:105 faceted, TYPE_FACET[prompts]=prompt), F5 docstring confirmed verbatim, F1/F6 confirmed (aw prompts is not a top-level command; TYPE_BACKENDS[prompts] at artifact_types.py:98-101 has only rename/group; the approved purity spec names the namespace). Found a BLOCKER (F8): the plan's own fence guaranteed a mid-execution halt, because every parser leaf MUST be declared in command_surface.COMMAND_INVENTORY (enforced by find_undeclared_leaves, test_command_surface_declarations.py:46-52) and command_surface.py was NOT in Scope-Paths, while the draft said to STOP if the manifest required an undeclared file; added command_surface.py to Scope-Paths, named specs new (command_surface.py:1053-1066) as the declaration model, and recorded that this test is ALREADY RED at baseline with 59 undeclared leaves so it cannot be a green gate and the other 59 are not this plan's to fix. Found a HIGH factual error (F9): E-03 told the executor to enumerate recognized kinds from the README, but the README documents YAML front-matter Kind: (README:7) which the approved spec P4 explicitly FORBIDS, so following the instruction would have propagated the banned convention; E-03 now derives from the measured corpus plus the spec, and E-01's README fix now repairs the metadata paragraph as well as the filename. Found an undefined default: --author has no resolver to inherit (specs new has no such flag; only driver-local driver_actor exists), so E-03 must state its rule and never emit a placeholder author. Recorded a real cross-artifact conflict (F10): the handoff workflow instructs YAML front-matter for session-handoff prompts (handoff.md:110, gate :134) and one such file exists in the gitignored untracked/ lane, so a whole prompt KIND disagrees with the purity contract; fenced out of this plan but recorded for the lint implementer. Recorded that this verb IS the aw prompts scaffold contemplated by the purity spec's OQ5 (F11), named new for consistency, so no second overlapping verb is added. Corrected F2's evidence (four references to the prompts tree exist, not one; the accurate claim is no CREATOR). Closed both fence questions the draft left to the approver, since both were certainties rather than judgment calls.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `i97baj` during the blocking-backlog graduation sweep. The item's OPEN DESIGN QUESTION (a standalone `aw prompt` noun versus extending `aw research`) is RESOLVED from repository evidence rather than left to the maintainer: an APPROVED spec already establishes the `aw prompts <verb>` namespace by name, and `prompts` is already a registered artifact type with a `prompt` facet and working `rename`/`group` verbs, so the namespace is settled and this plan only adds the missing `new`. See F1 and OQ-01. Two facts the item did not record were measured and change the work: the metadata comment is missing from 6 of 13 executed prompts (F3), and the documented filename grammar is self-contradictory across two authoritative files (F4).

## Goal

Make a staged prompt a tooled artifact like every other record in this repo. One verb mints it with the right name and the right metadata, the producer workflow calls that verb, and the naming contradiction that made hand-writing ambiguous is resolved rather than perpetuated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: settle the name, then mint it

- [x] E-01 RESOLVE THE FILENAME CONTRADICTION FIRST, because the verb cannot emit a conforming name until the repo agrees what one is, and this must be decided in the plan rather than improvised by the executor. Measured conflict (F4): `.aw/records/prompts/README.md` documents `YYYYMMDD-HHMM-NN-<slug>.md`, while the `research-prompt` workflow's Step 4 and exit gate specify `YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`, and separately the uniform artifact grammar registers a `prompt` facet with `prompts` in `TYPE_FACET`, which points at a THIRD possibility (a clustered `YYYYMMDD-<setid>-NN-<id6>-<slug>.prompt.md` name). On-disk evidence: every file in `executed/` uses the legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` shape, i.e. the facet IS present in practice while the README omits it. RECOMMENDED RESOLUTION for the approver: emit the legacy `YYYYMMDD-HHMM-NN-<slug>.prompt.md` shape, matching what is actually on disk and what `artifact_naming` documents for the id6-less types, and CORRECT the README to include the `.prompt.md` facet. Do NOT mint an id6-clustered name in this plan: `artifact_naming`'s own docstring states prompts are among the types it does NOT add an id6 to, and doing so would be a corpus-wide naming change well beyond this item. If the approver prefers the clustered id6 form, this plan needs re-scoping.
  THE README FIX IS NOW IN-FENCE AND MANDATORY, not an approver question: `.aw/records/prompts/README.md` is in `Scope-Paths` (added at review), so E-01 MUST correct it rather than record a follow-up. The fix has TWO parts, and the draft named only the first. Part one, the filename: add the `.prompt.md` facet to the naming paragraph at `:4`. Part two, the METADATA CONVENTION, which is the more consequential error (F9): the README at `:7` documents "Recognized prompt kinds (front-matter `Kind:`)", i.e. YAML front-matter, while the APPROVED purity spec P4 forbids YAML front-matter outright and mandates the single leading `aw-prompt` HTML comment. Replace that front-matter language with the comment convention this plan's verb emits, keeping the kind LIST (`run-once`, `research`, `session-handoff`) which is accurate. Leaving part two unfixed would ship a verb whose output its own README calls non-conforming. Note that the approved spec's Section 7 already assigns this same README correction; doing it here is executing that spec's documented intent, not overriding it, and the executor should say so.
  - Depends on: none
  - Expected outcome: ONE documented filename grammar for a staged prompt, recorded in the plan with the decision and its rationale; the README's naming paragraph carries the `.prompt.md` facet AND its metadata paragraph describes the leading `aw-prompt` comment instead of YAML front-matter; the README no longer contradicts either the workflow or the approved purity spec; and the choice is consistent with the existing on-disk corpus.
  - Execution state: performed

- [x] E-02 Add a new `agent_workflows/prompts.py` module with a `run_new(args)` following the ESTABLISHED owner-verb shape rather than a new one. Copy the structure of `specs.run_new` (locate by symbol), which is the closest sibling: resolve the repo root through `project_context.resolve_verb_repo_root`, derive the slug through `artifact_core.kebab` with a length bound, build the destination path, render the file, honor dry-run as the DEFAULT with `--apply` to write, write via `artifact_core.atomic_write`, and emit through the `CommandResult`/`select_output`/`get_renderer` pipeline so `--agent` and `--json` work like every other verb. Do NOT invent a bespoke output path or a bare `print`. Compute the `NN` per-minute sequence by inspecting existing files for that `YYYYMMDD-HHMM` prefix so a second prompt in the same minute gets `02`, and note the sequence must consider the WHOLE prompts tree, not only `pending/`, or a prompt minted after an earlier one moved to `executed/` can collide.
  - Depends on: E-01
  - Expected outcome: `aw prompts new --kind research --slug x` previews a conforming path and body and writes NOTHING; with `--apply` it writes exactly that file; `--agent` emits the standard JSONL result; a second call in the same minute yields `NN=02`; the sequence does not collide with a file already moved out of `pending/`.
  - Execution state: performed

- [x] E-03 Emit the leading metadata comment as a SINGLE line, exactly as the purity contract requires. The line takes the form `<!-- aw-prompt: Kind: <kind> | Status: pending | Created: <date> | Author: <agent> | Targets: ... | Concerns: ... -->` and must be the FIRST line of the file. Two properties are load-bearing and must not be broken by rendering convenience: it is an HTML comment so it is invisible when the prompt is pasted into a chat, and it is ONE line so nothing before the prompt body can be mistaken for prompt content (approved spec P4/P5, R1). Accept `--kind` (default `research`), plus optional `--targets`, `--concerns`, `--author`, and `--status` (defaulting to `pending`).
  DERIVE THE FIELD SHAPE AND THE KIND SET FROM THE MEASURED CORPUS AND THE APPROVED SPEC, NOT FROM THE README. The draft said to "enumerate from the README rather than inventing a set", which is not possible as written: the README does not document the comment at all, it documents YAML `front-matter Kind:` (`.aw/records/prompts/README.md:7`), a form the approved purity spec explicitly FORBIDS as an R1 violation (P4: "No YAML front-matter"). Deriving from it would reproduce the wrong convention (F9). Use instead: the kinds actually in use, measured across the corpus as `run-once`, `research`, and `session-handoff`; and the field order shown by the 7 conforming files. Accept an unknown `--kind` ONLY by rejecting it with a nonzero exit and no file written.
  DEFINE THE `--author` FALLBACK EXPLICITLY, because there is no shared resolver to inherit: verified that `aw specs new` has NO `--author` flag and the package exposes no general author/actor helper (the only `driver_actor` functions are driver-local and read run state). So `--author` cannot be "resolved like elsewhere". Decide and state one rule: either REQUIRE `--author` (the caller is always an agent that knows its own model id, and the corpus shows every conforming file naming a specific model), or omit the field entirely when not supplied rather than inventing a placeholder. Do NOT emit a guessed or `unknown` author into a tracked artifact.
  ONE OBSERVED CONVENTION TO DECIDE EXPLICITLY: all 7 conforming prompts end the comment with the sentence "This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt." (measured: 7 of 7). Emit it, so minted files match the corpus and a reader who does see the comment understands it is not prompt content, and record that choice. Emit NO OTHER body boilerplate, because the purity contract forbids any content that is not the prompt itself, and a helpful template would violate it.
  - Depends on: E-02
  - Expected outcome: the minted file's first line is a single-line `aw-prompt` HTML comment carrying the supplied fields and the trailing pipeline-metadata sentence; the kind set is the measured `run-once`/`research`/`session-handoff`; an unrecognized `--kind` is rejected with a nonzero exit and writes nothing; the `--author` rule is stated and no placeholder author is ever emitted; the file contains no YAML front-matter and no placeholder prose.
  - Execution state: performed

- [x] E-04 Register the verb so it is discoverable and dispatchable: add the `prompts` subparser with a `new` subcommand at the two CLI edit points in `cli.py` (the parser builder and the dispatcher; locate them by how `specs` is registered), and add `"new": "prompts.run_new"` to the `prompts` entry in `artifact_types.TYPE_BACKENDS`, which today lists only `rename` and `group` (verified at `artifact_types.py:98-101`). Note that `prompts` is currently NOT a valid top-level `aw` command at all (measured: `aw prompts check` errors with `invalid choice: 'prompts'`), so this E-item CREATES the namespace the approved prompt-purity spec already assumes. Leave room for that spec's `check` verb rather than designing it: register the noun and the one verb this plan owns, and do not stub `check`.
  ALSO ADD THE CONTRACT DECLARATION, which the draft left as a "find it, and STOP if it is outside the fence" instruction that would have halted execution. The requirement is now RESOLVED rather than deferred (F8): every parser leaf must carry an entry in `command_surface.COMMAND_INVENTORY`, enforced by `find_undeclared_leaves` in `tests/test_command_surface_declarations.py:46-52`. Add a `CommandDeclaration` for `prompts new` modeled on the `specs new` entry (`command_surface.py:1053-1066`), which is the exact analogue: `command_class="mutation"`, `human_recipe="preview"`, `agent_record_kind="result"`, `mutation_gate="dry_run_default"`, `empty_error_renderer="renderer_boundary"`, and the real flag list. `command_surface.py` is now in `Scope-Paths`, so this is in-fence and NOT a stop condition.
  BE HONEST ABOUT THE BASELINE: that test is ALREADY FAILING with 59 undeclared leaves at `f02c64e` (measured, F8), so it will NOT go green from your change alone. Do not "fix" the other 59; they are other people's undeclared leaves. Prove only that `prompts new` is NOT in the reported set after your change.
  - Depends on: E-02, E-03
  - Expected outcome: `aw prompts new --help` works, `aw prompts --help` lists `new`, `python3 -m agent_workflows prompts new` reaches the same code path, the backend registry resolves `("prompts", "new")`, and `find_undeclared_leaves` does not report `prompts new`; the pre-existing 59 undeclared leaves are untouched and named as pre-existing; no `check` stub is added.
  - Execution state: performed

### Task group 2: make the workflow use it, and prove the whole thing

- [x] E-05 Rewrite the `research-prompt` workflow so it CALLS the verb instead of hand-naming and hand-writing. Concretely, Step 4 currently instructs the agent to "Determine the timestamp and sequence number" and "Write the file", which is precisely the untooled behavior the backlog item objects to; replace that with an `aw prompts new` invocation supplying `--kind research` and the metadata fields, then have the agent write only the PROMPT BODY into the minted file. Update the exit gate accordingly, and keep the two existing requirements that must survive: run `aw check-local-leaks` on the finished file, and NEVER auto-stage or commit it. Also fix the naming line in this file to match E-01's resolution. Keep all prose free of em and en dashes per the execution contract, since this is an agent-facing workflow file that a human also reads.
  - Depends on: E-01, E-04
  - Expected outcome: the workflow no longer tells an agent to compute a filename or hand-write metadata; it names the exact `aw prompts new` invocation; the leak-scan and no-auto-commit requirements are intact; the exit gate checks the verb was used.
  - Execution state: performed

- [x] E-06 Add `tests/test_prompts_new.py` covering: dry-run writes NOTHING (assert the directory is unchanged) while printing the intended path; `--apply` writes exactly one file at the resolved path; the first line is a single-line `aw-prompt` comment with the supplied `Kind`, `Status: pending`, and `Created`; the per-minute sequence increments to `02` on a second call in the same minute; the sequence does NOT collide with a same-minute file that already sits in `executed/` (the E-02 whole-tree requirement); an unrecognized `--kind` exits nonzero and writes nothing; `--agent` output is parseable as the standard result envelope; and the minted file passes a purity property, namely that nothing precedes the comment and the comment occupies exactly one line. Pin the clock rather than depending on wall time, so the sequence tests are deterministic and parallel-safe under `xdist`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the module passes deterministically under the default parallel invocation; the dry-run, collision, and rejection cases each fail against a naive implementation that writes eagerly, sequences within `pending/` only, or accepts any kind.
  - Execution state: performed

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
| F2 | HIGH | `agent_workflows/` | The gap is total, not partial: NO code in the package CREATES a staged prompt. Substance CONFIRMED at review, with the evidence corrected: the plan said the only match is a docstring example, but there are in fact four references to the prompts tree (`agy_run.py:125-128` docstring examples, `doctor.py:656`, `engine.py:3687`) plus the `rename`/`group` backends. None of them WRITES a new prompt, so the verb is genuinely net-new; the precise claim is "no creator", not "no references". | `grep -rn "records/prompts" agent_workflows/*.py` at `f02c64e` returns `agy_run.py:125,127,128`, `doctor.py:656`, `engine.py:3687`; `artifact_rename.run_rename_prompts:819` / `run_group_prompts:847` rename only |
| F3 | HIGH | `.aw/records/prompts/executed/` | THE DRIFT IS ALREADY REAL, which the item asserts as a risk but does not measure. Only 7 of 13 executed prompts begin with the `aw-prompt` metadata comment; 6 have NONE. Hand-written metadata is therefore not merely untooled, it is unreliably applied, and the verb is the fix rather than a tidiness improvement. | measured at `d4c4a0a`: first-line `aw-prompt` present in 7 files, absent in 6 |
| F4 | HIGH | `.aw/records/prompts/README.md` versus `research-prompt.md` versus `artifact_naming.py` | THE DOCUMENTED FILENAME IS SELF-CONTRADICTORY THREE WAYS, so "write a conforming name" was underdetermined for any hand-authoring agent. The README says `YYYYMMDD-HHMM-NN-<slug>.md`; the workflow says `YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`; the uniform grammar registers a `prompt` FACET and a clustered id6 form. On-disk reality matches the workflow's faceted legacy shape. E-01 must settle this before the verb can emit anything. | README naming paragraph; workflow Step 4 and exit gate; `TYPE_FACET["prompts"] = "prompt"`; every `executed/` filename ends `.prompt.md` |
| F5 | MED | `artifact_naming.py` docstring | The clustered id6 form is NOT available to prompts today by design. The module states that prompts, roadmaps, releases, and walkthroughs "do not yet carry an id6 in most on-disk names" and that it "does NOT add an id6 to those types (out of scope)". So minting an id6-clustered prompt name would contradict the naming authority itself and is correctly out of this plan's scope (E-01). | module docstring, id6-less legacy types paragraph |
| F6 | MED | `cli.py` | `prompts` is not a top-level command at all today, so E-04 CREATES the namespace rather than extending it. This also means the approved purity spec's `aw prompts check` has nowhere to attach yet, which is worth stating so a reviewer does not assume half of it already exists. | measured: `aw prompts check` fails with `invalid choice: 'prompts'` and lists the valid commands; no `agent_workflows/prompts_lint.py` exists |
| F7 | LOW | `.aw/records/prompts/pending/` | The staging lane currently holds exactly ONE prompt plus a README, so this verb's blast radius on existing content is nil and the end-to-end check can be performed without disturbing a queue. CONFIRMED at review: `20260810-1544-01-awphysical-spec-to-reviewed-focus.prompt.md` plus `README.md`. | directory listing at `d4c4a0a`, re-verified at `f02c64e` |
| F8 | BLOCKER | added at review; `command_surface.py`, `tests/test_command_surface_declarations.py:46-52` | THE PLAN'S OWN FENCE WOULD HAVE HALTED EXECUTION. The draft told the executor to find the CLI-surface manifest requirement and, if satisfying it meant editing a file outside `Scope-Paths`, to STOP and report. That condition is CERTAIN, not conditional: every parser leaf must be declared in `command_surface.COMMAND_INVENTORY` or `find_undeclared_leaves` reports it, and `command_surface.py` was NOT in `Scope-Paths`. So the plan as written was guaranteed to stop partway through E-04 with the verb built but undeclarable. Fixed by adding `command_surface.py` to `Scope-Paths` and naming `specs new` as the declaration model. SEPARATELY, that test is ALREADY FAILING at baseline with 59 undeclared leaves, so it cannot be used as a green/red gate for this change; only the absence of `prompts new` from the reported set is provable. | `pytest tests/test_command_surface_declarations.py -m ''` at `f02c64e`: `AssertionError: 59 != 0 : Found undeclared parser leaves: {'test', 'ipd dependencies set', ... 'spec new', 'specs scaffold', ...}`; model entry `command_surface.py:1053-1066` (`command="specs new"`, `mutation_gate="dry_run_default"`) |
| F9 | HIGH | added at review; `.aw/records/prompts/README.md:7` versus approved spec P4 | E-03's INSTRUCTION WAS IMPOSSIBLE AS WRITTEN and would have propagated the wrong convention. It told the executor to enumerate recognized kinds "from the README rather than inventing a set", but the README documents YAML `front-matter Kind:` and says NOTHING about the `aw-prompt` comment; the approved purity spec P4 explicitly forbids YAML front-matter ("No YAML front-matter (it renders as text ... and is not invisible)") and mandates the single leading HTML comment. So the README is not merely incomplete on naming (F4), it is CONTRADICTORY on the metadata mechanism, which is the very thing this verb emits. E-01's README fix must therefore repair the metadata paragraph too, and E-03 must derive from the corpus and the spec. | README `:7` "Recognized prompt kinds (front-matter `Kind:`)"; spec P4/P5 and R1; measured: 0 tracked prompts use YAML front-matter, 7 use the comment |
| F10 | MED | added at review; `.aw/records/prompts/untracked/`, `handoff` workflow | A REAL CROSS-ARTIFACT CONFLICT the plan did not see, worth stating so the executor does not "fix" it. One live prompt DOES use YAML front-matter (`untracked/20260829-1422-01-session-handoff-run-ledger-defects.md`), and the `handoff` workflow INSTRUCTS that shape ("Front-matter: `Kind: session-handoff`, `Status: draft`", `handoff.md:110`, gate at `:134`). Both the `untracked/` and `local/` lanes are gitignored, so this is not a tracked-corpus violation today, but it means `session-handoff` prompts are produced in a form the approved purity spec forbids. This plan must NOT rewrite the handoff workflow (out of scope, and it writes to the gitignored lane), but should record the conflict so the purity-lint implementer knows a whole prompt KIND currently disagrees with the contract. | `head -1` of that file is `---`; `.aw/.gitignore:6` ignores `records/*/untracked/`; `handoff.md:108-110`, `:134` |
| F11 | LOW | added at review; approved spec OQ5 and Section 6 | THIS PLAN PARTLY ANSWERS AN OPEN QUESTION IN THE APPROVED SPEC, which strengthens the plan's justification and should be recorded rather than left implicit. That spec's OQ5 asks whether `check` should gain "a companion `--fix`/`aw prompts scaffold` that emits a conformant skeleton (leading `aw-prompt` comment + body) so authors start pure by construction", leaning "a later phase; scaffold prevents the error better than lint catches it", and its Section "future members" lists `aw prompts scaffold` as out of scope there. `aw prompts new` IS that scaffold under a different verb name. The executor should note the naming choice (`new`, consistent with `aw specs new`, rather than `scaffold`) in the terminal history so the purity-lint implementer does not add a second overlapping verb. | spec OQ5; spec future-members line "`aw prompts scaffold` (pure-by-construction authoring) ... out of scope here"; existing sibling `aw specs new` |

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

- Over-scope: none. The new module holds the verb, `cli.py` registers it, `artifact_types.py` adds the one registry entry, `command_surface.py` declares the leaf, the README carries the conventions the verb implements, the workflow file is the caller this item exists to fix, and the test module is new.
- BOTH FENCE QUESTIONS THE DRAFT LEFT TO THE APPROVER ARE NOW RESOLVED IN-PLAN, because both were certainties rather than judgment calls, and leaving either open guaranteed a mid-execution stop. First, `.aw/records/prompts/README.md` is now IN `Scope-Paths`: it carries both the contradictory naming claim (F4) and the contradictory metadata claim (F9), and shipping a verb whose own README calls its output non-conforming is not an acceptable outcome. The approved purity spec's Section 7 already assigns this README correction, so this is executing documented intent, not overriding the approver. Second, `agent_workflows/command_surface.py` is now IN `Scope-Paths`: the CLI-surface declaration is MANDATORY for any new parser leaf (F8), so the draft's "if it means editing a file outside `Scope-Paths`, STOP" was a guaranteed halt, not a safeguard.
- Under-scope otherwise: none outstanding. `cli.py` is frequently dirty from concurrent work; expect contention and re-read before editing.
- PRE-EXISTING FAILURE, NOT YOURS TO FIX: `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` fails at baseline with 59 undeclared leaves (F8). Do NOT declare the other 59; that is a separate, much larger piece of work touching other people's verbs. Your obligation is only that `prompts new` is not among them.

## Required tests / validation

- `tests/test_prompts_new.py` must pass with every case in E-06, deterministically under the default parallel invocation. Falsifiability: the dry-run case must fail against an implementation that writes eagerly; the collision case must fail against one that sequences within `pending/` only; the rejection case must fail against one that accepts any `--kind`.
- The CLI-surface conformance tests CANNOT be used as a green gate, because `test_zero_undeclared_parser_leaves` is ALREADY FAILING at baseline with 59 undeclared leaves (measured at `f02c64e`, F8). Run it explicitly, paste your own before and after readings, and prove the ONE thing that is provable: `prompts new` does not appear in the reported undeclared set after your change, and the count did not grow. Do NOT declare the other 59 and do NOT report this test as passing.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during this sweep at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Take your own before/after readings with their HEAD; concurrent agents are committing to `cli.py`.
- End-to-end, the property the item asks for: run `aw prompts new` for real, paste the minted path and the file's first line, run `aw check-local-leaks` on it, and confirm it was NOT staged or committed (`git status --porcelain` showing it untracked). Then delete or retire your test artifact so the staging queue is not polluted; the lane currently holds exactly one real prompt (F7).
- Also validate the WORKFLOW change by reading it back: paste the rewritten Step 4 and exit gate, and confirm no instruction to compute a filename or hand-write metadata survives anywhere in the file.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- `.aw/records/prompts/README.md` needs TWO corrections under E-01, both in-fence: the naming paragraph to the E-01 grammar, and the metadata paragraph from YAML `front-matter Kind:` to the leading `aw-prompt` HTML comment (F9), since the approved purity spec P4 forbids the former and this plan's verb emits the latter.
- Record in the terminal history that a whole prompt KIND currently disagrees with the purity contract: the `handoff` workflow instructs YAML front-matter for `session-handoff` prompts and one such file exists in the gitignored `untracked/` lane (F10). This plan deliberately does not change it; the purity-lint implementer needs to know.
- Record that `aw prompts new` is the verb the purity spec's OQ5 contemplated as `aw prompts scaffold` (F11), so no second overlapping verb is added later.
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
- Resolution or deferral rationale: THE LEGACY FACETED FORM `YYYYMMDD-HHMM-NN-<slug>.prompt.md`, and correct the README to match. Resolved from on-disk evidence plus the naming authority's own scope statement. Every file in `executed/` uses that shape, so it is what the corpus actually is; the workflow already specifies it; and `artifact_naming`'s docstring explicitly places prompts among the types it does NOT give an id6, so emitting a clustered id6 name would contradict the module that owns naming (F5). The README's bare `.md` claim is the outlier and is simply wrong against the corpus. UPDATED AT REVIEW: this is no longer a recommendation contingent on an approver granting a fence exception. `.aw/records/prompts/README.md` is now in `Scope-Paths`, so E-01 fixes it directly, and the fix covers the metadata contradiction as well as the filename (F9). The approved purity spec's Section 7 already assigns this README correction, so the edit executes documented intent rather than expanding scope on a whim.

### OQ-03: Should the verb also write a prompt BODY template?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, emit no body boilerplate. The prompt-purity contract requires the file to contain ONLY the prompt addressed to the target AI, with no user-facing instructions and nothing to strip before uploading, and it confines pipeline metadata to the single leading HTML comment precisely because that is invisible when pasted. A template body or placeholder prose would be content that is not the prompt, i.e. exactly what the contract forbids and what the still-unimplemented purity lint would flag. The verb therefore mints the metadata line and the file; the agent writes the prompt.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: state the chosen grammar and paste the three conflicting sources side by side (the README line, the workflow Step 4 line, and the `TYPE_FACET`/`ARTIFACT_TYPE_FACETS` entries) with the on-disk evidence that decides it (a listing of `executed/` showing the `.prompt.md` suffix). Then paste the README diff showing BOTH parts fixed: the naming paragraph now carries `.prompt.md`, AND the metadata paragraph now describes the leading `aw-prompt` HTML comment instead of YAML `front-matter Kind:` (F9). A diff that fixes only the filename FAILS this item, since the metadata contradiction is the one that would make the verb's own output non-conforming per the approved spec P4. The README is in `Scope-Paths`, so "recorded a follow-up instead" is no longer an acceptable outcome.
  - Observed evidence: CHOSEN GRAMMAR: the legacy faceted `YYYYMMDD-HHMM-NN-<slug>.prompt.md` (OQ-02's recommended resolution, unchanged after re-verifying the evidence). The three conflicting sources, measured at `d4d265b` before the fix:
    ```text
    README.md:3-5   Prompt files are named `YYYYMMDD-HHMM-NN-<slug>.md` (... the same convention as plans.
    workflow:9      - It PRODUCES one upload-ready research handoff prompt (`.prompt.md`) and writes it to `.aw/records/prompts/pending/YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`.
    workflow:98     1. Determine the timestamp and sequence number: `YYYYMMDD-HHMM-NN-research-<slug>.prompt.md` (e.g. ...).
    workflow:105    - [ ] File created under `.aw/records/prompts/pending/YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`.
    artifact_naming.py:61   "prompt",                 # ARTIFACT_TYPE_FACETS member
    artifact_naming.py:76   "prompts": "prompt",      # TYPE_FACET entry -> points at the clustered id6 form
    ```
    THE ON-DISK EVIDENCE THAT DECIDES IT: all 13 prompts in `executed/` carry the `.prompt.md` suffix (`ls .aw/records/prompts/executed/*.prompt.md | wc -l` -> `13`), i.e. the facet IS present in practice and the README's bare `.md` is the outlier. The clustered id6 form was rejected per F5: `artifact_naming`'s own docstring (`:32-36`) places prompts among the types it "does NOT add an id6 to (out of scope)".
    README DIFF, BOTH PARTS FIXED (`git diff` at `d4d265b`, committed in `42ec759`):
    ```diff
    -`YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit
    -per-minute sequence; `<slug>` is lowercase kebab-case), the same convention as plans.
    +`YYYYMMDD-HHMM-NN-<slug>.prompt.md` (the creating machine's local date and time; `NN` is a two-digit
    +per-minute sequence; `<slug>` is lowercase kebab-case; `.prompt` is the uniform artifact-type facet).
    +Do NOT hand-name a staged prompt: `aw prompts new` derives the name and writes the metadata for you
    +(dry-run by default, `--apply` to write, never auto-staged).
    -Recognized prompt kinds (front-matter `Kind:`): run-once / research prompts QUEUED to be executed
    -(the original staging use), and `Kind: session-handoff` resume prompts produced by `/handoff` (a
    -prompt for the NEXT session rather than a task to run now). Handoff drafts are written to the
    -gitignored `local/` lane (below) and promoted only after review.
    +Pipeline metadata lives in a SINGLE leading HTML comment, which must be the first line of the file:
    +
    +```text
    +<!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-30 | Author: <agent> (<model>) | Targets: ... | Concerns: ... -->
    +```
    +
    +An HTML comment is invisible when the file is pasted into a chat, so the prompt stays
    +select-all-and-upload ready. YAML front-matter is NOT permitted (it renders as visible text or a
    +stray table in many chat UIs, so it would become part of the prompt). Recognized prompt kinds
    +(the `Kind:` field of that comment): `run-once` and `research` prompts QUEUED to be executed (the
    +original staging use), and `session-handoff` resume prompts produced by `/handoff` (a prompt for the
    +NEXT session rather than a task to run now). Handoff drafts are written to the gitignored `local/`
    +lane (below) and promoted only after review.
    ```
    PART TWO IS PRESENT, which is what this item fails on if omitted: the YAML `front-matter Kind:` language at the old `:7` is GONE and replaced with the leading `aw-prompt` HTML comment convention plus an explicit "YAML front-matter is NOT permitted" statement, matching approved spec P4. The `Kind` LIST (`run-once`, `research`, `session-handoff`) is preserved because it was accurate. The workflow's naming references were updated in E-05.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the dry-run invocation showing the intended path and NO file written (a directory listing before and after). Paste the `--apply` run and the resulting file. Paste the same-minute second call yielding `NN=02`. Paste the COLLISION proof: a same-minute prompt already in `executed/` and a new mint that does not reuse its `NN`. Paste the `--agent` output showing the standard envelope. Name the sibling verb you copied.
  - Observed evidence: SIBLING COPIED: `specs.run_new` (`agent_workflows/specs.py:813`), as the plan directed. Same shape: `project_context.resolve_verb_repo_root`, `artifact_core.kebab` with a length bound, dry-run as the DEFAULT with `--apply`, `artifact_core.atomic_write`, and the `CommandResult`/`select_output`/`get_renderer` pipeline. Behavior measured in a scratch repo (`/tmp/opencode/pnew`) so the real staging queue was not polluted:
    ```console
    $ python3 -m agent_workflows prompts new --slug demo-topic --kind research --author "opencode (test)" --dir /tmp/opencode/pnew
    --- would write /tmp/opencode/pnew/.aw/records/prompts/pending/20260830-0221-01-demo-topic.prompt.md ---
    <!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-30 | Author: opencode (test) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
    EXIT=0
    $ ls -R /tmp/opencode/pnew/.aw/records/prompts        # BEFORE == AFTER: dry-run wrote NOTHING
    /tmp/opencode/pnew/.aw/records/prompts:
    pending
    /tmp/opencode/pnew/.aw/records/prompts/pending:
    ```
    `--apply`, then the same-minute second call, then the COLLISION case (an `NN=03` prompt planted in `executed/`):
    ```console
    $ python3 -m agent_workflows prompts new --slug demo-topic ... --date 2026-08-30 --time 0930 --apply --dir /tmp/opencode/pnew
    aw prompts new: wrote .../pending/20260830-0930-01-demo-topic.prompt.md
    EXIT=0
    $ python3 -m agent_workflows prompts new --slug other-topic --date 2026-08-30 --time 0930 --apply --dir /tmp/opencode/pnew
    aw prompts new: wrote .../pending/20260830-0930-02-other-topic.prompt.md      # NN=02
    EXIT=0
    $ printf '...' > .aw/records/prompts/executed/20260830-0930-03-already-run.prompt.md
    $ python3 -m agent_workflows prompts new --slug third-topic --date 2026-08-30 --time 0930 --apply --dir /tmp/opencode/pnew
    aw prompts new: wrote .../pending/20260830-0930-04-third-topic.prompt.md      # NN=04, NOT 03
    EXIT=0
    $ ls .aw/records/prompts/pending .aw/records/prompts/executed
    .aw/records/prompts/executed:
    20260830-0930-03-already-run.prompt.md
    .aw/records/prompts/pending:
    20260830-0930-01-demo-topic.prompt.md
    20260830-0930-02-other-topic.prompt.md
    20260830-0930-04-third-topic.prompt.md
    ```
    THE COLLISION PROPERTY IS THE LOAD-BEARING ONE: the third mint skipped to `NN=04` because `NN=03` already existed in `executed/`, proving the sequence is computed across the WHOLE prompts tree and not only `pending/` (E-02's requirement). Confirmed falsifiable in V-06 against a `pending/`-only sequencer.
    `--agent` standard envelope:
    ```console
    $ python3 -m agent_workflows prompts new --slug agentmode --agent --dir /tmp/opencode/pnew
    {"schema":"aw.agent/v1","kind":"result","cmd":"prompts new","outcome":"clean","exit":0,"verified":true,"complete":true,"applied":false,"findings":0,"changes":[{"kind":"create","path":".aw/records/prompts/pending/20260830-0221-01-agentmode.prompt.md"}],"next":null}
    EXIT=0
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the minted file's first TWO lines, showing the `aw-prompt` comment is exactly one line and that the prompt body (or nothing) follows. Paste an unrecognized `--kind` being rejected with a nonzero exit and no file written. Paste the recognized-kind list WITH the evidence you derived it from, which per F9 must be the measured corpus plus the approved spec P4, NOT the README's YAML `front-matter Kind:` line; cite the corpus measurement. State whether you emitted the trailing "This HTML comment is pipeline metadata only ..." sentence and note it appears in 7 of 7 conforming files. Confirm the file contains no YAML front-matter, no template, and no placeholder prose.
  - Observed evidence: THE MINTED FILE, real mint into this repo's tracked lane (`head -1` plus `wc -l` proving there IS no second line, i.e. the comment is exactly one line and nothing follows):
    ```console
    $ head -1 .aw/records/prompts/pending/20260830-0235-01-jxqdcw-e2e-verification.prompt.md
    <!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-30 | Author: opencode (its_direct/pt3-claude-opus-5-1m-us) | Targets: none (verification artifact) | Concerns: end-to-end proof that aw prompts new mints a conforming staged prompt . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
    $ wc -l .aw/records/prompts/pending/20260830-0235-01-jxqdcw-e2e-verification.prompt.md
    1 .aw/records/prompts/pending/20260830-0235-01-jxqdcw-e2e-verification.prompt.md
    ```
    The one-line and first-line properties are additionally asserted structurally by `tests/test_prompts_new.py::TestApplyWritesConformingFile::test_first_line_is_single_line_aw_prompt_comment_with_fields`, which checks `text.count("<!-- aw-prompt:") == 1`, `text.count("-->") == 1`, that line 0 both opens and closes the comment, and that every remaining line is blank.
    UNRECOGNIZED KIND REJECTED, nonzero exit, nothing written:
    ```console
    $ python3 -m agent_workflows prompts new --slug bad --kind nonsense --dir /tmp/opencode/pnew
    aw prompts new: unrecognized --kind 'nonsense'; expected one of run-once, research, session-handoff
    EXIT=2
    ```
    (`TestRejections::test_unrecognized_kind_exits_nonzero_and_writes_nothing` additionally asserts the pending dir is still empty afterward.)
    RECOGNIZED-KIND LIST AND ITS DERIVATION: `PROMPT_KINDS = ("run-once", "research", "session-handoff")`. Derived from the MEASURED CORPUS plus the approved spec, NOT from the README (F9: the README documented YAML `front-matter Kind:`, a form spec P4 forbids, so deriving from it would have propagated the banned convention). Corpus measurement: reading `head -1` of every `.prompt.md` under `.aw/records/prompts/`, the 8 files carrying an `aw-prompt` comment use exactly two kinds in the tracked lifecycle buckets, `Kind: run-once` (5 files: `20260808-1948-01`, `20260810-0102-01`, `20260810-1417-01`, `20260810-1530-01`, `20260810-1544-01`) and `Kind: research` (3 files: `20260813-0044-01`, `20260828-2156-01`, `20260829-1520-01`); `session-handoff` is the third kind, documented as a real kind by the staging README and produced by the `/handoff` workflow into the gitignored lane (see F10).
    TRAILING SENTENCE: YES, EMITTED. `prompts._METADATA_TRAILER` appends "This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt." exactly as it appears in 7 of 7 conforming files (verified by grepping the first line of each: all 8 files with the comment, including `pending/20260810-1544-01`, end with that sentence). Rationale recorded in the module docstring: it makes minted files match the corpus and tells a reader who DOES see the comment that it is not prompt content.
    NO YAML FRONT-MATTER, NO TEMPLATE, NO PLACEHOLDER PROSE: the file is one line long, so there is nothing to template. `--author` OMITTED emits NO `Author:` field rather than a placeholder (`TestApplyWritesConformingFile::test_omitted_author_emits_no_placeholder` asserts both `"Author:" not in first` and no `unknown`), which is the E-03 author rule: `aw specs new` has no `--author` to inherit from and the package exposes no shared author/actor resolver, so a guessed value would be worse than an absent one.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `aw prompts --help` and `aw prompts new --help`. Paste `python3 -m agent_workflows prompts new` reaching the same path. Paste the `TYPE_BACKENDS["prompts"]` entry showing `new` alongside `rename` and `group`. Paste the new `CommandDeclaration` for `prompts new` and the `specs new` entry you modeled it on. Then paste the BASELINE and POST-CHANGE runs of `test_zero_undeclared_parser_leaves`: both will FAIL (59 undeclared at `f02c64e`), so the required proof is that `prompts new` is ABSENT from the post-change reported set and the count did not grow. Do NOT claim this test passes and do NOT declare the other 59 leaves. Confirm no `check` stub was added.
  - Observed evidence: `aw prompts --help` now lists `new` (it was `invalid choice: 'prompts'` before this change, confirming F6 that E-04 CREATES the namespace):
    ```console
    $ python3 -m agent_workflows prompts --help
    usage: agent-workflows prompts [-h] [--no-color] [--agent] [--json] {new} ...
    Owner verbs for the operational prompt STAGING tree in .aw/records/prompts/: 'new' mints a conforming staged prompt into pending/, and 'set' transitions a staged prompt's status. ...
    positional arguments:
      {new}
        new       Mint a conforming staged prompt in pending/ (dry-run by default;
                  --apply to write).
    ```
    ```console
    $ python3 -m agent_workflows prompts new --help
    usage: agent-workflows prompts new [-h] [--no-color] [--agent] [--json]
                                       [--dir DIR] [--slug SLUG] [--kind KIND]
                                       [--status STATUS] [--author AUTHOR]
                                       [--targets TARGETS] [--concerns CONCERNS]
                                       [--date DATE] [--time TIME] [--apply]
    ```
    `python3 -m agent_workflows prompts new` reaches the same code path (same renderer output as the `aw` form):
    ```console
    $ python3 -m agent_workflows prompts new --slug module-path-check --date 2026-08-30 --time 1200 --dir /tmp/opencode/pnew
    --- would write /tmp/opencode/pnew/.aw/records/prompts/pending/20260830-1200-01-module-path-check.prompt.md ---
    <!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-30 . This HTML comment is pipeline metadata only; ... -->
    EXIT=0
    ```
    `TYPE_BACKENDS["prompts"]` with `new` alongside the pre-existing `rename`/`group`, and the registry resolving `("prompts", "new")` to the real callable:
    ```python
    "prompts": {
        "new": "prompts.run_new",
        "rename": "artifact_rename.run_rename_prompts",
        "group": "artifact_rename.run_group_prompts",
    },
    ```
    (`tests/test_prompts_new.py::TestBackendRegistration::test_prompts_new_resolves_through_the_type_backend_registry` asserts `at.resolve_backend("prompts", "new") is prompts_mod.run_new`.)
    THE NEW DECLARATION, and the `specs new` entry (`command_surface.py:1053-1066`) it was modeled on. Every field matches the model except the real flag list and the narrower exit contract (this verb has no findings state, so `(0, 2)`):
    ```python
    # NEW (mine)                                  # MODEL (specs new)
    command="prompts new",                        command="specs new",
    command_class="mutation",                     command_class="mutation",
    human_recipe="preview",                       human_recipe="preview",
    agent_record_kind="result",                   agent_record_kind="result",
    mutation_gate="dry_run_default",              mutation_gate="dry_run_default",
    empty_error_renderer="renderer_boundary",     empty_error_renderer="renderer_boundary",
    legacy_flags=("--slug","--kind","--status",   legacy_flags=("--title","--slug",
      "--author","--targets","--concerns",          "--summary","--date","--apply"),
      "--date","--time","--apply"),
    exit_contract=(0, 2),                         exit_contract=(0, 2),
    ```
    THE UNDECLARED-LEAVES TEST IS RED IN BOTH DIRECTIONS AND IS NOT CLAIMED AS PASSING. Baseline, measured on a clean worktree of `d4d265b` (this run's starting HEAD; the plan recorded `f02c64e` from review time, and the count is unchanged at 59):
    ```console
    $ python3 -m pytest tests/test_command_surface_declarations.py -m ''
    E  AssertionError: 59 != 0 : Found undeclared parser leaves: {'conf get', 'work begin', ... 'spec new', 'specs scaffold'}
    1 failed, 13 passed in 8.07s
    ```
    Post-change, at `42ec759`:
    ```console
    $ python3 -m pytest tests/test_command_surface_declarations.py -m ''
    E  AssertionError: 59 != 0 : Found undeclared parser leaves: {'conf exclude add', 'config get', ... 'specs scaffold'}
    1 failed, 13 passed in 7.57s
    ```
    THE PROVABLE THING, proven: the count did NOT grow (59 -> 59) and `prompts new` is ABSENT from the post-change reported set. Asserted in code too, so it cannot silently regress: `TestBackendRegistration::test_prompts_new_is_not_an_undeclared_parser_leaf` does `assertNotIn("prompts new", find_undeclared_leaves(_build_parser()))`. The other 59 leaves were NOT declared; they belong to other verbs and are out of this plan's fence.
    ADDITIONALLY VERIFIED (not required, but it is the guard the declaration exists to satisfy): the conformance matrix gives `prompts new` full scenario coverage, so the declaration is not merely present but complete. `required_scenarios(decl)` and `report.scenarios_for("prompts new")` are both `['agent','help','no_color','non_tty','success_preview','tty','usage_error']` with `MISSING: []`, and `report.declared_absent` is still exactly `{'prompts set'}`, so `test_declared_absent_leaves_are_only_the_known_prompts_family` is unaffected.
    NO `check` STUB WAS ADDED: `aw prompts --help` lists only `{new}`. `aw prompts check` remains owned by the approved purity spec, whose assumed attachment point now exists.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the rewritten Step 4 and exit gate. Paste a grep over the workflow file proving no instruction to compute a timestamp/sequence or hand-write metadata remains. Confirm the leak-scan and never-auto-commit requirements are still present. Confirm no em or en dash was introduced.
  - Observed evidence: THE REWRITTEN STEP 4 (was: "1. Determine the timestamp and sequence number ... 2. Write the file to ..."):
    ```markdown
    ## Step 4: Mint the file with `aw prompts new`, then write the body into it

    1. MINT the staged file with the verb. It derives the filename and writes the metadata comment; you supply the metadata fields:

       ```bash
       aw prompts new --kind research \
         --slug <topic-slug> \
         --author '<agent> (<model>)' \
         --targets '<target-ai-models>' \
         --concerns '<short-summary>' \
         --apply
       ```

       Omit `--apply` first if you want to preview the path it will use. The verb prints the path it wrote; use that path for the remaining steps. Do NOT compute a timestamp or sequence number, and do NOT hand-write the `<!-- aw-prompt: ... -->` comment: both are the verb's job, and hand-writing them is what drifted the existing corpus.

    2. APPEND your Step 3 prompt body to that file, after the metadata comment the verb wrote. Add nothing else: no user-facing instructions, no delimiters, no template scaffolding.
    3. Run `aw check-local-leaks <the-file>` (or `python3 -m agent_workflows check-local-leaks <the-file> --agent`) to ensure no machine or maintainer identifying leaks were introduced.
    4. Do NOT stage or commit the file.
    ```
    THE REWRITTEN EXIT GATE (first and fifth items changed; the rest retained verbatim):
    ```markdown
    - [ ] File was MINTED by `aw prompts new` (not hand-named, not hand-written metadata) and landed under `.aw/records/prompts/pending/`.
    - [ ] Emitted prompt contains ONLY the prompt addressed to the target AI (no user-facing instructions inside it).
    - [ ] Emitted prompt is completely self-contained.
    - [ ] Emitted prompt instructs the target AI to return its output as a DOWNLOADABLE markdown (`.md`) file.
    - [ ] File begins with the single-line `<!-- aw-prompt: Kind: research | Status: pending ... -->` metadata comment the verb emitted, with nothing before it.
    - [ ] `aw check-local-leaks` run on the finished file with zero violations.
    - [ ] No product code modified; prompt file is NOT auto-staged or committed.
    - [ ] User informed of the staged prompt path and how to upload/paste it to the target AI.
    ```
    Step 3 was also retitled "Draft the prompt BODY only" and its template no longer contains a hand-typed `aw-prompt` comment line to copy, which was the other place the old file invited hand-writing metadata.
    GREP PROVING NO HAND-NAMING INSTRUCTION SURVIVES. Both remaining matches are the NEGATION of the old instruction, not the instruction:
    ```console
    $ grep -n -i "determine the timestamp\|sequence number\|YYYYMMDD-HHMM" research-prompt.md
    9:   ... minted by `aw prompts new` into `.aw/records/prompts/pending/`. The verb derives the filename (`YYYYMMDD-HHMM-NN-<slug>.prompt.md`); never hand-name it.
    108:   ... Do NOT compute a timestamp or sequence number, and do NOT hand-write the `<!-- aw-prompt: ... -->` comment: both are the verb's job ...
    ```
    The old `:98` "Determine the timestamp and sequence number" instruction and the old `:105` hand-written filename gate item are GONE. `aw prompts new` is now named at 9 places in the file (`:9`, `:27`, `:28`, `:39`, `:66`, `:95`, `:100`, `:116`, `:129`).
    LEAK-SCAN AND NEVER-AUTO-COMMIT REQUIREMENTS INTACT (all six survive):
    ```console
    $ grep -n "check-local-leaks\|stage or commit\|auto-stage\|auto-commit" research-prompt.md
    28:3. **Target Tracked Pending Lane:** `aw prompts new` writes to `.aw/records/prompts/pending/` with `Status: pending`. Never auto-stage or commit.
    29:4. **Leak Sanitizer Awareness:** Run `aw check-local-leaks` on the finished file before concluding.
    111:3. Run `aw check-local-leaks <the-file>` ... to ensure no machine or maintainer identifying leaks were introduced.
    112:4. Do NOT stage or commit the file.
    121:- [ ] `aw check-local-leaks` run on the finished file with zero violations.
    122:- [ ] No product code modified; prompt file is NOT auto-staged or committed.
    130:- Never auto-commit the generated prompt.
    ```
    NO EM OR EN DASH INTRODUCED, checked on all three prose files I authored:
    ```console
    $ for f in .aw/records/prompts/README.md .../research-prompt.md agent_workflows/prompts.py; do grep -n $'\u2014\|\u2013' "$f" || echo "   (none)"; done
    -- .aw/records/prompts/README.md
       (none)
    -- .aw/system/workflows/research-prompt/research-prompt.md
       (none)
    -- agent_workflows/prompts.py
       (none)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the full test module output passing under the DEFAULT parallel invocation (not a serialized run), proving the clock was pinned rather than raced. Paste falsifiability evidence as actual failures: the dry-run case against an eager writer, the collision case against a `pending/`-only sequencer, and the rejection case against a permissive `--kind`.
  - Observed evidence: FULL MODULE UNDER THE DEFAULT PARALLEL INVOCATION (12 xdist workers, random ordering, no `-n` or `-p no:randomly` added), at `42ec759`:
    ```console
    $ python3 -m pytest tests/test_prompts_new.py -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=520124519
    rootdir: <repo>/.aw/worktrees/jxqdcw
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    created: 12/12 workers
    12 workers [15 items]

    ...............                                                          [100%]
    ============================== 15 passed in 2.30s ==============================
    ```
    THE CLOCK IS PINNED, NOT RACED, which is what makes the sequence tests safe under parallelism: every sequence assertion passes explicit `--date 2026-08-30 --time 0930`, and the one case that exercises the DEFAULT clock (`test_default_clock_is_used_when_date_and_time_omitted`) patches `prompts._now` to a fixed `datetime(2026, 8, 30, 9, 30)`. `_now()` exists as a single seam for exactly this reason. Each test also gets its own `tempfile.mkdtemp` repo, so workers cannot see each other's prompts trees.
    FALSIFIABILITY, PROVEN AS ACTUAL FAILURES against three deliberately broken implementations (each break reverted immediately; the module was re-run green afterward, `15 passed`):
    1. EAGER WRITER (`if not getattr(args, "apply", False):` -> `if False:`, i.e. always write):
    ```console
    $ python3 -m pytest tests/test_prompts_new.py -k dry_run
    >       self.assertIn("would write", out)
    E       AssertionError: 'would write' not found in 'aw prompts new: wrote /tmp/aw_test_prompts_new_d1on41j0/.aw/records/prompts/pending/20260830-0930-01-token-compression.prompt.md\n'
    FAILED tests/test_prompts_new.py::TestDryRunDefault::test_dry_run_prints_intended_path_and_writes_nothing
    1 failed in 2.27s
    ```
    2. `pending/`-ONLY SEQUENCER (`root.rglob` -> `(root / "pending").rglob`):
    ```console
    $ python3 -m pytest tests/test_prompts_new.py -k collide
    E       - ['20260830-0930-01-fresh-topic.prompt.md']
    E       + ['20260830-0930-02-fresh-topic.prompt.md']
    FAILED tests/test_prompts_new.py::TestPerMinuteSequence::test_sequence_does_not_collide_with_same_minute_file_in_executed
    1 failed in 2.25s
    ```
    3. PERMISSIVE `--kind` (`if kind not in PROMPT_KINDS:` -> `if False:`):
    ```console
    $ python3 -m pytest tests/test_prompts_new.py -k unrecognized
    >       self.assertNotEqual(rc, 0, out)
    E       AssertionError: 0 == 0 : aw prompts new: wrote /tmp/aw_test_prompts_new_mni8bemv/.aw/records/prompts/pending/20260830-0223-01-bad-kind.prompt.md
    FAILED tests/test_prompts_new.py::TestRejections::test_unrecognized_kind_exits_nonzero_and_writes_nothing
    1 failed in 2.06s
    ```
    All three required cases fail against a naive implementation, so they are load-bearing rather than decorative.
    SUITE-WIDE, NO REGRESSION. Failure sets were diffed against a clean worktree of the starting HEAD `d4d265b` rather than eyeballed:
    ```console
    $ python3 -m pytest                 # fast suite, at 42ec759
    15 failed, 2927 passed, 3 skipped, 4 xfailed in 28.86s
    $ python3 -m pytest                 # fast suite, baseline d4d265b
    15 failed, 2912 passed, 3 skipped, 4 xfailed in 59.69s
    $ python3 -m pytest -m ""            # full suite, at 42ec759
    19 failed, 3254 passed, 3 skipped, 4 xfailed in 94.46s
    $ python3 -m pytest -m ""            # full suite, baseline d4d265b
    19 failed, 3239 passed, 3 skipped, 4 xfailed in 110.10s
    $ diff before.txt after.txt && echo "IDENTICAL FAILURE SETS (19 each)"
    IDENTICAL FAILURE SETS (19 each)
    ```
    The failure SET is byte-identical to baseline, and passes rose by exactly the 15 new tests. The 19 pre-existing failures are 15 in `tests/test_run_viewer.py`, plus `test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`, `test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`, `test_cli_conformance_matrix.py::test_every_declared_leaf_gets_a_full_scenario_row_set` (all three are the same 59-undeclared-leaves debt, F8), and `test_cli.py::test_every_subparser_has_fuller_description` (44 pre-existing empty descriptions, verified at baseline with an identical problem list containing no `prompts` entry). None is mine and none is fixed here.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. Right-sizing checked per leaf: E-01 the naming decision, E-02 the verb, E-03 the metadata line, E-04 the registration, E-05 the workflow caller, E-06 the tests. Each has its own falsifiable surface.

Open questions: ALL RESOLVED, and notably the item's own OPEN DESIGN QUESTION is resolved from repository evidence (an approved spec already sanctions the `aw prompts` namespace, and `prompts` is already a registered artifact type missing only `new`), so no maintainer decision is required on the design. THE TWO FENCE QUESTIONS THE DRAFT LEFT OPEN WERE CLOSED AT REVIEW, because both were certainties whose deferral guaranteed a mid-execution halt rather than a maintainer choice: `.aw/records/prompts/README.md` and `agent_workflows/command_surface.py` are now both in `Scope-Paths` (F8, F9). The maintainer should be aware of THREE things rather than hidden assumptions. First, the README fix now also replaces its YAML `front-matter Kind:` language, because the approved purity spec forbids YAML front-matter and the README currently contradicts the very convention this verb emits; if you would rather the README change land with the purity lint instead, say so, and E-01 must then be narrowed to the filename only and the contradiction recorded. Second, `test_zero_undeclared_parser_leaves` is already RED at baseline with 59 undeclared leaves, so this plan cannot turn it green and does not try; if you want that debt paid, it is separate work. Third, per F11 this verb IS the `aw prompts scaffold` contemplated by the purity spec's OQ5, named `new` for consistency with `aw specs new`; confirm you want that name so a second overlapping verb is never added.

Scope fence: touch ONLY `agent_workflows/prompts.py` (new), `agent_workflows/cli.py`, `agent_workflows/artifact_types.py`, `agent_workflows/command_surface.py`, `.aw/records/prompts/README.md`, `.aw/system/workflows/research-prompt/research-prompt.md`, and the new `tests/test_prompts_new.py`. Do NOT implement `aw prompts check` (owned by the approved purity spec), do NOT declare the 59 pre-existing undeclared CLI leaves, do NOT add an id6 to prompt names, do NOT add a lifecycle transition verb, do NOT touch `aw research` or `.aw/records/research/`, do NOT write to or promote from the gitignored `local/` or `untracked/` lanes, do NOT rewrite the `handoff` workflow's front-matter instruction (F10; record the conflict instead), and do NOT edit AGENTS.md managed blocks. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with concurrent agents and `cli.py` is one of the most contended files in it, so re-read it immediately before editing and locate insertion points by how `specs` is registered rather than by line number. Line numbers are deliberately omitted from this plan.

Cleanup obligation specific to this plan: your end-to-end check MINTS A REAL PROMPT into the tracked staging lane. That lane currently holds exactly one genuine prompt, so remove or retire your artifact when done rather than leaving test residue in a queue other people read.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
