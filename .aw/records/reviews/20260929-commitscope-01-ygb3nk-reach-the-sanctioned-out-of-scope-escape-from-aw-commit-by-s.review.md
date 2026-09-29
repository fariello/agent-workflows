# Review findings: plan ygb3nk

- Subject-Id: ygb3nk
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `88d2aab9` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified (`git status --short` empty). No production code was modified by this
review; every post-change measurement was taken by rebinding `work_cmd._validate_plan_via_engine`
or mutating `check_engine.RULE_REGISTRY` IN MEMORY from scripts under the gitignored `.aw/state/`,
with fixture repos built in fresh temp dirs, exactly as the plan's own method rule mandates.

THE PLAN'S CENTRAL DIAGNOSIS AND ITS FIX ARE CORRECT, AND ITS MEASUREMENT DISCIPLINE IS UNUSUALLY
GOOD. The defect reproduced end-to-end: in a temp repo with a real lane and a real begin receipt,
a plan declaring two paths, having committed one undeclared path, is refused on a later
`aw commit <plan> -- <declared path>` with `refusing - 1 finding(s) ... check.scope-drift`, exit 1,
and the staged set literally `[]`. The prescribed fix works: with `check.scope-drift` rebound into
`advisory`, the same scenario prints the advisory and `committed 1 path(s)`, exit 0, with
`git show --name-only HEAD` listing only `agent_workflows/demo.py`. F-02 and F-03 reproduce (the two
refusals are distinct, and `_in_scope` returns `True`/`False`/`True` for the declared path, the
undeclared path, and the plan itself). F-05, F-06, F-07, F-12, F-13 and F-14 all reproduce as
written, including `_recover_commit_flags(['--scope-reason','a/b.py=why','--','x.py'])` parsing the
selector as `'a/b.py=why'`, and the absence of both test files the rule's docstrings cite.

WHAT REVIEW FOUND IS THAT THE PLAN'S OWN SAFETY GUARD WAS PARTLY VACUOUS, THAT ITS RESIDUAL-RISK
MEASUREMENT DOES NOT REPRODUCE AND UNDERSTATES A HOLE THIS CHANGE WIDENS, AND THAT A SECOND VERB
CHANGES BEHAVIOR WHILE THE PLAN DENIED IT. The code change itself needed nothing.

**E-05's BLAST-RADIUS ASSERTIONS COULD NOT DETECT THE MUTATION THEY EXISTED FOR (PR-601, HIGH).**
The plan's safety argument is that lowering `RULE_REGISTRY` to `warning` "silently retires three
gates including a CI step", and E-05(b)/(c) were drafted to turn red on it. Measured, three of the
four consumers are severity-blind between `error` and `warning`: `artifact_core.drift_exit_code`
exempts only `info` (`artifact_core.py:689`), so the REAL `cli.main(["check","plans","--agent"])`
in a lane with genuine drift exits `1` at registry `error` AND `1` at `warning` (`0` only at
`info`); `hooks/precommit_scope_gate.check` never reads severity at all (the substring is absent
from its body) and returns exit `1` at `error`, `warning` and `info` alike. So both drafted
assertions would have PASSED under the exact mutation V-05(c) demands they catch, shipping a false
proof of the plan's own safety claim. E-05 is rewritten to assert the registered severity alone,
with the honest blast radius required in its docstring, and V-05 now FAILS the item if either
vacuous assertion is re-added. The plan's DECISION not to edit the registry is untouched and still
correct.

**F-11's MEASUREMENT DOES NOT REPRODUCE, AND THE CORRECTED CONDITION IS ONE THIS PLAN MAKES
ROUTINELY REACHABLE (PR-602, HIGH).** F-11 states that a solo untrailered out-of-scope commit
yields `out_of_scope_paths: []` and finalize exit 0. Re-measured across three arrangements: with
that commit as the lane's ONLY commit, `attribution_source` is `none-fail-closed`,
`out_of_scope_paths` is `['agent_workflows/render.py']`, and `_reconcile_scope` DEMANDS a reason
(the `else True` "FAIL CLOSED WHEN COHESION KNOWS NOTHING" arm in `ipd_lifecycle.py` ~2917-2929).
The excuse appears only once an IN-SCOPE commit ALSO exists to anchor cohesion: then
`attribution_source` becomes `commit-cohesion`, `out_of_scope_paths` is `[]`,
`disregarded_unowned_paths` is `['agent_workflows/render.py']`, and no reason is demanded. That
anchoring in-scope commit is EXACTLY what this plan restores the ability to make, so the plan moves
the escape from narrow to routinely reachable on its own happy path, rather than leaving it
untouched as "pre-existing". Recorded in Findings, in Deferred, and in the approval paragraph so
the human accepts the real residue. Still correctly deferred to `s9z85a`: the alternative is the
unusable verb `ldy1al` reports, and with an `AW-Item` trailer the demand fires (measured).

