# Review findings: plan o7k6lt

- Subject-Id: o7k6lt
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `1d013100`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision. At `review-finalize` it now exits 1 on `IPD-Q501` (a blocking
question left open), which is the DESIGNED consequence of PR-001's escalation rather than a structural
defect: the workflow requires an unfixed finding at or above the gate threshold to become a
`- Blocking: yes` question precisely so the lint gate stops execution until a human answers. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy is
byte-identical to the tracked file.

FAVOURABLE CIRCUMSTANCE WORTH STATING FIRST: both declared dependencies (`je74a0`, `vv6y7e`) are
ALREADY `executed` at this HEAD, so the tree the plan's E-01 expects to measure on is the tree I could
measure on. That let me verify the plan's premises rather than reason about them, and I drove the real
`MigrationManager` end to end instead of probing the predicate alone.

**EVERY AUTHORED FINDING REPRODUCED, INCLUDING BOTH DATA-LOSS CLAIMS, END TO END.** F-1 (`return
"defer"` fall-through; the resolver already carries `je74a0`'s saved-answer read, satisfying the gate's
stop condition). F-2 (`defer` keeps the leftover, `remove` deletes it). F-6 (the spec's two sentences
are verbatim as quoted). F-7 is now spent: the skills fixture migrates cleanly, as the plan predicted.
The two that matter I drove through a REAL `execute_migration`, not the predicate:

```text
STAGED-NEVER-COMMITTED: file survives? False; any history? False
   >>> CONTENT EXISTS NOWHERE (unrecoverable loss)
COMMITTED-THEN-EDITED:  file survives? False; any history? True
   >>> HEAD has: 'original\n'          <- the local edit is gone
```

So the plan's central argument is correct and load-bearing: the maintainer's ruling rests on
"recoverable from history", and that premise is FALSE today. E-02 is the right fix in the right place,
and I verified its EXACT proposed command pair on five cases plus two the plan never named:

```text
clean tracked            cat-file=0   diff=0    -> removable
worktree-modified        cat-file=0   diff=1    -> preserved
staged-modified          cat-file=0   diff=1    -> preserved
staged-never-committed   cat-file=128 diff=1    -> preserved
no-HEAD repo             cat-file=128 diff=128  -> preserved
mode-change-only         cat-file=0   diff=1    -> preserved
clean symlink            cat-file=0   diff=0    -> removable
```

I also checked the failure mode a reviewer should worry about most with a diff-against-HEAD predicate:
that the migration's OWN staged renames dirty the leftover's diff and quietly turn the tightening into
a no-op that preserves everything. Instrumented at the moment `_handle_leftovers` calls the predicate
during a live migration, the clean leftover still measured `cat-file=0 diff=0`, so the flip remains
observable. That is now V-02's required evidence.

**THE PLAN EXTENDS THE MAINTAINER'S RULING BEYOND WHAT IT SAYS, AND DECIDES THAT ON ITS OWN
AUTHORITY.** This is the finding that moves the verdict. The ruling quoted verbatim on backlog `6kczjg`
is scoped to an UNATTENDED run; the plan's own title and `- Concern:` say "unattended"; but
`_install_leftover_disposition` is read by all three install call sites, two of which are INTERACTIVE
(confirm-to-migrate after `_ask_policy` returns True on a TTY, and split-brain migrate-now behind
`_prompt_yes_no`). Flipping the built-in default therefore makes an ATTENDED install destructive by
default too. OQ-02 resolved this "YES" with `Owner: this plan's author`. The engineering reasoning (one
resolver by design, install has no leftover prompt) is sound, but the scope of a destructive default is
a risk-appetite call AGENTS.md reserves for the human, and the same maintainer's earlier ruling on this
very item said a policy question like this "should ASK, with the prompt DEFAULTING TO THE ENCOURAGED
ACTION". I reopened OQ-02 as `Blocking: yes`, `Owner: maintainer`, with three concrete options and the
consequence of each, and gated E-04 onward behind it.

**THE DELETION IS COMPLETELY SILENT, WHICH IS WHAT MAKES A RECOVERABLE LOSS UNRECOVERABLE IN
PRACTICE.** The plan's whole safety case is "only files git can restore are deleted". A user can act on
that only if told a deletion happened. Measured on a full `aw install <repo> --to-aw --yes` that did
delete a tracked file:

