# IPD: Wire the resolved verification decision into both host drivers through the shared runner library

- Date: 2026-09-06
- Kind: child
- Concern: After child 01 (`tm2cz8`) the resolver produces a CORRECT per-host verification decision, and NOTHING CONSUMES IT. Two middle tiers of the documented four-tier chain remain dead in both drivers: `oc_runipd.resolve_launch_profile` calls `runner_profiles.resolve()` without `validate=` (`oc_runipd.py:2643-2650`), `launch_profile_record` omits the value (`:2657-2683`), the freeze site reads the raw flag instead (`:2969-2970`, `"validate": getattr(args, "validate", False)`), and `agy_runipd.py` references `runner_profiles` NOWHERE. So an operator's stored per-model choice is still silently ignored on both hosts, and verification remains a flag that must be retyped every invocation. That capability is not new: the verifier turn ran on every IPD across 13 runs through 2026-08-29 and the default was switched off deliberately after measuring roughly 33% extra cost for only nits ON THE PRIMARY MODEL (recorded as F-6 in executed plan `evgi9n`), a ruling that is explicitly CONDITIONAL ("on a weaker model it is not, which is why the per-model default is wanted"). This plan restores it, per host.
  THE WIRING GOES IN THE SHARED LIBRARY, NOT TWICE. `runner_shared.py` already owns the run-policy freeze (`freeze_run_policy_flags`, `:1673-1700`) for exactly this reason, and `agy_runipd.py` already binds 46 names from `oc_runipd` rather than re-declaring them, with the module stating why: a duplicated copy "is how the deleted `_read_deps` pair came to be identically wrong in both drivers". A per-driver copy of this resolution would recreate that failure, and the divergence measurement makes the cost concrete (F-7).
- Scope: Add ONE shared resolution helper to `runner_shared.py` that turns a driver's parsed args plus its host name into the resolved verification decision, and call it from BOTH drivers' freeze sites, each writing its OWN existing frozen key with its OWN polarity (`oc` writes `validate`/`no_audit`, `agy` writes `no_verify`). Record the resolved value and its provenance tier in the durable launch record. Give antigravity the `--validate`/`--no-validate` surface it lacks so the tri-state is expressible there. NO change to the resolver, the registry, the precedence order, or either host's EFFECTIVE default when nothing is configured.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_novalnomerge_integration.py
- Item-Dependencies: executed:tm2cz8
- Status: to-review
- Set: hostdefault
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ybkmzp
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history

- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the second half of the maintainer's chosen direction (per-host default in the registry, then wire), replacing superseded plan `mn3gwr`, whose approach this plan corrects in TWO ways rather than one. FIRST, `mn3gwr` wired ONE host and its review had to reshape its own E-02/E-03 from "do the same for agy" into "prove agy is unreachable" and "prove agy did not move", producing an opencode-only surface at a seam `rununify`'s orchestrator child table names as remaining convergence work (its row `03+` names "run initialization" as an example seam and `mn3gwr` modifies `initialize_run`; its row `last` names closing "opencode-only" surfaces). This plan lands the wiring in `runner_shared.py`, which REDUCES the gap those rows describe instead of widening it. SECOND, `mn3gwr` F-5 correctly identified the polarity inversion hazard (agy freezes `no_verify` and gates on `not no_verify`, so writing a resolved `validate` into that key un-negated makes resolved True mean "do not verify") and responded by FORBIDDING agy entirely; this plan instead makes the shared helper return a decision that each driver translates into its own key, so the inversion is handled once, in one place, with a test asserting both polarities. MEASURED AT AUTHORING, all at `f3e17ff6`: driving both real parsers shows a bare `oc start` yields `validate=False` while a bare `agy start` yields `no_verify=False` (verification ON), confirming the opposite postures; the two runners define 67 symbols in common of which only 7 are byte-identical and 36 diverge below 0.80 similarity, while agy's genuinely host-specific surface is just 3 symbols and 455 lines of 4845 (`run_agy_turn` 361, `render_agy_event` 81, `resolve_agy` 13), which is the measurement arguing for shared-library placement rather than pairwise equivalence. Suite baseline `5462 passed, 3 skipped, 2 xfailed`. No product code was modified by this authoring.

## Goal

