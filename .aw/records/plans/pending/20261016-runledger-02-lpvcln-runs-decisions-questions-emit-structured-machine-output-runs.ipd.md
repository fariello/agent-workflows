# IPD: runs decisions/questions emit structured machine output; runs evidence/verify-ledger stop leaking absolute ledger paths

- Date: 2026-10-16
- Kind: child
- Concern: `aw runs decisions` and `aw runs questions` print raw markdown under `--agent`/`--json` (stdout is not parseable by `json.loads`), and `aw runs evidence` (machine `ledger` key and human header) plus `aw runs verify-ledger` (human `Ledger:` and `FAIL:` lines) print the absolute ledger path.
- Scope: Give the two projection leaves a bare-JSON machine payload (same `_emit_machine` family as their `aw runs` siblings) while keeping human output and exit codes unchanged; route every ledger path these two ledger leaves print through `agent_schema.normalize_repo_path`; add behavioral tests; update the live conformance sweep and exemption registry that currently pin the raw-markdown gap; add a CHANGELOG line.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_runs_machine_output_paths.py, tests/test_live_conformance_sweep.py, tests/conformance_matrix.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: hbok5d
- Set: runledger
- Order: 2
- Highest E allocated: 06
- Author: opencode
- Id: lpvcln

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog hbok5d (F-07, F-08 measured by g5s94t).

## Goal

Make every `--agent`/`--json` stdout of `aw runs decisions` and `aw runs questions` a single parseable JSON object, and make `aw runs evidence` and `aw runs verify-ledger` print the ledger as a repo-relative path in every mode, so the machine surface is parseable and sanitizer-clean (D92 / `normalize_repo_path` contract), without changing exit codes or human projection text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Structured machine output for the projection leaves

- [ ] E-01 In `agent_workflows/run_cli.py`, factor `_run_decisions` and `_run_questions` through one helper (for example `_emit_projection(args, kind, filename, empty_marker)`). Human mode stays byte-identical (prints the markdown; missing file prints the `no ... projection found for this run (<path>)` line). When `_machine(args)` is true: (a) projection present -> `_emit_machine(args, {"ok": True, "projection": "decisions"|"questions", "run_id": <target>, "path": <repo-relative path>, "empty": <bool>, "entry_ids": [<ids from "## " heading lines, with any " (SUPERSEDED)"/" [consultation_preferred]" suffix stripped>], "content": <markdown text>, "exit_code": <0|1>})`; (b) projection missing -> `_emit_error(args, "no <kind> projection found for this run (<repo-relative path>)", 2, extra={"projection": <kind>, "path": <repo-relative path>})`. The path is `agent_schema.normalize_repo_path(path, repo_root)` where `repo_root` is the same `resolve_verb_repo_root(args.dir)` `_projection_dir` uses. Exit codes stay 0 found / 1 empty / 2 missing.
  - Depends on: none
  - Expected outcome: `aw runs decisions <id> --json` and `--agent` stdout parse with `json.loads` (agent: one compact line) into a dict whose `projection`, `empty`, `content` and `exit_code` agree with the projection file and the process exit code; human stdout unchanged.
  - Execution state: pending

### Task group 2: Repo-relative ledger paths

- [ ] E-02 In `run_cli._run_evidence`, compute `rel_ledger = agent_schema.normalize_repo_path(ledger_file, repo_dir)` once and use it for the machine payload `"ledger"` key (replacing `str(ledger_file)`) and the human header `Evidence for <ledger> (N items):`.
  - Depends on: none
  - Expected outcome: `aw runs evidence <id> --json`/`--agent` `ledger` is a non-absolute path ending in `ledger.jsonl`; human header contains no absolute path.
  - Execution state: pending

- [ ] E-03 In `run_cli._run_verify_ledger`, use the same normalized relative path for the human `Ledger: ...` line and the human `FAIL: Ledger verification failed for ...` line. Machine payloads are unchanged (they carry no path today).
  - Depends on: none
  - Expected outcome: `aw runs verify-ledger <id>` human stdout carries `Ledger: <relative path ending in ledger.jsonl>` and no occurrence of the absolute repo root.
  - Execution state: pending

### Task group 3: Tests, conformance registry, changelog

