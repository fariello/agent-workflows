# IPD: Honor the shared --fields flag in parser usage refusals under --agent

- Date: 2026-10-14
- Kind: child
- Concern: When `argparse` refuses an invocation before `parse_args` returns (such as missing required arguments on `ipd scaffold`, `research new`, `research new-comparison`, and `storage move`, or across any of the 67 required-argument CLI leaves, `invalid choice` subcommands, unknown top-level commands, or unrecognized options), `cli._AwArgumentParser.error` constructs `OutputContext(mode=OutputMode.AGENT)` without extracting `--fields` from `_RAW_DISPATCH_ARGV`, so `renderers.emit_usage_refusal` emits an unprojected `aw.agent/v1` `cannot-run` record carrying `"findings": 0` even when `--fields cmd` was requested. The four mutation leaves that hit `_AwArgumentParser.error` during the `tests/test_shared_flag_honored.py` sweep are currently xfailed in `KNOWN_BROKEN` citing `4y614a`.
- Scope: Add `cli._sniff_fields_from_raw_argv` next to `cli._sniff_mode_from_raw_argv` and pass `fields=_sniff_fields_from_raw_argv(raw_argv)` into `OutputContext(mode=OutputMode.AGENT, ...)` inside `cli._AwArgumentParser.error`, while keeping `OutputMode.JSON` unprojected. Remove the four `(leaf, "--fields"): "4y614a"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN` (making `test_known_broken_citations_resolve` tolerate an empty `KNOWN_BROKEN` once sibling items `aws1tg` and `jfdk7p` also land), and add behavioral regression coverage in `tests/test_shared_flag_honored.py` covering all 67 required-argument leaves, presence/absence non-vacuity, global-flag position, `--fields=`, repeated `--fields` last-flag-wins, bare `--` boundary, missing `--fields` value, unknown-command/`invalid choice`/unrecognized-option refusals, and `--json --fields` non-projection. EXCLUDES the nine handler-level `--fields` bypasses owned by `aws1tg` (`83ns86`) and the five `--json` parseability failures owned by `jfdk7p` (`pirm70`).
- Scope-Paths: agent_workflows/cli.py, tests/test_shared_flag_honored.py, .aw/records/plans/pending/20261014-4y614a-01-ksmdcd-honor-the-shared-fields-flag-in-parser-usage-refusals-under.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 4y614a
- Blocks-Release: next
- Set: 4y614a
- Order: 1
- Highest E allocated: 04
- Author: agy/gemini-4-argon-high
- Id: ksmdcd

## Workflow history
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed; readiness GO - PENDING HUMAN APPROVAL

- 2026-10-14 to-review (agy/gemini-4-argon-high): Authored review-ready child IPD from backlog item 4y614a.

## Goal

Make `cli._AwArgumentParser.error` honor `--fields` projection under `--agent` on every parse-time usage refusal as promised by `docs/cli-output-contract.md` Sections 6 and 11.4, and retire the four `"4y614a"` ceiling entries from `tests/test_shared_flag_honored.KNOWN_BROKEN` so CI gates projection across all parse-time usage refusals directly.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-derive baseline and wire `--fields` sniffing into `_AwArgumentParser.error`

