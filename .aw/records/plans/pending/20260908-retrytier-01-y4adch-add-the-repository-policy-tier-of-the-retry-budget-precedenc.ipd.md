# IPD: Add the repository-policy tier of the retry-budget precedence chain

- Date: 2026-09-08
- Kind: child
- Concern: A THREE-TIER PRECEDENCE CHAIN SHIPS WITH ITS MIDDLE TIER MISSING, AND THE CODE SAYS SO IN ITS OWN DOCSTRING. Spec `25kzda` (`- Status: approved`) fixes the chain twice: at `:158` "The CLI value overrides repository policy; repository policy overrides the default of 2. The frozen value cannot change on resume", and again in the invariant table at `:118` ("A2: configurable retries"). `resolve_retry_budget` (`agent_workflows/runner_shared.py:1987`) implements two of the three and states the gap in as many words (`:1990-1993`): "The MIDDLE TIER IS NOT IMPLEMENTED and is not faked here: no repository-policy home exists (backlog `dh3us4` tracks it), so this resolves CLI-over-default and the gap is stated in `--retry-budget`'s own `--help` rather than left for an operator to discover."
  THE WHOLE RESOLVER IS FOUR LINES AND HAS NO REPOSITORY-CONFIG READ AT ALL: `if cli_value is None: return run_recovery.DEFAULT_RETRY_LIMIT`, else `run_recovery.validate_retry_budget(cli_value)` wrapped into a `RunFlagRefusal`. It takes ONLY `cli_value`, so the middle tier requires a SIGNATURE CHANGE to receive a repo root, and both call sites must pass it (`oc_runipd.py:2783`, `agy_runipd.py:1792`, plus the freeze path `freeze_run_policy_flags` `runner_shared.py:2058`, retry branch `:2078-2079`).
  THE DEFAULT'S SINGLE DEFINITION IS `run_recovery.DEFAULT_RETRY_LIMIT` (`agent_workflows/run_recovery.py:67`, value `2`), read at `:275`, `:416` and `runner_shared.py:2004`, and deliberately not duplicated (`RETRY_BUDGET_OWNER`, `runner_shared.py:1915`, exists only to tell a reader where the number lives). The 0..10 bound belongs to `run_recovery.validate_retry_budget` and is CALLED, never re-checked, because executed plan `sq61qd` made that the single definition precisely so the flag layer could reach it at parse time. Both properties must survive.
  THE ITEM'S OWN DESIGN CAUTION IS WHERE IT IS MOST WRONG, AND CORRECTING IT SHRINKS THE WORK. It warns that `.aw/config/project.json` "is the obvious home, but adding a key there is a schema change with its own validation and defaulting rules." Measured: `project_schema.parse_portable_policy` (`agent_workflows/project_schema.py:558`) over `ProjectPolicySchema` (`:490`) carries a `known_keys` set (`:574-584`) but is PERMISSIVE, preserving unrecognized keys in `unknown_fields` (`:585`) and writing them BACK on serialization (`:519-522`). So the schema does NOT need editing, and there are TWO SHIPPED PRECEDENTS that deliberately bypass it, both reading the file directly in `config.py` and both documenting why: `dependency_schema_cutover` (`config.py:1044`, reader `:1047`, accessor `:1072`, FAIL-OPEN) and `review_findings_gate` (`:1097`, reader `:1106`, accessor `:1130`, FAIL-CLOSED, with its vocabulary tuple at `:1100` and default at `:1103`). The convention is written down at `config.py:1086-1089`.
