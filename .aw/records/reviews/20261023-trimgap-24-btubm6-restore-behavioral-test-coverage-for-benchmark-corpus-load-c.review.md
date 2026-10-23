# Review findings: plan btubm6

- Subject-Id: btubm6
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `08a77c338`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 24), test-only, one declared path.

Verified by direct call at the lane HEAD:
- `benchmark_corpus.load_corpus` refuses a non-directory root with "corpus root is not a directory", skips children without `task.json`, iterates `sorted(corpus_root.iterdir(), key=lambda p: p.name)`, and propagates `load_task`'s `CorpusError` (`seed ... has unknown task_class 'nope'` reproduced).
- `SeededTask.workspace_seed_path` returns `self.seed_path / WORKSPACE_DIRNAME`; a hand-built task with a nonexistent seed returns `<seed>/workspace`.
- Fixture corpus: 7 seeds, one per `TASK_CLASSES` member, each with `task.json`, `ground_truth.json`, `workspace/`; no `ground_truth.json` anywhere under any `workspace/`. `load_corpus(str(root))` works.
- F-01: `git cat-file -e f3afece92:tests/test_benchmark_corpus.py` fails as claimed; `03241d58a` is `work(78g6ic)`; `tests/test_benchmark_corpus.py` carries `pytestmark = pytest.mark.core` and is collected by a bare run. F-02 mutant counts not re-run (scratch production edits are out of bounds for a review); the claim is consistent with the restored core module calling `load_corpus` at `tests/test_benchmark_corpus.py` ("self.tasks = corpus.load_corpus(CORPUS_ROOT)").
- Sibling plans `78g6ic`, `5jevb2`, `33f8tn` are in `executed/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Testing (case cannot prove its claim; docstring/code contradiction) | `agent_workflows/benchmark_corpus.py:143` `load_corpus` docstring "Returns tasks sorted by (task_class, seed_id) for determinism" vs `:150` `key=lambda p: p.name` | E-02(e) named `migration` as `a_dir` and `simple_commands` as `b_dir`, so name order and class order give the same list; the case could not prove "order is by directory NAME" and a mutant sorting by `(task_class, seed_id)` would survive. Also, the documented order contradicts the code (measured: swapped layout yields `['simple_commands', 'migration']`), so the test pins behavior the docstring denies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02(e) swapped so name order and class order disagree, labelled a characterization citing backlog `qtd3lj`; added F-05; added mutation spot-check (4b) (sort by `(task_class, seed_id)`), referenced from V-02; deferral row with `- Carrier: qtd3lj` for the contract decision (filed this review). |
| PR-002 | LOW | IN-SCOPE | Testing (weak assertion) | E-03 "it does NOT contain `corpus.GROUND_TRUTH_FILENAME`" | "Does not contain" was ambiguous (top level only?) and vacuous if the truth file were absent everywhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now asserts `rglob(GROUND_TRUTH_FILENAME)` under the workspace is empty AND `(seed_path / GROUND_TRUTH_FILENAME).is_file()`. |

Rubric notes: A/B/C not applicable beyond the above (tests only, `tmp_path`, no subprocess, no secrets). Execution contract present (resolved OQ, declarative scope fence without a stop clause, paste-actual-output rule, `aw commit` path-scoped, never push, conditional finalize ownership). V-items map 1:1 to E-items with concrete evidence; no runtime-demonstration demands beyond test runs. Each E-item is one test surface. V-01's `rg -c` over `--collect-only -q` output counts lines, which is nonzero once the module is collected; acceptable as a presence check.

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Pin the code's name order, or the docstring's `(task_class, seed_id)` order, in E-02(e)? | Pin current code behavior as a labelled characterization; file `qtd3lj` for the contract decision | Pin the docstring order (would need a production edit, out of scope); drop the ordering case (loses mutation coverage) | `agent_workflows/benchmark_corpus.py:145`, `:150`; plan Scope excludes production edits; GUIDING_PRINCIPLES P16 (behavioral tests) | yes |
