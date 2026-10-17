# IPD: Restore behavioral test coverage for engine.py opt-in hooks, shim customization, managed blocks, and lane merge

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `7df9md` (Set `trimgap`, group 9 of the `b1mx2w` filing plan) records that 12 production keys in `agent_workflows/engine.py` (264 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests were deleted by the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), mainly from `tests/test_command_shims.py` and `tests/test_comms.py`. The surviving tests that do touch some of these symbols live in `tests/test_installer.py`, which carries `pytestmark = pytest.mark.slow` and is therefore outside the selection the reach measurement used. So a mutation that, for example, made `create_precommit_scope_gate_hook` clobber a user's existing `.pre-commit-config.yaml`, or made `_merge_tree` overwrite a destination file, would pass the routine suite.
- Scope: Add ONE new behavioral test module, `tests/test_engine_restored_behavior.py`, that drives the 12 keys through their public call surfaces (or, for the two private helpers with no cheaper public surface, through their nearest public caller) and asserts on real return values, written files and file contents. The 12 keys: `create_dependency_gate_hook`, `create_precommit_scope_gate_hook`, `create_prepush_authorization_gate_hook`, `_wire_optin_precommit_hook` (reached through the two `create_*_gate_hook` wrappers that delegate to it), `_merge_tree` (reached through `migrate_local_lanes_to_untracked`), `validate_shim_grammar`, `is_stale_shim_customized`, `is_shim_customized`, `is_shim_customized_vs_expected`, `_shim_is_user_modified`, `agents_pointer_block`, `agents_managed_block`. EXCLUDES any change to `agent_workflows/engine.py` or any other production file, EXCLUDES editing or un-slowing `tests/test_installer.py`, and EXCLUDES the 8 `budget-exhausted` engine keys (`prune_stale`, `migrate_local_lanes_to_untracked` as its own key, `create_setup_artifacts`, `classify_git_state`, `resolve_source_root`, `shim_body`, `strip_description_and_normalize`, `_ensure_untracked_gitignore`), which belong to backlog item `lrnh5f`.
- Scope-Paths: tests/test_engine_restored_behavior.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 7df9md
- Set: trimgap
- Order: 9
- Highest E allocated: 06
- Author: opencode
- Id: 33f8tn

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `7df9md`. Measured every key's current behavior by direct call at HEAD `d2ec81544` before writing any expected outcome (Findings F-02 through F-06), so the expected values below are observed and not inferred from docstrings.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 12 `unguarded-unreached` engine keys from backlog `7df9md` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its outputs and file-system side effects. Done means a mutation that breaks any of these behaviors (idempotency, no-clobber, opt-out, dry-run, non-clobbering merge, shim grammar acceptance and rejection, customization detection, managed-block shape) turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new behavioral test module

- [ ] E-01 Create `tests/test_engine_restored_behavior.py` with `pytestmark = pytest.mark.core`, importing `agent_workflows.engine` and `agent_workflows.manifest`, and `SOURCE_WORKFLOWS` from `tests.support`. Use `tmp_path` only, and `use_git=False` for every hook-wiring call, so the module spawns no subprocess and runs in well under one second. Add a module docstring naming backlog `7df9md`, findings `b1mx2w`, and the deleted source files `tests/test_command_shims.py` and `tests/test_comms.py` at `19313eed^`.
  - Depends on: none
  - Expected outcome: the file exists, is collected by a bare `python3 -m pytest` (it carries the `core` marker), and imports cleanly.
  - Execution state: pending

- [ ] E-02 Add a parametrized test over the three opt-in hook installers, `engine.create_dependency_gate_hook`, `engine.create_precommit_scope_gate_hook` and `engine.create_prepush_authorization_gate_hook`, each paired with its hook id (`ipd-dependency-statement-gate`, `aw-precommit-scope-gate`, `aw-prepush-authorization-gate`). For each, assert, in a fresh `tmp_path` per case: (a) OPT-OUT: `install=False` returns `{"created": [], "skipped": [], "notes": []}` and no `.pre-commit-config.yaml` exists; (b) DRY-RUN with no config: `install=True, dry_run=True` writes nothing and returns a note containing `would create .pre-commit-config.yaml` and the hook id; (c) FRESH CREATE: `install=True` returns `created == [".pre-commit-config.yaml"]` and the file contains the hook id and parses as YAML with a top-level `repos` list; (d) IDEMPOTENT: a second `install=True` returns `skipped` naming `already wired`, and the file is byte-identical to after (c); (e) NO-CLOBBER APPEND: with a pre-existing user config `repos:\n  - repo: https://example.invalid/user-hook\n    rev: v1\n    hooks:\n      - id: user-hook\n`, `install=True` returns a note starting `appended the`, the user's original text survives as a prefix of the new file, the hook id now appears exactly once, and the result still parses as YAML with both the user hook and the new hook; (f) DRY-RUN APPEND: on the same kind of pre-existing config, `dry_run=True` returns a `would append` note and the file is byte-unchanged. The two `create_*_gate_hook` wrappers that delegate to `_wire_optin_precommit_hook` are what reach that private helper.
  - Depends on: E-01
  - Expected outcome: 3 parametrized cases, each asserting the six behaviors above, pass.
  - Execution state: pending

