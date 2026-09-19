# IPD: Re-review spec uonrjg against the shipped yaxr4i flag surface before any resolver is built

- Date: 2026-09-19
- Kind: child
- Concern: Spec `uonrjg` Section 12a imposes a HARD, NON-OPTIONAL gate on its own implementation: "RE-REVIEW THIS SPEC AFTER `yaxr4i` EXECUTES, BEFORE THE RESOLVER IS BUILT. This is a requirement, not a suggestion." The reason is mechanical rather than procedural: `yaxr4i` moves the exact surface three of the spec's acceptance criteria are written against. It adds a `--color` flag where only `FORCE_COLOR` existed, adds `--no-color` to 25 of 219 subcommands that do not inherit it, settles the precedence between the two, and rewrites `docs/cli-output-contract.md` to retract a published promise that non-TTY stdout adopts `aw.agent/v1`. A11, A12, and A13 must be re-read against the flags AS SHIPPED, and Section 9.3's "MUST preserve current NO_COLOR/FORCE_COLOR/TERM=dumb/TTY behavior" needs re-pointing at whatever "current" then means.
- Scope: IN: re-read A11/A12/A13 and Section 9.3 of `uonrjg` once `yaxr4i` is `executed`, against the shipped flag surface and the rewritten contract doc, and record the round in the spec's workflow history via `aw specs note`. Amend A11/A12/A13/9.3 text if and only if the shipped surface differs from what the spec anticipates. OUT: building any part of the resolver (that is `udgilu` onward); any change to the spec's palette, glyph table, or mappings, none of which `yaxr4i` touches; invoking `/spec-review` or filing a `.review.md` for this spec (both are wrong for an `approved` spec, for the measured reasons in E-01 and findings F-04/F-05); and any transition of the spec's `- Status:`, which MUST remain `approved`.
- Scope-Paths: .aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
- Item-Dependencies: executed:yaxr4i
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n4xq3l
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Spec: uonrjg
- Blocks-Release: next

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-101..PR-105 all FIXED, none deferred, none open. Readiness go-pending-approval. OQ-01 left open, non-blocking and conditional.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101 (BLOCKER), PR-102 (HIGH), PR-103 (MEDIUM), PR-104 (MEDIUM), PR-105 (LOW) all FIXED, none deferred, none open. Reviewed at HEAD `6ce719d5`; `aw ipd lint --phase author --agent` clean, exit 0. THE CENTRAL DEFECT WAS THE MECHANISM, NOT THE INTENT: E-01 instructed running `/spec-review` on `uonrjg`, but that workflow REFUSES an `approved` spec (its Step 0.1 classifies it NOT REVIEWED), so the Section 12a gate this plan exists to discharge would have silently discharged nothing. Worse, running it anyway would have de-approved a release-gating spec (`approved -> reviewed` is a legal transition) and filed a review record that arms an approval gate with no override. E-01 now performs the re-read directly via `aw specs note`, and three writes are forbidden by name. Also: the waived suite run is restored with a measured baseline (25 test modules read the live tree), and OQ-01's rationale no longer rests on a Section 12a sentence whose premise does not hold at `approved`.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from spec uonrjg Section 12a obligation 2. Carries the spec's `Blocks-Release: next` gate.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Discharge the re-review gate spec `uonrjg` Section 12a places on its own implementation, so the resolver is built against the flag surface and output contract as SHIPPED by `yaxr4i` rather than as anticipated in a spec written before it landed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-read the three criteria against shipped behavior