- [ ] E-04 Add `tests/test_runs_machine_output_paths.py` (behavioral, subprocess-driven via `python -m agent_workflows` against a `tmp_path` repo seeded with `conformance_matrix.seed_ledger_fixture`): (a) for `decisions` and `questions` x `--json`/`--agent`, stdout parses as one JSON dict with `empty is True`, the fixture marker in `content`, `exit_code == returncode == 1`, and a non-absolute `path`; (b) after overwriting the decisions projection with `set_records.render_decisions([...one autonomous_decision record with decision_id "D-01"...])`, `--json` yields `empty is False`, `entry_ids == ["D-01"]`, returncode 0; (c) missing projection (unseeded run id) under `--json` yields `ok is False`, `exit_code == 2`, returncode 2, non-absolute `path`; (d) human output of `decisions` equals the projection file text; (e) `runs evidence --json`/`--agent` `ledger` is not absolute and endswith `ledger.jsonl`; (f) `runs evidence` and `runs verify-ledger` human stdout does not contain `str(tmp_path.resolve())` and verify-ledger contains a `Ledger: ` line ending in `ledger.jsonl`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the new module passes against the fixed code; cases (a), (c), (e), (f) fail against today's code (raw markdown / absolute paths).
  - Execution state: pending

- [ ] E-05 Update the gap pins: in `tests/test_live_conformance_sweep.py::test_live_ledger_read_leaves_non_vacuous`, replace the `PROJECTION_MARKERS` substring-only branch for agent/json with JSON parsing (assert dict, `empty is True`, marker in `content`), keeping the human marker assertion; in `tests/conformance_matrix.py` `EXEMPTION_REGISTRY`, change the `runs decisions` and `runs questions` entries from `not_runnable` "(gap hbok5d)" to `sanctioned_raw` with citation `docs/cli-output-contract.md Section 3.1` and the same bare-JSON `_emit_machine` reason text their `runs evidence`/`runs show` siblings carry, and fix the per-kind count comments (`# sanctioned_raw (N):`, `# not_runnable (N):`) to the new counts.
  - Depends on: E-01
  - Expected outcome: `tests/test_live_conformance_sweep.py`, `tests/test_agent_surface_conformance.py` and `tests/test_command_surface_declarations.py` pass; no registry entry still cites hbok5d.
  - Execution state: pending

- [ ] E-06 Add a `- Fixed:` line to the pending section of `CHANGELOG.md` (user-facing prose, no em/en dashes): `aw runs decisions` and `aw runs questions` now emit a JSON object under `--agent` and `--json`, and `aw runs evidence` and `aw runs verify-ledger` report the ledger as a repository-relative path.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: one new CHANGELOG line, dash-free.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_cli._emit_machine` is the single machine emitter for `aw run`/`aw runs`: bare dicts, compact JSON for `--agent`, pretty JSON for `--json`, payload scrubbed by `_redact_output`. The `_emit_error` docstring ("DELIBERATELY NOT AN `aw.agent/v1` RECORD (F-16)") records that these leaves are bare-dict by design; converting to `aw.agent/v1` is out of scope.
- `agent_schema.normalize_repo_path(path, repo_root)` "Never returns absolute paths, home directories, usernames, or hostnames"; `run_cli._run_init` already uses it for its `ledger` key (`rel_ledger = agent_schema.normalize_repo_path(ledger_path, repo)`), and `tests/test_run_init.py` asserts `not Path(agent_rec["ledger"]).is_absolute()`. That is the precedent for E-02/E-03.
- `tests/conformance_matrix.py` `EXEMPTION_REGISTRY` is "A CEILING, NOT A CONVENIENCE"; the `runs decisions`/`runs questions` entries currently read "prints raw markdown under all modes, including --agent and --json (gap hbok5d)", so they must be re-justified when the gap closes.
- `tests/test_live_conformance_sweep.py` `PROJECTION_MARKERS` only substring-checks agent/json stdout for the projection leaves, which a JSON `content` field still satisfies, but the JSON-parse assertion is the point of F-07.
- `tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted` requires a missing-projection run to exit 2 and redact a `ghp_` token in both human and `--agent` mode; `_emit_error` routes through `_redact_output`, so E-01(b) keeps it green.
- `set_records.render_decisions` / `render_open_questions` produce the projections; ids are on `## <id>` headings, with optional ` (SUPERSEDED)` and ` [consultation_preferred]` suffixes on decisions.
- Behavioral tests only (AGENTS.md, no code-pinning); run the suite bare with `python3 -m pytest`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Projection leaves ignore machine mode entirely. | `run_cli._run_decisions` / `_run_questions`: `_print_human(text, end=...)` with no `_machine(args)` branch. |
| F-2 | `runs evidence` machine payload leaks the absolute path. | `run_cli._run_evidence`: `"ledger": str(ledger_file)`; human `f"Evidence for {ledger_file} ..."`. |
| F-3 | `runs verify-ledger` human output leaks the absolute path. | `run_cli._run_verify_ledger`: `_print_human(f"Ledger: {ledger_file}")` and `f"FAIL: Ledger verification failed for {ledger_file}"`. |
| F-4 | Tests currently pin the gap rather than the fix. | `tests/conformance_matrix.py` exemption reason "(gap hbok5d)"; `tests/test_live_conformance_sweep.py` `PROJECTION_MARKERS` branch. |

