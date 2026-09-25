# Review: Make one lifecycle-subdir table the only source every placement consumer reads

- Subject-Id: d1lo52
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4e91bb1b`. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` after the revisions.

THE PLAN'S DIAGNOSIS IS ACCURATE AND ITS MEASUREMENT IS EXACT. I rebuilt the AST predicate it describes
and ran it: twelve literal sites in nine modules, precisely the ones the plan names. I also confirmed both
of its "FIXED by r9uvwc" rows (`status_set` now calls `record_placement.resolve_transition_path`; `specs`
calls `resolve_creation_path("specs", "draft", ...)`), and that every consumer-agreement assertion E-02
proposes already holds at HEAD. So the table transcribes current truth rather than changing it, which is
the property a pure refactor needs.

PR-701 IS THE FINDING THAT WOULD HAVE BROKEN A SHIPPED CONTRACT, and it is a type error hiding as a
wording choice. E-01 said to build the spec row from "the nine `attention_contract.SPEC_STATUSES` values
in their current listed order". `SPEC_STATUSES` is a `frozenset`. It has no order, and its iteration order
is not even stable between processes: three consecutive interpreters printed it in three different orders
here. "Current listed order" is true of the SOURCE LITERAL a human reads and false of the runtime object
an executor would iterate, and an executor following the instruction literally would have produced a row
whose order varied per run. That is not cosmetic, because order is pinned by an APPROVED spec: `kw5y2s`
specifies `"lifecycle_subdirs": ["draft", "to-review", "reviewed", "approved", "implementing",
"implemented", "deferred", "parked", "superseded"]` as a JSON array, and `layout.WorkspaceLayout.to_dict`
emits `list(rc.lifecycle_subdirs)` positionally. So the plan's own E-03 success criterion, a byte-identical
`aw layout --json`, would have failed non-deterministically: sometimes passing, sometimes not, on
unchanged code. The ordered authority is `layout`'s `specs` tuple, which agrees with the spec, and E-01
now sources from it with a three-seed determinism check in V-01.

PR-702 IS THE STRUCTURAL ONE AND IT IS NOT A STYLE PREFERENCE. E-02 created one test file holding two
classes whose pre-migration expectations are OPPOSITE: `ConsumerAgreementTests` must PASS immediately
(it is the baseline proving the table matches reality) while `LiteralDriftGuardTests` must FAIL (it is the
enforcement). The item's `Expected outcome` asserted only that the file "FAILS at this point", and its
V-02 asked for a nonzero failed count. Both are satisfied by a run in which the BASELINE is broken and
the guard is fine, which is the exact inversion that would invalidate every later "identical to the
pre-change capture" claim in the plan, since those are all measured against that baseline. Split into
E-02 (agreement, expected PASS) and E-03 (guard, expected FAIL), with V-02 and V-03 requiring the two
runs separately and the gate naming a failing baseline as a STOP condition.

PR-703 IS AN ENFORCEMENT CLAIM THAT IS FALSE AS MEASURED. The Findings section counts "two literal-set
expressions inside `record_placement`" among the copies the drift guard finds. It finds neither, and
cannot: both are lists of TYPE names (`("plans", "prompts", "backlog", "specs")` and
`("backlog", "specs")`), and no table row is a subset of either, so a superset predicate never matches.
Running the predicate over that file yields zero hits. The consequence is what matters: E-05's (now
E-06's) `record_placement` edits carry NO drift-guard protection, so the guard's clean post-migration run
is not evidence about that file, and the plan would have presented it as though it were. The guard's two
real limits are now written into the test's own docstring by E-03, so the next reader inherits the
measurement instead of the impression.

