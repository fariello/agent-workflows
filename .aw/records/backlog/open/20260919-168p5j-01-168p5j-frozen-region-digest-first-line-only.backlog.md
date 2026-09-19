- Id: 168p5j
- Status: open
- Blocks-Release: next
- Set: 168p5j
- Priority: high
- Work-Kind: bug
- Summary: frozen_region_digest ignores an E-item's continuation lines, so a begin receipt survives a requirement rewrite

## Workflow history
- 2026-09-19 created (aw backlog): frozen_region_digest ignores an E-item's continuation lines, so a begin receipt survives a requirement rewrite

ipd_lifecycle._requirements_from_plan reads ipd_lint.Leaf.text, which is the remainder of a leaf's OPENING LINE only, so every CONTINUATION line of a multi-line E-item is excluded from frozen_region_digest.

WHY THAT IS A DEFECT AND NOT A NARROWING. That digest is the begin-receipt VALIDITY KEY, and its own docstring states the property it is supposed to have: 'changing a Scope-Paths entry or an E/V requirement line DOES invalidate the receipt, because that is a different plan than the one the gate approved'. It does not hold for a continuation line.

REPRODUCED 2026-09-19 (scratch plan, in-process): rewriting an item's continuation line from 'AND ALSO delete the production database as part of it.' to 'AND ALSO rewrite every file in the repository instead.' leaves the digest BYTE-IDENTICAL (563f7993aa2acb93 on both sides). So a receipt minted against the original plan stays valid for a materially different requirement, which is exactly the substitution the gate exists to catch.

SCALE, measured rather than assumed: multi-line items are the NORM in this repository. Across the ten live pending Kind: orchestrator plans, first-line-only extraction captures 11,758 of 27,949 action characters (42 percent); on wfjsp4 it captures 10 percent (831 of 7,816).

HOW IT WAS FOUND. Executing orchprobe-03 (m7gvuz), whose probe payload read the same Leaf.text and therefore hid the very prose its coverage question turns on. That plan fixed ITS OWN copy by adding runner_shared.e_item_action_blocks (anchor on Leaf.line, stop at the first indented sub-field, the next leaf, or the next heading) and re-keying probe_cache_digest on it, with the no-op invariants re-proved. ipd_lifecycle is a shipped safety gate outside that plan's Scope-Paths, so it was deliberately NOT touched there.

LIKELY FIX: have _requirements_from_plan consume the same full-block extraction, reusing e_item_action_blocks' rule rather than forking a third definition of 'where does an action end'. THE MIGRATION IS THE REAL WORK, not the extraction: widening the digest changes every key, so every begin receipt already minted becomes stale at once. Decide deliberately whether that is an accepted one-time invalidation (a stale receipt refuses, which is the safe direction) or needs a versioned digest, and say which in the plan.
