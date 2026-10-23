# IPD: Run live /askme interactive trials per host/model and record the actual question fields

- Date: 2026-10-16
- Kind: child
- Concern: Plan `er11a0` rewrites the `/askme` workflow body, its manifest row and generated entry points, and the always-loaded communication contract. Its tests (`tests/test_askme_command_delivery.py`) prove the instructions are generated and DELIVERED; they cannot prove an agent then produces a question a human can answer. Research `y0vcm9` ("Actual questions produced by agents") says so directly ("Automated checks can establish that instructions were generated and delivered. They cannot prove that the resulting explanation is understandable") and prescribes a 12-row live trial table. `er11a0` defers exactly that work to backlog `jymlaw` (its `## Deferred / out of scope` row, `- Carrier: jymlaw`). Without the trials, nobody has observed whether the rewritten `/askme` fixes the reported failure ("/askme that question again" producing another unintelligible question).
- Scope: IN: run the 12 `y0vcm9` trials on each host/model combination in use in this repository (inventory established in E-01), in a disposable worktree against a planted fixture record; capture the ACTUAL question-interface fields (question text, header, every option label and description, free-text handling) and the subsequent handling for every trial; judge each with the `y0vcm9` test; record everything in one new research findings doc in Set `askmeplain`; scaffold one review-ready corrective plan per distinct failure. OUT: fixing any failure (each corrective plan carries its own fix); changing `/askme`, the reporting contract, the generator or the runner; building an automated prompt-quality checker (`y0vcm9`: "Start with these source and instruction changes before adding a new enforcement service").
- Scope-Paths: .aw/records/research/**/*-askme-live-trials.findings.md, .aw/records/plans/**/*-askmeplain-*.ipd.md
- Item-Dependencies: executed:er11a0
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: jymlaw
- Set: askmeplain
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lkn1zt
- Attended: required

## Workflow history
- 2026-10-23 executed (opencode model=uri/its_direct/pt3-claude-opus-5.5-1m-us attended=maintainer): 48 live /askme trials on 4 host/models (36 pass, 12 fail), findings auwidn; 5 corrective bug plans 9vttho lf4j52 wfy9ii l5f2hg pkz19w filed to-review
- 2026-10-17 attended (opencode its_direct/pt3-claude-opus-5.5-1m-us): marked `Attended: required` at the maintainer's direction: its own execution gate says E-04..E-06 need the maintainer answering /askme prompts live
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008
- 2026-10-16 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog jymlaw and research y0vcm9 "Actual questions produced by agents".
- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Observe, on every host/model in use, whether the `/askme` rewrite from `er11a0` makes agents ask questions a human can answer from the prompt alone, record the actual question fields as durable evidence, and turn every observed failure into a corrective plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: preflight and the evidence record

- [x] E-01 Preflight. Confirm `er11a0` is `executed` (`aw find er11a0`) and that the delivered workflow carries the new scopes (`grep -n "^## " .aw/system/workflows/askme/askme.md` shows "Recognize the request"). If either fails, STOP: mark every later item `blocked` and report, because trials against the old workflow measure nothing this item asks about. Then establish the host/model inventory from evidence, not assumption: `opencode --version`, `claude --version`, `agy --version`, `aw host capabilities` (lists the hosts the runners drive), and the model each host is configured to use (OpenCode: every profile in `aw oc profile list` plus the configured default, since each runner profile is a model in use; Claude Code: its `--model` default; Antigravity: its `--model` default). At authoring the installed hosts were OpenCode 1.18.35, Claude Code 2.1.283 and Antigravity CLI 1.4.0, and the OpenCode runner profiles were `opus` (`uri/its_direct/pt3-claude-opus-5.5-1m-us`, the default) and `gem` (`google/gemini-3.8-flash`); re-derive, these drift. A combination counts as "in use" if a host is installed AND this repo ships an entry point or runner for it (`.opencode/commands/askme.md`, `.claude/commands/askme.md`, `aw agy run`). Drop a combination only with a recorded reason (for example the binary is absent).
  - Depends on: none
  - Expected outcome: a host/model inventory table (host, version, model, entry point used for `/askme`, in-use reason) ready to paste into the findings doc; or every later item `blocked` with the reason.
  - Execution state: performed
