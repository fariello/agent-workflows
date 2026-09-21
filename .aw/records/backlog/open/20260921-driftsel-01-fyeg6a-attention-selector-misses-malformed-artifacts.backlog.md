- Id: fyeg6a
- Status: open
- Blocks-Release: next
- Set: driftsel
- Priority: medium
- Work-Kind: bug
- Summary: aw attention cannot find a MALFORMED artifact by id6: a parse failure yields drift and no item, so the selector matched nothing

## Workflow history
- 2026-09-21 created (aw backlog): aw attention cannot find a MALFORMED artifact by id6: a parse failure yields drift and no item, so the selector matched nothing

FOUND 2026-09-21 by plan fqnj8k's own E-06 test rather than predicted, and PARTIALLY FIXED there; this item covers the part fqnj8k could not reach.

THE SHAPE OF IT. A tracked artifact that fails to parse (measured case: a plan carrying no `- Status:`) produces ONE `attention.missing-status` Drift record and ZERO Items. Everything downstream of `scan()` that reasons over `items` therefore cannot see the file at all. `aw attention <its-id6>` consequently showed an empty board: the ONE artifact an operator most needs to find is the broken one, and the view could not name it.

WHAT fqnj8k FIXED. Its new `selector_match_facts()` now also matches a token against the DRIFT LOCATIONS, so naming a malformed artifact is no longer reported as a typo (it would otherwise have been a false no-match, i.e. worse than the silence the plan set out to remove). Pinned by `test_E03_a_token_naming_a_MALFORMED_artifact_is_matched_not_a_typo`.

WHAT REMAINS, and it is the substance of this item. The artifact is still NOT AN ITEM, so:
  * it appears in the board only as a VIOLATION line, never as a row with a status/class/priority;
  * `--paths`/`--filenames`/`-id` print nothing for it, because those iterate items;
  * `--json`'s `items` array omits it while `violations` names it, so a consumer counting work misses it;
  * `-t`/`--status` narrowing cannot select it.
So `aw att <id6>` on a malformed artifact answers "here is a contract violation" and never "here is your artifact, and it is broken".

WHY IT IS A BUG BY THIS REPO'S OWN TEST. The user-perceptible impact is that the tool cannot answer the question it exists to answer for exactly the artifacts that need attention most. This is a correctness gap, not a performance one.

A LIKELY DESIGN, not prescribed: emit a degraded Item for an artifact that resolves to a tracked tree but fails its per-tree parse (id6 from the filename, native_status "-", an attention class of `blocked` or a new `invalid`), so every surface can render it, WHILE keeping the Drift record so `--check` still fails closed. Note that adding an attention class touches `attention_contract.py`, which approved plan m867ox declares; sequence accordingly.

NOT FIXED IN fqnj8k because a new class or a degraded-item contract is a change to what the view SHOWS, which that plan's scope explicitly excludes.
