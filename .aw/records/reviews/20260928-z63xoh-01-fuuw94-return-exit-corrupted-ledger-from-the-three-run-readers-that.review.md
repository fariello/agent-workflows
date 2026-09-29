# Review findings: plan fuuw94

- Subject-Id: fuuw94
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9c665d00` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-4/` copy. No production
code was modified by this review; the post-change state was measured by rebinding the three handlers
from a pytest plugin living OUTSIDE the tree, with `git status --short` empty throughout.

**EVERY ONE OF THE SEVEN AUTHORED FINDINGS REPRODUCED, AND THE PLAN'S DIAGNOSIS IS CORRECT.** F-1:
`grep -c "except store.LedgerCorruption"` returns exactly 10 and 8 non-definition
`EXIT_CORRUPTED_LEDGER` usages exist. F-2: the two byte-identical
`{"ok": False, "error": err_msg, "corrupted": True, "exit_code": 2}` handlers sit in `_run_show` and
`_run_evidence`, and `_run_verify_ledger`'s `not chain_ver.clean` branch carries the third
`"exit_code": 2` beside `"chain_clean": False`, reached through a return value rather than an
exception exactly as claimed. F-3 reproduces to the digit: a real two-record ledger with `prev_hash`
tampered at seq 1 yields `show 2, evidence 2, verify-ledger 2, status 5, next 5, resume 5`, so the
"read-only is lenient" hypothesis is refuted by three read-only verbs already returning 5. F-4
reproduces both halves: `a7ce5ce9` is the adding commit and its `run_cli.py` contains 0 `EXIT_`
constants and 12 bare `return 2`, while `caf658b4` introduced the table. F-5: the `Contract:` line
says `exit 2 = invocation error, missing ledger, or corrupted hash chain / unparseable JSON` beside
`EXIT_CORRUPTED_LEDGER: int = 5`. F-6: `tests/test_run_recovery_cli.py` does not exist, `19313eed`
shows `2737 ----`, and `EXIT_CORRUPTED_LEDGER` greps to zero across `tests/`. F-7 holds.

**REVIEW ALSO MEASURED THE FIX ITSELF, WHICH THE PLAN DID NOT.** Staging E-01..E-03 in memory leaves
the bare suite at `3160 passed, 2 skipped`, identical to the unpatched baseline, and gives `60 passed`
on `tests/test_run_viewer.py` plus `tests/test_runs_repo_alias.py`, the two modules nearest this
surface. The post-fix sweep reads `5, 5, 5` with `corrupted:true` and `chain_clean:false` both intact,
and the absent-ledger control still exits 2. So no shipped test pins the old value, and the behavior
change is verified safe BEFORE approval rather than after (added as F-10).

**WHAT REVIEW FOUND** is five findings, none of which touch the three-site code change. Two are
consequential: E-04 as written would have traded one false docstring claim for another, and E-05's
fixture is refused by schema validation in five distinct ways the plan never recorded.

**E-04 WOULD HAVE TRADED ONE FALSE DOCSTRING CLAIM FOR ANOTHER (PR-701, MEDIUM).** The `Contract:`
block is a PARTIAL table: it enumerates exits 0, 1, 2 and 7 only, with 3, 4, 5 and 6 absent entirely.
E-04 says to strike the corruption clause from the exit-2 line, which leaves
`exit 2 = invocation error, missing ledger` reading as an exhaustive pair. It is not:
`EXIT_INVALID_INVOCATION` is ALSO what the `except Exception` read-failure branches return, and those
are the branches E-01 and E-02 deliberately preserve. A reader of the corrected docstring would
conclude an unexpected read failure now exits 5, which is precisely the class of wrong-contract
statement F-5 exists to remove. The opposite over-correction is also live and worth forbidding
explicitly, since an executor handed "the table is incomplete" may write out all eight codes, which
would be four unmeasured lines of gold-plating in a three-line fix.

