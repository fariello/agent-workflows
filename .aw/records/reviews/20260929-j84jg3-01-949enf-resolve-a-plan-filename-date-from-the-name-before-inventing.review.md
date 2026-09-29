# Review findings: plan 949enf

- Subject-Id: 949enf
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ca6b180f` in a lane worktree. No pre-review snapshot was needed: the plan was
committed and unmodified, and the lane-input copy is byte-identical to the tracked file (`diff`
reported no output). Structural preflight `aw ipd lint --phase author --agent` reported `clean` /
exit 0 with no advisories; `--phase review-finalize` still conforms after every revision below.

THE DEFECT IS REAL AND I REPRODUCED BOTH HALVES rather than trusting the brief. Driving the real
`cli.main` in-process in throwaway git repos:

```text
BEFORE: ['20260714-oldset-03-abc123-probe.ipd.md', '20260715-oldset-04-def456-probe.ipd.md', '20260716-oldset-05-ghi789-probe.ipd.md']
renamed .../20260714-oldset-03-abc123-probe.ipd.md -> .../20260101-newset-03-abc123-probe.ipd.md
renamed .../20260715-oldset-04-def456-probe.ipd.md -> .../20260101-newset-04-def456-probe.ipd.md
renamed .../20260716-oldset-05-ghi789-probe.ipd.md -> .../20260716-newset-05-ghi789-probe.ipd.md
```

The first is the absent-`- Date:` case, the second carries the exact production malformed string
`- Date: 2026-07-23 (fleshed 2026-07-26 from research)`, and the third (good `- Date: 20260716`)
is preserved in the same run, which is what makes the failure selective exactly as F-01 claims.

F-07's correction of the backlog item also holds, on the item's own production shape:

```text
renamed .../20260723-1100-07-clean-delta-design-spec.ipd.md -> .../20260101-newset-07-qrokie-clean-delta-design-spec.ipd.md
renamed .../20260720-oldset-02-ctrl01-clustered-control.ipd.md -> .../20260720-newset-02-ctrl01-clustered-control.ipd.md
```

So `aw rename plans` DOES fabricate on a legacy name while preserving on a clustered one, and the
plan is right that the fence must cover both verbs. F-02, F-03, F-04, F-06, F-08, F-09, F-10 and
F-12 all verified as stated; the proposed three-tier helper was prototyped over six inputs and
produced `20260714`, `20260715`, `20260723`, `20260716`, `20260101` (nothing anywhere) and
`20260801` (front matter only), so the tier table is confirmed. The two name grammars are DISJOINT
(`_CLUSTERED_RE` and `_LEGACY_TIMESTAMP_RE` never both match), so the tier order between them is
safe. Baseline `3246 passed, 2 skipped, 3 warnings in 48.85s`.

PR-001 IS THE FINDING THAT CHANGES WHAT THIS PLAN IS. F-05 was the plan's entire severity case and
it is misattributed. The three named consequences are real defects but they are NOT consequences of
the FILENAME date, so this fix reaches none of them:

```text
plan_shard_move / _shard_target   -> _plan_date(TEXT)          no filename parameter
sweep_candidates / _age_days      -> _plan_date(TEXT)          no filename parameter
_is_grandfathered_plan(text, cutover_date)                     no filename parameter
carrier_severity_for_plan(plan_text, repo_root)                no filename parameter
```

The decisive measurement is the POST-FIX state, not HEAD: a plan whose filename ALREADY reads the
correct `20260714`, with `- Date:` still absent, shards to `202601` rather than `202607`. So the
outcome is identical before and after. The three measurements quoted in F-05's own Evidence column
were each performed on TEXT (`carrier_severity_for_plan("- Date: 2026-09-28")`,
`carrier_severity_for_plan("- Id: abc123")`, `_is_grandfathered_plan(no-date, "20260828")`), which
is why the error was not visible from the evidence as recorded: those calls demonstrate the
FRONT-MATTER defects already filed as `dkfthf` and `5h8u3z`, not this one.

That matters beyond tidiness. It propagated into the Concern, the Goal, the Scope, the Scope check
(which invited a reviewer to "re-fence to include `plans_archive.py`" for a stronger assertion), the
workflow-history line, and OQ-02's rationale, and it produced PR-002: E-05 instructed the executor
to assert an archive-shard outcome that cannot hold even after the fix. E-05's own second paragraph
half-admits this ("the archive verb still computes `20260101` ... REGARDLESS of this plan's fix")
while its first paragraph demands the opposite, so the item contradicted itself and a conforming
executor would have written a failing test and then had to choose which half to obey.

I replaced the severity case rather than deleting it, because the defect IS worth fixing on a
correct basis (F-13, established by enumerating every `group("date")` site in the package): the
filename date is SELF-PERPETUATING, since both verbs read it precisely in order to preserve it, so
one fabrication is re-asserted by every later rename and the true date survives only in git; it
feeds the `<date>-<set>-<nn>` legacy citation handle `artifact_refs` uses to rewrite references; and
it is the identifier humans and agents actually read. F-06 measures all three having already
happened to the `qrokie` plan, whose real date propagated wrong into `DECISIONS.md` and a spec.

PR-003 IS A FACT THE PLAN COULD NOT HAVE KNOWN AND IT STRENGTHENS THE PLAN. Both verbs once had
this exact coverage. `tests/test_awnaming_grammar_and_producers.py` carried
`PlansMvPreservesOrderAndDateTests`, whose docstring reads "a bare `aw rename plans <id6> --slug X`
must not clobber Order or Date" and which asserted `- Date: 20260810` survived, plus
`PlansGroupPreservesOrderTests` (`e3hzyc`'s seven cases). Both were deleted wholesale in
`19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 318 files, 219,063 deletions),
and `grep -rn PreservesOrderAndDate` now returns nothing. So E-01/E-02 RESTORE a deleted guard
rather than adding a novel one. The Order half is not restored here (different invariant, would
roughly double the test surface), and I filed `l8upzx` for it rather than leaving a prose note or a
`NEEDS-FILING` placeholder; I verified the Order CODE is still correct (a bare metadata-only
regroup preserves `- Order: 3`), so that item is a coverage debt and is correctly `chore`, not a bug.

