# IPD: Restore behavioral test coverage for benchmark_corpus load_corpus and SeededTask.workspace_seed_path

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `3hurk1` (Set `trimgap`, group 12 of the `wo21z5` `## Filing plan`) records two `agent_workflows/benchmark_corpus.py` keys, `SeededTask.workspace_seed_path` and `load_corpus`, whose `return-none` mutants SURVIVED the surviving suite and were KILLED by the control file `tests/test_benchmark_corpus.py` (`wo21z5` `## Budget probe results`, final verdict `unguarded`), measured at baseline HEAD `f3afece92`. That control file had been deleted by suite trim `19313eed`. Since the baseline, executed sibling plan `78g6ic` (`trimgap` Order 19, commit `03241d58a`) restored `tests/test_benchmark_corpus.py` as a `core`-marked module, and a re-probe at HEAD `390d90f07` shows both recorded mutants are now killed by the routine suite (F-02). What remains unpinned is every behavior of the two keys other than "returns something non-None": `load_corpus` is only ever called on the one checked-in fixture root, so its refusal of a non-directory root, its skipping of non-seed children, its name-ordered return, its empty-root result, and its propagation of a malformed seed's `CorpusError` are reached by no test; and `workspace_seed_path` is asserted only indirectly, through `materialize_task`/`reset_task` hashes, so a mutant returning a wrong-but-existing directory (for example `seed_path` itself) is not named by any assertion of the path's value; existing tests catch such a mutant only indirectly, through side effects like the ground-truth leak guard (F-03, F-04).
- Scope: Add ONE new behavioral test module, `tests/test_benchmark_corpus_restored_behavior.py`, marked `core`, that drives `benchmark_corpus.load_corpus` against `tmp_path` corpus roots built by copying seeds from `tests/benchmark_fixtures/corpus/`, and asserts `SeededTask.workspace_seed_path` returns `seed_path / "workspace"`, an existing directory, for every fixture seed. EXCLUDES any change to `agent_workflows/benchmark_corpus.py` or any other production file, EXCLUDES editing `tests/test_benchmark_corpus.py` (owned by executed plan `78g6ic`), and EXCLUDES any change under `tests/benchmark_fixtures/`.
- Scope-Paths: tests/test_benchmark_corpus_restored_behavior.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 3hurk1
- Set: trimgap
- Order: 24
- Highest E allocated: 03
- Author: opencode
- Id: btubm6

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `3hurk1`. Re-probed both recorded `return-none` mutants at HEAD `390d90f07` against `tests/test_benchmark_corpus.py` + `tests/test_benchmark_runners_reports.py` (both killed; scratch edits reverted, `git diff agent_workflows/` empty) and measured every `load_corpus` branch by direct call before writing any expected outcome (F-02 through F-04).
- 2026-10-23 draft (opencode): created.

## Goal

Pin the observable contract of `load_corpus` (root validation, seed discovery, deterministic order, error propagation) and of `SeededTask.workspace_seed_path` (the exact executor-visible subtree) in the routine core tier, so a mutation that changes either key's result, not merely one that makes it return `None`, turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new behavioral test module

- [ ] E-01 Create `tests/test_benchmark_corpus_restored_behavior.py` with `pytestmark = pytest.mark.core`, importing `agent_workflows.benchmark_corpus as corpus`, with a module docstring naming backlog `3hurk1`, findings `wo21z5` group 12, and sibling plan `78g6ic`. Define `FIXTURE_CORPUS = Path(__file__).resolve().parent / "benchmark_fixtures" / "corpus"` and a helper `_copy_seed(name, dest)` that `shutil.copytree`s one fixture seed directory into `dest`. Use `tmp_path` only; spawn no subprocess.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, and is collected by a bare `python3 -m pytest` (it carries the `core` marker).
  - Execution state: pending