- [ ] E-03 Add a test of `engine.migrate_local_lanes_to_untracked` that reaches `_merge_tree` through its collision branch: in `tmp_path`, create both `.aw/records/comms/local/` and `.aw/records/comms/untracked/`, with `local/inbox/a.md` (unique), `local/inbox/b.md` = `OLD`, `untracked/inbox/b.md` = `NEW`, and a nested `local/inbox/deep/c.md` (unique, in a directory absent from `untracked`). Call `migrate_local_lanes_to_untracked(tmp_path, {})` and assert: the return value contains `.aw/records/comms/untracked`; `untracked/inbox/a.md` and `untracked/inbox/deep/c.md` now exist with their original contents; `untracked/inbox/b.md` still reads `NEW` (no clobber); `local/inbox/b.md` still exists reading `OLD` (the collided file is left behind, not deleted); and the emptied `local/inbox/deep/` directory no longer exists. Add a second case with no collision (only `local/` present, containing one file) asserting `local/` is gone, `untracked/` holds the file, and a second call is a no-op that leaves the file in place.
  - Depends on: E-01
  - Expected outcome: both merge cases pass, demonstrating non-clobbering recursive merge, emptied-directory removal, and idempotency.
  - Execution state: pending

- [ ] E-04 Add shim-grammar tests mined from the deleted `CommandShimsTests.test_validate_shim_grammar_positive_for_dispatcher_and_aliases` and `test_validate_shim_grammar_negative_cases` (at `19313eed^:tests/test_command_shims.py`). POSITIVE: with `workflows = engine.parse_manifest(SOURCE_WORKFLOWS)`, `engine.validate_shim_grammar(engine.aw_dispatcher_shim(workflows, tool, target_layout=layout), tool)` is True for every `tool` in (`opencode`, `claude`) and `layout` in (`aw`, `legacy`); and every non-README member of `engine.generate_shim_members(workflows, SOURCE_WORKFLOWS, target_layout="aw")` validates for its tool (`claude` when the path starts with `.claude`, else `opencode`), with the member set asserted non-empty so the loop cannot pass vacuously. NEGATIVE, one parametrized row each, each asserting False: empty string; whitespace only; unknown tool name; missing opening fence; missing closing fence; no `description:`; OpenCode without `agent:`; Claude with `agent: build`; no workflow-body reference; Claude `argument-hint:` with no `$ARGUMENTS`; `$ARGUMENTS` without the `If the user provided arguments` clause. Restore the deleted inputs verbatim where they still apply, and confirm each negative row fails for its stated reason by also asserting the corresponding unbroken control is True where a control exists.
  - Depends on: E-01
  - Expected outcome: 4 positive dispatcher combinations, the full generated alias set, and 11 negative rows pass.
  - Execution state: pending

- [ ] E-05 Add shim-customization tests. (a) `engine.is_shim_customized` and `engine.is_stale_shim_customized` return False for the generated OpenCode and Claude dispatcher shims and for every generated alias shim, and return True for the same dispatcher shim with an appended hand-written line (for example `my own extra instruction`), for content lacking any `Read and execute @...` line, and False for empty content (`is_stale_shim_customized("")`). (b) `engine.is_shim_customized_vs_expected(x, x)` is False; it stays False when only the `description:` line differs; it is True when a body line is added. (c) `engine._shim_is_user_modified` across its three regimes, building `engine.InstallPlan(source_root=SOURCE_WORKFLOWS, repo_root=tmp_path, dry_run=True, backup=False, prune=False, manifest=...)` (the dataclass is frozen, so pass `manifest` at construction): NO MANIFEST: a generated shim is NOT modified and foreign text IS modified; MANIFEST WITH A RECORDED HASH (via `manifest.Manifest().record(rel, generated)`): on-disk content equal to the recorded content is NOT modified even when the new expected text differs, and edited content IS modified; MANIFEST WITHOUT AN ENTRY for the path: falls back to the structural answer (generated NOT modified, foreign IS modified).
  - Depends on: E-01
  - Expected outcome: all customization assertions pass; each of the three `_shim_is_user_modified` regimes has at least one True and one False row.
  - Execution state: pending

