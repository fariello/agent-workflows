# IPD: Reconcile load_corpus docstring with its seed-directory-name order

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `qtd3lj` (Set `trimgap`, filed by `/plan-review` of `btubm6`) records that `agent_workflows/benchmark_corpus.py` `load_corpus` documents "Returns tasks sorted by (task_class, seed_id) for determinism" while its body iterates `sorted(corpus_root.iterdir(), key=lambda p: p.name)`, i.e. it returns tasks in seed DIRECTORY NAME order. The two orders diverge whenever a seed directory is not named after its class (F-01). The item asks which is the contract: fix the docstring (no behavior change) or change the sort and update `btubm6`'s characterization test.
- Scope: Decide the contract as "seed directory name order" (OQ-01) and rewrite ONLY the `load_corpus` docstring in `agent_workflows/benchmark_corpus.py` to state it. EXCLUDES any change to the function body or to any other symbol, EXCLUDES any test file (`tests/test_benchmark_corpus.py` belongs to executed plan `78g6ic`; `tests/test_benchmark_corpus_restored_behavior.py` belongs to `btubm6`, whose E-02(e) already pins name order and therefore needs no edit under this decision), and EXCLUDES `tests/benchmark_fixtures/`.
- Scope-Paths: agent_workflows/benchmark_corpus.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: qtd3lj
- Set: trimgap
- Order: 36
- Highest E allocated: 02
- Author: opencode
- Id: x8p9ek
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-24 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 fixed
- 2026-10-23 to-review (opencode): authored from backlog `qtd3lj`. Re-measured the order divergence by direct call at lane HEAD `503f15cbd` (F-01), enumerated every caller of `load_corpus` (F-02, F-03), and resolved the contract choice from repository evidence as docstring-fix (OQ-01).
- 2026-10-23 draft (opencode): created.

## Goal

Make `benchmark_corpus.load_corpus`'s docstring describe the order the function actually returns (seed directory name order), so the documented contract, the code, and `btubm6`'s characterization test all agree, with no behavior change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Docstring reconciliation

- [x] E-01 Replace the sentence "Returns tasks sorted by (task_class, seed_id) for determinism." in the `benchmark_corpus.load_corpus` docstring with wording stating that tasks are returned in ascending order of their seed DIRECTORY NAME (the child name under `corpus_root`) for determinism, that this is not `(task_class, seed_id)` order, and that the two coincide only when each seed directory is named after its class (as in the checked-in fixture corpus). Keep the existing first sentences ("Load every seeded task under a corpus root. A corpus root contains one subdirectory per seed (each with a task.json).") and also state the already-true behaviors that a non-directory root raises `CorpusError`, that non-directory children and subdirectories without a `task.json` are skipped, and that a malformed seed's `CorpusError` propagates. Change no line outside the docstring.
  - Depends on: none
  - Expected outcome: `git diff agent_workflows/benchmark_corpus.py` shows changed lines only inside the `load_corpus` docstring; `help(benchmark_corpus.load_corpus)` prints the new wording naming directory-name order.
  - Execution state: performed

### Task group 2: Behavior unchanged

