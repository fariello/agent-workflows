- Id: fjs11i
- Status: graduated
- Blocks-Release: next
- Set: hardreach
- Priority: medium
- Work-Kind: bug
- Summary: The hardened OS-sandbox execution profile is live dead code: options[execution_profile] is read but never set and has no CLI flag, so the capability cannot be requested

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan n5qca5 (hardreach-01), NARROWED. Defect re-verified by symbol: the one options[execution_profile] occurrence in the package is a COMMENT at oc_runipd.py:5392, no CLI flag exists, and detect_host_capabilities('opencode') reports supports_os_sandbox=True/landlock on this host, so the dead branch guards working enforcement. Constraint 2 is DEAD and dropped: dh0uno landed in 6771e590 (2026-09-02) via ipd_lifecycle.checkout_control_root:188, its item is in backlog/done/, tests/test_statefork_dh0uno.py passes 17/17, and 7p9n2v (which this item says the fix waits on) is in superseded/. Constraint 1 (Landlock is Linux-only against a macOS-100%/Windows-95% bar, q65sz3 still todo) survives intact and is why the plan is decision-first with a BLOCKING OQ-01 on the request surface. Blocks-Release: next inherited by the plan.
- 2026-09-03 set (aw backlog): RECLASSIFIED followup -> bug AND GATED, maintainer ruling 2026-09-03. Each of these three describes shipped behavior that does not match what the product claims, so under the all-bugs-block-release rule they are bugs, and the 'followup' label was the reason the 2026-09-03 gating audit skipped them. Work-Kind edited directly because 'aw backlog set' has no --work-kind flag (its 'aw ipd set' twin does); that tooling gap is filed separately.

PARTIAL OBSOLESCENCE RECORDED 2026-09-08 AT GRADUATION. Graduated to plan `n5qca5` (`hardreach-01`),
NARROWED. Read this before the constraints below, because ONE OF THE TWO is dead and it is the one that
made this look dangerous to touch.

CONSTRAINT 2 IS DEAD: `dh0uno` IS FIXED. The paragraph below says "IT WILL REFUSE LOUDLY UNTIL `dh0uno`
IS FIXED" and that `dh0uno` "is fixed by `7p9n2v`, written and tested but unmerged". Both halves are
stale. `dh0uno` landed in `6771e590` (2026-09-02, "anchor control state on the checkout, not the cwd
(closes dh0uno)"), by a DIFFERENT route than `7p9n2v`, which is now in `superseded/`.
`ipd_lifecycle.checkout_control_root` (`:188`) is the single control-root authority keyed on the git
common dir, the `dh0uno` item sits in `backlog/done/` recording the fix, and
`tests/test_statefork_dh0uno.py` passes 17/17 at HEAD. So enabling hardened mode no longer converts a
silent state fork into a hard failure, and that reasoning is NOT carried into the plan.

CONSTRAINT 1 SURVIVES INTACT and is the whole reason the plan is decision-first with a BLOCKING open
question: Landlock is Linux-only against a macOS-100%/Windows-95% bar, and research prompt `q65sz3`
(`- Status: todo`) is scoped at exactly the portable-confinement question. The plan carries this
verbatim in substance and explicitly forbids pre-empting that research.

THE DEFECT ITSELF WAS RE-VERIFIED BY SYMBOL rather than trusted, and it is real: the ONE
`options["execution_profile"]` occurrence in the package is a COMMENT (`oc_runipd.py:5392`), not an
assignment, and there is no CLI flag. `detect_host_capabilities("opencode")` on the graduating Linux
host reports `supports_os_sandbox=True` with `sandbox_mechanism="landlock"` and
`probe_notes["landlock"]="landlock jail enforced: write outside the allowed root was refused"`, so the
unreachable branch guards WORKING enforcement.

`1o4eif` (wtiso Phase 6) landed a WORKING hardened OS-sandbox profile that NOTHING can request, so the
capability ships but is unreachable. Found while reconciling that plan's lifecycle record (`b2b2bf6c`),
and filed rather than papered over: finalizing Phase 6 would otherwise imply the capability is usable.

MEASURED on main at `b2b2bf6c`:

  * `options.get("execution_profile")` is READ exactly once, in `_apply_execution_profile`
    (`agent_workflows/oc_runipd.py:4031`).
  * NOTHING ever SETS it: `grep -c 'options\["execution_profile"\]\s*='` over `agent_workflows/*.py`
    -> **0**.
  * There is NO CLI flag: no `add_argument` mentions it -> **0**.

So `select_execution_profile` returns `"default"` on every real invocation and the sandbox branch is
dead. This is not a defect in Phase 6's own work, which is correct and tested (27 tests pass in
`tests/test_host_sandbox_profile.py`, and its V-01/V-02 claims re-ran clean during the reconciliation:
all seven capability fields default `False`, and windows/darwin both report `supports_os_sandbox=False`,
i.e. fail-closed). The gap is purely the missing REQUEST path.

WHAT THIS ITEM NEEDS: a way to ask for the hardened profile (a CLI flag, a profile setting, or both),
plus a decision about the default. Deliberately NOT decided here.

TWO CONSTRAINTS THAT MUST SHAPE THE ANSWER, so they are not rediscovered:

1. PLATFORM. The enforcement is Landlock, i.e. Linux-only. The maintainer's stated platform bar is
   macOS 100% MUST and Windows 95%, so Landlock cannot be the whole answer and a Linux-only flag would
   ship a guarantee most target hosts cannot honor. The in-flight research prompt `q65sz3`
   (cross-platform agent write-confinement) is scoped at exactly this question, including options that
   sidestep OS confinement (separate clone, per-run user account, detect-and-refuse) because those are
   portable. Prefer waiting for it over inventing a Linux-only surface.
2. IT WILL REFUSE LOUDLY UNTIL `dh0uno` IS FIXED. The profile binds the MAIN checkout read-only, while
   `dh0uno` (inner `aw` resolves state against the lane worktree) means a lane turn still reaches into
   main's state. So enabling hardened mode before `dh0uno` lands converts a silent state fork into a
   hard failure. `dh0uno` is fixed by `7p9n2v`, written and tested but unmerged.

RELATED, and why this is not simply "turn it on": the same probe ladder already had to be corrected once
after Phase 6 merged (`909eb007` closed two fail-OPEN holes), which is the empirical case for gating the
request path behind a real decision rather than adding a flag opportunistically.
