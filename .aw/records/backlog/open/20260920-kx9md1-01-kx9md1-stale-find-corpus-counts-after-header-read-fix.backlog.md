- Id: kx9md1
- Status: open
- Set: kx9md1
- Priority: low
- Work-Kind: chore
- Summary: Stale aw find corpus counts in findtier records: ecdd348f changed wtiso from 3 to 8

## Workflow history
- 2026-09-20 created (aw backlog): Filed by plan 826o13 execution: commit ecdd348f (2026-09-19) fixed a truncated 4096-byte header read, so aw find plans wtiso now correctly returns 8 Set members rather than 3. Records authored before that fix still cite 3 as the contract answer.

## What is wrong

Several records state, as the authoritative answer for the `aw find` artifacts-not-references
contract, that `aw find plans wtiso` returns THREE plans (`8zgybk`, `1o4eif`, `qcqhj7`). Measured at
HEAD `881607b6` it returns EIGHT, and eight is CORRECT. Nothing about the contract changed; the
resolver's READ WINDOW did.

THIS IS NOT A REGRESSION AND MUST NOT BE "FIXED" IN THE CODE. Commit `ecdd348f` (2026-09-19,
`fix(selectors): read to the end of the metadata block, not a 4096-byte cap`) replaced a hard
4096-byte cap with a structural bound. Under the old cap, a `- Set:` bullet past byte 4096 was
INVISIBLE, so five of the eight `wtiso` members were silently dropped from their own Set. Measured
offsets of the `- Set: wtiso` bullet, which show the correspondence exactly:

| Plan | `- Set:` byte offset | Visible under the old 4096 cap |
|---|---|---|
| `8zgybk` | 2507 | yes |
| `qcqhj7` | 3894 | yes |
| `1o4eif` | 2954 | yes |
| `7p9n2v` | 4177 | NO |
| `bl9q3d` | 4241 | NO |
| `58ha43` | 5153 | NO |
| `rchpms` | 5581 | NO |
| `2c122z` | 7281 | NO |

The three the records name are EXACTLY the three that were visible under the cap, which is what
identifies the cause rather than merely correlating with it.

## Where

Records citing the stale count (each authored before `ecdd348f`):

- `.aw/records/plans/pending/20260908-findtier-01-826o13-...ipd.md` (Concern, F-6, `Required tests`)
- `.aw/records/reviews/20260910-findtier-01-826o13-...review.md`
- `.aw/records/backlog/open/20260912-59t9x5-01-59t9x5-find-display-layer-double-read.backlog.md`
- `.aw/records/backlog/graduated/20260901-findtwotier-01-f8m2z2-...backlog.md`

## Why it matters, and why it is low priority

A pin written against a moving corpus count fails for a reason unrelated to the contract it means to
protect. Plan 826o13 hit exactly this: its `Required tests` demanded `aw find plans wtiso` return
three records, and the honest execution had to record that the plan's number was stale rather than
assert a passing test against it. The plan's EXECUTION CONTRACT is explicit that a failed pin is a
discovery and not a license to edit `selectors.py`, so this was reported instead of "fixed".

It is low priority because the code is correct and the test suite no longer depends on the stale
number: `tests/test_cli_find.py` asserts tight counts on a SYNTHETIC fixture and only
corpus-independent PROPERTIES on the live tree (`RealRepoContractTests`). The remaining cost is that
a reader of those four records is misled about what `aw find` returns.

## Recommended fix

Correct the cited number in the four records above, noting `ecdd348f` as the cause so the change
does not read as a behavior regression. Do NOT change `selectors.py`.
