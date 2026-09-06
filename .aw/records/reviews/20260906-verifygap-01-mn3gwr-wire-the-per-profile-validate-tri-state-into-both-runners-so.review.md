# Review: wire the per-profile validate tri-state into both runners (child mn3gwr, Set verifygap)

- Subject-Id: mn3gwr
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `e0384cfb`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review and `--phase review-finalize` conformed after the revisions.

DISCLOSURE: I authored this plan earlier in the same session, so this is a SELF-REVIEW and worth less
than an independent one. That matters more than usual here, because the two most serious findings are
both cases where my own authoring reasoned from a sibling plan's prose instead of measuring the code:
`kgpptv`'s review record states plainly (its F-12) that the antigravity host has zero profile
integration, and I had read that record, yet I still authored an E-item instructing an executor to wire
agy's resolver call. The lesson is the one the repository keeps re-learning: a claim inherited from an
artifact, even a recently verified one, is not a measurement.

THE PLAN'S CORE PREMISE IS TRUE AND I RE-VERIFIED IT INDEPENDENTLY. The resolver implements the whole
four-tier chain correctly with per-field provenance, `ResolvedLaunch.validate` carries the result, and
the opencode runner passes no `validate=` and reads no resolved value, so the two middle tiers really
are dead. Live: `resolve(cfg, runner="oc").validate` is `False` with provenance `shipped-default`, and
with `defaults.validate: true` configured it becomes `True`/`defaults` while the runner still freezes
the raw flag. The wiring gap is real and worth fixing.

