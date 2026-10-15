# IPD: Make aw show refuse a zero-match selector with exit 2 and drop unreachable exit 1 from its contract

- Date: 2026-10-14
- Kind: child
- Concern: `aw show <ref>` exits 1 (`outcome: "findings"`, diagnostic rule `show.not_found`) when `<ref>` matches zero artifacts across `_run_show`'s seven queried record types, instead of refusing an unresolved non-vocabulary selector at exit 2 (`outcome: "cannot-run"`) and answering a standing-vocabulary token that happens to match zero records (`ref.strip().lower() in find_selector_vocabulary()`) with exit 0 (`outcome: "clean"`). Re-measured in this lane at HEAD `22e589747` with token `zzzzzz`: `aw show zzzzzz` exits 1 on human (writing `✗ FAIL  no records artifact matched 'zzzzzz'` to `stdout`, not `stderr`), exits 1 on `--agent` (`{"schema":"aw.agent/v1","kind":"result","cmd":"show","outcome":"findings","exit":1,...,"diagnostics":[{"location":"zzzzzz","rule":"show.not_found"}],"next":"aw find"}`, re-measured at review), and exits 1 on `--json` (`status: "findings"`, `exit_code: 1`). Likewise, `aw show prompt-library` (a standing-vocabulary status token in `cli.find_selector_vocabulary()` with zero matching artifacts in the live tree) exits 1 with `show.not_found` instead of exit 0. IPD `zyj8io` V-08's survey table recorded `aw show <sel>` as `2 | 2 | 2 | 2 | Conforming` because the survey drove `aw show` with `--paths`, which `argparse` rejects on `show` at exit 2 before `_run_show` runs; consequently backlog `tbe8v0` and sibling plan `yxsfjc` omitted `aw show`. Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`) Section 2.3 rules "Zero matches return exit 2" and Section 2.4a exempts standing status selectors ("An empty result is a success, not an error"); that spec governs the runner verbs and serves as PRECEDENT for read verbs, while `docs/cli-output-contract.md` Section 11.1 is the binding read-verb zero-match refusal convention. Finally, `command_surface.py` declares `CommandDeclaration(command="show", command_class="read", exit_contract=(0, 1, 2), ...)`; once `show.not_found` moves from exit 1 to exit 2, exit 1 is unreachable in `cli._run_show`, and keeping `1` in `exit_contract` would falsely require a `domain_failure` scenario under `tests.conformance_matrix.required_scenarios`.
- Scope: Update `cli._run_show` in `agent_workflows/cli.py` so that, when `unique` is empty, it asks the SHARED predicate `cli.selector_tokens_naming_no_artifact(repo_root, [ref])` (shipped by `yxsfjc`) whether `<ref>` names no artifact anywhere. A refusable token is refused at exit 2 through the SHARED emitter `cli.emit_zero_match_selector_refusal(ctx=ctx, cmd="show", tokens=refusable, next_cmd="aw find", next_desc="list all records", searched="all artifact types", term=term)` (`outcome: "cannot-run"`, `verified=False`, `complete=False`, home-path-redacted token; human on `stderr` with `stdout` empty; `--agent` `kind: "error"` with `unresolved_selectors`/`unresolved_targets`/`error`/`next`, schema-validated; `--json` `status="cannot-run"`, `exit_code=2`). A non-refusable token (a standing-vocabulary token, an existing file path, or a token naming a real artifact in a tree `aw show` does not display, e.g. a `releases` or `reviews` record) returns exit 0 (`status="clean"`, `verified=True`, `complete=True`, `Term.empty_result(..., status="clean")` on `stdout`). Narrow `CommandDeclaration(command="show", ...)` in `agent_workflows/command_surface.py` from `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` with an explanatory comment. Clean up stale action-ledger fallback prose in `cli._DESCRIPTIONS["show"]` and `p_show` parser help/epilog in `agent_workflows/cli.py`. Add behavioral and contract regression tests in `tests/test_cli_show.py`, and sync `docs/cli-output-contract.md` Section 11.1 and `CHANGELOG.md`. Does NOT change which record types `_run_show` searches when `<ref>` resolves, does NOT alter any other verb, and does NOT modify the shared predicate or emitter it reuses from executed sibling `yxsfjc`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_cli_show.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md
- Item-Dependencies: executed:zyj8io, executed:yxsfjc
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: upryxf
- From-Spec: none
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: selquiet
- Order: 3
- Highest E allocated: 06
- Author: Antigravity
- Id: uhp38x
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Record: .aw/records/reviews/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.review.md Round 1
- 2026-10-14 to-review (aw set): Authored from backlog item upryxf at HEAD 22e589747: aw show zero-match exits 2 (cannot-run), standing-vocabulary zero-match exits 0 (clean), and show exit_contract narrows from (0, 1, 2) to (0, 2).

- 2026-10-14 draft (Antigravity): created.

## Goal

Make `aw show <ref>` obey the repository's read-verb selector contract (`docs/cli-output-contract.md` Section 11.1, with Spec `25kzda` Sections 2.3 and 2.4a as precedent): refuse a selector naming no artifact anywhere in the repository at exit 2 (`cannot-run`) across human (`stderr`), `--agent`, and `--json`, through the shared predicate and emitter the other read verbs use; return exit 0 (`clean`) when a standing-vocabulary token matches zero displayable artifacts or the token names a real artifact `aw show` does not display; and narrow `show`'s declared `exit_contract` in `agent_workflows/command_surface.py` from `(0, 1, 2)` to `(0, 2)` so the declaration matches the reachable exit codes of `cli._run_show`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Pre-change baseline capture

- [ ] E-01 Capture the pre-change baseline in this worktree before editing any file: run `python3 -m pytest` (bare, with default `xdist` and `pytest-randomly` flags intact) and record the summary line; re-derive at execution time one standing-vocabulary token that matches zero displayable artifacts (a member of `cli.find_selector_vocabulary()` such as `prompt-library`; if `aw show <token>` now matches something, pick another member and record which); then drive `aw show` (via `python3 -m agent_workflows show ...`) across its 3 output surfaces (`human`, `--agent`, `--json`) x 5 token classes (`UNKNOWN` `zzzzzz`, `VOCABULARY-ZERO-MATCH` the re-derived token, `VOCABULARY-MATCHING` `approved`, `MATCHING` `f36de0`, and `NON-DISPLAYED-REAL-ARTIFACT` `f33nrj`, the release record id6 under `.aw/records/releases/`, which `_run_show`'s `record_types` does not search), recording `(exit_code, len(stdout), len(stderr), outcome/status)` for all 15 invocations.
  - Depends on: none
  - Expected outcome: The baseline suite passes and the 15-cell pre-change matrix shows `zzzzzz`, the vocabulary-zero-match token, and `f33nrj` exiting `1` with `outcome: "findings"` / `rule: "show.not_found"` and human output on `stdout` (`len(stderr) == 0`), while `approved` and `f36de0` exit `0` with `outcome: "clean"`. Any deviation from this expected baseline is recorded verbatim.
  - Execution state: pending

### Task group 2: Align `cli._run_show`, `show` help text, and `command_surface.py`

- [ ] E-02 Replace the zero-match tail of `cli._run_show` in `agent_workflows/cli.py` (the block after `if unique:` that builds `CommandResult(command="show", status="findings", exit_code=1, ...)` with `rule="show.not_found"`, plus the human `term.empty_result(..., status="fail")` / `return 1`) with the SHARED read-verb mechanism shipped by executed sibling `yxsfjc`: (1) `refusable = selector_tokens_naming_no_artifact(repo_root, [ref])`; (2) if `refusable` is non-empty, `return emit_zero_match_selector_refusal(ctx=ctx, cmd="show", tokens=refusable, next_cmd="aw find", next_desc="list all records", searched="all artifact types", term=term)` (that emitter already redacts every token through `agent_schema.redact_home_paths`, hand-builds and schema-validates the `--agent` `kind: "error"` record, emits `--json` `status="cannot-run"`/`exit_code=2`, and writes the human message to `stderr` with `stdout` empty; do NOT re-implement any of it); (3) otherwise (a standing-vocabulary token, an existing file path, or a token naming a real artifact in a tree `_run_show` does not display, such as a `releases` or `reviews` record) return exit `0`: on `--agent`/`--json` emit `CommandResult(command="show", status="clean", exit_code=0, summary=f"matched 0 displayable artifact(s) for '{ref}'", evidence=[Evidence(key="show-match", value={"count": 0}, status="verified")], data={"matches": [], "contents": {}}, next_actions=[NextAction(command=f"aw find {ref}", description="search every record tree")])` through `get_renderer(ctx).emit(res, ctx)`, and on human call `term.empty_result(summary=f"no displayable records for '{ref}'", filters={"ref": ref}, next_action=NextAction(command=f"aw find {ref}", description="search every record tree"), status="clean")` (on `stdout`) and `return 0`. Drop the `Diagnostic` import from `_run_show` if nothing else there uses it. Do NOT modify `selector_tokens_naming_no_artifact`, `emit_zero_match_selector_refusal`, or the `record_types` tuple.
  - Depends on: E-01
  - Expected outcome: `aw show` exits `2` (`cannot-run`, naming the redacted token; human on `stderr` with empty `stdout`) exactly when `selector_tokens_naming_no_artifact` returns the token; exits `0` (`clean`, human on `stdout`, empty `stderr`) for a non-refusable zero-match token (standing vocabulary, existing file path, or real artifact in a non-displayed tree); and keeps its existing exit `0` output unchanged when one or more artifacts match. No code path in `_run_show` returns `1`.
  - Execution state: pending

- [ ] E-06 Correct the stale `aw show` help text in `agent_workflows/cli.py`: rewrite `_DESCRIPTIONS["show"]` (the `"show": (` entry, which says it "falls back to the operational action ledger (an action id, or id@generation)"), the `p_show = sub.add_parser("show", ...)` `help=` string ("records first, then the action ledger"), its epilog example `aw show setup-repo-v1  # an action from the ledger`, and the `action_ref` argument help ("or an action id[@generation]"), so they describe only the records lookup `_run_show` actually performs (action-ledger support was removed in `19bd75020`) and state that a selector naming no artifact anywhere exits 2 while a standing-status token with nothing to show exits 0. Keep the argparse dest `action_ref` unchanged. Write no em or en dashes in the new help text.
  - Depends on: E-02
  - Expected outcome: `python3 -m agent_workflows show --help` no longer mentions an action ledger or `id@generation`, documents the exit-2 refusal and the exit-0 standing-status answer, and contains no `\u2014`/`\u2013` characters.
  - Execution state: pending

- [ ] E-03 Update `CommandDeclaration(command="show", ...)` in `agent_workflows/command_surface.py` from `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` with a one-line comment explaining that `aw show` is a pure read verb whose zero-match refusal exits `2` (`upryxf`; `docs/cli-output-contract.md` Section 11.1) and has no reachable exit `1` path (so `tests.conformance_matrix.required_scenarios` does not demand a synthetic `domain_failure` scenario), then run the command-surface and conformance test modules.
  - Depends on: E-02
  - Expected outcome: `command_surface.get_declaration("show").exit_contract == (0, 2)`, `"domain_failure" not in conformance_matrix.required_scenarios(get_declaration("show"))`, and `pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py` passes with 0 failures.
  - Execution state: pending

### Task group 3: Regression tests, documentation sync, and final validation gates

- [ ] E-04 Create `tests/test_cli_show.py` exercising `aw show` through `cli.main(["show", <token>, "--dir", <tmp>, ...])` against an isolated temporary repository fixture (pattern: `tests/test_read_verb_zero_match_refusal.py` `setUp`; the fixture holds plans, a backlog item, and one `.aw/records/releases/` record), capturing `stdout`/`stderr` and asserting on exit codes and parsed output across all three surfaces (`human`, `--agent`, `--json`). No test reads production source (P16). Cases: (1) `UNKNOWN` non-vocabulary token (`zzzzzz`) exits `2` (`human` writes to `stderr` with `stdout == ""` and names `zzzzzz` + `aw find`; `--agent` emits one record passing `agent_schema.assert_valid_agent_record` with `kind == "error"`, `cmd == "show"`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`, `unresolved_selectors == ["zzzzzz"]`, `unresolved_targets == ["zzzzzz"]`, `"zzzzzz" in error`, `next == "aw find"`; `--json` emits `status == "cannot-run"`, `exit_code == 2`, `verified is False`, `complete is False`, `data["unresolved_selectors"] == ["zzzzzz"]`, `data["unresolved_targets"] == ["zzzzzz"]`); (2) home-path-shaped unknown token (`f"{Path.home()}/secret-missing-ref"`) exits `2` on all three surfaces with `~/secret-missing-ref` (the `agent_schema.redact_home_paths` form) in the output and the literal `str(Path.home())` absent from both streams; (3) standing-vocabulary tokens with zero displayable matches in the fixture (`reusable` and `prompt-library`) exit `0` on all three surfaces (`human`: `stdout` non-empty and naming the token, `stderr == ""`; `--agent`: `kind == "result"`, `outcome == "clean"`, `exit == 0`, `verified is True`, `complete is True`, `findings == 0`; `--json`: `status == "clean"`, `exit_code == 0`, `data["matches"] == []`, `data["contents"] == {}`); (4) a token naming a REAL artifact in a tree `aw show` does not display (the fixture release record's id6) exits `0` and is not refused on all three surfaces; (5) matching selector tokens (by `id6`, `setid`, standing status `to-review`, and filename substring) exit `0` on all three surfaces and return the matched artifact path and markdown body in `stdout` / `data["matches"]` / `data["contents"]`; and (6) every exit code observed in cases (1)-(5) is a member of `command_surface.get_declaration("show").exit_contract`, none is `1`, and `"domain_failure" not in conformance_matrix.required_scenarios(command_surface.get_declaration("show"))`.
  - Depends on: E-02, E-03, E-06
  - Expected outcome: `python3 -m pytest tests/test_cli_show.py` passes all tests in the new module with 0 failures.
  - Execution state: pending

- [ ] E-05 Update `docs/cli-output-contract.md` Section 11.1 (the "Precedent and Scope" bullet, whose read-verb list names `aw attention`, `aw find`, `aw reviews decisions`, `aw record-history`, `aw graduation` and `aw ipd recheck-readiness`) to add `aw show` to that list, and add one `- Changed:` bullet to `CHANGELOG.md` under the current `## 2.0.0 (pending)` heading (beside the existing bullet beginning "- Changed: `aw reviews decisions`, `aw record-history`, and `aw graduation` now refuse at exit 2"; this CHANGELOG has no `## [Unreleased]` / `### Changed` headings) recording that `aw show <ref>` now refuses at exit 2 (`cannot-run`) a selector naming no artifact anywhere, answers exit 0 when a standing-status token or a real but non-displayed artifact has nothing to show, and no longer exits 1. Write zero em/en dashes (`\u2014` / `\u2013`) in added lines. Then run the full suite (`python3 -m pytest`), `aw ipd lint --phase pre-transition <this plan>`, `aw check release-gates`, and `aw sanitize --agent`.
  - Depends on: E-04
  - Expected outcome: `docs/cli-output-contract.md` and `CHANGELOG.md` reflect the shipped behavior with 0 em/en dashes; the full `python3 -m pytest` suite, `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent` all exit 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Read-verb zero-match selector contract (`docs/cli-output-contract.md` Section 11.1 is binding; Spec `25kzda` Sections 2.3 and 2.4a are precedent only, because that spec governs the runner verbs, as Section 11.1's "Precedent and Scope" bullet states)**:
  - A selector token that names NO artifact in any tracked record tree and is not standing vocabulary is an unresolved-selector refusal (`outcome: "cannot-run"`, `exit: 2`, `verified: false`, `complete: false`), NOT a domain finding (`exit: 1`) and NOT a clean empty result (`exit: 0`).
  - A token in the standing status/kind/facet vocabulary (`cli.find_selector_vocabulary`, `def find_selector_vocabulary() -> FrozenSet[str]:` in `agent_workflows/cli.py`), an existing file path, or a token naming a REAL artifact with nothing to report, is not refused and answers `exit: 0` (`outcome: "clean"`). Section 11.1: "a selector that names a real artifact with nothing to report is a clean empty answer, while one naming no artifact anywhere in the repository is refused with exit 2."
  - ONE shared predicate, `cli.selector_tokens_naming_no_artifact(repo_root, tokens)`, and ONE shared emitter, `cli.emit_zero_match_selector_refusal(ctx, cmd, tokens, next_cmd, next_desc, searched, term)`, implement this; both were shipped by executed `yxsfjc` and are used by `_run_record_history` (the `refusable = selector_tokens_naming_no_artifact(repo_root, [id6])` block) and the other `yxsfjc` verbs. The emitter redacts every token with `agent_schema.redact_home_paths`, hand-builds and validates (`agent_schema.assert_valid_agent_record`) the `--agent` `kind: "error"` record because `CommandResult.to_agent_record()` (`agent_workflows/result_types.py`) omits `summary` and `data`, and writes human output to `stderr` with `stdout` empty (`docs/cli-output-contract.md` Section 11.4).
  - On human output, an `exit: 0` empty result goes to `stdout` via `term.empty_result(..., status="clean")` (the `_run_record_history` precedent).
- **Command surface declaration and conformance matrix (`agent_workflows/command_surface.py` and `tests/conformance_matrix.py`)**:
  - `tests.conformance_matrix.required_scenarios` (`tests/conformance_matrix.py`, `def required_scenarios(decl: CommandDeclaration) -> Tuple[str, ...]:`) appends `"domain_failure"` whenever `1 in decl.exit_contract and decl.command_class in ("read", "check", "bare")`.
  - Pure read/inspection verbs without a domain-findings mode (`layout`, `graduation`, `research find`, `reviews decisions`, `host probe`, `host capabilities` in `agent_workflows/command_surface.py`, line 51: `COMMAND_DECLARATIONS: tuple[CommandDeclaration, ...] = (`) declare `exit_contract=(0, 2)`.
- **Test and prose rules (`AGENTS.md` / `GEMINI.md`)**:
  - Run `python3 -m pytest` bare (never pass `-n0`, extra `-q`, or `-p no:randomly`).
  - Never write code-pinning tests (`inspect`, `ast`, regex/substring checks on source files); test observable CLI behavior and outcomes.
  - Write no em or en dashes (`\u2014` or `\u2013`) in user-facing prose (`docs/cli-output-contract.md`, `CHANGELOG.md`, CLI help strings).

## Findings

| ID | Category | Location | Observation | Impact |
|---|---|---|---|---|
| F-1 | Defect (`upryxf`) | `cli._run_show` (`agent_workflows/cli.py`, the tail after `if unique:` building `rule="show.not_found"`) | When `unique` is empty, `cli._run_show` returns `1` on all three surfaces: `--agent` and `--json` emit `CommandResult(command="show", status="findings", exit_code=1, ..., diagnostics=[Diagnostic(location=ref, rule="show.not_found", ...)])`, and human calls `term.empty_result(..., status="fail")` which writes to `sys.stdout` and returns `1`. | Violates `docs/cli-output-contract.md` Section 11.1 (`cannot-run` at exit 2, human output on `stderr` with `stdout` empty), following the Spec `25kzda` Section 2.3 precedent ("Zero matches return exit 2"). |
| F-2 | Defect (Standing vocabulary exemption) | `cli._run_show` (`agent_workflows/cli.py`, comment `# 1. Try to resolve the token as a RECORDS artifact (id6 \| setid \| filename \| status)`) | `aw show` advertises status tokens in `cli._DESCRIPTIONS["show"]` and `p_show`, and calls `selectors.resolve_selectors` which matches status tokens. Yet when a standing-vocabulary token in `cli.find_selector_vocabulary()` matches zero artifacts (re-measured this review: `aw show prompt-library --agent` returns `outcome:"findings"`, `exit:1`, rule `show.not_found`), `cli._run_show` treats it identically to a typo. The same happens for a REAL artifact in a tree `_run_show` does not search: `aw show f33nrj --json` (the release record `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`) returns `status:"findings"`, `exit_code:1`, while `selector_tokens_naming_no_artifact(Path("."), ["f33nrj"])` returns `()` (not refusable). | Violates `docs/cli-output-contract.md` Section 11.1: a standing-vocabulary token with zero matches, or a selector naming a real artifact with nothing to show, must not be refused. A vocabulary-only check (the original E-02 design) would have REFUSED `f33nrj` at exit 2, mis-telling the operator that a real release record does not exist. |
| F-3 | Root cause of `zyj8io` V-08 misrecording | `.aw/records/plans/executed/20260929-selquiet-01-zyj8io-make-aw-find-refuse-a-zero-match-selector-with-exit-2-exempt.ipd.md` (V-08 survey table row `` | `aw show <sel>` | 2 | 2 | 2 | 2 | Conforming (25kzda) | ``) | `zyj8io` V-08 recorded `aw show <sel>` as `2 \| 2 \| 2 \| 2 \| Conforming` because the survey script passed `--paths` (`aw show zzzzzz --paths`), which `argparse` rejects on `show` at exit `2` (`error: unrecognized arguments: --paths`) before `cli._run_show` executes. Without `--paths`, `aw show zzzzzz` exits `1` on human, `--agent`, and `--json`. | Explains why `tbe8v0` and sibling plan `yxsfjc` did not include `aw show`, and why `upryxf` was filed to close the gap. |
| F-4 | Unreachable exit `1` in `command_surface.py` | `agent_workflows/command_surface.py` (`COMMAND_DECLARATIONS`, `CommandDeclaration(command="show", command_class="read", ..., exit_contract=(0, 1, 2))`) | After E-02, `cli._run_show` has only these post-lookup outcomes: `unique` non-empty (returns `0`), `unique` empty and refusable (returns `2` via the shared emitter), and `unique` empty and not refusable (returns `0`). Once `show.not_found` moves from exit `1` to exit `2`, exit `1` is completely unreachable in `cli._run_show`. Neither `ef55eadb1` (which added `show.not_found`) nor `efd2019ad` (which declared `exit_contract=(0, 1, 2)`) has shipped in any git release tag (`git tag --contains efd2019ad` and `git tag --contains ef55eadb1` are both empty). | Leaving `1` in `exit_contract` for a `command_class="read"` verb forces `tests.conformance_matrix.required_scenarios` to require a `domain_failure` scenario that `aw show` can never produce. Narrowing `exit_contract` to `(0, 2)` matches `layout`, `graduation`, `research find`, `reviews decisions`, `host probe`, and `host capabilities`. |
| F-5 | Cost of the shared predicate on the zero-match path | `cli.selector_tokens_naming_no_artifact` (loops every `artifact_types.ARTIFACT_TYPES` member, 11 types, after dropping vocabulary tokens and existing file paths) | The predicate is NOT free: measured this review in this worktree, `selector_tokens_naming_no_artifact(Path("."), ["zzzzzz"])` took 1.48s and 1.35s warm, against about 0.98s for the whole current `aw show zzzzzz`. Vocabulary tokens and existing paths short-circuit before any resolution. The cost lands only on the zero-match path (a typo or a non-displayed artifact), never on a successful `aw show`. Searching only the four trees `_run_show` skipped (`comms`, `releases`, `reviews`, `other`) measured 0.88s to 1.06s, so a bespoke variant would save roughly 0.4s at the price of a second predicate. | Accepted: one shared predicate across every read verb (the `yxsfjc` design) outweighs about 0.4s on an error path. Recorded so a reviewer can dispute the number (AGENTS.md "INEFFICIENCY A USER CAN NOTICE"). |
| F-6 | Reuse of the shipped mechanism from `yxsfjc` | `.aw/records/plans/executed/20261012-selquiet-02-yxsfjc-make-reviews-decisions-record-history-graduation-and-ipd-rec.ipd.md`; `cli.emit_zero_match_selector_refusal` and `cli.selector_tokens_naming_no_artifact` in `agent_workflows/cli.py` | `yxsfjc` is now `executed` and both shared helpers exist at HEAD. The original plan hedged ("if already present ... or else" hand-build an identical record), which would have allowed a second, divergent emitter, and keyed refusal on vocabulary alone. | E-02 now calls the shared predicate and emitter unconditionally, and `- Item-Dependencies:` adds `executed:yxsfjc` (satisfied today) so the dependency on those symbols is declared. |
| F-7 | Stale action-ledger help text on `aw show` | `cli._DESCRIPTIONS["show"]` (the `"show": (` entry) and `p_show = sub.add_parser("show", ...)` in `agent_workflows/cli.py` | `_DESCRIPTIONS["show"]` says it "falls back to the operational action ledger (an action id, or id@generation)"; `p_show` help says "records first, then the action ledger", its epilog shows `aw show setup-repo-v1  # an action from the ledger`, and the `action_ref` help says "or an action id[@generation]". Action-ledger support was removed from `_run_show` in commit `19bd75020`. | Owned by the separate `E-06` (split out of E-02 as an independent deliverable with its own `V-06`). |

## Proposed changes (ordered, validatable)

1. **Baseline measurement (`E-01` / `V-01`)**:
   - Run `python3 -m pytest` bare and record the summary line.
   - Re-derive a standing-vocabulary token with zero displayable matches, then drive `aw show` across `(human, --agent, --json)` x `(zzzzzz, <vocab-zero-match token>, approved, f36de0, f33nrj)` and record the 15-cell pre-change table.
2. **Route `cli._run_show`'s zero-match path through the shared mechanism (`E-02` / `V-02`)**:
   - In `cli._run_show` (`agent_workflows/cli.py`, `def _run_show(`), replace the tail after `if unique:` (the `rule="show.not_found"` `CommandResult` and the human `term.empty_result(..., status="fail")` / `return 1`) with: `refusable = selector_tokens_naming_no_artifact(repo_root, [ref])`; if non-empty, `return emit_zero_match_selector_refusal(ctx=ctx, cmd="show", tokens=refusable, next_cmd="aw find", next_desc="list all records", searched="all artifact types", term=term)`; otherwise emit a `clean` exit-0 empty answer (`data={"matches": [], "contents": {}}` on `--agent`/`--json`; `term.empty_result(..., status="clean")` on human `stdout`) whose next action is `aw find <ref>`.
3. **Correct the stale help text (`E-06` / `V-06`)**:
   - Rewrite `_DESCRIPTIONS["show"]`, the `p_show` `help=`/epilog, and the `action_ref` help to drop every action-ledger reference and state the exit-2 refusal and exit-0 standing-status answer.
4. **Narrow `show` `exit_contract` in `agent_workflows/command_surface.py` (`E-03` / `V-03`)**:
   - In `COMMAND_DECLARATIONS`, change `CommandDeclaration(command="show", ...)` from `exit_contract=(0, 1, 2)` to `exit_contract=(0, 2)` with a one-line comment citing `upryxf` and `tests.conformance_matrix.required_scenarios`.
5. **Add behavioral test suite `tests/test_cli_show.py` (`E-04` / `V-04`)**:
   - Cover unknown-token refusal, home-path redaction, standing-vocabulary zero-match exit 0, non-displayed real artifact exit 0, positive matches, and observed exit codes being members of the declared `exit_contract` (never `1`).
6. **Sync `docs/cli-output-contract.md` and `CHANGELOG.md` and run full verification (`E-05` / `V-05`)**:
   - Add `aw show` to Section 11.1's read-verb list and one `- Changed:` bullet under `## 2.0.0 (pending)`, then run `python3 -m pytest`, `aw ipd lint --phase pre-transition`, `aw check release-gates`, and `aw sanitize --agent`.

## Deferred / out of scope (with reason)

- Widening `cli._run_show`'s `record_types` tuple (`("plans", "specs", "research", "backlog", "prompts", "walkthroughs", "roadmaps")`) to the remaining `artifact_types.ARTIFACT_TYPES` members (`comms`, `releases`, `reviews`, `other`), so that `aw show f33nrj` would DISPLAY the release record instead of answering a clean empty result:
  - Carrier-Declined: `upryxf` scopes only the zero-match exit code and `exit_contract` declaration of `aw show`; changing which artifact trees `aw show` displays on a match would alter positive-match behavior outside `upryxf`'s scope. E-02's exit-0 answer for such a token names `aw find <ref>`, which does resolve it, so the operator is not misled meanwhile.
- Changing zero-match behavior on `aw reviews decisions`, `aw record-history`, `aw graduation`, or `aw ipd recheck-readiness`:
  - Carrier: yxsfjc
  - Carrier-Evidence: .aw/records/plans/executed/20261012-selquiet-02-yxsfjc-make-reviews-decisions-record-history-graduation-and-ipd-rec.ipd.md

## Scope check

- Over-scope: none. Every touched file in `- Scope-Paths:` is directly required to make `aw show` refuse at exit 2 a selector naming no artifact anywhere, answer exit 0 otherwise, declare `exit_contract=(0, 2)`, correct its help text, test that contract, and document the change. The plan file itself is listed so its own execution record can be committed with the change.
- Under-scope: none. Every surface of `aw show` (`human`, `--agent`, `--json`), its `command_surface.py` declaration, its conformance matrix interaction, its help text, its contract documentation, and its regression tests are included.

## Required tests / validation

- Targeted new test module: `python3 -m pytest tests/test_cli_show.py`
- Shared-mechanism regression (the predicate and emitter `_run_show` now reuses): `python3 -m pytest tests/test_read_verb_zero_match_refusal.py`
- Conformance and command-surface suites: `python3 -m pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py`
- Full repository test suite (run bare per repository rules): `python3 -m pytest`
- IPD structural and pre-transition lint: `aw ipd lint --phase pre-transition .aw/records/plans/pending/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md`
- Release gates and leak sanitizer: `aw check release-gates` and `aw sanitize --agent`

## Spec / documentation sync

- `docs/cli-output-contract.md` Section 11.1 ("Precedent and Scope"): add `aw show` to the list of read verbs that refuse a selector naming no artifact at exit 2 and keep standing questions and real-but-empty answers at exit 0.
- `CHANGELOG.md` (under `## 2.0.0 (pending)`, as a `- Changed:` bullet beside the `yxsfjc` bullet): record `aw show <ref>` moving from exit 1 (`show.not_found`) to exit 2 (`cannot-run`) for a selector naming no artifact anywhere, and answering exit 0 for a standing-status token or a real non-displayed artifact with nothing to show.
- Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`): no edit. It governs the runner verbs; `docs/cli-output-contract.md` Section 11.1 already records that read verbs take it as precedent, and that is the document this plan syncs. No `.spec.md` is in `- Scope-Paths:`.

## Open questions

### OQ-01: How should `aw show <ref>` handle a zero-match token that is a standing-vocabulary token, or that names a real artifact `aw show` does not display?

- Blocking: no
- Status: resolved
- Owner: plan author (revised at /plan-review)
- Resolution or deferral rationale: Resolved from repository evidence. `docs/cli-output-contract.md` Section 11.1 ("Precedent and Scope") rules: "a selector that names a real artifact with nothing to report is a clean empty answer, while one naming no artifact anywhere in the repository is refused with exit 2", and names the shared predicate `cli.selector_tokens_naming_no_artifact`. That predicate drops standing-vocabulary tokens (`cli.find_selector_vocabulary`) and existing file paths, then searches every `artifact_types.ARTIFACT_TYPES` member. Demonstrated this review: `selector_tokens_naming_no_artifact(Path("."), ["zzzzzz", "prompt-library", "f36de0", "plans"])` returned `('zzzzzz',)`, and `selector_tokens_naming_no_artifact(Path("."), ["f33nrj", "README.md"])` returned `()`. So `_run_show` refuses exactly the predicate's output at exit 2 via `cli.emit_zero_match_selector_refusal`, and answers exit `0` (`status="clean"`, `term.empty_result(..., status="clean")` on human `stdout`) otherwise. The original vocabulary-only check was rejected because it would have refused `f33nrj`, a real release record.

### OQ-02: Once `aw show`'s zero-match refusal moves from exit 1 to exit 2, does exit 1 remain reachable in `cli._run_show`, or should `CommandDeclaration(command="show", ...)` drop `1` from `exit_contract`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence. After E-02, `cli._run_show` has three post-lookup outcomes: `unique` non-empty (returns `0`), empty and refusable (returns `2` from `emit_zero_match_selector_refusal`), empty and not refusable (returns `0`). Exit `1` is a vestige: commit `19bd75020` removed the action-ledger lookup, `ef55eadb1` added `show.not_found`, and `efd2019ad` declared `exit_contract=(0, 1, 2)`; `git tag --contains` prints nothing for either of the latter two (re-run this review), so no released contract promises exit 1. Keeping `1` on a `command_class="read"` verb makes `tests.conformance_matrix.required_scenarios` demand a `domain_failure` scenario `aw show` cannot produce. Therefore `E-03` narrows the declaration to `(0, 2)`, matching other pure read verbs such as `layout`, `graduation`, `research find` and `reviews decisions`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest` summary line from the pre-change worktree, the name of the re-derived vocabulary-zero-match token, and the pasted 15-cell pre-change table (`human`, `--agent`, `--json` x `zzzzzz`, that token, `approved`, `f36de0`, `f33nrj`) produced by `python3 -m agent_workflows show ...`, showing `zzzzzz`, the vocabulary token and `f33nrj` exiting `1` prior to the fix (or the verbatim deviation).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` hunk for `_run_show` showing it calls `selector_tokens_naming_no_artifact` and `emit_zero_match_selector_refusal` and no longer contains `show.not_found` or a `return 1`, and the pasted 15-cell post-change matrix (same tokens and surfaces as V-01): `zzzzzz` exits `2` on all 3 surfaces (human `len(stdout) == 0`, `len(stderr) > 0`; `--agent` `kind == "error"`, `outcome == "cannot-run"`, `verified is False`, `complete is False`, `unresolved_selectors == ["zzzzzz"]`; `--json` `status == "cannot-run"`, `exit_code == 2`); the vocabulary token and `f33nrj` exit `0` on all 3 surfaces (human `len(stdout) > 0`, `len(stderr) == 0`; `--agent` `outcome == "clean"`; `--json` `status == "clean"`); and `approved` and `f36de0` exit `0` with the same matched-path set as in V-01. The observation is produced by the `_run_show` code path E-02 writes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- agent_workflows/command_surface.py` showing `exit_contract=(0, 2)` on `CommandDeclaration(command="show", ...)`, plus pasted output of `python3 -m pytest tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_exit_contract_conformance.py tests/test_agent_surface_conformance.py` with its `passed` summary line and exit `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" tests/test_cli_show.py -v` showing every test in the module passing (exit `0`), with test names or docstrings showing each of E-04's six cases is pinned (unknown-token exit 2 on all 3 surfaces, home-path redaction, standing-vocabulary zero-match exit 0, non-displayed real artifact exit 0, positive matches, observed exits within the declared `exit_contract`); plus pasted output of `python3 -m pytest tests/test_read_verb_zero_match_refusal.py` passing, proving the shared helpers were not regressed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- docs/cli-output-contract.md CHANGELOG.md`; pasted output of a check over the ADDED lines of that diff for `\u2014` / `\u2013` returning no matches; and pasted exit-0 outputs of `python3 -m pytest` (bare full suite, with its summary line), `aw ipd lint --phase pre-transition <this plan>`, `aw check release-gates`, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `git diff -- agent_workflows/cli.py` hunks for `_DESCRIPTIONS["show"]` and `p_show`, and the pasted full output of `python3 -m agent_workflows show --help`, showing no occurrence of `ledger` or `@generation`, the exit-2 refusal and exit-0 standing-status behavior described, and no `\u2014`/`\u2013` characters.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved uhp38x --by-human`); no open questions remain (OQ-01 and OQ-02 are resolved from repository evidence). Begin with `aw ipd begin uhp38x`, then perform `E-01`, `E-02`, `E-06`, `E-03`, `E-04`, `E-05` in dependency order. Do not mark any `E-*` item `performed` before running its action.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or `cli.selector_tokens_naming_no_artifact` / `cli.emit_zero_match_selector_refusal` being absent or having a different signature from the one cited in the conventions section (do not re-implement them).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*` `Observed evidence:`; never claim a result you did not run. Run `python3 -m pytest` bare (never `-n0`, never an extra `-q`, never `-p no:randomly`).

Commits: commit only the Scope-Paths files you changed through `aw commit uhp38x -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize uhp38x`. Never hand-roll a `git mv`.
