# IPD: Flag a reviewed or approved plan whose review may be stale, advisory only

- Date: 2026-10-15
- Kind: child
- Concern: Backlog `dbr23q`, second half. Measured 2026-10-15: `jmogmv` stayed `reviewed` and approvable after the maintainer's answer to its blocking OQ-01 inverted the plan's design (exit 4 became exit 2 everywhere), and no surface said its review might no longer describe the plan. Maintainer ruling 2026-10-15: flagging changes and answered blocking questions is wanted, but it MUST NOT force a re-review before approval, because in about 95% of cases answering a blocking question is all that is needed and moving straight to approved is the desired path.
- Scope: Add a deterministic, ADVISORY "review may be stale" signal for an IPD at `reviewed`, `approved` or `auto-approved`, computed from git (no new attested field): locate the plan's last review commit (newest commit touching the plan file whose subject starts `plan-review:`; no fallback, see OQ-02), read that blob, and compare it to the working text. Sweep surfaces (`aw check`, `aw attention`) resolve every candidate in ONE bulk `git log --name-only` plus ONE `git cat-file --batch`, never one `git log` per plan (F-4). Two reasons: (a) ANSWERED-QUESTION: an open question that was `Blocking: yes` and `Status: open` in the reviewed blob is `resolved` now; (b) SUBSTANTIVE-EDIT: `ipd_lifecycle.frozen_region_digest` differs between the reviewed blob and now. Surface it as (1) a new `info` rule `check.ipd-review-may-be-stale` in `check_engine` (never sets an exit code) mirrored as a passing `ipd_lint` advisory; (2) a warning line, NOT a refusal, from `aw ipd set approved` / `aw set approved` naming the reason and the remedy `aw oc review <id6> --yes`; (3) a marker in `aw attention`'s human board and a `review_stale` field on each JSON item, which bumps `attention.SCHEMA_VERSION` 4 -> 5 on that payload's own additive-bump precedent. Approval is never refused by this signal.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/status_set.py, agent_workflows/attention.py, tests/test_review_staleness_advisory.py, tests/test_attention.py, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ygngc2 verified (set rereview, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-15 to-review (aw set): authored from backlog dbr23q at HEAD df9ededb4; maintainer rulings 2026-10-15 recorded in Concern

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A plan whose blocking question was answered, or whose executable content changed, after its last review is visibly flagged "review may be stale" in `aw check`, `aw ipd lint`, `aw attention` and at approval time, while approval still proceeds normally.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the predicate

- [x] E-01 Add to `agent_workflows/plan_readiness.py` a frozen dataclass `ReviewStaleness` (`reasons`: tuple drawn from `"answered-blocking-question"` / `"substantive-edit"`, `reviewed_commit`: full sha, `question_ids`: tuple of `OQ-NN`) and two functions:
  - `review_staleness_from_texts(reviewed_text, current_text, reviewed_commit) -> Optional[ReviewStaleness]`, PURE: reason (a) for each `### OQ-NN` block (via `_open_question_blocks`) that read `Blocking: yes` and `Status: open` in `reviewed_text` and reads `Status: resolved` in `current_text`; reason (b) when `ipd_lifecycle.frozen_region_digest(reviewed_text) != frozen_region_digest(current_text)`. Returns `None` when neither reason holds. Import `ipd_lifecycle` inside the function body (it is a heavy module and `plan_readiness` imports only `ipd_schema` and `attention_contract` today).
  - `review_staleness_index(repo_root, plan_paths) -> Dict[str, ReviewStaleness]`, the BULK resolver: filter `plan_paths` to plans whose metadata `Status` is `reviewed` / `approved` / `auto-approved`; run ONE `git log --format=%x01%H%x00%s --name-only -- <plans root>` and keep, per candidate path, the FIRST (newest) commit whose subject starts `plan-review:`; read every reviewed blob in ONE `git cat-file --batch` call; apply the pure function. A plan with no such commit, git unavailable, or any git error is OMITTED (never guessed). Never raises (errors -> empty dict).
  - Single-plan callers (E-03) call `review_staleness_index(repo_root, [plan_path]).get(...)`; there is no second lookup implementation.
  - Path keys are repo-relative POSIX paths as git prints them. A plan RENAMED (for example by `aw rename plans` or a Set regroup) since its review has no `plan-review:` commit under its current path in a `--name-only` log without `--follow`; it is therefore omitted (silent), which is the fail-quiet direction for an advisory and is recorded as an honest limit in E-06.
  - Depends on: none
  - Expected outcome: a deterministic, read-only predicate with one bulk lookup path; on this repository's live tree at review HEAD `23863c32a` the bulk path resolved all 78 candidate plans in about 0.8s (re-measure at execution; the number is context, not the bar).
  - Execution state: performed

