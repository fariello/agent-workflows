# Review findings: plan eikajx

- Subject-Id: eikajx
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `869581a5` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision. No pre-review snapshot was owed: the plan was committed and unmodified,
byte-identical to its `.aw/state/lane-inputs/rev-11/` copy. NO PRODUCTION FILE WAS MODIFIED BY THIS
REVIEW: every probe ran against scratch `git init` repositories under `/tmp`, and the only tracked
files this review writes are the plan, this record, and one backlog item PR-901 required.

**THE PLAN'S CENTRAL DEFECT IS REAL, SEVERE, AND REPRODUCED EXACTLY.** F-02 is the finding that
justifies the plan and it is correct in every particular. Driving `set_records.close_on_answer` on a
scratch `blocked` item carrying three real records (`2026-09-20 note`, `2026-09-10 set`, `2026-09-01
created`) produced TWO records: `- 2026-09-28 created (aw backlog): a summary` and `- 2026-09-28 done
(aw set): question answered; close-on-answer`. So the function destroys three committed records AND
manufactures a false `created` line re-dated to today, which is worse than losing provenance because
it asserts a provenance that never existed. F-03 is equally exact: `_inject_history_line` inserts
AFTER the first bullet, so even on a single-record item the newest record lands second, contradicting
every other writer and `attention_contract.newest_history_record`. F-01 reproduced (`_reattach_history`
takes 3 records in and returns 4, originals byte-identical; `specs._append_history` prepends
newest-first). F-05 reproduced (`close_on_answer` has no caller outside its own module docstring, so
the defect is latent, which the plan states plainly rather than hiding). F-06 reproduced
(`migrate_inline_history`/`_slim_inline_history` have no caller, no CLI, no test; `8pcdoa`'s
recommendation is quoted accurately; `7jqev2` fixed WHICH record survives, not THAT it slims to one).
F-09 reproduced on all four spec passages, including OQ-2's own "Section 3, R1, R3 and AC2 are
untouched" parenthetical. F-10 reproduced (all three test files absent; `19313eed --stat` lists them
at 436, 154 and 85 deletions; AC1 cites two functions that no longer exist). F-11 reproduced. The
plan's honesty is also above average: it FALSIFIES its own backlog item's headline, states that
nothing is losing data today, and explains why it declines the item's recommended option (1).

Seven findings. One is a BLOCKER that would have failed the plan's own validation, and two are
misdiagnoses that would have had an executor change correct code.

**PR-901 (BLOCKER): E-01's PRESCRIBED CALL CANNOT PRODUCE THE RECORD E-01's OWN EXPECTED OUTCOME AND
V-01 DEMAND.** E-01 says to call `_backlog._reattach_history(text, rendered, "done", "question
answered; close-on-answer")` and its Expected outcome plus V-01 require the resulting record to read
`- <today> done (aw set): ...`. `_reattach_history` HARDCODES `new_record = f"- {today} set (aw
backlog): {msg}"` and uses `new_status` only as a message fallback, so review ran the exact call and
got `- 2026-09-28 set (aw backlog): question answered; close-on-answer`. The preservation half is
perfect, so the fix is right and only its stated outcome is wrong. Severity is BLOCKER because an
executor following E-01 literally satisfies the fix and then FAILS V-01, and both plausible
improvisations are harmful: widening the shared `_reattach_history` (which this plan's own gate and
Deferred section forbid, and which every `aw backlog set --status` call depends on) or hand-patching
the label after the call (re-introducing the bespoke writer E-01 exists to delete). Review resolved it
by accepting the emitted label, having measured that no machine consumer reads it on a backlog item
and that 318 records in this repository's own corpus already carry it.

**PR-902 (HIGH): F-04 IS A MISDIAGNOSIS AND E-02 WOULD HAVE CHANGED CORRECT CODE.** F-04 claims
`_extract_body` "DESTROYS THE PRE-HISTORY PROSE REGION" and that `close_on_answer` is "saved from the
loss by accident, not by design". Three measurements refute it. The function's documented contract is
"the prose body after the `## Workflow history` block" and it returns exactly that. It is
BYTE-IDENTICAL to `backlog._strip_metadata_and_history`, the sibling the entire `aw backlog set`
pipeline already relies on, across five probed inputs. And `_render_item`'s `source_text` branch
preserves the header region deliberately, computing `header_prose` and re-emitting it under a comment
reading "preserve header prose written between the leading bullets and ## Workflow history". Worse,
E-02's prescribed fix (bound the block as `_prior_history_records` does) is a measured REGRESSION on a
two-heading file, where it returns the second heading and its records as BODY while the current walk
correctly returns only the body. So the item would have changed working code to something slightly
worse, on a false premise, in a function E-01 is simultaneously editing.

