# IPD: Add gemini-quota CLI module and behavioral tests to agent_workflows

- Date: 2026-11-17
- Kind: child
- Concern: Bring the Antigravity `gemini-quota` CLI script into the `agent_workflows` Python package so `aw install more` can expose it without requiring external binaries or third-party dependencies.
- Scope: Add `agent_workflows/gemini_quota.py` (stdlib-only module implementing the `gemini-quota` status bar, dashboard, burn-rate forecast, JSON export, watch loop, and cache/API quota refresh) and `tests/test_gemini_quota.py` covering its CLI flags and rendering/forecast behavior. EXCLUDES modifying `[project.scripts]` in `pyproject.toml`, installing user PATH launchers (`58isyp`), and changing `agent_workflows/agy_runipd.py` statuslines.
- Scope-Paths: agent_workflows/gemini_quota.py, tests/test_gemini_quota.py, .aw/records/plans/pending/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Package the Antigravity gemini-quota status/forecast CLI under agent_workflows/gemini_quota.py with unit and CLI tests
- Work-Kind: feature
- Priority: medium
- Set: installmore
- Order: 1
- Highest E allocated: 04
- Author: antigravity
- Id: z403j4

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-18 review progress (antigravity/gemini-4-hydrogen-high): Round 1 completed revisions for PR-002..PR-006; escalated PR-001 as blocking OQ-02 awaiting maintainer answer in .aw/records/reviews/20261117-installmore-01-z403j4-add-gemini-quota-cli-module-and-behavioral-tests-to-agent-wo.review.md
- 2026-11-18 to-review (aw set): status set to to-review
- 2026-11-18 draft (antigravity): created and authored as self-contained Order 01 of Set `installmore`.

## Goal

Package `gemini-quota` inside `agent_workflows/gemini_quota.py` using Python stdlib modules only, so `agent-workflows` ships the tool in its wheel/sdist and `58isyp` can install a launcher for it via `aw install more`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Module implementation and behavioral verification