- Scope: Add the repository-policy tier: a project-config key read through a `config.py` accessor following the two shipped precedents, consulted by `resolve_retry_budget` only when no CLI value was passed, falling back to `run_recovery.DEFAULT_RETRY_LIMIT`, with the 0..10 bound still reached through `validate_retry_budget` and the resume freeze unchanged. EXCLUDES SPENDING the budget, which is `xipfy1`'s (`retrywire-01`) entire subject and which this plan must not touch; EXCLUDES the separate `--integration-retry-limit` knob (`51vw4y` E-02, explicitly told not to reuse `DEFAULT_RETRY_LIMIT`); EXCLUDES editing `project_schema.py`, which does not need it.
- Scope-Paths: agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_flag_surface.py
- Item-Dependencies: none
- Status: to-review
- Set: retrytier
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y4adch
- From-Backlog: dh3us4

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `dh3us4`. NOTHING IS OBSOLETE and no plan in any disposition adds the middle tier: searched all five for `retry-budget`, `retry_budget`, `DEFAULT_RETRY_LIMIT`, `retrypolicy`, `dh3us4`, "repository policy". Every hit is adjacent and each was checked individually. `sq61qd` (executed) made the 0..10 bound single-definition. `uyeko5` (executed) shipped CLI-over-default and its Deferred section FILED this item. `xipfy1` (`retrywire-01`, `to-review`, `From-Backlog: trjfyy`, `Blocks-Release: next`) EXPLICITLY EXCLUDES this tier three times: its scope says it "Adds no flag, no new budget semantics, and no repository-policy tier", its E-02 says "Do NOT call `resolve_retry_budget` again in the loop", and its Deferred section says "THE REPOSITORY-POLICY PRECEDENCE TIER. Owned by backlog `dh3us4` ... Adding it here would take over another item's scope". `51vw4y` E-02 adds a DIFFERENT knob (`--integration-retry-limit`) and is explicitly told not to reuse `DEFAULT_RETRY_LIMIT`. `m7gvuz` F-13/E-10 must merely DECIDE whether to reuse `--retry-budget` and adds no tier. `1bfppy` defers requeuing. THE CRITICAL RELATIONSHIP QUESTION IS ANSWERED AND IT IS NOT A DEPENDENCY: `xipfy1` consumes the already-FROZEN integer and does not change where or how the budget is RESOLVED, while this plan changes only the resolution. They touch the same file at different functions, so this is merge ordering. Graduated backlog `trjfyy` ("retry budget dormant zero callers") covers the CONSUMPTION gap and graduated to `xipfy1`; it distinguishes the two itself (`:31-33`: "`dh3us4` ... covers ONLY the repository-policy middle precedence tier ... i.e. it PRESUMES consumption exists"). THREE OF THE ITEM'S CLAIMS ARE NOW WRONG AND ALL THREE ARE RECORDED RATHER THAN CARRIED FORWARD. FIRST, `DEFAULT_RETRY_LIMIT` is at `run_recovery.py:67`, not `:62` (line 62 is inside the rationale comment); the value `2` is correct. SECOND, the "schema change with its own validation and defaulting rules" caution is misleading: `project_schema.parse_portable_policy` (`project_schema.py:558`) preserves unknown keys (`:585`) and round-trips them (`:519-522`), and TWO shipped repo-policy keys deliberately bypass it with the convention written at `config.py:1086-1089`, so the work is SMALLER than the item implies while the caution's substance ("do NOT add an ad-hoc config read; follow the authority") is satisfied by following those precedents. THIRD, "WHY IT IS GATED ON `uyeko5`" is stale: `uyeko5` is executed and the item is correctly `open`. ONE OF THE ITEM'S OWN ARGUMENTS IS NOW WEAKER, and honesty requires saying so: it claims "the two shipped tiers give correct behavior for every invocation", but the budget is NEVER SPENT today (`run_recovery.plan_retry` `:269` and `retry_budget_remaining` `:415` have no production callers, only their own module and `tests/test_run_recovery_cli.py`), so no invocation gets correct retry behavior at ANY tier until `xipfy1` lands. That weakens the not-urgent framing rather than the scope, and is why this plan carries no release gate: the item carries none. FINALLY, a shipped contract test constrains the change: `tests/test_run_flag_surface.py:628-639` (`test_the_bound_is_sq61qds_and_is_not_re_checked_here`) forbids a literal bound here, and `:288-291` requires `NOT IMPLEMENTED` and `dh3us4` in `--retry-budget`'s help, so the help text must be updated in the same change.

