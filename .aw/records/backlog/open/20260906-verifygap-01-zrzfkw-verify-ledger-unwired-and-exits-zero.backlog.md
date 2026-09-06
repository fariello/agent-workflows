- Id: zrzfkw
- Status: open
- Set: verifygap
- Priority: medium
- Work-Kind: bug
- Summary: aw runs verify-ledger reads a ledger.jsonl that no driver run writes, and exits 0 when it is absent, so it silently reassures instead of verifying

## Workflow history
- 2026-09-06 created (aw backlog): aw runs verify-ledger reads a ledger.jsonl that no driver run writes, and exits 0 when it is absent, so it silently reassures instead of verifying

TWO DEFECTS, one of which is a false reassurance.

DEFECT 1: THE FILE IT READS IS NEVER WRITTEN. `_run_verify_ledger` (`run_cli.py:502`) resolves a
target to `store.LEDGER_FILENAME` (`ledger.jsonl`), verifies its SHA-256 hash chain, then validates
recorded evidence and completion predicates. Measured 2026-09-05:
`find .aw/records/runs -name 'ledger.jsonl'` returns ZERO results across all 100 run directories.
No driver run has ever written one. Spec `25kzda`'s own header already concedes it: "the ledger is
built but UNWIRED".

DEFECT 2: IT EXITS 0 WHEN THE LEDGER IS ABSENT. Measured:

    $ aw runs verify-ledger run-20260905T211011Z-3780617
    error: ledger file not found for target 'run-20260905T211011Z-3780617'
    EXIT: 0

An error printed on a success exit is invisible to any script or CI step that checks the exit code.
Note the function itself `return 2` on that path (`run_cli.py:518`), so the nonzero is being lost
somewhere between the leaf and the process exit; find where rather than assuming the leaf is wrong.

WHAT IT WOULD DO IF THE LEDGER EXISTED, stated so nobody over-reads its name: it is a pure DATA
INTEGRITY check. It verifies hash chaining, evidence validity, and completion predicates over recorded
JSONL. It runs NO agent, executes NO tests, and reads none of the repository's actual source. It
cannot tell you whether the work was correct; only whether the record of it is internally consistent
and untampered.

A NAMING TRAP WORTH FIXING WITH IT (this misled an agent twice in one session): "ledger" names two
unrelated substrates. The DRIVERS say "ledger" 13 times in `oc_runipd.py` meaning
`events.jsonl` - the runner's own append-only event log, which DOES exist and works (see the
LEDGER-FIRST comment at `:1506`). `verify-ledger` means the hash-chained `ledger.jsonl` owned by
`run_ledger_store`, which nothing writes. `resolve_ledger_path` already refuses to conflate them
and cites a prior bug (`e6b9kt`) where doing so made healthy runs report as corrupt
(`run_cli.py:236-239`). Consider renaming one of the two in prose, or at minimum saying in
`--help` which file the command reads.

THE FIX, in order of value:
  1. Make the absent-ledger path exit NONZERO and say plainly that driver runs do not currently write
     a ledger, so the operator knows the answer is "cannot verify", not "nothing wrong".
  2. Decide whether the drivers SHOULD write a ledger. That is the larger question and it is
     genuinely open: the hash-chained ledger plus `AW-Run:`/`AW-Item:` commit trailers is the
     substrate spec `25kzda` assumes throughout Section 4.2, and backlog `a8eufb` records that the
     trailers exist but nothing writes them either. If the answer is no, the honest move is to say so
     in the spec rather than leave a command that cannot work.
  3. Clarify the two senses of "ledger".

Item 1 is worth doing on its own and does not depend on 2. Related: `6kq1lj` covers the sibling
fail-open where an unrecognized `aw runs` leaf degrades into a target search and also exits 0.