- [x] E-02 Re-run the direct order measurement and the benchmark corpus test modules after the edit, to show the documented order is the observed order and nothing regressed: copy fixture seeds `simple_commands` as `a_dir` and `migration` as `b_dir` into a temp root, call `load_corpus` on it, and print `[t.seed_path.name for t in tasks]` and `[t.task_class for t in tasks]`; then run `tests/test_benchmark_corpus.py`, `tests/test_benchmark_runners_reports.py`, and (if `btubm6` has executed and it exists) `tests/test_benchmark_corpus_restored_behavior.py`; then the bare routine gate.
  - Depends on: E-01
  - Expected outcome: the direct call prints `['a_dir', 'b_dir'] ['simple_commands', 'migration']` (name order, matching the new docstring); all named modules pass; bare `python3 -m pytest` passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). A docstring is not observable behavior, so this plan adds NO test asserting docstring text; the behavior the docstring now describes is already pinned by `btubm6` E-02(e).
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects `core`-marked tests (`conftest.pytest_collection_modifyitems`); explicit paths run everything non-slow in them.
- Do not edit a file another plan owns when not needed: `tests/test_benchmark_corpus.py` is `78g6ic`'s deliverable and `tests/test_benchmark_corpus_restored_behavior.py` is `btubm6`'s.
- Commit through `aw commit x8p9ek -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | direct call at lane HEAD `503f15cbd`: fixture seeds copied as `a_dir` (`simple_commands`) and `b_dir` (`migration`) into a temp root, then `load_corpus(root)` | Printed `['a_dir', 'b_dir'] ['simple_commands', 'migration']`. Order is by directory name, contradicting the docstring "sorted by (task_class, seed_id)". |
| F-02 | `rg load_corpus --type py` (excluding `.aw/`) | Callers: `tests/test_benchmark_corpus.py` `CorpusDeterminismTests.setUp` (fixture root), and `benchmark_reports` (imports `load_corpus`, calls `load_corpus(root)` on the fixture corpus, then iterates `tasks[:3]`). No spec or doc under `.aw/records/specs/` or `docs/` mentions `load_corpus` (`grep -rln load_corpus .aw/records/specs docs` is empty). |
| F-03 | `tests/benchmark_fixtures/corpus/` listing and each `task.json` `seed_id` | Seven seed directories, each named exactly its `task_class`, with `seed_id` `<class>-001`. So on the only corpus any caller loads, name order and `(task_class, seed_id)` order are identical; `benchmark_reports`'s `tasks[:3]` selection is the same under either. Choosing either contract changes no current caller's output. |
| F-04 | `btubm6` (approved, pending) E-02(e) and its `## Deferred / out of scope` | `btubm6` pins NAME order as a characterization and states "if `qtd3lj` changes the sort, it updates that test". A docstring fix leaves that test correct and unchanged; a sort change would require editing a file `btubm6` owns. |

## Proposed changes (ordered, validatable)

1. E-01 rewrites the `load_corpus` docstring to describe directory-name order (and the already-true refusal, skip, and propagation behaviors).
2. E-02 demonstrates by direct call and the existing benchmark test modules that behavior is unchanged and matches the new wording.

## Deferred / out of scope (with reason)

- Changing the sort to `(task_class, seed_id)` is declined (OQ-01): it is a behavior change with no caller that benefits (F-03), it would contradict `btubm6`'s approved characterization test (F-04), and directory-name order is already deterministic, which is the property the docstring says it is for.
  - Carrier-Declined: no work is owed; the docstring fix resolves the contradiction the item records.
- Adding a test that asserts the docstring wording is declined: it would pin text, not behavior (P16). The documented order is already behavior-tested by `btubm6` E-02(e).
  - Carrier-Declined: no work is owed; covered by `btubm6`.

## Scope check

- Over-scope: none. One docstring in one production file; no executable line changes.
- Under-scope: none. The item's single decision (which order is the contract) is made in OQ-01 and implemented by E-01; the item's alternative branch ("update btubm6's test") is not triggered by this decision.

## Required tests / validation

- Direct call (temp root with `a_dir`=`simple_commands`, `b_dir`=`migration`) printing names and classes, output pasted.
- `python3 -m pytest -o addopts="" -q tests/test_benchmark_corpus.py tests/test_benchmark_runners_reports.py` (plus `tests/test_benchmark_corpus_restored_behavior.py` if present), summary pasted.
- Bare `python3 -m pytest`, summary line pasted.
- `git diff agent_workflows/benchmark_corpus.py` pasted, showing only docstring lines changed.

## Spec / documentation sync

