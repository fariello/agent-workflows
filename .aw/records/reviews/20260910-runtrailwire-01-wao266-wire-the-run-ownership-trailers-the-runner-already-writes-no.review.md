# Review: wire the run ownership trailers the runner already writes nothing into, child wao266 (Set runtrailwire)

- Subject-Id: wao266
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `bf2c6b46`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries
`- Blocks-Release: next`, correctly inherited: backlog `a8eufb` carries the same field, and `next` resolves
to the single `planned` release record `f33nrj` (2.0.0).

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE PLAN'S STRUCTURAL WORK IS EXCELLENT AND I VERIFIED ALL OF IT. The narrowing from the item's three steps
to one is right: `commit_backlog_close` really is the only `offer_commit` call in either runner (measured:
one hit in `oc_runipd`, zero in `agy_runipd`), `agy_runipd` really does reach it by import, and the trailer
machinery really is empty-safe by construction. Deciding NOT to build a second commit path, NOT to add a CLI
flag, and NOT to touch the consumer are all correct calls with recorded reasoning. This is a carefully
scoped plan by an author who checked their premises.

BUT THE ONE MEASUREMENT NOBODY TOOK IS THE ONE THAT DECIDES THE PLAN'S VALUE. I asked how many commits the
wired call site has ever produced, and what they touch. Across ALL 2926 commits on all refs, exactly THREE
came from `commit_backlog_close`, and `git show --stat` shows each touched exactly ONE `.backlog.md` file.
Meanwhile the commits finalize's attribution reads are the AGENT's code commits in `base_head..HEAD`
(`ipd_lifecycle._changed_path_sources`), and those are made by the agent running raw `git commit -m msg --
<path>` as the runbook directs at `oc_runipd.py:2607`. They pass through no `offer_commit` call, so no
wiring of that helper can reach them.

SO THE PLAN DELIVERS A REAL WRITER THAT NOTHING WORTH READING WILL CARRY. That does not make it wrong: the
mechanism is currently DEAD CODE, a tested parameter no caller passes, and making it live with a
git-parser-verified end-to-end path is genuine value and a correct first step. It does mean the Concern,
Goal and Scope as authored overstate the reach, that finalize is exactly as capable after this plan as
before, and that `h9cn0y`'s accepted cost is untouched. All three sections now say so, and the work that
WOULD close the gap (trailering agent code commits, which means changing what the runner instructs the agent
to do, or routing agent commits through `aw commit`) is named in Deferred as unplanned and materially larger.

I RAISED THE RELEASE-GATE QUESTION RATHER THAN ANSWERING IT. Given the measured reach, whether this still
merits `Blocks-Release: next` is a value judgement about what a release gate is for, not a technical fact.
OQ-04 states both cases and stays non-blocking so the plan can be approved either way.

THREE STALENESS CORRECTIONS, one of which the plan itself asked its executor to check. `h9cn0y` has EXECUTED,
not `approved`, which makes its accepted cost live rather than prospective AND means it already performed the
characterization-test inversion this plan still lists as outstanding. The suite baseline is wrong in both
halves, and one of the two real failures is IN A FILE THIS PLAN DECLARES and is load-sensitive, so an
executor could easily mistake it for their own regression. And the plan's warning about a fragile
source-substring test overstated the risk: that assertion is an AST check, though it does forbid the literal
tokens `-A`/`add_all` even in a comment.

ONE IMPLEMENTATION TRAP the plan would have hit: `commit_backlog_close` returns None on `len(paths) < 2`
BEFORE reaching `offer_commit`, so a single-file test fixture never commits and every trailer assertion over
it would pass vacuously.

