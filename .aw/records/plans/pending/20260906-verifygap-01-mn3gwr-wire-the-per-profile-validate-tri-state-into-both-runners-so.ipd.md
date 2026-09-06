# IPD: Wire the per-profile validate tri-state into both runners so the per-model verification default is honored

- Date: 2026-09-06
- Kind: child
- Concern: Executed plan `f2mrsw` shipped a per-profile `validate` tri-state and a documented four-tier precedence chain for it, but neither runner passes `validate=` into `runner_profiles.resolve()` and neither reads `ResolvedLaunch.validate`. The two middle tiers (a named profile's own value, and `defaults.validate`) are therefore dead: the operator's stored per-model choice is silently ignored and verification remains a flag that must be retyped every invocation.
- Scope: Pass the explicit flag into the resolver and consume the resolved value as the run's frozen `validate` option, on BOTH hosts, preserving each host's CURRENT effective default when no flag and no profile speak. Record the resolved value and its provenance in run state. No change to the resolver, the schema, the precedence rules, or either host's default behavior.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_profiles.py
- Item-Dependencies: none
- Status: to-review
- Set: verifygap
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: mn3gwr
- From-Backlog: h7qsje
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `h7qsje`, inheriting its `Blocks-Release: next` gate. The premise is measured, not inferred: `runner_profiles.resolve()` implements the full tri-state chain correctly (`runner_profiles.py:1004-1017`) and `ResolvedLaunch.validate` carries the result (`:360`), but `resolve_launch_profile` calls `resolve()` WITHOUT `validate=` (`oc_runipd.py:2643-2650`), `launch_profile_record` omits the field (`:2673-2683`), and the verifier gate reads `state["options"]["validate"]` sourced from the CLI flag alone (`:6211-6215`). Verified live: `resolve(cfg, runner="oc").validate` returns `False` with provenance `shipped-default`. Corrects a false premise from the investigation that produced `h7qsje`: the verifier turn has NOT never run. It ran on every IPD across 13 runs through 2026-08-29, and the maintainer switched the default deliberately after measuring roughly 33% extra cost for only nits on the primary model (recorded as F-6 in executed plan `evgi9n`). That ruling is explicitly conditional - "on a weaker model it is not, which is why the per-model default is wanted" - which is the capability this plan restores.

## Goal

Make the operator's stored per-model verification choice actually take effect, so "check this model's work, do not check that one" is configuration rather than a flag a human must remember on every run. The design is already approved and shipped; only the wire is missing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the resolver see the flag

- [ ] E-01 In `oc_runipd.resolve_launch_profile` (`oc_runipd.py:2619`), pass the explicit verification flag into `runner_profiles.resolve()` as `validate=`. The value MUST be the tri-state the resolver expects: `True`/`False` when the operator spelled `--validate`/`--no-validate`, and `None` when neither appeared, so an unspecified flag FALLS THROUGH to the profile tier instead of being read as a decision. `--validate` is a `BooleanOptionalAction` (`oc_runipd.py:7467`), whose default must therefore be `None` rather than `False` for this to work; if changing that default alters any other reader of `args.validate`, adjust the reader rather than reintroducing a two-valued flag.
  - Depends on: none
  - Expected outcome: `resolve()` receives `None` on a bare invocation and a boolean when the flag is spelled; provenance reports `explicit` only in the latter case.
  - Execution state: pending

- [ ] E-02 Do the same for the antigravity host. It has no `--validate`: it carries `--no-verify`/`--no-audit` as a `store_true` (`agy_runipd.py:4447-4453`), so the tri-state must be derived, NOT read directly. `store_true` cannot distinguish "not passed" from "passed false", so derive `False` when the flag is present and `None` when it is absent, and do not invent a `--verify` spelling in this plan (the flag surface is `ki6tom`'s concern and is currently parked on a spec question).
  - Depends on: none
  - Expected outcome: `aw agy run start --no-verify` resolves `validate=False` with provenance `explicit`; a bare `aw agy run start` passes `None` and falls through.
  - Execution state: pending

### Task group 2: preserve each host's current default

- [ ] E-03 THE SAFETY-CRITICAL ITEM. `runner_profiles.SHIPPED_VALIDATE_DEFAULT` is `False` (`runner_profiles.py:112`), matching opencode. Antigravity's effective default is the OPPOSITE: verification is ON there, gated on `not no_verify`, and the divergence is deliberate and documented at `agy_runipd.py:3476-3482`. So consuming the resolver's shipped fallback unchanged on agy would FLIP that host from verify-by-default to skip-by-default. Prevent it: when no flag and no configured tier speak on agy, the effective value must remain `True`. Implement this as an explicit per-host fallback at the call site, and do NOT change `SHIPPED_VALIDATE_DEFAULT` (opencode depends on it, and a shared constant cannot carry two host defaults).
  - Depends on: E-01, E-02
  - Expected outcome: with no runner-profiles store present and no flag, `aw oc` still resolves `validate=False` and `aw agy` still resolves `validate=True`, exactly as today.
  - Execution state: pending

- [ ] E-04 Consume the resolved value as the run's frozen `validate` option in both `initialize_run` functions, replacing the direct read of `args.validate` / `args.no_verify` for that purpose. Keep the existing `options` keys and their meanings (`validate`, and agy's `no_verify`) so every downstream reader is untouched, including the verifier gate at `oc_runipd.py:6211-6215` and `agy_runipd.py:3482`. Freeze at queue build, so a resume cannot silently change what verification meant mid-run (the same rule the other policy flags already follow).
  - Depends on: E-03
  - Expected outcome: the verifier gate fires based on the RESOLVED value; no downstream reader changes.
  - Execution state: pending

### Task group 3: make the decision auditable

- [ ] E-05 Add `validate` and its provenance to `launch_profile_record` (`oc_runipd.py:2657`) and the agy equivalent, so `state.json` records WHICH tier decided verification for this run (`explicit`, `profile`, `default-profile`, `defaults`, `shipped-default`). The record already carries model/variant/agent provenance for exactly this reason; verification is the field whose silent default caused `vju5ba` and must not be the one field that cannot be audited afterward. Add no credentials and no new file.
  - Depends on: E-04
  - Expected outcome: `state.json` `options.launch_profile` shows the resolved `validate` and the tier that supplied it.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 Test the precedence chain end to end on BOTH hosts: explicit flag beats a profile value; a profile value beats `defaults.validate`; `defaults.validate` beats the shipped fallback; and absence at every tier yields each host's CURRENT default (oc `False`, agy `True`). Assert the tri-state does not collapse: a profile saying `validate: false` must be distinguishable from a profile that omits the field, since only the former is a decision. Include a regression test for E-03 asserting agy's default is unchanged, because that is the one silent-safety-change risk in this plan.
  - Depends on: E-05
  - Expected outcome: the four-tier chain is pinned per host, and agy's default is protected by an explicit test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The resolver is the single authority and is already correct. `runner_profiles.resolve()` implements the chain at `runner_profiles.py:1004-1017` with per-field provenance. Do NOT reimplement precedence at the call site; pass the flag in and read the result out.
- `validate` is a genuine TRI-STATE by explicit design: `_validate_tristate` (`runner_profiles.py:467`) and the module docstring (`:39-44`) require that ABSENT never collapse to `false` at parse time. `f2mrsw`'s review recorded the reason: an explicit flag must always beat a stored default, because "a profile silently beating a flag would reproduce [`vju5ba`] inverted".
- The two hosts have OPPOSITE verification defaults, deliberately. `agy_runipd.py:3476-3482` states it: agy gates on `not no_verify` (ON), opencode gates on `validate` (OFF).
- Both `initialize_run` functions freeze policy into `state["options"]` at queue build and treat a resume as bound by the frozen values. Follow that, do not add a second mechanism.
- Run under `python3 -m pytest` bare; the configured `addopts` already supply quiet/parallel/fast-subset.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The resolver is called without the flag, so tier 1 never registers as explicit. | `oc_runipd.py:2643-2650` passes `runner`, `profile`, `model`, `variant`, `agent` and no `validate` |
| F-2 | The resolved value is never read. `grep '\.validate' oc_runipd.py` finds only `validate_manifest`, a `validate_retry_budget` comment, and the resume path's `args.validate`. | measured 2026-09-06 |
| F-3 | Live proof the chain is inert: `resolve(cfg, runner="oc").validate` returns `False` with provenance `shipped-default`, regardless of any stored profile. | measured 2026-09-06 |
| F-4 | `launch_profile_record` omits `validate`, so even the value that IS resolved is not recorded. | `oc_runipd.py:2673-2683` |
| F-5 | **The flip risk.** `SHIPPED_VALIDATE_DEFAULT = False` matches opencode but is the opposite of agy's effective default, so naive consumption would silently disable verification on agy. | `runner_profiles.py:112` versus `agy_runipd.py:3476-3482` |
| F-6 | `--validate` is a `BooleanOptionalAction`; agy has no `--validate` at all, only `--no-verify`/`--no-audit` as `store_true`. The two hosts need different derivations to reach the same tri-state. | `oc_runipd.py:7467`, `agy_runipd.py:4447-4453` |
| F-7 | The capability was exercised historically and switched off on measured grounds, so this is a restoration rather than a new feature: 13 runs carry verification outcomes, the last on 2026-08-29. | `ls .aw/records/runs/*/outcomes | grep verification`; `evgi9n` F-6 |

## Proposed changes (ordered, validatable)

1. Pass the flag in as a tri-state on both hosts (E-01, E-02).
2. Pin each host's current default explicitly so neither flips (E-03).
3. Consume the resolved value as the frozen option, leaving downstream readers untouched (E-04).
4. Record the value and its provenance (E-05).
5. Pin the whole chain per host with tests, including an explicit guard on agy's default (E-06).

## Deferred / out of scope (with reason)

- Changing either host's DEFAULT verification behavior. This plan makes the stored choice effective; it does not decide what the choice should be. Any default change is a separate, measured decision.
- The flag SURFACE (whether agy should gain `--validate`/`--no-validate`, and whether the argparse-generated negations are acceptable). That is `ki6tom`'s concern, currently parked on a spec reading. This plan works with the flags as they ship.
- Per-role model routing (a distinct model for the verifier turn). That is `kgpptv` (`runprofile-06`, pending). Complementary: this plan decides WHETHER the verifier runs, `kgpptv` decides WHICH model runs it.
- A standalone re-verify command for an already-executed plan. Backlog `7u9kbm`, deliberately sequenced after this.

## Scope check

- Over-scope: none. Two runner modules plus their tests, all in Scope-Paths.
- Under-scope: does not add a ledger, does not change defaults, does not touch the resolver or the schema. Those are correct exclusions: the resolver already works and the defaults are a separate decision.

## Required tests / validation

- `python3 -m pytest` bare, full suite, before and after, with counts stated.
- Targeted: `tests/test_runner_profiles.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
- A live before/after demonstration that a stored profile value actually changes the resolved verification decision, which is the whole point of the plan and cannot be shown by unit tests alone.

## Spec / documentation sync

Spec `25kzda`'s amended Section 1.3 already records that skipping the independent verifier turn is a RETAINED, host-configurable choice rather than a prohibited bypass, and names `kgpptv` plus `f2mrsw` E-03 as the mechanism that makes it configuration. This plan implements that mechanism, so no spec change is required. If the executor finds the spec still implies verification is flag-only, note it rather than editing the spec inside this plan.

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
  - Required evidence: paste the resolved `validate` and its provenance for three opencode invocations: no flag (expect provenance NOT `explicit`), `--validate` (expect `True`/`explicit`), `--no-validate` (expect `False`/`explicit`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same three cases for agy, deriving from `--no-verify`: absent (not `explicit`), present (`False`/`explicit`). State explicitly how "absent" is distinguished from "false" given `store_true`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: with NO runner-profiles store present and no flags, paste the effective verification decision for BOTH hosts, showing oc `False` and agy `True`. This is the anti-regression check; a run showing agy `False` here is a failed execution, not a passing one.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `options` block from a `state.json` produced by a real invocation on each host, showing the frozen value, plus the verifier-gate outcome for that run (whether a verification outcome file was written).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `options.launch_profile` from a real `state.json` showing `validate` and its provenance tier, for at least two different tiers (e.g. `explicit` and one configured tier).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of the three targeted test modules and of the bare full suite, with the `N passed` summary line, and state the before/after suite counts. Name the test that pins agy's unchanged default.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). The executor must commit ONLY the five paths in Scope-Paths, path-scoped, and must never push. Tests must be RUN and their actual output pasted into `Observed evidence`; a `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

TWO STANDING WARNINGS FOR THE EXECUTOR. FIRST, this plan edits `oc_runipd.py` and `agy_runipd.py`, the two highest-contention modules in the repository; several other pending plans declare them, so expect to rebase or resolve and re-run the full suite after any merge. SECOND, V-03 is the one that matters most: this change can silently disable verification on the antigravity host, which would be a safety regression disguised as a wiring fix. If V-03 cannot be shown green, stop and report rather than proceeding.

On completion, close backlog `h7qsje`, which this plan carries as `- From-Backlog:`.
