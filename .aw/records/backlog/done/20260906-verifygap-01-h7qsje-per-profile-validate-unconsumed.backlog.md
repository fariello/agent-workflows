- Id: h7qsje
- Status: done
- Blocks-Release: next
- Set: verifygap
- Priority: high
- Work-Kind: bug
- Summary: the per-profile validate tri-state shipped in f2mrsw but no runner reads it, so the measured Opus-off/Gemini-on split is still an per-invocation flag the operator must remember

## Workflow history
- 2026-09-07 done (aw set): Handed off to plan tm2cz8 (approved, carries the same Blocks-Release: next), which moves the verification default into the per-host runner registry, with ybkmzp (to-review) wiring the resolved decision into both drivers. Note mn3gwr, the earlier carrier, is superseded. Closing per maintainer decision 2026-09-07: the release gate is PRESERVED via the From-Backlog handoff. Clears check.orphaned-live-blocker.
- 2026-09-06 created (aw backlog): the per-profile validate tri-state shipped in f2mrsw but no runner reads it, so the measured Opus-off/Gemini-on split is still an per-invocation flag the operator must remember

THE GAP, and it is a WIRING gap rather than a design question. Executed plan `f2mrsw`
(`runprofile-01`) shipped the per-profile verification default as a genuine TRI-STATE: each profile
and the top-level `defaults` object may carry an optional `validate` boolean, where ABSENT falls
through rather than reading as `false`. The documented precedence chain
(`runner_profiles.py:53-57`) is:

    explicit --validate/--no-validate  >  profile's own `validate`  >  defaults.validate  >
    SHIPPED_VALIDATE_DEFAULT (False)

`ResolvedLaunch` carries the resolved value as a field (`runner_profiles.py:360`).

NOTHING READS IT. Measured 2026-09-05: `grep '\.validate' oc_runipd.py` finds only
`runner_shared.validate_manifest`, a comment about `validate_retry_budget`, and the resume path at
`:7884-7885` which reads `args.validate` exclusively. The verifier gate itself
(`oc_runipd.py:6211-6215`) reads `state["options"]["validate"]`, populated from the CLI flag, and
never consults the resolved profile. So the middle two tiers of the precedence chain are dead.

WHY THIS IS THE ITEM THAT MATTERS MOST OF THE FOUR VERIFICATION GAPS. The maintainer's ruling
(2026-08-31, recorded as F-6 in executed plan `evgi9n`) was NOT that verification is unnecessary. It
was measured and conditional: "on this model the verifier turn added only nits for about 33% extra
cost, so that trade is accepted deliberately; ON A WEAKER MODEL IT IS NOT, WHICH IS WHY THE PER-MODEL
DEFAULT IS WANTED." The verifier ran on every IPD before that ruling (13 runs carry verification
outcomes, last on 2026-08-29) and has run on none since.

So the intended end state is per-model: OFF for the strong executor, ON for a weaker one. `f2mrsw`
built the schema for exactly that and its E-01 says so explicitly, citing the measured Opus-off /
Gemini-on split. Without the wiring, the choice reverts to a flag the operator must remember on every
invocation - which is precisely the failure mode backlog `vju5ba` documented, where a wrong default
went unnoticed across FIVE overnight runs.

THE FIX. Have both runners resolve `validate` through `runner_profiles` and freeze the RESOLVED
value into run state, instead of reading the raw flag. Two properties the plan `f2mrsw` already
demanded and that must be preserved:
  * The tri-state must not collapse. ABSENT means "not specified at this level" and MUST NOT be
    read as `false` at parse time.
  * An explicit `--validate`/`--no-validate` ALWAYS beats a stored default. `f2mrsw`'s review
    recorded why in one line: "a profile silently beating a flag would reproduce [vju5ba] inverted."

Also freeze the resolved value at queue build so a resume cannot silently change the meaning of a
run, matching how the other policy flags are frozen.

SCOPE NOTE: this touches both `oc_runipd.py` and `agy_runipd.py`, the two highest-contention
modules, and the two hosts have OPPOSITE verification defaults today (agy verification defaults ON via
`not no_verify`; oc defaults OFF via `validate`). The wiring must preserve each host's existing
default when no profile and no flag speak, or it becomes a silent safety change disguised as a
refactor. That asymmetry is documented at `agy_runipd.py:3476-3482`.

RELATED: `kgpptv` (`runprofile-06`, pending) gives the verifier turn its own profile, which is the
other half of per-role routing; the two should be sequenced together. Spec `25kzda`'s amended Section
1.3 now records that skipping the verifier turn is a RETAINED, host-configurable choice rather than a
prohibited bypass, so this wiring is the mechanism that makes that choice configuration rather than a
remembered flag.
