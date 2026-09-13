# Review: close a backlog item inside the lane so nothing writes to the shared checkout mid-run, child 9iq461 (Set dirtygates)

- Subject-Id: 9iq461
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b68da2dc`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review, and `--phase review-finalize` CONFORMS clean afterwards, with no
`IPD-Q501`: this plan's only open question was already resolved by the maintainer and this review added no
blocking question, unlike Orders 01 and 02.

DISCLOSURE: same repository, same model family as the author, so treat this as a near-self-review worth
less than an independent one. Its value rests on what was DRIVEN rather than re-read. Measured here: the
finalize/integrate/teardown/close ordering read at its four cited anchors; `evaluate_backlog_close` read
in full including its carrier rule; `collect_earned_paths` traced to the `git diff` it runs and the `cwd`
it runs in; `close_backlog_item`'s actual argv read (including `--dir` and `--no-commit`);
`plan_bucket` read to establish it does no IO; the multi-carrier population RECOMPUTED across both the
plans and specs trees; `find_from_backlog_artifacts` read to establish carriers include specs; the specs
tree grepped for any requirement binding the close to main; and the three approved release-blocking plans
grepped for any mention of the close path.

THIS IS THE STRONGEST PLAN IN THE SET AND REVIEW DID NOT WEAKEN IT. Its diagnosis is exactly right and
every ordering claim verified: the plan's own move already runs in the lane via `finalize_repo`
(`oc_runipd.py:6713`) while the backlog close runs against main (`:6863`) AFTER integration and AFTER
teardown (`:6825`), so a successful item really does commit into the shared checkout mid-run for no stated
reason. F-3's rebuttal of the existing comment is sound: a merge is atomic, so riding it achieves the
property the comment wants strictly better than waiting for it. The worker-versus-coordinator principle in
Step 0 is correctly applied and correctly distinguishes this plan from Order 04.

THE FINDING THAT MATTERS IS A SILENT-FAILURE MODE THE PLAN WOULD HAVE SHIPPED. `evaluate_backlog_close`
takes `earned_paths`, which `collect_earned_paths` computes by running
`git diff --name-only <starting_head>..<ending_head>` with `cwd=repo` (`:1279-1281`). For an isolated turn
BOTH commits are on the LANE BRANCH, so evaluating in main BEFORE the merge (which is exactly what E-03
mandates) does not raise: the function is best-effort and its own docstring says fewer earned paths "can
only ever WITHHOLD a close". The result would be an empty earned set, the gate refusing every close, and
the runner quietly never closing a backlog item again. Worse, E-05's regression as written (items 2 and 3
run, main clean) PASSES under that broken behavior, and so does every negative case V-03 originally
required. So the plan had a route to being marked validated while having disabled the feature it was
reorganizing. E-03 now names the hazard with two concrete options and V-03 now demands a POSITIVE close
plus the non-empty earned set, which is the only pair that separates "correct" from "silently disabled".

THREE SMALLER CORRECTIONS, EACH A FACT ABOUT CODE. E-01 is smaller than it reads: the setter is already
directory-parameterized and already non-committing (`aw backlog set <id6> --status done --dir <repo>
--no-commit`), so redirecting the move is passing the lane path, and the `--status done` spelling must not
be touched because the positional form skips the gated path that runs `evaluate_blocking_close`. E-01 must
also redirect `resolve_backlog_item`, not only the setter, or a lane-side move runs off a main-side path.
And F-6 understated the carrier population: carriers include SPECS as well as plans, and the strict
all-IPDs-executed rule applies only when at least one IPD carrier exists.

TWO NUMBERS WERE STALE AND ARE NOW MEASURED. F-5 said 20 of 107 multi-carrier items; it is 21 of 108, and
the tail is longer than the plan implies (`kjzlgw` has 9 carriers, three items have 3). That strengthens
rather than weakens OQ-01's answer. Separately, `plan_bucket` is a pure PATH inspector that "does no IO
and must not learn to", so the lane-versus-main difference OQ-01 relies on is a filesystem-LAYOUT
difference (this plan's file already sits in `executed/` inside the lane), not a stale-content one; stated
so a later reader does not "fix" it by reading file contents.

The plan's spec-sync chore was DISCHARGED here rather than left pending: no specs-tree requirement binds
the backlog close to a particular tree. And unlike Orders 01 and 02, this plan has NO intent collision
with the three approved `Blocks-Release: next` plans, which mention the close path zero times; the file
overlap in the two runner modules is ordinary and handled by worktree isolation.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | A (correctness), E (verification) | `oc_runipd.collect_earned_paths:1266-1296` (esp. the `cwd=repo` diff at `:1279-1281` and the best-effort docstring at `:1269-1270`); `process_backlog_close:1438`; E-03 as authored | E-03 mandates evaluating in MAIN before the merge, but the `earned_paths` gate is computed from two commits that exist only on the LANE branch pre-merge. The computation fails soft, so the result is an empty earned set and a close path that refuses UNCONDITIONALLY, silently disabling the feature. Every negative test the plan required still passes in that state, as does E-05's regression. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-03 now names the hazard, offers two concrete solutions (compute earned paths in the lane, preferred; or resolve lane commits by SHA from main) and requires the choice be stated in a code comment. V-03 gains a MANDATORY positive-close case plus the non-empty earned set. New F-7 records the measurement. |
| PR-302 | MEDIUM | UNDER-SCOPE | A, G (executability) | `oc_runipd.close_backlog_item:1298-1336` (argv incl. `--dir`/`--no-commit`, and its spelling warning); `process_backlog_close:1467` | E-01 said "perform the move against the lane tree" without naming the mechanism, though the setter is ALREADY `--dir`-parameterized and ALREADY `--no-commit`. It also omitted that `resolve_backlog_item` resolves against `repo` just before the setter runs, so redirecting only the setter would drive a lane-side move from a main-side path. The load-bearing `--status done` spelling (which routes through the gated `backlog.run_set`) could be broken by an executor editing that call. | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | E-01 names the `--dir` mechanism, forbids changing the `--status` spelling with the reason, and requires `resolve_backlog_item` be redirected too. New F-8 records it. |
| PR-303 | MEDIUM | IN-SCOPE | G (honest documentation) | recomputed at review across `.aw/records/plans/**/*.ipd.md` + `.aw/records/specs/**/*.spec.md`; `oc_runipd.py:1183-1186` | F-5's population was stale: 21 of 108, not 20 of 107, and the distribution has a real tail (`kjzlgw` 9 carriers; `dh0uno`, `h7qsje`, `wjl471` 3 each) rather than being a two-carrier phenomenon. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 re-measured with its method and the tail named; E-03's inline figure updated to match. |
| PR-304 | MEDIUM | IN-SCOPE | A, C (architecture) | `check_engine.find_from_backlog_artifacts:1946-1959`, `find_from_backlog_specs:1936-1943`; `oc_runipd.evaluate_backlog_close:1178-1200` | F-6 described carrier discovery as scanning the filesystem but not that carriers include SPECS, and that the strict "every IPD carrier must be `executed`" rule fires only when at least one IPD carrier exists. A lane-side reasoning that assumes carriers are plans would be wrong for a spec-first graduation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 extended with both facts and their anchors. |
| PR-305 | LOW | IN-SCOPE | C, G | `runner_shared.plan_bucket:1463-1487` ("A BUCKET IS A DIRECTORY; READINESS IS A FIELD", "does no IO and must not learn to") | OQ-01's premise that "the lane's view genuinely differs from main's" is right but imprecisely stated: `plan_bucket` reads the PATH, not file contents, so the difference is which directory each carrier occupies in the scanned tree. Left as-is, a later reader could "fix" the difference by making the inspector read contents, which its docstring explicitly forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-9 states the mechanism precisely and warns against the content-reading "fix". |
| PR-306 | LOW | IN-SCOPE | G | grepped `.aw/records/specs/` for `zhr6mc`, `backlog_close`, close-plus-main phrasings; the three approved plans grepped for the close path (0 hits each) | The spec-sync section deferred a verification to execution time ("VERIFY BEFORE EXECUTING"), and the plan never established whether it collides with the Set's contested siblings. Both were answerable now. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync records the verification as DONE (no requirement binds the close to a tree) while keeping a cheap re-check; scope check records the verified absence of intent collision and that this plan is approvable regardless of OQ-02. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-301 leaves a real design choice (where to compute `earned_paths`). Prescribe one, or escalate to the maintainer? | Prescribe BOTH acceptable options in E-03, recommend computing in the lane, and require the executor to state its choice in a comment. | Escalate as a blocking question; or mandate one option outright. | Both options preserve the gate's meaning and satisfy every V-item, so this is an implementation detail rather than a decision reserved to the human (AGENTS.md reserves scope/priority/risk/public contracts). `plan-review.md:201` fixes by default when remediation risk is not Medium-High or High. | yes |
| D-2 | Does this plan collide with the three approved `Blocks-Release: next` plans, as Orders 01 and 02 do? | No. Certify it as independently approvable. | Escalate a blocking question by analogy with Orders 01/02, since two of those plans declare the same runner files. | Measured: `fujm0y`, `51vw4y` and `3i0aaz` mention `process_backlog_close`/`commit_backlog_close`/the backlog close ZERO times. File overlap in different regions is handled by worktree isolation and the merge gate (AGENTS.md: "two plans naming the same file is not a hazard"), so it is not a contradictory instruction. | yes |
| D-3 | Readiness for a plan whose findings are all fixed and whose only open question was resolved by the maintainer before review? | `go-pending-approval`. | `no-go`, by association with the Set's blocked Orders 01 and 02. | `plan-review.md:539-542`: the clean bar is the right verdict, no open questions, no unfixed BLOCKER/HIGH, awaiting only human sign-off. OQ-01 is `resolved` and `IPD-Q501` does not fire. Readiness is per-plan, and this plan's execution does not depend on OQ-02. | yes |
| D-4 | Was discharging the plan's own "VERIFY BEFORE EXECUTING" spec chore in review appropriate? | Yes, verify now and record it as settled, keeping a cheap re-check. | Leave it for the executor as authored. | `plan-review.md:104-108` requires the reviewer to open referenced evidence and verify material claims; a claim the reviewer can settle should not be handed on as an open risk. Kept as a re-check because the specs tree is concurrently edited. | yes |

No `Reversible: no` decisions were made in this round, so no escalation is owed. PR-301 was FIXED rather
than escalated because both remedies preserve the gate and neither is a human-reserved call.

## Round 2

Reviewed at HEAD `36175959`, as an INDIVIDUAL review of this child. Unlike Orders 01, 02 and 04, this plan
was NOT named in the orchestrator's OQ-04: it already carried `Readiness: go-pending-approval` from a clean
round 1 (APPROVE WITH REVISIONS APPLIED, all six findings FIXED). So the question this round had to answer
was not "is the stale readiness earned?" but the sharper one: IS THAT POSITIVE READINESS STILL DESERVED?

Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0 findings) before semantic review;
`--phase review-finalize` CONFORMING after revisions.

DISCLOSURE: same model family as the author and as the round-1 reviewer, so treat this as a near-self-review
worth less than an independent one. Its value rests on what was MEASURED at this HEAD.

ROUND 1'S WORK HOLDS UP, AND I RE-MEASURED RATHER THAN RE-READ IT. Every anchor resolved exactly:
`finalize_repo` at `:6713`, `integrate_lane_branch` at `:6740`, `teardown_isolation_worktree` at `:6825`,
`process_backlog_close` at `:6863` with the comment F-3 disproves at `:6859-6862`; `collect_earned_paths`
at `:1266-1296` with its best-effort docstring at `:1269-1270`; `close_backlog_item`'s `--dir`/`--no-commit`
argv at `:1316-1328` with its explicit spelling warning. F-5's multi-carrier count was recomputed
independently and matches EXACTLY: 108 items with at least one `From-Backlog` carrier, 21 with more than
one. F-7's earned-paths hazard is real as stated. This is a well-built plan and round 1 improved it
materially.

WHAT ROUND 2 FOUND IS A HAZARD BOTH THE PLAN AND ROUND 1 MISSED, IN THE SAME SENTENCE THEY BOTH RELIED ON.
E-01 says redirecting the move "is a matter of passing the lane path as `--dir`", and F-8 calls the setter
"already directory-parameterized" as a reason the item is SMALLER than it looks. Traced at review: `--dir`
does not only choose where the file moves. The gated setter route runs `check_engine.evaluate_blocking_close`,
which is the very gate F-8 protects by forbidding a spelling change, and that predicate uses its `repo_root`
to SCAN THE TREE for release-gate carriers (`check_engine.py:2026`) and to RESOLVE the evidence citation
(`:2036`). So passing the lane as `--dir` silently re-points a RELEASE GATE at the lane's filesystem view.

THE ERROR DIRECTION IS THE UNSAFE ONE, which is what makes this worth a HIGH rather than a note. In the lane,
this plan's own file has already been moved to `executed/` and carries its `From-Backlog` line, so a
lane-side scan is MORE likely to find a satisfying carrier than main's. That means a lane-side evaluation
could legitimize a `done` transition on a release-gated item that main's view would REFUSE. That is the exact
inversion of the caution OQ-01 resolved for `evaluate_backlog_close`, and the plan applied that caution to
only one of the two predicates the redirect touches. It is not certain to differ on every item (the lane is a
worktree of main HEAD, so the committed trees match), but "usually identical" is not a safety argument for a
release gate, and the difference is precisely this plan's own in-flight move.

I ALSO FOUND THE VALIDATION COULD NOT CATCH IT. Round 1 correctly hardened V-03 against the
silently-disabled-close failure mode (F-7's insight, which is excellent). But nothing in V-01 to V-05 names
the release-gate predicate, so an implementation that widened the gate would pass every existing item: main's
status would be empty, the merge would carry the move, the multi-carrier negative case would refuse, and the
positive case would close. V-01 now demands the DISCRIMINATING fixture, a release-gated item whose only
would-be carrier is this plan's own file, which is the one case where the two trees disagree.

TWO SMALLER CORRECTIONS. The gate still said "OQ-01 is BLOCKING and must be answered before E-03 is written",
which was true when written and is now false since the maintainer resolved it; an executor would stall on an
answered question. And F-5's tail description ("`dh0uno`, `h7qsje` and `wjl471` have 3 each") understates the
concentration: measured, three further items sit at 4 or more (`1ap48y`, `5wdoze`, `sjsoqq`), which matters
only because the multi-carrier fixture should be built from a real shape rather than the easiest pair.

I DID NOT WEAKEN ANYTHING. No requirement was relaxed, no test dropped, and the plan's scope is unchanged;
the additions are one hazard, its validation, and one honest correction to a resolved-question claim.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-307 | HIGH | UNDER-SCOPE | B (security/authorization), A (correctness), D | `oc_runipd.close_backlog_item:1316-1328` (`--dir <repo>`); `check_engine.evaluate_blocking_close:1980`, its `done` branch scanning `find_from_backlog_artifacts(repo_root, item_id6)` at `:2026` (defined `:1947-1959`); lane provenance `runner_shared.allocate_isolation_worktree:833-847` | THE `--dir` REDIRECT SILENTLY MOVES A RELEASE GATE. E-01 and F-8 both treat `--dir` as choosing only where the file moves; it also re-points `evaluate_blocking_close`'s carrier scan at the lane's filesystem. The error direction is permissive: in the lane THIS plan's file is already in `executed/` with its `From-Backlog` line, so a lane-side scan finds a satisfying carrier main's view would not, and a release-gated item could close `done` when main would refuse. This is the same caution OQ-01 resolved for the eligibility predicate, applied to only one of the two predicates the redirect touches. | C:Medium; U:Low; S:Medium-High; F:Medium-High; Overall:Medium | FIXED | New F-10. E-01 now requires deciding and recording IN A CODE COMMENT which tree the legitimacy gate evaluates against, names main as the safe answer with OQ-01's reasoning, and forbids quietly accepting the lane for both purposes. E-01's expected outcome extended. V-01 requires the discriminating fixture. |
| PR-308 | MEDIUM | UNDER-SCOPE | A (correctness), E | `oc_runipd.process_backlog_close:1471-1478` passing `verdict.evidence`; `check_engine.evaluate_blocking_close` SATISFIED route `:2036-2043` calling `resolve_evidence_artifact(repo_root, evidence)` | THE EVIDENCE CITATION IS RESOLVED AGAINST THE SAME `repo_root`, so a path resolvable in one tree and not the other flips the verdict. The evidence is typically this plan's own plan path, which is exactly the path whose LOCATION differs between lane and main. A second, independent reason `--dir` cannot be treated as merely "where the file moves", and it was unaddressed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-11. E-01 requires verifying the chosen tree resolves the evidence; V-01 requires pasting the actual `verdict.evidence` string and its resolution in that tree. |
| PR-309 | MEDIUM | UNDER-SCOPE | E (testing), D | V-01..V-05 as they stood; PR-307's hazard | THE VALIDATION COULD NOT DETECT PR-307. No V-item named the release-gate predicate, so an implementation that widened the gate passes all five: main's status empty, the move in the merge, the multi-carrier case refusing, and the positive case closing. Round 1's V-03 hardening against a silently-disabled close was right and is untouched; this is the mirror-image failure (a silently-WIDENED gate) and it had no coverage at all. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | V-01 gains the discriminating release-gated fixture (whose only candidate carrier is this plan's own file, the one case where lane and main disagree) plus the evidence-resolution evidence. Required tests gain a release-gate test asserting the VERDICT rather than run completion. |
| PR-310 | MEDIUM | IN-SCOPE | G (executability) | gate paragraph (pre-edit) versus OQ-01 `Status: resolved` | THE GATE STILL DECLARED A RESOLVED QUESTION BLOCKING: "OQ-01 is BLOCKING and must be answered before E-03 is written". The maintainer answered it (option (a)), and the plan records that in the question itself, so the contract contradicted its own open-questions section and would stall an executor who has permission to proceed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: nothing gated, the answer restated, plus a consolidated "three ways to get this wrong" (the `--status done` spelling, the `--dir` gate redirect, and not accepting a green E-05 as proof) each traced to its finding. |
| PR-311 | LOW | IN-SCOPE | G (honest documentation), E | measured at review: 108 items with >=1 carrier, 21 with >1; top counts 9/6/5/4/4/4 | F-5's TAIL DESCRIPTION UNDERSTATES THE CONCENTRATION. Its headline counts are exactly right (re-measured), but it reports the next tier as "`dh0uno`, `h7qsje` and `wjl471` have 3 each" when three items sit at 4 or more (`1ap48y`, `5wdoze`, `sjsoqq`) and two others at 6 and 5. Matters only for fixture realism: an executor reading "mostly two, one nine" builds the easiest pair. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-12 records the full re-measured distribution; the multi-carrier test requirement now says to build from a real shape of at least three carriers rather than a synthetic pair. |
| PR-312 | LOW | UNDER-SCOPE | G, C | `Scope-Paths:7`; `check_engine.py` absent | `check_engine.py` IS UNDECLARED WHILE F-10/F-11 REACH INTO IT. The preferred implementation does not touch it, so the omission is probably correct, but the plan gave the executor no guidance for the case where the two `repo_root` uses cannot be separated from the caller, and that module is shared with `aw check` and the pre-commit hook. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check records both cases: leave it alone if the tree split is achievable from the caller (expected), else declare it in the same pass and note the blast radius. "State which case you hit; do not edit it silently." |
| PR-313 | LOW | IN-SCOPE | G | scope-check note citing "the orchestrator's OQ-02" | The no-collision note referenced the orchestrator's question by a number that has since MOVED (it was OQ-03 when written, was renumbered to OQ-02, and is now resolved). The note's substance is correct and was re-verified; only the pointer was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to record the renumbering and that the question is resolved, so it constrains nothing here either way. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-7 | PR-307: should the plan MANDATE that the close-legitimacy gate evaluate against main, or require the executor to decide and record? | Require an explicit decision recorded in a code comment, while NAMING main as the safe answer and giving OQ-01's reasoning. | Mandate main outright; or leave the choice unstated as the plan did. | Mandating one tree presumes the two `repo_root` uses are separable from the caller, which I did not establish (the setter takes a single `--dir`). `plan-review.md:214-222` requires replacing ambiguity, which a named-preference-plus-forced-decision does, without inventing an implementation I have not verified is reachable. The safety direction is stated so a wrong choice is a visible choice rather than an accident. | yes |
| D-8 | Is PR-307 severe enough to escalate as a blocking question rather than fix in place? | Fix in place; do not escalate. | Escalate as blocking, on the grounds that it touches a release gate. | The Fix Bar (`plan-review.md:201`) defers only at Medium-High or High overall remediation risk; this is Medium, and the fix is bounded plan text (an instruction plus validation) requiring no human decision. Nothing here needs the maintainer's authority: the hazard has an unambiguous safe direction, unlike Order 01's PR-108 where two approved plans genuinely conflict. | yes |
| D-9 | Does this plan's already-positive `go-pending-approval` survive round 2? | Yes. Restore/keep `go-pending-approval`; verdict APPROVE WITH REVISIONS APPLIED. | Downgrade to `no-go` because a HIGH was found this round. | `plan-review.md:543-545` makes NO-GO correct for an OPEN question or an UNFIXED BLOCKER/HIGH. PR-307 is FIXED in place, not left open, and no question is open; `aw ipd lint --phase review-finalize` reports CONFORMING. Severity governs reporting and escalation-if-unfixed, not the readiness of a finding that was fixed (`plan-review.md:342-346`). | yes |

No `Reversible: no` decision was taken in this round, so no escalation is required under
`plan-review.md:279-292`, and no finding was left OPEN or DEFERRED at or above the gate threshold.

NOTE ON THE ORCHESTRATOR'S OQ-04: this child was not one of the three it named, and its positive readiness
is CONFIRMED rather than merely inherited. Of the Set, `u23gbn` remains the last plan carrying an
unverified `no-go`.