- [x] E-02 Create the findings doc with the tool, not by hand: `aw research new --kind findings --set askmeplain --slug askme-live-trials --topic askme --summary "Live /askme interactive trial results per host/model (y0vcm9 trial table)" --apply` (dry-run at authoring derived `.aw/records/research/20261014-askmeplain-02-<id6>-askme-live-trials.findings.md`), then `aw research index`. Write into it: `## Method` (disposable worktree, fixture, capture procedure, the E-01 inventory table), `## Judging rule` (quote `y0vcm9`: "Judge the output by whether you can identify the subject, its purpose, the decision, and the consequences of each answer without looking elsewhere. If a trial requires asking 'What does that mean?' or 'Which file is that?', record that failure"), the verdict vocabulary (`pass`, `fail`, or `not-run` with the reason, the last only for a trial the host gives no mechanism to stage, never for a trial that was merely inconvenient), and an empty `## Trial results` section with one subsection per host/model.
  - Depends on: E-01
  - Expected outcome: the doc exists under `.aw/records/research/` with `kind: findings`, `set: askmeplain`, and the three sections; `aw research index --check` reports no drift.
  - Execution state: performed
- [x] E-03 Prepare the disposable trial bed so no trial can mutate a real record: `git worktree add --detach` a throwaway worktree at the current `HEAD` OUTSIDE `.aw/worktrees/` (for example under `/tmp/opencode/`; `--detach` so no branch is created and any commit a trial session makes is discarded with the worktree), and plant in it only a fixture IPD under `.aw/records/plans/pending/` whose `## Open questions` holds (a) one `Blocking: yes` design choice with NO malfunction (trial "New design choice with no malfunction"), (b) one question whose meaning depends on (a)'s answer (trial "Follow-up depends on an earlier answer"), and (c) a third independent question, so "Several open questions" has three to order. Describe the fixture verbatim in `## Method`. Never commit the fixture; the worktree is removed in E-08. Create the capture directory `.aw/state/askme-trials/` in the EXECUTING checkout (not in the disposable worktree, whose contents E-08 deletes).
  - Depends on: E-02
  - Expected outcome: a disposable worktree path and fixture id6 recorded in `## Method`; `git -C <primary lane> status --porcelain` shows no fixture file.
  - Execution state: performed

### Task group 2: the live trials (a human must be present)

- [x] E-04 On the OpenCode combination(s), run all 12 `y0vcm9` trials in the disposable worktree in an INTERACTIVE session, with the maintainer answering. Use the trial wording from the table: "use /askme" after a deliberately unclear question (stage it by first telling the agent "ask me fixture question (b) in one terse sentence, using only its identifiers", then, after it asks, sending "use /askme"); "/askme that question again" (sent right after an unclear question staged the same way); `/askme <question text>`; `/askme <fixture id6>`; `/askme` with no arguments and no outstanding question; the design-choice and follow-up questions from the fixture; a free-text "I don't understand" answer; a definite choice plus a wording complaint; question tool unavailable (deny the `question` permission through `OPENCODE_CONFIG_CONTENT`, the same mechanism `lane_containment.LANE_PERMISSION_POLICY` uses); an explicit noninteractive run (`opencode run` with the driver sentence "this run is non-interactive: do not invoke an interactive question tool or wait for human input", the text in `runner_shared` `build_prompt`); and several open questions. For each trial record in `## Trial results`: the exact input, the ACTUAL question-interface fields copied from the session (question, header, every option label and description, whether free text was offered), what the agent did next (waited, recorded, rescanned, guessed), the record edits it made, the judging verdict (`pass`/`fail`) and, for `fail`, the specific missing fact ("Which file is that?"). Capture each session with `opencode export <sessionID> --sanitize > <executing checkout>/.aw/state/askme-trials/opencode-<profile>-<NN>.json` (the gitignored capture directory from E-03); quote fields from it, do not commit it. Trial sessions must not commit or push.
  - Depends on: E-03
  - Expected outcome: 12 filled trial rows per OpenCode combination, each with the actual fields and a verdict.
  - Execution state: performed
- [x] E-05 Repeat E-04's 12 trials and capture on the Claude Code combination(s) (`claude` interactive, `/askme` from `.claude/commands/askme.md`; tool unavailable via `--disallowedTools AskUserQuestion`; noninteractive via `claude -p` with the driver sentence). Capture each session by copying its transcript (`~/.claude/projects/<project dir for the disposable worktree>/<session-id>.jsonl`) to `.aw/state/askme-trials/claude-<NN>.jsonl` in the executing checkout.
  - Depends on: E-03
  - Expected outcome: 12 filled trial rows per Claude Code combination, each with the actual fields and a verdict.
  - Execution state: performed
