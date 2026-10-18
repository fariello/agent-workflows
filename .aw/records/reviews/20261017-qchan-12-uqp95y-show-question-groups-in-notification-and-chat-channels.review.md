# Review findings: plan uqp95y

- Subject-Id: uqp95y
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the sealed lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisites `jshwxb`, `txl556`, `qrup8m` are `executed`; `mrlblc` is `approved`.

Verified against code:
- `notify.core.dispatch_checkpoint` calls `question_inbox.read_open_questions(run_dir)` and sends one entry per question; its acknowledgement pass sends one message per `(channel, question_id)` with an `answer-consumed` event.
- `notify.core.build_batch` renders `aw runs answer <run_id> <qid>`; `WebhookChannel.send` / `CommandChannel.send` compute `"count": len(batch.questions)`.
- `notify.registry.register` stores `run_dir`, `question_id`, `option`, `artifact_hash`; its only callers are in `TelegramChannel.send` (full-mode loop). `TelegramChannel._lookup_registered_message_id` and `registry.expire` key on `question_id`.
- `question_inbox.group_open_questions` narrows to awaiting-human items' `question_ids` when any exist, else all open questions; `write_group_answer(run_dir, state, group_id, ...)` recomputes groups under `answers/.group.lock` and calls `write_answer` per member with `applied_to`; `QuestionGroup.oq_id` is the first member qid. `run_cli` loads state with `runner_shared.load_state` when `state.json` exists.
- MEASURED: `question_inbox.group_questions` on two same-fingerprint records "Use C?"/"Use B?" gives `g-deadbeefdeadbeef-1` = "Use B?"; adding "Use A?" makes `-1` = "Use A?". Options `["pg","mysql"]` vs `["mysql","pg"]` share the driver fingerprint and split into `-1`/`-2`.
- Spec `6kwd2e` R4.1-R4.4, R9.2, R10.1, R10.3, R10.4 ("sends only"), R10.7, A9, A49, A53 read as cited. `agent_workflows/notify/` is absent from tag `v1.3.0-rc.1` (0 files), so `aw.notify/v1` has not shipped.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Reachability (inbound group routes) | `notify.registry.register` callers only in `TelegramChannel.send`; old Scope OUT "transport adapters for Telegram (owned by `qrup8m`)" | E-03 routed inbound events with a `group_id`, but nothing ever registered such a route: the only route producer, Telegram full mode, was out of scope. The inbound feature and V-03 were unreachable from any real channel. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-07/V-07: `TelegramChannel.send` sends one message per group and registers routes with `group_id` and `member_qids`; `telegram.py` in Scope-Paths; `executed:qrup8m` dependency (D-3). |
| PR-002 | HIGH | IN-SCOPE | Correctness (R4.1b wrong-answer) | measured `group_questions` renumbering of `g-<fp>-<n>` | Routing by the stored `group_id` can apply a human's answer to a different question once another same-fingerprint variant parks, because split ids are renumbered by sort order. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-03 resolves the CURRENT group containing the route's representative qid, falls back to `write_answer` when none; V-03 demands the renumbered case (D-1). |
| PR-003 | MEDIUM | IN-SCOPE | Spec conformance (R10.4) | spec `6kwd2e` R10.4 "sends only"; old OQ-01 and E-01 terse string `(1 group)` | The author's terse text inserted `(G group(s))` while claiming "strict conformance with R10.4", which says terse sends only the fixed sentence. | all Low | FIXED | Terse text unchanged; group density only as numeric `distinct_count` in JSON; OQ-01 re-resolved (D-2), which records the declined variant. |
| PR-004 | MEDIUM | IN-SCOPE | Compatibility (payload `count`) | `WebhookChannel.send` `"count": len(batch.questions)` | Grouping entries would silently change `count` from questions to groups; the plan's "`groups` dictionaries" shape was undefined against the existing `questions[]`. | all Low | FIXED | `OutboundBatch.question_count`; `count` keeps its meaning; additive `distinct_count` and per-entry group keys (D-6). |
| PR-005 | MEDIUM | UNDER-SCOPE | UX (acknowledgement storm) | `dispatch_checkpoint` ack loop per `(channel, question_id)`; `runner_shared.consume_answers` one `answer-consumed` per member | One group answer for 74 artifacts would send 74 "answered via" chat messages. | all Low | FIXED | New E-06/V-06: one acknowledgement per `(channel, group)`, `ack` rows for every member. |
| PR-006 | MEDIUM | IN-SCOPE | Regression (notification coverage) | `group_open_questions` narrowing to awaiting-human `question_ids`; old E-02 "when available" | Switching to `group_open_questions` could stop notifying open questions outside the current park, and "when available" left the fallback undefined. | all Low | FIXED | E-02 appends uncovered open questions as ungrouped entries (D-4); V-02 demands it. |
| PR-007 | MEDIUM | IN-SCOPE | Correctness (inbound mechanics) | `write_group_answer` per-member `write_answer`; route holds no state; `run_cli` state rule | E-03 claimed "atomically resolving all member questions" (it is per-member first-answer-wins) and did not say where `apply_inbound` gets `state`. | all Low | FIXED | E-03 loads state with `runner_shared.load_state` when `state.json` exists, else `None`, and states the non-atomic semantics. |
| PR-008 | MEDIUM | UNDER-SCOPE | Execution contract | old gate paragraph | The gate lacked the paste-actual-output rule, the tests-assert-behavior rule, the scope-fence declaration, and the conditional lifecycle ownership. | all Low | FIXED | Gate rewritten in the txl556/mrlblc contract shape. |
| PR-009 | LOW | UNDER-SCOPE | Documentation | no CHANGELOG/docs item; `mrlblc` owns `docs/notifications.md` | A user-visible change to channel output carried no CHANGELOG line or docs update. | all Low | FIXED | New E-08/V-08; `CHANGELOG.md`, `docs/notifications.md` in Scope-Paths; `executed:mrlblc` dependency (D-7). |
| PR-010 | LOW | IN-SCOPE | Validation (evidence and coverage) | old Required tests; old V-01..V-04; unbounded raiser list | Validation omitted `tests/test_notify_telegram.py`; V-items named no code path; listing 74 id6s in full mode is unbounded; non-group inputs had no stated compatibility. | all Low | FIXED | Telegram tests added to commands; V-items name code paths and demand pasted artifacts; raiser list capped at 10 with `and <m> more`; per-question rendering preserved (D-5). |

