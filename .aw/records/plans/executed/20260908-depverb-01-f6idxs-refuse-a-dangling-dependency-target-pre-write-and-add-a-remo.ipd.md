# IPD: Refuse a dangling dependency target pre-write and add a remove verb

- Date: 2026-09-08
- Kind: child
- Concern: `aw ipd dependencies set` validates the dependency GRAMMAR before writing but not the target's EXISTENCE, so a typo is accepted and written, and the error arrives later from a different surface (`aw check`). That directly contradicts the maintainer's stated requirement that "the id6/setid MUST be validated before it can be set or removed". Separately there is no `remove` subcommand at all, so dropping ONE edge from a many-edge statement means re-stating the whole list by hand, which is the hand-editing the verbs exist to prevent and which silently races a concurrent edit.
- Scope: The two gaps that are unambiguous and self-contained. IN: pre-write existence validation with an explicit escape hatch for a deliberate forward reference, and a `remove` subcommand that drops a single edge idempotently. OUT: source-side dependency fields on backlog and specs, setid-valued edges, and a close-time dependency gate, each of which needs a design decision or a prerequisite this plan does not own.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_dependency_verb.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: depverb
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f6idxs
- From-Backlog: rxoazt

## Workflow history
- 2026-09-13 executed (aw oc run): aw oc run self-finalize: f6idxs verified (set depverb, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/command_surface.py: changed by the plan's approved execution (auto-reconciled by aw oc run); out-of-scope tests/test_ipd_item_dependencies.py: changed by the plan's approved execution (auto-reconciled by aw oc run)]
- 2026-09-13 executed (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTED in lane `f6idxs` of run `run-20260913T031521Z-1774617`, commit `ecf5c703`. All six E-items performed and all six V-items verified with pasted evidence. SUITE: baseline `6034 passed, 3 skipped, 2 xfailed`, after `6074 passed, 3 skipped, 2 xfailed`, delta exactly the 40 new tests, no regressions. `aw check` gains NO diagnostic: finding counts identical rule-for-rule against pristine HEAD (201 = 201) and zero `check.ipd-dependency-*` on the live tree. `aw ipd lint --phase pre-transition` CONFORMING.
  THE REVIEW'S CENTRAL FINDING WAS FOLLOWED AND HELD UP. E-01 resolves through `check_engine.build_dependency_index` + `_resolve_edge`, NOT `match_selector`, so the setter and `aw check` provably name the same condition (V-01 pastes both verdicts side by side), and the `ambiguous` verdict F-11 uncovered is refused unconditionally, including under `--allow-dangling`.
  ONE FINDING CORRECTED, RECORDED RATHER THAN WORKED AROUND (D3). F-14 and E-03 both stated the grammar 'redirects `state:ipd:executed:` to canonical `executed:`'. MEASURED: it REFUSES it (`ipd_schema._parse_item_dependency_edge` returns 'is illegal; use the canonical ...'), and that refusal is deliberate per spec 2.7, which requires the `executed:` spelling so execution EVIDENCE is also demanded. Implementing the predicted redirect would have weakened a shipped contract, so the refusal is now PINNED for both verbs and canonical matching is proven with a spelling the grammar genuinely accepts (reordering plus whitespace). E-06's case (l) is satisfied; only its example changed.
  E-05 ROUTE CHOSEN ON MEASUREMENT (D1): an EQUIVALENT in-fence guard, not an extension of `_DRIVER_SOURCES`. Three of the four existing guard bodies are driver-specific, and decisively `test_drivers_reference_the_shared_dependency_api` requires `META_ITEM_DEPENDENCIES` in the source, measured TRUE for `status_set.py` but FALSE for `cli.py`. Extending would have forced a false assertion or a per-file exemption; `tests/test_runner_item_dependencies.py` was NOT modified and still passes.
  TWO OUT-OF-FENCE PATHS NEED A `--scope-reason` AT FINALIZE (D4), neither opportunistic: `agent_workflows/command_surface.py` (a new parser leaf without a `CommandDeclaration` fails `find_undeclared_leaves` in CI, so the verb E-03 mandates cannot exist without it) and `tests/test_ipd_item_dependencies.py` (fixture seeding only, for a case whose invented target ids the new pre-write check correctly refuses; its subject is canonical ordering, so seeding preserves its intent rather than converting it into a test of the escape hatch).
  NO SPEC AMENDMENT (D5): spec 2.7's 'only supported writer' sentence contrasts the TOOL with a hand edit, and `remove` upholds it by calling the SAME writer rather than adding one; the two `set` forms shown are illustrative, not an exhaustive enumeration bound by a test (unlike 2.1's flag grammar). Recorded as an optional documentation follow-up, not a contradiction.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-001..PR-008, ALL EIGHT FIXED, no open findings. `aw ipd lint --phase author` CONFORMING before semantic review and `--phase review-finalize` CONFORMING after every revision, so nothing here is structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on RE-RUNNING rather than re-reading: a fresh probe repo was built and the four gap claims were EXECUTED against the real CLI, and both candidate resolvers were CALLED in-process against the live tree.
  THE FINDING THAT CHANGES WHAT GETS BUILT. E-01's INSTRUCTION WOULD HAVE CREATED THE SECOND AUTHORITY E-05 FORBIDS (PR-002, F-11). It said to resolve targets "through the shared selector resolver so the setter agrees with `aw find` and with `aw check`". Measured: `aw check` does NOT use the selector resolver for edges. `evaluate_ipd_dependencies` calls `build_dependency_index` (`check_engine.py:2347`) and `_resolve_edge` (`:2368`), a purpose-built edge resolver that enforces the edge's TYPE via `ITEM_DEP_TYPE_TO_RECORD_TYPE` and returns a THREE-WAY verdict `ok`/`dangling`/`ambiguous`, which `match_selector` has no concept of. The divergence is real, not theoretical: id6 `uyeko5` is owned by one `plans` record and TWO `research` records in this repository today. So the two E-items contradicted each other, and following E-01 would have made the setter disagree with `aw check` about the exact class of edge it exists to validate. E-01 now uses `_resolve_edge`, which satisfies E-05 by construction and gains the ambiguous verdict; E-02 is scoped so `--allow-dangling` covers `dangling` and never `ambiguous`, since an ambiguous edge cannot become valid by waiting.
  ALSO FIXED. The anti-divergence guard E-05 cites CANNOT SEE this plan's code (PR-003, F-12): `AntiDivergenceGuardTests` scans `_DRIVER_SOURCES`, which is exactly `oc_runipd.py` and `agy_runipd.py`, so it would pass unchanged even if this work added a private dependency regex; E-05 must extend it (an out-of-fence `--scope-reason` edit) or write an equivalent, and record which. Three behaviors `remove` needs were unspecified (PR-004, F-14): it must match edges in CANONICAL form (the parser redirects `state:ipd:executed:` to `executed:`, so a raw-string compare would call a correct request absent), it must NOT inherit E-01's validation or a dangling edge becomes unremovable, and the setter's multi-plan loop means the absent-edge decision fires per plan with `rc_final` accumulating rather than aborting. The reproduction was UNDERSTATED (PR-001): the plan cited a dry run exiting 0, but the real write also exits 0 and genuinely persists the dangling value, in all three edge forms. Two side effects would have broken naive tests (PR-005, F-13): the setter appends a history receipt and, on an `approved` plan, rewrites `- Approval:`; both are `apply_status_change`'s shared behavior for every setter, so they are out of scope, but assertions must be scoped to the dependency line. F-6 was STALE and the deferral is now stronger (PR-006, F-15): `sjsoqq` is `graduated`, not `open`, into the live four-plan `setidhard` Set, so GAP 3's prerequisite is actively under design rather than merely unlanded. Both open questions were owned by `reviewer`/`executor` and answerable, so both are now `resolved` (PR-007), with OQ-02 confirmed from the parser (`unresolved` returns `ready=False` while `none` returns `ready=True`, so writing `unresolved` on removal would flip the plan not-ready as a side effect). The baseline named the wrong failing test (PR-008): measured `1 failed, 5919 passed, 3 skipped, 2 xfailed` in `test_reporting_contract`, environmental, not `5648`/`test_orchestrator_retirement`.
  CONFIRMED SOUND, AND THE NARROWING IS THE PLAN'S BEST DECISION. All four gap claims reproduce exactly as described, including GAP 3's refusal being CORRECT behavior with its verbatim message, which is the finding that justifies deferring it. The judgement to graduate two of five gaps is right, and each deferral names a real design decision or prerequisite rather than a preference. The single-evaluator discipline, the `none`-not-blank zero, the inherited no-op write path, and the neighbouring-fields distinction are all accurate. `2k42zu` really is `done`, so the item's own open question really is answered by events.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rxoazt`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. THIS IS A NARROWING: the item names FIVE gaps and this plan graduates TWO, with the reasons per gap recorded below and in Deferred. ALL FIVE RE-VERIFIED AT HEAD `a2e0438a` and all five are still live, so nothing is graduated as obsolete; the narrowing is about ownership and prerequisites, not staleness. GAP 4 (validation not pre-write) reproduces exactly: `aw ipd dependencies set <plan> exists:backlog:zzzzzz --dry-run --yes` reports `unchanged (dry-run)` and exits 0, although `zzzzzz` matches no artifact. GAP 2 (no remove) reproduces: `aw ipd dependencies --help` shows the subcommand choices as `{set}` only. GAP 1 reproduces: `aw backlog new`, `aw backlog set` and `aw specs set` each return zero matches for a dependency flag. GAP 3 reproduces and is CORRECT-BY-DESIGN today: `exists:backlog:worksequence` is refused pre-write with "exists target 'worksequence' is not a 6-char base36 id6. Refusing before making changes." and exit 2, which is the grammar path working. THE ITEM'S OPEN QUESTION IS NOW ANSWERED BY EVENTS, which is the main change since filing. It asks whether this item should be MERGED INTO `2k42zu` (`worksequence`), which owned the generalize-dependencies-beyond-plans question, and says to decide that before authoring. `2k42zu` IS NOW `done`, closed 2026-09-05 by the execution of IPD `i6015i` (the `aw next --order-by` work) with that plan cited as its evidence. So there is no live sibling to merge into, and this item correctly stays separate as the narrower CLI/validation item. That also REMOVES the stated blocker on GAP 1, but GAP 1 is still deferred here for a different reason recorded in Deferred: it is a spec-sanctioned follow-on that adds a FIELD to two artifact types, which is a data-model change deserving its own plan rather than riding along with a setter fix. GAP 3's prerequisite is unchanged and still open: `sjsoqq` (`setiduniq`, cross-type setid uniqueness) is `open`, and the item calls it "a likely prerequisite" because a setid edge could resolve ambiguously until it lands.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the dependency setter honor its own contract. A target that does not exist should be refused before anything is written, in the same breath as a malformed one, and removing one edge should be a verb rather than a hand-rewrite of the whole statement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: validate existence before writing

