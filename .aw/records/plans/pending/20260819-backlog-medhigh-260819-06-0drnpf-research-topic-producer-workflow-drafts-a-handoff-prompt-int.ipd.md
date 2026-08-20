# IPD: research topic producer workflow drafts a handoff prompt into prompts pending

- Date: 2026-08-19
- Kind: child
- Concern: There is no in-agent capability that turns a research topic into a house-conformant, upload-ready research handoff PROMPT and stages it. Authors hand-write these prompts, drifting from the AGENTS.md "Writing prompts for another AI" contract and the prompts staging lifecycle.
- Scope: Add ONE new standalone producer workflow (markdown body plus README) that, given a topic, DRAFTS an upload-ready research handoff prompt into the tracked prompts pending lane; register it in the workflows manifest; regenerate its per-host slash shim; add a test asserting the workflow file, index entry, shim, and prompt-purity rules are present. Not python beyond the manifest-driven shim. OUT: implementing the research itself, an `aw prompts` lint verb, and any change to `aw research`.
- Status: approved
- Set: backlog-medhigh-260819
- Order: 6
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0drnpf
- Approval: maintainer (human), 2026-08-19: blanket-approved the backlog-medhigh-260819 Set for unattended execution.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): drafted body from investigation of the handoff producer, the workflows manifest, the shim generator, and the prompts staging lifecycle.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-06-1 status->to-review->reviewed. Uses the canonical `python3 -m unittest discover` serial runner already (no runner fix needed). `.prompt.md` facet target confirmed against the live prompts lane and `ARTIFACT_TYPE_FACETS`. Anchors verified (index.md manifest markers/family prose:213, cli.py:771 `aw research`, handoff producer precedent). OQ-01 remains non-blocking OPEN (maintainer slash-name choice `/research-prompt` vs reserved `/research`, a one-line manifest rename). Verdict per open question: REVIEWED - OPEN QUESTIONS; readiness NO-GO until the maintainer confirms the name at approval.

## Goal

Add a producer workflow, invoked as `/research-prompt [topic]`, that DRAFTS a house-conformant, upload-ready research handoff prompt (a `.prompt.md`) into the tracked prompts pending lane `.aw/records/prompts/pending/`, so an author can get a compliant research prompt for another AI without hand-writing it and without drifting from the AGENTS.md prompt-purity contract.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Author the producer workflow

- [ ] E-01 Create `.aw/system/workflows/research-prompt/research-prompt.md`, a standalone producer workflow body. It takes `$ARGUMENTS` as the research topic (bare invocation asks for the topic). It gathers the topic, scope, and known constraints, then WRITES ONE upload-ready research handoff prompt to `.aw/records/prompts/pending/YYYYMMDD-HHMM-NN-research-<slug>.prompt.md`. The body MUST encode the AGENTS.md "Writing prompts for another AI" contract by construction: the emitted prompt contains ONLY the prompt addressed to the target AI (no user-facing instructions inside it), is self-contained, and instructs the target AI to return its answer as a DOWNLOADABLE `.md` file. It MUST also state the naming-collision distinction (this PRODUCES a prompt for another AI to do research; it is NOT `aw research new`, which creates a research DOC), carry pipeline metadata as a leading HTML comment (the sanctioned pasteable-metadata pattern), and state that it writes a `Status: pending` draft and never auto-commits.
  - Depends on: none
  - Expected outcome: `.aw/system/workflows/research-prompt/research-prompt.md` exists, follows the standalone-workflow shape (controlling header, operating principles, Step 0 discover, steps, explicit what-it-does/does-not-change), and contains the three prompt-purity requirements verbatim in intent (only-the-prompt, self-contained, downloadable-`.md`).
  - Execution state: pending
- [ ] E-02 Create `.aw/system/workflows/research-prompt/README.md` mirroring the existing per-workflow README shape (one-paragraph summary, the `/aw research [topic]` invocation, the universal "read and execute `.aw/system/workflows/research-prompt/research-prompt.md`" fallback, and a pointer to the index and to `aw research` for the distinct research-doc verb).
  - Depends on: E-01
  - Expected outcome: `.aw/system/workflows/research-prompt/README.md` exists and matches the shape of `.aw/system/workflows/handoff/README.md`.
  - Execution state: pending

### Task group 2: Register and wire the workflow

- [ ] E-03 Add one manifest row for the workflow inside the `WORKFLOWS-MANIFEST` markers in `.aw/system/workflows/index.md`, keeping the `command | body | lens | description` columns stable (body = `.aw/system/workflows/research-prompt/research-prompt.md`, lens = `-`). MAINTAINER DECISION: this producer is invoked as the `research` VERB under the single `/aw` dispatcher (Order 05), i.e. `/aw research [topic]` - NOT a standalone `/research-prompt` shim and NOT the bare reserved `/research`. So the manifest `command` cell registers it as the dispatcher verb `research` (matching how Order 05 routes verbs into the manifest); update the `agent-continuity-workflows` family prose to reference `/aw research` and state why it is namespaced (avoids the reserved `/research` + the distinct `aw research` doc verb).
  - Depends on: E-02
  - Expected outcome: `.aw/system/workflows/index.md` registers the producer as the `/aw research` verb (dispatcher-routed), the family prose references `/aw research`; the manifest columns are unchanged.
  - Execution state: pending
