# Review: build one shared record placement library and adopt it in every spec writer, child r9uvwc (Set specdirs)

- Subject-Id: r9uvwc
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed in an isolated lane worktree at HEAD `803d10f6`. `aw ipd lint --phase author` CONFORMING
before semantic review; after revision it reports exactly one `IPD-Q501`, which is the newly raised
blocking OQ-03 firing as designed and is NOT a structural defect.

THIS IS A SELF-REVIEW IN THE AUTHORSHIP SENSE AND THAT IS STATED UP FRONT: the plan's `- Author:` is
the same agent/model string as this reviewer. Nothing below therefore rests on the plan's own prose.
Every load-bearing claim was re-derived by RUNNING code in throwaway git repositories or by reading
the cited symbol at HEAD, and the four findings this review adds were all found by measurement the
plan had not performed.

THE PLAN'S SHAPE IS CORRECT AND ITS PROVENANCE CHECKS OUT, which is the first thing to confirm because
the plan itself asks to be checked on it. `wfjsp4` OQ-04 is `- Status: resolved`, owner maintainer,
and its recorded text does say "not 'add the writer child' but BUILD ONE SHARED PLACEMENT LIBRARY AND
ADOPT IT PER TYPE ... Adopting it replaces the EXISTING plans and backlog branches too". OQ-05's
ruling to amend `kw5y2s` in the same change is likewise recorded and the plan declares that spec path
in `- Scope-Paths:` as required. So the over-scope this plan carries is a maintainer ruling, not
gold-plating, and the `Size assessment: exception` is justified on that ground.

EVERY FIGURE THE PLAN CITES REPRODUCED EXACTLY, which is unusual and worth recording. 36 spec files
distributed 15 `implemented`, 13 `approved`, 2 each `superseded`/`draft`/`deferred`, 1 each
`to-review`/`implementing` (17 live / 19 terminal). The retired-filter trap: `specs._spec_files` 36,
`_iter_type_files` default 19, `include_retired=True` 36, sets equal by name. The `specs` record class
carries no `lifecycle_subdirs` while `plans`/`prompts`/`backlog` do, and
`test_lifecycle_subdirs_match_the_live_status_dirs` (`tests/test_layout.py:182-192`) covers backlog
and plans only. `kw5y2s` is `approved` and its `specs` row at `:104` reads `Single directory;
frontmatter status tracking`. The `status_set` relocation block is at `:1036-1078` with branches
`("plans","prompts")` and `backlog` and no `specs` case; `specs.run_new`'s flat-root write is at
`:1024` (the plan says `:976`, which was true at `41f6a45b`; it has drifted by the usual amount and
the plan already warns that these numbers move). All four cited backlog items resolve at the stated
statuses. `aw layout` confirms `specs` lifecycle `-`.

FOUR THINGS THE PLAN DID NOT MEASURE, EACH FOUND BY RUNNING, AND TWO OF THEM ARE DEFECTS IN CODE THE
PLAN PROPOSES TO ABSORB. This is the substance of this review.

FIRST, THE BRANCH THE LIBRARY WOULD REPLACE IS SHARD-UNSAFE (PR-002). The plan correctly warns that
plans are a many-to-one mapping, but the plans/prompts branch gets a SECOND shape wrong that the plan
never names: it tests `rec.path.parent.name` against the disposition tuple (`status_set.py:1056-1067`).
`aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/`, so a sharded plan's parent is
`202601`, the membership test MISSES, and the `else` rebuilds the path at the disposition ROOT.
MEASURED: a plan at `.aw/records/plans/executed/202601/...pl1234...` set to `superseded` landed at
`.aw/records/plans/superseded/...`, silently un-sharding it and reversing an archival decision. The
correct derivation already exists THREE times in this repository (`check_engine._plan_disposition`,
`attention._plan_disposition_from_rel`, `plans_index.scan_plans`), each taking `rel.split("/", 1)[0]`
and each commenting explicitly that a `parent.name` test breaks on shards. A library that copies the
branch it replaces inherits the bug and multiplies it across four types, which is the exact failure
mode the plan's own E-02 warns about for hardcoded status lists.

