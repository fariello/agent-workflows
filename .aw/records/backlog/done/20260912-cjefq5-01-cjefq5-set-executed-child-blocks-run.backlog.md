- Id: cjefq5
- Status: done
- Blocks-Release: next
- Set: cjefq5
- Priority: high
- Work-Kind: bug
- Summary: aw oc run on a Set with an already-executed child blocks the entire Set: both hosts' inline queue-status allowlist has no 'executed' arm, so an executed plan's queue entry says 'reviewed' and the cascade treats it as a dead prerequisite

## Workflow history
- 2026-09-17 done (aw set): Root cause corrected (the Set-expansion/synthesized-entry hypothesis was wrong): one inline allowlist at oc_runipd.py:3515 and its byte-identical twin at agy_runipd.py:2256 had no 'executed' arm, relabeling every executed plan 'reviewed' and making it a dead prerequisite. Fixed in ee99c41d with one shared runner_shared.initial_queue_status; 6 regression tests; 7825 passed.
- 2026-09-13 open (aw set): Gate on next per the all-bugs-block-release ruling: every bug blocks the next release
- 2026-09-12 created (aw backlog): aw oc run on a Set with an already-executed child blocks the entire Set: the queue entry gets file=null and status=reviewed instead of the discovered executed status

## Observed

`aw oc run runanalytics`, run `run-20260913T031139Z-1722888`, 2026-09-13. Outcome BLOCKED, 10 of 11
items `dependency-blocked`, 1 `reviewed`, **zero tokens spent**: it failed at queue build, before any
agent turn.

The Set's Order 01 child `xbwq8n` is ALREADY EXECUTED and correctly filed in
`.aw/records/plans/executed/20260908-runanalytics-01-xbwq8n-...ipd.md` with `- Status: executed`. The
other 10 members are legitimately `approved` in `pending/`.