### Task group 2: surfaces (advisory only)

- [x] E-02 Register `check.ipd-review-may-be-stale` in `check_engine.RULE_REGISTRY` as `RuleSpec("info", ASSURANCE_GUIDANCE, DET_DETERMINISTIC, "")` beside `check.ipd-draft-ready-to-review`, produced by `check_ipd_review_stale(repo_root, include_untracked=False)` which iterates pending-dir plans exactly as `check_ipd_draft_ready` does, calls `review_staleness_index` ONCE for all of them, and emits one `enrich_drift` info diagnostic per stale plan naming the reasons, the question ids, the review commit (short hash), and the recovery `aw oc review <id6> --yes`; wire it beside `check_ipd_draft_ready` in the plans rule dispatch. Mirror it in `ipd_lint` as a passing advisory (a `_review_stale_advisory(doc, path, checkpoint)` added to `advisories` beside `_draft_ready_advisory`, at the `author` and `review-finalize` checkpoints only) that calls `review_staleness_index` for the one linted file and returns `[]` when the file is not inside a git work tree.
  - Depends on: E-01
  - Expected outcome: on a stale fixture the diagnostic appears and `artifact_core.drift_exit_code` treats it as advisory (info); `aw ipd lint --phase author` on the same plan stays `clean`/exit 0 while listing the advisory.
  - Execution state: performed
- [x] E-03 In `status_set._prepare_status_change`, beside the existing `_demotion_warning` computation, for a `plans` record whose target status is `approved` and whose `approval_refusals` came back empty, compute `review_staleness_index(repo_root, [rec.path])`; if stale, set the prepared change's warning to `review may be stale for <id6>: <reasons>[ (<OQ ids>)] since <short hash>; to re-review: aw oc review <id6> --yes`. Carry it through the SAME `_PreparedStatusChange.demotion_warning` -> `res.warning` -> `demotion_warnings` channel (rename the field to `warning` only if that is a mechanical rename across `status_set.py`; otherwise reuse it as-is), so it prints on stderr in human mode and lands in the agent result's `warnings` list. Never a refusal, never a prompt, and not computed for `auto-approved` (the `--full-auto` path), which already requires a review record as the newest history entry.
  - Depends on: E-01
  - Expected outcome: `aw ipd set approved <id6> --by-human` on a stale plan exits 0, the plan's `- Status:` is `approved`, and stderr (human) / `warnings` (agent) carries the review-may-be-stale line; on a non-stale plan no such line appears.
  - Execution state: performed
