# Review findings: plan 00pirb

- Subject-Id: 00pirb
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (LOW, fixed), PR-807 (LOW, fixed)

## Round 1

Reviewed at HEAD `4e7dd52c` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision, including the new `E-06`/`V-06` pair.

THE PLAN'S PREMISE IS CORRECT AND I RE-MEASURED ALL OF IT. Every factual claim in the Findings table
verified. `probe_runner_safety_capabilities()` returns `supports_commit_gateway: False` with the note
beginning `DECLARED, NOT PROBED`, and `_RUNNER_SAFETY_PROBES[CAP_COMMIT_GATEWAY]` is `None` (F-1). The
`RUN-COMMIT-GATEWAY` row carries `binding='UNBOUND-BY-DEPENDENCY'` and `predicates=()` (F-8). `ACTION_CLASSES`
is `('read_only',)` with `required=()`, so nothing is gated (F-6). `RUNNER_ACTION_TO_CONTRACT_ACTION` is
literally `{}` and its comment does name `b7tlsh` as a successor (F-7). `RUN_FINDING_CODES` holds exactly 12
(F-8). Section 7 does read `ASSUME FOR THIS EXAMPLE` and `hhr83h` is `done` (F-2). F-10 reproduces: the spec
claims `tests/test_run_evidence_completion.py` asserts byte equality, that file is absent, and
`grep -rln RUN_FINDING_CODES tests/` returns nothing; its carrier `089bq4` resolves and is `open` with
`Blocks-Release: next`. F-5's keep-the-field argument also verified: `synthetic_gated_action` requires
`(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION)` with the stated docstring, and
`tests/test_host_capability_wiring.py` imports it, so the capability genuinely is the only lever by which the
shipped preflight's refusal half can be driven. OQ-01 and OQ-02 are both resolved correctly and on measured
grounds, and I would have reached the same answers.

So the plan needed no replan and its direction survived scrutiny intact. What review found is a set of
claims the plan makes ABOUT ITS OWN SCOPE that are false, and one pointer it was about to preserve that is
dead. Both matter more than they sound, because this is a plan whose entire subject is records asserting
things that are not true.

THE ONE THAT WOULD HAVE DONE REAL DAMAGE (PR-802). E-04 excluded 5.2 guarantee rows 1 and 3 on the ground
that they "belong to the `denypush` Set and to E-03 respectively". BOTH HALVES ARE FALSE. E-03 amends
Section 2.1's flag paragraph, not a guarantee-table row, so the second half is incoherent on the plan's own
text. And grepping all four `denypush` plans for the guarantee table, its rows, or the `Enforcement or proof`
column returns ZERO hits; `x2dwu5` E-03 declares the OPPOSITE, that "the 5.2 action table, and the 5.6
packet example's `deny_push` string are all UNCHANGED", and `01reg8` E-09's DO-NOT-TOUCH list names the
host-requirement bullet, the action table, and the packet example and does NOT name the guarantee table. So
nothing owns either row. Meanwhile both carry the IDENTICAL overclaim the plan is fixing in row 2: row 1
reads "Tool/network/credential denial plus captured process policy. An actual push attempt aborts the run."
while `supports_deny_push` and `CAP_DENY_PUSH` no longer resolve (`01reg8`) and `RUN-NO-PUSH` was retired
(`4h7tt0`); row 3 reads "Hook-preserving gateway and deny policy for `git commit --no-verify` or equivalent"
while `hook_preserving_commit` is a member of `UNREPRESENTED_SPEC_CAPABILITIES` whose own note says "this
contract has no field for it, so it cannot be gated here" - there is not even a field that could carry the
proof. A plan that fixes one row of three, while asserting a handoff for the other two that does not exist,
leaves them orphaned in precisely the manner it was filed to stop. Row 1 is the worse of the two, because
"An actual push attempt aborts the run" asserts a RUNTIME BEHAVIOR rather than merely naming a mechanism.
Fixed by FILING the carrier at review (backlog `ymlyqf`, `open`, `Work-Kind: bug`, `Blocks-Release: next`,
carrying both measurements and the reason each row was not fixed here), adding E-06/V-06 to VERIFY and
re-measure it at execution, rewriting E-04's exclusion to cite SCOPE rather than an owner, adding F-11, and
pointing Deferred's `Carrier:` at the real id6. Filing at review rather than deferring to E-06 was forced
as well as preferable: `check.ipd-uncarried-obligation` rejects a `Carrier:` value that is not a resolvable
bare id6 (measured: "malformed `Carrier` reference(s) 'filed by E-06' (expected a bare 6-char id6)"), so a
promised carrier cannot be cited. It also matches the precedent `sv9ce4` set in the `denypush` Set, where a
carrier was filed at authoring time precisely so it could not be lost if the Set never ran.

