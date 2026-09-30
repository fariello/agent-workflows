# Review findings: plan xvon5j

- Subject-Id: xvon5j
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-Y01 (HIGH, fixed), PR-Y02 (HIGH, fixed), PR-Y03 (MEDIUM, fixed), PR-Y04 (MEDIUM, fixed), PR-Y05 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `4b983db3`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author` reported `conforming` BEFORE semantic review and again at `review-finalize`
after revision; `aw check` reports zero findings against this plan both before and after. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. `- Item-Dependencies:
executed:76w6mq` resolves: that plan is in `.aw/records/plans/executed/`.

THIS IS AN UNUSUALLY WELL MEASURED PLAN AND MOST OF IT VERIFIES EXACTLY. I re-ran every finding rather
than trusting any:

- F-01 reproduces verbatim. `python3 -m agent_workflows set reviewed uyeko5 --dry-run` prints
  `FAIL Selector 'uyeko5' is a id6 collision matching multiple files (a data bug to fix, not overridable
  by --force)` and names the executed `runflags` plan plus both `awmetastore` research documents.
- F-03's core reproduces: `read_artifact_record` answers `uyeko5`/`reviewed`/`runflags` for BOTH
  documents, whose own fences read `id: takpys`/`27rjro`, `status: reference`, `set: awmetastore`. All
  three fields wrong, as claimed.
- F-04 reproduces: `match_selector('runflags')` returns 3 records, the real plan plus both quoting
  documents.
- F-02 reproduces: `grep status_set agent_workflows/artifact_adopt.py` returns nothing (exit 1), and
  `global_id6s`' body delegates to `_adopt.repository_id6s`, so the docstring's attribution to
  `status_set._ID_RE` is indeed false.
- F-07 reproduces precisely: `build_dependency_index` reports exactly ONE multi-owner id6, `uyeko5`,
  with 1 `plans` + 2 `research` owners.
- F-08 and F-09 reproduce to the token. Simulating the bounded reader over the whole inventory, exactly
  4 of 2650 selector tokens change answer, and they are the same four: `uyeko5` 3->1, `runflags` 3->1,
  `` `awoptimize` `` 1->0, `` `lane-branch-triage` `` 1->0. Inventory size is unchanged (2056 both ways).
- F-11 and F-12 reproduce: the `status_set`/`selectors` pattern pairs are not byte-identical, and
  `_ID_LINE_RE` versus `_ITEM_ID_RE` diverges on 0 of 2675 records.
- F-06's structural claims reproduce: `_META_BLOCKS_RELEASE_RE` diverges on 3 files,
  `_ITEM_PRIORITY_RE`/`_ITEM_WORK_KIND_RE`/`_META_FROM_BACKLOG_RE` on 0, and `_PLAN_STATUS_RE` is
  already bounded at two of three sites and raw at the third, exactly as described.
- E-05's premise reproduces: 38 spec records through `_iter_spec_records`, 0 divergent, and both
  `runner_shared` sites are where the plan says (`_ce._ITEM_ID_RE.search(text)` in `discover_specs`, and
  `_ce._ITEM_ID_RE.search(p.read_text(...))` in the spec-dispatch branch), paired with a bounded
  `_sel.read_front_matter_status` on the same text.

TWO SERIOUS FINDINGS, both of which would have misdirected an executor rather than merely read poorly.

PR-Y01 is the one that could have caused harm. E-01's Expected outcome states that the bounded reader
answers the two live documents `takpys`/`reference`/`awmetastore` and `27rjro`/`reference`/`awmetastore`.
I built the bounded reader and drove it: the third field is `None`, not `awmetastore`. The reason is
structural and the plan states it ELSEWHERE without connecting it: both documents declare `set:` in a
YAML fence, and `status_set.read_artifact_record` has no YAML `set:` fallback, a gap the plan's own
Deferred section names and deliberately refuses to fill because adding one would be a widening. So the
authored expectation is unreachable by the change the plan describes. The failure mode this creates is
specific and bad: an executor comparing against it either reports a defect that is not one, or, worse,
adds the forbidden YAML `set:` fallback to make the number come out, widening a mutating verb's selector
surface under cover of a bounding change. E-03 carried the same error into its fixture (asserting all
three fields recover), so a correct implementation would have failed the plan's own test. The invariant
is DECLARED-OR-NOTHING, never DECLARED-EXACTLY, and E-01, E-03, V-01, V-02 and the gate now say so.

PR-Y02 is a misidentified evidence file whose accompanying argument is also wrong. F-05 and E-02 name
`.aw/records/reviews/20260925-4sd62s-01-...review.md` as the one record where the unbounded YAML fallback
diverges. Driven at review, that file diverges on NEITHER pattern: unbounded and bounded both answer
`None`/`None`. The actual divergent file is its SPEC twin under `.aw/records/specs/reviewed/`, whose body
carries `id: abc123` and `status: approved` as literal example lines. Both files exist, which is how the
confusion arose. It matters beyond the filename because the row's safety argument is that "the whole
record has no metadata region to speak of" and "both readers answer `None` for it at HEAD" - true of the
review file, false of the spec, which has a real metadata region declaring `- Id: 4sd62s` and
`- Status: reviewed` and therefore answers `4sd62s`/`reviewed` today from its BULLETS. The correct reason
the spec is safe is that its bullet reads HIT so the fallbacks are never reached, which is a weaker
guarantee than emptiness: a future reformat removing that bullet would expose it.

THREE SMALLER FINDINGS.

PR-Y03: every call-site and divergence count in the plan has drifted at least once in the days between
authoring and review. `_ITEM_ID_RE.search(` sites 15 -> 16, with the argument split 12/3 -> 13/2/1;
`_PLAN_STATUS_RE` divergence 6 -> 7 (`README.md` joined); records swept 2381 -> 2675; inventory
1904 -> 2056. `_META_BLOCKS_RELEASE_RE` has EIGHT call sites, a figure the plan never states while E-04
requires all of them bounded. The gate already forbids asserting against these numbers, which is good
discipline, but E-04's and E-05's Expected outcomes still quoted some, so the instruction and the
expectation contradicted each other.

PR-Y04: F-12 compares `_ID_LINE_RE` to `_ITEM_ID_RE` and reports 0 divergence, which is correct and
which I confirmed. But that framing obscures that `_ID_LINE_RE` is ITSELF unbounded-divergent on the
same two documents when read raw (`uyeko5` raw, `None` bounded). It is safe wherever it is read through
`_read_declared_id` and unsafe anywhere it is read raw, so E-04's sweep must cover it too; the plan never
asked. A reader of F-12 alone would conclude it needs no attention.

PR-Y05: V-01 demanded the wrong third field, following E-01. Fixed with the rest of PR-Y01, plus a
positive requirement to show `selectors._read_setid` still answering `awmetastore`, which is what proves
nothing downstream is left without the value.

NOTHING ELSE WAS FOUND WRONG, AND SEVERAL THINGS ARE BETTER THAN THE RUBRIC REQUIRES. The scope fence is
exemplary: the mint reader is excluded with its reasoning written at the site it will be read (E-06), the
pattern-versus-bound split is held throughout, and the two quoting documents are explicitly protected
from being "fixed". The five `Carrier-Declined` rows each argue from measurement rather than convenience,
and the one `Carrier-Evidence` row resolves. E-05 is correctly labelled a no-op and forbidden from being
reported as a fix. E-07's honesty about `uyeko5`'s dependency edge resolving `ok` today (because the type
filter masks the pollution) is exactly the kind of claim most plans overstate, and it is stated as
"assert the pollution is gone, not that a previously-broken edge now resolves". F-09's note that the test
`selectors.py` cites as its pin no longer exists is a real catch that a lesser review would have missed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-Y01 | HIGH | IN-SCOPE | Rubric A (correctness), G (executability) | plan E-01 Expected outcome, E-03 fixture, V-01; driven bounded reader on both `awmetastore` documents; the plan's own Deferred row refusing a YAML `set:` fallback | E-01 states the bounded reader answers `.../awmetastore` for the setid on both live documents. Measured, it answers `None`: both declare `set:` in a YAML fence and this reader has no YAML `set:` fallback, which the plan elsewhere forbids adding. E-03 carried the error into its fixture, so a CORRECT implementation would have failed the plan's own test, and an executor chasing the number could have added the forbidden fallback, widening a mutating verb's selector surface under cover of a bounding change. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-01's outcome corrected to DECLARED-OR-NOTHING with the measured values and the reason; E-03 asserts `set_id is None` explicitly and offers a bullet-fence fixture as an addition rather than a replacement; V-01 requires the `None` and treats an `awmetastore` answer as proof the forbidden fallback was added; V-02 and the gate restate the prohibition. New OQ-03 records that this is a prose correction and not a change to what the plan does. |
| PR-Y02 | HIGH | IN-SCOPE | Step 1 evidence, Rubric A | plan F-05 and E-02; both `4sd62s` files driven at review | F-05/E-02 name the `4sd62s` REVIEW record as the one YAML-fallback divergence. It diverges on neither pattern (`None`/`None` both ways). The real file is its SPEC twin, whose body carries `id: abc123`/`status: approved`. The row's safety argument ("no metadata region to speak of", "both readers answer `None`") holds for the twin and NOT for the spec, which answers `4sd62s`/`reviewed` from its bullets, so the spec is safe for a weaker reason than the row gives. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-05 rewritten with both files driven, the correct path named, and the corrected safety reason (bullets HIT, so the fallback is unreached) stated. E-02 and its Expected outcome corrected; V-02 names the spec path and requires the corrected before/after. |
| PR-Y03 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria) | plan E-04/E-05 Expected outcomes against the gate's own prohibition; re-measurement at review | The gate forbids asserting against the plan's counts, but E-04's and E-05's Expected outcomes quote several, and they have drifted: `_ITEM_ID_RE` sites 15->16 with a 12/3->13/2/1 split, `_PLAN_STATUS_RE` divergence 6->7, records 2381->2675, inventory 1904->2056. `_META_BLOCKS_RELEASE_RE`'s eight call sites are never stated while E-04 requires all bounded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 records every drifted figure beside its authored value and separates the figures that HELD (safe as a sanity check). E-04 and E-05 now demand re-derivation with the sweep pasted and any difference named; the gate's prohibition now cites the measured drift rather than a hypothetical one. |
| PR-Y04 | MEDIUM | UNDER-SCOPE | Rubric D (anti-regression) | plan F-12; corpus sweep of `_ID_LINE_RE` unbounded vs bounded | F-12's pattern-to-pattern comparison (0 divergent, confirmed) obscures that `_ID_LINE_RE` is itself unbounded-divergent on the same two documents when read RAW. It is safe only where read through `_read_declared_id`. E-04 never asks the executor to confirm no raw read survives, so a reader of F-12 would conclude the pattern needs no attention. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-14 records the measurement and the distinction. E-04 requires confirming no raw `_ID_LINE_RE.search(` survives and adds it to the four-pattern sweep; V-04 requires the count for it; OQ-01's rationale notes it bears on the one-versus-two accessor choice. |
| PR-Y05 | LOW | IN-SCOPE | Rubric E (testing evidence) | plan V-01 | V-01 demanded the wrong third field, inheriting E-01's error, and asked for nothing proving the clean setid remains reachable elsewhere. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 corrected to `None`, with a positive requirement to paste `selectors._read_setid` answering `awmetastore` on both documents. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's expected `set_id` is unreachable. Correct the expectation, or add the YAML `set:` fallback so it becomes reachable? | CORRECT THE EXPECTATION to DECLARED-OR-NOTHING, and forbid the fallback explicitly in three places. | Adding the YAML `set:` fallback: rejected, and this is the important rejection. It would make the authored number true at the cost of WIDENING a mutating verb's selector surface inside a plan whose whole thesis is that this reader resolves too much. The plan's own Deferred row already rules it out, citing `xo3244` as precedent for a widening needing its own plan and a maintainer's acceptance. | Driven bounded reader on both documents (`set_id` `None`); `selectors._read_setid` answering `awmetastore`, so the value stays reachable; the plan's Deferred row and its `xo3244` precedent; F-08's token sweep showing no other setid resolution changes. | yes |
| D-2 | F-05 names a file that does not diverge. Repoint the row, or drop it? | REPOINT to the spec twin AND correct the safety argument, which was specific to the named file. | Dropping the row: rejected, the divergence is real and E-02 depends on it being real; a bounding item with no measured divergence would look precautionary and invite an executor to skip it. Repointing the path alone: rejected, because the row's reasoning ("no metadata region to speak of") is what makes it convincing and that clause is false of the spec, so a path-only fix would leave a true-looking claim resting on a wrong premise. | Both files driven at review: review twin `None`/`None` both ways; spec `abc123`/`approved` raw versus `None`/`None` bounded, with `read_artifact_record` answering `4sd62s`/`reviewed` from its bullets. | yes |
| D-3 | Does the corrected `set_id` outcome need maintainer acceptance before execution, like OQ-02's backticked tokens? | NO. Recorded as OQ-03, resolved, with the reasoning. | Raising it as `Blocking: yes`: rejected, nothing regresses. The reader answers a WRONG setid for these records today (`runflags`, quoted from another record), so `None` is strictly better than wrong, the clean value is already served by `selectors._read_setid`, and F-08 confirms no other setid resolution moves. Leaving it unrecorded: rejected, because an expected value moved between the plan's before and after text and a reviewer should see that it did and why. | The plan's Deferred row; `selectors._read_setid` driven; F-08's 4-token sweep; the precedent of OQ-02 existing for a smaller user-visible resolution change. | yes |
| D-4 | `_ID_LINE_RE` is unbounded-divergent when read raw. Expand E-04's scope to cover it, or file it separately? | EXPAND E-04, which already adds the accessor the fix needs. | Filing a separate item: rejected as fragmenting one bounding pass across two plans for one extra `grep`, when the accessor E-04 introduces is the remedy and the module is one of the most contended files in the repository, so a second visit costs another merge. Leaving it: rejected, F-12 as written actively misleads a reader into thinking the pattern is safe. | Corpus sweep: `_ID_LINE_RE` unbounded-vs-bounded divergent on the two `awmetastore` documents, identical to `_ITEM_ID_RE`; `76w6mq` bounded it at the accessor, not at the pattern, so raw reads were never covered. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 and OQ-02 remain `open` and `Blocking: no`
(an executor implementation choice and a maintainer acceptance respectively), neither of which makes the
plan `NO-GO` under the 2026-09-10 ruling; OQ-03 is `resolved`.