Make the operator's stored per-model verification choice actually take effect ON BOTH HOSTS, so "check this model's work, do not check that one" is configuration rather than a flag a human must remember. One resolution path, two host-correct polarities, and a durable record of which tier decided.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared resolution, correct for both polarities

- [ ] E-01 Add ONE helper to `runner_shared.py` that resolves the verification decision for a host: it takes the host's canonical runner name, the requested profile name (or `None`), and the operator's tri-state flag value (`True`/`False`/`None`), calls `runner_profiles.load()` and `runner_profiles.resolve(..., validate=...)`, and returns the resolved `ResolvedLaunch` (or at minimum the boolean plus its provenance tier). Place it beside `freeze_run_policy_flags` (`runner_shared.py:1673`), which already owns the freeze-time policy normalization for both drivers and is the precedent this follows.
  RETURN THE DECISION, NEVER A HOST KEY. The helper must NOT return something named `no_verify` or write into any driver's options dict, because the two hosts' frozen keys are OPPOSITE IN POLARITY: `oc` freezes `validate` and gates on it (`oc_runipd.py:2969-2970`, `:6212-6215`), `agy` freezes `no_verify` and gates on `not no_verify` (`agy_runipd.py:1837`, `:3392-3399`). Each driver performs its own translation at its own freeze site (E-03, E-04). A helper that returned a host-shaped key would put the inversion back in two places, which is precisely the hazard `mn3gwr` F-5 measured.
  TYPE THE FAILURE AT THE CALL SITE, NOT HERE. Both drivers define their OWN `DriverError` class (two distinct classes; `agy_runipd.py` documents the translation-wrapper problem this causes at its `enforce_dependency_preflight`), so this helper must raise `runner_profiles.RunnerProfileError` (or `runner_shared.DriverError`) and let each driver translate to its own type, exactly as agy's existing dependency-preflight wrapper does.
  - Depends on: none
  - Expected outcome: one shared function exists, is host-agnostic, takes a tri-state and returns a decision plus provenance, writes no host-specific key, and raises a type each driver can translate.
  - Execution state: pending

- [ ] E-02 Give antigravity the tri-state flag surface it lacks, so the chain is expressible there. Measured today by driving the real parsers: a bare `oc start` yields `validate=False`, `oc start --validate` yields `True`, `oc start --no-validate` yields `False`; agy has NO `--validate` at all, only `--no-verify`/`--no-audit` as `store_true` (`agy_runipd.py:4447-4453`), so a bare `agy start` yields `no_verify=False`. Add `--validate`/`--no-validate` to agy's `start` as a `BooleanOptionalAction` with `default=None`, matching oc's `resume` (`oc_runipd.py:7538`, which already ships `default=None` for exactly this tri-state reason).
  KEEP `--no-verify` WORKING AND UNCHANGED. It is the spelling every existing agy invocation and every piece of documentation uses, and removing or repurposing it would break operators for no gain. Define the interaction EXPLICITLY and record it: `--no-verify` remains an alias meaning "verification off", equivalent to `--no-validate`. If both are passed and they AGREE, accept; if they CONTRADICT (`--no-verify --validate`), REFUSE with a clear message rather than silently letting one win, because a silent winner in either direction is a verification decision the operator did not make.
  - Depends on: E-01
  - Expected outcome: `agy start --validate` / `--no-validate` parse; a bare `agy start` leaves the flag `None` so it falls through to the profile tier; `--no-verify` still turns verification off; a contradictory pair refuses with exit 2.
  - Execution state: pending

### Task group 2: consume it at each freeze site, in each host's own polarity

