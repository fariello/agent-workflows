# Review findings: plan 7eqw67

- Subject-Id: 7eqw67
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (HIGH, fixed), PR-402 (MEDIUM, fixed), PR-403 (MEDIUM, fixed), PR-404 (LOW, fixed), PR-405 (LOW, fixed), PR-406 (LOW, fixed)

## Round 1

Reviewed at HEAD `9929535a` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision.

THE PLAN'S CENTRAL INSIGHT IS CORRECT AND I REPRODUCED ALL EIGHT OF ITS LOAD-BEARING FACTS. I ran the
commands rather than reading the numbers. Refs and objects disagree by nearly two orders of magnitude
(20 lane refs against 632 dangling commits). The specific evidence the originating review retired is STILL
recoverable: `0abc01d9` resolves, `git merge-base --is-ancestor 0abc01d9 main` returns rc 1,
`git branch -a --contains` lists zero branches, and its subject is exactly "lifecycle(8u6770): finalize
8u6770 -> executed". F-04's over-match case is real and I found the same offender, `e18ceea4`, whose
subject is a WIP snapshot on lane `x75obw` that merely mentions `8u6770`. F-05 is the most valuable
finding in the plan and it verifies completely: `lost-found` already holds 1749 files in the shared git
dir, `git for-each-ref | grep -c lost-found` is 0 so those files do not even protect the objects they
name, and `--connectivity-only` returns a SORTED-EQUAL 632-sha set (`diff -q` reports no difference).
F-03's reason string is verbatim as quoted. F-08 verifies: `fsck`, `lost-found` and `dangling` each have
zero occurrences in `agent_workflows/`. E-06's self-correction is right, and I confirmed the long-form
twin carries the costlier-error rule verbatim.

So the direction, the data-safety refusal, the plural-return reasoning and the scope exclusions are all
sound. What review found is one item that could not be satisfied as written, one stale premise the plan
contradicts in its own findings, and four numbers that moved.