THE DEAD POINTER (PR-801). E-03 instructed "Keep both cross-references" on the clause it rewrites. One of
those two does not resolve: "5.8 row 3" is cited for the hooks guarantee, but Section 5.8 is the
interactive/unattended PARITY table whose row 3 is "Incomplete draft"; the hooks row is row 3 of the 5.2
guarantee-classification table. I checked the provenance rather than assuming rot: commit `844d195c`
(2026-09-06) introduced the reference, its own message says "5.8 row 3", and in that tree the hooks row IS
inside the section then numbered 5.8. So the citation was correct when written and rotted when sections were
inserted above it - the exact failure the repository's own citation convention (cite by symbol or quoted
string, never a bare offset) exists to prevent. Preserving it verbatim inside text this plan authors would
have shipped a known-dead pointer. Fixed: E-03 now retargets it to the 5.2 guarantee row and anchors it on
the quoted sentence rather than an ordinal, and V-03 demands command proof that "5.8 row 3" is gone and that
the replacement's quoted text is locatable under the `5.2` heading.

THE HOW-QUESTION E-02 LEFT TO THE EXECUTOR (PR-803). V-02 required proving the new test non-vacuous by
failing each of its three assertions, naming shipped seams for legs (1) and (3) but for leg (2) saying only
"state in prose which shipped seam was used or that none exists and the assertion was inverted locally".
That is a mechanism choice deferred to execution with no demonstration, which the workflow's HOW-question
rule forbids. I demonstrated it instead: `RunFindingCode` is a NamedTuple, so `row._replace(binding='BOUND',
predicates=('fake_pred',))` plus a rebind of `RUN_FINDING_CODES` and a `finally` restore works. Measured:
`MUTATED -> BOUND ('fake_pred',)` then `RESTORED -> UNBOUND-BY-DEPENDENCY`. Recorded into V-02 with the
observed output and with the warning that the rebind is process-global and must not ship inside a test.

COVERAGE OVERLAP E-02 DID NOT KNOW ABOUT (PR-804). E-02 specifies three assertions as if all three were
new. Measured: leg (1) is already asserted THREE times in the same file, and leg (3) in a weaker form once
(`test_requirement_map_structure_and_coverage` pins the map to the single `read_only` key). Leg (2) is
asserted NOWHERE, which is exactly why the binding and the prose could drift. The class is still worth
adding for (2) and for the joint statement, but an executor who did not know this would either write a third
duplicate or, worse, a later reader would delete a leg as redundant. E-02 now names the existing tests, says
why the legs are deliberately restated together, and requires leg (3) in the STRONGER form (no member lists
the capability) rather than the existing pin to one key.

THREE SMALLER ONES. The plan's gate (PR-805) carried no scope fence and an execution-contract paragraph
ending "before moving this plan to `.aw/records/plans/executed/`", which invites the hand `git mv` the
lifecycle contract forbids; replaced with a scope DECLARATION (not a stop directive, per the 2026-09-01
ruling), the tooled `aw ipd finalize` transition with the runner-ownership and `AW-LIFECYCLE-ROLE-001`
condition, and the `b7tlsh` gate-handoff ordering. `Scope-Paths` (PR-806) did not declare the backlog tree
E-06 writes to, and the Scope-check section claimed both paths were covered; both updated, with the note that
the path is a DIRECTORY because `aw backlog new` mints the filename. And the plan never checked for
concurrent spec editors (PR-807) on a spec that nine pending plans declare; I measured non-overlap with both
edit sites and recorded the measurement in the spec-sync section, along with the note that runner isolation
would make file overlap a non-hazard anyway but cannot decide SEMANTIC collision.