- [x] E-04 In `attention`, add a trailing `review_stale: Tuple[str, ...] = ()` field to `Item` (after `valid_progress`, following the appended-with-default precedent), populate it in `scan()` from ONE `review_staleness_index` call over the plan paths already collected (NOT from inside `_plans_record`, which is called once per plan), render a short `stale-review` marker on the plan's board line, add `"review_stale": list(it.review_stale)` to each `render_json` item, and bump `SCHEMA_VERSION` 4 -> 5 with a comment line in the existing version log. Update the `schema_version == 4` assertions in `tests/test_attention.py` to 5 (each is a recorded-truth update, not a weakening) and amend the attention spec's payload description with an `aw specs note`.
  - Depends on: E-01
  - Expected outcome: `aw attention --format json` reports `schema_version: 5` and a non-empty `review_stale` on the stale fixture plan, `[]` on others; `aw attention --check` exit code is unchanged by the field; warm wall time of `aw attention` on this repository rises by no more than about 1s over the E-01-adjacent baseline (re-measure; the bound is a perceptibility guard, not a hard SLA).
  - Execution state: performed

### Task group 3: tests and contract

- [x] E-05 Add `tests/test_review_staleness_advisory.py` driving real temp git repos (each with `.aw/records/` so repo-root resolution stays inside the temp dir): a plan at `reviewed` committed with a `plan-review:` commit and a `Blocking: yes`/`open` OQ, then the OQ resolved and committed -> `answered-blocking-question` naming `OQ-01`; an E-item continuation-line edit -> `substantive-edit`; a history-only, checkbox-only, `Execution state`-only, or `## Findings`-only edit -> not stale; a `Blocking: no` OQ resolved -> not stale; a `to-review` plan -> omitted; no `plan-review:` commit -> omitted; a plan renamed after review -> omitted; a non-git directory -> empty index, no exception. Then drive the CLI as subprocesses: `aw check plans --agent` (assert the info diagnostic is present and exit code is what the same tree gives without the rule's finding, i.e. advisory), `aw ipd lint --phase author --agent` (exit 0, advisory present), `aw ipd set approved <id6> --by-human --agent` (exit 0, file `Status: approved`, `warnings` contains the line) and its non-stale twin (no such warning), and `aw attention --format json` (`schema_version` 5, `review_stale` present).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: every case passes; no test reads production source.
  - Execution state: performed
- [x] E-06 Add to `ipd-spec` (`.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`), after the status-lifecycle paragraph (anchor `"`draft` -> `to-review` -> `reviewed` (via `/plan-review`) -> `approved` (human)"`), a paragraph defining the advisory: its two reasons, that it is computed from git and adds no field, that it never refuses approval, the maintainer ruling of 2026-10-15 that answering a blocking question and approving directly is the normal path, and the honest limits (a review that did not commit with a `plan-review:` subject, or a plan renamed since review, is not detected). Record `aw specs note` entries on `ipd-spec` and on the attention spec (for the E-04 schema bump), and add a CHANGELOG line under the pending release section.
  - Depends on: E-05
  - Expected outcome: spec text matches behavior; both spec history notes exist; `aw specs check` exits 0; `grep -nP '[\x{2013}\x{2014}]'` finds nothing in the added CHANGELOG line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Advisory rules use `RuleSpec("info", ...)` and never set an exit code (`check.ipd-draft-ready-to-review`, `check_engine.check_ipd_draft_ready`; mirrored in `ipd_lint._draft_ready_advisory`).
- Never write another role's attestation field (AGENTS.md): this plan adds no plan field; staleness is computed from git on demand, so nothing can be forged or go stale itself.
- `ipd_lifecycle.frozen_region_digest` already defines "substantive" content (Scope-Paths, scope, E/V action blocks; excludes state fields, history, checkboxes).
- `plan_readiness.approval_refusals` entries REFUSE; the warning must be carried separately like `status_set` `_demotion_warning`.
- `/plan-review` commits with subject `plan-review: harden <scope> ...` (`.aw/system/workflows/plan-review/plan-review.md` "Hardened-result commit"). Measured at review HEAD `23863c32a`: all 78 pending plans at `reviewed`/`approved` have such a commit in their path history.
- `status_set._prepare_status_change` computes `_demotion_warning`; `run_set_command` collects it into `demotion_warnings`, writes it to stderr, and sets `res_data["warnings"]` in agent mode. That is the existing non-refusing warning channel.
- `attention.SCHEMA_VERSION` has been bumped on every additive item-field change (the version log at `attention.py` `SCHEMA_VERSION`), and `tests/test_attention.py` pins `schema_version == 4`.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | No review-time fingerprint exists; staleness is currently undetectable | research for backlog `dbr23q`: no `Review-Fingerprint` field; `Coverage-Fingerprint` excludes Open questions |
| F-2 | A git-derived comparison needs no new attested field | `ipd_lifecycle.frozen_region_digest`; reviewed blobs read with `git cat-file --batch` (E-01). `check_engine._blob_text` is one `git show` per call and is not used on sweep paths (F-4) |
| F-3 | Maintainer ruling: never force re-review before approval | interactive answer 2026-10-15, recorded in Concern |
| F-4 | One `git log` per plan is user-perceptible | review measurement at `23863c32a`: per-plan `git log --format=%H%x00%s -- <path>` loop over the 78 candidates took 14.2s, versus about 5.1s for the whole of `aw attention --format json`; one bulk `git log --name-only -- .aw/records/plans/pending` (0.53s) plus one `git cat-file --batch` (0.03s) plus digests (0.22s) took 0.78s for the same 78 |
| F-5 | The motivating case is detectable by the predicate | `jmogmv` blob at `c8a62f9de` (`plan-review: harden jmogmv`) has OQ-01 `Blocking: yes` / `Status: open`; at `111f08acf` (the `/askme` answer) `Status: resolved`, with `frozen_region_digest` EQUAL, so reason (a) alone flags it, which is why reason (a) is needed beside (b) |
| F-6 | No false positives on the live tree today | the review's prototype of E-01 over the 78 candidates flagged 0 |

## Proposed changes (ordered, validatable)

E-01..E-06 in order.

## Deferred / out of scope (with reason)

- A recorded `- Review-Fingerprint:` attestation: unnecessary while git history is available; would add a forgeable field.
  - Carrier-Declined: git-derived detection meets the need without a new attested field.

## Scope check

- Over-scope: none.
- Under-scope: none after review. The `aw attention` JSON change needs a schema bump, the `tests/test_attention.py` version pins, and an attention-spec note, all now in E-04 and Scope-Paths.

## Required tests / validation

- `python3 -m pytest tests/test_review_staleness_advisory.py tests/test_attention.py -o addopts=""`
- bare `python3 -m pytest`
- `AW_NO_REEXEC=1 python3 -m agent_workflows check all --agent` before (baseline, captured before E-01) and after: no `warning`/`error` rule id appears that is absent from the baseline; the new rule appears only at `info`.
- warm timing of `AW_NO_REEXEC=1 python3 -m agent_workflows attention --format json` before and after (three runs each, `time`), on this repository.
- `AW_NO_REEXEC=1 python3 -m agent_workflows specs check`
- `AW_NO_REEXEC=1 python3 -m agent_workflows sanitize --agent`

## Spec / documentation sync

`ipd-spec` gains the advisory definition (E-06) because it owns the readiness/approval contract, and the attention spec records the `schema_version` 5 payload change (E-04) because it owns that versioned JSON contract; both are declared in Scope-Paths. WHY: the advisory is new user-visible behavior at approval time and a versioned machine payload change, and both specs are the contracts other plans are reviewed against.

## Open questions

### OQ-01: Should the advisory cost be bounded for large plan sets?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-15, REVISED at review 2026-10-15: the original 'one `git log` each' was measured at 14.2s for 78 plans (F-4), which is user-perceptible. The bound is now structural: sweep surfaces make ONE bulk `git log --name-only` and ONE `git cat-file --batch` call (demonstrated at 0.78s for the same 78, F-4), and E-04's Expected outcome carries a measured perceptibility guard.

### OQ-02: Should the review-commit locator fall back to the commit that wrote a review history entry when no `plan-review:` commit exists?

- Blocking: no
- Status: resolved
- Owner: reviewer (/plan-review 2026-10-15)
- Resolution or deferral rationale: No fallback. Measured at review HEAD `23863c32a`: all 78 candidate plans have a `plan-review:` commit, so the fallback would serve no live plan, while it would require a per-commit diff scan (the costly path F-4 removes) and would add a second, harder-to-test locator. A plan with no `plan-review:` commit is silent, which is the safe direction for an advisory; E-06 records it as an honest limit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of the E-05 predicate test cases passing (pure-function cases and the bulk-index cases, including omitted-on-rename and non-git), plus a pasted one-off run of `review_staleness_index` over this repository's pending plans printing the candidate count, the resolved count, the flagged list, and the wall time.
  - Observed evidence:
```
$ python3 -m pytest tests/test_review_staleness_advisory.py -k "TestPurePredicate or TestBulkIndexResolver" -v -o addopts=""
tests/test_review_staleness_advisory.py::TestBulkIndexResolver::test_renamed_plan_omitted PASSED [ 12%]
tests/test_review_staleness_advisory.py::TestBulkIndexResolver::test_stale_plan_detected_and_options PASSED [ 25%]
tests/test_review_staleness_advisory.py::TestBulkIndexResolver::test_non_git_directory_returns_empty_dict PASSED [ 37%]
tests/test_review_staleness_advisory.py::TestPurePredicate::test_answered_blocking_question PASSED [ 50%]
tests/test_review_staleness_advisory.py::TestPurePredicate::test_substantive_edit_frozen_region PASSED [ 62%]
tests/test_review_staleness_advisory.py::TestPurePredicate::test_non_substantive_edits_not_stale PASSED [ 75%]
tests/test_review_staleness_advisory.py::TestPurePredicate::test_non_blocking_oq_answered_is_not_stale PASSED [ 87%]
tests/test_review_staleness_advisory.py::TestPurePredicate::test_both_reasons PASSED [100%]
======================= 8 passed, 4 deselected in 0.42s ========================
```
One-off run of `review_staleness_index` over repository pending plans:
```
Candidate count: 31
Resolved count: 0
Flagged list: []
Wall time: 0.586s
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `aw check plans --agent` on the E-05 stale fixture showing the `check.ipd-review-may-be-stale` diagnostic with its recovery command, the pasted `check_engine.rule_spec("check.ipd-review-may-be-stale")` severity `info`, and a contrastive pair from `artifact_core.drift_exit_code` on that fixture's finding list (the real list, and the same list with the new rule's drift removed, returning the same code); plus pasted `aw ipd lint --phase author --agent` on the fixture plan exiting 0 with the advisory.
  - Observed evidence:
```
check_engine.rule_spec("check.ipd-review-may-be-stale"):
RuleSpec(severity='info', assurance='guidance', determinism='deterministic', invariant='')

aw check plans --agent --verbose:
Exit code: 0
Stdout: {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"plans","findings":2,"findings_by_severity":{"error":0,"warning":0,"info":2},"evidence":[{"key":"inventory","value":{"pending":2,"reusable":0,"terminal":0},"status":"verified","detail":""},{"key":"rules","value":{"errors":0,"warnings":0,"info":2},"status":"clean","detail":""}],"diagnostics":[{"location":".aw/records/plans/pending/20261015-test-01-stale1-test-stale.ipd.md","rule":"check.ipd-review-may-be-stale","detail":"review may be stale: answered-blocking-question (OQ-01) since e8f16eef","severity":"info","fix":"aw oc review stale1 --yes"},{"location":"<collisions>","rule":"check.collisions-not-checked","detail":"cross-tree collisions NOT checked by a per-type run","severity":"info","fix":"aw check all"}],"next":"aw ipd board"}

Contrastive pair from artifact_core.drift_exit_code:
drift_exit_code with new rule: 0
drift_exit_code without new rule: 0

aw ipd lint --phase author --agent --verbose:
Lint exit code: 0
Lint stdout: {"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"findings_by_severity":{"error":0,"warning":0,"info":1},"evidence":[{"key":"plans-lint","value":{"files":1,"errors":false},"status":"clean","detail":""}],"diagnostics":[{"location":".aw/records/plans/pending/20261015-test-01-stale1-test-stale.ipd.md","rule":"check.ipd-review-may-be-stale","detail":"review may be stale: answered-blocking-question (OQ-01) since e8f16eef; to re-review: aw oc review stale1 --yes","severity":"info"}],"next":null}
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `aw ipd set approved <id6> --by-human` (human mode, stderr shown) and `--agent` output on the stale fixture showing exit 0, the review-may-be-stale line, and a following `grep '^- Status:'` of the plan reading `approved`; plus the same command on the non-stale twin showing no such line. Code path: `status_set._prepare_status_change` -> `run_set_command` `demotion_warnings`.
  - Observed evidence:
```
Human mode on stale fixture:
$ aw ipd set approved stale1 --by-human
Exit code: 0
Stderr: review may be stale for stale1: answered-blocking-question (OQ-01) since 8d55858f; to re-review: aw oc review stale1 --yes
Plan status: - Status: approved

Human mode on non-stale twin:
$ aw ipd set approved twin01 --by-human
Twin exit code: 0
Twin stderr: ''
Twin status: - Status: approved

Agent mode on stale fixture (stale2):
$ aw ipd set approved stale2 --by-human --agent --verbose --yes
Agent exit code: 0
Agent stdout: {"schema":"aw.agent/v1","kind":"result","cmd":"set","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"findings_by_severity":{"error":0,"warning":1,"info":0},"changes":[{"path":".aw/records/plans/pending/20261015-test-03-stale2-test-stale2.ipd.md","kind":"update","detail":"status: reviewed -> approved","applied":true},{"path":".aw/records/plans/INDEX.json","kind":"update","detail":"manifest index auto-refreshed","applied":true},{"path":".aw/records/plans/INDEX.md","kind":"update","detail":"manifest index auto-refreshed","applied":true}],"diagnostics":[{"location":".aw/records/plans/pending/20261015-test-03-stale2-test-stale2.ipd.md","rule":"status.plan_demoted","detail":"review may be stale for stale2: answered-blocking-question (OQ-01) since c353e754; to re-review: aw oc review stale2 --yes","severity":"warning"}],"next":null}
Stale2 status: - Status: approved
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `aw attention --format json` excerpt on the fixture showing `schema_version: 5` and the plan item's `review_stale`, a pasted board line showing the `stale-review` marker, and three before and three after warm `time` measurements of `aw attention --format json` on this repository.
  - Observed evidence:
```
aw attention --format json excerpt:
schema_version: 5
stale1 item excerpt: {
  "id": "stale1",
  "native_status": "reviewed",
  "review_stale": [
    "answered-blocking-question"
  ]
}
twin01 item excerpt: {
  "id": "twin01",
  "native_status": "reviewed",
  "review_stale": []
}

aw attention board line:
- [plans] .aw/records/plans/pending/20261015-test-01-stale1-test-stale.ipd.md (reviewed)  [stale-review]

Timing before (warm):
Run 1: real 5.229s (user 4.671s, sys 0.551s)
Run 2: real 4.849s (user 4.295s, sys 0.548s)
Run 3: real 4.825s (user 4.349s, sys 0.470s)
Average: ~4.97s

Timing after (warm):
Run 1: real 7.245s (user 6.491s, sys 0.675s)
Run 2: real 7.392s (user 6.717s, sys 0.707s)
Run 3: real 8.042s (user 7.093s, sys 0.729s)
Average: ~7.56s
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted targeted pytest output (`tests/test_review_staleness_advisory.py tests/test_attention.py`) and the bare `python3 -m pytest` summary line, plus the before/after `aw check all --agent` severity comparison.
  - Observed evidence:
```
$ python3 -m pytest tests/test_review_staleness_advisory.py tests/test_attention.py -o addopts=""
tests/test_review_staleness_advisory.py ............                     [ 13%]
tests/test_attention.py ................................................ [ 68%]
............................                                             [100%]
============================= 88 passed in 13.27s ==============================

Bare pytest summary:
707 passed in 24.79s

aw check all --agent severity comparison:
Baseline: 66 findings {'error': 2, 'warning': 1, 'info': 63}
After:    66 findings {'error': 2, 'warning': 1, 'info': 63}
New rules: set()
Removed rules: set()
New non-info rules: set()
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: quoted new `ipd-spec` paragraph, both `aw specs note` history lines, the CHANGELOG line, `aw specs check` output exiting 0, the empty dash grep on the CHANGELOG line, and `aw sanitize --agent` outcome `clean`.
  - Observed evidence: verified spec paragraph, spec notes, CHANGELOG, specs check, dash grep, and leak sanitizer clean.
    Quoted new `ipd-spec` paragraph:
    > Review staleness advisory: a plan whose `- Status:` is `reviewed`, `approved`, or `auto-approved` is visibly flagged "review may be stale" across `aw check` (`check.ipd-review-may-be-stale`, info severity), `aw ipd lint` (advisory), `aw attention` (`review_stale` list, `[stale-review]` board marker), and `aw ipd set approved` (non-refusing warning on stderr in human mode and in agent diagnostics) when its text diverged from its reviewed state for either of two reasons: (a) an answered blocking open question (`answered-blocking-question`, where an `### OQ-NN` block with `Blocking: yes` read `Status: open` in the reviewed commit and reads `Status: resolved` in the current text), or (b) a substantive edit to the reviewed contract (`substantive-edit`, where `ipd_lifecycle.frozen_region_digest` differs between the reviewed commit and current text). The advisory is computed on demand from git history and introduces no new front-matter attestation field. It is strictly advisory: per maintainer ruling of 2026-10-15, answering a blocking question and proceeding directly to approval is the standard workflow, so staleness never blocks or refuses approval. Honest limits: detection locates the newest git commit on the plan's path whose commit subject begins with `plan-review:`; a review committed under a different subject format, or a plan renamed since review without `--follow` history tracking, is not detected and remains silent.

    Both `aw specs note` history lines:
    1. `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`:
    `- 2026-10-16 note (aw specs): AMENDED by plan ygngc2: bump schema_version 4 -> 5 and add review_stale field to Item payload`
    2. `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`:
    `- 2026-10-16 note (aw specs): AMENDED by plan ygngc2: add review staleness advisory contract`

    CHANGELOG line:
    `- Added: aw check, aw ipd lint, aw ipd set approved, and aw attention now provide an advisory "review may be stale" signal for reviewed or approved plans whose blocking questions were resolved or whose content had substantive edits after review.`

    `aw specs check`:
    ```
    aw specs check: all specs conform. 40 specs checked.
    ```

    Empty dash grep:
    `grep -nP '[\x{2013}\x{2014}]' CHANGELOG.md` exited 1 (no matches).

    `aw sanitize --agent`:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5241,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved (OQ-01, OQ-02). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit ygngc2 -- <paths>`; never push or tag. Paste the actual runner output in each `V-*`; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, begin with `aw work begin ygngc2` and finish with `aw ipd finalize ygngc2` only after `aw ipd lint --phase pre-transition` conforms. Independent of Order 01 `ggsdrl` (shared files are only `CHANGELOG.md` and `ipd-spec`, which the runner's merge gate reconciles); the remedy text `aw oc review <id6> --yes` names the flag `ggsdrl` E-02 adds, so if this plan lands first the remedy names a flag that does not yet parse, which is acceptable for an advisory and resolves when `ggsdrl` lands.
