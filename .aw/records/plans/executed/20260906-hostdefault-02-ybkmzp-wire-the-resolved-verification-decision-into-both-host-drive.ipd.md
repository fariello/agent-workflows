# IPD: Wire the resolved verification decision into both host drivers through the shared runner library

- Date: 2026-09-06
- Kind: child
- Concern: After child 01 (`tm2cz8`) the resolver produces a CORRECT per-host verification decision, and NOTHING CONSUMES IT. Two middle tiers of the documented four-tier chain remain dead in both drivers: the live resolution site calls `runner_profiles.resolve()` without `validate=` (`oc_runipd.resolve_launch_pair`, `oc_runipd.py:2673-2685`), `launch_profile_record` omits the value (`:2703-2729`), the freeze site reads the raw flag instead (`:3045-3046`, `"validate": getattr(args, "validate", False)`), and `agy_runipd.py` references `runner_profiles` NOWHERE. So an operator's stored per-model choice is still silently ignored on both hosts, and verification remains a flag that must be retyped every invocation. That capability is not new: the verifier turn ran on every IPD across 13 runs through 2026-08-29 and the default was switched off deliberately after measuring roughly 33% extra cost for only nits ON THE PRIMARY MODEL (recorded as F-6 in executed plan `evgi9n`), a ruling that is explicitly CONDITIONAL ("on a weaker model it is not, which is why the per-model default is wanted"). This plan restores it, per host.
  THE FUNCTION THIS PLAN WAS AUTHORED AGAINST NO LONGER CARRIES THE LIVE PATH, and that is the single most important correction review made. When this plan was written, `initialize_run` called `resolve_launch_profile`. Executed plan `kgpptv` (`runprofile-06`, merged `3798d236` on 2026-09-08, AFTER this plan was authored) replaced that call with `resolve_launch_pair`, which resolves the executor AND the verifier launch from ONE store read. MEASURED at review (`fac69fbd`, AST walk of `oc_runipd.py` for calls to either name): `resolve_launch_pair` is called exactly ONCE, at `:2742`, the first statement of `initialize_run`; `resolve_launch_profile` has ZERO callers in the whole package, and its only remaining references are two test modules and a docstring in `run_dispatch.py`. So an executor following the authored E-03 literally would have added `validate=` to a function no run executes, changed nothing observable, and had every V-item still pass at the resolver level while the frozen state was untouched. E-03 is rewritten to name `resolve_launch_pair`, and to state which of its TWO `resolve()` calls takes the flag and why the other must not.
  THE WIRING GOES IN THE SHARED LIBRARY, NOT TWICE. `runner_shared.py` already owns the run-policy freeze (`freeze_run_policy_flags`, `:2058-2084`) for exactly this reason, and `agy_runipd.py` already binds 46 names from `oc_runipd` rather than re-declaring them, with the module stating why: a duplicated copy "is how the deleted `_read_deps` pair came to be identically wrong in both drivers". A per-driver copy of this resolution would recreate that failure, and the divergence measurement makes the cost concrete (F-7).
