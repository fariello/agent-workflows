# Review findings: plan z28jah

- Subject-Id: z28jah
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `320b943c1` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified by driving the code:
- Default collection of the two files: 5 of 7 collected, `2 deselected`; neither named node is in the list. `-o addopts="" -m ''` collects 4 tests in `test_verbose_flag_reach.py`.
- `test_verbose_flag_end_to_end_observable_difference` carries `@pytest.mark.livecorpus` and no timeout. `TypecheckGateTests` is `@pytest.mark.slow` and its test carries `@pytest.mark.timeout(300)`.
- `conftest.py`: `_DEFAULT_TEST_CPU_TIMEOUT = 60.0` (ITIMER_PROF, CPU), `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`, and `_DEFAULT_TEST_TIMEOUT` is the CPU alias. A marker sets CPU and floors the wall ceiling.
- The node's work (`cli.main(["check","plans","--agent"])` and then with `--verbose`) driven in-process: wall 17.21s, CPU 16.41s, at load 1.12.
- `python3 -m pytest -m '' -n auto tests/test_verbose_flag_reach.py` -> `4 passed in 19.66s`.
- `python3 -m mypy agent_workflows` (Python 3.14.6, mypy 2.3.1) -> `Found 15 errors in 8 files (checked 193 source files)`. The count is the same under `--python-version 3.12`. Per file: attention 1, backlog 1, cli 6, releases 2, research_archive 1, research_refs 1, runner_shared 2, specs 1.
- Related open backlog `2rm0gz` (bug, `Blocks-Release: next`) covers a `render_stream.py` error, which is not in the current 15. `g321ny` and `fcua9q` are done.
- `ipd_lifecycle._scope_match(".aw/records/backlog/open/x.backlog.md", ".aw/records/backlog/open")` -> True, so the Scope-Paths directory entry covers a new item.
- `aw backlog new` is a dry run without `--apply`. `aw backlog check --agent` -> clean, 976 checked.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-03/V-03 "`3 passed`"; measured `4 passed in 19.66s` | The bar was a test count that is already wrong: the file holds 4 tests. A correct execution would fail V-03. V-01 likewise used the `2 tests were deselected` count, which is an artifact of test organization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now behavior: the named nodes are absent from the default collection and present under `-m ''`, there are zero failures, and the live-corpus node shows `PASSED` under `-rA`. Counts are kept only as context. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness (rationale) | `conftest.py` `_DEFAULT_TEST_CPU_TIMEOUT = 60.0` (ITIMER_PROF); review measured 16.4s CPU | E-02 told the executor to write a comment saying the 27s-135s cost exceeds the 60s CPU arm. 27s-135s are WALL times, and the CPU arm counts CPU (about 16s measured). The comment would ship a false mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now prescribes an honest comment (CPU grows with the corpus; the marker floors both arms) and forbids the wall-versus-CPU comparison. The Findings row now records the measured CPU. |
| PR-003 | MEDIUM | IN-SCOPE | G. Executability | `aw backlog new --help`: "dry-run by default; --apply to write" | The E-04 command omitted `--apply`, so it would write nothing. It also passed the body only in prose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `--body <body> --apply`. |
| PR-004 | MEDIUM | UNDER-SCOPE | Evidence / duplicate tracking | `.aw/records/backlog/open/20261002-2rm0gz-01-2rm0gz-typecheck-gate-error-in-render-stream-py-due-to-op.backlog.md` | The existing-item search pattern (`mypy agent_workflows`) misses the related open bug `2rm0gz`, which says "Typecheck gate". The executor could miss the relationship or file a confusing duplicate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now widens the search, names `2rm0gz` and why it does not cover the current 15, and requires the new item to reference it. |
| PR-005 | LOW | UNDER-SCOPE | E. Evidence quality | `.github/workflows/tests.yml` "Set up Python \"3.12\""; local Python 3.14.6 | The plan measured mypy only under local Python 3.14, while the CI gate runs 3.12. The bug body could misstate what CI sees. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now require the `--python-version 3.12` count and the tool versions (both give 15 at review). |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract / regression | `## Approval and execution gate`; `## Required tests` "Bare `python3 -m pytest` ... recorded under V-03" with no E-item | The bare-suite regression run had no E-item. The gate also lacked the OQ status, the must-paste rule, the scope-fence justification, runner ownership of finalize, and the ban on a hand `git mv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now runs base and post-change bare suites compared by name. Added an EXECUTION CONTRACT and a POST-GATE LIFECYCLE paragraph. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does `2rm0gz` already cover the mypy gate failure, so nothing should be filed? | No: file a whole-gate item that references `2rm0gz` | Cite `2rm0gz` and file nothing (it names a different file, absent from the current 15 errors) | review mypy per-file counts; `2rm0gz` Summary | yes |
| D-2 | Keep `timeout(300)` once the measured CPU is about 16s, well under 60s? | Keep it, with an honest rationale | Drop E-02 (the node keeps shrinking headroom as the corpus grows, and the backlog asks for an explicit budget) | backlog `wc5c5e` option (a); sibling `test_typecheck_gate_clean_exit` precedent | yes |
