- Id: a220ap
- Status: open
- Blocks-Release: next
- Set: bklgkind
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog set has no --work-kind flag although its aw ipd set twin does, so correcting a mislabeled backlog item requires hand-editing the frontmatter the tool otherwise owns

## Workflow history
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