- Scope: Add ONE shared resolution helper to `runner_shared.py` that turns a driver's parsed args plus its host name into the resolved verification decision, and call it from BOTH drivers' freeze sites, each writing its OWN existing frozen key with its OWN polarity (`oc` writes `validate`/`no_audit`, `agy` writes `no_verify`). Record the resolved value and its provenance tier in the durable launch record. Give antigravity the `--validate`/`--no-validate` surface it lacks so the tri-state is expressible there. NO change to the resolver, the registry, the precedence order, or either host's EFFECTIVE default when nothing is configured.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_novalnomerge_integration.py, tests/test_runner_profiles_e2e.py, docs/runner-profiles.md, .aw/records/backlog
- Item-Dependencies: executed:tm2cz8
- Status: executed
- Readiness: go-pending-approval
- Set: hostdefault
- Order: 2
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ybkmzp
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history
- 2026-09-14 executed (aw oc run): aw oc run self-finalize: ybkmzp verified (set hostdefault, attempt 2). [Scope reconciliation - in-scope-unmodified tests/test_agy_runipd_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-08 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-601..PR-610

- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-610. Reviewed at HEAD `fac69fbd`; `aw ipd lint --phase author` conformed before semantic review and `--phase review-finalize` after. SELF-REVIEW DISCLOSURE: the same session authored this plan and its predecessors, so this is the third self-review in the chain and is worth less than an independent one. THE PLAN'S THESIS HOLDS and was re-verified from scratch: the resolver produces a correct per-host decision (`resolve(runner="oc").validate` is `False`/`shipped-default`, `resolve(runner="agy")` is `True`/`shipped-default`), no driver consumes it, and the polarity inversion the plan centers on is real. WHAT REVIEW CHANGED IS THE OPENCODE HALF'S TARGET, and this is the finding that mattered: executed plan `kgpptv` merged `3798d236` on 2026-09-08, AFTER this plan was authored, and replaced `initialize_run`'s call to `resolve_launch_profile` with `resolve_launch_pair`. Measured by AST call-graph walk, `resolve_launch_profile` now has ZERO production callers, so an executor following the authored E-03 literally would have edited dead code: no behavior change, no test failure, every resolver-level V-item still green. E-03 was rewritten to the live site, with the new constraint that the flag must NOT be threaded into the verifier `resolve()` call (`verify_with` says WHICH model verifies, never WHETHER) and that the shared `config_digest` assertion must survive. SECOND, E-02's authored flag spelling CRASHES at parser build: copying oc's `--validate`/`--verify`/`--audit` alias list onto agy generates `--no-verify`/`--no-audit`, which agy already declares, and the measured result is `ArgumentError` on every `aw agy` invocation; the obvious `conflict_handler="resolve"` workaround is worse, silently stealing `--no-verify` so `args.no_verify` ceases to exist and antigravity stops verifying by default. THIRD, the promised contradiction refusal is hand-written work, not an argparse freebie (`--no-verify --validate` parses cleanly). FOURTH, NO SHIPPED COMMAND CAN WRITE the configuration this plan makes effective on agy (the wizard hardcodes `RUNNER = "oc"`, `aw agy profile` does not exist, `set_validate_default` has no caller), so new E-08 forces the documented-hand-edit path with executed proof, resolved to option (a) on child 01's own fence rather than left to the executor. FIFTH, THREE SHIPPED ASSERTIONS PIN THE CLAIM THIS PLAN FALSIFIES and one is invisible to the mandated bare suite (`tests/test_runner_profiles_e2e.py` is `pytest.mark.slow` against `-m 'not slow'`), so new E-09 owns them plus the published doc, and the validation section now requires `-m slow`. Also: every driver citation had drifted 70 to 200 lines and was re-resolved; the plan's Step 0 claim that the two drivers define separate `DriverError` classes is FALSE since `818uru` (verified: one class, both drivers bind it), so the prescribed translation wrapper was removed; agy declares no `--profile`, so its profile tier is the per-runner DEFAULT profile and E-06/E-07 were corrected accordingly. Scope-Paths grew from seven to ten. E-count 7 to 9. No product code was modified by this review.

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the second half of the maintainer's chosen direction (per-host default in the registry, then wire), replacing superseded plan `mn3gwr`, whose approach this plan corrects in TWO ways rather than one. FIRST, `mn3gwr` wired ONE host and its review had to reshape its own E-02/E-03 from "do the same for agy" into "prove agy is unreachable" and "prove agy did not move", producing an opencode-only surface at a seam `rununify`'s orchestrator child table names as remaining convergence work (its row `03+` names "run initialization" as an example seam and `mn3gwr` modifies `initialize_run`; its row `last` names closing "opencode-only" surfaces). This plan lands the wiring in `runner_shared.py`, which REDUCES the gap those rows describe instead of widening it. SECOND, `mn3gwr` F-5 correctly identified the polarity inversion hazard (agy freezes `no_verify` and gates on `not no_verify`, so writing a resolved `validate` into that key un-negated makes resolved True mean "do not verify") and responded by FORBIDDING agy entirely; this plan instead makes the shared helper return a decision that each driver translates into its own key, so the inversion is handled once, in one place, with a test asserting both polarities. MEASURED AT AUTHORING, all at `f3e17ff6`: driving both real parsers shows a bare `oc start` yields `validate=False` while a bare `agy start` yields `no_verify=False` (verification ON), confirming the opposite postures; the two runners define 67 symbols in common of which only 7 are byte-identical and 36 diverge below 0.80 similarity, while agy's genuinely host-specific surface is just 3 symbols and 455 lines of 4845 (`run_agy_turn` 361, `render_agy_event` 81, `resolve_agy` 13), which is the measurement arguing for shared-library placement rather than pairwise equivalence. Suite baseline `5462 passed, 3 skipped, 2 xfailed`. No product code was modified by this authoring.

- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
## Goal

Make the operator's stored per-model verification choice actually take effect ON BOTH HOSTS, so "check this model's work, do not check that one" is configuration rather than a flag a human must remember. One resolution path, two host-correct polarities, and a durable record of which tier decided.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared resolution, correct for both polarities

- [x] E-01 Add ONE helper to `runner_shared.py` that resolves the verification decision for a host: it takes the host's canonical runner name, the requested profile name (or `None`), and the operator's tri-state flag value (`True`/`False`/`None`), calls `runner_profiles.load()` and `runner_profiles.resolve(..., validate=...)`, and returns the resolved `ResolvedLaunch` (or at minimum the boolean plus its provenance tier). Place it beside `freeze_run_policy_flags` (`runner_shared.py:2058`), which already owns the freeze-time policy normalization for both drivers and is the precedent this follows.
  RETURN THE DECISION, NEVER A HOST KEY. The helper must NOT return something named `no_verify` or write into any driver's options dict, because the two hosts' frozen keys are OPPOSITE IN POLARITY: `oc` freezes `validate` and gates on it (`oc_runipd.py:3045-3046`, `:6555-6557`), `agy` freezes `no_verify` and gates on `not no_verify` (`agy_runipd.py:2001`, `:3553-3559`). Each driver performs its own translation at its own freeze site (E-03, E-04). A helper that returned a host-shaped key would put the inversion back in two places, which is precisely the hazard `mn3gwr` F-5 measured.
  THE IMPORT IS PERMITTED, AND KNOW WHY BEFORE YOU WRITE IT. `runner_shared`'s admission rules forbid importing EITHER RUNNER (`runner_shared.py:32-37`), enforced by AST in `tests/test_runner_shared.py::NoRunnerImportTests`, which rejects any module name containing `runipd`. `runner_profiles` is NOT a runner: it is a peer module in the same package that imports only `agent_workflows.config`, so importing it introduces no cycle (verified live: `import agent_workflows.runner_shared, agent_workflows.runner_profiles` succeeds) and trips no guard. Import it at MODULE level, not lazily inside the function, since the guard targets runners and a lazy import here would only obscure the dependency.
  THE FAILURE TYPE IS ALREADY ONE CLASS, so do NOT rebuild the translation this plan's Step 0 note describes. `DriverError` is defined ONCE, in `runner_shared.py:170`, and BOTH drivers bind that same object; verified live at review, `oc_runipd.DriverError is agy_runipd.DriverError is runner_shared.DriverError` is `True`. The two-distinct-classes problem was closed by `rununify` Order 02 (`818uru`), and agy's `enforce_dependency_preflight` wrapper explicitly records that its translation half "was DELETED" and only a `RuntimeError` guard remains (`agy_runipd.py:1343-1350`). So: raise `runner_profiles.RunnerProfileError` and let each driver wrap it in `DriverError` with its own message prefix (the pattern at `oc_runipd.py:2689-2692`), or raise `runner_shared.DriverError` directly. Do NOT add a per-driver translation wrapper; there is nothing left to translate.
  - Depends on: none
  - Expected outcome: one shared function exists, is host-agnostic, takes a tri-state and returns a decision plus provenance, writes no host-specific key, and raises a type each driver can translate.
  - Execution state: performed

- [x] E-02 Give antigravity the tri-state flag surface it lacks, so the chain is expressible there. Measured at review by driving the real parsers: a bare `oc start` yields `validate=False`, `oc start --validate` yields `True`, `oc start --no-validate` yields `False`; agy has NO `--validate` at all, only `--no-verify`/`--no-audit` as `store_true` (`agy_runipd.py:4663-4669`), so a bare `agy start` yields `no_verify=False`. Add `--validate`/`--no-validate` to agy's `start` as a `BooleanOptionalAction` with `default=None`, matching oc's `resume` (`oc_runipd.py:7929-7936`, which already ships `default=None` for exactly this tri-state reason).
  REGISTER THE BARE `--validate` ONLY. DO NOT COPY oc's ALIAS LIST, and this is a measured import-time crash rather than a style note (F-14). oc spells the flag `("--validate", "--verify", "--audit")`; `BooleanOptionalAction` auto-generates a `--no-X` for EVERY option string, so that alias list also generates `--no-verify` and `--no-audit`, which agy's `start` ALREADY declares. Measured on agy's real `start` parser (whose `conflict_handler` is the default `"error"`, verified live): adding the aliased form raises `argparse.ArgumentError: argument --validate/--no-validate/--verify/--no-verify/--audit/--no-audit: conflicting option strings: --no-verify, --no-audit`, at `build_parser()` time, so EVERY `aw agy` invocation dies. Also do NOT reach for `conflict_handler="resolve"`: measured, it makes the new action SILENTLY STEAL `--no-verify`/`--no-audit`, after which `args.no_verify` does not exist at all (`getattr` returns the `<gone>` sentinel) and agy's freeze site reads `False` unconditionally. The bare form is what works: measured on agy's real parser, `start.add_argument("--validate", dest="validate", action=BooleanOptionalAction, default=None)` yields bare `None`, `--validate` `True`, `--no-validate` `False`, with `no_verify` intact throughout.
  KEEP `--no-verify` WORKING AND UNCHANGED. It is the spelling every existing agy invocation and every piece of documentation uses, and removing or repurposing it would break operators for no gain. Define the interaction EXPLICITLY and record it: `--no-verify` remains an alias meaning "verification off", equivalent to `--no-validate`. If both are passed and they AGREE, accept; if they CONTRADICT (`--no-verify --validate`), REFUSE with a clear message rather than silently letting one win, because a silent winner in either direction is a verification decision the operator did not make. Measured: with the bare form registered, `--no-verify --validate` PARSES to `validate=True, no_verify=True` and argparse raises nothing, so the refusal is a HAND-WRITTEN check the executor must add; it is not free.
  PUT THE REFUSAL WHERE agy's OTHER PRE-RESOLUTION REFUSALS LIVE, not in `build_parser`. `initialize_run` already refuses unhonorable flags before any durable state, via three shared calls (`agy_runipd.py:1788-1791`, `refuse_unimplemented_run_flags` / `evaluate_unverifiable_admission` / `resolve_retry_budget`), all of which run BEFORE the run directory is created at `:1884-1885`. Raise `DriverError` there so agy's `main` catches it and exits 2 with a clean `runagy: ...` message; a `parser.error()` would exit 2 as well but would bypass the seam every other flag refusal uses.
  - Depends on: E-01
  - Expected outcome: `agy start --validate` / `--no-validate` parse; a bare `agy start` leaves the flag `None` so it falls through to the profile tier; `--no-verify` still turns verification off and `args.no_verify` still EXISTS; a contradictory pair refuses with exit 2 before any durable write; `aw agy --help` still builds.
  - Execution state: performed

### Task group 2: consume it at each freeze site, in each host's own polarity

- [x] E-03 Wire opencode, AT `resolve_launch_pair` AND NOT AT `resolve_launch_profile`. Read F-12 first: `resolve_launch_pair` (`oc_runipd.py:2652`) is the ONLY resolution the run executes, and it is the first statement of `initialize_run` (`:2742`); `resolve_launch_profile` (`:2613`) has ZERO production callers since `kgpptv` landed and editing it changes nothing. Pass the tri-state as `validate=` into `resolve_launch_pair`'s EXECUTOR `resolve()` call (`:2673-2685`), then consume the resolved value at the freeze site in `initialize_run`, replacing `"validate": getattr(args, "validate", False)` and its derived `"no_audit": not getattr(args, "validate", False)` (`:3045-3046`) with the RESOLVED decision. Keep BOTH keys and their existing meanings so every downstream reader is untouched, including the verifier gate's compatibility branch (`:6555-6557`, which reads `validate` and falls back to `not (no_verify or no_audit)` when the key is absent).
  DO NOT PASS `validate=` TO THE VERIFIER `resolve()` CALL (`:2686-2688`). That second call resolves the profile named by `executor.verify_with` and exists to answer WHICH model verifies, never WHETHER one does; spec `25kzda` and `docs/runner-profiles.md:182-184` both state the two are independent ("IT SAYS WHICH, NOT WHETHER"). Threading the flag into it would make a verifier profile's own `validate` field able to re-decide the gate, which is a second switch for one behavior and is exactly what the tri-state chain exists to prevent. `resolve_launch_pair` also ASSERTS both launches share one `config_digest` (`:2694-2699`); leave that assertion intact.
  DECIDE AND RECORD WHERE THE RESOLVED VALUE IS CARRIED. `resolve_launch_pair` returns a TUPLE `(executor, verifier_or_None)` and the freeze site already holds `resolved_launch`, whose `.validate` field carries the decision once the flag is threaded in. Reading `resolved_launch.validate` at the freeze site is therefore sufficient and adds no plumbing; do NOT add a third return value, and do NOT call `runner_profiles.load()` a second time (F-13 records why: two reads reintroduce the very window `kgpptv` closed).
  RECOVERING THE TRI-STATE IS A CHOICE AND THE OBVIOUS ONE BREAKS A SHIPPED TEST. `--validate` is a `BooleanOptionalAction` with `default=False` on `start` (`oc_runipd.py:7857-7865`), so `args.validate` cannot today distinguish "said nothing" from "said `--no-validate`". Option (a): change the `start` default to `None`, matching `resume`. MEASURED CONSEQUENCE: `tests/test_novalnomerge_integration.py:47-79` (`ShippedDefaultReachabilityTests::test_shipped_defaults_are_validate_off_and_self_finalize_on`) walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`, which FAILS under `None`. That test pins the PREMISE of executed plan `evgi9n`'s bug class, so it must be UPDATED DELIBERATELY to assert the EFFECTIVE default (a bare invocation still resolves verification OFF, which is what `evgi9n` actually depends on) and never deleted or skipped. Option (b): inspect parsed argv and derive `None`. CHOOSE ONE AND RECORD WHY; (a) is preferred as the more honest change since the flag genuinely is tri-state now.
  DO NOT MOVE `resolve_launch_pair`, which is deliberately the FIRST statement of `initialize_run` (`:2742`) so a malformed profile refuses before any durable write (the run directory is created 148 lines later, at `:2891-2895`). The resolved value is already available at the freeze site through the existing `resolved_launch` local; a second `runner_profiles.load()` would break the frozen-once guarantee that `3cm15q` E-04 established.
  - Depends on: E-02
  - Expected outcome: oc's frozen `validate` comes from the resolver; `no_audit` is derived from the RESOLVED value so the two keys can never disagree; the verifier gate fires on the resolved decision; `resolve_launch_pair` is still the first statement and its verifier call still receives no `validate=`; the pinning test is updated, passing, and still pins a bare invocation verifying OFF.
  - Execution state: performed

- [x] E-04 Wire antigravity, NEGATING at the boundary. Call the shared helper with `runner="agy"` and the E-02 tri-state, then freeze `"no_verify": not decision` at agy's existing freeze site (`agy_runipd.py:2001`). THE NEGATION IS THE WHOLE RISK OF THIS PLAN and `mn3gwr` F-5 records its arithmetic: writing a resolved `validate` into `no_verify` un-negated makes resolved `True` (verify) mean `no_verify=True` (do not verify), so verification would be requested and silently skipped. Assert the negation directly (E-06) rather than trusting review.
  CALL THE HELPER BEFORE THE FIRST DURABLE WRITE, which agy's `initialize_run` does NOT currently do for anything profile-shaped, so this is a placement DECISION and not a copy of oc's. oc resolves at the first statement of `initialize_run` deliberately (`3cm15q` F-13). agy's run directory is created at `agy_runipd.py:1884-1885`; place the call at or before the existing shared-refusal block (`:1788-1791`), so a malformed store refuses with no run id, directory, events, or state, exactly as it does on oc. Placing it after `run_dir.mkdir` would leave an orphan run directory on a bad store, which is the failure `3cm15q` closed on the other host.
  agy PASSES NO PROFILE NAME, and say so rather than leaving the executor to infer it. Measured at review: agy's `start` parser declares NO `--profile` (`getattr(args, "profile", ...)` returns absent), and agy has no `as <profile>` clause (`extract_profile_clause` is oc-only). So the helper is called with the profile argument `None`, and the reachable tiers on agy are the explicit flag (E-02), `defaults.profiles["agy"]` (a per-runner DEFAULT profile, which resolves without being named), `defaults.validate`, and the registry row. Confirmed live: with `defaults: {profiles: {agy: q}}` and profile `q` carrying `validate: false`, `resolve(cfg, runner="agy")` returns `False` with provenance `default-profile`. Do NOT add a `--profile` flag or an `as` clause to agy here; that is the deferred dispatch-adapter work.
  DO NOT ADD A `validate` KEY TO AGY'S FROZEN OPTIONS. A reader finding both `validate` and `no_verify` there would face two switches for one behavior, and oc's own compatibility branch (`oc_runipd.py:6555-6557`) shows those keys are disambiguated only by ABSENCE. Keep agy's frozen shape exactly as it is and change only where the boolean comes from.
  PRESERVE THE EFFECTIVE DEFAULT: with no store and no flag, agy must still verify. After child 01 that falls out of the registry row (`validate_default=True`) rather than from a hand-written fallback, which is the point of doing child 01 first, but it must still be PROVEN here (V-06) because this is the plan that could break it.
  - Depends on: E-03
  - Expected outcome: agy's frozen `no_verify` is the negation of the resolved decision; the helper is called before any durable write and a malformed store leaves no run directory; a bare `agy run` with an empty store still verifies; no `validate` key appears in agy's frozen options; agy's verifier gate expression (`not no_verify`) is unchanged.
  - Execution state: performed

- [x] E-08 Make the agy capability REACHABLE BY AN OPERATOR, or record honestly that it is not. Read F-15: after E-04 the wiring is correct and the only way to exercise it is a HAND-EDITED `runner-profiles.json`. Measured at review: the wizard hardcodes `RUNNER = "oc"` (`runner_profile_wizard.py:76`) and `aw oc profile add` writes `"runner": wiz.RUNNER` (`cli.py:10153`), so every profile any shipped command can create is an `oc` profile; `aw agy profile` does not exist (`invalid choice: 'profile'`, exit 2); and NOTHING in the package calls `runner_profiles.set_validate_default`, so `defaults.validate` has no writer either (`grep` over `--include=*.py` finds only the definition and its unit tests).
  DO OPTION (a): SHIP THE WIRING AND DOCUMENT THE MANUAL STEP. This is DECIDED, not left to the executor, and the repository decided it: child 01's own scope fence says "Do NOT widen the wizard to a second host" and "Do NOT add a `run_dispatch` adapter", so adding an agy writer surface here would contradict the immediately preceding child of this same Set. Concretely: add to `docs/runner-profiles.md` the exact JSON an operator writes to set an `agy` profile (including the `defaults.profiles` entry that makes it apply, since agy accepts no `--profile`) and to set `defaults.validate`, state plainly that no `aw` command writes either yet, and file a backlog item for the writer surface with `aw backlog new`.
  DO NOT ADD A WRITER HERE. A CLI surface is its own design question (which verb, which host argument, how it interacts with the oc-only wizard, whether `aw agy profile` should exist at all), and folding it into a wiring plan would both widen this plan and cross child 01's fence. If the executor believes a writer is genuinely required for this Set to be useful, that is a maintainer decision: record it as a new blocking open question rather than building it.
  - Depends on: E-04
  - Expected outcome: `docs/runner-profiles.md` shows the literal JSON for an `agy` profile (with its `defaults.profiles` entry) and for `defaults.validate`, states that no `aw` command writes them, and a backlog item exists for the writer surface with its id6 recorded here. No CLI or wizard code is changed.
  - Execution state: performed

### Task group 3: make the decision auditable

- [x] E-05 Add the resolved `validate` VALUE to `launch_profile_record` (`oc_runipd.py:2703-2729`), so `state.json` records the decision beside the tier that produced it. NOTE WHAT IS ALREADY THERE: the record's `provenance` dict ALREADY carries the `validate` tier, because it copies the resolver's whole provenance mapping (`"provenance": dict(resolved.provenance)`), verified live as including `'validate': 'defaults'`. What is missing is the VALUE, so this adds ONE key and must not duplicate the provenance already present. The tier vocabulary is the resolver's closed set (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`); child 01 OQ-01 deliberately kept `shipped-default` for the per-host tier, so no new member appears.
  BACKWARD COMPATIBILITY IS PINNED ALREADY: a run created before this change has no `validate` key in `options.launch_profile`, and `tests/test_oc_runipd.py` already asserts an older record must "still render, not raise", so read the new key defensively wherever it is displayed.
  IF AGY GAINS NO EQUIVALENT RECORD, SAY SO. That host has no `launch_profile` record today (`launch_profile_record` is one of the 22 oc-only symbols agy does not import). Do NOT build one here; note it for the registry-consolidation follow-up, because a provenance record for agy is a durable-state addition with its own compatibility surface.
  - Depends on: E-04
  - Expected outcome: oc's `state.json` `options.launch_profile` shows the resolved `validate` value; the tier is read from the provenance mapping already present, not duplicated; an older run without the key still renders; agy's lack of an equivalent is recorded, not silently accepted.
  - Execution state: performed

