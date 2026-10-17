# Review findings: plan mtmqlm

- Subject-Id: mtmqlm
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `db5d7f91c`. The plan was byte-identical to the lane input, and it already carries the orchestrator review's A11/A42 citation in E-04. `aw ipd lint --phase author --agent`: `clean`. Child plan.

Verified:
- `agent_workflows/question_inbox.py` does not exist yet.
- `run_ledger_schema`: `human_answer` needs `question_id` and `answer`; `RL-E051` requires `actor == "human"`; `question_disposition` value `answered_by_human` is in `QUESTION_DISPOSITIONS`; `validate_record` requires the common envelope (`seq`, `run_id`, `actor`, `timestamp`, `parent`), and `_RUN_ID_RE` is `^run-[0-9a-f]{8,}$`.
- `runner_shared` comment: no `ledger.jsonl` exists and no driver run writes one; `append_jsonl` fsyncs each line; `sha256_file` and `queue_artifact_path` exist.
- `set_records.write_local_projections` has no caller and writes under `run_artifacts_dir` (`.aw/workflow-artifacts/<workflow>/<run-id>`); `render_open_questions` renders `question_raised` minus `question_disposition`/`human_answer`.
- `filelock>=3` is the declared runtime dependency (`pyproject.toml`).
- Runner run directories are under the gitignored `.aw/records/runs/`.
- Spec `6kwd2e` R4a.1, R5.4, R5.6, R9.1, R9.2, A11, A42 read as cited.
- Downstream consumers: `j0ufrj` E-01 reads answers and marks questions `stale`; `8u071n` and `qrup8m` call `question_inbox.write_answer` with channel-supplied ids.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (identity collision) | plan E-01 `qid = f"{position:02d}-{id6}-{worker_qid}"`; `j0ufrj` E-04 "Re-park if the resumed turn asks again ... only new ones are written as open" | A resumed turn reusing worker id `q1` would map to the SAME qid as the answered question, so the new question either overwrote the answered one or was refused as "already answered". | all Low | FIXED | qid now includes the raising attempt (`-a<attempt>-`); `write_question` refuses to overwrite (link-based exclusive create). |
| PR-002 | HIGH | IN-SCOPE | Security (path traversal, untrusted input) | `qrup8m` "`question_inbox.write_answer`" called with chat-supplied ids; plan E-02 "refuse an unknown `qid`" | A qid from a CLI or chat channel was used to build `answers/<qid>.json` with no grammar check, and the answer text (later pasted into an agent prompt and a chat message) had no bound or character filter. | all Low | FIXED | `QID_RE` plus a resolved-parent check on every external qid; answer bounded to 4000 chars, channel/sender to 200, control characters rejected. |
| PR-003 | MEDIUM | IN-SCOPE | Accuracy (ledger contract) | `runner_shared` "NO driver run writes one"; `run_ledger_schema._RUN_ID_RE` `^run-[0-9a-f]{8,}$` | "append the `human_answer` ledger event" was ambiguous: there is no runner ledger, and a runner run id cannot pass `validate_record`. R5.4 also requires the `answered_by_human` disposition, which was not written. | all Low | FIXED | E-02 writes `human_answer` and `question_disposition`/`answered_by_human` as run events with the schema's fields; `actor` check asserted to agree with `RL-E051`; runner ledger is a Carrier-Declined row. |
| PR-004 | MEDIUM | UNDER-SCOPE | Architecture (single writer) | `j0ufrj` E-01 "question status `stale`", E-03 "mark the questions `answered` in the inbox" | The plan defined `status: open` but no writer for later transitions, so Order 04 would rewrite question files by hand, outside the lock. | all Low | FIXED | New E-05 `set_question_status` (open -> answered or stale only); `j0ufrj` E-01 now cites it and the hash recipe. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (staleness basis, R5.6) | plan E-01 "`artifact_hash` = SHA-256 of the artifact file at park time" | The plan did not say WHICH copy (the lane copy the worker edits, or main) or how the path is resolved, so Order 04 could recompute against a different file and mark every answer stale. | all Low | FIXED | Repo-relative path from `queue_artifact_path` in the MAIN checkout, hashed with `sha256_file`; `j0ufrj` E-01 uses the same recipe. |
| PR-006 | MEDIUM | IN-SCOPE | Correctness (projection freshness, R4a.1) | plan E-03 writes `open-questions.md` only at park time | Answers recorded later (CLI, Telegram) would leave answered questions listed. Concurrent writers could also lose updates. It also did not say how the existing renderer is reused or that review parks are covered. | all Low | FIXED | `write_projection` reuses `render_open_questions` via mapped records, runs at park AND after each answer under a projection lock, and covers both park branches (`epsti7` E-02, E-06); non-gating questions get no file. |
| PR-007 | LOW | IN-SCOPE | Testing (process boundary) | plan E-04 "concurrent first-answer-wins with real threads" | Adapters run as separate processes, and a lock that only works across threads would pass the test. | all Low | FIXED | E-02 and E-04 require a two-subprocess race too; V-02 demands it. |

`aw ipd sync --apply` assigned E-05/V-05. `aw ipd lint --phase review-finalize --agent`: `clean`, with one info `IPD-Z602` on E-02. E-02 is kept whole because every clause is a precondition or effect of the one guarded write. Sibling `j0ufrj` (to-review) E-01 edited; author-phase lint is `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to keep a re-asked question distinct? | Attempt number in the qid. | Content-hash suffix (REJECTED: two attempts may ask identical text deliberately; Order 08 dedups by fingerprint, not qid). | `j0ufrj` E-04; spec R9.1 "`question_id`". | yes |
| D-2 | Where do `human_answer` records go for a runner run? | `events.jsonl` events carrying the schema's fields. | Create a runner `ledger.jsonl` (REJECTED: new hash-chained store with no reader; out of spec scope). | `runner_shared` ledger comment; `run_ledger_schema._RUN_ID_RE`. | yes |
| D-3 | Which file does `artifact_hash` cover? | Main-checkout copy at the repo-relative path. | Lane copy (REJECTED: the worker edits it during the parked turn, so it differs immediately). | spec R5.6 "the artifact changed materially since"; `queue_artifact_path`. | yes |

No decision is `Reversible: no`. The `aw.question/v1` and `aw.answer/v1` schemas are new and have no consumer yet, so they are still reversible. No finding was left `OPEN` or `DEFERRED`.
