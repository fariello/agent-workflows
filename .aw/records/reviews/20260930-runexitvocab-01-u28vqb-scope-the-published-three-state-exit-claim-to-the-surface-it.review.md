# Review findings: plan u28vqb

- Subject-Id: u28vqb
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (HIGH, fixed), PR-703 (HIGH, fixed), PR-704 (MEDIUM, fixed), PR-705 (MEDIUM, fixed), PR-706 (MEDIUM, fixed), PR-707 (MEDIUM, fixed), PR-708 (MEDIUM, fixed), PR-709 (LOW, fixed), PR-710 (LOW, fixed), PR-711 (LOW, fixed), PR-712 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and unmodified before editing
(`git status --porcelain` empty on the whole tree), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with NO advisories of any
kind. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row
check does not apply. No production file, test, document or spec was modified by this review.

THE PLAN'S CENTRAL CASE IS CONFIRMED SOUND AND NO E-ITEM'S PURPOSE CHANGED. Every load-bearing
measurement was re-driven independently rather than read back, and the central ones reproduce:

```
total 163
out-of-range count 8
  ipd execute-set (0, 1, 2, 3) check
  run cancel      (0, 5, 6) mutation
  run finalize    (0, 1, 4, 6) mutation
  run record      (0, 2, 3, 5, 6) mutation
  run start       (0, 2, 3, 5, 6) mutation
  runs next       (0, 3) read
  runs resume     (0, 2, 5, 7) read
  runs status     (0, 1, 3, 5) read
CommandDeclaration.exit_contract default = (0, 1, 2)

oc runipd (0, 1, 2)        agy runipd (0, 1, 2)

needs_approval True   initial reviewed
entry {'path': 'x.ipd.md', 'status': 'reviewed', 'action': 'execute', 'needs_input': True}
run_exit_code 3
   ... same entry WITHOUT needs_input -> 1          <-- PR-702

exit3 errors: ["Field 'exit' must be an integer in (0, 1, 2), got '3'"]
exit1 errors: []
render raised ValueError Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2)

oc_runipd.run_queue  returns 2  (line 4053 run_exit_code, line 3518 literal 1)
agy_runipd.run_queue returns 2  (line 3461 run_exit_code, line 3018 literal 1)
oc_runipd.main       returns 15, two of them `return run_queue(...)`, plus `143 if is_sigterm else 130`

agent_record_kind census: Counter({'result': 161, 'raw_path': 1, 'summary': 1})   <-- PR-701
  all 8 out-of-range decls are agent_record_kind='result'; so are oc/agy runipd

runs next   <missing ledger> --agent  rc=2  schema=None
runs status <missing ledger> --agent  rc=2  schema=None
ipd lint --agent                      rc=0  schema='aw.agent/v1'

production call sites of deliberate_stop_exit_code: []                            <-- PR-706
  oc_runipd.py 5223 lines, agy_runipd.py 4129 lines (spec cites :7142 / :4233 / :7965)
  called only from 7 test files

EXIT_CODES / gate_failed / compatibility_break tree-wide: 3 hits, all in compat_migration.py
  (definition, __all__ entry, one CompatSurface prose field); test_surface_exit_codes_preserved absent

bare python3 -m pytest: 3872 passed, 2 skipped, 3 warnings in 114.68s             <-- PR-712
  test_release_exempt_setter_roundtrip_and_parity run alone: 1 passed
```

Per-finding against the plan's own Findings table:

- F-01 CONFIRMED: `rwvzqm` is in `pending/` at `- Status: approved` with every `E-*` pending, and
  `docs/cli-output-contract.md:164` still reads "The CLI enforces a uniform three-state exit
  classification across all verbs". No stopgap is in force.
- F-02 CONFIRMED: `runs resume` is `(0, 2, 5, 7)`, `command_class="read"`.
- F-03 CONFIRMED as to existence and the quoted comment, but NARROWED by PR-709/F-16: the table has
  zero consumers.
- F-04 REPRODUCES exactly: 163 total, exactly 8 out of range, same tuples and classes, same default.
- F-05 CONFIRMED in both halves: both pinning test files exist and assert what the plan says
  (`EXIT_CORRUPTED_LEDGER` across six `aw runs` leaves; the real CLI driven for 0/2/5/7 plus the
  negative `3 not in decl.exit_contract`), and `6kwd2e` R7.3 and A38 read verbatim as quoted.