PR-006 checks the one spec sentence that could be read AGAINST this fix, because the plan raised it
honestly and then moved on. Spec `agents-artifact-organization` Section 4.2 calls `YYYYMMDD` "the
SET's canonical date, shared by all members", which could license a regroup to restamp a member.
Measured over the live corpus: 31 of 589 clustered Sets ALREADY have members with different leading
dates (`rununify` spans four), and no code enforces the property. So preserving each member's own
date breaks no maintained invariant, and the plan's reading was right.

RIGHT-SIZING: five E-items over two files, each one concern. E-04 is deliberately an
evidence-only item expecting a negative finding, which is legitimate and well-justified by the
`e3hzyc` loop-index precedent (I confirmed the preview prints `p.new_path.name`, so no edit is
expected). No `IPD-Z602` advisory fired. P16 is satisfied: every added test drives a real verb and
asserts on filenames, and the scope fence now forbids source-reading assertions explicitly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression; G. Plan executability | plan F-05 and Concern para 3; `agent_workflows/plans_archive.py` symbols `plan_shard_move`, `sweep_candidates`; `agent_workflows/check_engine.py` symbols `_is_grandfathered_plan`, `carrier_severity_for_plan` | F-05 is the plan's whole severity case and it is MISATTRIBUTED. All four named consequences (archive shard, sweep age, cutover grandfathering, carrier severity) are decided by the `- Date:` FRONT MATTER; none of those consumers receives a filename or a path, so this filename fix reaches none of them. Decisive: a plan whose filename already reads the correct `20260714` with `- Date:` absent still shards to `202601`, identical to HEAD. The claim propagated into the Concern, Goal, Scope, Scope check, history line and OQ-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 marked WITHDRAWN in place with the measurement that falsifies it and a pointer to the front-matter carriers. Added F-13 enumerating what the filename date ACTUALLY drives (self-perpetuation, the `artifact_refs` legacy citation handle, human/agent reading). Corrected the Concern, Goal (new "no longer claims" paragraph), Scope (new "excludes by measurement" clause), Scope check (withdrew the re-fence invitation) and OQ-02. |
| PR-002 | HIGH | IN-SCOPE | E. Testing; G. Plan executability | plan E-05 para 1 (quoted "asserts the ARCHIVE SHARD it then lands in is the one its real date implies") versus E-05 para 2 (quoted "the archive verb still computes `20260101` and shards to `202601` REGARDLESS of this plan's fix") | E-05's headline instruction demands an assertion that CANNOT PASS even after the fix, and its own second paragraph says so, so the item contradicts itself and a conforming executor would write a failing test and have to choose which half to obey. Measured: post-fix, a correctly-named plan with no `- Date:` still shards to `202601`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 rewritten to pin the consequence the fix DOES close: a two-successive-regroup test proving the real date survives both, which pins the self-perpetuation mechanism (F-13 tier 1) that made the F-06 casualty permanent. Added an explicit prohibition on any archive, sweep, cutover or carrier-severity assertion. V-05 rewritten to match and to treat such an assertion as a FAILED validation. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. Anti-regression; E. Testing | `git show 19313eed^:tests/test_awnaming_grammar_and_producers.py` classes `PlansMvPreservesOrderAndDateTests` and `PlansGroupPreservesOrderTests`; commit `19313eed` | Both verbs ONCE had date (and Order) regression coverage and it was deleted wholesale in `19313eed`, which the plan does not know. So E-01/E-02 restore a lost guard rather than adding a new one, and the plan's claim that `e3hzyc` "already fixed and shipped" the Order behavior is true of the CODE but its guard is gone, so an Order regression would now pass CI silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with the deletion commit and the verification that the class names appear in no `.py` file. E-01 now tells the executor they are RESTORING a deleted guard, to read the deleted class first, and not to reintroduce its subprocess `_run_cli` shape. Filed backlog `l8upzx` for the un-restored Order half (verified the Order code still correct, so `chore` not `bug`) and replaced the placeholder carrier with it. Recorded in Scope, Scope check and Deferred. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture and operability | `tests/test_group_verb_policy.py` module docstring (quoted "setid length policy enforcement across all aw group backends"); its five tests all parameterized over `GROUP_TYPES` | The chosen test home declares itself as covering setid length policy for `group` backends only, and every existing test is a setid-length case. Adding a date-preservation suite for `group` AND `rename` makes that first line false, which is how a file's stated purpose rots. The file is nonetheless the right pragmatic home given `Scope-Paths` and the deleted module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 stating the mismatch and endorsing the file anyway. E-01 now requires the module docstring be widened in the same edit to name both topics and both verbs and to record the `19313eed` restoration, and forbids touching the five existing setid tests. Added to Required tests. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan `## Approval and execution gate` as authored (a one-paragraph EXECUTION CONTRACT with no declared surface and no approval summary) | The gate had the commit rule, the honesty rule and the lifecycle conditional, but no SCOPE FENCE declaring the intended surface for post-hoc reconciliation, and no statement of what a human would be approving. It also carried the stale "do not widen the fence to make E-05 assert a stronger shard outcome", which PR-001 makes meaningless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a scope fence written as a declaration with a "made and then JUSTIFIED" clause and no stop directive (2026-09-01 ruling), enumerating nine negative constraints. Added a "what a human would be approving" paragraph naming both review corrections. Kept the one legitimate stop directive (unreproducible failing-first) and labelled it as the genuinely-unsafe case. Removed the stale shard wording. |
| PR-006 | LOW | IN-SCOPE | Evidence completeness | spec `agents-artifact-organization` Section 4.2 (quoted "the SET's canonical date, shared by all members"); the live plans corpus | The plan raises the set-canonical-date tension honestly in its spec-sync section but leaves it as a reading rather than a measurement, so a reviewer cannot tell whether preserving a member's own date breaks a maintained invariant. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16 with the corpus measurement: 31 of 589 clustered Sets already carry members with different leading dates, and no code enforces the property (no `--date` flag exists on either verb), so the invariant is already unenforced and the plan's reading is safe. Cited from the Scope check. |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy | plan F-05(b) (quoted "roughly nine months older"); plan F-06 and commit `05c4deb1` | Two quantitative overstatements. (1) The `20260101`-versus-`20260714` gap is 194 days, about 6.4 months, not nine. (2) The `qrokie` casualty was produced by the one-off bulk migration `05c4deb1` ("back-fill Id + cluster the plan corpus"), which produced exactly ONE `20260101` name out of 122 renames, not by an `aw group plans` invocation, so the historical casualty is not evidence of the live verbs having caused it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 with both corrections and the arithmetic. The defect's reachability through the live verbs stands on F-01 and F-07, both of which I reproduced directly, so correcting the provenance of the historical casualty does not weaken the case for the fix. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-05, the plan's entire severity case, is measurably misattributed. Reject the plan, ask the maintainer whether it is still worth doing, or fix the basis and keep the fix? | FIX THE BASIS AND KEEP THE FIX: withdraw F-05 in place, add F-13 establishing what the filename date really drives, and correct every downstream restatement. | (a) `REJECT - NEEDS REPLAN`: rejected, because the DEFECT is real and reproduced twice and the proposed code change is correct and minimal; only the justification was wrong, which is a bounded edit, and replanning would discard a correct fix over a correct-able rationale. (b) Ask the maintainer whether a filename-only fix is worth shipping: rejected, the repository answers it. `artifact_rename.compute_target_name` already never fabricates a date for every other artifact type, so preserving a name's date is the established house behavior and bringing plans into line needs no new decision. (c) Delete F-05 silently and leave the severity unexplained: rejected, a plan carrying `Blocks-Release: next` with no stated harm is unapprovable, and the honest harm is available. (d) Keep F-05 and note it is "partly" reached: rejected as false, the measured reach is exactly zero. | `plan_shard_move`, `sweep_candidates`, `_is_grandfathered_plan`, `carrier_severity_for_plan` all take text and no filename; post-fix probe shards `202601` for a correctly-named file; every `group("date")` site in `agent_workflows/*.py` enumerated to build F-13; `artifact_rename.compute_target_name` reads the date from whichever grammar matched. | yes |
| D-2 | E-05 as authored cannot pass. Delete the item, or replace its assertion? | REPLACE IT with a two-successive-regroup test of the self-perpetuation mechanism. | (a) Delete E-05 and drop to four E-items: rejected, the plan would then pin only filenames and never the CONSEQUENCE, and E-05's instinct ("pin the consequence, not only the filename") is right even though its chosen consequence was wrong. (b) Keep the archive assertion and widen `Scope-Paths` to `plans_archive.py`: rejected, that converts a two-file fix into a different plan, and `dkfthf` already owns the archive defect in full. (c) Weaken E-05 to assert only the filename, duplicating E-01: rejected as redundant, it would add a fifth item that tests nothing new. | Post-fix shard probe returns `202601`; `run_mv`/`plan_set_assign` both READ the filename date to preserve it, so a fabrication is re-asserted on every later rename, which is the mechanism by which the F-06 casualty became permanent; `dkfthf` is filed `bug`/`Blocks-Release: next` and owns the front-matter copy. | yes |
| D-3 | The deleted `PlansGroupPreservesOrderTests` (Order half) is not restored by this plan. Fold it in, decline it, or carry it? | CARRY IT as a new backlog item, filed during review rather than left as a prose note or a `NEEDS-FILING` placeholder. | (a) Fold the seven Order cases into this plan: rejected, they pin a different invariant with a different precedent (`vf03z3`/`e3hzyc`) and would roughly double the plan's test surface for a code path that is currently CORRECT. (b) `Carrier-Declined`: rejected, this is a genuine coverage hole an unrelated commit created, not a deliberate divergence, so the carrier rules oblige a durable handoff. (c) Leave it in this plan's Deferred prose with no item: rejected, an obligation recorded only in a pending plan's prose is invisible to `aw attention` and vanishes when the plan executes. (d) File it as a `bug` with a release gate: rejected, the code preserves Order correctly today (verified), so there is no live defect to gate a release on; it is a coverage debt, hence `chore`. | `git show 19313eed^:` contains both classes; `grep -rn PreservesOrderAndDate` returns nothing; a bare metadata-only `aw group plans ... --apply` measured preserving `- Order: 3`; filed as `l8upzx`. | yes |
| D-4 | Spec Section 4.2 calls the date "the SET's canonical date, shared by all members", which could license a regroup to restamp it. Does preserving each member's own date violate the spec? | NO. Record the corpus measurement and proceed without a spec amendment. | (a) Treat it as a blocking spec conflict: rejected on evidence, the property is already unenforced in 31 of 589 live Sets and no code implements it. (b) Amend the spec in this plan to say the date is the member's: rejected as over-scope and as a contract change this defect does not require; the spec gap is that it never says which date a rename assigns when front matter is unreadable, and filling that by reading the filename is consistent with both specs. (c) Add a `--date` flag so an operator can set a set-canonical date: rejected, explicitly out of scope and a new public surface. (d) Say nothing: rejected, the plan raised the tension and a reviewer should either confirm or refute it rather than leave it as a worry. | 589 clustered sets enumerated, 31 date-heterogeneous (`rununify` spans `20260829`/`20260903`/`20260915`/`20260921`); no `--date` flag on either verb; spec `artifact-organization-plans-adopter` Section 8 OQ1 quoted "The leading date is the plan's date". | yes |
| D-5 | The plan's failing-first contract says to "stop and report" if the fabrication cases cannot be reproduced failing. The 2026-09-01 ruling forbids flagging a plan for lacking a stop clause and requires flagging one that HAS it for the out-of-scope-edit case. Keep this stop directive? | KEEP IT, and separately ADD the scope fence with an explicit "made and then JUSTIFIED" clause. | (a) Remove the stop directive as a ruling violation: rejected, it is misreading the ruling. The ruling governs stop-over-a-SCOPE-question; it explicitly preserves a stop directive "for a genuinely unsafe condition", and an unreproducible failing-first means the defect is unpinned and the plan's premise is in doubt, which is exactly that case. (b) Keep the gate as authored with no fence: rejected, the fence is a required execution-contract element and its absence is a finding. (c) Add a fence that also says stop on an out-of-scope edit: rejected outright, that is the wording the ruling forbids and which propagated into 224 executed plans. | The 2026-09-01 maintainer ruling's own carve-out for a genuinely unsafe condition; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` requirements as the sanctioned justify-afterwards mechanism. | yes |

### Deferred and open

- (none). All seven findings were FIXED in place. No finding reached the repository's gate threshold
  (`review_findings_gate.block_at`, default `HIGH`) while unfixed, so no escalation to a
  `- Blocking: yes` open question was required. The two HIGH findings (PR-001, PR-002) were both
  repaired with bounded edits rather than deferred.
- Pre-existing open questions: OQ-01 and OQ-02 remain `Blocking: no` / `Status: resolved` (OQ-02's
  rationale was corrected under PR-001 and D-1). OQ-03 remains `Blocking: no` /
  `Status: deferred` / `Owner: maintainer`, correctly, since repairing a committed record's filename
  is a judgement about rewriting history and is carried by `tf4jz5`; a typed `Gate-Kind`/`Gate-Ref`
  is not required for a deferred open question (that obligation is on a deferred SPEC).
- No `Reversible: no` decision was taken. One backlog item (`l8upzx`) was created; creating a
  tracking item is reversible by closing it.