## Proposed changes (ordered, validatable)

1. E-01: projection helper with machine payload and relative path.
2. E-02: relative `ledger` in `runs evidence`.
3. E-03: relative path in `runs verify-ledger` human lines.
4. E-04: new behavioral test module.
5. E-05: re-justify exemptions and strengthen the live sweep.
6. E-06: CHANGELOG.

## Deferred / out of scope (with reason)

- Converting `aw runs` machine payloads to `aw.agent/v1` records: a cross-leaf contract change explicitly deferred in the `run_cli._emit_error` docstring (F-16); this plan matches the sibling bare-dict shape instead.
- The same absolute-path pattern in `runs show` human `Ledger:` line (`run_cli._run_show`) and `_emit_not_a_ledger`'s `"path": str(exc.path)`: same defect class, but not named by hbok5d; changing them here would broaden scope. Recommend a follow-up backlog item.
- Reading decisions/questions from `ledger.jsonl` instead of the markdown projections: the exemption notes the projection source, but hbok5d asks only for parseable machine output.

## Scope check

- Over-scope: none; the missing-projection relative path in E-01 is part of making the same leaf's machine output clean.
- Under-scope: none; the five Scope-Paths cover the code, the new tests, the two test files that pin the gap, and the changelog.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runs_machine_output_paths.py tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_command_surface_declarations.py tests/test_run_cli_human_redaction.py tests/test_run_cli_error_payload_keys.py tests/test_run_init.py -q` passes.
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no failure.

## Spec / documentation sync

- No spec change: `docs/cli-output-contract.md` Section 3.1 already covers bare-JSON `aw runs` payloads; this plan brings the two projection leaves into it. `.aw/system/workflows/exec-set/exec-set.md` only names the commands and needs no edit. CHANGELOG via E-06.

## Open questions

### OQ-01: Should the machine payload carry parsed fields per entry rather than heading ids plus raw content?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved as ids plus `content`. The projections are rendered markdown (`set_records.render_decisions`), and re-parsing their bullet lines would duplicate the renderer's format as an implicit schema; `entry_ids` plus the verbatim text is parseable, lossless, and stable. Full per-record structure belongs to the deferred ledger-sourced reader.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted stdout of `aw runs decisions <fixture-run-id> --dir <scratch> --json` and `... --agent` (produced by `run_cli._run_decisions` after E-01) each piped through `python3 -c 'import json,sys; print(json.loads(sys.stdin.read()))'` without error, plus the exit code (1 for the empty fixture); and the human-mode stdout shown identical to the projection file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw runs evidence <fixture-run-id> --dir <scratch> --json` stdout (from `run_cli._run_evidence`) whose `ledger` value is relative and ends in `ledger.jsonl`, and human header without the scratch absolute path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted human stdout of `aw runs verify-ledger <fixture-run-id> --dir <scratch>` (from `run_cli._run_verify_ledger`) showing a relative `Ledger:` line and no absolute scratch path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted pytest summary line for `tests/test_runs_machine_output_paths.py` showing all passed, and a note (or pasted run against a stash-free scratch revert) that cases (a)/(c)/(e)/(f) fail without E-01..E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted pytest summary for `tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_command_surface_declarations.py tests/test_run_cli_human_redaction.py`, plus `grep -n hbok5d tests/conformance_matrix.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing the one new line, and a grep showing it contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit via `aw commit lpvcln -- <Scope-Paths>`; never push. Run the Required tests and paste actual runner output into the V-* evidence, then move the plan to `executed/` through the IPD lifecycle once `aw ipd lint --phase pre-transition` conforms.
