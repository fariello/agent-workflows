# IPD: runs decisions/questions emit structured machine output; runs evidence/verify-ledger stop leaking absolute ledger paths

- Date: 2026-10-16
- Kind: child
- Concern: `aw runs decisions` and `aw runs questions` print raw markdown under `--agent`/`--json` (stdout is not parseable by `json.loads`), and `aw runs evidence` (machine `ledger` key and human header) plus `aw runs verify-ledger` (human `Ledger:` and `FAIL:` lines) print the absolute ledger path.
- Scope: Give the two projection leaves a bare-JSON machine payload (same `_emit_machine` family as their `aw runs` siblings) while keeping human output and exit codes unchanged; route every ledger path these two ledger leaves print through `agent_schema.normalize_repo_path`, and the same-defect sibling sites in this file (`runs show` human `Ledger:` line and `_emit_not_a_ledger`'s machine `path`, review PR-001); add behavioral tests; update the live conformance sweep and exemption registry that currently pin the raw-markdown gap; add a CHANGELOG line.
- Scope-Paths: agent_workflows/run_cli.py, tests/test_runs_machine_output_paths.py, tests/test_live_conformance_sweep.py, tests/conformance_matrix.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: hbok5d
- Set: runledger
- Order: 2
- Highest E allocated: 07
- Author: opencode
- Id: lpvcln
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): plan-review: revisions applied (PR-001..PR-005)

- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog hbok5d (F-07, F-08 measured by g5s94t).

## Goal

Make every `--agent`/`--json` stdout of `aw runs decisions` and `aw runs questions` a single parseable JSON object, and make `aw runs evidence`, `aw runs verify-ledger` and `aw runs show` (plus the shared not-a-ledger refusal) print the ledger as a repo-relative path in every mode, so the machine surface is parseable and sanitizer-clean (D92 / `normalize_repo_path` contract), without changing exit codes or human projection text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Structured machine output for the projection leaves

- [ ] E-01 In `agent_workflows/run_cli.py`, factor `_run_decisions` and `_run_questions` through one helper (for example `_emit_projection(args, kind, filename, empty_marker)`). Human mode for a PRESENT projection stays byte-identical (prints the markdown); a MISSING projection still prints the `no ... projection found for this run (<path>)` line, but with the repo-relative path instead of the absolute one (review PR-001), so the human line and the machine `path` agree. When `_machine(args)` is true: (a) projection present -> `_emit_machine(args, {"ok": True, "projection": "decisions"|"questions", "run_id": <target>, "path": <repo-relative path>, "empty": <bool>, "entry_ids": [<ids from "## " heading lines, with any " (SUPERSEDED)"/" [consultation_preferred]" suffix stripped>], "content": <markdown text>, "exit_code": <0|1>})`; (b) projection missing -> `_emit_error(args, "no <kind> projection found for this run (<repo-relative path>)", 2, extra={"projection": <kind>, "path": <repo-relative path>})`. The path is `agent_schema.normalize_repo_path(path, repo_root)` where `repo_root` is the same `resolve_verb_repo_root(args.dir)` `_projection_dir` uses. Exit codes stay 0 found / 1 empty / 2 missing.
  - Depends on: E-04
  - Expected outcome: `aw runs decisions <id> --json` and `--agent` stdout parse with `json.loads` (agent: one compact line) into a dict whose `projection`, `empty`, `content` and `exit_code` agree with the projection file and the process exit code; human stdout for a present projection unchanged; the missing-projection line (human and machine) carries no absolute path; `tests/test_run_cli_human_redaction.py::test_projection_leaves_path_secret_redacted` still passes (the token survives `normalize_repo_path` and is scrubbed by `_redact_output`).
  - Execution state: pending

### Task group 2: Repo-relative ledger paths

- [ ] E-02 In `run_cli._run_evidence`, compute `rel_ledger = agent_schema.normalize_repo_path(ledger_file, repo_dir)` once and use it for the machine payload `"ledger"` key (replacing `str(ledger_file)`) and the human header `Evidence for <ledger> (N items):`.
  - Depends on: E-04
  - Expected outcome: `aw runs evidence <id> --json`/`--agent` `ledger` is a non-absolute path ending in `ledger.jsonl`; human header contains no absolute path.
  - Execution state: pending

- [ ] E-03 In `run_cli._run_verify_ledger`, use the same normalized relative path for the human `Ledger: ...` line and the human `FAIL: Ledger verification failed for ...` line. Machine payloads are unchanged (they carry no path today).
  - Depends on: E-04
  - Expected outcome: `aw runs verify-ledger <id>` human stdout carries `Ledger: <relative path ending in ledger.jsonl>` and no occurrence of the absolute repo root.
  - Execution state: pending

