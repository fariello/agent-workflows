# IPD: Cache an orchestrator probe verdict against a content digest that ignores execution state

- Date: 2026-09-07
- Kind: child
- Concern: Child 03 asks a model whether an orchestrator carries work no child covers. That answer costs tokens and time, and re-asking it about an UNMODIFIED orchestrator buys nothing. So the verdict needs a cache keyed on content. The naive key is a whole-file hash, and this repository has already MEASURED that as a dead end: `ipd_lifecycle.plan_content_digest` (`:457`) hashes exact bytes, and `frozen_region_digest` (`:462`) exists precisely because that made a begin receipt "go stale on every CORRECT execution" (backlog `xmqv5l`) - a conforming executor MUST tick checkboxes, fill `Observed evidence`, and append `## Workflow history`, so the byte digest changed while the reviewed contract had not. A byte-keyed probe cache would repeat that error and re-spend on every tick.
  THE EXISTING DIGEST ALREADY PASSES FOUR OF THE FIVE TESTS THIS CHILD PROPOSES, AND FAILS THE FIFTH. Measured at review by calling `frozen_region_digest` on a real orchestrator (`cczotj` at round 1, re-measured on `yeh7gc` at round 2): ticking a checkbox, filling an `Observed evidence`, appending a history line, and editing a prose section ALL leave the digest unchanged, and editing an E-item's action text DOES change it. So E-02's `xmqv5l` proof is, for those five cases, a proof about code that already exists. The ONE case where it differs is the one this child actually needs: editing the `## Child IPDs` table does NOT change `frozen_region_digest`, because `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item text. That single gap is the whole justification for a new digest, and the plan never said so. See F-4.
  AND THE CHILD-TABLE INPUT MUST BE THE ROW TEXT, NOT THE PARSED ORDER GRAPH, or the sole justification above collapses. Measured at round 2: `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}` and NOTHING else, so on `yeh7gc` a child Id swap (`8tgg6g` -> `qqqqqq`) and a full rewrite of a child's description BOTH leave `rows` byte-identical (`{'1': (), '2': (), '3': ()}` before and after). A digest keyed on that return value would therefore be blind to exactly the edits a coverage question turns on, while ADDING a row does move it, so OQ-01's fixture would pass and the general property would still be false. Worse, child 03 E-03 sends the child TABLE as the probe payload and requires the payload and the key be the same two things: if the probe reads row text the key does not cover, editing a row serves a STALE VERDICT, which child 03 names as "the one way this cache can be actively wrong rather than merely useless". Key on the row CELL TEXT. See F-10.
- Scope: The verdict store and its key. IN: a digest over ONLY what the probe's answer depends on (the orchestrator's E-item action text plus its child table), excluding execution state, checkbox marks, workflow history, and prose sections; a per-repo verdict store recording digest, verdict, timestamp, and the model that answered; read/write helpers with a fail-closed miss; a child-table extraction, since no existing parser exposes it in a form this digest can consume. OUT: the probe itself and its prompt (child 03), the refusal surfacing (child 01), and any change to `plan_content_digest` or `frozen_region_digest`, which other gates depend on.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_probe_cache.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: orchprobe
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8tgg6g
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-14 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): E-01..E-07 PERFORMED and V-01..V-07 verified with pasted evidence, in lane worktree `8tgg6g` from start HEAD `fea2c9f8`. Code commit `b816200c`, touching only the two declared `Scope-Paths` (`agent_workflows/runner_shared.py`, `tests/test_orchestrator_probe_cache.py`); `engine.py` was NOT touched, as the fence requires.
  E-04's PREREQUISITE HAD ALREADY LANDED, which is why this child could execute in full rather than stopping at E-03. OQ-03 assigned the installer `state/` ignore fix to `yvvf98`; measured at execution, commit `ee38864c` (2026-09-12, backlog `2812t3`) added anchored `/state/` to BOTH `_AW_GITIGNORE_TEMPLATE` and the `_ensure_aw_gitignore` back-fill list, i.e. exactly the two edits F-11 measured as required, plus `MachineLocalStateGitignoreTests`. Verified independently here in throwaway repos carrying only installer output, on BOTH the fresh-install and the already-installed back-fill paths (`git check-ignore` rc=0, attributed to `.aw/.gitignore`). ONE RESIDUE RAISED, NOT CLOSED: that commit records no `kw5y2s` spec amendment, which is owed by that work rather than by this child (whose fence excludes both `engine.py` and the spec). Recorded as DECISION 05-8tgg6g-D2.
  TWO ROUND-2 CORRECTIONS WERE RE-MEASURED AT EXECUTION, not taken on trust. F-4 holds: `frozen_region_digest` still ignores all four executor mutations and still moves on an E-item edit, and it does NOT move on any of the three child-table edits, so child-table sensitivity remains the SOLE justification for a new digest. F-10 holds: `parse_child_table(...).rows` is byte-identical for an Id swap and a description rewrite (`{'1': (), '2': (), '3': ()}` both sides) and moves only for a row ADD. Both are pinned as CONTRAST tests, so if either function ever gains the sensitivity this child relies on it lacking, the suite fails and tells the reader to re-derive the design.
  ONE ADDITION BEYOND THE LETTER OF THE PLAN, in the direction the review asked for: OQ-01's addendum notes its fixture adds a row, the one child-table edit a broken order-graph key would ALSO catch. A third case was added covering the ROW-ONLY remedy (a child added while the parent's item stays as sequencing prose), which is the case only row-cell sensitivity catches and the dangerous direction, since a genuinely fixed orchestrator would otherwise keep being served its old FAIL.
  THE PLAN'S `47` WAS ALREADY STALE and asserting it would have been a false baseline: the oc-to-agy import count measures 48 in this worktree BEFORE this child. V-07 therefore asserts the RULE (did not increase, before/after from `git show HEAD:`), which held at 48 -> 48 with no new symbol imported from `oc_runipd`.
  VALIDATION: `python3 -m pytest` bare gives `18 failed, 6867 passed, 3 skipped, 2 xfailed`; the worktree's own pre-change baseline was `18 failed, 6811 passed, 3 skipped, 2 xfailed` and the failing NODE IDS are BYTE-IDENTICAL (new failures NONE, fixed NONE), compared as node ids and never as totals. The new module is `56 passed`. Both mutation checks V-05 requires were run and reverted byte-for-byte: a miss returning `pass` failed 5 tests, and a digest ignoring the child-table rows failed 6. `aw sanitize --agent` reports `clean`, 0 findings.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its blocking OQ-03 was answered on 2026-09-08 and the finding it escalated (PR-009) is now closed in review round 3. Performed at HEAD `84111de2` at the maintainer's explicit instruction of 2026-09-10, who was shown that 10 of 15 `no-go` plans were held by stale bookkeeping and chose to have them hand-fixed with evidence recorded rather than re-reviewed. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2: REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-009..PR-015, six FIXED and one OPEN (PR-009), plus round 1's PR-001 now dispositioned FIXED by the maintainer's OQ-02 ruling. THE BLOCKER IS THAT THE DIGEST'S SOLE JUSTIFICATION WOULD NOT HAVE HELD AS ROUND 1 SPECIFIED IT (PR-010, new F-10). Round 1 concluded this child survives only on child-table sensitivity and told E-01/E-02 to key on `ipd_set_plan.parse_child_table`; measured, that returns the ORDER GRAPH (`{order: (dep_orders,)}`), so on `yeh7gc` a child Id swap and a full description rewrite BOTH leave `rows` byte-identical while only a row ADD moves it. The key would have been sensitive to row COUNT and blind to row CONTENT. That is the actively-wrong case, not the useless one: child 03 E-03 sends the child table AS the probe payload and requires payload and key be identical inputs, so a row edit the key ignores serves a STALE VERDICT. It would not have been caught either, because OQ-01's maintainer-specified fixture ADDS a row (the one edit both keys detect) and its mutation step would still have shown a failure, making the broken key look proven. Fixed by keying on row CELL TEXT, with E-03 requiring the Id-swap and description cases and V-03 requiring `parse_child_table(...).rows` pasted byte-identical for them. SECOND, ROUND 1 SENT THE EXECUTOR TO THE WRONG MODULE (PR-011): `runner_shared` ALREADY owns a child-table row scanner (`parse_declared_child_orders:2398`) that finds the section by schema heading, matches rows, skips the alignment row, then discards every cell but the first; importing `ipd_set_plan` would fork the definition of a child row in a Set whose own E-07 exists to stop symbol forking. Also measured: that scanner's naive `.split('|')` diverges from the backtick-aware `_split_table_row` on THREE live orchestrators (`94dhrt`, `mvz3d2`, `rreixg`; one splits 12 cells instead of 4), harmless for cell 0 and not for an all-cells digest. THIRD, THE MAINTAINER'S OQ-02 RULING RESTS PARTLY ON A FALSE FACT (PR-012, F-11): it cited that `_ensure_aw_gitignore` already back-fills missing rules so a template edit reaches existing adopters. It does not; the back-fill is a hand-maintained list of per-pattern literal checks, reproduced by appending `state/` to the template in a scratch repo and re-running it (existing file unchanged). Three other plans (`4r0qp1`, `yvvf98`, `rh5tt6`) each recorded this same two-edits rule. The DECISION stands (`install_wizard.py:288-294` does forbid a tracked `state_runtime`, re-verified); the COST does not, and E-04 depended on the cheaper version. OPEN: OQ-03 (`Blocking: yes`, PR-009) asks which plan owns the installer `state/` fix, since no pending plan or backlog item does and this child's fence excludes `engine.py`; recommendation (b), fold into `yvvf98`, which already opens both sites. ALSO FIXED: E-06's staleness rule keyed on `model`, which `runner_profiles.resolve` returns as None whenever nothing supplies one (`:975-991`, printed `model=(host default)`), so it would compare None to None and accept any age (PR-013); a gate paragraph asserting a block on OQ-02 that no code enforced, since OQ-02 has carried `Blocking: no` and `Status: resolved` since the ruling and `has_unresolved_blocking_question` returns False (PR-014, the same defect fixed on sibling `yeh7gc`); and a baseline that drifted `5632 passed` to `5648 passed` in one day with an IDENTICAL failing node id (PR-015). Item count UNCHANGED at seven: every round-2 finding corrected an existing item's content rather than adding a deliverable. Worth noting beyond this cache: in the adopter-shaped repo the SHIPPED begin receipts, finalize lock and finalize journals are ALL trackable, so the missing `state/` rule is a live framework defect wider than this child.
- 2026-09-08 to-review (aw set): status set to to-review
- 2026-09-07 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-008, seven FIXED and one OPEN. THE BLOCKER IS A PORTABILITY DEFECT IN THE STORE'S SITING, AND THE FINDING THAT AUTHORIZED IT CITED THE WRONG FILE. F-3 said `.aw/.gitignore` already ignores the runtime tree, so the store needs no new rule. Measured: `.aw/.gitignore` says NOTHING about `state/` (its only `state` string is a comment about `records/runs/`); the rule that ignores it HERE is the ROOT `.gitignore:60`, which the installer explicitly never writes ("it is NOT the user's root `.gitignore` (that is never touched here)", `engine.py:4308-4313`), and `_AW_GITIGNORE_TEMPLATE` contains ZERO occurrences of `state/`. Reproduced in a throwaway repo with that exact template installed: `git check-ignore .aw/state/runtime/probe-verdicts.json` exits 1, NOT ignored. So the store is gitignored in THIS repo by an accident of local history and committable in every adopter, which for a file recording LLM verdicts against machine paths is a leak-sanitizer concern, not just untidiness. V-03's `git check-ignore` would have PASSED here and proven nothing about an adopter. SECOND, THE DIGEST'S JUSTIFICATION WAS ALMOST ENTIRELY REDUNDANT AND ITS ONE REAL GAP WENT UNSTATED: measured, `frozen_region_digest` already ignores all four mutations E-02 tests and already changes on an E-item edit, so the ONLY behavior this child adds is child-table sensitivity, which it does not change. THIRD, E-01's stated reuse cannot deliver: `ipd_lint.parse` exposes no child table at all (its `ParsedDoc` has no such field), so the extraction must come from `ipd_set_plan.parse_child_table` or be written, and E-01 claimed the reuse without checking. OPEN: OQ-02 (`Blocking: yes`, PR-001) asks where the store may live given the adopter gap. ALSO FIXED: a lazy-import requirement the plan omitted (`runner_shared` imports no first-party module but `render_stream`, and `ipd_lifecycle` imports `ipd_lint` lazily at all seven of its sites), the "~46" count (measured 47), a `frozen_region_digest` line citation off by one, and an OQ-01 that asked the executor to confirm self-invalidation without naming the property that makes it true.

- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the probe cheap to keep on: an orchestrator whose meaningful content has not changed is never re-probed, while any change to what the probe reasons about does re-probe. A cache MISS must never be mistaken for a pass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a key that ignores what does not matter

- [x] E-01 Extract the child table's ROW CELL TEXT in `runner_shared`, extending the row scanner that module ALREADY owns (`parse_declared_child_orders`, `:2398`) rather than importing another module's parser.
  WHY THE ROW TEXT AND NOT THE PARSED GRAPH, which is the correction that keeps this child justified at all. `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}` and nothing else. Measured at round 2 on `yeh7gc`: swapping a child Id and rewriting a child's description BOTH leave `rows` byte-identical, so a digest keyed on it is blind to the edits a coverage question depends on. Key on the CELLS of each row (header row included), in document order, so any change to what the table SAYS moves the key.
  WHY THE PARSER IS ALREADY HERE, so no cross-module reach is needed. `runner_shared.parse_declared_child_orders` (`:2398`) already locates the section by `ipd_schema.H_CHILD_IPDS`, matches rows with `_TABLE_ROW_RE` (`:2227`), and skips the alignment row via `_TABLE_SEPARATOR_CELL_RE` (`:2230`); it then discards every cell but the first. Factor the row-walk into a shared helper returning the full cell tuples and have BOTH call it, so the cache and the retirement gate cannot disagree about what a row is.
  ONE MEASURED DEFECT NOT TO INHERIT: that scanner splits cells with a naive `.split("|")` (`:2442`), which `ipd_set_plan._split_table_row` (`:206`) exists to avoid because a backticked pipe shifts every later column. Measured, THREE live orchestrators (`94dhrt`, `mvz3d2`, `rreixg`) contain such a row, one splitting 12 cells instead of 4. For an ORDER token read from cell 0 that is harmless, which is why it shipped; for a digest over ALL cells it is not, since a plan filename in backticks would fragment. Use the backtick-aware split for the digest, and state whether `parse_declared_child_orders` was left alone (acceptable: cell 0 is unaffected) or fixed too.
  WHY ANY CROSS-MODULE IMPORT MUST BE LAZY, if E-02's E-item extraction needs one. `runner_shared` has exactly ONE module-level first-party import (`render_stream`, `:136`) and reaches `ipd_lint`, `ipd_schema` and `ipd_lifecycle` through function-local imports (`:2338`, `:2425`, `:2958`); `ipd_lifecycle` does the same at all seven of its `ipd_lint` sites. A module-level import here would change the graph for both host drivers.
  - Depends on: none
  - Expected outcome: one shared row-walk in `runner_shared` returning full cell tuples, consumed by both the digest and `parse_declared_child_orders`, using the backtick-aware split for the digest; no second table parser written; no new module-level first-party import in `runner_shared`.
  - Execution state: performed

- [x] E-02 Build the cache key: a stable digest over the orchestrator's E-item ACTION TEXT and its child-table row cells, and nothing else. Take the E-item text the same structural way `frozen_region_digest` does (`ipd_lint.parse` separates a leaf's action text `Leaf.text` from its sub-fields `Leaf.fields` and its checkbox `Leaf.checked`, `ipd_lint.py:146-155`), and take the rows from E-01. Serialize deterministically (`sort_keys=True` over sorted lists) so the digest is stable across runs and dict ordering.
  KNOW WHAT IS ACTUALLY NEW HERE, because most of it is not. Measured at review on a real orchestrator, `frozen_region_digest` ALREADY ignores a checkbox tick, a filled `Observed evidence`, an appended history line and a prose edit, and ALREADY changes on an E-item action edit. The ONLY behavior this digest adds is CHILD-TABLE SENSITIVITY: a child-table edit leaves `frozen_region_digest` unchanged, because `_requirements_from_plan` (`ipd_lifecycle.py:517-548`) reads only `Scope-Paths`, E-item text and V-item text. So this function exists for one reason, and the child-table case is the one that must not regress. Note also what it deliberately DROPS relative to `frozen_region_digest`: `Scope-Paths` and V-item text, neither of which the probe reasons about. State that choice rather than leaving it implicit.
  THE ROW CELLS ARE LOAD-BEARING, NOT A DETAIL OF E-01. Keying on the parsed order graph would leave an Id swap and a description rewrite invisible (measured, round 2), which is the one failure mode that makes this cache actively wrong rather than merely useless: child 03 E-03 sends the child table to the model, so anything the probe READS and the key does not COVER serves a stale verdict. Keep the two inputs identical to child 03's payload by construction.
  KEEP PROSE INSIDE THE SECTION OUT. The `## Child IPDs` section carries explanatory paragraphs between its table and the next heading (`yeh7gc:54-56`); those are not the table, and including them would reintroduce the prose sensitivity `frozen_region_digest` deliberately excludes. Digest ROWS ONLY, and prove it (E-03).
  - Depends on: E-01
  - Expected outcome: a digest function unchanged by ticking a box, filling evidence, appending history or editing prose (inside or outside the child-IPDs section), and changed by editing an E-item's action text, adding a child row, swapping a child Id, or rewriting a child description; the divergence from `frozen_region_digest` (child-table rows in, Scope-Paths and V-items out) stated in its docstring.
  - Execution state: performed

