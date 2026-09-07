# IPD: Move the verification default into the per-host runner registry row and register the antigravity host

- Date: 2026-09-06
- Kind: child
- Concern: The verification default is a SINGLE MODULE GLOBAL, `SHIPPED_VALIDATE_DEFAULT = False` (`runner_profiles.py:112`), consumed as tier 4 of the `validate` precedence chain (`:1015-1017`). But the two shipped hosts want OPPOSITE defaults, deliberately and on measured grounds: opencode gates the verifier turn on `validate` which defaults OFF (`oc_runipd.py:6212-6215`), while antigravity gates on `not no_verify`, verification ON, documented in as many words at `agy_runipd.py:3474-3482` ("NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`"). One constant cannot carry two host defaults, and it certainly cannot carry the six hosts `host_adapters.ALL_ADAPTER_HOSTS` already names. So the chain's bottom tier is CORRECT FOR ONE HOST BY COINCIDENCE and wrong for every other, which is a schema defect rather than a wiring gap.
  THE COST OF NOT FIXING IT IS ALREADY VISIBLE. Superseded plan `mn3gwr` (`- Status: superseded`, retired by this Set) reached the point of wiring the resolved value into the opencode driver and could not extend to antigravity, so its review reshaped its E-03 from "make agy's fallback correct" into "PROVE agy did not move": a TEST PINNING A HOST AGAINST A CONSTANT THAT DOES NOT DESCRIBE IT. That pin is the workaround this plan removes. `mn3gwr` F-5 records the arithmetic of the hazard correctly and this plan inherits that reasoning; what it corrects is the LOCATION of the fix.
- Scope: Add a `validate_default` field to `RunnerSpec`, the registry row that ALREADY carries the per-host launch facts (`supports_variant`, `supports_agent`), and resolve tier 4 from the row of the ALREADY-RESOLVED runner instead of from the module global. Register the antigravity host as a second registry row, which is what that registry's own docstring says adding a host costs ("Adding a host is ONE ROW here plus that host's own adapter work", `:194-196`). Update the five shipped tests that assert version 1's one-host population, deliberately and without weakening what they pin. NO driver is wired here and NO host's effective behavior changes: this plan makes the DATA correct so child 02 can consume it host-generally.
- Scope-Paths: agent_workflows/runner_profiles.py, tests/test_runner_profiles.py, tests/test_run_dispatch.py, tests/test_runner_profiles_e2e.py
- Item-Dependencies: none
- Status: to-review
- Set: hostdefault
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tm2cz8
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after a maintainer decision that redirected superseded plan `mn3gwr`. The maintainer asked why deepening the oc/agy driver divergence is a good thing (it is not), then asked for the options to be evaluated through the lens of eventual parity across opencode, antigravity, kiro-cli, claude, codex and hermes. THREE MEASUREMENTS DECIDED THE SHAPE, all taken live at `f3e17ff6` and all reproducible. FIRST, `mn3gwr`'s central blocker is OVERSTATED: its F-8 says wiring the second host needs "a registry (schema) change plus the whole seam `3cm15q` built for oc", but the `validate` chain does NOT consult the registry at all (`RUNNER_REGISTRY` and `canonical_runner` are both ABSENT from the chain block, verified by reading `inspect.getsource(resolve)`), and a PROTOTYPE adding one row plus one field made `resolve(runner="agy").validate` return `True` with provenance, made a profile declaring `runner: agy` parse and resolve, and kept the explicit flag winning on both hosts. SECOND, the real defect is the one `mn3gwr` worked around rather than the one it named: a single global cannot express two opposite host defaults, so its E-03 pin tests a host against a constant that does not describe it. THIRD, the six-host goal is already contradicted by FOUR host registries carrying FOUR different populations (`host_adapters.ALL_ADAPTER_HOSTS` 6, `host_capability_registry` 2, `runner_profiles.RUNNER_REGISTRY` 1, `run_dispatch.RUNNER_ADAPTERS` 1), so a per-host fact belongs in a row from the start. THE PROTOTYPE'S BLAST RADIUS WAS MEASURED, NOT ESTIMATED: full bare suite with the patch applied gave `5 failed, 5457 passed`, and all five failures are in two files and are deliberate one-host assertions or `RunnerSpec` constructor calls, enumerated as F-6. The prototype was then REVERTED and the baseline re-run clean at `5462 passed, 3 skipped, 2 xfailed`; no product code is modified by this authoring.

- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
## Goal

Make "how does this host verify by default" a per-host fact stored beside the other per-host facts, so the answer is correct for the second host today and for the sixth host without re-opening the resolver. This plan changes DATA and its resolution site only; no driver is wired and no host's observable behavior moves.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the default a per-host fact

- [ ] E-01 Add a `validate_default: bool` field to `RunnerSpec` (`runner_profiles.py:191-202`; RE-LOCATE BY SYMBOL, every line number in this plan may drift) and give the existing `oc` row the value `False`, which is its CURRENT effective default and must not change. Extend the class docstring to say what the field means and, critically, that it is the BOTTOM tier only: it is consulted when no explicit flag, no profile, and no `defaults.validate` spoke, so a row's value can never override an operator's typed choice.
  THE FIELD IS DELIBERATELY REQUIRED, NOT DEFAULTED. Giving it a Python default (`validate_default: bool = False`) would let a future host row omit it and silently inherit opencode's posture, which is the exact class of bug this plan exists to remove; a required field makes registering a host a decision about its verification posture. The measured consequence is that two shipped test call sites break (F-6), and E-05 updates them.
  - Depends on: none
  - Expected outcome: `RunnerSpec` carries `validate_default`; the `oc` row declares `False`; `RunnerSpec(...)` without the field raises `TypeError`; nothing else changed yet.
  - Execution state: pending

- [ ] E-02 Resolve tier 4 from the registry row instead of the module global. In `resolve()`'s validate chain (`runner_profiles.py:1015-1017`), replace `resolved_validate = SHIPPED_VALIDATE_DEFAULT` with the `validate_default` of the row for `resolved_runner`. THE ORDERING IS ALREADY CORRECT AND MUST BE CONFIRMED, NOT ASSUMED: `resolved_runner` is finalized in the `---- runner` block roughly 70 lines ABOVE the validate chain (measured: the runner block resolves at relative lines 29-53 of the function, the validate chain begins at relative line 103), so the row is available with no restructuring and no second lookup. Do NOT move either block.
  KEEP `SHIPPED_VALIDATE_DEFAULT` AS A NAME, do not delete it. Three tests reference it (`tests/test_runner_profiles.py:889-893`, `tests/test_runner_profiles_e2e.py:807`) and the module docstring cites it (`:56`). Redefine it as what it now is: the value the `oc` row carries, retained for compatibility, with a comment saying the authority moved to the row. Deleting it would break three tests for no benefit and would lose the documented link between the two.
  ALSO UPDATE THE MODULE DOCSTRING's precedence block (`:53-57`), which currently ends the chain at "the shipped default (`SHIPPED_VALIDATE_DEFAULT`, False, matching `oc_runipd`'s `--validate` ...)". That text becomes false the moment a second row exists with a different value, and this module's docstring is the only place the four-tier chain is written down in prose.
  - Depends on: E-01
  - Expected outcome: tier 4 reads the resolved runner's row; provenance for that tier is UNCHANGED (still `shipped-default`, see OQ-01); `SHIPPED_VALIDATE_DEFAULT` still exists and still equals `False`; the docstring's chain description matches the code.
  - Execution state: pending

### Task group 2: register the second host

- [ ] E-03 Add the `agy` registry row: `name="agy"`, `aliases=("antigravity",)`, `validate_default=True`. The alias is required for symmetry with `oc`'s `("opencode",)`, and `canonical_runner` already lowercases and checks aliases (`:409-414`), so `agy`/`AGY`/`antigravity` must all canonicalize to `agy` once the row exists.
  `validate_default=True` IS THE MEASURED CURRENT BEHAVIOR OF THAT HOST, not a new policy: `agy_runipd.py:3392-3399` gates the verifier on `not no_verify` and `--no-verify` is a `store_true` with an implicit `False` default (`:4447-4453`), so a bare `agy run start` verifies. This plan does NOT change that; it records it where the resolver can see it.
  SET `supports_variant=False` and `supports_agent=False`, which is also measured rather than chosen: `agy_runipd.py` appends only `--model` to its child argv (`:2575`) and its parser declares only `--model` (`:4417`), whereas `oc_runipd` appends all three (`:5223-5227`). A row claiming variant/agent support would let the store accept a profile whose fields that host silently drops, and `parse_profile` already refuses unsupported fields per row (`:517-531`), which is the mechanism that makes this honest.
  - Depends on: E-02
  - Expected outcome: `sorted(RUNNER_REGISTRY)` is `["agy", "oc"]`; `canonical_runner("antigravity")` returns `agy`; a profile declaring `runner: agy` with a valid `provider/model` parses; a profile declaring `runner: agy` WITH a `variant` or `agent` is REFUSED with the existing per-row message.
  - Execution state: pending

