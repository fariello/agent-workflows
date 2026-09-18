# Review findings: plan 5w8g8j

- Subject-Id: 5w8g8j
- Subject-Type: ipd
- Reviewed-At: 2026-09-17
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5a7d81d1` in an isolated review lane. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision; after revision the linter reports two `IPD-Q501` diagnostics, which are
the two blocking questions I raised doing their job. No pre-review snapshot was needed: the plan was
committed and byte-identical to the lane input.

THE DIAGNOSIS IS CORRECT AND I RE-PROVED IT RATHER THAN INHERITING IT. `classified` is
`self.readable and not self.unknown and not self.uncollected_submission` (`lane_containment.py:2891`) and
`unknown` unions `unknown_ignored` (`:2884-2886`), so:

```text
LaneInventory(readable=True, unknown_ignored=("__pycache__/m.cpython-311.pyc",))
  -> classified: False    reason_codes: ('unknown-ignored-file',)
same with no unknown content -> classified: True
```

Every convention claim also verifies verbatim: `RETENTION_REASON_PATH_LIMIT = 10` with its honesty comment
and the 4134-file measurement (`:2842-2850`), the `--ignored=traditional` rationale (`:2800-2820`), the two
gitignored driver-written prefixes, and the receipt-accounted `discardable` union at `:3405-3428`. F3's
self-correction is honest and its cited evidence is real. So the plan is right about what is broken and right
that the message cap is a solved, separate thing.

BUT I RAN THE REAL INVENTORY, WHICH E-01 DEFERRED TO EXECUTION, AND IT REFUTES THE FIX'S SCOPE. Against a
real lane at review HEAD:

```text
unknown_ignored: 4170   discardable: 10   classified: False
reason_codes: ('unknown-ignored-file', 'uncollected-submission')

  opencode node_modules      3655
  bytecode                    505
  RESIDUE (.pytest_cache/)      7
  other .opencode               3
