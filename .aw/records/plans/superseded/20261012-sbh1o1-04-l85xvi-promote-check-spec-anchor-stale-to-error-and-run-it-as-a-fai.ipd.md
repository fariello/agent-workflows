RETIRED 2026-10-12: CI is not watched, so a CI gate would gate nothing; maintainer chose the runner merge check plus a periodic checkup; superseded by .aw/records/plans/pending/20261012-cihealth-04-mnwkqu-refuse-to-merge-a-lane-that-makes-a-spec-line-pointer-stale.ipd.md (Set cihealth, cntxsm)

# IPD: Promote check.spec-anchor-stale to error and run it as a fail-closed CI step

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `1vd74h` asks whether `check.spec-anchor-stale` should gate and, if so, where a gate actually runs. Today it is `info`, it runs only behind the opt-in `--source-anchors` flag, and CI never runs it, so a newly stale spec line anchor re-accumulates silently (the class `mt54wr` and `atpvao` spent two plans sweeping).
- Scope: THE MAINTAINER DECISION RESERVED BY `mt54wr` OQ-01, PACKAGED SO THAT APPROVING THIS PLAN IS THE DECISION TO GATE (and retiring it `not-executed` is the decision not to). Three things. (1) Re-register `check.spec-anchor-stale` as `error` in `check_engine.RULE_REGISTRY`, rewriting its severity justification. (2) Add ONE fail-closed step to the `attention-check` job in `.github/workflows/tests.yml` running `python -m agent_workflows check --source-anchors --agent`, beside the existing `check plans`/`check releases`/`check backlog`/`check release-gates` steps. (3) Update the flag's `--help` text, the existing CLI tests that assert exit 0 on a finding, add a fail-closed regression, add a `CHANGELOG.md` line, and bring the fail-closed list in `docs/branch-protection.md` up to date. DELIBERATELY NOT a default: the detector stays OUT of bare `aw check specs` and bare `aw check`, so no interactive command gets slower. EXCLUDES all detector logic changes (Order 03 `fz3i3m`), EXCLUDES any speed optimisation, EXCLUDES a pre-commit hook, and EXCLUDES section-token validity (`mt54wr` OQ-02).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_spec_citation_anchors.py, .github/workflows/tests.yml, CHANGELOG.md, docs/branch-protection.md
- Item-Dependencies: executed:fz3i3m
- Status: superseded
- Readiness: no-go
- Work-Kind: chore
- Priority: low
- From-Backlog: 1vd74h
- From-Spec: none
- Set: sbh1o1
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: l85xvi

