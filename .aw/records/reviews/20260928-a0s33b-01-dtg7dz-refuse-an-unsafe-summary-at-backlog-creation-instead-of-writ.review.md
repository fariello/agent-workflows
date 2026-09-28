# Review: refuse an unsafe --summary at backlog creation instead of writing an item the checker immediately flags, child dtg7dz (Set a0s33b)

- Subject-Id: dtg7dz
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `935e0be3`. `aw ipd lint --phase author --agent` reported `conforming` BEFORE semantic
review and `--phase review-finalize --agent` after every revision. Every claim below was RE-MEASURED in
this lane by importing the modules and driving the verbs against temporary fixture repositories, and for
the two uncovered write paths by running the real CLI; none was read off the plan.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS EVIDENCE SURVIVED RE-MEASUREMENT WHOLE. Every finding F-01
through F-11 reproduced. `run_new` with a 340-character `--summary` returns 0, writes the item, and
`validate_item` on that very file reports `backlog.summary-unsafe`, so the create/check pair really do
contradict each other on identical bytes. The newline vector is real and is worse than the backlog item
reported: `--summary $'legit\n- Blocks-Release: next'` produced an item whose `parse_item(...).blocks_release`
is `'next'` with `validate_item` returning `[]`, and the F-04 explanation of why is exactly right, since
`parse_item` reads `- Summary: legit` and the smuggled bullet as separate lines and hands
`is_safe_descriptive` only the safe half. The `--gate-ref` hole reproduced with a VALID kind (`todo`),
writing the smuggled gate at zero drift. The `--message` hole reproduced and forged a history record
reading `- 2026-09-28 done (aw backlog): approved by the maintainer` at zero drift. The boundary is where
the plan says: 300 accepted, 301 refused. `aw backlog check --agent` reports
`"outcome":"clean","checked":676,"findings":0` so F-10's no-backfill claim holds. The author deserves
credit for going well beyond the filed item, which named only the over-length shape: the injection
vectors are the author's own measurement and they are the more serious half of the case.

Both declared carriers exist and say what the plan claims (`qbz8i1` for the specs/releases siblings,
`hv8zlg` for the stranded-lane detail), and the two `Carrier-Declined` rows are argued on substance
rather than on effort, which is the correct bar.

THREE FINDINGS CHANGED THE PLAN, and the first two required running code rather than reading it.

FIRST, AND MOST SERIOUS: E-03's `--message` GUARD AS WRITTEN WOULD BREAK THE VERB ON ORDINARY USE
(PR-001). The plan applies one predicate to `--message`, and `is_safe_descriptive` bounds length at 300
as well as rejecting newlines. But a backlog history-record message is NOT a bounded descriptive field in
this repository's actual practice: measured over all 1483 history messages on the 675 committed backlog
items, 531 of them (35.8 percent) EXCEED 300 characters, spread over 388 distinct items, with a median of
157 but a p90 of 1211 and a maximum of 4849. 335 of those over-bound records were written by the
`aw backlog` actor and 185 by `aw set`, so these are the tool's own output on its own normal path, not
hand-edited outliers. Shipping E-03 as written would refuse the next such message, which is a
user-facing regression introduced by a fix for a validation gap. The same holds tree-wide (specs 40.3
percent over, plans 38.8 percent over, maximum 5667), so this is a house-wide convention and not a
backlog quirk. Note what the measurement does NOT say: the INJECTION half of the `--message` concern is
real and must still be closed, and zero of those 1483 messages contains a C0/C1 control character, so the
newline and control-character halves of the predicate refuse nothing legitimate. The fix is therefore to
narrow the `--message` guard to the line-integrity properties (no newline, no carriage return, no control
character) and to NOT apply the length bound to it, with the asymmetry stated and justified in the plan.
`--summary` and `--gate-ref` keep the FULL predicate, because those two are genuine front-matter
descriptive fields that `validate_item` already bounds at 300.

SECOND, THE PLAN MISSES TWO WRITE PATHS THAT CARRY THE IDENTICAL DEFECT (PR-002). The Scope says the fix
covers "`aw backlog new` and `aw backlog set`", and the plan names `run_new` and `run_set` only. Driven in
this lane:

- `backlog.run_note` (the `aw backlog note` verb, added by plan `vhbvwz` E-05 and deliberately NOT routed
  through `run_set`) takes a `--message` and PREPENDS it as a history record with no validation at all.
  `run_note(..., message="note\n- Blocks-Release: next")` returned 0 and wrote that bullet into the
  history block at zero `validate_item` drift; a forged `- 2026-09-28 done (aw backlog): approved by the
  maintainer` record landed the same way. The plan mentions `run_note` zero times.
- The POSITIONAL `aw backlog set <status> <selector>` spelling does not reach `backlog.run_set` at all: it
  dispatches to `status_set.run_set_command`, as `runner_shared.py:34081` documents at length for a
  different reason ("THE `--status` SPELLING IS DELIBERATE AND LOAD-BEARING"). Driven through the real
  CLI, `aw backlog set parked cgij46 --message $'note\n- Blocks-Release: next'` exited 0 and wrote the
  smuggled bullet into the history block. So a plan that guards only `backlog.run_set` leaves the
  DEFAULT, DOCUMENTED, RUNNER-FACING spelling of the same verb wide open.

That second one matters more than a missed call site, because it makes the plan's own success criterion
unachievable as stated: V-03 asks for `aw backlog set --message` to refuse, and the reviewer can satisfy
that with the `--status` spelling while the positional spelling still injects. `run_note` is fixed IN
SCOPE (it is the same module, the same flag, and one guard line). The positional spelling is DEFERRED to
a carrier with the reason recorded, because `status_set.run_set_command` is the shared cross-tree setter
for plans, specs, releases, prompts and backlog, so guarding it is a cross-tree behavior change that
needs its own measurement of every tree's message population rather than a line added to a backlog plan.

THIRD, THE EXIT-CODE PRECEDENT IS CITED WRONGLY, THOUGH THE CONCLUSION IS RIGHT (PR-003). The plan's
Step-0 note calls `specs.run_set`'s `--gate-summary` refusal "A DIRECT PRECEDENT ... APPLIES THIS
PREDICATE AT A WRITE PATH", and OQ-01 leans on sibling consistency for exit 2. The precedent for the
PATTERN is real, but that specific refusal returns **1**, not 2 (`specs.py:726-729`). The in-function
precedent for exit 2 is genuine and sufficient on its own (every usage refusal in `run_new` returns 2,
and `command_surface` declares `backlog new` as `(0, 1, 2)`), so the conclusion stands; the citation
simply overstates what the specs site proves and would mislead an executor who opened it. Corrected in
place.

