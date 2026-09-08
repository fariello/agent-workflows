- Id: ol8iyx
- Status: graduated
- Set: wtisodebt
- Priority: low
- Work-Kind: followup
- Summary: wtiso retirement debt: the out-of-repo control-state relocation (Phase 4, 58ha43) has no successor plan, and six in-code pointers plus spec c4gd2h OQ-03 still name retired wtiso plans as the live owner of unbuilt work

## Workflow history
- 2026-09-08 graduated (aw set): PARTLY OBSOLETE, SPLIT IN TWO. Seven of the twelve sites (all wtiso_gate.py) were already fixed by executed plan 604wra (1d9bbbd3) in exactly the style this item's suggested fix (b) prescribes. Debt 2 (the five surviving stale pointers plus the spec c4gd2h OQ-03 annotation) graduated to plan 2iye0e. Debt 1 (the out-of-repo relocation) is an open DECISION not a defined change, so it split out to backlog item e820ka rather than being graduated. Three corrections recorded in the body: this item MISLABELS the platform_lock site (that capability shipped under y6mfgo, so the no-successor note would be false there), its VERIFY-WITH grep misses two Phase 4 claims that carry no id6, and editing describe_lane's docstring breaks an AST fingerprint freeze it does not mention. graduated not done because Debt 1 survives in e820ka.
- 2026-09-05 created (aw backlog): filed by plan eulhzt E-08: records the debt left by retiring wtiso Phases 4/5 unlanded, so aw attention can see it instead of it living only in plan prose

GRADUATED 2026-09-08, PARTLY OBSOLETE, AND SPLIT IN TWO. Read this header before acting on anything
below it: the site list and the prescribed fixes are no longer accurate.

WHAT IS ALREADY DONE (do NOT re-fix). SEVEN of the twelve `wtiso_gate.py`-related sites this item lists
were repaired by executed plan `604wra` (commit `1d9bbbd3`), in exactly the style this item's own
suggested fix (b) prescribes. `_unimplemented`'s contract now REQUIRES a message to name the owner AND
ITS DISPOSITION; `check_protected_refs` (`wtiso_gate.py:294`) reads "`2c122z` (Phase 5, RETIRED
UNLANDED 2026-09-02) ... NEITHER is in flight and the recovery surface has no successor";
`check_receipt` (`:423`, `:440`) records both owners retired plus what did land, which resolves this
item's own "doubly stale" complaint; and the module docstring (`:37-43`) states the retirement. Pinned
by `tests/test_containment_predicates.py`.

WHERE THE SURVIVING WORK WENT. Debt 2 (the stale pointers) graduated to plan `2iye0e`
(`.aw/records/plans/pending/20260908-wtisoptr-01-2iye0e-...ipd.md`, carrying `- From-Backlog: ol8iyx`),
narrowed to the FIVE pointers that actually survive plus the spec OQ-03 annotation. Debt 1 (the
relocation, which has no successor plan) is NOT graduated: it is an open DECISION rather than a defined
change, so it was split out to its own backlog item `e820ka` (Set `wtisoreloc`) where `aw attention`
keeps seeing it. That is why this item is `graduated` and not `done`.

THREE CORRECTIONS TO THIS ITEM'S OWN CONTENT, found while graduating it:
  1. ONE SITE IS MISLABELED. This item lists `runner_shutdown.py`'s `platform_lock` comment among the
     "no successor" sites. It is not: `agent_workflows/platform_lock.py` EXISTS on `main`, shipped
     under plan `y6mfgo`, whose record states it SUPERSEDES `2c122z`'s `platform_lock` portion and
     names the module to match `2c122z`'s references on purpose. Applying this item's generic note
     there would write a FALSE claim into the source. Plan `2iye0e` E-02 handles it separately.
  2. THE VERIFY-WITH GREP IS INSUFFICIENT. Two stale Phase 4 claims (`runner_stop.py:41-44` and
     `:362-363`) say "Set `wtiso` Phase 4" in prose with NO id6 anywhere, so
     `grep -rn "58ha43\|2c122z\|7p9n2v" agent_workflows/` returns success while both survive. Grep by
     phrase, not by id6 alone.
  3. A TRAP THIS ITEM DOES NOT MENTION. `describe_lane`'s docstring in `runner_shared.py` is frozen
     into an AST fingerprint fixture (`tests/fixtures/runner_shared_premove_fingerprints.json`,
     asserted by `tests/test_runner_shared.py`), and a docstring is part of the unparsed body, so
     editing it breaks that freeze. Verified mechanically by recomputing the fingerprint.
  Also minor: this item's citations `oc_runipd.py:4223` and `agy_runipd.py:2345` for `rchpms`
  provenance are stale; they are now `:5530` and `:2720`. The item's judgment that `rchpms` citations
  are LEGITIMATE (Phase 2 partly landed) is correct and was confirmed.

