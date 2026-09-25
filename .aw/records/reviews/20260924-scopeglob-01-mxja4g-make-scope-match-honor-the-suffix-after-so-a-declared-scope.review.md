# Review findings: plan mxja4g

- Subject-Id: mxja4g
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `scopeglob`, the only child, `- Item-Dependencies: none`. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize --agent` reports `clean`, exit 0, ZERO findings after the revisions. The plan
file was committed and unchanged, so no pre-review snapshot was needed. Everything below was measured
in this lane at HEAD `f768cadd`.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND EVERY AUTHOR CLAIM HELD. I re-derived all eight author
findings independently rather than re-reading them, and none was wrong. Specifically: the six defect
rows reproduce exactly; the code is shaped exactly as described (`_scope_match`'s `**` branch really
does `prefix = pat.split("**", 1)[0].rstrip("/")` and return a bare prefix test); `grep` really does
find that fallback in only that one function; and the blast-radius claim that ZERO plans narrow is
correct, re-derived over 444 plans and 2623 tracked paths.

I ALSO IMPLEMENTED E-02's PROPOSED MATCHER AT REVIEW, because a plan whose central mechanism is a
described algorithm should not be approved on the description alone. It behaves exactly as E-02
specifies on all 14 rows, and the pathological pattern returns `False` in about 0.0001s with `lru_cache`
memoization, so E-02's no-exponential requirement is achievable as written (F-15).

```text
DEFECT ROWS, reproduced at HEAD f768cadd (old matcher):
  True   .aw/records/backlog/open/anything.backlog.md   vs  .aw/records/**/index.md     # F-1
  True   .aw/records/specs/x.spec.md                    vs  .aw/records/**/index.md     # F-1
  True   tests/anything.txt                             vs  tests/**/*.py               # F-2
  True   agent_workflows/README.md                      vs  agent_workflows/**/*.py     # F-2
  True   tests/sub/test_a.py                            vs  tests/*.py                  # F-3
  False  .aw/records/specs/x.spec.md                    vs  .aw/records/plans/**        # control

REVIEWER'S REFERENCE IMPLEMENTATION of E-02: all 6 must-refuse -> False, all 8 must-accept -> True,
  a/**/**/**/**/**/**/z  vs a 30-segment path -> False in ~0.0001s

BLAST RADIUS, re-derived (F-12):
  pending 14 narrowed 0 | executed 402 narrowed 0 | superseded 27 narrowed 0
  not-executed 1 narrowed 0 | reusable 0 narrowed 0
  all 10 distinct glob entries in the plans tree end in `/**` -> unchanged branch
