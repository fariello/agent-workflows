# IPD: Route aw config exclude subcommand-less refusal through the shared family-help refusal

- Date: 2026-10-12
- Kind: child
- Concern: `aw config exclude --agent` (no subcommand) exits 2 and writes the HUMAN status line `FAIL     Usage: aw config exclude {add|list|rm} ...` to STDOUT instead of an `aw.agent/v1` record (backlog `o8cz48`, `Work-Kind: bug`, `Blocks-Release: next`). Re-measuring the whole `config` family at authoring HEAD `5f816e9aa`, as the item requires, also shows the three `config exclude` LEAVES (`add`, `list`, `rm`) printing human text under `--agent` and `--json` although `command_surface` declares each `agent_record_kind="result"`, while `config show`/`get`/`is` now conform (the `dtq6jr` ImportError is gone and no `dtq6jr` registry entry remains). All four broken surfaces live in ONE handler, `cli._run_config_exclude`, so the family is decided in one pass here.
- Scope: IN: (1) route the subcommand-less fall-through of `cli._run_config_exclude` through `cli._show_family_help(parser, "config exclude", "aw config exclude list", term, context)`, threading `parser` and `context` from the `config` dispatch; (2) give the `add`, `list` and `rm` leaves an `--agent` arm emitting one validated `result` record through the existing `cli._emit_config_agent_record` helper, and a `--json` arm emitting a bare sorted JSON dict, mirroring sibling `config` verbs (`_run_config_remove`, `_run_config_is`); (3) delete the stale `sanctioned_raw` exemption for `config exclude list` in `tests/conformance_matrix.EXEMPTION_REGISTRY` so the existing read-surface sweep gates it, and delete any `FAMILY_ROOT_EXEMPTION_REGISTRY` entry for `config exclude` if plan `0qdl9e` has landed one; (4) behavioral subprocess tests in `tests/test_config_agent_surface.py`; (5) one CHANGELOG line. OUT: the `add`/`rm` `arg_fixture_needed` entries in `MUTATION_EXEMPTION_REGISTRY` (the mutation sweep's fixture design is not this item's concern; the new tests cover both leaves with an isolated `XDG_CONFIG_HOME`); `aw runs` (owned by `l5dq92`); the family-root sweep itself (owned by `0qdl9e`); human-mode wording of the leaves; `_show_family_help` itself.
- Scope-Paths: agent_workflows/cli.py, tests/test_config_agent_surface.py, tests/conformance_matrix.py, CHANGELOG.md, .aw/records/plans/pending/20261012-o8cz48-01-2va0jb-route-aw-config-exclude-subcommand-less-refusal-through-the.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: o8cz48
- Blocks-Release: next
- Set: o8cz48
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2va0jb
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261012-o8cz48-01-2va0jb-route-aw-config-exclude-subcommand-less-refusal-through-the.review.md`). Re-measured at review HEAD `0d3ab57ab` with an isolated `XDG_CONFIG_HOME`: root and all three leaves still print human lines under `--agent` (F-01, F-03 confirmed); `0qdl9e` is still pending, so no `FAMILY_ROOT_EXEMPTION_REGISTRY` exists yet.
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog o8cz48; all four `config` family surfaces plus the three `config exclude` leaves re-measured at authoring HEAD 5f816e9aa.

## Goal

Every `aw config exclude` surface (the bare family root and its `add`, `list`, `rm` leaves) emits exactly one schema-valid `aw.agent/v1` record under `--agent` whose `exit` equals the process exit code, with the bare root emitting the same `kind: "error"`, `outcome: "cannot-run"`, `exit: 2`, `next` refusal its 16 conforming sibling roots already emit, so a caller probing the verb gets a refusal it can branch on instead of a JSONL parse error.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: production fix

- [ ] E-01 In `agent_workflows/cli.py`, change `_run_config_exclude(args, term)` to `_run_config_exclude(args, term, parser, context=None)` and update its single caller in `_dispatch` (`if subcmd == "exclude":` / `return _run_config_exclude(args, term)`) to pass `parser, context`. Replace the fall-through `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` / `return 2` with `return _show_family_help(parser, "config exclude", "aw config exclude list", term, context)`. `_show_family_help` resolves `cmd_name` against the ROOT parser's `choices`, where `"config exclude"` is not a key, so its HUMAN branch would fall back to the ROOT `parser.format_help()`: about 229 lines of top-level help that never mention `add`/`list`/`rm` (measured at review on `aw ipd dependencies`, which takes that fallback today). That would replace today's one-line human usage hint with worse guidance, so E-01 routes only the MACHINE branch through the helper and keeps a scoped human branch: `if context is not None and context.is_agent: return _show_family_help(parser, "config exclude", "aw config exclude list", term, context)`; otherwise print the `config exclude` subparser's own `format_help().rstrip()` (looked up through the root parser's `_SubParsersAction.choices["config"]` then its `choices["exclude"]`, the same lookup the helper does one level down), a blank line, and `term.format_next_action("aw config exclude list")`, then return 2, which is byte-for-byte the helper's human shape with the right help text. `--json` takes the human branch, exactly as `_show_family_help` does for every sibling root (`aw config --json` prints help; root `--json` parity is out of scope per `0qdl9e`) (OQ-02, revised at review). The next action is `aw config exclude list` because `list` is the only read-only subcommand (backlog item). Do not move the `cfg = config.load()` call (it is harmless and both leaves need it), and do not touch any other branch here.
  - Depends on: none
  - Expected outcome: `python3 -m agent_workflows config exclude --agent` prints one line, `{"schema":"aw.agent/v1","kind":"error","cmd":"config exclude","outcome":"cannot-run","exit":2,...,"next":"aw config exclude list"}`, exit 2; the human invocation prints the `config exclude` usage (containing `{add,list,rm}`) and `Next  aw config exclude list`, exit 2, and does NOT print the root `<command> ...` usage.
  - Execution state: pending

- [ ] E-02 In the same function, give the `list` leaf machine arms BEFORE its human rendering: if `args.json` (or `as_json`) print `json.dumps({"entries": current, "count": len(current)}, indent=2, sort_keys=True)` and return 0; elif `args.agent`, `return _emit_config_agent_record(cmd="config-exclude-list", outcome="clean", exit_code=0, verified=True, complete=True, extra={"entries": current, "count": len(current), **({"next": "aw config exclude add <path>"} if not current else {})}, args=args)`. Entries pass through `_sanitize_config_agent_value` inside the helper, so home paths stay `~`-relative. An empty list is a clean exit-0 answer (contract Section 11.1), not an error.
  - Depends on: none
  - Expected outcome: `config exclude list --agent` prints one valid `result` record with `entries`/`count`, exit 0; `--json` prints the bare dict; human output unchanged.
  - Execution state: pending

- [ ] E-03 In the same function, give the `add` and `rm` leaves machine arms on every return path, using the same `--json` then `--agent` precedence and cmd values `config-exclude-add` / `config-exclude-rm` (the hyphenated convention of `config-remove`, `config-is`). `add`: payload `{"entry": entry, "added": <bool>, "entries": current}`, `added: False` with `outcome: "clean"`, exit 0 when already present (idempotent no-op, as the human path already returns 0); `added: True`, `outcome: "clean"`, exit 0 after saving. Both `add` and `rm` records also carry `"applied": <bool>` (True only when the config file was written: `added` True, or `removed` non-empty), matching `docs/cli-output-contract.md` Section 11.3's agent-mode `applied` field for mutations; no `changes` list is added (the sibling `config-add`/`config-remove` records carry none, and the config path is already reported by those siblings, not here). `rm`: when nothing matched, payload `{"path": <args.path via config._preserve_home>, "removed": [], "entries": current}` with `outcome: "findings"`, `verified: False`, exit 1 (mirrors `config-remove`'s not-found arm); when matched, `{"path": ..., "removed": removed, "entries": kept}`, `outcome: "clean"`, exit 0. Every save happens before the emit, exactly as today; no behavior change to what is written to config.
  - Depends on: none
  - Expected outcome: each of the four add/rm outcomes prints one valid `result` record with exit parity under `--agent` and a bare dict under `--json`; the human lines are unchanged.
  - Execution state: pending

### Task group 2: registry and tests

- [ ] E-04 In `tests/conformance_matrix.py`, delete the `"config exclude list"` entry from `EXEMPTION_REGISTRY` (its `sanctioned_raw` reason, "Emits raw list of excluded configuration variable names", is false: the leaf printed a human heading, and the leaf now emits a record) and decrement the `# sanctioned_raw (7):` count comment to 6. That admits the leaf into `tests/test_agent_surface_conformance.UNIVERSE` (it is declared `command_class="read"`, `agent_record_kind="result"`), so the existing sweep gates it. If plan `0qdl9e` has already landed a `FAMILY_ROOT_EXEMPTION_REGISTRY` entry for `"config exclude"` citing `o8cz48`, delete that entry too (its own strict still-broken test would otherwise go red, which is the intended handoff); if it has not landed, record "not present" in V-04. Leave the `add`/`rm` `MUTATION_EXEMPTION_REGISTRY` entries alone (Scope OUT).
  - Depends on: E-02
  - Expected outcome: `config exclude list` is in `UNIVERSE` and its parametrized case passes; no registry entry cites `o8cz48`.
  - Execution state: pending

