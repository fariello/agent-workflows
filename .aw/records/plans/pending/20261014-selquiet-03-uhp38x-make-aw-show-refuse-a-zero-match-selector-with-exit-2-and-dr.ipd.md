# IPD: Make aw show refuse a zero-match selector with exit 2 and drop unreachable exit 1 from its contract

- Date: 2026-10-14
- Kind: child
- Concern: `aw show <ref>` exits 1 (`outcome: "findings"`, diagnostic rule `show.not_found`) when `<ref>` matches zero artifacts across `_run_show`'s seven queried record types, instead of refusing an unresolved non-vocabulary selector at exit 2 (`outcome: "cannot-run"`) and answering a standing-vocabulary token that happens to match zero records (`ref.strip().lower() in find_selector_vocabulary()`) with exit 0 (`outcome: "clean"`). Re-measured in this lane at HEAD `22e589747` with token `zzzzzz`: `aw show zzzzzz` exits 1 on human (writing `✗ FAIL  no records artifact matched 'zzzzzz'` to `stdout`, not `stderr`), exits 1 on `--agent` (`{"schema":"aw.agent/v1","kind":"result","cmd":"show","outcome":"findings","exit":1,...,"diagnostics":[{"location":"zzzzzz","rule":"show.not_found","severity":"error","message":"No records artifact matched 'zzzzzz'."}]}`), and exits 1 on `--json` (`status: "findings"`, `exit_code: 1`). Likewise, `aw show prompt-library` (a standing-vocabulary status token in `cli.find_selector_vocabulary()` with zero matching artifacts in the live tree) exits 1 with `show.not_found` instead of exit 0. IPD `zyj8io` V-08's survey table recorded `aw show <sel>` as `2 | 2 | 2 | 2 | Conforming` because the survey drove `aw show` with `--paths`, which `argparse` rejects on `show` at exit 2 before `_run_show` runs; consequently backlog `tbe8v0` and sibling plan `yxsfjc` omitted `aw show`. Spec `25kzda` Section 2.3 rules "Zero matches return exit 2", Section 2.4a exempts standing-vocabulary status/kind/facet tokens at exit 0, and `docs/cli-output-contract.md` Section 11.1 codifies the read-verb zero-match refusal convention. Finally, `command_surface.py` declares `CommandDeclaration(command="show", command_class="read", exit_contract=(0, 1, 2), ...)`; once `show.not_found` moves from exit 1 to exit 2, exit 1 is unreachable in `cli._run_show`, and keeping `1` in `exit_contract` would falsely require a `domain_failure` scenario under `tests.conformance_matrix.required_scenarios`.
- Scope: Update `cli._run_show` in `agent_workflows/cli.py` so a zero-match `<ref>` that belongs to `cli.find_selector_vocabulary()` returns exit 0 (`status="clean"`, `verified=True`, `complete=True`, `Term.empty_result(..., status="ok")` on `stdout`), while any other zero-match `<ref>` refuses at exit 2 (`outcome: "cannot-run"`, `verified=False`, `complete=False`) naming the `agent_schema.redact_home_paths`-redacted token across human (`stderr` via `Term(stream=sys.stderr, ...).format_empty_result(..., status="fail")`, `stdout` empty), `--agent` (`kind: "error"`, `outcome: "cannot-run"`, `exit: 2`, `unresolved_selectors: [redacted_ref]`, `unresolved_targets: [redacted_ref]`, `error`, `next: "aw find"`, validated via `agent_schema.assert_valid_agent_record`), and `--json` (`CommandResult(command="show", status="cannot-run", exit_code=2, ...)`). Narrow `CommandDeclaration(command="show", ...)` in `agent_workflows/command_surface.py` from `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` with an explanatory comment. Clean up stale action-ledger fallback prose in `cli._DESCRIPTIONS["show"]` and `p_show` parser help/epilog in `agent_workflows/cli.py`. Add behavioral and contract regression tests in `tests/test_cli_show.py`, and sync `docs/cli-output-contract.md` Section 11.1 and `CHANGELOG.md`. Does NOT change which record types `_run_show` searches when `<ref>` resolves, does NOT alter any other verb, and does NOT depend on unexecuted sibling plan `yxsfjc`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_cli_show.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: executed:zyj8io
- Status: to-review
- From-Backlog: upryxf
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: selquiet
- Order: 3
- Highest E allocated: 05
- Author: Antigravity
- Id: uhp38x