- [ ] E-01 Create `agent_workflows/gemini_quota.py` (with `from __future__ import annotations` and Python 3.9+ stdlib only, using `datetime.timezone.utc` rather than `datetime.UTC` and no runtime `X | Y` unions) implementing the quota payload reader/refresher (`DEFAULT_CACHE_PATHS = (Path("/tmp/antigravity_quota.json"), Path.home() / ".gemini" / "antigravity-cli" / "last_quota.json")`, `HISTORY_PATH = Path.home() / ".gemini" / "antigravity-cli" / "quota_history.json"`, `load_quota_payload`, `obtain_quota_payload`, `refresh_quota`, `load_history_samples`, `record_history_sample`), the ANSI/256-color renderers (`supports_color` honoring `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, and `isatty()`, `format_bar`, `format_duration`, `compute_reset_in_seconds`, `format_single_status_bar`, `render_dashboard`), and the 5-hour OLS burn-rate analyzer (`analyze_bucket`, `render_watch_forecast_panel`, `build_json_forecast`). Ensure trust-boundary safety: sanitize control/ANSI characters in payload strings, write `HISTORY_PATH` atomically (temp file + `os.replace`) with bounded pruning, enforce `https://` (or loopback `http://127.0.0.1`/`localhost`) and finite timeouts on any `urllib` request, pass `shell=False` with timeout on any `subprocess.run`, handle corrupt JSON or absent `/tmp` paths on Windows gracefully, never emit tokens/credentials in output or history, and keep all paths free of user-specific or machine-local strings.
  - Depends on: none
  - Expected outcome: `agent_workflows/gemini_quota.py` imports cleanly on Python 3.9+ with zero third-party dependencies and passes `ruff`, `mypy`, and `aw check-local-leaks`.
  - Execution state: pending

- [ ] E-02 Implement `build_parser()` and `main(argv: list[str] | None = None) -> int` in `agent_workflows/gemini_quota.py` supporting `--bar`/`-b`/`--status-bar`/`--compact`, `--gemini`/`-g`/`--gemini-only`, `--3p`/`-3`/`--third-party`, `--json`/`-j`, `--watch`/`-w` (optional float seconds, default `2.0`), `--max-staleness`/`-m` (float seconds, default `60.0`), `--no-color`/`--plain`, `--color`, `--plot`/`-p`/`--charts`, `--context`, and `--file`/`-f`, plus runnable `if __name__ == "__main__": sys.exit(main())`. When `--file` is supplied, read only that file without falling back to `DEFAULT_CACHE_PATHS` or `refresh_quota`, and do not write to live `HISTORY_PATH`. Handle `BrokenPipeError` cleanly.
  - Depends on: E-01
  - Expected outcome: `python3 -m agent_workflows.gemini_quota --help` renders all flags, missing/unreadable `--file` or missing quota data prints an actionable error on stderr and returns non-zero without side effects, and `--file`, `--bar`, `--json`, `--watch`, and dashboard modes render from fixture JSON.
  - Execution state: pending

- [ ] E-03 Add behavioral tests in `tests/test_gemini_quota.py` (marked with `pytestmark = pytest.mark.core` at module scope and using fast in-process `gemini_quota.main(argv)` and helper calls) against synthetic quota fixture files (`--file`): single-line `--bar` output, `--json` output with `burn_forecast`, `--gemini` vs `--3p` bucket filtering, `--no-color` plain output (and `NO_COLOR`/`FORCE_COLOR`), `--plot` Braille forecast panel, bounded `--watch` loop termination (e.g., via `KeyboardInterrupt` or sleep mock after 1-2 iterations), non-zero exit when `--file` is missing/corrupt or quota data is unavailable (`obtain_quota_payload` returning `None` with `refresh_quota` mocked/disabled and zero network access), and history sample recording/pruning under a temporary home path.
  - Depends on: E-02
  - Expected outcome: All tests in `tests/test_gemini_quota.py` run under the `core` tier, pass deterministically without network access or live Antigravity credentials, complete well below the 2s slow threshold, and contain no source-code inspection assertions.
  - Execution state: pending

- [ ] E-04 Run `aw check-local-leaks`, `ruff check agent_workflows/gemini_quota.py tests/test_gemini_quota.py`, `ruff format --check agent_workflows/gemini_quota.py tests/test_gemini_quota.py`, `python3 -m mypy agent_workflows`, `pre-commit run --files agent_workflows/gemini_quota.py tests/test_gemini_quota.py` (after staging), `python3 -m pytest -v tests/test_gemini_quota.py`, and bare `python3 -m pytest` confirming zero leaks, zero mypy regressions, and passing tests within budget.
  - Depends on: E-03
  - Expected outcome: `tests/test_gemini_quota.py` passes cleanly, `mypy` and `ruff` pass, leak check passes, and core pytest suite remains green within budget.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Runtime dependencies in `pyproject.toml` are strictly minimized (`filelock>=3` only), and `requires-python = ">=3.9"` across Linux, macOS, and Windows: `agent_workflows/gemini_quota.py` uses `from __future__ import annotations` and Python 3.9+ stdlib modules only (`argparse`, `datetime`, `json`, `os`, `re`, `shutil`, `subprocess`, `sys`, `time`, `urllib.*`, `pathlib`) so `dependencies` in `pyproject.toml` stays unchanged.
- `pyproject.toml` packages `agent_workflows` into wheels and sdists automatically (`packages = ["agent_workflows"]`).
- Bare `python3 -m pytest` runs only `@pytest.mark.core` tests (`conftest.py::pytest_collection_modifyitems`) within a 30s budget, and tests taking over 2s must appear in `tests/slow_allowlist.txt`; `tests/test_gemini_quota.py` uses `pytestmark = pytest.mark.core` and fast in-process calls.
- All tracked files must pass `aw check-local-leaks` (no local usernames or machine-local home paths; use `Path.home()` or `~/.gemini/...`).
- Tests must exercise observable behavior (`main`, temp JSON fixtures) with no `inspect`/`ast` source-pinning checks (`GUIDING_PRINCIPLES.md` P16).

## Findings

| Finding | Evidence | Impact on this plan |
| --- | --- | --- |
| `gemini-quota` uses stdlib only | Existing CLI uses stdlib modules (`argparse`, `datetime`, `json`, `urllib.*`, `pathlib`) and needs no new runtime dependency | Keeps `pyproject.toml` `dependencies = ["filelock>=3"]` unchanged |
| Wheel packaging covers all `agent_workflows/*.py` modules | `pyproject.toml` declares `[tool.hatch.build.targets.wheel] packages = ["agent_workflows"]` | Putting `gemini_quota.py` under `agent_workflows/` ships it automatically in builds and editable installs |
| Executable entrypoint stays separate from default `[project.scripts]` | Maintainer requested opt-in installation via `aw install more` after asking | Do NOT add `gemini-quota` to `[project.scripts]`; expose `python3 -m agent_workflows.gemini_quota` for `58isyp` to wrap on opt-in |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    A["cli main(argv)"] --> B["obtain_quota_payload(file, max_staleness)"]
    B -->|Missing or unreadable| C["Write error to stderr; exit 1"]
    B -->|Payload loaded via cache or refresh| D["record_history_sample then load_history_samples"]
    B -->|Payload loaded via --file| D2["load_history_samples (no live history write)"]
    D --> E{"Output mode"}
    D2 --> E
    E -->|--json| F["Emit JSON with burn_forecast"]
    E -->|--bar| G["Print format_single_status_bar"]
    E -->|Default / --plot| H["Print render_dashboard (+ forecast charts)"]
    E -->|--watch| I["Sleep interval and repeat until interrupted"]
    I --> B
```

1. Add `agent_workflows/gemini_quota.py` implementing the quota dashboard, cache/history handling, live refresh helpers, burn-rate forecast, and CLI entrypoint `main(argv=None)`.
2. Add `tests/test_gemini_quota.py` (with `pytestmark = pytest.mark.core`) exercising all CLI flags (including bounded `--watch`) and forecast/rendering paths with local temp fixtures (zero network calls).
3. Verify with `pytest`, `mypy`, `ruff`, `pre-commit`, and `aw check-local-leaks`.

## Deferred / out of scope (with reason)

- Registering `gemini-quota` in `aw install more` and adding the `aw install` discovery tip: owned by sibling Order 02 (`58isyp`).
  - Carrier: 58isyp
- Installing launchers into user bin directories by default in `pyproject.toml`: omitted intentionally because installation must be opt-in after asking (`aw install more`).
  - Carrier-Declined: intentional exclusion by design (default pyproject.toml script entry omitted so installation stays opt-in via aw install more in 58isyp)

## Scope check

- Over-scope: none.
- Under-scope: `PR-001` (`OQ-02`, blocking) remains open pending maintainer input on the Antigravity quota JSON schema, `refresh_quota` live-refresh protocol, `quota_history.json`/`--json` keys, and `--context` semantics before autonomous execution can proceed without inventing architecture.

## Required tests / validation

- `python3 -m pytest -v tests/test_gemini_quota.py`
- `python3 -m mypy agent_workflows`
- `ruff check agent_workflows/gemini_quota.py tests/test_gemini_quota.py` and `ruff format --check agent_workflows/gemini_quota.py tests/test_gemini_quota.py`
- `aw check-local-leaks`
- `python3 -m pytest` (core suite)

## Spec / documentation sync

- N/A for `z403j4`: companion CLI behavior and user installation docs live in `58isyp` (`README.md` / CLI help).

## Open questions

### OQ-01: Should `agent_workflows/gemini_quota.py` be copied verbatim from the maintainer's local script before execution or authored directly from the behavioral contract above?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Self-contained default for autonomous lanes: implement `agent_workflows/gemini_quota.py` from this plan's contract with no out-of-lane reads. If the maintainer wants byte-identical preservation of their local `~/.gemini/antigravity-cli/bin/gemini-quota` script, they can copy it to `agent_workflows/gemini_quota.py` on `main` before running `z403j4` (after adjusting `main()` to accept `argv: list[str] | None = None`).

### OQ-02: PR-001 leaves the Antigravity quota payload schema, `refresh_quota` protocol, history/`--json` schema, and `--context` semantics unspecified; how should autonomous execution obtain them?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: Pending maintainer decision on whether to supply the Antigravity quota payload schema, `refresh_quota` mechanism, `quota_history.json`/`--json` schema, and `--context` behavior (or copy the maintainer's local script into `agent_workflows/gemini_quota.py` on `main` before execution) vs. defining a synthetic-compatible greenfield schema with explicit unsupported/cache-only refresh. Recommendation strength: strong (provide the exact schema/refresh spec or pre-seed the module on `main` so `gemini-quota` works against live Antigravity state rather than an invented schema).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short agent_workflows/gemini_quota.py` showing the new module, `aw check-local-leaks` clean output, and `python3 -c "from agent_workflows import gemini_quota; print(callable(gemini_quota.format_single_status_bar), callable(gemini_quota.render_dashboard), callable(gemini_quota.analyze_bucket))"` printing `True True True`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m agent_workflows.gemini_quota --help` output showing `-b`/`--bar`, `-g`/`--gemini`, `-3`/`--3p`, `-j`/`--json`, `-w`/`--watch`, `-m`/`--max-staleness`, `--no-color`, `--color`, `-p`/`--plot`, `--context`, and `-f`/`--file`, plus `python3 -m agent_workflows.gemini_quota --file /nonexistent/quota.json --max-staleness -1` exiting non-zero with an error message on stderr and zero writes to `HISTORY_PATH`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -v tests/test_gemini_quota.py` showing every test node PASSED and 0 failed (covering `--bar`, `--json` `burn_forecast`, `--gemini`/`--3p`, `--no-color`, `--plot`, bounded `--watch`, missing/corrupt `--file`, and temp-home history pruning), plus `rg -n "^(import|from) (inspect|ast)\b" tests/test_gemini_quota.py` returning exit 1.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m mypy agent_workflows`, `ruff check agent_workflows/gemini_quota.py tests/test_gemini_quota.py`, `ruff format --check agent_workflows/gemini_quota.py tests/test_gemini_quota.py`, `pre-commit run --files agent_workflows/gemini_quota.py tests/test_gemini_quota.py` (after staging) showing all hooks passed, `aw check-local-leaks` clean output, and the summary line of bare `python3 -m pytest` passing within budget with `tests/test_gemini_quota.py` executed in the core tier.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:
- **Open questions**: `OQ-01` is resolved (`- Blocking: no`); `OQ-02` (`- Blocking: yes`, `- Finding: PR-001`) must be answered and resolved before approval or execution.
- **Scope fence**: Declared work paths are listed in `- Scope-Paths:`. An out-of-scope edit must be justified at finalize with `--scope-reason`, and any declared path left unmodified must be acknowledged with `--scope-ack`.
- **Safety stop**: Stop and report only on a genuinely unsafe condition (such as an unresolvable concurrent-edit conflict).
- **Evidence honesty**: MUST paste the actual runner output for every check and test run; never claim passing results without running them after the final edit.
- **Commit and push**: Commit only files you changed for this plan, limited to named paths, via `aw commit z403j4 -- <paths>`. Never use `git add -A`, `git commit -a`, or `--no-verify`, and never push without an explicit human directive.
- **Lifecycle transition**: When `aw oc run` or `aw agy run` executes this plan, the runner performs the terminal finalize (`aw ipd finalize z403j4`); a hand executor runs `aw ipd finalize z403j4` itself (never a hand `git mv` to `executed/`).