```

THE SUBSTANCE OF THE REVIEW IS WHAT THE PLAN DID NOT SAY, not what it got wrong. Three things: the
refusal this change makes routine names no remedy (PR-001); the plan's own measurement of that
behavior change is an undercount that also mischaracterizes the affected class (PR-002); and the plan
lists five fences without saying which can actually regress, which is the question a reviewer or
approver most needs answered (PR-004).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | F (UX, prevent silent failure) | `agent_workflows/work_cmd.py` `run_commit` out-of-scope branch | THE REFUSAL THIS PLAN MAKES ROUTINE IS A DEAD END. `run_commit` prints `"aw commit: refusing - out-of-scope change(s) present:"`, the offending paths, and `"  declared Scope-Paths: "`, then returns 1. It names NO remedy: not `--no-plan`, not declaring the path, nothing. That was tolerable while the matching bug made the refusal rare, and this plan is precisely what makes it common: F-5 measures 11 files across 6 `work:` commits (as re-measured, PR-002) that will now be refused, and the agent hitting it is mid-execution with work to land. Shipping a newly frequent dead-end refusal is a usability regression traceable to this change, and it is the kind of thing that gets "fixed" in the field by reaching for `--no-plan` reflexively, which defeats the fence. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | Added E-07: one remedy line naming both legitimate routes, with the pre-existing message lines and exit code held byte-identical, plus a test row asserting the text contains `--no-plan` and `Scope-Paths`. Added V-07. `agent_workflows/work_cmd.py` added to `- Scope-Paths:`, `Highest E allocated` 06 -> 07, and the over-scope admission justified in `Scope check` rather than left silent. |
| PR-002 | MEDIUM | IN-SCOPE | E (verification) | `git log --name-only --since=2026-08-01`; plan `F-5` | F-5 UNDERSTATES ITS OWN BLAST RADIUS AND MISFRAMES THE AFFECTED CLASS. Measured only from 2026-09-22, it reports 10 files in 5 commits, all backlog. Re-measured from 2026-08-01: 11 files across 6 commits, and the sixth (`4f7f5461`) is a `.spec.md`. So the newly refused class is "any records path", not "backlog files". This is not pedantry: OQ-01 is framed entirely as a possible `.aw/records/backlog/**` allowance, which would NOT have covered the measured spec case, so a maintainer answering OQ-01 from the plan as written would pick a remedy that misses part of the problem. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 records the re-measurement with the sixth commit named; OQ-01's title and rationale widened from "backlog items" to "records artifacts (backlog items, and also specs)" with the spec case called out as not covered by a backlog-only allowance; the gate's approval statement carries the corrected figure. |
| PR-003 | MEDIUM | IN-SCOPE | E (verification) | plan `F-1` ("1147 tracked paths"), `F-4` (10/400/27/1), `E-06`/`V-06` ("1826 passed") | FOUR LIVE ARTIFACT COUNTS WERE STATED AS THE BAR. F-1's 1147 is 1151 at this HEAD; F-4's per-directory plan counts are 14/402/27/1; and `1826 passed` is a suite count that drifts with every merge. Per the live-artifact convention, a criterion counting live artifacts must state the required PROPERTY and re-derive at execution; a figure measured at authoring belongs in prose as context. As written, an executor would either paste a stale number as if current or read a benign drift as a failure. The narrowed-count `0` is the real bar and survives; the raw populations do not. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-11 and F-12 record both measurements and label the counts live; V-01 states the per-row booleans are the bar and the tracked count must be re-derived; V-05 states `narrowed: 0` is the required property and forbids reproducing either set of population counts; E-06 and V-06 now require the baseline re-derived at execution HEAD and the delta stated as tests added. |
| PR-004 | MEDIUM | UNDER-SCOPE | C (architecture / operability) | `check_engine.check_scope_drift`; `wtiso_gate.check_scope`; `run_evidence.dirty_within`; `runner_shared.compute_scope_reconciliation` | THE PLAN NAMES FIVE FENCES AND SAYS WHICH DIRECTION ONLY ONE MOVES. Its Concern lists all five callers, and F-5 covers `aw commit` and asserts finalize is fine, but it says nothing about the other three, which is exactly the "can this start refusing somewhere I am not looking?" question an approver has. Verified at review: the post-execution drift rule is gated on a LIVE begin receipt (`read_receipt` then `_receipt_is_live`) and this tree has NO receipts, so it has no subject and `aw check` reports zero `check.scope-drift` findings; `wtiso_gate.check_scope` has ZERO callers by deliberate design, asserted structurally by `tests/test_containment_predicates.py`; and `dirty_within` gets strictly MORE PERMISSIVE, since narrowing the matcher can only shrink the hit set it reports as the refusal reason. All three are safe, and none of that was written down. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 and F-14 record the three verifications with their mechanisms; `Scope check` gained a paragraph enumerating all five fences and which can actually regress, so the answer is in the plan rather than re-derived per reviewer. Required tests gained `tests/test_containment_predicates.py` and `tests/test_check_engine_release_gate.py`, the two files asserting those properties. |
| PR-005 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE WAS ONE PARAGRAPH AND MISSED THIS PLAN'S DEFINING HAZARD. It had the commit discipline, the honesty rule, and the OQ dispositions, but no statement of what a human is approving (this tightens a fence every plan is judged against, with a measured friction cost), no declaration-style scope fence, no stop conditions, and no mention of SELF-APPLICATION: E-02 changes the very predicate `aw commit` uses, so the commit landing the change may be judged by the new matcher. An executor meeting an unexpected refusal there could reach for `--no-plan` and bypass the fence this plan exists to repair. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: what is approved, with the corrected measured cost and a pointer to OQ-01 for a maintainer who would rather widen; declaration-style fence naming the added `work_cmd.py`; an explicit self-application paragraph recording that this plan's own four declared paths are in scope under BOTH matchers (verified at review) and forbidding `--no-plan` as a workaround; two genuinely-unsafe stop conditions (E-01 finding the defect already fixed; a nonzero narrowed count); the bare-`pytest` rule with the `-qq` trap; the no-`git stash` restatement for the revert runs; staged-set verification; conditional transition with no hand-rolled `git mv`; and the `cfab6d` HANDOFF verified as already satisfied. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001's remedy hint requires editing `work_cmd.py`, which the plan did not declare. Add it here (widening scope), or file it as a follow-up? | Add it here as E-07 and declare `work_cmd.py`. | A follow-up plan or backlog item. Rejected: it would ship the dead-end refusal for the whole interval between the two changes, and the refusal only becomes frequent BECAUSE of this plan, so the two are one user-visible change rather than two. | The workflow's over-scope default is removal or explicit deferral, but the same section defines OVER-SCOPE as "not traceable to a driver or requirement"; this hint is traceable directly to E-02's measured consequence (F-5/F-10), so it is in-scope work that was simply undeclared. Recorded as an admitted over-scope with its justification in `Scope check` rather than hidden. | yes |
| D-2 | Does the self-application hazard (E-02 changing the predicate that judges its own commit) need a maintainer decision or a sequencing change? | No. Verify it is safe, record it, and forbid the dangerous workaround. | (a) Split E-02 so the matcher lands in a separate commit from the tests (rejected: the hazard is identical, and a half-landed matcher is worse). (b) Raise it as a blocking question (rejected: it is answerable from evidence, and I answered it). | Measured: this plan's four declared paths (`agent_workflows/ipd_lifecycle.py`, `agent_workflows/work_cmd.py`, `tests/test_scope_match.py`, the spec file) are all in scope under BOTH the old and the new matcher, and the plan file itself is covered by the `.aw/records/plans/**` implicit allowance, which takes the UNCHANGED trailing-`/**` branch. So the commit cannot refuse itself either way. The residual risk is an executor MISREADING some other refusal as this one and reaching for `--no-plan`, which the gate now names as a stop condition. | yes |
| D-3 | F-3 (single `*` confined to one segment) is not in backlog `cfab6d`. Is fixing it here over-scope that should be removed? | Keep it. The plan's existing justification is correct. | Splitting F-3 into its own plan. Rejected: E-02 rewrites the whole glob branch, so excluding F-3 would require deliberately re-implementing a known bug inside the replacement. | The function's own comment already states the intended behavior ("`dir/*.py` should not match nested"), so this is restoring documented intent rather than adding a requirement; and F-4/F-12 measured zero plans narrowing, so it carries no blast radius. The plan said this in `Scope check` and I verified both halves. | yes |
| D-4 | Is amending an `implemented` spec in place (E-05) legitimate, or does it need its own spec-lifecycle step? | Legitimate as authored; no change required. | Requiring the spec be moved back to a review status, or splitting the amendment into a separate spec-first change. Rejected: neither is the established practice here. | AGENTS.md states a plan MAY amend a spec and MUST declare it in `- Scope-Paths:`, which this plan does. The target spec already carries three in-place amendments with inline `(amended <date>, <setid>)` markers (Sections 4.5, 6, and the checkpoint table), so the convention is established in that exact file. E-05 also correctly limits itself to ONE added sentence and V-05 now pins that nothing else changed. | yes |
| D-5 | The author's counts (1147 tracked paths, 10/400/27/1 plans, 1826 passed) differ from mine. Is that a finding against the author's rigor? | No. Treat as expected drift; fix only where a count was used as the BAR. | Raising it as an evidence-integrity finding. Rejected: the tree demonstrably grew between authoring and review (2623 tracked files, 444 plans), the direction of every drift is consistent with growth, and the load-bearing figure (`narrowed: 0`) is identical in both measurements. | The live-artifact convention treats a count measured at authoring as legitimate CONTEXT and objects only when it becomes an acceptance criterion. That is exactly the line PR-003 draws: the four counts stay in the plan as prose, and the `V-*` bars were rewritten to state properties and require re-derivation. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent mxja4g -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent mxja4g -> {"outcome":"clean","exit":0,"findings":0}  (after revisions)

THE ONE FALLBACK, confirmed unique:
  grep -rn 'split("\*\*"' agent_workflows/  ->  ipd_lifecycle.py only (one hit, in _scope_match)

FIVE FENCES, direction of change (PR-004):
  work_cmd.run_commit               LIVE behavior change, refuses more     -> mitigated by new E-07
  ipd_lifecycle.finalize_precheck   reclassifies as out_of_scope           -> runner auto --scope-reason
  check_engine.check_scope_drift    gated on a LIVE receipt; none exist    -> no subject (aw check: 0 drift)
  wtiso_gate.check_scope            ZERO callers by design                 -> inert
  run_evidence.dirty_within         strictly MORE permissive               -> safe direction

work_cmd._in_scope('.aw/records/backlog/open/...', ['.aw/records/plans/pending'], <plan>) -> True today
  (F-5's mechanism; becomes False after the fix)

IMPLICIT ALLOWANCES, before and after:
  admitted today but not after: 1151 tracked paths, ALL via '.aw/records/**/index.md'
  tracked paths matching '.aw/records/**/index.md' AFTER the fix: 0    (F-6's claim holds)

HISTORY (PR-002), git log --since=2026-08-01, work: commits only:
  6 commits, 11 files admitted ONLY via the hole
  b369e3a3(1) 14afd939(2) c23a02a1(2) de4ba4de(4) 908db905(1) 4f7f5461(1 <- a .spec.md)

SELF-APPLICATION (D-2): this plan's 4 declared paths -> in scope under BOTH matchers
cfab6d HANDOFF: item has 'Blocks-Release: next'; this plan has 'From-Backlog: cfab6d' + the same
  'Blocks-Release: next' -> evaluate_blocking_close HANDOFF route satisfied
```

NOT RE-RUN AT REVIEW, and stated rather than implied: the repository suite. This review changed only
planning prose, so I claim no suite baseline in either direction. I did NOT reproduce F-8's
monkeypatched full-suite run, because writing the required plugin file outside this workspace is not
permitted here; instead I verified F-8's BASIS directly, which is arguably stronger for the specific
risk: zero test fixtures in the whole suite declare a Scope-Paths value with a suffix after `**` or a
single-`*`-with-suffix pattern, and only three test files reference any scope predicate at all, none
with an affected pattern. E-06 re-runs the bare suite at execution, which is the correct treatment.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open. OQ-01 and OQ-02
remain open at `Blocking: no`; OQ-01 was WIDENED at review (PR-002) because its framing missed a
measured case, which under the 2026-09-10 maintainer ruling still does not make the plan `NO-GO`.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: this is
a FENCE TIGHTENING, so its whole point is that some things that used to be accepted are now refused,
and the measured friction is 11 files across 6 commits in about five weeks needing `--no-plan` or an
explicit declaration. Zero existing plans lose a declared path and finalize is auto-reconciled, so the
cost falls entirely on the `aw commit` path, which E-07 now makes self-explanatory. The one decision
genuinely reserved to the maintainer is OQ-01: if the preference is to keep filing records artifacts
alongside plan work without ceremony, the right answer is a new implicit allowance for a deliberately
chosen class (note the measured case includes a spec, not only backlog), and that reverses part of
this plan's intent, so it is better answered before approval than after.
