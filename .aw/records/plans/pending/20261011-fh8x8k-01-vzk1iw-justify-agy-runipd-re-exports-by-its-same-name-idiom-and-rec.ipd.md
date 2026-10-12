# IPD: Justify agy_runipd re-exports by its same-name idiom and record the module export rule

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `fh8x8k`: `agent_workflows/oc_runipd.py` declares an `__all__` and `agent_workflows/agy_runipd.py` declares none, so `agy_runipd`'s deliberate re-exports can only be kept alive by `# noqa: F401` plus prose, and that prose is exactly what decayed to produce backlog `s4jctz`. Executed plan `h0zk2g` left `agy_runipd` on a re-justified `noqa` and recorded the residual asymmetry as its OQ-02 (Carrier `fh8x8k`). The item also asks for a decision on the shim asymmetry (`tools/ipdrunner/runagy.py` copies `vars(agy_runipd)` wholesale while `tools/ipdrunner/runipd.py` assigns five names) and for a stated RULE, since `runner_shared` also has no `__all__`.
- Scope: Remove BOTH `# noqa: F401` directives from `agy_runipd` by moving each re-export onto a form ruff recognizes without a suppression, WITHOUT adding an `__all__`: the `_read_id` binding becomes a plain module-level assignment from `selectors.read_front_matter_id`, and the `assert_child_tool_identity as assert_child_tool_identity` import (already the same-name idiom) loses its now-unused `noqa`. Rewrite the comments that describe the old mechanism (in `agy_runipd` and the one `oc_runipd` sentence that describes `agy_runipd`). Pin the shim's live consumer of `_read_id` with an outcome test inside `tests/`. Record the export rule and the shim decision as a `DECISIONS.md` entry. DOES NOT add `__all__` to `agy_runipd` or `runner_shared`, DOES NOT change `oc_runipd.__all__`, DOES NOT change either shim, and DOES NOT change which reader `_read_id` binds to.
- Scope-Paths: agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, tests/test_runner_shared.py, DECISIONS.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: fh8x8k
- Set: fh8x8k
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: vzk1iw

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `fh8x8k` at HEAD `d74169f1b`; resolves `h0zk2g` OQ-02 without an `__all__`, measured under ruff `0.16.3` and hook-pinned `0.4.4`.

## Goal

Make every deliberate re-export in `agy_runipd` self-evident to ruff with no `# noqa: F401`, so no prose justification can rot, and write down the rule for how host runner modules justify re-exports so the next module does not reopen the question.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: remove the suppressions from agy_runipd

- [ ] E-01 In `agent_workflows/agy_runipd.py`, replace the line `from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - re-export for tools/ipdrunner/runagy.py, ...` with `from agent_workflows import selectors as _selectors` (the alias avoids shadowing, since `expand_selectors` takes a parameter named `selectors`), and add the binding `_read_id = _selectors.read_front_matter_id` as a module-level assignment placed AFTER the module's last top-level import statement (`from agent_workflows import agy_models` at HEAD), never between imports: an assignment inside the import region triggers `E402` on every later import under the hook-pinned ruff (measured, F-4).
  - Depends on: none
  - Expected outcome: `agy_runipd._read_id is selectors.read_front_matter_id` remains True; the `_read_id` line carries no `noqa`; ruff `F401`, `E402` and `RUF100` are clean on the file under both ruff versions.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/agy_runipd.py`, delete the trailing `  # noqa: F401` from `assert_child_tool_identity as assert_child_tool_identity,` in the `from agent_workflows.runner_shared import (` block that also imports `ToolIdentityError`. The same-name form already marks it as an intentional export, so the directive is unused (ruff reports `RUF100 Unused noqa directive` on it at HEAD under both versions, F-3).
  - Depends on: E-01
  - Expected outcome: `grep -c "noqa: F401" agent_workflows/agy_runipd.py` prints `0`; `agy_runipd.assert_child_tool_identity is runner_shared.assert_child_tool_identity` remains True.
  - Execution state: pending

### Task group 2: correct the prose