- [ ] E-03 Wire opencode. Pass the tri-state into `resolve_launch_profile` (`oc_runipd.py:2619-2650`) as `validate=`, and consume the resolved value at the freeze site in `initialize_run`, replacing `"validate": getattr(args, "validate", False)` and its derived `"no_audit": not getattr(args, "validate", False)` (`:2969-2970`) with the RESOLVED decision. Keep BOTH keys and their existing meanings so every downstream reader is untouched, including the verifier gate's compatibility branch (`:6212-6215`, which reads `validate` and falls back to `not (no_verify or no_audit)` when the key is absent).
  RECOVERING THE TRI-STATE IS A CHOICE AND THE OBVIOUS ONE BREAKS A SHIPPED TEST. `--validate` is a `BooleanOptionalAction` with `default=False` on `start` (`oc_runipd.py:7467`), so `args.validate` cannot today distinguish "said nothing" from "said `--no-validate`". Option (a): change the `start` default to `None`, matching `resume`. MEASURED CONSEQUENCE: `tests/test_novalnomerge_integration.py:47-79` walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`, which FAILS under `None`. That test pins the PREMISE of executed plan `evgi9n`'s bug class, so it must be UPDATED DELIBERATELY to assert the EFFECTIVE default (a bare invocation still resolves verification OFF, which is what `evgi9n` actually depends on) and never deleted or skipped. Option (b): inspect parsed argv and derive `None`. CHOOSE ONE AND RECORD WHY; (a) is preferred as the more honest change since the flag genuinely is tri-state now.
  DO NOT MOVE `resolve_launch_profile`, which is deliberately the FIRST statement of `initialize_run` (`:2691`) so a malformed profile refuses before any durable write. The resolved value is already available at the freeze site through the existing `resolved_launch` local; a second `runner_profiles.load()` would break the frozen-once guarantee that `3cm15q` E-04 established.
  - Depends on: E-02
  - Expected outcome: oc's frozen `validate` comes from the resolver; `no_audit` is derived from the RESOLVED value so the two keys can never disagree; the verifier gate fires on the resolved decision; `resolve_launch_profile` is still the first statement; the pinning test is updated, passing, and still pins a bare invocation verifying OFF.
  - Execution state: pending

- [ ] E-04 Wire antigravity, NEGATING at the boundary. Call the shared helper with `runner="agy"` and the E-02 tri-state, then freeze `"no_verify": not decision` at agy's existing freeze site (`agy_runipd.py:1837`). THE NEGATION IS THE WHOLE RISK OF THIS PLAN and `mn3gwr` F-5 records its arithmetic: writing a resolved `validate` into `no_verify` un-negated makes resolved `True` (verify) mean `no_verify=True` (do not verify), so verification would be requested and silently skipped. Assert the negation directly (E-06) rather than trusting review.
  DO NOT ADD A `validate` KEY TO AGY'S FROZEN OPTIONS. A reader finding both `validate` and `no_verify` there would face two switches for one behavior, and oc's own compatibility branch (`oc_runipd.py:6213-6214`) shows those keys are disambiguated only by ABSENCE. Keep agy's frozen shape exactly as it is and change only where the boolean comes from.
  PRESERVE THE EFFECTIVE DEFAULT: with no store and no flag, agy must still verify. After child 01 that falls out of the registry row (`validate_default=True`) rather than from a hand-written fallback, which is the point of doing child 01 first, but it must still be PROVEN here (V-06) because this is the plan that could break it.
  - Depends on: E-03
  - Expected outcome: agy's frozen `no_verify` is the negation of the resolved decision; a bare `agy run` with an empty store still verifies; no `validate` key appears in agy's frozen options; agy's verifier gate expression (`not no_verify`) is unchanged.
  - Execution state: pending

### Task group 3: make the decision auditable

- [ ] E-05 Add the resolved `validate` VALUE to `launch_profile_record` (`oc_runipd.py:2657-2683`), so `state.json` records the decision beside the tier that produced it. NOTE WHAT IS ALREADY THERE: the record's `provenance` dict ALREADY carries the `validate` tier, because it copies the resolver's whole provenance mapping (`"provenance": dict(resolved.provenance)`), verified live as including `'validate': 'defaults'`. What is missing is the VALUE, so this adds ONE key and must not duplicate the provenance already present. The tier vocabulary is the resolver's closed set (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`); child 01 OQ-01 deliberately kept `shipped-default` for the per-host tier, so no new member appears.
  BACKWARD COMPATIBILITY IS PINNED ALREADY: a run created before this change has no `validate` key in `options.launch_profile`, and `tests/test_oc_runipd.py` already asserts an older record must "still render, not raise", so read the new key defensively wherever it is displayed.
  IF AGY GAINS NO EQUIVALENT RECORD, SAY SO. That host has no `launch_profile` record today (`launch_profile_record` is one of the 22 oc-only symbols agy does not import). Do NOT build one here; note it for the registry-consolidation follow-up, because a provenance record for agy is a durable-state addition with its own compatibility surface.
  - Depends on: E-04
  - Expected outcome: oc's `state.json` `options.launch_profile` shows the resolved `validate` value; the tier is read from the provenance mapping already present, not duplicated; an older run without the key still renders; agy's lack of an equivalent is recorded, not silently accepted.
  - Execution state: pending

