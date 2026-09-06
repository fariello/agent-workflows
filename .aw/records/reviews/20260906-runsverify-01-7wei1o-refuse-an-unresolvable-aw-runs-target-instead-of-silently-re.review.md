# Review: refuse an unresolvable aw runs target instead of silently reporting success (child 7wei1o, Set runsverify)

- Subject-Id: 7wei1o
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `de26ef00`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review; `--phase review-finalize` conformed after the revisions.

DISCLOSURE: I authored this plan earlier in the same session, so this is a SELF-REVIEW, not an
independent one. I compensated by re-deriving every measurement from scratch rather than trusting the
plan's prose, and by probing the surface in directions the plan did not consider. That second half is
where all four material findings came from, which is itself evidence that self-review is worth less
than an independent pass.

The plan's own claims held up completely: all seven of its exit-code assertions reproduce exactly,
unpiped, at `de26ef00`. That is unusual and worth stating plainly, because the interesting findings are
not corrections of what it said. They are things it did not look at: the test that already pins the old
behavior, the resolver that makes the refusal unreachable for common tokens, the mutating sibling with
the identical bug, and the machine renderer that automation actually reads.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression; G. executability | `tests/test_run_noun_split.py:280-284` | An EXISTING SHIPPED TEST asserts the exact behavior this plan removes, and its module was NOT in `Scope-Paths`. `test_leaf_name_as_viewer_target_is_reachable_via_the_escape_hatch` ends `_cli("runs","--dir",...,"--","no-such-target-xyz")` then `assertEqual(rc, 0)` and `assertIn("no matching runs found", out)`. Landing E-02/E-04 turns it red, and the executor would have hit a failing suite on a file it was fenced out of, forcing an unplanned scope decision mid-execution at exactly the moment it is least equipped to make one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_run_noun_split.py` to `Scope-Paths` and added E-06/V-06 to re-point the assertion to the new contract rather than delete the case (it is the escape hatch's only unresolvable-token coverage). Added F-8 and a gate warning |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness; F. prevent silent failure | `run_viewer.py:1141-1152` | The resolver's `state.json` fallback is `if f'"{t_str}"' in content`, a raw substring test over the WHOLE file rather than a setid lookup, so any quoted JSON key or value resolves. Measured over 106 records: `status`/`run`/`opencode`/`driver`/`run_id`/`options` -> 106, `clean` -> 105, `main` -> 96, `json` -> 79, `execute` -> 53, `approved` -> 46, `verified` -> 13. Every one of those tokens would be SILENTLY EXEMPTED from the new refusal, so the plan as written would ship a refusal that does not fire for a large class of plausible mistypes. That is the same fail-open one layer down | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-07/V-07 narrowing the fallback to the parsed setid field (`RunSummary.setids`, `:108`, `:916`), with V-07 requiring a before/after count table AND proof that `lanectn` (3), `runnernorm` (7) and `2367239` (1) are unchanged. Added F-9; noted in Scope and in E-04 that the mixed case cannot be judged before E-07 lands |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness; B. safety of a mutating verb | `run_viewer.py:2418-2429` | The identical fail-open exists on `repair`, the ONE MUTATING verb on this surface, and is worse: `for run_dir in resolve_target_runs(...)` simply never enters its body, so `aw runs repair totalgibberish` exits 0 having printed ZERO bytes (measured unpiped). The no-target case two lines above is already correct (error + exit 2), so this is an internal inconsistency in one function, inside the plan's fence, that the plan did not notice while fixing the read path beside it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-08/V-08 routing the unresolvable case through the same refusal, with V-08 requiring all three `repair` shapes measured and confirmation that no write occurred on the refused path. Added F-10 |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness; E. testing | `run_viewer.py:2538-2543` | The empty-state has a MACHINE branch that returns `{"runs": []}` and exit 0 for `--agent`/`--json` BEFORE the human line, and that is the branch automation reads. E-02 specified only a stderr message, so a literal execution would have left the fail-open exactly where it does the most damage: a script checking `$?` or parsing the record still sees success | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the refusal in all THREE renderers and an `aw.agent/v1` record carrying the nonzero `exit` (`agent_schema.py:21`), because the conformance matrix asserts agent `exit` agrees with the process code. E-05/V-05 extended to cover all three. Added F-11 |
| PR-005 | MEDIUM | IN-SCOPE | E. testing; environment | `tests/test_run_viewer.py:1-30`; `.aw/worktrees/5942n7` | The plan told the executor to validate in the real checkout but did not forbid adding a LIVE-RECORDS test, and the runner allocates an isolated worktree BY DEFAULT where `.aw/records/runs/` is empty. Re-measured: `46 passed` in the real checkout versus `14 failed, 32 passed` in a lane worktree. A new refusal test keyed to live records would pass for the executor and fail in CI and in every lane. The plan's own stale count (14/42) also predated the module growing to 46 tests | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now mandates a fixture repo and cites the module header's own prohibition; V-05 additionally requires the new tests GREEN in a bare worktree as positive evidence. Counts corrected to 46 / 14+32. Added F-12 and a fourth gate warning |
| PR-006 | MEDIUM | IN-SCOPE | E. testing; G. executability | `tests/test_cli_conformance_matrix.py:46`; `pyproject.toml:169` | `tests/test_cli_conformance_matrix.py` was named as a required validation target and is in `Scope-Paths`, but it is marked `pytest.mark.slow` and `addopts` filters `-m 'not slow'`, so the bare suite the execution contract mandates SKIPS it entirely (measured: `no tests ran`). The executor would have pasted a green bare run as evidence for a module that never executed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions and Required-tests now state the marker interaction and require `-m ''` if that module is touched; V-05 requires the explicit run |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy; C. architecture | `command_surface.py`; `discover_parser_leaves` | The plan implied `tests/test_cli_conformance_matrix.py` would guard the change. It cannot: `aw runs` is NOT a declared parser leaf (`discover_parser_leaves(_build_parser())` returns the nine `runs <leaf>` entries and no bare `runs`), so the viewer carries no `CommandDeclaration` and no `exit_contract`. Good news for the change (no declared contract is violated by a new nonzero) and bad news for the evidence (that module will not catch a viewer regression) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as a conventions note stating both halves, so the executor does not mistake a green matrix run for viewer coverage |
| PR-008 | LOW | IN-SCOPE | Spec sync; scope fence | plan "Spec / documentation sync"; spec `25kzda:47`, `:49` | The plan required editing spec `25kzda`'s header note but that file is not in `Scope-Paths`, leaving an unflagged fence decision. Separately the `runs` epilog (`cli.py:1668-1672`) advertises only three leaves, so a leaf-naming refusal message could disagree with the help text | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named the exact spec lines, stated the deliberate out-of-fence handling (make the edit, justify with `--scope-reason` at finalize, do not widen the fence), and required both places to read `_RUNS_VIEWER_LEAVES` rather than a second hardcoded copy |

No finding was DEFERRED, left OPEN, or marked REPLAN. PR-001 and PR-002 are HIGH but both were FIXED,
so no escalation to a `- Blocking: yes` question was required
(`check.review-finding-unescalated` applies only to a HIGH left OPEN or DEFERRED).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-002: is narrowing the resolver in scope for a plan about refusing unresolvable targets, or is it a separate concern? | IN SCOPE, as E-07, and sequenced before the mixed-case judgement. | A separate plan, REJECTED: the two are not merely related, the second DEFEATS the first. A refusal that never fires for `status`, `run`, `main`, `clean` or `execute` is a cosmetic fix, and shipping it alone would let the Set close its backlog item while the fail-open persists for the most likely mistypes. Leaving it to the executor to notice, REJECTED because the plan's E-01/E-02 read as complete. | `run_viewer.py:1148`; measured counts 106/105/96/79/53/46/13 at `de26ef00`; backlog `6kq1lj` lines 45-51 (the fix direction is "does not resolve to any run") | yes |
| D-2 | PR-002: prescribe the new matching rule, or require evidence? | Named the field to match (`RunSummary.setids`) but required a before/after count table rather than dictating the implementation. | Prescribing exact code, REJECTED as premature for a resolver with three fallback tiers. Requiring only "narrow it", REJECTED as untestable: without the paired unchanged-setid evidence, a narrowing that breaks `lanectn` would pass. | `run_viewer.py:108`, `:916`; `tests/test_run_viewer.py:63-69`; `plan-review.md:456-464` | yes |
| D-3 | PR-001: re-point the existing assertion, or delete the test case? | Re-point it to the new contract, explicitly forbidding deletion. | Deleting the case, REJECTED: it is the escape hatch's ONLY unresolvable-token coverage, so deleting it would remove the regression guard for the interaction most likely to break (hatch plus refusal). | `tests/test_run_noun_split.py:280-284`; `plan-review.md:449-454` (do not freeze or drop coverage) | yes |
| D-4 | PR-003: is `repair` a separate sweep (the plan explicitly defers "auditing every other verb")? | IN SCOPE, as E-08. | Deferring it with the sweep, REJECTED on two grounds: it is in the SAME FUNCTION the plan already edits, not another verb, and it is the only MUTATING path on the surface, where silence about a no-op is most dangerous. The deferral of a repo-wide sweep stands and was left intact. | `run_viewer.py:2418-2429`; plan "Deferred / out of scope" (the sweep, which remains deferred) | yes |
| D-5 | PR-004: what exit code for the machine renderers, and what record shape? | Exit 2 (`EXIT_INVALID_INVOCATION`) in all three renderers, with a conformant `aw.agent/v1` record carrying the nonzero `exit`. | A bare `{"runs": [], "exit": 2}`, REJECTED: the conformance matrix asserts the agent summary `exit` agrees with the process return code, so an ad-hoc shape risks failing a contract the repo already enforces. A new exit code, REJECTED per the plan's own reasoning (reuse the shipped vocabulary). | `run_cli.py:58`; `agent_schema.py:21`; `tests/test_cli_conformance_matrix.py:9-10` | yes |
| D-6 | Should the four new E-items be split into a second child plan? | No. Kept as one plan of eight E-items, with the cohesion rationale recorded in the gate. | Splitting, REJECTED with a specific reason rather than by appeal to the passing size lint: E-06 goes red the instant E-02 lands, and E-04 cannot be judged before E-07. A split would produce a plan whose tests fail until its sibling merges, which is the failure mode a Set exists to prevent. | `plan-review.md:490-496`; the E-06/E-02 and E-04/E-07 dependencies | yes |
| D-7 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status: reviewed`; no human sign-off). `no-go`, REJECTED: both HIGH findings are FIXED, both pre-existing open questions were already resolved from evidence, and no new open question was created. | `plan-review.md:531-546` | yes |