- [ ] E-05 Append to `tests/test_config_agent_surface.py` behavioral subprocess tests reusing its `_run_cli_agent` helper (isolated `XDG_CONFIG_HOME=tmp_path`, which already asserts one line, `validate_agent_record == []`, and exit parity): (a) `["config", "exclude", "--agent"]`: rc 2, `kind == "error"`, `outcome == "cannot-run"`, `cmd == "config exclude"`, `next == "aw config exclude list"`; (b) `list --agent` on an empty config: rc 0, `entries == []`, `count == 0`, `next` present; (c) `add <tmp>/legacy --agent`: rc 0, `added is True`; repeated: rc 0, `added is False`; then `list --agent` shows the entry; (d) `rm <tmp>/nope --agent`: rc 1, `outcome == "findings"`, `removed == []`; (e) `rm <tmp>/legacy --agent`: rc 0, `removed` non-empty, and a following `list --agent` shows `count == 0`; (f) `exclude list --json` and `exclude add --json` stdout parse with `json.loads` to dicts carrying the E-02/E-03 keys; (g) bare `["config", "exclude"]` (human) exits 2, its stdout does NOT contain `FAIL     Usage:`, DOES contain `{add,list,rm}` and `Next  aw config exclude list`, and does NOT contain `<command> ...` (the root-help fallback, PR-001); (h) `add <p> --agent` and `rm <p> --agent` carry `applied is True` and the repeated `add` and the no-match `rm` carry `applied is False`; (i) the `add`/`rm` records contain no `/home/` or `/Users/` substring (the `_run_cli_agent` validator already refuses an unsanitized home path, so this is a belt-and-braces outcome check on the stored entry). Every subprocess sets `XDG_CONFIG_HOME` to the test's `tmp_path` so the user's real config is never touched. No source reading, `inspect` or `ast` (GUIDING_PRINCIPLES P16).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all new tests pass post-fix; (a) through (i) fail against pre-fix `cli.py` (each pre-fix `--agent` run prints a human line, so `_run_cli_agent`'s `json.loads` or validator fails).
  - Execution state: pending

### Task group 3: user-facing note

- [ ] E-06 Add one `- Fixed:` line to the `## 2.0.0 (pending)` section of `CHANGELOG.md`: `aw config exclude` with no subcommand now refuses with a standard `aw.agent/v1` error record under `--agent` (exit 2, pointing at `aw config exclude list`) instead of printing a human usage line to stdout, and `aw config exclude add`, `list` and `rm` now emit `aw.agent/v1` result records under `--agent` and plain JSON under `--json`; human output and exit codes are unchanged. No em or en dashes.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: CHANGELOG carries the line; a dash check on it finds nothing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Subcommand-less family roots refuse through `cli._show_family_help`, which under `context.is_agent` emits `CommandResult(status="cannot-run", exit_code=2, next_actions=[NextAction(command=next_cmd)], data={"target": cmd_name})` via `get_renderer(context).emit`. Measured at authoring: `config --agent`, `storage --agent`, `ipd dependencies --agent`, `agy profile --agent` all emit `{"kind":"error","outcome":"cannot-run","exit":2,...,"next":...}`.
- `config` verbs emit agent records through `cli._emit_config_agent_record` (which sanitizes home paths with `_sanitize_config_agent_value`, honors `--fields`, and writes `agent_schema.render_jsonl_record`, which validates) and `--json` through a bare `json.dumps(..., indent=2, sort_keys=True)`, with `--json` tested before `--agent` (`_run_config_remove`, `_run_config_is`). `--agent --json` together is refused upstream ("conflicting output format flags").
- The read-surface sweep `tests/test_agent_surface_conformance.compute_conformance_universe` admits `read`/`check`/`bare` leaves declaring `agent_record_kind == "result"` minus `EXEMPTION_REGISTRY`; it runs via `conformance_matrix.run_cli`, which does NOT pin `XDG_CONFIG_HOME`, so only READ-only leaves may join it (`config show` already does).
- `tests/test_config_agent_surface.py` drives subprocesses with an isolated `XDG_CONFIG_HOME` and its `_run_cli_agent` asserts exactly one line, validator-clean, exit parity.
- Suite runs bare: `python3 -m pytest` (AGENTS.md repo-local development contract). Tests assert outcomes only (GUIDING_PRINCIPLES P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The bare root prints a human status line on stdout under `--agent` and `--json`. | `cli._run_config_exclude` fall-through `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` / `return 2`. Measured: `python3 -m agent_workflows config exclude --agent` stdout `FAIL     Usage: aw config exclude {add|list|rm} ...`, exit 2; `2>/dev/null` still shows the line, so it is stdout. |
| F-02 | The other three `config` surfaces the item names conform now; the `dtq6jr` registry text it warns about is already gone. | `config show --agent`, `config get repos.search --agent`, `config is repos.search x --agent` each printed one `aw.agent/v1` record (exit 0, 0, 1). `grep dtq6jr tests/` returns nothing; `UNIVERSE` contains `config get`, `config is`, `config show`. |
| F-03 | The three exclude LEAVES are also non-conforming machine surfaces despite declaring `result`. | `command_surface.COMMAND_INVENTORY`: `config exclude add` / `list` / `rm` all `agent_record_kind="result"`. Measured: `config exclude list --agent` and `--json` print `Never-install exclude list` plus entries; `exclude add <p> --agent` printed `OK       Added to the never-install exclude list: ...`; `exclude rm <nope> --agent` printed `WARN     No exclude entry matched: ...`, exit 1. All in the one handler. |
| F-04 | The `config exclude list` `sanctioned_raw` exemption is stale and inaccurate. | `EXEMPTION_REGISTRY["config exclude list"]` reason "Emits raw list of excluded configuration variable names.", citation `agent_workflows/cli.py`; actual output is a human heading plus indented paths (F-03), not a sanctioned raw stream; no doc section sanctions it (unlike `find`'s Section 12 citation). |
| F-05 | The proposed record shapes validate. | Probe: `agent_schema.validate_agent_record` on `{"kind":"result","cmd":"config-exclude-list","outcome":"clean","exit":0,"verified":true,"complete":true,"entries":[],"count":0,"next":"aw config exclude add <path>"}` returned `[]`; the `findings`/exit-1 rm variant also returned `[]`. |
| F-06 | Plan `0qdl9e` (to-review) may land a `known_broken` root exemption for `config exclude` citing `o8cz48` with a strict still-broken check. | `0qdl9e` E-03 "`\"config exclude\"` citing `o8cz48`. If E-01 shows either already conforming, OMIT its entry"; OQ resolution "the `l5dq92`/`o8cz48` executor sees one red test naming the entry to delete". Hence E-04's conditional deletion; no ordering edge is needed either way. |
| F-07 | No test pins the old usage line or the leaves' human text under machine flags. | `grep -rn "Usage: aw config exclude\|No exclude entry matched\|Already excluded" tests/` returns nothing; `tests/test_cli.py` only checks the `install` help mentions "never-install exclude list". |
| F-08 | No spec governs this surface. | `grep -rln "config exclude" .aw/records/specs/` returns nothing; the governing doc is `docs/cli-output-contract.md`, whose existing rules (Sections 4, 11) already require what this plan does, so it needs no edit. |

## Proposed changes (ordered, validatable)

1. E-01: root fall-through via `_show_family_help`.
2. E-02 / E-03: machine arms for `list`, `add`, `rm` via `_emit_config_agent_record` and bare `--json` dicts.
3. E-04: drop the stale `config exclude list` exemption (and any `0qdl9e` root entry citing `o8cz48`).
4. E-05: isolated-config subprocess tests for root and leaves.
5. E-06: CHANGELOG line.

Alternatives considered and rejected: (i) fix ONLY the root, as the item's "likely fix" sentence describes: leaves the three leaves in the same handler emitting human text under declared `result` machine flags, splitting one family across two plans, which the item says not to do ("The whole `config` family envelope should be decided in one pass"). (ii) Re-declare the leaves `human_recipe`-only / `sanctioned_raw`: contradicts their existing `agent_record_kind="result"` declarations and leaves a caller with no branchable verdict. (iii) Admit `add`/`rm` to the mutation sweep: requires a `RUNNABLE_ARGV` fixture design for that sweep; the new tests already isolate config and cover both leaves.

## Deferred / out of scope (with reason)

- `MUTATION_EXEMPTION_REGISTRY` `arg_fixture_needed` entries for `config exclude add` / `rm`: the mutation sweep's argv-fixture design is a harness concern unrelated to this defect; behavior is covered by E-05.
  - Carrier-Declined: no defect is left behind; E-05 covers both leaves with an isolated config, and the mutation-sweep fixture design is a harness choice, not an owed fix.
- The family-root sweep: owned by `0qdl9e`.
  - Carrier: 0qdl9e
  - Carrier-Evidence: .aw/records/plans/executed/20261012-o7wwop-01-0qdl9e-family-root-agent-conformance-gate-for-every-cli-subparser-r.ipd.md
- `_show_family_help` resolving nested `cmd_name` only against the root parser (affects `ipd dependencies` today, whose human bare invocation prints the root help): a human-guidance defect with no machine-surface effect; this plan sidesteps it for `config exclude` with a scoped human branch (OQ-02) and does not change the shared helper.
  - Carrier-Declined: not filed here; reported to the maintainer in the 2026-10-12 review report, and the `ipd dependencies` human output is pre-existing and outside this item.

## Scope check

- Over-scope: E-02/E-03 extend past the item's root-only "likely fix" to the three leaves, justified by the item's explicit one-pass family requirement and F-03; they touch only the same function.
- Under-scope: none known. No spec or doc edit is required (F-08).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_config_agent_surface.py -v`: all pass post-fix; the new cases shown failing against pre-fix `cli.py` (in the lane: `cp agent_workflows/cli.py /tmp/opencode/cli.fixed.py`, `git show HEAD:agent_workflows/cli.py > agent_workflows/cli.py`, run, then `cp /tmp/opencode/cli.fixed.py agent_workflows/cli.py`; never stash).
- `python3 -m pytest -o addopts="" "tests/test_agent_surface_conformance.py" -k "config" -v`: the `config exclude list` case appears and passes.
- `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_cli.py -q`: pass.
- Live: `python3 -m agent_workflows config exclude --agent; echo $?` shows the cannot-run record and 2.
- Full suite bare: `python3 -m pytest`, summary line pasted.

## Spec / documentation sync

- `CHANGELOG.md`: one Fixed line (E-06).
- No `.spec.md` touched and `docs/cli-output-contract.md` unchanged: no spec governs this surface, and the contract's existing Sections 4 and 11 already require exactly this behavior (F-08).

## Open questions

### OQ-01: Fix only the root, or the whole `config exclude` handler?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The whole handler. The backlog item requires re-measuring all `config` surfaces and deciding the family envelope in one pass; the re-measure (F-02, F-03) shows `show`/`get`/`is` already conform and the only remaining defects are the root plus its three leaves, all in `cli._run_config_exclude`. Record shapes reuse the family helper and validate (F-05).

### OQ-02: Accept `_show_family_help`'s root-help fallback for the nested `"config exclude"` name in human mode?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO (revised at review, PR-001). The authored answer accepted the fallback, but the fallback prints the ROOT help (measured at review: `aw ipd dependencies` human prints 229 lines starting `usage: agent-workflows [-h] ... <command> ...`, none naming the dependency verbs), which would regress today's human hint `Usage: aw config exclude {add|list|rm} ...` into worse guidance. E-01 therefore calls the shared helper for the agent branch only and prints the `config exclude` subparser's own help plus the same `Next` line for the human branch. Teaching the helper nested lookup would change shared behavior for other roots (`ipd dependencies`) and stays out of scope.

### OQ-03: `rm` with no match: `findings` exit 1, or `cannot-run` exit 2?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `findings`, exit 1. The human path already returns 1 there and the declaration is `exit_contract=(0, 1, 2)`; the sibling `config-remove` not-found arm emits `outcome: "findings"`, exit 1 (`tests/test_config_agent_surface.test_config_remove_not_found_agent`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- agent_workflows/cli.py` hunks for the signature, the caller, and the fall-through; paste live `python3 -m agent_workflows config exclude --agent; echo $?` (code path `cli._dispatch` -> `_run_config_exclude` -> `_show_family_help`, created by E-01) showing the `cannot-run` record with `next` and `2`; paste `python3 -m agent_workflows config exclude 2>/dev/null | grep -c "FAIL     Usage"` printing `0`, and the human stdout's first usage line and last line showing `agent-workflows config exclude` usage with `{add,list,rm}` and `Next  aw config exclude list` (not the root `<command> ...` usage).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: with `XDG_CONFIG_HOME` set to an empty temp dir, paste `python3 -m agent_workflows config exclude list --agent; echo $?` (code path `_run_config_exclude` `list` arm, created by E-02) showing one record with `"entries":[]`, `"count":0`, `next`, and `0`; paste the same with `--json` printing the bare dict.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: in the same isolated `XDG_CONFIG_HOME`, paste live `--agent` output plus `echo $?` for `add <p>` (added true, applied true, 0), repeated `add <p>` (added false, applied false, 0), `rm <nope>` (findings, applied false, 1), `rm <p>` (clean, removed non-empty, applied true, 0) (code path `_run_config_exclude` add/rm arms, created by E-03); paste `git diff -- agent_workflows/cli.py` for those arms showing the save calls unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- tests/conformance_matrix.py`; paste `grep -n "o8cz48" tests/conformance_matrix.py` returning nothing (and state whether a `0qdl9e` root entry was present); paste `python3 -m pytest -o addopts="" tests/test_agent_surface_conformance.py -k "config" -v` showing a PASSED line for `config exclude list`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_config_agent_surface.py -v` with every case passing post-fix, and the run of the new cases against pre-fix `cli.py` showing them failing; paste `grep -nE "inspect|import ast|read_text" tests/test_config_agent_surface.py` showing no new hits; paste the full suite bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff -- CHANGELOG.md` showing the one `- Fixed:` line under `## 2.0.0 (pending)`, and `git diff -U0 -- CHANGELOG.md | grep -nP "[\x{2013}\x{2014}]"` printing nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Reviewers should push hardest on OQ-01 (extending past the root to the three leaves) and on E-04 (admitting `config exclude list` to the unpinned-config read sweep, safe only because the leaf is read-only).

Execution contract: commit only the paths in `Scope-Paths` through `aw commit 2va0jb -- <paths>`, never `git add -A`, never push. Verify the staged set with `git diff --cached --name-only` before committing. Every live probe of an `add`/`rm` leaf MUST set `XDG_CONFIG_HOME` to a temp dir so the operator's real config is never mutated. Run the suite bare as `python3 -m pytest` and paste its actual summary line; for any failure, re-run that selection at the unmodified base commit and state whether it is pre-existing. `- Scope-Paths:` is a declaration, not a stop condition: an out-of-scope edit the work genuinely needs is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. All open questions are resolved (OQ-02 revised at review). Begin with `aw ipd begin`. Do not claim done while any `V-*` is pending: each carries pasted observed evidence and `aw ipd lint --phase pre-transition` must conform before the plan moves to `executed/`. Under `aw oc run`/`aw agy run` the runner owns that finalize; executed by hand, the executor runs `aw ipd finalize`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Backlog `o8cz48` is already `graduated`; it closes `done` via the From-Backlog handoff once this plan is executed, carrying `Blocks-Release: next`.