### Task group 4: prove it, on both hosts

- [ ] E-06 Test the POLARITY explicitly, in `tests/test_runner_shared.py` plus each driver's suite. This is the safety-critical item. Assert, at the FROZEN-STATE level and not merely at the resolver: a resolved decision of "verify" produces `validate=True` on oc AND `no_verify=False` on agy; a resolved decision of "do not verify" produces `validate=False` on oc AND `no_verify=True` on agy. A test that only checks one host, or only one direction, cannot detect the inversion, which is exactly how this class of bug survives review.
  ALSO ASSERT THE ANTI-REGRESSION FLOOR: with an isolated empty store (`XDG_CONFIG_HOME` pointed at a temp dir; `runner_profiles.store_path()` derives from `config.config_dir()`, `config.py:674-682`) and no flags, oc resolves verification OFF and agy resolves it ON, exactly as today. A run showing agy verification OFF here is a FAILED execution, not a passing one.
  - Depends on: E-05
  - Expected outcome: four polarity assertions pass across both hosts and both directions; the empty-store floor is pinned for both hosts; no test reads or writes the maintainer's real store.
  - Execution state: pending

- [ ] E-07 Test the CHAIN end to end THROUGH EACH RUNNER, which is the gap the shipped tests leave. `tests/test_runner_profiles.py:843-935` ALREADY pins all four tiers, both polarities, the absent-is-not-false case, the default-profile tier, and the measured strong-off / cheap-on split, at the RESOLVER level; read it first and do NOT duplicate it. What no test covers is that a stored profile value reaches the RUN, survives the freeze, and decides the verifier gate.
  Drive `initialize_run` on a real repository with `--prepare-only` (which exists on both hosts, `oc_runipd.py:7432`, `agy_runipd.py:4472`, and is the shipped pattern at `tests/test_run_flag_surface.py:956-970`) against an isolated store, and assert the FROZEN key for each host for: explicit flag beats a profile value; a profile value beats `defaults.validate`; `defaults.validate` beats the per-host registry row; and absence at every tier yields each host's OWN row value. Assert oc's `no_audit` agrees with `validate` in every case. Assert the tri-state does not collapse: a profile saying `validate: false` must be distinguishable from a profile OMITTING the field, since only the former is a decision.
  - Depends on: E-06
  - Expected outcome: the four-tier chain is pinned AT THE FROZEN-STATE LEVEL for BOTH hosts; the tri-state provably does not collapse; no resolver-level test is duplicated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SHARED LIBRARY IS THE ESTABLISHED HOME FOR CROSS-DRIVER POLICY, and the repository states why in the code. `runner_shared.py` already owns `freeze_run_policy_flags` (`:1673-1700`) and `RUN_POLICY_FLAGS` (`:1397+`), and `agy_runipd.py` binds 46 names from `oc_runipd` with an explicit comment that a duplicated copy "is how the deleted `_read_deps` pair came to be identically wrong in both drivers" and that `ruff` removing 6 re-exports was caught only by a cross-driver symmetry test. Add to the shared module; do not fork.
