# Review findings: plan x8p9ek

- Subject-Id: x8p9ek
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e9e14c28d`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 36), docstring-only, one declared path.

Verified at the lane HEAD:
- `benchmark_corpus.load_corpus` docstring reads "Returns tasks sorted by (task_class, seed_id) for determinism" while the body iterates `sorted(corpus_root.iterdir(), key=lambda p: p.name)` and keeps only `child.is_dir() and (child / TASK_FILENAME).is_file()`; non-directory root raises `CorpusError("corpus root is not a directory: ...")`; `load_task` errors propagate (no try/except).
- F-01 reproduced by direct call: seeds copied as `a_dir` (`simple_commands`) and `b_dir` (`migration`) load with `task_class` order `['simple_commands', 'migration']`. `SeededTask` exposes `seed_path` (used for the name list).
- F-02: `rg -n load_corpus --type py -g '!.aw/**'` finds only `benchmark_reports` (import plus `tasks = load_corpus(root)`) and `tests/test_benchmark_corpus.py` ("self.tasks = corpus.load_corpus(CORPUS_ROOT)"). `grep -rln load_corpus .aw/records/specs docs` is empty.
- F-03: seven fixture seed directories, each named its `task_class`, `seed_id` `<class>-001`; name order equals `(task_class, seed_id)` order there.
- F-04: `btubm6` is `Status: approved` in `pending/`; its E-02(e) pins `seed_path.name == ["a_dir", "b_dir"]` with `task_class == ["simple_commands", "migration"]`, and its deferral row says "if `qtd3lj` changes the sort, it updates that test". `tests/test_benchmark_corpus_restored_behavior.py` does not yet exist, which E-02's "if present" clause handles.
- Backlog `qtd3lj` is `graduated` to this plan; `From-Backlog: qtd3lj` carried; no `Blocks-Release` to inherit (`Work-Kind: chore`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | UNDER-SCOPE | G (execution contract: lifecycle transition) | plan `## Approval and execution gate` (no lifecycle bullet) | The gate lacked the conditional finalize ownership (runner performs `aw ipd finalize`; by hand, pre-transition lint then finalize, never `git mv`), and the scope fence did not state how an out-of-scope edit is justified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the Lifecycle bullet and `--scope-reason` wording to the gate, without a stop clause. |
| PR-002 | LOW | IN-SCOPE | E (validation precision) / honest docs | `agent_workflows/benchmark_corpus.py:151` `child.is_dir() and (child / TASK_FILENAME).is_file()`; plan E-01, E-02 | E-01 asked the docstring to say only "children without `task.json` are skipped", which omits that loose files are also skipped; E-02's direct call did not say what to print, so the expected `['a_dir', 'b_dir'] ['simple_commands', 'migration']` output was not reproducible without inventing the projection. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says non-directory children and subdirectories without `task.json` are skipped; E-02 names the printed projections `[t.seed_path.name ...]` and `[t.task_class ...]`. |

Rubric notes: A/B/C not applicable (docstring-only edit, no runtime change). D: invariant (name order) is already pinned by `btubm6` E-02(e) once executed; E-02 re-measures it directly meanwhile. P16 respected: no docstring-text test. V-items map 1:1 to E-items with pasted-output demands; V-02's runtime observation is produced by `benchmark_corpus.load_corpus` via E-02. Each E-item is one concern. No spec sync needed (F-02).

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01's contract choice (directory-name order, docstring fix) without asking the maintainer? | Accept | Change the sort to `(task_class, seed_id)` and edit `btubm6`'s test | `agent_workflows/benchmark_corpus.py:150` `key=lambda p: p.name`; fixture corpus names (F-03); backlog `qtd3lj` lists the docstring fix as "no behavior change, test stays"; `btubm6` E-02(e) | yes |