- [ ] E-03 Rewrite the comment block in `agent_workflows/agy_runipd.py` beginning `# \`_read_id\` F401 suppression is retained per s4jctz (h0zk2g / sznlsf).` so it states what is true after E-01: the binding is a module-level assignment, which ruff never reports as an unused import, so no suppression exists to justify; its one live consumer is `tools/ipdrunner/runagy.py` (read as `driver._read_id` in `tools/ipdrunner/test_runagy.py::AgyParserAndDiscoveryTests::test_read_deps_and_set`) and it is pinned in the bare suite by E-04's test; and point at the `DECISIONS.md` entry from E-05 for the rule. Keep the permissive-reader disclosure. In `agent_workflows/oc_runipd.py`, replace the single sentence `# In contrast, \`agy_runipd\` has no \`__all__\` and retains a noqa F401 directive.` with one stating that `agy_runipd` has no `__all__` and binds `_read_id` by module-level assignment instead (citing the same entry). Change nothing else in `oc_runipd.py`. Write the prose so it contains no literal `# noqa` token (h0zk2g measured that such prose triggers ruff's `Invalid # noqa directive` warning).
  - Depends on: E-02
  - Expected outcome: neither comment claims a `noqa` keeps `agy_runipd._read_id` alive; `ruff check` on both files emits no `Invalid # noqa directive` warning.
  - Execution state: pending

### Task group 3: pin the shim consumer in the bare suite

- [ ] E-04 Add an outcome test to `tests/test_runner_shared.py`, beside `CrossHostReadIdReExportTests`, that loads `tools/ipdrunner/runagy.py` with the file's existing `support.load_module` helper (imported at the top of the file as `from support import REPO_ROOT, load_module`) under a unique module name, then asserts `shim._read_id is agy_runipd._read_id` and that `shim._read_id("-\tId: abc123")` returns `"abc123"` (the permissive spelling). This moves the guarantee that the shim's one consumer depends on into the collected suite (`pyproject.toml` `testpaths = ["tests"]` never collects `tools/`). Remove the loaded name from `sys.modules` in cleanup.
  - Depends on: E-03
  - Expected outcome: the test passes at execution HEAD after E-01 and FAILS when the E-01 assignment is temporarily deleted (negative control in V-04).
  - Execution state: pending

### Task group 4: record the rule

- [ ] E-05 Append a `DECISIONS.md` entry using the next free `D<n>` number at execution time (`D162` is the last at authoring HEAD; re-check, since concurrent work may claim `D163`) in the file's `Context` / `Decision` / `Rejected` / `Applied` shape, titled along the lines of "Host runner modules justify deliberate re-exports by binding form, not by `__all__` or `noqa`". It must state: (1) RULE: in `agy_runipd`, `runner_shared`, and any module without an `__all__`, a deliberate re-export is written as `import X as X` (same-name) or as a module-level assignment, and never kept alive by `# noqa: F401`; (2) `oc_runipd`'s existing partial `__all__` is left as is (it already exists and its consumers rely on it), and is not a template for new modules; (3) REJECTED: adding `__all__` to `agy_runipd`, because a complete list would enumerate about 324 non-dunder names and a partial one would shrink `from agent_workflows.agy_runipd import *` (285 names at HEAD) to that list and understate the public surface, which the module's own `Heartbeat` comment already rejects; (4) SHIM DECISION: both shims stay as they are. `runagy.py`'s `vars()` loop is what makes private names such as `_read_id`, `_read_set` and `_read_order` reachable to `tools/ipdrunner/test_runagy.py`, and narrowing either shim could break unmeasured operator code; the asymmetry is accepted and documented; (5) Applied: the files of this plan, executed per IPD `vzk1iw` (backlog `fh8x8k`), resolving `h0zk2g` OQ-02.
  - Depends on: E-04
  - Expected outcome: `DECISIONS.md` has one new entry carrying the rule, the rejected `__all__` option, the shim decision, and the `vzk1iw` / `fh8x8k` / `h0zk2g` citations.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The repository has no ruff config (`pyproject.toml` has no `[tool.ruff]`, no `ruff.toml`), so the hook (`.pre-commit-config.yaml`, `ruff-pre-commit` `rev: v0.4.4`, `args: [--fix]`) runs ruff's DEFAULT rule set, which includes `F401` and `E402`. The locally installed ruff `0.16.3` picks up a broader user-level config (it reports 226 findings on the unmodified file), so local evidence must be taken with `--isolated` to reflect the project's rules. The hook binary is cached at the pre-commit cache path recorded for `ruff-pre-commit v0.4.4` (`h0zk2g` V-01 used it the same way).