- THE TWO DRIVERS DEFINE THEIR OWN `DriverError` CLASSES, and this is a documented trap: agy wraps `enforce_dependency_preflight` purely to re-raise in its own type, because otherwise the refusal "would surface as an unhandled traceback instead of a clean exit". A shared helper must therefore raise a neutral type and let each driver translate.
- THE HOSTS' FROZEN KEYS ARE OPPOSITE IN POLARITY, deliberately, and the code says so at length: `agy_runipd.py:3474-3482` states "NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`: this driver gates the verifier on `not no_verify` (verification defaults ON here), whereas `oc` gates on `validate` (which defaults OFF). The shared predicate takes `validate=`, so pass the locally-correct boolean rather than copying `oc`'s expression." That instruction IS this plan's design.
- `validate` is a genuine TRI-STATE by explicit design (`runner_profiles.py:39-44`, `_validate_tristate` at `:467`): ABSENT must never collapse to `false`, because an explicit flag must always beat a stored default. Both drivers must therefore pass `None` when the operator said nothing.
- `initialize_run` freezes policy into `state["options"]` at queue build and treats a resume as bound by the frozen values; `resolve_launch_profile` is deliberately its FIRST statement so a bad profile refuses before any durable write. Follow both; do not add a second mechanism.
- `--prepare-only` exists on both hosts and is how the shipped tests drive `initialize_run` without launching an agent.
- oc's `resume` already lets a passed `--validate` OVERWRITE the frozen value (`oc_runipd.py:7882-7886`, with a comment stating the behavior is preserved exactly). This plan changes where a NEW run's value comes from, not what a resume may do (OQ-02).
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The resolver is called WITHOUT the flag on oc, so tier 1 never registers as explicit, and the resolved value is never read. | `oc_runipd.py:2643-2650` passes `runner`, `profile`, `model`, `variant`, `agent` and no `validate=`; the freeze site reads `getattr(args, "validate", False)` at `:2969-2970` |
| F-2 | Antigravity has ZERO profile integration: `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to nothing in `agy_runipd.py`. | `rg` over `agent_workflows/agy_runipd.py`, exit 1 |
| F-3 | **The postures are opposite, measured by driving BOTH real parsers.** A bare `oc start` yields `validate=False`; `--validate` yields `True`; `--no-validate` yields `False`. A bare `agy start` yields `no_verify=False` (verification ON); `--no-verify` yields `True`. agy has no `--validate` at all. | live parser probe 2026-09-06 at `f3e17ff6`; `oc_runipd.py:7467`, `agy_runipd.py:4447-4453` |
| F-4 | **The inversion hazard, with its arithmetic.** agy freezes `no_verify` and gates on `not no_verify`, so writing a resolved `validate` into that key WITHOUT negating makes resolved `True` (verify) become `no_verify=True` (do not verify): verification requested and silently skipped. This is why E-01 forbids the helper from returning a host-shaped key and E-06 asserts both polarities. | `agy_runipd.py:1837`, `:3392-3399`, `:3474-3482`; `mn3gwr` F-5 |
| F-5 | `launch_profile_record` omits the `validate` VALUE but NOT the provenance, which arrives via `dict(resolved.provenance)`. Verified live: the record's provenance includes `'validate': 'defaults'` while `'validate' in record` is `False`. So E-05 adds ONE key, not two. | `oc_runipd.py:2657-2683`; live `launch_profile_record(resolve(cfg, runner="oc"))` |
| F-6 | **E-03's preferred mechanism breaks a shipped test, and that test is load-bearing.** `tests/test_novalnomerge_integration.py:47-79` walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`, pinning the PREMISE of executed plan `evgi9n`'s bug class. Under a `None` default `assertIs(None, False)` fails. `tests/test_oc_runipd.py:1966` uses `assertFalse` and survives `None`. | `tests/test_novalnomerge_integration.py:71-79`; `mn3gwr` F-9, independently re-measured |
| F-7 | **The divergence this plan must not deepen, measured.** The two runners define 67 top-level symbols in common: only 7 are byte-identical, 4 near (>=0.95), 20 similar, and 36 diverged below 0.80 (`initialize_run` 0.42, `build_parser` 0.54, `execute_item` 0.77 at 872/852 lines). But agy's genuinely host-specific surface is only 3 symbols and 455 lines of 4845 (`run_agy_turn` 361, `render_agy_event` 81, `resolve_agy` 13), and it already imports 38 oc-only symbols worth 1503 lines. So the sustainable shape is one shared driver plus small per-host adapters, and shared-library placement is what `rununify` is reaching for. | AST + `difflib` per-symbol comparison 2026-09-06 at `f3e17ff6` |
| F-8 | `no_audit` is DERIVED from `validate` at oc's freeze site and read by the verifier gate's compatibility branch plus five tests, so it must be derived from the RESOLVED value or the two frozen keys can disagree. | `oc_runipd.py:2969-2970`, `:6213-6214`; `tests/test_oc_runipd.py:2390`, `:2473`, `:2517`, `:2556`, `:2658` |
| F-9 | The capability was exercised historically and switched off on measured grounds, so this is a RESTORATION rather than a new feature: the verifier turn ran on every IPD across 13 runs through 2026-08-29, and the ~33% cost ruling is explicitly conditional on the primary model. | `evgi9n` F-6; 13 run directories carrying verification outcome files, latest `run-20260829T191652Z-4134000` |
| F-10 | agy has no `launch_profile` record to extend: `launch_profile_record` is among the 22 oc-only symbols agy does NOT import (`run_opencode`, `resolve_launch_profile`, `launch_profile_record`, `extract_profile_clause` and 18 others, 1027 lines). E-05 therefore covers oc only and must say so. | AST symbol-set difference minus agy's import list, measured 2026-09-06 |