```text
leftover deleted? True
'leftover': NOT MENTIONED
'remove':   NOT MENTIONED
'delete':   NOT MENTIONED
```

Hundreds of `[added ]` lines, and not one word about the file it destroyed. `execute_migration` itself
printed the empty string. The remedy is cheap because the data already exists: `_handle_leftovers`
returns the classified lists and `execute_migration` persists them, so reading the transaction back
gave me `"removed": [".agents/README.md"]` with no new bookkeeping. Added as E-08/E-09 with V-08/V-09.

**THE PLANNED TEST FIXTURE WOULD HAVE MADE THE REMOVAL CASES PASS VACUOUSLY.** E-03/E-05 build on
`InstallLeftoverDispositionThreadingTests._legacy_repo`, which uses `tests/support.py:init_repo`, which
runs `git init` plus three `git config` calls and NEVER commits. Under E-02 a HEAD-less repo removes
nothing, so "a clean tracked leftover IS removed" would pass because there is no HEAD, not because the
code is right, and a regression that deleted everything would still pass it. Both predicates agree on
such a repo for the WRONG reason (measured). E-03 now requires the fixture to commit for every removal
case, cites the `tests/test_layout_inventory.py::_make_git_repo` precedent, and V-03 requires pasting a
real `HEAD` sha to prove non-vacuity. I also added safety case (b2) for a STAGED edit, since the plan
pinned only the worktree half of a claim whose index half is exactly what `git rm -f` discards.

**TWO SMALLER ACCURACY PROBLEMS.** E-05 enumerated the old-default assertions to repair and MISSED one:
`test_leftover_flag_parsing_and_resolver` ends with a "Clear restores built-in default" case
(`unset_config_value` then expect `defer`) that must become `remove`, and an executor following the
list literally would leave a failing test. And E-07 justified running `tests/test_doctor.py` because
`_is_removable_leftover` "backs the doctor residue view's expectations", which is false:
`_is_removable_leftover` has one caller in the package, `doctor.py` never imports `layout_migration`,
and `test_doctor.py` contains no `removable` reference. The genuinely coupled files are
`tests/test_layout_inventory.py` (five real `leftover_disposition="remove"` calls) and
`tests/test_layout_migration.py`, both now named.

