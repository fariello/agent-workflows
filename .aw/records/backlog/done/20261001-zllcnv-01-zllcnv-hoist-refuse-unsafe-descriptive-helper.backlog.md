- Id: zllcnv
- Status: done
- Graduated-To: zllcnv
- Set: zllcnv
- Priority: low
- Work-Kind: chore
- Summary: Hoist the duplicated _refuse_unsafe_descriptive helper into attention_contract once backlog, specs and research all ship their own copy, reconciling the refusal wording deliberately rather than as collateral; recorded by uz05bl OQ-02 as a third-consumer decision

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD 685iq8 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-zllcnv-01-685iq8-hoist-the-duplicated-descriptive-refusal-helper-into-attenti.ipd.md); evidence .aw/records/plans/executed/20261002-zllcnv-01-685iq8-hoist-the-duplicated-descriptive-refusal-helper-into-attenti.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 685iq8
- 2026-10-01 created (aw backlog): Hoist the duplicated _refuse_unsafe_descriptive helper into attention_contract once backlog, specs and research all ship their own copy, reconciling the refusal wording deliberately rather than as collateral; recorded by uz05bl OQ-02 as a third-consumer decision

FILED AS THE CARRIER for the hoist row in plan `deftzy` (Set `7w6zsl`), which is the THIRD consumer that pending plan `uz05bl` OQ-02 named as the point at which a hoist becomes worthwhile.

THIS IS A `chore`, NOT A `bug`, AND CARRIES NO RELEASE GATE: all three copies will be correct and byte-compatible by construction, so nothing user-visible is wrong. The cost is three duplicated ~30-line helpers, which is a maintenance concern rather than a defect, and it is why the item is `low`.

STATE OF PLAY, measured 2026-10-01 at HEAD `9e813570a`: exactly ONE copy exists on disk, `backlog._refuse_unsafe_descriptive` (from executed plan `dtg7dz`), with six call sites in `backlog.py`. The `specs` copy is prescribed by pending plan `uz05bl` E-01 and does not exist yet; the `research` copy is prescribed by pending plan `deftzy` E-01. So this item is NOT actionable until both of those execute, and attempting it now would mean hoisting a single copy with no second caller, which is the premature abstraction `uz05bl` OQ-02 already declined once.

WHAT MAKES IT A DECISION RATHER THAN A MOVE. `dtg7dz` declined the hoist for a recorded reason that still holds: `specs.run_set` spells its `--gate-summary` refusal INLINE, so extracting a shared helper would mean editing that shipped message text as collateral of a refactor. A hoist therefore has to reconcile three shipped refusal WORDINGS deliberately, as its own change, rather than silently as a side effect. Both authored plans mitigate this in advance by requiring byte-compatible wording (`uz05bl` E-01 and `deftzy` E-01 both say so, and `deftzy` V-01 requires a side-by-side against the sibling's actual strings), so if both land as specified the hoist really is mechanical.

ONE DESIGN POINT FOR THE EVENTUAL PLAN. The helper's `bound_length` asymmetry is NOT uniform across trees and must not be collapsed on the way up: `specs` genuinely needs `bound_length=False` for history messages (60 of 148 committed spec messages exceed the 300-character bound, max 2594), while `research` uses `bound_length=True` everywhere (no research verb writes a history record at all, and its summary population is 3 of 124 over the bound). A hoist that drops the parameter because one caller never passes it would break the other.

VERIFY BEFORE STARTING, do not trust this note: re-grep for the helper in each module and confirm all three copies are present and their message strings actually agree. If `uz05bl` or `deftzy` was executed with drifted wording, reconciling that drift is part of this work and should be reported, not silently normalized.
