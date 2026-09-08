- Id: plbkp5
- Status: graduated
- Set: awinbox
- Priority: low
- Work-Kind: feature
- Summary: surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed

## Workflow history
- 2026-09-08 graduated (aw set): FULLY LIVE, nothing obsolete. Graduated to plan 9iiqmm. Verified unimplemented: grep for inbox over attention.py and attention_contract.py returns ZERO hits, so this plan writes the first reader of that directory; no plan carries From-Backlog: plbkp5; the sibling lznpv6 covers aw adopt only. I REPRODUCED the justifying hazard: selectors._ID_RE (selectors.py:111) is position-unanchored and matched a - Id: line sitting at line 5 of a body inside prose labelled a quoted example, so the listing-only constraint rests on measured behavior. The --check recommendation now has a citation: the exit code is owned solely by drift (attention.py:2715, :2956) and both existing advisory sections document that they never affect it. THREE things the item does not say, all load-bearing: .aw/inbox/ does not exist in a fresh worktree (gitignored, per-checkout), so absent must mean zero silently; the footer is an if/elif chain (:2940-2948) so an elif addition would hide the nudge exactly when setup is needed; and a new top-level JSON key would bump SCHEMA_VERSION 3, so OQ-01 keeps the count out of the JSON.
- 2026-09-05 created (aw backlog): surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed

GRADUATED 2026-09-08 TO PLAN `9iiqmm`, FULLY LIVE, NOTHING OBSOLETE.
(`.aw/records/plans/pending/20260908-awinbox-02-9iiqmm-...ipd.md`, carrying `- From-Backlog: plbkp5`.)

VERIFIED UNIMPLEMENTED AND UNCLAIMED AT HEAD `fac69fbd`. `grep -rn "inbox"` over BOTH
`agent_workflows/attention.py` and `agent_workflows/attention_contract.py` returns ZERO hits, so
attention is totally blind to the inbox and this plan writes the first reader of that directory. No plan
carries `- From-Backlog: plbkp5`. The sibling item in this Set (`lsztiu`, now plan `lznpv6`) covers
`aw adopt` only: grepping that plan for attention, count, waiting or nudge yields one incidental hit and
no E-item, confirming this item's "independent of `aw adopt`" claim.

THE HARD CONSTRAINT IS JUSTIFIED BY MEASURED BEHAVIOR, not theory: I REPRODUCED the over-capture.
`selectors._ID_RE` is `(?m)^- Id:\s*([0-9a-z]{6})\s*$` (`selectors.py:111`), applied with `.search()`
over a whole body, so it is position-unanchored. Fed a body whose line 5 was a `- Id:` line inside prose
explicitly labelled as a quoted example, it MATCHED and returned that id6. So listing cannot forge an
identity but parsing can, exactly as this item argues. Note `cqytxf` is `graduated` to plan `76w6mq`,
which will bound identity extraction to the metadata region; the listing-only rule stays correct after
that lands, as defense in depth.

THE `--check` RECOMMENDATION IS WELL FOUNDED AND NOW HAS A CITATION. The exit code is owned solely by
the drift set (`core.drift_exit_code(drift)` at `attention.py:2715` and `:2956`), and the two existing
advisory sections say so in their own comments: `gate_warnings` is "human view only; NEVER affect the
exit code" (`:2889-2891`) and `order_notices` "never affects the exit code" (`:2922-2925`). So "do not
fail `--check` on a non-empty inbox" is structural rather than a matter of taste.

THREE THINGS THIS ITEM DOES NOT SAY, each of which changes the implementation:
  1. `.aw/inbox/` DOES NOT EXIST IN A FRESH WORKTREE. It is gitignored (`.aw/.gitignore:28`, `/inbox/`)
     and therefore per-checkout; `ls .aw/inbox` in the graduating worktree returned No such file or
     directory, even though this item and `lznpv6:6` both describe it as holding 10-plus files. So
     "absent means zero, silently" is a first-class requirement, not an edge case.
  2. THE FOOTER IS AN `if/elif/elif` CHAIN (`attention.py:2940-2948`), so exactly ONE footer line ever
     prints. Appending with `elif` would hide the inbox nudge whenever setup is needed, which is the
     state of a fresh checkout, which is precisely where a forgotten drop is likeliest. The plan
     requires an independent `if`.
  3. A NEW TOP-LEVEL JSON KEY WOULD BE A SCHEMA BUMP. `render_json` (`:1070`) emits five keys and
     `SCHEMA_VERSION = 3` (`:33`) is asserted in `tests/test_attention.py`. The plan's OQ-01 therefore
     keeps the count OUT of the JSON, so `--format json` gains nothing; that is a deliberate scope
     decision, recorded so it is not mistaken for an unmet requirement.

THE RIGHT PRECEDENT ALREADY EXISTS: `setup_needed` (`attention.py:1405`) is a derived, read-only,
exception-swallowing boolean that feeds a footer nudge, touches neither the item list nor the exit code,
and whose docstring stresses it "NEVER creates anything". An inbox counter is its structural twin, and
the plan follows it rather than inventing a shape.

ORIGINAL ITEM TEXT FOLLOWS, uncorrected.

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
