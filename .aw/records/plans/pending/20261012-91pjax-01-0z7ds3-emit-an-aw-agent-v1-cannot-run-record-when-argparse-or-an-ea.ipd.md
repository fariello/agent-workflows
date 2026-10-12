# IPD: Emit an aw.agent/v1 cannot-run record when argparse or an early required-flag check refuses under --agent

- Date: 2026-10-12
- Kind: child
- Concern: Under `--agent`, a CLI-wide class of usage refusals exits `2` having written ZERO bytes to stdout, so a machine caller parsing stdout gets an empty string and cannot tell a refusal from a crash, a hang, or a no-op. `docs/cli-output-contract.md` Section 11.4 already requires the opposite ("Missing mandatory arguments ... MUST exit `2` ... Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` ... and a `next` recovery command (e.g. `aw <cmd> --help`)"). Backlog `91pjax` measured seven mutation leaves; re-measured at authoring HEAD `2a22b4ae2` all seven still exit `rc=2 bytes=0`, but they split into TWO mechanisms the item did not distinguish (F-01): four are refused INSIDE ARGPARSE (`_AwArgumentParser.error`) before any handler runs (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`), and three are refused by an EARLY HANDLER CHECK that writes only to stderr (`backlog new` missing `--priority`/`--work-kind`, `specs new` missing `--title`, `prompts new` missing `--slug`). The argparse half is CLI-wide: 67 of 157 canonical leaves carry a required argument (F-03), plus every `invalid choice` and unknown-subcommand refusal on the same path.
- Scope: IN: (1) re-measure the seven and the parser census at the executing HEAD, as a gate (E-01); (2) add ONE shared usage-refusal emitter that builds a schema-valid `kind: error` `outcome: cannot-run` `exit: 2` record with a `next` of `aw <leaf> --help` (E-02); (3) make `_AwArgumentParser.error` sniff the output mode from the raw argv it is parsing and, under `--agent` or `--json`/`--format json`, write that record to stdout while keeping the existing stderr diagnostic (E-03); (4) route the three handler-level missing-required refusals the sweep hits through the same emitter (E-04); (5) a behavioral sweep test over EVERY leaf with a required argument, driven from the live parser tree rather than a hand list (E-05); (6) remove the seven `owned_elsewhere` `91pjax` exemptions from `MUTATION_EXEMPTION_REGISTRY` so those leaves enter the mutation conformance universe (E-06); (7) a `CHANGELOG.md` `Fixed:` line and a doc note in Section 11.4 naming the parse-time path (E-07). OUT: the OTHER early refusals in those same handlers (`specs new --date` malformed, `backlog new` unsafe `--summary`, `ipd_authoring.run_scaffold`'s human `print` to stdout for an empty `--title`), filed at authoring as backlog `mmpjti`; the family-root (subcommand-less group) case, already owned by `_show_family_help` and closed under `lbbo9s`; the `aw config exclude` human-line case (`o8cz48`) and the `aw sanitize` branches (`k84fqu`), each owned by its own open item.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/renderers.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/prompts.py, tests/test_usage_refusal_agent_record.py, tests/conformance_matrix.py, docs/cli-output-contract.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 91pjax
- Blocks-Release: next
- Set: 91pjax
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: 0z7ds3
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed

- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261012-91pjax-01-0z7ds3-emit-an-aw-agent-v1-cannot-run-record-when-argparse-or-an-ea.review.md`). PR-001 replaced the per-parser argv capture with a dispatch-level `ContextVar`, demonstrated on Python 3.14 and 3.12. Census and the 67-leaf bare `--agent` sweep re-measured at review HEAD `f52907adc` (157 / 67 / 0; all 67 `rc=2`, 0 stdout bytes).
- 2026-10-12 to-review (opencode): authored from backlog item `91pjax`. Re-measured the seven leaves at HEAD `2a22b4ae2` (all `rc=2`, 0 stdout bytes) and found two mechanisms, four argparse-level and three handler-level (F-01). Resolved the item's open architectural question from repository evidence: sniff the mode from the raw argv inside `_AwArgumentParser.error` (OQ-01). Filed the handler refusals this plan does not convert as backlog `mmpjti` instead of widening scope.
- 2026-10-12 draft (opencode): created.