PR-704 IS A MISSED SITE, AND THE ONE I FOUND BY READING RATHER THAN BY TOOL. `backlog`'s `set` path joins
`_resolve_backlog_root(repo_root) / new_status`, which is the same hardcoded status-to-subdir join as the
creation site E-06 (now E-07) converts. A literal-collection predicate cannot see a path join, which is
precisely why the plan's probe-driven inventory missed it. Converting one of a matched pair and leaving
the other is how the next reader concludes the migration was deliberately partial. E-07 now converts both,
and V-07 requires driven `aw backlog set` output.

PR-705 is a behavior no test pins today, which made it a silent-regression candidate.
`record_placement.has_lifecycle_subdirs` resolves ALIASES, so `("plan")` and `("spec")` both return True,
because `layout.get_record_class` maps an alias before the literal fallback is reached.
`tests/test_record_placement.py` covers only `research` and `walkthroughs`. E-05 (now E-06) replaces only
the FALLBACK, so the behavior is in fact preserved, and I verified that; but nothing would have caught an
executor who read "replace the fallback with `bool(subdirs_for(record_type))`" as "make the function a
table lookup". E-02 now asserts both aliases and V-06 requires the diff to show the layout lookup still
runs first.

PR-706 is the mirror of PR-701 on the validation side. V-04 asked for five symbols printed "identical in
value and order", but three of them are sets. A raw-order comparison of a set is flaky rather than strict,
while `sorted()` on the two ordered tuples would have thrown away real information, because
`plans.DISPOSITION_DIRS`' order is user-visible: `plans.collect` and the board renderer iterate it
positionally to order the `## <disp>/` sections. E-02's assertion had the same defect in the other
direction (`set(DISPOSITION_DIRS) == set(...) | {"done"}` passes on any permutation). Both now compare
tuples positionally and sets with `sorted()`, and a conventions bullet states the rule once.

PR-707 is small and worth stating because the plan asserted the safe half without noticing the notable
half. E-03 (now E-04) calls `layout` "import-light", which is true and measured (importing it pulls 4
`agent_workflows` modules). What the plan did not say is that `layout`, `plans` and `attention_contract`
each have ZERO intra-package imports today, so this plan adds the FIRST one to three deliberately
dependency-free modules. That is acceptable, because a leaf cannot cycle, but the invariant survives only
if nobody later adds an import to `lifecycle_dirs`, so E-04 now requires that reason in the module's
docstring. Relatedly, E-05's original instruction routed `ipd_schema`'s spec vocabulary through
`attention_contract`, which `ipd_schema` does not currently import; deriving from the table directly avoids
a second avoidable edge and stops `ipd_schema` depending on a module whose own row this plan is
simultaneously re-deriving.

PR-708 is the gate, which was three sentences with no approval statement, no scope fence, no stop
conditions, an unconditional `git mv`-flavored transition instruction, and `Cohesion rationale: not
required` on what is now a nine-item plan.

ON RIGHT-SIZING: the split is 8 items to 9, and only one split was for size (E-02/E-03, and that one is
for a correctness reason, not length). E-06 (now E-07) gained a second site rather than being divided,
because both backlog joins are one concern verified by one command.