## Goal

Complete the spec's three-tier retry-budget precedence by giving a repository a standing default other than 2, following the two config-key precedents already shipped, without re-deciding the bound, duplicating the default, or touching how the budget is spent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: choose the key's contract before writing it

- [ ] E-01 DECIDE AND RECORD THE KEY's NAME, SHAPE AND FAILURE POSTURE, following the two shipped precedents rather than inventing a third pattern. Read both first: `dependency_schema_cutover` (`config.py:1044`, reader `:1047`, accessor `:1072`) is FAIL-OPEN; `review_findings_gate` (`:1097`, reader `:1106`, accessor `:1130`, vocabulary `:1100`, default `:1103`) is FAIL-CLOSED. The convention that neither is registered in `CONFIG_SCHEMA` is documented at `:1086-1089`, with the reason (`parse_portable_policy` preserves unknown keys and writes them back, so the key round-trips safely).
  FAIL-OPEN VERSUS FAIL-CLOSED IS THE REAL DECISION AND IT MUST BE ARGUED, NOT ASSUMED. A malformed or out-of-range value has two honest responses: ignore it and fall back to `DEFAULT_RETRY_LIMIT` (fail-open, so a typo cannot stop every run), or REFUSE the run with a message naming the key (fail-closed, so a repository that thinks it set a policy is never silently ignored). The second is more consistent with how the CLI value behaves: an out-of-range `--retry-budget` raises `RunFlagRefusal` (`runner_shared.py:2005-2008`), and silently ignoring the same bad value from config while refusing it from the CLI would be an inconsistency an operator cannot predict. Whichever you choose, record it in the accessor's docstring the way `config.py:1091-1094` records the other choice.
  THE VALUE'S BOUND IS NOT YOURS TO DEFINE. It is 0..10 and it belongs to `run_recovery.validate_retry_budget`. Route the config value through it; do not compare against literals. `tests/test_run_flag_surface.py:628-639` exists to enforce exactly this.
  - Depends on: none
  - Expected outcome: a recorded key name, value shape and fail-open/fail-closed decision with its reasoning and consistency argument against the CLI's own refusal behavior, and a stated plan to route the value through `validate_retry_budget`.
  - Execution state: pending

### Task group 2: read the policy the way the repository already reads policy

- [ ] E-02 ADD THE READER AND ACCESSOR TO `config.py`, COPYING THE SHIPPED SHAPE. `read_review_findings_gate` (`:1106-1127`) plus `findings_gate_threshold` (`:1130-1145`) is the closer model because it validates a value rather than merely reading a marker. Mirror its structure: a module constant for the key, a reader returning the raw value, and an accessor applying the default and the validation.
  DO NOT EDIT `project_schema.py`. `parse_portable_policy` (`:558`) preserves unrecognized keys in `unknown_fields` (`:585`) and writes them back on serialization (`:519-522`), so the key round-trips without a schema change. That is the documented convention (`config.py:1086-1089`), and it is the specific correction to the backlog item's design caution.
  HANDLE THE ABSENT CASES EXPLICITLY, all of which are normal: no `.aw/config/project.json` at all, a file without the key, a null value. Each must resolve to "no policy set", so the caller falls through to the default. A missing config file is the common case in a fresh repository and must never be an error.
  - Depends on: E-01
  - Expected outcome: a key constant, reader and accessor in `config.py` mirroring `read_review_findings_gate`/`findings_gate_threshold`, `project_schema.py` untouched, and every absent case resolving to "no policy set".
  - Execution state: pending