The frozen queue entry the run recorded for it (from that run's `state.json`):

```json
{"id6": "xbwq8n", "position": 2, "status": "reviewed", "action": "execute",
 "file": null, "setid": "runanalytics", "kind": "child"}
```

Two fields are wrong. `file` is `null`, and `status` is `reviewed` where the plan on disk says
`executed`. Note also the self-inconsistency the summary table displayed: `action: execute` alongside
`status: reviewed` for a plan whose file says `executed`.

(CORRECTION 2026-09-17: only `status` was actually wrong. There is no `file` KEY on a queue entry at
all, so the `null` above is the reporting layer rendering a missing key, not a null path; the entry's
real `configured_file` was correctly populated. And `action: execute` beside a terminal status is
BY DESIGN, since `action` is frozen for resume while dispatch admits only `status == "queued"`. See
the corrected root-cause section below.)

## Why that blocks everything

`bzz5e6` (Order 02) declares `executed:xbwq8n`. The in-run dependency test is
`oc_runipd.py:3376-3382`:

```python
required_states = EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES
if entry.get("status") not in required_states:
    return False, (f"{tok}: in-run target {edge.id6} is {entry.get('status')!r}, ...")
```

`EXECUTION_SUCCESS_STATES` is `{"executed", "substantially-complete"}` (`oc_runipd.py:337`), so
`reviewed` fails. The run reported exactly that: `bzz5e6: dependency-blocked (executed:xbwq8n (target
reviewed) (blocked))`. Reverse-edge propagation (`oc_runipd.py:4227-4281`) then took the whole Set:
02 blocked 03, 03 blocked 04, and so on through 10, and the orchestrator `5lxvl3` blocked on all nine
children.

ONE stale queue entry cost the entire Set. That amplification is why this is `high`, not `medium`.

## Root cause is NOT discovery

Verified interactively, so the fix is not aimed at the wrong layer. `discover_plans` walks
`.aw/records/plans` with `rglob("*.md")` (`runner_shared.py:1251-1259`), so `executed/` IS in scope,
and both discovery and the manifest are CORRECT:

```
xbwq8n discovered? True
  rel_path: .../plans/executed/20260908-runanalytics-01-xbwq8n-...ipd.md
  status:   executed
  order:    1
  kind:     child
in manifest? True {'set': 'runanalytics', 'file': '.../executed/...', 'status': 'executed', ...}
```

`build_dynamic_manifest` copies `rec.rel_path` into `file` and `rec.status` into `status`
(`oc_runipd.py:2233-2235`). So a correct record and a correct manifest entry BOTH exist, and the queue
entry still ended up with `status: "reviewed"`.

## CORRECTED 2026-09-17: the actual root cause (the section above was right, the one below replaced a wrong guess)

The original diagnosis blamed Set-selector / orchestrator-child-table expansion synthesizing an entry,
citing `file: null` as corroboration. BOTH halves of that were wrong, and an implementer sent to
`parse_child_table` would not have found the bug. Re-measured on run `run-20260917T033138Z-557584`
(9 mislabeled parents, 6 children plus 2 orchestrators killed, 0 tokens spent):

1. NOTHING IS SYNTHESIZED. The queue entry carries the CORRECT values from the manifest, including
   `initial_status: "executed"` and a fully populated `configured_file` pointing into `executed/`.
2. THERE IS NO `file` KEY AT ALL. The frozen entry's keys are `action, attempts, configured_file,
   dependencies, from_backlog, id6, initial_status, kind, order, position, setid, status`. The
   reporting layer rendered a missing key as `null`; it was never a null path from a synthesized row.

THE REAL CAUSE IS ONE EXPRESSION, at `oc_runipd.py:3515-3517` and byte-identically at
`agy_runipd.py:2256-2258`:

```python
"status": "queued"
if status in ("to-review", "draft", "approved", "auto-approved")
else "reviewed",
```

An allowlist with NO `executed` arm. Every terminal status falls through to the `else` and is
relabeled `reviewed`. `cascade_dependency_blocked` then reads `status` (not `initial_status`), and
`reviewed` is in `TERMINAL_STATES` but not in `EXECUTION_SUCCESS_STATES`, so the executed parent
becomes a dead prerequisite and every dependent dies at queue build, before any agent turn.

Reproduced in isolation; the verdict flips on QUEUE MEMBERSHIP ALONE for the same plan and edge:

```
in-queue : (False, "executed:cqx5v7: in-run target cqx5v7 is 'reviewed', needs one of ['executed', ...]")
external : (True, '')
```

That is what spec `20260826-25kzda-01` 2.9 line 399 explicitly prohibits: satisfaction must be decided
"by the consuming action and by nothing else: not by queue membership ... An implementation that lets
the same edge be satisfied or refused depending on queue membership is the evadability defect this
section exists to prevent." `edge_satisfied`'s external branch is correct ("A TERMINAL DIRECTORY IS
AUTHORITATIVE"); the in-queue branch was reading a corrupted input.

BLAST RADIUS: 13 runs carry this signature, not one. Worst cases by items lost:
`run-20260913T031521Z-1774617` (16), `run-20260913T031148Z-1722898` (12),
`run-20260913T031139Z-1722888` (10), `run-20260913T031350Z-1732436` (8),
`run-20260917T033138Z-557584` (6 children + 2 orchestrators).

## Expected

An id6 present in the manifest MUST take that manifest entry's `file` and `status`. A Set member that
is already `executed` must be admitted as satisfied (it is in `EXECUTION_SUCCESS_STATES`) so its
dependents run, exactly as an out-of-queue executed target already is at `oc_runipd.py:3386-3395`,
whose own comment states the rule this path violates: "A TERMINAL DIRECTORY IS AUTHORITATIVE".

A partially-executed Set is a NORMAL state (resume after an interrupted run, a child executed alone,
a Set executed over several sessions), so this is not an edge case.

## Scope note

Not specific to `runanalytics`. Any Set with at least one executed child and at least one dependent
of that child reproduces it. `aw agy run` shares the queue-build path and should be checked for the
same defect (host parity).

## Workaround (NO LONGER NEEDED as of the 2026-09-17 fix; the setid selector now works directly)

Select the children directly rather than via the Set selector, so each id6 resolves to a real file:

```sh
aw oc run bzz5e6 lhccjf 5f2h8i 8hald1 aflsz3 6eq3oq mm5p3v ixis0c 9xycbh 5lxvl3
```

Ordering still comes from the runner (dependency depth is the first sort key), and including
`5lxvl3` lets the orchestrator retire once its children are `executed`, spending no agent turn.

## Fix sketch (SUPERSEDED by the implementation below; kept for the record)

1. In the Set/orchestrator expansion path, join every declared child id6 to `manifest["plans"][id6]`
   and carry `file` + `status` from it. Never synthesize a status for an id6 the manifest knows.
2. Fail closed and LOUDLY on a declared child that discovery cannot resolve, rather than defaulting a
   status. A child row naming an id6 that does not exist is an authoring error worth naming; silently
   defaulting it to `reviewed` converts that error into a whole-Set block with a misleading reason.
3. Regression test: a Set fixture whose Order 01 is in `executed/` and whose Order 02 depends on it
   must dispatch Order 02 (assert NOT `dependency-blocked`), on BOTH hosts.
4. While here, check whether the `action`/`status` pairing shown in the summary table can disagree
   (`action: execute` + `status: reviewed` was displayed for an executed plan); if the queue entry is
   correct this display inconsistency should disappear, but assert it.

Items 1 and 2 are MOOT: nothing is synthesized and no id6 goes unresolved, so there was no
default-when-unresolved to remove. Item 3 was the right test and is implemented. Item 4 is answered
below.

## Fix as implemented (2026-09-17)

One shared helper, `runner_shared.initial_queue_status`, called from both hosts in place of the
inlined allowlist, so a future status addition lands in one place and cannot desync the two runners.

DELIBERATELY NARROW: `executed` is preserved and NO other terminal status is. A status is only safe to
write onto a queue entry if BOTH vocabularies admit it: the drivers' `TERMINAL_STATES` (or the cascade
cannot act on it) and `runner_shutdown.KNOWN_ITEM_STATUSES` (or Phase 0's R3 ledger-coherence check
calls the run "in an undefined state" and REFUSES ITS OWN RESUME). Measured: `executed` is in both,
while `superseded` and `not-executed` are in NEITHER. Preserving those two would have traded this
cascade bug for a resume-refusing ledger, so they keep falling back to `reviewed`, which already gives
the correct OUTCOME (both are non-success, so a dependent still refuses to run). This was caught by the
regression test rather than by inspection.

Also fixed incidentally: the one live plan carrying the upper-case `EXECUTED` form (`vfa1tl`) now
normalizes correctly, because the helper case-folds and strips.

ITEM 4, ANSWERED: `action` and `status` CAN still differ on an executed entry (`action: execute`,
`status: executed`). That is harmless and was left alone: `action` is frozen for RESUME so a resumed run
re-derives the same dispatch, and the selection loop admits only `status == "queued"`, so an executed
entry is never dispatched. The misleading part was `status`, which is now truthful.

Verification: `7825 passed, 3 skipped, 2 xfailed` (baseline before the change: 7819 passed; +6 new
tests). The originally failing selector `aw oc run lanectn integpath mergedirty` now blocks NOTHING and
admits exactly the 6 live plans, with the 9 executed ones present-but-never-dispatched.
