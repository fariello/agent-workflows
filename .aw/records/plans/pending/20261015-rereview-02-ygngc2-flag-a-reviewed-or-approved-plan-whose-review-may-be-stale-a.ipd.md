# IPD: Flag a reviewed or approved plan whose review may be stale, advisory only

- Date: 2026-10-15
- Kind: child
- Concern: Backlog `dbr23q`, second half. Measured 2026-10-15: `jmogmv` stayed `reviewed` and approvable after the maintainer's answer to its blocking OQ-01 inverted the plan's design (exit 4 became exit 2 everywhere), and no surface said its review might no longer describe the plan. Maintainer ruling 2026-10-15: flagging changes and answered blocking questions is wanted, but it MUST NOT force a re-review before approval, because in about 95% of cases answering a blocking question is all that is needed and moving straight to approved is the desired path.
- Scope: Add a deterministic, ADVISORY "review may be stale" signal for an IPD at `reviewed`, `approved` or `auto-approved`, computed from git (no new attested field): locate the plan's last review commit (newest commit touching the plan file whose subject starts `plan-review:`, else the commit that last wrote a review history entry recognised by `plan_readiness.is_review_history_entry`), read that blob via `check_engine._blob_text`, and compare it to the working text. Two reasons: (a) ANSWERED-QUESTION: an open question that was `Blocking: yes` and `Status: open` in the reviewed blob is `resolved` now; (b) SUBSTANTIVE-EDIT: `ipd_lifecycle.frozen_region_digest` differs between the reviewed blob and now. Surface it as (1) a new `info` rule `check.ipd-review-may-be-stale` in `check_engine` (never sets an exit code) mirrored as a passing `ipd_lint` advisory; (2) a warning line, NOT a refusal, from `aw ipd set approved` / `aw set approved` naming the reason and the remedy `aw oc review <id6> --yes`; (3) a marker in `aw attention`'s human board and a `review_stale` field in its JSON. Approval is never refused by this signal.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/status_set.py, agent_workflows/attention.py, tests/test_review_staleness_advisory.py, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: dbr23q
- Blocks-Release: next
- Set: rereview
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ygngc2

## Workflow history
- 2026-10-15 to-review (aw set): authored from backlog dbr23q at HEAD df9ededb4; maintainer rulings 2026-10-15 recorded in Concern

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A plan whose blocking question was answered, or whose executable content changed, after its last review is visibly flagged "review may be stale" in `aw check`, `aw ipd lint`, `aw attention` and at approval time, while approval still proceeds normally.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the predicate

- [ ] E-01 Add `plan_readiness.review_staleness(repo, plan_path) -> Optional[ReviewStaleness]` (frozen dataclass: `reasons` tuple of `"answered-blocking-question"` / `"substantive-edit"`, `reviewed_commit`, `question_ids`). Return `None` for statuses other than `reviewed`/`approved`/`auto-approved`, when no review commit is found (never guess), or when git is unavailable. Locate the review commit with `git log --format=%H%x00%s -- <path>` (first subject starting `plan-review:`, else the first commit whose diff adds a line accepted by `is_review_history_entry`); read its blob with `check_engine._blob_text`; compare OQ blocks via `_open_question_blocks` and executable content via `ipd_lifecycle.frozen_region_digest`. Bound cost: one `git log` per plan, and only for the three statuses.
  - Depends on: none
  - Expected outcome: deterministic, read-only, never raises to callers (errors -> `None`).
  - Execution state: pending

### Task group 2: surfaces (advisory only)

- [ ] E-02 Register `check.ipd-review-may-be-stale` in `check_engine` as `RuleSpec("info", ...)` beside `check.ipd-draft-ready-to-review`, produced by a `check_ipd_review_stale` that calls E-01 and emits one info diagnostic per stale plan naming the reasons, the review commit (short hash) and the remedy `aw oc review <id6> --yes`; mirror it as a passing advisory in `ipd_lint` exactly as `_draft_ready_advisory` does.
  - Depends on: E-01
  - Expected outcome: `aw check plans` exit code unchanged by the rule; the diagnostic appears.
  - Execution state: pending
- [ ] E-03 In `status_set.validate_transition_allowed` (or the prepared-change path right after `approval_refusals` returns empty), compute E-01 for a transition to `approved`; if stale, attach a warning carried exactly like `_demotion_warning` (printed on stderr in human mode, a `warnings` entry in the agent `result`), never a refusal, never prompting.
  - Depends on: E-01
  - Expected outcome: `aw ipd set approved <id6> --by-human` on a stale plan succeeds AND prints "review may be stale: <reasons> since <hash>; to re-review: aw oc review <id6> --yes".
  - Execution state: pending
