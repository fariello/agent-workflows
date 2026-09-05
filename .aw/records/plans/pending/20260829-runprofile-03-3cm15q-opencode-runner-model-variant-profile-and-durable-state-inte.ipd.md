# IPD: OpenCode runner model variant profile and durable-state integration

- Date: 2026-08-29
- Kind: child
- Concern: aw oc run currently accepts --model but has no --variant path and stores only the model in durable state. A superficial alias implementation could change only the initial execution turn, omit verifier turns, re-resolve a modified alias during resume, let an unknown profile create partial run state, confuse a profile name with an IPD selector, or report a launch identity different from the actual argv.
- Scope: Extend the OpenCode IPD driver with direct --model/--variant support and the collision-safe grammar run as PROFILE SELECTOR. Resolve named/default OpenCode profiles before run creation, apply explicit-field overrides, snapshot complete provenance in state.json, use that snapshot for every execution and verification turn and every resume, and expose it in status/report/prepare-only output.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py
- Item-Dependencies: executed:p0l1to
- Status: approved
- Readiness: go-pending-approval
- Set: runprofile
- Order: 3
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: 3cm15q
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-05 approved (opencode its_direct/pt3-claude-opus-5-1m-us): E-04 AMENDED IN PLACE, no scope or Order change, recorded here because this plan is `approved` and carries human sign-off that a silent edit would erase. MAINTAINER DIRECTION 2026-09-05: verification should be routable to a DIFFERENT MODEL than execution (the stated need is a cheaper model executing with a stronger model verifying, or a strong model executing and verification skipped because it was measured to need no material corrections). E-04 as written required every turn INCLUDING the verifier to append the same frozen `--model`/`--variant`, and the findings table lists 'Profile only affects first turn' as a defect to prevent, so read literally this item FORBADE the maintainer's requirement. The amendment separates the two ideas that were conflated: the invariant worth keeping is ONE FROZEN LAUNCH PER RUN with no dynamic re-resolution and no re-reading of `runner-profiles.json` on resume; the incidental consequence was ONE MODEL FOR EVERY TURN. New Order 6 (`kgpptv`, `Item-Dependencies: executed:3cm15q`) adds an optional `verify_with` profile reference giving the independent fresh-session verifier its own SEPARATELY FROZEN launch, which preserves the invariant. NOTHING IN THIS PLAN'S EXECUTABLE SCOPE CHANGES: implement E-04 exactly as written, since without that field the verifier correctly inherits the executor's launch. Order 6 also carries the measured note that per-role model routing greps to ZERO today and that both turns share one launcher (`run_opencode`, called at the execute and verifier sites), so the eventual change is at a call site rather than a new subprocess path.

- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): READINESS BOOKKEEPING, no scope or content change. Added the `- Readiness:` front-matter field, which postdates this plan (the field is a later addition to the review contract, `plan-review.md:377-398`, and automation FAILS CLOSED when it is absent, so a clean plan without it is simply never picked up). Value `go-pending-approval`.
  AND SUPERSEDED THE STALE `REVIEWED - OPEN QUESTIONS` VERDICT, which is the substantive half. That verdict was correct when written on 2026-09-01: the Set carried ONE blocking question, OQ-01, asking whether approved `runnamecollapse-01` (`0soncw`) had to land first, and the maintainer answered ORDER: `0soncw` FIRST, which made the Set depend on `0soncw` reaching `executed` AND inherited `0soncw`'s own unresolved blocking question. BOTH CONDITIONS ARE NOW DISCHARGED, verified rather than assumed: `0soncw` is in `.aw/records/plans/executed/` with `Status: executed`, and its three open questions (OQ-01 permanence, OQ-02 noun placement, OQ-03 subcommand-versus-viewer disambiguation, the one that gated this Set) are all `Status: resolved`. This plan's own OQ-01 is `Status: resolved`, and `aw ipd lint` reports no unresolved blocking question. So the verdict is stated here as APPROVE WITH REVISIONS APPLIED, superseding the neutral one, on the maintainer's 2026-09-04 reading that the outstanding record was bookkeeping rather than an unanswered question. NO re-review of the plan's technical content was performed in this pass and none is claimed: round 1's findings and their fixes stand as recorded.