- [ ] E-06 Add managed-block tests, mined from the deleted `PointerBlockTests.test_agents_block_has_check_inbox_clause` (`19313eed^:tests/test_comms.py`). (a) `engine.agents_pointer_block()` starts with `engine.AGENTS_BEGIN`, ends with `engine.AGENTS_END` plus a newline, and contains `.agents/comms/untracked/inbox/` and `UNTRUSTED`; `agents_pointer_block(target_layout="aw")` contains `.aw/records/comms/untracked/inbox/` instead. (b) `engine.agents_managed_block(target_layout="aw")` has first line `<!-- aw:block -->` and last line `<!-- /aw:block -->`, contains the `aw:pointer` and `aw:reporting` section openers in that order, does NOT contain the legacy `AGENTS_BEGIN` marker, and is stable when rendered twice (equal output). Do not assert on any other prose wording: these assertions are the observable contract a consumer (the installer and uninstaller) parses, not text pinning.
  - Depends on: E-01
  - Expected outcome: pointer-block and managed-block assertions pass for both layouts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). No `inspect`, `ast`, regex over production source, caller counts, or docstring pinning. Every assertion here calls the function and checks a return value or a file on disk. The managed-block markers in E-06 are a parsed contract, not prose.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`), under a 30s budget. A new module must therefore carry `pytestmark = pytest.mark.core` to be reached by the merge gate, and must stay fast (no subprocess, `use_git=False`).
- `tests/test_installer.py` already covers `_shim_is_user_modified` (`ManifestDriftDecisionTests`) and the shim helpers, but carries `pytestmark = pytest.mark.slow`, which is why `b1mx2w` measured these keys `unreached` (its baseline excludes `slow` and `livecorpus`, per `b1mx2w` `## Method`). This plan adds fast coverage alongside it rather than editing that slow file.
- Existing analogue: `tests/test_backlog_close_gate_prose.py` drives `engine.create_backlog_close_gate_hook(tmp_path, use_git=False, install=True)` and parses the result with `yaml`; E-02 follows that pattern for the three sibling hooks.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `agent_workflows/engine.py::*` | Exactly 12 engine keys carry `unreached` / `unguarded-unreached`: the 12 named in Scope. The other 8 engine keys are `budget-exhausted` and are owned by `lrnh5f`. `rg` over `tests/` finds no non-slow caller of `create_dependency_gate_hook`, `create_precommit_scope_gate_hook`, `create_prepush_authorization_gate_hook`, `_wire_optin_precommit_hook`, `_merge_tree`, `agents_managed_block`, or `validate_shim_grammar`; the remaining keys appear only in slow `tests/test_installer.py` or `tests/test_askme_command_delivery.py` (neither in the routine selection reach was measured against). |
| F-02 | direct calls at HEAD `d2ec81544`, `use_git=False`, fresh temp dirs | All three hook installers behave identically: `install=False` returns three empty lists and writes nothing; dry-run returns `would create .pre-commit-config.yaml with the <id> hook`; first install returns `created: ['.pre-commit-config.yaml']`; second returns `skipped: ['.pre-commit-config.yaml [<id> already wired]']`; against an existing `repos:\n  - repo: x\n` config returns `appended the <id> hook block` and the result begins with the original text. |
| F-03 | direct call of `migrate_local_lanes_to_untracked` with both `local/` and `untracked/` present | Returns `['.aw/records/comms/untracked']`; unique file moved; colliding `b.md` left in `local/` reading `OLD` while `untracked/` keeps `NEW`; an `.aw/.gitignore` is also written. So `_merge_tree` is reachable and observable through the public function. |
| F-04 | `parse_manifest(SOURCE_WORKFLOWS)` + `aw_dispatcher_shim` / `generate_shim_members` | Both dispatchers validate True; 54 shim members are generated and zero non-README members fail `validate_shim_grammar`. The deleted negative cases at `19313eed^:tests/test_command_shims.py` remain applicable to the current function's documented checks. |
| F-05 | direct calls | `is_shim_customized(dispatcher)` False, with an appended custom line True; `is_shim_customized_vs_expected(x, x)` False, with an appended line True; `_shim_is_user_modified` with no manifest: generated False, foreign True. `InstallPlan` is a frozen dataclass, so the manifest must be passed at construction (observed `FrozenInstanceError` on assignment). |
| F-06 | direct calls | `agents_pointer_block()` starts with `AGENTS_BEGIN` and contains `.agents/comms/untracked/inbox/` and `UNTRUSTED`; `agents_managed_block(target_layout="aw")` first line `<!-- aw:block -->`, last line `<!-- /aw:block -->`, contains `aw:pointer` and `aw:reporting`. |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked test module skeleton.
2. E-02 covers the three opt-in hook installers and, through them, `_wire_optin_precommit_hook`.
3. E-03 covers `_merge_tree` through `migrate_local_lanes_to_untracked`.
4. E-04 restores the shim-grammar positive and negative cases.
5. E-05 covers the four customization predicates.
6. E-06 covers the pointer and sectioned managed blocks.

