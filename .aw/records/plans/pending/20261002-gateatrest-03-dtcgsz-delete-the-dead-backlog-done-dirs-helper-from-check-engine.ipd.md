# IPD: Delete the dead _backlog_done_dirs helper from check_engine

- Date: 2026-10-02
- Kind: child
- Concern: `check_engine._backlog_done_dirs` is a generator over `backlog/done/` directories with ZERO consumers anywhere in the tree. It has been dead since the commit that introduced it (`596dd9acb`, 2026-08-25), it sits DIRECTLY ABOVE `_staged_backlog_done_items` where the at-rest walk really lives, and it is shaped exactly like the start of that walk. A reader auditing the release-gate backstop therefore meets a plausible-looking seam that nothing reaches, and plan `b24o3q`'s review recorded it as finding F-08 precisely so a reviewer would not read it as the intended entry point.
- Scope: Delete the one unreachable function and nothing else. EXCLUDES touching `_BACKLOG_DONE_RE`, `_staged_backlog_done_items`, `check_release_gate_consistency` (either arm), `evaluate_blocking_close`, or any rule id or severity. EXCLUDES deleting, renaming or re-homing any other symbol (F-13 measures that no other dead private helper exists in the module, so there is nothing else to sweep even opportunistically). EXCLUDES adding a lint rule, a census test, or any guard that would pin the absence of a symbol (such a test is forbidden by the repository's no-code-pinning contract). EXCLUDES any behavior change: after this plan every check rule returns byte-identical findings.
- Scope-Paths: agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: y2vnr7
- Set: gateatrest
- Order: 3
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dtcgsz
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved

- 2026-10-02 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Re-measured at HEAD `ac9648ed5`: F-01 (AST census 1 def, 0 refs), F-04 (`596dd9acb` sole commit, 1 occurrence), F-06, F-07 (40/6 tests), F-08, F-09 (`release-gates` 0 findings), F-10 (F811 passes), F-13 (57 private functions, only `_backlog_done_dirs` unreferenced) all reproduce. Fixed: E-01's ambiguous padding/line-count (now exactly 7 lines, boundary verified in-memory with `ruff format --check`), an unspecified census command (now pasted verbatim), V-01's suite bar keyed to authoring-time failures (now the executor's own baseline), the post-gate backlog wording (item is already graduated; the runner's backlog close advances it), and two miscounts in F-02/F-03.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `y2vnr7`. Every row in the Findings table was MEASURED in this lane at HEAD `0b57aeff6` with a clean `git status`, not transcribed from the item. THE ITEM'S CENTRAL CLAIM REPRODUCES EXACTLY AND BY A STRONGER METHOD THAN THE ITEM USED: an AST census over every tracked `.py` file (so a shadowed name or a string reference cannot hide) finds exactly one `FunctionDef` named `_backlog_done_dirs` and ZERO `Name`, `Attribute` or string-constant references to it; `git grep` across the whole tree adds only prose hits in three `.aw/records/` artifacts (the item itself, plan `b24o3q`, and `b24o3q`'s review). THE AUTHORING ALSO ESTABLISHED THREE THINGS THE ITEM DID NOT RECORD, each of which narrows the risk. F-04: the function has been dead since BIRTH (`git log -S` returns exactly one commit, `596dd9acb`, and the helper had no caller in that same commit), so this is not a caller that was removed and may return. F-06: `_BACKLOG_DONE_RE` on the line below IS live (read by `_staged_backlog_done_items`), which is the adjacent-symbol trap this plan must not fall into. F-08: the at-rest arm this helper resembles was built on `backlog._iter_items` rather than on a done-dirs walk, so no future caller is waiting for it either. NO TEST IS ADDED, and that is a deliberate contract decision recorded in F-07 and in the Deferred section rather than an omission: a test asserting the symbol's absence would be exactly the symbol census `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid, so the validation is the full suite plus the F811 gate CI already runs.

## Goal

Remove one unreachable function from `agent_workflows/check_engine.py` so the release-gate backstop reads as what it is: a STAGED arm driven by `_staged_backlog_done_items` and an AT-REST arm driven by `backlog._iter_items`, with no third done-dirs walk suggesting a seam that nothing uses.

