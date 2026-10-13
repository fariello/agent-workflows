# IPD: Make aw find --limit bound the human row listing and say how many rows it omitted

- Date: 2026-10-12
- Kind: child
- Concern: `aw find` accepts `--limit <N>` (declared once in the shared noun-verb loop in `cli._build_parser`, help string `"Max rows (index/find)."`), and only the `--agent` branch of `cli._run_find` honors it, through `renderers.AgentRenderer.render_stream` (plan `okiso1`, `executed`). The human row listing and the `--paths` listing both ignore it. Measured in this lane at HEAD `320b00a12`: `aw find plans | wc -l` prints 1414, `aw find plans --limit 3 | wc -l` prints 1414, and `aw find plans --limit 3 --paths | wc -l` prints 1415, while `aw find plans --limit 3 --agent` emits 3 items and a summary carrying `"total":1415,"emitted":3,"omitted":1412,"complete":false`. So the same flag on the same verb bounds one surface and silently does nothing on the two a human types. The help text documents it as "Max rows" with no surface restriction, so a human reading `--help` is told something false.
- Scope: Make `--limit N` bound the HUMAN row listing and the `--paths` listing of `aw find` to the first `N` matched rows, in the same order the unbounded listing prints and the same order `--agent` already bounds (measured identical, F-03). On the human surface, when rows were omitted, print one notice stating how many of how many were shown and a `Next` continuation command that reproduces the query unbounded. On `--paths`, keep stdout pure paths and write that notice to stderr. Does NOT change: which artifacts match, row format, the unflagged human output, the unflagged `--paths` output, the `--agent` stream (already correct), the `--json` payload, exit codes, the existing non-positive `--limit` refusal, the empty-result rendering, the `find.id6-collision` warning, or `--limit` on any other verb.
- Scope-Paths: agent_workflows/cli.py, tests/test_find_human_limit.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: no88yi
- Blocks-Release: next
- Set: no88yi
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: i00j2o

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: i00j2o verified (set no88yi, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `no88yi`, graduating it. Re-measured at HEAD `320b00a12` rather than carried over: the defect reproduces on the human surface (1414 lines with and without `--limit 3`) and ALSO on `--paths` (1415 lines with `--limit 3`), which the item does not mention and which this plan folds in (OQ-01). `--agent` already bounds correctly. Non-positive refusal already happens upfront for every surface (F-04), so no refusal work is needed.

## Goal

Make `aw find <type> --limit N` show a human at most `N` rows and say plainly that more exist and how to see them, so the flag means the same thing on every `aw find` surface that prints rows. This closes the last inert surface left after `okiso1` fixed the `--agent` stream.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: failing baseline

- [x] E-01 WRITE `tests/test_find_human_limit.py` AND SHOW IT RED BEFORE ANY PRODUCTION EDIT. Drive a FIXTURE repository through `cli.main(["find", ..., "--dir", <tmp>])` with stdout and stderr captured, reusing the fixture shape `tests/test_find_agent_stream.py` already uses in its `setUp` (several plans across `pending/` and `executed/`), so every count asserted is one the test created. Assert: (1) `find plans --no-color --limit 2` prints exactly the FIRST 2 rows of the unbounded `find plans --no-color` output, in the same order, followed by an omitted-rows notice stating `2` shown of the fixture's total and a `Next` line whose command is `aw find plans --limit <total>`; (2) with `--limit` at or above the row count, output is byte-identical to the unbounded run and carries no notice; (3) `find plans --paths --limit 2` prints exactly the first 2 lines of `find plans --paths` on stdout and nothing else there, with the omitted notice on stderr; (4) `--paths --limit` at or above the count leaves stdout byte-identical to unbounded `--paths` and stderr empty; (5) the paths printed under `--limit 2` equal the `path` fields of the 2 `item` records `find plans --agent --limit 2` emits (one meaning across surfaces); (6) a selector plus `--limit` (for example `find plans setalpha --limit 1`) bounds the filtered rows and its `Next` command carries the selector; (7) exit code is 0 in every bounded case; (8) unflagged human output, unflagged `--paths`, and `--json` with and without `--limit` are captured as in-test expected values and asserted unchanged; (9) COLLISIONS ARE NOT BOUNDED (OQ-02): over the `col001` spec-plus-backlog collision pair the `tests/test_find_agent_stream.py` fixture already creates, `find all col001 --no-color --limit 1` prints exactly 1 row, then the omitted notice and `Next` line, then the `find.id6-collision` warning naming BOTH claimant paths, in that order; (10) BRACE AND SPACE SELECTORS ARE NOT TEMPLATE-ESCAPED ON THE HUMAN SURFACE: with two plans whose names contain `{x}` and `has space` (the `test_09` fixture shape), `find plans '{x}' 'has space' --no-color --limit 1` prints a `Next` line containing `'{x}'` and `'has space'` and NOT `{{x}}`. NO STATIC ANALYSIS (GUIDING_PRINCIPLES P16): no reading `cli.py`, no symbol or call-site assertions; every assertion comes from command output, stderr, and exit code.
  - Depends on: none
  - Expected outcome: a new module whose bounding assertions (1), (3), (5), (6), (9), (10) FAIL at the base commit and whose invariance assertions (2), (4), (7), (8) PASS there.
  - Execution state: performed

### Task group 2: bound the two surfaces

- [x] E-02 FACTOR THE QUERY-PRESERVING CONTINUATION BUILDER OUT OF THE `--agent` BRANCH OF `cli._run_find` into one small helper reused by the agent branch and the new human and `--paths` notices. Today the agent branch builds `next_parts` inline (type token, sanitized selectors, `--id`/`--set`/`--status`/`--topic`/`--disposition`, `--fields`, then `--agent --limit {limit}`), escaping braces because `render_stream` formats it as a template. The helper returns the shared argument list (type token, selectors, and the five filter flags, in today's order, each value passed through `agent_schema.normalize_repo_path` and `shlex.quote` exactly as `_sanitize_for_next` does) with brace escaping CONTROLLED BY THE CALLER: the agent branch requests escaping (because `render_stream` calls `next_template.format(limit=...)`) and appends its own `--fields` / `--agent` / `--limit {limit}` tail; the human and `--paths` paths request NO escaping and append `--limit <total>` (and `--paths` on that surface). Escaping on the human surface would print a literal `{{x}}`, which E-01 assertion (10) refuses. The helper carries the same flag set as today and no more (see the deferred row on traversal flags). The `--agent` stream's `next` must stay byte-identical, which the existing `tests/test_find_agent_stream.py` (including `test_09`, the brace and space selector case) proves unmodified.
  - Depends on: E-01
  - Expected outcome: one builder serving both surfaces; `tests/test_find_agent_stream.py` passes unmodified.
  - Execution state: performed

- [x] E-03 BOUND THE HUMAN ROW LISTING. In the human branch of `cli._run_find` (the `for line in all_lines: term.line(line)` loop), print only `all_lines[:limit]` when `limit` is set and below `len(all_lines)`. Take `limit` from `ctx.limit` (the value `result_types.select_output` already parses from `args.limit`, and the same value `renderers.AgentRenderer.render_stream` reads), so the human, `--paths`, and `--agent` surfaces read one source and cannot disagree; do not re-parse `args.limit`. After the printed rows and BEFORE the existing `find.id6-collision` warnings, print a blank line, one `term.status("info", ...)` line reading `showing <N> of <total> matches (<omitted> omitted)`, and `term.next_action(<continuation>, "list every match")`. Keep the collision warnings computed over the FULL match set, unchanged: a collision among omitted rows is still a fact about the query, and hiding it under a token-control flag would suppress a warning. When nothing is omitted print no notice, so output is byte-identical. Add a comment at the site stating the order (`--agent` and human bound the same first `N` rows) and why collisions are not bounded.
  - Depends on: E-02
  - Expected outcome: `aw find plans --limit 3` prints 3 rows, a notice, and a `Next` line; `aw find plans --limit 99999` is byte-identical to `aw find plans`.
  - Execution state: performed

- [x] E-04 BOUND THE `--paths` LISTING. In the `getattr(args, "paths", False)` branch of `cli._run_find`, print only `all_paths[:limit]` when bounded, with `limit` read from `ctx.limit` as in E-03. Stdout must remain bare paths only (the `--paths` contract in `docs/cli-output-contract.md` Section 12: "no column headers, ANSI formatting, or summary boilerplate"), so write the omitted notice and continuation to STDERR through a `Term(stream=sys.stderr, ...)`, the same construction that branch already uses for its refusal message. Exit stays 0. When nothing is omitted, stderr stays empty.
  - Depends on: E-02
  - Expected outcome: `aw find plans --paths --limit 3 2>/dev/null | wc -l` prints 3; unbounded `--paths` output unchanged.
  - Execution state: performed

### Task group 3: documents and proof

- [x] E-05 RECONCILE THE DOCUMENTS. In `docs/cli-output-contract.md` Section 12, extend the `--paths` bullet (or add one sentence beside the `--agent` discovery bullet) stating that `aw find --limit <N>` bounds every row-printing surface to the first `N` matches: the `--agent` stream reports counts in its `summary`, the human listing prints an omitted notice and continuation, and `--paths` keeps stdout pure and reports the notice on stderr; and that `--json` remains the full unbounded dictionary. Add one `Fixed:` bullet to the pending top section of `CHANGELOG.md` naming the behavior. Both are user-facing prose: write no em or en dashes.
  - Depends on: E-03, E-04
  - Expected outcome: the contract and changelog describe the shipped behavior.
  - Execution state: performed

- [x] E-06 RUN THE AFFECTED AND FULL SUITES. Run `tests/test_find_human_limit.py`, `tests/test_find_agent_stream.py`, `tests/test_cli_find.py`, `tests/test_find_filters.py`, and `tests/test_find_single_read.py`, then the full suite BARE as `python3 -m pytest` (no added flags, per `AGENTS.md`), capturing the summary line at the base commit before any edit and at the end, and stating the failure-set delta as a set of test ids. The bar is an EMPTY delta. Also re-run the live measurements from the Concern (`aw find plans --limit 3 | wc -l`, `--paths --limit 3`, `--agent --limit 3 | tail -1`) and paste them.
  - Depends on: E-05
  - Expected outcome: targeted modules pass, empty failure-set delta, live measurements show 3 rows plus notice on each human surface.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE BARE SUITE IS THE CONTRACT: `python3 -m pytest` with no added flags (`AGENTS.md`, repository development contract).
- NO CODE-PINNING TESTS (GUIDING_PRINCIPLES P16): drive `cli.main` over a fixture and assert on output, stderr and exit code.
- `--dir` keeps tests off the live tree; `tests/test_find_agent_stream.py.run_find` is the harness to copy.
- `--paths` is the byte-stable script surface (`docs/cli-output-contract.md` Section 12), so stdout there must carry nothing but paths.
- No em or en dashes in user-facing prose (`docs/`, `CHANGELOG.md`).

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE FILED DEFECT REPRODUCES ON THE HUMAN SURFACE. `aw find plans` and `aw find plans --limit 3` each print 1414 lines (1415 matches; the count differs by one only from `wc -l` on the final line). | Both commands run in this lane at HEAD `320b00a12`. |
| F-02 | `--paths` IS EQUALLY INERT, WHICH THE ITEM DOES NOT STATE. `aw find plans --limit 3 --paths | wc -l` prints 1415. The `--paths` branch of `cli._run_find` prints `all_paths` in full and returns before the agent branch, so the flag never reaches it. | Command run in this lane; the `for p in all_paths: print(p)` loop read. |
| F-03 | `--agent` ALREADY BOUNDS, IN THE SAME ORDER THE OTHER SURFACES PRINT. `aw find plans --limit 3 --agent | tail -1` emits `{"kind":"summary",...,"total":1415,"emitted":3,"omitted":1412,"complete":false,"next":"aw find plans --agent --limit 1415"}`. `diff` of `aw find all --paths` against the `path` fields of `aw find all --agent` items printed nothing (3542 rows), so "first N" means the same rows on every surface and E-01 assertion (5) is satisfiable. | Commands run in this lane; the `render_stream` call in `cli._run_find` read. |
| F-04 | NON-POSITIVE `--limit` IS ALREADY REFUSED ON EVERY SURFACE. The `okiso1` validation block in `cli._run_find` ("Validate --limit upfront") runs before any branch: `aw find plans --limit 0` and `aw find plans --limit 0 --paths` both print `FAIL     --limit must be greater than zero.` and exit 2. No refusal work is needed here. | Both commands run with exit codes captured. |
| F-05 | `--json` CARRIES THE FULL LIST AND IS DOCUMENTED AS THE UNBOUNDED SURFACE. `aw find plans --limit 3 --json` reports `data.matches` of length 1415; `docs/cli-output-contract.md` Section 12 says "callers requiring the full unstreamed dictionary use explicit `--json`". | Command run; Section 12 quoted. |
| F-06 | THE CONTINUATION BUILDER EXISTS ONLY INSIDE THE AGENT BRANCH. `next_parts` in `cli._run_find` already reproduces the type, selectors and filter flags with home-path normalization through `agent_schema.normalize_repo_path` and `shlex.quote`; reusing it (E-02) avoids a second query-reconstruction that could drift. | The `next_parts` construction read. |
| F-07 | THE LIVE COUNTS DRIFT; THE PROPERTY DOES NOT. Re-measured at review HEAD `24f9f0cf3`: `aw find plans`, `--limit 3`, and `--limit 3 --paths` each print 1441 lines; `--agent --limit 3` reports `"total":1441,"emitted":3,"omitted":1438`; the `--paths` versus `--agent` path diff over `find all` is still empty. The numbers in F-01 to F-05 are authoring context only; E-06 / V-06 re-derive them at execution and the bar is the property (3 rows plus a notice), not a count. | Commands run in the review lane. |

## Proposed changes (ordered, validatable)

1. E-01 writes the failing fixture-driven baseline for both surfaces plus invariance captures.
2. E-02 factors the continuation builder so all surfaces reproduce the query identically.
3. E-03 bounds the human listing and prints the omitted notice and `Next` line.
4. E-04 bounds `--paths` with the notice on stderr.
5. E-05 updates `docs/cli-output-contract.md` Section 12 and `CHANGELOG.md`.
6. E-06 runs targeted and bare full suites and the live measurements.

## Deferred / out of scope (with reason)

- BOUNDING `--json`. Section 12 documents `--json` as the full unstreamed dictionary (F-05), and `okiso1` declared it unchanged; bounding it would change a documented machine contract that no item asks to change.
  - Carrier-Declined: no defect exists; `--json` is unbounded by documented design.
- `--limit` ON `group` AND `rename`, which inherit the same shared declaration. Mutation verbs with undecided semantics, already recorded as declined in plan `2zvxhx`'s deferred table.
  - Carrier-Declined: already recorded with reason in executed plan `2zvxhx`; no new measurement here.
- CARRYING `--max-depth` / `--include-ignored` INTO THE CONTINUATION. The `--agent` branch's `next_parts` omits these two `find`-only traversal flags today, and E-02 preserves that so the `--agent` `next` stays byte-identical. Measured at review (HEAD `24f9f0cf3`): `aw find plans --max-depth 0 --agent --limit 1`, `--max-depth 1`, and `--include-ignored` each report `total` 1441, the same as the unflagged query, so no observed continuation lists a different set.
  - Carrier-Declined: pre-existing on the already-shipped `--agent` surface, with no measured case where the dropped flag changes the listed set; adding it would change `--agent` bytes, which this plan's boundaries forbid.
- NARROWING THE SHARED `"Max rows (index/find)."` HELP STRING. After this plan the string is true for `find`; rewording it for the other verbs is a cosmetic change outside this item.
  - Carrier-Declined: after this plan the help text is accurate for the verb this item concerns; no user-visible defect remains to file.

## Scope check

- Over-scope: `--paths` (E-04) is not named in the item but is the same flag inert on the same verb at an adjacent site (F-02); fixing only the styled listing would leave the item's exact symptom on the other human-invoked surface. Resolved in OQ-01.
- Under-scope: none. `renderers.py`, `agent_schema.py`, and `result_types.py` are not edited; the `--agent` branch changes only by calling the factored builder, proven byte-identical by `tests/test_find_agent_stream.py`.

## Required tests / validation

- The new module `tests/test_find_human_limit.py` (E-01), RED before and GREEN after.
- `tests/test_find_agent_stream.py`, `tests/test_cli_find.py`, `tests/test_find_filters.py`, `tests/test_find_single_read.py` passing unmodified.
- Bare `python3 -m pytest` before and after with an empty failure-set delta.
- Live measurements from the Concern re-run and pasted.
- `aw ipd lint` conforming at `--phase pre-transition` before the terminal move.

## Spec / documentation sync

No `.spec.md` file is touched or declared, so the run must announce no declared spec edits. The behavior is governed by `docs/cli-output-contract.md` Section 12, a normative document rather than a spec record, which E-05 amends so the contract states the per-surface `--limit` behavior. `CHANGELOG.md` gets one `Fixed:` bullet. `docs/cli-human-guide.md` is not edited: its only `aw find --limit` row is the `--agent` example, which stays true.

## Open questions

### OQ-01: Should `--paths` honor `--limit` too, and where does its omitted notice go

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: yes, bound `--paths`, and put the notice on stderr. The flag is inert there for the same reason (F-02), and a human piping `aw find plans --paths --limit 5` gets 1415 lines, the item's exact symptom. No script can depend on `--limit` doing nothing, and unflagged `--paths` stays byte-identical, so the byte-stable contract is preserved. Section 12 forbids summary boilerplate on `--paths` stdout, so the notice goes to stderr, which is where this same branch already writes its refusal message.
- 2026-10-12 (opencode its_direct/pt3-claude-opus-5.5-1m-us): resolved at authoring.

### OQ-02: Should the `find.id6-collision` warning be bounded with the rows

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO. Plan `paw8so` E-03 established the warning as additive and never suppressing ("it never removes, reorders or suppresses a result", comment in the human branch of `cli._run_find`). A collision among omitted rows is still true of the query, and the `--agent` summary already carries collisions computed over the full set, so the human surface matches it.
- 2026-10-12 (opencode its_direct/pt3-claude-opus-5.5-1m-us): resolved at authoring.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the new module's RED run at the base commit (before any production edit), using `python3 -m pytest tests/test_find_human_limit.py -o addopts="" -v`, showing the bounding assertions failing and the invariance assertions passing. State the fixture's plan count and confirm it is the `total` the assertions use. State in one sentence how each assertion obtains its facts, confirming no production source is read.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=711053704
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_find_human_limit.py::TestFindHumanLimit::test_08_invariance_unflagged_and_json PASSED [ 10%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_02_limit_at_or_above_count_byte_identical PASSED [ 20%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_01_human_row_limit_bounding_and_notice FAILED [ 30%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_06_selector_filtered_limit_and_continuation FAILED [ 40%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_07_exit_code_zero_for_bounded_queries PASSED [ 50%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_09_collisions_not_bounded FAILED [ 60%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_05_paths_limit_matches_agent_items FAILED [ 70%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_03_paths_limit_bounding_and_notice_on_stderr FAILED [ 80%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_10_brace_and_space_selectors_human_surface FAILED [ 90%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_04_paths_limit_at_or_above_count_byte_identical PASSED [100%]

    =========================== short test summary info ============================
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_01_human_row_limit_bounding_and_notice
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_06_selector_filtered_limit_and_continuation
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_09_collisions_not_bounded
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_05_paths_limit_matches_agent_items
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_03_paths_limit_bounding_and_notice_on_stderr
    FAILED tests/test_find_human_limit.py::TestFindHumanLimit::test_10_brace_and_space_selectors_human_surface
    ========================= 6 failed, 4 passed in 3.96s ==========================
    ```
    The fixture defines 3 plans (pln001, pln002, pln003), matching the total of 3 used by the assertions. Each assertion obtains its facts solely by driving cli.main over a temporary fixture directory with stdout and stderr captured and inspecting the returned exit code, without reading or inspecting production source code.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `python3 -m pytest tests/test_find_agent_stream.py -o addopts="" -v` passing with the module unmodified (`git diff --stat -- tests/test_find_agent_stream.py` empty), and paste the `next` field of `aw find plans setalpha --agent --limit 1` over the fixture before and after, byte-equal.
  - Observed evidence:
    `git diff --stat -- tests/test_find_agent_stream.py` returns empty (0 lines).
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=2854610231
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 14 items

    tests/test_find_agent_stream.py::TestFindAgentStream::test_01_agent_stream_parses_json_and_schema_version PASSED [  7%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_05_agent_stream_fields_projection PASSED [ 14%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_07_agent_stream_limit_and_fields_retains_next PASSED [ 21%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_14_agent_collision_diagnostics_in_summary PASSED [ 28%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_12_paths_byte_identity PASSED [ 35%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_02_agent_stream_records_strictly_validate PASSED [ 42%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_06_agent_stream_no_ansi_escapes PASSED [ 50%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_04_agent_stream_limit_bounding_and_continuation PASSED [ 57%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_09_agent_stream_brace_and_space_selector_next PASSED [ 64%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_08_agent_stream_zero_match_lone_summary PASSED [ 71%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_11_agent_stream_nonpositive_limit_refusal PASSED [ 78%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_10_agent_stream_closed_pipe_clean_exit PASSED [ 85%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_03_agent_stream_terminal_summary_accounting PASSED [ 92%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_13_human_output_byte_identity PASSED [100%]

    ============================== 14 passed in 6.59s ==============================
    ```
    The `next` field of `aw find plans setalpha --agent --limit 1` over the fixture evaluated byte-equal:
    `NEXT: 'aw find plans setalpha --agent --limit 2'`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the GREEN run of the E-01 assertions (1), (2), (6), (7), (9), (10). Paste live `aw find plans --limit 3 --no-color` output in full (3 rows, blank line, INFO notice, Next line), produced by the human branch of `cli._run_find` that E-03 edits, and `cmp` of `aw find plans --no-color` against `aw find plans --no-color --limit 99999` showing no difference.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=4100481426
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items / 4 deselected / 6 selected

    tests/test_find_human_limit.py::TestFindHumanLimit::test_10_brace_and_space_selectors_human_surface PASSED [ 16%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_01_human_row_limit_bounding_and_notice PASSED [ 33%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_07_exit_code_zero_for_bounded_queries PASSED [ 50%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_09_collisions_not_bounded PASSED [ 66%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_06_selector_filtered_limit_and_continuation PASSED [ 83%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_02_limit_at_or_above_count_byte_identical PASSED [100%]

    NOTE: 4 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 6 passed, 4 deselected in 3.59s ========================
    ```
    Live `aw find plans --limit 3 --no-color` output:
    ```
    ✓  executed      d5tz36  -               .aw/records/plans/executed/20260704-advise-workflow-00-d5tz36-advise-workflow-and-personas.ipd.md
    ✓  executed      bl0nph  -               .aw/records/plans/executed/20260704-command-surface-00-bl0nph-command-surface-redesign.ipd.md
    ✓  executed      ksvzgc  -               .aw/records/plans/executed/20260704-guided-onboarding-00-ksvzgc-guided-onboarding-tour.ipd.md

    INFO     showing 3 of 1461 matches (1458 omitted)
    Next  aw find plans --limit 1461 (list every match)
    ```
    Comparison with `cmp`:
    ```
    python3 -m agent_workflows find plans --no-color > /tmp/find_unbounded.txt
    python3 -m agent_workflows find plans --no-color --limit 99999 > /tmp/find_limit99999.txt
    cmp /tmp/find_unbounded.txt /tmp/find_limit99999.txt
    # exited with code 0 (byte-identical)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the GREEN run of the E-01 assertions (3), (4), (5). Paste live `aw find plans --paths --limit 3` with stdout and stderr captured separately (stdout exactly 3 paths, stderr the notice), produced by the `--paths` branch E-04 edits, and the exit code.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=35680074
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items / 7 deselected / 3 selected

    tests/test_find_human_limit.py::TestFindHumanLimit::test_04_paths_limit_at_or_above_count_byte_identical PASSED [ 33%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_03_paths_limit_bounding_and_notice_on_stderr PASSED [ 66%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_05_paths_limit_matches_agent_items PASSED [100%]

    NOTE: 7 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 3 passed, 7 deselected in 2.76s ========================
    ```
    Live run of `aw find plans --paths --limit 3` (exit 0):
    Stdout:
    ```
    .aw/records/plans/executed/20260704-advise-workflow-00-d5tz36-advise-workflow-and-personas.ipd.md
    .aw/records/plans/executed/20260704-command-surface-00-bl0nph-command-surface-redesign.ipd.md
    .aw/records/plans/executed/20260704-guided-onboarding-00-ksvzgc-guided-onboarding-tour.ipd.md
    ```
    Stderr:
    ```
    INFO     showing 3 of 1461 matches (1458 omitted)
    Next  aw find plans --paths --limit 1461 (list every match)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste `git diff -- docs/cli-output-contract.md CHANGELOG.md`, confirm the change is limited to Section 12 and one changelog bullet, and paste a search over both diffs for U+2013 and U+2014 returning no matches.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 258468d62..55be43f04 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -28,6 +28,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: agents run by aw oc run and aw agy run can no longer change your aw user configuration; attempted changes are discarded and reported.
     - Fixed: `git_mv` in `artifact_core` and `engine` now refuses moves that cross repository boundaries before making any filesystem modifications, preventing out-of-repository destinations from overriding git refusal through the untracked file fallback.
     - Fixed: aw specs set <status> <path> run from outside the repository now writes the same history-sidecar record as aw specs set <path> --status <status> (F-06).
    +- Fixed: aw find --limit <N> now bounds the human row listing and the --paths listing to the first N matches instead of silently ignoring the flag. When rows are omitted, the human surface prints an informational notice and runnable continuation, --paths reports the notice on stderr while keeping stdout pure, and --json remains the full unbounded dictionary.

     - Fixed: aw sanitize and aw check-local-leaks under --agent and --json now emit structured records on stdout for the --fix branch and for cannot-run errors, and refuse un-attested machine --fix calls with an error record instead of prompting on stdout.
     - Fixed: usage errors such as a missing required argument or an invalid choice now emit an aw.agent/v1 cannot-run error record on stdout under --agent and --json.
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 0bac89e7d..5623d1f42 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -476,6 +476,6 @@ When a query, find, search, or list verb matches zero records or produces an emp
     Commands whose primary purpose is path discovery and artifact lookup (e.g. `aw find <selector>`, `aw find <type> <selector> --paths`) are strictly distinguished from verification, check, or mutation commands:

     - **Token-Efficient Bare Paths**: When an agent searches for an artifact (e.g. by `id6`, Set, status, or slug fragment), the optimal output is pure, newline-delimited, repo-relative file paths (e.g. `.aw/records/plans/pending/...`). Wrapping file paths in multi-field JSON envelopes imposes unnecessary LLM parsing overhead and token consumption.
    -- **`--paths` (`-p`) Flag**: Query and discovery verbs support `--paths` to emit bare repo-relative file paths on `stdout`, one per line, with no column headers, ANSI formatting, or summary boilerplate.
    +- **`--paths` (`-p`) Flag**: Query and discovery verbs support `--paths` to emit bare repo-relative file paths on `stdout`, one per line, with no column headers, ANSI formatting, or summary boilerplate. Passing `aw find --limit <N>` bounds every row-printing surface to the first `N` matches: the `--agent` stream reports counts in its `summary`, the human listing prints an omitted notice and continuation, and `--paths` keeps stdout pure and reports the notice on stderr; `--json` remains the full unbounded dictionary.
     - **`--agent` Mode for Discovery**: When `--agent` is passed to `aw find`, it emits a canonical `aw.agent/v1` stream: one `item` record per match followed by a terminal `summary` record. This allows token-bounded queries via `--limit` and field projection via `--fields`. While full unconstrained listings cost more than bare paths (measured on this repository at 1329 plans: 158031 bytes for bare paths versus 239238 bytes for path-only items (1.51x) or 329319 bytes for five-field records (2.08x)), bounded queries dramatically reduce token consumption (for example, `--limit 20` requires only 4809 bytes, or 3.0 percent of the bare full listing). Callers requiring bare paths use `--paths`, while callers requiring the full unstreamed dictionary use explicit `--json`.
     - **Exit Classification**: If one or more matching paths are found, the command exits `0`. If an empty result set occurs, the exit code follows the Section 11.1 standing-question discriminator (governed by spec `25kzda` Sections 2.3 and 2.4a, with `aw runs`, `aw attention`, and `aw find` conforming): listing an empty unfiltered set or asking a standing vocabulary question exits `0`, while a specific selector asserting a named artifact that matches zero paths is treated as an unresolved selector refusal and exits `2` with `outcome: "cannot-run"`. On `--paths`, a refusal prints diagnostic text to `stderr` while `stdout` remains empty (0 bytes).
    ```
    Dashes check: `git diff -- docs/cli-output-contract.md CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` returned exit code 1 (no matches).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the targeted five-module run output, both bare `python3 -m pytest` summary lines (base and final) verbatim, the failure-set delta stated as an explicit set (required empty), and the three live measurements from the Concern re-run after the change.
  - Observed evidence:
    Targeted five-module run output:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=2547806114
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 53 items

    tests/test_cli_find.py::CliFindResearchStatusTests::test_record_dirs_non_research_does_not_leak_legacy_research_nesting PASSED [  1%]
    tests/test_cli_find.py::CliFindResearchStatusTests::test_find_research_todo_returns_no_research_prompts PASSED [  3%]
    tests/test_cli_find.py::CliFindResearchStatusTests::test_find_research_through_a_symlinked_repo_root PASSED [  5%]
    tests/test_cli_find.py::CliFindVocabularyAndMatchFactsTests::test_match_facts_narrowing_filter PASSED [  7%]
    tests/test_cli_find.py::CliFindVocabularyAndMatchFactsTests::test_vocabulary_membership_and_gap PASSED [  9%]
    tests/test_cli_find.py::CliFindVocabularyAndMatchFactsTests::test_match_facts_multi_type PASSED [ 11%]
    tests/test_cli_find.py::CliFindVocabularyAndMatchFactsTests::test_match_facts_substring_query PASSED [ 13%]
    tests/test_cli_find.py::CliFindRefusalSurfacesTests::test_agent_surface_refusal_and_matching PASSED [ 15%]
    tests/test_cli_find.py::CliFindRefusalSurfacesTests::test_paths_surface_exit_codes_and_stdout PASSED [ 16%]
    tests/test_cli_find.py::CliFindRefusalSurfacesTests::test_json_surface_refusal PASSED [ 18%]
    tests/test_cli_find.py::CliFindRefusalSurfacesTests::test_human_surface_refusal PASSED [ 20%]
    tests/test_cli_find.py::CliFindExitMatrixTests::test_post_change_exit_matrix PASSED [ 22%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_02_limit_at_or_above_count_byte_identical PASSED [ 24%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_05_paths_limit_matches_agent_items PASSED [ 26%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_04_paths_limit_at_or_above_count_byte_identical PASSED [ 28%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_01_human_row_limit_bounding_and_notice PASSED [ 30%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_06_selector_filtered_limit_and_continuation PASSED [ 32%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_03_paths_limit_bounding_and_notice_on_stderr PASSED [ 33%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_07_exit_code_zero_for_bounded_queries PASSED [ 35%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_08_invariance_unflagged_and_json PASSED [ 37%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_10_brace_and_space_selectors_human_surface PASSED [ 39%]
    tests/test_find_human_limit.py::TestFindHumanLimit::test_09_collisions_not_bounded PASSED [ 41%]
    tests/test_find_filters.py::TestFindFilters::test_07_find_research_status_intake_accepted PASSED [ 43%]
    tests/test_find_filters.py::TestFindFilters::test_10_find_walkthroughs_status_anything_accepted_zero_rows PASSED [ 45%]
    tests/test_find_filters.py::TestFindFilters::test_04_find_specs_selector_plus_status_intersects PASSED [ 47%]
    tests/test_find_filters.py::TestFindFilters::test_02_find_specs_filter_id PASSED [ 49%]
    tests/test_find_filters.py::TestFindFilters::test_08_find_backlog_status_open_filtered PASSED [ 50%]
    tests/test_find_filters.py::TestFindFilters::test_03_find_backlog_filter_set PASSED [ 52%]
    tests/test_find_filters.py::TestFindFilters::test_01_find_specs_filter_status_to_review PASSED [ 54%]
    tests/test_find_filters.py::TestFindFilters::test_09_find_all_status_accepted_open_and_bogusvalue PASSED [ 56%]
    tests/test_find_filters.py::TestFindFilters::test_06_find_plans_status_bogusvalue_refused_exit_2 PASSED [ 58%]
    tests/test_find_filters.py::TestFindFilters::test_11_find_specs_no_flags_prints_all PASSED [ 60%]
    tests/test_find_filters.py::TestFindFilters::test_05_find_specs_status_bogusvalue_refused_exit_2 PASSED [ 62%]
    tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status PASSED [ 64%]
    tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows PASSED [ 66%]
    tests/test_find_single_read.py::test_a_find_plans_single_read_non_matched PASSED [ 67%]
    tests/test_find_single_read.py::test_b_find_research_single_read_non_matched PASSED [ 69%]
    tests/test_find_single_read.py::test_c_find_plans_setid_matches_oracle_and_shard_ordering PASSED [ 71%]
    tests/test_find_single_read.py::test_f_unreadable_matched_plan_raises_permission_error PASSED [ 73%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_12_paths_byte_identity PASSED [ 75%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_14_agent_collision_diagnostics_in_summary PASSED [ 77%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_02_agent_stream_records_strictly_validate PASSED [ 79%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_07_agent_stream_limit_and_fields_retains_next PASSED [ 81%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_01_agent_stream_parses_json_and_schema_version PASSED [ 83%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_04_agent_stream_limit_bounding_and_continuation PASSED [ 84%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_06_agent_stream_no_ansi_escapes PASSED [ 86%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_11_agent_stream_nonpositive_limit_refusal PASSED [ 88%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_13_human_output_byte_identity PASSED [ 90%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_10_agent_stream_closed_pipe_clean_exit PASSED [ 92%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_05_agent_stream_fields_projection PASSED [ 94%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_08_agent_stream_zero_match_lone_summary PASSED [ 96%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_03_agent_stream_terminal_summary_accounting PASSED [ 98%]
    tests/test_find_agent_stream.py::TestFindAgentStream::test_09_agent_stream_brace_and_space_selector_next PASSED [100%]

    ============================= 53 passed in 12.42s ==============================
    ```
    Bare `python3 -m pytest` summary line at base commit:
    `7777 passed, 4 skipped, 3 warnings in 972.71s (0:16:12)`
    Bare `python3 -m pytest` summary line at final:
    `7787 passed, 4 skipped, 3 warnings in 482.58s (0:08:02)`
    Failure-set delta: `set()` (empty set).
    Live measurements from Concern re-run:
    - `aw find plans --limit 3 | wc -l`: `6`
    - `aw find plans --paths --limit 3 | wc -l`: `3`
    - `aw find plans --agent --limit 3 | tail -1`:
      `{"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":1461,"emitted":3,"omitted":1458,"complete":false,"next":"aw find plans --agent --limit 1461"}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim. No `.spec.md` file is declared, so none may be edited. `agent_workflows/cli.py` is named by many other plans; verify the staged set with `git diff --cached --name-only` before committing.

BOUNDARIES. Do not change the `--agent` stream's bytes, the `--json` payload, unflagged human or `--paths` output, exit codes, or the collision warning's computation (OQ-02). An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`, never silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries concrete pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. In a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`; executing by hand, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit status or `git mv` the plan into `executed/`.
