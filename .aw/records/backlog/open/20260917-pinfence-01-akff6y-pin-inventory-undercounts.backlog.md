- Id: akff6y
- Status: open
- Set: pinfence
- Priority: low
- Work-Kind: followup
- Summary: A plan's Scope-Paths pin inventory was short in 3 of 4 rununify split children, so a real split would be refused at finalize

## Workflow history
- 2026-09-17 created (aw backlog): A plan's Scope-Paths pin inventory was short in 3 of 4 rununify split children, so a real split would be refused at finalize

## What is wrong

A plan that relocates a function must declare every test file that reads that function's SOURCE TEXT
in `- Scope-Paths:`, because such a pin BREAKS on relocation and must be re-based in the same change.
The `Scope-Paths` fence is what makes the runner's finalize gate able to tell an out-of-scope edit from
a declared one.

In THREE of the four `rununify` split children the fence was short, each discovered only by running a
scanner at execution time:

* `yrqyxb` (Order 07, `execute_item`): three undeclared pin files.
* `ty3cj6` (Order 08, `run_queue`): the review counted six pins, measurement found 10 sites across 9
  files; every file was fenced except the two negative shim pins.
* `orziju` (Order 09, `initialize_run`): the review counted 11 pins across 3 files, measurement found
  **14 sites across 6 files**. `tests/test_lane_clean_base.py:627` was NOT declared.

None of the three actually tripped the gate, because all three plans were re-scoped at review to
measure rather than split, so no test file needed editing. A plan that DID perform its split would have
been refused at finalize, or would have had to justify an out-of-scope edit after the fact.

## Why the review round missed them

The counts were derived by reading and grepping, and both under-count for a structural reason: a test
can reach a function's source FOUR ways, and a grep for `getsource` finds only one of them. The four
are `inspect.getsource(mod.f)`, an AST lookup by function name (`node.name == "f"`), a
`src.split("def f")` fence, and a bare `"def f"` string literal (typically a NEGATIVE assertion that a
shim contains no runner logic). `orziju`'s scanner finds all four and de-duplicates sites two detectors
both see; that is what took 11 to 14.

## What would fix it

A reusable scanner rather than a per-plan one. Each of the three children wrote its own throwaway
`pin_scan.py` into a GITIGNORED lane-submission tree, so the next plan writes a fourth. Candidates, in
increasing cost: (1) commit one scanner under `tools/`, (2) make it an `aw` verb (`aw pins <symbol>`),
or (3) have `aw ipd lint` warn when a plan's `Scope-Paths` omits a file whose tests read a symbol the
plan names. Option 3 is the only one that fails closed, and it needs a way to know which symbols a plan
intends to move, which no field currently declares.

## Where

`.aw/records/plans/executed/20260915-rununify-07-yrqyxb-*.ipd.md`,
`.aw/records/plans/executed/20260915-rununify-08-ty3cj6-*.ipd.md`, and plan `orziju`. The
four-detector scanner and the 14-row pin table are in
`.aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md`.
