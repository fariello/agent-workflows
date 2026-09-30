# Review findings: plan hyuos6

- Subject-Id: hyuos6
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-501 (HIGH, fixed), PR-502 (HIGH, fixed), PR-503 (MEDIUM, fixed), PR-504 (LOW, fixed)

## Round 1

Reviewed at HEAD `84cdeb94` in an isolated review lane. The plan file was already committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming`, exit 0, ZERO findings BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` with zero findings after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator
row check does not apply.

THIS PLAN IS UNUSUALLY WELL MEASURED AND I REPRODUCED ITS TWO BLOCKERS RATHER THAN TRUSTING THEM, because
they are the entire justification for its substantive half. BOTH REPRODUCE EXACTLY. F-05: re-unioning
`unknown_ignored` into `LaneInventory.unknown` (a full revert of the `5w8g8j` fix, the change that stranded
38 worktrees in production) leaves the bare suite at `3353 passed, 2 skipped, 3 warnings in 74.05s`,
identical to the unmutated baseline. F-06: dropping `unknown_untracked` from the same property, which makes
a merged lane holding an unaccounted untracked file eligible for force-teardown, also leaves
`3353 passed, 2 skipped`. Both reverted to an empty `git diff --stat`. So the retention rule genuinely has
no guard in either direction, including the data-loss direction, and the plan's decision to fix that here
rather than defer it (OQ-02) is correct. F-07's cause is exact: `19313eed` deleted
`tests/test_lane_retention.py` (1064 lines) and `tests/test_worktree_lease_merged_reclaim.py` (797 lines),
all three named deleted tests existed in `19313eed^`, no surviving test references `inventory_lane` or
`teardown_lane_if_classified`, and the only surviving `reclaim_lanes_on_interrupt` reference is the one
node id the plan names.

THE RECORD-CORRECTION HALF IS EQUALLY WELL EVIDENCED. F-01 reproduces: `65cuw0` E-04 really does end by
demanding a gitignored-only lane "be PRESERVED, with its reason code recorded" and V-03 really does demand
`unknown-ignored-file` pasted, while amended R5.5 reads "disposable upon lane destruction and do not block
teardown" and `RETENTION_UNKNOWN_IGNORED` documents itself "NEVER EMITTED BY `reason_codes` NOW,
deliberately". F-11's chronology is exact to the minute, including the ancestry test: round 2 at
`59d1d833` 2026-09-17 21:49:19, the amendment at `e94a7c4e` 2026-09-18 00:34:38, approval at `9ecb9f3f`
2026-09-18 00:45:43, with the amendment NOT an ancestor of the round-2 commit (rc=1) and IS an ancestor of
the approval commit (rc=0). F-12 reproduces: I staged a probe append and both
`python3 -m agent_workflows ipd-executed-gate` and `ipd-status-untooled-gate` exited 0 with `numstat`
reading `2 0`, then reverted cleanly. F-13 reproduces on temp copies: `is_plan_review_approved` True both
times, `newest_verdict` unchanged, `history_has_review_record` True both times, `_plan_status_events` 7
events with the same first event, and ONLY `extract_newest_history_entry` changed. V-02's structural claims
are exact: the existing `### Findings` table has 9 columns and `### Decisions` 6, the used id bands are
`PR-001..PR-107` and `D-1..D-5` so `PR-201+`/`D-6+` is genuinely fresh, and Round 2's D-4 says what the
plan quotes. OQ-01's refusal to amend R5.5 rests on a real recorded production measurement (the "100
percent of clean test runs" sentence is in the spec at R5.5's amendment note) and is the right call.