- [ ] E-07 In `run_cli._run_show`, print the human `Ledger: ... (N records)` line with `agent_schema.normalize_repo_path(ledger_file, repo_dir)`; in `run_cli._emit_not_a_ledger`, emit `"path": agent_schema.normalize_repo_path(exc.path, <repo root>)` instead of `str(exc.path)` (resolve the root with `resolve_verb_repo_root(getattr(args, "dir", None))`, the same resolver every caller uses). Same defect class as F-2/F-3 in the same file, folded in at review (PR-001) instead of being left uncarried.
  - Depends on: E-04
  - Expected outcome: `aw runs show <id>` human stdout carries no absolute repo root; a not-a-ledger refusal's machine `path` is non-absolute; every other key of the not-a-ledger payload and every exit code unchanged.
  - Execution state: pending

### Task group 3: Tests, conformance registry, changelog

- [ ] E-04 Add `tests/test_runs_machine_output_paths.py` (behavioral, subprocess-driven via `python -m agent_workflows` against a `tmp_path` repo seeded with `conformance_matrix.seed_ledger_fixture`): (a) for `decisions` and `questions` x `--json`/`--agent`, stdout parses as one JSON dict with `empty is True`, the fixture marker in `content`, `exit_code == returncode == 1`, and a non-absolute `path`; (b) after overwriting the decisions projection with `set_records.render_decisions([...one autonomous_decision record with decision_id "D-01"...])`, `--json` yields `empty is False`, `entry_ids == ["D-01"]`, returncode 0; (c) missing projection (unseeded run id) under `--json` yields `ok is False`, `exit_code == 2`, returncode 2, non-absolute `path`; (d) human output of `decisions` equals the projection file text; (e) `runs evidence --json`/`--agent` `ledger` is not absolute and endswith `ledger.jsonl`; (f) `runs evidence` and `runs verify-ledger` human stdout does not contain `str(tmp_path.resolve())` and verify-ledger contains a `Ledger: ` line ending in `ledger.jsonl`.
  Also (g): `runs show` human stdout does not contain `str(tmp_path.resolve())` and its `Ledger: ` line ends in `ledger.jsonl (N records)`; (h) `runs show <path-to-a-non-ledger-jsonl-file-inside-tmp_path> --dir <tmp_path> --json` yields `not_a_ledger is True` and a non-absolute `path`. AUTHOR THIS MODULE FIRST, before E-01..E-03/E-07 touch `run_cli.py`, and run it once to capture the RED baseline (review PR-003).
  - Depends on: none
  - Expected outcome: before E-01..E-03/E-07, cases (a), (c), (e), (f), (g), (h) fail and (b)'s `--json` parse fails (raw markdown / absolute paths); after them, the whole module passes.
  - Execution state: pending

- [ ] E-05 Update the gap pins: in `tests/test_live_conformance_sweep.py::test_live_ledger_read_leaves_non_vacuous`, replace the `PROJECTION_MARKERS` substring-only branch for agent/json with JSON parsing (assert dict, `empty is True`, marker in `content`), keeping the human marker assertion; in `tests/conformance_matrix.py` `EXEMPTION_REGISTRY`, change the `runs decisions` and `runs questions` entries from `not_runnable` "(gap hbok5d)" to `sanctioned_raw` with citation `docs/cli-output-contract.md Section 3.1` and the same bare-JSON `_emit_machine` reason text their `runs evidence`/`runs show` siblings carry, and fix the per-kind count comments (`# sanctioned_raw (N):`, `# not_runnable (N):`) to the new counts.
  - Depends on: E-01
  - Expected outcome: `tests/test_live_conformance_sweep.py`, `tests/test_agent_surface_conformance.py` and `tests/test_command_surface_declarations.py` pass; no registry entry still cites hbok5d.
  - Execution state: pending

- [ ] E-06 Add a `- Fixed:` line to the pending section of `CHANGELOG.md` (user-facing prose, no em/en dashes): `aw runs decisions` and `aw runs questions` now emit a JSON object under `--agent` and `--json`, and `aw runs evidence`, `aw runs verify-ledger` and `aw runs show` report the ledger as a repository-relative path.
  - Depends on: E-01, E-02, E-03, E-07
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
| F-5 | Same defect class, same file, found at review: `runs show` human line and the not-a-ledger refusal's machine `path` leak the absolute path. | `run_cli._run_show` human `Ledger: {ledger_file} (...)` (measured at review: `Ledger: <ROOT>/.aw/records/runs/<id>/ledger.jsonl (2 records)`); `run_cli._emit_not_a_ledger` `"path": str(exc.path)`. |
| F-4 | Tests currently pin the gap rather than the fix. | `tests/conformance_matrix.py` exemption reason "(gap hbok5d)"; `tests/test_live_conformance_sweep.py` `PROJECTION_MARKERS` branch. |