No `Reversible: no` decision was taken. Every decision above is undoable by editing the plan before
execution.

### Verified claims

Re-measured independently at `de26ef00`, UNPIPED (`cmd >/dev/null 2>&1; echo $?`), against 106 live run
records. All seven of the plan's claims reproduce:

- `aw runs verify <real-run-id>` -> exit 0, renders the full run report. F-3 holds; this is the
  motivating case.
- `aw runs totalgibberish` -> exit 0, prints `no matching runs found`. F-2 holds.
- `aw runs totalgibberish <real-run-id>` -> exit 0, prints the real run, bogus token dropped. F-4 holds.
- `aw runs verify-ledger <absent>` -> exit 2 (both for a nonexistent target and for a real run with no
  `ledger.jsonl`). F-6 holds, so a nonzero refusal is consistent with the surface rather than novel.
- Preserved cases, all exit 0: real run id; setid `lanectn`; bare `aw runs`; `--last 1`;
  `aw runs -- status`; `--since 2026-09-01`; `--since 7d`; `--since <run-id>`. F-7 holds and I extended
  it with the three `--since` forms the plan did not measure.
- The ambiguity rule works as documented: `aw runs status` (no hatch) exits 2 from the LEAF demanding
  its required target, while `aw runs -- status` reaches the viewer and renders 106 runs.
