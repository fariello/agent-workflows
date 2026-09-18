- Id: q96tpi
- Status: open
- Set: q96tpi
- Priority: medium
- Work-Kind: bug
- Summary: aw attention reports one stranded lane once per run, so 12 lanes render as 19 rows: the dedup key includes run_id

## Workflow history
- 2026-09-17 created (aw backlog): aw attention reports one stranded lane once per run (dedup key includes run_id), so 12 lanes render as 19 rows; measured 19 rows / 12 distinct at HEAD d188eaad

MEASURED 2026-09-18 at HEAD `d188eaad`, in the maintainer's primary (non-lane) checkout:

    $ aw att --format json | (count lane violations vs distinct locations)
    rows: 19 distinct: 12
    repeats: {'58ha43': 2, '7p9n2v': 3, 'qcqhj7': 3, 'rchpms': 3}

So the STRANDED LANES section claims 19 items of lost work when there are 12 lanes, overstating the
count by 58%. Four lanes are printed two or three times, each row differing only in the `run` id.

## Root cause

`runner_shared.stranded_lane_records` dedups the reported set on a THREE-part key
(`runner_shared.py:1283-1288`):

```python
key = (
    run_id,
    str(lane.get("branch") or ""),
    str(lane.get("worktree") or ""),
)
```

`run_id` is part of the key, so one lane touched by N runs yields N records. The function's docstring
justifies the key as "De-duplicated by `(run_id, branch, worktree)`, so one lane named by both an
attempt and the item-level `preserved_*` fields yields one record." That reasoning is CORRECT for the
WITHIN-run duplicate it was written for (an attempt and the item naming the same lane), and it is the
`run_id` component that makes it wrong ACROSS runs. The three tripled lanes are exactly the `wtiso`
chain lanes that appear in three separate historical runs
(`run-20260829T141137Z-3037978`, `run-20260829T153858Z-3207626`, `run-20260829T191652Z-4134000`).

## Expected

One lane is at most one row. A lane touched by N runs is reported ONCE, retaining the most informative
record and carrying the run count (and ideally the newest run id) so no evidence is lost from the row.

## Fix sketch

1. Keep the existing within-run collapse exactly as it is; it fixes a real duplicate.
2. Add a per-BRANCH collapse of the REPORTED set, choosing the most informative record (prefer one
   carrying an `integration_signal`, then the highest `commits_ahead`).
3. Carry `runs: N` (and the newest `run_id`) on the retained record so the row still shows that several
   runs touched the lane.
4. Regression test: two run states naming the same lane branch must produce exactly one record, and a
   single run naming one lane by both an attempt and `preserved_*` must still produce one.

## Why this matters beyond cosmetics

`aw attention --check` fails closed on these rows, and the section is the first thing an agent or human
reads when asking "what needs attention". An inflated count trains dismissal of the whole section,
which is the alarm-fatigue outcome spec F3a's own wording warns against ("a check that fails on correct
behavior is a check operators bypass"). It also buries any FUTURE genuine strand among repeats.

## Not a duplicate of

`qliia1` (triage the lane branches) and plan `ut0vzr`, which decide the DISPOSITION of the underlying
lanes; this is a defect in the REPORTING of whatever set exists, and it would still misreport a fresh
strand tomorrow after every current lane is retired. Also not `a58s04`, whose subject is lane
teardown/reclamation (a WRITE); this is read-only rendering.
