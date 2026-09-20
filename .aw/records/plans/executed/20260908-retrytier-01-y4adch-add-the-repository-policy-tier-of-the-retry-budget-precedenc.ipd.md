# IPD: Add the repository-policy tier of the retry-budget precedence chain

- Date: 2026-09-08
- Kind: child
- Concern: A THREE-TIER PRECEDENCE CHAIN SHIPS WITH ITS MIDDLE TIER MISSING, AND THE CODE SAYS SO IN ITS OWN DOCSTRING. Spec `25kzda` (`- Status: approved`) fixes the chain twice: at `:158` "The CLI value overrides repository policy; repository policy overrides the default of 2. The frozen value cannot change on resume", and again in the invariant table at `:118` ("A2: configurable retries"). `resolve_retry_budget` (`agent_workflows/runner_shared.py:1987`) implements two of the three and states the gap in as many words (`:1990-1993`): "The MIDDLE TIER IS NOT IMPLEMENTED and is not faked here: no repository-policy home exists (backlog `dh3us4` tracks it), so this resolves CLI-over-default and the gap is stated in `--retry-budget`'s own `--help` rather than left for an operator to discover."
  THE WHOLE RESOLVER IS FOUR LINES AND HAS NO REPOSITORY-CONFIG READ AT ALL: `if cli_value is None: return run_recovery.DEFAULT_RETRY_LIMIT`, else `run_recovery.validate_retry_budget(cli_value)` wrapped into a `RunFlagRefusal`. It takes ONLY `cli_value`, so the middle tier requires a SIGNATURE CHANGE to receive a repo root, and every caller must pass it. RE-MEASURED AT REVIEW (HEAD `c8461ef5`), because every anchor in `runner_shared.py` had drifted about 97 lines: the resolver is `runner_shared.py:2084`, `RETRY_BUDGET_OWNER` `:2012`, `freeze_run_policy_flags` `:2155` with its retry branch `:2175-2176`, `refuse_frozen_flags_on_resume` `:2131`; the call sites are `oc_runipd.py:2783` (unchanged) and `agy_runipd.py:1838` (the plan said `:1792`), and the freeze results land in state at `oc_runipd.py:3059` and `agy_runipd.py:2063` (the plan said `:2017`).
  THE CALLER COUNT IS LARGER THAN THE PLAN STATED, AND ONE FACT ABOUT THE TWO DRIVER CALLS CHANGES THE DESIGN. Found at review: the `initialize_run` calls DISCARD the return value. Both are bare expression statements (`runner_shared.resolve_retry_budget(getattr(args, "retry_budget", None))`) whose only purpose is the REFUSAL side effect, and the comment above each says so ("refuse an unhonorable flag BEFORE resolution... Nothing is re-decided here"). The value that actually reaches `state["options"]` comes solely from `freeze_run_policy_flags`. So the middle tier must be threaded into BOTH paths for different reasons: into the driver calls so a bad POLICY value is refused as early as a bad CLI value, and into the freeze path because that is the only call whose RESULT is kept. A change to only one of them either resolves the wrong number or refuses at the wrong time, and the plan's E-03 did not distinguish them. Both live inside `initialize_run`, where `repo` is already bound (`oc_runipd.py:2744`), so the root is available at all four sites.
  SIX TEST CALL SITES ALSO PASS ONE POSITIONAL ARGUMENT, so a required parameter breaks them. Measured: `tests/test_run_flag_surface.py` calls `resolve_retry_budget(...)` six times (`:608`, `:611`, `:615`, `:618`, `:619`, `:625`) and `freeze_run_policy_flags(...)` four times, all with the current signature. That file IS declared in `Scope-Paths`, and no other test module touches either symbol, so the blast radius is contained; but E-03 must state whether the new parameter is OPTIONAL (keyword with a default, leaving all ten call sites valid) or REQUIRED (ten call sites to update). See OQ-04.
  THE DEFAULT'S SINGLE DEFINITION IS `run_recovery.DEFAULT_RETRY_LIMIT` (`agent_workflows/run_recovery.py:67`, value `2`), read at `:275`, `:416` and `runner_shared.py:2004`, and deliberately not duplicated (`RETRY_BUDGET_OWNER`, `runner_shared.py:1915`, exists only to tell a reader where the number lives). The 0..10 bound belongs to `run_recovery.validate_retry_budget` and is CALLED, never re-checked, because executed plan `sq61qd` made that the single definition precisely so the flag layer could reach it at parse time. Both properties must survive.
  THE ITEM'S OWN DESIGN CAUTION IS WHERE IT IS MOST WRONG, AND CORRECTING IT SHRINKS THE WORK. It warns that `.aw/config/project.json` "is the obvious home, but adding a key there is a schema change with its own validation and defaulting rules." Measured, and CONFIRMED at review: `project_schema.parse_portable_policy` (`agent_workflows/project_schema.py:558`) carries a `known_keys` set (`:574`) but is PERMISSIVE, preserving unrecognized keys in `unknown_fields` (`:585`) and writing them BACK on serialization. So the schema does NOT need editing, and there are TWO SHIPPED PRECEDENTS that deliberately bypass it, both reading the file directly in `config.py` and both documenting why: `dependency_schema_cutover` (`config.py:1044`, reader `:1047`, accessor `:1072`, FAIL-OPEN) and `review_findings_gate` (`:1097`, reader `:1106`, accessor `:1130`, with its vocabulary tuple at `:1100` and default at `:1103`). The convention is written down at `config.py:1086-1089`. All `config.py` anchors verified unchanged at review.
  ONE CHARACTERIZATION OF THE SECOND PRECEDENT IS TOO COARSE, AND IT IS THE ONE OQ-01 TURNS ON. The plan calls `review_findings_gate` "FAIL-CLOSED" and treats it as the model for refusing a bad value. Read at review, it is fail-closed IN ITS DEFAULT and fail-OPEN ON A BAD VALUE: `findings_gate_threshold` (`config.py:1130-1145`) returns `REVIEW_GATE_DEFAULT` when the key is absent, when the value is not a string, AND when it is outside the vocabulary, and its docstring states that choice explicitly ("A typo therefore lands on the SAFE side (still gating) rather than silently disabling the gate"). It NEVER raises. So NEITHER shipped precedent refuses a run over a malformed config value, and OQ-01's fail-closed option would introduce a THIRD posture rather than follow the second precedent. That does not settle the question (a retry budget has no "safe side" the way a gate threshold does, since both a higher and a lower budget are merely different, not safer), but it changes what the choice costs and it is why OQ-01 is escalated to the maintainer rather than resolved here.
