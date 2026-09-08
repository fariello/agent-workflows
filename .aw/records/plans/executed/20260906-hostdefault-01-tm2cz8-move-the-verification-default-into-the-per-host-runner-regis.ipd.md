# IPD: Move the verification default into the per-host runner registry row and register the antigravity host

- Date: 2026-09-06
- Kind: child
- Concern: The verification default is a SINGLE MODULE GLOBAL, `SHIPPED_VALIDATE_DEFAULT = False` (`runner_profiles.py:112`), consumed as tier 4 of the `validate` precedence chain (`:1015-1017`). But the two shipped hosts want OPPOSITE defaults, deliberately and on measured grounds: opencode gates the verifier turn on `validate` which defaults OFF (`oc_runipd.py:6279-6288`), while antigravity gates on `not no_verify`, verification ON, documented in as many words at `agy_runipd.py:3568-3574` ("NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`"). One constant cannot carry two host defaults, and it certainly cannot carry the six hosts `host_adapters.ALL_ADAPTER_HOSTS` already names. So the chain's bottom tier is CORRECT FOR ONE HOST BY COINCIDENCE and wrong for every other, which is a schema defect rather than a wiring gap.
  LINE NUMBERS IN THE DRIVERS DRIFTED BETWEEN AUTHORING AND REVIEW. This plan was authored against `f3e17ff6`; every driver citation was re-resolved at review time against HEAD `aeb71ca2` and corrected in place. The drift is why RE-LOCATE BY SYMBOL (stated in the gate) is not optional advice: `oc_runipd.py` and `agy_runipd.py` moved by roughly 70 and 95 lines respectively in a single day. No driver is edited by this plan, so the citations are evidence only.
  THE COST OF NOT FIXING IT IS ALREADY VISIBLE. Superseded plan `mn3gwr` (`- Status: superseded`, retired by this Set) reached the point of wiring the resolved value into the opencode driver and could not extend to antigravity, so its review reshaped its E-03 from "make agy's fallback correct" into "PROVE agy did not move": a TEST PINNING A HOST AGAINST A CONSTANT THAT DOES NOT DESCRIBE IT. That pin is the workaround this plan removes. `mn3gwr` F-5 records the arithmetic of the hazard correctly and this plan inherits that reasoning; what it corrects is the LOCATION of the fix.
- Scope: Add a `validate_default` field to `RunnerSpec`, the registry row that ALREADY carries the per-host launch facts (`supports_variant`, `supports_agent`), and resolve tier 4 from the row of the ALREADY-RESOLVED runner instead of from the module global. Register the antigravity host as a second registry row, which is what that registry's own docstring says adding a host costs ("Adding a host is ONE ROW here plus that host's own adapter work", `:194-196`). Update the SIX shipped tests that assert version 1's one-host population, deliberately and without weakening what they pin, and correct the four in-code prose statements that assert a one-host registry. NO driver is wired here and NO host's effective behavior changes: this plan makes the DATA correct so child 02 can consume it host-generally.
  REGISTERING A ROW IS NOT INERT, WHICH THIS PLAN'S ORIGINAL SCOPE UNDERSTATED. `canonical_runner` is the WRITE-TIME gate for the whole store (`parse_profile` at `:517`, `_validate_referential_integrity` at `:564`, `set_default_runner` at `:884`), so the row makes `runner: agy` and `default_runner: agy` newly STORABLE. Measured at review: both dispatch routes then refuse at `adapter_for` with exit 2 and never launch the wrong host, so the fail-closed guarantee survives; but the operator-visible consequence is that a store can now hold a configuration nothing can run. E-04 and E-07 make that refusal, and its accuracy, an explicit deliverable rather than an assumption.
- Scope-Paths: agent_workflows/runner_profiles.py, agent_workflows/run_dispatch.py, agent_workflows/runner_profile_wizard.py, tests/test_runner_profiles.py, tests/test_run_dispatch.py, tests/test_runner_profiles_e2e.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: hostdefault
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tm2cz8
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history
- 2026-09-08 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Lane recovered and merged during the stranded-lane recovery; integration had been refused by the binary whole-repo suite gate (root cause tracked by 32ij2j/xtklpd) [Scope reconciliation - out-of-scope agent_workflows/oc_runipd.py: NOT THIS PLAN'S EDIT. Belongs to f7124702 merge lane nna8yz_attempt2: recover stranded validated work, , a concurrent lane or agent; verified absent from this plan's own commits (050ec996). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope docs/runner-profiles.md: NOT THIS PLAN'S EDIT. Belongs to 3798d236 runprofile-06 kgpptv: let the verifier turn resolve its own p, a concurrent lane or agent; verified absent from this plan's own commits (050ec996). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_oc_runipd.py: NOT THIS PLAN'S EDIT. Belongs to 2ceb645f merge lane kgpptv: recover stranded validated work, a concurrent lane or agent; verified absent from this plan's own commits (050ec996). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.]
- 2026-09-07 approved (aw set): status set to approved

- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-510. Reviewed at HEAD `aeb71ca2`; `aw ipd lint --phase author` conformed before semantic review and `--phase review-finalize` after. SELF-REVIEW disclosure: the same session authored this plan. The plan's THESIS was independently re-verified and holds: the prototype was rebuilt from scratch in an isolated worktree and `resolve(runner="oc").validate` is `False`/`shipped-default` while `resolve(runner="agy").validate` is `True`/`shipped-default`, `defaults.validate: false` still beats the row on agy, an `agy` profile omitting `validate` inherits `True` while one saying `validate: false` resolves `False`/`profile`, and a profile carrying `variant` is refused per row. What review CHANGED is that three of the plan's own measurements were wrong or incomplete, each in the direction of understating the work. FIRST, the blast radius is SIX tests, not five: `tests/test_runner_profiles_e2e.py` is `pytest.mark.slow` and the mandated bare suite DESELECTS it, so the authored measurement could not see it, and naming the path directly reports `no tests ran`. SECOND, the authored baseline is stale and HEAD is NOT clean, so the plan's stated pass criterion was unmeetable as written. THIRD, registering the row makes `default_runner: agy` newly WRITABLE, which reaches `adapter_for` through a route the plan never named; both routes were driven live and both refuse exit 2 without launching, so the guarantee holds, but it now has to be proven. Two new E-items were added (E-07 for four in-code prose statements that assert a one-host registry, two of them outside the authored Scope-Paths; E-08 for the explicit-`variant`/`agent` hole the row makes reachable), and two authoring traps were measured and forbidden in place: defining the retained constant from the registry raises `NameError` at import, and a `NamedTuple` annotation does not type-check, so `validate_default="yes"` is accepted and truthy. Scope-Paths grew from four to six. No product code was modified by this review; the prototype was reverted and its worktree removed.

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after a maintainer decision that redirected superseded plan `mn3gwr`. The maintainer asked why deepening the oc/agy driver divergence is a good thing (it is not), then asked for the options to be evaluated through the lens of eventual parity across opencode, antigravity, kiro-cli, claude, codex and hermes. THREE MEASUREMENTS DECIDED THE SHAPE, all taken live at `f3e17ff6` and all reproducible. FIRST, `mn3gwr`'s central blocker is OVERSTATED: its F-8 says wiring the second host needs "a registry (schema) change plus the whole seam `3cm15q` built for oc", but the `validate` chain does NOT consult the registry at all (`RUNNER_REGISTRY` and `canonical_runner` are both ABSENT from the chain block, verified by reading `inspect.getsource(resolve)`), and a PROTOTYPE adding one row plus one field made `resolve(runner="agy").validate` return `True` with provenance, made a profile declaring `runner: agy` parse and resolve, and kept the explicit flag winning on both hosts. SECOND, the real defect is the one `mn3gwr` worked around rather than the one it named: a single global cannot express two opposite host defaults, so its E-03 pin tests a host against a constant that does not describe it. THIRD, the six-host goal is already contradicted by FOUR host registries carrying FOUR different populations (`host_adapters.ALL_ADAPTER_HOSTS` 6, `host_capability_registry` 2, `runner_profiles.RUNNER_REGISTRY` 1, `run_dispatch.RUNNER_ADAPTERS` 1), so a per-host fact belongs in a row from the start. THE PROTOTYPE'S BLAST RADIUS WAS MEASURED, NOT ESTIMATED: full bare suite with the patch applied gave `5 failed, 5457 passed`, and all five failures are in two files and are deliberate one-host assertions or `RunnerSpec` constructor calls, enumerated as F-6. The prototype was then REVERTED and the baseline re-run clean at `5462 passed, 3 skipped, 2 xfailed`; no product code is modified by this authoring.

- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
## Goal

Make "how does this host verify by default" a per-host fact stored beside the other per-host facts, so the answer is correct for the second host today and for the sixth host without re-opening the resolver. This plan changes DATA and its resolution site only; no driver is wired and no host's observable behavior moves.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the default a per-host fact

- [x] E-01 Add a `validate_default: bool` field to `RunnerSpec` (`runner_profiles.py:191-202`; RE-LOCATE BY SYMBOL, every line number in this plan may drift) and give the existing `oc` row the value `False`, which is its CURRENT effective default and must not change. Extend the class docstring to say what the field means and, critically, that it is the BOTTOM tier only: it is consulted when no explicit flag, no profile, and no `defaults.validate` spoke, so a row's value can never override an operator's typed choice.
  THE FIELD IS DELIBERATELY REQUIRED, NOT DEFAULTED. Giving it a Python default (`validate_default: bool = False`) would let a future host row omit it and silently inherit opencode's posture, which is the exact class of bug this plan exists to remove; a required field makes registering a host a decision about its verification posture. The measured consequence is that two shipped test call sites break (F-6), and E-05 updates them.
  - Depends on: none
  - Expected outcome: `RunnerSpec` carries `validate_default`; the `oc` row declares `False`; `RunnerSpec(...)` without the field raises `TypeError`; nothing else changed yet.
  - Execution state: performed