- [ ] E-03 THREAD THE REPO ROOT INTO `resolve_retry_budget` AND ADD THE MIDDLE TIER, keeping the precedence exactly as spec `:158` states: CLI over repository policy over default 2. The function is at `runner_shared.py:1987` and today takes only `cli_value`, so this is a signature change.
  KEEP THE TWO INVARIANTS THE CURRENT DOCSTRING PROTECTS. The bound stays `validate_retry_budget`'s and is CALLED, never re-checked here (its docstring at `:1996-1999` explains that `sq61qd` made it single-definition precisely so the flag layer could reach it at parse time when no `RunEngine` and no step exist). And the default stays `run_recovery.DEFAULT_RETRY_LIMIT` (`run_recovery.py:67`), never copied; `RETRY_BUDGET_OWNER` (`runner_shared.py:1915`) exists only to point a reader at it.
  UPDATE THE DOCSTRING, because it currently asserts the gap this plan closes ("The MIDDLE TIER IS NOT IMPLEMENTED and is not faked here"). Leaving it would make the code lie about itself.
  PASS THE ROOT AT BOTH CALL SITES AND THROUGH THE FREEZE PATH: `oc_runipd.py:2783` and `agy_runipd.py:1792` (note the repo is already bound before the call at `oc_runipd.py:2744`, so the root is available), plus `freeze_run_policy_flags` (`runner_shared.py:2058`, retry branch `:2078-2079`) whose result is stored into `state["options"]` (`oc_runipd.py:3059`, `agy_runipd.py:2017`).
  DO NOT CHANGE THE RESUME FREEZE. `--retry-budget` carries `resume_rule=RESUME_REFUSE` and `refuse_frozen_flags_on_resume` (`:2034`) refuses it on resume; spec `:158` says "The frozen value cannot change on resume". A resumed run must keep the value frozen at start EVEN IF the repository policy changed in between, and that must be asserted rather than assumed.
  - Depends on: E-02
  - Expected outcome: `resolve_retry_budget` implementing CLI over policy over default with the bound still delegated and the default still single-defined, its docstring corrected, both call sites and the freeze path passing the root, and the resume freeze unchanged.
  - Execution state: pending

### Task group 3: tell the truth in the help text, and prove all three tiers

- [ ] E-04 UPDATE `--retry-budget`'s HELP TEXT IN THE SAME CHANGE, or a shipped test fails. `tests/test_run_flag_surface.py:288-291` requires `NOT IMPLEMENTED` and `dh3us4` to appear in that help while the gap exists; both must go, and the test must be updated with them.
  THE CURRENT TEXT DISCLOSES THE GAP HONESTLY (`runner_shared.py:1895-1901`: "NOTE: spec 2.1's MIDDLE precedence tier (repository policy) is NOT IMPLEMENTED - no repository-policy home exists yet (backlog dh3us4) - so precedence today is CLI over default"). Replace it with the real three-tier precedence and NAME THE CONFIG KEY, because an operator who wants a standing override needs to know what to write and where. Keep the sentence that the frozen value cannot change on resume.
  DO NOT DELETE THE DISCLOSURE PATTERN ITSELF. Other rows still use it for genuinely unimplemented behavior (`--follow-generated` names backlog `x8diyb`), and the help-honesty test protects them.
  - Depends on: E-03
  - Expected outcome: `--retry-budget`'s help describing the real three-tier precedence and naming the config key, the `dh3us4` disclosure removed, the help-honesty test updated and still protecting the remaining unimplemented row.
  - Execution state: pending

- [ ] E-05 PROVE THE RESOLVED VALUE IS CORRECT FOR EVERY INPUT COMBINATION, on fixtures. Seven combinations must each be asserted. (a) A CLI value alongside a set policy resolves to the CLI value. (b) A set policy with no CLI value resolves to the policy value. (c) Neither present resolves to `DEFAULT_RETRY_LIMIT`. (d) An absent config file resolves to the default without raising. (e) A policy value outside the 0..10 range behaves as E-01 decided, proven to route through `validate_retry_budget` rather than a local comparison. (f) A malformed policy value (wrong type or unparseable) behaves the same decided way. (g) A resume whose repository policy CHANGED since the run started still resolves to the frozen value.
  CASE (a) IS THE PRECEDENCE GUARD and case (g) IS THE FREEZE GUARD; both are the ones a careless implementation breaks. Quote their assertions separately.
  ASSERT THE BOUND IS NOT RE-DEFINED, keeping `tests/test_run_flag_surface.py:628-639` (`test_the_bound_is_sq61qds_and_is_not_re_checked_here`) green. If that test now needs adjusting because the function grew a parameter, adjust it WITHOUT weakening what it asserts, and say what changed.
  DO NOT WRITE TO THE REPOSITORY'S OWN `.aw/config/project.json`. It is a tracked, shared file, three agents are working in this checkout, and a test that mutates it would change every other run's behavior. Use throwaway repos, as `tests/test_run_flag_surface.py`'s existing fixtures do.
  - Depends on: E-04
  - Expected outcome: seven fixture cases passing with the precedence and freeze guards quoted separately, the bound-delegation test still green and not weakened, and the real `project.json` untouched.
  - Execution state: pending

