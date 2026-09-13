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