ORIGINAL ITEM TEXT FOLLOWS, uncorrected.

TWO DISTINCT DEBTS, filed together because one retirement created both. Plan `eulhzt` (which closed
backlog `dh0uno` by anchoring control state on the checkout) retired the seven `wtiso` plans to
`.aw/records/plans/superseded/` in `70b5338a`, with banners citing where each of the Set's three named
failures went. Two of those plans were retired UNLANDED, and this item records what that leaves behind.
Nothing on `main` is BROKEN by either debt, so this item deliberately carries no `Blocks-Release`.

DEBT 1: THE OUT-OF-REPO CONTROL-STATE RELOCATION HAS NO SUCCESSOR PLAN.

`wtiso` Phase 4 (`58ha43`, now `superseded/20260828-wtiso-05-58ha43-phase-4-relocate-runtime-machine-
state-out-of-the-repo-to-an.ipd.md`) would have relocated per-machine runtime state out of the
repository into an XDG state dir, defining `platform_state.state_home()` and
`platform_state.checkout_state_root(<checkout-id>)` under
`$XDG_STATE_HOME/agent-workflows/checkouts/<checkout-id>/` and routing the driver run root through
them. Its own retirement banner states the honest position: "retiring UNLANDED, with no successor for
its main deliverable ... nothing on `main` does that, so the capability is genuinely NOT delivered."

WHY THIS IS NOT URGENT, so nobody escalates it on reading the word "unlanded": the defect Phase 4 was
linked to (`dh0uno`) was caused by cwd-relative RESOLUTION, not by in-repo LOCATION, and it is closed.
Every worktree of a checkout now resolves ONE in-repo, gitignored control root through a single
function, `ipd_lifecycle.checkout_control_root` (keyed on `git rev-parse --git-common-dir`), pinned by
`tests/test_statefork_dh0uno.py` against a real `git worktree`. Relocation is the SEPARATE concern
Phase 4 bundled with it: keeping machine state out of a product tree. Because the location is now
decided in exactly one function, a later relocation is a small, contained change rather than a
migration.