- [x] E-03 Prove the `xmqv5l` trap is avoided, as a first-class deliverable rather than a side effect. Take a real orchestrator, apply each mutation a conforming executor makes (tick a checkbox, fill an `Observed evidence`, append a history line, edit a prose section), and assert the digest is IDENTICAL after each. Then assert it CHANGES for FOUR real edits: an E-item action edit, an ADDED child row, a child Id SWAP, and a child DESCRIPTION rewrite. The last two are the cases a parsed-order-graph key silently misses (measured, round 2), so a proof that omits them cannot distinguish a correct implementation from the broken one; the child-table cases together are also the only reason this digest exists rather than reusing `frozen_region_digest`. Add a fifth no-op: edit the explanatory prose INSIDE the `## Child IPDs` section and assert no change, which pins rows-not-section.
  - Depends on: E-02
  - Expected outcome: pasted before/after digests for FIVE no-op mutations (four executor mutations plus in-section prose) and FOUR real ones (E-item action, added row, Id swap, description rewrite).
  - Execution state: performed

- [x] E-04 Add the verdict store: per-repo, holding the digest, the verdict, when it was recorded, and WHICH MODEL answered. Record the model because a verdict is only as good as its author, and a future reader must be able to distrust an old one. Resolve the store's LOCATION per OQ-02 before writing it, and route the path through `ipd_lifecycle.checkout_control_root` (as `_runtime_dir` does, `:267-274`) rather than composing `repo_root / ".aw" / ...`, because an in-lane invocation's `repo_root` is the LANE and backlog `dh0uno` records that composing it by hand produced a second control store the driver could not see and teardown deleted.
  DO NOT ASSUME IT IS GITIGNORED. In THIS repo `.aw/state/` is ignored by the ROOT `.gitignore:60`, which the installer never writes; the framework-owned `.aw/.gitignore` it DOES write contains no `state/` entry, so in an adopter the path is NOT ignored (reproduced at review rounds 1 and 2: `git check-ignore` exits 1). Whatever location OQ-02 settles on, the ignore rule must be verified in a FRESH repo carrying only what the installer emits, not in this one.
  THE INSTALLER FIX IS A HARD PREREQUISITE OF THIS ITEM, NOT A NOTE, AND OQ-02's COST ARGUMENT FOR IT WAS MEASURED FALSE. OQ-02 resolved on option (a) partly because `_ensure_aw_gitignore` "already BACK-FILLS missing rules into an existing file, so adding `state/` reaches already-installed adopters on their next install". Measured at round 2: the back-fill is NOT generic. It is a hand-maintained list of per-pattern `if <literal> not in text` checks (`engine.py:5357-5404`), so adding `state/` to `_AW_GITIGNORE_TEMPLATE` alone reaches FRESH installs only; simulated by writing today's template into a scratch repo, appending `state/` to the template, and re-running `_ensure_aw_gitignore`, after which the existing file still had no `state/` line. Two edits are therefore required, exactly as plans `4r0qp1`/`yvvf98` and `rh5tt6` each independently recorded for their own patterns. DO NOT EXECUTE THIS ITEM until that installer change plus its `kw5y2s` spec amendment has landed under its own plan: this child's fence excludes `engine.py`, so writing the store first would ship a tracked LLM-verdict file to every adopter. No such plan exists today (searched), which OQ-03 now assigns.
  A SECOND, PRE-EXISTING EXPOSURE THIS ITEM MUST NOT BE BLAMED FOR AND MUST NOT WIDEN: in the same adopter-shaped repo, the SHIPPED control state is already trackable (`.aw/state/ipd-lifecycle/<id6>.receipt.json`, `state/runtime/locks/ipd_finalize_writer.lock`, `state/runtime/transactions/ipd_finalize_<id6>.json` all exit 1 from `git check-ignore`). So the `state/` template entry fixes a live defect wider than this cache, which strengthens the case for fixing it in the installer's own plan rather than here.
  - Depends on: E-02
  - Expected outcome: write-then-read round-trips; the store path is derived from `checkout_control_root`; a corrupt or unreadable entry is treated as absent rather than raising; the ignore status proven in an adopter-shaped repo AFTER the installer prerequisite landed, with the prerequisite's plan or commit cited.
  - Execution state: performed

