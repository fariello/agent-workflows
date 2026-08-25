# Spec: research lifecycle reliability (make research state, outcome, and provenance tool-owned and verifiable)

- Date: 2026-08-24
- Status: draft
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 5tapom
- Blocks-Release: next
- Parent: `.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md` (the research-org
  design, shipped as DECISIONS D123). This follow-on spec CORRECTS the gap between what the parent
  REQUIRES (B1/B2/H2/F2: reliably identify not-yet-ingested research, compartmentalize by outcome, and
  keep state tool-owned BECAUSE hand-typed status is unreliable) and what the parent's follow-on IPD
  Set actually SHIPPED (a tool that writes `status: intake` and `consumed-by: []` only at CREATION and
  never advances or validates them). It does not edit the parent (an `implemented` spec is
  transition-frozen to deferred/superseded); it extends it.
- Scope: the research lifecycle's RELIABILITY surfaces only - state advancement + unrun detection,
  the `outcome`/`consumed-by` provenance fields as tooled and validated, and the attention/query
  surfacing that consumes them. Implementation is a follow-on IPD Set (`reslife`). No change to the
  filename grammar, the four-state vocabulary, or the shard layout (those shipped and work).

This spec is the load-bearing rationale for the `reslife` IPD Set. It records the observed failure,
the parent requirements it violates, the chosen design and why, and the acceptance criteria, so the
IPD Set can be authored and reviewed against a single source of truth.

---

## 1. Problem statement (observed, with evidence)

The parent spec's central reliability claim is H2: "Hand-typed status is unreliable... a TOOL writes
status at creation AND reads it to build the manifest; state is acceptable in frontmatter precisely
because it is tool-owned, not hand-maintained." B1 restates the operational need: "Cheaply identify
NOT-yet-ingested research... without relying SOLELY on a hand-typed in-file status (proven
unreliable; agents forget to update it)."

In practice only HALF of "tool-owned" was implemented:

- `aw research new`/`new-comparison` hard-code `status="intake"` and `outcome="none-yet"` at creation
  (agent_workflows/research_cmd.py lines ~189 and ~244) and write `consumed-by: []`.
- NOTHING advances `status` after creation, NOTHING ever sets `outcome`, and NOTHING populates or
  validates `consumed-by`. There is no `aw research set-outcome` verb; `aw research index --check`
  does not validate `outcome`/`consumed-by`; `consumed-by` is not even carried in `INDEX.json`.

Consequences, measured in this repo on 2026-08-24 (before a manual triage):

- 11 research docs sat at `intake` though 10 of them had been RUN and ADOPTED (e.g. the `awoptimize`
  set drove 19 executed IPDs; the `agentadhere` set is cited by executed `proclint` and the
  release-blocker backlog `3gr7fk`). `intake` had become a permanent default, not a triage band.
- `aw attention` maps `intake -> ready`, so those finished docs showed as actionable work, inflating
  the "ready" bucket and making "which research must I still run?" unanswerable from the tool. After a
  by-hand triage exactly ONE genuinely-unrun prompt (`actorenv/8it88r`) remained at `intake`.
- `consumed-by` was populated on 1 of ~85 docs, so provenance ("what used this research?") was not
  answerable, and `outcome: adopted` was never recorded even where clearly true.

This is precisely the failure H2/B1 were written to prevent, re-introduced because state was made
tool-WRITTEN-at-creation but not tool-MAINTAINED.

## 2. Parent requirements this spec must satisfy

- B1 `[Must]` Cheaply identify NOT-yet-ingested research without recursively reading the corpus and
  without relying SOLELY on a hand-typed status.
- B2 `[Must]` Clear compartmentalization (active / kept-because-it-mattered / kept-just-in-case)
  discoverable without reading files.
- H2 State reliability: state must be genuinely tool-owned, i.e. advanced and validated by tooling,
  not just written once at creation.
- F2/F4 `[Must]` The manifest is tool-generated from frontmatter; `--check` fails on drift and is a
  CI/pre-commit gate.

## 3. Design

### 3.1 Unrun detection is STRUCTURAL, not status-typed (satisfies B1)

"Not yet run" is derived, not hand-declared: a research SET whose `NN=00` member is a
`kind: research-prompt` and which has NO `NN>=01` sibling members is UNRUN. A set with `NN>=01`
outputs is RUN. This is computed from the manifest (set membership + kind + order), so it is reliable
regardless of whether anyone updated `status`. The tool exposes it (Section 3.4) so "which research
must I still run?" is answerable without reading the corpus and without trusting hand-typed state.