- [x] E-06 Repeat E-04's 12 trials and capture on the Antigravity combination(s). Antigravity has no repo slash-command mechanism (`index.md` host table: "use the universal fallback"), so the invocation is "read and execute `.aw/system/workflows/askme/askme.md`" plus the trial's argument; record that substitution in each row. Noninteractive via `agy -p` with the driver sentence. For "question tool unavailable", use an `agy` mechanism that disables its interactive question tool if `agy --help` or its settings expose one, and record which; if none exists, record that trial as `not-run` with the reason (no fabricated substitute). Capture each session by copying its conversation record from `~/.gemini/antigravity-cli/conversations/` to `.aw/state/askme-trials/agy-<NN>.<ext>` in the executing checkout; if a conversation cannot be located, paste the question fields into the row verbatim from the screen at the time of the trial and say so.
  - Depends on: E-03
  - Expected outcome: 12 filled trial rows per Antigravity combination, each with the actual fields and a verdict (`not-run` only with its reason); or a recorded reason the host is not in use (from E-01).
  - Execution state: performed

### Task group 3: conclusions and corrective plans

- [x] E-07 Write `## Summary` in the findings doc: a host/model by trial verdict matrix, and a deduplicated list of DISTINCT failures (same root cause across hosts counts once, with every affected cell named). For each distinct failure, scaffold one corrective plan with `aw ipd scaffold --kind child --set askmeplain --order <next free> --work-kind bug --priority <judgement> --title ... --apply`, then set its gate with the tool, `aw ipd set to-review <new plan> --blocks-release next` (an agent producing an unanswerable question is a user-perceptible defect, so the every-live-bug-gates-the-release rule applies; `aw ipd scaffold` has no gate flag), citing this plan, the findings doc id6 and the failing trial rows, and complete it to `to-review` with `aw ipd lint` conforming. Record each new plan's id6 against its failure in `## Summary`. If there is no failure, write "no failure observed; no corrective plan filed" and file none.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: `## Summary` with the matrix and failure list; one `to-review`, lint-conforming corrective plan per distinct failure, or the explicit no-failure sentence.
  - Execution state: performed
- [x] E-08 Close out: `git worktree remove` the disposable worktree and confirm it is gone (`git worktree list`); run `aw sanitize --agent` and fix any finding in the findings doc (session ids and absolute paths must not appear); set the doc outcome with `aw research set-outcome <doc id6> --to adopted --consumed-by lkn1zt --apply` when E-07 filed a corrective plan, or `--to informational` when it filed none; `aw research index`; commit only the findings doc and any corrective plans through `aw commit lkn1zt -- <paths>`.
  - Depends on: E-07
  - Expected outcome: no disposable worktree remains (if `git worktree remove` refuses because of untracked trial edits, use `--force` on that path only, since it is disposable by construction); sanitizer `pass`; one commit containing exactly the findings doc and the corrective plans.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Research docs are named and indexed only by `aw research new` / `aw research index` (`.aw/records/research/README.md`: "Do NOT hand-name or hand-maintain research files or the index"); `findings` is a valid kind (dry-run accepted it, `bogus` was refused). `INDEX.json`/`INDEX.md` are gitignored (`.aw/.gitignore` lines for `records/research/INDEX.*`), so they are not committed or scoped.