## Goal

Make every usage refusal that fires before a command's handler emits output (and the three handler-level missing-required refusals the mutation sweep measures) write one schema-valid `aw.agent/v1` `cannot-run` error record to stdout under `--agent` or `--json`, as `docs/cli-output-contract.md` Section 11.4 already requires, without changing what a human sees on stderr or any exit code. Pin it with a sweep driven from the live parser tree so a new leaf with a required argument is covered automatically.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Re-drive the seven measured leaves and the required-argument census at the executing HEAD, recording both verbatim and editing no file.
  - Depends on: none
  - Expected outcome: two pasted transcripts. (a) THE PROBE: for each of `ipd scaffold`, `research new`, `research new-comparison`, `storage move`, `backlog new`, `specs new`, `prompts new`, run `python3 -m agent_workflows <leaf> --agent` from the repo root and print `rc`, the stdout byte count, and the first stderr error line. Expected at authoring: `rc=2 bytes=0` for all seven, with `the following arguments are required:` for the first four and the handler messages `aw backlog new: --priority and --work-kind required: ...`, `aw specs new: --title is required`, `aw prompts new: --slug is required` for the last three. (b) THE CENSUS: walk `cli._build_parser()` with `command_surface.discover_parser_leaves`, count leaves carrying an argument that is `required=True` or a positional whose `nargs` is not `?`, `*` or `REMAINDER`, and confirm every subparser in the tree is an `_AwArgumentParser` instance. Expected at authoring: 157 leaves, 67 with a required argument, 0 parsers of another class (all three re-measured at review HEAD `f52907adc`; every one of the 67, driven bare with `--agent`, exited 2 with 0 stdout bytes and a `the following arguments are required:` stderr line). Also probe `aw --agent ipd scaffold` (global flag before the leaf) and record it; it must be `rc=2 bytes=0` today.
    GATE: if any of the seven already emits a non-empty stdout, another lane has touched this path, so STOP and reconcile before editing. If the census finds a subparser that is NOT an `_AwArgumentParser`, record it: E-03's override would not reach it, and that parser must either be converted or named as excluded in V-05.
  - Execution state: pending

### Task group 2: the shared emitter and the parse-time path

- [ ] E-02 Add one shared usage-refusal emitter in `agent_workflows/renderers.py` (for example `emit_usage_refusal(cmd, message, next_cmd, context)`) that builds a `CommandResult(status="cannot-run", exit_code=2, verified=False, complete=False)` with the refusal text as its summary and `next_cmd` as its single `NextAction`, and emits it through `get_renderer(context)`.
  - Depends on: E-01
  - Expected outcome: for an AGENT context it writes exactly one `aw.agent/v1` line that passes `agent_schema.validate_agent_record` with `kind: error`, `outcome: cannot-run`, `exit: 2`, `complete: false`, and `next` set to `next_cmd`; for a JSON context it writes the `JsonRenderer` dict; for a HUMAN context it writes NOTHING to stdout and returns `2`, because the human diagnostic is the caller's stderr text and must not be duplicated (Section 7: "Diagnostics are never duplicated across both streams"). The refusal message passes through `agent_schema.redact_home_paths`, since argparse messages can echo a user-supplied path. It reuses `CommandResult.to_agent_record` rather than hand-assembling a dict, matching `cli._show_family_help`, which is the in-repo precedent for a `cannot-run` usage record.
  - Execution state: pending