THE ONE SERIOUS FINDING IS A COLLISION THE PLAN COULD NOT HAVE SEEN, AND IT WOULD HAVE INVERTED E-03's
ASSERTIONS. That is PR-501. The plan cites `nvymif` three times as a LIVE backlog question and V-04
requires it "shown to resolve"; measured at review it is no longer `open` but `- Status: graduated` as of
2026-09-30, `- Graduated-To: nvymif`, carried by pending plan `z8ex9f`. The stale status alone is minor.
The serious half is behavioral: `z8ex9f` declares `agent_workflows/lane_containment.py` in
`- Scope-Paths:`, its E-02 narrows `submission_retention` so a provably-empty lane is no longer
`uncollected`, and its E-03 ADDS A NEW BLOCKING CONDITION to `LaneInventory` for work that has not landed
on the integration target, threading a branch into `inventory_lane` as a new optional parameter and
explicitly treating an ABSENT branch as BLOCKING ("When no branch is supplied the condition cannot be
evaluated; treat that as BLOCKING"). This plan's E-03 drives the gate with a handle exposing only `.path`,
and `inventory_lane` takes a lane ROOT, so there is no branch to thread: after `z8ex9f` lands every case in
the new module classifies `False` on the new condition, the `clean` and `ignored` cases flip from
`torn_down=True` to `False`, and the two refusal cases would pass for the wrong reason. Whichever plan
lands second breaks the other, and neither declares an `- Item-Dependencies:` edge or mentions the other. I
did NOT add an edge, for the reason this repository has recorded before: the grammar has no "prefer after"
edge, and `z8ex9f` is `to-review`, so an `executed:` edge would gate a low-priority followup behind an
unrelated medium-priority chore's full cycle. E-03 now re-measures at execution and branches, which works
in either order.

THE SECOND FINDING IS THAT THE MUTATION EVIDENCE V-03 DEMANDS CAN BE SATISFIED BY A MODULE THAT DETECTS
NEITHER MUTATION. That is PR-502, and I found it only by running the mutations through the real gate rather
than reading the plan's prose. Under mutation (a) the ignored case flips to `torn_down=False` but its
`reason_codes` stays `()`; under mutation (b) the untracked case flips to `torn_down=True` but its
`reason_codes` stays `('unknown-untracked-file',)`. So reason codes are INVARIANT across both mutations in
exactly the cases each mutation is supposed to break, and a module asserting on reason codes alone (which
is the natural reading of E-03's "PRESERVED with `('unknown-untracked-file',)`" phrasing and of V-03's
own evidence list, where reason codes lead) would go GREEN under both. The state that actually moves is
`torn_down`/`classified` and whether the worktree is gone. Given the plan's entire purpose is avoiding a
vacuous guard (its own gate calls that "THE THIRD THING MOST LIKELY TO GO WRONG"), leaving this implicit was
the highest-leverage gap in the plan. Both E-03 and V-03 now require the failing assertion to be on
`torn_down` or worktree existence and refuse a reason-code assertion as evidence.

PR-503 is a smaller executability defect in the same fixture: `collection_receipt_path` calls `item_slug`,
which reads `int(item['position'])`, so a receipt fixture keyed on `order` raises `KeyError: 'position'`
rather than failing a test. I hit this writing the probe. Since F-04 makes the receipt load-bearing for all
four cases, an executor hitting a `KeyError` mid-fixture is a real stall, and one sentence prevents it.

PR-504 updates the baseline. The plan states `3246 passed, 2 skipped` at HEAD `9733d47a` and correctly says
to re-derive rather than copy; at review HEAD `84cdeb94` the bare suite is `3353 passed, 2 skipped, 3
warnings in 108.82s`, 107 tests higher. I added the review measurement beside the authored one rather than
replacing it, because the plan's own framing ("It is there to be COMPARED against, not copied") is right and
the drift is evidence for that framing.

I ALSO CHECKED FOUR THINGS THE PLAN DOES NOT CLAIM, none of which produced a finding. First, whether the
`specfin7ck` overlap the plan discloses is real and benign: `uuh71v` is `- Status: reviewed`, its E-03 does
owe a demonstration of "a lane holding ONLY gitignored content being torn down", and its `- Scope-Paths:`
are the spec file and `walkthroughs` only, so it touches no code and the plan's "different in kind"
reasoning holds. Second, whether the structure-pinning tests the plan refuses to restore really were in the
deleted files: all three are present in `19313eed^` (`TheNoDirectForceTeardownTests` three times), so the
no-code-pinning exclusion is grounded rather than precautionary. Third, whether `dwfmxz` is a genuine live
carrier rather than a formality: it is `open`, `- Work-Kind: chore`, and its body independently measures the
same deletion, so E-04's deferral is honest. Fourth, F-10's claim that `aw ipd` has no `note` verb:
confirmed, the subcommand list is `{lint,scaffold,sync,recheck-readiness,execute-set,board,set,dependencies,begin,finalize}`.

ONE JUDGEMENT THE PLAN INVITES SCRUTINY ON AND I AGREE WITH. Its gate says F-06 "is the kind of finding that
could justify" a `Blocks-Release` gate and declines to claim one, on the ground that no user-perceptible
defect exists today because the behavior is correct and only its guard is missing. That is the right reading
of the repository's `bug` test, which turns on user-perceptible impact rather than latent risk, and the plan
states the judgement openly with its measurements rather than burying it. I record my agreement rather than
silently passing over it, since the plan explicitly asks a reviewer to disagree if they see it differently.

Bare suite at review HEAD: `3353 passed, 2 skipped, 3 warnings in 108.82s`. Working tree clean after every
probe and mutation (`git status --short` empty; `git diff --stat agent_workflows/lane_containment.py` empty).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | Rubric A (concurrency/ordering), D (anti-regression), G (dependencies) | `.aw/records/backlog/graduated/20260922-nvymif-01-nvymif-r55-gate-refuses-every-interrupted-lane.backlog.md` (`- Status: graduated`, `- Graduated-To: nvymif`, 2026-09-30); `.aw/records/plans/pending/20260930-nvymif-01-z8ex9f-...ipd.md` `- Scope-Paths:` naming `agent_workflows/lane_containment.py`, its E-03 "treat that as BLOCKING"; `lane_containment.inventory_lane` takes `lane_root`, not a handle | `nvymif` graduated AFTER authoring to pending plan `z8ex9f`, which narrows `submission_retention` and adds a landing condition to `LaneInventory` whose ABSENT-BRANCH case blocks. E-03's fixture supplies no branch, so once `z8ex9f` lands every case classifies `False` on the new condition: the `clean` and `ignored` cases INVERT and the two refusal cases pass for the wrong reason. Whichever plan lands second breaks the other; neither declares an edge or mentions the other. The plan also still calls `nvymif` a live open question in three places. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. E-03 now re-measures at execution (does `LaneInventory` carry a landing code, does `inventory_lane` take a branch?) and branches: if `z8ex9f` has landed, thread the merged lanes' branch; assert the same four OUTCOMES either way and paste which branch was taken. V-03 requires that branch stated and proven, and `lane_containment.py` shown unchanged. E-04/V-04 now cite `z8ex9f` as the live carrier and require `nvymif`'s ACTUAL status rather than requiring it be `open`. No `Item-Dependencies` edge added (grammar has no "prefer after"; `z8ex9f` is `to-review`). |
| PR-502 | HIGH | IN-SCOPE | Rubric E (testing), D (anti-regression) | Drove `lane_containment.teardown_lane_if_classified` on real merged git lanes under each mutation: (a) ignored case `torn_down` True->False with `reason_codes` `()` BOTH times; (b) untracked case `torn_down` False->True with `reason_codes` `('unknown-untracked-file',)` BOTH times | THE MUTATION EVIDENCE V-03 DEMANDS IS SATISFIABLE BY A MODULE THAT DETECTS NEITHER MUTATION. `reason_codes` is INVARIANT across both mutations in exactly the cases each is meant to break, so a module asserting on reason codes alone (the natural reading of E-03's phrasing and of V-03's evidence list, where reason codes lead) goes GREEN under both and proves nothing. Only `torn_down`/`classified` and worktree existence move. This is the vacuous guard the plan's own gate names as the third thing most likely to go wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's expected outcome and V-03 both now require the failing assertion to be on `torn_down` or worktree existence, state the measured invariance of `reason_codes` under both mutations, and explicitly refuse a reason-code assertion as acceptable mutation evidence. |
| PR-503 | MEDIUM | IN-SCOPE | Rubric G (executability) | `lane_containment.collection_receipt_path` -> `item_slug`, whose body is `f"{int(item['position']):02d}-{item['id6']}"`; an `order`-keyed item raises `KeyError: 'position'` (hit while probing) | E-03 makes a COMPLETE receipt load-bearing for all four cases (F-04) but does not state the item shape the receipt path requires, so a fixture keyed on the plausible `order` raises mid-fixture rather than failing a test. A stall in the one piece of setup every case depends on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now records that the fixture item must carry `position`, naming the raise an `order` key produces. |
| PR-504 | LOW | IN-SCOPE | Rubric E (validation evidence) | Bare `python3 -m pytest` at review HEAD `84cdeb94`: `3353 passed, 2 skipped, 3 warnings in 108.82s` vs the plan's authored `3246 passed, 2 skipped` at `9733d47a` | The stated baseline has drifted by 107 tests. NOT a defect in the plan's method, which already says the figure is "there to be COMPARED against, not copied"; the drift is evidence for that instruction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the review re-measurement beside the authored figure in both places (the validation section and V-03), keeping the authored number rather than overwriting it, and recorded that both mutation runs reproduced green at review. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `z8ex9f` will invert E-03's assertions (PR-501). Declare an `- Item-Dependencies:` edge, drop E-03, or make E-03 adaptive? | MAKE E-03 ADAPTIVE: re-measure at execution and branch on whether `z8ex9f` has landed. | (a) Declare `executed:z8ex9f`: rejected, the grammar (`ipd_schema._parse_item_dependency_edge`) offers `executed:`/`exists:`/`state:` only with no "prefer after", and `z8ex9f` is `to-review`, so the edge would gate a low-priority followup behind a medium-priority chore's whole review and execution cycle, overstating a preference as a hard constraint. (b) Drop E-03 and let `z8ex9f` own the guard: rejected, `z8ex9f`'s own test module pins ITS six shapes, not the amended-R5.5 classification, so the F-05/F-06 hole would stay open. (c) Edit `lane_containment.py` here so both pass: rejected outright, that file is `z8ex9f`'s declared scope and is out of scope here. | `z8ex9f` `- Status: to-review` and its `- Scope-Paths:`; its E-03 "treat that as BLOCKING"; `lane_containment.inventory_lane` signature takes `lane_root`; the same reasoning recorded for plan `ery0ia` OQ-01 on 2026-09-30 | yes |
| D-2 | Should `nvymif`'s `- Carrier:` row in Deferred be re-pointed at `z8ex9f` now that the item is `graduated`? | NO. Keep `- Carrier: nvymif` and name `z8ex9f` in prose (F-14, E-04). | (a) Re-point the carrier field at `z8ex9f`: rejected, a graduated item still resolves and is the durable record of the obligation, while a pending plan can be superseded or not-executed, so pointing the machine-readable field at the less stable artifact weakens the link. (b) Leave the plan silent about the graduation: rejected, E-04 would then write a docstring sending readers to a closed item. | `check.from-backlog-dangling` / carrier resolution accept a graduated item; `nvymif` `- Graduated-To: nvymif` resolving to `z8ex9f`; `AGENTS.md` on `graduated` meaning design handed off | yes |
| D-3 | The plan declines a `Blocks-Release` gate for F-06 (unguarded data-loss direction) and invites disagreement. Accept or escalate? | ACCEPT the plan's judgement. | (a) Require a `Blocks-Release: next` gate: rejected, the repository's test for `bug` is USER-PERCEPTIBLE impact, and today's behavior is correct with only its guard missing, so no user experiences a defect; gating would misclassify latent risk as a live bug. (b) Ask the maintainer: rejected as unnecessary, the rule is written down and this case falls plainly on one side of it. | `AGENTS.md` "Every live bug gates the next release" and its perceptibility test ("inefficiency users cannot notice is not a defect"); backlog `0kdwm3` `- Work-Kind: followup` with no `- Blocks-Release:`; F-05/F-06 reproduced showing correct behavior, absent guard | yes |
