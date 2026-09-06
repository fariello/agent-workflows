# IPD: Wire the per-profile validate tri-state into both runners so the per-model verification default is honored


> **RETIRED 2026-09-06: SUPERSEDED BY THE `hostdefault` SET** (`tm2cz8` order 01, `ybkmzp` order 02),
> on a maintainer ruling. DO NOT EXECUTE. This plan was `approved`, and it is retired UNRUN rather
> than executed, so nothing here was implemented.
>
> WHY, since the reason is the whole point. The maintainer asked why deepening the oc/agy driver
> divergence is a good thing. It is not, and the framing that said otherwise ("Antigravity is
> untouched, so nothing gets worse") was wrong: the file is untouched but the GAP widens, at a seam
> `rununify`'s orchestrator child table already names as remaining work (its row `03+` names "run
> initialization" as an example seam and this plan modifies `initialize_run`; its row `last` names
> closing "opencode-only" surfaces and this plan would ADD one).
>
> TWO MEASURED CORRECTIONS TO THIS PLAN'S OWN REASONING, both verified live at `f3e17ff6`:
>
> 1. **F-8's blocker is OVERSTATED.** It says reaching antigravity needs "a registry (schema) change
>    plus the whole seam `3cm15q` built for oc". But the `validate` chain does NOT consult the
>    registry at all (neither `RUNNER_REGISTRY` nor `canonical_runner` appears in that block), and a
>    prototype of ONE field plus ONE row made `resolve(runner="agy").validate` return `True` with
>    provenance, made a profile declaring `runner: agy` parse and resolve, and kept the explicit flag
>    winning on both hosts. The registry's own docstring says as much: "Adding a host is ONE ROW here
>    plus that host's own adapter work."
> 2. **The real defect is the one this plan worked AROUND rather than the one it named.**
>    `SHIPPED_VALIDATE_DEFAULT` is a single module global that cannot express two opposite host
>    postures, so this plan's E-03 pins antigravity with a TEST against a constant that does not
>    describe it. That pin is the symptom of a missing per-host field.
>
> WHAT SURVIVES, because most of this plan is right: its F-5 polarity arithmetic (writing a resolved
> `validate` into agy's inverted `no_verify` key silently disables verification), its F-9 measurement
> that the `None`-default mechanism breaks `tests/test_novalnomerge_integration.py`, its F-4
> correction about `launch_profile_record` carrying provenance but not the value, its F-7 history of
> the 13 verifier runs and the conditional ~33% cost ruling, and every one of its resolved open
> questions. All are carried forward with citation into `tm2cz8` and `ybkmzp`.
>
> Its `- From-Backlog: h7qsje` and `- Blocks-Release: next` are INHERITED by both children, so the
> release gate is preserved rather than dropped.

- Date: 2026-09-06
- Kind: child
- Concern: Executed plan `f2mrsw` shipped a per-profile `validate` tri-state and a documented four-tier precedence chain for it, but the opencode runner does not pass `validate=` into `runner_profiles.resolve()` and does not read `ResolvedLaunch.validate`. The two middle tiers (a named profile's own value, and `defaults.validate`) are therefore dead: the operator's stored per-model choice is silently ignored and verification remains a flag that must be retyped every invocation.
  SCOPE CORRECTED IN REVIEW (PR-401), because the original "on BOTH hosts" premise is NOT IMPLEMENTABLE and the correction is a measured fact, not a preference. The antigravity host has ZERO profile integration (`runner_profiles`, `resolve_launch_profile`, and `launch_profile` all grep to nothing in `agy_runipd.py`, exit 1), AND `runner_profiles.RUNNER_REGISTRY` version 1 registers ONLY `oc`, so `resolve(cfg, runner="agy")` RAISES `ProfileSchemaError: unknown runner 'agy'; version 1 registers: oc` and a profile declaring `runner: agy` cannot even be written. Wiring agy therefore requires registering a second runner in the schema registry plus building the whole resolve/record/freeze seam that `3cm15q` built for oc: work this plan's own Scope fence forbids ("No change to the resolver, the schema") and whose files are not in Scope-Paths. So the agy half is impossible inside this fence rather than merely large, and it is deferred with the measured reason plus a required follow-up that inherits the release gate.
- Scope: Pass the explicit flag into the resolver and consume the resolved value as the run's frozen `validate` option ON THE OPENCODE HOST, preserving that host's CURRENT effective default when no flag and no profile speak. Record the resolved value in run state beside the provenance tier the record already carries. PIN the antigravity host's verification default as UNCHANGED, by leaving that host's verification path untouched and proving non-disturbance. No change to the resolver, the runner registry, the schema, the precedence rules, or either host's default behavior.
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_profiles.py, tests/test_novalnomerge_integration.py
- Item-Dependencies: none
- Status: superseded
- Readiness: go-pending-approval
- Set: verifygap
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: mn3gwr
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history
- 2026-09-06 superseded (aw set): Superseded UNRUN by the hostdefault Set (tm2cz8 order 01, ybkmzp order 02) on a maintainer ruling. Two measured corrections to this plan's reasoning: (1) its F-8 blocker is overstated, since the validate chain never consults the runner registry and a prototype of one field plus one row made resolve(runner='agy').validate work with provenance, the explicit flag still winning on both hosts; (2) the real defect is the one it worked around, a single module-global SHIPPED_VALIDATE_DEFAULT that cannot express two opposite host postures, which is why its E-03 pins antigravity with a test against a constant that does not describe it. Also: it would add an opencode-only surface at a seam rununify's child table names as remaining convergence work (row 03+ names 'run initialization', row last names closing opencode-only surfaces). Its F-4/F-5/F-7/F-9 findings and all resolved OQs are carried forward with citation; From-Backlog h7qsje and Blocks-Release next are inherited by both children.
- 2026-09-06 approved (aw set): status set to approved

- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-401..PR-408 all FIXED; GO - PENDING HUMAN APPROVAL. Lint conforming at `--phase author` and again at `--phase review-finalize`. SELF-REVIEW (I authored this plan in the same session), which matters here because both blockers are cases where authoring trusted a sibling plan's prose instead of measuring code that the sibling's own review had already measured. THE THESIS IS SOUND AND INDEPENDENTLY RE-VERIFIED: the resolver implements the whole four-tier chain with provenance, the runner passes no `validate=` and reads no resolved value, and live probes confirm a configured `defaults.validate: true` resolves `True`/`defaults` while the run still freezes the raw flag. WHAT CHANGED IS THE PLAN'S REACH. PR-401 (BLOCKER): the "on BOTH hosts" premise is not implementable. `RUNNER_REGISTRY` version 1 registers only `oc`, so `resolve(cfg, runner="agy")` RAISES `unknown runner 'agy'`, a profile declaring `runner: agy` is refused identically, and `agy_runipd.py` imports nothing from `runner_profiles`; reaching agy needs a registry/schema change plus the whole seam `3cm15q` built for oc, which this plan's own Scope forbids and its Scope-Paths exclude. The plan is now opencode-only, `agy_runipd.py` is OUT of Scope-Paths and off-limits by fence, and E-02 became a prove-and-record item that files the agy follow-up carrying the inherited `Blocks-Release: next` gate so the release blocker is not dropped. The honest consequence is stated: after this plan, per-model verification is configuration on opencode and still a remembered flag on agy. PR-402 (BLOCKER): the authored E-03/E-04 would have written a resolved `validate` into agy's `no_verify` key while claiming to preserve existing meanings, but those keys are INVERTED IN POLARITY, so resolved `True` becomes `no_verify=True` and the verifier does NOT run - verification requested and silently skipped. The plan's loudest warning described a hazard its own instructions created, and its proposed remedy fixed the value mismatch while leaving the inversion. E-03 is now a test-only PIN proving agy did not move, plus a prohibition on adding a `validate` key to agy's options. PR-403 (HIGH): E-01's required default change breaks a shipped test that pins the premise of `evgi9n`'s $528 bug class (`assertIs(defaults.get("validate"), False)`), measured by mutating the real parser; E-01 now names both mechanisms, requires the choice recorded, and requires that test UPDATED (not weakened or deleted) to pin the property `evgi9n` actually depends on. PR-405 (MEDIUM): E-06 specified coverage that already ships at the resolver level, leaving the seam this plan BUILDS untested; it now tests frozen run state through `initialize_run` with an isolated store. PR-404/406/407/408 correct a half-wrong provenance claim (the tier IS already recorded, only the value is missing), the untracked derived `no_audit` key, an unqualified host-parity claim plus a stale sibling status, and the absence of store isolation in tests. Five recorded decisions, all reversible; D-1 changes what the plan delivers and is surfaced to the maintainer explicitly.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `h7qsje`, inheriting its `Blocks-Release: next` gate. The premise is measured, not inferred: `runner_profiles.resolve()` implements the full tri-state chain correctly (`runner_profiles.py:1004-1017`) and `ResolvedLaunch.validate` carries the result (`:360`), but `resolve_launch_profile` calls `resolve()` WITHOUT `validate=` (`oc_runipd.py:2643-2650`), `launch_profile_record` omits the field (`:2673-2683`), and the verifier gate reads `state["options"]["validate"]` sourced from the CLI flag alone (`:6211-6215`). Verified live: `resolve(cfg, runner="oc").validate` returns `False` with provenance `shipped-default`. Corrects a false premise from the investigation that produced `h7qsje`: the verifier turn has NOT never run. It ran on every IPD across 13 runs through 2026-08-29, and the maintainer switched the default deliberately after measuring roughly 33% extra cost for only nits on the primary model (recorded as F-6 in executed plan `evgi9n`). That ruling is explicitly conditional - "on a weaker model it is not, which is why the per-model default is wanted" - which is the capability this plan restores.

## Goal

Make the operator's stored per-model verification choice actually take effect, so "check this model's work, do not check that one" is configuration rather than a flag a human must remember on every run. The design is already approved and shipped; only the wire is missing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the resolver see the flag

- [ ] E-01 In `oc_runipd.resolve_launch_profile` (`oc_runipd.py:2619`; RE-LOCATE BY SYMBOL, every line number in this plan may drift), pass the explicit verification flag into `runner_profiles.resolve()` as `validate=`. The value MUST be the tri-state the resolver expects: `True`/`False` when the operator spelled `--validate`/`--no-validate`, and `None` when neither appeared, so an unspecified flag FALLS THROUGH to the profile tier instead of being read as a decision.
  THE MECHANISM IS A CHOICE, AND THE OBVIOUS ONE BREAKS A SHIPPED TEST. `--validate` is a `BooleanOptionalAction` on `start` with `default=False` (`oc_runipd.py:7467`), so today `args.validate` cannot distinguish "operator said nothing" from "operator said `--no-validate`". Two ways to recover the tri-state:
  (a) CHANGE the `start` default to `None` (matching `resume`, which already ships `default=None` at `:7538` for exactly this reason). MEASURED CONSEQUENCE, verified by driving the real parser: this FAILS a shipped test. `tests/test_novalnomerge_integration.py:50` walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`; with `default=None` the probe returns `None` and `assertIs(None, False)` FAILS. That test is not incidental - it pins the PREMISE of executed plan `evgi9n`'s bug class, so it must be UPDATED DELIBERATELY (asserting that a bare invocation still resolves verification OFF, which is the property `evgi9n` actually depends on) and never deleted. `tests/test_oc_runipd.py:1966` uses `assertFalse`, which survives `None` unchanged (verified).
  (b) READ THE PARSED ARGV instead, deriving `None` when neither spelling appeared and leaving the default alone.
  CHOOSE ONE AND RECORD WHY. (a) is preferred as the smaller, more honest change (the flag genuinely IS tri-state now), but it is only correct if the shipped test is updated in the same commit. Do NOT reintroduce a two-valued flag, and do NOT leave the pinning test failing.
  - Depends on: none
  - Expected outcome: `resolve()` receives `None` on a bare invocation and a boolean when the flag is spelled; provenance reports `explicit` only in the latter case; `tests/test_novalnomerge_integration.py` still passes, having been updated to assert the effective default rather than the raw parser default if (a) was chosen.
  - Execution state: pending

- [ ] E-02 PROVE, AND RECORD, THAT THE OPENCODE PATH IS THE ONLY ONE REACHABLE, replacing this plan's original "do the same for agy" item, which review measured to be impossible inside this fence (PR-401). Three facts, all re-measurable in one pass: `rg 'runner_profiles|resolve_launch_profile|launch_profile' agent_workflows/agy_runipd.py` exits 1 with no output; `runner_profiles.RUNNER_REGISTRY` contains exactly `{"oc"}` (`runner_profiles.py:207-212`); and `runner_profiles.resolve(cfg, runner="agy")` RAISES `ProfileSchemaError: unknown runner 'agy'; version 1 registers: oc`, as does writing a profile whose `runner` is `agy`.
  SO THE agy HALF IS NOT DEFERRED FOR COST, IT IS UNREACHABLE WITHOUT WORK THIS PLAN FORBIDS ITSELF: registering a second runner in the registry is a SCHEMA change ("No change to the resolver, the schema" per Scope) touching `runner_profiles.py`, which is not in Scope-Paths. Do NOT register a runner, do NOT add a profile seam to agy, and do NOT touch agy's verification path in this plan. Instead file the follow-up (`aw backlog new`) for the agy profile seam, carrying `- Blocks-Release: next` inherited from `h7qsje`, so the gate is not silently dropped when that item closes, and record the three measurements in this plan's Findings.
  - Depends on: none
  - Expected outcome: the three measurements are pasted; a backlog item exists for the agy seam carrying the release gate; `agy_runipd.py` is NOT in the diff.
  - Execution state: pending

### Task group 2: preserve each host's current default

- [ ] E-03 THE SAFETY-CRITICAL ITEM, RESHAPED FROM "make agy's fallback True" INTO "prove agy did not move" (PR-402). The hazard the original item named is real and the review confirmed the direction of the inversion arithmetically: `runner_profiles.SHIPPED_VALIDATE_DEFAULT` is `False` (`runner_profiles.py:112`) while agy's effective default is the OPPOSITE (verification ON, gated on `not no_verify`, deliberately, documented at `agy_runipd.py:3474-3482`), and agy's frozen key is INVERTED IN POLARITY (`no_verify`, not `validate`), so writing a resolved `validate` into it without negating flips the host. Since E-02 establishes agy cannot be wired here at all, the correct discharge is a PIN, not a fallback: assert agy's verification default is UNCHANGED and that its file is untouched.
  Pin it in `tests/test_agy_runipd_cli.py` by driving the REAL parser and the REAL freeze site: a bare `agy run start` must yield `no_verify` False (verification ON), and the gate expression must remain `not no_verify`. Do NOT change `SHIPPED_VALIDATE_DEFAULT` (oc depends on it, and one shared constant cannot carry two host defaults). Do NOT introduce a `validate` key into agy's frozen options, because a reader finding both `validate` and `no_verify` there would face two switches for one behavior, and `oc_runipd.py:6213-6214`'s compatibility read (`if "validate" not in opts: validate = not (no_verify or no_audit)`) shows precisely how such a pair is disambiguated only by ABSENCE.
  - Depends on: E-01, E-02
  - Expected outcome: with no runner-profiles store present and no flag, `aw oc` still resolves `validate=False` and `aw agy` still verifies by default, exactly as today, the latter proven by a new test that fails if agy's default is ever flipped.
  - Execution state: pending

- [ ] E-04 Consume the resolved value as the run's frozen `validate` option in `oc_runipd.initialize_run`, replacing the direct `getattr(args, "validate", False)` read at `oc_runipd.py:2969-2970`. Keep the existing `options` keys and their meanings (`validate` and its derived `no_audit`) so every downstream reader is untouched, including the verifier gate at `oc_runipd.py:6211-6215`. Freeze at queue build, so a resume cannot silently change what verification meant mid-run (the same rule the other policy flags already follow).
  KEEP `no_audit` CONSISTENT WITH `validate`, since it is derived (`"no_audit": not getattr(args, "validate", False)`) and read by the verifier gate's own compatibility branch and by five tests. Derive it from the RESOLVED value, not from `args`, or a run can carry `validate: true` beside `no_audit: true` and the two disagree.
  DO NOT MOVE `resolve_launch_profile`, which is deliberately the FIRST statement of `initialize_run` (`:2691`) so a malformed profile refuses before any durable write. The resolved `validate` is already available at the freeze site through the existing `resolved_launch` local; no new call is needed and a second `runner_profiles.load()` would break the frozen-once guarantee `3cm15q` E-04 established.
  - Depends on: E-03
  - Expected outcome: the verifier gate fires based on the RESOLVED value; `validate` and `no_audit` never disagree; no downstream reader changes; `resolve_launch_profile` is still the first statement.
  - Execution state: pending

### Task group 3: make the decision auditable

- [ ] E-05 Add the resolved `validate` VALUE to `launch_profile_record` (`oc_runipd.py:2657`), so `state.json` records the decision beside the tier that produced it. NOTE WHAT IS ALREADY THERE, measured in review (PR-403): the record's `provenance` dict ALREADY carries the `validate` tier today, because it copies the resolver's whole provenance mapping (`dict(resolved.provenance)`), verified live as `{'runner': 'explicit', 'model': 'host-default', ..., 'validate': 'defaults'}`. What is genuinely missing is the VALUE, so this item adds one key and must not duplicate the provenance the record already has. The vocabulary is the resolver's closed set (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`).
  DO NOT add an agy equivalent (E-02: that host has no record to extend). Add no credentials and no new file.
  BACKWARD COMPATIBILITY: a run created before this change has no `validate` key in `options.launch_profile`, and `tests/test_oc_runipd.py` already pins that an older record must "still render, not raise", so read the new key defensively wherever it is displayed.
  - Depends on: E-04
  - Expected outcome: `state.json` `options.launch_profile` shows the resolved `validate` value; the tier is read from the provenance mapping already present; an older run without the key still renders.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 Test the chain end to end THROUGH THE RUNNER, which is the gap the shipped tests leave. `tests/test_runner_profiles.py:843-935` ALREADY pins all four tiers, both polarities, the absent-is-not-false case, the default-profile tier, and the measured strong-off / cheap-on split, at the RESOLVER level (re-read it before writing; do not duplicate it). What no test covers is the seam this plan builds: that a stored profile value reaches the RUN, survives the freeze, and decides the verifier gate.
  So test at the runner level: drive `oc_runipd.initialize_run` on a real repository with `--prepare-only` (the existing pattern at `tests/test_run_flag_surface.py:956-970`) against an isolated store (point `XDG_CONFIG_HOME` at a temp dir; `runner_profiles.store_path()` derives from `config.config_dir()`, `config.py:674-682`), and assert the FROZEN `state["options"]["validate"]` for: explicit flag beats a profile value; a profile value beats `defaults.validate`; `defaults.validate` beats the shipped fallback; and absence at every tier yields `False`, oc's current default. Assert `no_audit` agrees with `validate` in every case. Assert the tri-state does not collapse: a profile saying `validate: false` must be distinguishable from a profile omitting the field, since only the former is a decision. Include the E-03 agy pin, because that is the one silent-safety-change risk this plan carries.
  - Depends on: E-05
  - Expected outcome: the four-tier chain is pinned AT THE FROZEN-STATE LEVEL for oc, not only at the resolver; agy's default is protected by an explicit test; no resolver-level test is duplicated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The resolver is the single authority and is already correct. `runner_profiles.resolve()` implements the chain at `runner_profiles.py:1004-1017` with per-field provenance. Do NOT reimplement precedence at the call site; pass the flag in and read the result out.
- `validate` is a genuine TRI-STATE by explicit design: `_validate_tristate` (`runner_profiles.py:467`) and the module docstring (`:39-44`) require that ABSENT never collapse to `false` at parse time. `f2mrsw`'s review recorded the reason: an explicit flag must always beat a stored default, because "a profile silently beating a flag would reproduce [`vju5ba`] inverted".
- The two hosts have OPPOSITE verification defaults, deliberately. `agy_runipd.py:3474-3482` states it: agy gates on `not no_verify` (ON), opencode gates on `validate` (OFF). The keys are also OPPOSITE IN POLARITY, which is the inversion hazard: oc freezes `validate`, agy freezes `no_verify`.
- THE PROFILE MECHANISM IS OPENCODE-ONLY, BY CONSTRUCTION AND NOT BY CHOICE. `RUNNER_REGISTRY` version 1 registers only `oc` (`runner_profiles.py:207-212`), `resolve(runner="agy")` raises, and `agy_runipd.py` references nothing from `runner_profiles`. Any wording implying host parity is false; `kgpptv`'s review recorded the same fact independently (its F-12).
- The resolver-level precedence chain is ALREADY FULLY TESTED at `tests/test_runner_profiles.py:843-935` (all four tiers, both polarities, absent-is-not-false, the default-profile tier, the strong-off / cheap-on split). New tests belong at the RUNNER level, where nothing is covered.
- `oc_runipd.initialize_run` freezes policy into `state["options"]` at queue build and treats a resume as bound by the frozen values, and `resolve_launch_profile` is deliberately its FIRST statement so a bad profile refuses before any durable write. Follow both, do not add a second mechanism.
- `--prepare-only` exists on both hosts (`oc_runipd.py:7432`, `agy_runipd.py:4472`) and is how the shipped tests drive `initialize_run` without launching an agent.
- Run under `python3 -m pytest` bare; the configured `addopts` already supply quiet/parallel/fast-subset.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The resolver is called without the flag, so tier 1 never registers as explicit. | `oc_runipd.py:2643-2650` passes `runner`, `profile`, `model`, `variant`, `agent` and no `validate` |
| F-2 | The resolved value is never read. `grep '\.validate' oc_runipd.py` finds only `validate_manifest`, a `validate_retry_budget` comment, and the resume path's `args.validate`. | measured 2026-09-06 |
| F-3 | Live proof the chain is inert: `resolve(cfg, runner="oc").validate` returns `False` with provenance `shipped-default`, regardless of any stored profile. | measured 2026-09-06 |
| F-4 | `launch_profile_record` omits the `validate` VALUE. **CORRECTED IN REVIEW: it does NOT omit the provenance**, which arrives via `dict(resolved.provenance)`. Verified live: the record's provenance reads `{'runner': 'explicit', 'model': 'host-default', 'variant': 'host-default', 'agent': 'host-default', 'validate': 'defaults'}` while `'validate' in record` is `False`. So E-05 adds one key, not two. | `oc_runipd.py:2673-2683`; live `launch_profile_record(resolve(cfg, runner="oc"))` |
| F-5 | **The flip risk, and its arithmetic.** `SHIPPED_VALIDATE_DEFAULT = False` matches opencode but is the opposite of agy's effective default. Worse than a value mismatch, the KEYS ARE INVERTED: agy freezes `no_verify` and gates on `not no_verify`, so writing a resolved `validate` into that key without negating produces exactly the wrong behavior in both directions (resolved `True` -> `no_verify=True` -> verifier does NOT run). | `runner_profiles.py:112` versus `agy_runipd.py:3474-3482`, `:3392-3399` |
| F-6 | `--validate` is a `BooleanOptionalAction` with `default=False` on `start` and `default=None` on `resume`; agy has no `--validate` at all, only `--no-verify`/`--no-audit` as `store_true`. | `oc_runipd.py:7467` (`start`), `:7538` (`resume`), `agy_runipd.py:4447-4453` |
| F-7 | The capability was exercised historically and switched off on measured grounds, so this is a restoration rather than a new feature: 13 runs carry verification outcomes, the last on 2026-08-29. Re-measured in review: 13 distinct run directories, 34 verification outcome files, latest `run-20260829T191652Z-4134000`. | `ls -d .aw/records/runs/*/` filtered on `outcomes/*verification*.json`; `evgi9n` F-6 |
| F-8 | **THE agy HALF OF THIS PLAN IS UNREACHABLE, not merely large** (found in review, PR-401). `RUNNER_REGISTRY` version 1 registers only `oc`; `resolve(cfg, runner="agy")` raises `ProfileSchemaError: unknown runner 'agy'; version 1 registers: oc`; a profile declaring `runner: agy` is refused identically; and `agy_runipd.py` references nothing from `runner_profiles`. Wiring agy needs a registry (schema) change plus the whole seam `3cm15q` built for oc, both outside this plan's Scope and Scope-Paths. | `runner_profiles.py:207-212`; live `resolve`/`from_document` probes; `rg 'runner_profiles\|resolve_launch_profile\|launch_profile' agent_workflows/agy_runipd.py` exit 1 |
| F-9 | **E-01's required default change BREAKS A SHIPPED TEST** (found in review, PR-404). `tests/test_novalnomerge_integration.py:50-79` walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`. Verified by driving the real parser: `start`'s default is `False` today and becomes `None` under E-01(a), at which point `assertIs(None, False)` fails. `tests/test_oc_runipd.py:1966` uses `assertFalse` and survives `None`. | `tests/test_novalnomerge_integration.py:50`, `:71-75`; live parser mutation probe |
| F-10 | `no_audit` is DERIVED from `validate` at the freeze site and read by the verifier gate's compatibility branch plus five tests, so it must be derived from the RESOLVED value or the two frozen keys can disagree. | `oc_runipd.py:2969-2970`, `:6213-6214`; `tests/test_oc_runipd.py:2390`, `:2473`, `:2517`, `:2556`, `:2658` |

## Proposed changes (ordered, validatable)

1. Pass the flag in as a tri-state on opencode, choosing and recording the mechanism, and updating the test that pins the old default (E-01).
2. Measure and record that the agy half is unreachable inside this fence, and file the follow-up carrying the release gate (E-02).
3. Pin agy's current default so it provably does not flip (E-03).
4. Consume the resolved value as the frozen option, keeping `no_audit` consistent, leaving downstream readers untouched (E-04).
5. Record the resolved value beside the provenance the record already carries (E-05).
6. Pin the chain AT THE RUNNER LEVEL, where nothing is covered today, plus the agy guard (E-06).

## Deferred / out of scope (with reason)

- WIRING THE ANTIGRAVITY HOST, deferred on a MEASURED IMPOSSIBILITY rather than on cost (F-8, PR-401). The runner registry admits only `oc`, so `resolve(runner="agy")` raises and no agy profile can even be written; closing that needs a schema change plus the whole resolve/record/freeze seam, in files this plan excludes. E-02 files the follow-up and hands it this plan's `Blocks-Release: next` gate so the release blocker is not dropped. CONSEQUENCE STATED PLAINLY: after this plan, the per-model verification default is configurable on opencode ONLY, so an operator running agy still retypes `--no-verify`. That is a partial fix, and no user-facing text may imply otherwise.
- Changing either host's DEFAULT verification behavior. This plan makes the stored choice effective; it does not decide what the choice should be. Any default change is a separate, measured decision.
- The flag SURFACE (whether agy should gain `--validate`/`--no-validate`, and whether the argparse-generated negations are acceptable). That is `ki6tom`'s concern, currently parked on a spec reading. This plan works with the flags as they ship.
- Per-role model routing (a distinct model for the verifier turn). That is `kgpptv` (`runprofile-06`, `Status: reviewed`). Complementary: this plan decides WHETHER the verifier runs, `kgpptv` decides WHICH model runs it. NO ORDERING DEPENDENCY EXISTS IN EITHER DIRECTION: `kgpptv`'s fence forbids touching the `validate` tri-state and this plan does not touch `verify_with`, so the two can execute in any order. `kgpptv` is also oc-only for the same measured reason as this plan (its F-12).
- A standalone re-verify command for an already-executed plan. Backlog `7u9kbm`, deliberately sequenced after this.

## Scope check

- Over-scope: none. One runner module plus tests, all in Scope-Paths. `agy_runipd.py` was REMOVED from Scope-Paths in review (F-8): the plan must not touch it, and declaring a path it cannot legitimately edit would invite an unnecessary change to the highest-contention module in the repo.
- Scope widened in review: `tests/test_novalnomerge_integration.py` added, because E-01's default change breaks a shipped assertion there (F-9) and the plan must update it deliberately rather than discover it at CI. `tests/test_agy_runipd_cli.py` is RETAINED although `agy_runipd.py` is not, because E-03's pin is a test-only guard on that host.
- Under-scope: does not add a ledger, does not change defaults, does not touch the resolver, the runner registry, or the schema. Those are correct exclusions: the resolver already works, the registry change belongs to the deferred agy follow-up, and the defaults are a separate decision.

## Required tests / validation

- `python3 -m pytest` bare, full suite, before and after, with counts stated.
- Targeted: `tests/test_runner_profiles.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_novalnomerge_integration.py`.
- A live before/after demonstration that a stored profile value actually changes the FROZEN verification decision of a real run, which is the whole point of the plan and is not shown by the shipped resolver-level tests. Use an isolated store (`XDG_CONFIG_HOME` pointed at a temp dir) so the maintainer's own `~/.config/agent-workflows/runner-profiles.json` is never read or written by a test.

## Spec / documentation sync

Spec `25kzda`'s amended Section 1.3 already records that skipping the independent verifier turn is a RETAINED, host-configurable choice rather than a prohibited bypass, and names `kgpptv` plus `f2mrsw` E-03 as the mechanism that makes it configuration (verified in review at `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:105`, which says in as many words that "until per-role model routing exists ... a host-level control is the only available mechanism"). This plan implements that mechanism FOR OPENCODE ONLY, so no spec change is required and no spec edit is authorized here.

BUT DO NOT LET ANY USER-FACING TEXT IMPLY HOST PARITY. After this plan the per-model verification default is configuration on opencode and still a remembered flag on antigravity (F-8). If the executor writes or touches any user-facing description of this behavior, it must name the host. If the executor finds existing documentation already claiming host-agnostic profile behavior, NOTE IT for the deferred agy follow-up rather than editing the spec or widening this plan.

## Open questions

### OQ-01: Should a stored profile value be allowed to turn verification ON for a run the operator started without any flag?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, that is the entire purpose. The maintainer's measured position is per-model (off for the strong executor, on for a weaker one), and `f2mrsw` E-01 built the field for exactly that, citing the Opus-off / Gemini-on split. A stored value that could only turn verification OFF would leave the weak-model case still dependent on a remembered flag, which is the failure `vju5ba` recorded across five overnight runs. The explicit flag still wins when present, so an operator is never surprised in the direction they typed.

### OQ-02: Does freezing the resolved value break `--validate` on resume?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No, and the existing behavior is deliberately preserved. `oc_runipd.py:7882-7886` currently lets a resume OVERWRITE the frozen `validate` when the flag is passed, with a comment stating that this overwrite behavior is preserved exactly. E-04 changes where the value comes from on a NEW run, not what a resume may do. If the executor believes resume should refuse instead of overwrite, that is a separate decision and must not be folded in here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolved `validate` and its provenance for three opencode invocations: no flag (expect provenance NOT `explicit`), `--validate` (expect `True`/`explicit`), `--no-validate` (expect `False`/`explicit`). STATE WHICH MECHANISM YOU CHOSE, (a) the `None` default or (b) argv inspection, and why. If (a): paste the UPDATED `tests/test_novalnomerge_integration.py` assertion and its passing output, and state in one sentence what the new assertion pins instead (it must still pin that a bare invocation verifies OFF, which is `evgi9n`'s actual premise). A paste showing that test failing, skipped, or deleted is a FAILED validation.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste all three agy measurements verbatim: the `rg` over `agy_runipd.py` showing no output and its exit code; `RUNNER_REGISTRY`'s keys; and the `ProfileSchemaError` text from `resolve(cfg, runner="agy")` AND from a profile document declaring `runner: agy`. Paste the new backlog item's id6 and its `- Blocks-Release:` line. Paste `git diff --name-only` showing `agent_workflows/agy_runipd.py` is NOT modified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: with NO runner-profiles store visible (isolated `XDG_CONFIG_HOME`) and no flags, paste the effective verification decision for BOTH hosts, showing oc verification OFF and agy verification ON. Paste the new agy pin test's output and quote its assertion. This is the anti-regression check; a run showing agy verification OFF here is a failed execution, not a passing one. Also state explicitly that no `validate` key was added to agy's frozen options.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `options` block from a `state.json` produced by a real opencode invocation, showing the frozen `validate` AND `no_audit` and confirming they are consistent (`no_audit == not validate`). Paste a case where a stored PROFILE (not a flag) supplied the value, since a flag-only paste cannot distinguish this change from the old behavior. Paste the verifier-gate outcome for that run (whether a verification outcome file was written). Paste the first statement of `initialize_run` showing `resolve_launch_profile` was not moved.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `options.launch_profile` from a real `state.json` showing the `validate` VALUE and the provenance tier, for at least two different tiers (e.g. `explicit` and one configured tier). Paste the pre-existing test that renders an OLDER `launch_profile` record without the new key, still passing, since a record written before this change lacks it.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of the four targeted test modules and of the bare full suite (`python3 -m pytest`, no added flags), with the `N passed` summary line, and state the before/after suite counts. Name the test that pins agy's unchanged default and the test that asserts a frozen run honored a stored profile value. Confirm the new tests point `XDG_CONFIG_HOME` at a temp dir, and state that no test read or wrote the maintainer's real store.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the five paths in `Scope-Paths`. `agent_workflows/agy_runipd.py` IS DELIBERATELY EXCLUDED (F-8): that host cannot be wired here, so an edit to it is a scope violation, not a bonus. Do NOT change `runner_profiles.py`, `RUNNER_REGISTRY`, `SHIPPED_VALIDATE_DEFAULT`, the schema, or the precedence order. Do NOT add a `validate` key to agy's frozen options. Do NOT move `resolve_launch_profile` out of first position in `initialize_run`. Do not broaden casually; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark, and no claim of a passing suite may be written without the pasted output. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` is among the highest-contention modules in the repository and several other pending plans declare it, so expect drift, and expect to rebase or resolve and re-run the full suite after any merge. Find `resolve_launch_profile`, `launch_profile_record`, `initialize_run`'s freeze block, and the verifier gate by name.

THE ITEM THAT MATTERS MOST IS V-03. The original shape of this plan would have written a `validate` value into agy's inverted `no_verify` key and silently disabled verification on that host, a safety regression disguised as a wiring fix (F-5 records the arithmetic). The plan now forbids touching agy and demands a pin instead. If V-03 cannot be shown green, or if you find yourself editing `agy_runipd.py`, stop and report rather than proceeding.

On completion, close backlog `h7qsje`, which this plan carries as `- From-Backlog:`.