- [x] E-01 Resolve every dependency TARGET and refuse pre-write when it does not resolve, in `run_dependencies_set_command` (find by SYMBOL; `agent_workflows/status_set.py:1489` at review, not `:1515`). The function already validates and canonicalizes the grammar BEFORE any write via `ipd_schema.canonical_item_dependencies` and refuses with "Refusing before making changes." (`:1527-1534`), so this adds an EXISTENCE check alongside the existing GRAMMAR check at the same point, reusing that refusal contract and its wording rather than inventing a second failure shape. Cover all three edge forms the grammar admits, since each names a target differently: `executed:<id6>`, `exists:<type>:<id6>` and `state:<type>:<status>:<id6>`. RE-MEASURED AT REVIEW at HEAD `0a2626c9`: all THREE forms are accepted today with exit 0 and the value is genuinely WRITTEN (not merely dry-run clean), which is a stronger reproduction than the plan's original dry-run-only evidence.
  USE `check_engine._resolve_edge` PLUS `build_dependency_index`, NOT THE SELECTOR RESOLVER, AND THIS IS THE ITEM'S MOST IMPORTANT CORRECTION (F-11). The authored instruction said to "resolve the target through the shared selector resolver so the setter agrees with `aw find` and with `aw check`". Measured, that would make the setter DISAGREE with `aw check`, because `aw check` does not use the selector resolver at all: `evaluate_ipd_dependencies` calls `build_dependency_index` (`check_engine.py:2347`) and `_resolve_edge` (`:2368`), which is a PURPOSE-BUILT edge resolver that (a) enforces the edge's TYPE via `ITEM_DEP_TYPE_TO_RECORD_TYPE` and (b) returns a three-way verdict `ok`/`dangling`/`ambiguous`. A `match_selector` existence check has no ambiguity concept, and the divergence is REAL rather than theoretical: id6 `uyeko5` is owned by one `plans` record AND two `research` records in this repository today, so `match_selector("uyeko5", scoped_type="plans")` returns one hit (a naive check says OK) while the shared evaluator can classify the same id6's ownership. Reusing `_resolve_edge` gets the type check and the ambiguous verdict for free and satisfies E-05 by construction; building on `match_selector` would create the second authority E-05 forbids.
  REFUSE ON `ambiguous` TOO, NOT ONLY ON `dangling`, since `_resolve_edge` returns both and `check.ipd-dependency-ambiguous` is a real rule. An ambiguous target is not a forward reference and must NOT be admitted by `--allow-dangling`; decide and state whether it is refusable at all (the reviewer's reading: yes, unconditionally, because unlike a dangling edge it can never become valid by the target being authored later).
  - Depends on: none
  - Expected outcome: a dangling target in any of the three forms exits nonzero with nothing written; an AMBIGUOUS target likewise, and not coverable by the escape hatch; a valid target still succeeds; the refusal text matches the existing pre-write refusal contract; the resolution goes through `_resolve_edge`, so the setter and `aw check` cannot disagree.
  - Execution state: performed

- [x] E-02 Add the explicit escape hatch the item requires a decision on, rather than leaving today's accidental permissiveness. The item is direct: "authoring a chain top-down may legitimately need a forward reference to a plan that does not exist yet, so either require `--allow-dangling` for that case or require the target to exist unconditionally, but decide it rather than leaving today's accidental permissiveness." IMPLEMENT `--allow-dangling`, because the forward-reference case is real in this repository (Sets are routinely authored parent-first with children named before they exist) and an unconditional requirement would make that workflow impossible. The flag must be LOUD, not silent: print which targets were accepted as dangling, so the deferral is visible in the transcript, and note the edge remains fail-closed at the repository gate afterwards because `aw check` still reports it (`check.ipd-dependency-dangling` is `error` severity, `check_engine.py:211`).
  SCOPE THE HATCH TO `dangling` ONLY. `_resolve_edge` also returns `ambiguous`, and that verdict is not a forward reference: an id6 owned by two artifacts does not become unambiguous by waiting, so admitting it under this flag would let the setter write an edge that can never resolve. State that boundary in the flag's help text, not only here.
  - Depends on: E-01
  - Expected outcome: without the flag a dangling target refuses; with it the write proceeds and NAMES each dangling target; an ambiguous target still refuses even WITH the flag; `aw check` still reports the dangling edge afterwards.
  - Execution state: performed

### Task group 2: add the remove verb

- [x] E-03 Add `aw ipd dependencies remove <selector> <edge...>`, registered beside `set` in `cli.py`. RE-MEASURED AT REVIEW: `aw ipd dependencies --help` shows the choices as `{set}` and `aw ipd dependencies remove ...` fails with `invalid choice: 'remove' (choose from 'set')`, exit 2. Implement it by REUSING the same machinery `set` uses rather than writing a second write path: `run_dependencies_set_command` drives a same-status no-op transition through `run_set_command` carrying the canonicalized value in `args.item_dependencies` (`status_set.py:1556-1573`), so persistence-on-no-op is inherited. Removal is therefore "parse the current statement, drop the named edges, canonicalize, write the remainder", and when the remainder is empty it must write the explicit zero `none` rather than an empty string, since `none` is the grammar's zero and an empty value would be malformed.
  COMPARE EDGES IN CANONICAL FORM, NOT AS RAW STRINGS. `ipd_schema` gives every edge a `canonical()` rendering and `canonical_item_dependencies` normalizes an entire statement, so `remove` must canonicalize the operator's tokens BEFORE matching them against the parsed statement. Otherwise a spelling difference that the grammar treats as identical (whitespace, ordering, or the `state:ipd:executed:` form the parser explicitly redirects to canonical `executed:`) would be reported as an absent edge and refused by E-04, which would be a false negative on a correct request.
  REMOVAL MUST NOT VALIDATE EXISTENCE. An operator removing an edge whose target has since been deleted is the NORMAL repair case, so E-01's refusal must not apply to `remove`; wiring the new verb through a shared code path that validates targets would make a dangling edge unremovable, which is the opposite of the item's intent. State this explicitly and test it (E-06).
  MIND THE SELECTOR'S MULTI-MATCH LOOP. `run_dependencies_set_command` iterates `plan_matches` and drives one transition PER matched plan (`status_set.py:1555`), because a Set selector legitimately matches several plans. For `remove` that means the same edge is dropped from each matched plan and the ABSENT-EDGE decision in E-04 fires PER PLAN; decide and state whether one plan lacking the edge fails the whole invocation or only that plan, since the loop today accumulates `rc_final` rather than aborting.
  - Depends on: none
  - Expected outcome: removing one edge from a multi-edge statement leaves the others byte-identical; removing the last edge yields `none`; edges matched in canonical form; a dangling edge is still REMOVABLE; the multi-match semantics stated; the write goes through the existing no-op transition path.
  - Execution state: performed

- [x] E-04 Define the ABSENT-EDGE semantics deliberately, per the item: "remove a single edge idempotently, and error (not silently no-op) when the named edge is absent, unless a `--if-present` style flag is passed." So the default is an ERROR naming the edge that was not found, and `--if-present` downgrades it to a no-op with a notice. The distinction matters because a silent no-op on a typo'd edge would leave the operator believing they removed something they did not, which is the same class of failure as GAP 4 one level up. Also state and test the IDEMPOTENCY property that the item asks for: removing an edge that is already gone under `--if-present` must be a clean no-op, not a partial write.
  - Depends on: E-03
  - Expected outcome: removing an absent edge exits nonzero and names it; `--if-present` makes it exit 0 with a notice and no file change; repeated removal under `--if-present` is stable.
  - Execution state: performed

### Task group 3: prove it and keep one authority

- [x] E-05 Do NOT add a second evaluator or a second parser, and prove it. Spec `25kzda` section 2.10 is explicit: "All surfaces call this evaluator; none reimplements it." `check_engine.evaluate_ipd_dependencies` (find by symbol; `check_engine.py:2394` at review) is already consumed by `aw check` (`:2638`), `aw ipd lint` (`ipd_lint.py:1147`), the runner preflight (`oc_runipd.py:2562`) and the opt-in staged-overlay hook. The grammar authority is likewise single: `ipd_schema.parse_item_dependencies` (`:722`) and `canonical_item_dependencies` (`:778`).
  E-01 MUST USE `_resolve_edge`, NOT THE SELECTOR RESOLVER, WHICH IS WHAT MAKES THIS ITEM SATISFIABLE RATHER THAN CONTRADICTORY (F-11). The authored plan told E-01 to use the selector resolver and told E-05 to prove no second authority appeared; those two instructions conflict, because `aw check` resolves edges through `build_dependency_index` + `_resolve_edge` and NOT through `match_selector`. Reusing `_resolve_edge` satisfies both instructions at once.
  THE GUARD YOU ARE MIRRORING DOES NOT COVER YOUR FILE, SO EXTEND IT DELIBERATELY OR SAY WHY NOT. `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` scans `_DRIVER_SOURCES`, which is exactly `oc_runipd.py` and `agy_runipd.py` (`:46-49`); `status_set.py` and `cli.py` are NOT scanned, so the existing guard would pass unchanged even if this plan added a private dependency regex. Either add the two touched modules to that guard's source list (a `tests/test_runner_item_dependencies.py` edit, which is NOT in `Scope-Paths` and needs a `--scope-reason`), or put an equivalent guard in the new `tests/test_dependency_verb.py`. Choose and record; do not claim the existing guard covers work it cannot see.
  - Depends on: E-01, E-03
  - Expected outcome: a grep proving one grammar parser and one edge resolver remain; no new regex in either touched module; the four existing consumers unchanged; the anti-divergence guard demonstrably COVERING `status_set.py` and `cli.py`, either by extension or by a new equivalent, with the choice recorded.
  - Execution state: performed

- [x] E-06 Test the matrix, and pin the behaviors that must NOT change. Cover: each of the three edge forms with a dangling target refused pre-write; a valid target accepted; `--allow-dangling` accepting and naming; removing one edge of three; removing the last edge yielding `none`; removing an absent edge erroring; `--if-present` downgrading that to a no-op; and the two behaviors that already work correctly and must be preserved, namely the GRAMMAR refusal for a setid-shaped target (`exists:backlog:worksequence` -> exit 2, "not a 6-char base36 id6. Refusing before making changes.", nothing written, RE-VERIFIED at review) and the existing clear-by-empty-or-`none` behavior of `set`.
  THREE MORE CASES, EACH FROM A REVIEW MEASUREMENT. (j) AN AMBIGUOUS TARGET REFUSES, AND STILL REFUSES UNDER `--allow-dangling`, since `_resolve_edge` returns that third verdict and E-01/E-02 now handle it; seed the fixture with one id6 owned by two record types, which is a state this repository genuinely contains (`uyeko5`: one `plans` and two `research` records). (k) A DANGLING EDGE IS STILL REMOVABLE, proving E-01's validation does not leak into `remove` and make a broken edge unfixable. (l) AN EDGE SPELLED NON-CANONICALLY IS STILL MATCHED BY `remove` (for example a `state:ipd:executed:<id6>` token, which the parser redirects to canonical `executed:<id6>`), proving E-03 compares canonical forms rather than raw strings.
  ASSERT THE FAILING-FIRST CASE AGAINST THE WRITE, NOT THE DRY RUN. The plan cited a dry run exiting 0; review measured something stronger, so assert that: at HEAD, `aw ipd dependencies set <plan> exists:backlog:zzzzzz --yes` exits 0 AND the dangling value is genuinely written into `- Item-Dependencies:`. A dry-run-only assertion would understate the defect.
  Use a FIXTURE repository, not the live tree, since these are MUTATING verbs. Note the setter also appends a `## Workflow history` receipt and, for an `approved` plan, REWRITES the `- Approval:` line (measured at review; this is `apply_status_change`'s shared behavior for every setter, not deps-specific, F-13). Assert the dependency line, not whole-file equality, or the tests will fail on that unrelated churn.
  - Depends on: E-02, E-04, E-05
  - Expected outcome: TWELVE cases passing in a fixture repo; the dangling-refusal case shown failing before the change against a real WRITE; the setid grammar refusal and the clear path unchanged; assertions scoped to the dependency line so the receipt/Approval churn does not produce false failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

All line numbers below were RE-MEASURED AT REVIEW at HEAD `0a2626c9`; the authored plan cited `a2e0438a` and several had drifted. Locate by SYMBOL.

- MOST OF THE REQUESTED MODEL ALREADY SHIPPED, via the `ipddeps` Set (`r7xku3`, `g69y23`, `ovbnyq`, `mp88bl`, all executed), graduated from spec `25kzda` sections 2.7-2.11. The typed field, zero/one/many, a setter, and runner/checker/hook consumption all exist. This plan closes gaps, it does not build the model.
- ONE evaluator is a spec requirement, not a preference: section 2.10 says every surface calls it and none reimplements it. Four surfaces already do (`aw check` at `check_engine.py:2638`, `aw ipd lint` at `ipd_lint.py:1147`, the runner preflight at `oc_runipd.py:2562`, and the staged-overlay hook).
- THE EDGE RESOLVER IS A DISTINCT SHARED AUTHORITY FROM THE SELECTOR RESOLVER, AND THIS IS THE DISTINCTION THE PLAN ORIGINALLY MISSED. `aw check` resolves an edge with `build_dependency_index` (`check_engine.py:2347`) plus `_resolve_edge` (`:2368`), which enforces the edge's TYPE through `ipd_schema.ITEM_DEP_TYPE_TO_RECORD_TYPE` and returns `ok`/`dangling`/`ambiguous`. `status_set.match_selector` is a different mechanism with no type enforcement for edges and no ambiguity verdict. Measured divergence: id6 `uyeko5` is owned by one `plans` and two `research` records in this repository, so a `match_selector`-based existence check and the shared evaluator can reach different conclusions about the same id6. Any pre-write existence check must go through `_resolve_edge`.
- THE GRAMMAR HAS A SINGLE AUTHORITY in `ipd_schema` and an explicit ZERO value (`none`), which is why an emptied statement must become `none` rather than blank. It also CANONICALIZES: `state:ipd:executed:<id6>` is refused in favor of `executed:<id6>` (`ipd_schema.py:693-698`), so any edge comparison must be on canonical form.
- `run_dependencies_set_command` (`status_set.py:1489`) deliberately reuses the hoisted same-status write from `aw ipd set --from-backlog`, so persistence-on-a-no-op is inherited rather than reimplemented. A remove verb should inherit the same way.
- THE SETTER LOOPS OVER EVERY MATCHED PLAN. `plan_matches` may hold several records because a Set selector legitimately matches many, and the loop (`:1555`) drives one no-op transition per plan while ACCUMULATING `rc_final` rather than aborting on the first failure. Any per-plan decision (a dangling refusal, an absent-edge error) therefore fires per plan, and the all-or-nothing question must be answered rather than inherited by accident.
- The pre-write refusal contract already exists and has established wording ("Refusing before making changes."), used by both the scope check and the grammar check in `status_set.py` (`:1527-1534`).
- THE SETTER ALSO WRITES A HISTORY RECEIPT AND MAY REWRITE `- Approval:`. Measured at review: setting a dependency on an `approved` plan appends `- 2026-09-09 approved (aw set): set Item-Dependencies to ...` AND rewrites the `- Approval:` line to `recorded via aw ipd set: set Item-Dependencies to ...`. That is `apply_status_change`'s shared behavior for EVERY setter (a direct `aw ipd set approved` rewrites the same line), not a deps-specific defect, and it is out of scope; but a test asserting whole-file equality would fail on it, so scope assertions to the dependency line.
- `Item-Dependencies` must not be confused with three neighbours: the intra-plan `Depends on:` E-row field (a different namespace by spec 2.8, where an E-id is never legal in `Item-Dependencies` and an id6 never legal in an E row), `Gate-Kind`/`Gate-Ref` (the item's own blocked state), and `Blocks-Release` (which points at a release).
- The dangling-edge rule is `error` severity at the repository gate (`check_engine.py:211`), so nothing ships broken today; the defect is that the error arrives LATE and from a different surface.
- THE ANTI-DIVERGENCE GUARD DOES NOT COVER THIS PLAN'S FILES. `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` scans `_DRIVER_SOURCES` (`:46-49`), which is exactly `oc_runipd.py` and `agy_runipd.py`. Neither `status_set.py` nor `cli.py` is scanned, so citing that guard as proof of no-second-parser in THIS work is citing a test that cannot see the code. E-05 must extend it or add an equivalent.
- Honest limit worth restating: a git pre-commit hook is local, not cloned, and skippable, so the portable authority stays `aw check` plus CI.
- SUITE BASELINE RE-MEASURED at review on `0a2626c9`: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by 189 untracked `opencode-recovery/*.md` files belonging to another party in this shared checkout. It is ENVIRONMENTAL, it is NOT the `test_orchestrator_retirement` case the plan named, and it must not be fixed. Run the suite BARE; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.

## Findings

F-1..F-10 were authored at HEAD `a2e0438a`. F-11..F-15 were added at review at HEAD `0a2626c9`, where every authored claim was RE-RUN in a fresh probe repo rather than re-read.

| # | Finding | Evidence |
|---|---|---|
| F-1 | GAP 4 REPRODUCES, AND MORE STRONGLY THAN RECORDED. The plan cited a dry run exiting 0. Measured at review, the non-dry-run invocation also exits 0 and genuinely WRITES the dangling value: `- Item-Dependencies: exists:backlog:zzzzzz` appears in the file. All THREE edge forms behave this way (`executed:zzzzzz`, `exists:backlog:zzzzzz`, `state:spec:approved:zzzzzz`), each exit 0, each written. | fresh probe repo at review |
| F-2 | GAP 2 REPRODUCES: choices are `{set}` only; `remove` fails with `invalid choice: 'remove' (choose from 'set')`, exit 2. CONFIRMED. | `aw ipd dependencies --help` and a live invocation at review |
| F-3 | GAP 1 REPRODUCES: `aw backlog new`, `aw backlog set` and `aw specs set` all return zero matches for a dependency flag. | measured at `a2e0438a` |
| F-4 | GAP 3 REPRODUCES and today's refusal is CORRECT: a setid-shaped target is refused pre-write with "exists target 'worksequence' is not a 6-char base36 id6. Refusing before making changes." and exit 2, nothing written. RE-VERIFIED verbatim at review. So GAP 3 is a feature request rather than a defect. | probe at review |
| F-5 | THE ITEM'S OPEN QUESTION IS ANSWERED BY EVENTS: `2k42zu`, the sibling it asks whether to merge into, is now `done`. CONFIRMED (`- Status: done`). So this item correctly stays separate and there is no duplicate to reconcile. | `.aw/records/backlog/done/...2k42zu...backlog.md` |
| F-6 | SUPERSEDED BY F-15. Authored as "GAP 3's prerequisite is still open: `sjsoqq` is `open`". It is now `graduated`, and its four-plan `setidhard` Set is live in `pending/`. The deferral still holds but its REASON changed. | superseded at review |
| F-7 | The pre-write refusal seam already exists and is where E-01 belongs. Citations corrected: the function is at `status_set.py:1489` (not `:1515`) and the grammar refusal at `:1527-1534` (not `:1558`). | source read at review |
| F-8 | ONE evaluator is already the reality across four surfaces, so E-05 preserves rather than establishes it. Citations corrected: `check_engine.py:2394` consumed at `:2638`, `ipd_lint.py:1147`, `oc_runipd.py:2562`, plus the staged-overlay hook. | grep at review |
| F-9 | The removal path can inherit the existing write: `set` drives a same-status no-op transition carrying the canonicalized value, so persistence-on-no-op is already solved. CONFIRMED at `status_set.py:1556-1573`. | source read |
| F-10 | Nothing else covers this item: no pending or approved plan touches the dependency setter or adds a remove verb. | grep over `.aw/records/plans/pending/` |
| F-11 | **E-01's INSTRUCTION WOULD HAVE CREATED THE SECOND AUTHORITY E-05 FORBIDS.** It says to resolve targets "through the shared selector resolver so the setter agrees with `aw find` and with `aw check`". Measured: `aw check` does NOT use the selector resolver for edges. `evaluate_ipd_dependencies` calls `build_dependency_index` (`check_engine.py:2347`) and `_resolve_edge` (`:2368`), a purpose-built edge resolver that enforces the edge's type via `ITEM_DEP_TYPE_TO_RECORD_TYPE` and returns a THREE-WAY verdict `ok`/`dangling`/`ambiguous`. `match_selector` has neither. The divergence is real: id6 `uyeko5` is owned by one `plans` record and TWO `research` records in this repository, so `match_selector("uyeko5", scoped_type="plans")` returns one hit while the shared index records three owners. So E-01-as-authored would make the setter disagree with `aw check` on the exact class of edge it exists to validate, and E-05 would then have to fail its own item. | called both resolvers in-process against the live tree |
| F-12 | **THE ANTI-DIVERGENCE GUARD E-05 CITES CANNOT SEE THIS PLAN'S CODE.** `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` scans `_DRIVER_SOURCES` = exactly `oc_runipd.py` and `agy_runipd.py` (`:46-49`). Neither `status_set.py` nor `cli.py` is in that tuple, so the guard passes unchanged even if this work added a private dependency regex, and "mirroring the discipline" it enforces is not the same as being covered by it. `tests/test_runner_item_dependencies.py` is also NOT in `Scope-Paths`, so extending the guard needs a `--scope-reason`. | read the guard and its source tuple |
| F-13 | The setter has TWO side effects a whole-file assertion would trip on, neither deps-specific: it appends a `## Workflow history` receipt, and on an `approved` plan it REWRITES the `- Approval:` line to "recorded via aw ipd set: set Item-Dependencies to ...". Measured: a direct `aw ipd set approved` rewrites the same line, so this is `apply_status_change`'s shared behavior rather than a defect of this verb. Out of scope; but E-06's assertions must be scoped to the dependency line. | probe at review, `approved` and `reviewed` controls |
| F-14 | `remove` MUST NOT INHERIT E-01's VALIDATION, and the plan never said so. Removing an edge whose target has since been deleted is the normal repair case; if the new verb shares a code path that validates targets, a dangling edge becomes unremovable, which inverts the item's intent. Related: `remove` must match edges in CANONICAL form, because the parser redirects `state:ipd:executed:<id6>` to `executed:<id6>` (`ipd_schema.py:693-698`), so a raw-string comparison would report a correctly-spelled request as an absent edge. | grammar source read; E-04's absent-edge rule |
| F-15 | GAP 3's DEFERRAL REASON IS STALE BUT THE DEFERRAL IS STRONGER. `sjsoqq` is now `graduated`, not `open`, and it graduated into a live FOUR-PLAN Set (`setidhard` `yku4ga`/`drzbs9`/`bwgyum`/`dw7i3m`, two `reviewed` and two `to-review`) whose Order 03 is the setid-collision refusal this plan's sibling `e3hzyc` also cites. So the prerequisite is not merely unlanded, it is actively being designed by four plans, which is a better reason to keep setid-valued edges out than "the prerequisite is open". | backlog and plan front matter read at review |

## Proposed changes (ordered, validatable)

1. Refuse a dangling OR ambiguous target pre-write for all three edge forms, resolving through `check_engine._resolve_edge` so the setter cannot disagree with `aw check` (E-01).
2. Add a loud `--allow-dangling` escape hatch for deliberate forward references, scoped to `dangling` and never to `ambiguous` (E-02).
3. Add `aw ipd dependencies remove`, reusing the existing write path, matching edges canonically, leaving dangling edges removable, and writing `none` when emptied (E-03).
4. Make an absent edge an error by default, with `--if-present` downgrading it (E-04).
5. Prove one grammar parser and one edge resolver remain, and make the anti-divergence guard actually cover the touched modules (E-05).
6. Pin twelve cases in a fixture repo, including the three behaviors that must not change and the ambiguous, dangling-removal and canonical-matching cases (E-06).

## Deferred / out of scope (with reason)

- GAP 1, SOURCE-SIDE DEPENDENCY FIELDS ON BACKLOG AND SPECS. Spec `25kzda` section 2.92 deliberately deferred this ("A later design may add source-side dependency fields to those types, but the runner must not infer them from prose in v1"), so closing it is a sanctioned follow-on rather than a contradiction. It is nevertheless a DATA-MODEL change adding a field to two artifact types, with its own validation, rendering, check rules and migration questions, and it would dwarf the setter fixes it was bundled with. NOTE the item's stated blocker is GONE (`2k42zu` is `done`, F-5), so this is now unblocked and worth its own plan; it is deferred on size, not on dependency.
- GAP 3, SETID-VALUED EDGES. Two reasons, the second STRENGTHENED at review (F-15). FIRST, the item itself frames it as an undecided DESIGN QUESTION, not a defect: a setid edge is one-to-many and its membership CHANGES when a plan joins the Set, so "all current members" versus "all members at evaluation time" must be specified deliberately. SECOND, its prerequisite is not merely unlanded but ACTIVELY UNDER DESIGN BY FOUR PLANS: `sjsoqq` is now `graduated` (not `open` as F-6 recorded) into the `setidhard` Set (`yku4ga`, `drzbs9`, `bwgyum`, `dw7i3m`), whose Order 03 owns the cross-type setid refusal. Designing a setid EDGE against a setid IDENTITY that four in-flight plans are still defining would be building on a moving contract. Today's refusal is correct behavior (F-4), so nothing is broken while this waits.
- GAP 5, A CLOSE-TIME DEPENDENCY GATE. The item states the decision is open ("refused, warned, or allowed") and flags a hard constraint from `2k42zu`: a close-time gate must not be able to disagree with `aw attention`. That is a policy design question about surface consistency, not a setter fix, and answering it inside this plan would smuggle a behavior change into a validation change.
- CHANGING THE `Blocks-Release` CLOSE GATE. Separate concern with its own predicate (`check_engine.evaluate_blocking_close`), explicitly distinguished from dependencies in AGENTS.md.
- THE SETTER'S `- Approval:` LINE REWRITE (F-13). Measured at review: setting a dependency on an `approved` plan rewrites `- Approval:` to "recorded via aw ipd set: set Item-Dependencies to ...", overwriting whatever attestation was there. It is `apply_status_change`'s shared behavior for EVERY setter (a direct `aw ipd set approved` does the same), so it is neither introduced nor worsened here, and changing it would touch every status verb. Out of scope; recorded so E-06 scopes its assertions to the dependency line instead of whole-file equality, and so a later reader does not mistake it for this plan's doing.

## Scope check

- Over-scope: none. Two source modules and one new test module, all required by E-01 through E-04.
- ONE POSSIBLE OUT-OF-FENCE EDIT IS FORESEEN AND SHOULD BE MADE IF E-05 CHOOSES IT: extending `AntiDivergenceGuardTests._DRIVER_SOURCES` to cover `status_set.py` and `cli.py` means editing `tests/test_runner_item_dependencies.py`, which is NOT declared. That is legitimate (the guard is the natural home) but needs a `--scope-reason` at finalize; the alternative is an equivalent guard inside the new `tests/test_dependency_verb.py`, which stays in fence. E-05 must choose and record which.
- Under-scope: three of the item's five gaps are deferred with reasons (see Deferred). This plan therefore closes the two gaps that need no new design decision and no external prerequisite. Also NOT addressed and named rather than left silent: the setter's shared `- Approval:` rewrite (F-13), which this plan neither causes nor fixes.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, before and after, with both ACTUAL summary lines pasted. Do NOT add flags (`addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`). Baseline RE-MEASURED at review on `0a2626c9`: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being the environmental `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (189 untracked `opencode-recovery/*.md` files belonging to another party). It is NOT `test_orchestrator_retirement` as originally recorded. Expect it in BOTH runs; it cancels in the delta and must not be fixed. Judge on the DELTA, never an absolute count.
- `python3 -m pytest tests/test_dependency_verb.py tests/test_runner_item_dependencies.py tests/test_ipd_dependency_check.py` for the focused surface: the second holds the anti-divergence guard E-05 must make actually cover this code, and the third pins the `check.ipd-dependency-*` rule family whose verdicts E-01 must now agree with.
- All TWELVE E-06 cases run against a FIXTURE repository, with exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), and with assertions scoped to the `- Item-Dependencies:` line rather than whole-file equality (F-13).
- THE SETTER-VERSUS-CHECKER AGREEMENT PROVEN DIRECTLY, since that is E-01's whole contract: for at least one dangling and one ambiguous edge, paste the setter's refusal beside `aw check`'s verdict on the same edge and show they name the same condition. A setter that refuses an edge `aw check` would accept, or accepts one it would reject, is the defect this plan exists to close reappearing one level up.
- `python3 -m agent_workflows check` must not gain a diagnostic, and the `check.ipd-dependency-*` rule family must behave exactly as before on unchanged artifacts.

## Spec / documentation sync

Spec `25kzda` sections 2.7-2.11 define the dependency model this plan extends at the CLI layer. E-01 IMPLEMENTS the maintainer's stated "MUST be validated before it can be set" requirement, which the spec's model permits but does not currently mandate at the setter, and E-03 adds a verb the spec does not enumerate. NEITHER changes the FIELD, the GRAMMAR, or the evaluator, so no `.spec.md` is declared in `Scope-Paths`. TWO obligations for the executor. FIRST, read section 2.10's single-evaluator rule and confirm E-05 satisfies it, reporting any place the new code would become a second authority; note review already found ONE such place in the authored plan (E-01's selector-resolver instruction, F-11), so this is not a formality. SECOND, if the spec enumerates the dependency SUBCOMMANDS such that adding `remove` contradicts it, that IS a spec amendment: declare the spec path in `Scope-Paths` and justify it BEFORE editing, per the plan-may-amend-a-spec rule. The `aw ipd dependencies --help` text is generated from the parser and updates by construction.

TWO NEW OPERATOR-FACING STRINGS NEED WRITING, and both are in `cli.py`, which IS already declared. `--allow-dangling`'s help must state that it covers a dangling target and NOT an ambiguous one, since that boundary is now part of the flag's contract and an operator reading only `--help` would otherwise assume the escape hatch covers every resolution failure. `--if-present`'s help must state that it downgrades an absent-edge error to a no-op, not that it suppresses all errors. Operator-facing prose: write no em or en dashes.

## Open questions

### OQ-01: Should `--allow-dangling` be the flag name, and should it require a reason?

- Blocking: no
- Status: resolved
- Owner: this plan's executor (E-02)
- Resolution or deferral rationale: RESOLVED AT REVIEW, since the owner was `reviewer` and this is the review. NO MANDATORY REASON, and keep the name `--allow-dangling`. The plan's own recommendation is right and the counter-argument is weaker than it looks: the `--scope-reason` precedent it cites governs a FINALIZE-TIME reconciliation where the justification is the only record of an unplanned edit, whereas here E-02 already requires the output to NAME every target accepted as dangling, and `check.ipd-dependency-dangling` remains `error` severity (`check_engine.py:211`) so the edge stays fail-closed at the gate afterwards. Two independent records already exist; a third in prose would be filler, and this repository's own guidance is that requiring prose on a routine action trains agents to produce it emptily. The name is accurate and matches the verdict token `_resolve_edge` returns (`dangling`), which is a better reason to keep it than mere convention.
  ONE SCOPE CORRECTION FROM E-01's REVISION: the flag must NOT cover the `ambiguous` verdict. That was not a question the item asked, because the item did not know the resolver returns three verdicts, but it is now part of this decision: an ambiguous edge cannot become valid by waiting, so admitting it under a forward-reference flag would be admitting an edge that can never resolve.

### OQ-02: When `remove` empties a statement, should it write `none` or `unresolved`?

- Blocking: no
- Status: resolved
- Owner: this plan's executor (E-03)
- Resolution or deferral rationale: RESOLVED FROM THE GRAMMAR, and confirmed at review rather than left for the executor to confirm. `none` is correct. The grammar admits both and they mean different things: `none` asserts there ARE no dependencies, `unresolved` asserts they have not been determined, and `parse_item_dependencies` treats `unresolved` as the NOT-READY sentinel (it returns `ready=False` for it, `ipd_schema.py:742-745`) while `none` returns `ready=True` (`:744-745`). So writing `unresolved` on removal would flip the plan into a not-ready state as a side effect of dropping one edge, which is a behavior change nobody asked for. Verified also that an EMPTY value is tolerated as an implicit `none` by the parser (`:739-741`) but is not the canonical rendering, which is why E-03 must write the literal `none` rather than a blank.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: for EACH of the three edge forms (`executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>`) paste the dangling-target invocation, its UNPIPED exit code, the refusal text, and proof nothing was written (the plan file's `Item-Dependencies` line unchanged; do NOT assert an empty `git diff`, since the setter also writes a history receipt on a successful path, F-13). Then paste a VALID target for one form succeeding. PASTE THE AMBIGUOUS CASE refusing too, seeded from a fixture with one id6 owned by two record types. PASTE THE CODE showing resolution goes through `check_engine._resolve_edge` and `build_dependency_index`, NOT through `match_selector`; a V-01 that shows a `match_selector`-based existence check FAILS, because that is the second authority E-05 forbids and it demonstrably diverges from `aw check` (F-11). Finally, paste `aw check`'s verdict on one dangling and one ambiguous edge beside the setter's refusal, showing the two surfaces name the SAME condition.
  - Observed evidence: All commands run against a FIXTURE repo (`/tmp/.../f6idxs-ev`, seeded by `.aw/tmp/f6idxs/mkfixture.sh`), never the live tree. Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`). The verb is invoked as `python3 -m agent_workflows ...` because the installed `aw` shim on this machine resolves to a DIFFERENT checkout; that was measured and is why every probe below is module-invoked.

    ALL THREE EDGE FORMS REFUSE PRE-WRITE, and the on-disk line is unchanged in each case (baseline `- Item-Dependencies: none`):

    ```text
    $ ipd dependencies set aaaaaa executed:zzzzzz --yes
    FAIL     aw ipd dependencies set: dangling Item-Dependencies target: executed:zzzzzz: no ipd artifact has id6 zzzzzz. Refusing before making changes.
    INFO     Pass --allow-dangling to record a deliberate forward reference to a target that does not exist yet.
    exit=2  (UNPIPED)
    - Item-Dependencies: none

    $ ipd dependencies set aaaaaa exists:backlog:zzzzzz --yes
    FAIL     aw ipd dependencies set: dangling Item-Dependencies target: exists:backlog:zzzzzz: no backlog artifact has id6 zzzzzz. Refusing before making changes.
    exit=2  (UNPIPED)
    - Item-Dependencies: none

    $ ipd dependencies set aaaaaa state:spec:approved:zzzzzz --yes
    FAIL     aw ipd dependencies set: dangling Item-Dependencies target: state:spec:approved:zzzzzz: no spec artifact has id6 zzzzzz. Refusing before making changes.
    exit=2  (UNPIPED)
    - Item-Dependencies: none
    ```

    A VALID TARGET STILL SUCCEEDS, so the gate is not a blanket refusal:

    ```text
    $ ipd dependencies set aaaaaa executed:bbbbbb --yes
    -    plan        20260908-fix-01-aaaaaa  unchanged
    exit=0
    - Item-Dependencies: executed:bbbbbb
    ```

    THE AMBIGUOUS CASE REFUSES, seeded from a fixture where ONE id6 (`dupdup`) is owned by TWO plans records (the same shape as the live multi-owner `uyeko5`):

    ```text
    $ ipd dependencies set aaaaaa executed:dupdup --yes
    FAIL     aw ipd dependencies set: ambiguous Item-Dependencies target: executed:dupdup: id6 dupdup matches multiple ipd artifacts (.../20260908-fix-04-dupdup-p.ipd.md, .../20260908-fix-05-dupdup-p.ipd.md). Refusing before making changes.
    INFO     An ambiguous target cannot be admitted with --allow-dangling; repair the duplicate stable identity instead.
    exit=2
    - Item-Dependencies: executed:bbbbbb   (unchanged)
    ```

    RESOLUTION GOES THROUGH THE CHECKER'S RESOLVER, NOT `match_selector` (F-11). The new `status_set.resolve_dependency_edge_targets` body is exactly:

    ```python
    from agent_workflows import check_engine as _ce
    index = _ce.build_dependency_index(Path(repo_root))
    for edge in edges:
        verdict, detail = _ce._resolve_edge(edge, index)
    ```

    and `grep -n "def _resolve_edge\|def build_dependency_index" agent_workflows/status_set.py agent_workflows/cli.py` returns NOTHING, so neither module defines its own. Two tests assert this by BEHAVIOR rather than by reading the source, which is the stronger form: `test_the_setter_resolves_through_the_checkers_resolver_not_the_selector` patches `check_engine._resolve_edge` with a spy and asserts the spy RECORDED `executed:zzzzzz=dangling`, so a `match_selector`-based check would leave the spy uncalled and fail; and `test_the_typed_resolution_the_selector_could_not_do` proves the TYPE is enforced (a `plans`-owned id6 does not satisfy `exists:spec:`), which is precisely the enforcement `match_selector` lacks.

    THE TWO SURFACES NAME THE SAME CONDITION, asserted by calling the shared evaluator on the same edges:

    ```text
    aw check on 'executed:zzzzzz' -> ['check.ipd-dependency-dangling']    setter said: "dangling"
    aw check on 'executed:dupdup' -> ['check.ipd-dependency-ambiguous']   setter said: "ambiguous"
    ```

    `tests/test_dependency_verb.py::SetterAgreesWithCheckerTests` pins all four of these agreements.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the same dangling invocation WITH `--allow-dangling` showing it proceeds, showing the output NAMES the dangling target, and showing the resulting `Item-Dependencies` line. Paste the AMBIGUOUS case WITH `--allow-dangling` still REFUSING, proving the hatch is scoped to the `dangling` verdict only. Paste the flag's help text showing it states that boundary. Then paste `aw check` on the artifact afterwards, proving the dangling edge is still reported as an error at the repository gate.
  - Observed evidence: THE HATCH PROCEEDS AND NAMES THE TARGET (fixture repo `f6idxs-ev2`):

    ```text
    $ ipd dependencies set aaaaaa executed:zzzzzz --yes --allow-dangling
    WARN     aw ipd dependencies set: accepting DANGLING target executed:zzzzzz (--allow-dangling): executed:zzzzzz: no ipd artifact has id6 zzzzzz
    INFO     `aw check` still reports a dangling edge as an error (check.ipd-dependency-dangling); resolve it before the plan advances.
    -    plan        20260908-fix-01-aaaaaa  unchanged
    exit=0
    - Item-Dependencies: executed:zzzzzz
    ```

    The target is NAMED (`executed:zzzzzz` appears in the WARN line), so the deferral is visible in the transcript rather than silent, and the output itself states that the repository gate still reports it.

    `aw check` AFTERWARDS STILL ERRORS, so the edge remains fail-closed at the portable authority:

    ```text
    $ check plans --dir <fixture>
      Issue: executed:zzzzzz: no ipd artifact has id6 zzzzzz
      - .aw/records/plans/pending
    ```

    THE AMBIGUOUS CASE STILL REFUSES WITH THE FLAG, which is the boundary that makes the hatch honest:

    ```text
    $ ipd dependencies set aaaaaa executed:dupdup --yes --allow-dangling
    FAIL     aw ipd dependencies set: ambiguous Item-Dependencies target: executed:dupdup: id6 dupdup matches multiple ipd artifacts (...fix-04-dupdup..., ...fix-05-dupdup...). Refusing before making changes.
    INFO     An ambiguous target cannot be admitted with --allow-dangling; repair the duplicate stable identity instead.
    exit=2
    ```

    THE HELP TEXT STATES THE BOUNDARY, so an operator reading only `--help` learns it rather than discovering it:

    ```text
    $ ipd dependencies set --help
      --allow-dangling      Accept an edge whose target does not exist YET (a
                            deliberate forward reference, e.g. authoring a Set
                            parent-first). Each accepted target is named in the
                            output, and 'aw check' still reports it as an error.
                            This does NOT accept an AMBIGUOUS target (one id6
                            owned by several artifacts), which is refused even
                            with this flag because it can never become valid by
                            waiting.
    ```

    `tests/test_dependency_verb.py::AllowDanglingTests` pins all five properties, including a subTest asserting the ambiguous refusal both WITHOUT and WITH the flag, and a guard that neither help text contains an em or en dash.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a plan with three edges, the `remove` invocation dropping one, and the resulting line showing the other two BYTE-IDENTICAL. Then paste removing the last edge and the resulting `- Item-Dependencies: none`. PASTE THE CANONICAL-MATCHING CASE: remove an edge spelled non-canonically (for example `state:ipd:executed:<id6>` for a canonical `executed:<id6>`) and show it is matched rather than reported absent. PASTE THE DANGLING-REMOVAL CASE: an edge whose target does not exist is still removable, proving E-01's validation did not leak into `remove` (F-14). State the multi-match semantics you chose and paste a two-plan selector exercising it. Paste a grep or trace proving the write went through the existing no-op transition path rather than a new writer.
  - Observed evidence: THE VERB NOW EXISTS. At pristine HEAD `3c9663d5` the same invocation was `error: argument ipd_dependencies_command: invalid choice: 'remove' (choose from 'set')`, exit 2 (pasted under V-06). `ipd dependencies --help` now shows `{set,remove}`.

    REMOVING ONE OF THREE LEAVES THE OTHERS BYTE-IDENTICAL:

    ```text
    seeded:   - Item-Dependencies: executed:bbbbbb, exists:spec:ssssss, state:backlog:open:bbbklg
    $ ipd dependencies remove aaaaaa exists:spec:ssssss --yes
    -    plan        20260908-fix-01-aaaaaa  unchanged
    exit=0
    result:   - Item-Dependencies: executed:bbbbbb, state:backlog:open:bbbklg
    ```

    REMOVING THE LAST EDGE YIELDS THE EXPLICIT `none`, not a blank and not `unresolved` (OQ-02):

    ```text
    $ ipd dependencies remove aaaaaa executed:bbbbbb --yes
    exit=0
    - Item-Dependencies: none
    ```

    A DANGLING EDGE IS STILL REMOVABLE, proving E-01's validation did NOT leak into `remove` (F-14):

    ```text
    - Item-Dependencies: executed:zzzzzz        (admitted earlier via --allow-dangling)
    $ ipd dependencies remove aaaaaa executed:zzzzzz --yes
    exit=0
    - Item-Dependencies: none
    ```

    A NON-CANONICAL SPELLING IS STILL MATCHED (ordering reversed plus stray whitespace, which the grammar treats as identical; a raw-string compare would have called this ABSENT and refused it):

    ```text
    - Item-Dependencies: executed:bbbbbb, exists:spec:ssssss
    $ ipd dependencies remove aaaaaa " exists:spec:ssssss , executed:bbbbbb " --yes
    exit=0
    - Item-Dependencies: none
    ```

    ONE PLAN CORRECTION, MEASURED. The plan's F-14 and E-03 both said the parser "redirects `state:ipd:executed:` to canonical `executed:`", and cited that as the canonical-matching case to test. IT DOES NOT REDIRECT; IT REFUSES. `ipd_schema._parse_item_dependency_edge` returns the error "state:ipd:executed:<id6> is illegal; use the canonical 'executed:<id6>' edge", so `canonical_item_dependencies("state:ipd:executed:bbbbbb")` is `(None, <that error>)`. Both verbs therefore refuse that token identically, since both go through the one grammar authority:

    ```text
    $ ipd dependencies remove aaaaaa state:ipd:executed:bbbbbb --yes
    FAIL     aw ipd dependencies remove: invalid Item-Dependencies value: state:ipd:executed:<id6> is illegal; use the canonical 'executed:<id6>' edge in 'state:ipd:executed:bbbbbb'. Refusing before making changes.
    exit=2
    - Item-Dependencies: executed:bbbbbb   (unchanged)
    ```

    That is CORRECT behavior and is now pinned by `test_state_ipd_executed_is_a_grammar_error_in_both_verbs`, so a future reader does not re-derive the plan's wrong premise. The canonical-matching requirement is satisfied by the ordering/whitespace case above, which is the class of spelling difference the grammar genuinely accepts.

    MULTI-MATCH SEMANTICS, CHOSEN AND STATED: the loop ACCUMULATES a non-zero exit rather than aborting, mirroring `set`. For a REPAIR verb that is right, because aborting on the first plan would make a partially-broken fleet unfixable in one call, while the non-zero exit still reports that something did not apply. A two-plus-plan setid selector exercising it:

    ```text
    (aaaaaa and bbbbbb declare the edge; cccccc + the two dupdup plans do not)
    $ ipd dependencies remove fix exists:spec:ssssss --yes
    -    plan        20260908-fix-01-aaaaaa  unchanged
    -    plan        20260908-fix-02-bbbbbb  unchanged
    FAIL     20260908-fix-03-cccccc-p.ipd.md: Item-Dependencies does not declare exists:spec:ssssss; nothing removed. Pass --if-present to treat an absent edge as a no-op.
    FAIL     20260908-fix-04-dupdup-p.ipd.md: ... (same)
    FAIL     20260908-fix-05-dupdup-p.ipd.md: ... (same)
    exit=2   (accumulated, not aborted)
    aaaaaa: - Item-Dependencies: none      <- still repaired
    bbbbbb: - Item-Dependencies: none      <- still repaired
    ```

    THE WRITE GOES THROUGH THE EXISTING NO-OP TRANSITION PATH, NOT A NEW WRITER. `set` and `remove` both call the single hoisted `_write_item_dependencies`, which builds the same `Namespace(item_dependencies=..., args=[current, path])` and calls `run_set_command` at the plan's CURRENT status, so persistence-on-a-no-op is inherited exactly as `aw ipd set --from-backlog` inherits it. Proven by CALL rather than by grep: `test_removal_goes_through_the_one_shared_writer` patches `status_set._write_item_dependencies` with a spy and asserts the spy was called with the value `none`; a copied second writer would leave `calls == []` and fail.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste removing an ABSENT edge showing a nonzero UNPIPED exit code and the message naming that edge; then the same with `--if-present` showing exit 0, a notice, and an unchanged file; then a second `--if-present` removal of the same absent edge showing identical output (idempotency).
  - Observed evidence: Fixture `f6idxs-ev3`, plan holding `- Item-Dependencies: executed:bbbbbb`.

    ABSENT EDGE IS AN ERROR BY DEFAULT AND NAMES THE EDGE:

    ```text
    $ ipd dependencies remove aaaaaa exists:spec:ssssss --yes
    FAIL     20260908-fix-01-aaaaaa-p.ipd.md: Item-Dependencies does not declare exists:spec:ssssss; nothing removed. Pass --if-present to treat an absent edge as a no-op.
    exit=2   (UNPIPED)
    - Item-Dependencies: executed:bbbbbb   (unchanged)
    ```

    `--if-present` DOWNGRADES IT TO A NOTICE AND A CLEAN NO-OP, AND A REPEAT IS IDENTICAL:

    ```text
    $ ipd dependencies remove aaaaaa exists:spec:ssssss --yes --if-present
    INFO     20260908-fix-01-aaaaaa-p.ipd.md: edge(s) not present, nothing to remove (--if-present): exists:spec:ssssss
    $ ipd dependencies remove aaaaaa exists:spec:ssssss --yes --if-present
    INFO     20260908-fix-01-aaaaaa-p.ipd.md: edge(s) not present, nothing to remove (--if-present): exists:spec:ssssss
    exit=0   (UNPIPED)
    - Item-Dependencies: executed:bbbbbb   (unchanged after both)
    ```

    The two notices are BYTE-IDENTICAL, which is what idempotency means here, and the file is untouched, so it is a clean no-op rather than a partial write. `test_repeated_if_present_removal_is_idempotent` asserts the equality of the two captured outputs, not merely the two exit codes.

    THE FLAG SUPPRESSES ONE CONDITION, NOT ALL ERRORS, which is what its help text promises: `test_if_present_does_not_suppress_a_malformed_edge` shows `remove aaaaaa not-an-edge --if-present` still exits non-zero with "Refusing before making changes." and writes nothing. `test_a_present_and_an_absent_edge_together_under_if_present` covers the mixed request: the present edge is removed, the absent one is noted, exit 0.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a grep showing no new `re.compile` mentioning a dependency field name and no second edge resolver in either touched module; paste the four existing consumer call sites unchanged; paste the `tests/test_runner_item_dependencies.py` result. THEN state which coverage route you took for the guard and prove it: if you extended `_DRIVER_SOURCES`, paste the extended tuple showing `status_set.py` and `cli.py` in it plus the `--scope-reason` you will carry at finalize; if you wrote an equivalent guard in `tests/test_dependency_verb.py`, paste it. A V-05 that cites the existing guard WITHOUT one of those two is incomplete, because that guard scans only the two driver files and cannot see this plan's code (F-12).
  - Observed evidence: NO NEW DEPENDENCY REGEX AND NO SECOND EDGE RESOLVER in either touched module:

    ```text
    $ grep -nE "re\.compile\([^\n]*(Item-Dependencies|Dependencies|Depends-on)" agent_workflows/status_set.py agent_workflows/cli.py
      (none)
    $ grep -n "def _resolve_edge\|def build_dependency_index" agent_workflows/status_set.py agent_workflows/cli.py
      (none)
    ```

    THE EXISTING CONSUMER CALL SITES ARE UNCHANGED (`git diff` touches none of these lines):

    ```text
    agent_workflows/check_engine.py:2638:    return evaluate_ipd_dependencies(
    agent_workflows/ipd_lint.py:1147:                for d in _ce.evaluate_ipd_dependencies(
    agent_workflows/oc_runipd.py:2562:    drift = _ce.evaluate_ipd_dependencies(
    agent_workflows/engine.py:4899:  (staged-overlay hook, delegating to the shared evaluator)
    ```

    `python3 -m pytest tests/test_runner_item_dependencies.py` result, together with the other dependency surfaces:

    ```text
    $ python3 -m pytest tests/test_dependency_verb.py tests/test_runner_item_dependencies.py tests/test_ipd_dependency_check.py tests/test_ipd_item_dependencies.py tests/test_ipd_dependency_statement_gate.py
    197 passed in 20.44s
    ```

    THE GUARD ROUTE TAKEN, AND WHY. I wrote an EQUIVALENT guard in the in-fence `tests/test_dependency_verb.py::AntiDivergenceGuardTests` rather than extending `_DRIVER_SOURCES`, and the choice is on MEASUREMENT, not on the scope fence. I applied each of the existing class's four guard bodies to the two touched files before deciding, and three of them are DRIVER-SPECIFIC assertions rather than general ones: `test_no_driver_defines_the_deleted_private_parser` pins the removal of `_DEPS_RE`/`_read_deps`, symbols that only ever existed in the two runners; `test_no_driver_exposes_the_deleted_names` introspects the two driver MODULES by attribute; and `test_drivers_reference_the_shared_dependency_api` requires `META_ITEM_DEPENDENCIES` to appear in the source, which measured TRUE for `status_set.py` but FALSE for `cli.py`, whose dependency role is argument registration and dispatch and which correctly names no schema constant:

    ```text
    --- status_set.py   guard4 parse_item_dependencies=True  META_ITEM_DEPENDENCIES=True
    --- cli.py          guard4 parse_item_dependencies=False META_ITEM_DEPENDENCIES=False
    ```

    So adding these two files to that tuple would have forced either a FALSE assertion about `cli.py` or a per-file exemption, and every failure message in that class says "driver", which these files are not. The equivalent guard asserts what is actually true of these modules, stays inside `Scope-Paths`, and needs NO `--scope-reason`. It carries seven tests: no dependency regex (same `re.compile` hint pattern, same newline bound and the same comments-stripped-but-strings-kept reasoning, so it cannot go vacuous); no locally defined `_resolve_edge`/`build_dependency_index`; the setter module DOES consume all three shared authorities; the resolver function does not name `match_selector` in CODE (tokenizer-stripped, because the docstring legitimately names it to warn against it); `check_engine` did not learn the verb names, pinning the dependency DIRECTION; both subcommands are declared parser leaves; and the two verbs share one declared contract.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste all TWELVE cases with commands, UNPIPED exit codes and outcomes, including the three preservation cases (the setid grammar refusal with its exact message, the existing clear path, and the dangling edge remaining removable) and the ambiguous and canonical-matching cases. Paste the E-01 case FAILING against pre-change code, and assert it against the real WRITE rather than a dry run: at HEAD the invocation exits 0 AND the dangling value lands in `- Item-Dependencies:`. Paste the fixture setup proving the tests do not mutate the live tree, and show the assertions are scoped to the dependency line rather than whole-file equality (F-13).
  - Observed evidence: THE E-01 CASE FAILING AGAINST PRE-CHANGE CODE, ASSERTED AGAINST THE REAL WRITE. Pristine HEAD `3c9663d5` was exported with `git archive HEAD | tar -x -C .aw/tmp/f6idxs/prechange` (verified pristine: `grep -c run_dependencies_remove_command` returns 0 there) and run against the same fixture. All THREE forms exit 0 AND the dangling value LANDS on disk, which is the stronger reproduction the plan required:

    ```text
    ### PRE-CHANGE (pristine HEAD 3c9663d5)
    --- dangling form executed:zzzzzz            exit=0   - Item-Dependencies: executed:zzzzzz
    --- dangling form exists:backlog:zzzzzz      exit=0   - Item-Dependencies: exists:backlog:zzzzzz
    --- dangling form state:spec:approved:zzzzzz exit=0   - Item-Dependencies: state:spec:approved:zzzzzz
    --- ambiguous executed:dupdup               exit=0   - Item-Dependencies: executed:dupdup
    --- remove verb
    agent-workflows ipd dependencies: error: argument ipd_dependencies_command: invalid choice: 'remove' (choose from 'set')
    exit=2
    ```

    THE CASE MATRIX, every exit code measured UNPIPED. Each row's full transcript is pasted under the V-item it belongs to; this table is the index, not a substitute:

    | # | Case | Command | Exit | Outcome |
    |---|---|---|---|---|
    | a | dangling `executed:` | `set aaaaaa executed:zzzzzz` | 2 | refused pre-write, line unchanged (V-01) |
    | b | dangling `exists:` | `set aaaaaa exists:backlog:zzzzzz` | 2 | refused pre-write, line unchanged (V-01) |
    | c | dangling `state:` | `set aaaaaa state:spec:approved:zzzzzz` | 2 | refused pre-write, line unchanged (V-01) |
    | d | valid target | `set aaaaaa executed:bbbbbb` | 0 | written (V-01) |
    | e | hatch accepts + names | `set aaaaaa executed:zzzzzz --allow-dangling` | 0 | WARN names the target (V-02) |
    | f | remove one of three | `remove aaaaaa exists:spec:ssssss` | 0 | other two byte-identical (V-03) |
    | g | remove the last edge | `remove aaaaaa executed:bbbbbb` | 0 | `- Item-Dependencies: none` (V-03) |
    | h | remove an absent edge | `remove aaaaaa exists:spec:ssssss` | 2 | error NAMES the edge (V-04) |
    | i | `--if-present` downgrade | same `--if-present`, twice | 0 | identical notice, no change (V-04) |
    | j | ambiguous, with and without the hatch | `set aaaaaa executed:dupdup [--allow-dangling]` | 2 | refused BOTH ways (V-01/V-02) |
    | k | dangling edge still removable | `remove aaaaaa executed:zzzzzz` | 0 | `none`; validation did not leak (V-03) |
    | l | non-canonical spelling matched | `remove aaaaaa " exists:spec:ssssss , executed:bbbbbb "` | 0 | matched, not reported absent (V-03) |

    THE THREE PRESERVATION CASES, all still behaving exactly as before this change:

    ```text
    (m) setid-shaped target, GRAMMAR refusal with its exact established message:
    $ ipd dependencies set aaaaaa exists:backlog:worksequence --yes
    FAIL     aw ipd dependencies set: invalid Item-Dependencies value: exists target 'worksequence' is not a 6-char base36 id6. Refusing before making changes.
    exit=2
    (this fails on the GRAMMAR, not on the new existence check, proving the new check sits ALONGSIDE it)

    (n) the existing clear path:
    $ ipd dependencies set aaaaaa none   ->  - Item-Dependencies: none
    $ ipd dependencies set aaaaaa -      ->  - Item-Dependencies: none
    (neither reaches the existence check; `unresolved` also still writes, pinned separately)

    (k, restated as preservation) a dangling edge REMAINS REMOVABLE: pasted under V-03, exit 0.
    ```

    FIXTURE SETUP, PROVING THE TESTS DO NOT MUTATE THE LIVE TREE. `_FixtureRepo` builds each repo under `tempfile.TemporaryDirectory()` and registers `addCleanup(self.fx.cleanup)`, seeding its own `plans/pending`, `specs`, and `backlog/open` records plus the duplicate-id6 pair. Every CLI call passes `--dir str(self.fx.root)`. No test in the module reads or writes `.aw/records/` in this checkout; the only live-tree reads are the anti-divergence guard's `REPO_ROOT / "agent_workflows" / *.py` source reads, which are read-only by construction.

    ASSERTIONS ARE SCOPED TO THE DEPENDENCY LINE, NOT WHOLE-FILE EQUALITY (F-13). The helper is:

    ```python
    _DEP_LINE_RE = re.compile(r"(?m)^- Item-Dependencies:[^\n]*$")
    def dep_line(self, path=None) -> str:
        m = _DEP_LINE_RE.search((path or self.plan).read_text(encoding="utf-8"))
        return m.group(0) if m else ""
    ```

    Every "nothing was written" assertion compares `before == self.fx.dep_line()`, so the setter's shared history receipt and its `- Approval:` rewrite (out of scope, `apply_status_change`'s behavior for EVERY setter) cannot produce a false failure. The confirming detail is that these fixture plans are `approved`, so that rewrite genuinely happens on the success path and a whole-file assertion WOULD have failed.

    FULL MODULE RESULT: `40 passed in 3.24s` (`python3 -m pytest tests/test_dependency_verb.py`), which is 12 matrix cases plus 3 preservation cases plus the agreement, guard, multi-match, and idempotency cases.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan graduates TWO of the item's five gaps, with the other three deferred for stated reasons (F-4, F-5, F-15 and Deferred): GAP 1 is now unblocked but too large to ride along, GAP 3 is an undecided design question whose prerequisite is actively being designed by the four-plan `setidhard` Set, and GAP 5 is a policy decision about surface consistency.

ONE REVIEW FINDING CHANGES WHAT MUST BE BUILT, not merely how it is described, and it should be read before starting. F-11: E-01's authored instruction to resolve targets "through the shared selector resolver" would have created the very second authority E-05 forbids, because `aw check` resolves edges through `check_engine.build_dependency_index` + `_resolve_edge`, not through `match_selector`, and the two demonstrably diverge on a real id6 in this repository (`uyeko5`, owned by one `plans` and two `research` records). The corrected instruction also gains behavior the plan never had: `_resolve_edge` returns a THIRD verdict, `ambiguous`, which must refuse and must NOT be covered by `--allow-dangling`. Secondarily, F-12: the anti-divergence guard E-05 cites scans only the two runner files, so it cannot see `status_set.py` or `cli.py` and must be extended or duplicated deliberately.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. If E-05 extends `AntiDivergenceGuardTests`, that is an out-of-fence edit to `tests/test_runner_item_dependencies.py`: MAKE IT and carry a `--scope-reason` at finalize rather than working around it. Run the bare suite (`python3 -m pytest`, no added flags) and paste the ACTUAL summary lines before and after; expect the environmental `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` failure in both, and do NOT touch the untracked `opencode-recovery/*.md` files that cause it, which belong to another party in this shared checkout. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE these are MUTATING verbs that write plan front matter, so test against a fixture repository and never against the live tree. RE-LOCATE BY SYMBOL, since several of this plan's original citations had drifted: find `run_dependencies_set_command`, `match_selector`, `inventory_all_artifacts`, `check_engine.evaluate_ipd_dependencies`, `build_dependency_index`, `_resolve_edge`, `ipd_schema.parse_item_dependencies`, `canonical_item_dependencies`, `ITEM_DEP_TYPE_TO_RECORD_TYPE`, and `AntiDivergenceGuardTests._DRIVER_SOURCES` by name. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