**PR-903 (HIGH): E-03's PRE-CHANGE FAIL/PASS SPLIT IS WRONG FOR TWO OF ITS THREE FAILURE CASES, AND
THE INSTRUCTION AS WRITTEN PUSHES TOWARD FAKING A RED RUN.** E-03 requires (a), (b) and (c) to FAIL at
base. Review ran all three. (a) fails, hard and exactly as F-02 describes. (b) PASSES, for PR-902's
reason. (c) PASSES: driving `close_on_answer` on an item whose body carries an indented `  -
2020-01-01 fake (aw fake): ...` line does not promote it, because `_prior_history_records` bounds the
block at the first non-bullet line and requires column zero, which is the `tk1gqo` fix already in
place. The plan's own instruction "do not claim a test fails first when it does not" is exactly right,
and its own split violates it, which is the sharpest form of this finding: an executor obeying both
sentences at once cannot, and the tempting resolution is to weaken a correct test until it goes red.

**PR-904 (MEDIUM): E-03(f)'s FAILURE INJECTION IS ENVIRONMENT-DEPENDENT WHERE THE DELETED TEST'S WAS
DETERMINISTIC.** E-03(f) proposes making `.aw/records/` unwritable. The deleted
`SidecarFailureIsReportedTests` rebound `record_history.append` to raise `OSError(28, "No space left
on device")`. Prefer the original: a `chmod` does nothing when the suite runs as root, so the test
would silently stop testing rather than fail, and it is a filesystem side effect in a shared checkout.
Rebinding a module attribute is not a source-text assertion and does not offend P16, because it
injects a failure and asserts the observable outcome.

**PR-905 (MEDIUM): E-08's GATE BAR IS UNSATISFIABLE, AND HOLDING IT INVITES TOUCHING A CO-WORKER'S
WORK.** Its expected outcome requires "every gate command exiting 0". Measured before any change:
`aw backlog check` 0, `aw specs check` 0, `aw sanitize --agent` clean, but `aw check` EXIT 1 on four
pre-existing errors (a missing `.aw/system/layout.json`, plan-conformance on `y43g6q` and `dv7c49`, a
nonconformant slug on backlog `9uowl6`) and `aw attention --check` EXIT 1 on two pre-existing lane
findings (`lane-superseded` on `3brgb6`, `lane-stranded` on `om3rzi`). An executor holding the
authored bar must either report failure on a correct execution or "fix" another plan's error or
recover another lane, which the shared-checkout rule forbids outright.

**PR-906 (LOW): ONE F-07 SUB-CLAIM HAD ALREADY DECAYED.** F-07 asserts "this lane's checkout has NO
sidecar file at all (`.aw/records/history.jsonl` does not exist)". It exists (452 bytes, two records),
created by ordinary `aw backlog new` calls during this review sweep. The finding does not depend on it
(the help text is false because the sidecar is gitignored and partially written), but a claim that
transient should not sit in a findings table as evidence.

**PR-907 (LOW): F-12's HEADLINE CONTENTION CLAIM IS FALSE, THOUGH ITS CONCLUSION SURVIVES.** F-12
says "No pending plan declares any path in this plan's `- Scope-Paths:`" over 22 plans. Re-measured
over 26: EIGHT do. `agent_workflows/cli.py` is declared by `0ykozn`, `ao0v8x`, `t38a4o`, `rs03r2` and
`ghna7l`; `tests/test_backlog.py` by `ghna7l`; `CHANGELOG.md` by `5j7jv1` and `g1w58u`. The conclusion
holds for the reason F-12's own second sentence gives (the runners isolate each item and merge through
a revalidation gate) rather than its first, and no declaring plan touches the same region. Review also
recorded the one relationship worth naming: `ghna7l` carries `- Carrier: hg2oop`, so this plan's
backlog item must outlive this plan, which is why E-08's `note`-only treatment of it is correct.

