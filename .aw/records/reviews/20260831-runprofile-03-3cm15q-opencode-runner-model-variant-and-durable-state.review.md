# Review: OpenCode runner model/variant/profile and durable-state integration

- Plan-Id: 3cm15q
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `6a29f9c0`, working tree clean, plan committed and unchanged. Structural preflight
`aw ipd lint --phase author` reports `conforming`.

Verified its central premise TRUE by execution: `python3 -m agent_workflows oc run --help` shows NO
`--variant` flag, so the plan's Concern ("`aw oc run` currently accepts `--model` but has no `--variant`
path and stores only the model in durable state") is accurate.

THIS IS THE MOST CONTENDED CHILD IN THE SET and the reviewer should weigh that heavily: its Scope-Paths
include `agent_workflows/oc_runipd.py`, which is ALSO in the Scope-Paths of NINE approved plans
(`1o4eif`, `2c122z`, `58ha43`, `6knsrx`, `7p9n2v`, `97df1z`, `qcqhj7`, `rchpms`, `y0gg8o`), and
`tests/test_oc_runipd.py`, shared with `qcqhj7`. Five of those approved plans are the unmerged `wtiso`
lane stack holding 26 commits that `6knsrx` exists to land into exactly this file. Executing this child
before that stack lands means writing into a file about to receive a large merge.

The Set-wide BLOCKER (PR-001, the `0soncw` ordering conflict) is recorded on every member because it
affects each one's executability, but it is ESCALATED once, as a blocking open question on the
orchestrator `3m0urk`, which owns cross-Set sequencing. Six copies of one question would be six places
to answer it inconsistently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Sequencing / G. Plan executability | APPROVED `0soncw` ("Collapse run inspection under aw runs and retire the aw run noun"); its E-05 (`:103-108`) keeps `aw run` only as a deprecation stub returning a NONZERO exit and a message naming `aw runs`; its Scope-Paths include `cli.py`, `completion.py` and `command_surface.py`. Measured across this Set: `aw run as` x16, `aw run ipd` x12, and `grep -rln '0soncw\|runnamecollapse'` over all six plans returns NOTHING. | This plan builds on the `aw run` noun that an APPROVED plan is retiring, and the Set never mentions that plan. They are COMPLEMENTARY, not contradictory: `0soncw` retires the noun explicitly "so the name is free for a future driver verb", and this Set IS that verb, so the fix is ORDER (`0soncw` first, then this Set claims the vacated name). Reversed, `0soncw`'s stub would shadow a namespace this Set had just populated and `aw run as <profile>` would start exiting nonzero. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | OPEN | Cross-Set execution order is the maintainer's decision and `0soncw` itself still carries an unresolved BLOCKING OQ-03, so the prerequisite is not executable yet either. Escalated as a blocking OQ on the orchestrator `3m0urk` (the owner of cross-Set sequencing) rather than duplicated as six separate questions. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness (evidence discipline) | Measured citation counts: this Set has **0** `file:line` citations in ALL SIX plans, versus 9 / 4 / 5 in the comparable `6lu3rq` / `m73aet` / `wlxkoz` plans reviewed the same day. | The Set asserts many things about shipped code ("`cli.py` already registers `aw run` as the run-ledger family", "`oc_models.resolve_config_path()` already mirrors OpenCode configuration discovery") without a single line citation. The claims I spot-checked were TRUE, so this is an evidence-discipline defect rather than a correctness one, but it means an executor cannot re-verify a premise cheaply and cannot tell whether a claim was measured or remembered. That matters most here because the Set edits `cli.py` and `oc_runipd.py`, the two most contended files in the repo. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added a Findings row to each plan recording the gap and requiring the executor to MEASURE and cite `file:line` for every "already" claim before relying on it, since HEAD moves hourly here. |
| PR-003 | MEDIUM | IN-SCOPE | B. Sequencing | Computed: `oc_runipd.py` appears in the Scope-Paths of 9 approved plans, five of which (`qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`) are the unmerged `wtiso` lane stack holding 26 commits that approved `6knsrx` exists to land into this same file | The single most contended file in the repository, and this child edits it. The orchestrator's sequencing note covers `rununify` but not the `wtiso` stack. A child executing here before `6knsrx` lands would be writing into a file about to receive a 26-commit merge, and the lane-side work is reachable only from those branches. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added a Findings row naming the nine colliding plans and requiring the executor to re-measure this file's state against the `wtiso` stack immediately before editing, and to STOP and report if `6knsrx` has begun landing. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Escalate the `0soncw` conflict on this child, or once on the orchestrator? | ONCE on the orchestrator `3m0urk`, recorded as a finding here. | Raising a blocking OQ on all six children. Rejected: one cross-Set ordering decision answered in six places invites six inconsistent answers, and the orchestrator is the artifact that already owns Set-level sequencing (it carries CID-8 for `rununify`). | `3m0urk`'s existing CID-8 and its "STOP and re-review all runner scopes" clause; plan-review Step 2.4 ("fix it in the owning plan and cross-reference it from dependent plans") | yes |
| D-2 | Is the missing `file:line` evidence (PR-002) a BLOCKER or a MEDIUM? | MEDIUM. The claims I spot-checked were true, so this is evidence discipline, not incorrectness. | BLOCKER. Rejected because no verified claim was found to be false, and blocking a Set on citation formatting when its substance holds would be disproportionate. | Spot-checks: `oc_models.resolve_config_path` exists; `aw oc run --help` genuinely lacks `--variant`; `cli.py` genuinely registers the `aw run` family | yes |