- 2026-09-01 reviewed (aw set): plan-review round 1 (whole Set): REVIEWED - OPEN QUESTIONS. Blocking OQ on the aw run noun retirement by approved 0soncw; f2mrsw additionally APPROVE WITH REVISIONS APPLIED for the two maintainer-directed validate findings. See .aw/records/reviews/.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1 (whole `runprofile` Set, 6 plans, reviewed together at HEAD 6a29f9c0): REVIEWED - OPEN QUESTIONS. BLOCKER PR-001, escalated ONCE as blocking OQ-01 on the orchestrator 3m0urk: this Set builds its entire grammar on the `aw run` noun (measured: `aw run as` x16, `aw run ipd` x12) that APPROVED 0soncw is RETIRING behind a nonzero-exit deprecation stub, and NO plan in the Set mentions 0soncw even once. They are COMPLEMENTARY not contradictory (0soncw frees the name "for a future driver verb", which is this Set), so the fix is ORDER: 0soncw first, then this Set. Reversed, `aw run as gem` would start exiting nonzero. Not agent-resolvable: a cross-Set order decision, and 0soncw itself still carries an unresolved blocking OQ-03. PR-002 MEDIUM, fixed: the Set carries ZERO file:line citations across all six plans (versus 9/4/5 in the comparable 6lu3rq/m73aet/wlxkoz); spot-checked claims were TRUE so this is evidence discipline, and each plan now requires measuring and citing every "already" claim. Verified its premise BY EXECUTION: `aw oc run --help` genuinely has no --variant. PR-003 MEDIUM, fixed: this is the most contended child, editing oc_runipd.py which nine approved plans also claim, five of them the unmerged wtiso stack (26 commits) that 6knsrx lands into this same file; now requires re-measuring immediately before editing and stopping if 6knsrx has begun landing. Review artifact: .aw/records/reviews/20260831-runprofile-*-3cm15q-*.review.md

- 2026-08-30 to-review (codex gpt-5.6): authored to bind structured profiles and OpenCode variants to durable runner execution.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Make these commands deterministic and equivalent at launch:

    aw oc run as gem SELECTOR
    aw oc run SELECTOR --model google/gemini-3.7-flash --variant high

When an OpenCode default profile exists, unqualified aw oc run uses it. Every child turn, verifier turn, report, and resume must use and describe the same frozen resolution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: grammar and resolution before side effects

- [ ] E-01 Add --variant to the OpenCode start parser beside --model and preserve both through implicit-start parsing. Add one normalization function accepting as PROFILE only in the fixed clause immediately after run/implicit start or explicit start; reject missing profile and repeated/misplaced as clauses with exact usage. The token after as is always a profile and subsequent tokens are selectors/options. A profile-like token without as remains a selector. Preserve resume/status/report subcommands and provide an explicit documented escape for the rare literal selector as.
  - Depends on: none
  - Expected outcome: the word-oriented grammar is deterministic, direct flags remain first-class, and no configured alias can become or shadow a real runner command.
  - Execution state: pending

- [ ] E-02 Before creating a run directory or writing state, load and validate profile configuration and resolve the OpenCode launch using Order-01 precedence. aw oc run as NAME requires an existing oc profile; aw oc run without as uses the OpenCode default profile if configured and otherwise preserves current host-default behavior. Explicit --model, --variant, and --agent override only their corresponding profile fields. Unknown/wrong-runner/malformed profile configuration exits nonzero with no run ID, run directory, events, or partial state.
  - Depends on: E-01
  - Expected outcome: launch identity is decided once before side effects, with exact diagnostics and no unintended fallback.
  - Execution state: pending

### Task group 2: durable identity and identical turn argv

- [ ] E-03 Extend state.json options with resolved variant and a launch_profile object containing requested name or null, applied default or null, runner, source path, configuration digest, resolved model/variant/agent, and per-field provenance. Preserve the existing top-level options.model/options.agent compatibility inside the unreleased runner while making the resolved object authoritative. Reports, human status, JSON status, prepare-only output, and driver actor identity must show the resolved profile/model/variant without exposing credentials.
  - Depends on: E-01, E-02
  - Expected outcome: every durable artifact states exactly which runner profile and fields created the run, and operators can distinguish explicit, named, default, and host-default choices.
  - Execution state: pending