- [ ] E-01 Re-derive at execution HEAD the baseline `--agent --fields cmd` behavior across the four `4y614a` leaves and all 67 required-argument leaves in `tests.test_usage_refusal_agent_record.REQUIRED_LEAVES`, and verify the target code sites in `agent_workflows/cli.py` and `tests/test_shared_flag_honored.py` against Findings F-01 through F-04.
  - Depends on: none
  - Expected outcome: Execution HEAD sha is recorded; running `tests.test_usage_refusal_agent_record._capture_cli` with `["--agent", "--fields", "cmd"]` across the four `4y614a` leaves (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`) and all 67 `REQUIRED_LEAVES` confirms `rc=2` with unrequested `['findings']` outside `agent_schema._PRESERVED_FIELDS | {"cmd"}`; `python3 -m pytest -o addopts="" -rx tests/test_shared_flag_honored.py -k "fields and mutation"` confirms the four `4y614a` cases report `XFAIL`; and F-01..F-04 are marked CONFIRMED or CORRECTED.
  - Execution state: pending

- [ ] E-02 Add `cli._sniff_fields_from_raw_argv` in `agent_workflows/cli.py` and pass `fields=_sniff_fields_from_raw_argv(raw_argv)` into `OutputContext(mode=OutputMode.AGENT, ...)` inside `cli._AwArgumentParser.error`.
  - Depends on: E-01
  - Expected outcome: `cli._sniff_fields_from_raw_argv(raw_argv: List[str]) -> Optional[List[str]]` (placed immediately below `cli._sniff_mode_from_raw_argv`) truncates `raw_argv` at the first bare `"--"` token, scans left-to-right so repeated `--fields` flags obey `argparse`'s last-flag-wins `store` semantics (capturing `tokens[i + 1]` when `tok == "--fields"` and `i + 1 < len(tokens)` and `not tokens[i + 1].startswith("-")`, or capturing `tok[len("--fields=") :]` when `tok.startswith("--fields=")`), splits on `","` via `[f.strip() for f in raw_fields.split(",") if f.strip()]` matching `result_types.select_output`, and returns `fields_val or None`. `cli._AwArgumentParser.error` constructs `OutputContext(mode=OutputMode.AGENT, fields=_sniff_fields_from_raw_argv(raw_argv))` so `renderers.emit_usage_refusal` projects `cannot-run` records through `agent_schema.filter_record_fields` while `OutputMode.JSON` remains unprojected.
  - Execution state: pending

### Task group 2: Retire the `4y614a` `KNOWN_BROKEN` entries, add behavioral coverage, and verify sensitivity

- [ ] E-03 Remove the four `(leaf, "--fields"): "4y614a"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN` and update `test_known_broken_citations_resolve` to allow an empty `KNOWN_BROKEN` ceiling.
  - Depends on: E-02
  - Expected outcome: `("ipd scaffold", "--fields"): "4y614a"`, `("research new", "--fields"): "4y614a"`, `("research new-comparison", "--fields"): "4y614a"`, and `("storage move", "--fields"): "4y614a"` are removed from `KNOWN_BROKEN` in `tests/test_shared_flag_honored.py` (leaving any remaining `jfdk7p` and `aws1tg` entries untouched), `assert seen_citations` is removed from `test_known_broken_citations_resolve` so `KNOWN_BROKEN` can become empty once all three sibling items (`aws1tg`, `jfdk7p`, `4y614a`) have landed, and all four `4y614a` leaves pass directly in `test_fields_flag_honored_mutation`.
  - Execution state: pending

- [ ] E-04 Add behavioral regression tests in `tests/test_shared_flag_honored.py` covering `--fields` projection across all 67 required-argument leaves and `_AwArgumentParser.error` edge cases, prove mutation sensitivity with a restoring `try/finally` wrapper, and run the bare `python3 -m pytest` suite.
  - Depends on: E-03
  - Expected outcome: New tests in `tests/test_shared_flag_honored.py` verify (a) all 67 canonical required-argument leaves in `tests.test_usage_refusal_agent_record.REQUIRED_LEAVES` driven in-process via `_capture_cli(leaf.split() + ["--agent", "--fields", "cmd"])` exit `2`, pass `agent_schema.validate_agent_record`, and emit no keys outside `agent_schema._PRESERVED_FIELDS | {"cmd"}` (`"findings"` absent); (b) non-vacuous presence/absence across the four `4y614a` leaves (`--agent` without `--fields` includes `"findings": 0`, `--agent --fields cmd` omits `"findings"`, and `--agent --fields cmd,findings` and `--fields=cmd,findings` retain `"findings": 0`); and (c) parser usage-refusal `--fields` edge cases: global flags before the leaf (`["--agent", "--fields", "cmd", "ipd", "scaffold"]` and `["--agent", "--fields=cmd", "ipd", "set"]`), repeated `--fields` obeying last-flag-wins, bare `--` boundary (`["ipd", "scaffold", "--agent", "--", "--fields", "cmd"]` retains `"findings"`), missing `--fields` argument safety (`["ipd", "scaffold", "--agent", "--fields"]` and `["ipd", "scaffold", "--fields", "--agent"]` exit `2` with a valid `cannot-run` record and do not treat `"--agent"` as a field name), other `_AwArgumentParser.error` refusal classes (`["nosuch", "--agent", "--fields", "cmd"]`, `["ipd", "nosuch", "--agent", "--fields", "cmd"]`, and `["status", "--nosuchflag", "--agent", "--fields", "cmd"]` all omit `"findings"`), and unprojected `--json --fields cmd` (`["ipd", "scaffold", "--json", "--fields", "cmd"]`: stdout is ONE pretty-printed multi-line JSON object, so parse the WHOLE stdout with `json.loads(out)` rather than the last line, and assert it still carries the full payload keys `summary`, `diagnostics`, `next_actions` and `data`, as measured at review). For the repeated-flag case assert BOTH orders: `--fields cmd,findings --fields cmd` omits `"findings"` and `--fields cmd --fields cmd,findings` retains it, so last-flag-wins is proven in both directions. Each new test drives `cli.main` in-process via `_capture_cli` and parses the LAST non-empty stdout line as the `aw.agent/v1` record, passing it through `agent_schema.validate_agent_record`. Temporarily replacing `fields=_sniff_fields_from_raw_argv(raw_argv)` with `fields=None` in `agent_workflows/cli.py` (an on-disk edit inside a restoring `try/finally` wrapper, so the `run_cli` subprocess sweep sees it too) causes the new 67-leaf sweep, the projection edge cases, and the four retired `test_fields_flag_honored_mutation` cases to FAIL, while the presence-side cases (no `--fields`, `--fields cmd,findings`, bare `--`, missing `--fields` value) still pass; restoring it matches the pre-mutation `sha256` and passes, and the bare `python3 -m pytest` suite passes. The mutation is never committed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16: tests must exercise real code and assert observable outcomes (parsed stdout records, exit codes, and both presence without `--fields` and absence with `--fields` so a vacuous projection cannot pass), never inspecting source text via `ast`, `inspect`, or regex.
- `docs/cli-output-contract.md` Section 6 specifies that `--fields <list>` projects `aw.agent/v1` records down to requested fields while preserving `agent_schema._PRESERVED_FIELDS` (`schema, kind, cmd, exit, outcome, complete, verified, applied, total, emitted, omitted, next`). `--fields` scopes to `--agent` output; `--json` emits full unprojected payloads.
- `docs/cli-output-contract.md` Section 11.4 and executed IPD `0z7ds3` (`91pjax`) establish that parse-time usage refusals in `cli._AwArgumentParser.error` inspect `_RAW_DISPATCH_ARGV` (set in `cli._dispatch`) and call `renderers.emit_usage_refusal(cmd=cmd, message=message, next_cmd=next_cmd, context=ctx)`, which builds a `CommandResult(status="cannot-run", exit_code=2, ...)` and delegates to `get_renderer(ctx).emit(res, ctx)` -> `CommandResult.to_agent_record(ctx)`.
- `tests/test_shared_flag_honored.KNOWN_BROKEN` is a strict-xfail (`pytest.mark.xfail(strict=True)`) ceiling: fixing any of the four `4y614a` leaves without removing its `(leaf, "--fields"): "4y614a"` entry turns the test suite red with `XPASS(strict)`.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | All four `4y614a` leaves (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`) and all 67 required-argument leaves in `tests.test_usage_refusal_agent_record.REQUIRED_LEAVES` reproduce at authoring HEAD `6160fea94778f3fef827495ae25c735a10f5cbc1`, emitting unrequested `['findings']` (`"findings": 0`) under `--agent --fields cmd`. | Running `tests.test_usage_refusal_agent_record._capture_cli(leaf.split() + ["--agent", "--fields", "cmd"])` across the four `4y614a` leaves and all 67 `REQUIRED_LEAVES` returns `rc=2` with `extra=['findings']` on all 67 leaves (`Total REQUIRED_LEAVES: 67, unhonored: 67`). | Re-measured at review (lane HEAD): 67/67 unhonored, 0 non-refusing; a simulated fix (sniffed `fields` injected into the AGENT `OutputContext`) made 0/67 unhonored with every record passing `agent_schema.validate_agent_record`, and every E-04 edge case behaved as the plan states. The defect is CLI-wide across `cli._AwArgumentParser.error` and not specific to the four leaves whose `RUNNABLE_ARGV` happens to omit required arguments in `tests/test_shared_flag_honored.py`. |
| F-02 | `cli._AwArgumentParser.error` constructs `OutputContext(mode=OutputMode.AGENT)` with `fields=None` because `parse_args` has not returned `args` when `error()` fires, and `_sniff_mode_from_raw_argv` only sniffs the output mode (`AGENT` vs `JSON`). | In `agent_workflows/cli.py` (`_AwArgumentParser.error`, lines 829-852), `raw_argv = _RAW_DISPATCH_ARGV.get()` is passed to `_sniff_mode_from_raw_argv(raw_argv)` and then `ctx = OutputContext(mode=OutputMode.AGENT)` is passed to `renderers.emit_usage_refusal`. `CommandResult.to_agent_record(ctx)` in `agent_workflows/result_types.py` (lines 436 and 495-496) unconditionally sets `rec["findings"] = int(findings_count)` (`0`) and only strips unrequested fields when `context is not None and context.fields` is truthy. | Adding `_sniff_fields_from_raw_argv(raw_argv)` and passing `fields=_sniff_fields_from_raw_argv(raw_argv)` into `OutputContext(mode=OutputMode.AGENT, ...)` inside `_AwArgumentParser.error` fixes all 67 required-argument leaves plus `invalid choice`, unknown-command, and unrecognized-option refusals at the single parse-time seam. |
| F-03 | The three handler-level missing-required leaves wired in `0z7ds3` (`backlog new`, `specs new`, `prompts new`) already honor `--fields` because `parse_args` succeeds before their handlers call `ctx = select_output(args)` and pass `ctx` to `emit_usage_refusal`. | Probing `_capture_cli(leaf.split() + ["--agent", "--fields", "cmd"])` on `backlog new`, `specs new`, and `prompts new` at HEAD `6160fea94778f3fef827495ae25c735a10f5cbc1` shows `without_fields_has_findings=True, with_fields_has_findings=False, extra=[]` for all three. | No changes to `backlog.py`, `specs.py`, or `prompts.py` are needed for `4y614a` (and avoids overlapping sibling pending IPD `xvv7n4` for `mmpjti`). |
| F-04 | `tests/test_shared_flag_honored.KNOWN_BROKEN` holds entries for three sibling backlog items (`jfdk7p`, `aws1tg`, `4y614a`), and `test_known_broken_citations_resolve` currently asserts `assert seen_citations`. | In `tests/test_shared_flag_honored.py` (lines 54-76 and 374-384), `KNOWN_BROKEN` maps 5 `--json` entries to `"jfdk7p"` (pending IPD `pirm70`), 9 `--fields` entries to `"aws1tg"` (pending IPD `83ns86`), and 4 `--fields` entries to `"4y614a"`. Whichever of the three sibling plans executes last will empty `KNOWN_BROKEN`. | E-03 removes the four `"4y614a"` entries and drops `assert seen_citations` in `test_known_broken_citations_resolve` (matching `83ns86` and `pirm70`) so an empty `KNOWN_BROKEN` ceiling is valid regardless of merge order. |

