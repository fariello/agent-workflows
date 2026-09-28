# Review findings: plan tl2b2r

- Subject-Id: tl2b2r
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0a86a73d` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and unmodified, and the
lane-input snapshot is byte-identical to the tracked file (`diff` reports no difference). No
production code was modified by this review; every post-change claim was measured by driving the
shipped functions against synthetic fixtures in temp repositories.

THE PLAN'S DIAGNOSIS IS CORRECT AND UNUSUALLY WELL EVIDENCED, AND ITS CENTRAL CORRECTION OF THE
BACKLOG ITEM HOLDS. The item asserts that git merges the described lane shape cleanly; the plan
measured that git CONFLICTS on that shape and that the real defect is the add/add variant the item
never names. Review did not attempt to re-drive the two runner probes (F-01 through F-03), which are
Order 2's subject rather than this plan's, but every claim this plan's own deliverables rest on was
re-driven. F-04 reproduces (no placement-keyed rule exists; the three location-adjacent ids are all
declared-field-keyed). F-06 reproduces EXACTLY: 19 of 38 specs and 17 of 17 prompts declare no
`- Id:`, while plans and backlog declare one universally. The `_identity_slot_token` /
`_is_real_id6` guards, the `_DEFAULT_RULESPEC` fallback, the `warning`-fails-the-gate property, the
once-per-sweep `try/except` seam, and `lifecycle_dirs` being a true leaf module all reproduce as
described.

WHAT REVIEW FOUND IS ONE STRUCTURAL DEFECT THAT WOULD HAVE BROKEN THE SET AT ORDER 2's EXECUTION,
plus three measured falsehoods in the plan's own predictions and two overstated claims. The
approach is sound and every finding was repairable with bounded edits to this plan alone.

**THE SHARED-PREDICATE PREMISE THIS WHOLE SET RESTS ON WOULD NOT HAVE HELD (PR-002, HIGH).** Order 2
(`46u3tu`) exists to consume this plan's predicate, declares `- Item-Dependencies: executed:tl2b2r`
to enforce that, and its E-01 says to ask the predicate about a PREDICTED POST-MERGE TREE, taking
the tree `merge_write_set` builds and enumerating it with `git ls-tree -r --name-only <tree>`. E-01
as authored delivered exactly one entry point, gathering from `check_engine._iter_type_files`, which
is `d.rglob("*.md")` on the real filesystem. A tree object has no filesystem presence, so that
function cannot be called on it. Order 2 would therefore have arrived at execution with its
dependency satisfied, its declared consumption impossible, and its only route forward being the
local re-derivation its own plan calls "the two-readers drift this repository has already paid for".
This is the review's most consequential finding because the failure surfaces only at Order 2's
execution, with Order 1 already `executed` and unamendable in place.

**THE PLAN INSTRUCTS THE EXECUTOR TO DISREGARD A LIVE, SUITE-ENFORCED CONSTRAINT (PR-001, MEDIUM).**
E-02 says the `duplicate`-substring prohibition's "enforcing test was deleted by commit `19313eed`
and MUST NOT be cited as though it still ran". `tests/test_graduation_view.py` is indeed absent, but
the guard survived elsewhere: `tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests
::test_rule_id_contains_neither_graduation_nor_duplicate` asserts
`[k for k in RULE_REGISTRY if 'graduation' in k or 'duplicate' in k] == []` over the WHOLE registry,
and driven at review it passes. So the constraint is mechanical, not conventional, and a violating
id REDS the suite in a file this plan does not declare in `Scope-Paths`. The plan's wording points
the executor the wrong way on exactly the point where being wrong costs a scope breach.

**THREE OF THE PLAN'S OWN PREDICTIONS DO NOT REPRODUCE (PR-006, MEDIUM; PR-007, LOW; PR-008, LOW).**
F-05 and E-04 row (b) state the legacy no-`Id:` fixture reports "only `check.ipd-lint-diagnostic`".
Driven with this file's own helpers: `['check.identity-absent-from-name', 'check.ipd-lint-diagnostic']`.
The load-bearing half survives (neither is a placement finding), but the expected set is wrong, and
row (b) is the row the plan calls its only proof the stem key works, so an executor writing the
predicted set would get a legitimate failure on the most important row and might resolve it by
filtering. Separately, rows (a) and (c) trip NO lint diagnostic in default scope despite their
`executed/` fixture carrying `- Status: executed`, because the retired filter hides that file from
the content pass while the identity passes still see it, so the corrected sets are not uniform and
cannot be reasoned out by analogy. F-11's suite baseline moved from `2937 passed` to `3102 passed`
between authoring and review, and F-08's default-scope finding count from 3 to 5, both from
unrelated main traffic; the plan used the first as a comparison bar and the second as a baseline.

**E-03's TERMINAL CLAUSE IS PLAN-SHAPED AND WOULD LIE ON THE SIBLING DEFECT'S OWN SHAPE (PR-005,
MEDIUM).** E-03 requires the message say which copy is terminal, via
`run_selection_policy.is_in_terminal_directory`. Driven: that predicate answers `True` for
`plans/executed/`, `plans/reusable/` and `specs/superseded/`, and `False` for `specs/implemented/`,
`backlog/done/` and `backlog/parked/`, because `TERMINAL_DIRECTORY_SEGMENTS` is exactly the four
plan dispositions. So an unconditional terminal sentence says "neither is terminal" for a
`backlog/open/` + `backlog/done/` pair, which is precisely the shape of `5bmq5f`, the sibling item
this plan cites as the measured complaint it must not reproduce. The same predicate also counts
`/reusable/` as terminal while `.aw/records/plans/README.md` says `reusable` is "not a terminal
state", so a `pending/` + `reusable/` pair would be told the reusable copy supersedes the pending one.

**THE TYPE DOMAIN WAS NEVER DECIDED, AND THE UNDECIDED CASE FAILS SILENTLY (PR-003, MEDIUM).**
`check_engine.SUPPORTED` has eight types; `lifecycle_dirs.LIFECYCLE_SUBDIRS` has four keys. The four
absent (`research`, `walkthroughs`, `roadmaps`, `releases`) are flat trees. E-01 said to import the
enumeration from `LIFECYCLE_SUBDIRS` without saying which type list to iterate, and an
implementation iterating `SUPPORTED` would either raise `KeyError` on a flat type, swallowed by
E-02's mandated `try/except` and silently disabling the entire rule, or bucket every flat-tree file
to `None` and collapse them into one key. The four lifecycle types also share no bucket vocabulary
(plans/prompts five dispositions, specs nine statuses, backlog five), so a plan-shaped literal would
misread specs and backlog.

**THE PLAN OVERSTATES WHAT IS UNCOVERED (PR-004, MEDIUM).** The Deferred section says
`attention.duplicate-id` covers the backlog tree. `attention.scan` keys `seen_ids` across every
inventoried tree, and driven on a `pending/`+`executed/` same-`Id:` PLAN fixture it reports exactly
`attention.duplicate-id` naming both paths. So for the modern-plans shape, two rules already report
the fact and this would be a third. The gap is still real and the plan is still worth executing:
both existing readers key only on the declared `- Id:` and are blind to the 19-of-38 specs and
17-of-17 prompts declaring none, and neither reads the stem (driven: the legacy pair yields `[]` from
`attention.scan`). But the justification had to be narrowed to what measurement supports.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. Both authored open questions are `resolved` and both survive review; OQ-02's resolution is
reinforced by PR-004's measurement, which promotes the stem key from one of two conveniences to the
plan's principal justification. OQ-03 is new, recording the four-type domain decision. F-07 was
re-measured across all four lifecycle types and both keys rather than plans only (0 duplicates
everywhere across 884 plans, 38 specs, 17 prompts, 675 backlog items; also 0 declared id6 shared
across types over 1578 distinct ids), so the `error` severity choice is now evidenced for the
rule's actual reach rather than for one of its four trees.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Plan executability / E. Testing | plan E-02 ("its enforcing test was deleted by commit `19313eed`"); `tests/test_check_engine_spec_criteria.py::CheckEngineSpecCriteriaTests::test_rule_id_contains_neither_graduation_nor_duplicate`; driven `1 passed` | THE PLAN TELLS THE EXECUTOR A LIVE SUITE GUARD IS DEAD. The `duplicate`-substring prohibition is enforced TODAY by a test that asserts over the whole `RULE_REGISTRY`, not merely over its own rule id, and it passes at review HEAD. `tests/test_graduation_view.py` was deleted, but the guard survived in another file, so the prohibition is mechanical rather than conventional. An executor trusting "MUST NOT be cited as though it still ran" could register a `duplicate`-containing id, RED a test in an undeclared file, and be pushed toward relaxing that assertion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewritten to name the live test and its whole-registry assertion, carry the driven `1 passed` evidence, and state that the remedy is a placement-shaped id and never an edit to that file. V-02 now requires pasting the test result rather than an eyeballed substring check. Scope check lists the file as a foreseeable out-of-scope pull with the in-scope answer. |
| PR-002 | HIGH | UNDER-SCOPE | C. Architecture and operability | plan E-01 (single reader gathering via `_iter_type_files`); `check_engine._iter_type_files` -> `d.rglob("*.md")`; `46u3tu` E-01 ("enumerate its record paths with `git ls-tree -r --name-only <tree>`"); `46u3tu` `- Item-Dependencies: executed:tl2b2r` | THE SET'S SHARED-PREDICATE PREMISE WOULD NOT HAVE HELD. Order 2 must ask this predicate about a PREDICTED MERGE TREE that exists only as a git tree object, but the authored reader's only enumeration walks the real filesystem and cannot see a tree object. Order 2 would reach execution with its dependency satisfied and its declared consumption impossible, leaving local re-derivation (the exact drift the dependency exists to prevent) as its only route. The failure surfaces only after Order 1 is `executed` and can no longer be amended in place. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (a two-symbol split of code not yet written, with a test pinning the property) | FIXED | E-01 now mandates TWO symbols: a filesystem-free pure core taking gathered `(path, text_or_None)` records, plus a thin repository-scanning wrapper that delegates. The core must accept `text=None` (stem-keyed only) because `git ls-tree` yields paths and reading each blob costs a `cat-file`, and that degradation is documented rather than discovered. Added F-12. V-01 requires driving the core on synthetic paths that do not exist on disk; E-04's Expected outcome requires a test pinning it. |
| PR-003 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Architecture | `list(ce.SUPPORTED)` (8 members) vs `sorted(ld.LIFECYCLE_SUBDIRS)` (4 keys); `LIFECYCLE_SUBDIRS['specs']` (9 statuses) vs `['backlog']` (5) vs `['plans']` (5 dispositions) | THE TYPE DOMAIN WAS UNDECIDED AND ITS UNDECIDED CASE FAILS SILENTLY. Four of the eight `SUPPORTED` types are FLAT trees with no lifecycle subdirectory. An implementation iterating `SUPPORTED` would raise `KeyError` on one (swallowed by E-02's mandated `try/except`, disabling the whole rule with no diagnostic) or bucket every flat file to `None`, collapsing them into one key. The four lifecycle types also share no bucket vocabulary, so a plan-shaped literal misreads specs and backlog. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (a domain decision plus a pinning test, made before code exists) | FIXED | E-01 now mandates iterating `LIFECYCLE_SUBDIRS` (four keys) and NOT `SUPPORTED`, skipping flat types explicitly with the stated reason, and reading each type's vocabulary from `LIFECYCLE_SUBDIRS[type]`. Added F-13 and new OQ-03 recording the decision. E-04 gains row (f), a flat-tree row asserting the new rule is ABSENT, so a later widening fails a test rather than degrading silently. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness (claim accuracy) / C. Architecture | plan Deferred row ("`attention.duplicate-id` already cover that tree"); `attention.scan` `seen_ids` keyed over every inventoried tree; driven on a plans `pending/`+`executed/` same-`Id:` fixture -> `attention.duplicate-id` naming both paths; driven on the legacy no-`Id:` pair -> `[]` | THE PLAN UNDERSTATES EXISTING COVERAGE AND SO OVERSTATES ITS OWN NOVELTY. `attention.duplicate-id` is repo-wide, not backlog-scoped, so for the modern-plans shape TWO rules already report the fact and this is a third. Left uncorrected, E-02 would claim first detection for a case already covered twice, and the plan's real value (the stem key and the no-declared-`Id:` population, on which both existing readers are blind) would read as a secondary robustness argument rather than the justification. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with all three driven fixtures. The Deferred row now states the correction explicitly, narrows the claim to the stem key and the no-`Id:` population, and instructs E-02 not to claim novelty it does not have. OQ-02's resolution gains the measurement promoting the stem key to the principal justification. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness / F. UX (remedy honesty) | plan E-03 ("say which copy the lifecycle reading considers stale"); `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` = `('/executed/','/superseded/','/not-executed/','/reusable/')`; driven `False` for `specs/implemented/`, `backlog/done/`, `backlog/parked/` and `True` for `plans/reusable/`; `.aw/records/plans/README.md` ("`reusable/` ... not a terminal state") | THE TERMINAL CLAUSE IS PLAN-SHAPED AND WOULD LIE ON THE SIBLING DEFECT'S OWN SHAPE. The predicate E-03 reuses answers `False` for every spec and backlog terminal, so an unconditional sentence says "neither is terminal" for a `backlog/open/`+`done/` pair, which is exactly the `5bmq5f` shape this item cites as the defect it must not reproduce. It also calls `/reusable/` terminal against the plans README, so a `pending/`+`reusable/` pair would be told the reusable copy supersedes the pending one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03's terminal sentence is now CONDITIONAL: reuse the predicate where it answers, and where it answers `False` for every copy, omit the sentence and name the two buckets plainly. Added F-14. A prohibition on widening `TERMINAL_DIRECTORY_SEGMENTS` is recorded (it feeds the runner's records-only conflict arm and is outside `Scope-Paths`). V-03 requires pasting the backlog-pair and reusable-pair messages with the driven predicate results justifying each. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing and verification | plan F-05 and E-04 row (b) ("reported only `check.ipd-lint-diagnostic`"); driven `['check.identity-absent-from-name', 'check.ipd-lint-diagnostic']`; rows (a)/(c) driven `['check.id6-collision']` with no lint diagnostic | THE MOST IMPORTANT TEST ROW CARRIES A WRONG EXPECTED SET. The legacy no-`Id:` fixture also trips the `warning`-severity `check.identity-absent-from-name`, so row (b) needs three ids once the new rule lands, not two. Row (b) is the plan's only proof the stem key works, so an executor writing the predicted set gets a legitimate failure on the row that matters most and may resolve it by filtering the unexpected id. The sets are also non-uniform across rows (the retired filter hides the `executed/` fixture from the content pass in (a)/(c) but not the legacy body in (b)), so they cannot be reasoned out by analogy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 carries the correction and keeps its surviving half. E-04 now carries the driven pre-change sets for rows (a) through (d), explains why (b) differs and why (a)/(c) must NOT gain a lint diagnostic by analogy, and requires re-driving every set at execution rather than copying. |
| PR-007 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-11 (`2937 passed, 2 skipped ... 201 deselected`); re-driven `3102 passed, 2 skipped, 3 warnings in 47.90s` (205 deselected); plan F-08 (3 default-scope findings); re-driven 5 | TWO LIVE COUNTS ARE USED AS BARS AND BOTH DRIFTED BEFORE EXECUTION. V-04 required comparing the suite summary against F-11's figure, which moved by 165 tests from unrelated main traffic; a plan-recorded total cannot distinguish an added test from a merge. F-08's default-scope count moved 3 -> 5 and was cited as a baseline. This is the repository's own live-artifact-count convention applied to the plan's own validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 and F-08 both carry the re-driven figures and are relabelled as context that provably drifts. V-04 now requires a baseline taken in the same lane IMMEDIATELY BEFORE the change, with added tests accounted as the difference between two runs. The `aw check` bar is restated as "no finding carrying the NEW rule id", which is invariant to the drift. |
| PR-008 | LOW | IN-SCOPE | A. Correctness (measurement scope) | plan F-07 (plans-only `uniq -d` over "870 plans"); re-driven per type: plans 884, specs 38, prompts 17, backlog 675, all with `stem-dups=0` and `declaredId-dups=0`; 0 declared id6 shared across types over 1578 ids; `RULE_REGISTRY` 51 not 50 | THE ZERO-INSTANCE MEASUREMENT COVERED ONE OF THE RULE'S FOUR TREES. F-07 justifies the `error` severity on the ground that nothing reds today, but measured plans only while the rule fires on four types, so the severity choice rested on a quarter of the evidence it needed. The conclusion holds (all four trees are clean on both keys), which is why this is LOW rather than a severity re-open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 re-measured across all four lifecycle types and both keys, with the per-type counts and the cross-type declared-id check recorded, and notes it supersedes the plans-only reading. F-04's registry count corrected to 51 and labelled context. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Order 2 cannot call a filesystem-walking predicate. Split Order 1's reader into a pure core plus a scanning wrapper, re-scope Order 2, or ask the maintainer? | SPLIT ORDER 1's READER: a pure core taking gathered records (no filesystem) plus a thin scanning wrapper, with a test pinning the core runs on nonexistent paths. | (a) Let Order 2 re-derive the grouping locally - rejected: it is the two-readers drift Order 2's own plan names as the reason for its dependency, and the whole Set exists to avoid it. (b) Re-scope Order 2 to read the working tree after merging - rejected: its E-01 requires a PRE-merge refusal so main stays untouched and no suite run is spent, which is the property making the refusal cheap. (c) Have Order 2 write the predicted tree to a temp dir and scan it - rejected: it adds a checkout per integration to a hot path and invents a second enumeration route for one question. (d) Ask the maintainer - rejected: the repository answers it by reading the two plans and one function, and resolving from evidence is the instructed default. | `46u3tu` E-01 ("`git ls-tree -r --name-only <tree>`"); `check_engine._iter_type_files` -> `d.rglob("*.md")`; `46u3tu` `- Item-Dependencies: executed:tl2b2r` and its stated no-fork requirement. | yes |
| D-2 | Should the predicate cover all 8 `SUPPORTED` types or only the 4 with lifecycle directories? | THE FOUR with lifecycle directories, with the flat types skipped explicitly and a test pinning the domain. | (a) Iterate `SUPPORTED` and treat a flat tree as one implicit bucket - rejected: it detects nothing (two same-stem files in one directory is impossible on a filesystem) and an implementation asking `LIFECYCLE_SUBDIRS` for a flat type either raises `KeyError`, swallowed by E-02's `try/except` and silently disabling the whole rule, or buckets everything to `None`. (b) Leave it unstated - rejected: it is the one ambiguity whose wrong resolution disables the rule with no diagnostic. | `list(ce.SUPPORTED)` (8) vs `sorted(ld.LIFECYCLE_SUBDIRS)` (4); the four absent types are flat trees; E-02's mandated per-rule `try/except` in `check_types`. | yes |
| D-3 | E-03's terminal claim is false for spec and backlog terminals and wrong about `reusable`. Make the clause conditional, or widen `TERMINAL_DIRECTORY_SEGMENTS`? | MAKE THE CLAUSE CONDITIONAL: reuse the predicate where it answers, omit the sentence where it answers `False` for every copy. | (a) Widen `TERMINAL_DIRECTORY_SEGMENTS` to add `implemented`, `done` etc. - rejected: `run_selection_policy.py` is not in `Scope-Paths` and that constant feeds the runner's records-only conflict arm, so widening it changes integration behavior far outside this plan. (b) Keep the unconditional sentence - rejected: it makes a false claim on the `backlog/open/`+`done/` pair, which is the shape of the sibling defect the plan cites as the thing not to reproduce. (c) Add a type-aware terminal reading inside `check_engine` - rejected as gold-plating: the message only needs to omit a claim it cannot support, and a second terminal-vocabulary reading is a new divergence risk. | Driven `is_in_terminal_directory` over six real paths; `TERMINAL_DIRECTORY_SEGMENTS` membership; `.aw/records/plans/README.md` on `reusable`; `5bmq5f` being a backlog-tree item. | yes |
| D-4 | F-11's suite baseline and F-08's finding count both drifted before execution. Update the digits, or change what V-04 compares against? | BOTH: record the re-driven figures as context and change V-04's bar to a baseline taken immediately before the change in the same lane. | (a) Just update the numbers - rejected: they will drift again before execution (they already drifted once between authoring and review), and the repository's own convention says a live count belongs in prose as context rather than as a bar. (b) Drop the baseline requirement - rejected: accounting for added tests is a real obligation; only the reference point was wrong. | Re-driven `3102 passed, 2 skipped, 3 warnings in 47.90s` against the authored `2937 passed`; re-driven 5 default-scope findings against the authored 3; the live-artifact-count convention in the plan rubric. | yes |
| D-5 | `attention.duplicate-id` already reports the modern-plans shape repo-wide. Does that make this plan redundant? | NO: execute it, but narrow the stated justification to the stem key and the no-declared-`Id:` population. | (a) Retire the plan as redundant - rejected on measurement: both existing readers key only on the declared `- Id:`, so they are blind to 19 of 38 specs and 17 of 17 prompts, and driven on the legacy no-`Id:` pair `attention.scan` returns `[]`. The uncovered population is real and large. (b) Leave the Deferred row's backlog-only framing - rejected: it understates existing coverage, which would let E-02 claim first detection for a case two rules already report. (c) Narrow the rule to fire only where the declared-`Id:` readers are silent - rejected: it would make the finding's meaning depend on another rule's reach, and a placement-shaped remedy message is worth having for the covered case too. | `attention.scan` keying `seen_ids` over every inventoried tree; three driven fixtures (modern plans pair -> `attention.duplicate-id`; legacy pair -> `[]`; no-`Id:` spec pair -> only `attention.history-missing`); F-06's population counts. | yes |