**WHAT I CONFIRMED RATHER THAN CHANGED.** OQ-03 (`defer` for an unrecognized value) is correct and its
precedent holds. The plan's claim that the split-brain `MagicMock` test still passes unedited is right,
and I verified the mechanism (`getattr(MagicMock(), "leftovers")` is a MagicMock, not in the enum, so
the resolver returns `defer`). The `_legacy_repo` fixture already carries `.agents/skills`, so E-03's
"extended with" is unnecessary (corrected to say so). `aw migrate-layout` genuinely resolves separately
and its interactive step does show "[3] remove: Permanently delete leftover legacy files after move",
so OQ-02's migrate-layout half is settled and its `--yes` help stays accurate. `aw specs note` works on
an `implemented` spec (tested on a COPY; the tracked spec was not touched) and that spec already carries
a prior amendment note, so E-06(c)'s refusal contingency is unnecessary but harmless. The spec amendment
is correctly declared in `- Scope-Paths:`. Right-sizing: now 9 E-items across two modules and one
defect class, under the 18-leaf threshold, and the natural split point (safety versus flip) is already
expressed as a dependency plus a stop condition rather than needing two plans.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | F. principles / B. security-adjacent (a destructive default widened past its authorization) | the ruling quoted verbatim on `.aw/records/backlog/graduated/20260923-6kczjg-01-6kczjg-decide-default-leftovers-disposition.backlog.md` ("with nothing saved, an unattended aw install --to-aw migration defaults --leftovers to REMOVE"); `cli._install_leftover_disposition` read by all three call sites, two of them interactive (`_handle_legacy_migration` after `_ask_policy` on a TTY, `_split_brain_guard` behind `_prompt_yes_no`); the same item's earlier ruling "a policy question like this should ASK, with the prompt DEFAULTING TO THE ENCOURAGED ACTION" | **THE PLAN MAKES AN ATTENDED, INTERACTIVE INSTALL DESTRUCTIVE BY DEFAULT, WHICH THE MAINTAINER'S RULING DOES NOT AUTHORIZE, AND RESOLVES THAT ITSELF.** The ruling, the plan's title and its `- Concern:` all say UNATTENDED; the resolver being flipped is shared by the interactive paths, so the blast radius is wider than the authorization. OQ-02 decided "YES, apply to interactive too" with `Owner: this plan's author`. Sound engineering, but scope of a destructive default is a human's risk call. | C:Low; U:Medium; S:Medium; F:Medium; Overall:Medium-High (the fix is a MAINTAINER DECISION, not an edit: guessing it either over-reaches the ruling or silently narrows a change the maintainer may have wanted whole) | OPEN | OQ-02 REOPENED as `Blocking: yes`, `Owner: maintainer`, carrying `- Finding: PR-001`, with three options spelled out (accept the widening; restrict to unattended via the attended signal `_ask_policy` already computes; or add the leftover prompt, near backlog `kapm7y`). E-04 and everything downstream is gated behind it by a new numbered GENUINE STOP CONDITION; E-01..E-03 are explicitly cleared to proceed because they only make an existing destructive option safer. The approval paragraph now presents the decision to the human as its own section. `IPD-Q501` fires at every lint checkpoint, so execution fails closed. |
| PR-002 | HIGH | UNDER-SCOPE | E. testing (a control that passes for the wrong reason) | `tests/support.py:init_repo` runs `git init` + three `git config` and never commits; on a `_legacy_repo`-shaped repo `git rev-parse HEAD` -> `fatal: ambiguous argument 'HEAD'`; on that repo both the current and the E-02 predicate return removable=False (`cat-file`=128, `diff`=128) | **THE PLANNED FIXTURE HAS NO `HEAD`, SO E-03(c) AND E-05(f) WOULD PASS VACUOUSLY UNDER E-02.** A HEAD-less repo removes nothing, so a control asserting a clean tracked leftover IS removed would pass because there is no HEAD, not because the code is correct, and a regression deleting everything would still pass it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires `git add -A` + `git commit` of the base state for every case that asserts a REMOVAL, cites the `tests/test_layout_inventory.py::_make_git_repo` precedent, and explains that case (a) deliberately does the opposite so it distinguishes "not in HEAD" from "no HEAD at all". V-03 requires a real `HEAD` sha pasted from the (c) fixture. E-05(f) carries the same rule. Added F-8. |
| PR-003 | HIGH | UNDER-SCOPE | F. UX / prevent silent failure (a destructive default with no user-visible trace) | full `aw install <repo> --to-aw --yes` that deleted `.agents/README.md`: "leftover", "remove", "delete" all `NOT MENTIONED` in captured stdout+stderr; `execute_migration` printed `''`; the transaction records `{"removed": [".agents/README.md"], "preserved": [...]}` | **THE DELETION IS ENTIRELY SILENT, WHICH DEFEATS THE PLAN'S OWN SAFETY ARGUMENT.** The approval case is "only git-recoverable files are deleted", but a user can only recover a file they are told about. Flipping a default to destructive while keeping the operation silent turns a recoverable loss into an unrecoverable one in practice. | C:Low; U:Low; S:Low; F:Low; Overall:Low (the classified lists are already computed and already persisted, so this is a report, not new bookkeeping) | FIXED | Added E-08 (one `term.status("info", ...)` line in the three success branches when the disposition was `remove` and the recorded `removed` list is non-empty, naming the count, the recovery command, and the two opt-outs; read from the manager's own transaction, never re-derived; no unbounded file list) and E-09 (three tests asserting USER-VISIBLE output, including the negative cases). V-08 requires the before/after output contrast. `- Scope:` item (g), the scope fence and the approval paragraph updated. Added F-9, F-10. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. testing (an incomplete repair list leaves a failing test) | `test_leftover_flag_parsing_and_resolver`'s closing case: `CFG.unset_config_value("defaults.leftovers")` then `assertEqual(..., "defer")` | **E-05's ENUMERATION OF OLD-DEFAULT ASSERTIONS MISSES THE "Clear restores built-in default" CASE.** It names the two resolver assertions and the `(None, "defer")` rows but not this third one, so an executor following the list literally leaves a failing test and may then "fix" it by weakening something. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now names it explicitly, and V-05 requires the diff to include it. E-05 also now records that the test's own docstring ("safe fallback to defer") and the two `--yes` help strings were checked: install's needs no change, and migrate-layout's "leftovers defaults to defer" stays correct under OQ-02. |
| PR-005 | MEDIUM | UNDER-SCOPE | D. anti-regression (half a claim pinned) | measured: `git diff --quiet HEAD -- <rel>` returns 1 for a STAGED-modified path as well as a worktree-modified one; `_handle_leftovers` removes via `git rm -f`, which discards a staged edit | **NO CASE PINS THE INDEX HALF OF E-02's CLAIM.** E-02 promises "unmodified against HEAD in index AND worktree" and the safety cases cover only a worktree edit, yet the index half is exactly what `git rm -f` silently discards. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added safety case (b2) (a committed leftover whose edit is STAGED also survives) to E-03, with V-03 requiring it to fail before E-02. V-02 additionally requires the staged-modified probe. |
| PR-006 | LOW | IN-SCOPE | A. correctness of a stated rationale (a coupling that does not exist) | `grep -rn "_is_removable_leftover" agent_workflows/` -> 4 hits, all in `layout_migration.py`; `grep -rn "MigrationManager\|layout_migration" agent_workflows/doctor.py` -> no output; `grep -rn "removable" tests/test_doctor.py` -> no output; `tests/test_layout_inventory.py` calls `execute_migration(..., leftover_disposition="remove")` five times | **E-07 JUSTIFIES ITS TEST SELECTION WITH A FALSE CLAIM.** It says `_is_removable_leftover` "backs the doctor residue view's expectations"; the doctor never reaches that code. The genuinely coupled files (`test_layout_inventory.py`, `test_layout_migration.py`) were not named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07's file list corrected to `test_installer.py test_layout_inventory.py test_layout_migration.py`, with the false coupling called out so it is not propagated; running `test_doctor.py` is noted as harmless but not cited as coupled. V-07 updated. Added F-11. |
| PR-007 | LOW | IN-SCOPE | G. plan executability (stale watermark, counts, and an unjustified probe that would mutate a tracked spec) | `- Highest E allocated: 07` against 9 E-items after revision; E-06(c)'s "if that verb refuses ... paste the refusal"; `- Scope:` and the approval paragraph described two changes | **THE WATERMARK AND SUMMARY NO LONGER DESCRIBE THE PLAN, AND E-06(c)'s REFUSAL PROBE INVITES MUTATING A TRACKED `implemented` SPEC TO FIND OUT.** | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Watermark 07 -> 09; `- Scope:` gained item (g); `## Proposed changes` renumbered with the OQ-02 gate and the independence of steps 1 to 3 stated; the approval paragraph rewritten into three changes plus the decision; a gate paragraph forbids probing on the tracked spec and points at the scratch-copy method review used. Added F-13 recording that the verb does NOT refuse, so the contingency is unnecessary. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02 resolves "apply the new default to the interactive install paths too" on the author's own authority. Accept it, or reopen it for the maintainer? | REOPEN as `Blocking: yes`, `Owner: maintainer`, with three options, and gate E-04 onward behind it. | (a) Accept the author's resolution: rejected, the ruling says UNATTENDED and the plan silently widens a DESTRUCTIVE default to attended runs; that is a risk-appetite call AGENTS.md reserves for the human, and the same maintainer had already said this class of question should ASK. (b) Narrow it myself to unattended-only (make the resolver read the attended signal): rejected, it invents a maintainer decision in the opposite direction and would quietly withhold a change they may have wanted whole. (c) Reject the plan outright (REPLAN): rejected and would be wrong, since the plan is well built and only its scope needs a human word; its safety half (E-01..E-03) is valuable regardless. | The ruling quoted verbatim on `6kczjg`; the three call sites reading one resolver; the earlier ASK ruling on the same item; AGENTS.md ("asking the human ONLY when ... the decision is theirs (scope, priority, risk appetite)"). The plan is not yet executed, so answering the question resolves it either way. | yes |
| D-2 | The deletion is silent. Fix it here, or file it separately? | FIX IT HERE (E-08/E-09). | (a) File a follow-up: rejected, this plan is the one that makes the silence dangerous by flipping the default to destructive, so shipping the flip without the report knowingly creates the harm and defers the mitigation. (b) Print the full removed-file list: rejected, unbounded output on a large legacy tree; the report names a count, a few paths, and the recovery command. (c) Ask the maintainer whether they want a report: rejected as a question not worth their time; "tell the user what you deleted" needs no ruling. | Measured silence (three keywords absent from a real run); the transaction already carrying `removed`/`preserved`, so cost is near zero. | yes |
| D-3 | `_legacy_repo` has no HEAD, so E-02 makes the removal controls vacuous. Change the fixture, or drop the removal controls? | CHANGE THE FIXTURE (commit the base state for every removal case). | (a) Drop the removal controls: rejected, (c) and (f) are the cases proving the flip actually does something; without them the plan could pass review having changed nothing observable. (b) Leave the fixture and accept the passes: rejected outright, a vacuous green test is worse than no test because it is read as cover. (c) Add a commit inside `init_repo` itself: rejected, it is shared by many test classes and changing it is an out-of-scope blast radius. | `init_repo` read in full (no commit); `git rev-parse HEAD` failing on the fixture shape; both predicates returning False on a HEAD-less repo; `_make_git_repo` in `tests/test_layout_inventory.py` as the in-repo precedent that commits. | yes |
| D-4 | E-02's predicate diffs against HEAD. Could the migration's own staged renames dirty the leftover's diff and make the tightening a silent no-op? | NO, verified by instrumenting the predicate DURING a live migration; require that evidence in V-02 rather than trusting the reasoning. | (a) Reason it through and move on: rejected, this is the one failure mode that would make E-02 look correct in isolation and preserve everything in production, and it is cheap to measure. (b) Require only the isolated five-case probe (what the plan asked for): rejected as insufficient for the same reason. | In-migration instrumentation at the call site: the clean leftover measured `cat-file=0 diff=0` while the migration's other renames were staged. | yes |