## Proposed changes (ordered, validatable)

1. Re-measure the four `4y614a` leaves and all 67 `REQUIRED_LEAVES` under `--agent --fields cmd` and confirm F-01..F-04 at execution HEAD (E-01).
2. Add `cli._sniff_fields_from_raw_argv(raw_argv: List[str]) -> Optional[List[str]]` in `agent_workflows/cli.py` and pass `fields=_sniff_fields_from_raw_argv(raw_argv)` into `OutputContext(mode=OutputMode.AGENT, ...)` inside `cli._AwArgumentParser.error` (E-02).
3. Remove the four `"4y614a"` entries from `tests/test_shared_flag_honored.KNOWN_BROKEN` and allow an empty `KNOWN_BROKEN` in `test_known_broken_citations_resolve` (E-03).
4. Add behavioral regression tests in `tests/test_shared_flag_honored.py` covering all 67 required-argument leaves and `--fields` sniffing edge cases, prove mutation sensitivity with a restoring wrapper, and run the bare test suite (E-04).

## Deferred / out of scope (with reason)

- THE NINE HANDLER-LEVEL LEAVES THAT IGNORE `--fields` UNDER `--agent` (`ipd coverage`, `partition`, `oc update-models`, `storage reattach`, `upgrade-test env`, `list`, `probe`, `sandboxes`, `clean`). Separate handler-level bypass mechanisms owned by backlog item `aws1tg` and pending IPD `83ns86`.
  - Carrier: aws1tg