## Deferred / out of scope (with reason)

- The 8 `budget-exhausted` engine keys are not covered here: they were never mutation-probed, and probe-then-restore for them is backlog `lrnh5f`'s scope.
  - Carrier: lrnh5f
- Un-slowing or splitting `tests/test_installer.py` is out of scope: it is an integration suite that installs into temp repos, its slow marking is deliberate, and this plan's fast unit-level module covers the reach gap without changing that file.
  - Carrier-Declined: no work is owed; the reach gap this item records is closed by E-01 to E-06, and the slow suite still runs in `make test-all` and CI.

## Scope check

- Over-scope: none. One new test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 12 named keys. The 8 `budget-exhausted` keys are deliberately routed to `lrnh5f`.

## Required tests / validation

- `python3 -m pytest tests/test_engine_restored_behavior.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes (core tier, including the new module, within the 30s budget), with the summary line pasted.
- Reach: `python3 -m pytest tests/test_engine_restored_behavior.py -o addopts="" --cov=agent_workflows.engine --cov-report=term-missing` (or `coverage run -m pytest ...` followed by `coverage report --include=agent_workflows/engine.py`) shows the bodies of all 12 keys executed; paste the relevant output.
- Mutation spot-check: temporarily apply, in a scratch edit not committed, one mutation per group (make `_wire_optin_precommit_hook` skip the `hook_id in existing` check; make `_merge_tree` move even when `dest.exists()`; make `validate_shim_grammar` return True early; make `is_stale_shim_customized` return False early; make `agents_managed_block` return an empty string), run the new module, and paste the failure for each; then revert and confirm `git diff agent_workflows/` is empty.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should the new module be core-marked, or only non-slow?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: core-marked. The routine gate a bare `python3 -m pytest` runs is the core tier (`conftest.pytest_collection_modifyitems`), so non-core coverage would still be absent from the merge gate. The module spawns no subprocess and measured calls take milliseconds, so it fits the 30s core budget; E-01 and V-01 require the runtime be shown.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat` showing only `tests/test_engine_restored_behavior.py` added; paste the bare `python3 -m pytest` summary line showing it passed with the new module's tests included (for example via `python3 -m pytest --collect-only -q | rg test_engine_restored_behavior | wc -l` being nonzero) and the core-tier wall time under budget.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing the three parametrized hook cases as PASSED, and paste the mutation spot-check failure produced by disabling the `hook_id in existing` idempotency check in `_wire_optin_precommit_hook` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing both lane-merge cases as PASSED, and paste the failure produced by mutating `_merge_tree` to move a file even when `dest.exists()` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing the positive cases and all 11 negative rows as PASSED, and the failure produced by making `validate_shim_grammar` return True immediately (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` output listing the customization tests, including all three `_shim_is_user_modified` regimes, as PASSED, and the failure produced by making `is_stale_shim_customized` return False immediately (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `-v` output listing the pointer-block and managed-block tests as PASSED, the coverage output showing all 12 keys' bodies executed, the failure produced by making `agents_managed_block` return `""` (reverted afterwards), and a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_engine_restored_behavior.py` through `aw commit <plan> -- tests/test_engine_restored_behavior.py`; never push. Mutation spot-checks are scratch edits to `agent_workflows/engine.py` that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