- `.aw/state/` is gitignored (`git check-ignore` on `.aw/state/askme-trials/x.json` matched `.aw/.gitignore` `/state/`), so raw transcripts can live there without entering history.
- Unattended runners deny the OpenCode `question` permission (`lane_containment.LANE_PERMISSION_POLICY`, `"question": "deny"`) and tell the agent the run is non-interactive (`runner_shared` `build_prompt`). A human-answered trial therefore cannot run under `aw oc run` / `aw agy run`; see the execution gate.
- Antigravity has no repo-file slash-command mechanism (`.aw/system/workflows/index.md` host table), so its trials use the "read and execute" fallback.
- A plan that changes no spec carries no spec edit; Scope-Paths status-agnostic record entries use `.aw/records/<type>/**/<filename>` form (spec `ipd-structure-and-linting` Section 4.5).
- Every live bug gates the next release (AGENTS.md "Every live bug gates the next release"), hence `--blocks-release next` on corrective plans, set through `aw ipd set ... --blocks-release next`.
- Host capture mechanisms verified at review: `opencode export [sessionID] --sanitize` exists; `claude --help` lists `--disallowedTools` and `-p/--print`; `agy --help` lists `-p/--print`, `--conversation` and `--model` but no flag to disable its question tool; Claude Code keeps transcripts under `~/.claude/projects/`, Antigravity under `~/.gemini/antigravity-cli/conversations/`.
- OpenCode's question tool is disabled through `OPENCODE_CONFIG_CONTENT` as `{"permission": {"question": "deny"}}`, the JSON shape `lane_containment` builds (`json.dumps({"permission": requested}, ...)`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | `er11a0`'s validation proves delivery, not comprehension | `y0vcm9`: "They cannot prove that the resulting explanation is understandable"; `er11a0` V-07 tests generation and installation only |
| F-2 | `er11a0` explicitly hands this work to `jymlaw` | `er11a0` `## Deferred / out of scope`: "Live interactive trials per host/model ... Recorded as not run. - Carrier: jymlaw" |
| F-3 | The trial table is fixed at 12 rows with a stated pass test | `y0vcm9` "Actual questions produced by agents" table and its "Judge the output by whether ..." paragraph |
| F-4 | Three hosts are installed and two are driven by runners | `opencode --version` 1.18.35, `claude --version` 2.1.283, `agy --version` 1.4.0; `aw host capabilities` lists `opencode` and `antigravity` |
| F-5 | The trials need a human; unattended runners structurally cannot provide one | `LANE_PERMISSION_POLICY` denies `question`; driver prompt sentence quoted above |

## Proposed changes (ordered, validatable)

E-01 through E-08 in order; each is validated by its `V-*` twin. No source, test, workflow or spec file changes.

## Deferred / out of scope (with reason)

- Fixing any trial failure: each failure gets its own corrective plan from E-07 so its fix is reviewed on its own.
  - Carrier: lkn1zt
- An automated question-quality checker: `y0vcm9` advises against adding one before the instruction changes are observed; not requested.
  - Carrier-Declined: not requested; y0vcm9 recommends against it at this stage.

## Scope check

- Over-scope: none.
- Under-scope: none. Raw transcripts stay in gitignored `.aw/state/` and are not deliverables; the disposable worktree is created and removed by this plan (E-03, E-08).

## Required tests / validation

No code changes, so no new tests. Validation is evidence that each trial ran and was captured: the filled findings doc, `aw research index --check`, `aw ipd lint` on every corrective plan, `aw sanitize --agent`, `git worktree list`, and `git show --stat` of the commit. Because no code changes, the bare `python3 -m pytest` is not required; run it anyway only if E-07 files nothing else and the reviewer asks.

## Spec / documentation sync

N/A: this plan changes no behavior, spec or user-facing doc. The findings doc is a research record. Any spec or doc change a failure needs belongs to that failure's corrective plan.

## Open questions

### OQ-01: Which host/model combinations count as "in use"?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-16: a combination is in use when the host binary is installed AND this repo ships an `/askme` entry point or runner for it (F-4: OpenCode and Claude Code shims, `aw oc run`, `aw agy run`). Each OpenCode runner profile (`aw oc profile list`) is a separate combination, because each names a different model. E-01 re-derives the inventory at execution time and records any dropped combination with its reason.

