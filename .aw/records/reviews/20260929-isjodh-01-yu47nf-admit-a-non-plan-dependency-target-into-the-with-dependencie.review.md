# Review findings: plan yu47nf

- Subject-Id: yu47nf
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `610ab688` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after
revision (exit 0, `findings: 0`). `IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads
`child`. No pre-review snapshot was owed: the plan was committed and unmodified, `git status --short` empty
at review start. Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 59.78s`.
`tests/test_typed_queue_entries.py` alone: `11 passed`. `aw sanitize --agent`: `outcome: clean`, exit 0.

NO PRODUCTION FILE OR TEST WAS MODIFIED BY THIS REVIEW. Every measurement was a read, an in-process
probe, or a driven `initialize_run` against purpose-built fixture repositories under a gitignored `tmp/`
path, removed afterwards (`git status --short` empty again before commit).

THIS PLAN'S CENTRAL WORK IS EXCELLENT AND I DROVE EVERY LOAD-BEARING CLAIM THROUGH THE REAL RUNNER ON
BOTH HOSTS rather than reading for plausibility. All five defect claims reproduce, as do the four
"obstacle already closed" claims and the coverage claim:

- F-01 reproduces on BOTH hosts with the exact message: `ClosureRefusal: state:spec:reviewed:spctor:
  --with-dependencies cannot enqueue a spec target.`
- **F-07 reproduces and is the cleanest demonstration of the defect.** With a plan whose `exists:spec:spcapp`
  edge is ALREADY SATISFIED, `oc` and `agy` each froze `queue=[('pln001','ipd','review')]` BARE at exit 0,
  and each raised `ClosureRefusal` with `--with-dependencies`. A flag whose own help says it "Changes
  selection only" turns a working invocation into a failing one.
- **F-08 reproduces across all three advertised routes on both hosts.** Bare: `[RUN-DEPENDENCY-UNSATISFIABLE]`.
  Adding the spec to the selection (`--allow-mixed`): SAME finding, which is F-05 biting. `--with-dependencies
  --allow-mixed`: `ClosureRefusal`. So the refusal's own recovery text ("Add it to the selection or run with
  --with-dependencies") names two remedies and both refuse.
- **F-05 reproduces by code reading and by the live measurement above.** `enforce_freeze_time_refusal`'s
  `elif edge.kind in ("exists", "state")` branch reads the target status and composes a `why` but assigns
  `could_be_met` NOWHERE, unlike its `executed:` sibling which credits an in-queue target in both the
  review-consumer and execute-consumer arms.
- **F-06 reproduces for all three non-plan edge kinds against a correct IPD control.** With 6-char ids:
  `state:backlog:graduated:tgt001` gave depths `0,0` and `queue_sort_key` order `['pln001','tgt001']`
  (dependent FIRST); `exists:spec:tgt001` and `state:spec:reviewed:tgt001` likewise. The IPD control
  `executed:tgt001` gave depths `1,0` and order `['tgt001','pln001']`. The guard is
  `edge is None or edge.target_type != "ipd" or edge.id6 not in by_id`.
- F-02 confirms: `lookup_manifest_artifact` checks plans, then specs, then backlog, populating lazily via
  `populate_manifest_specs`/`populate_manifest_backlog`, and raises `DriverError`.
- F-03 confirms: the call site is `enforce_mixed_type_gate(repo, list(selection.all_paths), ...)`, so the
  gate sees non-plan paths. The mixed gate fired on my fixture (`Mixed work-item selection: IPDs: 1, Specs: 1`).
- F-04 confirms: the queue loop's statement is `atype, item_info = lookup_manifest_artifact(manifest, repo, id6)`.
- F-09 confirms exactly: `action_for_status` returned `plan` for `backlog/open`, `review` for `spec/to-review`,
  `plan` for `spec/approved`, `skip` for `backlog/graduated`, and `_SPEC_ACTIONS` has no row producing
  `approved`. So `add` genuinely cannot be unconditional, which is why E-02 derives the action.