**WHAT REVIEW CHECKED AND FOUND SOUND.** The deletion of `_inject_history_line` rather than its repair
is the right call and well argued. E-05's survivor analysis is exactly right: `_inline_history_records`
and `_parse_record_line` are imported by `ipd_lifecycle` (and one test calls the latter directly), and
review independently confirmed that `_iter_record_files`, `_record_id6` and `read_all` have no caller
outside `record_history`, so the retirement's blast radius is understood. The refusal to re-track the
sidecar is correct and its reasoning is the strongest section of the plan. The spec amendment is
genuinely required rather than optional (the document contradicts itself at Section 3 versus OQ-2, and
R4 mandates a helper E-05 deletes), it is declared in `- Scope-Paths:` as `AGENTS.md` requires, and it
correctly leaves `- Status: implemented` alone. E-06's instruction to record the amendment through
`aw specs note` rather than by hand-editing the history block is right. Every `Carrier-Declined` row
is argued rather than formulaic, and the three `- Carrier:` rows resolve. Right-sizing at eight
E-items is appropriate for the work. The plan's Step-0 conventions are accurate, including the
`AW_NO_REEXEC=1` note, which review relied on.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a `- Blocking:
yes` question is owed and none was written. All three open questions survive review UPHELD, with
`Owner` corrected from `none` to `plan author`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | ran E-01's exact call and got `- 2026-09-28 set (aw backlog): question answered; close-on-answer`; `_reattach_history` reads `new_record = f"- {today} set (aw backlog): {msg}"` with `msg = message.strip() or f"status -> {new_status}"`; `attention_contract.HISTORY_RECORD_RE` is `^- (?P<date>\d{4}-\d{2}-\d{2}) .+$` (date only); `ipd_lifecycle._plan_status_events` gates labels on `_PLAN_STATUS_VOCAB` (plans, not backlog); 318 `set (aw backlog)` records measured in this repo's backlog corpus | E-01's PRESCRIBED CALL CANNOT PRODUCE THE LABEL ITS OWN EXPECTED OUTCOME AND V-01 DEMAND (`done (aw set)`). The fix works and its stated outcome is wrong, so an executor satisfies the fix and then fails validation, and both improvisations are harmful (widen a shared writer this plan forbids touching, or hand-patch the label and re-introduce the bespoke writer being deleted). | C:Low; U:Low; S:Low; F:Low; Overall:Low (accept the emitted label; review measured no consumer reads it) | FIXED | E-01 gained a paragraph with the measurement, the hardcoded source line, three reasons to accept `set (aw backlog)`, and an explicit prohibition on widening `_reattach_history`. Expected outcome and V-01 corrected to the real label; V-01 additionally requires an EMPTY `git diff -- agent_workflows/backlog.py`. Added F-13. The positional-versus-`--status` label asymmetry is recorded and filed rather than smuggled in. |
| PR-902 | HIGH | OVER-SCOPE | A. Correctness and data integrity | `_extract_body` vs `backlog._strip_metadata_and_history`: byte-identical on five inputs (pre-history prose, none, indented quoted record, no history section, non-record bullet in block); `_render_item`'s `header_prose`/`rendered_head` lines under the comment "preserve header prose written between the leading bullets and ## Workflow history"; end-to-end `close_on_answer` showing the paragraph EXACTLY ONCE; the prescribed `_prior_history_records` bounding returning a second `## Workflow history` heading as BODY where the current walk does not | F-04 IS A MISDIAGNOSIS AND E-02 WOULD HAVE CHANGED CORRECT CODE ON A FALSE PREMISE. The function already returns exactly what E-02 prescribes, the pre-history region is preserved by design rather than by accident, and the prescribed reuse is a measured regression on the one input where the two boundings differ. | C:Low; U:Low; S:Low; F:Low; Overall:Low (stop changing it; document it) | FIXED | E-02 rewritten to change NO behavior, carrying all three measurements and an instruction to report a counterexample rather than edit speculatively; it now adds only a docstring note naming `_render_item` as the owner of the header region. F-04 marked WITHDRAWN with its original claim preserved. Added F-14. Expected outcome, V-02, Proposed change 2 and `## Scope check` all reconciled. |
| PR-903 | HIGH | IN-SCOPE | E. Testing and verification | (a) at base: 3 records in, 2 out, survivor `- 2026-09-28 created` re-dated (FAILS, correctly); (b) at base: pre-history paragraph present exactly once (PASSES); (c) at base: indented `  - 2020-01-01 fake (aw fake): SHOULD-NOT-BE-PROMOTED` not promoted, `_prior_history_records` returning only the real record (PASSES); (d) at base: `aw backlog set done <id6> --no-commit` preserving all three priors newest-first (PASSES) | E-03's PRE-CHANGE FAIL/PASS SPLIT IS WRONG FOR (b) AND (c), AND THE ITEM ALSO SAYS "do not claim a test fails first when it does not". An executor cannot obey both, and the tempting resolution is to weaken a correct test until it goes red, which would destroy the regression pin. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 gained the corrected split with every measurement, stating that (a) is the ONLY deliberate-failure case and (b) through (g) pin already-correct behavior, plus an explicit instruction not to manufacture a failure for (b) or (c). Expected outcome and V-03 reconciled. Added F-15. |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing and verification | `chmod 0o500` on `.aw/records/` raises `PermissionError` as euid 1000 but is a no-op as root; the deleted `SidecarFailureIsReportedTests` rebinds `record_history.append` to raise `OSError(28, "No space left on device")` in `setUp` and restores it in `tearDown`, and asserts BOTH the warning and the inline record | E-03(f)'s FAILURE INJECTION IS ENVIRONMENT-DEPENDENT WHERE THE DELETED TEST'S WAS DETERMINISTIC. A `chmod`-based test silently stops testing under root rather than failing, and mutates filesystem permissions in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires the deleted test's own rebinding approach, names the recovery command, explains why it does not offend P16 (it injects a failure and asserts an outcome), and requires all four original cases including `test_the_advisory_helper_returns_false_rather_than_raising`. V-03 requires the executor to confirm the mechanism explicitly. |
| PR-905 | MEDIUM | IN-SCOPE | G. Plan executability (gates) | measured at HEAD `869581a5` before any change: `aw backlog check` exit 0, `aw specs check` exit 0, `aw sanitize --agent` clean, `aw check` EXIT 1 on four errors (missing `.aw/system/layout.json`; plan-conformance on `y43g6q` and `dv7c49`; slug on backlog `9uowl6`), `aw attention --check` EXIT 1 on two lane findings (`lane-superseded` `3brgb6`, `lane-stranded` `om3rzi`) | E-08's "every gate command exiting 0" IS UNSATISFIABLE, and holding it invites touching another party's work. Two of six gates fail on pre-existing conditions this plan neither causes nor may repair. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 gained a paragraph naming which three gates legitimately exit 0 and which two must be judged on an UNCHANGED named finding set, with an explicit prohibition on repairing another plan's error or recovering another lane to green a gate. Expected outcome and V-08 reconciled; V-08 also now re-derives the suite baseline rather than trusting a transcribed count. Added F-16. |
| PR-906 | LOW | IN-SCOPE | Step 1 evidence quality | `ls -la .aw/records/history.jsonl` shows 452 bytes with two records (`tzqvjn`, `4bicgv`), both written by `aw backlog new` during this review sweep; `git check-ignore -v` still resolves to `.aw/.gitignore:11` | ONE F-07 SUB-CLAIM HAD ALREADY DECAYED: the finding asserts the sidecar file does not exist in this checkout, and it does. The finding's substance is unaffected (gitignored, partially written), but a claim this transient should not sit in a findings table. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07's Evidence cell corrected: the decayed sub-claim is replaced with the re-verified `git check-ignore` result and the `status_set` zero-writes fact, and the decay is recorded with the observation that the review's own tooling created the file. |
| PR-907 | LOW | IN-SCOPE | C. Architecture and operability (cross-plan) | re-measured over 26 pending plans: `cli.py` declared by `0ykozn`, `ao0v8x`, `t38a4o`, `rs03r2`, `ghna7l`; `tests/test_backlog.py` by `ghna7l`; `CHANGELOG.md` by `5j7jv1`, `g1w58u`; `ghna7l` is `reviewed`/`go-pending-approval` and carries `- Carrier: hg2oop` | F-12's HEADLINE CLAIM IS FALSE (eight pending plans declare a shared path, not zero), so the plan asserted an isolation the tree does not have. The conclusion survives on the runner-isolation argument F-12 itself gives second. Also unrecorded: `ghna7l` declares `hg2oop` as its CARRIER, so the item must outlive this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 rewritten with the re-measured declarer list and the corrected basis for its conclusion. Added F-17 naming the `ghna7l` carrier relationship and what an executor must not do (close `hg2oop` or clear its gate). `## Scope check` records the contention. The scope fence forbids editing the item beyond a `note`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `_reattach_history` cannot emit the `done (aw set)` label E-01 demands. Widen the shared writer, patch the label after the call, or accept `set (aw backlog)`? | ACCEPT `set (aw backlog)` and correct the plan's expected outcome and V-01 to match. | (a) Add a label parameter to `_reattach_history` - rejected: this plan's own gate and Deferred section forbid modifying that function ("out of scope and already correct"), and it is the shared writer every `aw backlog set --status` call uses, so a signature change would put a blast-radius edit inside a latent-defect fix. (b) Hand-patch the label after the call - rejected: that re-creates the bespoke history writer E-01 exists to DELETE, which is the whole defect class. (c) File the label asymmetry as blocking - rejected: nothing reads the label on a backlog item, so it is cosmetic; it is filed as a normal item instead. | measured output of the exact prescribed call; `_reattach_history`'s hardcoded `new_record`; `HISTORY_RECORD_RE` requiring only a date; `ipd_lifecycle`'s label consumption being plan-scoped; 318 existing `set (aw backlog)` records in the corpus. | yes |
| D-2 | F-04 does not hold. Delete E-02, or repurpose it? | REPURPOSE it as a docstring note, keeping E-03(b) as the end-to-end pin. | (a) Delete E-02 outright - rejected: the misdiagnosis is attractive enough that review reached for it too, so leaving no note invites the next reader to "fix" the function again; a sentence naming `_render_item` as the owner of the header region is cheap and durable. (b) Keep the prescribed code change anyway - rejected on measurement: it is a no-op on every realistic input and a regression on the two-heading case. (c) Renumber to remove the item - rejected: renumbering breaks the E/V bijection and the plan's cross-references for no gain. | the five-input byte-identical comparison against `_strip_metadata_and_history`; `_render_item`'s `header_prose` handling and its comment; the two-heading divergence measurement. | yes |
| D-3 | Should review file the positional-versus-`--status` label asymmetry it discovered? | YES, file it as its own backlog item rather than widening this plan. | (a) Fix it inside this plan - rejected: it means editing `_reattach_history` or `status_set`, both fenced out, and it is a cosmetic inconsistency with no data at risk, so it does not belong in a release-gated provenance fix. (b) Note it only in prose - rejected: an unfiled observation in a plan body is tracked nowhere, which is the same defect PR-802 found in a sibling review this sweep. | measured side-by-side output of both spellings on identical fixtures (`done (aw set)` versus `set (aw backlog)`); the plan's Deferred rows fencing both writers. | yes |
| D-4 | Three HIGH-or-worse findings, one a BLOCKER. Does this plan go NO-GO? | NO. All seven were FIXED by in-place revision, so readiness is `go-pending-approval`. | (a) NO-GO on the BLOCKER - rejected: severity is for reporting and the Fix Bar alone decides fixing; every fix here is Low Remediation Risk on all four axes (correct a label expectation, stop changing a function, correct a fail/pass split, name an achievable gate bar) and none touches shipped behavior. (b) REPLAN - rejected: the plan's central diagnosis is correct and severe, its design is right, and the defects were in stated outcomes and two misdiagnoses, all repairable with bounded edits. (c) Escalate as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the threshold, and none is. | the `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` absent from `.aw/config/project.json`, so the default `HIGH` threshold applies and nothing sits unfixed at it. | yes |
| D-5 | E-08 requires six gates to exit 0 and two cannot. Should review relax the bar or narrow the gate list? | RELAX THE BAR to an unchanged finding SET for the two that cannot, keeping both commands in the list. | (a) Drop `aw check` and `aw attention --check` from E-08 - rejected: they are the two broadest whole-tree gates, and dropping them would stop the plan noticing drift it DID cause; the delta form keeps that signal. (b) Require the executor to clear the pre-existing findings first - rejected outright: they belong to another plan, another lane, and a missing layout file, and touching a co-worker's work to green a gate is precisely what `AGENTS.md` forbids. | measured exit codes and finding sets of all six gates before any change; `AGENTS.md`'s shared-checkout rule. | yes |
| D-6 | F-12's contention claim is false. Does that change the plan's conclusion? | NO, but re-state the conclusion on its correct basis and record the carrier relationship. | (a) Leave F-12 as written - rejected: it tells an executor no plan shares these files, which is false for eight of them, and a plan that asserts a false isolation invites an unchecked assumption. (b) Declare a cross-plan ordering dependency - rejected on measurement: no declaring plan touches the same region, and the runners isolate and revalidate, so no ordering is owed. | the re-measured declarer list over 26 pending plans; `AGENTS.md` on worktree isolation and the merge-and-revalidate gate; `ghna7l`'s `- Carrier: hg2oop` row. | yes |