- [x] E-05 Make a MISS fail closed, and decide the FAIL-caching question OQ-01 records. A missing entry means "not probed", which child 03 must treat as blocking, never as a pass: the whole point is that silence stops meaning safe. Then determine from the real digest function whether a `CONTAINS EXECUTIONS` verdict can be safely cached, and record the finding either way rather than assuming it.
  - Depends on: E-02, E-04
  - Expected outcome: an explicit tri-state (`pass` / `fail` / `unknown`), with `unknown` returned for a miss, and a recorded decision on caching failures with its evidence.
  - Execution state: performed

- [x] E-06 Add a STALENESS guard on the stored verdict, which nothing else in this child provides. A digest match proves the orchestrator has not changed; it proves nothing about whether the ANSWER is still trustworthy, and the plan already accepts that premise by recording the model ("a future reader must be able to distrust an old one") without giving anyone a mechanism to act on it. Implement the minimum: a verdict recorded by a DIFFERENT model than the current run resolves, or older than a stated bound, reads as `unknown` rather than as its recorded value. State the rule and its default explicitly; an unbounded cache of LLM verdicts is a cache that eventually answers for a model nobody would ask.
  THE MODEL IDENTITY IS OFTEN ABSENT, so decide that case rather than discovering it. Measured: `runner_profiles.resolve` returns `model=None` with provenance `host-default` whenever no `--model`, no named profile and no per-runner default supplies one (`runner_profiles.py:975-991`), and `oc_runipd` prints exactly `model=(host default)` for it (`:3150`). So the run frequently CANNOT name the model it is about to use, and a rule comparing recorded-to-current would then compare `None` to `None` and accept any age. Pick one and say which: treat an unknown model as never matching (fail closed, re-probe), or fall back to the time bound alone in that case. Do NOT write a rule whose primary key is a value that is routinely `None`, which is why the time bound must be the guard that always applies.
  - Depends on: E-04, E-05
  - Expected outcome: a stated staleness rule, implemented, with a verdict that fails it returning `unknown` and a fresh one returning its recorded value; the default bound recorded with its rationale; the `model=None` (host default) case decided explicitly and covered by a test.
  - Execution state: performed

- [x] E-07 Confirm both hosts share every symbol added, by OBJECT IDENTITY not grep (`2r306y`/`818uru`). `agy_runipd` imports 47 names from `oc_runipd` (measured by AST walk 2026-09-07, re-measured unchanged at 47 on 2026-09-08; backlog `cnwy8g` recorded 40, so it is growing), and no symbol this child adds may deepen that: both hosts import from `runner_shared`, never from the other host's driver. RE-MEASURE the count in the executing worktree rather than trusting 47: it moved once already between `cnwy8g` and this plan.
  - Depends on: E-02, E-04, E-05, E-06
  - Expected outcome: pasted proof each new symbol is one shared object defined in `runner_shared`, and that the oc-to-agy import count did not increase from 47.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `frozen_region_digest`'s docstring is the design brief for this child. It documents both the failure (a byte digest punishes correct execution) and the fix (hash the reviewed contract, not the file), and it names exactly which fields are mutable state. Read it before writing E-02. Read `_requirements_from_plan` (`:517-548`) too, since that is what decides what the existing digest covers, and it is why a child-table edit does not move it.