- F-10 confirms: zero hits across `tests/` for `closure_target_admission`, `expand_dependency_closure`,
  `ClosureRefusal`, `CLOSURE_TERMINAL_BUCKETS`. `git show 19313eed --stat` shows
  `tests/test_run_flag_surface.py | 4863 -----`, and extracting `DependencyClosureTests` from the parent
  commit yields EXACTLY ELEVEN test methods, matching the plan's count.
- F-13 confirms: the walk pushes an admitted id onto `frontier`, then `resolve_plan_path` raises
  `DriverError` and `continue`s, so a non-plan node's own edges are never read.
- The spec claims confirm: the "Any newly introduced type" sentence is in Section 2.1 (line 224 at review
  HEAD); line 166 is the `prompt`-verb sentence; rule 4 lists type rank among "simultaneously ready
  independent nodes" and rule 5 already says "Explicit declared dependencies always win", so E-07's
  amendment makes rule 4 agree with rule 5 rather than changing the contract.
- All nine regression files named in Required tests exist.

SEVEN FINDINGS WERE RAISED AND ALL SEVEN FIXED IN PLACE. One is HIGH because it concerns another
approval-ready plan's validation item, and three would each have cost the executor a false measurement
or a failed self-check.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | Rubric C (architecture); G (sequencing) | plan F-14 as authored ("No file overlap with the one live sibling"); `.aw/records/plans/pending/20260929-ghff0p-01-kqb9ok-...ipd.md` `- Scope-Paths:`, `- Status: reviewed`, `- Readiness: go-pending-approval`, its E-04 and V-04 | F-14 understated a live collision in a way that matters. `kqb9ok` is ALSO approval-ready, overlaps this plan on TWO of its three declared paths (`runner_shared.py`, `tests/test_typed_queue_entries.py`), rewrites the SAME three `:166`-citing comments E-07 rewrites, and its V-04 requires evidence that "`closure_target_admission`'s refusal still states its two surviving reasons". THIS PLAN'S E-02 DELETES THAT REFUSAL, so if `yu47nf` lands first, `kqb9ok`'s V-04 is unsatisfiable as written. Neither plan declares an `- Item-Dependencies:` edge on the other, so the runner may dispatch them in either order and dependency depth cannot separate them. F-14 characterized this as a shared stale comment where "whichever lands second must reconcile", which understates a conflict that reaches a validation item rather than only prose. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | F-14 rewritten to state the overlap, the affected validation item, and both plans' readiness. Added OQ-03 (resolved) recording the ASYMMETRIC obligation: if `kqb9ok` lands first, E-07 must re-read both sites rather than pattern-match F-15's quoted strings; if this plan lands first, its executor must REPORT that `kqb9ok`'s V-04 has become unsatisfiable so its owner can re-scope. Added a fifth scope-fence constraint forbidding any edit to another plan's record. Deliberately NOT resolved with a dependency edge: the production behaviors are disjoint (`kqb9ok` E-02 refuses an unresolvable IPD manifest `file` in `initialize_run_core`, scoped to live actions), so an edge would assert a prerequisite relationship that does not exist. Added to the Scope check as a declared overlap. |
| PR-402 | HIGH | IN-SCOPE | Rubric G (executability); E (verification) | `grep -n "25kzda :166" agent_workflows/*.py` -> three hits, all `runner_shared.py`; the `RunPolicyFlag(flag="--with-dependencies", ...)` block -> zero `166` hits | E-07 named the wrong three sites. The real `:166` occurrences are BOTH inside `closure_target_admission` (its rationale comment AND its refusal f-string) plus `enforce_mixed_type_gate`'s docstring. E-07 instead named the refusal string, the `RUN_POLICY_FLAGS` help text, and the gate docstring. THE HELP TEXT CARRIES NO OFFSET AT ALL (it cites "spec 25kzda" bare). So E-07 as written would leave one real site (the rationale comment) uncorrected while editing a fourth that does not exist, and V-07's own `grep -rn '25kzda :166'` would then FAIL, making the plan fail its own acceptance check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now names all three real sites, instructs locating them by CONTENT SEARCH for the literal rather than by offset, and cites the spec by Section. Recorded as F-15; F-12's attribution corrected in place. The help text obligation is RETAINED but separated and re-justified on its own merits: it carries the narrowing prose "PLAN TARGETS ONLY: a spec or backlog dependency target REFUSES", which E-02 makes false, so a shipped `--help` would describe a refusal the code no longer performs. V-07 now requires the executor to state which three sites were corrected and that the help text never carried the offset. |
| PR-403 | MEDIUM | IN-SCOPE | Rubric D (anti-regression); G | `ls tests/ \| grep rununify` -> nothing; `grep -rn "NoRunnerImportTests" tests/` -> nothing; `git show 19313eed --stat` -> `test_rununify_host_descriptor.py \| 678 ------` and `test_runner_shared.py \| 3539 +++-----` | The conventions section claims the no-runner-import invariant is "enforced by `tests/test_runner_shared.py::NoRunnerImportTests::test_runner_shared_imports_neither_runner` and `tests/test_rununify_host_descriptor.py::TheSharedModuleStaysCleanTests`", copied verbatim from a stale in-code comment. BOTH were deleted by `19313eed`, the same commit that deleted this flag's coverage. The invariant still HOLDS, so E-02's obligation to thread the predicate is still correct, but the plan reassures its executor that a guard is watching a module E-02 is about to add a predicate to, and no guard is. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions bullet rewritten to state the invariant, that it is no longer test-enforced, that the cited guards are gone and must not be cited as protection, and that E-02 must obey by construction. Recorded as F-16. Added a Deferred row with a `Carrier-Declined` rationale explaining why restoring enforcement is NOT owed here: every available test shape (grep, AST walk, source read) is the code-pinning form P16 forbids, and the honest instrument would be an import-graph check in `aw check`, a different surface with its own review. Added to the scope fence as a negative constraint. |
| PR-404 | MEDIUM | IN-SCOPE | Rubric E (testing) | `parse_dependency_token`: `'executed:tgt001'` -> `('executed','ipd','tgt001')`; `'executed:ipd:tgt001'` -> `None` | The IPD control measurement V-04 demands can silently lie. The canonical IPD edge token is `executed:<id6>` with NO type segment, but the natural transcription by analogy with `state:backlog:graduated:<id6>` is `executed:ipd:<id6>`, which does NOT parse. `dependency_depth` then skips the edge and returns 0 for both nodes, which looks exactly like the defect E-04 fixes. An executor writing the control that way would conclude the IPD path is also broken, or would let a broken E-04 pass V-04. I hit this myself on my first probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-18 with both parse results. F-06's evidence now names the spelling trap explicitly. V-04 now requires the executor to NAME the control token and paste `parse_dependency_token(<token>)` beside the depths, so a reader can distinguish a real control from a silently-skipped edge, and to use 6-character ids. Added to the gate's silent-failure list as the first item. |
| PR-405 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | `rs.discover_plans(Path("."))` -> 1023 records; edge census -> `Counter({'executed/ipd': 205})` | F-11 states "Across 935 discovered plans, all 199 typed edges are `executed:ipd`". Re-measured: 1023 and 205. The LOAD-BEARING PROPERTY (zero non-plan edges anywhere, hence zero blast radius) is unchanged and confirmed, but the counts are a live-artifact population stated as though fixed, which the plan-executability re-derivation convention addresses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 restated as a PROPERTY with both measurements dated and labelled context rather than a bar, plus an explicit instruction that a non-zero non-plan count found at execution is a material change to the risk argument and must be reported. Recorded as F-17. No `V-*` demanded these counts, so no validation item needed loosening. |
| PR-406 | MEDIUM | UNDER-SCOPE | Rubric G (execution contract) | plan gate as authored | The gate was missing three required elements and carried one wrong instruction. Missing: a SCOPE FENCE, the hard-MUST honesty rule (paste the actual runner output), and the index-verification step for a shared checkout. Wrong: "Post-gate lifecycle move: on completion, transition with the tooled path (`aw ipd set executed <id6>`)", which names the wrong verb and omits the conditional runner/executor ownership the workflow requires. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the honesty rule, the `git diff --cached --name-only` verification, the UNPIPED exit-code rule, and the gitignored-fixture rule. Added a SCOPE FENCE worded as a DECLARATION for the runner to reconcile (not a stop directive, per the 2026-09-01 ruling) with five negative constraints, each closing a wrong turn this review found or the plan itself rejected. Replaced the lifecycle instruction with the unconditional finalize obligation and conditional owner, naming `AW-LIFECYCLE-ROLE-001` and forbidding a hand-rolled `git mv`. Added a "WHAT THE HUMAN WOULD BE APPROVING" paragraph and a "WHAT A REVIEWER SHOULD SCRUTINIZE" paragraph, since the gate previously offered an approver no summary of the change or its risks. |
| PR-407 | LOW | IN-SCOPE | Rubric E (verification checklist) | plan V-04, V-07, Required tests | Consequential to PR-401 through PR-404: the verification checklist could not have caught them. V-07's grep would have failed on PR-402's misattribution with no guidance; V-04 had no way to distinguish a real IPD control from a silently-skipped edge; nothing required the `kqb9ok` reconciliation to be reported; and no baseline was recorded for the owning test module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 and V-07 strengthened as described in PR-402 and PR-404. V-07 additionally requires the executor to state how the `enforce_mixed_type_gate` paragraph was reconciled against `kqb9ok` E-04 per OQ-03, naming which plan landed first, and to quote spec rule 5 beside the rule 4 diff so the "agrees rather than changes" claim is checkable. Required tests gained the `3246 passed, 2 skipped` and `11 passed` baselines with the `-o addopts=""` caveat. The gate gained a three-item silent-failure list. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `yu47nf` and `kqb9ok` reconcile, given both are approval-ready, overlap on two paths, and `kqb9ok`'s V-04 asserts a property `yu47nf` E-02 removes? | An ASYMMETRIC ordering obligation recorded in OQ-03, plus a fence constraint forbidding either plan from editing the other's record. No dependency edge. | (a) Declare `- Item-Dependencies:` on `kqb9ok`: REJECTED because the production behaviors are disjoint, so the edge would assert a prerequisite that does not exist and would needlessly serialize two independent changes. (b) Descope E-07's comment rewrite and let `kqb9ok` own all three: REJECTED because E-02 necessarily deletes the comment block it lives in, so this plan cannot avoid touching it. (c) Edit `kqb9ok`'s V-04 to match: REJECTED outright as rewriting another plan's record, which the execution contract forbids. (d) Say nothing, as authored: REJECTED because the collision reaches a validation item and would surface as a confusing failure for `kqb9ok`'s executor. | Both plans' front matter read directly (`- Status: reviewed`, `- Readiness: go-pending-approval`, `- Item-Dependencies: none` on each); `kqb9ok` V-04's text; this plan's E-02. The runner isolates each item in its own worktree and revalidates on merge, so a textual conflict surfaces at integration rather than corrupting a tree. | yes |
| D-2 | Should E-07's help-text obligation be dropped, since the help text does not carry the `:166` offset E-07 cited as the reason to edit it? | Keep it, re-justified on its own merits (the narrowing prose becomes false), and separate it from the offset fix. | (a) Drop it: REJECTED because `--with-dependencies`'s `--help` asserts "PLAN TARGETS ONLY: a spec or backlog dependency target REFUSES", which E-02 falsifies, and shipping a command whose documentation describes a refusal it no longer performs is the same defect class this plan exists to fix. (b) Leave E-07 as written and let the executor discover the mismatch: REJECTED because V-07's grep would fail and the executor would have no guidance on which site was actually missed. | The `RunPolicyFlag(flag="--with-dependencies", ...)` help string read directly; `grep` for `166` over that block returns zero while `grep -n "25kzda :166"` returns three hits elsewhere. The flag's "Changes selection only" promise is the sentence F-07 measures the code violating. | yes |
| D-3 | Should this plan restore test enforcement for the `runner_shared`-imports-neither-runner invariant, given both guards were deleted? | No; record the gap, stop citing the dead guards, and decline the work with a stated reason. | (a) Restore the deleted tests: REJECTED because both read production source to assert an import is absent, which is the code-pinning shape AGENTS.md and GUIDING_PRINCIPLES P16 forbid. (b) Write a behavioral equivalent: REJECTED as not available; "this module did not import that one" cannot be observed behaviorally without reading source or fabricating an import cycle. (c) File a backlog item: NOT taken, because the honest instrument is an import-graph rule in `aw check`, a different surface, and this plan has no standing to design it. (d) Keep the stale citation: REJECTED as the actively harmful option, since it tells the executor a guard is watching the module it is editing. | `19313eed` deleted `tests/test_rununify_host_descriptor.py` whole and `NoRunnerImportTests` with the same trim; `grep -n "import oc_runipd\|import agy_runipd" agent_workflows/runner_shared.py` returns only a comment, so the invariant holds unguarded. AGENTS.md's TEST OUTCOMES NOT CODE STRUCTURE rule (1) forbids `inspect`/`ast`/regex/substring reads of production source. | yes |
| D-4 | Is E-07's amendment to an APPROVED spec's Section 5.4 rule 4 legitimate for this plan to make? | Yes, as written, because it makes rule 4 agree with rule 5 rather than changing the contract; flagged in the gate for the approver to overrule. | (a) Refuse the spec edit and implement only the code: REJECTED because rule 4's type-rank sentence then reads as licensing the ordering F-06 measures as a defect, leaving the next reader unable to tell which rule governs. (b) Treat it as a contract change needing its own spec-review cycle: NOT taken, because rule 5 already states the precedence ("Explicit declared dependencies always win ... neither a higher Order nor a later requested position can delay an otherwise independent prerequisite relationship"), so the amendment is a clarification; but this is the judgement most open to maintainer disagreement, which is why the gate now names it explicitly as a thing a reviewer might overrule. | Spec Section 5.4 rules 4 and 5 read directly. The spec file IS declared in `- Scope-Paths:`, so the runner will announce the declared spec edit before the run starts and the finalize scope gate will reconcile it, which is the process AGENTS.md requires for a plan amending a spec. | yes |