SECOND, THE `git mv` RENAME IS DECOMPOSED AGAIN BEFORE THE COMMIT, A LIVE REGRESSION OF THE FIX THE
PLAN RELIES ON (PR-003). The plan's E-03 correctly instructs relocation via `git mv` move-first, and
`apply_status_change` does produce a clean staged `R100`. But `run_set_command` records only
`dest_path` in `touched_paths` (`status_set.py:1755-1760`, the source is never appended) and
`_offer_self_commit` then opens with `git reset --quiet HEAD -- <dest>` (`:1390`), whose docstring
calls that reset "a no-op for in-place set rewrites". It is not a no-op for a RELOCATION: unstaging
one half of a staged rename decomposes it. MEASURED END TO END on the tooled path, twice:
`aw backlog set graduated bk1234 --yes` produced a commit holding `A graduated/...` ALONE and left
`D open/...` staged-but-uncommitted; `aw ipd set superseded pl9999 --yes` behaved identically.
Stubbing ONLY `_offer_self_commit` leaves the clean `R100`, isolating the cause to the reset. This is
the precise shape of backlog `y39i16` (`done`), whose record documents one such leftover deletion
refusing 27 of 42 items in `run-20260913T031350Z-1732436`. It is NOT introduced by this plan and it
affects `plans`, `prompts` and `backlog` today; what would be wrong is adopting the path for a fourth
type while saying nothing. `offer_commit` already handles a renamed source correctly (`_in_index`,
`git_commit_helper.py:333-347`) and `ipd_lifecycle` finalize already passes both halves (`:3795`), so
the defect is at this caller and the fix is known.

THIRD, THE MIGRATION DISPATCHES BEFORE THIS PLAN TODAY, AND THE PLAN RECORDED THAT AS PROSE RATHER
THAN AS A BLOCKING QUESTION (PR-001). The plan says the `1bdxcp` edge "must be made before the Set
runs". A runner cannot read that sentence. I ran the runner's OWN scheduler
(`oc_runipd.simulate_dispatch_order`, composing `queue_sort_key` and `dependency_depth`) over the
Set's five items as their `- Item-Dependencies:` fields actually stand: the order is
`['y4bdoz','1bdxcp','r9uvwc','ingpvc','wfjsp4']`, and adding `executed:r9uvwc` to `1bdxcp` makes it
`['y4bdoz','r9uvwc','1bdxcp','ingpvc','wfjsp4']`. Both children are depth 1, so the Order digit
decides and `02` beats `03`. So `aw oc run specdirs` TODAY migrates 36 specs while the writers still
strand them. The runner is behaving exactly as specified. Only a human can fix it, because `1bdxcp` is
`approved` and this plan must not edit an approved sibling, so this is escalated as OQ-03
`- Blocking: yes` and is the sole reason for the `no-go`.

FOURTH, THE PLAN'S OWN F-10 IS HALF-FALSE AND E-06 WOULD HAVE RECORDED A FALSE CLAIM (PR-004). F-10
and E-06 both assert `attention.disposition-mismatch` was "measured DEAD in the `.aw` layout". The
SCOPING half is true (`attention_contract.py:688` reads `# plans dir vs terminal status` and
`attention.py:1141-1145` gates on `plans_mod.DIR_TERMINAL`, so specs stay uncovered). The DEAD half
is false at HEAD: `attcor rkn8ya` E-05 replaced the legacy prefix test with
`_plan_disposition_from_rel` (`attention.py:1094-1113`), which recognizes BOTH layouts and derives the
disposition from the first path component so a sharded plan still resolves. MEASURED: an `.aw`-layout
plan at `executed/202601/` carrying `- Status: superseded` emitted `attention.disposition-mismatch`
and `aw attention --check` exited 1. Backlog `4r91r1` is nonetheless still `- Status: open`, so what
is open is the RECORD, not the defect. E-06's deliverable is a RECORD, so shipping it with a false
premise would have written a false claim into permanent history, which is why a stale citation is a
real finding here rather than a nitpick.