- [ ] E-04 Verify `/aw research` routes to the producer via the Order 05 dispatcher; do NOT generate a standalone per-host `research-prompt` shim (the whole point of `/aw research` is that it is reached through the `/aw` dispatcher, not its own command file). After `aw install .` (regenerating shims), confirm NO `.opencode/commands/research-prompt.md` / `.claude/commands/research-prompt.md` standalone shim is produced, and that `/aw research` resolves to the workflow body through the dispatcher's manifest lookup. (This Order DEPENDS on Order 05 having landed the `/aw` dispatcher.)
  - Depends on: E-03
  - Expected outcome: `/aw research` resolves to the producer workflow body via the dispatcher; no standalone research-prompt command shim exists; `aw install .` does not create one.
  - Execution state: pending

### Task group 3: Test, validate, and close the backlog item

- [ ] E-05 Add a test (e.g. `tests/test_research_prompt_workflow.py`, stdlib `unittest`) asserting: the workflow body file exists; the README exists; the manifest row exists in `index.md` and points at the body; the producer is reachable as the `/aw research` verb (dispatcher manifest lookup resolves `research` to the body) and NO standalone `research-prompt` host shim exists; and the workflow body contains the three AGENTS.md prompt-purity requirements (only-the-prompt, self-contained, downloadable-`.md`). Then run the full serial suite (`python3 -m pytest -p no:xdist`) and capture the actual output.
  - Depends on: E-04
  - Expected outcome: the new test file exists and passes, and the full serial suite passes with pasted runner output.
  - Execution state: pending
- [ ] E-06 Close backlog item `6wlo04` to `done` with `aw backlog set .aw/records/backlog/open/20260815-research-prompt-pipeline-01-6wlo04-research-workflow-producer.backlog.md --status done --message "shipped /research-prompt producer workflow"`.
  - Depends on: E-05
  - Expected outcome: `6wlo04` reports `Status: done` and `aw backlog check` is clean.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Prompts staging is TRACKED and lifecycle-organized under `.aw/records/prompts/` (`pending/` -> `executed/` -> `superseded/`/`not-executed/`, plus standing `reusable/`); files are named `YYYYMMDD-HHMM-NN-<slug>.md` (`.aw/records/prompts/README.md:3`, `:32`). The `local/` lane is GITIGNORED quarantine and distinct from the tracked buckets (`.aw/records/prompts/README.md:44`).
- The AGENTS.md "Writing prompts for another AI" contract requires an upload-ready prompt: only the prompt, self-contained, and instructs the target AI to return a downloadable `.md` (`AGENTS.md:14`).
- `handoff` is the precedent producer workflow: it drafts a prompt into the prompts lane and never auto-commits (`.aw/system/workflows/handoff/handoff.md:15`, `:108`), though it targets the gitignored `local/` lane rather than tracked `pending/`.
- The workflows manifest is a table between the `WORKFLOWS-MANIFEST` markers with stable columns `command | body | lens | description`; the installer reads it to generate per-tool shims (`.aw/system/workflows/index.md:28`, `:19`).
- The index already reserves a "future `/research`" as part of the `agent-continuity-workflows` family (`.aw/system/workflows/index.md:213`) - a naming hazard.
- `aw research new` is a distinct CLI verb that creates a research DOC under `.aw/records/research/`, not a prompt (`AGENTS.md:21`, `agent_workflows/cli.py:771`). This workflow drafts a PROMPT for another AI to do the research.
- Shim host directories are `.opencode/commands` and `.claude/commands` (plural), generated from the manifest by the engine (`agent_workflows/engine.py:16`, `:133`, `:821`); a bare row (no lens) gets the generic per-host shim (`agent_workflows/engine.py:666`).
- The scaffold workflow documents the "create file(s) -> add manifest row -> regenerate shims" wiring flow (`.aw/system/workflows/scaffold/scaffold.md:22`, `:72`, `:82`).
- The serial test runner is `python3 -m unittest discover -s tests -t .` (`CONTRIBUTING.md:108`); tests are stdlib `unittest` (e.g. `tests/test_manifest.py:11`).
- Backlog item `6wlo04` lives at `.aw/records/backlog/open/20260815-research-prompt-pipeline-01-6wlo04-research-workflow-producer.backlog.md` and is transitioned with `aw backlog set ... --status done`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The backlog says `/research [topic]`, but `/research` is already reserved as a future name and `aw research` is a live verb. | `.aw/system/workflows/index.md:213`; `agent_workflows/cli.py:771`; backlog `6wlo04` summary. |
| F2 | A producer that drafts into the prompts lane already exists as a pattern (handoff), so this is a variation, not new machinery. | `.aw/system/workflows/handoff/handoff.md:15`, `:108`. |
| F3 | The target lane must be tracked `pending/`, not the gitignored `local/` handoff uses. | `.aw/records/prompts/README.md:33`, `:44`. |
| F4 | There is no `aw prompts check` verb yet, so prompt-purity cannot be lint-gated by a CLI; the workflow must enforce the contract by construction and the test asserts the contract text is present in the body. | `aw --help` command list has no `prompts`; spec `.aw/records/specs/20260808-1958-01-prompt-purity-lint.spec.md:67` is unimplemented. |
| F5 | Wiring a workflow is a fixed sequence: create files, add a manifest row, regenerate shims via `aw install .`. | `.aw/system/workflows/scaffold/scaffold.md:72`, `:82`. |

