# Review findings: spec 6kwd2e

- Subject-Id: 6kwd2e
- Subject-Type: spec
- Reviewed-At: 2026-09-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9697856e`. Structural preflight `aw specs check` CONFORMED (exit 0) before and after
revision. No pre-review snapshot needed: the spec was committed and unmodified.

THE STRONGEST SPEC OF THE FOUR, AND THE ONE WHOSE CITATIONS MOST NEEDED CHECKING. Its defect analysis is
exact and I re-verified the load-bearing parts: `question: deny` really is injected into a lane's
permission policy, `DEFAULT_STALL_TIMEOUT` really is 600 seconds and a silent child really is killed,
`prompt_for_gate_phrase` really is a 10-second exact-phrase admission gate whose docstring says a timeout
'can never grant an admission', and the interrupt menu's `readline()` really is described by its own
safety predicate as more dangerous than the measured wedge it followed. The three reasons parking beats a
live ask hold. Its own prior self-review had already found six defects, and the design is better for it.

THE ONE MATERIAL CORRECTION IS AN 'ALREADY EXISTS' THAT DOES NOT. R4a.1 says the open-questions renderer
'already exists' and frames the requirement as being about WHEN it is written. The RENDERER exists; the
WRITER is unwired. `set_records.write_local_projections` is the only function that writes that file and it
has NO caller anywhere in the package: two tests call it, and neither runner imports `set_records` at all
(the sole importer is `run_cli.py`, which only READS). So no live run has ever written the projection, and
`aw runs questions` returns exit 2 for every real run today. R4a.2's 'satisfying R4a.1 satisfies this' is
therefore conditional on wiring that does not exist, and an implementer reading 'about WHEN' would look
for a call to move and find none.

THE SPEC ALSO SENT AN IMPLEMENTER TO THE WRONG TABLE. R4a.6 requires a parked item to map to the
cross-tree class `ready` rather than `blocked`. But that class comes from a per-tree map keyed on the
ARTIFACT's own `- Status:`, and parking does not change it: a parked plan is still `approved` or
`to-review`, both of which ALREADY map to `ready`. Adding `awaiting-human` to that table would be a
category error, mixing a RUN disposition into an ARTIFACT status enum. The surface that needs the work is
the separate live-run column, whose mapping falls through to a truncated raw string for anything
unrecognized, so `awaiting-human` would render today as `awaitin`. And the natural place an implementer
would put it is beside `blocked`/`dependency-blocked`/`integration-blocked`, which is exactly the grouping
OQ-01 ruled against.

TWO REQUIREMENTS HAD NO CRITERION, and both are ones whose failure is silent. R1.5 is the durability rule
(an answer recorded only under the gitignored run directory is LOST, with no error), and R7.1 is the
human-presence predicate (a forked presence check is how one host comes to prompt when the other does
not). A40 and A41 were added.

ITS MEASURED POPULATION HAS ALREADY TURNED OVER, WHICH ITS OWN CRITERIA DEPEND ON. Section 0.2 names nine
`to-review` plans carrying open questions and A1 asserts against them. All nine are now `approved`; the
`to-review` set is six different plans. The DEFECT is unchanged and structural, so the fix is to phrase
the criteria against a queue SHAPE, which also makes them survive the next turnover.

OQ-02 WAS RESOLVABLE FROM EVIDENCE AND ASSUMED A FREEDOM THAT DOES NOT EXIST. It asks whether the sweep
covers specs and backlog items or plans only. Measured: no host registers `--type`, so no invocation can
put a non-plan artifact in a queue at all. So plans-only is not a choice, it is a consequence, and the
useful consequence for an implementer is the opposite of a scope decision: sweep THE RESOLVED QUEUE rather
than hardcoding a tree, which costs nothing now and widens by construction later. Resolved, with the
underlying concern (a spec's open question gating a dependent plan) recorded as a dependency question
rather than lost with the question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-301 | HIGH | IN-SCOPE | A. the spec describes the current state; G. it can be planned from | `set_records.write_local_projections` has no caller in `agent_workflows/` (only `tests/test_set_coordination.py` and `tests/test_exec_set_workflow.py`); `run_cli.py` is the sole package importer of `set_records` and only reads; `run_cli._run_questions` returns 2 when the file is absent | **R4a.1 SAYS THE MECHANISM 'ALREADY EXISTS' AND FRAMES ITSELF AS BEING ABOUT TIMING, BUT THE WRITER IS UNWIRED.** The renderer exists; nothing in the package calls the function that writes the projection, and neither runner imports the module. So no live run has ever written it, `aw runs questions` returns exit 2 for every real run, and R4a.2's claim that satisfying R4a.1 satisfies it is conditional on wiring the spec does not mention. An implementer looking for a call to move would find none and might conclude the requirement was already met. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | R4a.1 now distinguishes the RENDERER from the WRITER with the measurement, states that R4a.1 must WIRE the writer into both drivers rather than move a call, and records that `aw runs questions` currently returns exit 2 for every real run. The 0.4 dependency bullet reclassified as existing VOCABULARY rather than existing behavior. |
| SR-302 | HIGH | IN-SCOPE | A. correctness; B. requirements are testable | `attention_contract._PLANS_MAP` keyed on the artifact's own `- Status:`, with `approved` and `to-review` both mapping to READY; `attention.get_active_runs_map`'s explicit status list falling through to `raw_st[:7]` | **R4a.6 NAMES THE WRONG SURFACE, AND THE OBVIOUS IMPLEMENTATION IS A CATEGORY ERROR.** The cross-tree class comes from a per-tree ARTIFACT-status map, and parking does not change an artifact's status, so a parked plan already maps to `ready` and there is nothing to add. Adding `awaiting-human` to that table would mix a RUN disposition into an ARTIFACT status enum. The surface that needs work is the separate live-run column, where an unrecognized status truncates to seven characters (`awaitin`) and where the natural grouping an implementer would choose is beside the three `blocked` variants, which is precisely what OQ-01 ruled against. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | R4a.6 rewritten to name the live-run mapping as the surface, require an explicit label rather than the truncation fallback, forbid folding it into the `blocked` group, and state that the `ready` half of OQ-01's ruling is already satisfied by the artifact status being untouched (so nobody 'fixes' it by editing the artifact). A10g strengthened to assert the label text; new A10h pins that parking leaves the artifact status unchanged. |
| SR-303 | MEDIUM | IN-SCOPE | C. acceptance criteria cover the requirements | requirement-to-criterion mapping over the whole spec: R1.5 and R7.1 uncovered | **TWO REQUIREMENTS HAD NO CRITERION, AND BOTH FAIL SILENTLY.** R1.5 is the durability rule: an answer written only under the gitignored run directory is lost permanently with no error, so an uncovered R1.5 is the failure a human would discover by re-answering. R7.1 fixes human presence to the EXISTING predicate; a forked presence check is exactly how `--full-auto` came to mean opposite things on the two hosts. In a 46-criterion spec these two were the gaps. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A40 (R1.5) requires the answer to survive deletion of the run directory, with `- Blocking:` unchanged. A41 (R7.1) requires `--unattended` and `--full-auto` to yield no prompt even with a TTY, plus a grep proving no second presence test was introduced. A coverage statement now closes the section. |
| SR-304 | MEDIUM | IN-SCOPE | A. measured claims are current; C. criteria stay satisfiable | the nine plans of 0.2 (`planprio` x4, `nobugship` x4, `compinert` x1) all now `- Status: approved`; the current `to-review` set is six `dirtygates` plans, four carrying open questions | **A CRITERION ASSERTS AGAINST A POPULATION THAT NO LONGER EXISTS.** A1 names the nine measured plans; every one has moved to `approved` in the day since authoring. The defect is structural and unchanged, so the criterion fails for a reason unrelated to the design, and the same will happen to any replacement phrased against ids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 0.2 keeps its original measurement and gains the turnover, stating that the defect is unchanged and only the instances were transient. A1 rewritten against a queue SHAPE with a fixture, re-deriving the live population as context; A17 generalized from 74 to N with 74 named as the operative case. |
| SR-305 | MEDIUM | IN-SCOPE | E. open questions are dispositioned | `grep -c '\"--type\"'` -> 0 in both runners; `sweep_review_candidates_for_type(repo,'spec')` -> four specs at the function boundary; `enforce_mixed_type_gate`'s call site recording the same limit | **OQ-02 WAS RESOLVABLE FROM EVIDENCE AND ASSUMED A FREEDOM THE CODE DOES NOT OFFER.** It asks whether the sweep covers specs and backlog items or plans only, as though it were a scope choice. No host registers `--type`, so no invocation can put a non-plan artifact in a queue: plans-only is a consequence, not a decision. Leaving it open invited an implementer to hardcode the plans tree as 'the answer', which is the one outcome that does not widen when the flag lands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved to PLANS ONLY, AND NOT BY CHOICE, with the measurement. The useful consequence is stated as a requirement: R1.1 now sweeps THE RESOLVED QUEUE whatever types it holds, never a hardcoded tree, so it widens by construction. The underlying concern (a spec's open question gating a dependent plan; 5 specs past `approved` carry unresolved questions today) is recorded as a DEPENDENCY question owned elsewhere rather than lost with the question. |
| SR-306 | LOW | IN-SCOPE | F. honest limits | `write_local_projections` uncalled; `run_gates` unwired (the spec's own admission); `set_state.SET_WAITING_INPUT`'s transition rules declarative | **'THIS SPEC INVENTS ALMOST NOTHING' UNDERSTATES THE WORK, in a spec that is otherwise scrupulous about sizing.** The claim is true of the VOCABULARY and misleading about the effort: several of the cited pieces have no caller at all, so wiring a new state through two drivers, a statusline, an attention surface and a resume path is the bulk of the spec. A reader could price it as configuration. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The novelty statement keeps its point and gains a paragraph distinguishing existing vocabulary from existing behavior, naming the three uncalled pieces and stating plainly that the work is smaller than inventing the vocabulary and NOT small. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-301 | OQ-02 (does the sweep cover specs and backlog items?) was left open for the maintainer. Ask, or resolve? | RESOLVE from evidence, to PLANS ONLY as a consequence rather than a choice, and turn it into a requirement that R1 sweeps the resolved queue rather than a hardcoded tree. | (a) Ask the maintainer, rejected: the plan-review and spec-review contracts forbid asking a human what the repository answers, and a two-command grep answers it. (b) Leave it open as non-blocking, rejected because the harmful default is the silent one: an implementer would hardcode the plans tree and the sweep would not widen when `--type` lands. (c) Resolve it as 'plans only, by design', rejected as a false framing that would make a temporary limitation look like a decision. | zero `--type` registrations in both drivers; `sweep_review_candidates_for_type` resolving specs only when called directly; the mixed-type gate's call site recording the same honest limit | yes |
| D-302 | R4a.6 names the cross-tree class map, which is the wrong surface. Correct the requirement, or note the discrepancy in this record only? | CORRECT THE REQUIREMENT, naming the live-run mapping, forbidding the `blocked` grouping, and adding a criterion that parking leaves the artifact status untouched. | (a) Note it here only, rejected: the spec is what an implementer reads, and the wrong table is the one they would edit. (b) Add `awaiting-human` to the artifact-status map as the requirement implies, rejected as a category error that would put a RUN disposition into an ARTIFACT status enum, and it is unnecessary since a parked plan's own status already maps to `ready`. (c) Drop the requirement as already satisfied, rejected: the live-run column genuinely needs the explicit label, and without it the state renders as the truncated `awaitin`. | `_PLANS_MAP` keyed on artifact status with `approved`/`to-review` -> READY; `get_active_runs_map`'s explicit list and its `raw_st[:7]` fallback; OQ-01's ruling against the `blocked` grouping | yes |
| D-303 | The nine measured plans of 0.2 have all moved to `approved`. Re-measure and substitute the current set, or phrase the criteria against a shape? | PHRASE AGAINST A SHAPE (a fixture queue of known composition), and re-derive the live population as reported CONTEXT. | (a) Substitute today's six `dirtygates` plans, rejected as repeating the defect with a fresher list: they will turn over too, and a criterion naming ids is stale the moment the queue moves. (b) Leave the nine and note the drift, rejected because the criterion would be knowingly unsatisfiable. (c) Drop the live-population element entirely, rejected because the measured defect's reality is what justifies the spec, so the denominator is worth reporting. | all nine plans measured at `- Status: approved`; the current `to-review` set measured as six different plans, four with open questions | yes |

### Deferred and open

None. Six findings, all FIXED; none deferred, none REPLAN. Both open questions are now `resolved` (OQ-01
was already resolved from evidence at authoring; OQ-02 was resolved by this review).

### Honest limits of this review

- NOTHING IN THIS SPEC IS IMPLEMENTED, so every criterion is prospective. This review verified the spec's
  CITATIONS against the code, and could not verify its DESIGN by execution.
- I VERIFIED THE LOAD-BEARING CITATIONS, NOT ALL OF THEM. `question: deny`, the 600s stall timeout, the
  10s exact-phrase gate, the interrupt menu's unbounded read, the preserved-lane path, the ledger's
  human-actor rule, the projection renderer and writer, the presence predicate, and both attention
  surfaces were checked; the remaining line references were not individually re-derived.
- THE FINGERPRINT DESIGN IS UNTESTED BY CONSTRUCTION. R4.1a requires deterministic driver-computed
  normalization defined in one place, which is the right shape, but whether it deduplicates real questions
  well cannot be known before it exists. The spec's fail-toward-asking-separately rule (R4.1b) is the
  correct hedge and I did not second-guess it.