## Proposed changes (ordered, validatable)

1. One shared host-agnostic resolution helper in `runner_shared.py`, returning a decision and never a host key (E-01).
2. Give agy the `--validate`/`--no-validate` tri-state, keeping `--no-verify` as a working alias and refusing contradictions (E-02).
3. Wire oc: pass the tri-state in, consume the resolved value at the freeze site, keep `no_audit` consistent, update the pinning test deliberately (E-03).
4. Wire agy: negate at the boundary into its existing `no_verify` key, add no second key, preserve its verify-by-default floor (E-04).
5. Record the resolved value beside the provenance the record already carries, oc only, and say why agy has none (E-05).
6. Assert both polarities on both hosts, plus the empty-store floor (E-06).
7. Pin the four-tier chain at the FROZEN-STATE level for both hosts (E-07).

## Deferred / out of scope (with reason)

- CHANGING EITHER HOST'S EFFECTIVE DEFAULT. oc stays OFF and agy stays ON when nothing is configured. This plan makes the stored choice effective; it does not decide what the choice should be. Any default change is a separate, measured decision, and the maintainer's ruling on the ~33% cost stands.
- BUILDING A `launch_profile` PROVENANCE RECORD FOR AGY (F-10). That host has no such record; adding one is a durable-state addition with its own compatibility surface and belongs with the registry-consolidation work. E-05 records the gap rather than silently accepting it.
- ADDING AN `agy` DISPATCH ADAPTER so `aw run as <agy-profile>` launches that host. Child 01 E-04 keeps that refusal fail-closed; implementing it is a separate concern (argv contract, absent `--variant`/`--agent`, its own `main`).
- CONSOLIDATING THE FOUR HOST REGISTRIES (child 01 F-4). Real, worth doing, and larger than this Set.
- PER-ROLE MODEL ROUTING (a distinct model for the verifier turn). That is `kgpptv` (`runprofile-06`, `Status: reviewed`). Complementary and with NO ordering dependency in either direction: this plan decides WHETHER the verifier runs, `kgpptv` decides WHICH model runs it, and `kgpptv`'s fence forbids touching the `validate` tri-state. NOTE for whoever executes `kgpptv`: it was authored believing the profile mechanism is oc-only (its F-12), which child 01 makes false, so its scope should be re-read rather than trusted.
- THE FLAG SURFACE QUESTION on oc (whether argparse-generated negations are acceptable). That is `ki6tom`, which the `25kzda` spec amendment largely dissolved and which needs re-scoping or retiring as a maintainer decision.
- A STANDALONE RE-VERIFY VERB for an already-executed plan. Backlog `7u9kbm`, deliberately sequenced after this and inheriting the same cost question.
- UNIFYING THE 36 DIVERGED SYMBOLS (F-7). That is `rununify`'s job and it is blocked on its own unauthored `03+`/`last` child rows plus its E-02 characterization baseline. This plan deliberately adds its new logic to the SHARED module so it does not enlarge that backlog.

## Scope check

- Over-scope: none. One shared module, both drivers at their existing freeze sites, and the four test files the change touches.
- Scope-Paths justification: `runner_shared.py` hosts the new helper; `oc_runipd.py` and `agy_runipd.py` are each edited at their own freeze site and parser (unavoidable, since the whole point is that both hosts consume it); `tests/test_runner_shared.py` covers the helper and the polarity matrix; each driver's suite covers its own freeze; `tests/test_novalnomerge_integration.py` carries the pinning assertion F-6 measured as breaking.
- BOTH DRIVERS ARE IN SCOPE DELIBERATELY, unlike superseded `mn3gwr` which excluded `agy_runipd.py` because it could not reach that host. Child 01 removes that obstacle, so touching both is now the correct scope rather than an overreach. These are the two highest-contention modules in the repository: expect drift and re-locate by symbol.
- Under-scope: does not change the resolver, the registry, the precedence order, either default, or the diverged-symbol set. Each is excluded with a stated reason.