- [ ] E-01 Perform the Section 12a re-read of `.aw/records/specs/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` at a HEAD where `yaxr4i` is `executed`, and record the round in the spec's `## Workflow history` via `aw specs note`. DO NOT INVOKE `/spec-review`, and do NOT write a `.review.md` record for this spec; do the re-read directly against the criteria named in E-02. The two reasons are mechanical and both were measured at review (see F-04 and F-05).
  - Depends on: none
  - Expected outcome: A new workflow-history round appended by `aw specs note` naming the reviewing agent, the HEAD sha, and the per-criterion verdict. The spec's `- Status:` stays `approved` and is NOT transitioned; no review record is filed, so `uonrjg`'s approval gate stays unarmed.
  - Execution state: pending

  WHY NOT `/spec-review`, stated here because the instruction to avoid a named workflow needs its reason attached. FIRST, that workflow REFUSES an `approved` spec: its Step 0.1 says "A spec at `approved`, `implementing`, `implemented`, `deferred`, `parked`, or `superseded` is NOT REVIEWED with that status as the reason", and it permits a re-review only for a spec "already at `reviewed`... ONLY when explicitly requested". `uonrjg` is `- Status: approved` (verified 2026-09-19), so a conforming `/spec-review` run would classify it NOT REVIEWED and discharge nothing. SECOND, that workflow's own transition step runs `aw specs set reviewed <id6>`, which for an `approved` spec is a legal BACKWARD transition (`approved -> reviewed` is in `SPEC_TRANSITIONS`), so it would silently DE-APPROVE a release-gating spec and force a fresh `--by-human` approval. THIRD, it writes a typed review record, and filing one ARMS a live gate: `aw specs set approved` consults `plan_readiness.approval_refusals` -> `review_findings.subject_gating_blocks` keyed on the spec's `- Id:`, and that refusal has NO override. The re-read this plan owes is a documentary check, so it needs none of that machinery.

- [ ] E-02 Re-read A11, A12, A13, and Section 9.3 against the SHIPPED flag surface, and record for each whether the spec's text still holds. Measure rather than infer: enumerate the `--color`/`--no-color` flag presence across subcommands, and read `docs/cli-output-contract.md` as `yaxr4i` E-05 left it.
  - Depends on: E-01
  - Expected outcome: A per-criterion verdict (holds / needs amendment) recorded in the spec's re-review round, each citing the measurement that supports it. A11 in particular is asserted UNCONDITIONAL by the spec on the strength of the `yaxr4i` OQ-01 ruling; confirm the rewritten contract doc now agrees rather than still carrying the retracted promise.
  - Execution state: pending

- [ ] E-03 Amend A11, A12, A13, or Section 9.3 in the spec if and only if E-02 found a divergence, and state in the round what changed and why. If nothing diverged, record that explicitly rather than silently leaving the section untouched.
  - Depends on: E-02
  - Expected outcome: Either an amended spec whose criteria match shipped behavior, or a recorded finding that no amendment was needed. Both are conforming outcomes; an unrecorded no-op is not.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A spec re-review APPENDS a round and keeps the status; it does not reset to `to-review`. The spec's own Section 12a says so, and `aw specs note` is the tooled path for that append (`--help`: "Append a workflow-history record to a spec WITHOUT changing its status"), which works at ANY status and is therefore the right verb here.
