- Id: cjefq5
- Status: open
- Set: cjefq5
- Priority: high
- Work-Kind: bug
- Summary: aw oc run on a Set with an already-executed child blocks the entire Set: the queue entry gets file=null and status=reviewed instead of the discovered executed status

## Workflow history
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
entry still ended up with `file: null` and `status: "reviewed"`.

The defect is therefore in the path that expands a SET SELECTOR (or the orchestrator's child table)
into queue items: it appears to synthesize an entry from the orchestrator's declared child rows
(`ipd_set_plan.parse_child_table`, `:334`; `_parse_orchestrator_child_table`, `:413`) instead of
joining each declared child to its discovered record by id6. A synthesized entry has no path, hence
`file: null`, and takes a default status rather than the real one.

Compare `oc_runipd.py:2866` (`st = st or "approved"`), which is the analogous
default-when-unresolved in the pre-flight path: the same shape of guess, made where the answer was
already available.

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

## Workaround (verified reasoning, not yet run)

Select the children directly rather than via the Set selector, so each id6 resolves to a real file:

```sh
aw oc run bzz5e6 lhccjf 5f2h8i 8hald1 aflsz3 6eq3oq mm5p3v ixis0c 9xycbh 5lxvl3
```

Ordering still comes from the runner (dependency depth is the first sort key), and including
`5lxvl3` lets the orchestrator retire once its children are `executed`, spending no agent turn.

## Fix sketch

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