- THE FIVE LEAVES THAT FAIL `json.loads` UNDER `--json` (`config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, `upgrade-test clean`). Separate `--json` defect population owned by backlog item `jfdk7p` and pending IPD `pirm70`.
  - Carrier: jfdk7p

## Scope check

- Over-scope: none. Only `agent_workflows/cli.py`, `tests/test_shared_flag_honored.py`, and this plan file are touched. Putting the 67-leaf required-argument `--fields` sweep and edge-case tests in `tests/test_shared_flag_honored.py` (importing `_capture_cli` and `REQUIRED_LEAVES` from `tests.test_usage_refusal_agent_record` without editing `tests/test_usage_refusal_agent_record.py`) keeps the scope minimal and avoids any file overlap with pending IPD `xvv7n4` (`mmpjti`).
- Under-scope: none. Fixing `_AwArgumentParser.error` in `agent_workflows/cli.py` repairs not only the four mutation leaves caught by `test_fields_flag_honored_mutation` (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`), but all 67 required-argument leaves and every other parse-time usage refusal (`invalid choice`, unknown top-level command, unrecognized option).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_shared_flag_honored.py tests/test_usage_refusal_agent_record.py` passing with all four `"4y614a"` entries removed from `KNOWN_BROKEN` (zero `4y614a` xfails remaining) and all new 67-leaf and edge-case `--fields` regression tests passing (E-03, E-04).
- Direct behavioral verification of both presence (under `--agent` without `--fields`, and under `--agent --fields cmd,findings`) and absence (under `--agent --fields cmd`) of `"findings"` across `ipd scaffold`, `research new`, `research new-comparison`, and `storage move`, plus global-flag position (`--agent --fields cmd ipd scaffold`), `--fields=`, repeated `--fields` last-flag-wins, bare `--` boundary, missing `--fields` argument safety, and unprojected `--json --fields cmd` (E-02, E-04).
- Mutation-sensitivity proof using a restoring `try/finally` wrapper showing `tests/test_shared_flag_honored.py` fails when `fields=_sniff_fields_from_raw_argv(raw_argv)` in `cli._AwArgumentParser.error` is reverted and passes after restoration with matching before/after `sha256` (E-04).
- Full fast test suite run BARE via `python3 -m pytest` with the `N passed` summary pasted (E-04).

## Spec / documentation sync

N/A with reason: no `.spec.md` or user-facing documentation file is modified. `docs/cli-output-contract.md` Sections 1.3, 6, and 11.4 already specify that `--fields` projects `aw.agent/v1` records down to the requested fields plus `agent_schema._PRESERVED_FIELDS` and that parse-time usage refusals emit `aw.agent/v1` `cannot-run` records under `--agent`; this plan brings `_AwArgumentParser.error` into compliance with the existing documented contract.

## Open questions

### OQ-01: How should `cli._AwArgumentParser.error` behave when `--fields` itself is missing its argument or followed immediately by another flag (e.g. `aw ipd scaffold --agent --fields` or `aw ipd scaffold --fields --agent`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE. When `--fields` is passed at the end of argv with no value (`aw ipd scaffold --agent --fields`) or immediately before another option (`aw ipd scaffold --fields --agent`), `argparse` raises `error("argument --fields: expected one argument")`. In `_sniff_fields_from_raw_argv`, requiring `i + 1 < len(tokens) and not tokens[i + 1].startswith("-")` for the two-token `--fields <val>` form ensures that a trailing `--fields` or `--fields --agent` resolves `fields` to `None` rather than indexing past `tokens` or treating `"--agent"` as a requested field name, so `_AwArgumentParser.error` still emits a valid unprojected `cannot-run` error record for the malformed `--fields` invocation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: The execution HEAD sha; pasted output of running the four `4y614a` leaves (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`) and the 67-leaf `REQUIRED_LEAVES` sweep through `tests.test_usage_refusal_agent_record._capture_cli` with `["--agent", "--fields", "cmd"]` prior to the fix showing `rc=2` and unrequested `['findings']` on all 67; pasted `python3 -m pytest -o addopts="" -rx tests/test_shared_flag_honored.py -k "fields and mutation"` output showing the four `4y614a` cases as `XFAIL`; and an explicit CONFIRMED or CORRECTED mark for each of F-01..F-04.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Diff or excerpt of `agent_workflows/cli.py` showing `_sniff_fields_from_raw_argv` and `OutputContext(mode=OutputMode.AGENT, fields=_sniff_fields_from_raw_argv(raw_argv))` in `_AwArgumentParser.error`; plus pasted output from `cli.main` / `_capture_cli` showing that across `ipd scaffold`, `research new`, `research new-comparison`, and `storage move`: `--agent --fields cmd` emits only preserved envelope keys (`"findings"` absent), `--agent --fields cmd,findings` and `--agent --fields=cmd,findings` retain `"findings": 0`, `--agent` without `--fields` includes `"findings": 0`, `--agent --fields cmd` placed before the leaf (`aw --agent --fields cmd ipd scaffold`) omits `"findings"`, `--fields` after bare `--` (`aw ipd scaffold --agent -- --fields cmd`) is ignored, and `--json --fields cmd` remains unprojected.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Diff or excerpt of `tests/test_shared_flag_honored.py` showing removal of the four `"4y614a"` entries from `KNOWN_BROKEN` and removal of `assert seen_citations` in `test_known_broken_citations_resolve`; plus pasted `python3 -m pytest -o addopts="" -v tests/test_shared_flag_honored.py -k "(fields and mutation and (scaffold or research or move)) or known_broken"` output (parametrize ids contain spaces, e.g. `test_fields_flag_honored_mutation[ipd scaffold]`, so the underscore form selects none of them; measured at review) confirming all four `4y614a` leaves and the ceiling tests pass directly without xfail.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Diff or excerpt of `tests/test_shared_flag_honored.py` showing the new 67-leaf required-argument `--fields` sweep and `_AwArgumentParser.error` edge-case regression tests; pasted `python3 -m pytest -o addopts="" tests/test_shared_flag_honored.py tests/test_usage_refusal_agent_record.py` output showing all tests passing; pasted output of the restoring-wrapper mutation check showing a reverted fix causes the projection-side tests named in E-04 to FAIL while the presence-side cases pass and restoration produces the exact pre-mutation `sha256`; and pasted output of the bare full fast suite `python3 -m pytest` showing the `N passed` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (standing rules from `AGENTS.md` and `.aw/records/plans/README.md`):
1. All open questions are RESOLVED (OQ-01 is resolved above).
2. Scope fence: touch only the files declared in `Scope-Paths` (`agent_workflows/cli.py`, `tests/test_shared_flag_honored.py`, and this plan file). Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize.
3. Honesty rule (HARD MUST): when reporting tests or validation passed, paste the ACTUAL runner output into each `V-*` item's `Observed evidence:`; never claim success you did not run. Run the full suite bare as `python3 -m pytest`.
4. Commit only the files changed for this plan, path-scoped via `aw commit ksmdcd -- <paths>`, never `git add -A`/`-a`, and never push.
5. Begin with `aw ipd begin ksmdcd` after human approval (`aw ipd set approved ksmdcd --by-human`). Verify the staged set with `git diff --cached --name-only` before every commit; never tag.
6. Lifecycle: under `aw oc run` / `aw agy run` the RUNNER performs finalize after its merge-and-revalidate gate, so do not run it yourself. When executing by hand, once every `E-*` is `performed`, every `V-*` is `pass`, and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize ksmdcd --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv`.
7. STOP only for a genuinely unsafe condition: a concurrent edit to `tests/test_shared_flag_honored.py` (sibling plans `83ns86` and `pirm70` edit the same `KNOWN_BROKEN` dict and `test_known_broken_citations_resolve`) that cannot be safely combined; otherwise merge with whichever sibling landed first and keep its removals.
