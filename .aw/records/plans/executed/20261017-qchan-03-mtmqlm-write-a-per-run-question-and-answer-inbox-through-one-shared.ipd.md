# IPD: Write a per-run question and answer inbox through one shared answer writer

- Date: 2026-10-17
- Kind: child
- Concern: A parked question (Order 02) lives only on the queue item inside `state.json`. Spec `6kwd2e` R9.1-R9.2 (amended 2026-10-17) make a per-run inbox the ONE answer carrier: `questions/<question_id>.json` written when an item parks, `answers/<question_id>.json` written by any adapter, and one shared writer that enforces first-answer-wins, atomicity, `actor == "human"` and the ledger record. Without it every later channel (CLI, terminal, Telegram) would write answers its own way.
- Scope: IN: a new module `agent_workflows/question_inbox.py` with the question and answer file schemas, `write_question` (called by the driver at park time), `write_answer` (the only answer writer), `read_open_questions`, `read_answers`, run-scoped question ids (`<position>-<id6>-a<attempt>-<worker question_id>`), question status transitions (`open`/`answered`/`stale`) through one writer, the artifact content hash (R5.6), and the `human_answer` ledger entry; wiring `write_question` into the park branch. Also writes the `open-questions.md` projection at park time (R4a.1) from the same data. OUT: consuming answers (Order 04), the CLI (Order 05), channels (Orders 09-11).
- Scope-Paths: agent_workflows/question_inbox.py, agent_workflows/runner_shared.py, agent_workflows/set_records.py, tests/test_question_inbox.py
- Item-Dependencies: executed:epsti7
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: 6kwd2e
- Set: qchan
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mtmqlm

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: mtmqlm verified (set qchan, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/set_records.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give every question one durable file and every answer one guarded writer, so any number of answering surfaces can be added without touching the run loop (spec `6kwd2e` R9.1, R9.2, R4a.1, R5.4, R5.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the module

- [x] E-01 Create `agent_workflows/question_inbox.py` with `write_question(run_dir, item, question) -> Path` writing `questions/<qid>.json` (schema `aw.question/v1`: `question_id`, `run_id`, `artifact_id6`, `artifact_path`, `artifact_hash` = SHA-256 of the artifact file at park time, `fingerprint`, `gates_verdict`, `text`, `options`, `allow_free_text`, `evidence`, `action` (review/execute), `created_at`, `status: open`). Run-scoped `qid = f"{position:02d}-{id6}-a{attempt}-{worker_qid}"`, where `attempt` is the attempt number that raised it: a resumed turn (Order 04 E-04) that reuses a worker id such as `q1` must get a NEW question, not collide with the answered one. `write_question` REFUSES to replace an existing question file (create with `O_EXCL` semantics: write the temp file, then `os.link` it to the final name and unlink the temp, so an existing file raises instead of being overwritten). `artifact_path` is repo-relative and resolved with `runner_shared.queue_artifact_path(repo, item)` against the MAIN checkout (not the lane, whose copy the worker edits), and `artifact_hash` is `runner_shared.sha256_file` of that file, so Order 04 recomputes staleness from the same path the same way. Atomic write (temp in same dir, fsync, `os.replace` or `os.link`). Every function that takes a `qid` from outside (CLI, chat) validates it against `QID_RE = ^[0-9]{2,}-[a-z0-9]{6}-a[0-9]+-[A-Za-z0-9._-]{1,40}$` and checks the resolved path's parent is the run's `questions/` (or `answers/`) directory, refusing otherwise, so a channel-supplied id can never name a path outside the inbox.
  - Depends on: none
  - Expected outcome: a written question file round-trips through `read_open_questions` and carries the artifact hash of the main-checkout file as it was at park time; a second `write_question` for the same qid raises and leaves the first file unchanged; a qid of `../x` or one not matching `QID_RE` is refused.
  - Execution state: performed

- [x] E-02 Add `write_answer(run_dir, qid, *, answer, choice, channel, sender, actor) -> AnswerResult` as the ONLY answer writer (R9.2): refuse a `qid` failing `QID_RE` or absent from `questions/`; refuse a question whose status is not `open` (answered or stale); refuse `actor != "human"` (the same rule `run_ledger_schema.validate_record` enforces as `RL-E051`; the test asserts both agree); refuse a `choice` outside the options and a free-text answer when `allow_free_text` is false; bound `answer` to 4000 characters and `channel`/`sender` to 200, rejecting control characters other than newline and tab, because the answer is later pasted into an agent prompt (Order 04) and a chat message (Order 10); take a per-question `filelock.FileLock` on `answers/<qid>.lock`; if `answers/<qid>.json` exists return `already` and record the attempt in `answers/<qid>.rejected.jsonl` without changing the answer; otherwise write `aw.answer/v1` (`question_id`, `answer`, `choice`, `actor`, `channel`, `sender`, `artifact_hash` copied from the question, `answered_at`) atomically, then append to `events.jsonl` (through `runner_shared.append_jsonl`) a `human_answer` event carrying the `run_ledger_schema` `human_answer` fields (`kind: human_answer`, `question_id`, `answer`, `actor: human`, `channel`, `sender`, `at`) and a `question_disposition` event with `disposition: answered_by_human` (R5.4; the value is a member of `run_ledger_schema.QUESTION_DISPOSITIONS`). These are run EVENTS, not hash-chained ledger records: no driver run writes `ledger.jsonl` (the `runner_shared` comment "NO driver run writes one"), and a runner run id such as `run-20261017T053655Z-482502` does not match `run_ledger_schema`'s `^run-[0-9a-f]{8,}$` grammar, so `validate_record` cannot be the acceptance test for the envelope. A rejected attempt (unknown qid excepted, which has no directory to write into) is appended to `answers/<qid>.rejected.jsonl` and as an `answer-rejected` event. After recording, refresh the `open-questions.md` projection (E-03's renderer) so an answered question stops being listed. Return `recorded`/`already`/`rejected` with a reason.
  - Depends on: E-01
  - Expected outcome: two concurrent writers for one qid, in two THREADS and in two separate PROCESSES (adapters run as separate processes, e.g. the CLI beside the Telegram poller), yield exactly one `recorded` and one `already`; unknown qid, malformed qid, non-human actor, out-of-range choice, over-length answer and an answer to a `stale` question are `rejected`; the answer file never appears half-written; `events.jsonl` holds one `human_answer` and one `question_disposition` event per recorded answer.
  - Execution state: performed

- [x] E-05 Add `set_question_status(run_dir, qid, status, *, reason) -> bool` as the ONLY writer of a question file's `status` after creation, accepting `answered` and `stale` from `open` and nothing else (a stale question is never reopened: re-asking it means writing a NEW question under a new attempt qid, so the stale answer stays on record), under the same per-question lock, atomically, with a `question-status` event. Order 04 (`j0ufrj` E-01, E-03) uses it to mark answers stale and questions answered, so no consumer rewrites a question file itself.
  - Depends on: E-02
  - Expected outcome: `open -> answered` and `open -> stale` succeed and are reflected by `read_open_questions`; an illegal transition (for example `answered -> open`) returns False and leaves the file unchanged.
  - Execution state: performed

### Task group 2: wire it at park time

- [x] E-03 In BOTH park branches added by Order 02 (`epsti7` E-02 for execute, E-06 for review), call `write_question` for each valid GATING question (non-gating ones do not park and get no file) and store the returned run-scoped qids on the item. Then write `<run_dir>/open-questions.md` (`set_records.OPEN_QUESTIONS_FILE`) with `question_inbox.write_projection(run_dir)`, which REUSES the existing renderer `set_records.render_open_questions` by mapping each question file to a `question_raised`-shaped record (`question_id`, `context` = text, `affected_nodes` = [artifact id6], `timestamp`, `actor`) and each answer file to a `human_answer`-shaped record, then writes atomically under a run-level `questions/.projection.lock` so concurrent answer writers cannot drop each other's update. This is the R4a.1 writer for runner runs; `set_records.write_local_projections` stays as it is (it serves Set runs under `.aw/workflow-artifacts/`). Writing must not raise into the run loop: on an OSError record an event and keep the item parked.
  - Depends on: E-05
  - Expected outcome: a scripted run that parks one item leaves `questions/<qid>.json` and an `open-questions.md` whose `## <qid>` heading lists it while the run is still advancing; after `write_answer` records an answer the projection no longer lists it.
  - Execution state: performed

### Task group 3: tests

- [x] E-04 Add `tests/test_question_inbox.py` (asserts spec `6kwd2e` A11 and A42): schema round-trip, hash capture, no-overwrite and qid validation, concurrent first-answer-wins with real threads AND two subprocesses, every refusal reason, status transitions (E-05), projection refresh after an answer, atomicity (no partial file after a simulated crash between temp write and rename), the ledger event, and the park-time wiring through a scripted run.
  - Depends on: E-03
  - Expected outcome: the module passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Atomic writes use a temp file in the destination directory then `os.replace` (pattern used across the package for run state).
- `filelock` is the package's only runtime dependency and the established lock primitive.
- `run_ledger_schema` requires `human_answer` records to carry `actor == "human"`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `set_records.write_local_projections` has no caller in the package (spec `6kwd2e` R4a.1 correction), and it writes under `.aw/workflow-artifacts/<workflow>/<run-id>`, not a runner run directory; `set_records.render_open_questions` renders from `question_raised` minus `question_disposition`/`human_answer` records.
- `run_ledger_schema.validate_record` requires a full envelope (`seq`, `parent`, a `run-<hex>` run id); `RL-E051` is the `actor == "human"` rule. No driver run writes `ledger.jsonl`.
- `runner_shared.append_jsonl` appends one line per write with fsync; runner run directories live under the gitignored `.aw/records/runs/`.
- `aw runs questions` reads `open-questions.md`; writing it at park time makes the existing verb work mid-run.

## Proposed changes (ordered, validatable)

1. E-01 question writer. 2. E-02 answer writer. 3. E-05 status writer. 4. E-03 park wiring and projection. 5. E-04 tests.

## Deferred / out of scope (with reason)

- Reading answers in the loop: Order 04.
  - Carrier: j0ufrj
- Pointing `aw runs questions` at the runner run directory if its current lookup misses it: Order 05.
  - Carrier: 8u071n
- Writing a hash-chained `ledger.jsonl` record for runner runs: no driver run has a ledger today; this plan records the same fields as run events.
  - Carrier-Declined: no runner ledger exists to append to; a runner ledger is a separate design, not part of spec `6kwd2e`

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_question_inbox.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R9.1, R9.2, R4a.1 as amended 2026-10-17.

## Open questions

### OQ-01: Where should rejected or duplicate answers be recorded?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: beside the answer, in `answers/<qid>.rejected.jsonl`, and as an event in `events.jsonl`. R9.2 requires a second answer to be 'reported and recorded, never applied'; a sidecar keeps the accepted answer file single-valued.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session writing a question for a fixture artifact and printing the read-back record including `artifact_hash`, compared with `sha256sum` of the artifact, then the refusal output for a second write of the same qid and for the qid `../x`.
  - Observed evidence:
    ```
    $ python3 -c '
    import tempfile, hashlib
    from pathlib import Path
    from agent_workflows import question_inbox

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run_dir = root / ".aw" / "records" / "runs" / "run-v01"
        run_dir.mkdir(parents=True)
        art_file = root / "fixture.ipd.md"
        art_file.write_text("# Test Plan\n- Id: v01art\n", encoding="utf-8")

        item = {
            "position": 1,
            "id6": "v01art",
            "action": "execute",
            "run_id": "run-v01",
            "artifact_path": str(art_file),
        }
        q = {
            "question_id": "q1",
            "text": "Choose deployment target?",
            "options": ["cloud", "on-prem"],
            "gates_verdict": True,
            "evidence": ["fixture.ipd.md"],
        }

        p = question_inbox.write_question(run_dir, item, q, attempt=1, repo=root)
        print("Written file:", p.name)
        read_back = question_inbox.read_open_questions(run_dir)
        print("Read-back count:", len(read_back))
        rec = read_back[0]
        print("artifact_hash: ", rec["artifact_hash"])
        h = hashlib.sha256(art_file.read_bytes()).hexdigest()
        print("sha256sum:     ", h)
        assert rec["artifact_hash"] == h

        # Second write for same qid
        print("Attempting second write for same qid:")
        try:
            question_inbox.write_question(run_dir, item, q, attempt=1, repo=root)
        except FileExistsError as e:
            print("Refused (FileExistsError):", e)

        # Write for qid ../x
        print("Attempting write for qid ../x:")
        try:
            q_bad = dict(q, question_id="../x")
            question_inbox.write_question(run_dir, item, q_bad, attempt=1, repo=root)
        except ValueError as e:
            print("Refused (ValueError):", e)
    '
    Written file: 01-v01art-a1-q1.json
    Read-back count: 1
    artifact_hash:  fdd9ea4556be557f420d65ec3d56456e0c59a5f3d17567c40fe95c2a72c49b85
    sha256sum:      fdd9ea4556be557f420d65ec3d56456e0c59a5f3d17567c40fe95c2a72c49b85
    Attempting second write for same qid:
    Refused (FileExistsError): [Errno 17] File exists: '/tmp/tmpdnbnez4s/.aw/records/runs/run-v01/questions/.tmp_01-v01art-a1-q1_2788967_1792279568679131167' -> '/tmp/tmpdnbnez4s/.aw/records/runs/run-v01/questions/01-v01art-a1-q1.json'
    Attempting write for qid ../x:
    Refused (ValueError): Invalid question_id '01-v01art-a1-../x'; must match ^[0-9]{2,}-[a-z0-9]{6}-a[0-9]+-[A-Za-z0-9._-]{1,40}$
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `-v` test output for the thread and subprocess concurrent-writers cases (one `recorded`, one `already` each) and each refusal reason, plus the two `events.jsonl` lines of one recorded answer.
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_question_inbox.py -k "test_concurrent_answers_threads or test_concurrent_answers_subprocesses or test_answer_refusal_reasons or test_answer_atomicity_and_events" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1347824571
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/mtmqlm
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    6 workers [4 items]
    ....                                                                     [100%]
    ============================== 4 passed in 2.04s ===============================

    Concurrent writers demonstration:
    writer 1: recorded (recorded)
    writer 2: already (already answered)
    events.jsonl lines:
    {"actor": "human", "answer": "Choice A", "at": "2026-10-17T23:26:21.676809+00:00", "channel": "cli", "event": "human_answer", "kind": "human_answer", "question_id": "01-art001-a1-q1", "sender": "writer-1"}
    {"actor": "human", "at": "2026-10-17T23:26:21.676809+00:00", "disposition": "answered_by_human", "event": "question_disposition", "kind": "question_disposition", "question_id": "01-art001-a1-q1"}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `ls <run_dir>/questions` and the `open-questions.md` contents from a scripted run captured while a later item is still queued, then the same file after an answer is recorded.
  - Observed evidence:
    ```
    === ls <run_dir>/questions ===
    .projection.lock
    01-v03a01-a1-q-storage.json

    === open-questions.md (while item 2 queued) ===
    # Open questions

    ## 01-v03a01-a1-q-storage
    - Context: Storage engine choice?
    - Affected nodes: v03a01
    - Raised: 2026-10-17T23:26:39.557282+00:00 (actor worker)

    === open-questions.md (after answer recorded) ===
    # Open questions

    _No unresolved questions._
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -q tests/test_question_inbox.py
    ..........                                                               [100%]
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    10 passed in 3.37s

    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5865,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `-v` test output for `open -> answered`, `open -> stale` and the refused `answered -> open` transition, with the question file's `status` printed before and after the refused one.
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_question_inbox.py -k "test_question_status_transitions" -v
    1 passed in 1.15s

    Status transition demonstration:
    Initial status q1: open
    open -> answered: True status: answered
    Status before refused transition: answered
    answered -> open transition result: False
    Status after refused transition: answered
    Initial status q2: open
    open -> stale: True status: stale
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