### Deferred and open

- `PR-001` - `OPEN`:
  - Reason: the fix is a MAINTAINER DECISION about how far a destructive default may reach, not an edit
    a reviewer may make. Both directions (accept the widening, or narrow it to unattended) would be me
    inventing a human's risk judgement, which is the one thing this workflow forbids.
  - Remediation Risk: Medium-High
  - Axis: security-adjacent (blast radius of a destructive default) and functionality (narrowing may
    withhold a change the maintainer wanted whole)
  - Required decision or evidence: the maintainer picks one of OQ-02's three options: (i) accept that
    any install-driven migration with nothing saved removes recoverable leftovers, interactive or not;
    (ii) restrict the new default to unattended runs, which means the resolver learns the attended
    signal `_ask_policy` already computes; or (iii) add the interactive leftover prompt install lacks,
    which is closest to their earlier ASK ruling and would likely re-scope or supersede this plan.
  - Consequence if unresolved: E-04 onward must not execute. `IPD-Q501` already fails every lint
    checkpoint, so this fails closed rather than relying on anyone reading this row. E-01 through E-03
    remain executable and are worth executing: they make an ALREADY-AVAILABLE `--leftovers remove`
    (and `aw migrate-layout --leftovers remove`) stop destroying never-committed files and uncommitted
    edits, which is a live defect today independent of any default.

All six other findings were FIXED in place.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS and E-02's
proposed predicate; I did NOT implement any of it, so that the tightening composes correctly with the
existing guards in their current order, and that E-08's report lands in all three branches, remain
E-02/E-08's work and V-02/V-08's evidence. I did not run the bare suite against a patched tree, so E-07
is a real obligation. My "silent deletion" measurement is of the `--to-aw --yes` path specifically; I
did not separately capture the interactive confirm path's output, though it shares the same success
branch shape and the same absence of any leftover reporting. I measured `remove` on small scratch
fixtures only, so I have not characterized behavior on a large real legacy tree (which is part of why
E-08 is told not to print an unbounded list). Finally, F-8's vacuity claim is about the fixture the plan
NAMED; if the executor builds a different fixture that commits, the finding is already satisfied rather
than wrong.