THE ONE THAT WOULD HAVE BLOCKED EXECUTION (PR-401). V-05 requires "pasted output of the existing test
that enforces the module's stdlib-only property, showing it passes", and the Required-tests section says
the same. THERE IS NO SUCH TEST. `worktree_lease`'s own `inspect_lane` docstring claims the property is
"pinned by `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`"; that file
does not exist under `tests/`, `grep -rn stays_stdlib_only tests/` returns nothing, and
`git log --diff-filter=D` shows it deleted in commit `19313eed` ("test: trim test suite from 9,136 to
under 2,000 tests"). An executor following V-05 literally would either stall or fabricate a pass, and the
plan leans on this property elsewhere (its conventions note explains that `worktree_lease` is pinned
stdlib-only, which is why E-03's helper lives in `runner_shared` and E-05 is prose-only). I rewrote V-05
to demonstrate the property DIRECTLY, by showing the module's first-party import list empty before and
after, which is what the deleted test asserted anyway and costs one grep. The stale citation is itself a
real defect of a class this repository already tracks four instances of (`089bq4`, `2jz47s`, `gzmr54`,
`p5qx91`), so I FILED the carrier (`rdl9lh`) rather than folding an unrelated decision into this plan: the
fix needs a choice between restoring a behavioral guard and correcting the docstring, and the obvious
restoration form (parsing the source) is forbidden by the no-code-pinning rule.

THE STALE PREMISE (PR-402). The plan's `- Scope:` field says the long-form workflow twin "has ALREADY
DRIFTED by lacking the 'costlier error' rule entirely", while E-06 says authoring measured the opposite
and explicitly withdraws that claim. Both cannot be true, and the field is the wrong one: the twin carries
the rule verbatim, `88manw` precedent included, inside the same numbered 1-6 list. E-06's instruction to
diff the two at execution is exactly right and is kept; the field is corrected so an executor does not go
hunting for a divergence that is not there.

THE NUMBERS (PR-403), and they matter less than they look. Every structural fact held; five integers moved,
all in the direction that STRENGTHENS the plan. Lane refs 12 to 20. Dangling commits 622 to 632. The fsck
speed gap 14x to 27x (3.03s versus 83.09s). The batched-subject gap 3x to 152x (0.14s versus 21.18s, which
is a far bigger win than the 3x authoring measured). The `merge-tree` conflict count 53 to 60. The plan
already insists its numbers are dated and re-measurable, which is why this is MEDIUM rather than HIGH, but
two places transcribed a ratio into an instruction ("14x faster", "measured 1.04s versus 3.21s") where a
later reader could treat it as a constant. Both now carry both measurements and say to cite the
execution-time figure.

THREE SMALLER ONES. F-09 prices the CLI route at "all six scenarios from `conformance_matrix.required_scenarios`";
measured, that function takes a DECLARATION and returns six only for the rarest class, adding `json` for a
read/check/bare leaf and `domain_failure` when exit 1 is in its contract, with the live distribution
`{8: 88, 7: 62, 6: 12}`. A dangling-object search is a read, so it would owe eight. The finding's own
conclusion is therefore stronger than it claimed (PR-404). V-04 asks the executor to search for a consumer
parsing the `reason` text; I ran it, the answer is none (one hit, the emission itself; the only test on
that arm asserts `outcome.code`), and recording it as F-12 means the executor re-runs a known-clean check
rather than discovering the answer late (PR-405). And E-01 fact (f) assumes `lost-found` can be measured
from a clean baseline when it already holds 1749 files, so E-02 case 4 must compare before-and-after rather
than assert emptiness, with an explicit warning not to delete the directory to get a clean start (PR-406).

WHAT I DELIBERATELY DID NOT FLAG. The plan is long and its E-items carry heavy inline prose, which could
read as over-specification. It is not: this is a plan whose entire subject is a false inference drawn from
an under-specified check, and every one of those inline notes is a measured constraint that a plausible
simplification would violate (use `--lost-found`, return a single tip, match the body, add a CLI verb). The
`IPD-Z602` density advisory does not fire on any item. I also left both open questions resolved: OQ-01's
cap answer is an implementation detail nothing parses, and OQ-02's subject-only decision rests on a
precedent I verified in `worktree_lease`'s own comment, with F-04's measured over-match making the case
stronger here than in the precedent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | E (testing); G (executability) | plan V-05 ("pasted output of the existing test that enforces the module's stdlib-only property"); `worktree_lease.inspect_lane` docstring cites `tests/test_lane_allocation_idempotent.py::test_worktree_lease_stays_stdlib_only`; that file is absent, `grep -rn stays_stdlib_only tests/` returns nothing, `git log --diff-filter=D` shows it deleted in `19313eed` | V-05 and the Required-tests section demand a test that does not exist, making the item unsatisfiable as written; an executor would stall or fabricate a pass | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 and Required tests now demand a DIRECT demonstration (first-party import list empty before and after), which is what the deleted test asserted; added F-11; FILED carrier `rdl9lh` for the stale citation plus a Deferred row explaining why its fix needs its own decision |
| PR-402 | MEDIUM | IN-SCOPE | A (correctness of premise) | plan `- Scope:` ("which has ALREADY DRIFTED by lacking the 'costlier error' rule entirely") versus E-06 (authoring measured it present) versus review (present verbatim, `88manw` included, in the same 1-6 list) | The plan contradicts itself about the twin's state, and the `- Scope:` field carries the false half, sending an executor after a divergence that is not there | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope:` corrected to record the twin as measured CONSISTENT and to withdraw the earlier note, pointing at F-13; E-06's diff-at-execution instruction kept unchanged because it is correct |
| PR-403 | MEDIUM | IN-SCOPE | E (testing); live-measurement convention | authoring versus review at `9929535a`: refs 12/20, dangling 622/632, fsck gap 14x/27x (3.03s vs 83.09s), batched gap 3x/152x (0.14s vs 21.18s), merge-tree paths 53/60 | Five figures moved and two were transcribed into E-03 constraints as if constant ("14x faster", "1.04s versus 3.21s"), where a later reader could treat them as targets | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 with all re-measurements; E-01 now records that review took a second reading and expects a third; E-03's two constraints carry both figures and say to cite the execution-time measurement; the durable claims (order of magnitude, set equality, fact b) named explicitly |
| PR-404 | LOW | IN-SCOPE | C (architecture); evidence accuracy | plan F-09 ("all six scenarios ... `tty, non_tty, agent, no_color, help, usage_error`"); `required_scenarios(decl)` adds `json` for read/check/bare and `domain_failure` for exit-1 read/check; live distribution `{8: 88, 7: 62, 6: 12}` | The cost figure understates itself: a read leaf owes eight, and six is the rarest case | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 corrected with the real mechanism and the distribution, noting its conclusion is stronger than claimed |
| PR-405 | LOW | IN-SCOPE | D (invariants) | `grep -rn "nothing to integrate" agent_workflows/ tests/ tools/ --include=*.py` returns one hit (the emission); `tests/test_runner_shared.py` asserts `outcome.code == REINTEGRATE_LANE_ABSENT` | V-04 asks the executor to discover whether a consumer parses `reason`; the answer was cheaply knowable at review and its absence was the one risk that could turn a prose fix into a behavior change | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the measurement; V-04 now says to re-run rather than cite it, and to report a newly appeared consumer as a finding rather than widen scope |
| PR-406 | LOW | IN-SCOPE | E (testing) | `find "$(git rev-parse --git-common-dir)/lost-found" -type f \| wc -l` returns 1749 in this checkout | E-01 fact (f) and E-02 case 4 read as though `lost-found` starts empty; it does not, so "unchanged across the call" must be a before/after comparison | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the pre-existing count with an explicit instruction that case 4 compares before and after, and must NOT delete the directory to get a clean baseline (itself a write to the shared git dir) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should V-05 verify the stdlib-only property, given the test it cites does not exist? | Demonstrate it DIRECTLY: paste the module's first-party import list, empty before and after | Restore the deleted test inside this plan; drop the check entirely | Restoring needs a decision this plan has no authority to make (behavioral guard versus docstring correction) and the obvious restoration form parses source, which the no-code-pinning rule forbids; dropping loses a property the plan's own architecture depends on (it is why E-03's helper lives in `runner_shared` and E-05 is prose-only). A grep of the import list is exactly what the deleted test asserted and costs nothing | yes |
| D-2 | Was filing backlog `rdl9lh` from a review legitimate, rather than leaving the stale citation unrecorded? | Yes, filed | Fold the docstring fix into E-05; note it in prose with no carrier | A backlog item is a planning document, so filing one is within this workflow's mandate. Folding it in would smuggle an undeclared decision into a prose-only E-item whose whole constraint is "comment-only, no behavior change". Noting it without a carrier is the obligation loss `check.ipd-uncarried-obligation` exists to stop, and that rule also refuses a `Carrier:` value that is not a resolvable id6, so a promised carrier could not be cited; a filed record is durable, and the maintainer told outcome is that this review's final report names the item, its id6, its status and the decision its fix requires | no |
| D-3 | Which of the plan's two contradictory claims about the long-form twin is authoritative? | E-06's (the twin is consistent); the `- Scope:` field is corrected | Trust the `- Scope:` field; leave both and let the executor decide | Measured directly: `plan-review-long/01-discover-and-snapshot.md` carries the costlier-error sentence verbatim with its `88manw` precedent, inside the same numbered list. E-06 also already instructs checking rather than trusting, which is the correct standing instruction either way, so only the stale field needed changing | yes |
| D-4 | Should the moved numbers be updated in place, or reframed? | Reframed: record both measurements and name the durable claims | Update to review's figures; delete the figures | Updating moves the staleness (a third reading will differ again, as review's did from authoring's), and deleting loses the justification for the flag choice, which the plan rightly wants backed by a number. Recording both plus the durable claims (order of magnitude, set equality, fact b) is what makes a third figure read as expected rather than as a contradiction | yes |
| D-5 | Should review pre-answer V-04's consumer search, given the plan asks the executor to do it? | Yes, record it as F-12 but keep the re-run requirement | Leave it to execution; replace the requirement with the answer | It is the one check whose outcome could change this from a prose fix to a behavior change, so knowing it early de-risks the plan. But a consumer could appear between review and execution, so the requirement stays and the note says to re-run and to report a new consumer rather than widen scope | yes |