## Proposed changes (ordered, validatable)

1. E-04: new behavioral test module, authored first and run RED.
2. E-01: projection helper with machine payload and relative path.
3. E-02: relative `ledger` in `runs evidence`.
4. E-03: relative path in `runs verify-ledger` human lines.
5. E-07: relative path in `runs show` human line and the not-a-ledger machine `path`.
6. E-05: re-justify exemptions and strengthen the live sweep.
7. E-06: CHANGELOG.

## Deferred / out of scope (with reason)

- Converting `aw runs` machine payloads to `aw.agent/v1` records: a cross-leaf contract change explicitly deferred in the `run_cli._emit_error` docstring (F-16); this plan matches the sibling bare-dict shape instead.
  - Carrier-Declined: deliberate design of the `aw runs` family (bare dicts, `docs/cli-output-contract.md` Section 3.1, `tests/test_run_cli_error_payload_keys.py`), not a defect.
- Reading decisions/questions from `ledger.jsonl` instead of the markdown projections: the exemption notes the projection source, but hbok5d asks only for parseable machine output.
  - Carrier-Declined: an alternative data source, not a defect; spec `6kwd2e` R4a.1 already owns how the projection gets written.

## Scope check

- Over-scope: none; the missing-projection relative path in E-01 and E-07's two sibling sites are the same defect in the same file (review PR-001), folded in rather than left with no carrier.
- Under-scope: none; the five Scope-Paths cover the code, the new tests, the two test files that pin the gap, and the changelog.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runs_machine_output_paths.py tests/test_live_conformance_sweep.py tests/test_agent_surface_conformance.py tests/test_command_surface_declarations.py tests/test_run_cli_human_redaction.py tests/test_run_cli_error_payload_keys.py tests/test_run_init.py tests/test_run_recovery_cli.py -q` passes (the last module pins the not-a-ledger verdict E-07 touches). Measured at review before any change: the first seven minus the new module, `212 passed`.
- Routine gate `python3 -m pytest` passes.
- `aw sanitize --agent` reports no failure.

## Spec / documentation sync

- No spec change: `docs/cli-output-contract.md` Section 3.1 already covers bare-JSON `aw runs` payloads; this plan brings the two projection leaves into it. `.aw/system/workflows/exec-set/exec-set.md` only names the commands and needs no edit. CHANGELOG via E-06.

## Open questions

### OQ-01: Should the machine payload carry parsed fields per entry rather than heading ids plus raw content?

- Blocking: no
- Status: resolved
- Owner: plan author
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
  - Required evidence: the pasted RED run of `python3 -m pytest -o addopts="" -q tests/test_runs_machine_output_paths.py` taken BEFORE E-01..E-03/E-07 changed `run_cli.py` (showing cases (a), (c), (e), (f), (g), (h) failing), then the pasted GREEN run of the same command after them with zero failures. A note in place of the RED output is not acceptable.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff tests/conformance_matrix.py tests/test_live_conformance_sweep.py`; the pasted output of the full `## Required tests / validation` pytest command with zero failures; `grep -n hbok5d tests/conformance_matrix.py` returning nothing; the summary line of the routine gate `python3 -m pytest`; and the `aw sanitize --agent` result line.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted human stdout of `aw runs show <fixture-run-id> --dir <scratch>` (from `run_cli._run_show`) with a relative `Ledger:` line, and pasted `--json` stdout of `aw runs show <non-ledger-file> --dir <scratch>` (from `run_cli._emit_not_a_ledger`) with `not_a_ledger: true` and a non-absolute `path`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing the one new line, and a grep showing it contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution. All open questions are resolved.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit lpvcln -- <paths>` (never `git add -A`), never push. Every test claim MUST paste the actual runner output; never claim a result you did not run.

SCOPE FENCE. The declared scope is the five Scope-Paths. It is a declaration, not a stop rule: an out-of-scope edit that proves necessary is made and then justified at finalize (`--scope-reason` per path, `--scope-ack` per declared-but-unmodified path).

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all seven `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