Six findings, all FIXED in place, no deferrals. One new non-blocking open question. E-item and V-item counts
are unchanged at five each.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | C. architecture; G. executability | `git log --all` over 2926 commits -> 3 from this path (`484994ec`, `76c83c8c`, `80fa5441`), each 1 `.backlog.md` by `git show --stat`; `ipd_lifecycle._changed_path_sources` diffs `base_head..HEAD`; `oc_runipd.py:2607` | **THE WIRED CALL SITE PRODUCES ALMOST NO COMMITS AND NEVER TOUCHES CODE, so the plan delivers a writer that nothing worth reading will carry.** `commit_backlog_close` accounts for 3 commits in the repository's entire history, one backlog file each. The commits finalize's attribution reads are the AGENT's code commits in `base_head..HEAD`, made via raw `git commit` per the runbook directive, reachable by no `offer_commit` wiring. The plan is still correct and worth doing (the mechanism is dead code today), but its Concern, Goal and Scope all imply it closes the attribution gap, and it does not: finalize is exactly as capable afterwards | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Concern, Goal, Scope and under-scope all rewritten to state the measured reach honestly; E-01 gains claim (e) requiring the measurement BEFORE anything else with an explicit instruction not to restate the gap-closing claim; a new Deferred entry names the agent-commit work with its two candidate routes and their failure modes; the spec-sync docstring correction is made precise so it does not overstate; V-01 requires the measurement pasted. New F-12, and OQ-04 puts the release-gate consequence to the maintainer |
| PR-802 | HIGH | IN-SCOPE | Evidence accuracy; D. anti-regression | `.aw/records/plans/executed/20260906-scopeattr-01-h9cn0y-...ipd.md` with `- Status: executed`; its history decision `09-h9cn0y-D2` | **`h9cn0y` HAS EXECUTED, which the plan's own E-01(d) says must be reported, and it invalidates two of the plan's statements.** The plan says `approved` throughout. Consequences: its accepted cost is LIVE in the tree now rather than prospective, so the promised follow-up is a real outstanding gap; and it ALREADY INVERTED `test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation` to `..._is_now_disregarded_gap_CLOSED`, which this plan's Deferred section still lists as outstanding work belonging to it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01(d) rewritten to state the executed status as already-measured with both consequences; F-3 corrected; the stale inversion Deferred entry rewritten to record that it was checked and found already done; the post-gate follow-up instruction updated to say the cost is live today. New F-13 |
| PR-803 | MEDIUM | IN-SCOPE | E. testing; A. correctness | `oc_runipd.py:1405-1414` (`if len(paths) < 2: return None` above the `offer_commit` call); the three historical commits each touched 1 file | **A single-file test fixture would make every trailer assertion pass vacuously.** The fail-closed guard returns None BEFORE `offer_commit`, so unless E-04's fixture builds a genuine two-path move (both sides of the graduated -> done rename in the porcelain view), no commit is made and the read-back assertion tests nothing. The plan's E-04 does not say to construct a move | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required-tests gains an explicit two-path-move requirement with the reason; V-04 requires proof the fixture actually committed (a returned sha, not None). New F-14 |
| PR-804 | MEDIUM | IN-SCOPE | E. testing; Evidence accuracy | `tests/test_runner_backlog_close.py:574-600`; `_code_only` at `:57` | **The plan's fragility warning is aimed at the wrong risk, and the real textual constraint is unstated.** F-9 warns that a source-substring assertion at `:576` may break on a legitimate edit. The assertion is at `:574` and is STRUCTURAL: it `ast.parse`s the source and asserts an `ast.Compare`/`In` over `item_id6`/`name`, with a comment saying reformatting cannot break it. So a keyword-argument addition cannot trip it. What IS textual, over RAW source including comments, is a ban on `-A` and `add_all`, which an explanatory comment at the new site could plausibly violate | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 corrected and downgraded to LOW with the AST mechanism described; E-05 and V-05 restate the real constraint; the fence forbids writing `-A`/`add_all` even in a comment |
| PR-805 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | measured bare `2 failed, 5957 passed, 3 skipped, 2 xfailed`; `test_orchestrator_retirement` -> `112 passed`; `tests/test_runner_backlog_close.py` alone -> `47 passed`; `.gitignore:49` | **The suite baseline is wrong in both halves AND one failing test lives in a path this plan declares.** The plan cites `1 failed, 5648 passed` naming `test_orchestrator_retirement`, which passes. The real failures are the reporting-contract parity test (caused by the gitignored `opencode-recovery/` tree of another party's transcripts) and `test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, which is in a DECLARED file, passes in isolation, and fails on a 30-second timeout under `-n auto`. An executor would reasonably read that as their own regression | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 and required-tests carry the re-measured baseline, both node ids, the load-sensitivity warning and the instruction to verify per-file; the `opencode-recovery/` prohibition is in both the fence and required-tests; V-05 requires per-file evidence and node-id comparison. New F-15 |
| PR-806 | LOW | IN-SCOPE | G. executability; spec sync | `work_cmd._trailers_from_args` docstring; `oc_runipd.py:2607` | **The prescribed docstring correction would replace one misleading sentence with another.** The plan says to correct "the runner wiring is deliberately deferred" to say the runner now wires them. Post-change the accurate statement is that the runner wires its DRIVER-SIDE commit while the agent's code commits remain deferred; the blunt correction would mislead precisely the reader who later asks why finalize still cannot attribute | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section requires both halves be stated, keeps the no-public-flag reasoning, and keeps the out-of-scope-declaration instruction intact |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The wired path produces 3 commits in 2926 and never touches code (PR-801). Is the plan still worth executing, or should it be replanned? | KEEP AND EXECUTE, with every overstated claim narrowed in place and the real gap named in Deferred. The mechanism is dead code today; making it live, tested and git-parser-verified is real value and the correct smallest first step | REJECT - NEEDS REPLAN toward trailering agent commits instead (rejected: that is a prompt/runbook change whose compliance no code path can enforce, with its own fail-open failure mode, and it is a materially larger design decision deserving its own plan and maintainer input rather than being smuggled in as a rescope); leave the claims as authored (rejected outright: the Concern implied the attribution gap closes, and a future reader would trust it) | 3 commits measured across all refs, 1 `.backlog.md` each; `_changed_path_sources` reads `base_head..HEAD`; agent commits made via raw git per `oc_runipd.py:2607` | yes |
| D-2 | Does the measured reach change whether this warrants `Blocks-Release: next`? | ASK THE MAINTAINER via non-blocking OQ-04, stating both cases and the mechanism for dropping the gate. Did NOT clear or keep the gate on my own authority | Drop the gate in review (rejected: a release gate is the maintainer's risk-appetite call, and clearing an inherited gate unilaterally would silently drop an obligation the maintainer set on `a8eufb`); keep it silently (rejected: the plan's own value argument for the gate rests on reach it does not have, so approving on the authored version would be approving on wrong information) | The gate is inherited from `a8eufb`; `next` resolves to `f33nrj` (2.0.0); the measured reach is 3 backlog-file commits | yes |
| D-3 | The plan lists the characterization-test inversion as outstanding, but `h9cn0y` already did it. Delete the Deferred entry or rewrite it? | REWRITE it to record that it was checked and found ALREADY DONE, naming `h9cn0y`'s decision `09-h9cn0y-D2`, rather than deleting it | Delete the entry (rejected: a future reader comparing this plan to backlog `a8eufb`, which assigns that inversion by name, would find the obligation unaccounted for and might redo it); leave it (rejected: it asserts outstanding work that does not exist) | `h9cn0y`'s history records the inversion to `..._is_now_disregarded_gap_CLOSED` with its same-identity measurement retained | yes |