- The routing branch is exactly as described: leaf-or-viewer with no third outcome, `cli.py:672` and
  `:682`. F-1 holds.
- F-5's history holds: `98a0beed` is the correction commit, and `run_evidence.py:1319` now carries the
  corrected `verify-ledger` spelling.

Additional measurements that produced the findings:

- `aw runs totalgibberish --agent` -> exit 0, `{"runs": []}`; `--json` -> exit 0, the same object
  pretty-printed. The machine path fails open (PR-004).
- `aw runs repair totalgibberish` -> exit 0, zero bytes of output (PR-003).
- `resolve_target_runs` counts for JSON-key tokens: `status`/`run`/`opencode`/`driver`/`run_id`/
  `options` 106, `clean` 105, `main` 96, `json` 79, `execute` 53, `approved` 46, `verified` 13,
  `pass` 11 (PR-002). Legitimate cases for contrast: `lanectn` 3, `runnernorm` 7, `2367239` 1.
- `aw runs verified <real-run-id>` -> exit 0 rendering 14 runs, i.e. a "mixed" case where the bogus
  token accidentally resolves, which is why E-04 must follow E-07.
- `python3 -m pytest tests/test_run_viewer.py tests/test_run_noun_split.py -o addopts="" -q` ->
  `62 passed` in the real checkout. `tests/test_run_viewer.py` alone -> `46 passed` here versus
  `14 failed, 32 passed` in `.aw/worktrees/5942n7` (PR-005).
- `python3 -m pytest tests/test_cli_conformance_matrix.py` -> `no tests ran` (PR-006).
- `discover_parser_leaves(_build_parser())` contains the nine `runs <leaf>` names and NOT bare `runs`
  (PR-007).

### Right-sizing and conceptual density

Eight E-items, four task groups, two product modules and three test modules. I considered splitting
task group 3 (the two sibling fail-opens) into its own child and decided against it for the dependency
reason recorded in D-6, not because the count lint passes. Each E-item names one deliverable in one
region: E-01 the resolver's return shape, E-02 the refusal, E-03 the preservation matrix, E-04 the mixed
case, E-07 one fallback tier, E-08 one function's empty-loop path, E-05 the new fixture tests, E-06 one
existing assertion. Each maps to exactly one V-item demanding pasted evidence.

### Not verified, and stated as such

I implemented nothing and changed no product code. Every claim is a read of a named `path:line` at
`de26ef00` or the output of a read-only command run in the real checkout. Specifically NOT established:
whether narrowing the resolver (E-07) breaks any of the 23 live-records tests in
`tests/test_run_viewer.py` beyond the two I checked by hand, since that requires the code to exist;
V-07 exists to force that measurement. Nor did I verify the refusal message's final wording, which does
not exist yet.