WHAT A SUCCESSOR WOULD HAVE TO DECIDE (recorded so the eventual plan does not restart from zero):
whether to relocate at all given the fork is closed; the migration path for existing receipts, locks,
and journals under `<repo>/.aw/state/`; whether the driver run root (`.aw/records/runs/<run-id>/`,
gitignored, currently computed from the main-repo `repo` argument in both drivers' `state_root`) moves
with it; and the Windows/XDG-absent fallback.

DEBT 2: SIX IN-CODE POINTERS AND ONE SPEC OQ NAME A RETIRED PLAN AS THE LIVE OWNER OF UNBUILT WORK.

Each site below was VERIFIED present at the time of filing. The pattern is the same everywhere: a
comment or docstring says some capability is "owned by" a `wtiso` child, and that child is now
`superseded` and unlanded, so the pointer names a plan that will never run. None of these is a
behavior bug; each is a stale ownership CLAIM that will mislead the next reader deciding whether they
may build the thing.

Sites naming `2c122z` (`wtiso` Phase 5, retired unlanded), which was said to own the Windows
process-tree kill, the cross-platform `platform_lock`, the never-auto-stash requirement, and the
`aw doctor --lanes` / `aw recover` verbs:

- `agent_workflows/runner_stop.py:35` - "The Windows process-tree kill remains owned by Set `wtiso`
  Phase 5 (`2c122z`); do not build a second one here (GUIDING_PRINCIPLES P8)."
- `agent_workflows/runner_stop.py:1604` - the same prohibition restated at the module's level-5 block.
- `agent_workflows/runner_shutdown.py:202` - "the cross-platform ``platform_lock`` is owned elsewhere
  (`wtiso` Phase 5, `2c122z`), which this Set must not duplicate (orchestrator CID-5)."
- `agent_workflows/runner_shutdown.py:317` - "`wtiso` Phase 5 (`2c122z`) requires never auto-stashing,
  resetting, or overwriting a dirty user main."
- `agent_workflows/runner_shared.py:389` - "`aw doctor --lanes` and `aw recover` are owned by plan
  `2c122z`".
- `agent_workflows/wtiso_gate.py:152,156` - `check_protected_refs` raises `_unimplemented(...,
  "2c122z")`, i.e. the loud-failure skeleton names a retired owner in the exception itself.

Sites naming `58ha43` (`wtiso` Phase 4, retired unlanded):

- `agent_workflows/runner_stop.py:42` - "Set `wtiso` Phase 4 relocates the driver run root OUT of the
  repository to `platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/`, and because this
  module resolves through the shared accessor it inherits that relocation automatically."
- `agent_workflows/runner_stop.py:355` - "when Set `wtiso` Phase 4 moves that accessor's answer out of
  the repository, the flag moves with it and nothing here changes (spec OQ-03)."
- `agent_workflows/wtiso_gate.py:186` - `check_receipt`'s docstring: "`58ha43` (Phase 4) relocates the
  canonical receipt store and removes the in-lane copy." Doubly stale: `eulhzt` E-03 already made the
  in-lane receipt copy a no-op.

Spec, and the reason it needs care rather than an edit:

- `.aw/records/specs/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md`, OQ-03 ("Where
  does the stop-request flag live?"), `- Status: resolved`, resolved by the HUMAN maintainer on
  2026-08-29, in a spec whose own `- Status:` is `implementing`. Its resolution grounds the flag's
  location on Phase 4's accessors by citing "`wtiso-05` (`58ha43`) E-01/E-02 define `state_home()` and
  `checkout_state_root(checkout_id)`", and states that "the out-of-repo path REQUIRES `wtiso` Phase 3+4
  (`7p9n2v`, `58ha43`) to be executed first". With both plans retired unlanded, that stated
  precondition is now unsatisfiable as written. Its `- Blocking:` line also asserts the OQ "interacts
  directly with `wtiso` Phase 4".

NOT A LIVE BUG, and this is the part to read before "fixing" anything: `runner_stop.py` resolves the
stop-request flag through the drivers' own `state_root` accessor rather than constructing a path, so it
inherits whatever that accessor answers. Today that is `<repo>/.aw/records/runs/<run-id>/`, the flag
works, and if a relocation ever lands the flag moves with it and that module does not change. The spec's
resolved ANSWER (per-machine control state, inside the driver run dir, one accessor, never a
worktree-relative path) therefore remains correct; only its cited SEQUENCING is stale.

WHY `eulhzt` DID NOT FIX THIS ITSELF (so this is not a dropped ball): the retirement landed in
`70b5338a`, a separate commit outside that plan's `Scope-Paths` fence, and rewriting six modules' prose
plus a human-resolved spec question is a distinct concern that would have blown the plan's scope and
re-opened a signed-off OQ. `eulhzt` E-08 filed this item instead, so `aw attention` can see the debt
rather than it living only in plan prose.

SUGGESTED SHAPE OF THE FIX (one small plan, no code behavior change): (a) rewrite the six pointers to
name the CAPABILITY and its status rather than a retired plan id, e.g. "not implemented; no current
owner (was `wtiso` Phase 5 `2c122z`, retired unlanded 2026-09-02)", keeping the P8 do-not-duplicate
instruction intact since that is still the right guidance; (b) for `wtiso_gate.py`, keep the
`NotImplementedError` skeleton (Phase 0's loud-failure design is deliberate) and correct only the owner
string; (c) for spec `c4gd2h` OQ-03, add a note recording that the cited precondition plans are retired
and that the flag currently resolves through the in-repo accessor, WITHOUT reopening the
human-resolved answer, and cite this item as the successor tracker for the relocation.

VERIFY WITH: `grep -rn "58ha43\|2c122z\|7p9n2v" agent_workflows/` returns only non-ownership mentions
(or nothing), and the six sites read as capability-status rather than live-owner claims. Note that
`rchpms` (Phase 2) is deliberately EXCLUDED from this item: it is also `superseded`, but it PARTLY
LANDED (its `frozen_region_digest` fix is on `main` in `cdef9c90`), so `ipd_lifecycle.py`,
`oc_runipd.py:4223` and `agy_runipd.py:2345` cite it correctly as the provenance of shipped code, which
is a legitimate historical citation and not a stale ownership claim.
