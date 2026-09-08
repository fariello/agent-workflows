- Id: e820ka
- Status: open
- Set: wtisoreloc
- Priority: low
- Work-Kind: followup
- Summary: decide whether to relocate per-machine control state out of the repository at all, now that the state-fork defect it was bundled with is closed: wtiso Phase 4 (58ha43) was retired unlanded and has no successor

## Workflow history
- 2026-09-08 created (aw backlog): Carries forward Debt 1 of backlog ol8iyx, which plan 2iye0e deliberately does NOT graduate: the pointer-correction half is a defined change and became 2iye0e, while the relocation itself is an open DECISION and would have made that plan either implement an undecided design or do nothing. Filed so aw attention keeps seeing the debt instead of it living only in plan prose.

AN OPEN DECISION, NOT A DEFINED CHANGE. This is Debt 1 of backlog `ol8iyx`, split out so its
pointer-correction sibling could be graduated cleanly. `ol8iyx` bundled two debts created by one
retirement; plan `2iye0e` takes the stale-pointer half (a defined, mechanical edit), and this item
keeps the half that first requires a decision nobody has made.

WHAT WAS RETIRED. `wtiso` Phase 4 (`58ha43`, now
`.aw/records/plans/superseded/20260828-wtiso-05-58ha43-phase-4-relocate-runtime-machine-state-out-of-the-repo-to-an.ipd.md`)
would have relocated per-machine runtime state out of the repository into an XDG state dir, defining
`platform_state.state_home()` and `platform_state.checkout_state_root(<checkout-id>)` under
`$XDG_STATE_HOME/agent-workflows/checkouts/<checkout-id>/`, and routing the driver run root through
them. It was retired UNLANDED in `70b5338a` by plan `eulhzt`, and its own retirement banner states the
honest position: "retiring UNLANDED, with no successor for its main deliverable ... nothing on `main`
does that, so the capability is genuinely NOT delivered."

VERIFIED ABSENT AT HEAD `fac69fbd`: there is no `agent_workflows/platform_state.py`, and neither
`state_home` nor `checkout_state_root` appears anywhere in code (the only repo-wide hits are prose in
a spec, a backlog item, and two plan records).

WHY THIS IS LOW PRIORITY AND NOT URGENT, so nobody escalates on reading the word "unlanded". The
defect Phase 4 was linked to (`dh0uno`) was caused by cwd-relative RESOLUTION, not by in-repo
LOCATION, and it is CLOSED. Every worktree of a checkout now resolves ONE in-repo, gitignored control
root through a single function, `ipd_lifecycle.checkout_control_root` (`ipd_lifecycle.py:190`, keyed
on `git rev-parse --git-common-dir`), pinned by `tests/test_statefork_dh0uno.py` against a real
`git worktree`. Relocation is the SEPARATE concern Phase 4 bundled with it: keeping machine state out
of a product tree. Because the location is now decided in exactly one function, a later relocation is
a small contained change rather than a migration.

WHAT A SUCCESSOR MUST DECIDE FIRST, recorded so the eventual plan does not restart from zero. These
are the reason this is an item and not a plan:
  1. WHETHER TO RELOCATE AT ALL, given the fork defect is closed and the remaining motivation is
     hygiene (machine state in a product tree) rather than a live failure.
  2. The MIGRATION PATH for existing receipts, locks, and journals under `<repo>/.aw/state/`.
  3. Whether the DRIVER RUN ROOT (`.aw/records/runs/<run-id>/`, gitignored, currently computed from
     the main-repo `repo` argument in both drivers' `state_root`) moves with it.
  4. The WINDOWS and XDG-ABSENT FALLBACK.

CONSUMERS THAT WOULD BE AFFECTED, so the blast radius is known before the decision. `runner_stop.py`
resolves the stop-request flag through the drivers' own `state_root` accessor rather than constructing
a path, so it INHERITS whatever that accessor answers and would need no change; that indirection is
deliberate and must be preserved by any relocation. Spec `c4gd2h` OQ-03 (`- Status: resolved`, human
maintainer, 2026-08-29) grounds the flag's location on Phase 4's accessors and states the out-of-repo
path "REQUIRES `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) to be executed first"; plan `2iye0e` E-05
annotates that stale sequencing without reopening the resolved answer, and names this item as the
successor tracker. The resolved ANSWER (per-machine control state, inside the driver run dir, one
accessor, never a worktree-relative path) stays correct either way.

NOT BLOCKING ANYTHING AND CARRYING NO RELEASE GATE. Nothing on `main` is broken by the absence, which
is why `ol8iyx` carried no `Blocks-Release` and this item inherits none.