ONE THING I DELIBERATELY DID NOT FLAG. The plan carries five E-items for what is two prose edits, one test,
and a history note, which could read as over-structured. It is not: E-01's stop-if-moved measurement is
load-bearing precisely because this plan exists to fix a record that outlived its measurement, and folding it
into the edit items would remove the gate. Conceptual density is fine at six items; each names one
deliverable and one verifiable outcome.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | G (executability); citation convention | `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md:231` (clause "Sections 4.2 `RUN-COMMIT-GATEWAY` and 5.8 row 3"); `:1446` (`### 5.8 Interactive and unattended parity`, row 3 = "Incomplete draft"); `:1207` (hooks row, inside `#### Guarantee classification` under `### 5.2`) | E-03 instructed "Keep both cross-references", but "5.8 row 3" is DEAD: it names the hooks guarantee while 5.8 is the parity table. Verified as rot, not authoring error: commit `844d195c` (2026-09-06) introduced it and in that tree the hooks row was inside the section then numbered 5.8. The plan would have preserved a known-dead pointer inside text it authors | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now retargets it to the 5.2 guarantee row anchored on the quoted sentence rather than an ordinal, with the provenance recorded; V-03 demands greps proving "5.8 row 3" is absent and the replacement's quoted text resolves under the 5.2 heading |
| PR-802 | HIGH | UNDER-SCOPE | D (invariants); records honesty | `spec:1205` (row 1), `spec:1207` (row 3); `hsp.UNREPRESENTED_SPEC_CAPABILITIES['hook_preserving_commit']` = "this contract has no field for it, so it cannot be gated here"; `hasattr(hsp,'supports_deny_push')` False and `CAP_DENY_PUSH` unresolvable; `.aw/records/plans/executed/20260924-nopushflag-01-01reg8-...ipd.md:75` (DO-NOT-TOUCH list omits the guarantee table); zero grep hits for the guarantee table across all four `denypush` plans | E-04 excluded guarantee rows 1 and 3 claiming they "belong to the `denypush` Set and to E-03 respectively". BOTH halves false: E-03 amends Section 2.1, not a table row, and no `denypush` plan mentions the table. Both rows carry the IDENTICAL overclaim being fixed in row 2, and nothing owns them, so the plan would orphan two instances of the very defect it was filed to fix | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | FILED the carrier at review (backlog `ymlyqf`: `open`, `bug`, `Blocks-Release: next`, both measurements plus why neither row is fixed here), since `check.ipd-uncarried-obligation` refuses a non-id6 `Carrier:` value so a promised carrier cannot be cited; added E-06/V-06 to VERIFY and re-measure it; E-04's exclusion now cites scope, not an owner; added F-11; Deferred's `Carrier:` points at `ymlyqf` |
| PR-803 | MEDIUM | IN-SCOPE | E (testing); HOW-question rule | plan V-02 ("state in prose which shipped seam was used or that none exists and the assertion was inverted locally and reverted") | The falsification mechanism for leg (2) was deferred to the executor with no demonstration, which the HOW-question rule forbids: a resolution containing its own "or none exists, improvise" clause is undemonstrated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Demonstrated at review (`RunFindingCode` is a NamedTuple; `_replace` + rebind + `finally`, observed `MUTATED -> BOUND ('fake_pred',)` then `RESTORED -> UNBOUND-BY-DEPENDENCY`) and recorded into V-02 with the process-global warning |
| PR-804 | MEDIUM | IN-SCOPE | E (testing) | `tests/test_host_capability_extension.py` `test_the_unenforced_capability_is_declared_and_not_probed`, `test_a_forced_verdict_does_not_leak_out_of_the_context`, `test_the_production_path_is_unchanged_with_no_mock_supplied` (all assert leg 1); `test_requirement_map_structure_and_coverage` (weaker leg 3); `grep -rn RUN_FINDING_CODES tests/` empty (leg 2 unasserted) | E-02 specified three assertions as if all were new. Two are already covered; only leg (2) is genuinely missing, which is why the binding and the prose could drift. An executor unaware of this writes duplicates, or a later reader deletes a leg as redundant | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names the existing tests, states why the legs are deliberately restated jointly, and requires leg (3) in the stronger form (no member lists the capability) rather than the existing pin to one map key |
| PR-805 | MEDIUM | UNDER-SCOPE | G (execution contract) | plan gate ("before moving this plan to `.aw/records/plans/executed/`"); `agent_workflows/ipd_lifecycle.py:80` (`AW-LIFECYCLE-ROLE-001`) | The gate carried no scope fence and its closing sentence invites a hand move to `executed/`, which the lifecycle contract forbids; it also omitted the `b7tlsh` gate-handoff ordering | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with a scope DECLARATION (not a stop directive, per the 2026-09-01 ruling), the tooled `aw ipd finalize` transition with runner ownership and the `AW-LIFECYCLE-ROLE-001` condition, and the `graduated`-until-executed ordering for `b7tlsh` |
| PR-806 | LOW | UNDER-SCOPE | G (executability) | plan `- Scope-Paths:` (two entries) versus new E-06, which writes a backlog item | `Scope-Paths` did not declare the backlog tree, and the Scope-check section asserted every declared path was covered, so finalize's scope reconciliation would have flagged E-06's write as undeclared | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `.aw/records/backlog/open` to `Scope-Paths` and updated Scope check, noting the path is a directory because `aw backlog new` mints the filename |
| PR-807 | LOW | UNDER-SCOPE | C (operability) | Nine pending plans declare this spec in `Scope-Paths` (`cpi6p3`, `kcc71f`, `zdgc6t`, `yu47nf`, `entv1d`, and the four `denypush` plans); `x2dwu5` E-03 declares the 5.2 action table and packet example UNCHANGED | The plan never recorded whether its two edit sites collide with another pending plan's, on a heavily contended spec | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured non-overlap for both sites and recorded it in the spec-sync section, with the note that runner isolation makes file overlap a non-hazard but cannot decide semantic collision |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan AMEND 5.2 guarantee rows 1 and 3 itself, since they carry the same overclaim and nothing owns them? | No: file the carrier at review (`ymlyqf`) and keep the plan's two edit sites, with E-06 verifying it | (a) Amend all three rows here, which is the tempting "finish the table" move; (b) leave the exclusion as authored, which the measurement shows is an orphaning | Each needs a judgement this plan has not made. Row 1's cell asserts runtime behavior ("An actual push attempt aborts the run") and its correction is entangled with the live maintainer decision in backlog `wcbpqf` about how a PARTIAL push-denial guarantee should read. Row 3 cannot use E-04's shape at all, because `hook_preserving_commit` is in `hsp.UNREPRESENTED_SPEC_CAPABILITIES` (no field exists to name as the proof carrier). Filing the carrier at E-01 depth follows the precedent `sv9ce4` set in the `denypush` Set: a carrier filed at authoring time rather than promised by a closeout plan | yes |
| D-2 | Which `Work-Kind` and gate should the new carrier item carry? | `bug` with `- Blocks-Release: next` | `chore` (it is a records-only fix), or `bug` with no gate | `b7tlsh` itself is `Work-Kind: bug` for the identical defect class on row 2, so classifying its siblings differently would be incoherent. AGENTS.md's release-gate rule then makes the gate mandatory, not optional, for a live `bug` | yes |
| D-3 | What mechanism should V-02 require for falsifying leg (2), given no shipped seam exists? | A `_replace`-plus-rebind with a `finally` restore, demonstrated at review, recorded with its observed output | Leaving it to the executor's prose (as authored); inverting the assertion in the test source and reverting | The HOW-question rule requires a demonstration rather than a description. `RunFindingCode` is a NamedTuple (`type(row).__mro__` contains `tuple`, `hasattr(row,'_replace')` True), and the substitution was run: `MUTATED -> BOUND ('fake_pred',)` then `RESTORED -> UNBOUND-BY-DEPENDENCY` | yes |
| D-4 | Is the dead "5.8 row 3" pointer this plan's to fix, or a separate carrier like F-10's `089bq4`? | Fix it here | File it as a separate backlog item, consistent with how F-10 was handled | The clause CONTAINING it is being rewritten by this plan's own E-03, so the two are the same edit. F-10 is different in kind: it concerns Section 4.2's table guard, a site this plan does not touch, and its fix needs a restore-or-correct decision. Authoring fresh text around a pointer known to be dead would ship a defect knowingly | yes |
| D-5 | Is filing a new gated backlog item from a REVIEW legitimate, given plan-review edits planning documents only? | Yes, and it was filed | Leave the obligation as prose in the plan's Deferred section; add an E-item to file it at execution | A backlog item IS a planning document, not code, so filing one is within the workflow's mandate. The alternatives were both measured unusable: prose alone is exactly the uncarried obligation `check.ipd-uncarried-obligation` exists to catch, and a promised carrier cannot be CITED because the rule requires a resolvable bare id6 (measured refusal on `'filed by E-06'`). The repository's own precedent is explicit: `sv9ce4` was filed at authoring time with its plan recording that "a carrier that only exists if the Set executes is exactly the obligation-loss this Set was created to fix" | yes |