- [ ] E-06 PROVE NOTHING ELSE MOVED, because this file is shared and one sibling plan reads the value this one resolves.
  `xipfy1`'s CONSUMPTION PATH MUST BE UNAFFECTED. It reads the FROZEN budget from `state["options"]` and explicitly does not re-resolve ("Do NOT call `resolve_retry_budget` again in the loop"). Show the frozen options' shape is unchanged, so if `xipfy1` has landed it still reads the same key, and if it has not, its premise still holds.
  `run_recovery` MUST BE BYTE-UNCHANGED. `DEFAULT_RETRY_LIMIT` (`:67`), `validate_retry_budget` and `plan_retry` (`:269`) / `retry_budget_remaining` (`:415`) are not this plan's subject. Paste a diff proving it.
  THE OTHER RETRY KNOB MUST NOT BE TOUCHED. `51vw4y` E-02 adds `--integration-retry-limit` and is explicitly told not to reuse `DEFAULT_RETRY_LIMIT`; do not unify them here, and do not "helpfully" give it a policy tier too.
  RUN THE SUITE BARE and judge on the DELTA, stating observed counts rather than quoting a baseline.
  - Depends on: E-05
  - Expected outcome: the frozen options' shape unchanged, `run_recovery` byte-unchanged, `--integration-retry-limit` untouched, and an empty bare-suite failure-set delta with observed counts stated.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. Decide and record the key's name, shape and fail-open/fail-closed posture against the two precedents (E-01).
2. Add the reader and accessor to `config.py` mirroring `review_findings_gate`, leaving `project_schema.py` alone (E-02).
3. Thread the repo root into `resolve_retry_budget`, add the middle tier, correct the docstring, keep the resume freeze (E-03).
4. Replace the help text's gap disclosure with the real precedence and the key name, updating the help-honesty test (E-04).
5. Prove all three tiers plus every fallback, out-of-range, malformed and resume case on fixtures (E-05).
6. Prove the frozen options shape, `run_recovery` and the other retry knob are untouched (E-06).

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

- Over-scope: none. One config key with a reader and accessor, one resolver gaining one parameter and one tier, one help string, two test surfaces.
- Scope-Paths justification: `agent_workflows/config.py` holds the two precedent keys and their readers/accessors (`:1044`, `:1047`, `:1072`, `:1097`, `:1106`, `:1130`) and the convention note (`:1086-1089`) that E-02 follows; `agent_workflows/runner_shared.py` holds `resolve_retry_budget` (`:1987`) and its docstring gap statement (`:1990-1993`), the `--retry-budget` row and help (`:1889-1903`), `RETRY_BUDGET_OWNER` (`:1915`), `freeze_run_policy_flags` (`:2058`, retry branch `:2078-2079`) and `refuse_frozen_flags_on_resume` (`:2034`); `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` hold the two call sites (`:2783`, `:1792`) that must pass the repo root and the state writes that freeze the value (`:3059`, `:2017`); `tests/test_run_flag_surface.py` holds `RetryBudgetTests`, the bound-delegation test (`:628-639`) that must stay green and unweakened, and the help-honesty test (`:288-291`) that E-04 must update.
- Under-scope, stated rather than left as `none`: this plan does not spend the budget, does not touch `run_recovery.py`, does not touch `--integration-retry-limit`, does not edit `project_schema.py` or `CONFIG_SCHEMA`, does not change the resume freeze, does not add policy tiers to other flags, does not mutate the real project config, and amends no spec.

