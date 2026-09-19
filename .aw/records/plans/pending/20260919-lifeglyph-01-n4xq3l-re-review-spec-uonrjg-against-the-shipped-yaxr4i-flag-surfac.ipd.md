# IPD: Re-review spec uonrjg against the shipped yaxr4i flag surface before any resolver is built

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12a imposes a HARD, NON-OPTIONAL gate on its own implementation: "RE-REVIEW THIS SPEC AFTER `yaxr4i` EXECUTES, BEFORE THE RESOLVER IS BUILT. This is a requirement, not a suggestion." The reason is mechanical rather than procedural: `yaxr4i` moves the exact surface three of the spec's acceptance criteria are written against. It adds a `--color` flag where only `FORCE_COLOR` existed, adds `--no-color` to 25 of 219 subcommands that do not inherit it, settles the precedence between the two, and rewrites `docs/cli-output-contract.md` to retract a published promise that non-TTY stdout adopts `aw.agent/v1`. A11, A12, and A13 must be re-read against the flags AS SHIPPED, and Section 9.3's "MUST preserve current NO_COLOR/FORCE_COLOR/TERM=dumb/TTY behavior" needs re-pointing at whatever "current" then means.
- Scope: IN: run `/spec-review` on `uonrjg` once `yaxr4i` is `executed`, re-read A11/A12/A13 and Section 9.3 against the shipped flag surface and the rewritten contract doc, and record the round in the spec's workflow history. Amend A11/A12/A13/9.3 text if and only if the shipped surface differs from what the spec anticipates. OUT: building any part of the resolver (that is `udgilu` onward), and any change to the spec's palette, glyph table, or mappings, none of which `yaxr4i` touches.
- Scope-Paths: .aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
- Item-Dependencies: executed:yaxr4i
- Status: to-review
- Set: lifeglyph
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n4xq3l
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12a obligation 2. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Discharge the re-review gate spec `uonrjg` Section 12a places on its own implementation, so the resolver is built against the flag surface and output contract as SHIPPED by `yaxr4i` rather than as anticipated in a spec written before it landed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-read the three criteria against shipped behavior

- [ ] E-01 Run `/spec-review` on `.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` at a HEAD where `yaxr4i` is `executed`, and record the round in the spec's `## Workflow history` via `aw specs note`.
  - Depends on: none
  - Expected outcome: A new workflow-history round appended to the spec naming the reviewing agent, the HEAD sha, and the verdict. The spec's `- Status:` stays `approved` (a re-review appends a round; it does not re-open approval).
  - Execution state: pending

- [ ] E-02 Re-read A11, A12, A13, and Section 9.3 against the SHIPPED flag surface, and record for each whether the spec's text still holds. Measure rather than infer: enumerate the `--color`/`--no-color` flag presence across subcommands, and read `docs/cli-output-contract.md` as `yaxr4i` E-05 left it.
  - Depends on: E-01
  - Expected outcome: A per-criterion verdict (holds / needs amendment) recorded in the spec's re-review round, each citing the measurement that supports it. A11 in particular is asserted UNCONDITIONAL by the spec on the strength of the `yaxr4i` OQ-01 ruling; confirm the rewritten contract doc now agrees rather than still carrying the retracted promise.
  - Execution state: pending

- [ ] E-03 Amend A11, A12, A13, or Section 9.3 in the spec if and only if E-02 found a divergence, and state in the round what changed and why. If nothing diverged, record that explicitly rather than silently leaving the section untouched.
  - Depends on: E-02
  - Expected outcome: Either an amended spec whose criteria match shipped behavior, or a recorded finding that no amendment was needed. Both are conforming outcomes; an unrecorded no-op is not.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A spec re-review APPENDS a round and keeps the status; it does not reset to `to-review`. The spec's own Section 12a says so ("a re-review appends a new round and keeps the status `reviewed`"), and `aw specs note` is the tooled path for that append.
- `uonrjg` is `- Status: approved` with `- Blocks-Release: next`, so this plan inherits the release gate per the repo's Blocks-Release policy (AGENTS.md: a graduating plan inherits the item's gate).
- `- Readiness:` is deliberately ABSENT from this plan. It is an output of `/plan-review`, and AGENTS.md forbids an author hand-writing another role's attestation field. `aw ipd lint` refuses an unattested value under IPD-M107.
- Verified 2026-09-19: `yaxr4i` is `- Status: approved` and sits in `.aw/records/plans/pending/`, i.e. it is NOT executed yet. This plan's dependency edge is therefore live, not already-satisfied.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The spec's own Section 12a makes this re-review a precondition on building the resolver, so skipping it would violate the spec being implemented. | `uonrjg` Section 12a, obligation 2: "RE-REVIEW THIS SPEC AFTER `yaxr4i` EXECUTES, BEFORE THE RESOLVER IS BUILT. This is a requirement, not a suggestion." |
| F-02 | High | `yaxr4i` is approved but UNEXECUTED, so the gate cannot be discharged yet and every downstream child in this Set is genuinely blocked behind it. | `aw show yaxr4i` -> `- Status: approved`, file resides in `.aw/records/plans/pending/`, verified 2026-09-19. |
| F-03 | Medium | A11 is the criterion most at risk of being validated against a stale document. The spec warns that `docs/cli-output-contract.md` still carries the unretracted non-TTY promise until `yaxr4i` E-05 rewrites it. | `uonrjg` A11: "DO NOT RE-DERIVE THIS FROM THE CODE ALONE... An implementer reading that document instead of this line would conclude A11 is conditional. It is not." |