- MEASURE THE EXISTING DIGEST BEFORE WRITING A NEW ONE. It already satisfies four of the five properties this child was authored to establish; only child-table sensitivity is genuinely new. A new function that merely reproduces the old one is cost with no benefit.
- THE CHILD TABLE MUST BE DIGESTED AS ROW TEXT, NOT AS THE PARSED ORDER GRAPH. `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}`, so an Id swap and a description rewrite leave it byte-identical (measured on `yeh7gc`); only adding or removing a row moves it. Keying on it would make the digest blind to the edits a coverage question depends on, and would silently reintroduce the stale-verdict failure child 03 E-03 warns about.
- `runner_shared` ALREADY OWNS A CHILD-TABLE ROW SCANNER: `parse_declared_child_orders` (`:2398`) with `_TABLE_ROW_RE` (`:2227`) and `_TABLE_SEPARATOR_CELL_RE` (`:2230`). It keeps only cell 0. Extend/factor it rather than importing another module's parser, so the cache and the retirement gate agree on what a row is. Note it splits cells naively (`:2442`) where `ipd_set_plan._split_table_row` (`:206`) is backtick-aware; three live orchestrators (`94dhrt`, `mvz3d2`, `rreixg`) carry a backticked pipe, harmless for cell 0 and NOT harmless for an all-cells digest.
- `ipd_lint.parse` does NOT expose the child table. Its `ParsedDoc` fields are `title`, `meta_fields`, `meta_errors`, `h2`, `exec_leaves`, `valid_leaves`, `exec_task_groups`, `open_questions`, `size_assessment`, `history_lines`. It remains the right source for E-item action text (`Leaf.text`).
- IMPORT THE IPD PARSERS LAZILY from `runner_shared`. It has exactly ONE module-level first-party import (`render_stream`, `:136`) and already reaches `ipd_lint`, `ipd_schema` and `ipd_lifecycle` through function-local imports (`:2338`, `:2425`, `:2958`); `ipd_lifecycle` does the same at all seven of its `ipd_lint` sites. Adding a module-level first-party import to `runner_shared` would change the import graph for both host drivers.
- THE STORE IS NOT GITIGNORED BY THE FRAMEWORK. In this repo `.aw/state/` is ignored by the ROOT `.gitignore:60`. The installer explicitly does not write that file ("it is NOT the user's root `.gitignore` (that is never touched here)", `engine.py:4312-4313`), and `_AW_GITIGNORE_TEMPLATE` has no `state/` entry, so in an adopter the path is tracked. Verify any ignore claim in a fresh repo carrying only installer output. The same reproduction shows the SHIPPED control state (begin receipts, the finalize lock, finalize journals) is trackable there too, so this is a live framework defect wider than this cache.
- THE `.aw/.gitignore` BACK-FILL IS NOT GENERIC. `_ensure_aw_gitignore` (`engine.py:5357-5404`) is a hand-maintained list of per-pattern `if <literal> not in text` checks, so a new template entry reaches FRESH installs only until it is ALSO added to that list. Plans `4r0qp1`/`yvvf98` (F-7/F-14) and `rh5tt6` (F-12) each recorded this independently for their own patterns. Any claim that a template edit alone reaches existing adopters is false.
- A RUN OFTEN CANNOT NAME ITS MODEL. `runner_profiles.resolve` returns `model=None` with provenance `host-default` when nothing supplies one (`runner_profiles.py:975-991`), and the runner prints `model=(host default)` (`oc_runipd.py:3150`). A staleness rule keyed primarily on model identity would therefore compare `None` to `None` in the common case.
- Route control-state paths through `ipd_lifecycle.checkout_control_root`, never `repo_root / ".aw" / ...`: in a lane worktree `repo_root` is the LANE, and backlog `dh0uno` records that hand-composition produced a second store the driver could not see and teardown deleted.
- Do NOT modify `plan_content_digest` or `frozen_region_digest`. The begin receipt gate depends on them, and changing either would alter an unrelated safety check.
- BASELINE, RE-MEASURED AT ROUND 2: `python3 -m pytest` bare at HEAD `0274bc7c` gives `1 failed, 5648 passed, 3 skipped, 2 xfailed`. Round 1 measured `5632 passed` at HEAD `125105fe`, so the total moved by 16 in one day while the FAILING NODE ID stayed identical: `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, which asserts `{"kgpptv": "reviewed"}` while `kgpptv` reads `- Status: approved`. That is a test coupled to this repository's mutable plan statuses, unrelated to this child. This drift is exactly why the rule is compare failing NODE IDS, never totals: re-measure in the executing worktree and do not trust either number here.

## Findings

| Id | Severity | Location (2026-09-07; F-9..F-12 measured 2026-09-08) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:462` | The whole-file digest was measured to fail for this exact reason (`xmqv5l`); a byte-keyed cache would re-spend on every checkbox tick. | docstring records the measured failure |
| F-2 | MED | `ipd_lint.py:146-155` | `Leaf` already separates action text from sub-fields and checkbox state, so excluding mutable state is structural, not a fragile text rule. | source read |
| F-3 | BLOCKER | root `.gitignore:60`; `engine.py:4308-4313`, `_AW_GITIGNORE_TEMPLATE`; `.aw/.gitignore` | **THE STORE'S SITING RELIES ON AN IGNORE RULE THE FRAMEWORK NEVER SHIPS.** The original F-3 claimed `.aw/.gitignore` already ignores the runtime tree. It does not: that file says nothing about `state/` (its only `state` string is a comment about `records/runs/`). The rule ignoring it HERE is the ROOT `.gitignore:60`, which the installer explicitly never touches, and the template it DOES write contains zero occurrences of `state/`. So in every adopter repo the verdict store would be a TRACKED file holding LLM verdicts keyed to machine-local paths, which is a leak-sanitizer concern rather than mere untidiness. V-03's `git check-ignore` would have passed in this repo and proven nothing about an adopter. | reproduced in a throwaway repo carrying only `_AW_GITIGNORE_TEMPLATE`: `git check-ignore -v .aw/state/runtime/probe-verdicts.json` exits 1 (NOT ignored), while the same command in this repo matches `.gitignore:60` |
| F-4 | HIGH | `ipd_lifecycle.frozen_region_digest`, `_requirements_from_plan` (`:517-548`) | **FOUR OF THE FIVE PROPERTIES THIS CHILD PROPOSES TO ESTABLISH ALREADY HOLD, AND THE ONE REAL GAP WAS UNSTATED.** Measured on orchestrator `cczotj`: `frozen_region_digest` is UNCHANGED by a checkbox tick, a filled `Observed evidence`, an appended history line and a prose edit, and CHANGES on an E-item action edit. It does NOT change on a child-table edit, because `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item text. Child-table sensitivity is therefore the sole justification for a new digest, and E-02's proof as authored would have demonstrated only parity with the existing function. | called `frozen_region_digest` on the real file with each mutation applied; four `same=True`, E-edit `same=False`, child-table edit `same=True` |
| F-5 | HIGH | `ipd_lint.ParsedDoc`; `ipd_set_plan.parse_child_table` (`:334`) | **E-01's STATED REUSE DOES NOT EXIST.** The plan says to reuse `ipd_lint.parse`'s extraction for the child table, but `ParsedDoc` has no child-table field, so the executor would have discovered the gap mid-implementation and most likely written a second table parser beside `ipd_set_plan.parse_child_table`, which already resolves columns by header name and returns a typed refusal reason. | printed `ParsedDoc._fields`; no child/table member |
| F-9 | HIGH | `runner_shared.parse_declared_child_orders` (`:2398`), `_TABLE_ROW_RE` (`:2227`), `_TABLE_SEPARATOR_CELL_RE` (`:2230`), naive split (`:2442`); `ipd_set_plan._split_table_row` (`:206`) | **THE CHILD-TABLE ROW SCANNER IS ALREADY IN `runner_shared`, SO ROUND 1'S CROSS-MODULE REUSE WAS THE WRONG TARGET.** `parse_declared_child_orders` already finds the section by schema heading, matches rows, skips the alignment row, and then discards every cell but the first. Extending it (or factoring its row-walk) keeps ONE definition of "a child row" shared by the cache and the retirement gate; importing `ipd_set_plan` instead creates a second. One defect not to inherit: its cell split is naive `.split("\|")` where `ipd_set_plan._split_table_row` is backtick-aware, and three live orchestrators carry a backticked pipe (one splitting 12 cells instead of 4), harmless for cell 0 and not harmless for an all-cells digest. | source read; scanned every `Kind: orchestrator` plan comparing both splitters: `94dhrt`, `mvz3d2`, `rreixg` diverge |
| F-10 | BLOCKER | `ipd_set_plan.parse_child_table` return shape (`ChildTableResult.rows`, `:194-203`); child 03 (`m7gvuz`) E-03 | **THE DIGEST'S SOLE JUSTIFICATION COLLAPSES IF THE KEY USES THE PARSED ORDER GRAPH, WHICH IS WHAT ROUND 1's E-01 AND E-02 DIRECTED.** `rows` is `{order: (dep_orders,)}`, so on `yeh7gc` a child Id swap (`8tgg6g`->`qqqqqq`) and a full description rewrite BOTH leave it byte-identical; only adding/removing a row moves it. So the one property this child exists to add would hold for row COUNT changes and fail for row CONTENT changes, while OQ-01's fixture (which adds a row) would pass and hide it. This is the actively-wrong case, not the merely-useless one: child 03 E-03 sends the child table AS the probe payload and requires payload and key be the same inputs, so a row edit the key ignores serves a STALE VERDICT under apparent authority. | called `parse_child_table` on `yeh7gc` and on both mutations: `rows` identical (`{'1': (), '2': (), '3': ()}`) for the Id swap and the description rewrite; differs only for an added row. Row-cell extraction distinguishes all three |
| F-11 | HIGH | `engine._ensure_aw_gitignore` (`:5357-5404`); plans `4r0qp1` F-14, `yvvf98` F-7/E-06, `rh5tt6` F-12 | **OQ-02's RESOLUTION RESTS ON A FALSE COST CLAIM: THE BACK-FILL IS NOT GENERIC.** The maintainer's ruling cited that `_ensure_aw_gitignore` "already BACK-FILLS missing rules into an existing file, so adding `state/` reaches already-installed adopters on their next install". It is a hand-maintained list of per-pattern literal checks, so a template-only edit reaches FRESH installs ONLY. The chosen option therefore costs TWO edits plus a `kw5y2s` spec amendment, not one, and three other plans already recorded this same rule for their own patterns. The ruling's CONCLUSION still stands (option (a) is right, and `install_wizard.py:288-294` does forbid a tracked `state_runtime`); its cost basis does not, and E-04 was written to depend on it. | simulated an already-installed adopter: wrote today's template to `.aw/.gitignore`, appended `state/` to `_AW_GITIGNORE_TEMPLATE`, ran `_ensure_aw_gitignore` -> the existing file still had NO `state/` line |
| F-12 | MED | `runner_profiles.resolve` (`:975-991`, `PROVENANCE_HOST_DEFAULT`); `oc_runipd.py:3150` | **E-06's STALENESS RULE KEYS ON A VALUE THAT IS ROUTINELY ABSENT.** `resolve` returns `model=None` with provenance `host-default` whenever no explicit flag, named profile or per-runner default supplies a model, and the runner prints `model=(host default)`. A rule whose primary comparison is recorded-model versus current-model would then compare `None` to `None` and accept a verdict of any age, so the guard would silently not apply in the common case. The time bound must be the guard that always applies, and the `None` case must be decided explicitly. | source read; `PROVENANCE_HOST_DEFAULT` branch in `pick()` returns None for model/variant/agent |
| F-6 | MED | `runner_shared.py:136`; `ipd_lifecycle.py:515`, `:560`, `:950`, `:1326`, `:1783`, `:2046`, `:2618` | `runner_shared` has exactly ONE module-level first-party import and `ipd_lifecycle` reaches `ipd_lint` lazily at every site, so this child must import the IPD parsers inside functions. The plan did not say so, and a module-level import would change the graph for both drivers. | AST walk over `runner_shared`'s `ImportFrom` nodes at col 0 |
| F-7 | MED | measured | `agy_runipd` imports 47 names from `oc_runipd`, not the "~46" cited; `cnwy8g` recorded 40, so the coupling is still growing and a `~` figure is not a baseline a V-item can check. | AST walk over `ImportFrom` nodes targeting `oc_runipd` |
| F-8 | MED | plan E-03 (pre-revision) | The store records WHICH MODEL answered and the plan justifies it as letting "a future reader distrust an old one", but nothing consumed that field, so a verdict from a model nobody would ask today would still be served as authoritative forever. | plan read against its own E-items; no staleness rule anywhere |

## Proposed changes (ordered, validatable)

1. E-01 extracts child-table ROW CELLS by extending the scanner `runner_shared` already owns.
2. E-02 builds the key over row text; E-03 proves it, including the Id-swap and description-rewrite cases that are its only reason to exist.
3. E-04 adds the store (location per OQ-02, path via `checkout_control_root`), AFTER the installer prerequisite OQ-03 assigns; E-05 makes a miss fail closed and settles fail-caching.
4. E-06 makes the recorded model actionable via a staleness rule whose always-applicable guard is the time bound.
5. E-07 proves one shared definition without deepening the oc-to-agy coupling.

## Deferred / out of scope (with reason)

- The probe and its prompt: child 03 owns them, including the suspicion bias.
- Committing verdicts to git: deliberately not done. A verdict is an LLM output; keeping it box-local matches the receipt precedent and avoids a stale answer travelling to another machine. Cost accepted: a fresh clone re-probes once. NOTE this is a DECISION the current siting does not yet enforce in an adopter (F-3), which is what OQ-02 resolves.
- Any change to the two existing digest functions.
- Adding a `state/` entry to `_AW_GITIGNORE_TEMPLATE` **and to the `_ensure_aw_gitignore` back-fill list** so the framework ships the rule it relies on: that is a genuine defect this child MEASURED, and OQ-02 CHOSE it, but it belongs to the installer and affects every adopter. TWO edits are required, not one (F-11: the back-fill is a hand-maintained literal list, so a template-only change reaches fresh installs only), plus a `kw5y2s` spec amendment. It is a hard PREREQUISITE of E-04 rather than a parallel note, and OQ-03 assigns it because no plan owns it today.
- Reconciling `frozen_region_digest` and the new digest into one parameterized function: tempting after F-4, but `frozen_region_digest` is a begin-receipt gate input and this child's fence forbids touching it.

## Scope check

- Over-scope: none. Note `Scope-Paths` deliberately does NOT include `engine.py`: the installer gap (F-3, F-11) is real and OQ-02 chose to fix it, but it is a SEPARATE plan's work (OQ-03), not this child's to fix silently. That is why E-04 carries it as a prerequisite instead.
- Under-scope: none remaining. The child-table extraction (E-01) and the staleness rule (E-06) were under-scope before round 1. Round 2 added no new items: F-9/F-10/F-11/F-12 all corrected the CONTENT of existing items (what E-01 extracts, what E-02 keys on, what E-04 waits for, what E-06 keys on) rather than adding deliverables, so the item count is unchanged at seven.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals. In addition, the ignore-status check must run in a FRESH repo carrying only what `aw install` emits, because this repository's root `.gitignore` masks the adopter behavior (F-3).

## Spec / documentation sync

N/A for the cache mechanism: an internal store with no user-facing contract, and child 03 owns the spec sync for the gate.

ONE EXCEPTION TO CHECK RATHER THAN ASSUME: if OQ-02 resolves toward adding `state/` to `_AW_GITIGNORE_TEMPLATE`, that changes what every adopter receives on install, which IS a documented contract (spec `kw5y2s` governs the workspace hierarchy and the install-time emission). Whoever makes that change owes the spec amendment and must declare the file in `Scope-Paths`; this child does not, because the change is out of its fence.

## Open questions

### OQ-01: Is a `CONTAINS EXECUTIONS` (fail) verdict cached, or only a pass?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer: CACHE BOTH verdicts, and prove the stale-complaint case cannot happen with one test. There is no separate problem to solve here, because re-evaluate-on-change already covers it: the remedy for a fail is to move the work into a new child, which edits both the parent's checklist text and its child table, both of which the digest covers, so a genuine fix changes the key and discards the entry. The TEST is the deliverable, because the whole design rests on that property: build a throwaway fixture orchestrator in a temp dir, record its digest, store a hand-written fail verdict under it (NO model call), apply the fix within the fixture (remove the checklist item, add the child-table row), recompute, and assert the digest CHANGED and the lookup now returns not-checked rather than the stale fail. Paste both digests and both lookups. Then MUTATE the digest to ignore the child table, show the test FAILS, and revert: a test that cannot fail proves nothing.
  ROUND 2 ADDENDUM, and it strengthens the ruling rather than reopening it: the fixture as specified ADDS a child-table row, and a row ADD is the one child-table edit that a parsed-order-graph key would also catch (measured, F-10). So this fixture ALONE cannot distinguish a correct row-text digest from the broken order-graph one, and the mutation step would still show a failure, making it look sufficient. E-03 therefore additionally requires the Id-swap and description-rewrite cases, which only the row-text key catches. The ruling's requirement stands verbatim; it is now accompanied by the two cases it cannot see.

### OQ-02: Where may the verdict store live, given the framework does not ship the ignore rule this child assumed?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer: option (a), ADD `state/` TO THE INSTALLER TEMPLATE and site the store under `.aw/state/runtime/`. This is not a preference between equals: `install_wizard.py:288-293` already enforces a HARD INVARIANT that `state_runtime` MUST NOT be tracked in git and raises `InvalidPolicyError` for a policy that would track it, so the toolkit already forbids tracking this folder and merely fails to ship the `.gitignore` rule that makes the filesystem match its own declared policy. Any other location would route around a stated invariant. The installer change plus its spec amendment are OUTSIDE this child's fence and become its own dependency item.
  ONE FACT IN THE ORIGINAL RULING WAS MEASURED FALSE AT ROUND 2, and it changes the COST, not the CHOICE (F-11). The ruling stated that `_ensure_aw_gitignore` "already BACK-FILLS missing rules into an existing file, so adding `state/` reaches already-installed adopters on their next install rather than new ones only". It does not: the back-fill is a hand-maintained list of per-pattern `if <literal> not in text` checks (`engine.py:5357-5404`), so a template-only edit reaches FRESH installs ONLY. Reproduced by writing today's template into a scratch repo, appending `state/` to the template, and re-running `_ensure_aw_gitignore`: the existing file still carried no `state/` line. The correct cost is TWO edits (template AND back-fill list) plus the `kw5y2s` amendment, which is exactly what plans `4r0qp1`/`yvvf98` and `rh5tt6` each recorded for their own patterns. Option (a) remains right for the reason that actually decided it (the `install_wizard` invariant, re-verified at `:288-294`), and the correction is carried into OQ-03 and E-04.

### OQ-03: Which plan owns the installer `state/` ignore fix that E-04 now depends on?

- Blocking: yes
- Status: resolved
- Owner: none
- Finding: PR-009
- Question: OQ-02 chose option (a), so the framework must ship a `state/` ignore rule before this child writes a verdict store; measured, that needs TWO `engine.py` edits (`_AW_GITIGNORE_TEMPLATE` and the `_ensure_aw_gitignore` back-fill list) plus a `kw5y2s` spec amendment. Searched at round 2: no pending plan or backlog item owns it (`4r0qp1`/`yvvf98` cover the four INDEX manifests only, `rh5tt6` the two layout artifacts). This child's fence excludes `engine.py` deliberately, so the work has no owner and E-04 has an unmet prerequisite that no `Item-Dependencies` edge can express. Options: (a) file a backlog item and let it graduate normally, then add an `Item-Dependencies` edge from this child to the resulting plan; (b) fold the two edits plus the spec amendment into an existing gitignore-owning plan (`yvvf98` already edits both `engine.py` sites, so the marginal cost is two lines and one amendment); (c) widen THIS child's `Scope-Paths` to include `engine.py` and the spec, accepting that a cache plan now changes what every adopter receives on install; (d) re-open OQ-02 for a location that needs no new rule. Recommendation: (b), because `yvvf98` is already opening exactly those two functions for exactly this class of pattern, which avoids a third plan touching the same list. NOTE the fix is worth doing regardless of this cache: measured, the SHIPPED begin receipts, finalize lock and finalize journals are all trackable in an adopter today.
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: OPTION (b), fold the installer fix into `yvvf98`, which is already opening exactly those two functions for exactly this class of pattern. The marginal cost is about two lines plus one `kw5y2s` spec amendment, and it avoids a THIRD plan touching the same hand-maintained back-fill list.
  THE RECOMMENDATION'S PREMISE WAS RE-VERIFIED BEFORE ASKING, not taken on trust. `_AW_GITIGNORE_TEMPLATE` (`engine.py:4311`) and `_ensure_aw_gitignore` (`:5360`) are both real and both in `yvvf98`'s declared `- Scope-Paths:`, which already lists `agent_workflows/engine.py`; `yvvf98` is `- Status: approved` and mentions `engine.py` eight times. And the back-fill is confirmed NON-GENERIC: it is a sequence of literal `if "<pattern>" not in text:` checks, so adding `state/` to the template alone would reach FRESH installs only and every already-installed adopter would keep committing the file. Both edits are therefore required, as this question stated.
  CONSEQUENCE FOR THIS CHILD: E-04's prerequisite is now OWNED, so it gains an `Item-Dependencies` edge on `yvvf98` once that plan carries the fix. This child's fence stays as authored: `engine.py` remains OUT of its `- Scope-Paths:`, which is the property that made option (c) unattractive (a cache plan should not change what every adopter receives on install).
  RECORDED BECAUSE IT OUTLIVES THIS CACHE: the maintainer was told, and agreed the fix is worth doing on its own merits, that the SHIPPED begin receipts, the finalize lock and the finalize journals are all trackable in an adopter today. So `yvvf98` should fix the CLASS (every framework-written local-only path missing from the framework-owned ignore file), not merely add `state/` for this cache's benefit. Option (a) was declined as too slow for two lines, and option (d) as reopening a settled location decision while leaving the adopter problem unfixed for those other paths.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the extracted ROW CELLS for one real orchestrator (header row included) showing full cell tuples, not just Order tokens. Paste proof `parse_declared_child_orders` and the digest now share ONE row-walk (the shared helper's name plus both call sites), and paste its output on the three backticked-pipe orchestrators (`94dhrt`, `mvz3d2`, `rreixg`) showing the backtick-aware split does NOT fragment their rows; state whether `parse_declared_child_orders` itself was left on the naive split and why. Paste an AST walk over `runner_shared`'s module-level `ImportFrom` nodes showing it still has exactly ONE first-party module-level import (`render_stream`).
  - Observed evidence: VERIFIED 2026-09-14 in this lane worktree (`8tgg6g`) at start HEAD `fea2c9f8`. Measured, not recalled.

    (a) ROW CELLS for the REAL orchestrator `yeh7gc`, header row included, FULL tuples:

    ```
    ('Order', 'Id', 'Child plan', 'Depends on')
    ('01', 'r2i1b1', 'Surface a per-item refusal reason and its remedy in the run summary and `aw runs`', 'none')
    ('02', '8tgg6g', 'Cache an orchestrator probe verdict against a content digest that ignores execution state', 'none')
    ('03', 'm7gvuz', 'Probe every queued orchestrator for uncovered work before the run starts in earnest', 'executed:r2i1b1, executed:8tgg6g')
    ```

    (b) ONE SHARED ROW-WALK, helper name plus BOTH call sites (`inspect.getsource` over each caller):

    ```
    shared helper: child_table_rows
      parse_declared_child_orders: for cells in child_table_rows(orchestrator_text, backtick_aware=False):
      probe_cache_payload: "child_table_rows": [list(row) for row in child_table_rows(orchestrator_text)],
      parse_declared_child_orders still has its own row matcher? False
    ```

    So the gate no longer carries `_TABLE_ROW_RE.match` at all: there is exactly one definition of "a child row" and the retirement gate and the cache cannot disagree about it. No second table parser was written and `ipd_set_plan.parse_child_table` was NOT imported.

    (c) THE THREE BACKTICKED-PIPE ORCHESTRATORS, backtick-aware split does NOT fragment (cell counts per row, both splitters, on the live files):

    ```
    94dhrt  aware=[4, 4, 4, 4, 4, 4]   naive=[4, 4, 4, 5, 4, 4]   cell0 identical=True
      FRAGMENTED under naive: (..., 'Read-only `aw attention` full-scan over specs/plans/research; `--format json', 'markdown`, ...)
      same row, aware       : (..., 'Read-only `aw attention` full-scan over specs/plans/research; `--format json|markdown`, ...)
    mvz3d2  aware=[4, 4, 4, 4, 4, 4]   naive=[4, 12, 4, 4, 4, 4]  cell0 identical=True
      FRAGMENTED under naive: 12 cells, splitting `all|plans|specs|prompts|research|backlog|...` into eight bogus columns
      same row, aware       : 4 cells, the backticked vocabulary intact
    rreixg  aware=[4, 4, 4, 4]         naive=[4, 4, 5, 4]         cell0 identical=True
      FRAGMENTED under naive: (..., 'Add the `Blocks-Release: <release-id6\', 'next>` item field: ...)
      same row, aware       : (..., 'Add the `Blocks-Release: <release-id6\|next>` item field: ...)
    ```

    (d) `parse_declared_child_orders` WAS DELIBERATELY LEFT ON THE NAIVE SPLIT, and the reason is measured rather than asserted: it reads only cell 0, and cell 0 is IDENTICAL under both splitters for every row of every one of the three divergent orchestrators (`cell0 identical=True` above; the same scan over ALL `Kind: orchestrator` plans reported `rows where CELL 0 differs: NONE`). Changing it would be a behavior change to a retirement gate made by a plan whose subject is a cache. Its Order tokens are unchanged on exactly the three files where the splitters diverge:

    ```
    94dhrt (('01', '02', '03', '04', '05'), True)
    mvz3d2 (('01', '02', '03', '04', '05'), True)
    rreixg (('01', '02', '03'), True)
    ```

    Pinned by `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_the_gate_keeps_the_naive_split_so_its_behavior_is_unchanged` and `::test_the_gate_still_reads_the_five_real_column_shapes` (all five real column layouts, including `rununify`'s Id-less shape).

    (e) AST WALK over `runner_shared`'s MODULE-LEVEL first-party imports: unchanged, still the one `render_stream` import plus the designated peer `runner_profiles`:

    ```
    line 150: from agent_workflows import runner_profiles
    line 151: from agent_workflows.render_stream import Palette, render_run_summary_table
    ```

    Every IPD parser this child needs (`ipd_lint`, `ipd_schema`, `ipd_lifecycle`, `ipd_set_plan`) is reached through a FUNCTION-LOCAL import, so the import graph for both host drivers is unchanged. Pinned by `::test_no_new_module_level_first_party_import_in_runner_shared`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the digest of one real orchestrator computed twice in SEPARATE PROCESSES, showing byte-identical output (determinism, not just repeatability within one run). Paste the docstring passage stating the deliberate divergence from `frozen_region_digest` (child-table ROWS in; `Scope-Paths` and V-item text out). Paste the serialized payload the digest hashes for one orchestrator, so a reader can SEE that it carries row cell text and carries no in-section prose.
  - Observed evidence: VERIFIED 2026-09-14 in this lane worktree.

    (a) DETERMINISM ACROSS SEPARATE PROCESSES (two independent `python3 -c` interpreters, not two calls in one run):

    ```
    process 1: 20af5d0ec94406caa9696e6f460bb2cfa4ae7ae2a43ca87cb10b8250e417b099
    process 2: 20af5d0ec94406caa9696e6f460bb2cfa4ae7ae2a43ca87cb10b8250e417b099
    byte-identical: True
    ```

    Pinned by `::TheDigestIsDeterministic::test_two_separate_interpreters_agree`, which subprocesses a fresh interpreter twice rather than trusting in-process repeatability.

    (b) THE DOCSTRING PASSAGE stating the deliberate divergence, read back off the live function object (`rs.probe_cache_digest.__doc__`):

    ```
    DELIBERATE DIVERGENCE FROM :func:`ipd_lifecycle.frozen_region_digest`, stated because the
      * CHILD-TABLE ROWS ARE IN here and are OUT there. That is the only new sensitivity, and it is
        why this exists: `_requirements_from_plan` reads only `Scope-Paths`, E-item text and V-item
        text, so a child-table edit does not move the frozen digest (measured).
      * `Scope-Paths` and V-ITEM TEXT ARE OUT here and are IN there. The probe asks whether the
        parent's ACTIONS are covered by children; neither a scope entry nor a validation row can
        change that answer, so including them would re-probe for nothing.
    ```

    (c) THE SERIALIZED PAYLOAD THE DIGEST HASHES, so a reader can SEE what is in it and what is not:

    ```json
    {
      "child_table_rows": [
        ["Order", "Id", "Child plan", "Depends on"],
        ["01", "aaa111", "Surface the refusal reason and its remedy", "none"],
        ["02", "bbb222", "Cache the verdict against a content digest", "none"],
        ["03", "ccc333", "Probe every queued orchestrator", "executed:aaa111, executed:bbb222"]
      ],
      "e_items": [
        "E-01 SEQUENCE THE THREE CHILDREN IN ORDER, confirming each is executed before the next.",
        "E-02 CONFIRM the Set's records are reconciled once every child has landed."
      ]
    }
    ```

    It carries ROW CELL TEXT (`bbb222`, `Cache the verdict against a content digest`). It carries NO in-section prose, NO `Scope-Paths` and NO V-item text, each checked against the serialized blob:

    ```
    contains in-section prose ('DEFECT TODAY')? False
    contains Scope-Paths value?               False
    contains V-item text?                     False
    ```

    Pinned by `::TheDigestIgnoresWhatCorrectExecutionChanges::test_the_payload_carries_no_prose_from_inside_the_child_section`, `::test_the_payload_carries_the_row_cell_TEXT` and `::test_the_payload_carries_no_scope_paths_and_no_V_item_text`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste before/after digests for FIVE no-op mutations (tick a checkbox, fill Observed evidence, append a history line, edit a prose section, edit the prose INSIDE the `## Child IPDs` section) showing NO change, and for FOUR real edits showing a change: an E-item action edit, an ADDED child row, a child Id SWAP, and a child DESCRIPTION rewrite. Then paste TWO contrasts, both required: (a) the same child-table mutations run through `ipd_lifecycle.frozen_region_digest` showing it does NOT move, which is why this function exists at all; and (b) `ipd_set_plan.parse_child_table(...).rows` for the Id-swap and description-rewrite cases showing them BYTE-IDENTICAL, which is why the key must be row TEXT and not the parsed order graph (F-10). A V-03 missing either contrast, or missing the Id-swap and description cases, is not evidence: a row-ADD-only proof cannot tell a correct implementation from the broken one.
  - Observed evidence: VERIFIED 2026-09-14. Base `probe_cache_digest` = `20af5d0ec94406caa9696e6f460bb2cfa4ae7ae2a43ca87cb10b8250e417b099`. Each mutation is applied to a FROZEN in-module fixture (never to a live plan file, for the `RealRepositorySets` reason the orchestrator's CID-2 records), and each mutation function asserts the text actually changed before the digest is compared.

    (a) FIVE NO-OP mutations, digest UNCHANGED (the `xmqv5l` proof):

    ```
    tick-a-checkbox                        after=20af5d0e...e417b099 same=True
    fill-observed-evidence                 after=20af5d0e...e417b099 same=True
    append-a-history-line                  after=20af5d0e...e417b099 same=True
    edit-prose-outside-the-child-section   after=20af5d0e...e417b099 same=True
    edit-prose-inside-the-child-section    after=20af5d0e...e417b099 same=True
    ```

    The fifth is the rows-not-section pin: the explanatory paragraph INSIDE `## Child IPDs...` was rewritten wholesale and the digest did not move.

    (b) FOUR REAL edits, digest CHANGED, each to a DIFFERENT value:

    ```
    edit-an-e-item-action          after=f4f736496c1c945323962b9b1be183b15d196d99401d1bc3b1d3d792686b6786 changed=True
    add-a-child-row                after=95f3644ec5f71ede9d97ba7dc2858d968dc59d9bb081af4ad2092d52588fde53 changed=True
    swap-a-child-id                after=48e2573a73a7d14dc5d4be416e9fabdae2c96271fdf9683a1c4bad28cb590f2f changed=True
    rewrite-a-child-description    after=a2200e8106bfe563bdb3cabe8e43c3a5adc2a63781257398ea025aed184d6aef changed=True
    ```

    (c) CONTRAST 1, REQUIRED: `ipd_lifecycle.frozen_region_digest` on the SAME child-table edits does NOT move, which is the entire reason this function exists rather than reusing it:

    ```
    frozen base: 87d32cf0414e10360bf244464144fd96b04ca2712fd5154ab3644108ed3f13c7
    add-a-child-row                after=87d32cf0...ed3f13c7 MOVED=False
    swap-a-child-id                after=87d32cf0...ed3f13c7 MOVED=False
    rewrite-a-child-description    after=87d32cf0...ed3f13c7 MOVED=False
    control: frozen digest DOES move on an E-item edit: True
    ```

    The control line matters: it shows the frozen digest is live and reachable in this fixture, so the three `MOVED=False` results are a real gap and not a broken measurement.

    (d) CONTRAST 2, REQUIRED (F-10): `ipd_set_plan.parse_child_table(...).rows` is BYTE-IDENTICAL for the two row-CONTENT edits, and moves only for the row ADD:

    ```
    base rows:                     {'1': (), '2': (), '3': ()}
    swap-a-child-id                rows={'1': (), '2': (), '3': ()}            identical=True
    rewrite-a-child-description    rows={'1': (), '2': (), '3': ()}            identical=True
    add-a-child-row                rows={'1': (), '2': (), '3': (), '4': ()}   identical=False   <- the ONE both keys catch
    ```

    (e) The same two edits DO move the row cells, which is why the key is row CELL TEXT:

    ```
    swap-a-child-id                distinguished=True
    rewrite-a-child-description    distinguished=True
    ```

    Pinned by `::TheDigestIgnoresWhatCorrectExecutionChanges`, `::TheDigestChangesForARealEdit`, `::TheDigestDiffersFromFrozenRegionDigest` and `::TheKeyIsRowTextNotTheOrderGraph`. The last two classes are written as CONTRASTS deliberately: if `frozen_region_digest` ever gained child-table sensitivity, or `parse_child_table` ever gained row-content sensitivity, those tests FAIL and tell the reader to re-derive whether this function should exist at all.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a write-then-read round trip including the recorded model; paste the resolved store path showing it derives from `checkout_control_root` (and that it is IDENTICAL when computed from the main tree and from a linked worktree, which is the `dh0uno` property); paste the behavior on a deliberately corrupted entry showing it reads as absent rather than raising; and paste `git check-ignore -v` for the store path run inside a FRESH repo carrying only installer output, not this one. State which OQ-02 option was implemented, and CITE the plan or commit that landed the installer prerequisite (both `engine.py` edits plus the `kw5y2s` amendment). If that prerequisite has not landed, this V-item FAILS and E-04 must not have been performed: a passing `check-ignore` obtained any other way (running it in THIS repo, or hand-editing the scratch repo's `.aw/.gitignore`) does not satisfy it, because the property under test is what an ADOPTER receives from the installer.
  - Observed evidence: VERIFIED 2026-09-14. OQ-02 OPTION (a) WAS IMPLEMENTED: the store is sited under `.aw/state/runtime/`, as `orchestrator-probe-verdicts.json`.

    THE INSTALLER PREREQUISITE HAS LANDED, AND IT WAS NOT THIS CHILD THAT LANDED IT. Cited: commit `ee38864c` ("fix two gitignore defects: the parity test's tree walk, and the installer's state tree", 2026-09-12, backlog `2812t3`). Its message states the requirement this V-item exists to enforce: "Neither _AW_GITIGNORE_TEMPLATE (fresh) nor _ensure_aw_gitignore (the only path reaching an already-installed repo) had any entry for state/ or config/local.json. Both gained anchored /state/ and /config/local.json". So BOTH `engine.py` edits F-11 measured as required are present, verified independently here:

    ```
    '/state/' in _AW_GITIGNORE_TEMPLATE:                       True
    '/state/' in the _ensure_aw_gitignore back-fill list:      True
    ```

    That commit also carried the tests (`MachineLocalStateGitignoreTests`, `tests/test_engine_install.py:625`) and re-synced this repo's own `.aw/.gitignore` to the template. NOTE ON THE `kw5y2s` AMENDMENT: `ee38864c` landed the code and the tests but records no spec amendment, so if `kw5y2s` requires the emitted-ignore-set to be enumerated in the spec, that amendment is still owed BY THAT WORK, not by this child (whose fence excludes both `engine.py` and the spec). Recorded here rather than silently closed, and raised in the run's decisions register as DECISION 05-8tgg6g-D2.

    (a) WRITE-THEN-READ ROUND TRIP including the recorded model (store contents pasted verbatim):

    ```json
    {
      "entries": {
        "20af5d0ec94406caa9696e6f460bb2cfa4ae7ae2a43ca87cb10b8250e417b099": {
          "model": "its_direct/pt3-claude-opus-5-1m-us",
          "recorded_at": "2026-09-14T05:00:22+00:00",
          "verdict": "pass"
        }
      },
      "schema_version": 1
    }
    ```

    ```
    read back: ProbeVerdict(verdict='pass', recorded_verdict='pass',
                            recorded_at='2026-09-14T05:00:22+00:00',
                            model='its_direct/pt3-claude-opus-5-1m-us', stale_reason='')
    ```

    (b) THE PATH DERIVES FROM `checkout_control_root`, and the `dh0uno` property holds: a REAL `git worktree` was created and the store resolves to ONE location from both trees:

    ```
    from MAIN tree:   <tmp>/main/.aw/state/runtime/orchestrator-probe-verdicts.json
    from LANE tree:   <tmp>/main/.aw/state/runtime/orchestrator-probe-verdicts.json
    IDENTICAL: True
    derived via checkout_control_root: True
    ```

    (c) A CORRUPTED STORE AND A CORRUPTED ENTRY read as ABSENT rather than raising, and the two are DISTINGUISHED in the report:

    ```
    truncated JSON  -> ProbeVerdict(verdict='unknown', ..., stale_reason='no-entry')
    non-object entry-> ProbeVerdict(verdict='unknown', ..., stale_reason='unreadable-entry')
    ```

    (d) `git check-ignore -v` INSIDE A FRESH REPO CARRYING ONLY INSTALLER OUTPUT (a temp dir, `git init`, then `engine._ensure_aw_gitignore` and nothing else; NOT this repository, whose root `.gitignore` would have made this pass vacuously):

    ```
    $ git check-ignore -v .aw/state/runtime/orchestrator-probe-verdicts.json
    rc = 0 -> .aw/.gitignore:60:/state/	.aw/state/runtime/orchestrator-probe-verdicts.json
    ```

    And the ALREADY-INSTALLED adopter path (an existing `.aw/.gitignore` carrying only `records/*/untracked/`, i.e. a repo installed before `state/` existed, then the back-fill run):

    ```
    `/state/` back-filled: True
    rc = 0 -> .aw/.gitignore:12:/state/	.aw/state/runtime/orchestrator-probe-verdicts.json
    ```

    Both attribute the ignore to `.aw/.gitignore`, the FRAMEWORK-OWNED file, not to a root `.gitignore` the installer never writes. Pinned by `::TheStoreIsGitignoredInAnAdopter::test_check_ignore_matches_the_framework_owned_gitignore` and `::test_the_template_and_the_backfill_BOTH_carry_the_rule`, each building its own fresh repo.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a miss returning `unknown` (NOT pass), and the recorded fail-caching decision with its evidence: if a fail IS cached, paste the fixture where the remedy (moving the work into a new child) was actually applied and the digest MOVED, rather than an argument that it would. Include TWO mutation checks, since each pins a different property: make a miss return pass, show a test FAILS, revert; and make the digest ignore the child-table rows, show the OQ-01 fixture test FAILS, revert.
  - Observed evidence: VERIFIED 2026-09-14.

    (a) A MISS RETURNS `unknown`, NOT `pass`:

    ```
    empty store  -> ProbeVerdict(verdict='unknown', recorded_verdict='', recorded_at='', model='', stale_reason='no-entry')
    is it pass?   False
    ```

    (b) THE FAIL-CACHING DECISION, per OQ-01's ruling: BOTH polarities are cached, and the remedy was APPLIED to the fixture rather than argued about. `record_probe_verdict` accepts only `pass`/`fail` and REFUSES `unknown` with a `ValueError`, because storing `unknown` would turn "not probed" into a stored fact:

    ```
    digest BEFORE remedy: 20af5d0ec94406caa9696e6f460bb2cfa4ae7ae2a43ca87cb10b8250e417b099
    lookup BEFORE       : fail          <- the fail IS served before the remedy, or this proves nothing
    digest AFTER  remedy: 509115202eed1f87388bb2ed5ce0145e947fe9429e415fa87d76011e5a00e4bb
    moved: True
    lookup AFTER        : ProbeVerdict(verdict='unknown', ..., stale_reason='no-entry')
    ```

    The remedy actually applied to the fixture (unified diff), i.e. the parent's item moved OUT of the checklist and INTO a child row, exactly the two edits the ruling names:

    ```diff
    @@ -30,7 +30,2 @@
    -- [ ] E-02 CONFIRM the Set's records are reconciled once every child has landed.
    --  - Depends on: E-01
    --  - Expected outcome: records reconciled.
    --  - Execution state: pending
     ## Child IPDs, sequence, and dependencies
    @@ -44,2 +39,3 @@
     | 03 | ccc333 | Probe every queued orchestrator | executed:aaa111, executed:bbb222 |
    +| 04 | ddd444 | Reconcile the Set's records | executed:ccc333 |
    ```

    ROUND 2'S ADDENDUM IS HONORED: the ruling's fixture alone could not distinguish a correct row-text key from the broken order-graph one, so a THIRD case was added (`::test_a_ROW_ONLY_remedy_also_discards_the_stale_fail`) covering the remedy where a child is added and the parent's item is left as sequencing prose. That is the case only child-table sensitivity catches, and it is the dangerous direction: a fixed orchestrator would otherwise keep being served its old FAIL.

    (c) MUTATION CHECK 1 (a miss returns `pass`): `read_probe_verdict`'s miss branch was edited to return `PROBE_VERDICT_PASS`, the module suite was re-run, and FIVE tests FAILED, including the OQ-01 fixture. Actual output:

    ```
    === MUTATION 2: a cache MISS returns `pass` instead of `unknown` ===
    E       AssertionError: 'pass' != 'unknown'
    FAILED tests/test_orchestrator_probe_cache.py::VerdictStoreTests::test_a_corrupt_store_reads_as_ABSENT_rather_than_raising
    FAILED tests/test_orchestrator_probe_cache.py::AMissFailsClosed::test_an_empty_store_returns_unknown
    FAILED tests/test_orchestrator_probe_cache.py::AMissFailsClosed::test_a_digest_that_moved_is_a_MISS_not_the_old_verdict
    FAILED tests/test_orchestrator_probe_cache.py::AStaleFailCannotBeServed::test_the_remedy_MOVES_the_digest_so_the_fail_entry_is_discarded
    FAILED tests/test_orchestrator_probe_cache.py::AStaleFailCannotBeServed::test_a_ROW_ONLY_remedy_also_discards_the_stale_fail
    5 failed, 51 passed in 23.85s
    ```

    REVERTED, byte-for-byte (`restored identical: True`).

    (d) MUTATION CHECK 2 (the digest IGNORES the child-table rows): `probe_cache_payload`'s rows entry was replaced with `[]`, the module suite was re-run, and SIX tests FAILED. Actual output:

    ```
    === MUTATION 1: the digest IGNORES the child-table rows ===
    E       AssertionError: '0e925f6f...e8ce8e80c05557f04d7b17e0668b4faa73498' == '0e925f6f...ce8e80c05557f04d7b17e0668b4faa73498'
              : add-a-child-row left the digest unchanged; the probe would serve a stale verdict
    FAILED tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_the_digest_payload_also_calls_the_shared_row_walk
    FAILED tests/test_orchestrator_probe_cache.py::VerdictStoreTests::test_recording_one_verdict_does_not_discard_another
    FAILED tests/test_orchestrator_probe_cache.py::TheDigestIgnoresWhatCorrectExecutionChanges::test_the_payload_carries_the_row_cell_TEXT
    FAILED tests/test_orchestrator_probe_cache.py::AStaleFailCannotBeServed::test_the_remedy_is_detected_by_the_checklist_edit_ALONE_too
    FAILED tests/test_orchestrator_probe_cache.py::TheDigestDiffersFromFrozenRegionDigest::test_the_probe_digest_DOES_move_on_those_same_edits
    FAILED tests/test_orchestrator_probe_cache.py::TheDigestChangesForARealEdit::test_each_real_edit_MOVES_the_digest
    6 failed, 49 passed in 17.02s
    ```

    REVERTED, byte-for-byte (`restored identical: True`). NOTE the first mutation run was performed BEFORE `::test_a_ROW_ONLY_remedy_also_discards_the_stale_fail` was added, which is why that node id is absent from its failure list; that test's own failure under the same mutation is implied by `::test_the_remedy_is_detected_by_the_checklist_edit_ALONE_too` failing, and its row-only assertion depends on precisely the sensitivity the mutation removes.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the staleness rule and its default bound; paste a stored verdict that fails the rule (a different model, or past the bound) being read as `unknown` rather than as its recorded value; and paste a fresh verdict being read as its recorded value, so the rule is shown to discriminate rather than to reject everything. Paste the `model=None` (host default) case explicitly: a stored verdict with no recorded model read under a run that also resolves no model, showing the decided behavior (re-probe, or time-bound-only) rather than an accidental match of `None` to `None` (F-12).
  - Observed evidence: VERIFIED 2026-09-14.

    THE RULE, as implemented in `read_probe_verdict`: (1) no entry / unusable entry -> `unknown`; (2) OLDER THAN the bound -> `unknown` (the guard that ALWAYS applies); (3) recorded by a DIFFERENT named model than the caller resolves -> `unknown`; (4) otherwise the recorded verdict is served. THE DEFAULT BOUND is the named constant `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`, carrying its rationale in the source beside it (long enough that the cache saves the re-probes it exists to save, short enough that a verdict cannot much outlive the model generation that produced it); it is overridable per read and no call site hardcodes a literal.

    THE RULE DISCRIMINATES rather than rejecting everything. Seven cases, each recorded into a fresh store and read back:

    ```
    DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30
    fresh, same model                -> verdict=pass     stale_reason=(served)
    past the bound (400d)            -> verdict=unknown  stale_reason=older-than-bound
    DIFFERENT model                  -> verdict=unknown  stale_reason=model-changed
    model=None BOTH, fresh           -> verdict=pass     stale_reason=(served)
    model=None BOTH, 400d            -> verdict=unknown  stale_reason=older-than-bound
    recorded None, current named     -> verdict=pass     stale_reason=(served)
    recorded named, current None     -> verdict=pass     stale_reason=(served)
    ```

    A verdict rejected for age still REPORTS what was stored (`recorded_verdict='pass'`), so a human can see what expired rather than only that something did.

    THE `model=None` (HOST DEFAULT) CASE IS DECIDED, NOT ACCIDENTAL (F-12). DECISION: when EITHER side cannot name a model, the model comparison is SKIPPED and the TIME BOUND alone decides. The two `model=None BOTH` rows above show that explicitly: fresh -> served, 400 days -> `older-than-bound`, so the guard is not silently absent in the common case; it is the time bound doing the work, by design. The REJECTED alternative was "an unknown model never matches" (re-probe), which is superficially fail-closed but, since `host-default` is routine, would make the cache miss almost always. Recorded as DECISION 05-8tgg6g-D1 with the honest cost stated in the docstring: a verdict from an unnamed model A can be served to a run also using an unnamed model B, within the bound.

    THE PREMISE IS ASSERTED, so the rationale cannot quietly become false:

    ```
    runner_profiles.resolve(ProfileConfig(), runner="opencode").model            -> None
    runner_profiles.resolve(ProfileConfig(), runner="opencode").provenance['model'] -> 'host-default'
    ```

    An unparseable `recorded_at` is treated as INFINITELY OLD (`older-than-bound`), never as fresh. Pinned by `::StalenessRuleTests` (six tests) and `::TheHostDefaultModelCaseIsDecided` (six tests, including the premise test and the docstring-states-its-cost test).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted object-identity output per new symbol showing each resolves to the same object from both hosts and is defined in `runner_shared`, plus the AST-measured oc-to-agy import count taken IN THE EXECUTING WORKTREE before and after, showing it did not increase. Do not assert the literal 47 without re-measuring the before value: it was 40 at `cnwy8g` and 47 at both review rounds.
  - Observed evidence: VERIFIED 2026-09-14 IN THE EXECUTING WORKTREE. All sixteen new symbols resolve to ONE object reached identically from both hosts (`oc_runipd.runner_shared.X is runner_shared.X` and the same for `agy_runipd`), each DEFINED in `runner_shared`:

    ```
    child_table_rows                     oc is shared=True agy is shared=True defined_in=runner_shared
    probe_cache_payload                  oc is shared=True agy is shared=True defined_in=runner_shared
    probe_cache_digest                   oc is shared=True agy is shared=True defined_in=runner_shared
    probe_verdict_store_path             oc is shared=True agy is shared=True defined_in=runner_shared
    record_probe_verdict                 oc is shared=True agy is shared=True defined_in=runner_shared
    read_probe_verdict                   oc is shared=True agy is shared=True defined_in=runner_shared
    ProbeVerdict                         oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_VERDICT_PASS                   oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_VERDICT_FAIL                   oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_VERDICT_UNKNOWN                oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_VERDICT_STORE_SCHEMA_VERSION   oc is shared=True agy is shared=True defined_in=runner_shared
    DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS   oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_STALE_MISS                     oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_STALE_CORRUPT                  oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_STALE_MODEL_CHANGED            oc is shared=True agy is shared=True defined_in=runner_shared
    PROBE_STALE_TOO_OLD                  oc is shared=True agy is shared=True defined_in=runner_shared
    ```

    THE oc-to-agy IMPORT COUNT, RE-MEASURED HERE RATHER THAN TRUSTED. The plan says 47 (both review rounds) and backlog `cnwy8g` recorded 40; this worktree measures 48 BEFORE this child, so the literal in the plan was already stale and asserting it would have been a false baseline. The property asserted is that it DID NOT INCREASE, measured by AST walk over `agy_runipd`'s `ImportFrom` nodes targeting `oc_runipd`, before (from `git show HEAD:`) and after:

    ```
    count BEFORE (git HEAD): 48
    count AFTER this child:  48
    increased: False
    any new symbol imported from oc_runipd: NONE
    ```

    `::test_exactly_one_definition_package_wide` additionally walks every module in the package by AST and asserts each of the sixteen names is defined in `runner_shared.py` and nowhere else, so a future re-fork fails rather than merely being noticed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION IS BLOCKED ON OQ-03, and human approval alone does not clear it. OQ-03 carries `- Blocking: yes`, and that is the field the pre-execution checkpoint actually reads (verified at round 2: `plan_readiness.has_unresolved_blocking_question` returned False while this paragraph named OQ-02, because OQ-02 has carried `- Blocking: no` and `- Status: resolved` since the maintainer's 2026-09-07 ruling; the sentence asserted a gate nobody enforced). OQ-03 asks which plan owns the installer `state/` ignore fix that OQ-02's own resolution requires: the answer either assigns work to another plan or widens this child's fence to `engine.py`, so it is not an executor's call.

E-04 additionally carries a PREREQUISITE no gate can express: the installer fix must have LANDED before the verdict store is written, or this child ships a tracked LLM-verdict file to every adopter. `Item-Dependencies` cannot name a plan that does not yet exist, so V-04 enforces it by demanding the landing plan or commit be cited. E-01, E-02, E-03 and E-07 are unaffected and are the useful work available before that lands.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 8tgg6g --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