## Required tests / validation

- SEVEN FIXTURE CASES (E-05), each named with pasted output: CLI over policy; policy over default; default when neither; no config file at all; out-of-range policy; malformed policy; resume with a changed policy keeping the frozen value.
- THE PRECEDENCE GUARD AND THE FREEZE GUARD QUOTED SEPARATELY, since those two are what a careless implementation breaks.
- BOUND-DELEGATION PROOF: `tests/test_run_flag_surface.py:628-639` green and NOT weakened; if it needed adjusting for the new parameter, state exactly what changed and why the assertion is intact.
- NO-LITERAL-BOUND PROOF: show the new code contains no `0`/`10` comparison and routes the policy value through `run_recovery.validate_retry_budget`.
- SINGLE-DEFAULT PROOF: show `DEFAULT_RETRY_LIMIT` is still read rather than copied, and that `RETRY_BUDGET_OWNER`'s claim remains true.
- DOCSTRING PROOF: paste the corrected `resolve_retry_budget` docstring, since the current one asserts the gap this plan closes.
- HELP TEXT PASTED BEFORE AND AFTER, showing the `dh3us4` disclosure removed, the three-tier precedence stated, the config key NAMED, and the resume sentence kept. Plus the help-honesty test still protecting the remaining unimplemented row (`--follow-generated`, backlog `x8diyb`).
- FROZEN OPTIONS SHAPE UNCHANGED, so `xipfy1`'s consumption premise holds whether or not it has landed.
- `run_recovery.py` BYTE-UNCHANGED (`git diff` pasted), and `--integration-retry-limit` untouched.
- NEGATIVE PROOF THAT THE REAL CONFIG WAS NOT MUTATED: `git status --porcelain .aw/config/` clean.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set, with the counts you actually observed. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
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

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND ASSIGNED TO E-01, because the repository has shipped BOTH postures deliberately and neither is the obvious default. `dependency_schema_cutover` is fail-open (`config.py:1047`), `review_findings_gate` is fail-closed (`:1106`), and each records its reason. The argument for FAIL-CLOSED here is consistency with the sibling tier: an out-of-range `--retry-budget` on the CLI raises `RunFlagRefusal` (`runner_shared.py:2005-2008`), so silently ignoring the identical bad value when it comes from config would be an inconsistency an operator cannot predict, and a repository that believes it set a policy would be silently overridden. The argument for FAIL-OPEN is blast radius: a typo in a tracked, shared config file would refuse EVERY run for everyone until fixed, whereas a bad CLI value harms only the one invocation that typed it. That asymmetry is real and is why this is the maintainer's call rather than a coin flip. E-01 must record the choice and its reason in the accessor's docstring.

### OQ-02: What should the key be called and what shape should its value take?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A RULE, with the concrete name left to E-01 because it is a naming choice, not a design one. The value is a BARE INTEGER, not an object or a string, because the CLI value it overrides is `kind="int"` (`runner_shared.py:1892`) and the bound it must satisfy is an integer range owned by `validate_retry_budget`; any richer shape would need its own parser for no benefit. The name follows the two precedents' snake_case top-level style (`dependency_schema_cutover`, `review_findings_gate`) and should name the THING rather than the flag, so it reads as repository policy rather than as a CLI mirror. Deliberately rejected: nesting it under a `run` or `retry` object, since neither precedent nests and introducing a nesting convention for one key would leave the file with two shapes.