- [ ] E-03 Override the machine half of `_AwArgumentParser.error` so that, when the argv being parsed requests agent or JSON output, it calls the E-02 emitter on stdout before `self.exit(2)`, keeping the existing stderr usage, `error:` line and `Next` hint byte-identical.
  - Depends on: E-02
  - Expected outcome: `cli._dispatch` records the FULL raw argv of the invocation (the `argv_list` left after `_consume_early_flags`, held for the remainder of `_dispatch` so it covers both `parser.parse_args` call sites, including the `runs` re-parse) in one module-level `contextvars.ContextVar` (for example `_RAW_DISPATCH_ARGV`), set with a token and reset in a `try`/`finally` so a nested or repeated in-process `_dispatch` (the test suite calls it many times per process) never inherits a stale value, and `_AwArgumentParser.error` decides the mode by scanning THAT list for `--agent`, `--json`, or `--format json` / `--format=json`, stopping at a bare `--` so a forwarded token is never read as a flag. When the var is unset (a parser built and used outside `_dispatch`, for example a test calling `_build_parser().parse_args(...)` directly), `error` behaves exactly as today. Do NOT record the argv per parser inside `parse_known_args`: a subparser only ever sees the tokens left after its parent consumed its own, so `aw --agent ipd scaffold` (the global flag BEFORE the leaf) would be invisible to the leaf parser, and on Python 3.9 to 3.12 the stdlib's intermixed parse re-enters `parse_known_args` with the positionals already stripped, so a `+`-positional leaf (`ipd set`, `config set`) would record `[]` even for `aw ipd set --agent` (both measured at review, see the review record). The record is built with an `OutputContext(mode=OutputMode.AGENT)` or `OutputContext(mode=OutputMode.JSON, explicit_format="json")` constructed directly, because no parsed `args` exists yet. Mode precedence matches `result_types.select_output`: an explicit JSON request wins over `--agent`, and when BOTH are present the `ConflictingFlagsError` rule applies, so emit nothing extra and keep the plain stderr refusal. `cmd` is the leaf path derived from `self.prog` with the `agent-workflows ` prefix stripped (`agent-workflows ipd scaffold` -> `ipd scaffold`), and `next_cmd` is the same `aw <leaf> --help` string the stderr `Next` line already prints. The emitter is NOT invoked for `--help`/`--version` exits, which do not go through `error`. Exit code stays `2` on every path. A refusal from the top-level parser (unknown command) emits `cmd: aw` with `next: aw --help`.
  - Execution state: pending

### Task group 3: the three handler-level refusals the sweep measured

- [ ] E-04 Route the three missing-required handler refusals through the E-02 emitter: `backlog.run_new` when `--priority` or `--work-kind` is missing and when `--summary` is empty, `specs.run_new` when `--title` is empty, and `prompts.run_new` when `--slug` is empty.
  - Depends on: E-02
  - Expected outcome: each keeps its EXISTING stderr message byte-identical (so `tests/test_backlog_descriptive_safety.py::test_empty_summary_refusal_unchanged`, which asserts `err == "aw backlog new: --summary is required\n"`, stays green) and additionally calls the emitter with the `ctx` each handler already resolves via `select_output(args)`, so a HUMAN invocation is unchanged and an `--agent` invocation gains one `cannot-run` record whose `next` is `aw <verb> new --help`. `backlog.run_new` resolves no `ctx` before these checks today, so E-04 calls `select_output(args)` before them; it cannot raise `ConflictingFlagsError` there, because `_dispatch` already refused that combination before dispatching. No other `return 2` arm in these three handlers is touched: those belong to `mmpjti`.
  - Execution state: pending

### Task group 4: pin it