## Required tests / validation

- `python3 -m pytest` BARE, full suite, before and after, with the `N passed` summary line pasted and counts stated. Baseline at authoring: `5462 passed, 3 skipped, 2 xfailed in 115.53s` (plus whatever child 01 adds).
- Targeted: `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_novalnomerge_integration.py`, `tests/test_runner_profiles.py`.
- A live before/after demonstration that a stored profile value actually changes the FROZEN verification decision of a real run ON EACH HOST, which is the whole point of the plan and is not shown by the resolver-level tests.
- VALIDATE IN THE REAL CHECKOUT for anything touching `tests/test_run_viewer.py`: it reads `.aw/records/runs/`, which is gitignored, so it fails in a bare worktree and passes in the real checkout. Green elsewhere proves nothing.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`). A pipe through `head` reports the pipe's status, which has already produced one false finding in this area.
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda`'s amended Section 1.3 records that skipping the independent verifier turn is a RETAINED, host-configurable choice rather than a prohibited bypass, and states that "until per-role model routing exists ... a host-level control is the only available mechanism" (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:105`). This plan implements that mechanism FOR BOTH HOSTS, so no spec change is required and no spec edit is authorized here.

DO NOT EDIT SPEC `25kzda`'s §4.2 FINDING-CODE TABLE for any reason. `run_evidence.RUN_FINDING_CODES` transcribes those table cells VERBATIM and a test asserts byte equality, so editing a cell IS a code change; a note above the table already records this.

USER-FACING TEXT MAY NOW CLAIM BOTH HOSTS, which is the change from `mn3gwr`. If the executor writes or touches any user-facing description, it must be accurate about what ships: after this plan the per-model verification default is configuration on opencode AND antigravity, and still nothing for the four unregistered hosts. Do not imply parity beyond the two registered rows. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should `--no-verify` and `--validate` coexist on agy, or should one replace the other?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: COEXIST, with `--no-verify` retained as an alias and a contradiction refused (E-02). `--no-verify` is the spelling every existing agy invocation and all documentation uses, so removing it breaks operators for no functional gain, and repurposing it silently would change the meaning of a flag people already type. Adding the tri-state is what makes the chain expressible; keeping the old spelling is what makes the change non-breaking. The refusal on contradiction is the only honest handling: silently letting either win would be a verification decision the operator did not make, and both directions of that error are bad (skipping a check that was asked for, or paying for one that was declined).

### OQ-02: Does freezing the resolved value break `--validate` on resume?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No, and the existing behavior is deliberately preserved. `oc_runipd.py:7882-7886` currently lets a resume OVERWRITE the frozen `validate` when the flag is passed, with a comment stating that overwrite behavior is preserved exactly. This plan changes where a NEW run's value comes from, not what a resume may do. If the executor believes resume should refuse instead of overwrite, that is a separate decision and must not be folded in here.