## Workflow history
- 2026-10-14 to-review (aw set): Authored from backlog item upryxf at HEAD 22e589747: aw show zero-match exits 2 (cannot-run), standing-vocabulary zero-match exits 0 (clean), and show exit_contract narrows from (0, 1, 2) to (0, 2).

- 2026-10-14 draft (Antigravity): created.

## Goal

Make `aw show <ref>` obey the repository's read-verb selector contract (Spec `25kzda` Sections 2.3 and 2.4a; `docs/cli-output-contract.md` Section 11.1): refuse a non-vocabulary zero-match selector at exit 2 (`cannot-run`) across human (`stderr`), `--agent`, and `--json`; return exit 0 (`clean`) when a standing-vocabulary status/kind/facet token matches zero artifacts; and narrow `show`'s declared `exit_contract` in `agent_workflows/command_surface.py` from `(0, 1, 2)` to `(0, 2)` so the declaration matches the reachable exit codes of `cli._run_show`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Pre-change baseline capture

- [ ] E-01 Capture the pre-change baseline in this worktree before editing any file: run `python3 -m pytest` (bare, with default `xdist` and `pytest-randomly` flags intact) and record the summary line; and drive `aw show` across its 3 output surfaces (`human`, `--agent`, `--json`) x 4 token classes (`UNKNOWN` `zzzzzz`, `VOCABULARY-ZERO-MATCH` `prompt-library`, `VOCABULARY-MATCHING` `approved`, and `MATCHING` `f36de0`), recording `(exit_code, len(stdout), len(stderr), outcome/status)` for all 12 invocations.
  - Depends on: none
  - Expected outcome: The baseline test suite passes cleanly and the 12-cell pre-change matrix shows `UNKNOWN` (`zzzzzz`) and `VOCABULARY-ZERO-MATCH` (`prompt-library`) exiting `1` with `outcome: "findings"` / `rule: "show.not_found"` and human output on `stdout` (`len(stderr) == 0`), while `VOCABULARY-MATCHING` (`approved`) and `MATCHING` (`f36de0`) exit `0` with `outcome: "clean"`.
  - Execution state: pending

### Task group 2: Align `cli._run_show`, `show` help text, and `command_surface.py`

- [ ] E-02 Update `cli._run_show` and the `show` parser/description metadata in `agent_workflows/cli.py`: (1) when `unique` is empty after searching `record_types`, check `if ref.strip().lower() in find_selector_vocabulary():`; (2) on that standing-vocabulary zero-match branch, return `0` (`CommandResult(command="show", status="clean", exit_code=0, summary=f"matched 0 artifact(s) for '{ref}'", verified=True, complete=True, evidence=[Evidence(key="show-match", value={"count": 0}, status="verified")], data={"matches": [], "contents": {}, "ref": ref})` via `_emit_command_result(args, res, term)` on `--agent`/`--json`, and `term.empty_result(summary=f"no matching records for '{ref}'", filters={"ref": ref}, next_action=NextAction(command="aw find", description="list all records"), status="ok")` on human `stdout`); (3) on the non-vocabulary zero-match branch (`ref.strip().lower() not in find_selector_vocabulary()`), refuse at exit `2` (`cannot-run`) by delegating to `emit_zero_match_selector_refusal` if already present in `cli.py` or else passing `ref` through `redacted_ref = agent_schema.redact_home_paths(ref)` with `error_msg = f"unresolved selector: {redacted_ref} (matched 0 records; next: aw find)"` and emitting: on `--agent`, a hand-built `aw.agent/v1` record `{"schema": agent_schema.SCHEMA_ID, "kind": "error", "cmd": "show", "outcome": "cannot-run", "exit": 2, "verified": False, "complete": False, "findings": 1, "unresolved_selectors": [redacted_ref], "unresolved_targets": [redacted_ref], "error": error_msg, "next": "aw find"}` validated by `agent_schema.assert_valid_agent_record(rec)`; on `--json`, `CommandResult(command="show", status="cannot-run", exit_code=2, summary=error_msg, verified=False, complete=False, next_actions=[NextAction(command="aw find", description="list all records")], data={"unresolved_selectors": [redacted_ref], "unresolved_targets": [redacted_ref], "ref": redacted_ref, "matches": [], "count": 0})`; and on human, `Term(stream=sys.stderr, color=term.color, unicode=term.unicode).format_empty_result(summary=f"unresolved selector: {redacted_ref}", filters={"ref": redacted_ref}, next_action=NextAction(command="aw find", description="list all records"), status="fail") + "\n"` written to `sys.stderr` with `sys.stdout` empty; and (4) in `cli._DESCRIPTIONS["show"]` and `p_show` (`sub.add_parser("show", ...)` and `p_show.add_argument("ref", ...)`), remove stale references to falling back to the removed action ledger (`19bd75020`) and state the `(0, 2)` exit contract.
  - Depends on: E-01
  - Expected outcome: `aw show` returns `0` (`clean`, `stdout`) on standing-vocabulary zero-match tokens and `2` (`cannot-run`, naming the redacted token; `stderr` with empty `stdout` on human) on non-vocabulary zero-match tokens, while preserving existing exit `0` behavior when one or more artifacts match.
  - Execution state: pending

