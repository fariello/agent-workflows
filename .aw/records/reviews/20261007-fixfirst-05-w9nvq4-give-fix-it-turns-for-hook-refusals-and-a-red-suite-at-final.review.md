# Review findings: plan w9nvq4

- Subject-Id: w9nvq4
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `84368efb1`. The plan was committed and byte-identical to the sealed lane
input (sha256 prefix `dcc8d0a6cf339d62`), so there was no pre-review snapshot. `aw ipd lint --phase author --agent`:
`clean` before review; `--phase review-finalize`: `clean` after revision. Not an orchestrator.

Verified by symbol: `ipd_lifecycle._CommitRefused` and its handler in `_finalize_transaction`; `classify_commit_refusal`;
`finalize_refusal_is_retryable` (two arms); `integrate_lane_branch` (records re-derive, history auto-resolve, main
`--no-ff` arms); `owns_merge_in_progress`; `tag_integration_cause` / `read_integration_cause`;
`record_integration_refusal` (calls `record_refusal` only for `git-merge-conflict`); the merge-conflict send-back loop
and `prepare_lane_for_conflict_resolution` in `execute_item_core`; `gate_answer_is_warranted` (single call site, before
finalize); `perform_gate_answer` (`fixed` loop bounded by `retry_budget`); `GATE_ANSWER_MINE` docstring "the agent is not
repairing it"; `terminal_refusal_verdict`; `make_integration_validation_runner` / `_record_revalidation`
(`post_merge_revalidation.failures`, `baseline_comparison.new_ids`); `revalidation_was_unmeasured`; `extract_suite_failures`.

Scratch-repo demonstrations (real code, in the lane's gitignored `.aw/state/`):

```text
# finalize, .git/hooks/pre-commit exits 1
rc 2 | msg: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected in the coordinator worktree (hooks ran): HOOKSAYS: trailing whitespace in plan); rolled back to pre-finalize state.
receipt still present: True
plan still pending: True
retryable today: False
after hook fixed rc 0

# raw git: main advanced, .git/hooks/pre-merge-commit exits 1
merge rc=1
MERGE_HEAD present
unmerged: []

# integrate_lane_branch, same shape
integrated False | kind fail-merge | cause git-merge-conflict
why: [aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict; HOOKSAYS: refused
MERGE_HEAD left on main: False | status:
deferrable: False
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric G (premise) | `execute_item_core` single `gate_answer_is_warranted(...)` call after `integration_is_earned`; `GATE_ANSWER_MINE` "the agent is not repairing it"; `perform_gate_answer` `fixed` loop | E-03 put the gate-answer ask "first" for the post-merge combined-red refusal, but the ask runs before finalize on the lane's own suite and has no hook at the merge gate. It also proposed sending back on `mine`, which contradicts the documented meaning of that answer; `fixed` is already the bounded repair path there. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 sends combined-red back directly with `new_ids`; the ask and its vocabulary are excluded and unchanged. OQ-01 rewritten. D-2. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric A (classification) | demo `cause git-merge-conflict` for a `pre-merge-commit` refusal; `integrate_lane_branch` main arm `if rc == 1 and owns_merge_in_progress(...)` | E-02 covered only the re-derive and history-resolve commits. A hook refusing the main merge itself (the stage the repo's executed-transition gate runs on) is tagged as a git conflict with the false "BOTH SIDES CHANGED THE SAME REGION" verdict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 site (c): an owned merge with no unmerged paths is a hook refusal. D-1. |
| PR-003 | HIGH | IN-SCOPE | Rubric G (reachability) | merge-conflict loop: `if not prep.conflicted_paths: ... integrate_under_repository_lock(...); continue` | Admitting the hook cause to the existing conflict loop, as E-02 said, would merge main into the lane, find no conflict, and re-publish without ever asking the agent, spending the budget on the same refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06: a separate send-back beside that loop. |
| PR-004 | MEDIUM | IN-SCOPE | Security lens (path leak) | comment at the records re-derive arm: "their reason text carries GIT HOOK OUTPUT ... can embed an absolute path ... `record_refusal` - a writer that does NOT redact" | Tagging hook refusals without redaction could push absolute paths into the most-copied output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 redacts before tagging and keeps the new cause out of the `record_refusal` call. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric A | `classify_commit_refusal` "That is the signature of a CONCURRENT WRITER ... not a problem with this plan" | A concurrent-writer hook failure would have been handed to the agent as its own fault. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 refuses its arm when `DIAGNOSIS:` is present; Scope excludes it. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric D (anti-regression) | `tests/test_oc_runipd.py` `test_non_passing_gate_defers_not_faked_executed`, `test_non_passing_gate_records_merge_conflict_main_pristine` | Both drive combined-red through `execute_item` at the default budget and assert terminal `fail-merge`; E-03 would send them back into a fake that cannot re-commit. The file was out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 sets `retry_budget: 0` in those two tests only; file added to Scope-Paths. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric A (budget) | `finalize_retry_decision` uses `FINALIZE_RETRY_COUNT_KEY` and its exhausted text says "refused this plan's pre-transition checkpoint" | "Its own budget counter" was unspecified: a new finalize arm would share the pre-transition counter and its exhausted message would misname the kind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names three keys and requires kind-naming reasons; V-04 checks counter isolation. |
| PR-008 | MEDIUM | UNDER-SCOPE | Rubric D | combined-red fires after finalize on the lane | A post-finalize fix commit escapes finalize's scope reconciliation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 records fix-commit paths and warns on undeclared ones; noted as an accepted limit in Scope check, matching the shipped conflict send-back. |
| PR-009 | LOW | IN-SCOPE | Evidence accuracy | demo `rc 2`; `ipd_lifecycle` path unused | The Concern said rc 1, and E-01 planned an `ipd_lifecycle` change the existing message makes unnecessary. `extract_suite_failures` parses raw stdout, while the gate already records `failures`/`new_ids`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected; `ipd_lifecycle.py` removed from Scope-Paths; E-03 uses the gate record. |
| PR-010 | LOW | UNDER-SCOPE | Rubric G (execution contract, host parity) | original gate; E-05 single host | The execution contract was missing, tests named no host, and the `terminal_refusal_verdict` combined-red sentence would become false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Contract added; E-05 drives both hosts; E-03 updates the sentence; `needs-human` routing to Order 02 dropped as out of this plan's path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is a `pre-merge-commit` refusal told apart from a content conflict? | Owned merge (rc 1, `owns_merge_in_progress`) with `conflicted_paths` empty | Match git's "Not committing merge" text (localizable; the repo forbids text tests for this) | demo `MERGE_HEAD present`, `unmerged: []`; `merge_in_progress` docstring "THE DISCRIMINATOR IS `MERGE_HEAD`, NOT GIT'S ENGLISH" | yes |
| D-2 | Should combined-red go through the gate-answer ask, and should `mine` send back? | No ask at combined-red (none exists there); `mine` unchanged | Add a second ask at the merge gate (extra turn, no new information beyond `new_ids`); redefine `mine` as "fix it" (contradicts the 2026-09-19 vocabulary ruling recorded on `GATE_ANSWER_NEEDS_HUMAN`) | `gate_answer_is_warranted` single call site; `GATE_ANSWER_MINE` docstring | yes |
| D-3 | One counter or three? | Three (`HOOK_FINALIZE`, `HOOK_INTEGRATION`, `COMBINED_RED`) against the shared `frozen_retry_budget` | One shared counter (one kind starves another) | Orchestrator `lxb1ew` criterion 1 "within the existing per-kind `--retry-budget`" | yes |