- CORRECTED AT REVIEW: Section 12a's sentence reads "a re-review appends a new round and keeps the status `reviewed`", and that wording assumes a spec sitting at `reviewed`. `uonrjg` is at `approved` (verified 2026-09-19), so the sentence's PREMISE does not hold for this spec even though its CONCLUSION (append a round, do not re-open approval) is what this plan must do. The spec wrote that line on 2026-09-13 in the same round that also approved it, which is how the mismatch arose. Do not read it as authority to run `/spec-review`, which refuses an `approved` spec outright; see E-01.
- Verified 2026-09-19: `approved -> reviewed` IS a legal spec transition (`attention_contract.transition_allowed('approved','reviewed')` returns True), so nothing mechanical would stop a de-approving transition. That is precisely why E-01 forbids it in words: the guardrail here is the instruction, not the transition table.
- `uonrjg` is `- Status: approved` with `- Blocks-Release: next`, so this plan inherits the release gate per the repo's Blocks-Release policy (AGENTS.md: a graduating plan inherits the item's gate).
- `- Readiness:` is deliberately ABSENT from this plan. It is an output of `/plan-review`, and AGENTS.md forbids an author hand-writing another role's attestation field. `aw ipd lint` refuses an unattested value under IPD-M107.
- Verified 2026-09-19: `yaxr4i` is `- Status: approved` and sits in `.aw/records/plans/pending/`, i.e. it is NOT executed yet. This plan's dependency edge is therefore live, not already-satisfied.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | The spec's own Section 12a makes this re-review a precondition on building the resolver, so skipping it would violate the spec being implemented. | `uonrjg` Section 12a, obligation 2: "RE-REVIEW THIS SPEC AFTER `yaxr4i` EXECUTES, BEFORE THE RESOLVER IS BUILT. This is a requirement, not a suggestion." |
| F-02 | High | `yaxr4i` is approved but UNEXECUTED, so the gate cannot be discharged yet and every downstream child in this Set is genuinely blocked behind it. | `aw show yaxr4i` -> `- Status: approved`, file resides in `.aw/records/plans/pending/`, verified 2026-09-19. |
| F-03 | Medium | A11 is the criterion most at risk of being validated against a stale document. The spec warns that `docs/cli-output-contract.md` still carries the unretracted non-TTY promise until `yaxr4i` E-05 rewrites it. CONFIRMED LIVE at review: the promise is intact at `docs/cli-output-contract.md:159-163` ("Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL immediately upon release with no deprecation window"), under a heading that calls it a Hard Cutover. | `uonrjg` A11: "DO NOT RE-DERIVE THIS FROM THE CODE ALONE... An implementer reading that document instead of this line would conclude A11 is conditional. It is not."; `docs/cli-output-contract.md:159-163` read 2026-09-19. |
| F-04 | High | `/spec-review` CANNOT discharge this gate, because it refuses the spec's actual status. Its Step 0.1 classifies a spec at `approved` as NOT REVIEWED with that status as the reason, and admits a re-review only for one "already at `reviewed`". `uonrjg` is `approved`, so a conforming run of that workflow would do nothing and this plan's whole purpose would silently fail. The original E-01 named that workflow, so the defect was in the instruction rather than in the intent. | `.aw/system/workflows/spec-review/spec-review.md:110-114`; `uonrjg` front matter `- Status: approved` (line 4), verified 2026-09-19. |
| F-05 | High | Running that workflow anyway would actively DAMAGE a release-gating spec, in two independent ways. (a) Its transition step runs `aw specs set reviewed <id6>`, and `approved -> reviewed` is a LEGAL transition, so it would de-approve `uonrjg` and force a fresh `--by-human` approval that AGENTS.md reserves to the maintainer. (b) It writes a typed `.review.md`, and filing one arms a live approval gate whose refusal has no override, so any finding left at or above the threshold would then BLOCK re-approval of a spec that gates the next release. | `spec-review.md:259-284` (the `aw specs set reviewed` transition and the "KNOW WHAT YOUR RECORD DOES TO APPROVAL" section); `attention_contract.SPEC_TRANSITIONS['approved']` includes `reviewed`; `review_findings.subject_gating_blocks` is keyed on the artifact's `- Id:` and specs carry one. |

## Proposed changes (ordered, validatable)

1. Perform the Section 12a re-read round once `yaxr4i` is executed, recording it with `aw specs note` and WITHOUT invoking `/spec-review`, transitioning the status, or filing a review record (E-01).
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

- Over-scope: none. The plan does exactly what the spec's Section 12a obligation names. Corrected at review: the original E-01 named `/spec-review`, which would have gone BEYOND this scope destructively (a status transition plus a review record on a release-gating spec), so the over-scope risk was in the mechanism rather than in the intent.
- Under-scope: none for this item's concern, after two review additions. (a) A suite run and `aw check` are now required rather than waived, because 25 test modules read the live repository tree and this child edits a tracked record in it. (b) The three forbidden writes are now named explicitly in the gate, since the original plan relied on a workflow that would have performed two of them. Note that the OTHER Section 12a obligation (declare the `executed:yaxr4i` edge) is NOT this plan's to satisfy, and the earlier wording here claimed otherwise. Section 12a obligation 1 is explicit about whose edge it is: "The plan that lands the resolver MUST carry an `- Item-Dependencies:` edge" (`uonrjg` Section 12a, obligation 1). The resolver is landed by `udgilu`, not by this plan. Verified rather than assumed: `udgilu` carries `- Item-Dependencies: executed:yaxr4i, executed:n4xq3l`, so the obligation IS discharged, but by `udgilu`. This plan's own `- Item-Dependencies: executed:yaxr4i` exists for a different and independent reason, namely that the re-read cannot be performed before the surface it re-reads has shipped. THE CORRECTION MATTERS BEYOND PEDANTRY: the previous claim implied `udgilu`'s edge was redundant with this one, which would license a later tidier to delete it and free the resolver to be built against the pre-`yaxr4i` surface, the single outcome this whole plan exists to prevent.