### OQ-02: Can an unattended runner execute this plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-16: no for E-04 to E-06. A runner turn denies the `question` permission and says the run is non-interactive (F-5), so it cannot observe a human answering. A runner that dispatches this plan anyway performs only E-01, marks E-02 to E-08 `blocked` and reports, never simulating the human (execution gate). The plan is executed by hand in an attended session (execution gate).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `aw find er11a0` showing `executed`; pasted `grep -n "^## " .aw/system/workflows/askme/askme.md` containing "Recognize the request"; pasted output of `opencode --version`, `claude --version`, `agy --version`, the model-identification commands, and `aw host capabilities` host lines; and the resulting inventory table quoted.
  - Observed evidence: `aw find er11a0` -> "✓  executed      er11a0  askmeplain      .aw/records/plans/executed/20261014-askmeplain-01-er11a0-make-askme-handle-current-and-rewrite-this-question-requests.ipd.md"; `grep -n "^## " askme.md` -> "8:## Recognize the request", "38:## Establish facts before asking", ... "191:## Finish"; `opencode --version` -> 1.18.35; `claude --version` -> "2.1.283 (Claude Code)"; `agy --version` -> 1.4.2; `aw oc profile list` -> "gem oc google/gemini-3.8-flash high", "opus * oc uri/its_direct/pt3-claude-opus-5.5-1m-us high"; Claude settings `ANTHROPIC_MODEL` its_direct/pt3-claude-sonnet-5-1m-us; Antigravity settings "model": "Gemini 3.8 Flash (High)"; `aw host capabilities` -> "host opencode platform=linux sandbox_mechanism=landlock", "host antigravity platform=linux sandbox_mechanism=landlock". Inventory table quoted in findings `auwidn` `### Host/model inventory (E-01, 2026-10-18)` (four combinations, none dropped).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the pasted `aw research new ... --apply` output with the written path; pasted `grep -n "^## \|^kind:\|^set:" <doc>` showing `kind: findings`, `set: askmeplain`, `## Method`, `## Judging rule`, `## Trial results`; pasted `aw research index --check` exit 0.
  - Observed evidence: `aw research new ... --apply` -> "wrote .../.aw/records/research/20261014-askmeplain-02-auwidn-askme-live-trials.findings.md". `grep -n "^## \|^kind:\|^set:"` -> "4:set: askmeplain", "8:kind: findings", "19:## Method", "55:## Summary", "106:## Judging rule", "112:## Trial results". `aw research index` -> "up to date ... (159 docs)". `aw research index --check` exits 1 on PRE-EXISTING repo-wide drift in other docs (dangling citations, stale states, unrecognized models); zero of its lines name `auwidn` (`grep -c auwidn` -> 0), so the doc itself introduces no drift.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `git worktree list` showing the disposable worktree (created by E-03); the fixture's `## Open questions` quoted from `## Method`; pasted `git status --porcelain` from this lane showing no fixture file.
  - Observed evidence: At E-03 `git worktree list` showed "/tmp/opencode/askme-trialbed ce87838f8 (detached HEAD)" (later rebuilt at fixture commit 1b7657fc0, plus Claude Code, Antigravity and auto beds, then history-free beds; all recorded in `auwidn` `## Method` deviations). Fixture `m4rcyy` OQ-01..OQ-03 quoted verbatim in `auwidn` `### Trial bed (E-03)`. Lane `git status --porcelain` at commit time -> only the findings doc and plan files; no `trialfix` fixture path.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: for each OpenCode combination, the 12 trial rows QUOTED from the doc, each carrying the actual question/header/option fields (not a paraphrase or "the agent followed the workflow"), the next action and a verdict; plus `ls .aw/state/askme-trials/` in the executing checkout showing one export per session (observation produced by the E-04 interactive sessions).
  - Observed evidence: `auwidn` `### OpenCode + opus` T01..T12 and `### OpenCode + gem` T01..T12 each quote header, question, every option label/description, the answer, the next action, the record edits and a verdict (24 rows; `grep -c "^#### T"` over the doc = 50 including attempt/quota rows). Captures in the executing checkout: opencode-opus-01..06,08..12.json and opencode-gem-01..06,08..11.json (T07/T12 counted from T04 per the approved deviation; opus T12 also staged directly).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: for each Claude Code combination, the 12 trial rows QUOTED from the doc with actual fields, next action and verdict, plus `ls .aw/state/askme-trials/claude-*` (observation produced by the E-05 sessions).
  - Observed evidence: `auwidn` `### Claude Code + Sonnet 5` T01..T12 with quoted fields and verdicts. `ls .aw/state/askme-trials/claude-*` -> claude-01.jsonl claude-02.jsonl claude-03.jsonl claude-04.jsonl claude-05.jsonl claude-06.jsonl claude-08.jsonl claude-09.jsonl claude-09b.jsonl claude-10.jsonl claude-11.jsonl claude-11.stream.jsonl claude-11.fixture.diff.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: for each Antigravity combination, the 12 trial rows QUOTED from the doc with actual fields, next action, verdict and the read-and-execute substitution noted, plus `ls .aw/state/askme-trials/agy-*` or the stated screen-copy fallback, and for any `not-run` row its reason (observation produced by the E-06 sessions); or the E-01 not-in-use reason quoted.
  - Observed evidence: `auwidn` `### Antigravity + Gemini 3.8 Flash` T01..T12 with quoted fields, the read-and-execute substitution stated at the top of the section, and verdicts; no `not-run` row (T10 staged with a `PreToolUse` hook denying `ask_question`). `ls .aw/state/askme-trials/agy-*` -> agy-01..06,08..10 transcript.jsonl/.db plus agy-11.txt, agy-11.transcript.jsonl, agy-11.db.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: `## Summary` quoted (matrix plus failure list); for each corrective plan, pasted `aw ipd lint <plan>` showing `to-review` and conforming, and `grep -n "^- \(Work-Kind\|Blocks-Release\|Set\):" <plan>` showing `bug`, `next`, `askmeplain`; or the no-failure sentence quoted and `ls .aw/records/plans/pending/ | grep askmeplain` showing no new plan.
  - Observed evidence: `auwidn` `## Summary`: verdict matrix (OpenCode + opus 12/12, OpenCode + gem 10/12, Claude Code 4/12, Antigravity 10/12; 36 of 48 pass) and the distinct-failure table D-8, D-5, D-4, D-6, D-10, D-9 with every failing cell. Corrective plans (maintainer-chosen grouping): `aw ipd lint` -> "to-review plan 20261023-askmeplain-03-9vttho [high] [blocking] conforming", "...-04-lf4j52 [high] [blocking] conforming", "...-05-wfy9ii [high] [blocking] conforming", "...-06-l5f2hg [medium] [blocking] conforming", "...-07-pkz19w [medium] [blocking] conforming"; each greps "- Blocks-Release: next - Work-Kind: bug - Set: askmeplain".
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: pasted `git worktree list` without the disposable worktree; pasted `aw research set-outcome ... --apply` output; pasted `aw sanitize --agent` result `pass`; pasted `git show --stat HEAD` listing only the findings doc and the corrective plans.
  - Observed evidence: `git worktree list | grep -ciE "askme-trial|tb\.|askme-oc|askme-agy"` -> 0 (all trial beds removed; history-free beds deleted). `aw research set-outcome auwidn --to adopted --consumed-by lkn1zt --apply` -> "updated 20261014-askmeplain-02-auwidn-askme-live-trials.findings.md" (front matter now "outcome: adopted", "consumed-by: [lkn1zt]"). `aw sanitize --agent` -> outcome "clean", 0 diagnostics; a manual grep then found and removed one absolute local path, after which the grep for home paths, hostnames and session ids returned no hits. `git show --stat HEAD` (1033d38aa) -> the findings doc (+677) and the 9vttho E-id fix only; the five corrective plans were committed by `aw ipd set to-review` itself (65a6a2907, 243ec8bfe, c656ad3bf, 908e8a736, 18c65f9f3), so the plan-and-doc set spans six commits rather than one.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and only after `er11a0` is `executed` (`- Item-Dependencies: executed:er11a0`). THIS PLAN NEEDS A HUMAN IN THE LOOP: E-04 to E-06 require the maintainer to answer `/askme` prompts live, so execute it by hand in an attended session (`aw work begin lkn1zt`), not in an `aw oc run` / `aw agy run` queue. If a runner dispatches it anyway, perform only the read-only E-01, mark E-02 to E-08 `blocked` with the reason "needs an attended session", and report; do not create the findings doc or the disposable worktree (E-02, E-03), because a blocked run would never reach E-08 to remove them. Never simulate the human's answers or invent question fields. The maintainer should approve this plan only when ready to run it attended, since `aw oc run all` dispatches approved plans.

Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an edit outside it is justified at finalize with `--scope-reason`. The disposable worktree and `.aw/state/askme-trials/` are outside history by construction. Never run a trial in the primary checkout or this lane, because `/askme` edits records.

Honesty: copy the ACTUAL question fields from the captured sessions; a paraphrase or a "followed the workflow" claim does not count as evidence (`y0vcm9`: "not just a prose claim that the agent followed the workflow"). Paste the actual output of every command in each `V-*`.

Open questions: OQ-01 and OQ-02 are resolved; nothing blocks execution beyond the attended-session requirement above.

Commits: only the findings doc and corrective plans, through `aw commit lkn1zt -- <paths>`; never `git add -A`, never push, never tag.

Lifecycle: this plan is executed by hand, so the executor finalizes: `aw ipd finalize lkn1zt --actor <agent/model> --message <summary> --apply`, only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. If a runner did dispatch it, the runner owns finalize and the plan stays in `pending/` with its blocked items. Never `git mv` the plan to `executed/`.
