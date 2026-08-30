- Id: e6b9kt
- Status: done
- Set: runledgerpath
- Priority: high
- Work-Kind: bug
- Summary: aw run ledger resolution claims the runner's events.jsonl and misdiagnoses it as a corrupt ledger

## Workflow history
- 2026-08-29 done (aw set): Fixed in 99111c4: run-id resolution no longer claims events.jsonl (a ledger owns only LEDGER_FILENAME='ledger.jsonl'), and a new NotALedgerError (NOT a LedgerCorruption subclass) gives wrong-format files a distinct verdict on exit code 7 with not_a_ledger:true/corrupted:false. Adversarial tests prove the shape check cannot mask tampering: tampered prev_hash, deleted middle record, and schema-invalid envelope all still raise corruption at both store and CLI boundaries. Full suite: 2865 passed, 3 skipped, 4 xfailed.
- 2026-08-29 created (aw backlog): aw run ledger resolution claims the runner's events.jsonl and misdiagnoses it as a corrupt ledger

Two coupled defects, both reproduced live on this checkout at HEAD 477569a.

DEFECT 1 (filename collision). `run_cli.resolve_ledger_path` (agent_workflows/run_cli.py:181-206) has a
candidate list whose entries 4, 5 and 7 are `<...>/runs/<target>/events.jsonl`. That file EXISTS for
every real driver run, but it is the RUNNER's own event log in a completely different shape
(keys `at`/`event`/`queue`/`run_id`, or `at`/`event`/`id6`), not a hash-chained ledger record
(`schema_version`/`kind`/`seq`/`actor`/`timestamp`/`parent`/`prev_hash`). The ledger claims a filename
it does not own. `ipd_set_plan.py:731` hardcodes the same wrong path.

DEFECT 2 (false corruption diagnosis). Because of defect 1, `aw run show <any-real-run>` finds the
runner's event log, parses it as a ledger, and reports `ledger corruption detected` with eight
findings (RL-E010 x6 for the missing common fields, RL-E013 unknown kind, RL-E015 bad run_id). The
file is HEALTHY and is simply not a ledger. The tool accuses good data of being corrupt.
Wrong-format and corrupt are DIFFERENT diagnoses and must not share a verdict or an exit code.

Reproduction (verified):

    $ python3 -m agent_workflows run show run-20260824T140112Z-2227235
    error: ledger corruption detected: Schema-invalid record at seq 0: (Finding(code='RL-E010', ...

CONTEXT / DIRECTION (maintainer decision, 2026-08-29). The whole run-ledger subsystem is BUILT but
NEVER WIRED: `grep -c ledger agent_workflows/oc_runipd.py` returns 0 and no ledger file exists
anywhere on disk. Wiring it is DEFERRED (it overlaps wtiso Phase 2 rchpms, and spec 25kzda is still
to-review), so both defects are to be fixed DEFENSIVELY now:

  1. Stop claiming `events.jsonl` under any runs dir as a ledger path; a ledger must be an explicit
     path or a real `ledger.jsonl`.
  2. Add a shape check BEFORE the corruption verdict: when the required common envelope fields are
     absent WHOLESALE, report 'not a ledger file' (distinct message and exit code), never 'corrupt'.

An adversarial test must prove the guard fires: a genuinely corrupt ledger (valid envelope, tampered
hash chain) must STILL be reported as corruption, so the new shape check cannot mask real tampering.