## Proposed changes (ordered, validatable)

1. Author `.aw/system/workflows/research-prompt/research-prompt.md` as a standalone producer workflow encoding the AGENTS.md prompt-purity contract and writing to `.aw/records/prompts/pending/` (E-01).
2. Author its `README.md` (E-02).
3. Register the `research-prompt` manifest row and update the family prose in `index.md` (E-03).
4. Regenerate the per-host shims with `aw install .` (E-04).
5. Add the existence + prompt-purity test and run the full serial suite (E-05).
6. Close backlog `6wlo04` (E-06).

## Deferred / out of scope (with reason)

- Implementing the research itself: out of scope; this is a PRODUCER that emits a prompt for another AI to run.
- An `aw prompts check` prompt-purity lint verb: deferred to its own spec (`20260808-1958-01-prompt-purity-lint.spec.md`); this Order enforces purity by construction plus a text-presence test, not a new CLI gate.
- Any change to `aw research` / research records: out of scope; kept deliberately distinct to avoid the naming collision.
- Folding the shim into a single `/aw` namespace: owned by Order 05 of this Set; this Order only generates the standard per-host shim.

## Scope check

- Over-scope: none. No product-code change beyond the manifest-driven shim regeneration; the test is additive.
- Under-scope: the workflow does not validate an emitted prompt with a CLI lint (no such verb exists); mitigated by encoding the contract in the body and asserting its presence in the test.

## Required tests / validation

- New test `tests/test_research_prompt_workflow.py` (stdlib `unittest`): asserts the workflow body, README, manifest row, and both host shims exist, and that the body carries the three prompt-purity requirements.
- Full serial suite: `python3 -m unittest discover -s tests -t .`, with actual runner output pasted into the V evidence.
- `aw backlog check` clean after closing `6wlo04`.

## Spec / documentation sync

- Update the `agent-continuity-workflows` family prose in `.aw/system/workflows/index.md` (the "future `/research`" line) to name the shipped `/research-prompt` and explain the divergence from `aw research`.
- The per-workflow `README.md` (E-02) is the workflow's own doc. No other spec requires update; the prompt-purity lint spec remains a separate deferred item.

## Open questions

### OQ-01: Is `/research-prompt` the right slash name given the reserved `/research` and the `aw research` verb?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: This plan chooses `/research-prompt` (workflow dir `research-prompt/`) precisely to avoid the collision with the reserved `/research` name (`.aw/system/workflows/index.md:213`) and the distinct `aw research` doc verb (`agent_workflows/cli.py:771`). The name reads as "produce a research prompt," which is exactly what it does. RESOLVED (maintainer 2026-08-19): invoke it as `/aw research` - the `research` VERB under the Order 05 `/aw` dispatcher. This sidesteps BOTH collisions (it is namespaced under `/aw`, so it is neither the reserved bare `/research` nor the `aw research` CLI doc verb) and needs no standalone shim. Consequence: this Order now DEPENDS on Order 05 (the dispatcher must exist first); execute 05 before 06.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `.aw/system/workflows/research-prompt/research-prompt.md` exists; grep of the body shows the three prompt-purity requirements (only-the-prompt / self-contained / downloadable-`.md`), the `.aw/records/prompts/pending/` target path, the `aw research` distinction, and the never-auto-commit statement.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `.aw/system/workflows/research-prompt/README.md` exists and contains the `/aw research [topic]` invocation, the read-and-execute fallback, and the index pointer.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `index.md` shows a `research-prompt` manifest row between the `WORKFLOWS-MANIFEST` markers pointing at the body; the columns are unchanged; the family prose names `/research-prompt`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `.opencode/commands/research-prompt.md` and `.claude/commands/research-prompt.md` exist after `aw install .`, each referencing the workflow body.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_research_prompt_workflow.py` exists; pasted output of `python3 -m unittest discover -s tests -t .` shows the new test and the full suite passing (`OK`).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: `6wlo04` file is under `.aw/records/backlog/done/` with `Status: done`; `aw backlog check` exits 0 (pasted output).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution is gated on explicit human approval. On approval, execute E-01..E-06 in order, verify every V item with concrete pasted evidence (workflow files, manifest row, both shims, full-suite `OK`, backlog `done` + clean check), and only then run `aw ipd lint --phase pre-transition`, set the terminal `Status`, append the workflow-history line, and `git mv` this plan into `.aw/records/plans/executed/` as the post-gate lifecycle transaction. Commit only the files this plan changed, path-scoped; never `git add -A`, never push, never tag or release. If any validation fails, STOP and report rather than marking the plan executed.