- [ ] E-02 Add `load_corpus` behavioral tests (F-03), each asserting a real return value or raised exception: (a) a nonexistent root and (b) a regular FILE passed as the root each raise `corpus.CorpusError` whose message contains `corpus root is not a directory`; (c) an empty directory returns `[]`; (d) a root holding only a subdirectory WITHOUT `task.json` and a loose top-level `loose.json` file returns `[]` (non-seed children skipped); (e) a root holding copies of fixture seeds `simple_commands` as `b_dir` and `migration` as `a_dir` returns exactly two `SeededTask`s whose `seed_path.name` list is `["a_dir", "b_dir"]` and whose `task_class` list is `["migration", "simple_commands"]`, proving order is by directory NAME; (f) the same root with an added `zz_bad/task.json` of `{"task_class": "nope", "seed_id": "x"}` raises `corpus.CorpusError` whose message contains `unknown task_class 'nope'` (a malformed seed is propagated, not skipped); (g) `load_corpus(str(FIXTURE_CORPUS))` (a `str`, not a `Path`) returns 7 tasks whose `task_class` set equals `set(corpus.TASK_CLASSES)` and whose every `seed_path` is a `Path`.
  - Depends on: E-01
  - Expected outcome: all seven `load_corpus` cases pass.
  - Execution state: pending

- [ ] E-03 Add `SeededTask.workspace_seed_path` tests (F-04): for every task from `corpus.load_corpus(FIXTURE_CORPUS)`, `t.workspace_seed_path() == t.seed_path / corpus.WORKSPACE_DIRNAME`, it `is_dir()`, it differs from `t.seed_path`, and it does NOT contain `corpus.GROUND_TRUTH_FILENAME` (the hidden truth sits beside, not inside, it); and for a hand-built `corpus.SeededTask("simple_commands", "s", {}, tmp_path / "seed")` whose directory does not exist, `workspace_seed_path()` still returns `tmp_path / "seed" / "workspace"` (a pure path computation that does not touch the filesystem).
  - Depends on: E-01
  - Expected outcome: the per-seed path, existence, and pure-computation assertions pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). Every assertion calls `load_corpus` or `workspace_seed_path` and checks a return value or raised exception; the asserted `CorpusError` message substrings are the user-facing error text, asserted only as a discriminator between the two refusal branches.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`), under a 30s budget. The new module carries `pytestmark = pytest.mark.core` and spawns no subprocess.
- Sibling precedent: `trimgap` children `5jevb2` and `33f8tn` add one new `*_restored_behavior.py` core-marked module per backlog item, make no production edit, and run mutation spot-checks as reverted scratch edits.
- Do not edit a file another executed plan owns when a new module suffices: `tests/test_benchmark_corpus.py` is the `78g6ic` deliverable.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Probe queue`, `## Budget probe results`, `## Filing plan` group 12 | Both keys: operator `return-none`, survivor `tests/test_benchmark_runners_reports.py` survived, control `tests/test_benchmark_corpus.py` killed, verdict `unguarded`, at baseline HEAD `f3afece92`. The control file did not exist at that baseline (`git cat-file -e f3afece92:tests/test_benchmark_corpus.py` fails). |
| F-02 | scratch `return None` edits to each key, then `python3 -m pytest -o addopts="" -q -p no:cacheprovider tests/test_benchmark_corpus.py tests/test_benchmark_runners_reports.py` at HEAD `390d90f07`, reverted with `git checkout --` | `workspace_seed_path` mutant: `3 failed, 42 passed in 0.51s`; `load_corpus` mutant: `6 failed, 39 passed in 0.49s`. Commit `03241d58a` (plan `78g6ic`) restored the control file after the baseline, so the probe-recorded mutants are now killed. The backlog item's remedy is still owed for the branches below. |
| F-03 | direct calls of `benchmark_corpus.load_corpus` | Nonexistent root and a file root raise `CorpusError("corpus root is not a directory: ...")`; empty dir -> `[]`; dir with only a `task.json`-less subdir and a loose file -> `[]`; seeds copied as `a_dir` (`migration`) and `b_dir` (`simple_commands`) -> names `['a_dir', 'b_dir']`; a sibling seed with `task_class` `nope` raises `CorpusError("seed ... has unknown task_class 'nope'")`; fixture root -> 7 tasks. No existing test reaches any branch except the fixture-root success path. |
| F-04 | direct call; `rg workspace_seed_path tests/` | `ts[0].workspace_seed_path() == ts[0].seed_path / 'workspace'` is True. The only test callers reach it indirectly through `materialize_task`/`reset_task`/`seed_workspace_hash`. Those compare two results of the same (possibly mutated) path against each other, so they catch a wrong path only when a side effect breaks (for example the ground-truth leak guard); no assertion names the path's value or its separation from `ground_truth.json`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module, fixture constant, and seed-copy helper.
2. E-02 pins `load_corpus` root refusal, empty and skip results, name ordering, error propagation, and `str` acceptance.
3. E-03 pins `SeededTask.workspace_seed_path` value, existence, separation from ground truth, and filesystem independence.