- [ ] E-04 In `attention._plans_record`, add an optional trailing `review_stale` field (reasons list or empty) following the `blocks_release` precedent, render a short marker (e.g. `stale-review`) in the human board, and include the field in `--format json`.
  - Depends on: E-01
  - Expected outcome: `aw attention --format json` carries `review_stale` for the plan; `--check` exit unaffected.
  - Execution state: pending

### Task group 3: tests and contract

- [ ] E-05 Add `tests/test_review_staleness_advisory.py` driving real temp git repos: a plan committed with a `plan-review:` commit and a `Blocking: yes`/`open` OQ, then the OQ resolved and committed -> E-01 reports `answered-blocking-question`; an E-item text edit -> `substantive-edit`; a history-only or checkbox-only edit -> `None`; a `to-review` plan -> `None`; no review commit -> `None`. Then drive `aw check plans --agent`, `aw ipd set approved ... --by-human --agent` (assert exit 0, status `approved`, warning present) and `aw attention --format json` (assert the field).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: all pass.
  - Execution state: pending
- [ ] E-06 Add to `ipd-spec`, near the readiness/approval text, a paragraph defining the advisory (its two reasons, that it never refuses approval, and the maintainer ruling that answering a blocking question and approving directly is the normal path), record an `aw specs note`, and add a CHANGELOG line.
  - Depends on: E-05
  - Expected outcome: spec text matches behavior; no em/en dashes in CHANGELOG.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Advisory rules use `RuleSpec("info", ...)` and never set an exit code (`check.ipd-draft-ready-to-review`, `check_engine.check_ipd_draft_ready`; mirrored in `ipd_lint._draft_ready_advisory`).
- Never write another role's attestation field (AGENTS.md): this plan adds no plan field; staleness is computed from git on demand, so nothing can be forged or go stale itself.
- `ipd_lifecycle.frozen_region_digest` already defines "substantive" content (Scope-Paths, scope, E/V action blocks; excludes state fields, history, checkboxes).
- `plan_readiness.approval_refusals` entries REFUSE; the warning must be carried separately like `status_set` `_demotion_warning`.
- `/plan-review` commits with subject `plan-review: harden <scope> ...` (plan-review.md "Hardened-result commit").

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | No review-time fingerprint exists; staleness is currently undetectable | research for backlog `dbr23q`: no `Review-Fingerprint` field; `Coverage-Fingerprint` excludes Open questions |
| F-2 | A git-derived comparison needs no new attested field | `check_engine._blob_text`, `ipd_lifecycle.frozen_region_digest` |
| F-3 | Maintainer ruling: never force re-review before approval | interactive answer 2026-10-15, recorded in Concern |

## Proposed changes (ordered, validatable)

E-01..E-06 in order.

## Deferred / out of scope (with reason)

- A recorded `- Review-Fingerprint:` attestation: unnecessary while git history is available; would add a forgeable field.
  - Carrier-Declined: git-derived detection meets the need without a new attested field.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest tests/test_review_staleness_advisory.py -o addopts=""`, bare `python3 -m pytest`, `aw check all` showing no new non-info findings versus a pre-change baseline, and a timing comparison of `aw attention` before/after (warm) to confirm no user-perceptible slowdown.

## Spec / documentation sync

`ipd-spec` gains the advisory definition (E-06) because it owns the readiness/approval contract; declared in Scope-Paths.

## Open questions

### OQ-01: Should the advisory cost be bounded for large plan sets?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-15: only plans at reviewed/approved/auto-approved are examined (one `git log` each), and the required-tests section demands a measured before/after `aw attention` timing; if the slowdown is user-perceptible the executor must cache per HEAD before finalizing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted passing E-05 predicate cases.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `aw check plans --agent` on the E-05 fixture showing the info diagnostic and exit 0.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `aw ipd set approved <id6> --by-human` on the stale fixture showing success plus the warning (code path `status_set.validate_transition_allowed`).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `aw attention --format json` excerpt with `review_stale`, plus before/after warm timings of `aw attention` on this repo.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted targeted pytest output and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: quoted spec paragraph, spec history note, CHANGELOG line; `aw specs check` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval. Begin with `aw work begin ygngc2` in an isolated worktree; commit via `aw commit ygngc2 -- <paths>`; never push or tag. Paste ACTUAL output in each `V-*`. Independent of Order 01 (no shared files besides CHANGELOG.md and the `ipd-spec` file, which the runner's merge gate reconciles).