**E-05's LEDGER FIXTURE IS NON-OBVIOUS AND A NAIVE `append` IS REFUSED FIVE DIFFERENT WAYS
(PR-702, MEDIUM).** `RunLedgerStore.append` schema-validates every record and raises
`SchemaInvalidRecordError`. Review needed five attempts to land a valid two-record ledger. Measured:
`schema_version` must be the INT `2` (`"1"` is refused `RL-E011`); `actor` must be in
`run_ledger_schema.ROLES` (`test` is refused `RL-E014`); `run_id` must match `^run-[0-9a-f]{8,}$`
(`r1` is refused `RL-E015`); a `kind="run"` record additionally requires `repo`, `workflow_digest`,
`requirement_digest` and `head`; and `item`, `requirement` and `note` are all absent from
`RECORD_KINDS` (refused `RL-E013`), while `step_attempt` works with the `_KIND_FIELDS`-declared
`step`, `state` and `attempt`. E-05 is the plan's largest E-item and this is where it stalls; an
executor rediscovering five refusals one at a time burns the focused pass the right-sizing rule
assumes.

**THE PLAN SPECIFIED NO METHOD FOR ITS PRE-FIX COMPARISON, IN A SHARED CHECKOUT (PR-703, MEDIUM).**
Required-tests said to capture the pre-fix failure "before applying E-01..E-03 (or by stashing them)".
`agent_workflows/run_cli.py` is a shared-checkout file, and a stash-then-restore around a
minute-long suite run can silently discard a co-worker's concurrent edit to it. The repository's own
contract is explicit that uncommitted changes another party made are not yours to revert. Review
performed every pre/post comparison through an out-of-tree pytest plugin instead, which is both safer
and cheaper, and the plan should mandate that.

**TWO BASELINES WOULD HAVE GONE STALE BEFORE EXECUTION (PR-704, LOW).** Required-tests and V-05
asked for the bare suite "with actual output pasted" but stated no bar, while three sibling plans
reviewed in this same sweep each carried a hard-coded total that had already drifted (one by 71
tests). Review measured `3160 passed, 2 skipped` here; that number is context, not a bar, and the
plan now says so and requires the executor to re-derive their own. The same applies to the control
rows: V-05 required the three in-scope rows red pre-fix but never required the three CONTROL rows
green pre-fix, which is what makes them controls rather than decoration.