- `agy_runipd` uses the `as <same-name>` idiom for over 200 re-exports (for example `Heartbeat as Heartbeat`, `render_queue_dispositions as render_queue_dispositions`), and its `Heartbeat` comment says the explicit alias is used "without introducing a partial `__all__` that would understate the rest of the public surface". `_read_id` is the one re-export that cannot use that idiom, because it renames `read_front_matter_id`.
- Tests must exercise behavior and never read source (AGENTS.md, GUIDING_PRINCIPLES P16). The suite is run BARE as `python3 -m pytest`.
- `tests/test_runner_shared.py::CrossHostReadIdReExportTests` already pins `agy_runipd._read_id is selectors.read_front_matter_id` and the permissive behavior on both hosts.

## Findings

| # | Finding | Evidence (measured at HEAD `d74169f1b`) | Consequence |
|---|---|---|---|
| F-1 | `agy_runipd` has no `__all__` and two `# noqa: F401` directives | `grep -n "noqa: F401" agent_workflows/agy_runipd.py`: the `_read_id` import and `assert_child_tool_identity as assert_child_tool_identity,  # noqa: F401`; `hasattr(agy_runipd, "__all__")` is False | Both are in scope |
| F-2 | The live consumer of `agy_runipd._read_id` is the shim | `python3 -c` with `tools/ipdrunner` on `sys.path`: `runagy._read_id is agy_runipd._read_id is selectors.read_front_matter_id` printed `True`; `tools/ipdrunner/test_runagy.py` line `self.assertEqual(driver._read_id(text), "a1b2c3")` | The binding must stay; E-04 pins it in `tests/` |
| F-3 | The `assert_child_tool_identity` noqa is already unused | `ruff check --select RUF100 agent_workflows/agy_runipd.py` reports `636:64: RUF100 [*] Unused noqa directive` under both `0.16.3` and `0.4.4`; same-name aliases pass `F401` without it | E-02 just deletes it |
| F-4 | A module-level assignment removes the need for a suppression, but only after the imports | A candidate copy with the import replaced by `from agent_workflows import selectors as _selectors` and `_read_id = ...` placed right after it: hook ruff `0.4.4` reported `E402 Module level import not at top of file` at every later import (116 findings). With the assignment placed after the last import (after `DEFAULT_TIMEOUT = "240m"`): `ruff 0.4.4` `All checks passed!` (default rules) and `ruff 0.16.3 --isolated --select F401,E402,RUF100` `All checks passed!` | E-01 fixes the placement |
| F-5 | An `__all__` is the costly option | 324 non-dunder module attributes; `from agent_workflows.agy_runipd import *` yields 285 names today; any partial `__all__` would cut that to the listed names | Rejected; recorded in E-05 |
| F-6 | `oc_runipd` already describes `agy_runipd`'s mechanism | `oc_runipd.py` sentence `In contrast, \`agy_runipd\` has no \`__all__\` and retains a noqa F401 directive.` | Becomes false after E-01; E-03 corrects it |
| F-7 | Nothing outside the shim and tests reads `agy_runipd._read_id` | `grep` for `_read_id` across `tools/ipdrunner/*.py` (excluding `test_runagy.py`) found nothing; in `tests/` only `test_runner_shared.py` | Behavior is unchanged by E-01 |

## Proposed changes (ordered, validatable)

1. E-01: `_read_id` moves from an aliased import with `noqa` to `_selectors.read_front_matter_id` assigned after the imports.
2. E-02: drop the unused `noqa` from `assert_child_tool_identity`.
3. E-03: correct the comments in both host modules.
4. E-04: add a shim-consumer outcome test to the bare suite.
5. E-05: record the rule and the shim decision in `DECISIONS.md`.

## Deferred / out of scope (with reason)

- Adding `__all__` to `agy_runipd` or `runner_shared`: rejected with reasons in E-05 and F-5, not deferred.
- Changing either shim: decided against in E-05 (accepted asymmetry), because narrowing `runagy.py` breaks `tools/ipdrunner/test_runagy.py`'s private-name reads and possibly unmeasured operator code.
- Removing `# noqa` directives for other rules elsewhere in the runners: outside this item, which is about `F401` re-export justification.
- The pre-existing failures in `tools/ipdrunner/test_runagy.py` recorded by `h0zk2g`: unrelated.

## Scope check