### Task group 4: prove it, on both hosts

- [x] E-06 Test the POLARITY explicitly, in `tests/test_runner_shared.py` plus each driver's suite. This is the safety-critical item. Assert, at the FROZEN-STATE level and not merely at the resolver: a resolved decision of "verify" produces `validate=True` on oc AND `no_verify=False` on agy; a resolved decision of "do not verify" produces `validate=False` on oc AND `no_verify=True` on agy. A test that only checks one host, or only one direction, cannot detect the inversion, which is exactly how this class of bug survives review.
  ALSO ASSERT THE ANTI-REGRESSION FLOOR: with an isolated empty store (`XDG_CONFIG_HOME` pointed at a temp dir; `runner_profiles.store_path()` derives from `config.config_dir()`, `config.py:674-683`) and no flags, oc resolves verification OFF and agy resolves it ON, exactly as today. A run showing agy verification OFF here is a FAILED execution, not a passing one.
  - Depends on: E-05
  - Expected outcome: four polarity assertions pass across both hosts and both directions; the empty-store floor is pinned for both hosts; no test reads or writes the maintainer's real store.
  - Execution state: performed

- [x] E-09 Update the THREE shipped assertions and the ONE published doc that assert agy reads no profile symbol, all of which this plan makes FALSE. Read F-16: these are not prose, they are tests that will FAIL, and one of them is invisible to the bare suite.
  (1) `tests/test_oc_runipd.py:5256-5273` (`VerifierRoutingHostAsymmetryTests::test_the_agy_runner_has_no_profile_integration_at_all`) asserts `agy_runipd` source contains `runner_profiles`, `resolve_launch_profile`, `launch_profile` and `verify_with` exactly ZERO times, with the message "the OC-only claim needs re-measuring". This plan makes agy reference `runner_profiles` (or the shared helper) deliberately, so the count becomes nonzero and the test fails in the BARE suite. Do NOT delete it: rewrite it to pin what remains TRUE and load-bearing, which is that agy participates in the `validate` chain but NOT in `verify_with` model routing (that is still oc-only, and E-05 keeps agy without a `launch_profile` record). The `verify_with` half of the assertion should SURVIVE unchanged.
  (2) `tests/test_runner_profiles_e2e.py:852-869` (`PublishedContractParityTests::test_the_doc_states_the_verify_with_limits_rather_than_implying_parity`) asserts the same zero-count for `runner_profiles`, `launch_profile` and `verify_with`, AND asserts the doc contains "does not read runner profiles". BOTH halves break. THIS FILE IS `pytest.mark.slow` (`:58`) and the configured `addopts` supply `-m 'not slow'` (`pyproject.toml:169`), so the BARE suite DESELECTS it and a bare-only paste shows green while it is red; measured at review, a bare `python3 -m pytest tests/test_runner_profiles_e2e.py` reports `no tests ran in 2.80s`. Validate with `-m slow` as well (see the validation section), which is the same trap child 01's review recorded as its F-10.
  (3) `docs/runner-profiles.md:187-189` states "IT IS OPENCODE ONLY. The Antigravity runner does not read runner profiles at all, so it neither honors `verify_with` nor any other profile field." After this plan the first clause is false and the `verify_with` clause is still true. Rewrite to say precisely which fields each host honors: `validate` on both, `verify_with`/`variant`/`agent` on opencode only (`variant`/`agent` because `RUNNER_REGISTRY["agy"]` sets `supports_variant=False`/`supports_agent=False`). Also correct `:139` ("The shipped default, which is off"), which describes tier 4 as ONE value and became per-host in child 01: it is off on opencode and on on antigravity. Write no em or en dashes.
  DO NOT WEAKEN ANY OF THE THREE INTO A TAUTOLOGY. Each currently pins a real property; each must still pin a real property after the edit. A test rewritten to assert only that the file exists, or a doc sentence that says nothing checkable, is a FAILED execution of this item even though the suite goes green.
  - Depends on: E-08
  - Expected outcome: both tests pin the NEW true property (agy in the `validate` chain, oc-only for `verify_with`) and pass; the doc names per-field, per-host honoring and the per-host tier 4; nothing was deleted or skipped.
  - Execution state: performed

- [x] E-07 Test the CHAIN end to end THROUGH EACH RUNNER, which is the gap the shipped tests leave. `tests/test_runner_profiles.py:862-994` (`ValidatePrecedenceMatrixTests`) and `:1389-1497` (`PerHostShippedPostureTests`) ALREADY pins all four tiers, both polarities, the absent-is-not-false case, the default-profile tier, and the measured strong-off / cheap-on split, at the RESOLVER level; read it first and do NOT duplicate it. What no test covers is that a stored profile value reaches the RUN, survives the freeze, and decides the verifier gate.
  Drive `initialize_run` on a real repository with `--prepare-only` (which exists on both hosts and is the shipped pattern at `tests/test_run_flag_surface.py:955-970`, whose `run_and_read_status` helper already drives BOTH runners against a temp repo and returns the frozen state; reuse it rather than rebuilding a harness) against an isolated store, and assert the FROZEN key for each host for: explicit flag beats a profile value; a profile value beats `defaults.validate`; `defaults.validate` beats the per-host registry row; and absence at every tier yields each host's OWN row value. Assert oc's `no_audit` agrees with `validate` in every case. Assert the tri-state does not collapse: a profile saying `validate: false` must be distinguishable from a profile OMITTING the field, since only the former is a decision.
  ON AGY THE "PROFILE" TIER IS THE PER-RUNNER DEFAULT PROFILE, NOT A NAMED ONE, and the test must be built that way or it cannot pass. agy declares no `--profile` and has no `as` clause (Step 0), so the only way a profile-level `validate` reaches an agy run is `defaults.profiles["agy"] = "<name>"`. Confirmed live at review: with that default set and the profile carrying `validate: false`, `resolve(cfg, runner="agy")` returns `False` with provenance `default-profile`. Write the agy rows against a store shaped that way, and note in the test that the provenance is `default-profile` rather than `profile` on that host.
  - Depends on: E-06
  - Expected outcome: the four-tier chain is pinned AT THE FROZEN-STATE LEVEL for BOTH hosts; the tri-state provably does not collapse; no resolver-level test is duplicated.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SHARED LIBRARY IS THE ESTABLISHED HOME FOR CROSS-DRIVER POLICY, and the repository states why in the code. `runner_shared.py` already owns `freeze_run_policy_flags` (`:2058-2084`) and `RUN_POLICY_FLAGS`, and `agy_runipd.py` binds 46 names from `oc_runipd` with an explicit comment that a duplicated copy "is how the deleted `_read_deps` pair came to be identically wrong in both drivers" and that `ruff` removing 6 re-exports was caught only by a cross-driver symmetry test. Add to the shared module; do not fork.