**E-01 DENIED A SECOND BEHAVIOR CHANGE AND MISCITED THE ITEM THAT SUPPOSEDLY PINNED IT (PR-603,
MEDIUM).** E-01 claimed begin-time behavior "is unchanged in the case that exists, and E-04 pins
that". E-04 is entirely about `run_commit` and says nothing about `aw work begin`. And the case is
reachable: `_validate_plan_via_engine` is shared with `run_work_begin` (`work_cmd.py:321`), and
re-running `aw work begin` on a plan whose lane already holds an out-of-scope commit is refused
today (measured exit 1, `refusing to start - 1 finding(s) ... check.scope-drift`) and becomes an
advisory afterwards. The behavior is wanted, but it was unreviewed and uncovered. Added E-06/V-06
to pin it (advisory, exit 0, rule named, and the lease file asserted PRESENT), with V-06(d)
re-running the two existing `work begin` refusal tests so the item cannot be satisfied by making
that verb stop refusing everything.

**F-15's STATED REASON FOR NOT FIXING THE MISLEADING HEADING IS FALSE (PR-604, LOW).** F-15 claims
correcting the `(warning)` parenthetical "would break `test_commit_warning_drift_commits_with_advisory`,
which asserts `advisory` in the output". That test asserts the SUBSTRING `advisory`
(`tests/test_work_gate_severity.py:192`), which survives any edit to the parenthetical (verified by
substitution). The gap stays out of scope on honest grounds (the heading is shared with
`run_work_begin`; the gain is cosmetic), but since the justification did not survive it is now
CARRIED rather than declined: filed as backlog `7gr0vr`.