WHAT ROUND 1 CHANGED IS THE PLAN'S SHAPE, on two independent counts, each of which would have produced
a failed or dangerous execution.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | BLOCKER | IN-SCOPE | G. executability; A. correctness | `runner_profiles.py:207-212`; live `resolve(cfg, runner="agy")`; `rg 'runner_profiles\|resolve_launch_profile\|launch_profile' agent_workflows/agy_runipd.py` exit 1 | E-02 instructed the executor to pass the tri-state into `runner_profiles.resolve()` on the antigravity host. THAT CALL CANNOT BE WRITTEN. `RUNNER_REGISTRY` version 1 registers only `oc`, so `resolve(cfg, runner="agy")` raises `ProfileSchemaError: unknown runner 'agy'; version 1 registers: oc`, and a profile document declaring `runner: agy` is refused identically; agy imports nothing from `runner_profiles` at all. Reaching agy needs a REGISTRY (schema) change plus the entire resolve/record/freeze seam `3cm15q` built for oc, both forbidden by this plan's own Scope ("No change to the resolver, the schema") and absent from Scope-Paths. So E-02/E-03/E-05's agy halves were unimplementable, and an executor would have discovered it only after editing the repo's highest-contention module | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Plan narrowed to opencode with the measurement as its stated reason. E-02 replaced by a prove-and-record item that files the agy follow-up carrying the inherited `Blocks-Release: next` gate; `agy_runipd.py` REMOVED from Scope-Paths and the fence now forbids editing it; the partial-fix consequence is stated in Deferred rather than implied. Added F-8 |
| PR-402 | BLOCKER | IN-SCOPE | A. correctness; B/D. safety | `runner_profiles.py:112` vs `agy_runipd.py:3474-3482`, `:3392-3399` | E-03/E-04 told the executor to freeze the RESOLVED value into agy's existing `no_verify` key while "keeping the existing keys and their meanings". Those two instructions CONTRADICT each other, because the keys are INVERTED IN POLARITY: oc freezes `validate` and gates on it, agy freezes `no_verify` and gates on `not no_verify`. Verified arithmetically: a resolved `validate=True` written into `no_verify` yields `no_verify=True`, so the verifier does NOT run - verification requested and silently skipped, in both directions. The plan's own centerpiece warning ("this change can silently disable verification on agy") therefore described a hazard its instructions actively created, and E-03's stated remedy (a per-host `True` fallback) addressed the VALUE mismatch while leaving the POLARITY inversion untouched | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-03 reshaped from "give agy a True fallback" into "prove agy did not move": a test-only pin driving the real parser and freeze site, plus an explicit prohibition on introducing a `validate` key into agy's frozen options (two switches for one behavior, disambiguated today only by absence at `oc_runipd.py:6213-6214`). V-03 now fails the execution if agy verification shows OFF. Added the arithmetic to F-5 |
| PR-403 | HIGH | IN-SCOPE | E. testing | `tests/test_novalnomerge_integration.py:50`, `:71-75`; live parser mutation | E-01 required `--validate`'s default to become `None` and said only "if changing that default alters any other reader, adjust the reader". It does, and not a reader: it breaks a SHIPPED TEST. `test_shipped_defaults_are_validate_off_and_self_finalize_on` walks the real subparsers and asserts `assertIs(defaults.get("validate"), False, "--validate must still default False for this bug class to exist")`. Measured by mutating the real parser: the probe returns `False` today and `None` under E-01, so `assertIs(None, False)` fails. That test pins the PREMISE of executed plan `evgi9n`'s $528 bug class, so an executor meeting a red test with no guidance might weaken or delete it - converting a wiring fix into the loss of a deliberate regression guard | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now names both mechanisms (change the default, or inspect argv), requires the choice to be recorded, states the measured breakage, and requires the test be UPDATED to pin the property `evgi9n` actually depends on (a bare invocation verifies OFF) rather than the raw parser default. V-01 fails on a paste showing that test failing, skipped, or deleted. `tests/test_novalnomerge_integration.py` added to Scope-Paths. Added F-9 |
| PR-404 | MEDIUM | IN-SCOPE | Evidence accuracy | `oc_runipd.py:2673-2683`; live `launch_profile_record(resolve(cfg, runner="oc"))` | F-4 and E-05 both claimed the durable record omits `validate` "and its provenance". Half wrong: the record copies the resolver's whole provenance mapping, so the TIER is already recorded today (verified live: `{'runner': 'explicit', ..., 'validate': 'defaults'}`) while only the VALUE is missing. An executor following E-05 literally would have added a second, duplicate provenance entry to a durable state object | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 corrected with the live probe; E-05 now adds one key, explicitly forbids duplicating the existing provenance, and adds the backward-compatibility requirement (an older record lacking the key must still render, which a shipped test already pins). Added |
| PR-405 | MEDIUM | UNDER-SCOPE | E. testing | `tests/test_runner_profiles.py:843-935`; `tests/test_run_flag_surface.py:956-970` | E-06 specified exactly the coverage that ALREADY SHIPS. All four tiers, both polarities, absent-is-not-false, the default-profile tier, and the measured strong-off / cheap-on split are pinned at the RESOLVER level, and `tests/test_runner_profiles.py` was already in Scope-Paths, so the plan's only proof item would have re-tested working code while leaving the seam it BUILDS - a stored value reaching a real run's frozen state and deciding the gate - completely uncovered | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-06 redirected to the runner level: drive `initialize_run` with `--prepare-only` (the shipped pattern) against a store isolated via `XDG_CONFIG_HOME`, and assert the FROZEN `options["validate"]` per tier plus `no_audit` consistency. Told explicitly not to duplicate the resolver tests. V-04 now requires a profile-sourced (not flag-sourced) case, since a flag-only paste cannot distinguish the new behavior from the old |
| PR-406 | MEDIUM | UNDER-SCOPE | A. correctness | `oc_runipd.py:2969-2970`, `:6213-6214`; `tests/test_oc_runipd.py:2390`+ | E-04 named `validate` as the key to source from the resolver and never mentioned `no_audit`, which is DERIVED from the same flag at the same site, read by the verifier gate's compatibility branch, and written by five tests. Sourcing one from the resolved value and leaving the other on `args` produces a run whose two frozen keys disagree about whether verification was requested | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires `no_audit` be derived from the RESOLVED value, and forbids moving `resolve_launch_profile` from first position (the pre-durable-write refusal guarantee) or adding a second `load()`. V-04 requires pasted evidence that the two keys agree. Added F-10 |
| PR-407 | LOW | IN-SCOPE | F. UX; honesty | spec `20260826-0718-01-...spec.md:105`; `kgpptv` F-12 | The spec-sync section said "this plan implements that mechanism" without qualification, which after the PR-401 narrowing is a host-parity claim the plan cannot support. Separately, a stale sibling status (`kgpptv` "pending", now `reviewed`) and no statement of whether the two plans have an execution ordering constraint | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec section now qualifies the claim to opencode, forbids user-facing text implying parity, and routes any parity-claiming documentation found to the deferred follow-up rather than to a spec edit here. Sibling status corrected and the absence of an ordering dependency stated in both directions with each plan's fence as the reason |
| PR-408 | LOW | UNDER-SCOPE | G. executability; B. privacy | `runner_profiles.py:655-663`; `config.py:674-682` | No item said how a test reaches a controlled profile store, and the store lives in the maintainer's real `~/.config/agent-workflows/`. An executor writing "with no store present" tests could have read or written the maintainer's actual configuration | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 and the validation section now require an isolated store via `XDG_CONFIG_HOME`, citing the derivation path; V-06 requires stating that no test touched the real store |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` question
was required. Both BLOCKERS were repaired rather than rejected because the plan's thesis is
independently verified and its target seam is correct; only its reach was wrong.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-401: narrow the plan to opencode, or widen it to register `agy` in the runner registry and build that host's profile seam? | Narrowed to opencode, with the agy seam deferred to a new backlog item inheriting the `Blocks-Release: next` gate. | Widening, REJECTED: it means a schema/registry change plus reproducing the whole `3cm15q` seam on the repo's other highest-contention module, which is a different and much larger plan than "wire an existing resolved value", and this plan's own Scope forbids schema changes. Silently dropping the agy half, REJECTED: the release gate would vanish with no successor. | `runner_profiles.py:207-212`; live `ProfileSchemaError` from `resolve(runner="agy")`; plan Scope line forbidding schema change; `AGENTS.md` release-gate handoff rule | yes |
| D-2 | PR-402: give agy a per-host `True` fallback as authored, or forbid touching agy and pin its default instead? | Forbid touching agy; pin the default with a test. | The authored fallback, REJECTED on two grounds: it is unreachable after D-1, and it addressed only the value mismatch while leaving the `no_verify` polarity inversion that actually flips the host. | `agy_runipd.py:3392-3399`, `:3474-3482`; the inversion arithmetic recorded in F-5 | yes |
| D-3 | PR-403: which tri-state mechanism should E-01 mandate, the `None` default or argv inspection? | Neither mandated. E-01 names both, states the measured test breakage, and requires the executor to choose and record. | Mandating the `None` default (preferred, and said so), REJECTED as a mandate because the choice interacts with a shipped regression guard and the executor holds the current tree; mandating argv inspection, REJECTED as the more roundabout of the two. | `tests/test_novalnomerge_integration.py:50`; live parser mutation probe; `oc_runipd.py:7538` (`resume` already ships `default=None`) | yes |
| D-4 | Is PR-403 a BLOCKER or HIGH? | HIGH. | BLOCKER, REJECTED: it produces a RED TEST, which fails loudly at CI rather than silently corrupting behavior, unlike PR-401 (unimplementable instruction) and PR-402 (silent verification loss). Not MEDIUM, because the wrong response (weakening the test) destroys a deliberate guard on a $528 bug class. | `plan-review.md:504-509`; `evgi9n` F-6 | yes |
| D-5 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status: reviewed`, no human sign-off). `no-go`, REJECTED: no open question remains and no BLOCKER or HIGH is left unfixed; both blockers were repaired in place. | `plan-review.md:531-546` | yes |