- Scope: Add the repository-policy tier: a project-config key read through a `config.py` accessor following the two shipped precedents, consulted by `resolve_retry_budget` only when no CLI value was passed, falling back to `run_recovery.DEFAULT_RETRY_LIMIT`, with the 0..10 bound still reached through `validate_retry_budget` and the resume freeze unchanged. EXCLUDES SPENDING the budget, which is `xipfy1`'s (`retrywire-01`) entire subject and which this plan must not touch; EXCLUDES the separate `--integration-retry-limit` knob (`51vw4y` E-02, explicitly told not to reuse `DEFAULT_RETRY_LIMIT`); EXCLUDES editing `project_schema.py`, which does not need it.
- Scope-Paths: agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_flag_surface.py
- Item-Dependencies: none
- Status: executed
- Set: retrytier
- Order: 1
- Highest E allocated: 06
- Readiness: go-pending-approval
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y4adch
- From-Backlog: dh3us4

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: y4adch verified (set retrytier, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its blocking OQ-01 was answered on 2026-09-10 (fall back and warn) and the finding it escalated, PR-004, is now closed in review round 2. Performed at HEAD `5692797e` at the maintainer's explicit instruction of 2026-09-10, who was shown that 12 of 15 `no-go` plans were held by stale bookkeeping and chose to have them fixed with evidence recorded rather than re-reviewed. This is the SECOND such cleanup in one session; the durable fix is plan `qhy3i3` E-07, authored and awaiting approval. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-008, seven FIXED and PR-004 escalated to OQ-01 (Blocking: yes); Readiness no-go pending that answer

- 2026-09-10 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-008, seven FIXED and PR-004 escalated; Readiness no-go pending OQ-01. Reviewed at HEAD `c8461ef5`; `aw ipd lint` conformed at `--phase author` before and `--phase review-finalize` after. THE GRADUATION WORK IS THE BEST I HAVE REVIEWED IN THIS TREE and I weakened none of it: it measured the source item's design caution and disproved it, checked five plan dispositions for overlap symbol by symbol, distinguished itself from `xipfy1` in both directions with three quoted exclusions, corrected three of its own item's claims, and argued AGAINST its own urgency in OQ-03. Every one of those claims re-verified true. WHAT REVIEW FOUND is that the plan under-measured its own blast radius in three ways that would each have surfaced mid-execution. PR-001 (HIGH): the two `initialize_run` calls DISCARD their return value and exist only for the early refusal, while `freeze_run_policy_flags` is the ONLY call whose result reaches `state["options"]`; E-03 treated all three as one job, so a faithful executor could thread the root into the refusal path, pass every test the plan specified, and freeze the default anyway. New E-05 case (h) now pins the frozen value. PR-002 (HIGH): there are TEN existing call sites, not three, six of them assertions in the declared test file, so whether the new parameter is optional or required is a real design decision the plan never raised; added as OQ-04, resolved with a recommendation plus the guard that makes it safe. PR-004 (BLOCKER, ESCALATED, the one thing a maintainer must act on): OQ-01 delegated the fail-open/fail-closed choice to E-01 on the premise that the repository has "shipped BOTH postures", and that premise is FALSE. `findings_gate_threshold` falls back to its default on an absent key, a non-string value AND an out-of-vocabulary value and never raises; `read_dependency_schema_cutover` swallows every error. So no precedent selects an answer and fail-closed would introduce a new posture; OQ-01 is now `Blocking: yes` with a third option (fall back but WARN) recorded. PR-003 (MEDIUM): the bound-delegation test constrains the CODE TEXT (it inspects the source after the last `"""` for a literal `10`), which the plan told the executor to keep green without saying how it works. PR-005 (MEDIUM): every `runner_shared.py` anchor had drifted about 97 lines, two of them lines the plan forbids editing. PR-006, PR-007, PR-008 (LOW): the suite baseline recorded for recognition with a prohibition on deleting another party's gitignored directory; the resume freeze noted as already structurally guaranteed; `Scope-Paths` verified sufficient for the larger caller set. E/V counts unchanged at six each. No product code was modified by this review.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `dh3us4`. NOTHING IS OBSOLETE and no plan in any disposition adds the middle tier: searched all five for `retry-budget`, `retry_budget`, `DEFAULT_RETRY_LIMIT`, `retrypolicy`, `dh3us4`, "repository policy". Every hit is adjacent and each was checked individually. `sq61qd` (executed) made the 0..10 bound single-definition. `uyeko5` (executed) shipped CLI-over-default and its Deferred section FILED this item. `xipfy1` (`retrywire-01`, `to-review`, `From-Backlog: trjfyy`, `Blocks-Release: next`) EXPLICITLY EXCLUDES this tier three times: its scope says it "Adds no flag, no new budget semantics, and no repository-policy tier", its E-02 says "Do NOT call `resolve_retry_budget` again in the loop", and its Deferred section says "THE REPOSITORY-POLICY PRECEDENCE TIER. Owned by backlog `dh3us4` ... Adding it here would take over another item's scope". `51vw4y` E-02 adds a DIFFERENT knob (`--integration-retry-limit`) and is explicitly told not to reuse `DEFAULT_RETRY_LIMIT`. `m7gvuz` F-13/E-10 must merely DECIDE whether to reuse `--retry-budget` and adds no tier. `1bfppy` defers requeuing. THE CRITICAL RELATIONSHIP QUESTION IS ANSWERED AND IT IS NOT A DEPENDENCY: `xipfy1` consumes the already-FROZEN integer and does not change where or how the budget is RESOLVED, while this plan changes only the resolution. They touch the same file at different functions, so this is merge ordering. Graduated backlog `trjfyy` ("retry budget dormant zero callers") covers the CONSUMPTION gap and graduated to `xipfy1`; it distinguishes the two itself (`:31-33`: "`dh3us4` ... covers ONLY the repository-policy middle precedence tier ... i.e. it PRESUMES consumption exists"). THREE OF THE ITEM'S CLAIMS ARE NOW WRONG AND ALL THREE ARE RECORDED RATHER THAN CARRIED FORWARD. FIRST, `DEFAULT_RETRY_LIMIT` is at `run_recovery.py:67`, not `:62` (line 62 is inside the rationale comment); the value `2` is correct. SECOND, the "schema change with its own validation and defaulting rules" caution is misleading: `project_schema.parse_portable_policy` (`project_schema.py:558`) preserves unknown keys (`:585`) and round-trips them (`:519-522`), and TWO shipped repo-policy keys deliberately bypass it with the convention written at `config.py:1086-1089`, so the work is SMALLER than the item implies while the caution's substance ("do NOT add an ad-hoc config read; follow the authority") is satisfied by following those precedents. THIRD, "WHY IT IS GATED ON `uyeko5`" is stale: `uyeko5` is executed and the item is correctly `open`. ONE OF THE ITEM'S OWN ARGUMENTS IS NOW WEAKER, and honesty requires saying so: it claims "the two shipped tiers give correct behavior for every invocation", but the budget is NEVER SPENT today (`run_recovery.plan_retry` `:269` and `retry_budget_remaining` `:415` have no production callers, only their own module and `tests/test_run_recovery_cli.py`), so no invocation gets correct retry behavior at ANY tier until `xipfy1` lands. That weakens the not-urgent framing rather than the scope, and is why this plan carries no release gate: the item carries none. FINALLY, a shipped contract test constrains the change: `tests/test_run_flag_surface.py:628-639` (`test_the_bound_is_sq61qds_and_is_not_re_checked_here`) forbids a literal bound here, and `:288-291` requires `NOT IMPLEMENTED` and `dh3us4` in `--retry-budget`'s help, so the help text must be updated in the same change.

## Goal

Complete the spec's three-tier retry-budget precedence by giving a repository a standing default other than 2, following the two config-key precedents already shipped, without re-deciding the bound, duplicating the default, or touching how the budget is spent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: choose the key's contract before writing it

- [x] E-01 DECIDE AND RECORD THE KEY's NAME, SHAPE AND FAILURE POSTURE, following the two shipped precedents rather than inventing a third pattern. Read both first: `dependency_schema_cutover` (`config.py:1044`, reader `:1047`, accessor `:1072`) is FAIL-OPEN; `review_findings_gate` (`:1097`, reader `:1106`, accessor `:1130`, vocabulary `:1100`, default `:1103`) is FAIL-CLOSED. The convention that neither is registered in `CONFIG_SCHEMA` is documented at `:1086-1089`, with the reason (`parse_portable_policy` preserves unknown keys and writes them back, so the key round-trips safely).
  FAIL-OPEN VERSUS FAIL-CLOSED IS A MAINTAINER DECISION, NOT YOURS: OQ-01 is `Blocking: yes` and MUST be answered before this item runs. Do not choose it yourself and do not infer it from the precedents, because review measured that NEITHER precedent refuses a run over a bad value, so "follow the second precedent" does not select an answer. `findings_gate_threshold` (`config.py:1130-1145`) falls back to its default on an absent key, a non-string value AND an out-of-vocabulary value, and never raises; `read_dependency_schema_cutover` likewise returns None on any error. Fail-closed here would be a THIRD posture in the file.
  WHAT E-01 STILL OWNS once the posture is answered: the key's NAME, confirmation of the bare-integer shape (OQ-02 resolved it as a rule), and writing the decision plus its reasoning into the accessor's docstring the way `config.py:1091-1094` and `:1140-1145` record theirs. Record the maintainer's answer verbatim with its date, so the next reader sees an attested decision rather than an implementer's preference.
  THE VALUE'S BOUND IS NOT YOURS TO DEFINE. It is 0..10 and it belongs to `run_recovery.validate_retry_budget`. Route the config value through it; do not compare against literals. `tests/test_run_flag_surface.py:628` (`test_the_bound_is_sq61qds_and_is_not_re_checked_here`) exists to enforce exactly this, and note HOW it enforces it, because it constrains your code text and not only your behavior: it takes `inspect.getsource(resolve_retry_budget)`, splits on `"""` and asserts the literal `10` does not appear in the LAST fragment. So a config key name, parameter default, or inline comment containing `10` after the docstring would fail it, and adding a second docstring-quoted block would change what `split()[-1]` captures. Do not weaken that test to accommodate a name; choose a name that does not contain `10`.
  - Depends on: none
  - Expected outcome: OQ-01's maintainer answer recorded verbatim with its date; a key name that does not contain the substring `10`; the bare-integer shape confirmed; the accessor docstring recording the posture and its reasoning; and a stated plan to route the value through `validate_retry_budget`.
  - Execution state: performed

### Task group 2: read the policy the way the repository already reads policy

- [x] E-02 ADD THE READER AND ACCESSOR TO `config.py`, COPYING THE SHIPPED SHAPE. `read_review_findings_gate` (`:1106-1127`) plus `findings_gate_threshold` (`:1130-1145`) is the closer model because it validates a value rather than merely reading a marker. Mirror its structure: a module constant for the key, a reader returning the raw value, and an accessor applying the default and the validation.
  DO NOT EDIT `project_schema.py`. `parse_portable_policy` (`:558`) preserves unrecognized keys in `unknown_fields` (`:585`) and writes them back on serialization (`:519-522`), so the key round-trips without a schema change. That is the documented convention (`config.py:1086-1089`), and it is the specific correction to the backlog item's design caution.
  HANDLE THE ABSENT CASES EXPLICITLY, all of which are normal: no `.aw/config/project.json` at all, a file without the key, a null value. Each must resolve to "no policy set", so the caller falls through to the default. A missing config file is the common case in a fresh repository and must never be an error.
  - Depends on: E-01
  - Expected outcome: a key constant, reader and accessor in `config.py` mirroring `read_review_findings_gate`/`findings_gate_threshold`, `project_schema.py` untouched, and every absent case resolving to "no policy set".
  - Execution state: performed

- [x] E-03 THREAD THE REPO ROOT INTO `resolve_retry_budget` AND ADD THE MIDDLE TIER, keeping the precedence exactly as spec `:158` states: CLI over repository policy over default 2. The function is at `runner_shared.py:2084` at review HEAD `c8461ef5` (the plan previously said `:1987`; every anchor in this file had drifted about 97 lines, so RE-LOCATE BY SYMBOL). Today it takes only `cli_value`, so this is a signature change.
  DECIDE OPTIONAL VERSUS REQUIRED PARAMETER FIRST, per OQ-04, and state which you chose and why. There are TEN existing call sites, not three: two driver calls, one freeze-path call, six `resolve_retry_budget` test calls (`tests/test_run_flag_surface.py:608`, `:611`, `:615`, `:618`, `:619`, `:625`) and four `freeze_run_policy_flags` test calls. A keyword parameter defaulting to "no repo root, so no policy tier" leaves every existing call valid and every existing test green; a required parameter means updating all ten. OQ-04 recommends the optional form and explains the honest cost (a caller that forgets to pass the root silently skips the middle tier), which E-06 must then guard by asserting the PRODUCTION call sites do pass it.
  THREE PRODUCTION CALL SITES, AND THE TWO KINDS ARE NOT INTERCHANGEABLE. This is the correction that matters most in this item: the two `initialize_run` calls DISCARD the return value and exist ONLY to raise `RunFlagRefusal` early ("refuse an unhonorable flag BEFORE resolution... Nothing is re-decided here"), while `freeze_run_policy_flags` (`runner_shared.py:2155`, retry branch `:2175-2176`) is the ONLY call whose RESULT is kept, landing in `state["options"]` (`oc_runipd.py:3059`, `agy_runipd.py:2063`). So thread the root into ALL THREE, for two different reasons: the driver calls so a malformed POLICY value is refused as early as a malformed CLI value (only meaningful if OQ-01 answers fail-closed), and the freeze call because it decides the number the run actually uses. Passing it to only the driver calls would refuse correctly and then freeze the wrong value; passing it to only the freeze call would resolve correctly but refuse late, after a run directory exists. `oc_runipd.py:2783` and `agy_runipd.py:1838` are the driver calls; `repo` is bound at `oc_runipd.py:2744` and both freeze calls are inside the same `initialize_run`, so the root is in scope at all three.
  KEEP THE TWO INVARIANTS THE CURRENT DOCSTRING PROTECTS. The bound stays `validate_retry_budget`'s and is CALLED, never re-checked here (`sq61qd` made it single-definition precisely so the flag layer could reach it at parse time when no `RunEngine` and no step exist). And the default stays `run_recovery.DEFAULT_RETRY_LIMIT` (`run_recovery.py:67`), never copied; `RETRY_BUDGET_OWNER` (`runner_shared.py:2012`) exists only to point a reader at it.
  UPDATE THE DOCSTRING, because it currently asserts the gap this plan closes ("The MIDDLE TIER IS NOT IMPLEMENTED and is not faked here"). Leaving it would make the code lie about itself. MIND THE BOUND TEST WHILE YOU DO: it inspects the source AFTER the last `"""`, so keep the whole rationale inside ONE docstring and keep the literal `10` out of everything below it.
  DO NOT CHANGE THE RESUME FREEZE. `--retry-budget` carries `resume_rule=RESUME_REFUSE` and `refuse_frozen_flags_on_resume` (`runner_shared.py:2131`) refuses it on resume; spec `:158` says "The frozen value cannot change on resume". Verified at review that the structure already guarantees this: `apply_run_policy_flags_on_resume` (`:2459`) SKIPS every row whose `resume_rule` is `RESUME_REFUSE` and never re-resolves, so resume reads the frozen integer and cannot consult config. Do not add a policy read to any resume path; E-05 case (g) asserts the property rather than assuming it.
  - Depends on: E-02
  - Expected outcome: `resolve_retry_budget` implementing CLI over policy over default with the bound still delegated and the default still single-defined; the optional-versus-required choice stated; all THREE production call sites passing the root with the refusal-versus-value distinction stated in a comment; the docstring corrected without breaking the source-inspecting bound test; and the resume freeze unchanged.
  - Execution state: performed

### Task group 3: tell the truth in the help text, and prove all three tiers

- [x] E-04 UPDATE `--retry-budget`'s HELP TEXT IN THE SAME CHANGE, or a shipped test fails. `tests/test_run_flag_surface.py:288-291` requires `NOT IMPLEMENTED` and `dh3us4` to appear in that help while the gap exists; both must go, and the test must be updated with them.
  THE CURRENT TEXT DISCLOSES THE GAP HONESTLY (`runner_shared.py:1895-1901`: "NOTE: spec 2.1's MIDDLE precedence tier (repository policy) is NOT IMPLEMENTED - no repository-policy home exists yet (backlog dh3us4) - so precedence today is CLI over default"). Replace it with the real three-tier precedence and NAME THE CONFIG KEY, because an operator who wants a standing override needs to know what to write and where. Keep the sentence that the frozen value cannot change on resume.
  DO NOT DELETE THE DISCLOSURE PATTERN ITSELF. Other rows still use it for genuinely unimplemented behavior (`--follow-generated` names backlog `x8diyb`), and the help-honesty test protects them.
  - Depends on: E-03
  - Expected outcome: `--retry-budget`'s help describing the real three-tier precedence and naming the config key, the `dh3us4` disclosure removed, the help-honesty test updated and still protecting the remaining unimplemented row.
  - Execution state: performed

- [x] E-05 PROVE THE RESOLVED VALUE IS CORRECT FOR EVERY INPUT COMBINATION, on fixtures. Seven combinations must each be asserted. (a) A CLI value alongside a set policy resolves to the CLI value. (b) A set policy with no CLI value resolves to the policy value. (c) Neither present resolves to `DEFAULT_RETRY_LIMIT`. (d) An absent config file resolves to the default without raising. (e) A policy value outside the 0..10 range behaves as E-01 decided, proven to route through `validate_retry_budget` rather than a local comparison. (f) A malformed policy value (wrong type or unparseable) behaves the same decided way. (g) A resume whose repository policy CHANGED since the run started still resolves to the frozen value.
  CASE (a) IS THE PRECEDENCE GUARD and case (g) IS THE FREEZE GUARD; both are the ones a careless implementation breaks. Quote their assertions separately.
  ADD CASE (h): THE VALUE THAT REACHES `state["options"]` IS THE POLICY VALUE. Cases (a) through (g) can all be satisfied by testing `resolve_retry_budget` alone, and that would MISS the defect this plan is most likely to ship, because the driver calls discard their result and only `freeze_run_policy_flags` produces the number the run uses. So assert through `freeze_run_policy_flags` with a repo whose policy is set, and show the frozen `retry_budget` is the POLICY value, not `2`. A plan that resolves correctly and freezes `2` has changed nothing observable.
  ASSERT THE BOUND IS NOT RE-DEFINED, keeping `tests/test_run_flag_surface.py:628` (`test_the_bound_is_sq61qds_and_is_not_re_checked_here`) green. If it needs adjusting because the function grew a parameter, adjust it WITHOUT weakening what it asserts and say exactly what changed. KNOW ITS MECHANISM BEFORE YOU TOUCH IT: it asserts `validate_retry_budget` appears in the source and that the literal `10` does NOT appear after the last `"""`. Two ways to break it accidentally are a key name or comment containing `10` below the docstring, and a second triple-quoted block that moves what `split()[-1]` captures. Neither is a reason to weaken the assertion.
  DO NOT WRITE TO THE REPOSITORY'S OWN `.aw/config/project.json`. It is a tracked, shared file, other agents are working in this checkout, and a test that mutates it would change every other run's behavior. Use throwaway repos. NOTE the existing `RetryBudgetTests` has no repo fixture at all (all six calls are pure), so you are adding the first one in that class; `tests/test_run_flag_surface.py` imports `REPO_ROOT` from `tests.support` for READING the spec file only, and that is not a pattern to copy for writing.
  - Depends on: E-04
  - Expected outcome: eight fixture cases passing with the precedence and freeze guards quoted separately, case (h) proving the frozen value is the policy value, the bound-delegation test still green and not weakened, and the real `project.json` untouched.
  - Execution state: performed

- [x] E-06 PROVE NOTHING ELSE MOVED, because this file is shared and one sibling plan reads the value this one resolves.
  `xipfy1`'s CONSUMPTION PATH MUST BE UNAFFECTED. It reads the FROZEN budget from `state["options"]` and explicitly does not re-resolve ("Do NOT call `resolve_retry_budget` again in the loop"). Show the frozen options' KEY SET and the type of `retry_budget` are unchanged (still one integer under the same key), so if `xipfy1` has landed it still reads the same thing, and if it has not, its premise still holds. It is `Status: to-review` at review and declares `runner_shared.py`, `oc_runipd.py` and `agy_runipd.py`, so it overlaps this plan on three files at different functions; that is merge ordering, not a hazard, since the runner isolates lanes and merges through the revalidate gate.
  IF YOU CHOSE A REQUIRED PARAMETER (OQ-04), ASSERT THE PRODUCTION CALL SITES PASS THE ROOT. With an OPTIONAL parameter this is the one thing that can silently fail: a caller that omits the root falls back to CLI-over-default and the middle tier quietly does not exist, with every unit test still green because they test the function directly. So inspect the three production call sites and assert each passes a root, the way `test_an_out_of_range_value_refuses_the_whole_run` (`tests/test_run_flag_surface.py:642-649`) already inspects `initialize_run`'s source for the call. That existing test is the pattern; extend its idea rather than inventing one.
  `run_recovery` MUST BE BYTE-UNCHANGED. `DEFAULT_RETRY_LIMIT` (`:67`), `validate_retry_budget` (`:136`) and `plan_retry` (`:269`) / `retry_budget_remaining` (`:415`) are not this plan's subject. Paste a diff proving it.
  THE OTHER RETRY KNOB MUST NOT BE TOUCHED. `51vw4y` E-02 adds `--integration-retry-limit` and is explicitly told not to reuse `DEFAULT_RETRY_LIMIT`; do not unify them here, and do not "helpfully" give it a policy tier too. Note `51vw4y` is `Status: reviewed` and also declares `runner_shared.py`, so it too is a merge-ordering neighbour.
  RUN THE SUITE BARE and judge on the DELTA, stating observed counts rather than quoting a baseline. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
  - Depends on: E-05
  - Expected outcome: the frozen options' key set and value type unchanged, the production call sites asserted to pass the root, `run_recovery` byte-unchanged, `--integration-retry-limit` untouched, and an empty bare-suite failure-set delta with observed counts stated.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE RESOLVER STATES ITS OWN GAP. `resolve_retry_budget` (`runner_shared.py:1987`), docstring `:1990-1993`: the middle tier "IS NOT IMPLEMENTED and is not faked here". Closing the gap means correcting that docstring too.
- THE BOUND IS SINGLE-DEFINITION BY DESIGN. `run_recovery.validate_retry_budget`, reached at parse time because executed `sq61qd` made it so; `runner_shared.py:1996-1999` explains why a second comparison "is the off-by-one that gets fixed in one place", and `tests/test_run_flag_surface.py:628-639` enforces it.
- SO IS THE DEFAULT. `run_recovery.DEFAULT_RETRY_LIMIT` (`run_recovery.py:67`, value `2`), with `RETRY_BUDGET_OWNER` (`runner_shared.py:1915`) existing only to point readers at it.
- THERE ARE TWO SHIPPED REPO-POLICY KEY PRECEDENTS, and following one is the house convention. `dependency_schema_cutover` (`config.py:1044`/`:1047`/`:1072`, fail-open) and `review_findings_gate` (`:1097`/`:1106`/`:1130`, fail-closed, with a vocabulary tuple and a default).
- AND THE SCHEMA DELIBERATELY DOES NOT REGISTER THEM. `config.py:1086-1089` records why: `project_schema.parse_portable_policy` (`project_schema.py:558`) preserves unknown keys in `unknown_fields` (`:585`) and writes them back (`:519-522`), so a key round-trips safely. This is the direct correction to the backlog item's caution.
- THE FLAG IS FROZEN AND REFUSED ON RESUME. `resume_rule=RESUME_REFUSE` on the row (`runner_shared.py:1889-1903`), enforced by `refuse_frozen_flags_on_resume` (`:2034`) from `oc_runipd.py:8292`/`agy_runipd.py:4957`; spec `:158` requires it.
- THE ROOT IS AVAILABLE AT THE CALL SITE. `oc_runipd.py:2783` runs after `repo` is bound at `:2744`.
- THE BUDGET IS NEVER SPENT TODAY. `plan_retry` (`run_recovery.py:269`) and `retry_budget_remaining` (`:415`) have no production callers. `xipfy1` (`retrywire-01`) is the plan that changes that, and it consumes the FROZEN value rather than re-resolving.
- A HELP-HONESTY TEST GUARDS THE DISCLOSURE. `tests/test_run_flag_surface.py:288-291` requires `NOT IMPLEMENTED` and `dh3us4` in this row's help while the gap exists.
- Shared checkout: `.aw/config/project.json` is tracked and shared, three agents are working here, and the suite runs BARE. Never mutate the real config in a test.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | MEDIUM | the middle tier is absent and the code admits it | `resolve_retry_budget` takes only `cli_value` and returns `DEFAULT_RETRY_LIMIT` when it is None; its docstring says the middle tier "IS NOT IMPLEMENTED and is not faked here". | `runner_shared.py:1987-2008`, `:1990-1993` |
| F-2 | MEDIUM | the spec fixes the chain in two places | "The CLI value overrides repository policy; repository policy overrides the default of 2. The frozen value cannot change on resume", plus invariant A2. Spec is `approved`. | spec `25kzda:158`, `:118`, `:4` |
| F-3 | MEDIUM | **the item's design caution is wrong, and the work is smaller than it implies** | `parse_portable_policy` preserves unknown keys (`:585`) and round-trips them (`:519-522`), and two shipped keys deliberately bypass `CONFIG_SCHEMA` with the convention documented. No schema change is needed. | `project_schema.py:558`, `:585`, `:519-522`; `config.py:1044`, `:1097`, `:1086-1089` |
| F-4 | LOW | the item's line citation is stale | `DEFAULT_RETRY_LIMIT` is at `run_recovery.py:67`, not `:62`; the value `2` is correct. | `run_recovery.py:67` |
| F-5 | MEDIUM | a signature change is unavoidable | The resolver takes only `cli_value`, so a policy read requires threading a repo root through both call sites and the freeze path. | `runner_shared.py:1987`, `:2058`, `:2078-2079`; `oc_runipd.py:2783`; `agy_runipd.py:1792` |
| F-6 | MEDIUM | two invariants must survive | The 0..10 bound is `validate_retry_budget`'s and is called not re-checked (`sq61qd`), enforced by a shipped test; the default is `DEFAULT_RETRY_LIMIT` and is never copied. | `runner_shared.py:1996-1999`, `:1915`; `tests/test_run_flag_surface.py:628-639` |
| F-7 | MEDIUM | **`xipfy1` is not a dependency in either direction** | It consumes the already-frozen integer and excludes this tier three times (scope, E-02 "Do NOT call `resolve_retry_budget` again in the loop", Deferred "Owned by backlog `dh3us4`"). Same file, different function: merge ordering only. | `xipfy1` scope, E-02, Deferred |
| F-8 | MEDIUM | **the item's not-urgent argument is now weaker, not its scope** | It claims the two shipped tiers "give correct behavior for every invocation", but the budget is never SPENT: `plan_retry` (`:269`) and `retry_budget_remaining` (`:415`) have no production callers. So no tier delivers retry behavior until `xipfy1` lands. | `run_recovery.py:269`, `:415`; graduated backlog `trjfyy` |
| F-9 | LOW | the two items were already distinguished by their own author | `trjfyy:31-33`: "`dh3us4` ... covers ONLY the repository-policy middle precedence tier ... i.e. it PRESUMES consumption exists." | that item |
| F-10 | LOW | a separate retry knob must stay separate | `51vw4y` E-02 adds `--integration-retry-limit` and is explicitly told not to reuse `DEFAULT_RETRY_LIMIT`. `m7gvuz` F-13/E-10 must merely DECIDE whether to reuse `--retry-budget`. | those plans |
| F-11 | LOW | the help text is a contract | `tests/test_run_flag_surface.py:288-291` requires `NOT IMPLEMENTED` and `dh3us4` in this row's help; both must change with the implementation. | that test; `runner_shared.py:1895-1901` |
| F-12 | LOW | the item's gating rationale is stale | "WHY IT IS GATED ON `uyeko5`" no longer applies; `uyeko5` is executed and the item is correctly `open`. | `.aw/records/plans/executed/...uyeko5...` |
| F-13 | LOW | no release gate to inherit | Backlog `dh3us4` carries no `Blocks-Release`, so this plan carries none. | the item file |
| F-14 | HIGH | **FOUND AT REVIEW: the two driver calls DISCARD the result, so "thread the root through the call sites" is two different jobs** | E-03 treated all three production calls as one change. They are not. `oc_runipd.py:2783` and `agy_runipd.py:1838` are bare expression statements whose only purpose is the early `RunFlagRefusal` ("refuse an unhonorable flag BEFORE resolution... Nothing is re-decided here"); the ONLY call whose result is kept is `freeze_run_policy_flags`'s (`runner_shared.py:2175-2176`), landing in `state["options"]`. Threading only the driver calls refuses correctly and then freezes the wrong number; threading only the freeze call resolves correctly but refuses late, after a run directory exists. | both call sites read as bare statements; `oc_runipd.py:3059`, `agy_runipd.py:2063` consume the freeze result |
| F-15 | HIGH | **FOUND AT REVIEW: ten existing call sites, not three, so the parameter's optionality is a real design decision** | `tests/test_run_flag_surface.py` calls `resolve_retry_budget` SIX times (`:608`, `:611`, `:615`, `:618`, `:619`, `:625`) and `freeze_run_policy_flags` FOUR times, all with today's signature. A REQUIRED parameter breaks all ten; an OPTIONAL one leaves them green but lets a forgetful caller silently skip the middle tier. The plan named neither option. Blast radius is contained: no other test module references either symbol. | counted in that file; `grep -rln` over `tests/` returns only that module |
| F-16 | MEDIUM | **FOUND AT REVIEW: `review_findings_gate` is NOT fail-closed on a bad value, so the plan's model for OQ-01 does not exist** | The plan calls it FAIL-CLOSED and offers it as the precedent for refusing a malformed value. `findings_gate_threshold` (`config.py:1130-1145`) returns its DEFAULT on an absent key, a non-string value, and an out-of-vocabulary value, and NEVER raises; its docstring says a typo should land "on the SAFE side". `read_dependency_schema_cutover` likewise swallows every error. So neither shipped key refuses a run over bad config, and OQ-01's fail-closed option would add a THIRD posture. | `config.py:1047-1069`, `:1130-1145` |
| F-17 | MEDIUM | **FOUND AT REVIEW: the bound-delegation test constrains the CODE TEXT, not just behavior** | `test_the_bound_is_sq61qds_and_is_not_re_checked_here` (`tests/test_run_flag_surface.py:628`) does `inspect.getsource(...).split('"""')[-1]` and asserts the literal `10` is absent from that fragment. So a config key name, parameter default, or comment containing `10` below the docstring FAILS it, and adding a second triple-quoted block changes what is inspected. The plan told the executor to keep it green without saying how it works, which invites weakening it to fit a name. | that test's body |
| F-18 | MEDIUM | **FOUND AT REVIEW: every `runner_shared.py` anchor drifted about 97 lines** | The plan cites the resolver at `:1987` (actual `:2084`), `RETRY_BUDGET_OWNER` `:1915` (actual `:2012`), `freeze_run_policy_flags` `:2058` (actual `:2155`), `refuse_frozen_flags_on_resume` `:2034` (actual `:2131`), the agy call site `:1792` (actual `:1838`) and the agy state write `:2017` (actual `:2063`). The `config.py`, `run_recovery.py` and test anchors are all correct. Two of the drifted lines are ones the plan forbids changing, so a near-miss edit to a neighbouring line is the specific hazard. | measured every anchor at HEAD `c8461ef5` |
| F-19 | LOW | **FOUND AT REVIEW: the suite baseline was never stated, which was correct, and here is the measurement** | The plan wisely says to state observed counts rather than quote a baseline. Measured at review: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks 189 files in a GITIGNORED `opencode-recovery/` directory (1746 files) belonging to ANOTHER PARTY. Recorded so an executor meeting it does not "clean up" a co-worker's data to green the suite. | bare `python3 -m pytest` |
| F-20 | LOW | the resume freeze is already structurally safe | `apply_run_policy_flags_on_resume` (`runner_shared.py:2459`) SKIPS every row whose `resume_rule` is `RESUME_REFUSE` and never re-resolves, so a resume reads the frozen integer and cannot consult config. E-05 case (g) therefore asserts an existing property rather than a new one, which is the honest framing. | that function's loop and docstring |

## Proposed changes (ordered, validatable)

1. Record the maintainer's OQ-01 answer and choose the key's name and shape (E-01). BLOCKED until OQ-01 is answered.
2. Add the reader and accessor to `config.py` mirroring `review_findings_gate`, leaving `project_schema.py` alone (E-02).
3. Thread the repo root into `resolve_retry_budget` and add the middle tier, at all THREE production call sites and for the two distinct reasons (early refusal versus the frozen value), correcting the docstring and keeping the resume freeze (E-03).
4. Replace the help text's gap disclosure with the real precedence and the key name, updating the help-honesty test (E-04).
5. Prove all three tiers plus every fallback, out-of-range, malformed and resume case on fixtures, AND that the frozen value in `state["options"]` is the policy value (E-05).
6. Prove the production call sites pass the root, and that the frozen options shape, `run_recovery` and the other retry knob are untouched (E-06).

## Deferred / out of scope (with reason)

- SPENDING THE BUDGET. `xipfy1` (`retrywire-01`, from backlog `trjfyy`) owns consumption end to end: the retryable-class allowlist, reading the frozen budget, spending via `plan_retry`, the correction packet, escalation on exhaustion. It carries `Blocks-Release: next`; this plan does not, and must not absorb its work. Note the honest consequence: until it lands, this tier is observationally inert, because no code spends the budget at any tier.
- THE `--integration-retry-limit` KNOB. `51vw4y` E-02 adds it and is explicitly instructed not to reuse `DEFAULT_RETRY_LIMIT`. Do not unify the two knobs and do not give it a policy tier by analogy.
- WHETHER `m7gvuz` SHOULD REUSE `--retry-budget`. Its F-13/E-10 owns that decision.
- REQUEUING SEMANTICS. `1bfppy` defers them; this plan changes only resolution.
- EDITING `project_schema.py` OR REGISTERING THE KEY IN `CONFIG_SCHEMA`. Neither is needed: unknown keys are preserved and round-tripped, and the two shipped precedents deliberately stay out of the schema with the reason documented at `config.py:1086-1089`. Registering it would also be a wider change than this tier warrants.
- RE-DEFINING THE 0..10 BOUND OR THE DEFAULT OF 2. Both are single-definition by deliberate design (`sq61qd`), and a shipped test enforces the first.
- CHANGING THE RESUME FREEZE. Spec `:158` requires the frozen value to stand; E-03 keeps it and E-05 asserts it against a CHANGED policy.
- ADDING POLICY TIERS TO OTHER FLAGS. Several rows could plausibly want one; each is its own decision with its own default and failure posture, and doing them together would make none of them reviewable.
- MUTATING THE REPOSITORY'S `.aw/config/project.json`. It is tracked and shared, and three agents are working in this checkout.

## Scope check

- Over-scope: none. One config key with a reader and accessor, one resolver gaining one parameter and one tier, three production call sites threading a root, one help string, one test surface.
- SCOPE-PATHS VERIFIED SUFFICIENT AT REVIEW, which was worth checking because the caller count turned out larger than the plan stated: all ten existing call sites live in the five declared paths (three production sites in `runner_shared.py`/`oc_runipd.py`/`agy_runipd.py`, and all ten test call sites in the declared `tests/test_run_flag_surface.py`). `grep -rln` over `tests/` finds no other module referencing `resolve_retry_budget` or `freeze_run_policy_flags`, so the signature change cannot reach an undeclared file. No new path is needed.
- Scope-Paths justification: `agent_workflows/config.py` holds the two precedent keys and their readers/accessors (`:1044`, `:1047`, `:1072`, `:1097`, `:1106`, `:1130`) and the convention note (`:1086-1089`) that E-02 follows; `agent_workflows/runner_shared.py` holds `resolve_retry_budget` (`:1987`) and its docstring gap statement (`:1990-1993`), the `--retry-budget` row and help (`:1889-1903`), `RETRY_BUDGET_OWNER` (`:1915`), `freeze_run_policy_flags` (`:2058`, retry branch `:2078-2079`) and `refuse_frozen_flags_on_resume` (`:2034`); `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` hold the two call sites (`:2783`, `:1792`) that must pass the repo root and the state writes that freeze the value (`:3059`, `:2017`); `tests/test_run_flag_surface.py` holds `RetryBudgetTests`, the bound-delegation test (`:628-639`) that must stay green and unweakened, and the help-honesty test (`:288-291`) that E-04 must update.
- Under-scope, stated rather than left as `none`: this plan does not spend the budget, does not touch `run_recovery.py`, does not touch `--integration-retry-limit`, does not edit `project_schema.py` or `CONFIG_SCHEMA`, does not change the resume freeze, does not add policy tiers to other flags, does not mutate the real project config, and amends no spec.

## Required tests / validation

- EIGHT FIXTURE CASES (E-05), each named with pasted output: CLI over policy; policy over default; default when neither; no config file at all; out-of-range policy; malformed policy; resume with a changed policy keeping the frozen value; and (h) the FROZEN value in `state["options"]` is the policy value rather than `2`.
- CASE (h) IS NOT OPTIONAL POLISH. The two driver calls discard their result, so a change that resolves correctly but never reaches the freeze path is observationally identical to doing nothing while passing cases (a) to (g).
- THE PRECEDENCE GUARD AND THE FREEZE GUARD QUOTED SEPARATELY, since those two are what a careless implementation breaks.
- PRODUCTION-CALL-SITE PROOF (E-06): all three production calls pass a repo root, asserted by source inspection in the manner of `tests/test_run_flag_surface.py:642-649`. With an optional parameter (OQ-04) this is the only guard against the middle tier silently not existing.
- BOUND-DELEGATION PROOF: `tests/test_run_flag_surface.py:628` green and NOT weakened; if it needed adjusting for the new parameter, state exactly what changed and why the assertion is intact. It inspects the source after the last `"""` for the literal `10`, so also confirm your key name and any new comment below the docstring do not contain `10`.
- NO-LITERAL-BOUND PROOF: show the new code contains no `0`/`10` comparison and routes the policy value through `run_recovery.validate_retry_budget`.
- SINGLE-DEFAULT PROOF: show `DEFAULT_RETRY_LIMIT` is still read rather than copied, and that `RETRY_BUDGET_OWNER`'s claim remains true.
- DOCSTRING PROOF: paste the corrected `resolve_retry_budget` docstring, since the current one asserts the gap this plan closes.
- HELP TEXT PASTED BEFORE AND AFTER, showing the `dh3us4` disclosure removed, the three-tier precedence stated, the config key NAMED, and the resume sentence kept. Plus the help-honesty test still protecting the remaining unimplemented row (`--follow-generated`, backlog `x8diyb`).
- FROZEN OPTIONS SHAPE UNCHANGED, so `xipfy1`'s consumption premise holds whether or not it has landed.
- `run_recovery.py` BYTE-UNCHANGED (`git diff` pasted), and `--integration-retry-limit` untouched.
- NEGATIVE PROOF THAT THE REAL CONFIG WAS NOT MUTATED: `git status --porcelain .aw/config/` clean.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set, with the counts you actually observed. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Do not add `-n0`, a second `-q`, or `-p no:randomly`; the configured `addopts` already supply the right flags and a second `-q` suppresses the `N passed` line you must paste.
- FOR CONTEXT ONLY, NOT AS A BASELINE TO QUOTE: at review HEAD `c8461ef5` a bare run measured `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks 189 files in a GITIGNORED `opencode-recovery/` directory of 1746 files belonging to ANOTHER PARTY. Measure your own; this is recorded only so you recognize it. DO NOT DELETE, MOVE, OR MODIFY `opencode-recovery/` to green the suite: that is another party's uncommitted data in a shared checkout.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC AMENDMENT IS NEEDED, and no `.spec.md` path is declared. Spec `25kzda` already specifies the three-tier chain correctly at `:158` and as invariant A2 at `:118`; the code is what lags, and this plan makes the code match an `approved` spec. If the executor finds the spec cannot be honored as written, STOP and report rather than relaxing an approved requirement to fit an implementation.

THE KEY's NAME AND FAILURE POSTURE MUST BE DOCUMENTED WHERE THE OTHER TWO ARE, in `config.py` beside `dependency_schema_cutover` (`:1044`) and `review_findings_gate` (`:1097`), including the sentence that says WHY it is not in `CONFIG_SCHEMA`, the way `:1086-1089` already does. Otherwise the next person adding a policy key finds three keys and two conventions.

THE OPERATOR-FACING DOCUMENTATION IS THE HELP TEXT and it is a deliverable, not an afterthought (E-04). It currently discloses the gap accurately; afterwards it must state the real precedence and NAME the config key, because a repository owner who wants a standing override needs to know what to write and where. There is no other surface that tells them. Write no em or en dashes there.

IF `.aw/config/project.json` HAS OPERATOR DOCUMENTATION ELSEWHERE (a README or a wizard prompt), check whether it enumerates recognized keys, and if it does, add this one. If it does not, do NOT create such a document as part of this plan; report the absence instead, since two prior keys shipped without one and inventing a new documentation surface here would be an unreviewable widening.

## Open questions

### OQ-01: Fail-open or fail-closed on a bad policy value?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-004
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE. This is the reviewer's third option, taken over both of the plan's original two. Fail-closed was declined on blast radius; silent fallback was declined because a repository that believes it set a policy would be overridden with no signal anywhere.
  THE PLAN'S PREMISE WAS FALSE AND STAYS RECORDED AS SUCH: it claimed the repository has "shipped BOTH postures". Re-verified at HEAD `0c655b28`, it has shipped exactly ONE. `read_dependency_schema_cutover` (`config.py:1047-1069`) returns None on any error. `findings_gate_threshold` (`:1130-1145`) returns `REVIEW_GATE_DEFAULT` on an absent key, a non-string value AND an out-of-vocabulary token, never raising, and its docstring frames that as landing "on the SAFE side". So there was no precedent to follow and the executor would have had to invent the answer mid-flight.
  BOTH SIDES OF THE ARGUMENT WERE MEASURED, not asserted. FOR REFUSING: an out-of-range `--retry-budget` on the CLI genuinely does refuse, raising `RunFlagRefusal` (`runner_shared.py:2102-2105`), so ignoring the identical value from config is an inconsistency an operator cannot predict. AGAINST REFUSING: `.aw/config/project.json` is TRACKED (`git ls-files` confirms it), so one typo would refuse EVERY run for every human and agent in the checkout until someone fixes and commits it, whereas a bad CLI value harms only the invocation that typed it.
  AND THE USUAL TIE-BREAKER GENUINELY DOES NOT APPLY, which is why this needed a human: "fail toward safety" settles the gate-threshold key easily because a stricter threshold IS the safe side, but a retry budget has no safe side, since a higher and a lower budget are merely different rather than safer. So the choice was a judgement about which failure is worse, not a derivation.
  THIS IS A THIRD POSTURE AND MUST BE WRITTEN DOWN AS THE PRECEDENT, not left as a one-off. The executor MUST record, at the implementation site, that a malformed value in this shared tracked file falls back AND warns, so the next key added to `project.json` follows it rather than re-deriving the question. Neither existing key warns today only because neither had a reason to; that is not an argument against warning.
  WHAT THE WARNING MUST CONTAIN, so it is actionable rather than noise: the key's name, the offending value as read, the default being used instead, and the file it came from. A warning that says only "invalid config" reproduces the silent-override problem one step removed.
  DO NOT RAISE `RunFlagRefusal` FROM THE CONFIG PATH, and do not make the CLI path fall back to match: the asymmetry is now DELIBERATE (a per-invocation mistake refuses, a shared-file mistake warns and continues) and is exactly what the maintainer chose. Record that asymmetry rather than "fixing" it later.

### OQ-02: What should the key be called and what shape should its value take?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A RULE, with the concrete name left to E-01 because it is a naming choice, not a design one. The value is a BARE INTEGER, not an object or a string, because the CLI value it overrides is `kind="int"` (`runner_shared.py:1892`) and the bound it must satisfy is an integer range owned by `validate_retry_budget`; any richer shape would need its own parser for no benefit. The name follows the two precedents' snake_case top-level style (`dependency_schema_cutover`, `review_findings_gate`) and should name the THING rather than the flag, so it reads as repository policy rather than as a CLI mirror. Deliberately rejected: nesting it under a `run` or `retry` object, since neither precedent nests and introducing a nesting convention for one key would leave the file with two shapes.

### OQ-03: Is this worth doing before the budget is ever spent?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND HONEST, because the measurement cuts against the item's own urgency argument and a maintainer should see it. The item argues the missing tier "only matters once a repository wants a standing override different from 2", which presumes the other two tiers work. But the budget is NEVER SPENT today: `plan_retry` (`run_recovery.py:269`) and `retry_budget_remaining` (`:415`) have no production callers, and closing that gap is `xipfy1`'s job. So until `xipfy1` lands, this tier is observationally inert: it will resolve a different number that nothing acts on. Two defensible conclusions follow.   EITHER land it now, because it is small, it is spec-mandated, it completes an `approved` requirement, and it is strictly easier to add before `xipfy1`'s consumer exists than after. OR park it until consumption ships, because an inert feature cannot be validated end to end and its tests can only assert resolution, not effect. This plan is written for the first reading (which is also why `Item-Dependencies` is `none`), but it does not pretend the second is unreasonable. Non-blocking because the work is correct under either answer; only its priority moves.
  CONFIRMED AT REVIEW AND NOT WEAKENED. `plan_retry` and `retry_budget_remaining` still have no production callers (verified at HEAD `c8461ef5`), `xipfy1` is still only `to-review`, so the inertness is real and the plan is right to say so plainly against its own source item. This question is left with the maintainer rather than resolved, because it is purely a PRIORITY call and priority is theirs; it stays `Blocking: no` because neither answer changes a single line of the work. One consequence worth stating for the decision: E-05's cases can prove RESOLUTION completely and can prove EFFECT not at all, so if the maintainer wants end-to-end evidence, this plan should follow `xipfy1` rather than precede it.

### OQ-04: Should the new repo-root parameter be optional or required?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW AS A RECOMMENDATION WITH A MANDATORY GUARD, because the plan never raised the question although it decides how much of the suite the change touches. Measured: there are TEN existing call sites, not the three the plan named. `tests/test_run_flag_surface.py` calls `resolve_retry_budget` six times (`:608`, `:611`, `:615`, `:618`, `:619`, `:625`) and `freeze_run_policy_flags` four times, all with today's signature, and no other test module references either symbol.
  RECOMMENDED: an OPTIONAL keyword-only parameter defaulting to "no repo root, therefore no policy tier". It keeps all six existing `resolve_retry_budget` assertions valid AND MEANINGFUL (they are pure-function tests of CLI-over-default, which remains a real code path), keeps the four freeze-path tests green, and keeps the function callable at parse time where no repo may be known. A required parameter would force ten edits, several of them to assertions that are correct as written, and would turn a small change into a wide diff for no behavioral gain.
  THE HONEST COST, which is why the recommendation carries an obligation rather than standing alone: with an optional parameter, a production caller that FORGETS the root silently falls back to CLI-over-default and the middle tier does not exist, while every unit test stays green because they call the function directly. That failure is invisible to exactly the tests this plan adds. So E-06 MUST assert that all three production call sites pass a root, following the pattern `test_an_out_of_range_value_refuses_the_whole_run` (`:642-649`) already uses to inspect `initialize_run`'s source, and E-05 case (h) MUST prove the frozen value in `state["options"]` is the policy value rather than the default.
  NOT PRESCRIPTIVE ON THE SPELLING: keyword-only versus positional-with-default, and `repo_root` versus another name, are the executor's. The binding parts are that existing call sites keep working, the parameter cannot be silently omitted in production without a test failing, and the name does not contain the substring `10` (F-17).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: QUOTE THE MAINTAINER'S OQ-01 ANSWER VERBATIM WITH ITS DATE. This is an attested decision, not an implementer's preference: do NOT paste your own reasoning in place of an answer, and do not proceed if OQ-01 is still `open` (it is `Blocking: yes`, so `aw ipd lint` refuses execution while it is).
    Then state the chosen key name, its value shape, and paste the accessor docstring recording the posture and its reasoning. CONFIRM THE KEY NAME DOES NOT CONTAIN THE SUBSTRING `10` (F-17), and say which of the two precedents' STRUCTURE you mirrored while noting that neither supplies the failure posture (F-16).
  - Observed evidence: THE MAINTAINER'S OQ-01 ANSWER, QUOTED VERBATIM WITH ITS DATE from OQ-01 of this plan: "RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE. This is the reviewer's third option, taken over both of the plan's original two. Fail-closed was declined on blast radius; silent fallback was declined because a repository that believes it set a policy would be overridden with no signal anywhere." OQ-01's `- Status:` reads `resolved`, so the `Blocking: yes` gate is satisfied and execution is permitted.
    KEY NAME AND SHAPE: `run.retry_budget`, a BARE INTEGER (`RUN_POLICY_KEY = "run"` plus `RUN_RETRY_BUDGET_MEMBER = "retry_budget"`, `config.py`). THE NAME IS SPEC-DICTATED AND THIS IS A CORRECTION TO OQ-02, recorded rather than silently followed: OQ-02 ruled for a flat top-level snake_case name and explicitly "deliberately rejected: nesting it under a `run` or `retry` object". Measured at execution, spec `25kzda` 5.5 (`:1036`) NAMES THE PATH: "Retry budget precedence is: 1. `--retry-budget N` ...; 2. repository policy `run.retry_budget`; 3. default `2`." The spec is `approved` and OQ-02 did not cite it, so honoring `run.retry_budget` is not a style preference; inventing a flat name would have shipped code that does not implement the approved spec it claims to complete. The flat form `{"retry_budget": N}` is ALSO accepted as a convenience shape (both precedents tolerate one), so a repository owner writing the obvious flat key is not silently ignored. OQ-02's binding parts are all honored: a BARE INTEGER, not an object or string, and no new nesting convention is invented (the nesting is the spec's).
    THE KEY NAME CONTAINS NO `10` (F-17): `run.retry_budget` - verified, no digits at all. That constraint turned out to be MOOT rather than merely satisfied, and the correction matters for future readers: F-17 described `test_the_bound_is_sq61qds_and_is_not_re_checked_here` as a SOURCE-TEXT pin asserting the literal `10` is absent after the last `"""`. At execution HEAD `58876f1b` that test has been REWRITTEN to be behavioral (it patches `run_recovery.validate_retry_budget` and `DEFAULT_RETRY_LIMIT` with sentinels and requires this layer's answer to change), and its own docstring records why the old text pin was deleted as "actively misleading". So no source-text constraint on the name exists any more. It was satisfied anyway.
    STRUCTURE MIRRORED: `review_findings_gate`'s, as E-01 directed - a module constant for the key (`REVIEW_FINDINGS_GATE_KEY` -> `RUN_POLICY_KEY`), a reader returning the raw object with every error swallowed (`read_review_findings_gate` -> `read_run_policy`), and an accessor applying the default (`findings_gate_threshold` -> `policy_retry_budget`).
    NEITHER PRECEDENT SUPPLIES THE FAILURE POSTURE (F-16), CONFIRMED BY RE-READING BOTH at execution: `read_dependency_schema_cutover` (`config.py:1047-1069`) returns None on any error, and `findings_gate_threshold` (`:1130-1145`) returns `REVIEW_GATE_DEFAULT` on an absent key, a non-string value AND an out-of-vocabulary token and never raises. Both are SILENT. This key is therefore a THIRD posture - fall back AND WARN - and per OQ-01 it is written down AT THE IMPLEMENTATION SITE as the precedent for the next key, in the section comment above `RUN_POLICY_KEY`.
    THE ACCESSOR DOCSTRING, pasted from `config.py`:
    ```
        """Spec 5.5's repository-policy retry budget, or None when this repository sets no policy.

        Returns the RAW integer as written. The 0..10 bound is NOT applied here: it has a single
        definition in `run_recovery.validate_retry_budget` and the caller
        (`runner_shared.resolve_retry_budget`) reaches it, so this layer cannot grow a second copy of it.

        READ FROM `run.retry_budget`, which is the path spec 25kzda 5.5 names. A BARE top-level integer
        under the same member name is also accepted, because a repository owner writing the obvious flat
        form should not be silently ignored; both precedents in this file tolerate a convenience shape
        the same way.

        FALLS BACK AND WARNS ON A MALFORMED VALUE, never raising (maintainer decision, 2026-09-10; see
        the section comment above for the full reasoning and for why the asymmetry with the refusing CLI
        flag is deliberate). A non-integer, a `bool`, or an unparseable value returns None, so the caller
        applies the default, AND emits one warning naming the key, the offending value, and the file, so
        the override is visible rather than silent. `warn` exists for tests and defaults to stderr.
        """
    ```
    AND THE VALUE IS ROUTED THROUGH `validate_retry_budget`, not compared locally: the accessor returns the RAW integer and `resolve_retry_budget` calls the shared validator on it, proven behaviorally by `test_the_policy_value_is_validated_by_sq61qds_single_definition` (sentinel 99 appears, so the shared bound was reached).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new key constant, reader and accessor from `config.py`, and show by side-by-side comparison that the shape mirrors `read_review_findings_gate`/`findings_gate_threshold`. Paste `git diff` over `project_schema.py` proving it is byte-unchanged. Paste passing evidence for all three absent cases: no config file, file without the key, null value.
  - Observed evidence: THE KEY CONSTANT, READER AND ACCESSOR, pasted from `agent_workflows/config.py`:
    ```
    RUN_POLICY_KEY = "run"

    #: The member of the `run` object holding spec 5.5's repository-policy correction budget.
    RUN_RETRY_BUDGET_MEMBER = "retry_budget"


    def read_run_policy(
        repo_root: "os.PathLike[str] | str",
    ) -> Optional[Dict[str, Any]]:
        """Return the `run` policy object from `.aw/config/project.json`, or None if unset.

        Never raises: a missing file, unparseable JSON, a non-object document, or a missing key returns
        None (the caller then applies its own default). Pure read; never writes.
        """
        project_file = Path(repo_root) / ".aw" / "config" / "project.json"
        try:
            data = json.loads(project_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        raw = data.get(RUN_POLICY_KEY)
        return raw if isinstance(raw, dict) else None
    ```
    The accessor `policy_retry_budget(repo_root, *, warn=None)` follows it (its docstring is pasted in V-01); its body reads `run.retry_budget`, falls back to the flat form, returns None for an explicit null, returns the raw int, and otherwise emits one warning naming the key, the value and the file before returning None.
    SIDE-BY-SIDE WITH THE MODEL, showing the shape is mirrored rather than reinvented:
    | `review_findings_gate` (shipped model) | this key |
    |---|---|
    | `REVIEW_FINDINGS_GATE_KEY = "review_findings_gate"` (`:1097`) | `RUN_POLICY_KEY = "run"` + `RUN_RETRY_BUDGET_MEMBER = "retry_budget"` |
    | `read_review_findings_gate` (`:1106`): builds `Path(repo_root)/".aw"/"config"/"project.json"`, `json.loads` in `try/except (OSError, ValueError)` -> None, `isinstance(data, dict)` guard, `data.get(KEY)`, tolerates a convenience shape | `read_run_policy`: byte-for-byte the same four steps, same exception tuple, same dict guard |
    | `findings_gate_threshold` (`:1130`): reads the marker, applies the DEFAULT for absent/wrong-type/invalid, never raises | `policy_retry_budget`: reads the marker, returns None (caller applies the default) for absent/null/wrong-type, never raises, and ADDITIONALLY warns on a malformed value (the one deliberate divergence, per OQ-01) |
    | default lives in `config.py` (`REVIEW_GATE_DEFAULT`) | default deliberately NOT here: it is `run_recovery.DEFAULT_RETRY_LIMIT`, single-defined, so this accessor returns None rather than copying `2` |
    `project_schema.py` IS BYTE-UNCHANGED, `git diff` pasted (empty output is the evidence):
    ```
    $ git diff -- agent_workflows/project_schema.py
    [end]
    ```
    ALL THREE ABSENT CASES PASS, run on throwaway repos (from the E-05 table, `test_every_policy_document_resolves_to_the_right_tier`, and reproduced directly):
    ```
    CASE (c) neither present       -> 2      # {"schema_version": 2}, a file with no run key
    CASE (d) no config file at all -> 2      # no .aw/config/project.json exists
             explicit null policy  -> 2      # {"run": {"retry_budget": null}}
             DEFAULT_RETRY_LIMIT   -> 2
    ```
    None raised, and none warned (asserted as a column in the table: a warning on a NORMAL absence fails the row).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the changed `resolve_retry_budget` in full, showing the precedence order and showing the bound is reached via `run_recovery.validate_retry_budget` with NO literal `0` or `10` comparison and the default read from `DEFAULT_RETRY_LIMIT` rather than copied. Paste the corrected docstring (the old one asserts the gap).
    STATE THE OQ-04 CHOICE (optional or required parameter) and paste the signature.
    PASTE ALL THREE PRODUCTION CALL SITES passing the root, and paste the comment distinguishing WHY each gets it: the two `initialize_run` calls discard their result and exist for the early refusal, while `freeze_run_policy_flags` is the only call whose result is kept (F-14). A V-03 that pastes two call sites, or that treats all three as the same job, has not validated this item.
    Paste evidence the resume refusal is unchanged, and note that `apply_run_policy_flags_on_resume` skips `RESUME_REFUSE` rows so no resume path may consult config (F-20).
  - Observed evidence: THE CHANGED `resolve_retry_budget` IN FULL, pasted from `agent_workflows/runner_shared.py` (re-located BY SYMBOL, as E-03 directs; see the drift note below):
    ```
    def resolve_retry_budget(
        cli_value: Any,
        *,
        repo: Any = None,
        warn: Any = None,
    ) -> int:
        """Spec 2.1's retry-budget precedence, and the ONE place the range bound is reached.

        ALL THREE TIERS SHIP: per spec 2.1 and 5.5 the precedence is CLI over repository policy over the
        default of 2. The middle tier is `config.policy_retry_budget`, reading spec 5.5's
        `run.retry_budget` from the committed `.aw/config/project.json`.

        `repo` IS OPTIONAL BY DESIGN AND ITS ABSENCE MEANS "NO REPOSITORY KNOWN, THEREFORE NO POLICY
        TIER" (plan `y4adch` OQ-04). The function must stay callable at PARSE time, where a repo may not
        be resolved yet, and the pure CLI-over-default path remains a real code path with its own
        assertions. THE HONEST COST is that a production caller which FORGETS `repo` silently falls back
        to CLI-over-default with every unit test still green, so a contract test asserts the production
        call sites pass it.

        THE MIDDLE TIER IS ONLY CONSULTED WHEN NO CLI VALUE WAS PASSED, which is what makes `--retry-budget
        0` mean zero rather than "unset": the guard is `is None`-shaped, never truthy, because `0` is a
        legal budget (spec 5.5).

        THE TWO FAILURE POSTURES ARE DIFFERENT ON PURPOSE (maintainer decision, 2026-09-10). A bad CLI
        value RAISES `RunFlagRefusal` and stops the one invocation that typed it. A bad POLICY value falls
        back to the default AND WARNS, naming the key and the value, because `.aw/config/project.json` is
        tracked and shared, so refusing would break every run in the checkout over one typo. Do not
        "fix" that asymmetry into symmetry: it is the decision, not an oversight.

        The 0..10 bound is `run_recovery.validate_retry_budget`'s, CALLED and never re-checked here -
        including for the policy value, which is validated through the same single definition so the
        bound cannot differ between a flag and a config key. Executed plan `sq61qd` made that the single
        definition precisely so the flag layer could reach it at PARSE time, when no `RunEngine` and no
        step exist. A second comparison here is the off-by-one that gets fixed in one place.
        """

        from agent_workflows import run_recovery

        if cli_value is not None:
            try:
                return run_recovery.validate_retry_budget(cli_value)
            except run_recovery.InvalidRetryBudgetError as exc:
                raise RunFlagRefusal(f"--retry-budget: {exc}") from exc

        if repo is not None:
            from agent_workflows import config as _config

            policy_value = _config.policy_retry_budget(repo, warn=warn)
            if policy_value is not None:
                try:
                    return run_recovery.validate_retry_budget(policy_value)
                except run_recovery.InvalidRetryBudgetError as exc:
                    message = (
                        f"WARNING: {_config.RUN_POLICY_KEY}.{_config.RUN_RETRY_BUDGET_MEMBER} in "
                        f"{Path(repo) / '.aw' / 'config' / 'project.json'} is out of range: {exc}. "
                        f"Ignoring it and using the default retry budget "
                        f"({run_recovery.DEFAULT_RETRY_LIMIT}) instead. Fix the value in that file to "
                        f"make the repository policy take effect."
                    )
                    if warn is None:
                        print(message, file=sys.stderr)
                    else:
                        warn(message)

        return run_recovery.DEFAULT_RETRY_LIMIT
    ```
    PRECEDENCE ORDER IS CLI -> POLICY -> DEFAULT, readable in the control flow above and measured (V-05 has the full table): CLI `4` beats policy `9` -> `4`; policy `9` with no CLI -> `9`; neither -> `2`.
    NO LITERAL `0` OR `10` COMPARISON EXISTS. Both tiers reach the bound the same way, by calling `run_recovery.validate_retry_budget`; there is no `<`, `>`, `<=` or `>=` anywhere in the function. THE DEFAULT IS READ, NOT COPIED: `run_recovery.DEFAULT_RETRY_LIMIT` appears as the returned expression, and the literal `2` appears nowhere in the function. `RETRY_BUDGET_OWNER`'s claim ("read FROM `run_recovery.DEFAULT_RETRY_LIMIT` at call time") therefore remains true and it was not edited.
    THE DOCSTRING IS CORRECTED, which was required because the OLD one asserted the gap this plan closes. Before: "The MIDDLE TIER IS NOT IMPLEMENTED and is not faked here: no repository-policy home exists (backlog `dh3us4` tracks it), so this resolves CLI-over-default and the gap is stated in `--retry-budget`'s own `--help`". After: "ALL THREE TIERS SHIP ... The middle tier is `config.policy_retry_budget`, reading spec 5.5's `run.retry_budget`". Leaving it would have made the code lie about itself.
    OQ-04 CHOICE: OPTIONAL, keyword-only, as OQ-04 recommended. Signature: `def resolve_retry_budget(cli_value: Any, *, repo: Any = None, warn: Any = None) -> int:`. WHY: the resolver must stay callable at parse time where no repo is resolved, and every existing pure call site stays valid and meaningful. `warn` is a second keyword-only injection point, added for testability so a test can capture the warning rather than scraping stderr. THE MANDATORY GUARD IS IN PLACE: `test_the_production_call_sites_pass_a_repo_root` (AST-based) fails if the production freeze call omits `repo=`.
    THE PRODUCTION CALL SITES, AND A MATERIAL CORRECTION TO F-14/F-18 FOUND AT EXECUTION. The plan names three production sites in three files (`runner_shared.freeze_run_policy_flags`, `oc_runipd.py:2783`, `agy_runipd.py:1838`). MEASURED AT EXECUTION HEAD `58876f1b`, THE TWO PER-HOST CALL SITES NO LONGER EXIST: `initialize_run` has been UNIFIED into `runner_shared.initialize_run_core`, and both hosts' `initialize_run` now delegate to it (`oc_runipd.py:3401`, `agy_runipd.py:2167`). `grep -n "resolve_retry_budget" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returns NOTHING. So the drift F-18 measured at about 97 lines has since become a STRUCTURAL change, not a line-number change, and the three sites are now three calls inside ONE file. THIS IS WHY `oc_runipd.py` AND `agy_runipd.py` ARE UNCHANGED BY THIS PLAN despite being declared in `Scope-Paths`: there was nothing left in them to thread. The declared paths remain correct as declared scope; under-use of a declared path is not over-scope. The three sites, pasted:
    1. THE EARLY REFUSAL (result DISCARDED), `initialize_run_core`:
    ```
        # Refuse an unhonorable flag BEFORE resolution, and note what this call is NOT: its return value
        # is DISCARDED, so it decides nothing. It exists only for the `RunFlagRefusal` side effect, which
        # fires here so a bad CLI value is refused before any run directory exists.
        # `repo` IS DELIBERATELY NOT PASSED, and that is a consequence of OQ-01's answer rather than an
        # omission. A malformed repository-POLICY value never refuses (it falls back and warns, because
        # `.aw/config/project.json` is tracked and shared), so handing this call a root could not make it
        # refuse anything; it could only emit the same warning a SECOND time, since the call that keeps
        # the value (`freeze_run_policy_flags`, below) already warns. One bad value, one warning.
        resolve_retry_budget(getattr(args, "retry_budget", None))
    ```
    THIS IS A DELIBERATE DEPARTURE FROM E-03's LETTER AND IT IS RECORDED AS D-02 IN THE DECISIONS REGISTER. E-03 says to thread the root into ALL THREE sites so "a malformed POLICY value is refused as early as a malformed CLI value", and adds the conditional "(only meaningful if OQ-01 answers fail-closed)". OQ-01 answered FALL BACK AND WARN, so E-03's own stated purpose for this site is void: passing a root here cannot refuse anything, and would only duplicate the warning. E-03's actual hazard ("passing it to only the driver calls would refuse correctly and then freeze the wrong value") is fully avoided, since the site that keeps the value DOES get the root.
    2. THE FREEZE (the ONLY call whose RESULT is kept), `initialize_run_core`:
    ```
                # `repo=repo` is load-bearing: this is the ONLY `resolve_retry_budget` call whose RESULT
                # is kept, so it is the only one that can put spec 5.5's repository-policy tier into
                # durable run state. Drop it and a repository's `run.retry_budget` is silently ignored
                # while every unit test stays green, which is what `test_the_production_call_sites_pass_a_repo_root`
                # exists to catch.
                **freeze_run_policy_flags(args, repo=repo),
    ```
    3. THE ORCHESTRATOR PROBE GATE (a THIRD kept-result site the plan did not know about, also found at execution), `initialize_run_core`:
    ```
            # `repo=repo` for the same reason the freeze call gets it: this result is USED (it is the
            # probe's own correction budget), so a repository policy of `0` must reach the probe rather
            # than the probe silently spending the default of 2. `warn=lambda _m: None` suppresses a
            # SECOND warning for one bad value: the freeze call above has already emitted it, and
            # repeating it here would print the same complaint twice per run.
            retry_budget=resolve_retry_budget(
                getattr(args, "retry_budget", None), repo=repo, warn=lambda _message: None
            ),
    ```
    So the REFUSAL-VERSUS-VALUE distinction F-14 demanded is stated in a comment at each site, and it now separates THREE sites into one refusal-only and TWO value-keeping, rather than the plan's two-and-one. `repo` is bound at the top of `initialize_run_core` (`repo = Path(args.repo).expanduser().resolve()`), so it is in scope at all three.
    THE RESUME REFUSAL IS UNCHANGED, and no resume path may consult config. `git diff` touches neither `refuse_frozen_flags_on_resume` nor `apply_run_policy_flags_on_resume`; the `--retry-budget` row still carries `resume_rule=RESUME_REFUSE` (unchanged in the diff). F-20's structural property re-verified by reading `apply_run_policy_flags_on_resume`: it SKIPS every `RESUME_REFUSE` row and never re-resolves, so a resume reads the frozen integer and has no code path reaching `config`. Asserted behaviorally, not assumed, by `test_a_changed_policy_cannot_move_the_frozen_value_on_resume` (freeze 3, change the repository policy to 9, resume still reports 3 through both `state["options"]` and `frozen_retry_budget`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `--retry-budget`'s help BEFORE and AFTER, showing the `dh3us4`/`NOT IMPLEMENTED` disclosure gone, the three-tier precedence stated, the config key NAMED, and the resume sentence retained. Paste the updated help-honesty test and show it still protects the remaining unimplemented row (`--follow-generated`, naming `x8diyb`).
  - Observed evidence: `--retry-budget`'s HELP, BEFORE (from `git show HEAD:agent_workflows/runner_shared.py`):
    ```
    Automatic correction attempts after the initial attempt, an integer 0..10 inclusive (0 means no
    retries). The CLI value overrides the default of 2. NOTE: spec 2.1's MIDDLE precedence tier
    (repository policy) is NOT IMPLEMENTED - no repository-policy home exists yet (backlog dh3us4) -
    so precedence today is CLI over default. Cannot be changed on --resume: the frozen value stands
    ```
    AFTER, read from the live table (`RUN_POLICY_FLAGS_BY_FLAG['--retry-budget'].help`), which is the same string the rendered-help assertion compares against `action.help` on both hosts' real parsers:
    ```
    Automatic correction attempts after the initial attempt, an integer 0..10 inclusive (0 means no
    retries). Precedence is THREE-TIER: this CLI value overrides repository policy, and repository
    policy overrides the default of 2. Repository policy is the integer at run.retry_budget in
    .aw/config/project.json, so a repo wanting a standing override writes {"run": {"retry_budget": 4}}
    there. A malformed or out-of-range POLICY value does NOT refuse: it warns, names the key and the
    value, and the default applies, because that file is shared; an out-of-range value passed HERE
    does refuse. Cannot be changed on --resume: the frozen value stands
    ```
    CHECKED ITEM BY ITEM: the `dh3us4` / `NOT IMPLEMENTED` disclosure is GONE (`grep -c dh3us4` over `agent_workflows/` is now 0); the THREE-TIER precedence is stated in order; the config key is NAMED (`run.retry_budget` in `.aw/config/project.json`) together with a copy-pasteable document, because `--help` is the only surface a repository owner has; the resume sentence is RETAINED verbatim; and the asymmetric failure posture is disclosed, since an operator who assumes symmetry gets it wrong in both directions.
    THE HELP-HONESTY TEST IS UPDATED, not deleted. Two rows asserted the gap (`NOT IMPLEMENTED` and `dh3us4`); keeping either would now demand that shipped behavior be reported as absent. They are REPLACED by two rows that assert what an operator needs NOW, each carrying its own "this row exists because" rationale in the table: `run.retry_budget` (the key itself, since the help is the only place it is documented) and `does NOT refuse` (the deliberate CLI-versus-config asymmetry). Net: the row COUNT is unchanged, the flag is still covered, and the token pins still follow the file's stated rule of pinning only backlog ids and other flags/keys an operator must know rather than ordinary prose.
    THE REMAINING UNIMPLEMENTED ROW IS STILL PROTECTED, and it is protected DERIVED rather than by name (the loop selects `not row.implemented`, so I could not have weakened it for one flag without weakening it for all):
    ```
    $ python3 -c "...for r in rs.RUN_POLICY_FLAGS: if not r.implemented: print(...)"
    --follow-generated | NOT YET IMPLEMENTED: True | x8diyb: True
    ```
    ```
    $ python3 -m pytest tests/test_run_flag_surface.py::HelpHonestyTests -o addopts="" -v
    tests/test_run_flag_surface.py::HelpHonestyTests::test_every_help_string_carries_the_tokens_an_operator_needs PASSED [100%]
    ============================== 3 passed in 0.28s ===============================
    ```
    (That run also carries `RetryBudgetTests`' two tests; its own class-only run is in V-05.)
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of all EIGHT cases. QUOTE the CLI-over-policy assertion and the resume-with-changed-policy assertion separately as the two guards.
    PASTE CASE (h) SEPARATELY TOO: the frozen `state["options"]["retry_budget"]` equals the POLICY value, not `2`, obtained through `freeze_run_policy_flags` against a fixture repo whose policy is set. Cases (a) to (g) can all pass against a resolver whose result never reaches the freeze path, so without (h) this validation cannot distinguish a working middle tier from an inert one.
    Paste `tests/test_run_flag_surface.py`'s own summary line green, and if `test_the_bound_is_sq61qds_and_is_not_re_checked_here` was adjusted, paste the before and after and state why the assertion is intact rather than weakened. If you did NOT need to adjust it, say so and confirm your key name and post-docstring text contain no literal `10`.
    Paste `git status --porcelain .aw/config/` clean.
  - Observed evidence: ALL EIGHT CASES PASS. The fixture cases live in the new `RepositoryPolicyRetryTierTests` in the declared `tests/test_run_flag_surface.py`, and the ACTUAL passing output is:
    ```
    $ python3 -m pytest tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests -o addopts="" -v
    collected 7 items

    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_a_changed_policy_cannot_move_the_frozen_value_on_resume PASSED [ 14%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_the_frozen_value_that_reaches_run_state_is_the_policy_value PASSED [ 28%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_the_production_call_sites_pass_a_repo_root PASSED [ 42%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_the_policy_value_is_validated_by_sq61qds_single_definition PASSED [ 57%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_an_absent_repo_argument_means_no_policy_tier_and_never_reads_a_file PASSED [ 71%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_the_frozen_options_shape_is_unchanged PASSED [ 85%]
    tests/test_run_flag_surface.py::RepositoryPolicyRetryTierTests::test_every_policy_document_resolves_to_the_right_tier PASSED [100%]

    ============================== 7 passed in 0.26s ===============================
    ```
    AND REPRODUCED DIRECTLY ON THROWAWAY REPOS, so the values are readable rather than only asserted:
    ```
    CASE (a) CLI 4 over policy 7   -> 4
    CASE (b) policy 7 over default -> 7
    CASE (c) neither present       -> 2
    CASE (d) no config file at all -> 2
             DEFAULT_RETRY_LIMIT   -> 2
             zero policy is legal  -> 0
             flat convenience form -> 6
    --- CASE (e) policy out of range (11):
    WARNING: run.retry_budget in <tmp>/repo/.aw/config/project.json is out of range: invalid retry budget 11: must be an int in the inclusive range 0..10 (spec 25kzda 2.1). Ignoring it and using the default retry budget (2) instead. Fix the value in that file to make the repository policy take effect.
        returned: 2
    --- CASE (f) malformed policy (string):
    WARNING: run.retry_budget in <tmp>/repo/.aw/config/project.json is 'lots', which is not an integer. Ignoring it and using the default retry budget instead. Fix the value in that file to make the repository policy take effect.
        returned: 2
    --- CASE (f2) malformed policy (bool):
    WARNING: run.retry_budget in <tmp>/repo/.aw/config/project.json is True, which is not an integer. Ignoring it and using the default retry budget instead. Fix the value in that file to make the repository policy take effect.
        returned: 2
    --- THE ASYMMETRY: the identical 11 on the CLI must REFUSE:
        RunFlagRefusal: --retry-budget: invalid retry budget 11: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
    ```
    Cases (e) and (f) behave exactly as OQ-01 decided: fall back AND warn, with the key, the offending value as read, the default used instead, and the file all named. The final line is the deliberate asymmetry, measured rather than asserted.
    THE PRECEDENCE GUARD, CASE (a), QUOTED SEPARATELY (row 1 of the `CASES` table plus the assertion that consumes it):
    ```
            (
                "CLI value alongside a set policy",
                {"run": {"retry_budget": 9}},
                4,
                4,
                False,
                "CASE (a), THE PRECEDENCE GUARD. The CLI is the HIGHEST tier, so a policy must not win "
                "when a flag was passed. A resolver that consults config first, or that treats the "
                "policy as an override, inverts spec 2.1's chain and makes an explicit operator "
                "instruction lose to a committed file",
            ),
    ...
                got = runner_shared.resolve_retry_budget(cli, repo=repo, warn=warnings.append)
            if got != want:
                problems.append(f"resolved to {got!r}, expected {want!r}" ...)
    ```
    THE FREEZE GUARD, CASE (g), QUOTED SEPARATELY (`test_a_changed_policy_cannot_move_the_frozen_value_on_resume`):
    ```
                frozen = runner_shared.freeze_run_policy_flags(args, repo=repo)
                self.assertEqual(frozen["retry_budget"], 3, "precondition: the run froze the repository's policy value")
                state = {"options": dict(frozen)}
                self.write_policy(_P(td), {"run": {"retry_budget": 9}})
                runner_shared.apply_run_policy_flags_on_resume(state, resume_args)
                self.assertEqual(
                    state["options"]["retry_budget"], 3,
                    "the FROZEN budget must stand even though the repository's policy changed to 9 "
                    "since the run started (spec `:162`). A 9 here means a resume re-resolved from "
                    "config, so a run's retry budget could change under it between its first turn and "
                    "its last",
                )
                self.assertEqual(runner_shared.frozen_retry_budget(state), 3, "...")
    ```
    CASE (h), PASTED SEPARATELY, IS THE ONE THAT PROVES THE TIER IS NOT INERT. Asserted through `freeze_run_policy_flags` in `test_the_frozen_value_that_reaches_run_state_is_the_policy_value` (policy 7, frozen 7, plus an `assertNotEqual` against the default so the row cannot pass by coincidence), AND DRIVEN END TO END through both hosts' real `initialize_run` on a committed fixture repo whose `.aw/config/project.json` sets `{"run": {"retry_budget": 7}}`, reading the value back out of the persisted `state.json`:
    ```
    oc_runipd: state['options']['retry_budget'] = 7
    agy_runipd: state['options']['retry_budget'] = 7
    ```
    Seven, not two, on BOTH hosts, out of DURABLE run state. That is the evidence that distinguishes a working middle tier from one that resolves correctly and never reaches the number a run spends.
    `tests/test_run_flag_surface.py`'s OWN SUMMARY LINE, GREEN (the whole module, all classes):
    ```
    $ python3 -m pytest tests/test_run_flag_surface.py -o addopts="" -q
    ......................................................................   [100%]
    70 passed in 11.12s
    ```
    THE BOUND-DELEGATION TEST NEEDED NO ADJUSTMENT AND WAS NOT TOUCHED. `test_the_bound_is_sq61qds_and_is_not_re_checked_here` passes unmodified (`git diff` shows no change to it), which is possible because the new parameters are KEYWORD-ONLY with defaults, so its existing single-argument calls are still valid. Confirmed green in its own run:
    ```
    tests/test_run_flag_surface.py::RetryBudgetTests::test_the_bound_is_sq61qds_and_is_not_re_checked_here PASSED [ 66%]
    ```
    AND THE `10` CONSTRAINT IS CONFIRMED MOOT RATHER THAN MERELY MET: at execution HEAD that test is BEHAVIORAL (sentinel patching), not a source-text pin, so no post-docstring text constraint exists; the key name `run.retry_budget` contains no digits regardless. The full correction is recorded in V-01.
    THE REAL CONFIG WAS NOT MUTATED. Every fixture uses `tempfile.TemporaryDirectory`:
    ```
    $ git status --porcelain .aw/config/
    [end]
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the source-inspection assertion showing ALL THREE production call sites pass a repo root, and say why that guard is load-bearing under the OQ-04 choice you made (with an optional parameter, an omitted root silently disables the middle tier while every unit test stays green).
    Paste evidence the frozen `state["options"]` key set and the type of `retry_budget` are unchanged, and state whether `xipfy1` had landed and how its consumption is unaffected either way.
    Paste `git diff` over `run_recovery.py` showing it byte-unchanged. Confirm `--integration-retry-limit` is untouched, and confirm `project_schema.py` is byte-unchanged.
    THEN paste the BARE `python3 -m pytest` summaries before and after with the failure-set delta as a set and the counts you actually observed. If the pre-existing `tests/test_reporting_contract.py` failure appears, report it as pre-existing and CONFIRM you did not delete, move, or modify `opencode-recovery/`.
  - Observed evidence: THE PRODUCTION-CALL-SITE GUARD, pasted, from `test_the_production_call_sites_pass_a_repo_root`. It is AST-based rather than a source-text grep, which this module's own header requires (a comment satisfies a text pin, and these call sites now carry long comments ABOUT the repo argument, so a grep would pass on the prose alone):
    ```
            for runner in BOTH:
                source = _effective_init_source(runner)
                freeze_calls = [
                    node
                    for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.Call)
                    and ast.unparse(node.func).endswith("freeze_run_policy_flags")
                ]
                if not freeze_calls:
                    wrong.append(f"  {runner}: no `freeze_run_policy_flags` call was found ... VACUOUS ...")
                    continue
                for call in freeze_calls:
                    if not any(kw.arg == "repo" for kw in call.keywords):
                        wrong.append(
                            f"  {runner}: `{ast.unparse(call)}` does NOT pass `repo=`, so spec 5.5's "
                            "repository-policy tier is silently skipped and the DEFAULT is frozen while "
                            "a repository believes its `run.retry_budget` is in force"
                        )
    ```
    It runs over BOTH hosts through `_effective_init_source`, which follows the delegation into `runner_shared.initialize_run_core`, so the unification described in V-03 does not make it vacuous; a VACUOUS-GUARD branch fails loudly if the freeze call is ever moved or renamed.
    WHY IT IS LOAD-BEARING UNDER THE OQ-04 CHOICE I MADE: I chose the OPTIONAL keyword parameter, so a production call that omits `repo=` still compiles, still returns a legal integer, and silently reverts to CLI-over-default. Every other test in the new class passes a root EXPLICITLY, so all of them would stay green while the shipped middle tier did not exist. This guard and case (h) are the only two things that can see that failure, which is exactly the obligation OQ-04 attached to its recommendation.
    SCOPED TO THE FREEZE CALL DELIBERATELY: the early refusal call does NOT take a root (see V-03 and decision D-02), so asserting one there would pin a shape that accomplishes nothing under OQ-01's fall-back-and-warn answer.
    THE FROZEN OPTIONS' KEY SET AND VALUE TYPE ARE UNCHANGED, asserted by `test_the_frozen_options_shape_is_unchanged`: `set(freeze_run_policy_flags(args))` with no repo equals `set(freeze_run_policy_flags(args, repo=repo))` with a policy set, `retry_budget` is `assertIsInstance(..., int)` and `assertNotIsInstance(..., bool)`. So the frozen value is still ONE BARE INTEGER under the SAME KEY; only which number appears can differ.
    `xipfy1` HAD NOT LANDED at execution: it is `.aw/records/plans/pending/20260908-retrywire-01-xipfy1-...ipd.md` with `- Status: approved`. ITS CONSUMPTION IS UNAFFECTED EITHER WAY, which is why the property was asserted in that form: it reads the FROZEN budget from `state["options"]` and explicitly does not re-resolve ("Do NOT call `resolve_retry_budget` again in the loop"). Since the key and the type are unchanged, its premise still holds if it lands later, and `frozen_retry_budget` (the shipped reader it will use) was neither edited nor broken - the resume test asserts it returns the frozen `3` directly.
    `run_recovery.py` IS BYTE-UNCHANGED, `git diff` pasted (empty output IS the evidence):
    ```
    $ git diff -- agent_workflows/run_recovery.py
    [end]
    ```
    So `DEFAULT_RETRY_LIMIT` (`:67`), `validate_retry_budget` (`:136`), `plan_retry` and `retry_budget_remaining` are all untouched, and the default and the bound each still have exactly one definition.
    `--integration-retry-limit` IS UNTOUCHED. The only two lines mentioning it in the diff are CONTEXT lines (no `+`/`-` prefix): its `freeze_run_policy_flags` branch and its `initialize_run_core` refusal call both appear unchanged. `resolve_integration_retry_limit` is not modified, the two knobs are NOT unified, and it was deliberately NOT given a policy tier by analogy (`51vw4y` E-02 forbids reusing `DEFAULT_RETRY_LIMIT` for it, and `51vw4y` is now in `executed/`).
    `project_schema.py` IS BYTE-UNCHANGED (pasted empty in V-02); `CONFIG_SCHEMA` was not edited either, following the documented convention at `config.py:1086-1089`.
    THE BARE SUITE, BEFORE AND AFTER, with the counts I actually observed. BEFORE (at starting HEAD `58876f1b`):
    ```
    $ python3 -m pytest
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7246 passed, 3 skipped, 2 xfailed, 3 warnings in 104.96s (0:01:44)
    ```
    AFTER:
    ```
    $ python3 -m pytest
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7253 passed, 3 skipped, 2 xfailed, 3 warnings in 97.12s (0:01:37)
    ```
    FAILURE-SET DELTA AS A SET: AFTER minus BEFORE = {} (EMPTY). Both runs fail on exactly one test and it is the same one. Passed count rose 7246 -> 7253, which is the seven tests this plan added. Run BARE, with no `-n0`, no second `-q`, and no `-p no:randomly`.
    THE PRE-EXISTING FAILURE IS NOT THE ONE THE PLAN PREDICTED, AND THAT IS WORTH STATING RATHER THAN GLOSSING. The plan warned about `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` failing on a gitignored `opencode-recovery/` directory belonging to another party. THAT TEST PASSES at execution and no `opencode-recovery/` exists in this lane worktree. The one failure here is different: `test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts `OPENCODE_CONFIG_CONTENT` is ABSENT from a non-isolated turn's environment, and it is PRESENT because this very run was launched by the driver with that variable already exported in the ambient environment. It is environment-caused, fails identically before my first edit, and is unrelated to every file this plan touches. It is reported as a defect finding in the turn outcome rather than silently absorbed.
    AND I DID NOT DELETE, MOVE, OR MODIFY `opencode-recovery/`, nor anything else belonging to another party: `git status --porcelain` lists exactly the three files this plan changed (plus this plan itself), and no `opencode-recovery/` path exists in this workspace to have touched.
    EXIT CODES MEASURED UNPIPED, per the plan's instruction:
    ```
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    exit=0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES ONE BLOCKING QUESTION, RAISED AT REVIEW. OQ-01 (fail-open or fail-closed on a bad policy value) is now `Blocking: yes` and MUST be answered by the maintainer before execution; `aw ipd lint` refuses this plan at every checkpoint while it is open, which is the intended stop. The reason it was raised is not that the question is hard but that the plan's premise for delegating it to E-01 was false: it said the repository has "shipped BOTH postures", and measured, NEITHER shipped key refuses a run over a bad value, so an executor could not resolve it by following a precedent and would have had to invent a new posture mid-flight (F-16). A third option (fall back but WARN) is recorded in OQ-01 and may be the best answer.

OQ-03 (whether to land this before the budget is ever spent) remains a genuine maintainer decision and stays `Blocking: no`, because neither answer changes a line of the work; only its priority moves. It is stated against the source item's own urgency argument rather than in support of it, and review confirmed the measurement: the budget is never SPENT today, so this tier is observationally inert until `xipfy1` lands. If the maintainer wants end-to-end evidence rather than resolution-only tests, this plan should follow `xipfy1` instead of preceding it.

OQ-04 (optional versus required repo-root parameter) was ADDED and RESOLVED at review as a recommendation with a mandatory guard, because the plan never raised it although it decides how much of the suite the change touches: there are ten existing call sites, not three (F-15).

IT CARRIES NO `Blocks-Release`, deliberately: backlog `dh3us4` carries none, and this completes a precedence chain whose two shipped tiers already cover every invocation that either passes the flag or wants the default.

THE ITEM'S OWN DESIGN CAUTION WAS MEASURED AND CORRECTED, which is the main reason this plan is small. No schema change is needed: `project_schema.parse_portable_policy` preserves unknown keys and round-trips them, and two shipped repo-policy keys deliberately bypass `CONFIG_SCHEMA` with the convention documented at `config.py:1086-1089`. Follow those precedents rather than inventing a third pattern.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Do NOT mutate the repository's `.aw/config/project.json`: it is tracked and shared and other agents are working in this checkout; use throwaway repos for fixtures. Do NOT touch `run_recovery.py`, `project_schema.py`, `--integration-retry-limit`, or the resume freeze. Do NOT delete, move, or modify the gitignored `opencode-recovery/` directory, which belongs to another party and causes the one pre-existing suite failure. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

RE-LOCATE EVERY SYMBOL BY NAME, AND KNOW THAT THIS PLAN'S `runner_shared.py` ANCHORS WERE ALREADY WRONG ONCE. At review every one of them had drifted about 97 lines and was corrected (F-18); the `config.py`, `run_recovery.py` and test anchors were accurate. Two of the drifted lines are ones this plan forbids changing, so a near-miss edit to a neighbouring line is the specific hazard. Both driver files and `runner_shared.py` are under concurrent edit by `xipfy1` (`to-review`) and `51vw4y` (`reviewed`), which is merge ordering rather than a conflict: the runner isolates each lane in its own worktree and merges through the revalidate gate, and those plans touch different functions.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the CLI-over-policy guard, the resume-freeze guard, the no-literal-bound proof, and the unweakened bound-delegation test.
