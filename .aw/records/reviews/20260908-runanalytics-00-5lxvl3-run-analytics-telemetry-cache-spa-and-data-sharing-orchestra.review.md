# Review: run analytics, telemetry, cache, SPA, and data-sharing orchestration (orchestrator 5lxvl3, Set runanalytics)

- Subject-Id: 5lxvl3
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `5699c6ad`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions. The
Set was authored by a different agent (Codex) and delivered through `.aw/inbox/`, so its claims were
treated as untrusted external input and re-measured rather than accepted.

SCOPE OF THE LEDGER. The invocation named ONE plan, the Order-0 orchestrator. The ten children were
read in full as evidence (an orchestrator cannot be judged without them) but were NOT edited and are
NOT ledger candidates; findings that belong to a child are recorded here and bound on the child from
the parent's coordination sections, which is the orchestrator's own instrument. Mid-review I did
briefly unescape backticks across all eleven files, then reverted the ten children with
`git checkout --` before committing anything; only the orchestrator is modified.

METHOD. The Set makes claims about what specific code does, about the local run corpus, and about what
is already implemented, so each class was measured independently rather than reasoned about: the three
run enumerators and the `aw runs` dispatcher were read and exercised at HEAD; the 135-run corpus was
parsed for driver lineage and forbidden-value content; the worker path-fence predicate was called
directly; E-item density was counted across the whole pending and executed plan corpus for a baseline.

WHAT THE SET GETS RIGHT, and it is substantial. The ten-child decomposition is sound and the ownership
boundaries are real: storage before cache before telemetry before runner integration before ingestion
before analysis before presentation before agent access before sharing before closeout is a coherent
dependency chain, and every declared child row resolves to an authored plan on disk
(`find_unauthored_child_rows` returns `((), True)`), so this Set cannot hit the `unauthored-child-rows`
retirement refusal that `rununify` is stuck in. The privacy posture is the best part: an allowlist
projection rather than a denylist, an explicit refusal to claim anonymity, submission gated as a
separate command that is unavailable until an endpoint policy is approved, and an explicit prohibition
on correlation-as-causation. Order 09's tier table and Order 06's refusal to run ANOVA without checking
assumptions are exactly the right instincts. The prompt's requirement that findings propose experiments
rather than change behavior is carried faithfully.

THE MOST CONSEQUENTIAL CORRECTION IS THAT THE CORPUS IS NOT WHAT FOUR PLANS SAY IT IS. Orders 01, 05,
06 and 10 each assert there is "no live run corpus in this checkout". There are 135 run directories,
all with `state.json`, `events.jsonl` and `sessions/`. More importantly the corpus is SINGLE-HOST:
120 runs name `agent_workflows/oc_runipd.py`, 13 name the legacy `tools/ipdrunner/runipd.py`, 2 name
`tools/ipdrunner/ipdrunner.py`, and ZERO name `agy_runipd.py`. That matters in two directions the plans
do not address. Agy parity (Order 04) and cross-host fixtures (Order 10) have no observed Agy artifact
to normalize against, so that evidence is necessarily synthetic and must not be reported as corpus
validation; and the two legacy driver generations are the REAL historical schema drift in this repo,
unnamed anywhere in the Set, which means Order 10's scenario 3 ("mixed-runner corpus") would be
satisfied entirely by OpenCode-lineage runs while the actual variance went untested.

THE PRIVACY BOUNDARY IS TIGHTER THAN THE PLANS REALIZE, in the sense that the canary is already inside
the first field an ingester touches. Every one of the last 20 `state.json` files carries an absolute
maintainer home path in BOTH `repo` and `driver.path`. So the forbidden-value case is not an edge case
to be seeded into a fixture; it is the default content of the primary source. Proving the boundary with
author-written canaries alone is circular (the same agent writes the allowlist and the canary list), so
the parent now requires real-artifact scanning too, and requires that scan to CONSUME the repo's
existing `aw sanitize --agent` engine rather than grow a second detector in `run_analytics_*`, per P11
and P8. Relatedly, `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` already contains `.aw/records/runs/`,
so `path_is_worker_forbidden('.aw/records/runs/analytics/index.html')` is True today and a worker lane
cannot write analytics; recorded so that no child "fixes" that by weakening the fence.

THE ONE PLACE A CHILD'S REQUIREMENT WAS UNDER-SPECIFIED RATHER THAN WRONG is Order 01's exclusion. The
scan half is already satisfied by accident: `discover_run_dirs` matches `run-`-prefixed children at one
level, so a nested `analytics/snapshots/run-*` is skipped, and name/substring targeting finds nothing.
But `resolve_target_runs` handed the explicit PATH of such a directory RETURNS IT as a run, because that
branch tests only `is_dir()` and the presence of `state.json` with no containment check. So the work
Order 01 owes is precisely a containment test on the explicit-target and file-target branches. And there
is a THIRD enumerator it does not declare: `completion.run_id_candidates` lists every non-dot child of
the runs root and will offer `analytics` as a shell-completion candidate the moment the directory
exists (verified). It is absent from Order 01's `Scope-Paths`.