## Round 2

Opened 2026-09-04 at the maintainer's direction, to close round 1's PR-001 now that its stated
danger no longer exists and the ordering it asked for is machine-enforced. A NEW ROUND rather than an
edit to round 1: the gate reads only the CURRENT round, and rewriting a completed round would hide
that the finding was ever open (`.aw/records/reviews/README.md`, "Rounds").

NOTHING ABOUT THIS SET'S CODE CHANGED. What changed is the PREREQUISITE, and it changed in the
direction that removes the hazard:

1. `0soncw` NO LONGER RETIRES THE `aw run` NOUN. Round 1's BLOCKER rested on `0soncw` E-05 leaving
   `aw run` as a deprecation stub returning a NONZERO exit, which would have shadowed the namespace
   this Set populates. That was REVERSED by maintainer ruling 2026-08-31 (`0soncw` OQ-03): the
   surface splits BY DIRECTION, `aw run` SURVIVES as the WRITING verb, and only the nine READ-ONLY
   viewer leaves move to `aw runs`. `aw run as <profile>` was never among those nine.
2. `0soncw` E-05 NOW NAMES THIS SET EXPLICITLY as the intended consumer of the surviving noun: "it is
   the noun the `runprofile` Set then extends with `aw run as <profile>`", and it records the
   conclusion this finding reached: "the ordering (`0soncw` first, then `runprofile`) was settled".
3. `0soncw` IS NOW EXECUTABLE, which round 1 explicitly said it was not. Its OQ-03 was resolved
   2026-08-31 and its OQ-01 on 2026-09-03; it carries `Status: approved`, `Item-Dependencies: none`,
   and zero unresolved blocking questions (verified with `plan_readiness.has_unresolved_blocking_question`).
   So round 1's clause "the prerequisite is not executable yet either" is STALE.
4. THE ORDER IS NOW MACHINE-ENFORCED, not prose. Round 1 said "the fix is ORDERING, not redesign",
   but nothing in this Set's metadata encoded it. Orchestrator `3m0urk` now carries
   `- Item-Dependencies: executed:0soncw`, so the shipped pre-execution dependency preflight refuses
   the Set until `0soncw` reaches `executed`. That is what actually discharges the finding: a
   maintainer ruling in prose cannot stop a runner, and a declared edge can.

WHAT IS NOT CLAIMED. This round re-verifies the SEQUENCING premise only. It does not re-review this
plan's substance, and every other round-1 finding keeps the disposition round 1 gave it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Sequencing / G. Plan executability | `0soncw` E-05 (now `:118-128`): "Do NOT retire the `aw run` noun. REVERSED BY MAINTAINER RULING 2026-08-31 (see OQ-03)... it is the noun the `runprofile` Set then extends with `aw run as <profile>`... the ordering (`0soncw` first, then `runprofile`) was settled"; `0soncw` OQ-03 and OQ-01 both `- Status: resolved`; `0soncw` `- Status: approved` with `- Item-Dependencies: none`; `3m0urk` now carries `- Item-Dependencies: executed:0soncw` | CARRIED FORWARD FROM ROUND 1 AND NOW RESOLVED. The finding was correct when raised: this Set built its grammar on `aw run` while an approved plan was retiring that noun, and no plan in the Set mentioned it. Both halves of the hazard are now gone - `0soncw` was re-scoped to KEEP `aw run` as the writing verb and to name this Set as its consumer, and `0soncw`'s own blocking question is resolved so it is executable. The residual requirement, that `0soncw` land FIRST, is now a declared dependency edge rather than a sentence in an open question. | C:Low; U:Low; S:Low; F:Low; Overall:Low (recording an edge the maintainer had already decided; no code or scope change) | FIXED | Maintainer decision 2026-08-31 (order) plus 2026-09-04 (encode it). `3m0urk` now declares `- Item-Dependencies: executed:0soncw`, so the pre-execution preflight enforces the order for the whole Set. Round 1's recommended order was adopted unchanged; nothing in this plan's scope or design was altered. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Close PR-001 by editing round 1's row, or by appending this round? | APPEND round 2, leaving round 1 intact. | Editing round 1's `OPEN` to `FIXED` in place. Rejected: the reviews README states rounds are appended rather than edited precisely so a superseded finding stops gating WITHOUT erasing that it was raised; an in-place edit would make the record claim the BLOCKER never existed. | `.aw/records/reviews/README.md` ("Rounds": the LAST round is current, only current findings are live); `review_findings.current_findings()` semantics | yes |
| D-2 | Put the enforcing edge on the orchestrator `3m0urk`, or on all six Set members? | ON THE ORCHESTRATOR ONLY. | An edge on each of the six children. Rejected: the children already chain to each other (`f2mrsw` -> `executed:0soncw` plus `p0l1to` -> `executed:f2mrsw` and onward), so one edge at Order 0 gates the Set's entry point, and six copies of one cross-Set fact invite six inconsistent answers - the same reasoning round 1's own D-1 used to escalate once rather than six times. | Round 1 D-1 on this Set; the per-child `Item-Dependencies` chain measured across Orders 1-5; `3m0urk` is Order 0 | yes |