## Required tests / validation

No code changes, so the SUBSTANCE of this child's validation is documentary and is verified by reading the spec's appended round. But RUN THE SUITE BARE ANYWAY (`python3 -m pytest`) and paste the actual summary line, because "no code changes" does not imply "no test can break": 25 test modules read the LIVE repository tree rather than a fixture (measured by `grep -rlc "parents\[1\]" tests/*.py` on 2026-09-19), and this child edits a tracked record in that tree. The corpus-wide record checks are the specific risk, since an amended criterion changes a `.spec.md` that `aw check`-style tests enumerate.

BASELINE, measured in this lane at HEAD `6ce719d5` on 2026-09-19 so an executor can tell a pre-existing failure from one it caused:

```text
8369 passed, 3 skipped, 2 xfailed in 100.98s (0:01:40)
```

Compare NODE IDS, not totals, since the plan corpus is mutable and the count moves as records land. Also run `aw check specs` (or `aw check`) and confirm the amended spec still conforms, which is the cheap check that actually covers this child's deliverable. Do NOT add `-n0`, a second `-q`, or `-p no:randomly` per AGENTS.md.

## Spec / documentation sync

This plan's entire deliverable is a WRITE TO THE SPEC FILE, and the spec is declared in `- Scope-Paths:` so both runners announce the declared spec edit before the run and reconcile it at finalize. WHY it is legitimate rather than an unauthorized edit of an approved spec: AGENTS.md states a plan MAY amend a spec and MUST declare it, and this particular round is required BY THE SPEC ITSELF (Section 12a obligation 2), which is the strongest form of authority an edit can carry.

PRECISELY WHAT IS AND IS NOT WRITTEN, since "a spec amendment" overstates the guaranteed case. The GUARANTEED write is an appended `## Workflow history` round via `aw specs note`, which changes no status and no requirement. A CONDITIONAL write follows only if E-02 finds a divergence: an amendment to A11, A12, A13, or Section 9.3. NOTHING ELSE is written, and three specific writes are FORBIDDEN: the `- Status:` line (which MUST remain `approved`), a `- Readiness:` field (specs have no such field, and inventing one creates a machine signal no consumer may act on), and a `.review.md` record for this spec (which would arm its approval gate). An executor that finds itself running `aw specs set` on `uonrjg` has left this plan's scope.

## Open questions

