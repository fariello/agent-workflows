# IPD: Sweep pre-existing open questions before dispatch

- Date: 2026-10-17
- Kind: child
- Concern: Questions that already exist before a run starts (`### OQ-*` blocks with `- Status: open` in queued artifacts) are never put to the human by a runner: `/plan-review` NO-GOs on any open question, and the runners never read open questions at dispatch (spec `6kwd2e` 0.2, R1). Spec R1 requires a pre-flight sweep that collects them across the resolved queue, asks a present human in one bounded batch with a human-scale timeout, records each answer durably IN THE ARTIFACT before the next question, and parks the rest.
- Scope: IN: collecting open OQ blocks across the resolved queue (whatever types it holds, not a hardcoded plans tree), a new bounded free-text prompt distinct from `prompt_for_gate_phrase` (R1.3: `select` with a configurable human-scale timeout, never `readline()`/`input()`), `--blocking-only` and `--question-timeout` as shared run policy flags, durable artifact write-back (`- Status: resolved`, rationale naming the human and date, `- Blocking:` unchanged) committed through `git_commit_helper.offer_commit`, running in `initialize_run_core` beside `enforce_draft_admission_gate`, and presence decided only by `is_interactive_run` (R7.1). Unanswered questions (unattended, timed out, or skipped) are written to the inbox (Order 03); an item with an unanswered BLOCKING question is held non-terminally and released, with the answer written back into the artifact, by Order 04's checkpoint consumption. OUT: cross-question dedup (Order 08 owns `question_fingerprint` reuse and ordering; this plan calls it if present and otherwise asks in queue order).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/question_inbox.py, tests/test_question_preflight.py
- Item-Dependencies: executed:mtmqlm, executed:j0ufrj
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 4kkcex

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 4kkcex verified (set qchan, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified agent_workflows/oc_runipd.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Put every already-known open question in the queue to a present human before any work starts, keep each answer in the artifact itself, and route the rest to the inbox (spec `6kwd2e` R1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: collect and ask

- [x] E-01 Add `collect_preflight_questions(repo, queue, *, blocking_only=False) -> list[PreflightQuestion]` in `runner_shared.py`. For every queued item that resolves to an artifact file (`runner_shared.queue_artifact_path`, so the collector reads whatever types the queue holds and hardcodes no tree, spec `6kwd2e` R1.1), parse the file with `ipd_lint.parse` and take its `doc.open_questions` entries whose `Status` is `open` (`ipd_schema.OQ_STATUS_VALUES`; `deferred` and `resolved` are not asked). `ipd_lint.parse` reads only the `## Open questions` H2 (`ipd_schema.H_OPEN_QUESTIONS`), which plans and specs share; an artifact without that section yields none. `PreflightQuestion` carries `artifact_id6`, repo-relative `artifact_path`, `oq_id`, the heading text, `blocking`, the source line, and `artifact_hash` (`sha256_file` at collection time). Default scope is every open question; `blocking_only` keeps `Blocking: yes` (R1.2). Order: queue order, then OQ order within an artifact; if `question_inbox.group_open_questions` (Order 08) exists use its grouping, otherwise ask in that order (OQ-02). Register `--blocking-only` (`kind="bool"`) and `--question-timeout SECONDS` (`kind="int"`, default 300, must be >= 1) as rows of `runner_shared.RUN_POLICY_FLAGS`, so both hosts' `start` parsers get them from one definition and they are frozen into the run's options; both are `resume_rule=RESUME_NONE_DEFAULT` so a `resume` may change them.
  - Depends on: none
  - Expected outcome: for a fixture queue of 3 artifacts holding 2 blocking and 2 non-blocking open questions plus one `deferred` and one `resolved`, the collector returns 4, and 2 with `blocking_only` (A1); `aw oc run --help` and `aw agy run --help` both list both flags.
  - Execution state: performed

- [x] E-02 Add `prompt_for_free_text(question, *, timeout, stdin=None, stderr=None, read_chunk=None) -> str | None` in `runner_shared.py`, inheriting the four constraints of `prompt_for_gate_phrase`'s docstring and differing in the three ways R1.3 names. It returns None without printing when either stream is not a TTY (the caller additionally gates on `is_interactive_run`, the only presence predicate, R7.1). It prints the question to stderr, then loops on `select.select([stdin], [], [], remaining)` against a monotonic deadline, reading available bytes with `os.read(stdin.fileno(), 4096)` (never `input()`, `readline()` or `sys.stdin.read()`, R1.3a) until a newline arrives; it returns the stripped text before the newline, an empty answer meaning SKIP (returns None), and None on timeout (meaning PARK, not refuse) or on EOF. It caps the collected answer at 4000 characters (the `question_inbox.write_answer` bound) and decodes UTF-8 with replacement. The timeout constant `PREFLIGHT_QUESTION_TIMEOUT = 300.0` is distinct from `GATE_PROMPT_TIMEOUT` (180.0).
  - Depends on: E-01
  - Expected outcome: with a patched `select` that never reports ready and a patched monotonic clock it returns None without blocking; with a pipe fed `answer text\n` in two chunks it returns `answer text`; `PREFLIGHT_QUESTION_TIMEOUT != GATE_PROMPT_TIMEOUT` (A16); with non-TTY streams it returns None and writes nothing to stderr.
  - Execution state: performed

### Task group 2: record and route

- [x] E-03 Run the sweep in `runner_shared.initialize_run_core`, the one shared pre-flight seam, AFTER the draft admission gate, `--with-dependencies` expansion, `enforce_dependency_preflight` and `enforce_mixed_type_gate` (so the queue is fully resolved), and BEFORE the run directory is minted and before any dispatch (R1.4, A28); skip it under `--prepare-only`. Only when `is_interactive_run(args)` is true: print the sitting's shape (distinct questions, artifacts affected, R4.4 subset), then for each question call `prompt_for_free_text` with the frozen `--question-timeout`. For each answer, BEFORE asking the next question: write it into the artifact with a new `runner_shared.record_oq_answer(repo, path, oq_id, *, answer, who, channel, date)` that rewrites ONLY that OQ block (`- Status: open` -> `- Status: resolved`; `- Resolution or deferral rationale:` set to `RESOLVED <date> by <who> via <channel>: <answer>`; `- Blocking:` and `- Owner:` unchanged), refusing and leaving the file untouched if the artifact's hash differs from the question's `artifact_hash` or the block is no longer `open`; then commit that one path with `git_commit_helper.offer_commit(repo, [path], message=..., assume_yes=True, on_unrelated_staged="scope", runner=<host label>, run_id=None)`, the same path-scoped tooled helper `aw commit --no-plan` uses, never a raw `git commit`. The commit message names the artifact, the OQ id and `pre-flight sweep`. A refused or failed commit leaves the answer in the file, prints the reason, and the question is then routed as unanswered (E-04). `who` is `getpass.getuser()`; `channel` is `aw <host> run pre-flight`. A timeout, empty answer, EOF or Ctrl-C ends or skips that question; Ctrl-C ends the sitting keeping every committed answer, and the run continues to E-04 with the rest (R1.7).
  - Depends on: E-02
  - Expected outcome: after answering 2 of 4 questions and timing out on the third, the two artifacts read `- Status: resolved` with the rationale naming the user and date, their `- Blocking:` lines are unchanged, `git log` shows one commit per answer each touching only its artifact, and the run continues with 2 questions routed to E-04; the commit is made before the next prompt is printed (asserted by ordering in captured output).
  - Execution state: performed

- [x] E-04 Route unanswered pre-flight questions (unattended, timed out, skipped, or failed to record), after the run directory exists: write each to the inbox with `question_inbox.write_question` (Order 03) as `action: "preflight"`, `gates_verdict` = (`Blocking: yes`), with the `artifact_hash` collected in E-01, and store the qids on the item. Hold the owning item ONLY when at least one of its unanswered questions is `Blocking: yes`: set it `awaiting-human` with `needs_input` (the Order 02 non-terminal status, so dependents wait and the drain exits 3), but mark it `preflight_parked: true` and give it NO preserved lane and NO session (no turn has run). A `Blocking: no` question is written to the inbox and does NOT hold its item. In Order 04's `consume_answers` (`j0ufrj` E-01), for an item with `preflight_parked`, call `record_oq_answer` and the same commit as E-03 for each answered question (staleness: refuse and mark `stale` when the artifact hash moved, R5.6), then set the item `queued` WITHOUT `resume_with_answers`, so it dispatches as a normal first attempt with no lane adoption (Order 04 E-03 applies only to items that ran). Do this in `consume_answers` itself so Order 04's single checkpoint call covers it.
  - Depends on: E-03
  - Expected outcome: under `--unattended` with a TTY, no prompt is printed; a queue with one blocking and one non-blocking open question on two different items writes both to `questions/`, holds only the blocking one's item (`awaiting-human`, no lane) and dispatches the other; answering the blocking one with `aw runs answer` resolves it in the artifact (with a commit) at the next checkpoint and the item then dispatches as attempt 1 (A14, A41, A47).
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_question_preflight.py` on both hosts (asserts spec `6kwd2e` A1, A2, A14, A16, A18, A27, A28, A40, A41, A47) using a temporary git repository fixture and pseudo-TTY or patched-TTY streams: A1 collector scope; A2 timeout without waiting (patched clock and `select`, and a real pipe that never yields bounded by a test timeout so a regression fails instead of hanging); A16 distinct timeout; A18 a sitting interrupted after the 4th of 15 answers keeps 4 resolved and committed and routes 11 (11 written to `questions/`); A27 behaviorally: drive the sweep with `builtins.input` and `sys.stdin.readline` patched to raise, and assert it completes (the spec's static grep half is NOT implemented, because AGENTS.md forbids tests that read production source, P16; recorded as D-3); A28 the sweep's events precede `run-created` and any `ipd-started`; A40 the artifact block after the run directory is deleted; A41 `--unattended` and `--full-auto` each produce no prompt with a TTY present; A47 the unattended inbox route and checkpoint consumption; plus a stale artifact (edited between collection and answer) refusing the write.
  - Depends on: E-04
  - Expected outcome: the module passes on both hosts, and the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Front-loaded prompts all sit at one pre-flight seam (spec `25kzda` :278). Since rununify that seam is ONE shared function, `runner_shared.initialize_run_core`, which calls `enforce_draft_admission_gate`; the spec's per-host line citations into `oc_runipd`/`agy_runipd` predate it. The run directory is minted later in that same function (`mint_run_dir`), so the inbox route (E-04) must run after it.
- Run flags are rows of `runner_shared.RUN_POLICY_FLAGS` (one definition, both hosts, frozen into options, `resume_rule`).
- The OQ parser is `ipd_lint.parse(text).open_questions` (dicts keyed by `ipd_schema.OQ_FIELDS` plus `id`/`line`); `ipd_lint.check_open_questions` is a linter over it, not a collector.
- Path-scoped tooled commits from package code go through `git_commit_helper.offer_commit` (used by `cli.py`, `plans_archive.py`, `research_archive.py`).
- `is_interactive_run` is the only presence predicate (spec `6kwd2e` R7.1).
- Record answers durably in the artifact, never only in the gitignored run directory (`askme.md` 'Record project decisions').
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `prompt_for_gate_phrase` is an admission gate with a short timeout where silence means refuse; free text needs silence to mean park (spec `6kwd2e` R1.3).
- The runners never read OQ blocks at dispatch (exploration 2026-10-17).
- `GATE_PROMPT_TIMEOUT` is 180.0 today (the spec quotes 10.0 from an earlier revision); the new default only has to differ from it and be human-scale.
- `prompt_for_gate_phrase` uses `select` and then `stdin.readline()`; a `readline()` after `select` can still block on a partial line, which is why E-02 reads with `os.read` in a deadline loop.
- `ipd_lint.py` needs no change: the collector consumes its existing parser, so it was removed from Scope-Paths.
- Spec A27 asks for a STATIC grep for `readline()`/`input()`; that conflicts with AGENTS.md's ban on tests reading production source, so it is satisfied behaviorally (D-3).

## Proposed changes (ordered, validatable)

1. E-01 collect. 2. E-02 bounded prompt. 3. E-03 ask and record. 4. E-04 inbox route. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Fingerprint dedup and unblock-count ordering of the batch: Order 08 (this plan asks in queue order until 08 lands).
  - Carrier: jshwxb

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_question_preflight.py tests/test_question_resume.py tests/test_question_parking.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R1 and R7.1; the unattended inbox route is R9.7. No spec file is edited. `--blocking-only` and `--question-timeout` are new `aw <host> run` flags not listed in spec `25kzda` 2.1's grammar block; spec `6kwd2e` R1.2 authorizes `--blocking-only` and R1.3 requires a configurable timeout, so they are added as run policy rows without amending `25kzda` (OQ-03). The A27 static half is replaced by a behavioral test (D-3).

## Open questions

### OQ-01: Commit each pre-flight answer immediately, or batch them?

- Blocking: no
- Status: resolved
- Owner: plan author (settled by spec `6kwd2e` R1.7; recorded at review as decision D-1)
- Resolution or deferral rationale: RESOLVED: immediately, one tooled commit per answer. R1.7 requires each answer durable before the next question so an interrupted sitting loses nothing; a batched commit would lose every answer given before an interrupt.

### OQ-02: How are pre-flight questions ordered before Order 08 lands?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (review decision D-4)
- Resolution or deferral rationale: RESOLVED: queue order, then OQ order. Order 08 (`jshwxb`) depends on this plan (`executed:4kkcex`), so its `group_open_questions` never exists when this plan executes; the "call it if present" clause is a hook Order 08 fills by calling the sweep through its grouping (its E-05 already lists A17 "via Order 07's sweep"). Spec R1.6's dedup is therefore delivered by Order 08, not here.

### OQ-03: Do the two new run flags require amending spec `25kzda` 2.1?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (review decision D-5)
- Resolution or deferral rationale: RESOLVED: no amendment in this plan. `25kzda` 2.1 is the grammar of `aw <host> run`, but `6kwd2e` (approved, amended 2026-10-17) explicitly authorizes `--blocking-only` (R1.2) and requires a configurable timeout (R1.3). The `RUN_POLICY_FLAGS` comment states the table follows 2.1's grammar block "and nothing currently derives or checks it", so nothing breaks; a follow-up spec edit adding the two flags to the block can be made by the maintainer at any time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the collector output for the fixture queue with and without `blocking_only` (4 and 2, the `deferred` and `resolved` ones absent), and the `--blocking-only`/`--question-timeout` lines of `aw oc run --help` and `aw agy run --help`.
  - Observed evidence:
    ```
    collect_preflight_questions(blocking_only=False): count = 4
      art001 OQ-01: blocking=True
      art001 OQ-02: blocking=False
      art002 OQ-01: blocking=True
      art003 OQ-01: blocking=False
    collect_preflight_questions(blocking_only=True): count = 2
      art001 OQ-01: blocking=True
      art002 OQ-01: blocking=True

    aw oc runipd start --help:
      --blocking-only, --no-blocking-only
      --question-timeout SECONDS

    aw agy runipd start --help:
      --blocking-only, --no-blocking-only
      --question-timeout SECONDS
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the test output proving timeout returns None under a patched clock and `select`, the two-chunk pipe returning the joined answer, `PREFLIGHT_QUESTION_TIMEOUT` printed next to `GATE_PROMPT_TIMEOUT` (300.0 vs 180.0), and the empty stderr capture for non-TTY streams.
  - Observed evidence:
    ```
    PREFLIGHT_QUESTION_TIMEOUT: 300.0
    GATE_PROMPT_TIMEOUT: 180.0
    Timeout result: None
    Two-chunk pipe result: 'first chunk second chunk'
    Non-TTY result: None
    Non-TTY stderr captured: ''
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the two artifacts' OQ blocks after the sitting (`Status: resolved`, rationale with user and date, `Blocking:` unchanged), `git log --stat` for the answer commits showing one artifact per commit, the captured output showing each commit line before the next prompt, and the stale-artifact refusal (produced by E-03's sweep in `initialize_run_core` and `record_oq_answer`).
  - Observed evidence:
    ```
    [v03a01] OQ-01 committed: 3b793a1f5e113d39c811bd7477aab02c511fa3a5
    [v03a02] OQ-01 committed: 6de14dd04ed74819b9458c2f2a12e748abb3b6d1
    Stale artifact write refused: True

    Artifact 1 OQ block:
    ### OQ-01: Design choice 1

    - Blocking: yes
    - Status: resolved
    - Owner: test author
    - Resolution or deferral rationale: RESOLVED 2026-10-17 by alice via aw oc run pre-flight: Adopt architecture A

    Artifact 2 OQ block:
    ### OQ-01: Design choice 2

    - Blocking: no
    - Status: resolved
    - Owner: test author
    - Resolution or deferral rationale: RESOLVED 2026-10-17 by alice via aw oc run pre-flight: Adopt schema B

    git log --stat -2:
    commit 6de14dd04ed74819b9458c2f2a12e748abb3b6d1
    Author: Test User <test@example.com>
    Date:   Sat Oct 17 22:14:09 2026 -0400

        v03a02 OQ-01: pre-flight sweep answer

     .aw/records/plans/pending/20261017-qpfl-02-v03a02-plan.ipd.md | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)

    commit 3b793a1f5e113d39c811bd7477aab02c511fa3a5
    Author: Test User <test@example.com>
    Date:   Sat Oct 17 22:14:09 2026 -0400

        v03a01 OQ-01: pre-flight sweep answer

     .aw/records/plans/pending/20261017-qpfl-01-v03a01-plan.ipd.md | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the unattended run's `questions/` listing (both questions), the held item's status and `preflight_parked` with no `preserved_lane_id`, the other item's `ipd-started` event, and after `aw runs answer` and the next checkpoint the artifact's OQ block, its commit, and the held item's `ipd-started` with `attempt: 1` (produced by E-04's routing in `initialize_run_core` and its branch in Order 04's `consume_answers`).
  - Observed evidence:
    ```
    questions/ listing: ['01-v04a01-a1-OQ-01.json', '02-v04a02-a1-OQ-01.json']
    item 1 (blocking OQ) status: awaiting-human preflight_parked: True preserved_lane_id: None
    item 2 (non-blocking OQ) status: queued preflight_parked: None
    item 2 dispatched: ipd-started event appended
    write_answer recorded: True
    [v04a01] OQ-01 committed: fff70ead21e3300141134f84251a4fc3883c15b2
    consume_answers requeued: ['v04a01']
    item 1 status after consume_answers: queued preflight_parked: False resume_with_answers: None

    Artifact 1 OQ block after checkpoint:
    ### OQ-01: Question OQ-01

    - Blocking: yes
    - Status: resolved
    - Owner: test author
    - Resolution or deferral rationale: RESOLVED 2026-10-18 by maintainer via aw runs answer: Resolved blocking architecture question
    Artifact 1 git commit: fff70ea v04a01 OQ-01: pre-flight sweep answer
    ipd-started events: [{'at': '2026-10-18T02:14:15+00:00', 'attempt': 1, 'event': 'ipd-started', 'id6': 'v04a02'}, {'at': '2026-10-18T02:14:15+00:00', 'attempt': 1, 'event': 'ipd-started', 'id6': 'v04a01'}]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" tests/test_question_preflight.py tests/test_question_resume.py tests/test_question_parking.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1756117609
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/4kkcex
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 31 items

    tests/test_question_parking.py .........                                 [ 29%]
    tests/test_question_resume.py ...........                                [ 64%]
    tests/test_question_preflight.py ...........                             [100%]

    ============================= 31 passed in 49.06s ==============================
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
