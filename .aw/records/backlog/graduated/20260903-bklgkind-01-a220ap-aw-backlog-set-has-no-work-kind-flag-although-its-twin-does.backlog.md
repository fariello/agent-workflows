- Id: a220ap
- Status: graduated
- Blocks-Release: next
- Set: bklgkind
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog set has no --work-kind flag although its aw ipd set twin does, so correcting a mislabeled backlog item requires hand-editing the frontmatter the tool otherwise owns

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan b5sfwm (Set bklgkind, .aw/records/plans/pending/20260908-bklgkind-01-b5sfwm-...ipd.md), which carries From-Backlog: a220ap and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done: no code is written yet. ONE CORRECTION TO THIS ITEM, which WIDENED the plan rather than narrowing it: this item asserts 'only Priority is reachable on a BACKLOG item', and that is FALSE. Verified at HEAD 44d4950d: aw backlog set --help lists neither --priority nor --work-kind (its full flag list is --dir --status --message --gate-kind --gate-ref --blocks-release --evidence --dry-run --yes --commit/--no-commit, registered at cli.py:3966-4016), and --priority exists only on aw backlog new (cli.py:3914-3916). So NEITHER classification field is tool-settable on an existing item, and fixing only --work-kind would have left the identical hole one field over; the plan covers both (E-01 and E-02). NOTHING IN THIS ITEM IS OBSOLETE: the asymmetry is live, aw ipd set still has both flags (--priority cli.py:1282-1289, --work-kind :1293-1300), and no pending or approved plan touches the backlog work-kind surface. ONE DISCOVERY THAT SHRANK THE WORK: aw backlog set on its POSITIONAL spelling already routes through status_set.apply_status_change (cli.py:11140-11149), whose Work-Kind (:762-773) and Priority (:749-760) writers are record-type-agnostic and hoisted out of every status branch, which is exactly how the ipd twin earns its persists-on-a-no-op-transition behavior; so that spelling needs a parser change only. The --status spelling forks to backlog.run_set (cli.py:11150-11156) and does need its own write, which is the plan's main risk (E-03). The test this item REQUIRES (a no-status-change reclassification persists and appends history) is E-06/V-06, and the plan-side template it should follow already exists at tests/test_work_kind.py:337-377.
- 2026-09-03 set (aw backlog): Gated under the all-bugs-block-release rule: a Work-Kind the tool cannot correct is one that stays wrong, and this gap caused the 2026-09-03 audit to skip three real release blockers.

FOUND 2026-09-03 while applying the maintainer's ruling to reclassify three mislabeled items
(`cnwy8g`, `fjs11i`, `a8eufb`) from `followup` to `bug`. The reclassification could not be done with
the owner verb and had to be a hand edit, which is exactly what the noun-verb grammar exists to prevent.

## The asymmetry

`aw ipd set` HAS the flag (`aw ipd set --help`):

    --work-kind {bug,feature,chore,security,followup,-}
                          Set the plan's Work-Kind (bug|feature|chore|security|followup);
                          '-' clears it (wkindname). Persists on a no-op transition.

`aw backlog set` does NOT. Its full option list is `--dir`, `--status`, `--message`, `--gate-kind`,
`--gate-ref`, `--blocks-release`, `--evidence`, `--dry-run`, `--yes`. So `Priority` and `Work-Kind` are
settable on a PLAN but only `Priority` is reachable on a BACKLOG item, even though both types carry both
fields and `backlog.py` owns the single `KINDS` vocabulary that plans validate against.

Note `aw backlog set` DOES support `--blocks-release`, so the gate half of the same operation is tooled
while the classification half is not.

## Why it matters beyond convenience

The repo's own convention is that agents must not hand-name or hand-maintain these records: the tool owns
the frontmatter. When a field is unreachable, an agent either edits frontmatter directly (what happened
here, recorded in each item's history so the deviation is auditable) or silently leaves the item
mislabeled.

MISLABELING HAS A MEASURED CONSEQUENCE, which is why this is filed as a bug rather than a chore: the
2026-09-03 all-bugs-block-release audit selected on `Work-Kind: bug` and therefore SKIPPED all three
items above, each of which describes shipped behavior that does not match what the product claims. A
label the tool cannot correct is a label that stays wrong, and here it caused three release blockers to
be invisible to the audit that existed to find them.

## What is wanted

Add `--work-kind {bug,feature,chore,security,followup,-}` to `aw backlog set`, mirroring the `aw ipd set`
implementation (including its `-` clears semantics and its persists-on-a-no-op-transition behavior, since
a pure reclassification IS a no-op transition). Validate against the same `backlog.KINDS` vocabulary
rather than a second literal list, so the two verbs cannot drift.

REQUIRED OF WHOEVER TAKES THIS: a test asserting a reclassification with NO status change is persisted
and appends a history record, because that no-op case is the one this defect was hit on.

## Gate

Carries `Blocks-Release: next` under the maintainer's all-bugs-block-release rule. It is a small,
self-contained CLI gap, but it defeats an audit that the release depends on.