### OQ-03: Should a stored profile value be allowed to turn verification ON for a run started with no flag?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, that is the entire purpose. The maintainer's measured position is per-model (off for the strong executor, on for a weaker one), and the `validate` field was built for exactly that. A stored value that could only turn verification OFF would leave the weak-model case still dependent on a remembered flag, which is the failure `vju5ba` recorded across five overnight runs. The explicit flag still wins when present, so an operator is never surprised in the direction they typed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new helper's signature, docstring, and body. Confirm by inspection and state explicitly that it returns NO host-specific key (no `no_verify`, no writing into an options dict) and that it raises a neutral exception type each driver translates. Paste the tri-state behavior: called with `True`, `False`, and `None`, showing `None` falls through to the configured tier rather than being read as a decision.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste parsed-args output from driving agy's REAL parser for four invocations: bare `start` (expect the flag `None`), `--validate` (`True`), `--no-validate` (`False`), and `--no-verify` (verification off). Paste the exit code and message for the CONTRADICTORY pair `--no-verify --validate`, measured UNPIPED, showing a refusal rather than a silent winner. Confirm `--no-verify` alone still behaves exactly as before.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the resolved `validate` and its provenance for three oc invocations: no flag (provenance NOT `explicit`), `--validate` (`True`/`explicit`), `--no-validate` (`False`/`explicit`). STATE WHICH MECHANISM YOU CHOSE, (a) the `None` default or (b) argv inspection, and why. If (a): paste the UPDATED `tests/test_novalnomerge_integration.py` assertion and its passing output, and state in one sentence what it now pins (it must still pin that a bare invocation verifies OFF). A paste showing that test failing, skipped, xfailed, or deleted is a FAILED validation. Paste the first statement of `initialize_run` showing `resolve_launch_profile` was not moved.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste agy's frozen `options` block from a real `--prepare-only` invocation showing `no_verify`, for BOTH a resolved-verify and a resolved-do-not-verify case, and show the negation is correct in both directions. Paste the frozen options in full and confirm NO `validate` key was added. Quote agy's verifier gate expression showing it is still `not no_verify`, unchanged. Paste the empty-store bare invocation showing agy STILL VERIFIES.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `options.launch_profile` from a real oc `state.json` showing the `validate` VALUE and the provenance tier, for at least two different tiers (for example `explicit` and one configured tier). Paste the pre-existing test that renders an OLDER `launch_profile` record lacking the new key, still passing. State explicitly that agy gained no equivalent record and where that gap is recorded.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THE SAFETY-CRITICAL PASTE. A four-cell matrix from ACTUAL test output: resolved verify -> oc `validate=True` AND agy `no_verify=False`; resolved do-not-verify -> oc `validate=False` AND agy `no_verify=True`. All four cells must be shown; a paste covering one host or one direction is a FAILED validation because it cannot detect the inversion. Also paste the empty-isolated-store floor for both hosts (oc OFF, agy ON) and confirm `XDG_CONFIG_HOME` pointed at a temp dir so the maintainer's real store was never read or written.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL output of the five targeted test modules and of the BARE full suite (`python3 -m pytest`, no added flags) with its `N passed` summary line, stating before/after counts. Paste the frozen-state result for each of the four tiers on EACH host (explicit beats profile; profile beats `defaults`; `defaults` beats the registry row; absence yields the row). Paste the case distinguishing a profile that says `validate: false` from one that OMITS the field, proving the tri-state did not collapse. Confirm oc's `no_audit` agreed with `validate` in every case, and confirm no resolver-level test from `tests/test_runner_profiles.py:843-935` was duplicated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

DEPENDENCY: this plan declares `- Item-Dependencies: executed:tm2cz8` and MUST NOT run before child 01 is executed. Child 01 puts the per-host default in the registry row; without it, agy's tier-4 fallback resolves to opencode's `False` and E-04's floor (agy verifies by default) would silently break. The runner re-checks dependencies at dispatch, so a queued-together Set is safe, but a hand-run of this plan alone is not.

Scope fence: touch ONLY the seven paths in `Scope-Paths`. Do NOT change `runner_profiles.py`, `RUNNER_REGISTRY`, the schema, or the precedence order (child 01 owns those and is expected to be executed already). Do NOT add a `validate` key to agy's frozen options. Do NOT move `resolve_launch_profile` out of first position in `initialize_run`. Do NOT change either host's effective default. Do NOT edit spec `25kzda`. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. NOTE: this is a SHARED CHECKOUT and a driver run may be live; run `aw runs` before starting and expect contention on both driver modules.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the two highest-contention modules in the repository and other pending plans declare them, so expect drift and expect to rebase and re-run the full suite after any merge. Find `resolve_launch_profile`, `launch_profile_record`, each `initialize_run` freeze block, each verifier gate, and `freeze_run_policy_flags` by name.

THE ITEM THAT MATTERS MOST IS V-06. The hosts' frozen keys are OPPOSITE IN POLARITY, so a wiring change that looks correct can silently disable verification on antigravity: resolved `True` written un-negated into `no_verify` means the verifier does NOT run, so verification would be requested and skipped with no error anywhere. F-4 records the arithmetic. All four cells of the polarity matrix must be pasted from real output. If V-06 cannot be shown green in all four cells, STOP and report rather than proceeding.

On completion of THIS plan (not child 01), close backlog `h7qsje`, which both children carry as `- From-Backlog:`. The operator-visible capability it describes ships here, because this is the plan after which a stored per-model choice actually decides a run.