- [ ] E-04 Keep the DISPATCH refusal intact and prove it is now the reachable one. `run_dispatch.RUNNER_ADAPTERS` registers only `oc` (`run_dispatch.py:106-108`) and `adapter_for` deliberately distinguishes "not a runner at all" from "registered but has no adapter" (`:117-142`). Before this plan, an `agy` profile was refused EARLIER, at store load by the schema, so the registered-but-unimplemented branch was unreachable for that name; `tests/test_runner_profiles_e2e.py:624-632` records exactly that ("refused at STORE LOAD by the schema, before the router ever reaches its adapter table"). After E-03 the refusal MOVES to the adapter table.
  DO NOT ADD AN `agy` ADAPTER, and do not make `aw run as <agy-profile>` launch the antigravity driver. That is host-neutral dispatch for a second host, a separate concern with its own surface (the driver's argv contract, `--variant`/`--agent` absence, its own `main`), and folding it in here would make a data-shape plan into a dispatch plan. The REQUIRED outcome is that the refusal stays fail-closed and its MESSAGE remains accurate, naming the runner as known-but-not-dispatchable and pointing at the runners this build can reach.
  - Depends on: E-03
  - Expected outcome: `aw run as <profile with runner agy>` still refuses with exit 2 and still does NOT invoke `oc_runipd.main`; the refusal now comes from `adapter_for`'s registered-but-unimplemented branch, and the e2e test's assertion is updated to pin the NEW message while pinning the SAME guarantee (the wrong host driver is never launched).
  - Execution state: pending

### Task group 3: update the tests that pin one host

- [ ] E-05 Update the five shipped tests the change breaks, enumerated with their measured failure modes in F-6. EACH MUST BE UPDATED TO PIN THE SAME PROPERTY OVER THE NEW POPULATION, never deleted and never weakened to pass:
  (1) `tests/test_runner_profiles.py:158-166` `test_only_registered_runners_are_accepted` asserts `sorted(RUNNER_REGISTRY) == ["oc"]` and that `agy`/`antigravity`/`codex`/`claude` all raise. Update the population to `["agy", "oc"]`, MOVE `agy`/`antigravity` from the refused list to an accepted list, and KEEP `codex`/`claude`/`""`/`None`/`3` refused, since the point of the test is that the registry is closed, not that it has one row.
  (2) `tests/test_runner_profiles.py:651-656` `test_default_runner_setter_canonicalizes_and_clears` asserts `set_default_runner(cfg, "agy")` RAISES. That is now legal; change the negative case to a name that is still unregistered (`codex`) so the test still proves the setter canonicalizes AND refuses an unknown host.
  (3) `tests/test_runner_profiles.py:753-760` `test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back` asserts `resolve(cfg, runner="agy", profile="gem")` raises `ProfileSchemaError`. With `agy` registered, the RIGHT refusal for an oc profile requested on agy is `ProfileResolutionError` ("profile 'gem' runs on 'oc', but 'agy' was requested", `:938-942`), which is a BETTER test of the same property: a profile is never silently run on the wrong host. Update the expected exception type and say why in a comment.
  (4) and (5) `tests/test_run_dispatch.py:337-339` and `:395-397` construct `RunnerSpec(name="agy", aliases=(), supports_variant=True, supports_agent=False)` to SIMULATE a registered-but-unimplemented host. Both now fail with `TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'`. Add the field. Note these two tests become partly redundant once `agy` is really registered, but do NOT delete them: they pin the refusal for a HYPOTHETICAL future host, which is exactly the case that recurs at host three.
  - Depends on: E-04
  - Expected outcome: all five tests pass and each still pins its original property over the two-host population; no test was deleted, skipped, or had an assertion removed rather than updated.
  - Execution state: pending

- [ ] E-06 Add the tests this plan's own guarantees need, which the shipped suite cannot express because it predates a second row. FOUR properties, and the third is the one that would have caught the defect this plan fixes:
  (a) TIER 4 IS PER HOST: with an EMPTY store and no flag, `resolve(runner="oc").validate` is `False` and `resolve(runner="agy").validate` is `True`, both with provenance `shipped-default`.
  (b) A ROW NEVER BEATS AN OPERATOR: for BOTH hosts, an explicit `validate=True`/`validate=False` wins over the row (provenance `explicit`), and a `defaults.validate` wins over the row (provenance `defaults`). Assert the agy case with `defaults.validate: false`, which is the direction that proves the row is a FLOOR and not an override.
  (c) EVERY REGISTERED ROW DECLARES ITS POSTURE DELIBERATELY: iterate `RUNNER_REGISTRY` and assert every row's `validate_default` is a `bool`. This is the guard that makes host three a decision instead of an inheritance, and it is cheap and permanent.
  (d) THE TRI-STATE DOES NOT COLLAPSE ON THE NEW HOST: a profile for `agy` OMITTING `validate` must resolve to the row's `True`, while a profile explicitly saying `validate: false` must resolve `False` with provenance `profile`. Absent is not false; that is this module's stated contract (`:39-44`).
  Do NOT duplicate the resolver-level tier tests already at `tests/test_runner_profiles.py:843-935`; read them first and add only what a second host makes newly expressible.
  - Depends on: E-05
  - Expected outcome: four new assertions pass; (c) fails if a future row omits a deliberate posture; no existing resolver test is duplicated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE REGISTRY IS ALREADY THE HOME FOR PER-HOST LAUNCH FACTS, and says so. `RunnerSpec` carries `supports_variant` and `supports_agent` and its docstring calls itself "THE REGISTRY SEAM", stating "Adding a host is ONE ROW here plus that host's own adapter work; it is deliberately data rather than a `register_runner()` mutator, so nothing at runtime can widen the accepted runner set" (`runner_profiles.py:191-197`). This plan follows that instruction literally rather than inventing a mechanism.
- `resolve()` finalizes `resolved_runner` BEFORE the validate chain runs, so a per-host tier 4 needs no restructuring (measured: runner block at function-relative lines 29-53, validate chain at 103).
- The `validate` chain does not currently consult the registry at all. Verified by reading `inspect.getsource(resolve)`: neither `RUNNER_REGISTRY` nor `canonical_runner` appears in the chain block. That absence IS the defect, and it is why the fix is small.
- `validate` is a genuine TRI-STATE by explicit design (`_validate_tristate`, `:467`; docstring `:39-44`): ABSENT must never collapse to `false` at parse time, because an explicit flag must always beat a stored default. A per-host tier 4 sits strictly BELOW all three specified tiers and cannot violate this.
- `parse_profile` already enforces per-row field support (`:517-531`), so declaring `supports_variant=False` on a row is load-bearing: it makes the store refuse a profile whose fields that host would silently drop.
- THE TWO HOSTS' OPPOSITE DEFAULTS ARE DELIBERATE AND DOCUMENTED IN THE CODE. `agy_runipd.py:3474-3482` states the semantic difference explicitly and instructs a reader to "pass the locally-correct boolean rather than copying `oc`'s expression". This plan is the structural version of that instruction.
- Four separate registries name hosts with four different populations (F-4). A new per-host fact must go in a row, not in another global, or it inherits that fragmentation.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset; adding `-n0` or a second `-q` is measurably worse and suppresses the summary line this plan requires pasted.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The verification default is ONE MODULE GLOBAL consumed as tier 4, so it cannot express two hosts. | `runner_profiles.py:112` (`SHIPPED_VALIDATE_DEFAULT = False`), consumed at `:1015-1017` |
| F-2 | The two hosts' defaults are OPPOSITE, deliberately, and the code says so. opencode gates on `validate` (default OFF); antigravity gates on `not no_verify` (default ON, `--no-verify` is `store_true`). | `oc_runipd.py:6212-6215`, `:2969-2970`; `agy_runipd.py:3392-3399`, `:3474-3482`, `:4447-4453` |
| F-3 | **`mn3gwr`'s blocker is OVERSTATED, and this is why this plan exists.** Its F-8 says reaching agy needs "a registry (schema) change plus the whole seam `3cm15q` built for oc". But the validate chain never consults the registry (no `RUNNER_REGISTRY`, no `canonical_runner` in the chain block), and a live prototype of ONE field plus ONE row produced `resolve(runner="agy").validate == True` with provenance `defaults`/`shipped-default`, a parsing `runner: agy` profile resolving `validate=True` with provenance `profile`, and the explicit flag still winning on both hosts. | `inspect.getsource(runner_profiles.resolve)` chain-block scan; prototype run 2026-09-06 at `f3e17ff6`, reverted, tree verified clean |
| F-4 | **FOUR host registries carry FOUR different populations**, so a per-host fact placed anywhere but a row inherits the fragmentation: `host_adapters.ALL_ADAPTER_HOSTS` has 6 (opencode, codex, kiro, gemini_cli, claude_code, antigravity), `aw host capabilities` reports 2 (opencode, antigravity), `runner_profiles.RUNNER_REGISTRY` has 1, `run_dispatch.RUNNER_ADAPTERS` has 1. A plan titled "host-neutral run-as dispatch" (`ygzq71`) already EXECUTED and the runner registry is still one row. | `host_adapters.py:64-75`; `aw host capabilities` output; `runner_profiles.py:207-211`; `run_dispatch.py:106-108` |
| F-5 | **The workaround this plan removes.** `mn3gwr` E-03 pins antigravity's default with a TEST because no field could express it, and its own text calls that "a PIN, not a fallback". A test asserting a host's posture against a constant that does not describe that host is the symptom of the missing field. | `mn3gwr` E-03 and F-5 (`.aw/records/plans/pending/20260906-verifygap-01-mn3gwr-...ipd.md`, retired by this Set) |
| F-6 | **BLAST RADIUS MEASURED, NOT ESTIMATED: exactly 5 failures in 2 files, all deliberate one-host assertions.** Full bare suite with the prototype applied: `5 failed, 5457 passed, 3 skipped, 2 xfailed in 121.17s`. (1) `test_runner_profiles.py::RunnerCanonicalizationTests::test_only_registered_runners_are_accepted` (asserts the population is `["oc"]` and that `agy` raises); (2) `::MutationTests::test_default_runner_setter_canonicalizes_and_clears` (`AssertionError: ProfileSchemaError not raised` for `set_default_runner(cfg, "agy")`); (3) `::ResolutionPrecedenceTests::test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back` (expects `ProfileSchemaError` for `runner="agy"`); (4) `test_run_dispatch.py::AdapterRegistryTests::test_a_registered_but_unimplemented_runner_is_a_distinct_refusal` and (5) `::FailClosedRefusalTests::test_a_profile_whose_runner_has_no_adapter_refuses`, both `TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'`. | prototype full-suite run 2026-09-06; baseline re-verified clean afterwards at `5462 passed, 3 skipped, 2 xfailed in 115.53s` |
| F-7 | The e2e test that documents agy's refusal explicitly records that it happens at STORE LOAD "before the router ever reaches its adapter table", which is precisely the assertion that must move (not weaken) once the row exists. | `tests/test_runner_profiles_e2e.py:624-632` |
| F-8 | `SHIPPED_VALIDATE_DEFAULT` has three live test references and one docstring reference, so it must be retained rather than deleted when the authority moves to the row. | `tests/test_runner_profiles.py:889-893`; `tests/test_runner_profiles_e2e.py:807`; `runner_profiles.py:56` |
| F-9 | Antigravity genuinely supports neither `--variant` nor `--agent`: it appends only `--model` to child argv and declares only `--model`, whereas opencode appends all three. So the new row's `supports_*` values are measured, and `parse_profile`'s per-row refusal makes them enforceable. | `agy_runipd.py:2575`, `:4417`; `oc_runipd.py:5223-5227`; `runner_profiles.py:517-531` |

## Proposed changes (ordered, validatable)

1. Add `validate_default` to `RunnerSpec` as a REQUIRED field; give `oc` its current `False` (E-01).
2. Resolve tier 4 from the resolved runner's row; retain `SHIPPED_VALIDATE_DEFAULT` as a compatibility name; correct the module docstring's chain description (E-02).
3. Register the `agy` row with its measured posture and its measured field support (E-03).
4. Leave dispatch unimplemented for that host, and prove the refusal stays fail-closed while its message moves to the accurate branch (E-04).
5. Update the five one-host tests to pin the same properties over two hosts (E-05).
6. Add the four newly-expressible guarantees, including the per-row deliberateness guard (E-06).

## Deferred / out of scope (with reason)

- WIRING EITHER DRIVER. This plan changes the resolver's DATA and nothing consumes the resolved value yet, so no host's behavior moves. Child 02 (`ybkmzp`) does the wiring, host-generally, and declares `Item-Dependencies: executed:tm2cz8`. Splitting here is deliberate: a data-shape change with a measured 5-test blast radius should land and be verified before any driver reads it.
- ADDING AN `agy` DISPATCH ADAPTER (`aw run as <agy-profile>` actually launching that host). Separate concern with its own contract surface, and E-04 keeps the refusal fail-closed meanwhile. Deliberately NOT folded in: it is dispatch, not data.
- CONSOLIDATING THE FOUR HOST REGISTRIES (F-4). Real and worth doing, and it is the natural next step once a second row exists in the narrowest of them, but it touches `host_adapters`, `host_capability_registry` and `run_dispatch` and would dwarf this change. File it as backlog rather than widening this plan; this plan makes the case concrete by putting a real second row in one registry.
- REGISTERING kiro, codex, claude_code, gemini_cli or hermes. Each needs its own measured verification posture and its own adapter work; a row asserting a posture nobody measured would be exactly the unexamined normative claim this repository's spec-provenance audit found. E-06(c)'s guard makes each future row a deliberate decision.
- CHANGING EITHER HOST'S EFFECTIVE DEFAULT. `oc` stays OFF, `agy` stays ON. This plan records the existing postures; it does not rule on them.

## Scope check

- Over-scope: none. One resolver module plus the three test files F-6 measured as affected.
- Scope-Paths justification: `tests/test_runner_profiles.py` and `tests/test_run_dispatch.py` carry the five measured failures (F-6); `tests/test_runner_profiles_e2e.py` carries the refusal assertion that must move (F-7). No driver module is in scope, which is the point of the split.
- Under-scope: does not wire a driver, does not add a dispatch adapter, does not consolidate the registries, does not register a third host. Each is excluded with a stated reason above.

## Required tests / validation

- `python3 -m pytest` BARE, full suite, before and after, with the `N passed` summary line pasted and the counts stated. Baseline at authoring: `5462 passed, 3 skipped, 2 xfailed in 115.53s`.
- Targeted: `tests/test_runner_profiles.py`, `tests/test_run_dispatch.py`, `tests/test_runner_profiles_e2e.py`.
- A live per-host tier-4 demonstration with an ISOLATED store (`XDG_CONFIG_HOME` pointed at a temp dir, since `runner_profiles.store_path()` derives from `config.config_dir()`, `config.py:674-682`), so no test reads or writes the maintainer's real `runner-profiles.json`.
- `aw sanitize --agent` clean.

## Spec / documentation sync

The `validate` precedence chain is documented in `runner_profiles.py`'s own module docstring (`:39-57`), which E-02 must update: its tier-4 clause names `SHIPPED_VALIDATE_DEFAULT` and asserts the value "False, matching `oc_runipd`'s `--validate`", which becomes false for the second row. That docstring is the only prose statement of the four-tier chain, so leaving it stale would make the module lie about itself.

No SPEC change is authorized here. Spec `25kzda` records that skipping the verifier turn is a retained, host-configurable choice rather than a prohibited bypass (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:105`); this plan makes the host-level control expressible per host, which that text already anticipates. If the executor finds documentation claiming a single global verification default, NOTE IT for child 02 rather than editing a spec here.

## Open questions

### OQ-01: Should tier 4's provenance stay `shipped-default`, or gain a distinct per-host value?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP `shipped-default`, unchanged. The provenance vocabulary is a CLOSED SET (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`) that is recorded into run state and read by `launch_profile_record`, so adding a member is a state-format change with its own compatibility surface, and it would be a change to a field consumers already parse. The tier's MEANING is unchanged (it is still "nothing was configured, so the built-in applies"); only its VALUE became host-specific, which is what the `runner` field of the same record already tells a reader. If a later plan wants `host-default` as a distinct tier name, that is a deliberate vocabulary extension with its own migration, not a side effect of this one.

### OQ-02: Should `SHIPPED_VALIDATE_DEFAULT` be deleted once the row owns the value?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, retain it (F-8). Three tests reference it (`tests/test_runner_profiles.py:889-893`, `tests/test_runner_profiles_e2e.py:807`) and the module docstring cites it. Deleting it breaks three tests for no functional gain and destroys the documented link between the constant and the `oc` row. Redefine it as the `oc` row's value with a comment stating the authority moved; that keeps the compatibility surface while making the new source of truth unambiguous.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new `RunnerSpec` definition and the `oc` row. Paste a Python probe showing `RunnerSpec(name="x", aliases=(), supports_variant=True, supports_agent=True)` raising `TypeError` for the missing required argument, which proves the field cannot be silently omitted by a future host row. Quote the docstring sentence stating the field is the BOTTOM tier only.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the changed tier-4 lines from `resolve()`. Paste a probe showing that for an EMPTY store, `resolve(runner="oc").validate` is `False` and `resolve(runner="agy").validate` is `True`, with each provenance value shown. Paste the retained `SHIPPED_VALIDATE_DEFAULT` line and its new comment, plus the three tests that reference it still passing. Paste the UPDATED module-docstring precedence block and confirm in one sentence that it no longer claims a single global tier-4 value.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `sorted(RUNNER_REGISTRY)` showing both rows. Paste `canonical_runner` results for `agy`, `AGY`, and `antigravity`. Paste a successful parse of a profile declaring `runner: agy` with a valid `provider/model`, AND the REFUSAL text for the same profile carrying a `variant` or `agent`, since that refusal is what makes `supports_variant=False` load-bearing rather than decorative. State where agy's `validate_default=True` was measured from, citing the gate expression and the flag default.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the exit code and message for `aw run as <profile whose runner is agy>` with an isolated store, showing exit 2 and showing the refusal now names a known-but-not-dispatchable runner. Paste evidence that `oc_runipd.main` was NOT called (the shipped e2e pattern asserts an empty call list). Paste `sorted(run_dispatch.RUNNER_ADAPTERS)` showing it is still `['oc']`, proving no adapter was added. Paste the updated e2e assertion and state in one sentence which guarantee it still pins.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the three targeted test files. For EACH of the five tests in F-6, quote the updated assertion and state in one sentence what property it now pins over two hosts. A test that was deleted, skipped, `xfail`ed, or had an assertion removed rather than updated is a FAILED validation, and so is a paste that does not account for all five.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of the four new tests and of the BARE full suite (`python3 -m pytest`, no added flags) with its `N passed` summary line, stating before/after counts against the `5462 passed, 3 skipped, 2 xfailed` baseline. Name the test implementing guard (c) and paste proof it FAILS when a row omits a deliberate posture (add a bad row in a `mock.patch.dict`, show the failure, revert). Confirm the new tests point `XDG_CONFIG_HOME` at a temp dir and state that no test read or wrote the maintainer's real store. Confirm no resolver-level tier test from `tests/test_runner_profiles.py:843-935` was duplicated.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the four paths in `Scope-Paths`. Do NOT modify `oc_runipd.py` or `agy_runipd.py` in this plan; no driver is wired here, and an edit to either is a scope violation rather than a bonus (child 02 owns the wiring, and those two modules are the highest-contention files in the repository). Do NOT add a `run_dispatch` adapter. Do NOT change either host's effective default. Do NOT register a third host. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. NOTE: this repository is a SHARED CHECKOUT and a driver run may be live; `aw runs` before you start.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `RunnerSpec`, `RUNNER_REGISTRY`, `resolve`'s validate chain, `SHIPPED_VALIDATE_DEFAULT`, and `adapter_for` by name.

THE ITEM THAT MATTERS MOST IS V-05. The five failing tests are DELIBERATE assertions that version 1 admits exactly one host, and the cheap way to make them pass is to delete or weaken them. That would silently discard the "the registry is CLOSED" property, which is the guarantee that stops a runtime from widening the accepted host set. Every one of the five must end up pinning the same property over the two-host population. If any of the five cannot be updated that way, STOP and report rather than proceeding.

This plan's `- From-Backlog: h7qsje` and `- Blocks-Release: next` are INHERITED from superseded plan `mn3gwr`, so the release gate that plan carried is preserved rather than dropped. Do NOT close backlog `h7qsje` here: the operator-visible capability it describes is not delivered until child 02 (`ybkmzp`) wires the resolved value into the drivers, and closing it after this plan would claim a capability that no driver yet reads.
