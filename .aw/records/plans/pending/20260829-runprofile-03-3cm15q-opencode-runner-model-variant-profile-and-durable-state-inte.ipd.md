# IPD: OpenCode runner model variant profile and durable-state integration

- Date: 2026-08-29
- Kind: child
- Concern: aw oc run currently accepts --model but has no --variant path and stores only the model in durable state. A superficial alias implementation could change only the initial execution turn, omit verifier turns, re-resolve a modified alias during resume, let an unknown profile create partial run state, confuse a profile name with an IPD selector, or report a launch identity different from the actual argv.
- Scope: Extend the OpenCode IPD driver with direct --model/--variant support and the collision-safe grammar run as PROFILE SELECTOR. Resolve named/default OpenCode profiles before run creation, apply explicit-field overrides, snapshot complete provenance in state.json, use that snapshot for every execution and verification turn and every resume, and expose it in status/report/prepare-only output.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py
- Item-Dependencies: executed:p0l1to
- Status: to-review
- Set: runprofile
- Order: 3
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: 3cm15q

## Workflow history

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

- [ ] E-04 Update the OpenCode argv builder so every normal execution, recovery execution, review, and independent fresh-session verifier appends --model and --variant from the frozen state when nonempty, plus the frozen agent, using one argv list and shell=False. Resume MUST NOT reload runner-profiles.json; editing, deleting, or repointing gem after run creation cannot alter that run. Directly started runs without a profile remain behavior-equivalent except for explicitly requested --variant.
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

No open questions.

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
