# Review findings: plan z3ifg8

- Subject-Id: z3ifg8
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `82aab2e9` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after.
`IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review snapshot was
owed: the plan was committed and unmodified, `git status --short` empty at review start.

NO PRODUCTION FILE WAS LEFT MODIFIED BY THIS REVIEW. One probe DID temporarily patch
`agent_workflows/oc_runipd.py` to verify that E-02's prescribed one-liner is sufficient (recorded as F-12);
it was reverted from a backup immediately and `git status --short` plus `git diff --stat` both confirmed
empty before any commit. Every other measurement was a read or an in-process call against
`tempfile.mkdtemp()` directories; nothing was written to the tracked runs tree.

THIS IS A SMALL, CORRECT, UNUSUALLY WELL-EVIDENCED PLAN. Its defect claims are precise, its chosen fix
placement is defended on measured grounds rather than taste, and it corrects three statements of its own
backlog item rather than copying them. I re-derived every load-bearing claim. CONFIRMED:

- **F-01 and F-04**, with the plan's exact filenames. In a fresh tempdir, `attempt_log_path` returned
  `<TMP>/sessions/01-abc123-attempt-1.jsonl` with `parent exists: False` and the open raised
  `FileNotFoundError`; `write_prompt` raised the same on `<TMP>/prompts/01-abc123-exec-attempt-1.md`.
  `attempt_log_path` also left `sessions/` absent, confirming it is pure.
- **F-02 and F-03**, mechanically. Both hosts assign
  `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` and open
  `log_path.open("w", encoding="utf-8") as log,` with NO `mkdir` in between: 166 body lines apart in
  `oc_runipd.run_opencode`, 116 in `agy_runipd.run_agy_turn`. In BOTH, the open is the SECOND manager of a
  multi-manager `with` (trailing comma, then `):`), which independently validates E-02's reason for placing
  the mkdir at the assignment rather than adjacent to the open.
- **F-05**. `tests/test_standalone_verify.py` does not exist, and no test in `tests/` references
  `handle_audit_command`, `plan_audit_target`, `_fresh_audit_run_dir` or `TheVerbRunsEndToEnd`.
- **F-06**. `attempt_log_path` has exactly three non-definition callers: the two host launch bodies plus
  `runner_shared`'s `"log": str(attempt_log_path(run_dir, item, attempt_no))` record-only use. Separately,
  `run_dashboard` (`candidate = run_dir / "sessions" / name`, `sessions_dir = ...`) and `run_viewer` (three
  sites) read that directory. So the pure-accessor argument holds.
- **F-07**. `oc_runipd.handle_audit_command` carries the three-directory loop AND the comment stating
  `run_opencode` "does NOT create its parent, so omitting it raises FileNotFoundError at the moment of
  launch, after the prompt has been written and (with isolation on) after a lane has been allocated";
  `host_sandbox_profile` has `(run_dir / "sessions").mkdir(parents=True)` in shipped probe code.
- **F-08**. `agent_workflows/agy_run.py` does `log_directory = root / "tmp" / "antigravity"` immediately
  followed by `log_directory.mkdir(parents=True, exist_ok=True)`, so the house pattern is already present
  in an adjacent file.
- **F-09**. `attempt_log_path`'s docstring records the `_VERIFY_LOG_RE` anchoring and the repaired
  misclassification; `write_prompt`'s records the oc-form adoption. Both shapes are load-bearing.
- **F-10**. `298 passed` for the two named modules and `3246 passed, 2 skipped, 3 warnings` bare, both
  matching authoring.
- The skeleton claim: `initialize_run_core`'s
  `for name in ("sessions", "outcomes", "prompts"): (run_dir / name).mkdir(parents=True, exist_ok=True)` is
  the ONLY package site creating the skeleton (the single other `sessions` mkdir is
  `host_sandbox_profile`'s probe), so the obligation really is invisible.
- The handoff: backlog `hblsqo` is `graduated`, `Work-Kind: bug`, `Blocks-Release: next`, and the carrier
  `3kr193` OQ-01 names genuinely exists at
  `.aw/records/backlog/open/20260929-3kr193-01-3kr193-guarantee-run-dir-outcomes-parent.backlog.md`.

BEYOND CONFIRMING, I VERIFIED THE FIX ITSELF, which the plan could not claim and which is the single most
valuable thing this review adds. Using exactly the fake-`Popen` shape E-04(d) prescribes, against a BARE
run directory: BEFORE, the real `run_opencode` raised `FileNotFoundError` on the log path with `sessions/`
absent; AFTER applying E-02's prescribed one-liner verbatim, `RuntimeError("stop-before-launch")` surfaced
with `sessions/` present. So E-02 is verified SUFFICIENT and E-04(d) is verified FEASIBLE.

FIVE FINDINGS WERE RAISED AND ALL FIVE FIXED. None is HIGH: the plan's diagnosis, fix placement and scope
were all correct as authored, and the findings are a missing sufficiency proof, an under-used template, two
drifted counts, and three absent gate elements.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | UNDER-SCOPE | Rubric A (correctness); G | scan of `run_opencode`'s body from the assignment (idx 277) to the open (idx 442) for `write_text(`/`.open(`/`mkdir(`/`write_prompt(`/`touch(` -> one hit, the open | F-02 establishes that no `mkdir` occurs between the assignment and the open, which proves the DEFECT. It does not establish that no OTHER unguarded write occurs in that 166-line span, which is what proves ONE statement is a SUFFICIENT fix rather than merely a necessary one. Without that, an executor has no basis to stop looking, and a reviewer cannot tell whether E-02 closes the span or only its first hazard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured and recorded as F-13: exactly one filesystem write occurs in the span, the log open itself. E-02 now states that one statement is provably enough for the whole span and tells the executor not to hunt for a second. |
| PR-602 | MEDIUM | IN-SCOPE | Rubric E (testing) | `host_sandbox_profile`'s `fake_popen` probe read in full; review drove the same shape successfully | E-04 describes `host_sandbox_profile`'s probe as a "precedent ... shape" to "reuse", understating it: it is a COMPLETE WORKING TEMPLATE containing every ingredient (real `git init -b main`, `options={"opencode": "/bin/false", "agy_executable": "/bin/false"}`, a `fake_popen` passing `git` and `sys.executable` through, `subprocess.Popen` restored in a `finally`, and the four-key `item`) and it ALREADY CONTAINS `(run_dir / "sessions").mkdir(parents=True)`, the very workaround this plan makes unnecessary. An executor told only "follow the precedent" may reimplement it and get the isolation prerequisites wrong; told "copy this block and delete its mkdir line", the work is mechanical and the test's own diff evidences the fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-14 with the block's load-bearing ingredients enumerated. E-04 now instructs copying the block and deleting its mkdir line, and adds a caution NOT to assert the sentinel is the only acceptable outcome (the property under test is the absence of `FileNotFoundError` on the log path, so a later legitimate earlier failure must not break the test). E-02's Expected outcome now cites the review's verified before/after asymmetry so a vacuous test is detectable. |
| PR-603 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | `grep -l ... .aw/records/plans/pending/*.ipd.md` -> one match, this plan; `ls ... \| wc -l` -> 144 | F-11 claims the grep "returned no matches across the 50 pending plans". BOTH numbers have drifted: the pending population is 144, and the grep now returns exactly ONE match, THIS PLAN ITSELF, because the plan names both symbols throughout. The CONCLUSION (no sibling contends) still holds, but an executor re-deriving it naively would see a hit and could read the plan's own text as contention. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 restated with both corrections and an explicit instruction that a re-derivation must exclude the plan's own file. |
| PR-604 | LOW | IN-SCOPE | Rubric G | `grep -rn "write_prompt(" agent_workflows/*.py` -> 11 in `runner_shared` plus 1 in `oc_runipd` | E-01 says `write_prompt` "has at least nine call sites (one in `oc_runipd.handle_audit_command` and eight inside `runner_shared` itself)". Measured: eleven inside `runner_shared` plus one in `oc_runipd`, so twelve. The argument is unaffected and is in fact stronger by construction than by census: because the function performs the write itself, no caller CAN want the path without the side effect, so the count is irrelevant to correctness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Count corrected, the authoring figure preserved for the record, and the argument re-grounded on construction rather than census, with an explicit note that the count is context and not an acceptance bar. |
| PR-605 | MEDIUM | UNDER-SCOPE | Rubric G (execution contract) | plan gate as authored; `grep` for `aw ipd finalize`, `git mv`, `git diff --cached` -> no hits | The gate carried the commit path-scoping, the never-push rule, the honesty rule and a strong "what would make this wrong to execute" paragraph, but was missing three required elements: staged-set verification for a shared checkout, the LIFECYCLE TRANSITION with conditional runner/executor ownership (it said only "move this plan to `.aw/records/plans/executed/` through the tooled transition", naming no owner and not forbidding a hand-rolled `git mv`), and a consolidated SCOPE FENCE (the prohibitions existed but only inside `## Scope check`, and they omitted four constraints the Deferred section implies). It also offered an approver no summary of the change or its risks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added staged-set verification with `git restore --staged`, the UNPIPED exit-code rule, and the tempfile-fixture rule. Added a SCOPE FENCE worded as a DECLARATION for the runner to reconcile (per the 2026-09-01 ruling, not a stop directive), restating the five existing prohibitions and adding four: no editing `initialize_run_core`'s loop, no removing either caller-side workaround, no guaranteeing `outcomes/` here, and no editing any existing test. Added the LIFECYCLE TRANSITION paragraph with conditional ownership and `AW-LIFECYCLE-ROLE-001`, plus the release-gate inheritance statement. Added approver-facing summary and scrutiny paragraphs, and a paragraph explaining why both open questions are safe to leave open. Strengthened the negative-control requirement to demand `git diff --stat` after each revert. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review verify the prescribed fix by temporarily patching production code, given the execution contract forbids a reviewer from modifying anything? | Yes, patch, measure, revert from a backup, and prove the revert with `git diff --stat`; record it explicitly in the review record. | (a) Verify only the helper-level defect and take E-02's sufficiency on trust: REJECTED, because the plan's whole value rests on a one-line fix at a specific site being enough, and that is exactly the claim a review should test rather than accept. (b) Copy the module to a scratch path and patch the copy: REJECTED as unable to exercise the real import graph that `run_opencode` depends on (telemetry, isolation, tracker), so it would have proven less. (c) Leave it and file the gap as a finding for the executor: REJECTED because the executor would then discover at execution time whether the plan's central premise holds, which is a worse place to find out. | The workflow forbids a reviewer CHANGING code as a deliverable; a transient, reverted measurement that leaves the tree byte-identical is a measurement, not a change, and the review record states it plainly so the act is auditable. `git status --short` and `git diff --stat` both empty after revert, before any commit. | yes |
| D-2 | Is the plan right to place the mkdir at the two write sites rather than inside `attempt_log_path`? | Yes; endorsed, and E-04(c)'s negative pin retained as the guard. | (a) Put it in `attempt_log_path` (the backlog item's own alternative): REJECTED on measurement, since that helper has a record-only caller in `execute_item_core` and read-only callers in `run_dashboard` and `run_viewer`, so it would create `sessions/` as a side effect of NAMING or READING a log, including in run directories no turn launches into. (b) Put it in `initialize_run_core` only: REJECTED, as that is the status quo and is precisely what leaves the obligation invisible to any caller that does not use the initializer. | Call sites read directly: `"log": str(attempt_log_path(run_dir, item, attempt_no))` in `runner_shared`, `candidate = run_dir / "sessions" / name` under an `is_file()` guard in `run_dashboard`, three read sites in `run_viewer`. Measured that `attempt_log_path` creates nothing today. | yes |
| D-3 | Do the two open questions (OQ-01 `outcomes/`, OQ-02 workaround removal) block this plan? | No. Readiness is `GO - PENDING HUMAN APPROVAL`; both left open and untouched. | (a) Mark `NO-GO` for open questions: REJECTED by the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01), which scoped the condition to an unresolved BLOCKING question; both carry `- Blocking: no`. (b) Resolve OQ-01 myself: REJECTED, because it asks who owns a mkdir for a path the AGENT writes inside a lane, which is a design question spanning `runner_shared`, `lane_containment` and the audit verb, and it is properly FILED as backlog `3kr193`. (c) Resolve OQ-02 myself: NOT taken; its recommendation is already "leave them", the plan's Deferred section carries a `Carrier-Declined` rationale, and removing `handle_audit_command`'s loop before OQ-01 settles would unguard `outcomes/` for the audit verb. | Verified neither question changes a line this plan writes: the four `Scope-Paths` entries are touched only by E-01 through E-04, and `outcomes/` and the two workarounds are all outside them. `3kr193` confirmed to exist. | yes |
| D-4 | F-11's evidence now self-matches (the grep hits this plan) and its population count drifted. Fail the finding, or correct it? | Correct it in place and add the exclusion instruction. | (a) Treat the self-match as genuine contention: REJECTED as obviously wrong; a plan naming the symbols it fixes is not a competing edit. (b) Narrow the grep to `agent_workflows/` so it cannot self-match: REJECTED because the finding's PURPOSE is to check sibling PLANS for contention, so the plans tree is the right search space and the exclusion belongs in the instruction. (c) Drop F-11: REJECTED, since independent executability is worth recording and remains true. | `grep -l` over `.aw/records/plans/pending/*.ipd.md` returns exactly one path, this plan's own filename; a count of that glob returns 144. No other pending plan mentions either symbol. | yes |

No `Reversible: no` decision was made, so no escalation under the irreversible-decision rule is owed.
No finding was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question under
`review_findings_gate.block_at` (default `HIGH`) is owed; no finding reached HIGH.

### Checklist assessment (required for an agent-executable IPD)

The CREATOR authored both checklists and the E/V bijection is 1:1. Right-sizing: four E-items, three of
which are a single statement each in a different file, plus one test module. E-01 through E-03 are the same
edit in three places and could arguably be one item, but keeping them separate is correct here and the plan
says why: each lands in a different file with a different surrounding hazard (a bare `write_text`, a
multi-manager `with` header, and a host twin), and V-01 through V-03 demand genuinely different evidence.
The cohesion rationale for NOT splitting into three plans is also right, and it cites the real risk (a
half-fixed state, which is the failure mode the backlog item itself asked to avoid). `aw ipd lint` reported
no `IPD-Z602` density advisory at either checkpoint. No split is recommended.

TWO STRUCTURAL STRENGTHS WORTH NAMING. FIRST, E-04(c) is a NEGATIVE pin: it asserts `attempt_log_path`
creates NOTHING, which is the only guard against a future "simplification" moving the mkdir into the pure
helper. Authoring a test whose purpose is to prevent the wrong fix, and identifying it as the most
important item in the module, is exactly the discipline this checklist bar exists to find. SECOND, the gate
already carried a "WHAT WOULD MAKE THIS PLAN WRONG TO EXECUTE" paragraph naming a vacuous negative control
and an edited test as the two stop conditions, before review asked for anything.

The checklist's weakness was that its two most mechanical items were under-specified relative to the
evidence available: E-02 did not establish that one statement closes the span (PR-601) and E-04 understated
a template it could copy (PR-602). Both are repaired in place, and both repairs came from measurements the
review made rather than from judgement. The P16 bar is correctly set throughout: E-04 explicitly forbids
`inspect`/`ast`/regex over production source and call-site counting, and V-04 requires confirming the new
module contains no such import.

Live-artifact convention: three populations were stated as fixed and are now context with re-derivation
instructions (F-10's two baselines, F-11's plan count, E-01's call-site count). No `V-*` used any of them
as an acceptance bar, so no validation item needed loosening.