- [ ] E-03 Update `CommandDeclaration(command="show", ...)` in `agent_workflows/command_surface.py` from `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` with a comment explaining that `aw show` is a pure read/inspection verb whose zero-match refusal exits `2` (`upryxf` / Spec `25kzda` Section 2.3) and has no reachable exit `1` path (so `tests.conformance_matrix.required_scenarios` does not demand a synthetic `domain_failure` scenario), then run the command-surface and conformance test modules.
  - Depends on: E-02
  - Expected outcome: `command_surface.get_declaration("show").exit_contract == (0, 2)`, `"domain_failure" not in conformance_matrix.required_scenarios(get_declaration("show"))`, and `pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py` passes with 0 failures.
  - Execution state: pending

### Task group 3: Regression tests, documentation sync, and final validation gates

- [ ] E-04 Create `tests/test_cli_show.py` exercising `aw show` through `cli.main` in an isolated temporary repository fixture across all three surfaces (`human`, `--agent`, `--json`): (1) `UNKNOWN` non-vocabulary token (`zzzzzz`) exits `2` (`human` writes to `stderr` with `stdout == ""` and names `zzzzzz` + `aw find`; `--agent` emits a schema-valid `aw.agent/v1` record with `kind == "error"`, `cmd == "show"`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`, `unresolved_selectors == ["zzzzzz"]`, `unresolved_targets == ["zzzzzz"]`, `"zzzzzz" in error`, `next == "aw find"`; `--json` emits `status == "cannot-run"`, `exit_code == 2`, `verified is False`, `complete is False`, `data["unresolved_selectors"] == ["zzzzzz"]`, `data["unresolved_targets"] == ["zzzzzz"]`); (2) home-path-shaped unknown token (`f"{Path.home()}/secret-missing-ref"`) exits `2` on all three surfaces with `<home>/secret-missing-ref` in the output and the literal `str(Path.home())` absent everywhere; (3) standing-vocabulary tokens with zero matches in the fixture (`reusable` and `prompt-library`) exit `0` on all three surfaces (`human` writes `no matching records for 'reusable'` to `stdout` with `stderr == ""`; `--agent` emits `kind == "result"`, `outcome == "clean"`, `exit == 0`, `verified is True`, `complete is True`, `findings == 0`; `--json` emits `status == "clean"`, `exit_code == 0`, `data["matches"] == []`, `data["contents"] == {}`); (4) matching selector tokens (by `id6`, `setid`, standing status `to-review`, and filename substring) exit `0` on all three surfaces and return the matched artifact path and markdown body in `stdout` / `data["matches"]` / `data["contents"]`; and (5) contract declaration check (`command_surface.get_declaration("show").exit_contract == (0, 2)` and `"domain_failure" not in conformance_matrix.required_scenarios(command_surface.get_declaration("show"))`).
  - Depends on: E-02, E-03
  - Expected outcome: `python3 -m pytest tests/test_cli_show.py` passes all tests in the new module with 0 failures.
  - Execution state: pending

- [ ] E-05 Update `docs/cli-output-contract.md` Section 11.1 ("Precedent and Scope", listing `aw show` alongside conforming read verbs and noting its standing-vocabulary zero-match exemption) and `CHANGELOG.md` under `## [Unreleased]` -> `### Changed` (recording that `aw show <ref>` now exits `2` `cannot-run` on an unresolved non-vocabulary selector, exits `0` `clean` when a standing-vocabulary token matches zero records, and declares `exit_contract=(0, 2)` in `command_surface.py`), ensuring zero em/en dashes (`\u2014` / `\u2013`) in edited user-facing prose; then run the full test suite (`python3 -m pytest`), `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-04
  - Expected outcome: `docs/cli-output-contract.md` and `CHANGELOG.md` reflect the shipped behavior with 0 em/en dashes; the full `python3 -m pytest` suite, `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent` all exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Read-verb zero-match selector contract (`25kzda` Sections 2.3 and 2.4a; `docs/cli-output-contract.md` Section 11)**:
  - A selector token that names a specific artifact (id6, setid, slug/substring, path) and matches zero artifacts is an unresolved-selector refusal (`outcome: "cannot-run"`, `exit: 2`, `verified: false`, `complete: false`), NOT a domain finding (`exit: 1`) and NOT a clean empty result (`exit: 0`).
  - A selector token that belongs to the standing status/kind/facet vocabulary (`cli.find_selector_vocabulary()` in `agent_workflows/cli.py`, line 12169: `def find_selector_vocabulary() -> frozenset[str]:`) asks a standing state question across the repository and is exempt from zero-match refusal: when zero artifacts match that status/kind/facet, the verb returns `exit: 0` (`outcome: "clean"`, `verified: true`, `complete: true`).
  - On human output, `exit: 0` empty results go to `stdout` (`term.empty_result(..., status="ok")`), whereas `exit: 2` refusals go to `stderr` (`Term(stream=sys.stderr, color=term.color, unicode=term.unicode).format_empty_result(..., status="fail")`) with `stdout` empty (`0` bytes) (`cli._run_find` in `agent_workflows/cli.py`, line 12361; `docs/cli-output-contract.md` Section 11.4).
  - On `--agent` output, `CommandResult.to_agent_record()` (`agent_workflows/output_contract.py`, line 276: `def to_agent_record(`) omits `CommandResult.summary` and `CommandResult.data`, so a `cannot-run` refusal must hand-build the `aw.agent/v1` `kind: "error"` record with `unresolved_selectors`, `unresolved_targets`, `error`, and `next` and validate it via `agent_schema.assert_valid_agent_record` (`agent_workflows/agent_schema.py`, line 330: `def assert_valid_agent_record(`) after redacting every user-supplied token with `agent_schema.redact_home_paths` (`agent_workflows/agent_schema.py`, line 217: `def redact_home_paths(`).
- **Command surface declaration and conformance matrix (`agent_workflows/command_surface.py` and `tests/conformance_matrix.py`)**:
  - `tests.conformance_matrix.required_scenarios` (`tests/conformance_matrix.py`, line 69: `def required_scenarios(decl: CommandDeclaration) -> tuple[str, ...]:`) appends `"domain_failure"` whenever `1 in decl.exit_contract and decl.command_class in ("read", "check", "bare")`.
  - Pure read/inspection verbs without a domain-findings mode (`layout`, `graduation`, `research find`, `reviews decisions`, `host probe`, `host capabilities` in `agent_workflows/command_surface.py`, line 51: `COMMAND_DECLARATIONS: tuple[CommandDeclaration, ...] = (`) declare `exit_contract=(0, 2)`.
- **Test and prose rules (`AGENTS.md` / `GEMINI.md`)**:
  - Run `python3 -m pytest` bare (never pass `-n0`, extra `-q`, or `-p no:randomly`).
  - Never write code-pinning tests (`inspect`, `ast`, regex/substring checks on source files); test observable CLI behavior and outcomes.
  - Write no em or en dashes (`\u2014` or `\u2013`) in user-facing prose (`docs/cli-output-contract.md`, `CHANGELOG.md`, CLI help strings).

## Findings

| ID | Category | Location | Observation | Impact |
|---|---|---|---|---|
| F-1 | Defect (`upryxf`) | `cli._run_show` (`agent_workflows/cli.py`, line 12554: `# Not found anywhere`) | When `unique` is empty, `cli._run_show` returns `1` on all three surfaces: `--agent` and `--json` emit `CommandResult(command="show", status="findings", exit_code=1, ..., diagnostics=[Diagnostic(location=ref, rule="show.not_found", ...)])`, and human calls `term.empty_result(..., status="fail")` which writes to `sys.stdout` and returns `1`. | Violates Spec `25kzda` Section 2.3 ("Zero matches return exit 2") and `docs/cli-output-contract.md` Section 11.1 (`cannot-run` at exit 2, human output on `stderr` with `stdout` empty). |
| F-2 | Defect (Standing vocabulary exemption) | `cli._run_show` (`agent_workflows/cli.py`, line 12513: `# 1. Try to resolve the token as a RECORDS artifact (id6 \| setid \| filename \| status)`) | `aw show` advertises status tokens (`to-review`, `approved`, `executed`, etc.) in `cli._DESCRIPTIONS["show"]` and `p_show`, and calls `selectors.resolve_selectors` which matches `MATCH_STATUS` at rung 4. Yet when a standing-vocabulary token in `cli.find_selector_vocabulary()` matches zero artifacts (e.g. `aw show prompt-library` in the live repo, or `aw show reusable` in a fixture with no reusable plan), `cli._run_show` treats it identically to a typo and exits `1` (`show.not_found`). | Violates Spec `25kzda` Section 2.4a and `docs/cli-output-contract.md` Section 11.1: standing-vocabulary status/kind/facet tokens with zero matches must return exit `0` (`clean`), not `1` or `2`. |
| F-3 | Root cause of `zyj8io` V-08 misrecording | `.aw/records/plans/executed/20260929-selquiet-01-zyj8io-make-aw-find-refuse-a-zero-match-selector-with-exit-2-exempt.ipd.md` (V-08 survey table, line 407) | `zyj8io` V-08 recorded `aw show <sel>` as `2 \| 2 \| 2 \| 2 \| Conforming` because the survey script passed `--paths` (`aw show zzzzzz --paths`), which `argparse` rejects on `show` at exit `2` (`error: unrecognized arguments: --paths`) before `cli._run_show` executes. Without `--paths`, `aw show zzzzzz` exits `1` on human, `--agent`, and `--json`. | Explains why `tbe8v0` and sibling plan `yxsfjc` did not include `aw show`, and why `upryxf` was filed to close the gap. |
| F-4 | Unreachable exit `1` in `command_surface.py` | `agent_workflows/command_surface.py` (`COMMAND_DECLARATIONS`, line 222: `CommandDeclaration(command="show", command_class="read", exit_contract=(0, 1, 2), ...)`) | `cli._run_show` has only two code paths after `selectors.resolve_selectors`: `unique` non-empty (returns `0`) and `unique` empty (returns `0` for standing-vocabulary tokens and `2` for unresolved selectors). Once `show.not_found` moves from exit `1` to exit `2`, exit `1` is completely unreachable in `cli._run_show`. Neither `ef55eadb1` (which added `show.not_found`) nor `efd2019ad` (which declared `exit_contract=(0, 1, 2)`) has shipped in any git release tag (`git tag --contains efd2019ad` and `git tag --contains ef55eadb1` are both empty). | Leaving `1` in `exit_contract` for a `command_class="read"` verb forces `tests.conformance_matrix.required_scenarios` to require a `domain_failure` scenario that `aw show` can never produce. Narrowing `exit_contract` to `(0, 2)` matches `layout`, `graduation`, `research find`, `reviews decisions`, `host probe`, and `host capabilities`. |
| F-5 | Zero extra I/O on `_run_show` empty path | `cli._run_show` (`agent_workflows/cli.py`, line 12514: `record_types = ("plans", "specs", "research", "backlog", "prompts", "walkthroughs", "roadmaps")`) | Unlike the four verbs in `yxsfjc` (which query only reviews, sidecars, or `From-Backlog:` links and therefore need a secondary cross-tree probe on their empty path), `cli._run_show` has ALREADY called `selectors.resolve_selectors(repo_root, rt, [ref])` across its `record_types` before reaching the empty branch. Checking `ref.strip().lower() in find_selector_vocabulary()` is an in-memory `frozenset` lookup with zero disk reads. | No cross-tree re-scan is needed in `cli._run_show`; the empty path stays O(1) beyond the lookup already performed. |
| F-6 | Independence from sibling plan `yxsfjc` | `.aw/records/plans/pending/20261012-selquiet-02-yxsfjc-make-reviews-decisions-record-history-graduation-and-ipd-rec.ipd.md` | `yxsfjc` (Set `selquiet`, Order 2, status `approved`) touches `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `docs/cli-output-contract.md`, `CHANGELOG.md`, and creates `tests/test_read_verb_zero_match_refusal.py`. Placing `aw show`'s tests in `tests/test_cli_show.py` avoids a new-file collision, and writing `_run_show` to either call `emit_zero_match_selector_refusal` (if present) or emit the identical refusal shape directly allows `uhp38x` and `yxsfjc` to execute in either order and merge cleanly in isolated runner worktrees. | `- Item-Dependencies: executed:zyj8io` is sufficient and accurate; `uhp38x` cannot be dependency-blocked by `yxsfjc`. |
| F-7 | Stale action-ledger help text on `aw show` | `cli._DESCRIPTIONS["show"]` (`agent_workflows/cli.py`, line 493) and `p_show` (`agent_workflows/cli.py`, line 4382: `sub.add_parser("show", ...)`) | Both `cli._DESCRIPTIONS["show"]` and `p_show`'s help/epilog still claim `aw show` "falls back to looking up a legacy action ledger file by action ID", even though action-ledger support was removed from `cli._run_show` in commit `19bd75020` (`setupmarker-01`). | Updating `cli._DESCRIPTIONS["show"]` and `p_show` in `E-02` removes misleading documentation and states the real selector resolution and `(0, 2)` exit contract. |

## Proposed changes (ordered, validatable)

1. **Baseline measurement (`E-01` / `V-01`)**:
   - Run `python3 -m pytest` bare and record the pass summary and duration.
   - Drive `aw show` across `(human, --agent, --json)` x `(zzzzzz, prompt-library, approved, f36de0)` and record the 12-cell pre-change behavior table.
2. **Update `cli._run_show` and `show` help strings in `agent_workflows/cli.py` (`E-02` / `V-02`)**:
   - In `cli._run_show` (`agent_workflows/cli.py`, line 12497: `def _run_show(args: argparse.Namespace) -> int:`), replace the `# Not found anywhere` block (lines 12554-12587) with:
     - Standing-vocabulary zero-match check: `if ref.strip().lower() in find_selector_vocabulary():` returning `0` (`CommandResult(command="show", status="clean", exit_code=0, summary=f"matched 0 artifact(s) for '{ref}'", verified=True, complete=True, evidence=[Evidence(key="show-match", value={"count": 0}, status="verified")], data={"matches": [], "contents": {}, "ref": ref})` on `--agent`/`--json`; `term.empty_result(summary=f"no matching records for '{ref}'", filters={"ref": ref}, next_action=NextAction(command="aw find", description="list all records"), status="ok")` on human `stdout`).
     - Non-vocabulary zero-match refusal returning `2`: redact `ref` via `redacted_ref = agent_schema.redact_home_paths(ref)` and emit:
       - `--agent`: `aw.agent/v1` `kind: "error"`, `cmd: "show"`, `outcome: "cannot-run"`, `exit: 2`, `verified: False`, `complete: False`, `findings: 1`, `unresolved_selectors: [redacted_ref]`, `unresolved_targets: [redacted_ref]`, `error: f"unresolved selector: {redacted_ref} (matched 0 records; next: aw find)"`, `next: "aw find"`, validated with `agent_schema.assert_valid_agent_record(rec)`.
       - `--json`: `CommandResult(command="show", status="cannot-run", exit_code=2, summary=error_msg, verified=False, complete=False, next_actions=[NextAction(command="aw find", description="list all records")], data={"unresolved_selectors": [redacted_ref], "unresolved_targets": [redacted_ref], "ref": redacted_ref, "matches": [], "count": 0})`.
       - Human: `Term(stream=sys.stderr, color=term.color, unicode=term.unicode).format_empty_result(summary=f"unresolved selector: {redacted_ref}", filters={"ref": redacted_ref}, next_action=NextAction(command="aw find", description="list all records"), status="fail") + "\n"` written to `sys.stderr` with `sys.stdout` empty.
   - Update `cli._DESCRIPTIONS["show"]` (`agent_workflows/cli.py`, line 493) and `p_show` (`agent_workflows/cli.py`, line 4382) to remove legacy action-ledger references and document the `(0, 2)` exit contract.
3. **Narrow `show` `exit_contract` in `agent_workflows/command_surface.py` (`E-03` / `V-03`)**:
   - In `agent_workflows/command_surface.py` (`COMMAND_DECLARATIONS`, line 222: `CommandDeclaration(command="show", ...)`), change `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` and add a concise comment citing `upryxf` and `tests.conformance_matrix.required_scenarios`.
4. **Add behavioral test suite `tests/test_cli_show.py` (`E-04` / `V-04`)**:
   - Create `tests/test_cli_show.py` covering unknown token refusal (`exit 2`, `cannot-run`, `stderr` on human with empty `stdout`, schema-valid `--agent` error record, `--json` `CommandResult`), home-path redaction on refusal, standing-vocabulary zero-match exemption (`exit 0`, `clean`, `stdout` on human), matching selectors (`id6`, `setid`, status, filename substring -> `exit 0` with contents), and `command_surface.get_declaration("show").exit_contract == (0, 2)`.
5. **Sync `docs/cli-output-contract.md` and `CHANGELOG.md` and run full verification (`E-05` / `V-05`)**:
   - Update `docs/cli-output-contract.md` Section 11.1 and `CHANGELOG.md` (with zero em/en dashes), then run `python3 -m pytest`, `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

- Widening `cli._run_show`'s `record_types` tuple (`("plans", "specs", "research", "backlog", "prompts", "walkthroughs", "roadmaps")`) to all 11 members of `artifact_types.ARTIFACT_TYPES` (such as `reviews`, `assessments`, `releases`, `design`):
  - Carrier-Declined: `upryxf` scopes only the zero-match exit code (`1` -> `2` with standing-vocabulary `0` exemption) and `exit_contract` declaration of `aw show`; changing which artifact trees `aw show` displays on a match would alter positive-match behavior outside `upryxf`'s scope.
- Changing zero-match behavior on `aw reviews decisions`, `aw record-history`, `aw graduation`, or `aw ipd recheck-readiness`:
  - Carrier: yxsfjc
  - Carrier-Evidence: .aw/records/plans/executed/20261012-selquiet-02-yxsfjc-make-reviews-decisions-record-history-graduation-and-ipd-rec.ipd.md

## Scope check

- Over-scope: none. Every touched file in `- Scope-Paths:` is directly required to make `aw show` exit 2 on unresolved non-vocabulary selectors, exit 0 on zero-match standing-vocabulary tokens, declare `exit_contract=(0, 2)`, test that contract, and document the change.
- Under-scope: none. Every surface of `aw show` (`human`, `--agent`, `--json`), its `command_surface.py` declaration, its conformance matrix interaction, its help text, its contract documentation, and its regression tests are included.

## Required tests / validation

- Targeted new test module: `python3 -m pytest tests/test_cli_show.py`
- Conformance and command-surface suites: `python3 -m pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py`
- Full repository test suite (run bare per repository rules): `python3 -m pytest`
- IPD structural and pre-transition lint: `aw ipd lint --phase pre-transition .aw/records/plans/pending/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md`
- Release gates and leak sanitizer: `aw check release-gates` and `aw sanitize --agent`

## Spec / documentation sync

- `docs/cli-output-contract.md` Section 11.1 ("Precedent and Scope"): add `aw show` to the list of read verbs conforming to the zero-match selector refusal and standing-vocabulary exemption convention.
- `CHANGELOG.md` (`## [Unreleased]` -> `### Changed`): record `aw show <ref>` moving from exit 1 (`show.not_found`) to exit 2 (`cannot-run`) on non-vocabulary zero-match selectors, exiting 0 (`clean`) on zero-match standing-vocabulary tokens, and narrowing its declared `exit_contract` in `agent_workflows/command_surface.py` from `(0, 1, 2)` to `(0, 2)`.
- Spec `.aw/records/specs/20260928-1400-01-25kzda-cli-usability-quiet-default-and-selector-hygiene.spec.md`: no edit needed because Sections 2.3 and 2.4a already specify this exact behavior.

## Open questions

### OQ-01: How should `aw show <ref>` handle a standing-vocabulary token (`ref.strip().lower() in find_selector_vocabulary()`) that matches zero artifacts?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence. `aw show` explicitly accepts status selectors (`cli._DESCRIPTIONS["show"]` at `agent_workflows/cli.py`, line 493; `p_show` at `agent_workflows/cli.py`, line 4382; `cli._run_show` comment at line 12513) and resolves them through `selectors.resolve_selectors` (`MATCH_STATUS` at rung 4). Per Spec `25kzda` Sections 2.3 and 2.4a and `docs/cli-output-contract.md` Section 11.1, a standing-vocabulary status/kind/facet token (`ref.strip().lower() in find_selector_vocabulary()`) asks a standing state question across the repository and is exempt from zero-match refusal: when it matches zero artifacts, `cli._run_show` returns exit `0` (`status="clean"`, `verified=True`, `complete=True`, `Term.empty_result(..., status="ok")` on human `stdout`).

### OQ-02: Once `aw show`'s zero-match refusal moves from exit 1 to exit 2, does exit 1 remain reachable in `cli._run_show`, or should `CommandDeclaration(command="show", ...)` drop `1` from `exit_contract`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence. Inspection of `cli._run_show` (`agent_workflows/cli.py`, lines 12497-12587) confirms that `_run_show` has only two post-lookup branches: `unique` non-empty (returns `0`) and `unique` empty (returns `0` for standing-vocabulary tokens and `2` for unresolved selectors). Exit `1` is a vestige of the removed action-ledger lookup (`19bd75020`) that `ef55eadb1` wrapped as `show.not_found` and `efd2019ad` recorded as `exit_contract=(0, 1, 2)` in `agent_workflows/command_surface.py` (line 222); neither `ef55eadb1` nor `efd2019ad` has shipped in any release tag (`git tag --contains` is empty for both). Keeping `1` in `exit_contract` on a `command_class="read"` verb causes `tests.conformance_matrix.required_scenarios` (`tests/conformance_matrix.py`, line 81) to demand a `domain_failure` scenario that `aw show` cannot produce. Therefore `E-03` narrows `show`'s `exit_contract` in `agent_workflows/command_surface.py` from `(0, 1, 2)` to `(0, 2)`, matching `layout`, `graduation`, `research find`, `reviews decisions`, `host probe`, and `host capabilities`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest` summary line from the pre-change worktree and the 12-cell pre-change table (`human`, `--agent`, `--json` x `zzzzzz`, `prompt-library`, `approved`, `f36de0`) produced by driving `cli.main(["show", ...])` in `E-01`, showing `zzzzzz` and `prompt-library` exiting `1` prior to the fix.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` and the 12-cell post-change matrix produced by driving `cli.main(["show", ...])` across (`human`, `--agent`, `--json`) x (`zzzzzz`, `prompt-library`, `approved`, `f36de0`) after `E-02`: `zzzzzz` exits `2` on all 3 surfaces (`len(stdout) == 0` and `len(stderr) > 0` on human; `outcome == "cannot-run"`, `verified is False`, `complete is False`, `unresolved_selectors == ["zzzzzz"]` on `--agent`; `status == "cannot-run"`, `exit_code == 2` on `--json`), `prompt-library` exits `0` on all 3 surfaces (`len(stdout) > 0` and `len(stderr) == 0` on human; `outcome == "clean"` on `--agent`; `status == "clean"` on `--json`), and `approved` and `f36de0` exit `0` on all 3 surfaces.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/command_surface.py` showing `exit_contract=(0, 2)` on `CommandDeclaration(command="show", ...)`, plus pasted output of `python3 -m pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py` exiting `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted output of `python3 -m pytest tests/test_cli_show.py -v` showing all tests in `tests/test_cli_show.py` passing (`exit 0`), covering `UNKNOWN` token exit `2` on all 3 surfaces, home-path redaction on refusal, standing-vocabulary zero-match exit `0` on all 3 surfaces, positive selector matches (`id6`, `setid`, status, filename substring), and `exit_contract == (0, 2)`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- docs/cli-output-contract.md CHANGELOG.md`, verification that zero em/en dashes (`\u2014` / `\u2013`) appear in `docs/cli-output-contract.md` and `CHANGELOG.md` added lines, and pasted exit-0 outputs of `python3 -m pytest` (bare full suite), `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Execution contract**: Execute `E-01` through `E-05` in dependency order inside an isolated worktree. Do not mark any `E-*` item `performed` before running its action, and do not mark any `V-*` item `pass` without pasting the concrete observed output into `Observed evidence:`. Run `python3 -m pytest` bare (never `-n0`, never extra `-q`, never `-p no:randomly`). Commit only files listed in `- Scope-Paths:` plus this IPD using `aw commit uhp38x -- <paths>`.
- **Post-gate lifecycle move**: Once `E-01`..`E-05` are `performed`, `V-01`..`V-05` are `pass`, and `aw ipd lint --phase pre-transition` reports 0 errors, transition the plan to `executed` via `aw ipd set executed uhp38x` (which moves the file from `.aw/records/plans/pending/` to `.aw/records/plans/executed/` and refreshes `.aw/records/plans/index.md`).
