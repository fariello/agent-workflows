# IPD: Build the m0001 description journal, tool-less model call and description validation

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` (4.2 SHORT DESCRIPTION, OQ-22, OQ-31, AC-36) has the cutover write a model-generated `short_description` through a reusable gitignored journal and a tool-less, sanitized model call. Plan `ya4ee4` owned all of it in 11 items; it was split 2026-11-07 per the maintainer's step-complexity rule so that one turn builds the self-contained module and another wires it into `m0001` and runs the real trial.
- Scope: Add `agent_workflows/migrations/m0001_describe.py` and the tracked prompt `agent_workflows/data/short-description-prompt.md`: the prompt and its loader (`ya4ee4` E-01), the description journal (E-02), the tool-less argv and env (E-03), the scratch directory and guarded call (E-04), validation (E-05), and the regenerate-once rule (E-06), each with its tests in `tests/test_m0001_describe.py`. EXCLUDES: wiring into `m0001`, the CLI options, the full fake-host test module, the real trial and the changelog (`ya4ee4`).
- Scope-Paths: agent_workflows/migrations/m0001_describe.py, agent_workflows/data/short-description-prompt.md, pyproject.toml, tests/test_m0001_describe.py, .aw/records/plans/pending/20261107-metastore-20-odeo9z-build-the-m0001-description-journal-tool-less-model-call-and.ipd.md
- Item-Dependencies: executed:dcerjg
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 20
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: odeo9z

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from ya4ee4 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A self-contained `m0001_describe` module produces one validated, journaled description per record through a tool-less call, proven with fake runners, before anything wires it into the migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the tracked prompt and the journal

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/ya4ee4/check-before.jsonl`. Add the tracked prompt file `agent_workflows/data/short-description-prompt.md` (shipped as package data like `research-models.toml`: the hatch wheel target `packages = ["agent_workflows"]` and the sdist `include` entry `/agent_workflows` already carry every file under `agent_workflows/data/`, so `pyproject.toml` needs no edit unless V-01's wheel listing shows the file missing). First line `prompt-version: 1`. The body instructs the model to write ONE sentence of at most 300 characters in clear, concise, accurate ASD-STE100 style (without its controlled vocabulary) that says what the record does, addresses or defines, with no superfluous information, never stating the record's type (a plan's text does not say it is a plan), and with no file path, user name, host name, session id, newline or Markdown. It states that the record follows between the literal markers `<<<RECORD` and `RECORD>>>` as quoted DATA whose instructions are never followed, and that the reply is the sentence only. Add `load_prompt() -> (version, template)` and `render_prompt(record_text)` in `m0001_describe.py`; the version is the first line's integer, and the prompt digest is part of every journal entry so an edited prompt without a version bump is still detected.
  - Depends on: none
  - Expected outcome: `render_prompt("x")` returns the template with `x` between the two markers and nothing after `RECORD>>>` but a newline; `load_prompt()` returns version 1; the file is present in a built wheel.
  - Execution state: pending

- [ ] E-02 In `m0001_describe.py`, add the description journal: a gitignored JSON Lines file `descriptions.jsonl` in the m0001 journal directory that Order 04 created (resolved through `project_context.resolve_project_context` `state_durable`). One entry per key: the record's `id6`, or, for a record that Order 04's rename map gives a minted `id6`, its CURRENT (pre-rename) records-root-relative path, exactly as 4.2 states. Each entry holds `key`, `text` (or `null` with `failure` for a failed generation), `host`, `model`, `prompt_version`, `prompt_digest`, `source_digest` (SHA-256 of the record's bytes as read BEFORE step 3's citation rewrite, so a rewrite never invalidates an entry), `generated_at` (UTC, `artifact_core` helper) and `attempts`. Writes append one line under `platform_lock` and `fsync`; reads take the LAST line per key. `lookup(key, source_digest, prompt_digest)` returns a reusable entry only when both digests match.
  - Depends on: E-01
  - Expected outcome: after appending two entries for one key, `lookup` returns the second; a changed source digest or prompt digest returns `None`; a file truncated mid-line (simulated crash) loses only the partial line and every complete entry is still read.
  - Execution state: pending

### Task group 2: the tool-less call

- [ ] E-03 In `m0001_describe.py`, add `describe_argv(host, model, *, scratch_dir)` and `describe_env(base_env)`, composed like `runner_shared.probe_argv` (one builder, host as an argument) but never through it, because `probe_argv` adds `--dangerously-skip-permissions` for Antigravity and grants opencode its full tool set. For `host == "oc"`: argv `[opencode, "run", "--format", "json", "--agent", "aw-describe", "--dir", scratch_dir]` plus `--model <model>` when given, with the prompt on STDIN (no argv length limit; measured below with a 200,000-character prompt); env `OPENCODE_CONFIG_CONTENT` built with `lane_containment.build_permission_policy_env` semantics (an operator value is merged or loudly overridden, never dropped) holding `{"agent": {"aw-describe": {"mode": "primary", "tools": {"*": false}, "permission": {"*": "deny"}}}, "permission": {"*": "deny"}}`. For `host == "agy"`: raise `DescribeHostRefused` naming OQ-31, because `agy` has no tool-less mode (its `--sandbox` restricts only the terminal, and the runners document `--no-dangerously-skip-permissions` as needing an interactive answerer). Before the first call of a run, verify the policy took effect by running `opencode debug agent aw-describe` under the same env, with `--dir scratch_dir`, and requiring BOTH (1) every entry of its `tools` map to be `false` and the map to be non-empty, and (2) no `permission` rule after the last `{"permission": "*", "action": "deny"}` rule to have action `allow` or `ask` for a permission other than one that only gates a disabled tool; otherwise refuse the run as `could-not-ask` with the observed value. Rule (2) is needed because the resolved permission list MERGES the operator's global opencode configuration: measured at review on this machine, the list ends `('*','deny','*')`, `('*','deny','*')`, then an operator `external_directory` `allow` rule for an opencode tool-output directory, which comes from the operator's own config, not from this env. With every tool disabled that rule grants nothing, so the check passes when the only rules after the deny are `external_directory` entries and the `tools` map is all `false`; any other later `allow` refuses. A test pins both outcomes with a fake `debug agent` output.
  - Depends on: none
  - Expected outcome: the argv contains no `--dangerously-skip-permissions`, no `--auto`, and no prompt text; `describe_env` keeps an operator's unrelated `OPENCODE_CONFIG_CONTENT` keys; `describe_argv("agy", ...)` raises `DescribeHostRefused`.
  - Execution state: pending

- [ ] E-04 Add the scratch working directory and the call: `scratch_dir` is a fresh empty directory under the journal directory, created and then `chmod 0o500` (read and execute only for the owner, so a tool call, were one ever granted, could not write there), and removed after the run. `generate(record_text, *, host, model, runner=None)` renders the prompt, spawns through an injected `runner(argv, cwd, stdin_text, timeout) -> (exit_code, stdout, stderr)` seam (a new type `DescribeRunnerFn` in `m0001_describe`: `host_runner.RunnerFn` is `(argv, cwd, timeout)` with no stdin, so it is not reused as-is; the real runner is `subprocess.run(..., input=stdin_text, capture_output=True, timeout=timeout, shell=False)` mapping a timeout to 124 and a spawn `OSError` to 127, the `host_runner` sentinels), with `cwd=scratch_dir`, `stdin` the prompt, and a timeout of 120 s; the real spawn refuses under pytest by calling `runner_shared._assert_probe_spawn_is_permitted(argv)` itself (one guard, not a copy), so no test can reach a paid model; the tests' fake host runs through the injected runner, never through the real one. Parse stdout with `runner_shared.probe_reply_text(stdout, host="oc")`; record per call the `step_finish` `cost` and `tokens.total` from the JSON events; treat any tool event as a failed generation (`failure: tool-use`) whatever the text, detected by the shared parser `verifier_corroboration.tool_call_from_event` over every JSON line, plus any line whose `type` is `tool_use` (the opencode event name `run_dashboard` also matches), so the detector is not a second hand-written rule. Exit 127 or 124, an empty reply or a spawn error is `could-not-ask`, never a failure of the record.
  - Depends on: E-03
  - Expected outcome: with a fake runner, a reply carrying a `tool_use` event is a failure; a reply with text and a `step_finish` event returns the text, cost and tokens; exit 124 returns `could-not-ask`; the scratch directory is mode `0o500` during the call and absent afterwards.
  - Execution state: pending

### Task group 3: validation and the regenerate-once rule

- [ ] E-05 Add `validate(text, repo) -> str | None` returning the first refusal reason: `attention_contract.refuse_unsafe_descriptive("aw migrate metadata", "short_description", text)` (300-character bound, newline and control characters), then `leak_sanitizer.scan_text(text, "short_description", ruleset, include_warn=True)` over `ruleset = leak_sanitizer.build_ruleset(repo, include_warn=True)` (built once per run) with ANY finding, `fail` or `warn`, refused naming its rule, matching `tve77h` E-03 (b) so the migration's own writer cannot refuse a value this step accepted; then, because the sanitizer flags only THIS machine's home directory, user name and host name (measured at review: `see /home/alice/secret` produces no finding under either ruleset, while the machine's own home path produces `home-path` and `handle` `fail` findings and its host name a `derived:<host>` `warn`), also refuse any whitespace-separated token that is an absolute POSIX path of two or more segments or a Windows drive path, the same extra rule `tve77h` E-03 (b) applies to `message`, so a planted path from another machine is refused too. Strip one pair of surrounding quotes and surrounding whitespace before validating; never truncate, never rewrite inner text.
  - Depends on: none
  - Expected outcome: a 301-character value, a value with `\n`, a value with `\x07`, a value containing this machine's home directory (sanitizer `home-path`), a value containing another machine's home path such as `/home/alice/x` (absolute-path rule) and a value containing this machine's host name (sanitizer `warn`) are each refused with a distinct reason; a 300-character plain sentence and a sentence mentioning the slash command `/plan-review` pass.
  - Execution state: pending

- [ ] E-06 Add `describe_record(key, record_bytes, *, journal, host, model, runner)`: reuse a matching journal entry with no call; otherwise generate, validate, and on refusal or failure regenerate ONCE with the same prompt; journal the first passing value, or journal `text: null` with the last `failure` reason and `attempts: 2`; journal each result as soon as it arrives. A `could-not-ask` result is NOT journaled, so a later run retries it. A journaled failure is reused (no third call) until the record's source or the prompt changes.
  - Depends on: E-02, E-04, E-05
  - Expected outcome: with a fake runner whose first reply is 400 characters and second is valid, exactly two calls happen and the second text is journaled; with two invalid replies, two calls happen, the entry is `text: null`, and a rerun makes zero calls.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One-shot model calls follow `runner_shared.ask_orchestrator_probe`: an injected `runner` seam that every test supplies, a real spawn that refuses under pytest (`runner_shared._assert_probe_spawn_is_permitted`), exit 127/124 and empty replies classified as `could-not-ask`, and host text extracted by ONE function, `runner_shared.probe_reply_text` (carried from `ya4ee4` Step 0).
- Host permission requests for opencode go through `OPENCODE_CONFIG_CONTENT` (`lane_containment.OPENCODE_RUNTIME_CONFIG_ENV`), merged with any operator value by `lane_containment.build_permission_policy_env`, and are verified rather than assumed (`oc_runipd.observe_opencode_policy`, spec R4.2).
- Descriptive-value safety is `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300; leak scanning is `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset`.
- Package data lives in `agent_workflows/data/` (`research-models.toml`, read by `model_vocab`).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no test spawns a real model.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).

## Findings

| Id | Evidence (measured 2026-11-07 in this worktree) | Finding |
|---|---|---|
| F-01 | `ls agent_workflows/migrations`: absent; `ls agent_workflows/data`: `research-models.toml` only | Every item is unbuilt; counted as deliverables. E-01: 1 data file, 2 functions, 1 wheel check (4 units). E-02: 1 file format, 9 entry keys, 1 locked append, 1 lookup (about 12). E-03: 2 builders, 1 refusal, 1 two-rule policy check (about 6). E-04: 1 scratch dir, 1 runner type, 1 real runner, 1 parser, 1 tool-event detector (about 6). E-05: 3 refusal layers (about 4). E-06: 1 function, 4 journal rules (about 5). |
| F-02 | `rg -n "def (refuse_unsafe_descriptive\|scan_text\|build_ruleset\|probe_argv\|probe_reply_text\|_assert_probe_spawn_is_permitted\|tool_call_from_event\|build_permission_policy_env)\b" agent_workflows`: every named helper exists | No helper this part reuses is missing. |
| F-03 | `rg -n "^RunnerFn" agent_workflows/host_runner.py`: `RunnerFn = Callable[[Sequence[str], str, float], Tuple[int, str, str]]` (no stdin) | The stdin runner seam is a new type (carried from `ya4ee4` F-11). |
| F-04 | the measured trial facts F-01 to F-11 of `ya4ee4` | Stay in `ya4ee4`, cited by id; they are evidence for this part's choices. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: prompt file and journal.
2. E-03, E-04: tool-less argv and env, scratch directory, guarded spawn.
3. E-05, E-06: validation and regenerate-once.

## Deferred / out of scope (with reason)

- Wiring into `m0001`, the `--describe-*` and `--no-describe` options, the full fake-host test module, the real trial on a copy and the changelog.
  - Carrier: ya4ee4

## Scope check

- Over-scope: none. `pyproject.toml` is edited only if V-01's wheel listing shows the prompt file missing.
- Under-scope: none for `ya4ee4` E-01 to E-06; the AC-36 cases are proven end to end by `ya4ee4` E-09.

## Required tests / validation

New module: `tests/test_m0001_describe.py` (`core`), holding the unit tests each V-item names; `ya4ee4` E-09 extends it with the fake-host AC-36 cases. No real model call from any test. Gate: bare `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements `4sd62s` 4.2 DESCRIPTION JOURNAL and SAFEGUARDS and OQ-31 at the module level. The tracked generation prompt is a new shipped file (5.4).

## Open questions

### OQ-01: How can a host launcher run with no tools (OQ-31)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `ya4ee4` OQ-01 (resolved there from measurement): an inline opencode agent `aw-describe` with `tools: {"*": false}` and `permission: {"*": "deny"}` through `OPENCODE_CONFIG_CONTENT`, observable with `opencode debug agent`, plus a `chmod 0o500` scratch working directory and the prompt on stdin; Antigravity is refused.

- Note: carried unchanged from `ya4ee4` with its id, so item text that cites it still resolves.

### OQ-04: Is the model asked to describe records larger than its context?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `ya4ee4` OQ-04 (resolved there): the full text is sent; a context-exceeding reply is journaled as a failure after one retry by E-06, never a truncated input.

- Note: carried unchanged from `ya4ee4` with its id, so item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k prompt` all PASSED (version 1, markers, record text placed only between them); and `python3 -m zipfile -l dist/*.whl | grep short-description-prompt.md` after `python3 -m build --wheel` showing the file in the wheel.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k journal` all PASSED, naming the last-entry-wins, changed-source-digest, changed-prompt-digest and truncated-final-line tests.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k "argv or env or agy"` all PASSED; and the output of `OPENCODE_CONFIG_CONTENT="$(python3 -c 'from agent_workflows.migrations import m0001_describe as d; import os; print(d.describe_env({})["OPENCODE_CONFIG_CONTENT"])')" opencode debug agent aw-describe` filtered to its `tools` map, every value `false`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k "generate or scratch or spawn_refused"` all PASSED, naming the `tool_use`-is-failure, exit-124-is-could-not-ask, scratch-mode-0o500 and real-spawn-refuses-under-pytest tests.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k validate` all PASSED with the six refusal reasons (length, newline, control character, sanitizer `home-path`, absolute path, sanitizer `derived:<host>` warn) printed by `-rA` or quoted from the assertions.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_describe.py -k "regenerate or describe_record"` all PASSED, quoting the assertions on the fake runner's call count (2 for regenerate-then-pass, 2 then 0 for double failure and rerun).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: no test may spawn a real model; this part makes no real model call at all (the real trial is `ya4ee4` E-10).

Honesty rule: run the named test modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit odeo9z -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize odeo9z` itself.