`aw ipd lint --phase review-finalize --agent`: `clean` (one `info` advisory `IPD-Z602` on clause count, kept).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What key identifies a group in an inbound route? | The representative member qid, resolved to its current group at answer time. | Stored `group_id` (REJECTED: measured renumbering misapplies answers). | measured `question_inbox.group_questions`; spec `6kwd2e` R4.1b. | yes |
| D-2 | Terse text with groups? (OQ-01) | Unchanged fixed sentence; N = member questions. | `(G groups)` suffix (REJECTED: R10.4 "only"). | spec `6kwd2e` R10.4. | yes |
| D-3 | Defer Telegram group routes to a backlog item, or include them? | Include `TelegramChannel.send` changes here. | Defer (REJECTED: leaves E-03 unreachable). | `notify.registry.register` callers. | yes |
| D-4 | Open questions outside every group? | Notify them as ungrouped entries. | Drop them (REJECTED: regression vs today). | `question_inbox.group_open_questions` narrowing. | yes |
| D-5 | Non-group inputs to `build_batch`? | Byte-identical per-question rendering. | Wrap every input as a group of one (REJECTED: changes existing output and tests). | `tests/test_notify_core.py` `test_build_batch_terse_and_full`. | yes |
| D-6 | `aw.notify/v1` shape for groups? | Additive per-entry keys and `distinct_count`; `count` stays questions. | New top-level `groups` list (REJECTED: duplicates `questions[]`). | `WebhookChannel.send`; notify absent from `v1.3.0-rc.1`. | yes |
| D-7 | Where do user docs go? | CHANGELOG plus `docs/notifications.md`, after `mrlblc`. | CHANGELOG only (REJECTED: docs would describe old full mode). | `mrlblc` Scope-Paths. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