No `Reversible: no` decision was taken. D-1 materially changes what the plan DELIVERS (opencode-only
configurability rather than both hosts), so although it is reversible by editing the plan, it is
surfaced explicitly to the maintainer in the review report rather than left to be discovered in the
diff.

### Verified claims

- The wiring gap is exactly as described. `resolve_launch_profile` passes `runner`/`profile`/`model`/
  `variant`/`agent` and no `validate` (`oc_runipd.py:2642-2650`); the freeze site reads
  `getattr(args, "validate", False)` (`:2969-2970`); the gate reads `opts.get("validate", False)`
  (`:6212`). Live: `resolve(cfg, runner="oc").validate` is `False`/`shipped-default` with no store, and
  `True`/`defaults` with `defaults.validate: true` configured, which the runner never sees.
- The resolver's chain is correct and fully tested at all four tiers, so the plan is right that no
  resolver change is needed (`runner_profiles.py:1004-1017`; `tests/test_runner_profiles.py:843-935`).
- The historical claim holds, re-measured: 13 distinct run directories carry verification outcomes
  (34 outcome files), the latest `run-20260829T191652Z-4134000`, i.e. 2026-08-29 as stated.
- The maintainer ruling the plan rests on is quoted accurately, including its conditionality:
  `evgi9n` F-6 records "on a weaker model it is not, which is why the per-model default is wanted".
- Spec `25kzda` Section 1.3 says what the plan claims, and independently supports the host-level
  reading: "until per-role model routing exists ... a host-level control is the only available
  mechanism" (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:105`).
- Every line citation in the plan resolved to the claimed construct at review time (spot-checked 11 of
  them), with one wording drift: agy's divergence comment begins at `:3474`, not `:3476`. Corrected.
- OQ-01 and OQ-02 are both correctly resolved and correctly non-blocking. OQ-02's premise was
  re-verified: the resume path does overwrite the frozen `validate` when the flag is passed
  (`oc_runipd.py:7882-7885`), and this plan changes only where a NEW run's value comes from.
