# Review findings: plan 69rdv6

- Subject-Id: 69rdv6
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-501 (HIGH, fixed), PR-502 (MEDIUM, fixed), PR-503 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cad63dc2`. The plan file is committed and unmodified
(`git status --short` empty before edits), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) with two `IPD-Z602` density
advisories on E-03 and E-04; the plan already assesses both in its Scope check and I concur with its
reasoning (E-03's clauses share one fixture set and one red run; E-04's three clauses are three
invocations of one runner over one tree state, not three deliverables). This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

All probe work was done under the gitignored `tmp/` and removed afterwards. No production file and no
test was modified by this review.

THE DESIGN IS CONFIRMED SOUND AND REVIEW CHANGED NO E-ITEM'S INTENT. I re-drove the entire
reachability matrix independently in fresh temp ledgers rather than reading the plan's findings back,
and it reproduces cell for cell:

```
fixture                            next                   status     resume
clean(1rec)          3 No runnable step       1 Run: run-0000abc 0 Run run-
absent               2 error: ledger fi       2 error: ledger fi 2 error: l
empty                2 error: ledger is       2 error: ledger is 2 error: l
notaledger           7 error: not a run       7 error: not a run 7 error: n
chainbreak           5 error: ledger co       5 error: ledger co 5 error: l
term:complete        0 Run run-0000abcd       0 Run: run-0000abc 0 Run run-
term:cancelled       0 Run run-0000abcd       3 Run: run-0000abc 0 Run run-
badflag next: 2 / badflag status: 2

runs next    declared=[0, 3]       measured=[0, 2, 3, 5, 7]    MISSING=[2, 5, 7] OVER=[]
runs status  declared=[0, 1, 3, 5] measured=[0, 1, 2, 3, 5, 7] MISSING=[2, 7]    OVER=[]
runs resume  declared=[0, 2, 5, 7] measured=[0, 2, 5, 7]       MISSING=[]        OVER=[]
```

- F-01 REPRODUCES: both declarations read `(0, 3)` and `(0, 1, 3, 5)` with `command_class="read"`.
- F-02 REPRODUCES by reading every arm. `_resolve_or_error` returns 2 via `_emit_no_target` and
  `_emit_ledger_not_found`; `_build_engine` returns 7 on `NotALedgerError`, 5 on `LedgerCorruption`,
  and 2 on both its `except Exception` catch-all and its `if not records` empty arm. `_run_next` and
  `_run_status` each open with `ledger_file, code = _resolve_or_error(args)` then
  `engine, _records, code = _build_engine(args, ledger_file)`, each forwarding `code` verbatim.
- F-03 REPRODUCES including `resume`'s `MISSING=[] OVER=[]`.
- F-04 IS CONFIRMED AND IS THE PLAN'S SHARPEST CONTRIBUTION. A `terminal_status="complete"` second
  record gives BOTH leaves exit 0; `terminal_status="cancelled"` gives `status` exit 3 (with a
  `Cancellation:` line) while `next` still exits 0, because its terminal arm returns `EXIT_OK` for
  either terminal state. So an executor computing the diff from the backlog item's single-fixture
  matrix really would have DELETED three reachable codes, exactly as the plan warns.
- F-05 REPRODUCES: zero live `.py` importers of `tests/conformance_matrix.py` (only its own definition
  and three `command_surface.py` comments), and `.github/workflows/tests.yml`'s `output-conformance`
  job runs only `tests/test_command_surface_declarations.py`.
- F-07 REPRODUCES AND IS STRONG: `tests/test_run_cli_corruption_exit.py` is green (`8 passed in
  3.22s`) and its `CORRUPTION_CASES` parametrizes `status`, `next` and `resume` over exit 5 while
  `runs next`'s contract omits 5. A passing test already contradicts the declaration.
- F-08 REPRODUCES: `RUNS_VIEWER_LEAF_NAMES` holds exactly the nine named leaves.
- F-09 REPRODUCES: four existing test functions in the declarations file; the two other files reading
  `exit_contract` name neither leaf.
- F-10 REPRODUCES VERBATIM, including that spec `25kzda` Section 5.6's own row 4 says "UNRECONCILED
  CONFLICT, recorded 2026-09-05 rather than silently resolved" and names `run_cli`'s table as the
  shipped one. The plan's refusal to reconcile is correct.
- The convention notes check out: `exit_codes` appears nowhere as an identifier in the tree (the item
  does say "declares (0, 3)" without naming the field), and `run_cli` has three prose mentions of
  `agent_schema` but zero import statements, so `_emit_error`'s docstring claim is literally true.
- `ck0vya`'s F-08 and F-12 independently corroborate the matrix and the fixture-schema trap.

TWO NEW FINDINGS WERE ADDED FROM MEASUREMENT RATHER THAN ARGUMENT, both strengthening the plan:

- F-12: I evaluated `required_scenarios` directly on the before and after declarations for both leaves
  instead of reasoning about the `1 in exit_contract` predicate. `runs next` yields the same seven
  scenarios before and after; `runs status` yields those plus `domain_failure` before and after. Both
  E-items' invariance claims hold mechanically and V-02(e) is satisfiable as written.
- F-13: the exact-set bar is stronger than membership and would fail if any other `run_cli` code were
  reachable, so I checked the two candidates. `EXIT_INVALID_EVIDENCE` (4) and `EXIT_OPERATIONAL` (6)
  appear only in `_run_finalize`/`_run_record`/`_run_cancel` and siblings, never in either handler, and
  neither shared helper can produce them. Both proposed tuples equal their measured set exactly.

ALL THREE FINDINGS CONCERN VALIDATION BARS AN EXECUTOR COULD NOT HAVE MET, which is where this plan's
real risk sat.

PR-501 (HIGH). F-06 claims the tree is "fully green", and E-04/V-04 make "zero failures" the bar. That
is not a property of the tree. At review the bare suite is `1 failed, 3394 passed, 2 skipped`, and the
failure is a MIDNIGHT-BOUNDARY FLAKE in
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`: it
writes two records in sequence and compares their rendered history lines, so it fails when the UTC date
rolls over between the writes (observed `- 2026-09-30 HIST_ACTOR` versus `+ 2026-10-01 HIST_ACTOR` at
00:12Z). The file is unmodified in this lane and outside this plan's `- Scope-Paths:`. The bar is wrong
in the DANGEROUS direction: an executor told "zero failures" will either chase unrelated red or treat a
genuine regression as the known flake. FIXED: F-06 rewritten with the correction; E-04, V-04(a) and the
Required tests bullet now demand a by-NAME before/after failure-set comparison, and V-04(a) tells the
executor to re-run the flake alone and show the date diff before attributing it to the clock.