## Workflow history
- 2026-10-13 superseded (aw set): RETIRED 2026-10-12, maintainer decision during /plan-review of Set gradfix: CI is not watched (red since 2026-09-27, 1,623 main commits), so gating stale spec pointers in CI would gate nothing. OQ-01 answered: gate them at the runner merge check (cihealth Order 04, mnwkqu) plus the periodic checkup (cihealth Order 02, n7xlhm). Superseded by Set cihealth (cntxsm).
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (HIGH, fixed: OQ-01 relabelled Blocking: yes, since --full-auto could otherwise execute the maintainer's reserved decision), PR-002, PR-003, PR-004, PR-005, PR-006 (fixed). OQ-01 open, owned by the maintainer. Record: .aw/records/reviews/20261012-sbh1o1-04-l85xvi-promote-check-spec-anchor-stale-to-error-and-run-it-as-a-fai.review.md

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 04 of two plans graduating backlog 1vd74h; carries the maintainer-owned gating decision (mt54wr OQ-01) as its approval.

## Goal

Make a newly stale spec line anchor fail CI, without slowing any command a person runs, once Order 03 has made the detector's census zero for honest reasons.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Precondition

- [ ] E-01 CONFIRM THE CENSUS IS ZERO BEFORE PROMOTING, and refuse to promote otherwise. Run and paste `aw check specs --source-anchors` and `aw check --source-anchors --agent` on the real tree. Both must report zero findings and exit 0 with no traceback (Order 03 E-02 and E-05 deliver that), and the `--agent` record must carry `outcome` `clean`. If ANY finding remains, do not perform E-02 through E-05: mark this item `blocked`, name each remaining finding (location and validity) in the item, and leave it for a corrective plan. The one exception: a genuinely stale anchor in a COMMENT in a declared path (`check_engine.py`, `cli.py`, `tests/test_spec_citation_anchors.py`) may be retargeted onto a `Section N.N` token here with the quoted claim intact, then E-01 re-run. A false positive, or an anchor in any other file, is detector or tree debt owned by Order 03 or a successor. This is a genuine-precondition stop, not a scope stop: promoting over a non-zero census would red `main` the moment this lands. Also confirm the Order 03 precondition E-02 relies on, behaviorally rather than by reading source: on a self-written fixture with one stale anchor (a spec carrying `### 1.1` and `### 2.1` headings and an `agent_workflows/m.py` line `# spec <id6> Section 2.1 :<offset inside 1.1>`), `aw check --source-anchors --agent --verbose --dir <fixture>` must exit 0 with `outcome` `conforms` and its diagnostic must carry `"severity":"info"`, which is the observable sign that the branch reads severity from the registry (a literal would read the same today, so also run the E-02 probe below immediately after the edit). Also run and paste the bare suite `python3 -m pytest` summary line and failing-id set as the baseline for E-05, and three timings each of `aw check specs` and `aw check --source-anchors` (`/usr/bin/time -f "%U user %e real"`), so the record shows the default command is unaffected.
  - Depends on: none
  - Expected outcome: pasted zero-finding output from both commands, the pasted fixture probe (exit 0, `conforms`, `severity` `info`), the suite baseline, and the timings. The timings are context, not a bar: they show the default command does not run the detector, and their absolute values move with the machine.
  - Execution state: pending

### Task group 2: Promotion

- [ ] E-02 RE-REGISTER THE RULE AS `error`. In `check_engine.RULE_REGISTRY`, change `"check.spec-anchor-stale": RuleSpec("info", ...)` to `"error"` and rewrite the comment above it: the old reasons (an unswept tree, a necessary-not-sufficient verdict) are answered by Order 03 (zero census; a table-row false positive fixed; unattributed anchors reported), the remedy for any finding is always cheap (cite a `Section N.N` token or fix the offset), and `error` rather than `warning` because `artifact_core.drift_exit_code` treats both identically and a rule parked at `warning` is a recorded failure mode (`rnkqrc` E-05, the precedent the `check.live-bug-ungated` comment cites). Keep the invariant `""`. Because Order 03 E-02 derives the `--source-anchors` exit code, outcome and diagnostic severity from `check_engine.rule_spec`, no exit logic is touched here. Immediately after the edit, re-run the E-01 fixture probe: it must now exit 1 with `outcome` `findings` and `"severity":"error"`, with no traceback. If it still exits 0 or still says `info`, the branch is not reading the registry: mark this item `blocked` with that pasted output and do not hand-patch the branch, because the exit derivation is Order 03 E-02's deliverable and a second copy here would fork it.
  - Depends on: E-01
  - Expected outcome: `check_engine.rule_spec("check.spec-anchor-stale").severity` returns `error`; `aw check --source-anchors --agent` exits 1 with `outcome` `findings` on a fixture with a stale anchor and exits 0 with `outcome` `clean` on a fixture with none.
  - Execution state: pending
- [ ] E-03 UPDATE THE FLAG'S HELP TEXT. In `cli.py`, the `--source-anchors` argument help currently says "(opt-in, advisory info; runs across source regardless of positional record type)". Change it to say the report is opt-in, fails (exit 1) on any stale or unattributed spec line anchor, and is run by CI. Do not add the detector to any default path.
  - Depends on: E-02
  - Expected outcome: `aw check --help` shows the new text; bare `aw check specs` still does not report `check.spec-anchor-stale`.
  - Execution state: pending

### Task group 3: CI, tests, changelog

- [ ] E-04 WIRE THE CI STEP AND RECORD THE CHANGE. Add to the `attention-check` job in `.github/workflows/tests.yml`, after the `aw check release-gates` step, a step named "aw check --source-anchors (stale spec line anchors; fail closed)" with `shell: bash` and `run: python -m agent_workflows check --source-anchors --agent`, plus a two-line comment naming this plan and backlog `1vd74h`. Add one `CHANGELOG.md` line under the pending 2.0.0 section, in plain prose with no em or en dashes (user-facing text): "Changed: `aw check --source-anchors` now exits 1 when it finds a stale or unattributed spec line-anchor citation, and CI runs it as a fail-closed step. It remains opt-in locally, so `aw check` and `aw check specs` are unchanged." In `docs/branch-protection.md` section "What CI enforces (fail-closed, already in the repo)", add `aw check --source-anchors` (stale or unattributed spec line-anchor citations in source) to the fail-closed bullet list, in plain prose with no em or en dashes. That list is already stale (it still calls `aw check backlog` advisory, which `0i4fkt` made fail-closed, and omits `aw check release-gates`, which `3cs7qg` made fail-closed, per the comments in `.github/workflows/tests.yml`); correct those two entries in the same edit so the list matches the job, since a list this plan extends must not keep claiming a gate is advisory.
  - Depends on: E-02
  - Expected outcome: the workflow file carries the new step; the CHANGELOG carries the line; the `docs/branch-protection.md` fail-closed list names every fail-closed `aw` step in the `attention-check` job, including the new one.
  - Execution state: pending
- [ ] E-05 UPDATE AND ADD TESTS in `tests/test_spec_citation_anchors.py`, fixtures only. Change `test_cli_check_specs_source_anchors_exits_zero_with_finding` and `test_cli_non_specs_positional_type_runs_anchor_report` to expect exit 1 with the finding printed (rename the first to say it exits nonzero). Add: (a) `aw check --source-anchors --agent --verbose --dir <fixture>` with a stale anchor exits 1, writes no traceback to stderr, and its result record has `outcome` `findings`, `exit` 1, and a `check.spec-anchor-stale` diagnostic with `severity` `error` (`--verbose` is required: the compact `--agent` diagnostic carries only `location` and `rule`, per `result_types.CommandResult.to_agent_record`); (b) the same command on a fixture with no stale anchor exits 0 with `outcome` `clean` (zero findings report `clean`, not `conforms`, which Order 03 E-02 keeps); (c) `test_cli_bare_check_specs_omits_finding` still passes unchanged (the rule stays out of the default). Order 03 E-06 (e) and (f) assert the `info`-era contract (`conforms`, exit 0 with a finding); update (e) to the `error` contract or fold it into (a) rather than leaving a test that now contradicts the registry. Then run the bare suite and compare to the E-01 baseline.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: all tests in the file pass; no new suite failures relative to E-01.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.drift_exit_code` exempts only `info`, so there is no "warn but pass" tier: `warning` and `error` both exit 1.
- CI's `attention-check` job already runs the fail-closed `aw check` family as separate named steps (`check plans`, `check releases`, `check backlog`, `check release-gates`), each with an explanatory comment; this plan adds one sibling in the same shape.
- `check.live-bug-ungated`'s registry comment states the house rule this plan follows: "`error`, ... NOT a staged `warning` with a promise to tighten later: a rule left permanently at `warning` is a recorded failure mode in this repository (`rnkqrc` E-05)".
- AGENTS.md: CHANGELOG is user-facing prose, so it is written without em or en dashes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Each of the five points backlog `1vd74h` says "must be answered before a promotion is honest", answered with measurements at `92a6f240d` (2026-10-12):

| ID | Backlog point | Answer | Evidence |
|---|---|---|---|
| F-01 | (1) bare `aw check specs` already exits 1 on an unrelated finding, so a "bare check specs exits 0" bar is unsatisfiable. | NO LONGER TRUE, and no longer the bar. Bare `aw check specs` now conforms. The gate's bar is the dedicated step exiting 0, which does not depend on unrelated spec findings at all. | `aw check specs` at authoring: "CONFORMS  21 specs checked", "errors 0 warnings 0 info 1", exit 0. |
| F-02 | (2) CI never runs `aw check specs`, so wiring into it gates nothing. | Wire the gate where CI DOES run: a dedicated `check --source-anchors` step in the `attention-check` job (E-04), not into `check specs`. | `.github/workflows/tests.yml` `attention-check` steps: `specs check`, `attention --check`, `check plans`, `check releases`, `check backlog`, `check release-gates`; no `check specs`. |
| F-03 | (3) about 3.5s user CPU against about 0.6s for bare `check specs`, a user-perceptible slowdown if made default. | Do NOT make it default. CI runs it; nobody waits on it locally unless they ask for it. The default commands are untouched. | Re-measured at authoring: `aw check specs --source-anchors` 4.21s user / 4.97s real; bare `aw check specs` 1.05, 1.17, 1.05s user (three runs). |
| F-04 | (4) the census is not zero: the `check_engine.py` `pqsx96` `:135` I-07 table-row citation is misread. | Fixed by Order 03 E-03 (table-row acceptance); E-01 here refuses to promote unless the census is zero. | Census at authoring: exactly that one finding. |
| F-05 | (5) the detector misses anchors in blocks that do not name the id6. | The three named sites were already retargeted by `atpvao`; authoring found three MORE in `oc_runipd.py`/`agy_runipd.py`. Order 03 E-04 reports this class as `unattributed` and E-05 retargets the three, so the gate covers it. | Order 03 F-03 and F-04. |
| F-06 | (not in the backlog) the `--agent` report crashes whenever it has a finding, which would make a CI step using `--agent` fail with a traceback instead of a finding list. | Fixed by Order 03 E-02 (bug `g3ropl`), which is why this plan depends on Order 03. | Order 03 F-01. |

## Proposed changes (ordered, validatable)

1. Confirm a zero census (E-01).
2. Promote to `error` (E-02) and update help text (E-03).
3. Wire CI and record the change (E-04); update tests (E-05).

## Deferred / out of scope (with reason)

- A PRE-COMMIT HOOK. Not added: hooks are local, opt-in and skippable, and the 4s cost would land on every commit; CI is the portable authority this repository already uses for its other fail-closed checks.
  - Carrier-Declined: deliberately not wanted; the AGENTS.md release-gate section records that local hooks are skippable and that CI is the portable authority.
- MAKING THE DETECTOR FASTER. Not needed while it is CI-only (F-03). Revisit only if a later plan proposes making it default.
  - Carrier-Declined: no user-perceptible cost while CI-only (AGENTS.md: inefficiency users cannot notice is not a defect); a plan making it default must own the speed work.
- SECTION-TOKEN VALIDITY (`mt54wr` OQ-02). A renamed section is a different rot class; out of scope for the offset gate.
  - Carrier-Declined: owned by `mt54wr` OQ-02, which declines a carrier until the maintainer rules on it.

## Scope check

- Over-scope: none. Every declared path is modified: `check_engine.py` (E-02), `cli.py` (E-03), `.github/workflows/tests.yml`, `CHANGELOG.md` and `docs/branch-protection.md` (E-04), `tests/test_spec_citation_anchors.py` (E-05).
- Under-scope: none known.

## Required tests / validation

- `tests/test_spec_citation_anchors.py` updated and extended (E-05), asserting on exit codes, printed output and JSON records over fixtures; no live-tree census assertion.
- Executed CLI probes on the real tree after E-02: `aw check --source-anchors --agent` exits 0 with `outcome` `clean` (clean tree); bare `aw check specs` unchanged. Executed fixture probes before and after E-02 (E-01, E-02) showing the exit flip from 0/`conforms`/`info` to 1/`findings`/`error`.
- Invariant mapping: "the CI step fails on any stale or unattributed anchor" is pinned by E-05 (a); "a clean tree passes" by E-05 (b) and the V-04 real-tree run; "the default commands do not run the detector" by E-05 (c) and V-03.
- The bare suite `python3 -m pytest`, compared with the E-01 baseline.

## Spec / documentation sync

N/A for specs: `check.spec-anchor-stale` is not specified by any spec (its registry entry claims invariant `""`; no catalog invariant in spec `pqsx96` governs citation freshness), so changing its severity amends no spec. User-facing: the `--help` text (E-03), `CHANGELOG.md` (E-04), and the fail-closed list in `docs/branch-protection.md` (E-04), which is the document telling a repo admin what the `attention-check` required check enforces.

## Open questions

### OQ-01: Should `check.spec-anchor-stale` gate at all? (`mt54wr` OQ-01, reserved to the maintainer)

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: THE DECISION IS THE MAINTAINER'S AND THIS PLAN DOES NOT TAKE IT. TO ANSWER "YES": set this question `- Status: resolved` with the answer and date in this field (Owner stays `maintainer`), then approve the plan. TO ANSWER "NO": retire the plan `not-executed`. What the repository CAN answer is the conditional `mt54wr` OQ-01 left open: every measurable objection is now addressed (Findings F-01 through F-06), the CI-only placement costs no interactive time, and a finding is always cheap to fix. What it cannot answer is whether the maintainer wants CI to fail on a stale comment citation, which is a check-noise tolerance call. If declined, Order 03 still stands on its own (it fixes a crash and makes the opt-in report accurate), and backlog `1vd74h` should be closed `done` citing this retirement. BLOCKING (changed from `no` at review, finding PR-001): the authoring premise that only HUMAN approval can start execution is false. `aw oc run --full-auto` clears a `reviewed` plan whose `- Readiness:` is `go-pending-approval` to `auto-approved` and executes it, recording "an AUTOMATED clear, NOT human approval" (`runner_shared` `--full-auto` RunPolicyFlag help; predicate `plan_readiness.is_plan_review_approved`). Measured at review on a copy of this plan set `reviewed`/`go-pending-approval` with a review record: `is_plan_review_approved` returned `True` with `Blocking: no`, so automation could have taken the maintainer's reserved decision. `Blocking: yes` makes `aw ipd lint` refuse at every checkpoint (`IPD-Q501`) until a human answers here.
- Carrier-Declined: the question is answered on this plan itself (resolve it to approve, or retire the plan), so no separate carrier exists; it cannot vanish silently because `IPD-Q501` holds the plan until it is answered.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `aw check specs --source-anchors` and `aw check --source-anchors --agent` on the real tree showing zero findings, exit 0 and (agent) `outcome` `clean`, re-derived at execution; the pasted pre-edit fixture probe record showing exit 0, `outcome` `conforms` and `"severity":"info"`; the pasted bare-suite summary and failing-id set; and the six pasted timings. If the census was not zero, the pasted remaining findings and the item marked `blocked`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the pasted registry diff; the pasted output of `python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('check.spec-anchor-stale'))"` showing severity `error`; and the pasted post-edit fixture probe (`aw check --source-anchors --agent --verbose --dir <fixture>` plus `echo $?`) showing exit 1, `outcome` `findings`, `"severity":"error"` and no traceback, beside the same command on a fixture with no stale anchor showing exit 0 and `outcome` `clean` (produced by `cli._run_check`'s `--source-anchors` branch reading `check_engine.rule_spec`, which Order 03 E-02 creates). The contrast with V-01's pre-edit `info`/exit-0 probe on the same fixture is what localizes the exit flip to this registry edit.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `aw check --help` excerpt showing the new `--source-anchors` text, and pasted `aw check specs --agent` output on the real tree containing no `check.spec-anchor-stale` diagnostic.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the pasted `git diff` of `.github/workflows/tests.yml`, `CHANGELOG.md` and `docs/branch-protection.md`, and the pasted result of running the new step's exact command `python -m agent_workflows check --source-anchors --agent; echo exit=$?` locally on the real tree (exit 0).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` with every test passing and the tests pinning E-05 (a), (b) and (c) visible by name (names are pointers, not the bar: the bar is that the fail-closed, clean and default-omission behaviors are each asserted), and the pasted bare-suite summary line compared with the E-01 baseline (no new failures).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Explicit human approval is required before execution, and only after the maintainer has answered OQ-01 on this plan. OQ-01 is the one open question and it is blocking; do not execute under `--full-auto` or any automated clear while it is open.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push. Paste ACTUAL runner output for every test or probe claim, and never claim a result you did not run; run the suite bare (`python3 -m pytest`).

SCOPE FENCE. Do NOT add the detector to bare `aw check` or `aw check specs`, do NOT change detector logic in `spec_citations.py` (Order 03's), and do NOT add a hook. An out-of-scope edit that proves necessary is MADE and then JUSTIFIED to `aw ipd finalize` with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.

POST-GATE LIFECYCLE. Do not move this plan to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries observed evidence. Under `aw oc run` / `aw agy run` the runner performs finalize; executed by hand, run `aw ipd finalize l85xvi --actor <agent/model> --message <summary> --apply`. Backlog `1vd74h` may close `done` once both its carriers (`fz3i3m` and this plan) are executed.