- [ ] E-05 Create `tests/test_usage_refusal_agent_record.py`, a behavioral sweep that drives the real CLI and asserts on stdout, stderr and exit code.
  - Depends on: E-03, E-04
  - Expected outcome: (1) A parametrized test over EVERY canonical leaf from `discover_parser_leaves(cli._build_parser())` that has a required argument, computed at collection time from the live parser tree (never a hand list), that drives `cli.main(<leaf tokens> + ["--agent"])` IN-PROCESS with `contextlib.redirect_stdout`/`redirect_stderr` and `SystemExit` caught (the `tests/test_leak_sanitizer_machine_flags.py` `_capture_cli_separate` pattern), with cwd-independent arguments only, the required arguments omitted, and asserts: exit `2`; stdout non-empty; the LAST stdout line parses as JSON and `validate_agent_record` returns `[]`; `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `next == f"aw {leaf} --help"`; no `/home/` and no temporary path in stdout. A leaf whose handler-free refusal is impossible in that form (for example a positional consumed by `REMAINDER`, which argparse never refuses) is excluded by a named, reasoned set in the test, and the set size is printed in the test id or asserted, so an exclusion is visible rather than silent. (2) The same leaves with `--json` assert the stdout parses as one JSON object whose `status` is `cannot-run` and `exit_code` is `2`. (3) A HUMAN control on a representative leaf (`ipd scaffold`) asserts stdout is EXACTLY empty and stderr still contains `the following arguments are required:` and `Next  aw ipd scaffold --help`. (4) `--agent --json` together on `ipd scaffold` asserts exit `2` and no JSON line on stdout. (5) A token after `--` on a forwarding leaf (`aw test -- --agent`, or another leaf whose REMAINDER is measured in E-01) is not treated as a mode request. (6) The unknown-command case `aw nosuch --agent` emits `cmd == "aw"`, `next == "aw --help"`. (7) The three E-04 leaves under `--agent` emit a valid `cannot-run` record and, without `--agent`, keep stdout empty. (8) GLOBAL-FLAG POSITION: `aw --agent ipd scaffold` and `aw --agent ipd set` (flag BEFORE the leaf, a `+`-positional leaf in the second case) each emit the same valid record as the trailing-flag spelling; this is the case a per-parser argv capture misses (PR-001). (9) An `invalid choice` refusal on a family (`aw ipd nosuch --agent`) emits `cmd == "ipd"`, `next == "aw ipd --help"`. The in-process drive is REQUIRED, not a stylistic choice: E-01 measured one bare-leaf subprocess at about 1 second (67 leaves took 66 seconds serially at review), and parametrizing (1) and (2) as subprocesses would add over two minutes to the fast suite, against the 0.23 seconds per call measured in-process. Cases (5), (6) and one representative of (1) MAY additionally run as a subprocess with a timeout to prove the real entry point; any such subprocess carries a timeout. The sweep must not depend on Python 3.13+ argparse behavior, because the CI matrix starts at the `requires-python = ">=3.9"` floor and the stdlib's intermixed-parse path differs before 3.13; V-05 names the interpreter used and, if an interpreter below 3.13 with the project's dependencies is available, runs the sweep there too. The file reads no production source and asserts on no comment or docstring (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
  - Execution state: pending

- [ ] E-06 Delete the seven `reason_kind="owned_elsewhere"`, `citation="91pjax"` entries from `MUTATION_EXEMPTION_REGISTRY` in `tests/conformance_matrix.py` and correct the `# owned_elsewhere (9):` count comment to `(2)`, so those leaves enter `MUTATION_UNIVERSE` and `test_agent_surface_conformance_mutation` drives them.
  - Depends on: E-03, E-04
  - Expected outcome: `MUTATION_UNIVERSE` grows from 24 to 31 (measured 24 at authoring), and all seven new rows pass, because each leaf invoked bare with `--agent` now emits a valid `cannot-run` record whose `exit` equals the process exit. The two `eeiytw` entries (`rename`, `group`) are left untouched. If any of the seven fails a property other than the ones this plan fixes (for example the path-leak checks), STOP and record which: re-adding it with a NEW citation is a human decision, not something to paper over.
  - Execution state: pending

### Task group 5: keep the record true

- [ ] E-07 Add one `CHANGELOG.md` `Fixed:` line under the pending 2.0.0 section, and one sentence to `docs/cli-output-contract.md` Section 11.4 stating that the agent-mode `cannot-run` record also applies to refusals raised while parsing arguments, before any command runs, and that the human stderr text is unchanged.
  - Depends on: E-03
  - Expected outcome: both are user-facing prose, so neither contains an em or en dash (`AGENTS.md`). The changelog line names the observable change ("usage errors such as a missing required argument or an invalid choice now emit an aw.agent/v1 cannot-run error record on stdout under --agent and --json"). The doc sentence adds no new requirement: Section 11.4 already states the rule; it only removes the ambiguity about when it applies.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert OUTCOMES, not code structure (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). E-05 drives the real CLI through subprocesses and inspects stdout, stderr and exit codes; it never greps `cli.py`.