- [x] E-02 Resolve tier 4 from the registry row instead of the module global. In `resolve()`'s validate chain (`runner_profiles.py:1015-1017`), replace `resolved_validate = SHIPPED_VALIDATE_DEFAULT` with the `validate_default` of the row for `resolved_runner`. THE ORDERING IS ALREADY CORRECT AND MUST BE CONFIRMED, NOT ASSUMED: `resolved_runner` is finalized in the `---- runner` block roughly 70 lines ABOVE the validate chain (measured: the runner block resolves at relative lines 29-53 of the function, the validate chain begins at relative line 103), so the row is available with no restructuring and no second lookup. Do NOT move either block.
  KEEP `SHIPPED_VALIDATE_DEFAULT` AS A NAME, do not delete it. Three tests reference it (`tests/test_runner_profiles.py:889-893`, `tests/test_runner_profiles_e2e.py:807`) and the module docstring cites it (`:56`). Retain it as the literal `False` with a comment stating that it is now the `oc` row's value and that the AUTHORITY moved to the row. Deleting it would break three tests for no benefit and would lose the documented link between the two.
  DO NOT DEFINE IT AS `RUNNER_REGISTRY["oc"].validate_default`. That is the obvious-looking expression of "retain it as the row's value" and it does not import: the constant is defined at `:112` and `RUNNER_REGISTRY` at `:207`, so the reference is a module-level forward reference. MEASURED at review: `NameError: name 'RUNNER_REGISTRY' is not defined` at import, which breaks the entire package rather than one test. Either keep the literal (preferred, one line, no ordering coupling) or move the constant BELOW the registry; if you move it, say so, because the module docstring's tier-4 clause and the reading order both assume it precedes the schema constants. A test asserting the two agree (E-06) is what keeps a literal honest.
  ALSO UPDATE THE MODULE DOCSTRING's precedence block (`:53-57`), which currently ends the chain at "the shipped default (`SHIPPED_VALIDATE_DEFAULT`, False, matching `oc_runipd`'s `--validate` ...)". That text becomes false the moment a second row exists with a different value, and this module's docstring is the only place the four-tier chain is written down in prose.
  - Depends on: E-01
  - Expected outcome: tier 4 reads the resolved runner's row; provenance for that tier is UNCHANGED (still `shipped-default`, see OQ-01); `SHIPPED_VALIDATE_DEFAULT` still exists and still equals `False`; the module IMPORTS (no forward reference); the docstring's chain description matches the code.
  - Execution state: performed

- [x] E-07 Correct the FOUR in-code prose statements that assert a one-host registry, which the row makes false. This is not polish: three of them are the reader's only statement of the registry's population, and one of them is the docstring of the very field this plan adds.
  (1) `runner_profiles.py:194` `RunnerSpec`'s own docstring, "THE REGISTRY SEAM. Version 1 registers OpenCode only." Restate the population as the two rows, and KEEP the load-bearing sentence that follows ("Adding a host is ONE ROW here plus that host's own adapter work"), which this plan is the proof of.
  (2) `runner_profiles.py:205-206` the `RUNNER_REGISTRY` comment, "Version 1: OpenCode (`oc`), whose CLI accepts `--model`, `--variant` and `--agent`". Name both rows and state each one's measured field support, since the two differ and that difference is now enforced.
  (3) `run_dispatch.py:101` "Version 1 registers OpenCode only, matching `runner_profiles.RUNNER_REGISTRY`." That sentence is now DOUBLY wrong and in the more dangerous direction: the two registries no longer match, and their disagreement is exactly what makes the registered-but-unimplemented branch reachable. Say that plainly, because a future reader who believes the two tables match will not understand why `adapter_for` refuses a name the schema accepted.
  (4) `runner_profile_wizard.py:71-73` "Version 1 of the schema registers OpenCode only (`runner_profiles.RUNNER_REGISTRY`); a second host needs its own adapter, not a widened wizard." The parenthetical CONCLUSION stays correct and is worth keeping; the premise does not. Correct the premise and keep `RUNNER = "oc"` unchanged: the wizard still configures opencode only, and widening it is not in this plan.
  DO NOT widen any behavior while editing these four sites. This item changes COMMENTS AND DOCSTRINGS ONLY, and `git diff` must show no executable line touched in `run_dispatch.py` or `runner_profile_wizard.py`.
  - Depends on: E-03
  - Expected outcome: no in-code prose claims a one-host registry; `RUNNER = "oc"` unchanged; the diff for the two non-resolver modules is comment-only.
  - Execution state: performed

### Task group 2: register the second host

- [x] E-03 Add the `agy` registry row: `name="agy"`, `aliases=("antigravity",)`, `validate_default=True`. The alias is required for symmetry with `oc`'s `("opencode",)`, and `canonical_runner` already lowercases and checks aliases (`:409-414`), so `agy`/`AGY`/`antigravity` must all canonicalize to `agy` once the row exists.
  `validate_default=True` IS THE MEASURED CURRENT BEHAVIOR OF THAT HOST, not a new policy: `agy_runipd.py:3392-3399` gates the verifier on `not no_verify` and `--no-verify` is a `store_true` with an implicit `False` default (`:4447-4453`), so a bare `agy run start` verifies. This plan does NOT change that; it records it where the resolver can see it.
  SET `supports_variant=False` and `supports_agent=False`, which is also measured rather than chosen: `agy_runipd.py` appends only `--model` to its child argv (`:2575`) and its parser declares only `--model` (`:4417`), whereas `oc_runipd` appends all three (`:5223-5227`). A row claiming variant/agent support would let the store accept a profile whose fields that host silently drops, and `parse_profile` already refuses unsupported fields per row (`:517-531`), which is the mechanism that makes this honest.
  - Depends on: E-02
  - Expected outcome: `sorted(RUNNER_REGISTRY)` is `["agy", "oc"]`; `canonical_runner("antigravity")` returns `agy`; a profile declaring `runner: agy` with a valid `provider/model` parses; a profile declaring `runner: agy` WITH a `variant` or `agent` is REFUSED with the existing per-row message.
  - Execution state: performed