## Proposed changes (ordered, validatable)

1. Run the spec-review round once `yaxr4i` is executed (E-01).
2. Re-measure the flag surface and contract doc, and record a per-criterion verdict for A11, A12, A13, and Section 9.3 (E-02).
3. Amend only what diverged, and record the outcome either way (E-03).

## Deferred / out of scope (with reason)

- Building any resolver code: that is children `udgilu` through `7p3tt8` of this Set. This plan deliberately produces no code, because its whole purpose is to establish that the code is built against a settled contract.
  - Carrier: udgilu
- OQ-02 of the spec (whether `needs_input` or `awaiting-human` retires): the spec explicitly holds it open, non-blocking, and out of its own scope, and it needs no answer for any presentation work here.
  - Carrier-Declined: The spec OWNS this question and deliberately holds it open as not-its-to-decide (uonrjg OQ-02: "NOT BLOCKING, AND DELIBERATELY NOT THIS SPEC'S TO DECIDE"), with a stated closing condition (whoever wires `run_gates` into the runners decides). It is an upstream lifecycle-vocabulary question, not an obligation this presentation plan incurs, and the spec's tables need no change either way. Filing a carrier here would assert a work item the spec explicitly declined to create.
- Amending `25kzda` Section 5.6: that obligation is carried by child `7p3tt8`, which owns the spec-amendment work.
  - Carrier: 7p3tt8

## Scope check

- Over-scope: none. The plan does exactly what the spec's Section 12a obligation names.
- Under-scope: none for this item's concern. Note that the OTHER Section 12a obligation (declare the `executed:yaxr4i` edge) is satisfied structurally by this plan's own `- Item-Dependencies:` line and by child `udgilu` carrying the same edge, so no separate item is needed.

## Required tests / validation

No code changes, so no suite run is required for this child's own correctness. Validation is documentary and is verified by reading the spec's appended round. The Set's code children each carry their own suite obligations.

## Spec / documentation sync

This plan's entire deliverable IS a spec amendment, and the spec is declared in `- Scope-Paths:` so both runners announce the declared spec edit before the run and reconcile it at finalize. WHY the amendment is legitimate rather than an unauthorized edit of an approved spec: AGENTS.md states a plan MAY amend a spec and MUST declare it, and this particular amendment is required BY THE SPEC ITSELF (Section 12a obligation 2), which is the strongest form of authority an amendment can carry.

## Open questions

### OQ-01: Does the re-review need a fresh maintainer approval if it amends a criterion?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: CONDITIONAL AND SELF-CLOSING WITHIN THIS PLAN'S OWN EXECUTION. The question only arises if E-03 actually amends a criterion, and E-03 is this plan's own item, so the decision point occurs during execution rather than after it. If a criterion is amended the executing agent surfaces it to the maintainer then, and V-03 already demands the diff or an explicit no-change statement as evidence. There is no residual obligation to hand to a later record.
- Resolution or deferral rationale: NOT BLOCKING, because the spec answers the common case: Section 12a says a re-review "appends a new round and keeps the status", so an ordinary re-read that finds no divergence plainly needs no new approval. The residual question is narrow and only arises if E-03 actually amends a CRITERION (A11/A12/A13) rather than clarifying prose, since a criterion is what a later reviewer holds the implementation to. If that happens, the executing agent should surface the amended criterion to the maintainer rather than deciding unilaterally that an approved spec's acceptance bar may move without sign-off. Recorded rather than guessed because it is a question about approval authority, which AGENTS.md reserves to the human.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the appended `## Workflow history` round from the spec file, showing the date, the reviewing agent, and the verdict. Paste `git log --oneline -1 -- .aw/records/plans/executed/*yaxr4i*` (or equivalent) proving `yaxr4i` was executed BEFORE this round's date, since a round recorded earlier would not discharge the gate.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the per-criterion verdict for A11, A12, A13, and Section 9.3, each with its supporting measurement. For A11 specifically, paste the relevant lines of `docs/cli-output-contract.md` as shipped, proving whether the retracted promise is gone. For the flag surface, paste the command and output enumerating `--color`/`--no-color` presence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Either `git diff` of the spec showing the amended criteria, or an explicit recorded statement in the round that all four re-read items held unchanged. An empty diff with no recorded statement FAILS this item, because it cannot be distinguished from the work not having been done.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved n4xq3l --by-human`), and it additionally MUST NOT execute until `yaxr4i` is `executed`, which its `- Item-Dependencies: executed:yaxr4i` edge enforces at dispatch. The runner re-checks that edge at dispatch time and marks this item `dependency-blocked` rather than failing the run if the edge is unmet.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