- [ ] E-04 Update the OpenCode argv builder so every normal execution, recovery execution, review, and independent fresh-session verifier appends --model and --variant from the frozen state when nonempty, plus the frozen agent, using one argv list and shell=False.
  AMENDED 2026-09-05 (maintainer-directed, see this plan's history): the invariant this item establishes is ONE FROZEN LAUNCH IDENTITY PER RUN, NOT one model for every turn. Order 6 (`kgpptv`) adds an optional `verify_with` profile reference that gives the INDEPENDENT FRESH-SESSION VERIFIER its own SEPARATELY FROZEN launch, so a run can execute with one model and verify with another. Implement this item as written, because absent that field the verifier legitimately inherits the executor's launch and the 'profile only affects first turn' defect in the findings table below remains a real defect. Do NOT read the words 'every ... verifier' here as a prohibition on the Order 6 field: what must never happen is a turn resolving its launch DYNAMICALLY or re-reading `runner-profiles.json` on resume, and a second frozen resolution preserves that rule rather than breaking it. Resume MUST NOT reload runner-profiles.json; editing, deleting, or repointing gem after run creation cannot alter that run. Directly started runs without a profile remain behavior-equivalent except for explicitly requested --variant.
  - Depends on: E-03
  - Expected outcome: all turns in one durable run have a stable model/variant identity, including verifier and resumed turns.
  - Execution state: pending

- [ ] E-05 Add focused parser, initialization, argv, state, report, and resume tests. Cover implicit and explicit start; as grammar errors; command-like profile names; a selector whose text equals a profile; direct fields; profile defaults; partial explicit overrides; no default; unknown/wrong-host/malformed profiles; no-side-effect failure; exact execution and verifier argv; provider-default omission of --variant; changed/deleted profile before resume; status/report provenance; and controlled negative tests that deliberately omit verifier --variant or re-resolve on resume and therefore fail.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the runner suite detects cosmetic-only integration, turn asymmetry, alias/selector confusion, partial state, provenance mismatch, and mutable-resume identity.
  - Execution state: pending

## Project conventions discovered (Step 0)

- aw oc run captures argparse.REMAINDER in cli.py and forwards it unchanged to oc_runipd.main(); the runner's parser and implicit-start shim are the authoritative grammar.
- initialize_run() writes selectors, queue, options, driver digest, and other durable state only after selector expansion. Profile resolution must occur before its first write.
- run_opencode() constructs one argv used by primary and verifier call sites. Adding variant there from frozen options reaches all turn types, but tests must prove every caller.
- Isolated and verifier turns force fresh sessions; a fresh session must not imply re-resolving user configuration.
- The pending rununify Set explicitly forbids behavior changes and requires a fresh inventory at execution. This behavior-changing child lands first; rununify must inventory and preserve it afterward instead of this child targeting an unwritten shared module.

## Findings

| Failure mode | Why a weak implementation may miss it | Required protection |
|---|---|---|
| Variant only parsed | Parser test passes while argv omits it. | Exact argv assertions for all turn types. |
| Profile only affects first turn | Happy-path execution works; verifier differs. | Execution/verifier/recovery matrix. |
| Alias edited before resume | Resume silently changes models. | Frozen-state test with changed/deleted config. |
| Unknown alias after run creation | Failed command leaves misleading durable state. | Assert no run directory/event/state exists. |
| Alias named status | Dynamic parser shadows status. | Fixed as grammar and command-like-name tests. |
| Direct override replaces whole profile | --variant override accidentally drops model. | Per-field precedence matrix. |
| Sequencing against an approved plan | FOUND AT REVIEW (PR-001, BLOCKER): APPROVED `0soncw` is RETIRING the `aw run` noun this plan builds on (its E-05 leaves a nonzero-exit deprecation stub), and no plan in this Set mentions it. They are complementary, not contradictory: `0soncw` frees the name "for a future driver verb", which is this Set. Escalated as blocking OQ-01 on the orchestrator `3m0urk`; recommended order is `0soncw` FIRST, then this Set. Do NOT execute this plan until that order is settled. | Settle orchestrator OQ-01 before executing. |
| Unverifiable "already" claims | FOUND AT REVIEW (PR-002): this plan carries ZERO `file:line` citations, as does every member of this Set (measured: 0 across all six, versus 9/4/5 in the comparable `6lu3rq`/`m73aet`/`wlxkoz` plans). The claims spot-checked at review were TRUE, so this is evidence discipline rather than incorrectness, but an executor cannot cheaply re-verify a premise. MEASURE and cite `file:line` for every "already" claim before relying on it; HEAD moves hourly here. | Cite `file:line` for each, measured at the current HEAD. |
| Editing the most contended file in the repo | FOUND AT REVIEW (PR-003): `oc_runipd.py` is in the Scope-Paths of NINE approved plans (`1o4eif`, `2c122z`, `58ha43`, `6knsrx`, `7p9n2v`, `97df1z`, `qcqhj7`, `rchpms`, `y0gg8o`), five being the unmerged `wtiso` lane stack (26 commits) that `6knsrx` exists to land into this same file. | Re-measure this file against the `wtiso` stack immediately before editing; STOP and report if `6knsrx` has begun landing. |

## Proposed changes (ordered, validatable)

1. Add direct variant and fixed as grammar.
2. Resolve profiles/defaults before durable side effects.
3. Snapshot complete identity and provenance.
4. Use frozen state in every turn/resume/report.
5. Add adversarial tests that fail on shallow integration.

## Deferred / out of scope (with reason)

- Generic aw run dispatch is Order 04.
- Profile authoring/model selection is Order 02.
- Agy parity is deferred until its typed runner capabilities are designed; this child must not copy OpenCode variant semantics into Agy.
- Live model calls are optional smoke validation only; deterministic argv/state tests are authoritative.
- Runner deduplication stays in rununify. This child changes behavior and must remain reviewable independently.

## Scope check

- Over-scope: no main CLI parser changes, profile storage/wizard edits, setup integration, Agy changes, OpenCode config edits, or shared-runner refactor.
- Under-scope: direct arguments, word grammar, defaults, precedence, durable provenance, all turn types, resume stability, status/report visibility, and failures-before-side-effects are included.

## Required tests / validation

- python3 -m pytest -p no:randomly tests/test_oc_runipd.py tests/test_oc_runipd_cli.py -q
- Exact argv snapshots for primary, review, recovery, and verifier turns.
- Byte/path assertions for failure before run-state creation.
- Resume test that mutates runner-profiles.json between start and resume.
- Existing OpenCode runner regression cases for implicit start, sessions, worktrees, and verification.

## Spec / documentation sync

- Runner --help and epilog show --model, --variant, run as PROFILE, default behavior, and the literal-as selector escape.
- Broader user documentation is Order 05.

## Open questions

### OQ-01: Must APPROVED `runnamecollapse-01` (`0soncw`) land BEFORE this plan?

- Blocking: yes
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: MAINTAINER DECIDED 2026-08-31: ORDER IS `0soncw` FIRST, THEN THIS SET. The rename vacates the `aw run` noun (leaving its deprecation stub), and this Set then claims the vacated name for real dispatch. This is the order both plans were designed for and the only one in which nothing breaks. CONSEQUENCE, stated plainly: this Set now DEPENDS on `0soncw` reaching `executed`, and `0soncw` itself carries an unresolved blocking question (how `aw runs` distinguishes a subcommand from a viewer target), so that question gates this Set too. Do NOT execute any member of this Set until `0soncw` has landed. ORIGINAL FINDING AS RAISED: RAISED AT REVIEW as a BLOCKER, not agent-resolvable. This plan builds on the `aw run` noun that APPROVED `0soncw` is RETIRING behind a nonzero-exit deprecation stub, and no plan in this Set mentions `0soncw`. The two are COMPLEMENTARY (`0soncw` frees the name "for a future driver verb", which is this Set), so the fix is ORDER, not redesign: recommended `0soncw` FIRST, then this Set. Reversed, `aw run as <profile>` would begin exiting nonzero. A human must answer because it is a cross-Set execution-order decision AND `0soncw` carries its own unresolved blocking OQ-03. THE SET-LEVEL QUESTION IS OQ-01 ON THE ORCHESTRATOR `3m0urk`; this copy exists because the review-finding escalation gate requires the plan carrying the open finding to name it, and answering the orchestrator's OQ-01 answers this one too. Do not answer them differently.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste parser-test output and parsed namespaces for implicit run as gem SELECTOR, explicit start as gem SELECTOR, direct --model/--variant, command-like profile names, profile-like tokens without as remaining selectors, missing/repeated/misplaced as failures, unchanged status/report/resume routing, and the literal-as selector escape.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste initialization tests for named, per-runner-default, no-default, partial explicit overrides, wrong-runner, unknown, and malformed configuration. For every failure, paste assertions showing no run ID/directory/state/events were created and no OpenCode process was invoked.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste prepare-only/status/report/JSON assertions and one state.json excerpt containing requested/applied profile, config source/digest, resolved runner/model/variant/agent, and per-field provenance. Show driver actor includes resolved model/variant and no credentials.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste exact argv assertions for review, primary execution, recovery, and independent verifier turns with model/variant/agent; provider-default omission of --variant; shell=False; and resume after editing/deleting the source profile. Include a controlled failing test or mutation demonstrating verifier omission/re-resolution is detected.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste the complete focused OpenCode runner/CLI suite command, exit code, and summary with named parser, side-effect, argv, state, report, verifier, and resume cases. Paste existing session/worktree/lifecycle regression summaries to prove the feature did not bypass them.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Orders 01 and 02 must be executed. Use their resolver; do not fork profile parsing/storage inside oc_runipd.py.
3. This behavior-changing child executes before rununify extraction. If rununify has already moved these symbols, STOP and re-scope/re-review against the actual shared boundary.
4. Touch only Scope-Paths. Preserve all existing lifecycle, isolation, session, output, and verification semantics.
5. Run every named focused test and paste ACTUAL output with exit codes. Exact argv/state evidence is mandatory; a parser-only pass is insufficient.
6. Commit only this plan's files, path-scoped; inspect git diff --cached --name-only; never use git add -A, bare git add, git commit -a, --no-verify, or push.
7. After every E/V item passes, run aw ipd lint --phase pre-transition, then aw ipd finalize PLAN --actor AGENT/MODEL --message SUMMARY --apply. Lifecycle transition is not an E-item.