- `runner_shared` MAY IMPORT `runner_profiles` BUT NEVER A RUNNER. The admission rules (`runner_shared.py:32-37`) forbid importing either driver, at module level OR lazily, enforced by AST in `tests/test_runner_shared.py::NoRunnerImportTests` (which flags any module name containing `runipd`). `runner_profiles` is a peer, not a runner, and imports only `agent_workflows.config`, so there is no cycle. E-01 records the measurement.
- THERE IS NOW ONE `DriverError` CLASS, NOT TWO, and the authored plan's Step 0 said otherwise. Verified live at review: `oc_runipd.DriverError is agy_runipd.DriverError is runner_shared.DriverError` is `True`; the single definition is `runner_shared.py:170`, and `rununify` Order 02 (`818uru`) closed the two-class problem. agy's `enforce_dependency_preflight` wrapper survives only as a `RuntimeError` guard and its own comment says the translation half "was DELETED" (`agy_runipd.py:1343-1350`). So a shared helper needs no per-driver translation wrapper; the historical trap is closed and should not be rebuilt.
- THE HOSTS' FROZEN KEYS ARE OPPOSITE IN POLARITY, deliberately, and the code says so at length: `agy_runipd.py:3636-3643` states "NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`: this driver gates the verifier on `not no_verify` (verification defaults ON here), whereas `oc` gates on `validate` (which defaults OFF). The shared predicate takes `validate=`, so pass the locally-correct boolean rather than copying `oc`'s expression." That instruction IS this plan's design.
- `validate` is a genuine TRI-STATE by explicit design (`runner_profiles.py:41-44`, `_validate_tristate` at `:599`): ABSENT must never collapse to `false`, because an explicit flag must always beat a stored default. Both drivers must therefore pass `None` when the operator said nothing.
- oc's `initialize_run` freezes policy into `state["options"]` at queue build and treats a resume as bound by the frozen values; `resolve_launch_pair` (NOT `resolve_launch_profile`, see F-12) is deliberately its FIRST statement (`oc_runipd.py:2742`) so a bad profile refuses before any durable write, and the run directory is created 148 lines later at `:2891-2895`. Follow both; do not add a second mechanism.
- agy's `initialize_run` HAS NO PROFILE RESOLUTION AT ALL, so E-04's placement is a decision rather than a mirror. Its pre-durable refusal seam is the three shared calls at `agy_runipd.py:1788-1791`, and its run directory is created at `:1884-1885`.
- agy DECLARES NO `--profile` AND HAS NO `as <profile>` CLAUSE. Measured at review: `getattr(args, "profile", ...)` is absent on agy's parsed `start` namespace, and `extract_profile_clause` is oc-only (`oc_runipd.py:8081`). The tiers reachable on agy are the explicit flag, a per-runner DEFAULT profile (`defaults.profiles["agy"]`, which resolves without being named), `defaults.validate`, and the registry row.
- `--prepare-only` exists on both hosts and is how the shipped tests drive `initialize_run` without launching an agent.
- oc's `resume` already lets a passed `--validate` OVERWRITE the frozen value (`oc_runipd.py:8315-8318`, with a comment stating the behavior is preserved exactly). This plan changes where a NEW run's value comes from, not what a resume may do (OQ-02).
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The resolver is called WITHOUT the flag on oc, so tier 1 never registers as explicit, and the resolved value is never read. | `oc_runipd.py:2673-2685` (the live `resolve_launch_pair` executor call) passes `runner`, `profile`, `model`, `variant`, `agent`, `verify_with` and no `validate=`; the freeze site reads `getattr(args, "validate", False)` at `:3045-3046` |
| F-2 | Antigravity has ZERO profile integration: `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to nothing in `agy_runipd.py`. | `rg` over `agent_workflows/agy_runipd.py`, exit 1 |
| F-3 | **The postures are opposite, measured by driving BOTH real parsers.** A bare `oc start` yields `validate=False`; `--validate` yields `True`; `--no-validate` yields `False`. A bare `agy start` yields `no_verify=False` (verification ON); `--no-verify` yields `True`. agy has no `--validate` at all. | live parser probe 2026-09-06 re-measured at review `fac69fbd`; `oc_runipd.py:7857-7865`, `agy_runipd.py:4663-4669` |
| F-4 | **The inversion hazard, with its arithmetic.** agy freezes `no_verify` and gates on `not no_verify`, so writing a resolved `validate` into that key WITHOUT negating makes resolved `True` (verify) become `no_verify=True` (do not verify): verification requested and silently skipped. This is why E-01 forbids the helper from returning a host-shaped key and E-06 asserts both polarities. | `agy_runipd.py:2001`, `:3553-3559`, `:3636-3643`; `mn3gwr` F-5 |
| F-5 | `launch_profile_record` omits the `validate` VALUE but NOT the provenance, which arrives via `dict(resolved.provenance)`. Verified live: the record's provenance includes `'validate': 'defaults'` while `'validate' in record` is `False`. So E-05 adds ONE key, not two. | `oc_runipd.py:2703-2729`; live `launch_profile_record(resolve(cfg, runner="oc"))` |
| F-6 | **E-03's preferred mechanism breaks a shipped test, and that test is load-bearing.** `tests/test_novalnomerge_integration.py:47-79` (`ShippedDefaultReachabilityTests::test_shipped_defaults_are_validate_off_and_self_finalize_on`) walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`, pinning the PREMISE of executed plan `evgi9n`'s bug class. Under a `None` default `assertIs(None, False)` fails. `tests/test_oc_runipd.py:1966` uses `assertFalse` and survives `None`. | `tests/test_novalnomerge_integration.py:71-79`; `mn3gwr` F-9, independently re-measured |
| F-7 | **The divergence this plan must not deepen, measured.** The two runners define 67 top-level symbols in common: only 7 are byte-identical, 4 near (>=0.95), 20 similar, and 36 diverged below 0.80 (`initialize_run` 0.42, `build_parser` 0.54, `execute_item` 0.77 at 872/852 lines). But agy's genuinely host-specific surface is only 3 symbols and 455 lines of 4845 (`run_agy_turn` 361, `render_agy_event` 81, `resolve_agy` 13), and it already imports 38 oc-only symbols worth 1503 lines. So the sustainable shape is one shared driver plus small per-host adapters, and shared-library placement is what `rununify` is reaching for. | AST + `difflib` per-symbol comparison 2026-09-06 at `f3e17ff6` |
| F-8 | `no_audit` is DERIVED from `validate` at oc's freeze site and read by the verifier gate's compatibility branch plus five tests, so it must be derived from the RESOLVED value or the two frozen keys can disagree. | `oc_runipd.py:3045-3046`, `:6555-6557`; `tests/test_oc_runipd.py:2390`, `:2473`, `:2517`, `:2556`, `:2658` |
| F-9 | The capability was exercised historically and switched off on measured grounds, so this is a RESTORATION rather than a new feature: the verifier turn ran on every IPD across 13 runs through 2026-08-29, and the ~33% cost ruling is explicitly conditional on the primary model. | `evgi9n` F-6; 13 run directories carrying verification outcome files, latest `run-20260829T191652Z-4134000` |
| F-10 | agy has no `launch_profile` record to extend: `launch_profile_record` is among the 22 oc-only symbols agy does NOT import (`run_opencode`, `resolve_launch_profile`, `launch_profile_record`, `extract_profile_clause` and 18 others, 1027 lines). E-05 therefore covers oc only and must say so. | AST symbol-set difference minus agy's import list, measured 2026-09-06 |
| F-12 | **THE AUTHORED TARGET FUNCTION IS DEAD CODE, and this is the finding that would have silently voided the whole opencode half.** Executed plan `kgpptv` (merged `3798d236`, 2026-09-08, AFTER this plan was authored) replaced `initialize_run`'s call to `resolve_launch_profile` with `resolve_launch_pair`. MEASURED at review by AST-walking `oc_runipd.py` for calls to either name: `resolve_launch_pair` is called exactly ONCE (`:2742`), and `resolve_launch_profile` has ZERO callers anywhere in `agent_workflows/`; its only surviving references are `tests/test_oc_runipd.py`, `tests/test_runner_profiles_e2e.py`, and a docstring line in `run_dispatch.py:26`. An executor following the authored E-03 would have added `validate=` to a function no run executes: no behavior change, no test failure, and every resolver-level assertion still green. E-03 now names the live site and forbids threading the flag into the VERIFIER call. | AST call-graph walk at `fac69fbd`; `oc_runipd.py:2613` (def, unused) vs `:2652` (def) and `:2742` (sole call); `git log -S resolve_launch_pair` -> `3798d236` |
| F-13 | The live site resolves TWO launches from ONE store read and ASSERTS they share a `config_digest`, so the wiring has a constraint the authored plan did not know about. `resolve_launch_pair` calls `resolve()` twice: the executor (`:2673-2685`) and, only when `executor.verify_with` is set, the verifier profile (`:2686-2688`). Its docstring states ONE read is deliberate ("Two independent `runner_profiles.load()` calls would leave a window in which the file is edited between them"), and `:2694-2699` refuses if the digests differ. So the flag goes into the EXECUTOR call only, and no second `load()` may be added. | `oc_runipd.py:2652-2701`, docstring and assertion read at review |
| F-14 | **E-02's spelling as authored CRASHES EVERY `aw agy` INVOCATION AT PARSER BUILD.** The plan says to mirror oc's `--validate` flag, which oc spells with the aliases `("--validate", "--verify", "--audit")`. `BooleanOptionalAction` auto-generates a `--no-X` for every option string, so that list also generates `--no-verify` and `--no-audit`, both ALREADY declared on agy's `start` (`agy_runipd.py:4663-4669`). Measured on agy's real parser (default `conflict_handler="error"`, verified live): `ArgumentError: argument --validate/--no-validate/--verify/--no-verify/--audit/--no-audit: conflicting option strings: --no-verify, --no-audit`. The obvious workaround is worse: with `conflict_handler="resolve"` the new action SILENTLY STEALS `--no-verify`/`--no-audit` and `args.no_verify` ceases to exist, so agy's freeze site would read `False` unconditionally, which is verification-off-by-default on the host whose whole point is verification-on. The bare `--validate` form works: measured bare `None`, `--validate` `True`, `--no-validate` `False`, `no_verify` intact. Also measured: `--no-verify --validate` parses cleanly to `validate=True, no_verify=True`, so E-02's promised refusal is hand-written work, not an argparse freebie. | live probes at `fac69fbd` on `agy_runipd.build_parser()`; `agent_workflows/cli.py:611` (where `conflict_handler="resolve"` IS used, and `:3730` documents its measured in-place mutation hazard) |
| F-15 | **NO SHIPPED COMMAND CAN WRITE THE CONFIGURATION THIS PLAN MAKES EFFECTIVE ON AGY.** The wizard hardcodes `RUNNER = "oc"` (`runner_profile_wizard.py:76`) and the noninteractive `aw oc profile add` writes `"runner": wiz.RUNNER` (`cli.py:10153`), so every profile any shipped verb creates is an `oc` profile. `aw agy profile` does not exist (measured: `invalid choice: 'profile'`, exit 2). And `runner_profiles.set_validate_default`, the only writer for `defaults.validate`, has NO caller in the package (`grep -rn --include=*.py` finds the definition and `tests/test_runner_profiles.py` only). So after this plan the agy chain is exercisable ONLY by hand-editing `runner-profiles.json`. That is a legitimate ship-with-a-documented-manual-step, but it must be a DECISION and it must reach the docs; E-08 forces the choice. | `runner_profile_wizard.py:76`; `cli.py:10153`; live `aw agy profile list` exit 2; package-wide grep for `set_validate_default` |
| F-16 | **THREE SHIPPED ASSERTIONS PIN THE CLAIM THIS PLAN FALSIFIES, and one is invisible to the mandated bare suite.** (1) `tests/test_oc_runipd.py:5256-5273` asserts `agy_runipd` source contains `runner_profiles`, `resolve_launch_profile`, `launch_profile`, `verify_with` exactly ZERO times, message "the OC-only claim needs re-measuring"; it passes today (measured `2 passed`) and will fail in the BARE suite. (2) `tests/test_runner_profiles_e2e.py:852-869` asserts the same zero-count AND that the doc contains "does not read runner profiles"; BOTH halves break, and this file is `pytest.mark.slow` (`:58`) against `addopts = ... -m 'not slow'` (`pyproject.toml:169`), so the bare run deselects it (measured `no tests ran in 2.80s`) and a bare-only paste shows green while it is red. (3) `docs/runner-profiles.md:187-189` states the Antigravity runner "does not read runner profiles at all"; `:139` additionally still describes tier 4 as one shipped default "which is off", which child 01 already made per-host. E-09 owns all four. | `tests/test_oc_runipd.py:5256`; `tests/test_runner_profiles_e2e.py:58`, `:852`; `pyproject.toml:169`; `docs/runner-profiles.md:139`, `:187`; measured pass/deselect output at `fac69fbd` |
| F-17 | Every driver line citation in the authored plan had drifted, in the same way child 01's review measured (its PR-508). The `kgpptv` merge moved oc's freeze site from `:2969` to `:3045`, its verifier gate from `:6212` to `:6555`, agy's freeze site from `:1837` to `:2001`, its gate from `:3392` to `:3553`, its semantic-difference note from `:3474` to `:3636`, and agy's `--no-verify` declaration from `:4447` to `:4663`. Every cited construct still EXISTS and every claim about it is TRUE, so this is citation rot, not a false claim; all citations in this plan were re-resolved at `fac69fbd`. This is why the gate's RE-LOCATE BY SYMBOL rule is not optional advice. | all citations re-resolved at review; `git log -S` for the moving commit |

## Proposed changes (ordered, validatable)

1. One shared host-agnostic resolution helper in `runner_shared.py`, returning a decision and never a host key (E-01).
2. Give agy the `--validate`/`--no-validate` tri-state, keeping `--no-verify` as a working alias and refusing contradictions (E-02).
3. Wire oc: pass the tri-state in, consume the resolved value at the freeze site, keep `no_audit` consistent, update the pinning test deliberately (E-03).
4. Wire agy: negate at the boundary into its existing `no_verify` key, add no second key, preserve its verify-by-default floor (E-04).
5. Decide and record whether the agy capability gets a writer surface or a documented manual step (E-08).
6. Record the resolved value beside the provenance the record already carries, oc only, and say why agy has none (E-05).
7. Assert both polarities on both hosts, plus the empty-store floor (E-06).
8. Update the three shipped assertions and the published doc that assert agy reads no profile (E-09).
9. Pin the four-tier chain at the FROZEN-STATE level for both hosts (E-07).

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

- Over-scope: none. One shared module, both drivers at their existing freeze sites, the test files the change touches, and the one published doc whose claim the change falsifies.
- Scope-Paths justification: `runner_shared.py` hosts the new helper; `oc_runipd.py` and `agy_runipd.py` are each edited at their own freeze site and parser (unavoidable, since the whole point is that both hosts consume it); `tests/test_runner_shared.py` covers the helper and the polarity matrix; each driver's suite covers its own freeze; `tests/test_novalnomerge_integration.py` carries the pinning assertion F-6 measured as breaking.
- THREE PATHS WERE ADDED AT REVIEW, each because a MEASURED failure or a false published claim lands there (F-16). `tests/test_runner_profiles_e2e.py` holds the `slow`-marked zero-count assertion that breaks; `docs/runner-profiles.md` states "does not read runner profiles at all" and still describes tier 4 as one shipped default; `.aw/records/backlog/` is where E-08 option (a) files the writer-surface item. Without these three the plan would ship a red test invisible to the bare suite and a doc that contradicts the code.
- BOTH DRIVERS ARE IN SCOPE DELIBERATELY, unlike superseded `mn3gwr` which excluded `agy_runipd.py` because it could not reach that host. Child 01 removes that obstacle, so touching both is now the correct scope rather than an overreach. These are the two highest-contention modules in the repository: expect drift and re-locate by symbol.
- Under-scope: does not change the resolver, the registry, the precedence order, either default, or the diverged-symbol set. Each is excluded with a stated reason.

## Required tests / validation