**THE "THREE OTHER CONSUMERS" COUNT IS FOUR (PR-605, LOW).** `aw doctor` also fans out through
`check_engine.check_type` (`doctor.py:510`) and exits via `core.drift_exit_code(report.all_drift)`
(`doctor.py:1676`). It is unaffected, and more strongly than the plan argues: `doctor` rebuilds each
finding as a 3-field `Drift` (`doctor.py:530`) whose `severity` is `''`, so it fails closed at every
registry value. F-09 corrected to name it.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Both authored open questions are `resolved` and both survive review: OQ-01's refusal of the
flag route is upheld on F-13/F-14, which reproduce exactly; OQ-02's choice to show rather than drop
the finding is upheld and is strengthened by PR-602, since an agent whose out-of-scope path will
later be silently excused needs the commit-time notice more, not less.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | high | IN-SCOPE | E. Testing and verification | `agent_workflows/artifact_core.py:689` (`drift_exit_code`); `agent_workflows/hooks/precommit_scope_gate.py:38` (`check`, no severity read) | E-05(b)/(c) asserted `drift_exit_code` nonzero and the pre-commit hook refusing as proof that lowering `RULE_REGISTRY` retires other gates. Both are severity-blind between `error` and `warning`, so both stay GREEN under the mutation V-05(c) demands they turn RED, making the plan's safety guard partly vacuous. Measured: real `aw check plans --agent` exits 1 at `error` AND at `warning`; hook exits 1 at `error`, `warning` and `info`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 rewritten to assert the registered severity alone and to require the honest blast radius in its docstring; V-05 rewritten to FAIL if either vacuous assertion is re-added. New F-16 records the measurement. |
| PR-602 | high | IN-SCOPE | D. Anti-regression and domain invariants | `agent_workflows/ipd_lifecycle.py` ~2917-2929 (the `else True` / "FAIL CLOSED WHEN COHESION KNOWS NOTHING" arm); review probe over three commit arrangements | F-11 does not reproduce: a solo untrailered out-of-scope commit is DEMANDED (`none-fail-closed`, `out_of_scope_paths: ['render.py']`), not excused. The excuse requires an IN-SCOPE commit to anchor cohesion (`commit-cohesion`, `out_of_scope_paths: []`, `disregarded_unowned_paths: ['render.py']`) - and that commit is exactly what this plan restores, so the plan WIDENS the hole it describes as untouched. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | fixed | New F-17 records the corrected measurement; Deferred entry and the approval paragraph rewritten so the human accepts the real, wider residue. Still deferred to carrier `s9z85a` (fixing it needs a maintainer ruling on fail-toward-demanding vs excusing). |
| PR-603 | medium | UNDER-SCOPE | G. Plan executability | `agent_workflows/work_cmd.py:321` (`run_work_begin` call site); review probe measuring exit 1 then advisory | E-01 asserted the `aw work begin` case "does not exist" and that E-04 pinned it. E-04 concerns only `run_commit`. The case is reachable and the routing changes that verb too (measured refused today, advisory after), so a second user-visible behavior change was denied by the plan and covered by no `V-*` item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01's cross-reference corrected to state the change honestly; E-06 and V-06 added to pin the `aw work begin` advisory path (including the lease file) with V-06(d) re-running the two existing refusal tests. `Highest E allocated` bumped to 06. New F-18 records it. |
| PR-604 | low | IN-SCOPE | F. KISS, principles, and UX | `tests/test_work_gate_severity.py:192` (`assertIn("advisory", out)`) | F-15 justified leaving the `(warning)` heading by claiming a correction would break the sibling test. The test asserts the substring `advisory`, which survives the edit, so the justification is false even though the deferral is reasonable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-15 corrected to record the falsification and to rest the deferral on honest grounds (shared with `run_work_begin`, cosmetic). Gap converted from `Carrier-Declined` to `Carrier: 7gr0vr`, filed during review. |
| PR-605 | low | IN-SCOPE | A. Correctness and data integrity | `agent_workflows/doctor.py:510` (`check_type` fan-out), `:530` (3-field `Drift` rebuild), `:1676` (`drift_exit_code`) | The plan repeatedly says "three other consumers"; there are four. `aw doctor` also consumes the rule, and is unaffected for a stronger reason than the plan's (it strips severity to `''`, so it fails closed at every registry value). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-09 corrected to name `aw doctor` and its three cited lines; the Deferred registry entry and the approval paragraph updated to say four. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-05's two vacuous assertions cannot detect an `error` -> `warning` registry edit. Remove them, or keep them and weaken V-05's mutation proof to a severity the hook/exit-code can see (`info`)? | Remove them; assert the registered severity alone and require the honest blast radius in the test docstring. | (a) Keep them and mutate to `info` instead, which they WOULD catch: rejected because `info` is not the plausible misimplementation (the plan's own risk paragraph names `warning`), so the proof would guard the wrong mutation while still implying the stronger claim. (b) Keep them as non-mutation-proved regression assertions: rejected because the plan cites them specifically as the guard that turns a registry lowering red, which they do not. | `agent_workflows/artifact_core.py:689` (`drift_exit_code` exempts only `info`); `agent_workflows/hooks/precommit_scope_gate.py:38` (no severity read); review probe measuring real `aw check plans --agent` exit 1 at both `error` and `warning`. | yes |
| D-2 | F-11's measurement does not reproduce. Correct it in place, block the plan on the corrected (wider) residue, or raise it as a blocking question for the maintainer? | Correct it in place, record that this plan WIDENS the residue, and surface it in the approval paragraph; do not block. | (a) Block as a BLOCKER finding: rejected because the residue is pre-existing in MECHANISM, the carrier `s9z85a` already exists, and blocking leaves the mandated commit verb unusable, which is the live release-gating bug `ldy1al` reports. (b) Leave F-11 as written: rejected as a false measurement in a plan whose approval paragraph asks the human to accept precisely that risk. | Review probe over three commit arrangements (`none-fail-closed`/DEMANDED, `commit-cohesion`/EXCUSED, trailered/DEMANDED); `agent_workflows/ipd_lifecycle.py` ~2917-2929 `else True` arm; carrier `s9z85a` already filed. | yes |
| D-3 | The `aw work begin` behavior change is real and uncovered. Add an E-item for it, or declare it out of scope? | Add E-06/V-06 covering it in the already-declared `tests/test_work_gate_severity.py`. | (a) Declare it out of scope: rejected because it is not separable - it is the SAME shared function and ships whether or not it is tested, so declaring it out of scope would ship an untested behavior change. (b) Split it into a sibling plan: rejected as disproportionate; it is one mirrored test in a file already in `- Scope-Paths:` with three sibling `work begin` tests. | `agent_workflows/work_cmd.py:321` and `:695` (the two call sites); `tests/test_work_gate_severity.py:303` (`test_work_begin_warning_drift_allocates_with_advisory`, the shape mirrored); review probe measuring the refusal today. | yes |
| D-4 | F-15's deferral justification is false. Keep the gap deferred, or bring the heading fix into scope? | Keep it out of scope, but replace the false reason with an honest one and file a carrier (`7gr0vr`) instead of declining the obligation. | (a) Fix the heading in this plan: rejected because it touches `run_work_begin`'s output for cosmetic gain and breaks the plan's one-partition discipline. (b) Keep `Carrier-Declined`: rejected because the declination rested entirely on the falsified test claim, so with that gone there IS an outstanding (if minor) obligation. | `tests/test_work_gate_severity.py:192`; review probe confirming the substring survives the corrected heading; backlog `7gr0vr` filed 2026-09-29. | yes |