THE GOAL IS A PURE DELETION WITH NO BEHAVIOR DELTA. No rule changes id, severity, scope or finding set; no other symbol moves; no test is added or removed. Success is measured as "the suite's pass/fail set is unchanged and the release-gate rules still return exactly what they returned before", which is why this plan's validation is a before/after comparison rather than a new assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: delete the unreachable function

- [x] E-01 In `agent_workflows/check_engine.py`, delete the five-line function `_backlog_done_dirs` in its entirety (its `def` line, its `for root_rel in (".aw/records/backlog", ".agents/backlog"):` loop, and the `yield d`) together with the TWO blank lines that FOLLOW it, so the two blank lines that already PRECEDE it remain as the module's two-blank-line spacing between `evaluate_blocking_close`'s closing `return CloseVerdict(...)` and `_BACKLOG_DONE_RE = ...`. That is exactly SEVEN removed lines (5 code + 2 blank). Review verified this boundary in-memory: cutting from `def _backlog_done_dirs` up to (not including) `_BACKLOG_DONE_RE = ` removes 7 lines and `ruff format --check -` on the result exits 0.
  RE-CONFIRM DEADNESS AT EXECUTION TIME BEFORE DELETING, because this plan was authored against HEAD `0b57aeff6` and another lane may legitimately add a caller before it runs. Re-run the AST census (not a bare grep, which cannot tell a definition from a reference) and require ONE definition and ZERO references. Use exactly this command so the before and after runs are comparable, run from the repo root:
  `python3 -c 'import ast,subprocess,collections as C;N="_backlog_done_dirs";c=C.Counter();fs=[f for f in subprocess.check_output(["git","ls-files","*.py"],text=True).split() if not f.startswith((".aw/","build/","dist/"))];[c.update([(("def" if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==N else "ref" if (isinstance(n,ast.Name) and n.id==N) or (isinstance(n,ast.Attribute) and n.attr==N) else "str" if isinstance(n,ast.Constant) and isinstance(n.value,str) and N in n.value else None),f)]) for f in fs for n in ast.walk(ast.parse(open(f,encoding="utf-8").read()))];print({k:v for k,v in c.items() if k[0]})'`
  Review ran it at HEAD `ac9648ed5` and it printed `{('def', 'agent_workflows/check_engine.py'): 1}`. IF A CALLER NOW EXISTS, DO NOT DELETE: mark this item `blocked`, record the caller, and report, because the premise of the whole plan has expired.
  DO NOT TOUCH THE TWO ADJACENT SYMBOLS, which is the one real hazard here. `_BACKLOG_DONE_RE` on the line immediately BELOW is LIVE: `_staged_backlog_done_items` calls `.search(new_path...)` on it (F-06). `evaluate_blocking_close`'s closing `return CloseVerdict(True, "ok", "unchecked transition", (), None)` immediately ABOVE is the predicate's default arm and is live (F-05). Deleting either would change behavior; the deletion boundary is exactly the `def` and its body.
  ADD NOTHING IN ITS PLACE. No tombstone comment, no `# removed by ...` marker. The record of why it went lives in this plan, in the backlog item, and in the commit message; a comment asserting the absence of code is the prose form of the symbol-census pin F-07 rules out.
  - Depends on: none
  - Expected outcome: `agent_workflows/check_engine.py` is exactly 7 lines shorter (5 code lines plus the 2 trailing blank lines), and no tracked `.py` file defines or references `_backlog_done_dirs` (prose mentions in `.aw/records/` remain and are history, see Spec sync); the AST census command above prints `{}`; `python3 -c "from agent_workflows import check_engine"` imports clean; `python3 -m ruff format --check agent_workflows/check_engine.py` reports the file unchanged by formatting.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A DELETION IS NOT AUTOMATICALLY WELCOME HERE, AND THE REPOSITORY SAYS SO IN CODE. `host_adapters` carries an in-source warning that one unused-looking symbol is "an extension seam, NOT dead code to prune", `backlog`'s window comment states it is "deliberately RETAINED after the corpus migration as cheap insurance; it is not dead code", and `tests/test_status_set.py` carries a comment telling a future reader not "to delete the `Type mismatch` refusal as dead code; it is not dead". So the bar for deleting is evidence that the symbol is unreachable AND that nobody declared it a seam; F-01 through F-04 and F-08 supply both halves for this one.
