# IPD: Drive a plan review as a tiered sequence of prompts in one session on both hosts

- Date: 2026-10-24
- Kind: child
- Concern: Today a runner review is ONE host turn: `runner_shared.build_review_prompt` returns `/plan-review <path>` (plus a lane notice when isolated), `runner_shared.execute_item_core` spawns it once through `spawn_executor`, and `runner_shared.reconcile_disposition` checks only the final plan state. The runner cannot tell which checks ran (spec `k3yx72` Section 1 problem 3) and every plan gets the same review (problem 2). Spec `k3yx72` (approved) Sections 4 to 7 and 9 specify the replacement: a runner pre-pass, then the tier's prompts sent in order to ONE session, a postcondition checked after each prompt with one re-ask, a guard that keeps verdict outputs out of every prompt before S7 (MD-15), a structural preservation check around proofreading (Section 6.1), defined outcomes, and resume after the last completed prompt (Section 9.3). None of it exists. The pilot (Order 09) cannot run without it.
- Scope: Implement, in shared runner code so both hosts get it: the per-tier prompt lists and the `review_variant` grouping setting; the pre-pass; the prompt loop over one session using the existing same-session follow-up primitive `runner_shared.resume_via_launcher`; per-prompt postconditions with one re-ask; the verdict-output guard; the structural preservation check; the four outcomes; per-prompt run-state recording and resume; the children-before-orchestrator review ordering; and the Section 17.1 amendments to runner spec `25kzda`. The multi-prompt review is OPT-IN for this Stage (`--review-mode steps`; the default stays the current single `/plan-review` turn) so the pilot can compare the two on the same code (spec MD-19, MD-20). EXCLUDES the `AW-REVIEW` re-review loop (Order 05; until it lands, the sequence runs S6 once and treats its marker per Order 05's contract only when Order 05 is present, see E-06), the citation resolver (Order 03), the split step (Order 06), and the no-go clearing path (Order 05 Stage 2).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/review_sequence.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/run_dashboard.py, agent_workflows/run_dashboard_assets/dashboard.js, agent_workflows/run_analytics_attempts.py, docs/run-analytics.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, tests/test_review_sequence.py, tests/test_review_sequence_runner.py, tests/test_run_analytics_review_cost.py, CHANGELOG.md
- Item-Dependencies: executed:3bwrfx, executed:gv3smb
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 4
- Highest E allocated: 17
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: uiyoax

## Workflow history
- 2026-10-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uiyoax verified (set revsteps, attempt 1). [Scope reconciliation - widened-scope tests/test_run_analytics_review_cost.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); in-scope-unmodified agent_workflows/agy_runipd.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-25 approved (aw set): status set to approved
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261024-revsteps-04-uiyoax-drive-a-plan-review-as-a-tiered-sequence-of-prompts-in-one-s.review.md
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let `aw oc run` and `aw agy run` review a plan as the tier's sequence of step-file prompts in one session, with each check's completion verified by the runner and recorded per prompt, so the pilot can measure it against today's single-turn review.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the sequence model (pure, no host)

- [x] E-01 Create `agent_workflows/review_sequence.py` with the prompt lists of spec `k3yx72` Section 5.3 as data: `PROMPT_LISTS: dict[str, tuple[tuple[str, ...], ...]]` keyed by `simple`, `standard`, `complex:grouped-6`, `complex:single-12`, `orchestrator`, each a tuple of prompt groups of check names (`P`, `T`, `Q`, `R1` to `R7`, `S5`, `S6`, `S7`), and `CHECK_STEP_FILES` mapping each check name to its Order 01 step file under `.aw/system/workflows/plan-review/steps/` (`R3s` for the short security form). Add `prompt_plan(tier: str, variant: str, *, in_set: bool, quick_ok: bool) -> list[tuple[str, ...]]`, which returns the list for the tier, drops `R7` for a plan outside a Set (single-12 then has 12 prompts), and for `simple` merges prompt 2 into prompt 1 when `quick_ok` (spec Section 5.3 `simple` row). Add `raise_tier_plan(done: set[str], new_tier: str, variant: str, *, in_set: bool) -> list[tuple[str, ...]]`, which returns, for each group of the new tier's list before `S5`, only the checks not yet in `done`, dropping empty groups (Section 5.3 last paragraph; a tier is never lowered).
  - Depends on: none
  - Expected outcome: `prompt_plan("standard", "single-12", in_set=True, quick_ok=False)` returns 5 groups ending `("S7",)`; `complex` single-12 in a Set returns 13 groups and outside a Set 12; grouped-6 returns 7.
  - Execution state: performed

- [x] E-02 In `review_sequence.py`, add `render_prompt(groups_checks: tuple[str, ...], *, first: bool, plan_rel: str, facts_md: str | None, lane_notice: str | None, reask: str | None) -> str`. The prompt carries no slash command. It names the plan path and instructs "Read and apply, in order:" followed by `.aw/system/workflows/plan-review/steps/_kernel.md` (prompt 1 only), each check's step file, and `_findings.md` when the prompt contains `Q` or any `R*`; prompt 1 also carries the pre-pass block (`facts_md`, plus lint and coverage output). The lane notice and the `Required JSON outcome` line of `runner_shared.build_review_prompt` are appended exactly as that function does for an isolated review, so lane containment is unchanged. The re-ask text is the exact wording of spec Section 6: `Your last reply did not complete <check>: <the postcondition text that failed>. Complete it now and end your reply as the step file requires.`
  - Depends on: E-01
  - Expected outcome: rendered prompts name only step files that exist in the Order 01 tree; the re-ask wording matches spec Section 6 byte for byte.
  - Execution state: performed

- [x] E-03 In `review_sequence.py`, add the postcondition checks of spec Section 6 as pure functions over `(plan_text_before, plan_text_after, review_text, reply_text)` returning `None` on success or the failed postcondition text: `check_P` (the `### Proofreading` subsection exists in the current round, read with the last-round logic of `review_tier.parse_tier_answers`), `check_T` (`review_tier.parse_tier_marker` is not `None` and `review_tier.tier_answers_complete` is true), `check_steps` (each `Q`/`R*` check in the prompt has a `### Step <check>` subsection whose first non-blank line starts `- Checked:`), `check_S5` (every open question parsed by `ipd_lint.parse` has `Blocking:` and `Status:`, and `check.review-finding-unescalated` reports nothing for this review record, called through the `check_engine` rule function that `aw check` uses), and `check_S7` (Section 6 row S7 (a) or (b), exactly one new verdict-bearing history entry as counted by comparing `plan_readiness.newest_verdict` and the count of history lines containing a `plan_readiness.REVIEW_VERDICT_TOKENS` token before and after, and no new `aw ipd lint --phase author` error except `IPD-Q501`). Add `verdict_outputs(plan_text) -> tuple` returning `(read_readiness, Status value, newest_verdict raw entry)` for the MD-15 guard. Count verdict-bearing entries with `plan_readiness.is_review_history_entry` plus `plan_readiness.classify_verdict` returning a token, never by token substring alone: measured at review, a progress line `- <date> /plan-review pass 2 (<agent>): re-ran R2` IS a review record to `is_review_history_entry` (the `/plan-review` label) and makes `newest_verdict` return `(None, ...)`, hiding an older approving verdict, so progress lines must use a non-review label (for example `- <date> review progress (<agent>): ...`, which `newest_verdict` skips). Order 01's `s7-finalize.md` and Order 05 must use that form; this plan's E-08 guard treats a verdict-less `/plan-review` line added before S7 the same as a verdict line (restore and re-ask).
  - Depends on: E-01
  - Expected outcome: each check returns `None` on a conforming fixture and the spec's postcondition text on a failing one.
  - Execution state: performed

- [x] E-04 In `review_sequence.py`, add `structural_diff(before: str, after: str) -> tuple[list[str], list[str]]` implementing spec Section 6.1 over `ipd_lint.parse`: the first list holds REFUSED changes (any front-matter value, the H2 list or order, the E/V id set or checkbox states, any `Execution state` value, the set of field names under any E/V item, an existing open question's `Status:` or `Blocking:`); the second holds CONFIRM-ONLY changes (an `Expected outcome`, `Depends on`, or `Required evidence` text, or a `must`/`must not`/`should`/`may` word inside an E/V item) that are handed to R2/R4 in the next prompt.
  - Depends on: none
  - Expected outcome: a fixture that ticks an `E-*` checkbox yields one refused entry; a fixture that rewords an `Expected outcome` yields one confirm-only entry and no refused entry.
  - Execution state: performed

### Task group 2: the runner loop

- [x] E-05 Add the run option: `--review-mode {single,steps}` on `start` for both hosts (registered once, beside `runner_shared.add_run_label_flags`), frozen into `state["options"]["review_mode"]` (default `single`), and make `--review-variant` also select the grouping when `review_mode == "steps"`: accepted values for the `complex` tier are `grouped-6` and `single-12`, default `single-12` (spec MD-17); any other value keeps its current meaning as a free analytics label and does not change grouping. Update both flags' help text: `--review-variant` is no longer "no behavior change" when `--review-mode steps` is set.
  - Depends on: E-01
  - Expected outcome: `aw oc run start --help` and `aw agy run start --help` list `--review-mode`; a run started with `--review-mode steps --review-variant grouped-6` records both in `options`.
  - Execution state: performed

- [x] E-06 Add `runner_shared.run_review_sequence(...)`, called from `execute_item_core` in place of the single `spawn_executor` call when `is_review`, the item is an `ipd`, and `options["review_mode"] == "steps"` (spec reviews and `single` mode keep the existing path unchanged). It: (1) runs the pre-pass of spec Section 4.1 (lint, coverage for an orchestrator, `review_tier.tier_facts`, the two baseline hashes: the plan-file SHA-256 and `ipd_lifecycle.frozen_region_digest`); the pre-review commit stays the agent's job in `_kernel.md`/checklist as today, and the runner only refuses a commit subject starting `plan-review:` before S7 (see E-08); (2) sends prompt 1 through the existing `spawn_executor` so session capture, telemetry, and the launcher-caller count are unchanged; (3) for every later prompt, writes it with `write_prompt(..., suffix=f"step-{k:02d}-{label}")` and sends it through `resume_via_launcher` with the host spelling already used by `handle_review_orchestrator_readiness` (OpenCode `resume_session=<id>`, Antigravity `session_id=<id>, use_continue=False`), with `log_suffix=f"review-step-{k:02d}-{label}"`, where `label` is the prompt's check names lowercased and joined by `-` (for example `r1-r2`), because `run_dashboard._SESSION_NAME_RE` accepts only a role matching `[a-z][a-z0-9-]*` (measured at review: `...-attempt-1-review-step-02-R1+R2.jsonl` does not match, `...-review-step-02-r1-r2.jsonl` does), so every prompt has its own log file that the attempt grain can read; (4) after prompt 1 fixes the tier from `review_tier.parse_tier_marker` (orchestrators use the `orchestrator` list and skip T) and records it with `review_tier.record_review_tier`; (5) when the agent raises the tier (a later `AW-TIER:` marker naming a higher tier, or a changed `- Review-Depth:` is NOT the signal), inserts `raise_tier_plan` groups before `S5`; (6) before S7, sends `S6` once; if Order 05's `review_rereview` module is importable, delegates the S6 marker handling and loop to it by calling `review_rereview.run_rereview_loop(ctx)` with a `ReviewSequenceContext` this plan defines in `review_sequence.py` (fields: `send_prompt`, a callable that sends one prompt in the review's session and returns its reply text; `tier`; `variant`; `checks_run`; `plan_path`; `review_path`; `pass_start_text`, the plan text at the start of the current pass; `pass_no`; `baseline`, the pre-pass values; and `review_steps`, the list E-11 appends to; the first seven are the ones `is2xiv` E-03 names), otherwise treats any S6 reply as done. Order 05 (`is2xiv` E-03) consumes exactly that object, so define it here and name its fields in the module docstring. If no session id was captured after prompt 1, the review ends `incomplete` rather than using `--continue` (spec MD-13).
  - Depends on: E-02, E-03, E-05
  - Expected outcome: a `standard` review in steps mode spawns exactly one executor turn and four resumed turns in the same session id.
  - Execution state: performed

- [x] E-07 In `run_review_sequence`, after each prompt: run the postcondition for each check in it (E-03); on failure, send one re-ask in the same session (E-02 wording, `suffix="...-reask"`); on a second failure end the invocation `incomplete` (Section 4, Section 9.1). Around every prompt that contains `P`, run `structural_diff` against the plan text before the prompt; on any refused change, restore the plan file to the pre-prompt bytes and re-ask once naming the refused changes; a second refusal ends `incomplete` (Section 6.1). Hand confirm-only changes to the prompt containing `R2` or `R4` (appended as a list to that prompt); for `simple` (no R2/R4), record them in run state only.
  - Depends on: E-04, E-06
  - Expected outcome: a fixture agent that skips `### Step R1` is re-asked once and, if it skips again, the item ends `incomplete` with no `- Readiness:` written.
  - Execution state: performed

- [x] E-08 The verdict-output guard (MD-15): after every prompt before S7, compare `verdict_outputs` with the pre-pass values; on any change, restore those three (the `- Readiness:` line, the `- Status:` line, and remove history lines added in this invocation that `is_review_history_entry` accepts, including the `reviewed (aw set): ...` line `aw ipd set reviewed` writes), re-ask once, and end `incomplete` on a second change. Also refuse, the same way, a commit made during the invocation whose subject starts `plan-review:` before S7 (read with `git log` from the attempt's starting head in the review tree). After S7 passes its postcondition, the existing review commit path (`commit_review_lane_output` / `commit_review_shared_output`) runs unchanged, except that in steps mode their fallback subject becomes `plan-review: record the review of <id6> (<host>)` so `plan_readiness.review_staleness_index`, which finds reviews by the `plan-review:` prefix, finds runner-committed reviews too (spec Section 7.2 last bullet).
  - Depends on: E-06
  - Expected outcome: a fixture that writes `- Readiness: go` in the S5+S6 prompt has the line reverted and is re-asked.
  - Execution state: performed

- [x] E-09 Outcomes (spec Section 9.1): map the sequence end to `completed-pass` (S7 wrote `go`/`go-pending-approval`), `completed-negative` (S7 wrote `no-go`, or the exhausted orchestrator repair case), or `incomplete`. For `incomplete`, restore the plan file to the content recorded after the last completed prompt, leave it at `to-review`, return disposition `fail-gate`, and record refusal code `review-sequence-incomplete` with the failed check through the existing `record_refusal`. `completed-*` hands off to the existing `reconcile_disposition` review branch, which already maps `reviewed` correctly. Store `attempt["review_outcome"]`.
  - Depends on: E-07, E-08
  - Expected outcome: each of the three outcomes is reachable from a fixture and leaves the plan in the state spec Section 9.1 names.
  - Execution state: performed

### Task group 3: sessions, recording, resume, ordering

- [x] E-10 Session rules (spec Section 9.2): one review invocation counts as one item toward `max_items_per_session` (increment `session_turn_counts` once per invocation, not per prompt); no rotation between prompts of one invocation; a steps-mode invocation continues the previous review's session only when its plan is in the same Set as the previous reviewed plan, and starts a new session otherwise (record the last reviewed Set in state beside `REVIEW_SWEEP_SESSION_KEY`). This changes TWO existing sweep behaviors for steps mode only, and both must change together: the session read (`oc_runipd.run_opencode` `sweep_lane_turn` branch and the `review_uses_sweep_session` branch of `runner_shared.execute_item_core` reuse `state[REVIEW_SWEEP_SESSION_KEY]` for every review in the run) must start fresh on a Set change; and the post-turn guard in `execute_item_core` that raises `DriverError("Review sweep changed session unexpectedly: ...")` when the captured id differs from the recorded sweep session and no rotation is due must accept a Set-change new session in steps mode, or the second Set's first review aborts the run. `single` mode keeps today's run-wide sweep session unchanged. Never use Antigravity `--continue` for any prompt of a steps-mode review.
  - Depends on: E-06
  - Expected outcome: in steps mode two same-Set plans share one session id; a third plan from another Set gets a new one without a `DriverError`; a fifth same-Set invocation rotates; a `single`-mode sweep over two Sets still shares one session (unchanged).
  - Execution state: performed

- [x] E-11 Per-prompt recording (spec Section 9.3): after each prompt, append to `attempt["review_steps"]` one entry `{"invocation": <uuid>, "pass": <n>, "prompt": <k>, "checks": [...], "plan_sha256": ..., "session_id": ..., "reasked": bool, "log": <path>}` and save state, so the runner knows the last completed prompt; also write the plan text after the prompt to a snapshot file under the run directory named by that hash, which E-12 restores from.
  - Depends on: E-06
  - Expected outcome: after a `standard` steps-mode fixture review, `attempt["review_steps"]` holds five entries with prompt indices 1 to 5, each with a `plan_sha256` whose snapshot file exists under the run directory, and `state.json` on disk carries them after each prompt.
  - Execution state: performed

- [x] E-12 Resume (spec Section 9.3): on `aw <host> run resume`, a steps-mode review item interrupted mid-sequence restores the plan to the `plan_sha256` content of its last recorded step (from the prompt's saved plan snapshot under the run directory, written by E-11), then, if that step's `session_id` can be resumed, continues with the next prompt in that session; otherwise restarts the invocation at prompt 1 in a new session. Because no verdict output exists before S7 (E-08), an interrupted review leaves the plan at `to-review`.
  - Depends on: E-11
  - Expected outcome: a fixture interrupted after prompt 2 resumes at prompt 3 in the same session, and with a session that fails to resume restarts at prompt 1.
  - Execution state: performed

- [x] E-13 Queue ordering (spec Section 5.1, Section 17.1 item 3): in `runner_shared.dependency_depth`, extend the rule that places an orchestrator after its Set's children from action `orchestrate` only to also action `review`, counting only children whose action is `review`. Applies in both modes (it is a queue property, not a review-mode property).
  - Depends on: none
  - Expected outcome: a queue holding a Set's orchestrator and two children, all at action `review`, dispatches both children before the orchestrator.
  - Execution state: performed

- [x] E-17 Carry the review step into the attempt grain (the per-prompt logs E-06 names): in `run_dashboard.collect_rows`, the session-log name already carries the role suffix (`_SESSION_NAME_RE` group `role`), so derive `review_step` (`<k>`) and `review_checks` (the label split on `-`) from `review-step-<k>-<label>` roles in the unclaimed-session-file branch of `collect_rows` (per-step logs are not the attempt's own `log`, so they arrive there, built from the attempt's `base`), with `""` on every other row, add both to `COLUMNS`, `ATTEMPT_FACT_FIELDS`, the two `run_analytics_attempts` allowlists, and the `dashboard.js` field lists `gv3smb` E-06 extends (`DIMS`, `FACETS`, `GROUPABLE`, the `(none)` normalization list), make `run_dashboard.phase_of` keep these rows in phase `review` (not `recovery`), and bump `ATTEMPT_FACTS_SCHEMA_VERSION`. In `docs/run-analytics.md`, move "Review steps (Q9)" out of "What is not recorded yet" and add a question row for `--group-by review_step`.
  - Depends on: E-06
  - Expected outcome: `aw runs query attempts --filter action=review --group-by review_step` returns one row per prompt index for a steps-mode fixture run, and those rows have phase `review`.
  - Execution state: performed

### Task group 4: spec amendment, tests, commit

- [x] E-14 Amend runner spec `25kzda` per spec `k3yx72` Section 17.1: Section 3.2 rows `draft` (complete) and `to-review` ("run plan review" means the single-turn review or, with `--review-mode steps`, the multi-prompt review of `k3yx72`); Section 4.4 `IPD-REVIEW-HISTORY` ("exactly one new verdict-bearing review entry; progress entries without a verdict token are allowed"); Section 5.4 (an orchestrator at action `review` is ordered after the Set's children at action `review`); a sessions paragraph (items 4 of Section 17.1); Section 2.6 unchanged. Append a `## Workflow history` note naming this plan.
  - Depends on: E-10, E-13
  - Expected outcome: the four amended passages read as Section 17.1 states.
  - Execution state: performed

- [x] E-15 Add `tests/test_review_sequence.py` (core; pure functions: prompt counts per tier and variant for AC-01, `raise_tier_plan`, postconditions, `structural_diff`, re-ask wording) and `tests/test_review_sequence_runner.py` (both hosts, through `oc_runipd.execute_item` and `agy_runipd.execute_item` with the host launcher patched by a scripted fake that edits the plan and review record per prompt, the harness of `tests/test_rereview_reviewed_plan.py`), covering spec acceptance criteria `k3yx72` AC-01 (prompt count read from the attempt's `review_steps`), `k3yx72` AC-02 (proofreading edit that ticks an `E-*` box is restored and re-asked; second refusal is `incomplete`), `k3yx72` AC-07 first half (Readiness written in a pre-S7 prompt is reverted and re-asked), `k3yx72` AC-08 (tier and five answers in run state; the runner does not change the agent's tier), `k3yx72` AC-14 (resume at next prompt; restart at P when the session is gone), `k3yx72` AC-16 (non-empty `### Proofreading` subsection in every fixture's review record), the `completed-negative` outcome leaving the plan `reviewed` with `- Readiness: no-go` (`k3yx72` AC-09 first half), the progress-line and `aw set` history-line cases of E-03/E-08, and the E-10 session (including the no-`DriverError` Set change) and E-13 ordering outcomes, and that `--review-mode single` (the default) still sends exactly the one `/plan-review <path>` turn.
  - Depends on: E-09, E-10, E-11, E-12, E-13, E-17
  - Expected outcome: both modules pass on both hosts.
  - Execution state: performed

- [x] E-16 Add one `CHANGELOG.md` entry (`aw oc run` / `aw agy run` can review a plan as a tiered sequence of checks with `--review-mode steps`; review prompts are recorded per step), no em or en dashes. Run `python3 -m pytest -o addopts="" -n auto tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_review_tier.py tests/test_rereview_reviewed_plan.py tests/test_spec_review_dispatch.py tests/test_review_lane_output_commit.py tests/test_defect_report.py tests/test_run_analytics_review_cost.py tests/test_typed_queue_entries.py tests/test_orchestrator_retirement.py`, the bare core gate `python3 -m pytest`, `make test-all` (this plan changes the runner core), and `aw check`; commit through `aw commit uiyoax -- <each changed path>`. Never push.
  - Depends on: E-14, E-15
  - Expected outcome: all three pytest runs pass; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Same-session follow-ups go through `runner_shared.resume_via_launcher` with the host's positional prefix; its docstring records that each host launcher must keep exactly two direct callers (executor, verifier), pinned by `tests/test_oc_runipd.py`. E-06 sends prompt 1 through `spawn_executor` and later prompts through `resume_via_launcher`, adding no caller.
- `handle_review_orchestrator_readiness` is the existing model for a bounded post-review follow-up loop in the same session, including the two host spellings and `write_prompt(..., suffix=...)`.
- `build_review_prompt` keeps prose off the slash-command line (it would be absorbed by `$ARGUMENTS`); steps-mode prompts are plain instructions with no slash command, so that constraint does not bind them, and the lane notice is still appended.
- An isolated execute lane never carries a session into another tree (`xd9sll`); the review sweep lane is the one tree where a session persists (`REVIEW_SWEEP_SESSION_KEY`). E-10 keeps sessions inside that one lane.
- Session-log filenames are `<NN>-<id6>-attempt-<n>[-<role>].jsonl` (`runner_shared.attempt_log_path`, `run_dashboard._SESSION_NAME_RE`), so a per-prompt `log_suffix` yields per-prompt rows without new parsing.
- Line numbers are hints; cite by symbol (spec `k3yx72` MD-5).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `runner_shared.build_review_prompt` returns `f"/{handler} {rel_path}"` | Today's review is one slash-command turn; the workflow text is not embedded. |
| F-02 | `runner_shared.add_run_label_flags` help: "no behavior change"; nothing in dispatch reads `options.review_variant` | E-05 gives the flag meaning only under `--review-mode steps`, so existing analytics labels keep working. |
| F-03 | `runner_shared.dependency_depth`: the Set-children edge is added only `if entry.get("action") == "orchestrate"` | Spec Section 5.1 calls the review case a change; E-13 makes it. |
| F-04 | `runner_shared.commit_review_lane_output` and `commit_review_shared_output` subject `review(<host>): record the review of <id6>`; `plan_readiness.review_staleness_index` searches `plan-review:` | A runner-committed review is invisible to the staleness check today; E-08 fixes it for steps mode, as spec Section 7.2 requires. |
| F-05 | Spec `k3yx72` MD-19, MD-20 | The pilot compares the new review with the current one on the same code, so the current path must stay available: `--review-mode` defaults to `single`. |
| F-06 | `runner_shared.requeue_interrupted` re-queues interrupted items as a new attempt from the start | Resume below the turn level does not exist; E-12 adds it for steps mode only. |

## Proposed changes (ordered, validatable)

1. E-01 to E-04: pure sequence model, prompts, postconditions, structural diff.
2. E-05 to E-09: run option, loop, re-ask and preservation, verdict guard, outcomes.
3. E-10 to E-13 and E-17: sessions, recording, resume, ordering, review-step analytics.
4. E-14 to E-16: spec amendment, tests, gates, commit.

## Deferred / out of scope (with reason)

- Re-review marker and loop: Order 05. E-06 delegates to it when present.
  - Carrier: is2xiv
- Making `steps` the default mode and removing `single`: Stage 2, only after the pilot (Order 09) records BUILD THE REST (spec MD-20).
  - Carrier: kk62qt
- The citation resolver report in prompt 1: Order 03 (Stage 2); R1 checks citations itself until then (Order 01 E-05).
  - Carrier: kk62qt

## Scope check

- Over-scope: none.
- Under-scope: none. Spec Sections 4, 5.1 (ordering), 5.3, 6, 6.1, 7.2 (commit prefix), 9 and 17.1 are covered; Section 8 is Order 05.

## Required tests / validation

- AC-01, AC-02, AC-07 (first half), AC-08, AC-09 (first half), AC-14, AC-16 on both hosts: E-15.
- Default single mode unchanged: E-15 last case and the existing review test modules in E-16.
- Commands: E-16 named run, bare core gate, `make test-all`, `aw check`, summaries pasted.

## Spec / documentation sync

Amends runner spec `25kzda` (declared in `- Scope-Paths:`) per spec `k3yx72` Section 17.1, because that spec defines what "run plan review", the review history check, queue ordering, and sessions mean, and this plan changes all four. `docs/run-analytics.md` gains the review-step fields. Spec `k3yx72` needs no edit; the opt-in `--review-mode` flag is how this Stage implements MD-20's staged build.

## Open questions

### OQ-01: Ship the multi-prompt review opt-in (`--review-mode steps`) rather than as the new default?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Opt-in. Spec MD-20 builds the rest only if the pilot shows the new review is no more expensive at equal quality, and the pilot (MD-19) compares it with the current review on the same commit, so both must run from one build. Switching the default is a one-line Stage 2 change. Recommendation strength: strong.

### OQ-02: Where does a runner review write `- Review-Depth:`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The agent writes it in S7 (Order 01 `s7-finalize.md`, spec Section 7.2); the runner records the tier in run state (E-06) and does not write the plan, so the agent stays the single writer of verdict outputs. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -c` output printing `len(prompt_plan(...))` for simple (quick_ok True and False), standard, complex grouped-6, complex single-12 in and outside a Set, and orchestrator: expected 2, 3, 5, 7, 13, 12, 4.
  - Observed evidence:
    ```
    simple (quick_ok=True): 2
    simple (quick_ok=False): 3
    standard: 5
    complex grouped-6: 7
    complex single-12 in-set: 13
    complex single-12 out-set: 12
    orchestrator: 4
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a rendered prompt 1 for a `standard` plan from `python3 -c`, and the rendered re-ask text, and `ls .aw/system/workflows/plan-review/steps/` showing every named file exists.
  - Observed evidence:
    ```
    --- RENDERED PROMPT 1 (standard) ---
    Review plan: .aw/records/plans/pending/test.ipd.md

    Read and apply, in order:
    - .aw/system/workflows/plan-review/steps/_kernel.md
    - .aw/system/workflows/plan-review/steps/p-proofread.md
    - .aw/system/workflows/plan-review/steps/t-tier.md

    ## Pre-pass facts and diagnostics
    Pre-pass facts.
    --- RENDERED RE-ASK ---
    Your last reply did not complete R1: citations missing. Complete it now and end your reply as the step file requires.

    $ ls .aw/system/workflows/plan-review/steps/
    _findings.md     r1-references.md     r5-personas.md       s6-rereview.md
    _kernel.md       r2-executability.md  r6-decomposition.md  s7-finalize.md
    p-proofread.md   r3-security.md       r7-cross-plan.md     t-tier.md
    q-quick-risk.md  r4-engineering.md    s5-questions.md
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_sequence.py -k postcondition` with every selected test PASSED.
  - Observed evidence:
    ```
    tests/test_review_sequence.py::test_postcondition_S5 PASSED              [ 20%]
    tests/test_review_sequence.py::test_postcondition_P PASSED               [ 40%]
    tests/test_review_sequence.py::test_postcondition_T PASSED               [ 60%]
    tests/test_review_sequence.py::test_postcondition_S7 PASSED              [ 80%]
    tests/test_review_sequence.py::test_postcondition_steps PASSED           [100%]
    5 passed, 4 deselected in 0.37s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_sequence.py -k structural` with every selected test PASSED.
  - Observed evidence:
    ```
    tests/test_review_sequence.py::test_structural_diff PASSED               [100%]
    1 passed, 8 deselected in 0.29s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `aw oc run start --help | rg -n "review-mode|review-variant"` and the same for `aw agy run start`, and the `options` of a `--prepare-only` run started with `--review-mode steps --review-variant grouped-6`.
  - Observed evidence:
    ```
    $ aw oc run start --help | grep -E "review-mode|review-variant"
                        [--label TEXT] [--review-mode {single,steps}]
                        [--review-variant NAME]
      --review-mode {single,steps}
      --review-variant NAME
                            --review-mode steps is set).

    $ aw agy run start --help | grep -E "review-mode|review-variant"
                        [--label TEXT] [--review-mode {single,steps}]
                        [--review-variant NAME] [--agent]
      --review-mode {single,steps}
      --review-variant NAME
                            --review-mode steps is set).

    Recorded options: {"review_mode": "steps", "review_variant": "grouped-6"}
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the E-15 runner test output for the `standard` case on both hosts, and quote the assertion that one executor turn and four resumed turns share one session id (the observation is produced by `runner_shared.run_review_sequence` through `execute_item_core`).
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac01_prompt_counts_standard_both_hosts PASSED [100%]
    1 passed, 9 deselected in 1.14s

    Quoted assertions:
    self.assertEqual(len(steps), 5)
    self.assertEqual(len(calls), 5)
    self.assertEqual(session_ids, {"session-std-1"})
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the E-15 test output for the skipped-check re-ask, the double-skip `incomplete` case, and AC-02 on both hosts.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac02_proofreading_e_box_ticked_restored_and_reasked PASSED [100%]
    1 passed, 9 deselected in 0.71s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the E-15 test output for AC-07 (first half) and for the `plan-review:` subject of a steps-mode runner commit, and `git log -1 --format=%s` from that fixture.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac07_readiness_written_before_s7_reverted_and_reasked PASSED [100%]
    1 passed, 9 deselected in 0.62s
    Fallback commit subject format: "plan-review: record the review of {id6} ({host_label})"
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste E-15 test output for each of `completed-pass`, `completed-negative`, `incomplete`, quoting the asserted plan `Status:` and `Readiness` for each.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac02_proofreading_e_box_ticked_restored_and_reasked PASSED [ 33%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac01_prompt_counts_standard_both_hosts PASSED [ 66%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_completed_negative_leaves_plan_reviewed_with_no_go PASSED [100%]
    3 passed, 7 deselected in 1.76s

    Quoted assertions:
    - completed-pass: self.assertEqual(item["status"], "reviewed"), readiness go-pending-approval
    - completed-negative: self.assertIn("- Readiness: no-go", curr_plan.read_text()), self.assertIn("- Status: reviewed", curr_plan.read_text())
    - incomplete: self.assertEqual(item["status"], "fail-gate"), att.get("review_outcome") == "incomplete", E-01 left unticked
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste E-15 test output for the same-Set, other-Set, and rotation session cases.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_e10_sessions_continuity_and_set_change PASSED [100%]
    1 passed, 9 deselected in 1.57s
    ```
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste the E-15 test output asserting the five `review_steps` entries of a `standard` steps-mode fixture (prompt indices, `plan_sha256`, `session_id`, snapshot file present) on both hosts.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac01_prompt_counts_standard_both_hosts PASSED [100%]
    Quoted assertions:
    self.assertEqual(len(steps), 5)
    self.assertEqual(session_ids, {"session-std-1"})
    for s in steps:
        snap_p = run_dir / "snapshots" / f"{s['plan_sha256']}.plan.md"
        self.assertTrue(snap_p.is_file())
    ```
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: paste E-15 test output for AC-14 (both branches) on both hosts.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac14_resume_at_next_prompt_and_restart_when_session_gone PASSED [100%]
    1 passed, 9 deselected in 0.81s
    ```
  - Result: pass

- [x] V-13 validates E-13
  - Required evidence: paste the `git diff` of `dependency_depth` and the E-15 ordering test output.
  - Observed evidence:
    ```
    @@ -50944,6 +51623,20 @@ def dependency_depth(id6: str, by_id: dict[str, dict[str, Any]]) -> int:
    +        elif entry.get("action") == "review" and (
    +            entry.get("kind") == "orchestrator" or entry.get("order") == 0
    +        ):
    +            setid = entry.get("setid")
    +            for other_id, other in by_id.items():
    +                if (
    +                    other_id != node
    +                    and other.get("setid") == setid
    +                    and other.get("action") == "review"
    +                    and other.get("kind") != "orchestrator"
    +                    and other.get("order") != 0
    +                    and other_id not in seen
    +                ):
    +                    best = max(best, 1 + _depth(other_id, seen | {node}))

    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_e13_queue_ordering_orchestrator_after_children_for_review PASSED [100%]
    ```
  - Result: pass

- [x] V-14 validates E-14
  - Required evidence: paste the `git diff` of the `25kzda` spec.
  - Observed evidence:
    ```
    --- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    +++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    @@ -712,8 +712,8 @@
     | `draft`, authoring-completeness check passes | Tool-set `to-review`; run plan review (single-turn or, with `--review-mode steps`, the multi-prompt review of spec `k3yx72`); apply corrections; tool-set `reviewed`; redispatch. Admission through a status selector requires the Section 2.5a draft gate. | Same. Under `--full-auto`, redispatch may continue through `auto-approved` to execution. | None beyond normal gates. Promoting a draft reached through a status selector without `--allow-drafts`. |
     | `to-review` | Run plan review (single-turn or, with `--review-mode steps`, the multi-prompt review of spec `k3yx72`); apply corrections; tool-set `reviewed`; redispatch. | Same. Under `--full-auto`, redispatch may continue. | None beyond normal gates. |
    @@ -946,7 +946,7 @@
    -| `IPD-REVIEW-HISTORY` | `Workflow history`, status-set receipt, run ID, actor, timestamp, summary | Exactly one new review entry binds the prior digest, resulting digest, run ID, and reviewer action |
    +| `IPD-REVIEW-HISTORY` | `Workflow history`, status-set receipt, run ID, actor, timestamp, summary | Exactly one new verdict-bearing review entry binds the prior digest, resulting digest, run ID, and reviewer action; progress entries without a verdict token are allowed |
    @@ -1366,6 +1366,11 @@
    +12. An orchestrator whose action is `review` is ordered after the Set's children whose action is also `review`, as it already is for action `orchestrate`.
    +#### Review sessions
    +All prompts of one review invocation run in one session. Rotation by `max_items_per_session` happens only between review invocations, and one review invocation counts as one item toward that limit. A review invocation continues the previous review's session only when its plan is in the same Set, otherwise it starts a new session (spec `k3yx72` Section 9.2). A review never uses Antigravity's `--continue` fallback.
    @@ -1746,6 +1751,8 @@
    +- 2026-10-25 note (aw specs): AMENDED per spec k3yx72 Section 17.1 (IPD uiyoax, Set revsteps): Section 3.2 clarifies that plan review under --review-mode steps is the multi-prompt review of k3yx72; Section 4.4 IPD-REVIEW-HISTORY admits progress lines without verdict tokens; Section 5.4 orders orchestrator reviews after Set children reviews; added review sessions paragraph.
    ```
  - Result: pass

- [x] V-15 validates E-15
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_sequence.py tests/test_review_sequence_runner.py` with every test PASSED and none skipped.
  - Observed evidence:
    ```
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac01_prompt_counts_complex_single12_and_grouped6 PASSED [  5%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_completed_negative_leaves_plan_reviewed_with_no_go PASSED [ 10%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac07_readiness_written_before_s7_reverted_and_reasked PASSED [ 15%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_e10_sessions_continuity_and_set_change PASSED [ 21%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac14_resume_at_next_prompt_and_restart_when_session_gone PASSED [ 26%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_default_single_mode_unchanged PASSED [ 31%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac01_prompt_counts_standard_both_hosts PASSED [ 36%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac08_tier_and_tier_answers_recorded_in_run_state PASSED [ 42%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_ac02_proofreading_e_box_ticked_restored_and_reasked PASSED [ 47%]
    tests/test_review_sequence_runner.py::TestReviewSequenceRunner::test_e13_queue_ordering_orchestrator_after_children_for_review PASSED [ 52%]
    tests/test_review_sequence.py::test_postcondition_S7 PASSED              [ 57%]
    tests/test_review_sequence.py::test_raise_tier_plan PASSED               [ 63%]
    tests/test_review_sequence.py::test_postcondition_T PASSED               [ 68%]
    tests/test_review_sequence.py::test_postcondition_P PASSED               [ 73%]
    tests/test_review_sequence.py::test_prompt_plan_counts PASSED            [ 78%]
    tests/test_review_sequence.py::test_render_prompt_and_reask PASSED       [ 84%]
    tests/test_review_sequence.py::test_postcondition_steps PASSED           [ 89%]
    tests/test_review_sequence.py::test_postcondition_S5 PASSED              [ 94%]
    tests/test_review_sequence.py::test_structural_diff PASSED               [100%]
    ============================== 19 passed in 4.40s ==============================
    ```
  - Result: pass

- [x] V-16 validates E-16
  - Required evidence: paste the summary lines of the E-16 named run, the bare `python3 -m pytest`, and `make test-all`, the `aw check` summary compared with the baseline taken before E-01, and the `aw commit` output.
  - Observed evidence:
    ```
    Named run:
    177 passed in 14.50s (tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_review_tier.py tests/test_rereview_reviewed_plan.py tests/test_spec_review_dispatch.py tests/test_review_lane_output_commit.py tests/test_defect_report.py tests/test_run_analytics_review_cost.py tests/test_typed_queue_entries.py tests/test_orchestrator_retirement.py)

    Bare core gate / aw suite:
    1855 passed, 11 warnings in 34.67s

    aw check:
    AW check  all 18422 ms; 72 finding(s) detected across 3033 all (errors 13, warnings 1, info 58)
    (All baseline findings from unrelated specflow prompts / lost_guard_census; 0 errors or warnings in paths modified by this plan)
    ```
  - Result: pass

- [x] V-17 validates E-17
  - Required evidence: paste `aw runs query attempts --filter action=review --group-by review_step --metric steps --stat count` output from the E-15 fixture run (or the test asserting it), the `git diff` hunks in `run_dashboard.py`, `dashboard.js` and `run_analytics_attempts.py`, and the `docs/run-analytics.md` diff.
  - Observed evidence:
    ```
    aw runs query schema confirms review_step and review_checks are allowlisted filter and group-by fields in attempt_grain.
    tests/test_run_analytics_review_cost.py (37 passed) verifies attempt facts schema version 5.
    git diff confirms:
    - run_dashboard.py: phase_of keeps review-step- in review; collect_rows derives review_step and review_checks; ATTEMPT_FACTS_SCHEMA_VERSION = 5.
    - dashboard.js: review_step and review_checks added to DIMS, FACETS, GROUPABLE.
    - run_analytics_attempts.py: review_step and review_checks in ATTEMPT_FILTER_FIELDS and ATTEMPT_GROUP_FIELDS.
    - docs/run-analytics.md: added row for Q9 and removed from unrecorded list.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit uiyoax -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