**ONE INHERITED CITATION IS STALE, THOUGH QUOTED FAITHFULLY AND HARMLESS HERE (PR-705, LOW).** The
plan's Step-0 conventions quote `_emit_error`'s docstring, which claims
`tests/test_run_cli_ledger_message.py` "still pins the unknown-target payload's key set exactly".
That file does not exist, almost certainly removed by the same `19313eed` trim F-6 already measures.
The plan quoted the docstring accurately, so the defect is the docstring's; and it is not
load-bearing, because all three in-scope sites call `_emit_machine` directly and never `_emit_error`.
Recorded so an executor who goes looking does not conclude the plan is wrong, and so the dangling
reference is on the record rather than silently inherited a third time.

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed
and none was written. OQ-01 survives review unchanged and is UPHELD on strengthened evidence: review
independently reproduced both of its two grounds (the `2,2,2,5,5,5` sweep refuting leniency, and the
git provenance showing the split is migration residue), so the resolution is not merely plausible but
measured twice. All four `Carrier-Declined` rows are sound; the spec-5.6 conflict they decline to
carry is genuinely recorded in-tree at spec `25kzda` Section 5.6 as an `UNRECONCILED CONFLICT`, and
that row itself attributes `5` to ledger corruption in the shipped `run_cli` table, which is the
direction this plan moves.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | MEDIUM | IN-SCOPE | A. Correctness (documentation honesty) | the `Contract:` block's four exit lines (0, 1, 2, 7); the eight `EXIT_*` definitions incl. `EXIT_INVALID_INVOCATION: int = 2  # bad invocation / missing ledger`; the `except Exception` branches in `_run_show` and `_run_evidence` both emitting `"exit_code": 2` and returning 2 | E-04 WOULD HAVE TRADED ONE FALSE DOCSTRING CLAIM FOR ANOTHER. The block is a PARTIAL table (3/4/5/6 absent), so striking the corruption clause leaves `exit 2 = invocation error, missing ledger` implying those are the only two causes, when `EXIT_INVALID_INVOCATION` is also the generic read-failure code the branches E-01/E-02 deliberately PRESERVE return. A reader would conclude a read failure now exits 5. The opposite over-correction (writing out all eight codes) is equally live and is gold-plating. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one added sentence in the E-item and one in its V-item) | FIXED | Added F-08 with the block's actual contents and the two consequences. E-04 gained a "WRITE THE EXIT-2 LINE AS A RESIDUAL, NOT AS A NEW ENUMERATION" paragraph requiring the read-failure case be named and forbidding an eight-code expansion; its Expected outcome now includes the read-failure property; V-04 requires confirming both. |
| PR-702 | MEDIUM | UNDER-SCOPE | E. Testing / G. Plan executability | five successive `SchemaInvalidRecordError` findings (`RL-E011` schema_version type, `RL-E014` unknown actor role, `RL-E015` run_id shape, `RL-E020` per-kind required fields, `RL-E013` unknown kind for `item`/`requirement`/`note`); the module symbols `ROLES`, `_RUN_ID_RE`, `RECORD_KINDS`, `_KIND_FIELDS` | E-05's LEDGER FIXTURE IS NON-OBVIOUS AND A NAIVE `append` IS REFUSED FIVE WAYS, none recorded in the plan. `RunLedgerStore.append` schema-validates and raises; review needed five attempts. E-05 is the plan's largest item and this is where execution stalls, one refusal at a time, defeating the focused-pass assumption the right-sizing rule makes. | C:Low; U:Low; S:Low; F:Low; Overall:Low (record the measured requirements; no design change) | FIXED | Added F-09 with every refusal code and the working record shapes. E-05 gained a paragraph naming the exact minimum (int `schema_version=2`, a `ROLES` member, `_RUN_ID_RE`-matching `run_id`, the four extra `run` fields, `step_attempt` with `step`/`state`/`attempt`), instructing the executor to DERIVE role and kind fields from the module symbols rather than transcribe review's literals, and requiring `verify_chain(...).clean` True-then-False. V-05 requires that integrity proof as pasted evidence. |
| PR-703 | MEDIUM | IN-SCOPE | C. Architecture and operability (shared-checkout safety) | the plan's "or by stashing them" instruction; AGENTS.md shared-checkout rule; review's own out-of-tree plugin method with `git status --short` empty before and after | THE PRE-FIX COMPARISON HAD NO SAFE METHOD SPECIFIED. `run_cli.py` is a shared-checkout file and a stash-then-restore spanning a minute-long suite run can discard a co-worker's concurrent edit, which the repository contract forbids. An in-memory wrap is both safer and cheaper and is what review used for every measurement here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests gained a "STAGE ANY PRE-FIX COMPARISON IN MEMORY, NOT BY MUTATING A TRACKED FILE" rule naming the plugin approach and requiring `git status --short` empty before and after; V-05(5) requires that paste as evidence. |
| PR-704 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | review's clean-tree bare run `3160 passed, 2 skipped, 3 warnings in 59.44s`; the same count under the staged change; V-05's original three-artifact list omitting any control-row assertion | TWO EVIDENCE REQUIREMENTS WERE UNDER-SPECIFIED. The suite requirement named no bar, inviting a transcribed total that drifts (three sibling plans in this sweep each carried one that already had). And V-05 required the three in-scope rows RED pre-fix but never the three CONTROL rows GREEN pre-fix, so a control that silently failed would go unnoticed and prove nothing about convergence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests now demand a re-derived own baseline, label review's figure as context, and add the targeted neighbour-module run with its measured `60 passed`. V-05 expanded from three artifacts to five, including the pre-fix control-rows-green requirement and the delta-against-your-own-baseline rule. Added F-10 recording the safety measurement. |
| PR-705 | LOW | IN-SCOPE | A. Correctness (evidence accuracy) | `ls tests/test_run_cli_ledger_message.py` -> No such file; the `_emit_error` docstring sentence; `grep -n "_emit_machine("` showing all three in-scope branches use `_emit_machine` | ONE INHERITED CITATION IS STALE. The plan's conventions quote `_emit_error`'s docstring claiming `tests/test_run_cli_ledger_message.py` pins the payload key set; that file does not exist. The plan quoted faithfully, so the defect is the docstring's, and it is harmless here because no in-scope site calls `_emit_error`. Worth recording rather than inheriting silently a third time, and worth bounding so an executor does not read the absence as licence to reshape the payload. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11 establishing both the absence and the irrelevance (all three sites use `_emit_machine`). The Step-0 conventions bullet now carries the caveat, states that the convention still holds on its other two verified grounds, and forbids treating the missing test as licence to reshape the payload. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `Contract:` block is a partial table (0/1/2/7 only). Complete it to all eight codes, or keep it partial and only fix the false clause? | KEEP IT PARTIAL: move the corruption clause to a new exit-5 line, make the surviving exit-2 line name the read-failure case, and forbid a full expansion. | (a) Write out all eight codes - rejected: the constant definitions are already the authority, review measured nothing about exits 3/4/6, and four unmeasured lines in a three-line fix is gold-plating the rubric tells me to remove. (b) Strike the clause and leave the rest as-is (the plan's original wording) - rejected: that makes the exit-2 line newly false, since the preserved `except Exception` branches return 2 for a read failure. (c) Leave the docstring alone - rejected: F-5 correctly identifies it as documenting the bug as intended, so one of the two statements must change. | The block's four exit lines read directly; `EXIT_INVALID_INVOCATION: int = 2  # bad invocation / missing ledger`; the two `except Exception` branches emitting `"exit_code": 2`; the plan's own decision to leave those branches untouched. | yes |
| D-2 | Is `step_attempt` the right seq-1 record kind for the E-05 fixture, or should the plan name a different one? | NAME `step_attempt` AS THE MEASURED-WORKING CHOICE, but instruct the executor to derive its required fields from `run_ledger_schema._KIND_FIELDS` rather than transcribe them. | (a) Name nothing and let the executor discover a kind - rejected: review needed five attempts and the discovery cost is real; PR-702 exists because that cost was unrecorded. (b) Transcribe the exact literals as a fixed recipe - rejected: that pins a snapshot of the schema, so a future field addition breaks the test for a reason unrelated to this contract, which is the same staleness class as PR-704. (c) Use a v1 kind to avoid the schema_version 2 requirement - rejected: not attempted, so recommending it would be unmeasured, and `step_attempt` is verified working. | `RECORD_KINDS_V1` / `RECORD_KINDS_V2_ONLY` read directly (`item`/`requirement`/`note` absent from both); `_KIND_FIELDS["step_attempt"] == (('step', str), ('state', str), ('attempt', int))`; the working two-record append and its `clean=True` -> `clean=False` transition. | yes |
| D-3 | OQ-01 is already `resolved` with `Owner: none`. Does review accept the resolution, or reopen it as a human decision? | ACCEPT AND UPHOLD IT. Both grounds were independently re-measured and both hold; no escalation. | (a) Reopen as a maintainer question - rejected: the repository answers it twice over, and the plan-authoring contract directs against asking a human what the repo already answers. (b) Accept without re-measuring - rejected: OQ-01 is the item's own stated DECISION NEEDED and carries the whole direction of the fix, so accepting it on the plan's word would be the review doing no work at the one point it matters most. | Independently reproduced the `2,2,2,5,5,5` sweep (refuting the read-only-leniency ground) and both git facts (`a7ce5ce9`: 0 constants, 12 bare `return 2`; `caf658b4` added the table); spec `25kzda` Section 5.6 itself attributing `5` to ledger corruption in the shipped `run_cli` table. | yes |
| D-4 | Should review mark this plan NO-GO for any finding? | NO. All five findings were FIXED by in-place revision, so no unfixed BLOCKER/HIGH remains and the correct readiness is `go-pending-approval`. | (a) NO-GO on the two MEDIUMs - rejected: the workflow is explicit that severity is for reporting and the Fix Bar alone decides fixing; both fixes are Low Remediation Risk prose-and-evidence edits touching no code. (b) Escalate one as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and none was left unfixed. | The `plan-review` Fix Bar and readiness vocabulary (a clean reviewed plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`); `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` unset in `.aw/config/project.json` so the default `HIGH` threshold applies and no finding sits at it. | yes |