- NO CODE-STRUCTURE PINS, WHICH DECIDES THIS PLAN'S TEST SHAPE. `AGENTS.md` forbids tests that "assert on caller counts, symbol censuses, or module line counts as a proxy for correctness", and `GUIDING_PRINCIPLES.md` P16 is cited as the authority. This plan therefore adds no test; see F-07.
- THE ONE SANCTIONED STATIC GATE IS `F811`, AND IT IS A CI STEP, NOT A TEST. `.github/workflows/tests.yml` runs `ruff check --no-cache --select F811 --target-version py312 --config 'lint.dummy-variable-rgx="^$"' agent_workflows/ tests/ tools/`, and `GUIDING_PRINCIPLES.md` records why that is not a P16 violation (it reports a condition under which the shipped module's behavior is already wrong). The `dummy-variable-rgx` override is load-bearing for THIS plan's verification because without it ruff exempts leading-underscore names, which is exactly what `_backlog_done_dirs` is.
- CITE BY SYMBOL, NOT BY BARE OFFSET. Spec `ipd-structure-and-linting` Section 10.2 permits a line number only as a trailing convenience appended to a symbol or quoted string; this plan cites `module.function` and quoted source throughout.
- RUN THE SUITE BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`.

## Findings

Every row was measured in this lane at HEAD `0b57aeff6` with a clean `git status`.

| Id | Finding | Evidence |
| :--- | :--- | :--- |
| F-01 | THE ITEM'S CLAIM REPRODUCES UNDER AST CENSUS, which is stronger than the grep the item used. | An `ast.walk` over every tracked `.py` file outside `.git`/`.aw`/`__pycache__`/`build`/`dist` counting `FunctionDef`/`AsyncFunctionDef` named `_backlog_done_dirs`, plus `ast.Name`, `ast.Attribute` and string-constant references to it, printed `{('def', 'agent_workflows/check_engine.py'): 1}` and nothing else: one definition, zero references, zero string mentions. |
| F-02 | A whole-tree `git grep` adds only PROSE hits, so no config, hook template, workflow or doc reaches it either. | `git grep -n "_backlog_done_dirs"` returns the `def` in `agent_workflows/check_engine.py` plus `.aw/records/` prose lines in three artifacts (corrected at review from "four lines"; re-measured at `ac9648ed5`, excluding this plan's own mentions): the backlog item's Summary (1 line), plan `b24o3q` (3 lines: its reviewed history entry, its F-08 row, its Deferred row), and `b24o3q`'s review record (2 lines). All are history records. The repository's `.git/hooks/` contains no match. |
| F-03 | It is unreachable by dynamic lookup too, so "no static caller" is not hiding a runtime one. | `check_engine` declares no `__all__`, no `globals()[...]` lookup and no `getattr(check_engine, ...)` indirection; it has six `getattr(` sites (corrected at review from "five"): five target record objects (`rec.id6`, `dec.basis`/`chosen`/`alternatives`, `result.diagnostics`) and the sixth, `getattr(_authoring, "_AUTHORING_PLACEHOLDERS", ())`, targets the `ipd_authoring` module with a fixed literal name, so none can resolve `_backlog_done_dirs`. No module in `agent_workflows/` does `getattr(check_engine, ...)` or `getattr(_ce, ...)`. No `from ... import *` exists anywhere in `agent_workflows/`. |
| F-04 | IT HAS BEEN DEAD SINCE BIRTH, so this is not a removed caller that might return. | `git log --all --oneline -S'_backlog_done_dirs' -- agent_workflows/` returns exactly ONE commit, `596dd9acb` ("feat(release-gate): shared close-legitimacy predicate + backlog done gate + aw check rules (orb9zb)", 2026-08-25), and `git grep -c` at that same commit counts 1 occurrence in the file, i.e. the definition with no call. |
| F-05 | The symbol ABOVE the deletion boundary is live and must not be disturbed. | The lines immediately preceding are `evaluate_blocking_close`'s final arm, `return CloseVerdict(True, "ok", "unchecked transition", (), None)`; the predicate is consumed by `backlog.run_set`, `status_set.run_set_command`, `set_records.close_on_answer`, `check_engine.check_release_gate_consistency` (both arms) and the opt-in close-gate hook. |
| F-06 | The symbol BELOW the deletion boundary is live and must not be disturbed. | `_BACKLOG_DONE_RE = _re.compile(r"(?:^|/)backlog/done/[^/]+\.md$")` is read by `_staged_backlog_done_items` as `_BACKLOG_DONE_RE.search(new_path.replace("\\", "/"))`, and that function is called from `check_release_gate_consistency`'s Rule 1. This adjacency is the one real hazard in an otherwise trivial deletion. |
| F-07 | NO TEST CAN LEGITIMATELY PIN THIS DELETION, so adding one would itself be a defect. | `AGENTS.md` forbids tests that "assert on caller counts, symbol censuses, or module line counts as a proxy for correctness" and forbids reading production source with `inspect`, `ast`, regex or substring search. A test asserting `not hasattr(check_engine, "_backlog_done_dirs")` is a symbol census by definition. The existing coverage is the right shape instead: `tests/test_check_engine_release_gate.py` drives the real rules over synthetic fixtures (40 `def test_` methods, 6 of them `test_rule_blocking_item_closed_at_rest_*` cases), and its verdicts are what must stay identical. |
| F-08 | NO FUTURE CALLER IS WAITING FOR IT EITHER: the at-rest walk it resembles was built on a DIFFERENT iterator. | `check_release_gate_consistency`'s at-rest arm iterates `backlog._iter_items(repo_root)` and filters on `_status_meta(item_txt) != "done"`, not on a done-directory walk. `_iter_items` covers all five `STATUS_DIRS` across both `BACKLOG_ROOTS`, and measured on this tree it returns 887 items in 11.25 ms against a done-dirs-only walk's 580 in 3.81 ms, so the surviving design is deliberate (it reads the FIELD, which can disagree with the directory) and not a performance compromise awaiting this helper. |
| F-09 | The release-gate surface is GREEN right now, so a post-deletion comparison is a meaningful test. | `aw check release-gates --agent` emits `{"outcome":"conforms","exit":0,"findings":0}`; in-process, `check_release_gate_consistency(repo)` returns 0 findings and `check_release_gate_consistency(repo, at_rest=True)` returns 0. A clean-to-clean comparison is weak on its own, which is why V-01 also demands the suite's 4624-pass figure be reproduced. |
| F-10 | The F811 CI gate currently PASSES, so this deletion cannot be hiding a duplicate definition. | `python3 -m ruff check --no-cache --select F811 --target-version py312 --config 'lint.dummy-variable-rgx="^$"' agent_workflows/ tests/ tools/` reports `All checks passed!` (with two pre-existing unrelated `# noqa` directive warnings in `agy_runipd.py` and `oc_runipd.py`). |
| F-11 | The `chore` classification is correct: no user-perceptible impact exists in either direction. | The function is never executed, so no command a user waits on is slower by one byte and no output is wrong. `AGENTS.md`'s inefficiency-is-a-defect test requires a measured user-perceptible cost; dead code that never runs has none. The cost is purely to a reader of the release-gate backstop, which is a maintainability concern. |
| F-12 | The `done`-vs-directory distinction the surviving design relies on currently holds on this tree, which is why no behavior hangs on the choice today. | Comparing `_status_meta` against the parent directory name across all 887 items via `backlog._iter_items` found 0 mismatches. Recorded so a reviewer knows the at-rest arm's field-based filter is not currently masking a divergence this deletion could expose; it masks none. |
| F-13 | THIS IS THE ONLY DEAD PRIVATE FUNCTION IN THE MODULE, so the plan is complete rather than the first of a series. | A census parsing `check_engine` for its top-level private `FunctionDef`s (57 of them) and then AST-walking every `.py` file under `agent_workflows/`, `tests/` and `tools/` for `Name`, `Attribute` or string-constant references to each returned exactly one zero-reference name: `['_backlog_done_dirs']`. All 56 others are reached. This answers OQ-01 and is why no sibling deletion is deferred. |

## Proposed changes (ordered, validatable)

1. Delete the unreachable `_backlog_done_dirs` function from `agent_workflows/check_engine.py`, re-confirming deadness by AST census immediately before the edit and leaving both adjacent symbols untouched (E-01).

## Deferred / out of scope (with reason)

- SWEEPING OTHER DEAD PRIVATE HELPERS OUT OF `check_engine` IN THE SAME PASS. There are none to sweep: F-13's census over all 57 top-level private functions in the module found `_backlog_done_dirs` to be the ONLY one with zero references anywhere in `agent_workflows/`, `tests/` or `tools/`. This row exists because the obvious reviewer question ("is this the first of twelve?") deserves a measured answer rather than silence.
  - Carrier-Declined: NO DEFECT EXISTS HERE. The population is empty by measurement, so there is nothing to carry.
- ADDING A GENERAL DEAD-CODE GATE (a `vulture` run, an unreferenced-private-symbol check, or a CI census over `agent_workflows/`). Out of scope by two independent reasons: it is a tooling decision with repository-wide consequences far beyond one five-line function, and `GUIDING_PRINCIPLES.md` explicitly declines to read the F811 precedent as general permission ("this does not re-open `inspect`, `ast`, or regex reads of production source in tests"). A dead-code gate would need its own spec and its own measured false-positive budget, since the repository demonstrably contains deliberately-retained unused seams (see the Step 0 conventions).
  - Carrier-Declined: NO DEFECT EXISTS HERE. The absence of a dead-code linter is a deliberate posture, not a bug; adopting one is a feature decision for a maintainer.
- ADDING A TEST THAT ASSERTS THE SYMBOL IS GONE. Explicitly refused, not merely deferred: F-07 measures that such a test is the symbol census `AGENTS.md` forbids. The behavior-preserving property IS tested, by the existing `tests/test_check_engine_release_gate.py` suite whose verdicts V-01 requires to be unchanged.
  - Carrier-Declined: NO DEFECT EXISTS HERE. Declining to add a forbidden test is compliance, not a coverage gap.
- WIDENING `check.blocking-item-closed-without-gate` FROM STAGED SCOPE, or otherwise changing either arm of `check_release_gate_consistency`. Already owned elsewhere: pending plan `1hrlp3` (from item `mbjuv5`) holds the audit of historically closed gated items and explicitly defers the scope widening with its own carrier. This plan must not touch that surface.
  - Carrier-Declined: NO DEFECT EXISTS HERE FOR THIS PLAN. The concern is real and is already carried by `1hrlp3`; duplicating it here would create two owners for one change.

## Scope check

- Over-scope: none. The single E-item deletes one function in the one declared path. Three candidate paths were checked and need NO change: `tests/test_check_engine_release_gate.py`, because F-01 measures no test references the symbol and F-07 explains why none should be added; `.github/workflows/tests.yml`, because the F811 gate it runs already passes (F-10) and a deletion cannot introduce a duplicate definition; and `agent_workflows/engine.py`, because the opt-in close-gate hook template it writes invokes `python3 -m agent_workflows backlog-blocking-close-gate` and names no private helper (F-02 found no hook-template match).
- Under-scope: the plan audits `check_engine`'s 57 top-level PRIVATE functions for deadness (F-13) and does NOT extend that census to the module's 37 public `check_*` symbols, which are reached by registry and CLI dispatch rather than by direct call and so need a different reachability question than an AST reference count. It also does not re-verify each of `evaluate_blocking_close`'s consumers individually; F-05 establishes that the predicate above the deletion boundary is live, which is all the deletion boundary turns on.

## Required tests / validation

- Bare `python3 -m pytest` (the repository contract; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so do not add flags). RE-ESTABLISH THE BASELINE IN YOUR OWN LANE BEFORE THE EDIT and paste it; do NOT compare against the figure below, which will have expired. Authoring measured `3 failed, 4624 passed, 2 skipped` in 120.16s at HEAD `0b57aeff6` with a clean `git status`, i.e. BEFORE any edit. THE THREE FAILURES ARE PRE-EXISTING AND ARE NOT THIS PLAN'S: `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. None references `_backlog_done_dirs` (F-01 verified by AST census that NO file does). If any is still red at execution, record it as pre-existing by reproducing it at the baseline BEFORE the edit; do not fix them here and do not let them mask a real regression.
- `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_check_engine.py -o addopts=""` for per-test counts on the two suites that exercise the edited module's release-gate surface, run BEFORE and AFTER so the counts can be compared rather than merely observed.
- THE AST CENSUS FROM F-01, re-run before the edit (expecting 1 definition, 0 references, which authorizes the deletion) and after (expecting 0 definitions, 0 references).
- `python3 -m ruff check --no-cache --select F811 --target-version py312 --config 'lint.dummy-variable-rgx="^$"' agent_workflows/ tests/ tools/`, the gate CI runs, plus `python3 -m ruff format --check agent_workflows/check_engine.py` to prove the deletion left no formatting churn for the pre-commit formatter to rewrite.
- `aw check release-gates --agent` and an in-process comparison of `check_release_gate_consistency(repo)` and `check_release_gate_consistency(repo, at_rest=True)` finding counts before and after (F-09 recorded both as 0).
- `aw ipd lint --phase pre-transition` must conform before any terminal transition.

## Spec / documentation sync

- N/A, WITH REASON, AND THE REASON IS CHECKED RATHER THAN ASSUMED. No spec, README or managed-block paragraph names `_backlog_done_dirs`: F-02's whole-tree `git grep` found its only prose mentions in three `.aw/records/` artifacts, and all three are RECORDS OF HISTORY that must not be edited. Specifically, plan `b24o3q` is in `.aw/records/plans/executed/` and its F-08 row and Deferred row state that it deliberately did not touch this helper, which was TRUE when it executed; `AGENTS.md` forbids changing what an executed plan records, and rewriting those lines would falsify history to match a later change. The same holds for `b24o3q`'s review record. The backlog item `y2vnr7` is the third; it is already `graduated`, and the runner's backlog-close step advances it to `done` once this plan executes (see the gate).
- NO SPEC IS AMENDED, so `- Scope-Paths:` declares no `.spec.md` file. The release-gate contract documented in `AGENTS.md` and in the backlog README describes rules, severities and the three legitimacy paths; this deletion changes none of them, which is the behavior-identity property V-01 requires evidence for.

## Open questions

### OQ-01: Are there OTHER dead private helpers in `check_engine` that should be swept in the same pass?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED NO, FROM REPOSITORY EVIDENCE RATHER THAN BY JUDGEMENT, and recorded because it is the first question a reviewer of a dead-code deletion asks. F-13 measures the complete population: parsing `check_engine` for its 57 top-level private `FunctionDef`s and then AST-walking every `.py` file under `agent_workflows/`, `tests/` and `tools/` for `Name`, `Attribute` or string references to each yields exactly ONE zero-reference name, `_backlog_done_dirs`. There is therefore no sweep to decline and no sibling item to file. NON-BLOCKING, and now moot: the answer changes nothing in E-01 or V-01 either way. HONEST LIMIT ON THAT CENSUS, stated so it is not trusted further than it holds: it covers the three source trees named and the three reference shapes named, so a reference built by string concatenation at runtime would evade it. That residual risk is already carried by V-01's requirement to re-run the census and the full suite immediately before and after the edit, which is a behavioral check rather than a static one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste ALL SIX of the following, in this order. (1) THE PRE-EDIT AST CENSUS, the exact command given in E-01, printing `{('def', 'agent_workflows/check_engine.py'): 1}` and nothing else, which is what authorizes the deletion at execution time rather than at authoring time; if it shows a caller, this item is `blocked`, not `pass`. (2) THE POST-EDIT AST CENSUS, the same command, printing `{}`, plus `git grep -n "_backlog_done_dirs"` output showing only `.aw/records/` prose hits and no `agent_workflows/` hit. (3) THE `git diff` OF `agent_workflows/check_engine.py`, which must show ONLY removed lines, must contain the removed `def _backlog_done_dirs` and its `yield d`, and must NOT touch the `return CloseVerdict(True, "ok", "unchecked transition", (), None)` above it or the `_BACKLOG_DONE_RE = _re.compile(...)` below it (F-05, F-06); state the removed line count, which must be 7 (`git diff --numstat agent_workflows/check_engine.py` showing `0	7`). (4) THE BEHAVIOR-IDENTITY COMPARISON: a Python session printing `len(check_release_gate_consistency(repo))` and `len(check_release_gate_consistency(repo, at_rest=True))` AFTER the edit, beside the pre-edit figures you measured yourself, plus `aw check release-gates --agent` output showing `"exit":0`. (5) THE SUITE, BEFORE AND AFTER: the bare `python3 -m pytest` summary line from your own pre-edit baseline and from after the edit, with the pass count IDENTICAL and the failure set IDENTICAL to YOUR OWN pre-edit baseline's failure set (the three failures named in Required tests are authoring-time context, not the bar; any failure present after but not before is a regression and this item is `failed`); plus the `-o addopts=""` per-test counts for `tests/test_check_engine_release_gate.py tests/test_check_engine.py` before and after. (6) THE STATIC GATES: `ruff check --select F811 ...` reporting `All checks passed!` and `ruff format --check agent_workflows/check_engine.py` reporting no file would be reformatted. A pasted summary line alone is NOT sufficient evidence for this item, because a pure deletion's whole risk is that it removed one line too many, and only the diff and the before/after comparison can show it did not.
  - Observed evidence:
    (1) THE PRE-EDIT AST CENSUS:
    ```
    $ python3 -c 'import ast,subprocess,collections as C;N="_backlog_done_dirs";c=C.Counter();fs=[f for f in subprocess.check_output(["git","ls-files","*.py"],text=True).split() if not f.startswith((".aw/","build/","dist/"))];[c.update([(("def" if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==N else "ref" if (isinstance(n,ast.Name) and n.id==N) or (isinstance(n,ast.Attribute) and n.attr==N) else "str" if isinstance(n,ast.Constant) and isinstance(n.value,str) and N in n.value else None),f)]) for f in fs for n in ast.walk(ast.parse(open(f,encoding="utf-8").read()))];print({k:v for k,v in c.items() if k[0]})'
    {('def', 'agent_workflows/check_engine.py'): 1}
    ```
    Measured at pre-edit baseline: exactly 1 definition, 0 references across all tracked Python files.

    (2) THE POST-EDIT AST CENSUS:
    ```
    $ python3 -c 'import ast,subprocess,collections as C;N="_backlog_done_dirs";c=C.Counter();fs=[f for f in subprocess.check_output(["git","ls-files","*.py"],text=True).split() if not f.startswith((".aw/","build/","dist/"))];[c.update([(("def" if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==N else "ref" if (isinstance(n,ast.Name) and n.id==N) or (isinstance(n,ast.Attribute) and n.attr==N) else "str" if isinstance(n,ast.Constant) and isinstance(n.value,str) and N in n.value else None),f)]) for f in fs for n in ast.walk(ast.parse(open(f,encoding="utf-8").read()))];print({k:v for k,v in c.items() if k[0]})'
    {}
    ```
    ```
    $ git grep -n "_backlog_done_dirs" agent_workflows/
    (exit 1, zero matches)
    ```
    `git grep -n "_backlog_done_dirs"` across the entire tree shows only historical prose in `.aw/records/plans/`, `.aw/records/reviews/`, and `.aw/records/backlog/`, with zero matches in `agent_workflows/`.

    (3) THE git diff OF agent_workflows/check_engine.py:
    ```
    $ git diff --numstat agent_workflows/check_engine.py
    0	7	agent_workflows/check_engine.py
    ```
    ```diff
    $ git diff agent_workflows/check_engine.py
    diff --git a/agent_workflows/check_engine.py b/agent_workflows/check_engine.py
    index 0ef2a1ddb..1c202c025 100644
    --- a/agent_workflows/check_engine.py
    +++ b/agent_workflows/check_engine.py
    @@ -5074,13 +5074,6 @@ def evaluate_blocking_close(
         return CloseVerdict(True, "ok", "unchecked transition", (), None)


    -def _backlog_done_dirs(repo_root: Path):
    -    for root_rel in (".aw/records/backlog", ".agents/backlog"):
    -        d = Path(repo_root) / root_rel / "done"
    -        if d.is_dir():
    -            yield d
    -
    -
     _BACKLOG_DONE_RE = _re.compile(r"(?:^|/)backlog/done/[^/]+\.md$")

    ```
    Shows ONLY removed lines (0 additions, 7 deletions), containing `def _backlog_done_dirs` and its body, leaving `return CloseVerdict(...)` above and `_BACKLOG_DONE_RE = _re.compile(...)` below completely untouched with 2 blank lines preserved between them.

    (4) THE BEHAVIOR-IDENTITY COMPARISON:
    Pre-edit in-process checks:
    ```
    $ python3 -c 'from pathlib import Path; from agent_workflows.check_engine import check_release_gate_consistency; repo = Path("."); print("unstaged:", len(check_release_gate_consistency(repo))); print("at_rest:", len(check_release_gate_consistency(repo, at_rest=True)))'
    unstaged: 0
    at_rest: 0
    ```
    Post-edit in-process checks:
    ```
    $ python3 -c 'from pathlib import Path; from agent_workflows.check_engine import check_release_gate_consistency; repo = Path("."); print("unstaged:", len(check_release_gate_consistency(repo))); print("at_rest:", len(check_release_gate_consistency(repo, at_rest=True)))'
    unstaged: 0
    at_rest: 0
    ```
    Post-edit CLI gate:
    ```
    $ python3 -m agent_workflows check release-gates --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}
    ```

    (5) THE SUITE, BEFORE AND AFTER:
    Pre-edit focused tests:
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py tests/test_check_engine.py -o addopts=""
    ======================== 90 passed in 68.84s (0:01:08) =========================
    ```
    Post-edit focused tests:
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py tests/test_check_engine.py -o addopts=""
    ============================= 90 passed in 33.31s ==============================
    ```
    Pre-edit bare pytest suite baseline:
    ```
    $ python3 -m pytest
    =========================== short test summary info ============================
    FAILED tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs
    FAILED tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    FAILED tests/test_oc_runipd.py::HostReviewAliasExpansionTests::test_alias_freezes_the_same_run_state_as_the_canonical_invocation
    4 failed, 4947 passed, 2 skipped, 3 warnings in 964.18s (0:16:04)
    ```
    Post-edit bare pytest suite:
    ```
    $ python3 -m pytest
    =========================== short test summary info ============================
    FAILED tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit
    FAILED tests/test_oc_runipd.py::HostReviewAliasExpansionTests::test_alias_freezes_the_same_run_state_as_the_canonical_invocation
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    3 failed, 4948 passed, 2 skipped, 3 warnings in 562.60s (0:09:22)
    ```
    The 3 post-edit failures are a strict subset of the 4 pre-edit baseline failures (test_box_renderer_invariants_across_swept_inputs passed on the second run; zero regressions).

    (6) THE STATIC GATES:
    ```
    $ python3 -m ruff check --no-cache --select F811 --target-version py312 --config 'lint.dummy-variable-rgx="^$"' agent_workflows/ tests/ tools/ && python3 -m ruff format --check agent_workflows/check_engine.py
    warning: Invalid `# noqa` directive on agent_workflows/agy_runipd.py:74: expected code to consist of uppercase letters followed by digits only (e.g. `F401`)
    warning: Invalid `# noqa` directive on agent_workflows/oc_runipd.py:830: expected code to consist of uppercase letters followed by digits only (e.g. `F401`)
    All checks passed!
    1 file already formatted
    ```
    Clean import check:
    ```
    $ python3 -c "from agent_workflows import check_engine"
    (exit 0, clean import)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

NEITHER SIZE THRESHOLD IS APPROACHED, so the assessment is `standard` and no exception rationale is owed. Recorded for a reviewer who may expect a second E-item: a single-E-item plan is right-sized here because the change is one atomic deletion of one unreachable function in one file, with no second deliverable to split off. The item names exactly one symbol, F-07 establishes that no test may be added, and the Spec sync section establishes that no document may be edited, so splitting would produce an E-item with nothing to do. The plan's weight sits in the EVIDENCE (thirteen measured findings and a six-part validation) rather than in the edit, which is the correct shape for a deletion whose only real risk is taking an adjacent line with it. Per the spec, these thresholds are review triggers and not targets, and an author must not pad a small plan toward them.

This plan is `to-review` and carries NO `- Readiness:` field, because that field is an output of `/plan-review` and writing it here would forge an attestation no review performed. It requires explicit human approval before execution.

EXECUTION CONTRACT. The executor commits only `agent_workflows/check_engine.py`, through `aw commit <plan> -- agent_workflows/check_engine.py`, never `git add -A` and never `--no-verify`, and does not push. The suite is run bare per the repository contract and the ACTUAL output is pasted into V-01's Observed evidence block; V-01 may not be marked `pass` from E-01's execution checkmark. IF THE PRE-EDIT CENSUS FINDS A CALLER, STOP: mark E-01 `blocked`, mark V-01 `blocked`, leave the file untouched, and report that the plan's premise expired, because another lane adding a legitimate caller makes this deletion wrong rather than merely harder.

POST-GATE LIFECYCLE. After V-01 is `pass` with concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled transition, never by a hand-rolled `git mv` or a hand-edited `- Status:`. Under `aw oc run` / `aw agy run` the RUNNER performs that finalize; when executing by hand, the executor runs `aw ipd finalize` itself. Backlog item `y2vnr7` is ALREADY `graduated` (it sits in `.aw/records/backlog/graduated/`); once this plan, its only `From-Backlog` carrier, is executed, the runner's backlog-close step (`runner_shared.process_backlog_close`) is what advances it to `done`. The executor does not hand-edit its status either way.
