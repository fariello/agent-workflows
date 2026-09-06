# IPD: OpenCode runner model variant profile and durable-state integration

- Date: 2026-08-29
- Kind: child
- Concern: aw oc run currently accepts --model but has no --variant path and stores only the model in durable state. A superficial alias implementation could change only the initial execution turn, omit verifier turns, re-resolve a modified alias during resume, let an unknown profile create partial run state, confuse a profile name with an IPD selector, or report a launch identity different from the actual argv.
- Scope: Extend the OpenCode IPD driver with direct --model/--variant support and the collision-safe grammar run as PROFILE SELECTOR. Resolve named/default OpenCode profiles before run creation, apply explicit-field overrides, snapshot complete provenance in state.json, use that snapshot for every execution and verification turn and every resume, and expose it in status/report/prepare-only output.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py
- Item-Dependencies: executed:p0l1to
- Status: executed
- Readiness: go-pending-approval
- Set: runprofile
- Order: 3
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: 3cm15q

## Workflow history
- 2026-09-06 executed (aw oc run): aw oc run self-finalize: 3cm15q verified (set runprofile, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_oc_runipd_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-06 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-05 performed, V-01..V-05 verified with pasted evidence. Implemented the `as PROFILE` grammar, pre-side-effect resolution through the Order-01 resolver, the `options.launch_profile` provenance snapshot, and the frozen-identity guarantee; +366 lines in `agent_workflows/oc_runipd.py`, +675 in `tests/test_oc_runipd.py` (26 new tests). Named focused suite: 155 passed, exit 0. Whole suite: 18 failed / 5268 passed, and the failing set is BYTE-IDENTICAL to the pre-change baseline at this commit (zero regressions; the 18 are pre-existing `test_run_viewer`/`test_next_ordering`/one stop-trigger timing case). GATES RE-VERIFIED BEFORE EDITING, per execution contract items 2-3 and finding PR-003: prerequisites `f2mrsw`, `p0l1to` and cross-Set `0soncw` are all in `executed/`; `6knsrx` is `superseded` so the `wtiso` stack is NOT landing into this file; and `rununify-02` (`818uru`) had already extracted 34 shared symbols but LEFT `initialize_run`/`run_opencode`/`build_parser` local to `oc_runipd.py` (verified absent from `runner_shared.py`), so the plan's declared boundary still held and no re-scope was needed. THREE MATERIAL FINDINGS, all recorded rather than smoothed over: (1) the plan's premise had gone stale, `--variant` having landed 2026-09-01 via plan `429f30` AFTER this plan's review measured its absence, so that half of E-01/E-04 was preserved rather than reimplemented (DECISION 18-3cm15q-D1, new findings-table row); (2) hoisting the shim's `subcommands` set into a module constant broke a STRUCTURAL guard in `test_runner_stop_triggers` that regexes the source, so the inline literal was restored rather than the test weakened; (3) adding the launch line inside `print_status` broke `test_runner_shared`'s cross-host parity guard, so it moved to the call sites. Decisions register: `.aw/state/lane-submissions/run-20260905T211011Z-3780617/18-3cm15q/attempt-1/decisions-and-questions.md` (D1-D3, no deferred questions).
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

- [x] E-01 Add --variant to the OpenCode start parser beside --model and preserve both through implicit-start parsing. Add one normalization function accepting as PROFILE only in the fixed clause immediately after run/implicit start or explicit start; reject missing profile and repeated/misplaced as clauses with exact usage. The token after as is always a profile and subsequent tokens are selectors/options. A profile-like token without as remains a selector. Preserve resume/status/report subcommands and provide an explicit documented escape for the rare literal selector as.
  - Depends on: none
  - Expected outcome: the word-oriented grammar is deterministic, direct flags remain first-class, and no configured alias can become or shadow a real runner command.
  - Execution state: performed
  - Evidence: `--variant` was ALREADY PRESENT and is PRESERVED, not rewritten: it landed 2026-09-01 via a different plan (`git log -S'"--variant"'` -> commit `8ced15ce` "plan 429f30"), i.e. AFTER this plan's 2026-08-31 review measured its absence by execution. Cited at `oc_runipd.py:7411-7423` (start `--model`/`--variant`/`--agent`, help text extended to state the per-field override) and `:7553-7555` (resume). See DECISION 18-3cm15q-D1. NEW in this pass: `extract_profile_clause` (`oc_runipd.py:7674-7758`), a POSITIONAL grammar rather than a scan for the word `as`, so the command position is decided BEFORE any configuration is read and no configured name can shadow a command; `ProfileClauseError` (`:7665`, a `DriverError` subclass) refused at `:7777-7779` with stderr + exit 2 so a malformed invocation creates nothing; the clause is stripped ahead of the implicit-start shim at `:7770-7779` and bound to `args.profile` at `:7795-7799`. The literal-`as` escape is the conventional `--` end-of-options marker (DECISION 18-3cm15q-D2), which also terminates the clause scan.

- [x] E-02 Before creating a run directory or writing state, load and validate profile configuration and resolve the OpenCode launch using Order-01 precedence. aw oc run as NAME requires an existing oc profile; aw oc run without as uses the OpenCode default profile if configured and otherwise preserves current host-default behavior. Explicit --model, --variant, and --agent override only their corresponding profile fields. Unknown/wrong-runner/malformed profile configuration exits nonzero with no run ID, run directory, events, or partial state.
  - Depends on: E-01
  - Expected outcome: launch identity is decided once before side effects, with exact diagnostics and no unintended fallback.
  - Execution state: performed
  - Evidence: `resolve_launch_profile` (`oc_runipd.py:2619-2654`) DELEGATES the entire precedence decision to the Order-01 resolver `runner_profiles.resolve` (executed `f2mrsw`, `runner_profiles.py:902`), forking nothing, as execution contract item 2 requires; `runner_profiles` is imported as a MODULE at `oc_runipd.py:47-53` (measured before this pass: `grep -c runner_profiles agent_workflows/oc_runipd.py` -> 0, so this is the first consumer). It is called as the FIRST statement of `initialize_run` (`:2686-2691`), before even the repo check and well before the first durable write (the run-dir mkdir at `:2843`), which is what makes a refusal leave nothing behind. `runner="oc"` not `generic=True`, so the runner is never re-guessed from `default_runner` (that is Order 04). Failures are re-raised as `DriverError` at `:2651-2654`, preserving the resolver's exact diagnostic. An ABSENT store is a typed no-op (`present=False`), so a machine with no config is byte-identical to before; MALFORMED still fails closed (DECISION 18-3cm15q-D3).

### Task group 2: durable identity and identical turn argv

- [x] E-03 Extend state.json options with resolved variant and a launch_profile object containing requested name or null, applied default or null, runner, source path, configuration digest, resolved model/variant/agent, and per-field provenance. Preserve the existing top-level options.model/options.agent compatibility inside the unreleased runner while making the resolved object authoritative. Reports, human status, JSON status, prepare-only output, and driver actor identity must show the resolved profile/model/variant without exposing credentials.
  - Depends on: E-01, E-02
  - Expected outcome: every durable artifact states exactly which runner profile and fields created the run, and operators can distinguish explicit, named, default, and host-default choices.
  - Execution state: performed
  - Evidence: `launch_profile_record` (`oc_runipd.py:2657-2682`) builds the provenance object and it is frozen into `state["options"]["launch_profile"]` at `:2963`, carrying requested/applied profile, runner, config source, `config_present`, `config_digest`, resolved model/variant/agent, and PER-FIELD provenance from the resolver's closed vocabulary (`explicit`/`profile`/`default-profile`/`host-default`, `runner_profiles.py:370-378`). Compatibility PRESERVED: the existing `options.model`/`variant`/`agent` keys keep their names and now hold the RESOLVED values (`:2957-2959`), so `run_opencode` and every other reader is untouched. Surfaces: `render_launch_identity` (`:3038-3079`) is the ONE renderer, consumed by the report (`- Launch:` line, `:3101`) and by `print_launch_identity` (`:7264-7284`) which is called from `--prepare-only` (`:7842`) and human `status` (`:7859`). `--json` status needed no change (it dumps `state.json` verbatim). `driver_actor` (`:799-819`) now appends `variant=` and `profile=` beside `model=`, still parenthesis-free for the attribution lint and still byte-identical for a model-only run. NOTE the deliberate placement: the launch line is NOT inside `print_status`, because `test_runner_shared.py::PrintStatusRenderingTests` asserts each host's `print_status` renders byte-identically to the shared definition (measured: putting it there fails with "oc_runipd.print_status diverged from the shared definition"), so it is emitted by the call sites instead.

- [x] E-04 Update the OpenCode argv builder so every normal execution, recovery execution, review, and independent fresh-session verifier appends --model and --variant from the frozen state when nonempty, plus the frozen agent, using one argv list and shell=False.
  AMENDED 2026-09-05 (maintainer-directed, see this plan's history): the invariant this item establishes is ONE FROZEN LAUNCH IDENTITY PER RUN, NOT one model for every turn. Order 6 (`kgpptv`) adds an optional `verify_with` profile reference that gives the INDEPENDENT FRESH-SESSION VERIFIER its own SEPARATELY FROZEN launch, so a run can execute with one model and verify with another. Implement this item as written, because absent that field the verifier legitimately inherits the executor's launch and the 'profile only affects first turn' defect in the findings table below remains a real defect. Do NOT read the words 'every ... verifier' here as a prohibition on the Order 6 field: what must never happen is a turn resolving its launch DYNAMICALLY or re-reading `runner-profiles.json` on resume, and a second frozen resolution preserves that rule rather than breaking it. Resume MUST NOT reload runner-profiles.json; editing, deleting, or repointing gem after run creation cannot alter that run. Directly started runs without a profile remain behavior-equivalent except for explicitly requested --variant.
  - Depends on: E-03
  - Expected outcome: all turns in one durable run have a stable model/variant identity, including verifier and resumed turns.
  - Execution state: performed
  - Evidence: implemented EXACTLY AS WRITTEN per the 2026-09-05 amendment. Structurally satisfied by ONE argv builder with TWO call sites: `run_opencode` appends `--model`/`--variant`/`--agent` from frozen `state["options"]` at `oc_runipd.py:5222-5227`, and is called at `:5998` (normal + recovery execution, and review, which differ only by `log_suffix`/`label_suffix`) and `:6243` (the independent fresh-session verifier). Since both read the same frozen options, no turn can diverge; `shell=False` confirmed (no `shell=True` anywhere in the launch path, and the test asserts it on the Popen kwargs). VERIFIED BY EXECUTION for all four turn kinds, with the pasted argv under V-04. RESUME DOES NOT RELOAD: nothing on the resume path calls `runner_profiles.load()`; the shipped explicit `--variant` override is preserved deliberately (`:7897-7907`, plan `429f30`'s behavior) and the frozen `launch_profile` snapshot is left untouched so an override is visible as a divergence. A belt-and-braces guard refuses a profile named on any non-`start` command with exit 2 (`:7801-7815`), so a later shim change cannot create the silent misfire. Proven live: repointing `gem` at `EVIL/repointed-model` AND then deleting the store entirely both left the run's identity unchanged (V-04).

- [x] E-05 Add focused parser, initialization, argv, state, report, and resume tests. Cover implicit and explicit start; as grammar errors; command-like profile names; a selector whose text equals a profile; direct fields; profile defaults; partial explicit overrides; no default; unknown/wrong-host/malformed profiles; no-side-effect failure; exact execution and verifier argv; provider-default omission of --variant; changed/deleted profile before resume; status/report provenance; and controlled negative tests that deliberately omit verifier --variant or re-resolve on resume and therefore fail.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the runner suite detects cosmetic-only integration, turn asymmetry, alias/selector confusion, partial state, provenance mismatch, and mutable-resume identity.
  - Execution state: performed
  - Evidence: 26 new tests in four classes appended to `tests/test_oc_runipd.py` (+675 lines): `LaunchProfileGrammarTests` (9), `LaunchProfileResolutionTests` (6), `LaunchProfileDurableStateTests` (4), `LaunchProfileFrozenTurnArgvTests` (7). Every case named in the item is covered; the store is isolated per test via `XDG_CONFIG_HOME` (`_profile_store`) so no test reads the developer's real `runner-profiles.json`. THE DETECTION CLAIM IS PROVEN BY SABOTAGE, not asserted: three defects were injected into the implementation and the suite caught each, then the implementation was restored (evidence pasted under V-05). Two in-suite controlled negatives also exist (`test_controlled_negative_a_verifier_missing_variant_would_be_detected`, `test_controlled_negative_re_resolving_on_resume_would_be_detected`) so the positive assertions cannot pass vacuously.

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
| The plan's own premise went stale | FOUND AT EXECUTION 2026-09-06: `--variant` ALREADY EXISTED when this plan ran. `/plan-review` verified its absence BY EXECUTION on 2026-08-31, then commit `8ced15ce` (plan `429f30`) added it on 2026-09-01. So E-01/E-04's `--variant` half was pre-satisfied and was PRESERVED, not rewritten (DECISION 18-3cm15q-D1); the genuinely absent substance was the `as` grammar, resolution, provenance, and freezing (`runner_profiles` had ZERO importers in `oc_runipd.py`). | Re-measure a plan's "already"/"does not exist" premises at execution, not at review; a fast-moving file can invalidate either direction. |
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

- [x] V-01 validates E-01
  - Required evidence: Paste parser-test output and parsed namespaces for implicit run as gem SELECTOR, explicit start as gem SELECTOR, direct --model/--variant, command-like profile names, profile-like tokens without as remaining selectors, missing/repeated/misplaced as failures, unchanged status/report/resume routing, and the literal-as selector escape.
  - Observed evidence: All 9 grammar tests pass (`python3 -m pytest tests/test_oc_runipd.py -k LaunchProfileGrammar -o addopts="" -v`):

    ```text
    LaunchProfileGrammarTests::test_implicit_and_explicit_start_both_carry_profile_and_selectors PASSED
    LaunchProfileGrammarTests::test_direct_model_and_variant_flags_are_preserved PASSED
    LaunchProfileGrammarTests::test_missing_repeated_and_misplaced_as_clauses_are_refused PASSED
    LaunchProfileGrammarTests::test_profile_like_token_without_as_stays_a_selector PASSED
    LaunchProfileGrammarTests::test_command_like_profile_names_do_not_shadow_subcommands PASSED
    LaunchProfileGrammarTests::test_other_subcommands_route_unchanged PASSED
    LaunchProfileGrammarTests::test_profile_named_on_resume_is_refused_not_silently_ignored PASSED
    LaunchProfileGrammarTests::test_double_dash_escapes_a_literal_as_selector PASSED
    LaunchProfileGrammarTests::test_selector_whose_text_equals_a_profile_name_is_still_a_selector PASSED
    ```

    PARSED NAMESPACES (asserted in `test_implicit_and_explicit_start_both_carry_profile_and_selectors`
    and its siblings; the profile never leaks into `selectors`):

    ```text
    run as gem 3cm15q          -> command=start  profile='gem'  selectors=['3cm15q']
    run start as gem 3cm15q    -> command=start  profile='gem'  selectors=['3cm15q']
    run 3cm15q --model M --variant high -> profile=None model='google/gemini-3.7-flash' variant='high' selectors=['3cm15q']
    run as status 3cm15q       -> command=start  profile='status'  selectors=['3cm15q']   (also resume/report/stop/start/all/reviews)
    run gem                    -> profile=None  selectors=['gem']  (even with `gem` CONFIGURED)
    run -- as                  -> profile=None  selectors=['as']   (the literal-as escape)
    status run-xyz             -> command=status  profile=None     (report/resume likewise unchanged)
    ```

    MISSING/REPEATED/MISPLACED, refused with exit 2 and no `initialize_run` call (run by execution):

    ```text
    $ python3 -m agent_workflows.oc_runipd as ; echo exit=$?
    runipd: 'as' requires a profile name. usage: aw oc run as <profile> [SELECTOR ...]   (the 'as' clause comes FIRST, immediately after 'run'/'start'; use 'aw oc run -- as' for a literal 'as' selector)
    exit=2
    $ python3 -m agent_workflows.oc_runipd as gem as gem ; echo exit=$?
    runipd: misplaced 'as': the 'as' clause may appear only once. usage: aw oc run as <profile> [SELECTOR ...]   (...)
    exit=2
    $ python3 -m agent_workflows.oc_runipd 3cm15q as gem ; echo exit=$?
    runipd: misplaced 'as': the 'as' clause must come FIRST, before any selector. usage: aw oc run as <profile> [SELECTOR ...]   (...)
    exit=2
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste initialization tests for named, per-runner-default, no-default, partial explicit overrides, wrong-runner, unknown, and malformed configuration. For every failure, paste assertions showing no run ID/directory/state/events were created and no OpenCode process was invoked.
  - Observed evidence: All 6 resolution tests pass:

    ```text
    LaunchProfileResolutionTests::test_named_profile_supplies_all_three_fields PASSED
    LaunchProfileResolutionTests::test_per_runner_default_profile_applies_without_as PASSED
    LaunchProfileResolutionTests::test_no_default_preserves_host_default_behavior PASSED
    LaunchProfileResolutionTests::test_partial_explicit_override_keeps_the_other_profile_fields PASSED
    LaunchProfileResolutionTests::test_unknown_wrong_runner_and_malformed_all_fail PASSED
    LaunchProfileResolutionTests::test_unknown_profile_creates_no_run_state_and_launches_nothing PASSED
    ```

    THE PER-FIELD PRECEDENCE MATRIX, resolved live against a store holding
    `gem = {model: google/gemini-3.7-flash, variant: low, agent: build}` set as the `oc` default:

    ```text
    --- as gem
      model/variant/agent: google/gemini-3.7-flash | low | build
      provenance: {'runner': 'explicit', 'model': 'profile', 'variant': 'profile', 'agent': 'profile', ...}
    --- as gem --variant high
      model/variant/agent: google/gemini-3.7-flash | high | build
      provenance: {'runner': 'explicit', 'model': 'profile', 'variant': 'explicit', 'agent': 'profile', ...}
    --- default profile (no as)
      model/variant/agent: google/gemini-3.7-flash | low | build
      provenance: {'runner': 'explicit', 'model': 'default-profile', 'variant': 'default-profile', 'agent': 'default-profile', ...}
    --- direct flags only
      model/variant/agent: anthropic/claude | high | build
      provenance: {'runner': 'explicit', 'model': 'explicit', 'variant': 'explicit', 'agent': 'default-profile', ...}
    ```

    Note row 2: `--variant high` overrode ONLY the variant and did NOT drop the profile's model or
    agent, which is the "direct override replaces whole profile" failure mode.

    NO SIDE EFFECTS ON FAILURE, proven on a real tmp repo (not a mock):

    ```text
    $ python3 -m agent_workflows.oc_runipd as nope dem001 ; echo exit=$?
    runipd: runner profile: no runner profile named 'nope' (known profiles: (none)). Create it with 'aw oc profile add nope'.
    exit=2
    $ ls -la .aw/records/runs
    ls: cannot access '.aw/records/runs': No such file or directory
    ```

    `test_unknown_profile_creates_no_run_state_and_launches_nothing` asserts the same as a regression:
    the run-dir listing is unchanged before/after and stdout contains no `Run ID:` line (so no run id
    was minted and no OpenCode process was reached, the launch being downstream of the refusal).
    Malformed (`{not json`) and wrong-runner (`runner: "agy"`) both raise `DriverError` as asserted in
    `test_unknown_wrong_runner_and_malformed_all_fail`. An ABSENT store is a no-op, not a failure
    (`test_absent_store_is_a_no_op_not_a_failure`, exit 0 with `model=None`).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste prepare-only/status/report/JSON assertions and one state.json excerpt containing requested/applied profile, config source/digest, resolved runner/model/variant/agent, and per-field provenance. Show driver actor includes resolved model/variant and no credentials.
  - Observed evidence: All 4 durable-state tests pass:

    ```text
    LaunchProfileDurableStateTests::test_state_records_resolved_fields_and_per_field_provenance PASSED
    LaunchProfileDurableStateTests::test_report_and_status_render_the_launch_identity PASSED
    LaunchProfileDurableStateTests::test_driver_actor_includes_variant_and_profile_without_parens_in_values PASSED
    LaunchProfileDurableStateTests::test_render_launch_identity_tolerates_a_pre_field_run PASSED
    ```

    `--prepare-only` for `aw oc run as gem dem001 --variant high`, last line of the real run:

    ```text
    Launch: model=google/gemini-3.7-flash (profile); variant=high (explicit); agent=build (profile); profile=gem (requested)
    ```

    THE state.json EXCERPT from that same run (`options`):

    ```text
    model  : google/gemini-3.7-flash
    variant: high
    agent  : build
    launch_profile:
    {
      "agent": "build",
      "applied": "gem",
      "config_digest": "22585321c15e4bd286c322d6c943b784dd42d0d4e8576a1890c3b0b2b6aa7e93",
      "config_present": true,
      "config_source": "<xdg>/agent-workflows/runner-profiles.json",
      "model": "google/gemini-3.7-flash",
      "provenance": {
        "agent": "profile",
        "model": "profile",
        "runner": "explicit",
        "validate": "shipped-default",
        "variant": "explicit"
      },
      "requested": "gem",
      "runner": "oc",
      "variant": "high"
    }
    ```

    THE REPORT line from the same run's `execution-report.md`:

    ```text
    10:- Launch: model=google/gemini-3.7-flash (profile); variant=high (explicit); agent=build (profile); profile=gem (requested)
    ```

    `--json` status needed no change and is asserted intact: it dumps `state.json` verbatim, so the
    `launch_profile` object above IS the JSON surface (consumed that way by the V-04 freeze test).

    DRIVER ACTOR, and NO CREDENTIALS:

    ```text
    driver_actor({"options": {"model": "g/m", "variant": "high", "launch_profile": {"applied": "gem"}}})
      -> "aw oc run model=g/m variant=high profile=gem"     (asserted: no "(" anywhere)
    driver_actor({"options": {"model": "opus"}})
      -> "aw oc run model=opus"                              (byte-identical to before this change)
    ```

    The test also asserts no credential-shaped key appears in the serialized snapshot; structurally
    guaranteed because `runner_profiles`' schema admits only runner/model/variant/agent/validate
    (`runner_profiles.py:501` `parse_profile` + `_reject_unknown_keys`). `aw sanitize --agent` on the
    tree: `{"outcome":"clean","exit":0,"findings":0}`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste exact argv assertions for review, primary execution, recovery, and independent verifier turns with model/variant/agent; provider-default omission of --variant; shell=False; and resume after editing/deleting the source profile. Include a controlled failing test or mutation demonstrating verifier omission/re-resolution is detected.
  - Observed evidence: All 7 argv/freeze tests pass:

    ```text
    LaunchProfileFrozenTurnArgvTests::test_execute_recovery_review_and_verifier_turns_all_carry_model_variant_agent PASSED
    LaunchProfileFrozenTurnArgvTests::test_provider_default_omits_variant_entirely PASSED
    LaunchProfileFrozenTurnArgvTests::test_resume_does_not_reload_profiles_after_the_store_changes PASSED
    LaunchProfileFrozenTurnArgvTests::test_controlled_negative_a_verifier_missing_variant_would_be_detected PASSED
    LaunchProfileFrozenTurnArgvTests::test_controlled_negative_re_resolving_on_resume_would_be_detected PASSED
    LaunchProfileFrozenTurnArgvTests::test_direct_start_without_a_profile_is_behavior_equivalent PASSED
    LaunchProfileFrozenTurnArgvTests::test_absent_store_is_a_no_op_not_a_failure PASSED
    ```

    THE EXACT ARGV for all four turn kinds, captured off a patched `subprocess.Popen` (so the real
    builder ran) with `shell=False` asserted on the kwargs of every call:

    ```text
    execute                  --model=google/gemini-3.7-flash --variant=high --agent=build  shell=False
    recovery                 --model=google/gemini-3.7-flash --variant=high --agent=build  shell=False
    review                   --model=google/gemini-3.7-flash --variant=high --agent=build  shell=False
    verifier(fresh session)  --model=google/gemini-3.7-flash --variant=high --agent=build  shell=False
    ```

    One full argv, for shape (execute turn):

    ```text
    ['opencode', 'run', '--dir', '<tmp>', '--format', 'json', '--model', 'g/m', '--variant', 'high',
     '--agent', 'build', '--auto', '--title', 'aw-exec-run-test-s1-prof03', '--file', '<plan>', '--', 'do the thing']
    ```

    PROVIDER-DEFAULT OMISSION: with only `model` frozen, the argv contains `--model` and asserts
    `--variant` and `--agent` are ABSENT entirely (not passed empty).

    RESUME AFTER MUTATING THE STORE, run live end to end. The run was created with
    `gem = google/gemini-3.7-flash` + `--variant high`, then the profile was REPOINTED and finally
    DELETED; the identity did not move:

    ```text
    # after repointing gem -> EVIL/repointed-model, variant minimal
    Launch: model=google/gemini-3.7-flash (profile); variant=high (explicit); agent=build (profile); profile=gem (requested)
    --- now DELETE the store entirely ---
    Launch: model=google/gemini-3.7-flash (profile); variant=high (explicit); agent=build (profile); profile=gem (requested)
    ```

    `test_resume_does_not_reload_profiles_after_the_store_changes` asserts the same through
    `status --json`, including that `config_digest` is UNCHANGED from the frozen value (a re-resolution
    would necessarily change it).

    CONTROLLED NEGATIVES / MUTATION EVIDENCE. Two in-suite negatives prove the assertions are not
    vacuous: one sabotages the verifier turn's `options["variant"]` and asserts the omission is
    observable, the other performs a real re-resolution across a store edit and asserts the model AND
    digest both change (i.e. re-resolution IS detectable, which is what the freeze test rules out).
    Additionally, THREE defects were injected into the implementation itself and the suite caught each
    (implementation then restored; see V-05 for the runs).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Paste the complete focused OpenCode runner/CLI suite command, exit code, and summary with named parser, side-effect, argv, state, report, verifier, and resume cases. Paste existing session/worktree/lifecycle regression summaries to prove the feature did not bypass them.
  - Observed evidence: THE PLAN'S NAMED FOCUSED COMMAND, with its exit code:

    ```text
    $ python3 -m pytest -p no:randomly tests/test_oc_runipd.py tests/test_oc_runipd_cli.py -q -o addopts=""
    ........................................................................ [ 46%]
    ........................................................................ [ 92%]
    ...........                                                              [100%]
    155 passed in 17.60s
    exit=0
    ```

    (`-o addopts=""` clears the repo's configured `addopts`, which is what the AGENTS contract
    prescribes when per-test counts are needed from a narrowed run; the plan itself names
    `-p no:randomly -q`.)

    THE 26 NEW CASES, all passing, enumerated by name under V-01 (9 parser/grammar), V-02 (6
    resolution + side-effect), V-03 (4 state/report/actor) and V-04 (7 argv/verifier/resume).

    REGRESSION PROOF THAT NOTHING WAS BYPASSED. Sessions, worktrees, lifecycle, stop-triggers, and the
    shared-runner parity guard all still pass:

    ```text
    $ python3 -m pytest tests/test_runner_profiles.py tests/test_runner_profile_wizard.py \
        tests/test_oc_profile_cli.py tests/test_agy_runipd_cli.py tests/test_agy_runipd_shim.py \
        tests/test_host_sandbox_profile.py -o addopts="" -q
    280 passed in 9.28s

    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    43 passed in 5.45s
    ```

    WHOLE SUITE, compared against the pre-change baseline at this same commit. The failing set is
    BYTE-IDENTICAL before and after, so this change introduces ZERO regressions:

    ```text
    $ python3 -m pytest                       # with this change
    18 failed, 5268 passed, 3 skipped, 4 xfailed in 108.91s

    $ diff <(baseline FAILED lines) <(after FAILED lines) && echo "IDENTICAL: no regression introduced"
    IDENTICAL: no regression introduced
    18
    ```

    The 18 pre-existing failures are in `tests/test_run_viewer.py`, `tests/test_next_ordering.py`, and
    one signal-timing case in `tests/test_runner_stop_triggers.py`
    (`test_the_terminal_rung_still_records_the_item_interrupted`, which fails 3/3 times with this
    change STASHED). They are unrelated to this plan and are NOT claimed as passing.

    ONE REGRESSION WAS FOUND AND FIXED DURING THIS PASS, recorded because it is the kind of thing a
    summary would hide: hoisting the shim's `subcommands` set into a module constant broke
    `test_runner_stop_triggers.py::test_stop_is_listed_in_both_shims_subcommand_sets`, which asserts
    STRUCTURALLY by regexing `subcommands = \{(.*?)\}` in both drivers' sources. The set literal was
    restored inline (with a comment saying why it must stay inline) rather than weakening the test,
    since that guard is what stops `stop <run-id>` being rewritten to `start stop <run-id>`.

    SABOTAGE EVIDENCE that these tests detect shallow integration. Each defect was injected into the
    implementation, the suite was run, and the implementation was restored:

    ```text
    # 1. argv builder drops --variant (parsed-but-not-forwarded)
    FAILED LaunchProfileFrozenTurnArgvTests::test_execute_recovery_review_and_verifier_turns_all_carry_model_variant_agent
      AssertionError: '--variant' not found in ['opencode','run','--dir',...,'--model','g/m','--agent','build',...]
    1 failed, 25 passed

    # 2. resolution moved AFTER the run directory is created (partial durable state)
    FAILED LaunchProfileResolutionTests::test_unknown_profile_creates_no_run_state_and_launches_nothing
      - []
      + ['run-20260906T074509Z-4124217'] : a refused run left durable state behind
    1 failed, 25 passed

    # 3. profile resolved but the RAW flags frozen instead (cosmetic-only integration)
    FAILED LaunchProfileFrozenTurnArgvTests::test_resume_does_not_reload_profiles_after_the_store_changes
    FAILED LaunchProfileDurableStateTests::test_state_records_resolved_fields_and_per_field_provenance
    FAILED LaunchProfileDurableStateTests::test_report_and_status_render_the_launch_identity
    3 failed, 23 passed
    ```
  - Result: pass


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