N/A: no spec or user-facing document describes `load_corpus` ordering (F-02); the docstring IS the documentation being corrected. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Which order is the contract: the documented `(task_class, seed_id)` or the implemented directory-name order?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: directory-name order; fix the docstring. Evidence: no caller can distinguish the two orders on the only corpus loaded anywhere (F-02, F-03), so the code's order is the de facto contract with zero migration cost; the approved sibling `btubm6` already pins name order (F-04); the docstring's stated purpose ("for determinism") is satisfied by name order; and the backlog item lists the docstring fix as a first option with "no behavior change, test stays". This is the least disruptive and fully reversible choice.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/benchmark_corpus.py` showing every changed line lies inside the `load_corpus` docstring and the new text names seed directory name order; paste `python3 -c "from agent_workflows import benchmark_corpus as c; print(c.load_corpus.__doc__)"` output; paste `git status --short` showing no other modified path besides this plan.
  - Observed evidence:
```diff
diff --git a/agent_workflows/benchmark_corpus.py b/agent_workflows/benchmark_corpus.py
index 056539f86..49f8caa91 100644
--- a/agent_workflows/benchmark_corpus.py
+++ b/agent_workflows/benchmark_corpus.py
@@ -142,7 +142,17 @@ def load_task(seed_path: Path) -> SeededTask:

 def load_corpus(corpus_root: Path) -> List[SeededTask]:
     """Load every seeded task under a corpus root. A corpus root contains one subdirectory per seed
-    (each with a task.json). Returns tasks sorted by (task_class, seed_id) for determinism."""
+    (each with a task.json).
+
+    Returns tasks sorted in ascending order of their seed directory name (the child name under
+    ``corpus_root``) for determinism. This is directory name order, not ``(task_class, seed_id)``
+    order; the two coincide only when each seed directory is named after its class (as in the
+    checked-in fixture corpus).
+
+    Raises :class:`CorpusError` if ``corpus_root`` is not a directory, or if any seed subdirectory
+    is malformed (errors from :func:`load_task` propagate). Non-directory children and subdirectories
+    without a ``task.json`` are skipped.
+    """
     corpus_root = Path(corpus_root)
     if not corpus_root.is_dir():
         raise CorpusError("corpus root is not a directory: {0}".format(corpus_root))
```

```
Load every seeded task under a corpus root. A corpus root contains one subdirectory per seed
(each with a task.json).

Returns tasks sorted in ascending order of their seed directory name (the child name under
``corpus_root``) for determinism. This is directory name order, not ``(task_class, seed_id)``
order; the two coincide only when each seed directory is named after its class (as in the
checked-in fixture corpus).

Raises :class:`CorpusError` if ``corpus_root`` is not a directory, or if any seed subdirectory
is malformed (errors from :func:`load_task` propagate). Non-directory children and subdirectories
without a ``task.json`` are skipped.
```

```
 M .aw/records/plans/pending/20261023-trimgap-36-x8p9ek-reconcile-load-corpus-docstring-with-its-seed-directory-name.ipd.md
 M agent_workflows/benchmark_corpus.py
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the direct-call output (produced by `benchmark_corpus.load_corpus`, created in E-02) reading `['a_dir', 'b_dir'] ['simple_commands', 'migration']`; paste the pytest summary line for the named benchmark modules with zero failures; paste the bare `python3 -m pytest` summary line with zero failures.
  - Observed evidence:
    Direct-call output:
    ```
    ['a_dir', 'b_dir'] ['simple_commands', 'migration']
    ```

    Named benchmark modules test run:
    ```
    54 passed in 0.64s
    ```
    (`python3 -m pytest -o addopts="" -q tests/test_benchmark_corpus.py tests/test_benchmark_runners_reports.py tests/test_benchmark_corpus_restored_behavior.py`)

    Bare pytest test run:
    ```
    1777 passed, 11 warnings in 32.13s
    ```
    (`aw suite`: cached result for tree 077be9a26991: 1777 passed, 11 warnings in 32.13s; bare `python3 -m pytest`: 1777 passed, 11 warnings in 34.74s)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01).
- Scope fence: `agent_workflows/benchmark_corpus.py` is the only declared path, and only its `load_corpus` docstring is intended to change; an out-of-scope edit is justified at finalize (`--scope-reason`).
- Paste ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit x8p9ek -- agent_workflows/benchmark_corpus.py <this plan>`, verify `git diff --cached --name-only`, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize`. Never `git mv` the plan to `executed/` by hand.