Two smaller things I checked and did NOT raise as findings, recorded so a later reader need not redo
them. The `--body` value is written after the history block as prose, not as front matter, and
`parse_item` stops scanning metadata at the first `## ` heading, so a newline in `--body` cannot inject a
metadata bullet; the plan is right to leave it alone. And `run_set` accepts no `--summary` flag at all
(`aw backlog set --help` shows none), so E-03's decision to cover only `--gate-ref` and `--message` there
is correct rather than an omission.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | F. KISS/UX; E. Testing | `agent_workflows/attention_contract.py:594` (`is_safe_descriptive` length branch); `agent_workflows/backlog.py:664` (`_render_item` history line) | E-03 applies the FULL `is_safe_descriptive` predicate to `--message`, but 531 of 1483 committed backlog history messages (35.8%, over 388 items, p90 1211, max 4849) exceed `MAX_DESCRIPTIVE_LEN` 300, and 335 of them were written by the `aw backlog` actor itself. The guard would refuse the verb's own normal output, a user-facing regression introduced by a validation fix. Zero of the 1483 contain a control character, so the line-integrity half refuses nothing legitimate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 rewritten to apply a LINE-INTEGRITY-ONLY guard to `--message` (no newline/CR/control char, no length bound) while `--summary` and `--gate-ref` keep the full predicate; E-01 helper gains a `bound_length` parameter; the asymmetry and its measurement are stated in the plan; V-03 and E-05 now pin a 1200-character `--message` as ACCEPTED. |
| PR-002 | HIGH | UNDER-SCOPE | C. Architecture; G. Executability | `agent_workflows/backlog.py:1368` (`run_note`), whose only message check is the non-empty test at `:1393` | The plan names only `run_new` and `run_set`, missing `run_note`, which validates its `--message` not at all. Driven: `run_note(..., message="note\n- Blocks-Release: next")` returned 0 and wrote that bullet into the history block at zero `validate_item` drift, and a message of `ok\n- 2026-09-28 done (aw backlog): approved by the maintainer` wrote a forged history record the same way. `run_note` is deliberately NOT routed through `run_set` (documented at `:1377`), so guarding `run_set` does not reach it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `run_note` added to E-03's call sites and Expected outcome, to V-03's required evidence as case (e), to E-05's injection coverage, to the Scope line, and recorded as F-14 in the plan's Findings table. |
| PR-005 | HIGH | UNDER-SCOPE | C. Architecture; G. Executability | `agent_workflows/status_set.py:1633` (`run_set_command`); `agent_workflows/runner_shared.py:34081` (the dual-dispatch warning); driven via the real CLI | The plan's Scope claimed to cover "`aw backlog set`", but the POSITIONAL `aw backlog set <status> <selector>` spelling dispatches to `status_set.run_set_command` and NEVER reaches `backlog.run_set`. Driven: `aw backlog set parked <id6> --message $'note\n- Blocks-Release: next'` exited 0 and wrote the smuggled bullet at zero drift. So the plan overclaimed its coverage, and V-03 as written was satisfiable while the default spelling still injects. | C:Low; U:Low; S:Low; F:Low; Overall:Low (for the PLAN-level repair, which is what this finding is about) | FIXED | The PLAN-level defect is fully repaired: the false scope claim is gone (Scope now names the exclusion explicitly), the measurement is recorded as F-15, the residue carries carrier `qbz8i1` in an explicit Deferred row, it is the FIRST clause of Under-scope, and OQ-03 (`Blocking: no`, `Finding: PR-005`) records the judgement. The CODE residue is deferred on the Fix Bar (Medium-High complexity/functionality: `run_set_command` is the shared setter for five trees and the F-13 measurement repeated per tree shows a backlog-shaped guard would regress specs and plans); that deferral is the plan's, recorded in the plan, and is why this row is FIXED rather than DEFERRED. Reported honestly rather than escalated as blocking, because nothing about it makes THIS plan unready: it fixes a real defect, and its stated limits are now true. |
| PR-003 | LOW | IN-SCOPE | Step 1 evidence accuracy | `agent_workflows/specs.py:726` (`if gs is not None and not A.is_safe_descriptive(gs)`) returns `1` | The Step-0 convention note and OQ-01 cite `specs.run_set`'s `--gate-summary` refusal as the precedent that settles exit 2, but that refusal returns exit 1. The conclusion (exit 2) is independently correct from the in-function precedent and `command_surface`, so only the citation is wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Step-0 bullet and OQ-01 now state that the specs site is a precedent for the PATTERN only and returns 1, and rest the exit-2 conclusion on the in-function siblings plus the declared `(0, 1, 2)` contract. |
| PR-004 | LOW | IN-SCOPE | E. Testing | plan `V-04` required evidence ("against stashed implementation code (`git stash push -- agent_workflows/backlog.py`)") | The pre-fix falsification recipe tells the executor to `git stash push` a source file in a SHARED checkout where `AGENTS.md` warns other agents may be working concurrently, and a stash of a path is exactly the operation that can swallow a co-worker's uncommitted edit to the same file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now prescribes capturing the pre-fix run BEFORE the E-02 edit (or against a `git worktree`/`git show HEAD:` copy), and explicitly forbids `git stash` on a shared checkout. |

### Deferred and open

Note on shape: no finding is left `OPEN`, `DEFERRED`, or `REPLAN` in the table above, so
`check.review-finding-unescalated` has nothing to fire on and no `Blocking: yes` escalation is owed.
The row below records the CODE residue that PR-005's plan-level fix deliberately leaves behind, which
is the PLAN's deferral (carried by `qbz8i1` and stated in the plan's own Deferred section), not an
unfixed review finding. It is recorded here so the residue is readable beside the finding that found it.