- The in-repo precedent for a usage-class `cannot-run` record is `cli._show_family_help`: it builds `CommandResult(status="cannot-run", exit_code=2, next_actions=[NextAction(...)], verified=False, complete=False)` and emits through `get_renderer(context)`. Measured at authoring: `aw project --agent` prints `{"schema":"aw.agent/v1","kind":"error","cmd":"project","outcome":"cannot-run","exit":2,...,"next":"aw project status"}` with 0 bytes on stderr. E-02 follows that shape.
- Output mode is resolved by `result_types.select_output(args)` AFTER `parser.parse_args(argv)` in `cli._dispatch`, which is the crux the item names: `_AwArgumentParser.error` fires inside `parse_args`, before `args` exists. `_consume_early_flags` already strips `--color`/`--no-color`/`--interactive`/`--no-interactive` from raw argv BEFORE parsing, which is the in-repo precedent for reading a presentation decision from raw argv.
- Every subparser in the tree is created by `_AwArgumentParser` (census at authoring: 0 of any other class), so an override on that class reaches every leaf. `_RunsArgumentParser` subclasses it and inherits the override.
- `_AwArgumentParser.parse_known_args` already wraps the parse with guards (reentrancy sentinel, REMAINDER/PARSER bypass); E-03 does NOT touch it. The argv is captured once at `cli._dispatch`, which sees the whole invocation, rather than per parser, which sees only a suffix (review finding PR-001).
- Stream separation (`docs/cli-output-contract.md` Section 7): stdout carries the final structured result; stderr carries usage diagnostics. Under `--agent` this plan ADDS the record to stdout and keeps the stderr usage text, the same split `_show_family_help` does not need only because it has no stderr text.
- Run the suite BARE as `python3 -m pytest` (`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Use `-o addopts=""` only for per-test counts on a narrowed run (`AGENTS.md`).
- `- Readiness:` is omitted on purpose: `/plan-review` writes it, the author does not (`AGENTS.md`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **The seven re-measure, but as two mechanisms.** All seven exit `rc=2` with 0 stdout bytes under `--agent`. Four are refused by argparse: `ipd scaffold` ("the following arguments are required: --kind, --title, --set, --order"), `research new` ("--kind"), `research new-comparison` ("--set, --slug, --models"), `storage move` ("--new-dir"). Three are refused by the handler after parsing succeeds: `backlog.run_new` ("aw backlog new: --priority and --work-kind required: ..."), `specs.run_new` ("aw specs new: --title is required"), `prompts.run_new` ("aw prompts new: --slug is required"). So a parse-time fix alone leaves three of the seven red, and a handler fix alone leaves four. | Probe loop at HEAD `2a22b4ae2`: `ipd scaffold rc=2 bytes=0`, `research new rc=2 bytes=0`, `research new-comparison rc=2 bytes=0`, `storage move rc=2 bytes=0`, `backlog new rc=2 bytes=0`, `specs new rc=2 bytes=0`, `prompts new rc=2 bytes=0`, with the stderr lines quoted. |
| F-02 | **The rule this violates is already written down.** `docs/cli-output-contract.md` Section 11.4 says "Missing mandatory arguments, unknown subcommands, or invalid selectors MUST exit `2`" and "Agent Mode: emits a `kind: "error"` record with `outcome: "cannot-run"` ..., `exit: 2`, `verified: false`, `complete: false`, and a `next` recovery command (e.g. `aw <cmd> --help`)". So this is conformance work, not a new contract, and no spec needs amending. | Quoted text of Section 11.4. |
| F-03 | **The argparse half is CLI-wide, which is why the fix belongs on the parser class.** 67 of 157 canonical leaves carry a required argument (for example `runs show` refuses with "the following arguments are required: target" and 0 stdout bytes), and every `invalid choice` and unknown top-level command takes the same path (`aw nosuch --agent` writes only the stderr refusal). A per-verb fix cannot reach them because the handlers never run, as the item states. | Parser census at HEAD `2a22b4ae2`: `157 67`; `aw runs show --agent` and `aw nosuch --agent` measured. |
| F-04 | **The mode is unknowable from `args` at error time, but knowable from argv.** `_dispatch` calls `parser.parse_args(argv)` and only then `select_output(args)`. Inside `_AwArgumentParser.error` the only mode signal is the argv being parsed. `--agent`, `--json` and `--format` are declared on the shared `common` parent and accepted after the leaf tokens (the bare-leaf invocations above parse `--agent` correctly up to the missing-argument check), so scanning that argv is reliable. Restructuring the parse into two passes was the alternative and is rejected in OQ-01. | `cli._dispatch` source: `args = parser.parse_args(argv)` then `context = select_output(args)`; `_consume_early_flags` as precedent. |
| F-05 | **One existing test pins the current silence for a case this plan does NOT touch.** `tests/test_backlog_descriptive_safety.py::test_agent_mode_refusal_shape` asserts `out == ""` for an `--agent` `backlog new` whose `--summary` contains a newline. That is the unsafe-descriptive refusal, which E-04 deliberately leaves to `mmpjti`, so the test stays green under this plan, and `mmpjti`'s body records that its fix must update that assertion. | Test source quoted; `mmpjti` body. |
| F-06 | **The handler-level refusal family is larger than the three the sweep hits.** `specs new --title x --date bad --agent` exits `2` with 0 stdout bytes, and `ipd scaffold --title ""` (argparse satisfied, handler refuses) prints the human line "error: --title is required" to STDOUT, which is neither empty nor a valid record. Converting every `return 2` arm in these handlers would multiply this plan's surface; they are filed as backlog `mmpjti`. | Measured at authoring; `ipd_authoring.run_scaffold` uses `print("error: --title is required")`. |

## Proposed changes (ordered, validatable)

1. **Re-measure (E-01).** Seven-leaf probe and parser census at the executing HEAD; a changed result stops the plan.
2. **Shared emitter (E-02).** One function builds and renders the `cannot-run` usage record for every caller, so the parse-time path and the handler path cannot diverge in shape.
3. **Parse-time path (E-03).** `_AwArgumentParser.error` emits the record on stdout when the parsed argv asks for agent or JSON output; stderr is unchanged.
4. **Handler path (E-04).** The three missing-required handler refusals call the same emitter.
5. **Pin (E-05, E-06).** A sweep test over every leaf with a required argument, generated from the parser tree, plus the seven leaves rejoining the mutation conformance universe.
6. **Record (E-07).** A changelog line and one clarifying sentence in Section 11.4.

## Deferred / out of scope (with reason)

- **The other early refusals in `backlog new`, `specs new`, `prompts new` and `ipd scaffold` (malformed `--date`, unsafe descriptive text, the `ipd scaffold` empty-`--title` human line on stdout).** They are handler arms the sweep does not reach with a bare invocation, each needs its own test case, and one of them is currently pinned by an existing test (F-05).
  - Carrier: mmpjti
  - Carrier-Evidence: .aw/records/backlog/open/20261012-mmpjti-01-mmpjti-handler-refusals-silent-on-agent-surface.backlog.md
- **The subcommand-less family-root case.** Already handled by `cli._show_family_help` and closed under `lbbo9s` via plan `7pnneh`.
  - Carrier-Declined: already fixed; no obligation remains.
- **Restructuring `_dispatch` into a two-pass parse so `select_output` can run first.** Rejected in OQ-01.
  - Carrier-Declined: a rejected alternative creates no obligation; it is recorded in OQ-01.

## Scope check

- Over-scope: E-03 changes behavior for every leaf with a required argument and for `invalid choice` / unknown-command refusals, not only the seven named leaves. That is the item's own stated scope boundary ("CLI-wide and affects every leaf with a required positional ... a complete fix should be gated by a behavioral sweep over every leaf"), and E-05 is that sweep.
- Under-scope: the three handler-level leaves are included even though the item framed the defect as argparse-only, because without E-04 the item's own seven-leaf list stays red (F-01). The remaining handler arms are carried by `mmpjti`.
- Right-sizing: seven items, one concern each. E-02 and E-03 are separate because the emitter is reused by E-04 and is testable alone. E-05 and E-06 are separate because they touch different test surfaces (a new sweep file versus the existing mutation registry).

## Required tests / validation

- `python3 -m pytest tests/test_usage_refusal_agent_record.py -o addopts="" -q` with output pasted, showing every parametrized leaf passed and the exclusion set size.
- `python3 -m pytest tests/test_agent_surface_conformance.py -o addopts="" -q -k mutation` with output pasted, showing the seven formerly exempt leaves now pass.
- The targeted regression set, output pasted: `tests/test_backlog_descriptive_safety.py tests/test_specs_date_containment.py tests/test_research_date_containment.py tests/test_specs_releases_descriptive_safety.py tests/test_flag_surface_uniformity.py tests/test_options_anywhere.py tests/test_ipd_authoring.py tests/test_cli.py` (the existing refusal-message, parser backstop and options-anywhere tests that assert on stderr text).
- The E-01 probe re-run after E-03/E-04, pasted, showing each of the seven now `rc=2` with a non-empty stdout record.
- A bare `python3 -m pytest`, compared by FAILURE SET rather than count. Any failure must be shown to reproduce on an unmodified tree at the same HEAD before it is called pre-existing.
- `aw ipd lint --phase pre-transition` conforming on this plan; `aw check`; `aw sanitize --agent` over the changed files.

## Spec / documentation sync

- `docs/cli-output-contract.md` Section 11.4 gets one clarifying sentence (E-07). It is the normative description of the agent error record and already states the rule (F-02).
- `CHANGELOG.md` gets one `Fixed:` line (E-07).
- No spec amendment: no `.spec.md` describes the argparse refusal path (`grep -rln "usage error\|arguments are required" .aw/records/specs/approved .aw/records/specs/implementing .aw/records/specs/reviewed .aw/records/specs/to-review` returned nothing at authoring), so `- Scope-Paths:` declares no `.spec.md`.

## Open questions

### OQ-01: How is the output mode known at parse time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SNIFF IT FROM THE RAW INVOCATION ARGV, recorded once in `cli._dispatch` in a `ContextVar` and read in `_AwArgumentParser.error` (E-03). REVISED AT REVIEW (PR-001): the authored mechanism recorded the argv per parser in `parse_known_args`, which a review probe showed cannot see a global `--agent` placed before the leaf (`aw --agent ipd scaffold`: the leaf parser recorded `[]`) and, on Python 3.12, records `[]` for `aw ipd set --agent` because the intermixed parse re-enters with positionals stripped. DEMONSTRATED at review on Python 3.14 and 3.12 with a monkeypatched prototype of the dispatch-level capture: `ipd set --agent`, `--agent ipd set`, `config set --agent`, `--agent ipd scaffold` and `nosuch --agent` each exited 2 with one stdout record for which `validate_agent_record` returned `[]`, while `ipd scaffold -- --agent` and `ipd scaffold --agent --json` wrote nothing to stdout. Evidence for the approach: `_consume_early_flags` already reads presentation flags from raw argv before parsing, so this adds no new convention; every subparser is an `_AwArgumentParser` (F-03 census), so one override covers the tree; and `--agent`/`--json`/`--format` are defined on the shared `common` parent, so their spelling is fixed. Rejected: (a) a two-pass `parse_known_args` in `_dispatch` to run `select_output` first, because forwarding commands (`commit`, `test`, `oc run`, `agy run`) declare `REMAINDER` positionals and the guarded intermixed parse would have to be run twice with different semantics, a larger and riskier change for the same observable result; (b) a per-verb fix, which the item already rules out because the handler never runs. Reversible: the change is confined to one `ContextVar` set in `_dispatch`, one class method, and the emitter.

### OQ-02: Should the human stderr text change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. Several existing tests assert on the stderr refusal text (for example `tests/test_research_date_containment.py` "the following arguments are required: --models" and `tests/test_flag_surface_uniformity.py` "not allowed with argument"), and Section 11.4 already specifies stderr for the human path. The record is ADDED to stdout in machine mode only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the seven-leaf probe transcript (leaf, `rc`, stdout byte count, first stderr error line for each) and the census output (leaf count, required-argument leaf count, non-`_AwArgumentParser` count), both taken BEFORE any edit, with the HEAD hash. State explicitly whether the GATE fired.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the `git diff` of `agent_workflows/renderers.py` showing the emitter, and an interpreter transcript that calls it once with an AGENT context, once with a JSON context and once with a HUMAN context (each with a captured stdout), printing the captured stdout and the return value for each, plus `validate_agent_record` of the AGENT line returning `[]`. The HUMAN stdout must be the empty string. Code path: the E-02 emitter called directly.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the `git diff` of `agent_workflows/cli.py` limited to `_AwArgumentParser` and the `_dispatch` argv capture. Paste real CLI runs (code path: `_AwArgumentParser.error` reached through `cli._dispatch`) of `aw ipd scaffold --agent`, `aw --agent ipd scaffold`, `aw ipd set --agent`, `aw ipd scaffold --json`, `aw ipd scaffold` (human), `aw ipd scaffold --agent --json`, and `aw nosuch --agent`, each showing exit code, full stdout, and stderr. Show the human run's stderr is byte-identical to the pre-change stderr captured in V-01 for the same leaf (paste both, or a `diff` of the two showing no output).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the `git diff` of `agent_workflows/backlog.py`, `agent_workflows/specs.py`, `agent_workflows/prompts.py` showing only the missing-required arms changed. Paste real CLI runs (code path: each `run_new` handler reached through `cli._dispatch`) of `aw backlog new --agent`, `aw specs new --agent`, `aw prompts new --agent` showing exit `2` and a `cannot-run` record, and the same three without `--agent` showing empty stdout and the unchanged stderr message.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `python3 -m pytest tests/test_usage_refusal_agent_record.py -o addopts="" -q` output with the pass count and zero failures, and state the number of parametrized leaves and the size and members of the named exclusion set, the Python version that ran it, and (if an interpreter below 3.13 with the project's dependencies is available) the same run on it, or a statement that none was available. Paste one deliberate-failure check: temporarily revert the E-03 change in a scratch copy (or `git stash` is NOT allowed; use `git worktree add` on a throwaway branch at the pre-change HEAD and copy only the new test file in) and paste the run showing the sweep FAILS there, proving the test can fail. Remove the throwaway worktree afterwards and paste `git worktree list` showing it gone.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the `git diff` of `tests/conformance_matrix.py` showing exactly the seven `91pjax` entries removed, the count comment corrected and the two `eeiytw` entries untouched. Paste `python3 -c "from tests.test_agent_surface_conformance import MUTATION_UNIVERSE; print(len(MUTATION_UNIVERSE))"` showing 31 (or the E-01-adjusted number with the reason), and the `-k mutation` run of `tests/test_agent_surface_conformance.py` showing all seven leaf ids PASSED. Paste `grep -rn 91pjax tests/` showing no remaining citation.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the `git diff` of `CHANGELOG.md` and `docs/cli-output-contract.md`, and a search of the added lines for the em dash and en dash characters returning nothing. Paste `aw sanitize --agent` output over the changed files showing a pass, and the bare `python3 -m pytest` final summary line with the failure set (empty, or each failure shown to reproduce at the unmodified HEAD).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the files this plan declares, through `aw commit <plan> -- <paths>`. Never use `git add -A` or `-a`, and never push (`AGENTS.md`). Check the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`. When you report tests, paste the ACTUAL runner output. A claimed pass with no transcript does not satisfy any `V-*` item.

SCOPE FENCE. The declared `- Scope-Paths:` are nine files. No `.spec.md` is declared, because no spec describes this path (see Spec / documentation sync). The fence is a DECLARATION, not a stop condition: an out-of-scope edit that turns out to be genuinely necessary is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). `agent_workflows/ipd_authoring.py` is deliberately NOT in scope: its stdout `print` belongs to `mmpjti`.