### OQ-03: Is this worth doing before the budget is ever spent?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND HONEST, because the measurement cuts against the item's own urgency argument and a maintainer should see it. The item argues the missing tier "only matters once a repository wants a standing override different from 2", which presumes the other two tiers work. But the budget is NEVER SPENT today: `plan_retry` (`run_recovery.py:269`) and `retry_budget_remaining` (`:415`) have no production callers, and closing that gap is `xipfy1`'s job. So until `xipfy1` lands, this tier is observationally inert: it will resolve a different number that nothing acts on. Two defensible conclusions follow. EITHER land it now, because it is small, it is spec-mandated, it completes an `approved` requirement, and it is strictly easier to add before `xipfy1`'s consumer exists than after. OR park it until consumption ships, because an inert feature cannot be validated end to end and its tests can only assert resolution, not effect. This plan is written for the first reading (which is also why `Item-Dependencies` is `none`), but it does not pretend the second is unreasonable. Non-blocking because the work is correct under either answer; only its priority moves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: state the chosen key name, its value shape, and the fail-open/fail-closed decision WITH its reasoning, including the consistency argument against the CLI's own `RunFlagRefusal` behavior and the blast-radius counter-argument. Cite which of the two precedents you followed and why. Paste the accessor docstring recording the choice.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new key constant, reader and accessor from `config.py`, and show by side-by-side comparison that the shape mirrors `read_review_findings_gate`/`findings_gate_threshold`. Paste `git diff` over `project_schema.py` proving it is byte-unchanged. Paste passing evidence for all three absent cases: no config file, file without the key, null value.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the changed `resolve_retry_budget` in full, showing the precedence order and showing the bound is reached via `run_recovery.validate_retry_budget` with NO literal `0` or `10` comparison and the default read from `DEFAULT_RETRY_LIMIT` rather than copied. Paste the corrected docstring (the old one asserts the gap). Paste both call sites and the freeze path passing the repo root. Paste evidence the resume refusal is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `--retry-budget`'s help BEFORE and AFTER, showing the `dh3us4`/`NOT IMPLEMENTED` disclosure gone, the three-tier precedence stated, the config key NAMED, and the resume sentence retained. Paste the updated help-honesty test and show it still protects the remaining unimplemented row (`--follow-generated`, naming `x8diyb`).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of all seven cases. QUOTE the CLI-over-policy assertion and the resume-with-changed-policy assertion separately as the two guards. Paste `tests/test_run_flag_surface.py`'s own summary line green, and if `test_the_bound_is_sq61qds_and_is_not_re_checked_here` was adjusted, paste the before and after and state why the assertion is intact rather than weakened. Paste `git status --porcelain .aw/config/` clean.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste evidence the frozen `state["options"]` shape is unchanged, and state whether `xipfy1` had landed and how its consumption is unaffected either way. Paste `git diff` over `run_recovery.py` showing it byte-unchanged. Confirm `--integration-retry-limit` is untouched. THEN paste the BARE `python3 -m pytest` summaries before and after with the failure-set delta as a set and the counts you actually observed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, but OQ-01 (fail-open or fail-closed) and OQ-03 (whether to land this before the budget is ever spent) are both genuine maintainer decisions, and OQ-03 is stated against the source item's own urgency argument rather than in support of it: the budget is never SPENT today, so this tier is observationally inert until `xipfy1` lands. The work is correct under either answer; only its priority moves.

IT CARRIES NO `Blocks-Release`, deliberately: backlog `dh3us4` carries none, and this completes a precedence chain whose two shipped tiers already cover every invocation that either passes the flag or wants the default.

THE ITEM'S OWN DESIGN CAUTION WAS MEASURED AND CORRECTED, which is the main reason this plan is small. No schema change is needed: `project_schema.parse_portable_policy` preserves unknown keys and round-trips them, and two shipped repo-policy keys deliberately bypass `CONFIG_SCHEMA` with the convention documented at `config.py:1086-1089`. Follow those precedents rather than inventing a third pattern.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Do NOT mutate the repository's `.aw/config/project.json`: it is tracked and shared and three agents are working in this checkout; use throwaway repos for fixtures. Do NOT touch `run_recovery.py`, `--integration-retry-limit`, or the resume freeze. Re-locate every symbol by NAME; both driver files are under concurrent edit. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the CLI-over-policy guard, the resume-freeze guard, the no-literal-bound proof, and the unweakened bound-delegation test.
