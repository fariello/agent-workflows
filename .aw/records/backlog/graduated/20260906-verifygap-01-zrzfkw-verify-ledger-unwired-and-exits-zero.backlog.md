- Id: zrzfkw
- Status: graduated
- Set: verifygap
- Priority: medium
- Work-Kind: bug
- Summary: aw runs verify-ledger reads a ledger.jsonl that no driver run writes, and exits 0 when it is absent, so it silently reassures instead of verifying

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan i1hlgx (ledgerhonest-01), NARROWED to fix #1 plus the unfinished remainder of fix #3. DEFECT 2 IS DEAD by the item's own 2026-09-06 correction and was re-verified independently unpiped: exit is 2, not 0 (run_cli.py:512-518), so there is no lost-nonzero bug and the instruction to hunt one is not carried forward. DEFECT 1 SURVIVES, re-measured three ways: no ledger.jsonl anywhere, zero run_ledger_store references in EITHER driver, and spec 25kzda:29 still conceding 'the ledger is built but UNWIRED'; sibling plan 8hald1's review independently measured it absent from all 135 real runs. FIX #3 IS PARTLY OBSOLETE: the item asks 'at minimum' for a --help note naming the file read, and the help ALREADY says a run id resolves only to a ledger.jsonl and that events.jsonl differs, so only the REFUSAL MESSAGE remains; the drivers' 13 'ledger' mentions were re-counted as exactly 13. FIX #2 EXCLUDED as a design question, which approved plan 7wei1o independently reached, naming it 'the remaining half of backlog zrzfkw' and out of its own scope. CONSTRAINT DISCOVERED: 7wei1o E-02 cites verify-ledger's absent-path exit 2 as the precedent it aligns its own refusal with, so the exit code must NOT change. No Blocks-Release on the item, so none inherited.
- 2026-09-06 set (aw backlog): CORRECTION 2026-09-06: DEFECT 2 AS FILED WAS FALSE, and the error was mine. The item claimed 'aw runs verify-ledger exits 0 when the ledger is absent'. It does NOT. Re-measured without a shell pipe: 'aw runs verify-ledger <run-id>' prints 'error: ledger file not found' and exits 2, exactly as the leaf's 'return 2' at run_cli.py:518 intends. My original measurement piped the command through 'head', so the '$?' I read was head's exit status, not the command's; a piped exit status reports the LAST stage of the pipeline. There is no lost-nonzero plumbing bug and nothing to hunt for. The instruction in this item to 'find where the nonzero is lost between leaf and process exit' should be disregarded. DEFECT 1 IS UNAFFECTED AND REMAINS TRUE, re-verified: 'find . -name ledger.jsonl' returns ZERO results anywhere in the repository, so no driver run has ever written the file this command reads, and spec 25kzda's header still concedes 'the ledger is built but UNWIRED'. So the command is honest about failing; it is simply unable to verify a driver run at all, which is a wiring question rather than a fail-open one, and that lowers this item's urgency considerably. THE GENUINE FAIL-OPEN IS THE SIBLING ITEM, not this one: 'aw runs verify <run-id>' (no such leaf) really does exit 0 having verified nothing, re-measured without a pipe. That is tracked in 6kq1lj, which is correctly filed as high and release-blocking. The naming-trap observation in this item (two unrelated substrates both called 'ledger') also stands unchanged.

PARTIAL OBSOLESCENCE RECORDED 2026-09-08 AT GRADUATION. Graduated to plan `i1hlgx` (`ledgerhonest-01`),
NARROWED to fix #1 plus the unfinished remainder of fix #3.

DEFECT 2 IS DEAD BY THIS ITEM'S OWN CORRECTION, and it was re-verified independently rather than taken on
trust: `aw runs verify-ledger <run> >/dev/null 2>&1; echo $?` prints `2` at HEAD, exactly as
`_run_verify_ledger`'s `return 2` intends (`run_cli.py:512-518`). There is no lost-nonzero plumbing bug, and
the instruction in the body below to "find where the nonzero is lost" is NOT carried into the plan.

DEFECT 1 SURVIVES and was re-measured three ways: no `ledger.jsonl` exists anywhere in the repository; zero
`run_ledger_store`/`RunLedgerStore` references in EITHER driver (`grep -c` -> 0 and 0); and spec `25kzda:29`
still concedes "the ledger is built but UNWIRED". Independently corroborated by sibling plan `8hald1`'s
review, which measured `ledger.jsonl` present in ZERO of 135 real run directories and marked the ledger
adapter fixture-only.

FIX #3 IS PARTLY OBSOLETE: this item asks for, "at minimum", a `--help` note saying which file the command
reads. THAT IS ALREADY SHIPPED. The target's help text states "NOTE: a run id resolves only to a
ledger.jsonl; the drivers' own events.jsonl is a different format." So only the REFUSAL MESSAGE still lacks
the disambiguation, and that is where an operator actually meets the confusion. The drivers' "ledger"
mentions were re-counted and are exactly 13 as stated.

FIX #2 IS EXCLUDED FROM THE PLAN as a design question, not deferred by preference: whether the drivers
SHOULD write a ledger is entangled with the `AW-Run:`/`AW-Item:` trailers (which `a8eufb`, now plan
`wao266`, records as built but unwritten) and with spec `25kzda` Section 4.2's assumptions throughout.
APPROVED plan `7wei1o` independently drew the same line, naming "whether driver runs should WRITE a
`ledger.jsonl` at all" as "the remaining half of backlog `zrzfkw` and a genuine design question", explicitly
outside its scope. This item's own text agrees that fix #1 "is worth doing on its own and does not depend
on 2".

ONE CONSTRAINT DISCOVERED THAT THE PLAN MUST HONOR: approved plan `7wei1o` E-02 cites `aw runs
verify-ledger <absent>` exiting 2 as the precedent it aligns ITS new refusal with. So the exit code must NOT
change, or an approved plan's reference point moves under it.

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