No `Reversible: no` decision was made, so no escalation under the irreversible-decision rule is owed.
No finding was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question under
`review_findings_gate.block_at` (default `HIGH`) is owed; both HIGH findings were FIXED.

### Checklist assessment (required for an agent-executable IPD)

The CREATOR authored both checklists and the E/V bijection is 1:1 with concrete per-item evidence demands.
Right-sizing per the density diagnostics: seven E-items across three task groups, each naming one concern.
E-02 through E-04 are the three coordinated production changes and are correctly kept SEPARATE despite
having to land together, because each has its own distinct verification surface (admission verdicts, freeze
gate credit, depth and sort order); bundling them would have produced one E-item needing three unrelated
V-items, which is the (b) diagnostic. E-05 and E-06 split restored coverage from newly-created coverage,
which is the right seam because only E-06's cases can fail for a reason this plan introduced. `aw ipd lint`
reported no `IPD-Z602` density advisory at either checkpoint. No split is recommended.

The checklist's ONE STRUCTURAL STRENGTH worth naming is E-01: it requires the two defects to be pinned as
FAILING tests before any production edit, and V-01 requires the failure pasted. Given F-10 measures ZERO
existing coverage for this flag, that ordering is the only thing that can prove the new tests bite, and the
plan got it right without prompting.

The checklist's weakness was EVIDENCE PRECISION rather than coverage, which is what PR-404 and PR-407
repair: V-04 asked for a control measurement that a plausible transcription error makes vacuous, and V-07
asked for a grep the plan's own misattribution would have failed. Both now demand the observation that
distinguishes a real result from a silently-skipped one.

Live-artifact convention: F-11's plan/edge counts were the one population stated as fixed; they are now
context with a re-derivation instruction (PR-405). Every other count this plan asserts is a stable code
fact (the eleven deleted tests, the three `:166` sites, the action-table rows, the nine regression files),
so no further re-derivation clause is owed.
