- Id: fjs11i
- Status: open
- Blocks-Release: next
- Set: hardreach
- Priority: medium
- Work-Kind: bug
- Summary: The hardened OS-sandbox execution profile is live dead code: options[execution_profile] is read but never set and has no CLI flag, so the capability cannot be requested

## Workflow history
- 2026-09-03 set (aw backlog): RECLASSIFIED followup -> bug AND GATED, maintainer ruling 2026-09-03. Each of these three describes shipped behavior that does not match what the product claims, so under the all-bugs-block-release rule they are bugs, and the 'followup' label was the reason the 2026-09-03 gating audit skipped them. Work-Kind edited directly because 'aw backlog set' has no --work-kind flag (its 'aw ipd set' twin does); that tooling gap is filed separately.

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