### OQ-01: Does the re-review need a fresh maintainer approval if it amends a criterion?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: CONDITIONAL AND SELF-CLOSING WITHIN THIS PLAN'S OWN EXECUTION. The question only arises if E-03 actually amends a criterion, and E-03 is this plan's own item, so the decision point occurs during execution rather than after it. If a criterion is amended the executing agent surfaces it to the maintainer then, and V-03 already demands the diff or an explicit no-change statement as evidence. There is no residual obligation to hand to a later record.
- Resolution or deferral rationale: NOT BLOCKING, and SHARPENED AT REVIEW (2026-09-19) because the original rationale rested on a sentence whose premise does not hold for this spec. Section 12a's "appends a new round and keeps the status `reviewed`" was written assuming a spec at `reviewed`; `uonrjg` is at `approved`, so that sentence cannot be cited as settling the status question here. What DOES settle the common case is the verb: `aw specs note` appends history "WITHOUT changing its status" (its own `--help`), so a re-read that finds no divergence provably needs no approval because it changes no requirement and no status. The residual question is narrower still and arises only if E-03 amends a CRITERION (A11/A12/A13) rather than clarifying prose, since a criterion is what a later reviewer holds the implementation to, AND because `uonrjg` carries `- Blocks-Release: next`, so its acceptance bar gates a release. If that happens, the executing agent MUST surface the amended criterion to the maintainer rather than deciding unilaterally that an approved, release-gating spec's acceptance bar may move without sign-off. It must NOT reach for `aw specs set` in either direction: de-approving to `reviewed` and re-approving are both the maintainer's call, and `--by-human` is an attestation an agent may never self-write. Left OPEN rather than resolved because it is a question about approval authority, which AGENTS.md reserves to the human, and this run had no interactive channel.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the appended `## Workflow history` round from the spec file, showing the date, the reviewing agent, and the verdict. Prove `yaxr4i` was executed BEFORE this round's date, since a round recorded earlier would not discharge the gate. USE A COMMAND THAT FAILS LOUDLY WHEN THE ANSWER IS NO, for example `ls .aw/records/plans/executed/ | grep yaxr4i` (nonzero exit when absent) followed by `git log --oneline -1 -- '.aw/records/plans/executed/'` filtered to that filename. DO NOT paste a bare `git log --oneline -1 -- .aw/records/plans/executed/*yaxr4i*`: the glob is expanded by the SHELL, not by git, so while `yaxr4i` is still in `pending/` it matches nothing, git is handed a literal pathspec that matches nothing, and the command prints NOTHING and exits 0. Measured 2026-09-19 at a HEAD where `yaxr4i` is in `pending/`: both the quoted and unquoted forms returned empty with exit 0. Empty-and-successful is indistinguishable from "I checked and it was fine", so that command can be pasted as satisfied evidence of the very thing it failed to establish. ALSO PASTE THREE NEGATIVE PROOFS, each of which fails this item if absent: (a) `grep -n "^- Status:" <uonrjg spec>` still showing `approved`, proving no de-approving transition occurred; (b) `ls .aw/records/reviews/ | grep uonrjg` returning NOTHING, proving no review record was filed and the approval gate was not armed; and (c) `git diff --stat` for the spec showing the ONLY change is the appended history line (plus any E-03 amendment), proving the append went through `aw specs note` rather than a hand-edit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the per-criterion verdict for A11, A12, A13, and Section 9.3, each with its supporting measurement. For A11 specifically, paste the relevant lines of `docs/cli-output-contract.md` as shipped, proving whether the retracted promise is gone. For the flag surface, paste the command and output enumerating `--color`/`--no-color` presence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Either `git diff` of the spec showing the amended criteria, or an explicit recorded statement in the round that all four re-read items held unchanged. An empty diff with no recorded statement FAILS this item, because it cannot be distinguished from the work not having been done. Paste the BARE `python3 -m pytest` summary line and compare it against the baseline node ids recorded in Required tests (a differing TOTAL is expected as records land; a NEW failing node id is not). Paste `aw check specs` (or `aw check`) output showing the amended spec conforms.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved n4xq3l --by-human`), and it additionally MUST NOT execute until `yaxr4i` is `executed`, which its `- Item-Dependencies: executed:yaxr4i` edge enforces at dispatch. The runner re-checks that edge at dispatch time and marks this item `dependency-blocked` rather than failing the run if the edge is unmet.

OPEN QUESTIONS: OQ-01 is non-blocking and CONDITIONAL. It fires only if E-03 amends a criterion (A11/A12/A13), and if it fires the executor surfaces the amended criterion to the maintainer rather than deciding it. No `aw specs set` on `uonrjg` in either direction, and never a self-written `--by-human`.

SCOPE FENCE: the only file this plan may write is the one declared in `- Scope-Paths:`, the `uonrjg` spec. An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Within that file, three writes are FORBIDDEN outright rather than merely out of scope, because each forges a signal or moves a release gate: the `- Status:` line (it MUST stay `approved`), a `- Readiness:` field (a spec has none, and inventing one creates a machine signal no consumer may act on), and a `.review.md` record for this spec (it arms an approval gate whose refusal has no override). DO STOP AND REPORT for one genuinely unsafe condition: if `yaxr4i` landed but `docs/cli-output-contract.md` still carries the retracted non-TTY promise at `:159-163`, then A11 cannot be validated against a settled document and the premise of E-02 is absent; report that rather than re-deriving A11 from the code, which the spec explicitly forbids.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, an `aw check` result, or a flag-surface enumeration you did not run.

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