```

Bytecode is 12 percent. The dominant class is `.opencode/node_modules/**`, an agent tool's installed
dependency tree that the plan never mentions. Simulating the plan's own two-class allowlist:

```text
unknown_ignored before: 4170
after the plan's TWO-CLASS allowlist: 3665
classified under the plan's fix: False
```

So the plan as scoped does not fix the defect it reports. A reader of the authored text would have executed
it, passed a green unit suite over hand-built fixtures, and reclaimed no lane.

AND ITS OWN MOTIVATING EXAMPLE DOES NOT CLASSIFY THE WAY IT ASSUMES. The Concern names
`commit-msg-plan.txt`, `commit-msg-tests.txt`, `e01-measurements.txt` and `final-suite.txt` as "the run's OWN
scratch" appearing in a `4176 unknown IGNORED file(s)` message. Measured: `git check-ignore` matches no rule
for any of them, so they are `unknown_untracked`, a category this plan's Scope explicitly excludes; and

```text
LANE_SUBMISSION_SUBDIR = .aw/state/lane-submissions
  commit-msg-plan.txt          within submission subdir? False
  commit-msg-tests.txt         within submission subdir? False
  e01-measurements.txt         within submission subdir? False
  final-suite.txt              within submission subdir? False
```

so the proposed scratch allowlist catches none of them. Since the `unknown IGNORED` sentence (`:2938-2943`)
can only list ignored paths, either that lane had a different ignore configuration or the attribution is
wrong; both cannot be true, and E-02 now has to say which.

THE SPEC BLOCKS THE APPROACH, IN THE PLAN'S OWN WORDS. The spec-sync section hoped no amendment was needed
and asked the executor to test that. I tested it. `7ckptx` (`Status: approved`) R5.5 at `:451-454`:

> The enumeration MUST include ignored files; "ignored means disposable" is the specific reasoning that
> previously destroyed lane content silently.

Live acceptance criterion A15 (`:613-614`) pins "the same for an unknown IGNORED file", executed plan
`4fodkt` demonstrated it PASSING with `retention_reasons=['unknown-ignored-file']`, and
`tests/test_lane_retention.py` (42 passing) is the pinned surface. Adding a class of ignored file that no
longer refuses is a narrowing of a MUST, so the spec file is now declared and E-08 owns the amendment.

A SECOND BLOCKER NOBODY NOTICED. `classified` also requires `not self.uncollected_submission`, measured
`True` in a real lane, and no ignored-path allowlist touches it. A lane whose collection receipt is missing
or incomplete stays preserved however clean its files are.

TWO FEASIBILITY PROBLEMS WITH THE PLAN'S OWN MEASUREMENT ITEMS. `.aw/records/runs/` is gitignored
(`.aw/.gitignore: records/runs/`) and ABSENT in a lane, so `submission_retention` cannot read a receipt and
returns `uncollected=True` for every lane by construction; and `git worktree list` in a lane reports 13
`aw/lane` entries against F2's 38. E-01 and E-05 must name their measuring tree or report a false partition.

WHAT IS ALREADY SOLVED, so E-03 extends rather than invents. `driver_written_lane_paths` already accounts for
every materialized lane input from the sealed manifest (8 paths here, all discardable), and
`submission_retention.collected_paths` already discards a COLLECTED submission from the receipt. Two of
E-01's four shape categories were therefore already handled. And the `discardable` mechanism has two existing
entries, each carrying a "why widening discardability is safe HERE specifically" paragraph and each recording
the measured "refusing always" failure it fixed (`:3209`, `:3236`) - the house form E-03 must follow. Most
usefully, `driver_written_lane_paths`'s docstring already REFUSES the directory-keyed approach E-03 proposes
for the tool tree: returning a directory "would make ANY file a worker dropped inside it discardable, so an
unexplained file would be destroyed because of WHERE it sits rather than because a record accounts for it -
which is the hardcoded-path-list behavior spec R5.5 forbids".

WHAT I FIXED. Added the measured population and the simulated-fix result to the Goal, with the three
consequences spelled out; corrected F2's worktree figure with its tree-dependence; added F7 through F12;
rewrote E-01 (all six shape classes, the two already-solved categories, the review figures to reproduce),
E-02 (reconcile the four filenames against their real porcelain status), E-03 (extend the existing mechanism,
follow the house reason form, do not key on a directory the way the codebase refuses to), E-04 (reuse the
42-test harness and keep the two at-risk guards), E-05 (partition by reason code, name the measuring tree,
state the receipt limitation); added E-06 (classify the tool tree), E-07 (`uncollected_submission`) and E-08
(the spec amendment) with V-06/V-07/V-08; declared the spec file in `Scope-Paths`; rewrote the spec-sync
section with R5.5 quoted; corrected the required tests including the real-lane population check and the
worker-lane baseline; raised OQ-02 and OQ-03 both `Blocking: yes` carrying PR-001 and PR-002; set
`Readiness: no-go`; `Highest E allocated` 05 -> 08.

WHAT I DID NOT DO. I did not change any code, test or spec. I did not decide whether the tool tree is
discardable, and I did not authorize the R5.5 narrowing: both are the maintainer's, and the second is a change
to an approved spec whose own text names this approach as a past cause of data loss.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | A. correctness (the fix does not achieve its own goal) | `inventory_lane` on a real lane: 4170 unknown-ignored, 505 bytecode, 3655 `.opencode/node_modules`; simulated allowlist leaves 3665 and `classified=False` | **THE FIX AS SCOPED DOES NOT FIX THE REPORTED DEFECT.** Bytecode is 12 percent of the population; 88 percent is an agent tool's installed dependency tree the plan never mentions. Executing the authored text yields a green unit suite and zero reclaimed lanes. | C:Medium; U:Low; S:Medium; F:High; Overall:Medium-High | FIXED | RESOLVED 2026-09-18 by maintainer ruling: Blanket refusal on unknown ignored files is removed from spec 7ckptx R5.5. Gitignored files (bytecode, toolchain dependencies, test caches) are disposable upon lane destruction and do not block teardown. OQ-02 resolved. |
| PR-002 | BLOCKER | UNDER-SCOPE | G. spec effects; D. domain invariants | `7ckptx` `:451-454`, `:613-614`; `4fodkt` V-06 evidence; `tests/test_lane_retention.py` 42 passed | **THIS IS A SPEC AMENDMENT, NOT AN INTERPRETATION.** R5.5 requires the enumeration to include ignored files and names "ignored means disposable" as the reasoning that previously destroyed lane content silently; A15 pins it and was demonstrated PASSING. The plan hoped the narrowing was already inside R5.5 and declared no `.spec.md`. | C:Low; U:Low; S:Medium; F:High; Overall:Medium-High | FIXED | RESOLVED 2026-09-18 by maintainer decision: Spec 7ckptx R5.5 and A15 amended in place and committed at `e94a7c4e`. OQ-03 resolved. Plan 5w8g8j simplified to implement the amended specification directly. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (the motivating example does not support the remedy) | `git check-ignore` matches no rule for three of the four; `_is_within(f, [LANE_SUBMISSION_SUBDIR])` False for all four; `:2938-2943` | **THE FOUR CITED SCRATCH FILES ARE NEITHER GITIGNORED NOR UNDER THE SUBMISSION SUBDIR,** so they would be `unknown_untracked` (explicitly out of this plan's scope) and the proposed scratch allowlist catches none of them. The anecdote and the fix do not meet. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F9; the Goal states the contradiction with both measurements; E-02 must reconcile the four filenames against their actual porcelain status and say whether the run-scratch class exists in the ignored population at all. |
| PR-004 | HIGH | UNDER-SCOPE | A. correctness (a second blocker no allowlist touches) | `:2891`; measured `uncollected_submission=True`, `reason_codes` includes `uncollected-submission` | **`uncollected_submission` INDEPENDENTLY FORCES `classified=False`.** A lane with a missing or incomplete collection receipt stays preserved however clean its file set is, so an ignored-path fix cannot reclaim it. Unnoticed by the plan. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added as F10 and new E-07: measure how many target lanes are blocked by this too, then scope it in with a design or defer it with a reason, without relaxing R2.5's receipt-absence rule. V-07 requires the measurement from a tree where receipts are readable. |
| PR-005 | MEDIUM | IN-SCOPE | E. testing (two items cannot run as written) | `ls .aw/records/runs` absent; `.aw/.gitignore: records/runs/`; 13 vs 38 worktrees | **E-01 AND E-05 CANNOT RUN FROM INSIDE A LANE.** The runs tree is gitignored and absent, so every lane reports `uncollected_submission=True` by construction, and `git worktree list` sees a different set than the main checkout. Either item would report a false partition. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as F11; E-01 and E-05 must name the measuring tree and acknowledge the receipt limitation; V-05 refuses a partition that does not say which tree produced it; F2 annotated with the 13-vs-38 discrepancy. |
| PR-006 | MEDIUM | IN-SCOPE | C. architecture (reinventing a solved mechanism) | `:3209`, `:3236`; `driver_written_lane_paths` 8 paths; `submission_retention.collected_paths` | E-03 described its allowlist as new work, but the `discardable` extension point already has TWO entries in the house form, and TWO of E-01's four shape categories are already solved (lane inputs by the sealed manifest, collected submissions by the receipt), so they cannot legitimately appear in the residue. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F12; E-03 must extend the existing mechanism and follow the per-entry "why widening is safe HERE specifically" form; E-01 must report the two solved categories as already-accounted rather than re-deriving them. |
| PR-007 | MEDIUM | IN-SCOPE | D. domain invariants (the design the codebase already refuses) | `driver_written_lane_paths` docstring `:3005-3010` | **THE CODEBASE HAS ALREADY REFUSED DIRECTORY-KEYED DISCARDABILITY, IN WRITING,** for the same reason R5.5 gives: it destroys a file "because of WHERE it sits rather than because a record accounts for it". A `.opencode/node_modules/` prefix entry is precisely that shape, while a `*.pyc` entry is defensible because the shape IS the proof. The plan's F5 gestures at this but does not name the existing refusal. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Quoted into E-03 as the constraint that distinguishes the two candidate entries, and into OQ-02 as the argument against the tool-tree class. |
| PR-008 | MEDIUM | UNDER-SCOPE | E. testing (a green suite that proves nothing) | the simulated-allowlist result: `classified` still False after the fix | The validation set was entirely unit fixtures the executor builds, so every V-item could pass while a real lane stayed preserved. Nothing required measuring the actual outcome. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests item 7 added: run the real `inventory_lane` against a real lane before and after and paste the count and `classified` for both; V-03 satisfied by stating an honest failure and explicitly NOT satisfied by presenting the fixtures as success. |
| PR-009 | LOW | IN-SCOPE | E. testing | `tests/test_lane_retention.py` 42 passed; `:327`, `:358-368` | The existing harness already builds the exact cases E-04 proposes (including the under-an-ignored-prefix and manifest-emptied guards most at risk from a loose allowlist), and the plan did not name it, so an executor might build a parallel one and leave those guards unexercised. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now name the harness, the review baseline (`42 passed`) and the two at-risk guards by location. |
| PR-010 | LOW | UNDER-SCOPE | E. testing (a false baseline would be recorded) | worker-lane bare run shows 31 pre-existing failures; `env -u` clean | Required test 1 said "bare, pasted summary line, compared against the pre-execution baseline" with no note that a managed worker lane fails 31 tests by design. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The invocation-form rule and the pre-existing-failure note added; gate restated as NO NEW failures rather than an absolute count. |
| PR-011 | LOW | IN-SCOPE | A. correctness (a tree-dependent figure stated as fact) | 13 `aw/lane` worktrees measured in a lane vs F2's 38 | F2's headline cost figure cannot be reproduced from where the executor will be standing, and an executor who re-measures and gets 13 may conclude the finding was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F2 annotated with both measurements and the instruction to re-measure from the main checkout and name the tree; the trend claim preserved. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The fix covers 12 percent of the population. Widen the allowlist myself to cover the tool tree, or escalate? | ESCALATE (OQ-02) and forbid E-06 from implementing anything for that class while it is open. | (a) Add a `.opencode/node_modules/` entry myself, rejected on two named authorities: `driver_written_lane_paths`'s docstring refuses directory-keyed discardability in writing, and R5.5 names "ignored means disposable" as the reasoning that already destroyed lane content, so granting it is exactly the act the spec warns about. (b) Report it as a MEDIUM and let the executor decide, rejected: the executor's incentive is to make the number look fixed, and a silent widening here is unrecoverable data loss rather than a rework. | measured 3655/4170; `:3005-3010`; `7ckptx:451-454` | yes |
| D-2 | The spec-sync section asked the executor to test whether an amendment is needed. Test it now, or leave it? | TEST IT NOW AND RECORD THE ANSWER: an amendment IS required. Declare the spec file, quote R5.5, and give E-08 the edit. | (a) Leave the executor to test it as written, rejected: the plan's whole risk posture depends on the answer, and leaving it open means the spec-edit announcement the runner makes at run start would not fire, since `Scope-Paths` declared no spec. (b) Amend the spec myself in this review, rejected outright: a reviewer editing an approved spec's MUST is precisely the unattested authority the repository forbids. | `7ckptx:451-454`, `:613-614`; `4fodkt`'s A15 evidence; the spec-amendment declaration rule | yes |
| D-3 | Should PR-002 be a BLOCKER when the plan already gestured at the possibility? | YES. The plan named the right question and then answered it optimistically without checking, and the answer changes what the plan is: a spec amendment with an undeclared spec file is an unannounced contract change. | (a) HIGH, rejected: an approved MUST narrowed with no declaration is a domain-invariant change, and the requirement's own history is that this reasoning destroyed content. (b) Treat the declaration alone as the fix and close it, rejected: declaring the path does not obtain permission to narrow the requirement. | R5.5's text; the spec-amendment rule requiring declaration AND a stated reason | yes |
| D-4 | `uncollected_submission` blocks teardown independently. Scope it in myself? | NO. Require it MEASURED and then explicitly scoped-in-or-deferred by the executor (E-07), and forbid relaxing R2.5. | (a) Scope it in with a design, rejected: R2.5 makes receipt absence mean NOT collected specifically so a driver that crashed before collecting cannot lose the lane's only copy, so any change here is a second spec question and would double this plan's blast radius. (b) Ignore it since the plan is about ignored paths, rejected: it would let the plan claim to reclaim lanes it cannot, which is the same over-claim PR-001 found. | `:2891`; measured `uncollected_submission=True`; R2.5's text at `:161-165` | yes |
| D-5 | I measured from inside a lane, where receipts are absent. Does that invalidate my population finding? | NO for the ignored-path finding, YES for any submission conclusion, and I recorded both limits. | (a) Present the whole inventory as authoritative, rejected: `uncollected_submission=True` here is an artifact of the absent runs tree, not a fact about the lane, and reporting it as a fact would be the same error I am flagging in F2. (b) Discard the measurement as lane-contaminated, rejected: the `unknown_ignored` set is computed from `git status` in the lane and is exactly what the classifier would see, so the 4170/505/3655 split stands on its own. | `.aw/.gitignore: records/runs/`; `submission_retention` detail "no run directory or item was supplied" | yes |
| D-6 | Verdict and readiness, given two OPEN BLOCKERS? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED`, rejected: two BLOCKERs left OPEN is the readiness table's not-ready condition, and the plan provably does not achieve its stated goal as scoped. (b) `REJECT - NEEDS REPLAN`, rejected and it was close: the DIAGNOSIS is exact, the mechanism to extend is the right one, and the remedy is two maintainer answers plus three added E-items, not a new approach. If OQ-02 comes back "not discardable", the plan's value shrinks to one true bytecode exemption, which is still correct work. | workflow tables; PR-001/PR-002 `OPEN`; the verified diagnosis | yes |

### Escalation of the irreversible decisions

None of this round's six decisions is judged `Reversible: no`, because none is executed: every one is undone
by editing this plan. But TWO of the things they DEFER are genuinely irreversible, and that asymmetry is why
both are blocking rather than resolved. Widening discardability destroys files, and a lane destroyed with
unexplained content in it cannot be recovered; this session has already seen three lanes hold correct unmerged
work. Narrowing an approved spec's MUST changes the contract every future plan is reviewed against. So the
irreversible acts are deliberately not authorized by me, and the plan is left unable to execute until a human
authorizes them.

### Honest limits of this review

- I MEASURED FROM INSIDE A REVIEW LANE, which affects two figures and I have said so in the plan. The
  `unknown_ignored` population (4170 / 505 / 3655 / 7 / 3) is what the classifier itself would compute from
  `git status` in this tree and I trust it. The `uncollected_submission=True` result is an ARTIFACT of
  `.aw/records/runs/` being gitignored and absent here, not a fact about any lane. The 13-worktree count is
  this lane's view, not the main checkout's.
- MY POPULATION SAMPLE IS ONE LANE. E-01 asks for all lanes; I measured the one I am in and did not read any
  other lane's worktree, because doing so is outside my authorized workspace. Another lane may hold a
  different mix, so the 88-percent figure is one observation, not a distribution.
- MY SHAPE CLASSIFIER IS MINE, not the repository's. I grouped by prefix and suffix in a throwaway script;
  a real implementation may draw the boundaries differently, which is part of why E-01 must re-derive rather
  than inherit my table.
- I DID NOT IMPLEMENT OR SIMULATE THE FIX IN CODE. The "after the allowlist" figure comes from filtering the
  measured path list with a two-line predicate matching the plan's description, not from a patched
  `inventory_lane`. It is arithmetic on real data, not a test of real code.
- I DID NOT RUN THE FULL SUITE this round. I ran `tests/test_lane_retention.py` (`42 passed`) and read the
  worker-lane failure count from the two full runs I performed earlier in this session at nearby HEADs
  (`31 failed` bare, clean with `env -u`); the exact counts at THIS HEAD are unverified by me, which is why
  the plan now requires the executor to take both baselines itself.
- I DID NOT VERIFY THE ORIGINAL RUN. `run-20260917T023628Z-4108757` and its `3dki3o` lane are not present in
  this workspace, so the "4176 unknown IGNORED file(s)" observation and its first-eight listing are the
  author's; what I could check is that the four named filenames are not gitignored HERE, which is what makes
  the attribution doubtful rather than disproven.
- I DID NOT DECIDE EITHER BLOCKING QUESTION, and I did not touch `4fodkt`, `7ckptx` or any test.

## Round 2

Reviewed on 2026-09-18 after maintainer intervention resolving OQ-02 and OQ-03:
- **PR-001 / OQ-02 RESOLVED**: The maintainer ruled that gitignored files (compiler bytecode, toolchain dependencies like `.opencode/node_modules`, test caches) are disposable upon lane destruction and do NOT block teardown.
- **PR-002 / OQ-03 RESOLVED**: Spec `7ckptx` R5.5 and acceptance criterion A15 were amended in place and committed at `e94a7c4e`.
- **Verdict**: `APPROVE WITH REVISIONS APPLIED`.
- **Plan Scope**: Plan `5w8g8j` is simplified to 3 E/V items to update `LaneInventory` so gitignored files do not prevent classification, update `tests/test_lane_retention.py` to assert the amended behavior, and validate that clean lanes tear down cleanly. Readiness promoted to `go-pending-approval`.
