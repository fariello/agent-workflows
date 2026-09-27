# Review findings: plan 5xzld0

- Subject-Id: 5xzld0
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8e96d348` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED (disposition `conforming`) with ONE advisory, `IPD-Z602` on E-05 ("action text may bundle
multiple concerns ... 3 clauses"); that advisory is now cleared by the E-05/E-10 split (PR-005), and
`--phase review-finalize` conforms with no advisories. No pre-review snapshot was needed: the plan was
committed and unmodified, and the lane-input copy is byte-identical to the tracked file (`diff`
reported no output).

ALL FOUR DEFECTS ARE REAL AND I REPRODUCED ALL FOUR IN A SINGLE RUN rather than trusting the brief.
Driving the real `cli.main(["rename","specs",...,"--to-id6","--apply","--no-commit"])` in a temp repo
seeded with a review record, a test file, an in-fence transcript and an out-of-fence citation:

```text
rc: 0
renamed .aw/records/specs/20260701-1200-01-legacy.spec.md -> .aw/records/specs/20260701-rttogp-01-rttogp-legacy.spec.md
rewrote 2x '20260701-1200-01-legacy.spec.md' -> '20260701-rttogp-01-rttogp-legacy.spec.md' in .aw/records/plans/pending/...
-- .aw/records/reviews/20260701-x.review.md
cites 20260701-1200-01-legacy.spec.md and bare 20260701-1200-01      <- F-1: NOT rewritten
-- tests/test_x.py
NAME = "20260701-1200-01-legacy.spec.md"                             <- F-1: NOT rewritten
-- the plan fixture
outside fence: 20260701-rttogp-01-rttogp-legacy.spec.md              (correct)
```
    --- would rename .aw/records/specs/20260701-rttogp-01-rttogp-legacy.spec.md -> y ---   <- F-3: transcript FALSIFIED
```

F-2 and F-4 reproduce together on the live tree, which is the single most economical piece of evidence
in this plan and is now quoted verbatim in E-10:

```text
--- would rewrite 1x '20260725-0957-01' -> '20260725-uaeizs-01-uaeizs-external-delivery-host-probe.prompt'
    in .aw/records/plans/executed/20260908-specdirs-02-1bdxcp-...ipd.md ---
```

whose target line is `    - deferred (2): 20260725-0957-01, 20260726-1239-01`, a citation of the deferred
SPEC, not of the prompt being renamed. So one edit shows both the short-handle expansion and the
cross-type contamination. The shared-prefix census is exact: over all 60 legacy-prefixed records in
`.aw/records/**` there is precisely ONE collision, `20260725-0957-01`, held by a prompt and a spec.

The fence analysis is likewise exact, including its own honest limit. Computing fence state line by
line with `ipd_lint._FENCE_RE`'s semantics: 3i6rso's two transcript lines are `inside_fence=True`,
ha55fi's two are `inside_fence=False`. So fence masking fixes the first and genuinely cannot fix the
second, which is what F-3 says. `d6b2fa00`'s commit message independently corroborates every defect,
including the 9 hand-fixed reviews and the two hand-restored short handles.