PR-502 (MEDIUM). E-04 conflates two markers and assumes the slow set is green. `-m slow` collects
**202**, not the 207 the bare run deselects; the other **5** are `-m livecorpus` (202 + 5 = 207), so
`-m slow` does not cover everything the bare run skipped and an executor reconciling 202 against 207
hunts five tests that do not exist. And the slow set carries THREE pre-existing failures (`3 failed,
199 passed, 3402 deselected in 388.72s`): installer deep-cleanup twice and
`test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, whose gap list
is missing subparser descriptions for `config unset`, `conf unset` and six `upgrade-test` leaves. None
touches this plan's scope paths and the run costs about 6.5 minutes. FIXED: new finding F-11; E-04,
V-04(c) and the Required tests bullet now state 202, explain the 5, name all three expected failures so
a FOURTH is recognizable, and apply the same by-name comparison.

PR-503 (MEDIUM). E-03's exit-5 fixture recipe is incomplete in the way that stalls execution. Building
it from the prose alone, review hit `SchemaInvalidRecordError ... (RL-E020 kind 'step_attempt' requires
field 'attempt', RL-E030 attempt state must be one of ['blocked', 'failed', 'performed'])`. The item
does say to "copy their construction", which mitigates it, but it then describes the record in prose
that omits both fields, and a reader following the prose fails. FIXED: E-03 now names both missing
fields with the measured refusal codes and points at the shipped `resume` test's record (`attempt: 1`,
`state: "performed"`, `input_digest`) as the field-for-field authority.

NOTHING WAS DEFERRED and no finding is left OPEN, so no escalation to a `- Blocking: yes` question is
required by Step 4's gate threshold (`review_findings_gate.block_at`, default `HIGH`).

OQ-01 verified correctly `resolved` and genuinely non-blocking: it is a test-organization choice
(per-leaf versus parametrized) with no bearing on what is asserted, its cited precedent is real (the
file does have one test function per leaf), and its premise that the two contracts differ is confirmed
(`status` includes 1, `next` does not).

`aw ipd lint --phase review-finalize --agent` reports `conforming` after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The bare suite has a pre-existing failure the plan claims does not exist. Does that block the plan, or change a bar? | Change the BAR: require a by-name before/after failure-set comparison instead of "zero failures". | (a) Treat it as a blocker and set `no-go`, rejected because the failure is a clock artifact in a file outside this plan's scope and unmodified in this lane, so it says nothing about this plan's correctness; (b) tell the executor to ignore that one test by name, rejected because a hard-coded exemption would mask a genuine future regression in the same test; (c) fix the flake here, rejected as out of scope (this plan's `Scope-Paths` is two files, neither of them `tests/test_backlog.py`). | Bare run at review HEAD `1 failed, 3394 passed`; the narrowed re-run showing `- 2026-09-30` versus `+ 2026-10-01`; `git diff HEAD --name-only` empty; `date -u` 00:12Z. | yes |
| D-2 | Should the plan's `-m slow` instruction be corrected to 202, or widened to cover all 207 the bare run deselects? | Correct to 202 AND tell the executor the other 5 are `livecorpus`, leaving running them optional with an explicit statement either way. | Silently leaving 207, rejected because the executor then cannot reconcile the number and may conclude collection is broken; mandating `-m livecorpus` too, rejected as scope growth for a declaration chore whose two scope paths neither marker's tests touch. | `--collect-only -m slow` -> `202/3604`; `--collect-only -m livecorpus` -> `5/3604`; the bare run's `207 tests were deselected` note. | yes |
| D-3 | Is the plan's exact-set assertion (declared tuple equals measured-reachable set) actually satisfiable, or should it be weakened to membership like the shipped `resume` precedent? | Keep the exact-set bar; it is satisfiable and is the stronger property. | Weakening to membership-only to match the existing `resume` test, rejected because membership passes for an OVER-declared contract too, which is precisely the failure mode F-04 warns about and which the plan's own V-03(c) mutation proof targets. | Symbolic census showing `EXIT_INVALID_EVIDENCE` (4) and `EXIT_OPERATIONAL` (6) absent from both handlers and unproducible by either shared helper; both proposed tuples measured `MISSING=[] OVER=[]`. Recorded as F-13. | yes |