THINGS I CHECKED AND FOUND CORRECT, recorded so a later reader does not re-derive them: `aw layout --json`
IS byte-stable across runs, so E-04's diff is a meaningful test; `target_subdir("backlog", s)` is an
identity for every input including an invalid one, so E-07's backlog conversion is provably behavior-neutral;
E-05's `DISPOSITION_DIRS` concatenation formula reproduces the current tuple exactly; `ipd_lint._dir_of`
returns the first anchor of its TUPLE rather than of the path, so preserving row order is load-bearing and
the table does preserve it; `tests/test_layout.py`'s overlapping test compares the backlog and specs rows
against live symbols and so is not a fifth full copy; and `tests/test_layout.py` +
`tests/test_record_placement.py` + `tests/test_backlog.py` are 75 passed at HEAD, which is the
behavior-preservation baseline. Backlog item `x9qv9q` carries no `- Blocks-Release:` and is
`Work-Kind: chore`, so no release gate is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression | `type(attention_contract.SPEC_STATUSES)` is `frozenset`; three consecutive interpreters printed `list(SPEC_STATUSES)` in three different orders; approved spec `kw5y2s` pins `"lifecycle_subdirs": ["draft", "to-review", ...]` as a JSON array; `layout.WorkspaceLayout.to_dict` emits `list(rc.lifecycle_subdirs)` positionally | E-01 DERIVED AN ORDERED ROW FROM AN UNORDERED SET. "The nine `SPEC_STATUSES` values in their current listed order" describes the source literal a human reads, not the runtime object an executor iterates, and that object's order varies per process. Order is a SHIPPED CONTRACT pinned by an approved spec and emitted positionally, so a set-derived row would have produced a spec-violating permutation that differs between runs of unchanged code, and the plan's own byte-identical-JSON criterion would have failed non-deterministically. | C:Low; U:Low; S:Low; F:Medium (a shipped, spec-pinned array emitted wrong, intermittently); Overall:Medium | FIXED | E-01 now takes the spec row from `layout`'s ordered `lifecycle_subdirs` tuple, writes it as a literal tuple in the one exempt module, and states why a frozenset is not a source. V-01 requires three `PYTHONHASHSEED` runs printing the row identically plus a comparison against layout's tuple. E-02 asserts the emitted `to_dict` array positionally. Added the measurement to Findings and a conventions bullet stating the tuple-versus-set rule. |
| PR-702 | HIGH | UNDER-SCOPE | E. Testing / G. Plan executability | Original E-02 built one file with `ConsumerAgreementTests` (must pass pre-migration) and `LiteralDriftGuardTests` (must fail pre-migration); its `Expected outcome` was "FAILS at this point" and V-02 asked for "a nonzero failed count"; verified at review that every agreement assertion holds at HEAD | ONE ITEM BUNDLED TWO CLASSES WITH OPPOSITE PRE-MIGRATION EXPECTATIONS AND A SUCCESS CRITERION THAT CANNOT TELL THEM APART. A run where the BASELINE is broken and the guard is fine satisfies "fails with a nonzero count" exactly as well as the intended state. That inversion matters more than it sounds: every later "identical to the pre-change capture" claim in the plan is measured against that baseline, so a broken one silently invalidates E-04 through E-07's evidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-02 (agreement, expected PASS immediately, stated as the baseline) and E-03 (drift guard, expected FAIL). V-02 and V-03 require the two runs separately and require the classes be distinguishable in the output. The gate names a failing baseline at E-02 as a STOP condition, since it means the table does not transcribe current truth. |
| PR-703 | MEDIUM | IN-SCOPE | F. Honest documentation / E. Testing | Running the predicate over `record_placement.py` yields ZERO hits; its two literals are `("plans", "prompts", "backlog", "specs")` and `("backlog", "specs")`, lists of TYPE names that no table row is a subset of; the 12 flagged sites are all in other modules | THE FINDINGS SECTION COUNTED TWO SITES THE GUARD CANNOT SEE, overstating what the enforcement covers. The consequence is concrete rather than clerical: `record_placement`'s edits have NO drift-guard protection, so the guard's clean post-migration run is not evidence about that file, and the plan presented it as if it were. The same blind spot is why the thirteenth site in PR-704 was missed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the Findings claim with the measurement and the consequence. E-03 requires both guard limits in the test's docstring (it sees only subdir-name collections, and the at-most-one-extra bound is what spares the 11- and 6-element vocabularies). E-06's expected outcome now names the tests that DO pin `record_placement`. OQ-01's rationale records both limits. Added a Deferred entry declining to widen the guard to type-name lists. |
| PR-704 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Architecture | `backlog`'s `set` path: `dest_dir = _resolve_backlog_root(repo_root) / new_status`; its creation path: `dest = _resolve_backlog_root(repo_root) / status / filename`; `target_subdir("backlog", s)` verified an identity for every input including an invalid one | A THIRTEENTH HARDCODED STATUS-TO-SUBDIR JOIN WAS MISSED, in the same module and the same shape as the one the plan does convert. It is invisible to a literal-collection predicate because it is a path join, which is exactly why a probe-driven inventory missed it. Converting one of a matched pair and leaving the other leaves the next reader to conclude the migration was deliberately partial, which is how a "single source of truth" refactor loses its guarantee one site at a time. | C:Low; U:Low; S:Low; F:Low (the conversion is provably behavior-neutral); Overall:Low | FIXED | E-07 now converts BOTH backlog joins, with the identity measurement stated so the neutrality is checkable. V-07 requires driven `aw backlog set` output across at least two statuses. Findings records the site and why the probe could not see it. `- Scope:` now says "`backlog` new AND `backlog set`". |
| PR-705 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing | `has_lifecycle_subdirs("plan")` and `("spec")` both True today via `layout.get_record_class`'s alias resolution, which runs BEFORE the literal fallback; `tests/test_record_placement.py` asserts only `research` and `walkthroughs` | AN ALIAS BEHAVIOR NO TEST PINS SAT DIRECTLY UNDER AN ITEM THAT REWRITES THAT FUNCTION. E-05 as written replaces only the fallback, so the behavior survives, and I verified it does. But the instruction is readable as "make this a table lookup", and `subdirs_for` takes canonical names only, so that reading silently breaks alias support with no failing test. An unpinned behavior beside an edit to its own function is a regression waiting for a careless pass. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 asserts both aliases. E-06 is explicit that the `layout.get_record_class` lookup stays PRIMARY and only the fallback changes, and its expected outcome names the alias check as the proof. V-06 requires the diff to show the lookup still runs first. Findings records that no existing test pinned it. |
| PR-706 | MEDIUM | IN-SCOPE | E. Testing | `backlog.STATUS_DIRS` and `plans.DISPOSITION_DIRS` are tuples; `SPEC_STATUSES`, `TYPE_STATUSES["specs"]` and `_ITEM_DEP_STATE_STATUSES["spec"]` are sets; `plans.collect` and the board renderer iterate `DISPOSITION_DIRS` positionally to order the `## <disp>/` sections | THE VALIDATION CONFLATED ORDERED AND UNORDERED SYMBOLS IN BOTH DIRECTIONS. V-04 demanded five symbols be "identical in value and order" when three are sets, making it flaky rather than strict; E-02's set-union comparison of `DISPOSITION_DIRS` against the plans row plus `done` would conversely PASS on a permutation that visibly reorders the plans board. One assertion was too strong for its subject and the other too weak. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 compares `DISPOSITION_DIRS` as an ordered tuple with the reason stated; V-05 prints the two tuples raw and the three sets `sorted()`, each with its justification; E-05 says which spelling to use and why a raw-order set comparison would be flaky. Added a conventions bullet naming every ordered and unordered symbol once. |
| PR-707 | LOW | UNDER-SCOPE | C. Architecture | `attention_contract`, `plans` and `layout` each have ZERO `from agent_workflows import` statements today; importing `layout` pulls 4 `agent_workflows` modules; `ipd_schema`'s intra-package imports are `artifact_core`, `backlog`, `plans` (no `attention_contract`) | THE PLAN ASSERTED THE SAFE HALF OF ITS IMPORT ARGUMENT AND OMITTED THE NOTABLE HALF. It says `layout` stays import-light, which is true; it does not say that three of the modules being edited currently import NOTHING from the package, so this adds their first edge. The invariant that makes it safe (a leaf cannot cycle) holds only while nobody adds an import to the new module, and nothing recorded that. Separately, E-04's instruction routed `ipd_schema` through `attention_contract`, which it does not import, adding a second avoidable edge to reach a value the leaf table already holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states the measurement and requires the no-cycle reason in the new module's docstring. E-05 now derives BOTH spec re-listings from the table directly, with the reason that `ipd_schema` does not import `attention_contract`. V-05 requires the diff to show no new `attention_contract` import. Conventions bullet records the zero-import measurement. |
| PR-708 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences (approve-first, commit path, "Move this plan to `.aw/records/plans/executed/`"); `- Cohesion rationale: not required` against what is now 9 items | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS. No statement of what a human is approving (and there are two things here worth a look: the first intra-package import into three dependency-free modules, and the new module becoming authority for a spec-pinned sequence); no scope fence naming the intended surface per path, on a plan touching eleven files; no stop conditions; and a transition instruction naming a directory move rather than the runner's ownership or `aw ipd finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming both notable consequences; a per-path scope fence stated as a DECLARATION with an explicitly-not-in-scope list mirroring Deferred, and the finalize-justifies-afterwards rule rather than a stop-on-scope directive; the hard-MUST honesty rule naming the two specific temptations (a combined V-02/V-03 run, and citing the guard as evidence about `record_placement`); three genuine stop conditions; and the transition with conditional runner/executor ownership and no hand-rolled `git mv`. Filled in the cohesion rationale. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the table's spec-row ORDER come from, given the plan named an unordered frozenset? | `layout`'s `specs` `lifecycle_subdirs` tuple, written into the new module as a literal, with a three-seed determinism check. | (a) Follow the plan and derive from `SPEC_STATUSES` - rejected: measured non-deterministic across processes, and it would emit a permutation of an array approved spec `kw5y2s` pins. (b) `sorted(SPEC_STATUSES)` for determinism - rejected: deterministic but WRONG, since alphabetical order is not the spec's order and the emitted JSON would change. (c) Ask the maintainer - rejected: the spec states the required sequence explicitly, so the repository answers it. | `type(SPEC_STATUSES)` is `frozenset`; three interpreters gave three orders; spec `kw5y2s`'s pinned JSON array; `to_dict` emits `list(rc.lifecycle_subdirs)` positionally | yes |
| D-2 | Should the agreement test and the drift guard stay one E-item, given they share a file? | Split them, because their pre-migration expectations are opposite. | (a) Keep one item and sharpen its expected outcome to name both classes - rejected: V-02 would still read one aggregate result, and the specific inversion (broken baseline, healthy guard) satisfies "nonzero failed count" while invalidating every later comparison in the plan. (b) Put them in two FILES - rejected as churn: one file is fine, two items and two V-items is what the evidence needs. | Verified every agreement assertion passes at HEAD, so PASS is the correct pre-migration expectation for one class and FAIL for the other | yes |
| D-3 | The plan's inventory missed `backlog set`'s status join. Add it here, or file it separately? | Add it to E-07, in this plan. | (a) File a follow-up backlog item - rejected: it is the same join, in the same module, converted by the same one-line change, and splitting a matched pair is what leaves a "single source" refactor partial. (b) Leave it and note it - rejected: an unconverted twin beside a converted one reads as a deliberate exception to a later maintainer. | `backlog`'s two joins are textually the same shape; `target_subdir("backlog", s)` measured an identity for every input, so converting both is behavior-neutral | yes |
| D-4 | Should `ipd_authoring`'s hardcoded `.aw/records/plans` type-dir prefix also be routed through `record_placement`? | No. Convert only the `"pending"` subdir; decline the prefix with a reason. | (a) Convert both for consistency - rejected: the resulting path feeds `_existing_plan_ids`, whose `_plans_root_for` walk expects that shape, so it is an unmeasured behavior change. (b) Say nothing about the prefix - rejected: it sits in the same statement E-07 edits, so silence invites the change. | `_existing_plan_ids` / `_plans_root_for` consume the path; the backlog item asks for status-subdir unification, not type-dir resolution | yes |