- `python3 -m pytest` BARE, full suite, before and after, with the `N passed` summary line pasted and counts stated.
- `python3 -m pytest -m slow`, full slow subset, before and after, with its summary line pasted. THIS IS REQUIRED, NOT FLAG-BOLTING, and it is the same trap child 01's review recorded as its F-10: `tests/test_runner_profiles_e2e.py` is in Scope-Paths and is `pytest.mark.slow` (`:58`), so the configured `addopts` (`pyproject.toml:169`, `-m 'not slow'`) DESELECT it and a bare-only paste reports green while a Scope-Paths file is red. Measured at review: a direct `python3 -m pytest tests/test_runner_profiles_e2e.py` reports `no tests ran in 2.80s`. `-m slow` REPLACES the marker filter and adds nothing else.
- MEASURE YOUR OWN BEFORE-BASELINE AND JUDGE ON THE DELTA, do not compare to a number written in this plan. The authored baseline (`5462 passed, 3 skipped, 2 xfailed` at `f3e17ff6`) is stale, and child 01's review measured HEAD as NOT clean in both subsets (a pre-existing bare failure asserting a sibling plan's live status, plus 6 to 8 order-dependent slow failures). Run the suite BEFORE touching anything, record it, and require that after-minus-before is EMPTY. Do NOT fix an unrelated pre-existing failure inside this fence, and do NOT paste a red suite and call it expected without naming each pre-existing failure and showing it red in your own before-run.
- Targeted: `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_novalnomerge_integration.py`, `tests/test_runner_profiles.py`, and `tests/test_runner_profiles_e2e.py` under `-m slow`.
- A live before/after demonstration that a stored profile value actually changes the FROZEN verification decision of a real run ON EACH HOST, which is the whole point of the plan and is not shown by the resolver-level tests.
- VALIDATE IN THE REAL CHECKOUT for anything touching `tests/test_run_viewer.py`: it reads `.aw/records/runs/`, which is gitignored, so it fails in a bare worktree and passes in the real checkout. Green elsewhere proves nothing.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`). A pipe through `head` reports the pipe's status, which has already produced one false finding in this area.
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda`'s amended Section 1.3 records that skipping the independent verifier turn is a RETAINED, host-configurable choice rather than a prohibited bypass, and states that "until per-role model routing exists ... a host-level control is the only available mechanism" (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md:105`). This plan implements that mechanism FOR BOTH HOSTS, so no spec change is required and no spec edit is authorized here.

DO NOT EDIT SPEC `25kzda`'s §4.2 FINDING-CODE TABLE for any reason. `run_evidence.RUN_FINDING_CODES` transcribes those table cells VERBATIM and a test asserts byte equality, so editing a cell IS a code change; a note above the table already records this.

USER-FACING TEXT MAY NOW CLAIM BOTH HOSTS, which is the change from `mn3gwr`. If the executor writes or touches any user-facing description, it must be accurate about what ships: after this plan the per-model verification default is configuration on opencode AND antigravity, and still nothing for the four unregistered hosts. Do not imply parity beyond the two registered rows. Write no em or en dashes in user-facing prose.

THE DOC EDIT IS NOT OPTIONAL AND IS NOT MERELY PROSE (E-09, F-16). `docs/runner-profiles.md:187-189` currently states "The Antigravity runner does not read runner profiles at all", and `tests/test_runner_profiles_e2e.py:852-869` ASSERTS that sentence is present AND that `agy_runipd` contains zero profile symbols. So the doc claim is enforced by a shipped test: this plan cannot land without changing both, and leaving the doc alone means leaving the test red. The doc must end up stating PER FIELD which host honors what (`validate` on both; `verify_with`, `variant`, `agent` on opencode only, the latter two because `RUNNER_REGISTRY["agy"]` sets `supports_variant=False`/`supports_agent=False`), and must correct `:139` ("The shipped default, which is off"), which child 01 already made per-host (off on opencode, on on antigravity). If E-08 chooses option (a), the doc also carries the literal hand-edit JSON and the statement that no `aw` command writes it.

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
- Resolution or deferral rationale: No, and the existing behavior is deliberately preserved. `oc_runipd.py:8315-8318` currently lets a resume OVERWRITE the frozen `validate` when the flag is passed, with a comment stating that overwrite behavior is preserved exactly. This plan changes where a NEW run's value comes from, not what a resume may do. If the executor believes resume should refuse instead of overwrite, that is a separate decision and must not be folded in here.

### OQ-03: Should a stored profile value be allowed to turn verification ON for a run started with no flag?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, that is the entire purpose. The maintainer's measured position is per-model (off for the strong executor, on for a weaker one), and the `validate` field was built for exactly that. A stored value that could only turn verification OFF would leave the weak-model case still dependent on a remembered flag, which is the failure `vju5ba` recorded across five overnight runs. The explicit flag still wins when present, so an operator is never surprised in the direction they typed.

