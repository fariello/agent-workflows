- Id: plbkp5
- Status: open
- Set: awinbox
- Priority: low
- Work-Kind: feature
- Summary: surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed

## Workflow history
- 2026-09-05 created (aw backlog): surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed

Context: `.aw/inbox/` (commit b534fee9) is deliberately invisible to every records view: it sits
outside `.aw/records/` so the `other` catch-all cannot sweep it, and its files are not artifacts (no
id6, no status, no lifecycle). That is the correct default and must not change.

The cost of that invisibility: a file dropped there and then forgotten stays forgotten. `aw attention`
is the repo's answer to "what needs attention?", and it currently cannot see the queue at all.

Ask: have `aw attention` report a plain count, e.g. `inbox: 3 files waiting`, as a NUDGE.

HARD CONSTRAINT, and the reason this item is worth writing down rather than doing casually: the
implementation may read DIRECTORY ENTRIES ONLY (names, and at most size/mtime). It must NEVER open or
parse an inbox file. Rationale, measured: `selectors._ID_RE` harvests a metadata-shaped `- Id:` line
from anywhere in a body, so parsing a raw external drop lets that drop's CONTENT assert an identity
and collide with a real artifact (see item `cqytxf`; this is live today for a tracked doc). Listing
cannot do that; parsing can. Keep the distinction explicit in the code and its comment: inbox items
are VISIBLE AS FILES, never INTERPRETED AS RECORDS.

Design notes:
- The count is derived on demand, like the rest of the attention view; nothing is committed.
- Do NOT invent a status for inbox items. They have none, and they must not appear in the
  ready/active/blocked/done/parked classification, which is defined over tracked artifacts. A count
  in its own line (or an advisory note) is the whole feature.
- Decide whether `--check` should ever fail on a non-empty inbox. Recommendation: NO. A waiting drop
  is not a repository defect, and failing CI on the presence of a local, gitignored, box-local file
  would be wrong (other machines cannot even see it).
- Hidden files, non-`.md` drops, and nested directories should all count as "something is waiting";
  the point is a nudge, not a typed inventory.

Depends on nothing; independent of `aw adopt` (item `lsztiu`), though the two compose: the count
tells you work is waiting, `adopt` is how you clear it.