## Deferred / out of scope (with reason)

- Editing `tests/test_benchmark_corpus.py` to add these cases is out of scope: it is the executed `78g6ic` deliverable, and a new module gives the same core-tier reach without touching it.
  - Carrier-Declined: no work is owed; this plan's new module carries the coverage.
- The other `benchmark_corpus` keys (`load_task`, `hash_tree`, `materialize_task`, and so on) are out of scope: they belong to `78g6ic`'s 25-key slice, already executed.
  - Carrier-Declined: no work is owed; covered by executed plan `78g6ic`.

## Scope check

- Over-scope: none. One new test file is the only declared and changed path. No production code changes.
- Under-scope: none. Both keys named by `3hurk1` are covered by E-02 and E-03.

## Required tests / validation

- `python3 -m pytest tests/test_benchmark_corpus_restored_behavior.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest`: every test passes, summary line pasted. A core-tier wall-time overrun pre-existing on the host is reported, not a pass/fail bar; the bar is that the new module itself runs in under 1s.
- Mutation spot-checks as scratch edits to `agent_workflows/benchmark_corpus.py`, each followed by running only the new module and pasting the failure, then reverting with `git checkout -- agent_workflows/benchmark_corpus.py`: (1) `workspace_seed_path` returns `self.seed_path`; (2) `load_corpus` drops the `is_dir()` refusal (returns `[]` for a non-directory); (3) `load_corpus` drops the `(child / TASK_FILENAME).is_file()` filter; (4) `load_corpus` iterates `corpus_root.iterdir()` reversed; (5) `load_corpus` wraps `load_task` in `try/except CorpusError: continue`. Finally `git diff agent_workflows/` is empty.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is the backlog item still owed now that `78g6ic` restored the control file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: yes, narrowed. F-02 shows the probe's exact `return-none` mutants are now killed, so the item's recorded gap no longer reproduces as measured. But the remedy shape is "restore behavioral coverage", and F-03/F-04 show every `load_corpus` branch except the fixture-root success path, and the value of `workspace_seed_path`, remain unasserted. Adding that coverage is cheap, in scope for the item, and does not alter the item's requirements; closing the item with no work would rest on a narrower operator than the remedy names.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `?? tests/test_benchmark_corpus_restored_behavior.py` (plus this plan's own lifecycle edit); paste `python3 -m pytest --collect-only -q | rg -c test_benchmark_corpus_restored_behavior` (nonzero); paste the bare `python3 -m pytest` summary line with every test passed; paste `python3 -m pytest tests/test_benchmark_corpus_restored_behavior.py -o addopts="" -q` showing the module's runtime under 1s.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing each of the seven `load_corpus` cases (a) through (g) as PASSED, and the pasted failure output of mutation spot-checks (2), (3), (4) and (5) from `## Required tests / validation`, each run against the new module only and reverted afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing the `workspace_seed_path` tests as PASSED; the pasted failure output of mutation spot-check (1) (`workspace_seed_path` returns `self.seed_path`), reverted afterwards; and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01).
- Scope fence: `tests/test_benchmark_corpus_restored_behavior.py` is the only declared path; an out-of-scope edit is justified at finalize (`--scope-reason`).
- Paste ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (return values, raised exceptions), never source text or structure.
- Mutation spot-checks are scratch edits to `agent_workflows/benchmark_corpus.py` that must be reverted before commit; confirm with an empty `git diff agent_workflows/`.
- Commit only through `aw commit btubm6 -- tests/test_benchmark_corpus_restored_behavior.py`, verify `git diff --cached --name-only` lists only that path, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize`. Never `git mv` the plan to `executed/` by hand.