- F-06 REPRODUCES and is strengthened: the 3 is real, the path is unclamped, and BOTH production
  sites that set the `needs_input` flag were located (the queue-build append via
  `item_needs_approval`, and the spec-artifact branch on a `reviewed` spec turn). Also bounded:
  `run_exit_code` passes neither `run_wide_abort_class` nor `interrupted`, so 4 and 130 are NOT
  reachable through `run_queue`.
- F-07 CONFIRMED as to the two comments and the three prose-only `agent_schema` hits in `run_cli`
  (both drivers match zero times), but see PR-701: the boundary must be worded as EMISSION.
- F-08 REPRODUCES on real calls.
- F-09 CONFIRMED with one correction: the `docs/` grep matches `docs/README.md`, not the root
  `README.md`, so it is five documents counting the root one separately.
- F-10 CONFIRMED and EXTENDED by PR-706.
- F-11 CONFIRMED with both statuses now stale (`69rdv6` is `approved`; `1mnit8` is `reviewed` with
  `- Readiness: go-pending-approval`).
- F-12 NOT REPRODUCIBLE; corrected by PR-712.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | G (executability), A (correctness) | `agent_workflows/command_surface.py:29` (`CommandDeclaration.agent_record_kind`), the per-kind census, `tests/conformance_matrix.py:163` (`EXEMPTION_REGISTRY`), `tests/test_agent_surface_conformance.py:32` (`compute_conformance_universe`) | E-03 was told to draw the published boundary at the "`aw.agent/v1` record format" while F-07 cites `command_surface` as already stating it, and the field that appears to report it, `agent_record_kind`, does NOT: 161 of 163 declarations set it to `"result"`, including all eight out-of-range verbs and both `oc runipd`/`agy runipd`. A sentence keyed on that field would assert in the same document that every listed exception is capped at `{0,1,2}`. The boundary is the record a verb EMITS, which is directly observable (bare `{"error":...,"exit_code":2,"ok":false}` with no `schema` key from `runs next --agent`, versus `schema: aw.agent/v1` from `ipd lint --agent`) and already encoded as an exemption reason ("Emits `schema_version: 1` execution manifest rather than `aw.agent/v1` envelope") | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies emission as the boundary, forbids citing `agent_record_kind`, and names `run_cli._emit_error` as the counter-example; new F-13 records the measurement; V-03 adds a grep proving the field is not cited; the Concern and OQ-01 both record the narrowing |
| PR-702 | HIGH | IN-SCOPE | E (verification), G | `agent_workflows/runner_shared.py:26689` (the gate clause in `aggregated_run_items`), `:26394` (`NEEDS_INPUT_KEY`), `:28287` (the queue-build append) | E-01's probe as written does not reproduce the 3 it gates on. `aggregated_run_items` reads `entry.get(NEEDS_INPUT_KEY)` off the entry rather than re-deriving it, so `{"status": "reviewed", "action": "execute"}` returns 1 and only the flagged entry returns 3. E-01 named `item_needs_approval` and `initial_queue_status` but not the flag they feed, so a literal executor measures 1, reads "a returned code other than `3` must be reconciled", and stops a correct plan at its first item | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now specifies the production entry shape (all three keys, built from the same predicates the queue builder uses) and states explicitly that a flagless 1 is an invalid probe and NOT a falsification; V-01 and the EXECUTION CONTRACT carry the same correction; new F-18 records it |
| PR-703 | HIGH | IN-SCOPE | G (executability) | the plan's E-03, E-04 and E-05 read against each other; `docs/cli-output-contract.md` heading census; the plan's `- Scope-Paths:` | E-05's destination was unspecified ("the user-facing documentation") while E-04 requires every other document to "point at the one place E-05 writes it" and E-03 to name where the wider vocabulary is documented. An executor would have had to invent the destination after writing the pointers to it, and a new file would also have fallen outside the declared fence | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Resolved (D-1) to a new `### 3.1` of `docs/cli-output-contract.md`, with the reasons stated in E-05: normative home, already in the fence, existing `### N.N` convention at 1.1/1.2/1.3/9.1/11.1, stable anchor for the pointers, no new file. New F-15 records it; E-03/E-04/V-04/V-05 and OQ-02's trigger all now name the anchor |
| PR-704 | MEDIUM | UNDER-SCOPE | G, F (honest documentation) | `docs/cli-migration.md:127` ("Confirm the exit codes your script branches on still mean the same thing: `0` clean, `1` findings, `2` cannot run. That classification did not change.") | A fifth document publishes the identical false uniformity claim, to the reader with the most at stake (someone wiring a script against the codes). The plan's own F-09 lists the file among the grep matches while E-04 omits it, which is exactly the defect E-04's own rationale forbids leaving on another surface | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 extended to `docs/cli-migration.md` with the specific bullet named; `- Scope-Paths:` and the Scope line updated; V-04 adds the confirming grep; new F-14 records it |
| PR-705 | MEDIUM | IN-SCOPE | G (scope fence) | the plan's E-07 ("`run_evidence.py`'s comment ... is corrected to name this plan") against its `- Scope-Paths:` | E-07 names an edit to `agent_workflows/run_evidence.py` that the fence did not declare. `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path, so the execution would have hit a reconciliation refusal for an edit the plan deliberately intended | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `agent_workflows/run_evidence.py` added to `- Scope-Paths:`; the spec-sync section records why it is declared |
| PR-706 | MEDIUM | IN-SCOPE | A (correctness), D | spec `25kzda` 5.6 row 4 and the 130 row; AST walk over `agent_workflows/*.py` for `deliberate_stop_exit_code` returning `[]`; `wc -l` on both drivers; the two `run_exit_code` probes | E-07 would have refreshed citation offsets while preserving two further false statements in the same text. (a) Row 4 says "The drivers themselves return only `0`/`2`/`130`/`143` today (`oc_runipd.main`)", which directly contradicts E-02's measured 3 and would ship a spec disagreeing with the declaration the same plan corrects. (b) The 130 row says `deliberate_stop_exit_code` "is called at `oc_runipd.py:7142` and `agy_runipd.py:4233`", and it is called NOWHERE in production; both offsets are past end of file, and the live deliberate-stop concession runs through `exit_code_statuses`/`aggregated_run_items` into `aggregate_run_exit` (a queue of `executed`+`queued` returns 0 under `stopped=True`, 1 under `stopped=False`) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 now corrects all three false sub-claims and both dead citations, with the prohibition on altering any code's MEANING kept; V-07 demands the AST and `wc -l` evidence; new F-17 records it; the spec-sync section states why row 4's denial must be fixed in the same change as E-02 |
| PR-707 | MEDIUM | IN-SCOPE | D (anti-regression), E | the plan's E-06 clause (c); `69rdv6` and `1mnit8` target tuples | E-06 correctly rejects a bare count because the census moves, but "every out-of-range declaration is a member of an allowlist" is satisfiable symmetrically, and the natural symmetric implementation (set equality, or "every allowlist key is still out of range") pins the population exactly as the count does. `1mnit8` adds the argparse 2 to four of these and `69rdv6` widens two, so a symmetric assertion re-creates the drift the item was designed to avoid | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now specifies superset-only, keyed on `command`, with no count assertion in any form and a failure message that directs the reader to add a reasoned entry rather than widen the test; V-06 demands a demonstration run under each sibling's tuples; new F-19 records it |
| PR-708 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's `## Approval and execution gate`; `plan-review.md` Step 4; AGENTS.md 2026-09-01 scope-fence ruling | The gate carried the honesty rule, the commit scoping and the never-push, but no SCOPE FENCE declaration, and its lifecycle paragraph said only "through the tooled transition" without naming `aw ipd finalize` or the conditional runner/executor ownership. It also asserted the runner would set `858lhj` to `graduated`, which is already its status | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE as a DECLARATION (not a stop directive), naming the nine paths, the `--scope-reason`/`--scope-ack` reconciliation, the two likeliest ack candidates, and keeping the two genuine stop conditions; POST-GATE LIFECYCLE now names `aw ipd finalize` with conditional ownership, forbids a hand `git mv` and a hand `- Status:` edit, and records that `858lhj` is already `graduated` so no transition is owed |
| PR-709 | LOW | IN-SCOPE | F (honest documentation) | tree-wide grep for `EXIT_CODES`/`gate_failed`/`compatibility_break` returning 3 hits all inside `compat_migration.py`; `test_surface_exit_codes_preserved` absent from `tests/` | F-03 treats `compat_migration.EXIT_CODES` as a third table and E-05 would have published it to operators with a row for `3` and `4`. It has ZERO consumers anywhere, its comment's claim that "a machine consumer imports these" is false, and the test its own compat surface names as its pin does not exist. Publishing it would document codes no `aw` verb can return, in the document being fixed for publishing a false claim | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now forbids an operator-facing row for it and permits naming it only as an unconsumed internal constant with that fact stated; OQ-01 and the renumbering deferral demote it to a supporting reason with the two live test files carrying the refusal; new F-16 records it, and a new deferral row records the residual compat-surface defect with an explicit Carrier-Declined rationale |
| PR-710 | LOW | IN-SCOPE | G (live-artifact criteria) | `command_surface.py:80` ("All 78 leaves"); the plan's "155 of 163"; `69rdv6` and `1mnit8` front matter; measured 163 declarations against 152 parser leaves with 0 undeclared | Three live counts were stale or will rot. E-07 would have replaced `All 78 leaves` with a single measured number while the comment conflates declarations with parser leaves, so one wrong count becomes another. The "155 of 163" validated-against-nothing figure is exactly the population `1mnit8` changes. Both sibling statuses had advanced since authoring | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 must now distinguish the two numbers (163 declarations, 152 parser leaves, 0 undeclared); the "155 of 163" and the "155 that declare the plain `(0,1,2)` default" dropped as live counts with the reason stated; F-11 and both deferral rows refreshed to `approved`/`reviewed` |
| PR-711 | LOW | IN-SCOPE | A, D | the plan's E-02 ("include the reachable exit `3`"); `1mnit8`'s never-narrow rule | E-02 did not state whether `3` is ADDED to `(0,1,2)` or substituted, and the nearest precedent (`ck0vya`, which changed `(0,3)` to `(0,2,5,7)`) both added and removed. An executor writing `(0,3)` or `(3,)` would narrow a correct tuple, which is the defect `1mnit8`'s review found in its own sibling | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now specifies `(0, 1, 2, 3)` on each as a pure widening and says so explicitly; V-02 adds the never-narrow check that 0, 1 and 2 are all still present; F-11 records that the widening is what keeps the three plans order-independent |
| PR-712 | LOW | IN-SCOPE | E (verification bar) | bare `python3 -m pytest` at review HEAD; `tests/test_backlog.py` `_DATE` normalization and the `fnb8pl` comment | The F-12 baseline is not reproducible and V-07 compares against it as a constant. The tree is fully green at `3872 passed, 2 skipped` against an authored `1 failed, 3457 passed`, a 415-test drift in one day, and the authored "pre-existing date-rollover failure" PASSES: that test normalizes every history date before comparing and records the clock skew as live bug `fnb8pl` rather than asserting a literal date. So V-07 would have compared against a count that cannot recur AND excused a failure that no longer exists | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 rewritten with both observations and the drift stated; V-07 and the Required tests section now compare the FAILURE SET by node id against an empty set, treat the pass count as informational, forbid every count constant, and require any claimed pre-existing failure to be shown reproducing on an unmodified tree |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-05 must write the run-exit vocabulary somewhere, and E-03/E-04 both promise to point at that place, but the plan never names it. Where does it go? | A new `### 3.1` subsection of `docs/cli-output-contract.md`, directly under the Section 3 text E-03 amends. | (a) A new standalone `docs/exit-codes.md`, rejected because it falls outside the declared `- Scope-Paths:` (so finalize would demand a scope reason for the plan's own central deliverable), and because it separates the exception from the rule it is an exception to, which is how the two drifted in the first place; (b) `docs/recovery.md` or `docs/troubleshooting.md`, rejected because the plan's own F-09 measures those as stating no exit code at all, so neither is the normative home and a reader looking for the contract would not find it there; (c) leave it to the executor, rejected because E-04's pointers must name a target BEFORE E-05 writes it, so an unspecified destination is not a free choice but an ordering contradiction. | `docs/cli-output-contract.md` is the normative exit-contract home (`docs/README.md:29` describes it as covering "exit codes"); its heading census already uses `### N.N` at 1.1, 1.2, 1.3, 9.1, 11.1, 11.2, 11.3, 11.4; the file is already in the plan's `- Scope-Paths:`; `grep -rln "exit code" docs/` already matches it, so V-05's closing check is satisfiable without a new file. Recorded as F-15. | yes |