### OQ-04: No shipped command can write an agy profile or `defaults.validate`, so is the capability operator-reachable at all?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RAISED AT REVIEW (F-15) and resolved from repository evidence: SHIP THE WIRING WITH A DOCUMENTED MANUAL STEP, which is E-08. The gap is real and was measured, not inferred: the wizard hardcodes `RUNNER = "oc"` (`runner_profile_wizard.py:76`), `aw oc profile add` writes that constant (`cli.py:10153`), `aw agy profile` does not exist (live exit 2), and `runner_profiles.set_validate_default` has no caller anywhere in the package. So after this plan the agy chain is exercisable only by hand-editing `runner-profiles.json`. What decides the question is child 01's scope fence, which states "Do NOT widen the wizard to a second host": adding a writer here would contradict the immediately preceding child of this same Set, and a CLI surface is a separate design question (which verb, which host argument, how it relates to the oc-only wizard). Documenting the hand-edit is therefore the correct scope, and it is ONLY acceptable because the doc is a required deliverable with executed proof (V-08 makes the executor run the JSON it documents), not a promise. NON-BLOCKING because the wiring is correct and useful either way: the opencode half is fully reachable today through the existing wizard, and the antigravity half is reachable by hand. The follow-up writer surface is filed as backlog by E-08.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new helper's signature, docstring, and body. Confirm by inspection and state explicitly that it returns NO host-specific key (no `no_verify`, no writing into an options dict) and that it raises a neutral exception type each driver translates. Paste the tri-state behavior: called with `True`, `False`, and `None`, showing `None` falls through to the configured tier rather than being read as a decision. Paste `tests/test_runner_shared.py::NoRunnerImportTests` passing, which proves the new `runner_profiles` import did not trip the no-runner-import guard, and paste `python3 -c "import agent_workflows.runner_shared"` succeeding in a fresh interpreter (the guard's companion no-cycle check). State whether you raise `RunnerProfileError` or `DriverError` and confirm you added NO per-driver translation wrapper, citing the live check that there is now ONE `DriverError` class.
  - Observed evidence: PASS. Helper signature/body pasted; returns `VerificationDecision(validate, provenance)` with NO host key and no options-dict write; raises the ONE `runner_shared.DriverError` with no per-driver wrapper; tri-state driven live on both hosts; `NoRunnerImportTests` 2 passed and a fresh interpreter imports the module. Detail:
    SIGNATURE AND BODY, from `agent_workflows/runner_shared.py` (placed beside `freeze_run_policy_flags`,
    by symbol neighborhood as the gate requires):

    ```python
    class VerificationDecision(NamedTuple):
        validate: bool
        provenance: str

    def resolve_verification_decision(
        *,
        runner: str,
        profile: Optional[str] = None,
        validate: Optional[bool] = None,
    ) -> VerificationDecision:
        try:
            cfg = runner_profiles.load()
            resolved = runner_profiles.resolve(
                cfg, runner=runner, profile=profile, validate=validate
            )
        except runner_profiles.RunnerProfileError as exc:
            raise DriverError(f"runner profile: {exc}") from exc
        return VerificationDecision(
            validate=bool(resolved.validate),
            provenance=str(resolved.provenance.get("validate", "")),
        )
    ```

    NO HOST-SPECIFIC KEY, confirmed by inspection AND asserted mechanically. The return type's fields
    are exactly `("validate", "provenance")`; there is no `no_verify` field, and the function writes
    into no options dict (it returns a value and touches no caller state). `validate` is the decision
    in its POSITIVE sense, so each driver performs its own translation at its own freeze site.
    `tests/test_runner_shared.py::SharedVerificationResolutionTests::test_the_helper_returns_a_decision_and_never_a_host_key`
    pins this.

    THE TRI-STATE, driven live at an isolated `XDG_CONFIG_HOME`:

    ```
    oc flag= True VerificationDecision(validate=True, provenance='explicit')
    oc flag= False VerificationDecision(validate=False, provenance='explicit')
    oc flag= None VerificationDecision(validate=False, provenance='shipped-default')
    agy flag= True VerificationDecision(validate=True, provenance='explicit')
    agy flag= False VerificationDecision(validate=False, provenance='explicit')
    agy flag= None VerificationDecision(validate=True, provenance='shipped-default')
    ```

    `None` FALLS THROUGH (provenance `shipped-default`, i.e. the configured chain decided, not the
    flag) while `False` registers as `explicit`. With a store carrying `defaults.validate: true`,
    `None` resolves `True`/`defaults` and `False` resolves `False`/`explicit`
    (`test_the_tristate_does_not_collapse`), so absence is provably not read as a decision.

    THE IMPORT GUARD, which the new module-level `from agent_workflows import runner_profiles` had to
    survive:

    ```
    $ python3 -m pytest tests/test_runner_shared.py::NoRunnerImportTests -o addopts="-p no:randomly"
    tests/test_runner_shared.py ..                                           [100%]
    ============================== 2 passed in 0.46s ===============================
    $ python3 -c "import agent_workflows.runner_shared as m; print('fresh import OK:', m.__name__)"
    fresh import OK: agent_workflows.runner_shared
    ```

    THE EXCEPTION TYPE: `runner_shared.DriverError`, raised directly, with NO per-driver translation
    wrapper added. The live check that this is legitimate:
    `test_a_malformed_store_raises_the_one_driver_error_class` asserts
    `oc_runipd.DriverError is agy_runipd.DriverError is runner_shared.DriverError` and then that a
    malformed store (`defaults.validate: "yes"`) raises that one class with the resolver's own
    diagnostic. So both drivers' existing `except DriverError` in `main` catch it and exit 2.

  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste parsed-args output from driving agy's REAL parser for four invocations, showing BOTH `validate` AND `no_verify` in every row: bare `start` (expect `validate=None`, `no_verify=False`), `--validate` (`True`, `False`), `--no-validate` (`False`, `False`), and `--no-verify` (`None`, `True`). SHOWING `no_verify` IS MANDATORY, NOT DECORATION: F-14 measured that the wrong argparse spelling makes that attribute CEASE TO EXIST, which silently turns antigravity's verification off by default, and a paste that omits it cannot detect that. An `AttributeError` or a sentinel where `no_verify` should be is a FAILED validation. Paste `agy_runipd.build_parser()` completing without raising, and `aw agy --help >/dev/null 2>&1; echo $?` as `0`, since the aliased spelling F-14 forbids raises at parser-build time and would break every invocation. Paste the exit code and message for the CONTRADICTORY pair `--no-verify --validate`, measured UNPIPED, showing a refusal rather than a silent winner, and confirm the refusal happens BEFORE any run directory is created (show that no new directory appeared under the state root). Confirm `--no-verify` alone still behaves exactly as before.
  - Observed evidence: PASS. Four agy invocations plus the contradictory pair pasted with BOTH `validate` AND `no_verify` present in every row; `aw agy --help` exit 0; `--no-verify --validate` refused unpiped with exit 2 and no run directory created. Detail:
    AGY'S REAL PARSER, four invocations plus the contradictory pair, showing BOTH attributes in every
    row (`no_verify` is shown because its ABSENCE is the F-14 silent-bypass signature):

    ```
    []                               validate=None   no_verify=False
    ['--validate']                   validate=True   no_verify=False
    ['--no-validate']                validate=False  no_verify=False
    ['--no-verify']                  validate=None   no_verify=True
    ['--no-audit']                   validate=None   no_verify=True
    ['--no-verify', '--validate']    validate=True   no_verify=True
    ```

    `no_verify` is PRESENT and correct in every row: no `AttributeError`, no sentinel. `--no-verify`
    alone behaves exactly as before (`no_verify=True`, `validate` untouched at `None`), and
    `--no-audit` remains its alias. Pinned by
    `tests/test_runner_shared.py::AgyVerificationFlagSurfaceTests::test_the_tristate_parses_and_no_verify_still_exists`.

    PARSER BUILDS, so the aliased spelling F-14 forbids was not used:

    ```
    $ python3 -m agent_workflows.agy_runipd --help >/dev/null 2>&1; echo "EXIT=$?"
    EXIT=0
    $ aw agy --help >/dev/null 2>&1; echo "EXIT=$?"
    EXIT=0
    ```

    `build_parser()` also now ASSERTS the two spellings did not collide
    (`assert_verification_flags_are_distinct`), which is a stronger guarantee than "it happened to
    build": a future edit that registers `--validate` with oc's alias list, or sets
    `conflict_handler="resolve"`, is refused by name rather than silently stealing `--no-verify`.
    `test_a_stolen_flag_is_refused_at_the_parser_not_silently_accepted` builds the stolen parser
    deliberately and asserts the refusal.

    THE CONTRADICTORY PAIR, measured UNPIPED (redirected to a file, then `echo $?`, so no pipe status
    is read):

    ```
    $ python3 -m agent_workflows.agy_runipd start nonexistent --repo . --no-verify --validate >/tmp/refuse.out 2>&1; echo "EXIT=$?"
    EXIT=2
    $ head -3 /tmp/refuse.out
    runagy: --no-verify (or --no-audit) and --validate contradict each other: one asks to skip turn-2 verification and the other asks to run it. Pass exactly one; --no-verify is the same request as --no-validate
    ```

    A refusal, not a silent winner. BEFORE ANY DURABLE WRITE, asserted directly by
    `test_the_refusal_happens_before_any_durable_run_state`, which drives the real `initialize_run` on
    a temp repo and then asserts `list(runs.glob("run-*")) == []`, i.e. no new run directory appeared
    under the state root. An AGREEING pair (`--no-verify --no-validate`) is accepted and resolves to
    `False`.

  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the resolved `validate` and its provenance for three oc invocations: no flag (provenance NOT `explicit`), `--validate` (`True`/`explicit`), `--no-validate` (`False`/`explicit`). STATE WHICH MECHANISM YOU CHOSE, (a) the `None` default or (b) argv inspection, and why. If (a): paste the UPDATED `tests/test_novalnomerge_integration.py` assertion and its passing output, and state in one sentence what it now pins (it must still pin that a bare invocation verifies OFF). A paste showing that test failing, skipped, xfailed, or deleted is a FAILED validation. Paste the first statement of `initialize_run` showing the resolution call was not moved, AND paste the re-measured call-graph probe from the gate showing WHICH function that call names, so it is proven you wired the live site and not `resolve_launch_profile` (F-12). Paste the verifier `resolve()` call showing it received NO `validate=` argument, and paste the `config_digest` assertion still present and intact (F-13).
  - Observed evidence: PASS. Mechanism (a) chosen and why; three oc invocations with provenance; the pinning test UPDATED and passing while still pinning a bare invocation verifying OFF; re-measured call-graph probe shows the ONE live call is `resolve_launch_pair`, still the first statement; the verifier `resolve()` takes no `validate=` and the `config_digest` assertion is intact. Detail:
    MECHANISM CHOSEN: OPTION (a), the `None` default on `start`. Why: the flag genuinely IS a
    tri-state now, `resume` has always shipped `default=None` for exactly this reason, and argv
    inspection would put a second, weaker copy of argparse's own knowledge in the driver. The plan
    named (a) as preferred and the measurement below confirms nothing else depends on the literal.

    THREE OC INVOCATIONS, resolved value and provenance, at an isolated store:

    ```
      []                 args.validate=None   resolved=False  provenance='shipped-default'
      ['--validate']     args.validate=True   resolved=True   provenance='explicit'
      ['--no-validate']  args.validate=False  resolved=False  provenance='explicit'
    ```

    No flag is NOT `explicit` (it is `shipped-default`, so the chain decided); both explicit spellings
    are `explicit`.

    THE UPDATED PINNING TEST, `tests/test_novalnomerge_integration.py::ShippedDefaultReachabilityTests::test_shipped_defaults_are_validate_off_and_self_finalize_on`.
    It now asserts the parser default is `None` (the tri-state) AND, at an isolated
    `XDG_CONFIG_HOME`, that the EFFECTIVE default is still verification OFF with provenance
    `shipped-default`. IN ONE SENTENCE: it pins that a bare `aw oc run` still does not verify, which
    is the property `evgi9n`'s bug class actually depends on, rather than the parser literal that used
    to stand in for it. Passing:

    ```
    $ python3 -m pytest tests/test_novalnomerge_integration.py -o addopts="-p no:randomly"
    ...
    FAILED tests/test_novalnomerge_integration.py::EndToEndIntegrationTests::test_validation_off_run_records_the_suite_signal_not_a_stranded_item
    1 failed, 22 passed in 1.26s
    ```

    The one failure is PRE-EXISTING (it appears in the before-baseline below, caused by an unrelated
    `begin refused (no execution authority)` condition in this worktree) and is NOT
    `ShippedDefaultReachabilityTests`, which passes. The test was neither deleted, skipped, nor
    xfailed.

    THE LIVE SITE, re-measured at execution rather than trusted from the plan:

    ```
    $ python3 -c "...ast walk of oc_runipd for calls to resolve_launch*..."
      first statement: resolved_launch, resolved_verify = resolve_launch_pair(args)
      calls to resolve_launch*: [('resolve_launch_pair', 2761)]
    ```

    ONE call, to `resolve_launch_pair`, and it is still the FIRST statement of `initialize_run`
    (`resolve_launch_profile` still has zero callers, so the authored target really was dead code).
    The resolution was not moved.

    THE VERIFIER CALL RECEIVED NO `validate=`, and the digest assertion is intact:

    ```python
    verifier = runner_profiles.resolve(
                cfg, runner="oc", profile=executor.verify_with
            )
    ...
    if verifier.config_digest != executor.config_digest:
        raise DriverError(
            "runner profile: the executor and verifier launches were resolved from different "
            "configurations; refusing rather than freezing an inconsistent pair"
    ```

    THE FREEZE SITE now reads the resolved value, with `no_audit` derived from the SAME value so the
    two keys cannot disagree:

    ```python
    "validate": resolved_launch.validate,
    "no_audit": not resolved_launch.validate,
    ```

    No second `runner_profiles.load()` was added.

  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste agy's frozen `options` block from a real `--prepare-only` invocation showing `no_verify`, for BOTH a resolved-verify and a resolved-do-not-verify case, and show the negation is correct in both directions. Paste the frozen options in full and confirm NO `validate` key was added. Quote agy's verifier gate expression showing it is still `not no_verify`, unchanged. Paste the empty-store bare invocation showing agy STILL VERIFIES.
  - Observed evidence: PASS. agy's frozen `no_verify` pasted for both directions from real `--prepare-only` runs; no `validate` key added; gate expression still `not no_verify`; empty-store bare invocation still verifies; SABOTAGE CHECK removing the negation turned 8 assertions red. Detail:
    AGY'S FROZEN OPTIONS from real `--prepare-only` runs against an isolated store, BOTH directions.
    Driven through the real `initialize_run` by
    `tests/test_runner_shared.py::VerificationPolarityTests`, whose captured output is:

    ```
    POLARITY MATRIX: resolved verify -> oc validate=True / agy no_verify=False; resolved do-not-verify -> oc validate=False / agy no_verify=True
    EMPTY-STORE FLOOR: oc validate=False; agy no_verify=False (verifies)
    ```

    And from the live demonstration driving the documented store:

    ```
    === AFTER: doc block 1 (agy profile validate:false via defaults.profiles) ===
      agy frozen no_verify = True (True = does NOT verify, as documented)
      agy --validate       = False (False = explicit flag still wins)
      agy frozen has 'validate' key: False
    === AFTER: doc block 2 (defaults.validate: true) ===
      agy frozen no_verify = False (False = verifies)
    ```

    THE NEGATION IS CORRECT IN BOTH DIRECTIONS: resolved verify gives `no_verify=False`, resolved
    do-not-verify gives `no_verify=True`.

    NO `validate` KEY WAS ADDED to agy's frozen options: `agy frozen has 'validate' key: False`, also
    asserted by `test_agy_freezes_no_validate_key_and_its_gate_expression_is_unchanged`.

    AGY'S VERIFIER GATE EXPRESSION IS UNCHANGED, still `not no_verify`:

    ```python
    if (
        not is_review
        and disposition in ("executed", "substantially-complete")
        and not no_verify
    ):
    ```

    EMPTY STORE, BARE INVOCATION: agy STILL VERIFIES (`no_verify=False`), pinned by
    `test_the_empty_store_floor_is_unchanged_on_both_hosts`.

    THE HELPER IS CALLED BEFORE ANY DURABLE WRITE: the call sits in `initialize_run` immediately after
    the three shared refusals and BEFORE `run_dir` is created, and
    `test_the_refusal_happens_before_any_durable_run_state` proves a refusing invocation leaves no
    `run-*` directory.

    SABOTAGE CHECK, because this is the item the gate calls the whole risk of the plan. The negation
    was deliberately removed (`"no_verify": verification.validate`) and the suite was re-run:

    ```
    SABOTAGED: negation removed
    FAILED tests/test_runner_shared.py::VerificationPolarityTests::test_all_four_polarity_cells
    FAILED tests/test_runner_shared.py::VerificationPolarityTests::test_oc_and_agy_agree_on_the_decision_for_the_same_store
    FAILED tests/test_runner_shared.py::VerificationPolarityTests::test_the_empty_store_floor_is_unchanged_on_both_hosts
    FAILED tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_a_profile_omitting_validate_is_not_a_profile_saying_false
    FAILED tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_tier_1_explicit_flag_beats_a_stored_profile_value
    FAILED tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_tier_2_a_profile_value_beats_defaults_validate
    FAILED tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_tier_3_defaults_validate_beats_the_per_host_registry_row
    FAILED tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_tier_4_absence_yields_each_hosts_own_row
    8 failed, 2 passed, 79 deselected in 2.98s
    ```

    The inversion is DETECTED, not merely reviewed. Restored and re-verified green
    (`10 passed, 79 deselected`).

  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `options.launch_profile` from a real oc `state.json` showing the `validate` VALUE and the provenance tier, for at least two different tiers (for example `explicit` and one configured tier). Paste the pre-existing test that renders an OLDER `launch_profile` record lacking the new key, still passing. State explicitly that agy gained no equivalent record and where that gap is recorded.
  - Observed evidence: PASS. `options.launch_profile` pasted at two tiers (`explicit` and `defaults`) showing the VALUE with the tier read from the existing provenance mapping; the older-record rendering test still passes; agy's lack of an equivalent asserted and recorded. Detail:
    OC'S `options.launch_profile` from real runs, at TWO different tiers:

    ```
    === explicit ===
      oc  --validate       = validate: True tier: explicit
    === a configured tier (defaults.validate: true) ===
      oc  frozen validate  = True no_audit = False
      oc  launch_profile   = validate: True tier: defaults
    ```

    The VALUE is present and the TIER is read from the `provenance` mapping the record already
    carried, not duplicated: the record has ONE new key. Pinned by
    `tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_oc_records_the_resolved_value_beside_its_provenance_tier`,
    which asserts `explicit`/`True` and `defaults`/`True`.

    BACKWARD COMPATIBILITY: the pre-existing test rendering an OLDER record that lacks the key
    (`tests/test_oc_runipd.py`, the case whose fixture is `"launch_profile": {"applied": "gem"}` with
    the comment "A run created before `launch_profile` existed must still render, not raise") passes
    in the full bare suite below; nothing reads the new key non-defensively.

    AGY GAINED NO EQUIVALENT RECORD, stated explicitly and asserted:
    `test_oc_records_the_resolved_value_beside_its_provenance_tier` ends with
    `assertNotIn("launch_profile", frozen("agy_runipd", [], None))`. The gap is recorded in this
    plan's "Deferred / out of scope" section (a provenance record for agy is a durable-state addition
    with its own compatibility surface, belonging with the registry-consolidation work), so it is
    recorded rather than silently accepted.

  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: THE SAFETY-CRITICAL PASTE. A four-cell matrix from ACTUAL test output: resolved verify -> oc `validate=True` AND agy `no_verify=False`; resolved do-not-verify -> oc `validate=False` AND agy `no_verify=True`. All four cells must be shown; a paste covering one host or one direction is a FAILED validation because it cannot detect the inversion. Also paste the empty-isolated-store floor for both hosts (oc OFF, agy ON) and confirm `XDG_CONFIG_HOME` pointed at a temp dir so the maintainer's real store was never read or written.
  - Observed evidence: PASS. All FOUR polarity cells pasted from actual test output plus the empty-store floor for both hosts; `XDG_CONFIG_HOME` pointed at a temp dir throughout, so the real store was never read or written. Detail:
    THE FOUR-CELL MATRIX, from ACTUAL test output (captured stdout of
    `tests/test_runner_shared.py::VerificationPolarityTests`, which reads each host's real frozen
    `state.json` after driving `initialize_run --prepare-only`):

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="-p no:randomly -s" -k VerificationPolarityTests
    POLARITY MATRIX: resolved verify -> oc validate=True / agy no_verify=False; resolved do-not-verify -> oc validate=False / agy no_verify=True
    EMPTY-STORE FLOOR: oc validate=False; agy no_verify=False (verifies)
    ======================= 4 passed, 86 deselected in 1.64s =======================
    ```

    All FOUR cells, spelled out:

    | resolved decision | oc frozen `validate` | agy frozen `no_verify` |
    |---|---|---|
    | verify | `True` | `False` |
    | do not verify | `False` | `True` |

    Each cell is a separate `assertIs` with its own message (`"cell 1: oc, resolved verify"` etc.), and
    oc's `no_audit` is asserted to agree in both rows.

    THE EMPTY-STORE FLOOR, both hosts: oc `validate=False` (does not verify) and agy
    `no_verify=False` (STILL VERIFIES). An agy run showing verification OFF here would have failed the
    assertion; it does not.

    NO REAL STORE WAS READ OR WRITTEN. Every case wraps its work in
    `mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": td})` with `td` a `TemporaryDirectory`, and
    `runner_profiles.store_path()` derives from `config.config_dir()`, which honors that variable. The
    helper writes the fixture store inside that temp dir only.

    THE MATRIX DETECTS THE INVERSION rather than merely describing it: see the sabotage check pasted
    under V-04, where removing the single `not` turned 8 of these assertions red.

  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the ACTUAL output of the five targeted test modules and of the BARE full suite (`python3 -m pytest`, no added flags) with its `N passed` summary line, stating before/after counts. Paste the frozen-state result for each of the four tiers on EACH host (explicit beats profile; profile beats `defaults`; `defaults` beats the registry row; absence yields the row). Paste the case distinguishing a profile that says `validate: false` from one that OMITS the field, proving the tri-state did not collapse. Confirm oc's `no_audit` agreed with `validate` in every case, and confirm no resolver-level test from `tests/test_runner_profiles.py:862-994` (`ValidatePrecedenceMatrixTests`) and `:1389-1497` (`PerHostShippedPostureTests`) was duplicated.
  - Observed evidence: PASS. Four-tier chain pinned at the FROZEN-STATE level on both hosts; tri-state proven not to collapse; oc's `no_audit` agrees with `validate` in every case; no resolver-level test duplicated; bare suite before 17 failed/6740 passed, after 17 failed/6760 passed, DELTA EMPTY. Detail:
    THE FOUR TIERS AT THE FROZEN-STATE LEVEL, on BOTH hosts, in
    `tests/test_runner_shared.py::VerificationChainFrozenStateTests`. Each case drives the real
    `initialize_run` with `--prepare-only` against an isolated store and reads the host's OWN frozen
    key through `verifies()`, which asserts oc's `no_audit` agrees with `validate` on every read:

    | tier | oc | agy |
    |---|---|---|
    | 1 explicit flag beats a stored profile value | `--validate` over profile `validate:false` -> verifies | `--no-validate` AND `--no-verify` over profile `validate:true` -> does not verify |
    | 2 a profile value beats `defaults.validate` | profile `true` over defaults `false` -> verifies | same, via `defaults.profiles.agy` |
    | 3 `defaults.validate` beats the registry row | defaults `true` over row `False` -> verifies | defaults `false` over row `True` -> does not verify |
    | 4 absence yields the host's OWN row | no store -> does not verify | no store -> verifies |

    Tier 3 is deliberately written to OPPOSE each host's own row (true on oc, false on agy), so it
    cannot pass by coincidence.

    THE TRI-STATE DOES NOT COLLAPSE, at the frozen level
    (`test_a_profile_omitting_validate_is_not_a_profile_saying_false`): a profile OMITTING `validate`
    falls through to the host row (oc does not verify, agy DOES), while a profile with a PRESENT
    `validate: false` makes both hosts not verify. Only the present value is a decision.

    ON AGY THE PROFILE TIER IS THE PER-RUNNER DEFAULT PROFILE, as the plan requires: every agy row is
    built with `defaults: {profiles: {agy: "p"}}` because that host declares no `--profile`, and the
    provenance is `default-profile` rather than `profile`.

    NO RESOLVER-LEVEL TEST WAS DUPLICATED. `tests/test_runner_profiles.py::ValidatePrecedenceMatrixTests`
    and `::PerHostShippedPostureTests` are untouched (that file is not in this plan's diff at all) and
    these cases assert on FROZEN STATE, which is the gap they leave.

    TARGETED MODULES:

    ```
    $ python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_novalnomerge_integration.py tests/test_runner_profiles.py
    14 failed, 477 passed in 12.67s
    ```

    All 14 are pre-existing (see the delta below); the new tests all pass.

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="-p no:randomly" -k "SharedVerificationResolution or VerificationPolarity or VerificationChainFrozenState or AgyVerificationFlagSurface"
    ====================== 19 passed, 70 deselected in 3.80s =======================
    ```

    THE BARE FULL SUITE, before and after, with the delta:

    ```
    BEFORE (at fa6c6727, before any edit):
    17 failed, 6740 passed, 3 skipped, 2 xfailed in 234.44s (0:03:54)

    AFTER (final, at 400d6407):
    17 failed, 6760 passed, 3 skipped, 2 xfailed in 74.68s (0:01:14)

    DELTA (set difference of FAILED node ids):
    NEW: NONE
    FIXED: NONE
    ```

    AFTER MINUS BEFORE IS EMPTY: the same 17 pre-existing failures, and 20 more tests passing. The 17
    are unrelated to this plan and were red before I touched anything; they cluster in
    `WorktreeIsolationTests` / `FailClosedIntegrationGuardTests` / `SelfFinalizeHelperTests` /
    `BeginCliTests` / `test_worker_role_refusal` on both hosts, all failing on the same
    `begin refused (no execution authority)` lifecycle-role condition of running inside a managed
    lane. I did not fix them, per the fence.

    ONE REGRESSION WAS FOUND AND FIXED DURING EXECUTION, not carried: my first `agy` implementation
    raised on an absent `no_verify` attribute, which broke three shipped tests that legitimately build
    partial `Namespace` objects (`test_run_order_announcement.py` x2,
    `test_orchestrator_retirement.py` x1). The check was moved to where the hazard is actually
    decidable (the parser) and those tests pass:
    `236 passed in 17.84s` for `tests/test_runner_shared.py tests/test_run_order_announcement.py tests/test_orchestrator_retirement.py`.

  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste the added `docs/runner-profiles.md` passage showing the literal JSON for an `agy` profile INCLUDING its `defaults.profiles` entry AND for `defaults.validate`, and paste the sentence stating no `aw` command writes either. Paste the created backlog item's id6 and path. Paste the re-measured reachability probe, so the claim is current at execution rather than quoted from review: `grep -rn "set_validate_default" --include=*.py .` and `aw agy profile list >/dev/null 2>&1; echo $?` (expect 2). PROVE THE DOCUMENTED JSON ACTUALLY WORKS: write exactly the JSON you documented into an isolated `XDG_CONFIG_HOME`, run a real `--prepare-only` agy invocation against it, and paste the frozen `no_verify` showing the documented configuration produced the documented effect. A doc example that was never executed is not evidence. Confirm NO CLI or wizard file was modified (`git diff --stat` over `agent_workflows/cli.py` and `agent_workflows/runner_profile_wizard.py` empty). Confirm `aw sanitize --agent` is clean, since a hand-edit example must not contain a real home path.
  - Observed evidence: PASS. Doc passage with both literal JSON blocks (including `defaults.profiles`) and the no-writer sentence pasted; backlog `fxiqse` created; reachability probe re-measured; the documented JSON EXECUTED against a real run (which caught and fixed an invalid model identifier); cli/wizard untouched; `aw sanitize --agent` clean. Detail:
    THE ADDED DOC PASSAGE, `docs/runner-profiles.md`, section "Setting the verification default on
    antigravity, by hand":

    ```
    No `aw` command writes an antigravity profile or `defaults.validate` yet. The profile wizard and
    `aw oc profile add` create opencode profiles only, and `aw agy profile` does not exist. Until a
    writer surface ships, edit `~/.config/agent-workflows/runner-profiles.json` yourself.

    Antigravity accepts no `--profile` flag and has no `as <profile>` clause, so a profile reaches an
    antigravity run ONLY by being that host's default profile. Both parts are required:

    {
      "schema_version": 2,
      "profiles": {
        "agy-quiet": {"runner": "agy", "model": "google/gemini-3-pro", "validate": false}
      },
      "defaults": {
        "profiles": {"agy": "agy-quiet"}
      }
    }

    With that store, `aw agy run <selector>` skips the verifier turn, and `aw agy run --validate
    <selector>` still runs it, because an explicit flag always wins.

    To set one default for every host and profile that does not state its own, use `defaults.validate`:

    {
      "schema_version": 2,
      "defaults": {"validate": true}
    }
    ```

    Both blocks are present, the `defaults.profiles` entry is included (without it the profile would
    never apply on that host), and the sentence stating no `aw` command writes either is the first
    line.

    THE BACKLOG ITEM: id6 `fxiqse`, at
    `.aw/records/backlog/open/20260913-fxiqse-01-fxiqse-agy-profile-writer-surface.backlog.md`
    ("Add a writer surface for antigravity runner profiles and defaults.validate"), created with
    `aw backlog new --apply`; `aw backlog check: all backlog items conform.`

    THE REACHABILITY PROBE, RE-MEASURED AT EXECUTION rather than quoted from review:

    ```
    $ grep -rn "set_validate_default" --include=*.py .
    ./tests/test_runner_profiles.py:671:        cfg = RP.set_validate_default(RP.empty_config(), True)
    ./tests/test_runner_profiles.py:673:        self.assertIs(RP.set_validate_default(cfg, False).validate, False)
    ./tests/test_runner_profiles.py:674:        self.assertIsNone(RP.set_validate_default(cfg, None).validate)
    ./tests/test_runner_profiles.py:676:            RP.set_validate_default(cfg, "yes")  # type: ignore[arg-type] - negative test
    ./tests/test_runner_profiles.py:874:            cfg = RP.set_validate_default(cfg, defaults_validate)
    ./tests/test_runner_profiles.py:1890:                    cfg = RP.set_validate_default(RP.empty_config(), level)
    ./tests/test_runner_profiles.py:1895:            RP.set_validate_default(RP.empty_config(), False), runner="agy"
    ./agent_workflows/runner_profiles.py:1328:def set_validate_default(cfg: ProfileConfig, value: Optional[bool]) -> ProfileConfig:
    $ aw agy profile list >/dev/null 2>&1; echo "EXIT=$?"
    EXIT=2
    ```

    The definition and its own unit tests only: still NO caller in the package, and `aw agy profile`
    still does not exist. The claim is current.

    THE DOCUMENTED JSON WAS ACTUALLY EXECUTED, extracted LITERALLY from the shipped doc (not retyped)
    and fed to real `--prepare-only` runs at an isolated `XDG_CONFIG_HOME`:

    ```
    extracted 2 JSON blocks from the doc section

    === BEFORE: no store at all ===
      agy frozen no_verify = False (False = VERIFIES, the shipped agy floor)
      oc  frozen validate  = False (False = does NOT verify, the shipped oc floor)

    === AFTER: doc block 1 (agy profile + defaults.profiles) ===
      agy frozen no_verify = True (True = does NOT verify, as documented)
      agy --validate       = False (False = explicit flag still wins)
      agy frozen has 'validate' key: False

    === AFTER: doc block 2 (defaults.validate: true) ===
      agy frozen no_verify = False (False = verifies)
      oc  frozen validate  = True no_audit = False
      oc  launch_profile   = validate: True tier: defaults
      oc  --validate       = validate: True tier: explicit
    ```

    THIS REQUIREMENT CAUGHT A REAL DEFECT, which is worth recording because it is exactly why the gate
    demands execution rather than prose: the first draft of the doc wrote `"model": "gemini-3-pro"`,
    and the real loader REFUSED it (`invalid model 'gemini-3-pro': expected an exact 'provider/model'
    identifier`). The doc was corrected to `google/gemini-3-pro` and a new test,
    `tests/test_runner_profiles_e2e.py::PublishedContractParityTests::test_the_documented_hand_edit_json_is_actually_valid`,
    now extracts both blocks from the shipped doc and resolves them, so the example cannot silently
    rot again. A second new case,
    `test_the_doc_states_no_aw_command_writes_the_agy_configuration`, re-measures the
    `set_validate_default` caller set in CI and fails if a writer appears while the doc still claims
    none exists.

    NO CLI OR WIZARD FILE WAS MODIFIED:

    ```
    $ git diff --stat -- agent_workflows/cli.py agent_workflows/runner_profile_wizard.py
    (empty)
    ```

    LEAK SCAN CLEAN, so the hand-edit example carries no real home path:

    ```
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste the BEFORE failure and the AFTER pass for BOTH tests, by name: `tests/test_oc_runipd.py::VerifierRoutingHostAsymmetryTests::test_the_agy_runner_has_no_profile_integration_at_all` and `tests/test_runner_profiles_e2e.py::PublishedContractParityTests::test_the_doc_states_the_verify_with_limits_rather_than_implying_parity`. The second MUST be run with `python3 -m pytest -m slow`, and a paste reading `no tests ran` is a FAILED validation, not evidence: that file is `pytest.mark.slow` and the bare suite deselects it (measured `no tests ran in 2.80s`). Paste the rewritten assertion bodies and state in one sentence, per test, what real property each now pins; a rewrite that only asserts a file exists, or that deletes/skips/xfails either test, is a FAILED validation. Confirm the `verify_with` half of each assertion SURVIVED, since that limit is still true. Paste the `docs/runner-profiles.md` diff showing the per-field per-host honoring and the corrected per-host tier 4, plus `python3 -c "from agent_workflows import docs_check; print([str(f) for f in docs_check.check_doc('docs/runner-profiles.md')])"` clean, and confirm no em or en dash was introduced.
  - Observed evidence: PASS. Both tests' before/after pasted by name (test 1 was a FALSE NEGATIVE rather than a failure, stated honestly; test 2 red under `-m slow` then 34 passed); rewritten assertions each pin a real property and the `verify_with` halves survived; doc diff and clean `docs_check` pasted. Detail:
    TEST 1, `tests/test_oc_runipd.py::VerifierRoutingHostAsymmetryTests`. HONEST ACCOUNT OF THE
    BEFORE STATE, which differs from what the plan predicted and matters: because E-01 put the
    resolution in `runner_shared` (as the plan REQUIRED), `agy_runipd` never gains the literal string
    `runner_profiles`, so the old zero-count assertion did NOT go red. Measured after the wiring:

    ```
    $ grep -c 'runner_profiles\|resolve_launch_profile\|launch_profile\|verify_with' agent_workflows/agy_runipd.py
    0
    $ python3 -m pytest tests/test_oc_runipd.py::VerifierRoutingHostAsymmetryTests -o addopts=""
    tests/test_oc_runipd.py ..                                               [100%]
    ============================== 2 passed in 0.19s ===============================
    ```

    So it was a FALSE NEGATIVE, not a failure: it kept asserting "antigravity has no profile
    integration" while that host had just joined the `validate` chain. Rewriting it was therefore
    MORE necessary, not less, and it is recorded here rather than papered over.

    AFTER, rewritten and passing:

    ```
    $ python3 -m pytest tests/test_oc_runipd.py::VerifierRoutingHostAsymmetryTests -o addopts="-p no:randomly"
    tests/test_oc_runipd.py ..                                               [100%]
    ============================== 2 passed in 0.44s ===============================
    ```

    WHAT IT NOW PINS, in one sentence: that `verify_with` MODEL ROUTING is still opencode-only (agy
    references `verify_with`/`launch_profile`/`resolve_launch_profile` zero times and has no
    `launch_profile_record` or `resolve_launch_pair` attribute) WHILE agy does participate in the
    `validate` chain through the shared helper, proven by resolving a real store with
    `defaults.validate: false` and asserting the decision is `False` with provenance `defaults`. The
    `verify_with` half of the original assertion SURVIVED unchanged.

    TEST 2, `tests/test_runner_profiles_e2e.py::PublishedContractParityTests::test_the_doc_states_the_verify_with_limits_rather_than_implying_parity`.
    This one DID go red, exactly as F-16 predicted, once the doc was corrected: the doc no longer
    contains "does not read runner profiles". Run with `-m slow`, since the bare suite deselects this
    file:

    ```
    BEFORE (doc corrected, assertion not yet updated):
    $ python3 -m pytest tests/test_runner_profiles_e2e.py -o addopts="-m slow -p no:randomly"
    >       self.assertIn("does not honor `verify_with`", self.text)
    E       AssertionError: 'does not honor `verify_with`' not found in ...
    FAILED tests/test_runner_profiles_e2e.py::PublishedContractParityTests::test_the_doc_states_the_verify_with_limits_rather_than_implying_parity
    1 failed, 31 passed in 5.75s

    AFTER:
    $ python3 -m pytest tests/test_runner_profiles_e2e.py -o addopts="-m slow -p no:randomly"
    tests/test_runner_profiles_e2e.py ..................................     [100%]
    ============================== 34 passed in 5.52s ==============================
    ```

    Not `no tests ran`: 34 collected and run under `-m slow` (32 before, plus the 2 new E-08 cases).

    WHAT IT NOW PINS, in one sentence: that the doc states the limit PER FIELD (it contains
    "honors `validate`" and "does not\n  honor `verify_with`, `variant`, or `agent`", and does NOT
    contain the superseded absolute claim "does not read runner profiles at all"), and that the claim
    is true of the system (agy references `launch_profile`/`verify_with` zero times yet does contain
    `resolve_verification_decision`). The `verify_with` and "routes the model, not the host" halves
    SURVIVED.

    NEITHER TEST WAS DELETED, SKIPPED, OR XFAILED, and neither was weakened into a tautology: each
    asserts a behavioral property (a resolved decision from a real store; a per-field doc claim
    cross-checked against the source), not merely that a file exists.

    THE DOC DIFF, per-field per-host honoring and the corrected per-host tier 4:

    ```diff
    -4. The shipped default, which is off.
    +4. The shipped default for the host that is running, which is off on opencode and on on
    +   antigravity.
    +
    +Tier 4 is PER HOST because the two shipped hosts want opposite postures: `aw oc run` does not
    +verify unless you ask, and `aw agy run` verifies unless you decline.
    ...
    -- IT IS OPENCODE ONLY. The Antigravity runner does not read runner profiles at all, so it neither
    -  honors `verify_with` nor any other profile field. Verifying under a DIFFERENT RUNNER than the one
    -  that executed is also not available: this routes the model, not the host.
    +- IT IS OPENCODE ONLY, and the limit is per FIELD rather than per host. The antigravity runner
    +  honors `validate`, so a stored per-model verification choice decides its runs too, but it does not
    +  honor `verify_with`, `variant`, or `agent`: it keeps no verifier launch of its own, and its
    +  registry row supports neither a model variant nor an agent. Verifying under a DIFFERENT RUNNER
    +  than the one that executed is also not available: this routes the model, not the host.
    ```

    DOCS CHECK CLEAN, and no em or en dash introduced:

    ```
    $ python3 -c "from pathlib import Path; from agent_workflows import docs_check; print([str(f) for f in docs_check.check_doc(Path('docs/runner-profiles.md'))])"
    []
    ```

    The shipped `test_the_doc_contains_no_em_or_en_dash` case also passes in the 34-test run above.

  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

DEPENDENCY: this plan declares `- Item-Dependencies: executed:tm2cz8` and MUST NOT run before child 01 is executed. Child 01 puts the per-host default in the registry row; without it, agy's tier-4 fallback resolves to opencode's `False` and E-04's floor (agy verifies by default) would silently break. The runner re-checks dependencies at dispatch, so a queued-together Set is safe, but a hand-run of this plan alone is not.

Scope fence: touch ONLY the ten paths in `Scope-Paths`. Do NOT change `runner_profiles.py`, `RUNNER_REGISTRY`, the schema, or the precedence order (child 01 owns those and is expected to be executed already). Do NOT add a `validate` key to agy's frozen options. Do NOT move `resolve_launch_pair` out of first position in oc's `initialize_run`. Do NOT thread `validate=` into `resolve_launch_pair`'s VERIFIER `resolve()` call (F-13: `verify_with` says WHICH, never WHETHER). Do NOT add a `--profile` flag or an `as` clause to agy. Do NOT copy oc's `--validate` ALIAS LIST onto agy's `start`, and do NOT set `conflict_handler="resolve"` there (F-14: the first raises at parser build, the second silently steals `--no-verify`). Do NOT change either host's effective default. Do NOT edit spec `25kzda`. Do NOT delete, skip, or xfail either of the two assertions E-09 owns. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. NOTE: this is a SHARED CHECKOUT and a driver run may be live; run `aw runs` before starting and expect contention on both driver modules.

A NEWER SET DECLARES ALL THREE OF THIS PLAN'S PRODUCT MODULES, so read its state before you start rather than discovering it in a merge. Set `runnerlayer` (`lyo1tz` Order 00, `9kmbr0` Order 01, `1f7xno` Order 02, all `to-review` at review time) is re-homing host-neutral names out of `oc_runipd` into `runner_shared`; `1f7xno`'s Scope-Paths are `runner_shared.py`, both drivers, and `tests/test_runner_shared.py`, which is this plan's core set. This is NOT a reason to refuse to run: the runner isolates each execute item in its own worktree and returns changes through the merge-and-revalidate gate, so overlap is handled. It IS a reason to (1) re-run the call-graph probe above after any rebase, since a re-homing plan can move the very symbols you are editing, and (2) place the new helper by SYMBOL NEIGHBORHOOD (beside `freeze_run_policy_flags`) rather than by line number, so a concurrent re-home does not land it in an unrelated section.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest` AND from `python3 -m pytest -m slow`. BOTH ARE REQUIRED, and the second is not a flag added to "help": `tests/test_runner_profiles_e2e.py` is in Scope-Paths and is marker-excluded from the bare run, so a bare-only paste can show green while that file is red (F-16). A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, and F-17 measured why: every driver citation in the authored plan had already drifted by 70 to 200 lines when `kgpptv` merged two days later. `oc_runipd.py` and `agy_runipd.py` are the two highest-contention modules in the repository and other pending plans declare them, so expect drift and expect to rebase and re-run the full suite after any merge. Find `resolve_launch_pair` (NOT `resolve_launch_profile`, which F-12 measured as having zero production callers), `launch_profile_record`, each `initialize_run` freeze block, each verifier gate, and `freeze_run_policy_flags` by name.

BEFORE YOU EDIT EITHER DRIVER, RE-MEASURE WHICH RESOLUTION FUNCTION `initialize_run` ACTUALLY CALLS. This plan was authored against `resolve_launch_profile` and that call was replaced by `resolve_launch_pair` two days later; the same thing can happen again between approval and execution. One command settles it: `python3 -c "import ast,inspect;from agent_workflows import oc_runipd as m;print([ (n.func.id,n.lineno) for n in ast.walk(ast.parse(inspect.getsource(m))) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and 'resolve_launch' in n.func.id])"`. Wire the function that is actually CALLED. Adding the flag to an uncalled function is the one failure mode of this plan that produces zero test failures and zero behavior change, so it cannot be caught by the suite.

THE ITEM THAT MATTERS MOST IS V-06. The hosts' frozen keys are OPPOSITE IN POLARITY, so a wiring change that looks correct can silently disable verification on antigravity: resolved `True` written un-negated into `no_verify` means the verifier does NOT run, so verification would be requested and skipped with no error anywhere. F-4 records the arithmetic. All four cells of the polarity matrix must be pasted from real output. If V-06 cannot be shown green in all four cells, STOP and report rather than proceeding: this is a genuinely unsafe condition (a shipped silent bypass of the safety mechanism the whole Set exists to make configurable), not a scope question.

THE SECOND WAY TO SHIP A SILENT BYPASS is `conflict_handler="resolve"` on agy's `start` parser, and F-14 measured it: the auto-generated `--no-validate` family would steal `--no-verify`/`--no-audit`, after which `args.no_verify` does not exist and the freeze site reads `False` unconditionally, meaning antigravity stops verifying by default and no test that only checks the new flag would notice. V-02 must therefore paste `args.no_verify` as PRESENT, not merely paste that `--validate` parses.

On completion of THIS plan (not child 01), close backlog `h7qsje`, which both children carry as `- From-Backlog:`. The operator-visible capability it describes ships here, because this is the plan after which a stored per-model choice actually decides a run.