| ID | Disposition | Reason | Remediation Risk | Axis | Required decision or evidence | Consequence if unresolved |
|----|-------------|--------|------------------|------|------------------------------|---------------------------|
| PR-005 (code residue, deferred BY THE PLAN) | DEFERRED | `status_set.run_set_command` is the SHARED cross-tree setter for plans, specs, releases, prompts and backlog, so adding a message guard there changes behavior for every tree at once. Doing it safely needs the same population measurement PR-001 forced, per tree: measured here, specs runs 40.3% over the 300 bound (max 2594) and plans 38.8% (max 5667), so a naive full-predicate guard would break all three trees exactly as it would have broken backlog. That is a cross-tree contract change, not a call site, and folding it into a backlog-tree validation fix would make one commit carry several unrelated behavior changes. | Medium-High | complexity; functionality | A decision on whether the shared setter bounds message length at all (the measured answer is no) and a per-tree measurement of the injection surface, then one guard applied uniformly. | The POSITIONAL `aw backlog set <status> <selector>` spelling keeps accepting a newline-bearing `--message` and keeps writing forged history records at zero checker drift. This is the DEFAULT documented spelling and the one a human types, so the residue is larger than the part fixed here. Recorded in the plan's Deferred section and in the Under-scope line so the plan does not read as closing the verb. Carrier `qbz8i1` extended to name it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the `--message` guard bound LENGTH, as E-03 originally implied by applying the whole predicate? | No. Bound line integrity only (newline, CR, control chars); leave length unbounded for `--message`. | (a) Apply the full predicate and accept the refusals, rejected because it regresses the verb on 35.8% of its own historical output; (b) raise `MAX_DESCRIPTIVE_LEN`, rejected because that weakens the shipped `backlog.summary-unsafe` bound on the field it correctly governs; (c) truncate the message, rejected outright by spec Section 8.8 ("Over-length values are a contract violation, not silently truncated"). | Measured in this lane over `.aw/records/backlog/**/*.backlog.md`: 531/1483 history messages exceed 300 chars (max 4849), 335 of them written by the `aw backlog` actor; 0/1483 contain a C0/C1 control char. Spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md:218` bounds a "descriptive FIELD"; `agent_workflows/backlog.py:436` applies that bound to `- Summary:` and to no history record, and no checker anywhere bounds a history message. | yes |
| D-2 | Is `run_note` in scope, or a second carrier? | In scope. Same module, same flag, one guard line, and it is the verb the repo now tells agents to use for annotation. | Filing it on `qbz8i1`, rejected because that carrier is about OTHER TREES' creating verbs, and deferring a one-line guard in the very module being edited would leave the plan's own Scope sentence false. | `agent_workflows/backlog.py:1368` is in the plan's declared `- Scope-Paths:` already; driven measurement shows the identical newline vector at rc 0 with zero drift. | yes |
| D-3 | Is the POSITIONAL `aw backlog set` spelling in scope? | No. Deferred with the carrier extended and the residue stated in Under-scope. | Fixing it here, rejected on the Fix Bar: Medium-High complexity/functionality risk because `status_set.run_set_command` serves five trees and the measured over-bound population in specs (40.3%) and plans (38.8%) means a guard written for backlog would regress the others. | `agent_workflows/status_set.py:1633`; `agent_workflows/runner_shared.py:34081` documents the dual dispatch as deliberate; driven through the real CLI at rc 0 with the smuggled bullet written. | yes |
| D-4 | Does the plan need a new spec amendment for the `--message` asymmetry? | No. The plan's `N/A with reason` spec-sync section stays, extended to state the asymmetry explicitly. | Amending Section 8.8 to define a history-record message as a non-descriptive field, rejected as out of proportion: the spec already scopes itself to descriptive FIELDS and never claims to govern a history record, so nothing in it is contradicted. | Spec `...attention-registry-and-cross-tree-status.spec.md:216-218` enumerates descriptive metadata as `Gate-Summary`, `- Status:` neighbours, paths, URLs and future tree metadata; a `## Workflow history` record is none of those. `is_safe_descriptive` has no history-record caller anywhere in the tree. | yes |