WHAT I CHECKED AND FOUND SOUND, recorded so the absence of a finding is not read as an absence of
review. The plan's E-01 requirement that writer 2 be proven through a legally-transitionable fixture
is correct and necessary: I confirmed `specs.run_set`'s gates fire before placement
(`transition_allowed` at `specs.py:570`, the `review_record` attestation at `:679`, and
`TRANSITION_AUTHORITY` carrying `->reviewed` with `review_record: True`), and confirmed the legal
transition graph so a fixture is constructible (`draft -> to-review`, `to-review -> reviewed` with a
`.review.md` carrying `- Subject-Id:`/`- Subject-Type: spec`). Its instruction not to weaken a gate to
make a fixture easy is the right call. The plan's refusal to write a `- Readiness:` field is correct
and I did not treat the absence as an omission. Its `Carrier-Declined:` rows are individually
defensible and each names a real owner or a real prohibition. Its deferrals all point at live
artifacts I verified. The suite-baseline instruction (judge on the failing NODE ID delta, measure your
own baseline, do not delete another party's untracked directory) is correct and materially better than
the parent's, whose cited baseline the plan correctly calls wrong.

THE SUITE WAS NOT RUN IN THIS REVIEW, deliberately and disclosed: this review changed no code, only a
planning document and a review record, so there is no code result to report. The plan's own V-04
mandates the delta measurement at execution.

`aw check` WAS RUN BEFORE AND AFTER, and the delta is ONE finding, which is correct propagation rather
than damage. Baseline 364 findings, after 365, and the single new row is
`check.ipd-dependency-findings-blocked` at `20260920-specdirs-04-ingpvc-...ipd.md`. That is the
designed consequence of this review: `ingpvc` declares `- Item-Dependencies: ... executed:r9uvwc`, and
`_findings_blocks_for` delegates to the same `review_findings.subject_gating_blocks` predicate that
now reports this record's unresolved `PR-001`. So the Set's verification child correctly reports that
one of its prerequisites carries a recorded gating finding, and the row disappears when OQ-03 is
answered and `PR-001` is cleared in a later round. Nothing GONE from the baseline. No other rule
changed, and in particular `check.review-finding-unescalated` does not fire, because `PR-001` is
escalated into the plan as OQ-03 carrying its `- Finding:` back-reference; verified directly:
`subject_gating_blocks` returns the single `PR-001` block and `stale_escalated_findings` returns empty
(the question is open, so the finding is correctly NOT stale).

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/status_set.py`
(`apply_status_change` dest block `:1036-1078`, the `git mv` comment `:1116-1154`, `touched_paths`
`:1742-1760`, `_offer_self_commit` `:1366-1429`), `agent_workflows/specs.py` (`run_set` `:546`, gates
`:570`/`:664`/`:679`, `run_new` `:982`, flat-root dest `:1024`, `_offer_specs_set_commit` `:734`),
`agent_workflows/git_commit_helper.py` (`_staged_paths` `:324`, `_in_index` `:333-347`, `offer_commit`
`:407-647`), `agent_workflows/artifact_core.py` (`git_mv` `:358-370`),
`agent_workflows/ipd_lifecycle.py:3735-3805`, `agent_workflows/layout.py` (`RecordClassDefinition`
`:120-142`, record classes `:145-230`), `agent_workflows/attention_contract.py` (`SPEC_STATUSES`
`:269`, `TRANSITION_AUTHORITY` `:486`, `SPEC_TRANSITIONS`/`transition_allowed` `:536`, rule list
`:688`), `agent_workflows/attention.py` (`_plan_disposition_from_rel` `:1094-1113`, the mismatch check
`:1133-1152`), `agent_workflows/check_engine.py` (`_plan_disposition` `:1979-1998`,
`load_emitted_layout` `:2150`, `check_system_layout` `:2182`), `agent_workflows/plans.py`
(`PRE_TERMINAL`/`TERMINAL` `:25-27`, `DISPOSITION_DIRS` `:31`, `DIR_TERMINAL` `:39`,
`_resolve_area_dir` `:148-164`), `agent_workflows/plans_archive.py:44-75`,
`agent_workflows/backlog.py:78-79`, `agent_workflows/oc_runipd.py` (`dependency_depth` `:4246`,
`queue_sort_key` `:4281`, `simulate_dispatch_order` `:4330`), `tests/test_layout.py:182-192`, spec
`kw5y2s` (`:104`, `:190-211`, `:253-262`, `:359`), plans `wfjsp4`, `y4bdoz`, `1bdxcp`, `ingpvc`,
backlog `y39i16`, `4r91r1`, `uwerb5`, `sv0sf3`, `qzhfk2`, `mqmlug`, and `.aw/config/project.json`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | C. Architecture / G. Executability | `oc_runipd.py:4246,4281,4330`; `1bdxcp:13` | THE MIGRATION DISPATCHES BEFORE THIS PLAN TODAY. Measured with the runner's own scheduler: as the Set's fields actually stand, `simulate_dispatch_order` returns `['y4bdoz','1bdxcp','r9uvwc','ingpvc','wfjsp4']`; with `executed:r9uvwc` added to `1bdxcp` it returns `['y4bdoz','r9uvwc','1bdxcp','ingpvc','wfjsp4']`. Both children are depth 1, so the Order digit decides and `02` beats `03`. The plan recorded this as prose ("must be made before the Set runs"), which a runner cannot read and which therefore gates nothing. Consequence: `aw oc run specdirs` migrates 36 specs while the writers still strand them. | C:Low; U:Low; S:Low; F:High; Overall:High | OPEN | ESCALATED as OQ-03 with `- Blocking: yes` and `- Finding: PR-001`, carrying the measured simulation, three options ((a) maintainer adds the edge to the approved sibling, (b) run the Set by hand in the documented order, (c) run only the first two children now) and a recommendation of (a). Also recorded as F-14 and quantified in the gate's sequencing paragraph. Cannot be fixed in-plan: the remedy is a field edit on an `approved` sibling, which only a human may make. |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness / D. Invariants | `status_set.py:1056-1067`; `plans_archive.py:59-62`; `check_engine.py:1979-1998`; `attention.py:1094-1113` | THE BRANCH THE LIBRARY REPLACES IS SHARD-UNSAFE, a second wrong shape the plan never named. It tests `path.parent.name` against the disposition tuple; a sharded terminal plan's parent is `YYYYMM`, so the test misses and the `else` rebuilds the destination at the disposition ROOT. MEASURED: `executed/202601/...pl1234...` set to `superseded` landed at `superseded/...`, silently un-sharding it. Three other modules already derive this from the first path component and each comments that `parent.name` breaks on shards. A library that copies the branch inherits the bug across four types. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now names the shard-unsafety as a distinct shape from the many-to-one mapping, pastes the measurement, directs reuse of one of the three existing derivations rather than a fourth hand-written `split("/")`, and requires the executor to DECIDE and STATE whether a status change preserves an existing shard. V-02 now requires a sharded-plan test and requires the pinned behavior to be named; an unasserted answer does not satisfy it. |
| PR-003 | HIGH | UNDER-SCOPE | A. Correctness / E. Testing | `status_set.py:1755-1760,:1390`; `git_commit_helper.py:333-347`; `ipd_lifecycle.py:3795`; backlog `y39i16` | THE `git mv` RENAME IS DECOMPOSED BEFORE THE COMMIT, a live regression of the fix this plan's E-03 relies on. `touched_paths` records only `dest_path`; `_offer_self_commit` then runs `git reset -- <dest>`, unstaging one half of the staged rename. MEASURED END TO END: `aw backlog set graduated --yes` committed `A graduated/...` ALONE and left `D open/...` staged-but-uncommitted; `aw ipd set superseded --yes` did the same; stubbing only `_offer_self_commit` leaves the clean `R100`. One such leftover deletion refused 27 of 42 items in `run-20260913T031350Z-1732436`. Pre-existing and affecting plans/prompts/backlog today, so adopting the path for specs silently extends it to a fourth type. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 now carries the measurement, requires the library to return BOTH paths for a relocation and `touched_paths` to record both, cites the already-correct `_in_index` and finalize precedents, forbids `--no-verify` and gate weakening, and permits FILING it as a `Work-Kind: bug` item instead if fixing in place would over-widen the plan, on condition that V-03 cites the item. V-03 now refuses a `porcelain` `R` measured before the self-commit and demands `git show --name-status -M <sha>` showing both halves plus a clean tree afterwards. Also raised as non-blocking OQ-04 so the maintainer may choose bundling. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest docs | `attention.py:1094-1113,1141-1145`; `attention_contract.py:688`; backlog `4r91r1` | THE PLAN'S OWN F-10 AND E-06 ASSERT A FALSE PREMISE. Both say `attention.disposition-mismatch` was measured DEAD in the `.aw` layout. The SCOPING half is true; the DEAD half is false at HEAD, because `attcor rkn8ya` E-05 replaced the legacy prefix test with `_plan_disposition_from_rel`. MEASURED: an `.aw`-layout plan at `executed/202601/` with `- Status: superseded` emitted the rule and `aw attention --check` exited 1. `4r91r1` is still `open`, so the RECORD is open while the code is fixed. E-06's deliverable IS a record, so it would have written a false claim into permanent history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-11 correcting F-10. E-06 rewritten: it must NOT report the check as dead, must cite the `plans_mod.DIR_TERMINAL` gate as the real scoping reason, must re-measure `4r91r1` at execution and state the code-fixed-but-record-open asymmetry, and must not close another plan's item. V-06 now explicitly refuses a transcript repeating the "dead in the `.aw` layout" wording. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Executability | plan's `## Approval and execution gate` | THE GATE WAS MISSING THREE OF THE FIVE REQUIRED EXECUTION-CONTRACT ELEMENTS. It carried path-scoped commit and never-push, and a finalize instruction, but had NO scope fence, NO explicit paste-the-actual-output honesty rule, and its finalize instruction was UNCONDITIONAL ("move this plan ... through `aw ipd finalize`"), which is wrong under a runner that owns the transition itself. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate extended with a scope fence written as a DECLARATION (make the edit, then justify it via `--scope-reason`/`--scope-ack`) and explicitly NOT a stop order, with the two genuinely-unsafe stop conditions named separately; an explicit hard-MUST honesty rule naming V-04; and a lifecycle-transition paragraph with an unconditional finalize OBLIGATION and conditional runner/executor OWNERSHIP. |
| PR-006 | LOW | IN-SCOPE | A. Correctness | `specs.py:1024`; findings table header | TWO CITATIONS HAVE DRIFTED SINCE `41f6a45b`, which the plan anticipates in F-04 but does not date its own table for: `specs.run_new`'s flat-root write is now `:1024` (plan says `:976`) and the `status_set` dest block is now `:1036-1078` (plan says `:1027-1069`). The findings table claimed a single measurement HEAD for rows the review then added at a different HEAD. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The findings table now states which rows were measured at which HEAD (F-01..F-10 at `41f6a45b`, F-11..F-14 at `803d10f6`) and records that only F-10's "dead check" half was found false. Line numbers left as authored deliberately: the plan already instructs verification by symbol rather than by line, and rewriting them each review is churn. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `1bdxcp` dependency gap: fix it myself by editing the sibling, or ask? | ASK. Escalated as blocking OQ-03 with the measured simulation, three options and a recommendation. | Editing `1bdxcp`'s `- Item-Dependencies:` myself, rejected because it is `approved` and the repository forbids adding to another plan's approved file; also rejected: leaving it as the plan's prose, which measurably gates nothing. | `1bdxcp:14` is `- Status: approved`; AGENTS.md forbids in-place edits to an approved sibling; `simulate_dispatch_order` proves the consequence. Workflow rule: never guess a human decision. | yes |
| D-2 | Is the shard-unsafety mine to fix in this plan, or a separate item? | Neither decided FOR the executor: E-02 must reuse an existing derivation and must DECIDE and STATE the shard-preservation behavior, with V-02 requiring a test either way. | Picking shard-preserving myself, rejected because it is a behavior choice with a real user-visible consequence (an archival decision either survives a status change or does not) and the repository has no recorded ruling; filing it separately, rejected because the library is BEING written here and would otherwise be born with the bug. | `plans_archive.py:59-62` defines the shard; the three existing derivations each comment that `parent.name` breaks on it; measured un-sharding in a throwaway repo. | yes |
| D-3 | The self-commit rename decomposition: require the fix here, or allow filing it? | ALLOW EITHER, with an obligation that cannot vanish: E-03 permits filing a `Work-Kind: bug` item if fixing in place would over-widen the plan, but V-03 then requires the item's id6 be cited. Also raised as non-blocking OQ-04 so the maintainer may prefer bundling. | Mandating the fix here, rejected because the self-commit path is shared by every `set` verb and its blast radius exceeds this plan's, making a library change and a commit-staging change one diff; saying nothing, rejected outright since adopting a defective path for a fourth type silently is the worse outcome. | Measured end to end on two verbs; `y39i16` documents the identical shape and its 27-of-42 cost; `git_commit_helper._in_index` and `ipd_lifecycle.py:3795` show the fix is known and small. | yes |
| D-4 | F-10's "dead check" claim: correct it, or leave the executor to discover it? | Correct it, as F-11, and rewrite E-06/V-06 to forbid the stale wording. | Leaving it, rejected because E-06's deliverable IS a record, so an unchallenged false premise becomes a false claim in permanent history rather than a wasted turn. | `attention.py:1094-1113` shows the fix; measured firing on an `.aw`-layout sharded plan; `4r91r1` still `open`. | yes |
| D-5 | Is the plan's over-scope (replacing working plans/prompts/backlog code) a finding? | No. It is a recorded maintainer ruling and is correctly justified in the plan's own scope check. | Flagging it OVER-SCOPE, rejected because `wfjsp4` OQ-04 explicitly requires it and dismissing a recorded ruling would be the larger error. | `wfjsp4` OQ-04, `- Status: resolved`, owner maintainer, quoted verbatim in the plan and verified in the parent. | yes |
| D-6 | Is the plan too large under the right-sizing rule? | No REPLAN and no split. Its `Size assessment: exception` stands. | Splitting E-05/E-06 into their own Order, which the plan itself offers as the honest split, rejected because OQ-05 requires the spec amendment to land WITH the code and the two enforcement items are small; splitting E-02 from E-03, rejected for the reason the plan gives (a module nothing calls). | OQ-05's ruling declined amend-first and ship-the-contradiction; `aw ipd lint` size thresholds pass; each E-item names one concern. | yes |
| D-7 | Did the gate's missing elements warrant a finding, or a silent repair? | A finding (PR-005) AND an in-place repair, per the workflow's Step 4 instruction to add the element and record it. | Silently adding them, rejected because the workflow requires it recorded; refusing the plan over it, rejected as disproportionate for a mechanical gap. | plan-review Step 4 and rubric G; the 2026-09-01 scope-fence ruling on declaration-not-stop wording. | yes |
| D-8 | Is the approach sound overall? | Sound. The `no-go` rests on OQ-03 alone, not on plan quality. | REPLAN, rejected because every figure reproduced, the defect is real and current, the shape is a maintainer ruling, and all four review findings are instruction-level repairs or a question. | The whole measurement pass above. | yes |

PR-001 is the only finding not FIXED. It is `BLOCKER`, at or above the repository's gate threshold, and
it is therefore ESCALATED into the plan as OQ-03 carrying `- Blocking: yes` and `- Finding: PR-001`, so
`aw ipd lint` refuses the plan at every checkpoint until a human answers. It is NOT a defect in this
plan's own content: this plan is safe to run in isolation, and the refusal exists to stop the SET
running in an order that would waste the migration. No `Reversible: no` decision was made in this
round.