THE LIKELIEST SILENT ERRORS are (1) emitting the record for a HUMAN invocation, which duplicates the diagnostic onto stdout and breaks pipe-clean callers (V-03's human run and V-02's HUMAN case catch it), (2) reading a `--agent` token that sits after a bare `--` on a forwarding command as a mode request (E-05 case 5 catches it), and (3) capturing the argv per parser instead of per invocation, which silently misses `aw --agent <leaf>` and, below Python 3.13, every `+`-positional leaf (E-05 case 8 catches the first; the interpreter note in E-05 covers the second).

POST-GATE LIFECYCLE. Execution requires explicit human approval. `- Status:` is `to-review`, and this plan has no `- Readiness:` because `/plan-review` writes that field, not the author (`AGENTS.md`). The terminal transition is never a hand-rolled `git mv`. Under `aw oc run` or `aw agy run`, the RUNNER owns finalize. The executor makes sure every `V-*` has pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, then leaves the transition to the runner. When executed by hand with no runner, the executor performs the transition through `aw ipd finalize` (per the `ipd-lifecycle` workflow), and only after that same lint and evidence bar is met. Backlog item `91pjax` is ALREADY `graduated` (it lives under `.aw/records/backlog/graduated/`); this plan inherits its `- Blocks-Release: next` gate, and the item closes `done` only through the normal handoff once this plan is `executed`. The executor must not set it `done` by hand.