- [x] E-04 Keep the DISPATCH refusal intact and prove it is now the reachable one. `run_dispatch.RUNNER_ADAPTERS` registers only `oc` (`run_dispatch.py:106-108`) and `adapter_for` deliberately distinguishes "not a runner at all" from "registered but has no adapter" (`:117-142`). Before this plan, an `agy` profile was refused EARLIER, at store load by the schema, so the registered-but-unimplemented branch was unreachable for that name; `tests/test_runner_profiles_e2e.py:624-632` records exactly that ("refused at STORE LOAD by the schema, before the router ever reaches its adapter table"). After E-03 the refusal MOVES to the adapter table.
  DO NOT ADD AN `agy` ADAPTER, and do not make `aw run as <agy-profile>` launch the antigravity driver. That is host-neutral dispatch for a second host, a separate concern with its own surface (the driver's argv contract, `--variant`/`--agent` absence, its own `main`), and folding it in here would make a data-shape plan into a dispatch plan. The REQUIRED outcome is that the refusal stays fail-closed and its MESSAGE remains accurate, naming the runner as known-but-not-dispatchable and pointing at the runners this build can reach.
  COVER BOTH ROUTES, NOT ONLY `as`. `default_runner: agy` is newly STORABLE once the row exists, because `set_default_runner` and `_validate_referential_integrity` both gate on `canonical_runner` (`:884`, `:564`), so `aw run ipd <selector>` reaches `adapter_for` through `resolve_default_runner` (`run_dispatch.py:180-196`) with no profile named at all. MEASURED at review with an isolated store holding `default_runner: agy`: both `aw run ipd SEL` and `aw run as g SEL` exit 2 with the registered-but-unimplemented message and launch nothing. Pin BOTH; the original E-04 named only the profile route, which would have left the default route's refusal unproven at exactly the moment it became reachable.
  - Depends on: E-03
  - Expected outcome: BOTH `aw run as <profile with runner agy>` and `aw run ipd <selector>` under `default_runner: agy` refuse with exit 2 and do NOT invoke `oc_runipd.main`; the refusal comes from `adapter_for`'s registered-but-unimplemented branch; the e2e test's assertion is updated to pin the NEW message while pinning the SAME guarantee (the wrong host driver is never launched).
  - Execution state: performed

- [x] E-08 Decide and record what an EXPLICIT `variant`/`agent` argument means for a row that declares no support, which registering the second row makes reachable for the first time. `parse_profile` enforces `supports_variant`/`supports_agent` for a STORED profile (`:517-531`), but `resolve()`'s per-field block consults NEITHER flag: MEASURED at review, `resolve(cfg, runner="agy", variant="high", agent="build")` returns `variant='high'`, `agent='build'` with provenance `explicit`, silently carrying fields that host's argv builder does not emit (`agy_runipd.py:2667` appends only `--model`). Before this plan the path was unreachable, because `runner="agy"` raised at `canonical_runner`; after it, it resolves.
  THE MINIMUM DELIVERABLE IS A RECORDED DECISION PLUS A TEST, NOT NECESSARILY A REFUSAL. Two defensible answers: (a) REFUSE in `resolve()`, consistent with `parse_profile`, so the store and the caller enforce the same row contract; or (b) ACCEPT and document that an explicit caller field is the caller's problem, on the ground that no dispatch path can reach agy anyway (E-04) so nothing can act on the stray value today. Choose ONE, state the reasoning in a comment at the decision site, and add a test pinning the CHOSEN behavior so it is a decision rather than an accident. If you choose (a), the refusal must be a typed `ProfileSchemaError` matching `parse_profile`'s wording, and you must confirm no shipped test asserted the permissive behavior.
  DO NOT let this item grow into a general per-field capability audit. It concerns exactly the two `supports_*` flags already on the row, exactly in `resolve()`, and exactly for an explicitly-passed value.
  - Depends on: E-03
  - Expected outcome: `resolve()`'s treatment of an unsupported explicit `variant`/`agent` is deliberate, commented at the site, and pinned by a test; the choice between refusing and documenting is recorded with its reason.
  - Execution state: performed

### Task group 3: update the tests that pin one host

- [x] E-05 Update the SIX shipped tests the change breaks, enumerated with their measured failure modes in F-6. THE COUNT WAS FIVE AT AUTHORING AND IS WRONG; see F-10 for why the sixth was invisible. EACH MUST BE UPDATED TO PIN THE SAME PROPERTY OVER THE NEW POPULATION, never deleted and never weakened to pass:
  (1) `tests/test_runner_profiles.py:158-166` `test_only_registered_runners_are_accepted` asserts `sorted(RUNNER_REGISTRY) == ["oc"]` and that `agy`/`antigravity`/`codex`/`claude` all raise. Update the population to `["agy", "oc"]`, MOVE `agy`/`antigravity` from the refused list to an accepted list, and KEEP `codex`/`claude`/`""`/`None`/`3` refused, since the point of the test is that the registry is closed, not that it has one row.
  (2) `tests/test_runner_profiles.py:651-656` `test_default_runner_setter_canonicalizes_and_clears` asserts `set_default_runner(cfg, "agy")` RAISES. That is now legal; change the negative case to a name that is still unregistered (`codex`) so the test still proves the setter canonicalizes AND refuses an unknown host.
  (3) `tests/test_runner_profiles.py:753-760` `test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back` asserts `resolve(cfg, runner="agy", profile="gem")` raises `ProfileSchemaError`. With `agy` registered, the RIGHT refusal for an oc profile requested on agy is `ProfileResolutionError` ("profile 'gem' runs on 'oc', but 'agy' was requested", `:938-942`), which is a BETTER test of the same property: a profile is never silently run on the wrong host. Update the expected exception type and say why in a comment.
  (4) and (5) `tests/test_run_dispatch.py:337-339` and `:395-397` construct `RunnerSpec(name="agy", aliases=(), supports_variant=True, supports_agent=False)` to SIMULATE a registered-but-unimplemented host. Both now fail with `TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'`. Add the field. Note these two tests become partly redundant once `agy` is really registered, but do NOT delete them: they pin the refusal for a HYPOTHETICAL future host, which is exactly the case that recurs at host three. While there, consider renaming the simulated host so it does not collide with a REAL row (a `mock.patch.dict` that overwrites the shipped `agy` row now silently shadows real data rather than adding a fictional host); that is a clarity improvement, not a requirement.
  (6) `tests/test_runner_profiles_e2e.py` `NegativeE2E::test_wrong_runner_profile_is_not_launched_by_opencode`, which F-7 already identifies as the assertion that must MOVE. Its two message assertions (`"unknown runner 'agy'"`, `"registers: oc"`) both fail; MEASURED at review, the observed message is now `runner 'agy' is a known runner but has no dispatch adapter in this build ... Runners this build can dispatch to: oc.` KEEP the two assertions that carry the guarantee (`rc == 2`, `calls == []`, both of which still pass unchanged), REPLACE the two message assertions, and REWRITE the eight-line comment above them, which currently states the refusal happens "at STORE LOAD by the schema, before the router ever reaches its adapter table" and is now precisely backwards.
  ALSO CHECK `tests/test_run_dispatch.py:266-267` `test_only_oc_is_registered_in_version_1`, which asserts `run_dispatch.registered_runners() == ["oc"]`. It does NOT break, because that function reads `RUNNER_ADAPTERS` and no adapter is added. Do NOT "fix" it; its continuing to pass is the PROOF that E-04 added no adapter, and V-04 requires that. Its NAME becomes slightly misleading (it now pins the dispatch table, not the schema registry), which you may correct in a comment.
  - Depends on: E-04
  - Expected outcome: all six tests pass and each still pins its original property over the two-host population; `test_only_oc_is_registered_in_version_1` still passes UNCHANGED; no test was deleted, skipped, or had an assertion removed rather than updated.
  - Execution state: performed

- [x] E-06 Add the tests this plan's own guarantees need, which the shipped suite cannot express because it predates a second row. FOUR properties, and the third is the one that would have caught the defect this plan fixes:
  (a) TIER 4 IS PER HOST: with an EMPTY store and no flag, `resolve(runner="oc").validate` is `False` and `resolve(runner="agy").validate` is `True`, both with provenance `shipped-default`.
  (b) A ROW NEVER BEATS AN OPERATOR: for BOTH hosts, an explicit `validate=True`/`validate=False` wins over the row (provenance `explicit`), and a `defaults.validate` wins over the row (provenance `defaults`). Assert the agy case with `defaults.validate: false`, which is the direction that proves the row is a FLOOR and not an override.
  (c) EVERY REGISTERED ROW DECLARES ITS POSTURE DELIBERATELY: iterate `RUNNER_REGISTRY` and assert every row's `validate_default` is a `bool`. This is the guard that makes host three a decision instead of an inheritance, and it is cheap and permanent.
  A `NamedTuple` ANNOTATION IS NOT A RUNTIME CHECK, which is what makes (c) load-bearing rather than redundant. MEASURED at review: `RunnerSpec(..., validate_default="yes").validate_default` returns the string `'yes'` with no error, and `"yes"` is truthy, so an unexamined row would resolve tier 4 to a silent ON. The REQUIRED assertion is therefore `isinstance(row.validate_default, bool)` and NOT a mere `assertIn(row.validate_default, (True, False))`, since `1 in (True, False)` is `True` in Python and would let an `int` through. Assert `type(...) is bool` or `isinstance(..., bool)`; state which you used and why in a comment.
  While iterating, ALSO assert `SHIPPED_VALIDATE_DEFAULT == RUNNER_REGISTRY["oc"].validate_default`. E-02 keeps the constant as a literal for import-ordering reasons, so this one assertion is what stops the retained compatibility name from silently drifting away from the row it claims to mirror.
  (d) THE TRI-STATE DOES NOT COLLAPSE ON THE NEW HOST: a profile for `agy` OMITTING `validate` must resolve to the row's `True`, while a profile explicitly saying `validate: false` must resolve `False` with provenance `profile`. Absent is not false; that is this module's stated contract (`:39-44`).
  Do NOT duplicate the resolver-level tier tests already at `tests/test_runner_profiles.py:843-935`; read them first and add only what a second host makes newly expressible.
  - Depends on: E-05
  - Expected outcome: four new assertions pass; (c) fails if a future row omits a deliberate posture AND if a row declares a non-`bool`; the constant-mirrors-the-row assertion passes; no existing resolver test is duplicated.
  - Execution state: performed

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
| F-6 | **BLAST RADIUS: SIX failures in THREE files, all deliberate one-host assertions.** CORRECTED AT REVIEW; the authored count of five was measured with a command that cannot see the sixth (F-10). Re-measured at HEAD `aeb71ca2` with the prototype applied. Bare run: (1) `test_runner_profiles.py::RunnerCanonicalizationTests::test_only_registered_runners_are_accepted` (asserts the population is `["oc"]` and that `agy` raises); (2) `::MutationTests::test_default_runner_setter_canonicalizes_and_clears` (`AssertionError: ProfileSchemaError not raised` for `set_default_runner(cfg, "agy")`); (3) `::ResolutionPrecedenceTests::test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back` (expects `ProfileSchemaError` for `runner="agy"`); (4) `test_run_dispatch.py::AdapterRegistryTests::test_a_registered_but_unimplemented_runner_is_a_distinct_refusal` and (5) `::FailClosedRefusalTests::test_a_profile_whose_runner_has_no_adapter_refuses`, both `TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'`. SLOW run (`-m slow`): (6) `test_runner_profiles_e2e.py::NegativeE2E::test_wrong_runner_profile_is_not_launched_by_opencode`, `AssertionError: "unknown runner 'agy'" not found in "aw run as: runner 'agy' is a known runner but has no dispatch adapter in this build..."`. | prototype run 2026-09-06 at `aeb71ca2` in an isolated worktree: bare `20 failed, 5535 passed` (of which 15 `test_run_viewer.py` failures are the known worktree `.aw/state` artifact `dh0uno` and 1 is the pre-existing failure in F-11, leaving 4 attributable), `-m slow` `7 failed, 457 passed` (of which 6 pre-existing per F-11, leaving 1 attributable) |
| F-7 | The e2e test that documents agy's refusal explicitly records that it happens at STORE LOAD "before the router ever reaches its adapter table", which is precisely the assertion that must move (not weaken) once the row exists. CONFIRMED at review to be one of the six real failures, not merely a comment to update. | `tests/test_runner_profiles_e2e.py:624-632` |
| F-8 | `SHIPPED_VALIDATE_DEFAULT` has three live test references and one docstring reference, so it must be retained rather than deleted when the authority moves to the row. It must ALSO stay a LITERAL: defining it as `RUNNER_REGISTRY["oc"].validate_default` is a module-level forward reference (constant at `:112`, registry at `:207`) and raises `NameError` at import, measured at review. | `tests/test_runner_profiles.py:889-893`; `tests/test_runner_profiles_e2e.py:807`; `runner_profiles.py:56`, `:112`, `:207` |
| F-9 | Antigravity genuinely supports neither `--variant` nor `--agent`: it appends only `--model` to child argv and declares only `--model`, whereas opencode appends all three. So the new row's `supports_*` values are measured, and `parse_profile`'s per-row refusal makes them enforceable FOR A STORED PROFILE. It does NOT constrain an EXPLICIT caller argument: `resolve()` consults neither `supports_*` flag, so `resolve(runner="agy", variant="high", agent="build")` returns both values with provenance `explicit` (measured at review). E-08 makes that a decision. | `agy_runipd.py:2667`, `:4534-4538`; `oc_runipd.py:5292-5297`; `runner_profiles.py:517-531`; live `resolve()` probe under the prototype |
| F-10 | **WHY THE SIXTH FAILURE WAS INVISIBLE, and the process lesson.** `tests/test_runner_profiles_e2e.py:58` sets `pytestmark = pytest.mark.slow`, and the configured `addopts` (`pyproject.toml:169`) supply `-m 'not slow'`, so the BARE `python3 -m pytest` this repository mandates DESELECTS that whole file (30 tests). Naming the file does not help: `python3 -m pytest tests/test_runner_profiles_e2e.py` reports `no tests ran`, because the marker filter still applies. The authored F-6 measurement was therefore correct for the command it ran and incomplete for the change it assessed. Any plan whose Scope-Paths name a `slow`-marked test file MUST validate with `-m slow` as well; this one does, in the validation section. | `tests/test_runner_profiles_e2e.py:58`; `pyproject.toml:169`; measured `no tests ran in 2.00s` for the direct-path invocation |
| F-11 | **THE BASELINE AT HEAD IS NOT CLEAN, so the authored baseline cannot be used as the pass criterion.** The plan cites `5462 passed, 3 skipped, 2 xfailed` from `f3e17ff6`. Measured at HEAD `aeb71ca2`: bare `1 failed, 5554 passed, 3 skipped, 2 xfailed`, the failure being `test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` (`{'kgpptv': 'approved'} != {'kgpptv': 'reviewed'}`), which asserts against a REAL plan's live status and broke when a sibling plan was approved; it is unrelated to this plan and is not this plan's to fix. `-m slow` gives `6 to 8 failed, 456-458 passed`, varying run to run (`test_installer`/`test_cli` cleanup and the CLI-surface declaration guards), i.e. partly order- or environment-dependent. The executor must therefore compare against a baseline IT MEASURES ITSELF immediately before the change, not against the number in this plan. | bare and `-m slow` runs at `aeb71ca2`, 2026-09-06, review session |
| F-12 | **FOUR IN-CODE PROSE STATEMENTS ASSERT A ONE-HOST REGISTRY** and become false with the row, two of them in modules the authored Scope-Paths did not include. `runner_profiles.py:194` ("Version 1 registers OpenCode only", the docstring of the very type this plan extends), `:205-206` (the registry comment, which also enumerates only opencode's field support), `run_dispatch.py:101` ("Version 1 registers OpenCode only, matching `runner_profiles.RUNNER_REGISTRY`", now wrong in the dangerous direction since the tables' DISAGREEMENT is what makes `adapter_for`'s second branch reachable), and `runner_profile_wizard.py:71-73`. E-07 corrects all four, comment-only. | `runner_profiles.py:194`, `:205-206`; `run_dispatch.py:101`; `runner_profile_wizard.py:71-73` |
| F-13 | **REGISTERING THE ROW MAKES A NEW STORE STATE WRITABLE, which the authored plan did not state.** `canonical_runner` is the write-time gate for `parse_profile` (`:517`), `_validate_referential_integrity` (`:564`) and `set_default_runner` (`:884`), and its own docstring gives the rationale ("a profile naming a host nobody can launch is a failure the user should see at write time, not at 3am", `:401-402`) - which the row partially inverts, since `agy` becomes storable while remaining unlaunchable. MEASURED at review with an isolated store carrying `default_runner: agy` plus an `agy` profile: `aw run ipd SEL` and `aw run as g SEL` BOTH exit 2 with the registered-but-unimplemented message and launch nothing, so the guarantee holds on both routes. E-04 now pins both. | `runner_profiles.py:401-402`, `:517`, `:564`, `:884`; `run_dispatch.py:180-196`; live two-route probe under the prototype |

## Proposed changes (ordered, validatable)

1. Add `validate_default` to `RunnerSpec` as a REQUIRED field; give `oc` its current `False` (E-01).
2. Resolve tier 4 from the resolved runner's row; retain `SHIPPED_VALIDATE_DEFAULT` as a LITERAL compatibility name (not a forward reference, F-8); correct the module docstring's chain description (E-02).
3. Register the `agy` row with its measured posture and its measured field support (E-03).
4. Leave dispatch unimplemented for that host, and prove the refusal stays fail-closed on BOTH routes while its message moves to the accurate branch (E-04).
5. Update the six one-host tests to pin the same properties over two hosts (E-05).
6. Add the four newly-expressible guarantees, including the per-row deliberateness guard with a real `isinstance` check (E-06).
7. Correct the four in-code prose statements that assert a one-host registry, comment-only (E-07).
8. Decide, comment, and pin what an explicit unsupported `variant`/`agent` means for a row that declares no support (E-08).

## Deferred / out of scope (with reason)

- WIRING EITHER DRIVER. This plan changes the resolver's DATA and nothing consumes the resolved value yet, so no host's behavior moves. Child 02 (`ybkmzp`) does the wiring, host-generally, and declares `Item-Dependencies: executed:tm2cz8`. Splitting here is deliberate: a data-shape change with a measured 5-test blast radius should land and be verified before any driver reads it.
- ADDING AN `agy` DISPATCH ADAPTER (`aw run as <agy-profile>` actually launching that host). Separate concern with its own contract surface, and E-04 keeps the refusal fail-closed meanwhile on BOTH routes. Deliberately NOT folded in: it is dispatch, not data. ACCEPTED CONSEQUENCE, stated because the row makes it newly possible (F-13): a store can now hold `runner: agy` or `default_runner: agy`, which nothing in this build can run. That partially inverts `canonical_runner`'s own stated rationale of refusing at write time rather than at 3am (`runner_profiles.py:401-402`). It is acceptable here because the failure is a CLEAR exit-2 refusal naming the reachable runners at every dispatch entry point (measured on both routes), not a silent misroute, and because the wizard still only writes `oc` (`runner_profile_wizard.py:73`), so reaching this state takes hand-editing the store. If the adapter does not land reasonably soon, the honest follow-up is a store-load WARNING for a registered-but-undispatchable runner; that is a separate change and is not authorized here.
- WIDENING THE PROFILE WIZARD to offer a second host. `RUNNER = "oc"` stays, and E-07 explicitly keeps it while correcting only the false premise in its comment. Offering agy in the wizard would let a user create by wizard exactly the unrunnable store state described above, which is the opposite of what this plan wants.
- CONSOLIDATING THE FOUR HOST REGISTRIES (F-4). Real and worth doing, and it is the natural next step once a second row exists in the narrowest of them, but it touches `host_adapters`, `host_capability_registry` and `run_dispatch` and would dwarf this change. File it as backlog rather than widening this plan; this plan makes the case concrete by putting a real second row in one registry.
- REGISTERING kiro, codex, claude_code, gemini_cli or hermes. Each needs its own measured verification posture and its own adapter work; a row asserting a posture nobody measured would be exactly the unexamined normative claim this repository's spec-provenance audit found. E-06(c)'s guard makes each future row a deliberate decision.
- CHANGING EITHER HOST'S EFFECTIVE DEFAULT. `oc` stays OFF, `agy` stays ON. This plan records the existing postures; it does not rule on them.

## Scope check

- Over-scope: none. One resolver module, two comment-only modules, and the three test files F-6 measured as affected.
- Scope-Paths justification: `tests/test_runner_profiles.py` and `tests/test_run_dispatch.py` carry five of the six measured failures (F-6); `tests/test_runner_profiles_e2e.py` carries the sixth, which is the refusal assertion that must move (F-7). `agent_workflows/run_dispatch.py` and `agent_workflows/runner_profile_wizard.py` were ADDED at review for E-07: each carries a comment asserting a one-host registry that the row makes false (F-12), and each edit is COMMENT-ONLY with the diff constrained accordingly. No driver module is in scope, which is the point of the split.
- Under-scope: does not wire a driver, does not add a dispatch adapter, does not consolidate the registries, does not register a third host, does not widen the profile wizard to a second host. Each is excluded with a stated reason above.

## Required tests / validation

- `python3 -m pytest` BARE, full suite, before and after, with the `N passed` summary line pasted and the counts stated.
- `python3 -m pytest -m slow`, full slow subset, before and after, with its summary line pasted. THIS IS NOT OPTIONAL AND NOT A DEVIATION FROM THE BARE-SUITE RULE: `tests/test_runner_profiles_e2e.py` is in Scope-Paths and is `pytest.mark.slow`, so the bare run DESELECTS it entirely and cannot see failure (6) (F-10). A bare-only paste would report green while a Scope-Paths file is red. `-m slow` REPLACES the configured marker filter and adds nothing else, so it is not "bolting on flags to help".
- MEASURE YOUR OWN BEFORE-BASELINE and paste it. Do NOT use the authored `5462 passed` figure as the pass criterion: HEAD is not clean and the slow subset is partly order-dependent (F-11). The criterion is that the set of failures AFTER your change, minus the set you measured BEFORE it, is EMPTY. If a pre-existing failure disappears, say so; if one appears, it is yours until you prove otherwise by name.
- Targeted: `tests/test_runner_profiles.py`, `tests/test_run_dispatch.py`, and `tests/test_runner_profiles_e2e.py` (the last REQUIRES `-m slow`; naming the path alone reports `no tests ran`, measured).
- A live per-host tier-4 demonstration with an ISOLATED store (`XDG_CONFIG_HOME` pointed at a temp dir, since `runner_profiles.store_path()` derives from `config.config_dir()`, `config.py:674-682`), so no test reads or writes the maintainer's real `runner-profiles.json`.
- A live TWO-ROUTE dispatch refusal demonstration under the same isolated store (`aw run as <agy profile>` and `aw run ipd` with `default_runner: agy`), per E-04 and F-13.
- `python3 -c "import agent_workflows.runner_profiles"` succeeds. Trivial, and it is the check that catches the F-8 forward-reference `NameError`, which breaks the whole package rather than one test.
- `aw sanitize --agent` clean.

## Spec / documentation sync

The `validate` precedence chain is documented in `runner_profiles.py`'s own module docstring (`:39-57`), which E-02 must update: its tier-4 clause names `SHIPPED_VALIDATE_DEFAULT` and asserts the value "False, matching `oc_runipd`'s `--validate`", which becomes false for the second row. That docstring is the only prose statement of the four-tier chain, so leaving it stale would make the module lie about itself.

E-07 corrects the OTHER four prose statements, which are in-code comments rather than the docstring E-02 owns (F-12). Two of them live outside the resolver, which is why `run_dispatch.py` and `runner_profile_wizard.py` joined Scope-Paths at review; both edits are comment-only and V-07 requires the diff to prove it.

No SPEC change is authorized here. Spec `25kzda` records that skipping the verifier turn is a retained, host-configurable choice rather than a prohibited bypass (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:105`), verified verbatim at review including its conditional reasoning ("until per-role model routing exists ... a host-level control is the only available mechanism"); this plan makes the host-level control expressible per host, which that text already anticipates. If the executor finds documentation claiming a single global verification default, NOTE IT for child 02 rather than editing a spec here.

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

- [x] V-01 validates E-01
  - Required evidence: paste the new `RunnerSpec` definition and the `oc` row. Paste a Python probe showing `RunnerSpec(name="x", aliases=(), supports_variant=True, supports_agent=True)` raising `TypeError` for the missing required argument, which proves the field cannot be silently omitted by a future host row. Quote the docstring sentence stating the field is the BOTTOM tier only.
  - Observed evidence: VERIFIED. `RunnerSpec` carries `validate_default`; the `oc` row declares `False` (unchanged effective default); the field is REQUIRED, proven by the `TypeError` probe below; the docstring states it is the BOTTOM tier only. Full evidence:
    THE NEW FIELD LIST (`agent_workflows/runner_profiles.py`, `class RunnerSpec`):

    ```python
        name: str
        aliases: Tuple[str, ...]
        supports_variant: bool
        supports_agent: bool
        validate_default: bool
    ```

    THE `oc` ROW, whose value is its CURRENT effective default and did not change:

    ```python
        "oc": RunnerSpec(
            name="oc",
            aliases=("opencode",),
            supports_variant=True,
            supports_agent=True,
            validate_default=False,
        ),
    ```

    THE FIELD IS REQUIRED, not defaulted (probe, `logs/probe-resolver.txt`):

    ```text
    == V-01: RunnerSpec requires validate_default ==
    TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'
    ```

    THE BOTTOM-TIER SENTENCE, quoted verbatim from the extended class docstring: "``validate_default`` is that host's SHIPPED verification posture, and it is the BOTTOM TIER of the `validate` precedence chain ONLY: it is consulted when no explicit flag, no profile `validate`, and no `defaults.validate` spoke, so a row can never override an operator's typed choice." The docstring also records WHY the field carries no Python default: "a defaulted field would let a future host row omit it and silently inherit OpenCode's posture, which is the exact class of bug the per-host row exists to remove."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the changed tier-4 lines from `resolve()`. Paste a probe showing that for an EMPTY store, `resolve(runner="oc").validate` is `False` and `resolve(runner="agy").validate` is `True`, with each provenance value shown. Paste the retained `SHIPPED_VALIDATE_DEFAULT` line and its new comment, plus the three tests that reference it still passing. Paste the output of `python3 -c "import agent_workflows.runner_profiles"` succeeding, which is what proves the F-8 forward-reference trap was avoided; if you MOVED the constant below the registry instead of keeping the literal, say so and state what else you had to reorder. Paste the UPDATED module-docstring precedence block and confirm in one sentence that it no longer claims a single global tier-4 value.
  - Observed evidence: VERIFIED. Tier 4 now reads `RUNNER_REGISTRY[resolved_runner].validate_default`; an empty store resolves `oc`->`False` and `agy`->`True`, both provenance `shipped-default`; `SHIPPED_VALIDATE_DEFAULT` is retained as a LITERAL (not moved, nothing reordered) and the module imports; the docstring chain no longer claims a single global. Full evidence:
    THE CHANGED TIER-4 BRANCH, the `else` arm of the validate chain in `resolve()` (neither the runner block nor the chain was moved):

    ```python
        else:
            # TIER 4 IS PER HOST (`hostdefault-01` E-02). Read the SHIPPED posture off the row of the
            # runner resolved above, not off a module global: `oc` verifies OFF by default and `agy`
            # verifies ON, so one constant would be right for one host by coincidence and wrong for
            # every other. `resolved_runner` is finalized in the `---- runner` block far above and is
            # always a canonical registry key, so this lookup needs no restructuring and cannot miss.
            # The provenance stays `shipped-default` (OQ-01): the tier's MEANING is unchanged
            # ("nothing was configured, so the built-in applies"); only its value is host-specific,
            # and the record's own `runner` field already says which host that was.
            resolved_validate = RUNNER_REGISTRY[resolved_runner].validate_default
            provenance["validate"] = PROVENANCE_SHIPPED
    ```

    PER-HOST TIER 4 WITH AN EMPTY STORE (isolated `XDG_CONFIG_HOME`, store confirmed absent; `logs/probe-resolver.txt`):

    ```text
    store_path (isolated): /tmp/aw-isolated-store-<tmp>/agent-workflows/runner-profiles.json
    store exists: False
    config present (absent store): False
      resolve(runner='oc').validate = False  provenance='shipped-default'
      resolve(runner='agy').validate = True  provenance='shipped-default'
    SHIPPED_VALIDATE_DEFAULT = False == oc row: True
    ```

    Provenance for the tier is UNCHANGED (`shipped-default` on both hosts), per OQ-01.

    THE CONSTANT WAS KEPT AS A LITERAL AND NOT MOVED. Nothing was reordered; the constant still precedes the schema constants exactly as before, so the module's reading order is untouched:

    ```python
    #: The `oc` row's shipped `validate` default, retained as a COMPATIBILITY NAME. FALSE, matching
    #: `oc_runipd.py`'s `--validate` (`BooleanOptionalAction`, `default=False`).
    #:
    #: THE AUTHORITY FOR TIER 4 MOVED TO THE REGISTRY ROW: :func:`resolve` reads
    #: ``RUNNER_REGISTRY[<resolved runner>].validate_default``, because the two shipped hosts want
    #: OPPOSITE defaults and one global cannot express both. This name is kept because tests and this
    #: module's docstring cite it, and it must stay a LITERAL rather than
    #: ``RUNNER_REGISTRY["oc"].validate_default``: the registry is defined BELOW this line, so that
    #: expression is a module-level forward reference and raises `NameError` at import. A test asserts
    #: this literal still equals the `oc` row's value, which is what keeps the two from drifting.
    SHIPPED_VALIDATE_DEFAULT = False
    ```

    THE IMPORT SUCCEEDS, which is the check that proves the F-8 forward-reference trap was avoided:

    ```text
    $ python3 -c "import agent_workflows.runner_profiles; print('import OK')"
    import OK
    ```

    THE THREE REFERENCING TESTS STILL PASS. The two in `tests/test_runner_profiles.py` (the level-4 case at `:916-917`, plus the new drift assertion at `:1047`):

    ```text
    $ python3 -m pytest -o addopts="" -q \
        "tests/test_runner_profiles.py::ValidatePrecedenceMatrixTests::test_level_4_shipped_default_applies_when_no_level_specified" \
        "tests/test_runner_profiles.py::PerHostValidateDefaultTests::test_every_registered_row_declares_a_real_bool_posture"
    ..                                                                       [100%]
    2 passed in 0.16s
    ```

    and the `slow` e2e doc test that cites it (`tests/test_runner_profiles_e2e.py:810`):

    ```text
    $ python3 -m pytest -o addopts="-m slow" -q "tests/test_runner_profiles_e2e.py" -k "doc"
    ......                                                                   [100%]
    6 passed, 24 deselected in 0.50s
    ```

    THE UPDATED MODULE-DOCSTRING PRECEDENCE BLOCK:

    ```text
    For `validate`, with an ABSENT level falling THROUGH rather than reading as `false`::

        explicit --validate/--no-validate  >  profile's own `validate`  >
        `defaults.validate`  >  the RESOLVED RUNNER's shipped posture
        (:attr:`RunnerSpec.validate_default` on its :data:`RUNNER_REGISTRY` row)

    TIER 4 IS PER HOST, not one global. The two shipped hosts want OPPOSITE defaults, deliberately:
    `oc` verification defaults OFF (`oc_runipd`'s `--validate` BooleanOptionalAction defaults False)
    while `agy` defaults ON (`agy_runipd` gates its verifier on `not no_verify`, and `--no-verify` is
    a `store_true`). One module constant cannot carry two host postures, so the value lives on the
    registry row beside the other per-host launch facts. :data:`SHIPPED_VALIDATE_DEFAULT` is retained
    as a compatibility name for the `oc` row's value only.
    ```

    That block no longer claims a single global tier-4 value: it names the RESOLVED RUNNER's row as the authority and demotes `SHIPPED_VALIDATE_DEFAULT` to a compatibility name for the `oc` row only. `resolve()`'s own docstring chain line was updated to match ("the RESOLVED RUNNER's `validate_default` row value").
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `sorted(RUNNER_REGISTRY)` showing both rows. Paste `canonical_runner` results for `agy`, `AGY`, and `antigravity`. Paste a successful parse of a profile declaring `runner: agy` with a valid `provider/model`, AND the REFUSAL text for the same profile carrying a `variant` or `agent`, since that refusal is what makes `supports_variant=False` load-bearing rather than decorative. State where agy's `validate_default=True` was measured from, citing the gate expression and the flag default.
  - Observed evidence: VERIFIED. `sorted(RUNNER_REGISTRY)` is `['agy', 'oc']`; `agy`/`AGY`/`antigravity` all canonicalize to `agy`; an `agy` profile parses and is REFUSED when it carries `variant` or `agent`; `validate_default=True` is measured from the driver's gate expression and flag default. Full evidence:
    BOTH ROWS, CANONICALIZATION, PARSE AND PER-ROW REFUSAL (`logs/probe-resolver.txt`):

    ```text
    == V-02/V-03: registry + per-host tier 4 ==
    sorted(RUNNER_REGISTRY): ['agy', 'oc']
      row agy: RunnerSpec(name='agy', aliases=('antigravity',), supports_variant=False, supports_agent=False, validate_default=True)
      row oc: RunnerSpec(name='oc', aliases=('opencode',), supports_variant=True, supports_agent=True, validate_default=False)
      canonical_runner('agy') -> 'agy'
      canonical_runner('AGY') -> 'agy'
      canonical_runner('antigravity') -> 'agy'
      canonical_runner('oc') -> 'oc'
      canonical_runner('OpenCode') -> 'oc'

    == V-03: agy profile parses; variant/agent refused per row ==
      parsed: LaunchProfile(runner='agy', model='synthetic/gem-test', variant=None, agent=None, validate=None)
      REFUSED (variant): profile 'gg': runner 'agy' does not support a model variant
      REFUSED (agent): profile 'gg': runner 'agy' does not support an agent
    ```

    Note the parse input declared `runner: "antigravity"` and the stored value came back canonicalized to `agy`, so the alias is live through `parse_profile` and not merely through `canonical_runner`.

    WHERE `validate_default=True` WAS MEASURED, re-resolved BY SYMBOL at this HEAD rather than trusting the plan's authored line numbers (which drifted, per the plan's own note):
    - THE GATE EXPRESSION, `agent_workflows/agy_runipd.py:3626-3632`: `no_verify = state.get("options", {}).get("no_verify") or state.get("options", {}).get("no_audit")`, then the verifier turn runs `if (not is_review and disposition in ("executed", "substantially-complete") and not no_verify)`. So the verifier is gated on `not no_verify`, i.e. verification is ON unless suppressed.
    - THE FLAG DEFAULT, `agent_workflows/agy_runipd.py:4738-4743`: `"--no-verify", "--no-audit", dest="no_verify", action="store_true"`, so `no_verify` is implicitly `False` and a bare `agy run start` verifies.
    - THE DRIVER ITSELF SAYS SO IN PROSE, `agy_runipd.py:3709-3713`: "NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`: this driver gates the verifier on `not no_verify` (verification defaults ON here), whereas `oc` gates on `validate` (which defaults OFF)."
    - THE OPPOSITE POLE, for contrast, `oc_runipd.py:7643-7649`: `"--validate", "--verify", "--audit", dest="validate", action=argparse.BooleanOptionalAction, default=False`, and the gate at `:6455` reads `if integration_gate_relevant and not validate`.

    `supports_variant=False`/`supports_agent=False` are equally measured, not chosen: `agy_runipd.py:2802` appends only `["--model", options["model"]]` to the child argv (plus `--effort`, which is not a profile field), its parser declares `--model` at `:4707` and declares no `--variant` and no `--agent` at all (`grep` for either `add_argument` returns nothing), whereas `oc_runipd` appends all three.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the exit code and message for BOTH routes with an isolated store: `aw run as <profile whose runner is agy>` AND `aw run ipd <selector>` with `default_runner: agy`, each showing exit 2 and each showing the refusal names a known-but-not-dispatchable runner. A single-route paste is a FAILED validation, because the default route is the one the row newly made reachable (F-13). Paste evidence that `oc_runipd.main` was NOT called (the shipped e2e pattern asserts an empty call list). Paste `sorted(run_dispatch.RUNNER_ADAPTERS)` showing it is still `['oc']`, and paste `test_only_oc_is_registered_in_version_1` PASSING UNCHANGED, which together prove no adapter was added. Paste the updated e2e assertion and state in one sentence which guarantee it still pins.
  - Observed evidence: VERIFIED ON BOTH ROUTES. `aw run as <agy profile>` and `aw run ipd` under `default_runner: agy` each exit 2 with the registered-but-unimplemented message and an EMPTY `oc_runipd.main` call list; `RUNNER_ADAPTERS` is still `['oc']` and `test_only_oc_is_registered_in_version_1` passes unchanged. Full evidence:
    BOTH ROUTES REFUSED, exit 2, no driver launched. Isolated store holding BOTH newly-writable states at once (`default_runner: agy` AND a profile whose runner is `agy`), with `oc_runipd.main` patched to record any call (`logs/probe-dispatch.txt`):

    ```text
    isolated store: /tmp/aw-isolated-store-<tmp>/agent-workflows/runner-profiles.json
    {"schema_version": 1, "default_runner": "agy", "profiles": {"g": {"runner": "agy", "model": "synthetic/gem-test"}}}
    sorted(run_dispatch.RUNNER_ADAPTERS): ['oc']
    run_dispatch.registered_runners(): ['oc']

    $ aw run as g SEL
      exit code: 2
      oc_runipd.main calls: []
      output: aw run as: runner 'agy' is a known runner but has no dispatch adapter in this build, so `aw run` cannot launch it. Runners this build can dispatch to: oc. Use that host's own command directly, or name a profile whose runner is one of them ('aw oc profile list').

    $ aw run ipd SEL
      exit code: 2
      oc_runipd.main calls: []
      output: aw run ipd: runner 'agy' is a known runner but has no dispatch adapter in this build, so `aw run` cannot launch it. Runners this build can dispatch to: oc. Use that host's own command directly, or name a profile whose runner is one of them ('aw oc profile list').
    ```

    Both messages come from `adapter_for`'s registered-but-unimplemented branch (they say "is a known runner but has no dispatch adapter", not "unknown runner"), and both name the reachable set (`oc`). The store LOADED in both cases, which is the change: the refusal moved from the schema to the adapter table. The DEFAULT route reached `adapter_for` with no profile named at all, via `resolve_default_runner`, which is the route F-13 identified as newly reachable.

    NO ADAPTER WAS ADDED. `sorted(run_dispatch.RUNNER_ADAPTERS)` is `['oc']` (above), and the shipped guard passes UNCHANGED (`git diff -- tests/test_run_dispatch.py` contains no occurrence of its name, so it was not edited):

    ```text
    $ python3 -m pytest -o addopts="" -q "tests/test_run_dispatch.py::AdapterRegistryTests::test_only_oc_is_registered_in_version_1" -v
    collected 1 item
    tests/test_run_dispatch.py .                                             [100%]
    ============================== 1 passed in 0.16s ===============================
    ```

    THE UPDATED e2e ASSERTION (`tests/test_runner_profiles_e2e.py`, `NegativeE2E::test_wrong_runner_profile_is_not_launched_by_opencode`):

    ```python
            self.assertEqual(rc, 2, out)
            self.assertEqual(calls, [], "the wrong host driver was launched")
            self.assertIn("no dispatch adapter", out)
            self.assertIn("'agy'", out)
    ```

    It still pins the guarantee that has always mattered: a profile written for another host is refused (exit 2) and the OpenCode driver is NEVER called (`calls == []`); only the WHERE of the refusal moved, from store load to the adapter table. Both message assertions were REPLACED rather than removed, and the eight-line comment above them, which said the refusal happened "at STORE LOAD by the schema, before the router ever reaches its adapter table" and is now precisely backwards, was rewritten to describe the new location and to state that the guarantee is unchanged (see V-05).

    A REGRESSION TEST FOR THE REAL ROW was also added rather than relying on the probe alone: `tests/test_run_dispatch.py::FailClosedRefusalTests::test_the_real_agy_row_refuses_on_both_routes_without_launching` drives BOTH routes through the CLI against the shipped registry (no `mock.patch.dict`), asserting exit 2, an empty host-call list, and the registered-but-unimplemented message for each.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the three targeted test files, and note that `tests/test_runner_profiles_e2e.py` requires `-m slow` (a paste showing `no tests ran` for that file is NOT evidence it passed). For EACH of the SIX tests in F-6, quote the updated assertion and state in one sentence what property it now pins over two hosts. A test that was deleted, skipped, `xfail`ed, or had an assertion removed rather than updated is a FAILED validation, and so is a paste that does not account for all six. Also confirm the e2e test's now-backwards comment was rewritten, not merely its assertions.
  - Observed evidence: VERIFIED, ALL SIX. Every one of the six was UPDATED to pin its original property over the two-host population; none was deleted, skipped, xfailed or had an assertion removed; the e2e test's now-backwards comment was rewritten, not merely its assertions. Full evidence:
    THE THREE TARGETED FILES, ACTUAL OUTPUT. The two fast files:

    ```text
    $ python3 -m pytest tests/test_runner_profiles.py tests/test_run_dispatch.py
    bringing up nodes...
    ........................................................................ [ 55%]
    ..........................................................               [100%]
    130 passed in 9.18s
    ```

    and the third file, which REQUIRES `-m slow` (naming its path under the configured `addopts` reports `no tests ran`, per F-10):

    ```text
    $ python3 -m pytest -m slow tests/test_runner_profiles_e2e.py
    bringing up nodes...
    ..............................                                           [100%]
    30 passed in 6.60s
    ```

    ALL SIX, INDIVIDUALLY RUN AND PASSING (`logs/six-tests-fast.txt`):

    ```text
    ### tests/test_runner_profiles.py::RunnerCanonicalizationTests::test_only_registered_runners_are_accepted
    1 passed in 0.12s
    ### tests/test_runner_profiles.py::MutationTests::test_default_runner_setter_canonicalizes_and_clears
    1 passed in 0.13s
    ### tests/test_runner_profiles.py::ResolutionPrecedenceTests::test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back
    1 passed in 0.11s
    ### tests/test_run_dispatch.py::AdapterRegistryTests::test_a_registered_but_unimplemented_runner_is_a_distinct_refusal
    1 passed in 0.16s
    ### tests/test_run_dispatch.py::FailClosedRefusalTests::test_a_profile_whose_runner_has_no_adapter_refuses
    1 passed in 0.26s
    ### e2e (slow)
    1 passed in 0.28s
    ```

    (1) `test_only_registered_runners_are_accepted`:

    ```python
            self.assertEqual(sorted(RP.RUNNER_REGISTRY), ["agy", "oc"])
            for name, canonical in (("agy", "agy"), ("antigravity", "agy"), ("AGY", "agy")):
                with self.subTest(accepted=name):
                    self.assertEqual(RP.canonical_runner(name), canonical)
            for name in ("codex", "claude", "kiro", "", None, 3):
                with self.subTest(runner=name):
                    with self.assertRaises(RP.ProfileSchemaError):
                        RP.canonical_runner(name)
    ```

    PINS: the registry is CLOSED over the two-host population. `agy`/`antigravity` MOVED from the refused list to an accepted list (with `AGY` added to prove the row's alias path lowercases), while every unregistered host and every non-name stays refused, so nothing at runtime can widen the accepted host set. The property was never "there is one row"; a comment now says so, and `kiro` was added to the refused set so the closure claim covers a host that `host_adapters` names but this registry does not.

    (2) `test_default_runner_setter_canonicalizes_and_clears`:

    ```python
            self.assertEqual(
                RP.set_default_runner(cfg, "antigravity").default_runner, "agy"
            )
            with self.assertRaises(RP.ProfileSchemaError):
                RP.set_default_runner(cfg, "codex")
    ```

    PINS: the setter still does BOTH of its jobs over two hosts, canonicalizing any registered host (now demonstrated through the `agy` alias, not only `opencode`) and refusing an unregistered one, with `codex` taking over the negative case that `agy` used to serve. A comment records that `agy` is now storable-but-unlaunchable.

    (3) `test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back`:

    ```python
            with self.assertRaises(RP.ProfileResolutionError):
                RP.resolve(self.cfg, runner="agy", profile="gem")
            # An UNREGISTERED runner is still the schema refusal, so both halves stay covered.
            with self.assertRaises(RP.ProfileSchemaError):
                RP.resolve(self.cfg, runner="codex", profile="gem")
    ```

    PINS: a profile is never silently run on a host it was not written for, and it now pins that through the REAL cross-host mismatch (`ProfileResolutionError`: "profile 'gem' runs on 'oc', but 'agy' was requested") rather than through a name the registry rejected before resolution got that far, which is a strictly stronger test of the same property. The `ProfileSchemaError` half was KEPT by moving it to `codex`, so unregistered-runner coverage did not disappear.

    (4) `test_a_registered_but_unimplemented_runner_is_a_distinct_refusal`:

    ```python
            spec = runner_profiles.RunnerSpec(
                name="futurehost",
                aliases=(),
                supports_variant=True,
                supports_agent=False,
                validate_default=False,
            )
            with mock.patch.dict(
                runner_profiles.RUNNER_REGISTRY, {"futurehost": spec}, clear=False
            ):
    ```

    PINS: "known runner, no adapter" is reported distinctly from "not a runner at all", for a HYPOTHETICAL host, which is the case that recurs at host three. The required `validate_default` was added, and the simulated host was RENAMED from `agy` to `futurehost` (the clarity improvement the plan invited): patching the key `agy` would now SHADOW a shipped row rather than add a fictional one, so the test would have silently stopped testing what it claims. Both original assertions (`"no dispatch adapter"` present, `"is not a registered runner"` absent) are untouched.

    (5) `test_a_profile_whose_runner_has_no_adapter_refuses`: same `validate_default=False` addition and same `futurehost` rename, with the store's profile now declaring `"runner": "futurehost"`; the assertion `self.assertIn("no dispatch adapter", out)` is unchanged. PINS: a profile naming a schema-valid host with no adapter refuses fail-closed without launching any driver, whichever host that is. The REAL `agy` case is not left to the probe: a new sibling test covers both dispatch routes against the shipped registry (see V-04).

    (6) `NegativeE2E::test_wrong_runner_profile_is_not_launched_by_opencode`: the two surviving assertions (`rc == 2`, `calls == []`) are unchanged and the two message assertions were REPLACED with `assertIn("no dispatch adapter", out)` and `assertIn("'agy'", out)`, as quoted in V-04. PINS: the wrong host's driver is never launched for a profile written for another host.

    THE e2e COMMENT WAS REWRITTEN, not merely the assertions. It previously asserted the refusal happens "at STORE LOAD by the schema, before the router ever reaches its adapter table", which is now backwards. It now reads:

    ```python
            # MEASURED behavior, and WHERE THE REFUSAL COMES FROM MOVED in `hostdefault-01`. It used to
            # happen at STORE LOAD, because the schema registry admitted `oc` only, so `agy` was
            # rejected before the router ever reached its adapter table. The schema now registers `agy`
            # too (that is where the host's verification posture lives), so the store LOADS and the
            # refusal comes one step later, from `run_dispatch.adapter_for`'s
            # registered-but-unimplemented branch: a known runner with no adapter in this build.
            # THE GUARANTEE IS UNCHANGED AND IS THE POINT: the OpenCode driver is NOT called, so a
            # profile written for another host is never quietly run by this one.
    ```

    NOTHING WAS DELETED, SKIPPED OR WEAKENED. `git diff -- tests/` contains no removed `def test_` line and no added `skip`/`xfail`:

    ```text
    $ git diff -- tests/ | grep -E "^\-.*def test_|^\+.*(skip|xfail)"
    NONE: no test definition deleted, no skip/xfail added
    ```

    `test_only_oc_is_registered_in_version_1` also still passes UNCHANGED (V-04), which is the proof required that E-04 added no adapter; its name now describes the dispatch table rather than the schema registry, and the sibling test added beside it makes that distinction explicit in prose.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of the four new tests, of the BARE full suite (`python3 -m pytest`), AND of `python3 -m pytest -m slow`, each with its summary line. State your OWN before-baseline for both commands and show that the after-minus-before failure set is empty; do NOT compare against the plan's authored `5462 passed` figure (F-11). Name the test implementing guard (c) and paste proof it FAILS in BOTH ways: when a row OMITS a deliberate posture, and when a row declares a NON-`bool` truthy value such as `"yes"` (add each bad row in a `mock.patch.dict`, show the failure, revert). A guard that only catches the omission is half a guard, since `NamedTuple` does not type-check at runtime. Paste the `SHIPPED_VALIDATE_DEFAULT == RUNNER_REGISTRY["oc"].validate_default` assertion passing. Confirm the new tests point `XDG_CONFIG_HOME` at a temp dir and state that no test read or wrote the maintainer's real store. Confirm no resolver-level tier test from `tests/test_runner_profiles.py:843-935` was duplicated.
  - Observed evidence: VERIFIED. The new tests pass; my OWN measured before-baseline was 33 bare / 6 slow failures and the after-minus-before failure set is EMPTY on both commands (bare passing rose 5616->5623); guard (c) fails BOTH ways and passes on shipped data; the constant-mirrors-the-row assertion passes; no test touched the real store; no existing tier test was duplicated. Full evidence:
    THE NEW TESTS, ACTUAL OUTPUT. The four E-06 properties live in `PerHostValidateDefaultTests` and the two E-08/E-03 row-contract cases in `RegisteredRowFieldSupportTests`, six tests in total:

    ```text
    $ python3 -m pytest -o addopts="" -q tests/test_runner_profiles.py -k "PerHostValidateDefaultTests or RegisteredRowFieldSupportTests" -v
    collected 81 items / 75 deselected / 6 selected
    tests/test_runner_profiles.py ......                                     [100%]
    ======================= 6 passed, 75 deselected in 0.21s =======================
    ```

    (a) `test_tier_4_is_per_host`, (b) `test_a_row_never_beats_an_operator`, (c) `test_every_registered_row_declares_a_real_bool_posture`, (d) `test_the_tristate_does_not_collapse_on_the_new_host`. Their live values are in the V-02/V-03 probe pastes and in `logs/probe-resolver.txt` (`agy` + `defaults.validate:false` -> `False`/`defaults`; `agy` profile absent -> `True`/`shipped-default`, present-false -> `False`/`profile`).

    MY OWN BEFORE-BASELINE, measured at HEAD `4647890f` immediately before any edit (NOT the plan's stale `5462 passed`, per F-11):

    ```text
    BEFORE, bare:  33 failed, 5616 passed, 3 skipped, 2 xfailed in 109.75s (0:01:49)
    BEFORE, slow:   6 failed, 458 passed in 246.10s (0:04:06)
    ```

    AFTER, same two commands:

    ```text
    $ python3 -m pytest
    33 failed, 5623 passed, 3 skipped, 2 xfailed in 92.96s (0:01:32)

    $ python3 -m pytest -m slow
    6 failed, 458 passed in 292.88s (0:04:52)
    ```

    THE AFTER-MINUS-BEFORE FAILURE SET IS EMPTY on both commands, compared by full test id rather than by count:

    ```text
    $ comm -13 baseline-bare-failures.txt after-bare-failures.txt   # NEW failures
    (empty)
    $ comm -23 baseline-bare-failures.txt after-bare-failures.txt   # disappeared
    (empty)
    $ comm -13 baseline-slow-failures.txt after-slow-failures.txt   # NEW failures
    (empty)
    $ comm -23 baseline-slow-failures.txt after-slow-failures.txt   # disappeared
    (empty)
    ```

    The bare failure count is IDENTICAL (33) and the passing count rose by exactly 7 (5616 -> 5623), which is the six new tests plus the one new dispatch test in V-04. No pre-existing failure disappeared, so nothing is being masked. All four baseline/after failure lists are preserved in `logs/`.

    THE 33 PRE-EXISTING BARE FAILURES ARE NOT MINE, and the plan named some of them in advance: 15 in `tests/test_run_viewer.py` are the known lane `.aw/state` artifact (`dh0uno`), `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` is F-11's recorded failure asserting against a sibling plan's live status, and the remainder are lifecycle/worktree/role tests that fail in an isolated lane (`test_ipd_lifecycle_cli`, `test_worker_role_refusal`, the `oc`/`agy` self-finalize and worktree-isolation suites). None touches this plan's Scope-Paths, and I did not attempt to fix any of them. The 6 slow failures are F-11's environment/order-dependent set (`test_installer`/`test_cli` cleanup and the CLI-surface declaration guards).

    GUARD (c) IS `PerHostValidateDefaultTests::test_every_registered_row_declares_a_real_bool_posture`, AND IT FAILS BOTH WAYS (`logs/probe-guard.txt`; each bad row injected with `mock.patch.dict`, the guard run, then reverted):

    ```text
    === half 1: a row OMITTING the posture cannot even be constructed ===
    TypeError: RunnerSpec.__new__() missing 1 required positional argument: 'validate_default'

    === half 2: a row declaring a NON-bool truthy value ('yes') FAILS the guard ===
    every row declares a bool posture: {"agy": true, "badhost": "yes", "oc": false}
    --- validate_default='yes': failures=1 errors=0
    AssertionError: 'yes' is not an instance of <class 'bool'> : row 'badhost' must declare a real bool verification posture

    === half 2b: an INT 1 also fails (assertIn would have passed it) ===
    every row declares a bool posture: {"agy": true, "badhost": 1, "oc": false}
    --- validate_default=1: failures=1 errors=0
    AssertionError: 1 is not an instance of <class 'bool'> : row 'badhost' must declare a real bool verification posture

    === control: shipped registry PASSES the guard ===
    shipped registry: failures=0 errors=0
    ```

    ON THE OMISSION HALF, stated precisely because it differs from what the plan anticipated: a row that omits the posture cannot be CONSTRUCTED at all, since E-01 made the field required with no default, so the omission is caught one step earlier than the guard by a `TypeError` at construction. The guard therefore covers the case the type system cannot: a row that DOES declare a value which is not a `bool`. Both directions are proven above, and the int case shows why the assertion is `isinstance(..., bool)` and not a membership check (the probe also confirms `1 in (True, False)` is `True` in Python, so `assertIn` would have admitted it). The comment at the assertion records that reasoning and states `isinstance` was chosen over `type(...) is bool`.

    THE NAMEDTUPLE DOES NOT TYPE-CHECK, measured directly, which is what makes the guard load-bearing rather than redundant:

    ```text
    RunnerSpec(validate_default='yes').validate_default = 'yes' truthy: True isinstance bool: False
    ```

    THE DRIFT ASSERTION PASSES, keeping the retained literal honest (same test, run above and in V-02):

    ```python
            self.assertIs(
                RP.SHIPPED_VALIDATE_DEFAULT, RP.RUNNER_REGISTRY["oc"].validate_default
            )
    ```

    ```text
      SHIPPED_VALIDATE_DEFAULT = False == oc row: True
    ```

    NO TEST TOUCHED THE MAINTAINER'S REAL STORE. The six new tests build every config IN MEMORY (`RP.empty_config()`, `RP.add_profile`, `RP.set_validate_default`, `RP.from_document`) and never call `RP.load()` or `RP.store_path()`, so there is no filesystem path to point anywhere; the class docstring states this. The two LIVE probes, which do reach the store path, each set `XDG_CONFIG_HOME` to a fresh `tempfile.mkdtemp()` BEFORE importing `runner_profiles`, and the resolver probe asserts the isolated store is absent both before and after (`store exists: False` ... `store still absent (no write to any real store): True`). The dispatch probe wrote its store only inside its own temp dir (path shown in V-04).

    NO RESOLVER-LEVEL TIER TEST WAS DUPLICATED. `ValidatePrecedenceMatrixTests` (the block the plan cites) was read first and left entirely unmodified: it covers levels 1-3 and fall-through ON `oc`, and the new class covers only what a SECOND row makes newly expressible (a per-host tier 4, the row-as-floor property on both hosts, the per-row deliberateness guard, and the tri-state on the new host). The new class's docstring says so explicitly. `git diff -- tests/test_runner_profiles.py` shows no change inside `ValidatePrecedenceMatrixTests`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the BEFORE and AFTER text of all four corrected prose sites. Paste `git diff -- agent_workflows/run_dispatch.py agent_workflows/runner_profile_wizard.py` IN FULL and confirm in one sentence that every changed line is a comment or docstring, with no executable line touched. Paste the line showing `RUNNER = "oc"` unchanged in the wizard. State in one sentence what the corrected `run_dispatch.py:101` now says about the two registries no longer matching, since that is the sentence a future reader needs in order to understand why `adapter_for` refuses a name the schema accepted.
  - Observed evidence: VERIFIED. All four enumerated prose sites corrected (plus a fifth, recorded as DECISION D2); the diff of the two non-resolver modules is COMMENT-ONLY with no executable line touched; `RUNNER = "oc"` unchanged. Full evidence:
    SITE (1), `RunnerSpec`'s own docstring. BEFORE: "THE REGISTRY SEAM. Version 1 registers OpenCode only. Adding a host is ONE ROW here plus that host's own adapter work; it is deliberately data rather than a `register_runner()` mutator, so nothing at runtime can widen the accepted runner set." AFTER, restating the population and KEEPING the load-bearing sentence this plan is the proof of:

    ```text
        THE REGISTRY SEAM. Version 1 of the schema registers TWO rows, OpenCode (`oc`) and
        Antigravity (`agy`), which deliberately differ in every field below because the two hosts
        genuinely differ. Adding a host is ONE ROW here plus that host's own adapter work; it is
        deliberately data rather than a `register_runner()` mutator, so nothing at runtime can widen
        the accepted runner set.
    ```

    (The same docstring then documents the new field itself, quoted in V-01.)

    SITE (2), the `RUNNER_REGISTRY` comment. BEFORE: "Canonical runner name -> spec. Version 1: OpenCode (`oc`), whose CLI accepts `--model`, `--variant` and `--agent` (`oc_runipd.py` `run_opencode` appends exactly those three)." AFTER, naming both rows with each one's MEASURED field support, since the two now differ and that difference is enforced:

    ```python
    #: Canonical runner name -> spec. Version 1 registers TWO rows, whose fields are MEASURED from
    #: each driver rather than assumed:
    #:
    #: * ``oc`` (OpenCode): accepts `--model`, `--variant` and `--agent` (`oc_runipd.run_opencode`
    #:   appends exactly those three), and verification defaults OFF (`--validate` is a
    #:   `BooleanOptionalAction` with `default=False`, and the verifier turn is gated on it).
    #: * ``agy`` (Antigravity): accepts `--model` ONLY (`agy_runipd`'s child argv appends only
    #:   `--model` and its parser declares only `--model`), so `supports_variant`/`supports_agent`
    #:   are False and `parse_profile` refuses a stored profile carrying either; and verification
    #:   defaults ON (that driver gates its verifier on `not no_verify`, and `--no-verify` is a
    #:   `store_true`, so a bare run verifies).
    #:
    #: The two rows' OPPOSITE `validate_default` values are the reason this is a per-host field and
    #: not a module global: one constant cannot describe both hosts.
    ```

    SITES (3) AND (4) ARE THE FULL DIFF OF THE TWO NON-RESOLVER MODULES, pasted IN FULL as required:

    ```diff
    diff --git a/agent_workflows/run_dispatch.py b/agent_workflows/run_dispatch.py
    index c70e0fe8..f37b5f82 100644
    --- a/agent_workflows/run_dispatch.py
    +++ b/agent_workflows/run_dispatch.py
    @@ -98,11 +98,17 @@ def _dispatch_opencode(argv: Sequence[str]) -> int:
     #: Canonical runner name -> adapter. THE HOST SEAM, and deliberately DATA rather than a
     #: `register()` mutator so nothing at runtime can widen the set of hosts a run may reach.
     #:
    -#: Version 1 registers OpenCode only, matching `runner_profiles.RUNNER_REGISTRY`. A runner that
    -#: is a valid SCHEMA value but has no row here is "registered but not implemented", which is a
    -#: distinct and separately-reported failure from "not a runner at all": the first is a roadmap
    -#: gap, the second is a typo, and telling the operator which one they hit is the difference
    -#: between a five-second fix and a bug report.
    +#: This table registers OpenCode only, and it DELIBERATELY NO LONGER MATCHES
    +#: `runner_profiles.RUNNER_REGISTRY`, which registers both `oc` and `agy` (`hostdefault-01`).
    +#: THAT DISAGREEMENT IS WHAT MAKES THE SECOND REFUSAL BELOW REACHABLE, so a reader who assumes
    +#: the two tables are kept in sync will not understand why `adapter_for` refuses a runner name the
    +#: schema happily accepted. A runner that is a valid SCHEMA value but has no row here is
    +#: "registered but not implemented", which is a distinct and separately-reported failure from
    +#: "not a runner at all": the first is a roadmap gap, the second is a typo, and telling the
    +#: operator which one they hit is the difference between a five-second fix and a bug report.
    +#: `agy` is exactly that roadmap gap today: a store may name it (so the schema can record that
    +#: host's verification posture), and every dispatch route refuses it fail-closed rather than
    +#: launching the wrong driver.
     RUNNER_ADAPTERS: Dict[str, Callable[[Sequence[str]], int]] = {
         "oc": _dispatch_opencode,
     }
    diff --git a/agent_workflows/runner_profile_wizard.py b/agent_workflows/runner_profile_wizard.py
    index 011402ec..9acc6674 100644
    --- a/agent_workflows/runner_profile_wizard.py
    +++ b/agent_workflows/runner_profile_wizard.py
    @@ -68,8 +68,11 @@ MAX_ATTEMPTS = 5
     #: accept none of these, and a provider may accept something not listed (hence the custom option).
     COMMON_VARIANTS: Tuple[str, ...] = ("low", "medium", "high", "max")

    -#: The runner this wizard configures. Version 1 of the schema registers OpenCode only
    -#: (`runner_profiles.RUNNER_REGISTRY`); a second host needs its own adapter, not a widened wizard.
    +#: The runner this wizard configures. The schema's registry (`runner_profiles.RUNNER_REGISTRY`)
    +#: now holds a second row (`agy`), but this wizard still writes OpenCode profiles ONLY, and that
    +#: is deliberate rather than an oversight: a second host needs its own adapter, not a widened
    +#: wizard. `agy` has no dispatch adapter (`run_dispatch.RUNNER_ADAPTERS`), so offering it here
    +#: would let a user create by wizard a profile nothing in this build can launch.
     RUNNER = "oc"

     _CANCEL_WORDS = frozenset(("q", "quit", "cancel", "abort"))
    ```

    EVERY CHANGED LINE IN BOTH MODULES IS A `#:` COMMENT LINE; no executable line was touched, and the diff contains no added or removed statement, expression, import or definition in either file. The wizard's premise was corrected while its CONCLUSION was kept, and `RUNNER = "oc"` is unchanged:

    ```text
    $ grep -n '^RUNNER = ' agent_workflows/runner_profile_wizard.py
    76:RUNNER = "oc"
    ```

    WHAT THE CORRECTED `run_dispatch.py` COMMENT NOW SAYS about the mismatch, in one sentence: that this adapter table registers OpenCode only and DELIBERATELY no longer matches `runner_profiles.RUNNER_REGISTRY` (which holds both `oc` and `agy`), and that this disagreement is precisely what makes the registered-but-unimplemented refusal reachable, so a reader who assumes the two tables are kept in sync cannot understand why `adapter_for` refuses a name the schema accepted.

    A FIFTH STALE SITE WAS ALSO CORRECTED, beyond E-07's literal enumeration, and the decision is recorded as DECISION 05-tm2cz8-D2. `canonical_runner`'s docstring asserted "a profile naming a host nobody can launch is a failure the user should see at write time, not at 3am", an absolute this very change falsifies (the row makes `runner: agy` and `default_runner: agy` storable but unlaunchable, exactly as F-13 records). The docstring now states the partial inversion and why it is bounded, in the same comment-only style, inside a declared Scope-Path file. Leaving it would have reproduced the defect E-07 exists to remove.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: state WHICH option you chose (refuse in `resolve()`, or accept and document) and quote the comment you wrote at the decision site giving the reason. Paste the probe showing the CHOSEN behavior for `resolve(cfg, runner="agy", variant="high", agent="build")`: either the typed `ProfileSchemaError` and its message, or the accepted values with a statement of why that is safe today. Paste the new test pinning it. Confirm you checked whether any shipped test asserted the previous permissive behavior, and name the result of that search.
  - Observed evidence: VERIFIED. Chose option (a), REFUSE in `resolve()` with a typed `ProfileSchemaError` mirroring `parse_profile`; the reason is commented at the decision site; a probe shows the exact message per field and that `oc` is unaffected; a new test pins it; NO shipped test asserted the previous permissive behavior. Full evidence:
    OPTION CHOSEN: (a) REFUSE in `resolve()` with a typed `ProfileSchemaError` mirroring `parse_profile`'s wording. Recorded in full, with alternatives and reversibility, as DECISION 05-tm2cz8-D1 in the run's decisions register.

    THE COMMENT AT THE DECISION SITE, quoted verbatim:

    ```python
        # ---- an EXPLICIT field the resolved host does not support --------------------------------
        # REFUSE, matching `parse_profile` (`hostdefault-01` E-08). `parse_profile` has always
        # enforced `supports_variant`/`supports_agent` for a STORED profile, but this function
        # consulted neither flag, so an explicit caller argument was carried through with provenance
        # `explicit` even for a host whose argv builder cannot emit it. That path was UNREACHABLE
        # while `oc` was the only row (any other `runner=` raised in `canonical_runner`); registering
        # `agy`, which supports neither field, makes it reachable, so it becomes a decision.
        #
        # WHY REFUSE rather than accept-and-document: the store and the caller must enforce the SAME
        # row contract, or `--variant high` is refused when written to a profile and silently dropped
        # when typed on the command line, which is a difference the operator cannot see. Silently
        # dropping a field the operator explicitly asked for is the same class of lie this module's
        # "an explicit flag always wins" rule exists to prevent: better a typed refusal naming the
        # host than a run that ignores half the command line. The message deliberately mirrors
        # `parse_profile`'s wording so the two refusals read as one rule.
    ```

    THE PROBE, showing the typed refusal and its exact message for each field, plus the unchanged behavior for a host that DOES support them (`logs/probe-resolver.txt`):

    ```text
    == V-08: explicit unsupported variant/agent ==
      REFUSED {'variant': 'high'}: ProfileSchemaError: runner 'agy' does not support a model variant, so an explicit variant cannot be honored; omit it
      REFUSED {'agent': 'build'}: ProfileSchemaError: runner 'agy' does not support an agent, so an explicit agent cannot be honored; omit it
      oc honored: high build explicit explicit
    ```

    The refusal is the typed `ProfileSchemaError` the plan required (not a bare `ValueError`), and `oc` still resolves `variant='high'`, `agent='build'` with provenance `explicit`, so nothing about the shipped host's behavior moved.

    THE NEW TEST PINNING IT, `RegisteredRowFieldSupportTests::test_an_explicit_unsupported_field_is_refused_at_resolution`:

    ```python
            with self.assertRaises(RP.ProfileSchemaError) as ctx:
                RP.resolve(RP.empty_config(), runner="agy", variant="high")
            self.assertIn("agy", str(ctx.exception))
            self.assertIn("does not support a model variant", str(ctx.exception))
            with self.assertRaises(RP.ProfileSchemaError) as ctx:
                RP.resolve(RP.empty_config(), runner="agy", agent="build")
            self.assertIn("agy", str(ctx.exception))
            self.assertIn("does not support an agent", str(ctx.exception))
            # Unchanged for a host that DOES support them.
            got = RP.resolve(
                RP.empty_config(), runner="oc", variant="high", agent="build"
            )
            self.assertEqual((got.variant, got.agent), ("high", "build"))
            self.assertEqual(got.provenance["variant"], RP.PROVENANCE_EXPLICIT)
    ```

    Its sibling `test_a_stored_profile_is_refused_per_row` pins the same row contract on the `parse_profile` side (including that the SAME fields are still accepted for `oc`, so the refusal is about the ROW and not about the fields).

    THE SEARCH FOR A SHIPPED TEST ASSERTING THE PERMISSIVE BEHAVIOR WAS RUN, AND THE RESULT IS NONE. `grep -rn "supports_variant\|supports_agent" --include=*.py .` returns only the two `RunnerSpec(...)` constructor calls in `tests/test_run_dispatch.py` (which simulate a registered-but-unimplemented host and assert nothing about explicit fields) plus the resolver/registry definition lines themselves. `grep -rn "resolve(.*variant=" tests/*.py` returns exactly two call sites, `tests/test_runner_profiles.py:727` and `tests/test_runner_profiles_e2e.py:791`, and BOTH pass `runner="oc"`, a host that supports both fields, so neither is affected. The only product caller passing these fields is `oc_runipd.resolve_launch_profile`, which hard-codes `runner="oc"`. The empty after-minus-before failure set on both full suites (V-06) independently confirms nothing depended on the permissive path.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the six paths in `Scope-Paths`. Do NOT modify `oc_runipd.py` or `agy_runipd.py` in this plan; no driver is wired here, and an edit to either is a scope violation rather than a bonus (child 02 owns the wiring, and those two modules are the highest-contention files in the repository). Do NOT add a `run_dispatch` adapter, and do NOT change any EXECUTABLE line in `run_dispatch.py` or `runner_profile_wizard.py`: those two are in scope for E-07's comment corrections ONLY. Do NOT change either host's effective default. Do NOT register a third host. Do NOT widen the wizard to a second host. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. NOTE: this repository is a SHARED CHECKOUT and a driver run may be live; `aw runs` before you start.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest` AND from `python3 -m pytest -m slow`. BOTH ARE REQUIRED HERE, and the second is not a flag added to "help": a Scope-Paths test file is marker-excluded from the bare run, so a bare-only paste can show green while that file is red (F-10). A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: this plan's authored baseline (`5462 passed`) is STALE and HEAD is NOT clean (F-11). Measure your own before-baseline for both commands, paste it, and judge yourself on the DELTA. Do not report the pre-existing `test_orchestrator_retirement` failure as caused by this change, and do not attempt to fix it here; it asserts against a sibling plan's live status and is out of scope.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `RunnerSpec`, `RUNNER_REGISTRY`, `resolve`'s validate chain, `SHIPPED_VALIDATE_DEFAULT`, and `adapter_for` by name.

THE ITEM THAT MATTERS MOST IS V-05. The six failing tests are DELIBERATE assertions that version 1 admits exactly one host, and the cheap way to make them pass is to delete or weaken them. That would silently discard the "the registry is CLOSED" property, which is the guarantee that stops a runtime from widening the accepted host set. Every one of the six must end up pinning the same property over the two-host population. If any of the six cannot be updated that way, report it in the plan and continue with the rest rather than abandoning the run; the fence and `aw ipd finalize` will surface an unfinished item, and a half-updated test suite left uncommitted is worse than a recorded gap.

This plan's `- From-Backlog: h7qsje` and `- Blocks-Release: next` are INHERITED from superseded plan `mn3gwr`, so the release gate that plan carried is preserved rather than dropped. Do NOT close backlog `h7qsje` here: the operator-visible capability it describes is not delivered until child 02 (`ybkmzp`) wires the resolved value into the drivers, and closing it after this plan would claim a capability that no driver yet reads.