WHAT I DID NOT FLAG, deliberately, because the runners already settle it: file overlap between plans,
queue ordering, and this Order-0 parent's presence in the queue. Each execute item gets an isolated
worktree by default (`isolate_worktree` default True at `oc_runipd.py:3063`), the queue sorts on
dependency depth first, and dependencies are re-checked at dispatch. The parent now says so, so a later
reader does not re-raise it. The genuinely real contention note is that fourteen other pending plans
declare one of the two runner modules in their own `Scope-Paths`, which Order 04 will meet.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G. Plan executability / lifecycle | `20260908-runanalytics-00-5lxvl3-...ipd.md:18-19` (pre-fix) | The `## Workflow history` was ordered OLDEST-FIRST, contradicting the newest-first contract (`.aw/records/plans/README.md:53-60`). Consequence is mechanical, not cosmetic: `ipd_lifecycle._plan_status_events` reverses the section to derive the transition stream, so it read `to-review -> draft` and `validate_transition` refused it as a backwards transition; `aw check plans` reports `check.lifecycle-transition-invalid` for this plan. `plan_readiness.extract_newest_history_entry` also took the wrong record as "newest", which is the input the back-compat approval fallback reads. All eleven plans in the Set share the defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered newest-first. Re-verified: events now `draft -> to-review -> reviewed`, every transition `ok=True`. The ten children still carry it and are outside this ledger. |
| PR-002 | HIGH | UNDER-SCOPE | G. Right-sizing and conceptual density | all eleven plans' checklists; corpus count across `.aw/records/plans/**` | Every child carries EXACTLY THREE E-items (31 across the Set) while the house corpus ranges 3 to 9 for pending children (median 6) and reaches 14 executed. Uniformity at the minimum indicates granularity chosen to fit a template, not derived from the work, and the count-based lint fires only above 18 leaves so it passes by construction. Four items each bundle multiple independent deliverables and test surfaces: Order 07 E-02 (the entire SPA: filters, toggles, charts, tables, findings, pricing, quality, raw-data), Order 09 (three distinct trust surfaces in three items: local tiers, network transport, interactive consent), Order 06 E-02 (pricing joined to all statistics), Order 10 E-03 (33-scenario matrix + performance + sanitizer + offline + suite + lint + diff). The tail of exactly these items is where the privacy, offline and packaging proofs sit. | C:Medium; U:Low; S:Medium; F:Medium-High; Overall:Medium-High | OPEN | Escalated as OQ-01 (`Blocking: yes`, owner maintainer) with three options and a recommendation of (b), re-cut Orders 06/07/09/10 within existing child boundaries. Not applied unilaterally: re-cutting four children rewrites another agent's Set and changes what a human would approve. |
| PR-003 | HIGH | IN-SCOPE | G. Plan executability / execution contract | gate section (pre-fix), lines 137-142 | The `Approval and execution gate` carried NO execution contract: no scope fence, no paste-the-actual-runner-output honesty rule, no path-scoped-commit / never-push clause, and no lifecycle-move instruction. The repo requires all five in every IPD's gate (`.aw/records/plans/README.md:98-136`). A plan handed to an agent from its path alone would have had no commit discipline and no honesty rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all five, with the fence worded as a DECLARATION (make the edit and justify at finalize) and explicitly NOT a stop directive, per the 2026-09-01 maintainer ruling. |
| PR-004 | HIGH | IN-SCOPE | A. Correctness / scope declaration | `- Scope-Paths:` (pre-fix) | `Scope-Paths` enumerated all ten child plan FILES. Every one is already implicitly in scope (`ipd_schema.scope_paths_implicit_allowances()` covers `.aw/records/plans/**`; verified `_is_implicitly_allowed` returns True for a sibling child), so the declaration adds nothing but makes ten paths declared-but-unmodified, and `aw ipd finalize` refuses to complete without a `--scope-ack` per such path. The executor would have been forced to acknowledge ten paths it was correctly told not to edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `.aw/records/plans/pending`, matching the in-repo orchestrator precedent (`cczotj`, `3m0urk`). Verified `_scope_match` satisfies it on the plan's own move, so no spurious ack. |
| PR-005 | HIGH | UNDER-SCOPE | D. Domain invariants / evidence | 135 `state.json` files parsed at review | Four plans assert "no live run corpus in this checkout"; FALSE (135 runs). The load-bearing part is that the corpus holds ZERO Agy runs (120 `oc_runipd.py`, 13 legacy `runipd.py`, 2 `ipdrunner.py`), so Agy parity and cross-host evidence are necessarily synthetic and must not be labeled corpus validation, and the two legacy driver generations are unnamed real schema drift that Order 10's "mixed-runner corpus" scenario would miss. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Completion criterion corrected with the measured counts and two explicit obligations; legacy generations added to the parent's required-tests list as their own ingestion scenarios; Agy evidence required to be labeled synthetic. |
| PR-006 | HIGH | UNDER-SCOPE | B. Security and privacy | `state.json` `repo` + `driver.path` in all of the last 20 runs | The forbidden-value canary is the DEFAULT content of the primary source: every recent `state.json` carries an absolute maintainer home path in two fields. Proving the boundary with author-seeded canaries alone is circular. Separately, the Set implies a new sanitizer inside `run_analytics_*`, duplicating the repo's deterministic leak-sanitizer (P11 delegate-to-script, P8 single source of truth). | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Criterion now requires real-artifact scanning alongside planted canaries and requires the scan to consume `aw sanitize --agent` rather than reimplement detection. Also recorded that the analytics tree is already worker-forbidden so no child weakens `path_is_worker_forbidden`. |
| PR-007 | MEDIUM | UNDER-SCOPE | C. Architecture / reuse | `run_viewer.py:1077-1092`, `:1113-1129`; `completion.py:448-460`; all exercised at review | Order 01's exclusion requirement did not distinguish which half is missing. Measured: the directory scan already skips a nested `analytics/snapshots/run-*`, and name/substring targeting finds nothing, but `resolve_target_runs` given the explicit PATH RETURNS it as a run (no containment check on that branch). And `completion.run_id_candidates` is an undeclared THIRD enumerator that will offer `analytics` as a completion candidate once the directory exists. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Criterion now names the explicit-target/file-target branches as the specific work, confirms the adversarial `run-*` case is real, and requires `completion.py` be added to Order 01's `Scope-Paths` or explicitly deferred with a reason. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. Specification synchronization | spec `25kzda` lines 142-144 (`- Status: approved`) | Order 08 states its spec obligation CONDITIONALLY ("if the repository maintains a controlling CLI grammar spec"). It does: spec `25kzda` enumerates the `aw runs` leaves, so adding `analyze`/`query` amends a table an approved spec fixes. Neither Order 08 nor Order 09 declares that spec in `Scope-Paths`, though Order 04 correctly does, so the runners' pre-run spec-impact announcement would not name it and the finalize scope gate would not reconcile it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Cross-IPD validation row now names the spec and its exact lines and requires Orders 08 and 09 to declare it in their own `Scope-Paths`. |
| PR-009 | MEDIUM | IN-SCOPE | E. Testing and verification / F. UX | V-01 (pre-fix); E-01 (pre-fix); 16 escaped backticks | Three separate weaknesses in the parent's own instrument. V-01 restated the completion criteria instead of demanding pasted evidence, so it could be marked pass by assertion. E-01 said "execute children" without forbidding the parent from performing a child's work, which is the exact failure the rollup's skipped E/V checkpoint cannot catch. And 16 `\`` sequences rendered as literal backslash-backtick. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands four specific pasted artifacts including `git diff --stat` proving the parent touched no source file, and states that re-asserting Set behavior here is a FAILED validation. E-01 rewritten with the do-not-perform-a-child's-work prohibition and the rollup rationale. Backticks unescaped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review re-cut the four over-dense children's checklists itself, or escalate to the maintainer? | Escalate as OQ-01 with a recommendation of option (b), and leave the children unedited. | (a) Re-cut Orders 06/07/09/10 in place under "fix by default"; (c) mark the Set REPLAN. | The Fix Bar defers when Remediation Risk is Medium-High, and re-cutting four children is exactly that on functionality: it rewrites another agent's authored Set, invalidates the E/V bijection a human may already have read, and risks losing requirement coverage the current items do carry. `plan-review.md:214-229` also confines edits to bounded surgical revisions and forbids inventing decisions that require the human. REPLAN was rejected because the decomposition itself is sound (`plan-review.md:527-530` reserves REPLAN for an unsound approach). | yes |
| D-2 | The ledger names only the orchestrator, but eight findings are really about child plans. Fix them in the children, or bind them from the parent? | Record them here and bind each on the children through the parent's Completion criteria, Cross-IPD validation, and required-tests sections. | Edit all ten children (exceeds the named scope, and `plan-review.md:50-52` forbids adding non-candidates to the ledger); or report them as prose only, where nothing enforces them. | `plan-review.md:224-226`: fix a cross-plan finding in the OWNING plan and cross-reference from dependents. The orchestrator's coordination sections ARE its enforcement instrument over children, and Order 10's closeout reads them, so a criterion written here is binding rather than advisory. | yes |
| D-3 | Is "no live run corpus in this checkout" a harmless authoring slip or a finding? | A finding (PR-005), because the corrected fact changes required work rather than merely a sentence. | Silently correct the wording in the parent. | The measurement (zero Agy runs of 135; two legacy driver generations) means Agy parity evidence cannot be corpus-validated and that real schema drift is untested. Correcting only the prose would leave both obligations unstated. | yes |
| D-4 | Should the parent's Scope-Paths be `.aw/records/plans/pending` or the `none` sentinel that `yeh7gc` uses? | `.aw/records/plans/pending`. | `none` (as `orchprobe`'s parent declares). | Verified both against `ipd_lifecycle._scope_match`: `none` matches nothing, so the plan's own lifecycle move leaves `none` declared-but-unmodified and finalize demands a `--scope-ack` for it. `.aw/records/plans/pending` matches the plan's own path and needs no ack. The majority in-repo precedent (`cczotj`, `3m0urk`) agrees. | yes |

No `Reversible: no` decision was taken in this round.
