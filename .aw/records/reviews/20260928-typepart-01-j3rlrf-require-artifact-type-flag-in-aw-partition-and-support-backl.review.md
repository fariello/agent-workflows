# Review: Require artifact type flag in aw partition and support backlog and specs

- Subject-Id: j3rlrf
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: Codex/GPT-6
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Structural author preflight: `aw ipd lint --phase author --agent` returned `outcome: clean`, `exit: 0`, `findings: 0`. Read-only action-policy probe returned `backlog/open -> plan`, `backlog/graduated -> skip`, `spec/to-review -> review`, `spec/approved -> plan`, `spec/reviewed -> undetermined`, `ipd/approved -> execute`. No implementation or tests were run in this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness | `agent_workflows/status_set.py:41` `TYPE_STATUSES`; `agent_workflows/attention.py:86` `Item`; `agent_workflows/attention.py:2493` `_extract_identity_parts` | Plan referenced nonexistent `VALID_STATUSES` and `Item.date`, so execution would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the actual status vocabulary and filename creation-date extraction; validation names concrete outcomes. |
| PR-002 | HIGH | UNDER-SCOPE | Runner safety | `agent_workflows/run_selection_policy.py:145` `_SPEC_ACTIONS`; `agent_workflows/run_selection_policy.py:164` `_BACKLOG_ACTIONS`; `agent_workflows/runner_shared.py:26168` `enforce_requested_action` | Terminal-only filtering and unrestricted explicit action could emit commands for skipped or incompatible items; mixed spec stages need different global action flags. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Plan now derives legal next action, excludes non-runnable scan results, refuses ineligible explicit items and mixed-action selection, and treats `--action` as a constraint. |
| PR-003 | HIGH | UNDER-SCOPE | Ordering and dependencies | `agent_workflows/partition.py:46` `in_selection_edges`; `agent_workflows/partition.py:115` `partition`; `agent_workflows/partition.py:180` `sorted_shards` | Collection-only date sorting is erased by shard re-sort; IPD-only edges can split backlog/spec prerequisites. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added dependency-aware creation-date ordering through shard output and same-type edge recognition, while retaining greedy balancing. |
| PR-004 | MEDIUM | UNDER-SCOPE | Selection integrity | `agent_workflows/partition.py:231` `collect`; `agent_workflows/selectors.py:826` `resolve` | Stdin bypasses filters, no-match/ambiguous selectors can silently yield incomplete queues, and duplicate IDs can distort balancing. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Requires identical filters across input modes, explicit resolution errors, and deduplication before partitioning. |
| PR-005 | MEDIUM | UNDER-SCOPE | Testing and right-sizing | `agent_workflows/partition.py:197` `format_shard`; `agent_workflows/cli.py:3832` partition parser | Ordering and action formatting were bundled in one E-item; tests missed spec actions, profile output, selector errors, and shard order. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split action formatting into tool-allocated E-05/V-05 and expanded behavioral CLI evidence requirements. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should omitted and explicit `--action` mean for typed selections? | Derive the canonical next action per item; explicit action constrains legality; refuse mixed actions. | Treat explicit action as an override; silently split mixed selections. | `agent_workflows/run_selection_policy.py:333` `action_for_status`; read-only policy probe above; `agent_workflows/runner_shared.py:26168` `enforce_requested_action` | yes |
| D-2 | How should chronological backlog order survive partitioning? | Use filename creation date, dependency depth first, and the same tie-break order in shards. | Use nonexistent `Item.date`; use attention's last-history sort; sort only before `--max`. | `agent_workflows/attention.py:2493` `_extract_identity_parts`; `agent_workflows/partition.py:180` `sorted_shards` | yes |