WHAT I FIXED. Six findings. The two that matter most are PR-001 and PR-002, and both came from RUNNING
the thing rather than reading it. PR-001: E-01's own case (d) fixture, written as the plan specifies,
makes the ENTIRE rename return rc=2 and rename nothing, because a path citation naming a directory
other than the artifact's real one trips `find_unrewritable_path_citations` and `run_rename_generic`
refuses on `--apply`. Four of the five cases meant to pin real defects would have failed for that
unrelated reason, sending the executor after the wrong bug on the plan's first step. PR-002: F-5's
premise is measurably false. I compared the unrewritable set under current versus widened roots across
all 60 legacy-prefixed records and widening newly blocks ZERO of them; the spec F-5 names already
yields 25 unrewritable citations across 14 files from the CURRENT roots, so it already cannot be
`--apply`-renamed today. Leaving that finding at MEDIUM would have had the executor hunting a
regression this plan does not cause.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. testing / A. correctness (a fixture that makes five tests fail for the wrong reason) | Executed at review: with case (d)'s transcript written as `x/20260701-1200-01-legacy.spec.md` the command returned `rc: 2`, `error: full-path citation 'x/...' names a different directory than the file; cannot auto-rewrite`, and NOTHING was renamed or rewritten; with the same fixture citing `.aw/records/specs/20260701-1200-01-legacy.spec.md` it returned `rc: 0` and reproduced all four defects. Mechanism: `artifact_rename.find_unrewritable_path_citations` + the `if unrewritable:` arm of `run_rename_generic` returning `MutationResult(2)` BEFORE any rewrite | **E-01'S OWN FIXTURE, AS SPECIFIED, ABORTS THE COMMAND IT IS TESTING.** Case (d) tells the executor to write a fenced transcript reading `--- would rename .../20260701-1200-01-legacy.spec.md -> ... ---`, and the natural reading of `.../` is any placeholder directory. Any directory other than the spec's real one makes `--apply` exit 2 with nothing done, so cases (a), (b), (c) and (e) all fail too, with a message about path citations that has nothing to do with the four defects they pin. The plan had no exit-code assertion anywhere, so this would have presented as five mysterious reds on the plan's FIRST item. | C:Low; U:Low; S:Low; F:Medium-High if pasted as real defect evidence, but the FIX is Low (name the real directory; assert rc) | FIXED | E-01 gains a named FIXTURE TRAP paragraph with both measured runs (rc=2 nothing-done versus rc=0 all-four-reproduced), mandates that every path citation in every fixture name the artifact's REAL directory, and requires each test to assert exit code 0. Its Expected outcome now records what the corrected fixture actually produced, including that the whole-stem edit fires twice so case (c) needs a bare prefix token with no slug to isolate the legacy-prefix edit. V-01 requires the executor to state, per case, that rc was 0 and the file WAS renamed, and says explicitly that an all-cases `cannot auto-rewrite` paste is the trap and not the defects. The gate lists it as trap (1). |
| PR-002 | MEDIUM | IN-SCOPE | D. anti-regression (a finding whose premise is false, pointing the executor at a non-existent regression) | Measured at review over all 60 legacy-prefixed records, unrewritable set under CURRENT roots vs WIDENED (`+.aw/records/reviews`, `+tests`, `+.py`): already-blocked 23, NEWLY blocked 0, clean 37. For F-5's own example, `find_unrewritable_path_citations` on `20260802-1904-01-ipd-structure-and-linting.spec.md` returns 25 citations across 14 files FROM CURRENT ROOTS, so `--apply` already exits 2 today; the live preview prints 25 such WARNING lines at HEAD | **F-5 CLAIMED WIDENING THE ROOTS WOULD NEWLY BLOCK RENAMES. IT BLOCKS NOTHING NEW.** The two citing files it names are real, but the artifact they cite is already blocked from the current roots, and across the whole legacy corpus the widened roots add zero newly blocked targets. Left as a MEDIUM the executor would either look for a regression that cannot occur, or (worse) read E-07's 25 pre-existing warnings as damage this plan caused and start "fixing" unrelated stale citations mid-execution. F-5 also mis-attributed the fence work to E-05 when E-04 owns it. | C:Low; U:Low; S:Low; F:Low (a findings-row correction plus an expectation in E-07) | FIXED | F-5 downgraded to LOW and rewritten with the measured comparison and the corrected E-number. E-07 gains a paragraph stating that its spec preview prints 25 pre-existing full-path warnings at HEAD, that they are NOT caused by this plan, that the executor must not try to clear them, and that consequently that spec cannot be `--apply`-renamed today, which is a further reason E-07 is preview-only. The gate repeats the operational note so an approver is not surprised. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. anti-regression (a coupling the plan's own reasoning stops one step short of) | Measured at review: `tests/test_history_order.py::DerivationIsUnchangedTests` asserts `assertGreaterEqual(len(intersection), 700)` against a 777-key path-keyed baseline; live intersection is 732, margin 32. The baseline's keys are paths (`.aw/records/plans/executed/...ipd.md`), and F-6 correctly keeps `.json` out of the rewrite | **EXCLUDING `.json` IS NECESSARY BUT NOT SUFFICIENT, AND THE PLAN TREATS IT AS SUFFICIENT.** Because the baseline keys PATHS and is deliberately never rewritten, every `aw rename plans` / `aw group plans --rename` of a TERMINAL plan silently drops one key from the intersection. About 33 such renames breach the floor and redden a guard whose failure message ("expected at least 700 paths in common") points a reader at `derive_plan_status` rather than at the renames that caused it. The coupling predates this plan, but this plan is what makes renaming routine enough to reach it. | C:Medium (the fix is a test-architecture choice: re-key by id6, floor as a fraction, or regenerate); U:Low; S:Low; F:Low; Overall:Medium | FIXED (recorded + carried) | Added as F-7 with the measured margin, and carried as backlog `p0a5kr` (bug, `Blocks-Release: next`) with three candidate fix directions and the reasoning for preferring id6 re-keying. Declared under "Deferred / out of scope" with `- Carrier: p0a5kr` and named in the Scope check's under-scope list, so it is visibly accepted rather than missed. Not fixed here: `tests/test_history_order.py` is outside `- Scope-Paths:` and the change is a guard other work depends on. |
| PR-004 | MEDIUM | IN-SCOPE | G. executability (a Goal claim wider than the delivered work) | Measured at review: 44 citations of real record filenames or legacy prefixes in `agent_workflows/*.py`, including FULL filenames in `attention_contract.py` (`20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`), `ipd_schema.py`, `check_engine.py` (two), `install_wizard.py`, `project_context.py`, `project_layout.py`, `project_registry.py`, `project_schema.py`, `record_producers.py`, `research_contract.py`, `runner_stop.py`, `selectors.py`, `storage.py`. `d6b2fa00`'s message lists "two spec handles in `runner_shared.py` comments" among its hand fixes | **THE GOAL PROMISED "EVERY REAL CITATION" WHILE LEAVING 44 IN THE SHIPPED PACKAGE.** The defect class the carrier item describes is citation rot on rename; production source has it too, and the maintainer has already paid for it by hand at least once. Unqualified, the Goal would let a future reader audit "does a rename reach every citation now?", read this plan's title, and answer yes. | C:Low; U:Low; S:Low; F:Low (the FIX here is a narrowed claim plus a carrier; actually rewriting the shipped package is a much larger change and is correctly NOT proposed) | FIXED (narrowed + carried) | Goal gains an explicit "WHAT 'EVERY REAL CITATION' DOES NOT INCLUDE" paragraph naming production source and pointing at F-8. Added as F-8 with the measured 44 and the `d6b2fa00` corroboration, carried as backlog `zftbta` (bug, `Blocks-Release: next`) which also records a cheaper alternative worth weighing first (a CHECK reporting dangling record citations in source, with no rewrite risk). Declared with `- Carrier: zftbta`, named in the Scope check, and stated in the approval gate so a human approves the narrowed scope knowingly. |
| PR-005 | LOW | IN-SCOPE | G. executability / right-sizing (one item, two independent surfaces) | `aw ipd lint --phase author` advisory `IPD-Z602`: "E-05: action text may bundle multiple concerns (chains multiple semicolon-separated action clauses (likely multi-concern; 3 clauses))". Reading E-05: one detection decision inside `plan_reference_rewrites`, PLUS printing plumbing through `run_rename_generic`, `run_group_generic`, `plans_refs.apply_renames` and `research_refs._apply_renames` | **E-05 BUNDLED A ONE-FUNCTION DECISION WITH FOUR-CALL-SITE PLUMBING IN THREE MODULES.** These have different failure modes and different evidence: the decision is provable by content assertions, while the plumbing is provable only by showing the warning reaching each surface. Bundled, an executor can satisfy "E-05 done" having wired one or two call sites, and the missing ones fail silently, which is precisely the silent-skip defect the item exists to prevent. The linter flagged it; a maintainer's sizing signal is a finding to investigate, not to dismiss. | C:Low; U:Low; S:Low; F:Low | FIXED | Split into E-05 (detect and skip, exposing `plan_reference_rewrites_with_warnings`) and E-10 (carry the warning to all four call sites, on BOTH preview and apply), with ids assigned by `aw ipd sync --apply` (watermark 09 -> 10) rather than by hand. V-10 was written to replace the generated `TODO falsifiable evidence` placeholder and now requires per-call-site confirmation, since an unreached call site is the exact regression. V-05 narrowed to the content assertion. The `IPD-Z602` advisory is cleared at `review-finalize`. |
| PR-006 | LOW | IN-SCOPE | A. correctness (an unstated bound on a guard a dependent plan relies on) | Measured at review: `20260722-2317-01` has exactly ONE holder on disk (`.aw/records/prompts/executed/20260722-2317-01-token-efficient-managed-sections-research-prompt.prompt.md`), so E-05 finds no collision and DOES emit the legacy-prefix edit. Yet `DECISIONS.md` cites "research `20260722-2241-01` ... and `20260722-2317-01`" and executed plan `kemhdg` cites `research '20260722-2317-01:10-38'`. Dependent plan `iyi4hc` (carrying `- Item-Dependencies: executed:5xzld0`) records in its own F-4 that a research file with that prefix existed, per `git log --all --name-only` | **E-05'S UNIQUENESS CHECK IS A CURRENT-TREE TEST AND THE PLAN DOES NOT SAY SO.** A prefix unique on disk can still be historically ambiguous, so renaming that prompt would rewrite two citations that name a DELETED research artifact. The risk of leaving this implicit is specific and real: the dependent plan assigns the gap to its own E-03 while relying on this plan's guard, so with the bound unstated each plan could assume the other covers it. | C:Low; U:Low; S:Low; F:Low | FIXED | Added as F-9 with the measured holders and both citing documents, and declared under "Deferred / out of scope" as a reasoned `Carrier-Declined` that names `iyi4hc`'s E-03 as the downstream owner. Deliberately NOT widened into E-05: a history-walking uniqueness check is a different and far slower design, and the case is already covered downstream. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-5 claims widening the roots newly blocks renames. Verify or accept? | MEASURE IT, and on finding it false, downgrade to LOW and rewrite the row with the comparison, plus set E-07's expectation for the 25 pre-existing warnings. | (a) Accept the plan's MEDIUM and move on: rejected, a false regression claim costs the executor a hunt and, worse, invites "fixing" unrelated stale citations mid-execution. (b) Delete the row: rejected, the citers it names are real and a future reader would re-derive the same worry; recording the measurement inoculates them. (c) Add pre-fixing those 25 citations to this plan: rejected as OVER-SCOPE, they are pre-existing breakage the plan's own scope explicitly excludes ("any already-broken citation in the tree"). | Measured across all 60 legacy-prefixed records: newly-blocked 0, already-blocked 23. `find_unrewritable_path_citations` on the named spec returns 25 hits across 14 files from CURRENT roots; live preview prints 25 WARNING lines and `--apply` returns `MutationResult(2)` via the `if unrewritable:` arm. | yes |
| D-2 | Two real unfixed defects surfaced (production-source citations; baseline-floor erosion). Fold in, decline, or carry? | CARRY BOTH as new `Blocks-Release: next` bug items (`zftbta`, `p0a5kr`) and narrow the Goal; fix neither here. | (a) Fold into this plan: rejected for both. Production source means rewriting the SHIPPED package, where a bad substitution is a runtime defect rather than a stale document, and 13-plus modules are outside `- Scope-Paths:`; the baseline fix is a test-architecture decision on a guard other work depends on. (b) `Carrier-Declined` both: rejected, these are genuine unfixed DEFECTS rather than deliberate divergences, and the carrier rules oblige a durable handoff for exactly that case; declining would bury two real bugs in an executed plan's prose. (c) Say nothing about production source: rejected outright, it leaves the Goal's "every real citation" false. | 44 measured citations in `agent_workflows/*.py`; `d6b2fa00` names `runner_shared.py` among its hand fixes; `test_history_order` floor 700 vs live intersection 732. `ipd_schema.CARRIER_DECLINED_FIELD` semantics (a decline is a recorded decision that something needs no carrier). | yes |
| D-3 | E-05 carries an `IPD-Z602` density advisory. Split it, or note the advisory and proceed? | SPLIT into E-05 + E-10 via `aw ipd sync --apply`, and write a real V-10. | (a) Note it and proceed: rejected, the workflow states a sizing signal is "an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed", and here the bundling has a concrete failure mode (a partially-wired warning fails silently at the unwired call sites). (b) Hand-number the new item E-10: rejected, ids are assigned by `aw ipd sync` and hand-numbering risks colliding with the watermark. (c) Leave `aw ipd sync`'s generated `TODO falsifiable evidence` in V-10: rejected, a TODO placeholder in a validation item is exactly what the lifecycle forbids in a review-ready plan. | `IPD-Z602` advisory text from `ipd_lint.lint_file(checkpoint='author')`; four call sites confirmed by reading `artifact_rename`, `plans_refs` and `research_refs`; `aw ipd sync --apply` reported "assigned E-10; watermark advanced"; `review-finalize` now conforms with no advisories. | yes |
| D-4 | Does E-02's new root list conflict with spec `4sd62s`, which requires scanners including `artifact_refs` and `artifact_core.iter_scan_files` to exclude a `records/meta/` tree through ONE shared exclusion list? | NO CONFLICT. Proceed, and record the obligation for whoever implements that spec. | (a) Treat it as a blocking spec conflict: rejected on evidence, the spec is `- Status: reviewed` (not implemented) and no `records/meta` exclusion exists in `artifact_core` today, so there is nothing to diverge from. (b) Pre-emptively add a meta exclusion here: rejected as OVER-SCOPE and premature, it would implement part of an unapproved spec. (c) Say nothing: rejected, a second root list is exactly the kind of thing that spec's implementer must know about, and silence is how one list gets the exclusion and the other does not. | `4sd62s` Section 4.4 text; its `- Status: reviewed`; `rg 'records/meta' agent_workflows/artifact_core.py` returns nothing. | yes |

### Deferred and open

- (none). All six findings were FIXED in place (PR-003, PR-004 and PR-006 as recorded-and-carried, with
  two new backlog items and one reasoned decline). No finding reached the repository's gate threshold
  (`HIGH` per default) AND was left OPEN or DEFERRED: PR-001 is HIGH and is FIXED, so no escalated
  `- Blocking: yes` question is owed. Both of this plan's open questions are `resolved` and
  non-blocking. No `Reversible: no` decision was taken, so no escalation is owed.

HONEST LIMITS, stated because they bound what this round proves. I reproduced all four defects end to
end, measured the shared-prefix census, the fence positions of both named transcripts, the widened-root
blocking comparison, the 44 source citations, the baseline margin, and the scan cost. I did NOT write
any code or any test, so that the shipped fix is correct, that the new tests are non-vacuous, and that
the bare suite stays green remain E-02..E-10's work and V-02..V-10's evidence. My reproduction used
`rename specs --to-id6` only; I did NOT exercise `aw group`, `rename plans`, or `rename research`, so
the four-call-site claim in E-10 rests on READING `artifact_rename`, `plans_refs` and `research_refs`
rather than on running each path, which is exactly why V-10 now demands per-call-site evidence. I ran
the bare suite once for the `2501 passed, 2 skipped in 59.95s` baseline and did NOT run the slow set
(`make test-all`); `tests/test_installer.py` and `tests/test_cli.py` are both slow-marked and both
contain legacy-prefix tokens, so a rename-related interaction there would not have been caught by my
run. That is a hole, not a clearance. My "no newly blocked targets" measurement covers the 60
legacy-prefixed records only; a CLUSTERED-name record could in principle carry stale path citations I
did not enumerate, though the same fail-loud contract would surface them identically. Finally, both new
backlog items assert a fix DIRECTION, not a decided design; the maintainer may prefer another.