- Over-scope: none. `agy_runipd.py` (E-01, E-02, E-03), `oc_runipd.py` (E-03, one sentence), `tests/test_runner_shared.py` (E-04), `DECISIONS.md` (E-05). No `.spec.md` is touched.
- Under-scope: none known. The item's three asks (remove the noqa reliance, decide the shim asymmetry, state the rule) map to E-01/E-02, E-05 (4), and E-05 (1)-(3).

## Required tests / validation

- `python3 -m pytest` BARE, run once BEFORE any edit and once after; compare the failing node-id set by name and require the pass count to rise by exactly the tests E-04 adds. Paste both summary lines.
- `python3 -m pytest -o addopts="" tests/test_runner_shared.py -k "CrossHostReadId or RunagyShim"` (or the class name E-04 chose), pasted.
- `ruff check agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` under the hook-pinned `0.4.4` (default rules), and `ruff check --isolated --select F401,E402,RUF100` under the local ruff, both pasted with version banners.
- `pre-commit run ruff --files agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` and `pre-commit run ruff-format --files ...`, to show the `--fix` hook does not strip or move the binding.
- `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -k test_read_deps_and_set`, pasted, to show the shim consumer still works.

## Spec / documentation sync

- `DECISIONS.md` gains one entry (E-05). No spec describes runner module export lists, so no `.spec.md` is amended. No user-facing docs or `CHANGELOG.md` change: there is no behavior change.

## Open questions

### OQ-01: Should `agy_runipd` gain an `__all__` (the question `h0zk2g` OQ-02 deferred to this item)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED NO from repository evidence. The item's goal is that re-exports not depend on a rotting `noqa`; F-4 shows that goal is met with a module-level assignment and no `__all__`, while F-5 shows an `__all__` would either be a 324-name list or change `import *` and understate the surface, which the module's own `Heartbeat` comment already rejects. Recorded as the rule in E-05.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: (a) the new `from agent_workflows import selectors as _selectors` line and the `_read_id = _selectors.read_front_matter_id` line quoted from the file, with the import that immediately precedes the assignment quoted to show it is after the last top-level import; (b) pasted `python3 -c "from agent_workflows import agy_runipd, selectors; print(agy_runipd._read_id is selectors.read_front_matter_id)"` printing `True`; (c) pasted hook-pinned `ruff 0.4.4` `ruff check agent_workflows/agy_runipd.py` showing `All checks passed!`, and local `ruff check --isolated --select F401,E402,RUF100 agent_workflows/agy_runipd.py` showing `All checks passed!`, each with its `--version` banner.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `grep -c "noqa: F401" agent_workflows/agy_runipd.py` printing `0`, and pasted `python3 -c` printing `True` for `agy_runipd.assert_child_tool_identity is runner_shared.assert_child_tool_identity`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the rewritten `agy_runipd` comment block and the replaced `oc_runipd` sentence quoted in full; `git diff --stat agent_workflows/oc_runipd.py` pasted showing only comment lines changed; pasted `ruff check agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py 2>&1 | grep -c "Invalid # noqa"` printing `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) pasted pytest output of the new test passing; (b) NEGATIVE CONTROL: temporarily delete the E-01 `_read_id = ...` assignment, rerun the new test and paste its FAILURE, then restore and paste `git diff --stat` showing the restoration; (c) pasted `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -k test_read_deps_and_set` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new `DECISIONS.md` entry quoted in full, showing its `D<n>` number is unique (`grep -c "^### D<n>\." DECISIONS.md` printing `1`), the rule, the rejected `__all__` option, the shim decision, and the `vzk1iw` / `fh8x8k` / `h0zk2g` citations; plus the bare `python3 -m pytest` before and after summary lines and the `pre-commit run ruff` / `ruff-format` outputs from Required tests.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Low-risk chore with no behavior change: every binding keeps its object identity, and the only new code is one test. The reviewer should check F-4's placement rule (an assignment inside the import region would make the hook report `E402` on every later import) and whether the E-05 rule is the one the maintainer wants for modules without `__all__`.

Execution contract: commit only the `Scope-Paths` files, through `aw commit vzk1iw -- <paths>`, never `git add -A`, never push. This is a shared checkout: verify the staged set with `git diff --cached --name-only` before committing. Paste actual runner output for every test claim. Finalize through the lifecycle tooling (`aw ipd finalize` or the runner's self-finalize); never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Backlog `fh8x8k` is set `graduated` by the runner, not `done`, by this authoring turn.