### 3.2 State is tool-ADVANCED and drift-checked (satisfies H2)

- `status` stays the four-state vocabulary (`intake`/`active`/`reference`/`archive`); NO new state.
- `aw research index --check` (and `aw check`) gains a DRIFT rule: a doc at `intake`/`active` whose set
  is RUN (has `NN>=01` outputs) OR which is cited by an executed plan/spec/backlog is flagged as
  stale-state to promote. This makes the unreliable case VISIBLE and fail-closed in CI rather than
  silently accumulating.
- A one-time, reviewed triage pass (the parent's migration step 4: "cited -> reference; uncited/dead-end
  -> archive, as a reviewed pass, not a blind default") is provided as a tool-assisted classifier the
  maintainer confirms, not an automatic mutation.

### 3.3 `outcome` and `consumed-by` become tooled and validated (satisfies B2, provenance)

- A verb sets them deliberately: `aw research set-outcome <id6> --to <adopted|informational|rejected|none-yet>`
  and `--consumed-by <id6[,id6...]>` (append/replace/clear), appending a workflow-history-style record
  where the tree supports it.
- `INDEX.json` carries `outcome` and `consumed-by` (today it omits `consumed-by`).
- `aw research index --check` / `aw check` validate: a `consumed-by` entry must resolve to an existing
  plan/spec/backlog id6 (dangling -> flagged, mirroring the existing citation `--check`); and
  `outcome: adopted` REQUIRES a non-empty `consumed-by` (an adopted doc must name what adopted it).

### 3.4 Surfacing: separate "untriaged" from "actionable" (satisfies B1/B2 at a glance)

- `aw research` gains a pending query: `aw research pending` (or `find --unrun`) listing UNRUN prompts
  (Section 3.1) - the authoritative answer to "what do I still have to run?".
- `aw attention` stops treating plain `intake` as `ready`: an `intake` doc that is UNRUN is surfaced as
  genuine actionable research; an `intake` doc that is RUN/cited is surfaced as stale-state-to-promote
  (a drift item), not as ready work. The exact class split is an implementation choice in the IPD Set
  as long as finished-but-unpromoted research no longer masquerades as actionable.

## 4. Non-goals

- No change to the filename grammar, the four `status` values, the `outcome` vocabulary, the shard
  layout, or `INDEX.md`'s bounded hot-glance design. Those shipped and work.
- No automatic status mutation without human confirmation for the initial triage (H2's whole point is
  distrust of blind writes); ongoing drift is REPORTED by `--check`, remediated deliberately.

## 5. Acceptance criteria (Definition of done for the reslife IPD Set)

1. `aw research pending`/`find --unrun` lists exactly the UNRUN prompts (structural derivation), proven
   against a fixture where a set with outputs is excluded and a bare `NN=00` prompt is included.
2. `aw research index --check` / `aw check` flag: (a) an `intake`/`active` doc whose set is RUN or which
   is cited by an executed artifact; (b) a dangling `consumed-by`; (c) `outcome: adopted` with empty
   `consumed-by`. Each with a regression test; clean when satisfied.
3. `aw research set-outcome` writes `outcome` and `consumed-by`; `INDEX.json` carries both.
4. `aw attention` no longer files finished-but-unpromoted research under `ready`.
5. Whole suite green; the parent spec's B1/B2/H2 are demonstrably met by tests, not prose.

## 6. Open questions

### OQ-01: Does `aw attention` gain a distinct class for "stale-state-to-promote", or reuse an existing one?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to the attention/surfacing child IPD, which owns the
  attention_contract CLASS_MAP change; both a new class and reusing a drift/needs-attention signal are
  viable. Non-blocking for this spec.

### OQ-02: Is the initial triage classifier a new verb or folded into `aw archive`/`promote --suggest`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to the state-advancement child IPD. The 2026-08-24 manual
  triage (10 docs promoted to `reference` with `outcome`/`consumed-by` back-filled) is the reference
  behavior to reproduce tool-assisted.

## Workflow history

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored as the follow-on rationale
  for the reslife IPD Set, correcting the parent research-org spec's unimplemented reliability half
  (tool-owned state/outcome/provenance). Blocks 2.0.0 (f33nrj). Interim: the reslife IPDs cannot carry
  Blocks-Release until vwios6ipd ships the field (IPD-M103), so the release-blocker intent is anchored
  on this spec and the f33nrj record until then.
