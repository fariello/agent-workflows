# IPD: Mint id6 against the unified inventory and close D140's declared-duplicate blind spot

- Date: 2026-09-08
- Kind: child
- Concern: id6 IS MINTED PER-TREE, SO A CROSS-TYPE COLLISION IS POSSIBLE AT CREATION, AND ONE EXISTS ON MAIN RIGHT NOW THAT `aw check all` DOES NOT REPORT. `artifact_core.generate_id6(existing)` is collision-checked against a caller-supplied set, and every caller supplies only its OWN tree: `backlog.py:356` scans backlog ids, `releases.py:62` release ids, `specs.py:933` spec ids, `ipd_authoring.py:316`/`:328` plan ids, `artifact_rename.py:513` one type's ids. The unified inventory that WOULD make this impossible already exists and is already what the collision CHECKER consumes, so the substrate is present and simply not used at mint time.
  MEASURED AT HEAD, AND IT IS A DIFFERENT INSTANCE THAN THE ITEM DESCRIBES. `status_set.inventory_all_artifacts` returns 703 artifacts carrying an id6, 702 distinct, ONE colliding: `uyeko5` is declared by BOTH the executed plan `.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md` AND the research prompt `.aw/records/research/20260905-awmetastore-00-27rjro-where-aw-metadata-should-live.research-prompt.md`. The research prompt's OWN identity is `27rjro` (its YAML front matter says `id: 27rjro`, and its filename slot agrees); the `uyeko5` it declares is inside a QUOTED EXAMPLE in its prose, at `:60`, illustrating a plan's metadata block for an external LLM. `aw find uyeko5` today prints THREE rows: the plan, that research prompt, and a review file.
  THE BLIND SPOT IS NOT THE ONE THE ITEM PREDICTED, AND THAT MATTERS FOR THE FIX. The item's defect 3 says D140's identity-slot rule cannot catch a file that DECLARES another artifact's id6 while its slot agrees. Verified true by direct call: `_check_identity_slots` returns ZERO findings for a synthetic record pair where both files declare AND slot the same id6, because rule (a) compares slot against the file's own declared Id (equal, so it passes) and rule (b) is skipped for a file that declares an Id. But the LIVE case is a different shape again: the research prompt's slot is `None` (`_identity_slot_token` returns None for its `-00-` order-first name), so no identity-slot rule engages at all, while the plain `- Id:` regex (`_ID_LINE_RE`, `check_engine.py:758`) matches a line in PROSE. So the live defect is a FRONT-MATTER PARSER reading a body line, not an identity-slot gap. Both must be fixed; conflating them would leave one open.
  WHY THE FULL SWEEP MISSES IT, WHICH IS THE MOST SURPRISING MEASUREMENT HERE. `aw check all` reports ZERO `check.id6-collision` at HEAD, while `aw doctor` DOES report exactly this one. The cause is the RETIRED filter, not the collision rule: `_iter_type_files` skips a retired path unless `include_retired=True` (`check_engine.py:493`), the colliding plan lives in `executed/` which `is_retired` treats as retired (`:453-460`), and `cli.py:9213` sets `include_retired` from `args.all`. So plans iterated for `aw check all` = 46, versus 532 with `--all`. `aw doctor` passes `include_retired=True` unconditionally (`doctor.py:530`) and therefore sees it. Confirmed by running all three: `aw check all` -> 0 id6-collisions, `aw check all --all` -> 1, `aw doctor --agent` -> 1. A collision between a LIVE artifact and a TERMINAL one is still a real collision, because a terminal plan's id6 is permanently cited across the repository.
- Scope: Make a cross-type id6 collision impossible AT CREATION by minting against the unified inventory, and make the two DETECTION gaps this graduation measured impossible to reintroduce: a `- Id:` matched in prose rather than in front matter, and the identity-slot rule's blind spot for a file that both declares and slots a foreign id6. EXCLUDES the lookup-surface presentation half, which is Order 02's whole subject, and excludes setid uniqueness, which is `sjsoqq`.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/check_engine.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/ipd_authoring.py, agent_workflows/artifact_rename.py, tests/test_id6_global_mint.py, tests/test_check_engine_collisions.py
- Item-Dependencies: none
- Status: to-review
- Set: id6integ
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: sk7ggr
- From-Backlog: wx95o4
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `wx95o4`, RESHAPED by measurement rather than transcribed. THREE of the item's four numbered defects survive but two changed shape, and the item's two named INSTANCES are both GONE. (1) The `y6mfgo` walkthrough and the `ntf6sx` duplicate were BOTH cleared in `ba8bcf2e`/`6a29f9c0` (2026-08-31), the same commit that filed this item: the walkthrough was renamed to its own id6 `5gdzyz` and the duplicate pending plan was deleted. Verified: `inventory_all_artifacts` finds ONE collision today and it is neither of them. So the item's "IMMEDIATE, SEPARABLE CLEANUP" paragraph is DEAD and is not carried forward. (2) A DIFFERENT live collision was found while verifying: research prompt `27rjro` declares `- Id: uyeko5` inside a QUOTED EXAMPLE at `:60`, colliding with executed plan `uyeko5`. That is a front-matter parser reading a body line, which the item did not anticipate, and it is now E-04. (3) The item's defect 4 (collision only in the full sweep) is TRUE but its mechanism is worse than stated: `aw check all` misses this collision entirely because the colliding plan is in `executed/` and the retired filter excludes it, while `aw doctor` catches it; measured 0 versus 1. (4) Defect 3 (D140's declared-duplicate blind spot) re-verified TRUE by direct call on `_check_identity_slots`. (5) Defect 2 (`generate_id6(set())`) re-verified TRUE at `ipd_authoring.py:152`, and the reachability question the item asked is now E-05's explicit job. The `sjsoqq` setid half is deliberately NOT folded in, contrary to the item's suggestion: 12 `check.setid-collision` findings exist today and are overwhelmingly the legitimate backlog-item-shares-a-setid-with-its-plan pattern, so treating them as this plan's business would either mass-flag a working convention or require a policy decision this plan has no mandate for.

## Goal

Make it impossible to MINT a colliding id6, and make an existing collision impossible to MISS, so identity stays the one thing in this repository that can always be trusted to name exactly one file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prevent the collision at creation

- [ ] E-01 GIVE `generate_id6` THE UNIFIED INVENTORY AS ITS COLLISION SET, at every call site, so a cross-type collision cannot be created. `status_set.inventory_all_artifacts` already spans every type and already backs the collision CHECKER, so this consumes an existing substrate rather than building one.
  DO NOT CHANGE `generate_id6`'S SIGNATURE TO FETCH ITS OWN SET. It takes `existing: set` and an injectable `_rng`, which is what makes it deterministically testable; a function that reaches out to the filesystem cannot be unit-tested that way. Add a helper that BUILDS the global set and have each caller pass it, keeping the generator pure.
  THE INVENTORY MUST INCLUDE TERMINAL ARTIFACTS, and this is the load-bearing detail. A retired or executed artifact's id6 is permanently cited across the repository (`Item-Dependencies`, `From-Backlog`, review filenames, prose), so reusing it is a real collision even though nothing is "live". The measured `uyeko5` case is exactly this shape: one side is in `executed/`. If your global set is built from a helper that defaults to excluding retired paths, that default is WRONG here and must be overridden explicitly, with a comment saying why.
  CALL SITES, TO BE RE-LOCATED BY SYMBOL: `backlog.py:356`, `specs.py:933`, `releases.py:62`, `ipd_authoring.py:316` and `:328`, `artifact_rename.py:513`. Each currently passes a per-type set built by its own `_existing_*` helper.
  - Depends on: none
  - Expected outcome: every mint site collision-checks against a global, terminal-inclusive id6 set; `generate_id6` stays pure and injectable; no call site retains a per-type-only check.
  - Execution state: pending

- [ ] E-02 DECIDE AND IMPLEMENT WHAT THE EMPTY-SET CALL SHOULD DO, rather than passing it a set and calling the job done. `ipd_authoring.py:152` calls `_core.generate_id6(set())`, so any id6 is "unique" against nothing.
  ANSWER THE ITEM'S REACHABILITY QUESTION FIRST, because it decides which fix is correct. That call sits in the SKELETON GENERATOR, whose docstring says `plan_id` "is the stable `- Id:` handle; when omitted a fresh one is generated" and that "deterministic output for tests can pin `plan_id`". So establish by inspection whether any production path reaches it WITHOUT passing `plan_id` (the scaffold verb at `:316`/`:328` mints properly and passes it in). If the only unpinned caller is a test, the honest fix is to give it the real inventory ANYWAY or to document it as deliberately unchecked WITH THE REASON; if a production path reaches it, it is a live bug and must get the global set.
  DO NOT LEAVE AN EMPTY-SET COLLISION CHECK WITH NO COMMENT under any outcome. It is wrong on its face, and the next reader will re-derive this whole question.
  - Depends on: E-01
  - Expected outcome: a written reachability finding for that call site, and either the global set passed or an explicit comment recording why it is deliberately unchecked; never a bare `set()` with no explanation.
  - Execution state: pending

### Task group 2: close the two detection gaps

- [ ] E-03 CLOSE D140's DECLARED-DUPLICATE BLIND SPOT by adding the third case the rule is missing: a file whose declared `- Id:` is ALSO another file's declared `- Id:`, where the two are DIFFERENT TYPES.
  THE BLIND SPOT IS PROVEN, NOT ASSUMED. Verified by calling `_check_identity_slots` directly with a synthetic record pair in which both files declare and slot the same id6: ZERO findings. Rule (a) compares the slot against the file's OWN declared Id and passes when they agree; rule (b) is skipped entirely for a file that declares an Id. So the shape D140 most cares about, an artifact ASSERTING ownership of another's identity, is invisible to the rule written for D140.
  MIND THE OVERLAP WITH `check.id6-collision`, and do not emit two findings for one fact. The plain declared-Id duplicate is ALREADY reported by `check_collisions`'s `seen_ids` pass. So decide deliberately whether this is a new identity-slot case or simply the EXISTING collision rule being surfaced properly (E-06 covers surfacing), and record the choice. Emitting `check.id6-collision` and `check.id6-identity-slot` for the same pair is worse than one clear finding.
  DO NOT MASS-FLAG CONFORMANT FILES. `_is_real_id6`'s discriminator exists because legacy slugs whose first word matches `[0-9a-z]{6}` (`assess`, `agents`) were being flagged. Any new case must preserve that guard, and V-03 requires the before/after repo-wide finding count to prove it.
  - Depends on: none
  - Expected outcome: the declared-duplicate-across-types shape produces exactly ONE clear finding; no double-reporting with `check.id6-collision`; the repo-wide finding count does not grow for conformant files.
  - Execution state: pending

- [ ] E-04 STOP MATCHING `- Id:` IN PROSE. This is the live defect on main and it is the reason a real collision exists: `_ID_LINE_RE` (`check_engine.py:758`) is a multiline whole-line match with no positional bound, so it matches a `- Id: uyeko5` line at `:60` of a research prompt where that line is a QUOTED EXAMPLE inside a document whose real identity is `27rjro` (declared as YAML `id: 27rjro`).
  BOUND THE SEARCH TO THE FRONT MATTER, and be honest that two dialects exist. Bullet-style types carry `- Id:` in a leading metadata block; RESEARCH uses YAML `---` front matter with `id:` (that dialect difference is already documented as a selectors limitation and has its own item, `05aqbj`). So the fix must either read only the header region or recognize the type's dialect; a fix that reads the whole file with a tighter regex will still hit the next quoted example.
  DO NOT "FIX" THIS BY EDITING THE RESEARCH PROMPT. Its quoted example is legitimate content: it is illustrating a plan's metadata block to an external model, and the prompt cannot do its job without it. Changing the document to satisfy a parser would hide the defect and would recur the moment any artifact quotes another's front matter, which is a normal thing for a prompt, a spec, or a plan-review to do. THIS IS THE PARSER'S BUG.
  A REAL COLLISION MAY REMAIN AFTER THE FIX, and that is a legitimate outcome to report rather than to paper over: if bounding the parser makes the `uyeko5` finding disappear, the collision was never real and V-04 must say so plainly; if some OTHER genuine collision surfaces once the parser is correct, report it as a finding for a human, and do NOT rename anyone's artifact as part of this plan.
  - Depends on: none
  - Expected outcome: a `- Id:`-shaped line in a document BODY is no longer read as that document's identity; the research dialect is handled or explicitly scoped out with its reason; no records file is edited to satisfy the parser; the `uyeko5` verdict after the fix is stated either way.
  - Execution state: pending

### Task group 3: make an existing collision impossible to miss

- [ ] E-05 MAKE `aw check` SEE A COLLISION INVOLVING A TERMINAL ARTIFACT, because today it does not and that is why this collision sat undetected. MEASURED: `aw check all` reports ZERO `check.id6-collision`, `aw check all --all` reports ONE, `aw doctor --agent` reports ONE. The cause is that `_iter_type_files` drops retired paths unless `include_retired=True` (`check_engine.py:493`), `executed/` counts as retired (`is_retired`, `:453-460`), and `cli.py:9213` binds `include_retired` to `args.all`; plans iterated go from 46 to 532 with the flag.
  THE COLLISION SCAN SHOULD NOT INHERIT THE LIVENESS FILTER, and that is the narrow claim to implement. Excluding terminal artifacts is right for most rules (a finished plan's own conformance is not actionable) and WRONG for identity, because a terminal id6 is permanently cited. So make the collision pass see every artifact regardless of the caller's retired setting, rather than telling users to remember `--all`.
  DO NOT WIDEN ANY OTHER RULE. This E-item changes what the COLLISION scan enumerates and nothing else; a broader change would alter finding counts across every type and make V-05's delta unreadable.
  STATE THE COST. Enumerating every artifact including archives is more IO than the default sweep does today; measure the wall-clock difference and report it, so the choice is made on evidence rather than assumed free.
  - Depends on: E-04
  - Expected outcome: `aw check all` (no flags) reports a collision that involves a terminal artifact; no other rule's enumeration changed; the added cost is measured and stated.
  - Execution state: pending

- [ ] E-06 DECIDE WHAT A PER-TYPE `aw check <type>` OWES THE AUTHOR, and implement that decision. MEASURED: `aw check research` reports `errors 0 warnings 0` and exits 0 on a tree containing a real id6 collision, because `collisions` is gated on `norm == "all"` (`cli.py:9237`). An author who checks the type they just wrote is told they are fine.
  THREE LEGITIMATE OUTCOMES, and the item explicitly left this open: run the collision scan for the type being checked (correct but pays the repo-wide inventory cost on every per-type run); put it behind a flag; or have the per-type report SAY that collisions are only checked in the full sweep. The third is the cheapest honest answer and is not a cop-out, because the failure mode here is a SILENT clean bill of health, and one sentence removes it.
  WHATEVER IS CHOSEN, A CLEAN PER-TYPE REPORT MUST NOT IMPLY COLLISION-CLEAN. That is the whole defect. Do not resolve this by leaving the report unchanged.
  - Depends on: E-05
  - Expected outcome: a per-type check either performs the collision scan or explicitly states that it does not; no per-type run reports an unqualified clean when collisions were never examined.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE UNIFIED INVENTORY ALREADY EXISTS AND IS ALREADY CONSUMED BY THE CHECKER (`status_set.inventory_all_artifacts`), so global minting is a wiring change, not a new mechanism.
- `generate_id6(existing, _rng=None)` is PURE and injectable by design (`artifact_core.py:58`); keep it that way and pass the set in.
- `_iter_type_files` DROPS RETIRED PATHS BY DEFAULT (`check_engine.py:493`) and `executed/` is retired (`is_retired`, `:453`). This is correct for most rules and wrong for identity.
- `aw doctor` ALREADY PASSES `include_retired=True` (`doctor.py:484`, `:499`, `:530`), which is why it catches what `aw check all` misses. The two surfaces must not disagree about what a collision is.
- TWO FRONT-MATTER DIALECTS EXIST: bullet `- Key: value` for most types, YAML `---` for research. The selectors module already documents this as a known limitation with its own backlog item (`05aqbj`).
- `_is_real_id6`'s DISCRIMINATOR IS LOAD-BEARING: without it, legacy slugs beginning with a six-character word get mass-flagged. Preserve it.
- D140 IS THE GOVERNING DECISION and its own text already names the enforcement gap ("`check_collisions` today reads only the frontmatter `- Id:` line ... it NEVER inspects the filename identity slot"). The slot rule was added since; the PROSE-MATCH gap was not anticipated there.
- 12 `check.setid-collision` findings exist today and are dominated by the legitimate pattern of a backlog item sharing a setid with the plan it graduated into. Do NOT treat them as defects in this plan.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | a LIVE collision exists and the default sweep misses it | `uyeko5` is declared by executed plan `runflags-01-uyeko5` AND by research prompt `27rjro`. `aw check all` -> 0 `check.id6-collision`; `aw check all --all` -> 1; `aw doctor --agent` -> 1. | all three commands run at HEAD in the graduation worktree |
| F-2 | HIGH | the cause is a PROSE MATCH, not an identity gap | The research prompt's real identity is `27rjro` (YAML `id: 27rjro`, and its filename agrees). The `uyeko5` it "declares" is a QUOTED EXAMPLE at `:60` illustrating a plan's metadata block. `_ID_LINE_RE` is an unbounded multiline match, so it reads a body line as identity. | `check_engine.py:758`; the prompt's `:55-61` |
| F-3 | HIGH | the retired filter is why the sweep is blind | `_iter_type_files` skips retired paths unless `include_retired=True`; `executed/` is retired; `cli.py:9213` binds that to `args.all`. Plans iterated: 46 default versus 532 with `--all`. A terminal id6 is permanently cited, so this exclusion is wrong for identity. | `check_engine.py:493`, `:453-460`; `cli.py:9213`; both counts measured |
| F-4 | HIGH | D140's blind spot is REAL, verified by direct call | `_check_identity_slots` returns ZERO findings for a record pair where both files declare AND slot the same id6: rule (a) compares slot to the file's own Id and passes, rule (b) is skipped for a declaring file. | direct invocation with a synthetic two-record input |
| F-5 | HIGH | minting is per-tree at every site | Each caller passes only its own type's ids: `backlog.py:356`, `specs.py:933`, `releases.py:62`, `ipd_authoring.py:316`/`:328`, `artifact_rename.py:513`. | read at HEAD |
| F-6 | MEDIUM | one call site checks nothing at all | `ipd_authoring.py:152` calls `generate_id6(set())`; any id6 is unique against an empty set. Reachability from production is E-02's explicit question. | `ipd_authoring.py:152` and the surrounding docstring |
| F-7 | MEDIUM | a per-type check reports a false clean | `aw check research` -> `errors 0 warnings 0`, exit 0, on a tree holding a real collision, because `collisions` is gated on `norm == "all"`. | command run at HEAD; `cli.py:9237` |
| F-8 | HIGH | BOTH instances the item named are ALREADY FIXED | The `y6mfgo` walkthrough was renamed to its own id6 `5gdzyz` and the duplicate `ntf6sx` pending plan was deleted, both in `ba8bcf2e`/`6a29f9c0` (2026-08-31) - the same commit that FILED this item. `aw find y6mfgo` and `aw find ntf6sx` each return one plan today. So the item's "IMMEDIATE, SEPARABLE CLEANUP" is dead work. | `git log` on those shas; `aw attention` reports `valid: True` |
| F-9 | MEDIUM | the item's setid suggestion is declined with a reason | The item proposes folding `sjsoqq` (setid uniqueness) in here. 12 `check.setid-collision` findings exist today and are dominated by the LEGITIMATE backlog-item-shares-its-plan's-setid pattern, so folding it in would either mass-flag a working convention or demand a policy decision this plan has no mandate for. | `aw check all --agent` rule tally; the finding locations |
| F-10 | LOW | the two surfaces already disagree | `aw doctor` catches this collision and `aw check all` does not, from the same engine function. Whatever E-05 does must leave them agreeing. | `doctor.py:530` versus `cli.py:9237` |

## Proposed changes (ordered, validatable)

1. Mint against a global, terminal-inclusive id6 set at every call site, keeping `generate_id6` pure (E-01).
2. Resolve the empty-set call site's reachability and either fix or document it (E-02).
3. Add D140's missing declared-duplicate case without double-reporting the existing collision rule (E-03).
4. Bound identity parsing to front matter so a quoted example is never read as identity (E-04).
5. Make the collision scan see terminal artifacts by default, measuring the added cost (E-05).
6. Make a per-type check either scan for collisions or say that it does not (E-06).

## Deferred / out of scope (with reason)

- THE `aw find` / LOOKUP PRESENTATION HALF. Order 02 (`paw8so`) owns it entirely: this plan makes collisions detectable and preventable, that one makes them VISIBLE at the surface an operator uses. Split because they touch different modules and have different test surfaces, and because a fix to the parser (E-04) changes what Order 02 has to display.
- SETID UNIQUENESS (`sjsoqq`). The item suggests folding it in; declined with the reason in F-9. 12 setid-collision findings exist and are dominated by a legitimate convention, so this needs a policy decision first.
- THE RESEARCH YAML DIALECT AS A GENERAL PROBLEM (`05aqbj`). E-04 must handle research well enough not to misread it, but making the bullet-oriented selectors fully fluent in YAML front matter is that item's subject.
- RENAMING OR EDITING ANY EXISTING ARTIFACT. Explicitly forbidden by E-04: the research prompt's quoted example is legitimate content and the parser is the bug. If a genuine collision survives the fix, report it for a human decision.
- THE ITEM'S "IMMEDIATE, SEPARABLE CLEANUP". Dead: both instances were fixed in `ba8bcf2e`/`6a29f9c0` before this graduation (F-8).
- A PRE-COMMIT HOOK. The item asks whether one is warranted. Not here: hooks are local, not cloned by default, and skippable, so the portable authority is the `aw check` rule plus CI, which E-05 and E-06 are. A hook could be added later as best-effort feedback on top of a correct rule, never instead of one.
- THE `ntf6sx`-SHAPED DEFECT (one plan in two lifecycle directories). A lifecycle problem, not an identity one, and no instance exists today.

## Scope check

- Over-scope: none. One generator helper, one check-engine rule set, five mint call sites, two test modules.
- Scope-Paths justification: `artifact_core.py` holds `generate_id6` (E-01, kept pure); `check_engine.py` holds `_ID_LINE_RE`, `check_collisions`, `_check_identity_slots`, `_iter_type_files` and `is_retired`, i.e. E-03, E-04 and E-05 in full; `backlog.py`, `specs.py`, `releases.py`, `ipd_authoring.py` and `artifact_rename.py` are the five mint call sites E-01 and E-02 must change; `tests/test_id6_global_mint.py` is new and covers minting plus the empty-set decision; `tests/test_check_engine_collisions.py` covers the parser bound, the D140 case, the terminal-inclusive enumeration and the per-type behavior. `cli.py` is deliberately NOT in scope: E-06 may be satisfiable inside the check engine's own report, and if the executor finds it genuinely needs a CLI edit, that is a scope-widening finding to record and reconcile at finalize, not a silent addition.
- Under-scope, stated rather than left as `none`: this plan does not touch the lookup surfaces, does not address setid uniqueness, does not make selectors fluent in YAML front matter, does not rename or edit any existing artifact, does not add a pre-commit hook, and does not change any rule's enumeration other than the collision scan's. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed` (the pre-existing `test_orchestrator_retirement` case). Roughly 32 further failures inside a lane are environmental. Criterion: the AFTER failure set minus the BEFORE set is EMPTY, never an absolute count.
- A MINTING TEST proving a fresh id6 cannot equal a DIFFERENT type's existing id6, including a TERMINAL one, driven through the injectable `_rng` so the collision is forced rather than hoped for.
- A PARSER TEST using a document whose BODY contains a `- Id:` line for another artifact, asserting that document's identity is its own. Build it as a fixture; do NOT assert against the live `27rjro` file, whose content may legitimately change.
- A D140 TEST for the declared-duplicate-across-types shape, plus a NEGATIVE test that a conformant file pair produces no finding and that legacy slug names are still not mass-flagged.
- REPO-WIDE FINDING COUNTS BEFORE AND AFTER, per rule, from `aw check all --agent`. Baseline measured 2026-09-08: `check.scope-drift` 78, `check.lifecycle-transition-invalid` 20, `check.setid-collision` 12, `check.name-nonconformant` 8, `check.review-finding-unescalated` 4, `check.ipd-dependency-findings-blocked` 2, `check.from-backlog-dangling` 1, `check.from-backlog-gate-mismatch` 1, `check.system-layout-missing` 1, `check.id6-collision` 0. Compare per RULE, not the total: several of these counts drift for unrelated reasons (scope-drift moves with live receipts, lifecycle-transition-invalid grows as any plan gains a history line).
- THE THREE-COMMAND AGREEMENT CHECK after E-05: `aw check all`, `aw check all --all` and `aw doctor` must report the SAME id6-collision set. Paste all three.
- A COST MEASUREMENT for E-05: wall-clock `aw check all` before and after.
- `aw check research` re-run after E-06, showing it no longer reports an unqualified clean.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`check_collisions`'s DOCSTRING is the authoritative prose statement of the (a)/(b) identity-slot rule and must be extended, not replaced, for whatever E-03 adds; it currently enumerates exactly two cases and a reader trusts that enumeration. It must also gain a sentence stating that identity is checked across TERMINAL artifacts too, with the reason (a terminal id6 is permanently cited), because that is the non-obvious part of E-05 and the next person to add a rule will otherwise inherit the default liveness filter without noticing.

`_ID_LINE_RE`'s new bound needs a comment naming the measured failure it fixes: a research prompt quoting a plan's metadata block was read as declaring that plan's id6. Without that comment the tighter parse looks like a gratuitous restriction and will be loosened again.

DECISIONS.md D140 is the governing decision and its "Enforcement gap identified" paragraph is now partly historical (the slot rule shipped) and partly incomplete (it did not anticipate the prose match). Do NOT rewrite the decision's Context or Decision. If an amendment is warranted, add to its Applied line, and say why in this section.

No spec change is expected. If the executor finds spec text asserting that id6 minting is globally unique TODAY, that is a false claim; declare the spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

## Open questions

### OQ-01: Should the new declared-duplicate case be a distinct rule or the existing collision rule surfaced better?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SURFACED BETTER, NOT A NEW RULE, decided from the measurement. `check_collisions`'s `seen_ids` pass ALREADY detects a plain declared-Id duplicate and already emits `check.id6-collision` for the live case (proven: `aw check all --all` reports exactly that). The reason it was invisible is the retired filter (E-05) and the prose match (E-04), NOT a missing rule. So adding a second rule for the same fact would produce two findings for one problem and give an operator two remedies to choose between, which the item itself warns against for a different pair. E-03 therefore adds the declared-duplicate case only where it is NOT already covered, and must not double-report; where it IS covered, the fix is enumeration and parsing.

### OQ-02: Should a per-type `aw check <type>` run the repo-wide collision scan?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY LEFT OPEN, because it trades a real cost against a real silence and the item left it open too. Running it makes every per-type check pay for a repo-wide inventory, which is the kind of quiet slowdown that gets a check removed from a hook later. NOT running it leaves `aw check research` exiting 0 with `errors 0 warnings 0` on a tree holding a real collision, which is what allowed the live case to persist. E-06 is written so that the CHEAPEST honest option (a report line saying collisions are only checked in the full sweep) is a legitimate resolution, so this question does not block execution: it constrains WHICH of three implementations E-06 chooses. It is non-blocking because every option removes the false clean; the maintainer's preference decides how much it costs.

### OQ-03: What if bounding the parser makes the only known collision disappear?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THEN IT WAS NEVER A COLLISION, AND V-04 MUST SAY SO. This is the expected outcome, not a failure: the research prompt's identity really is `27rjro`, and `uyeko5` appearing in its body is a quotation. The value of E-04 is that the parser stops manufacturing a finding, and the value of E-05 is that a REAL terminal-involving collision would now be seen. Both are worth doing independently of whether this particular pair survives. What is forbidden is quietly editing the prompt to make the finding go away, or reporting a disappeared finding as a fixed collision; the executor must state which of the two happened.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL passing output of the forced-collision minting test, and quote the assertion showing the candidate id6 belonged to a DIFFERENT type. Paste proof that a TERMINAL artifact's id6 is in the collision set (for example the set's size against `inventory_all_artifacts`'s count, which measured 703 at authoring). Paste `generate_id6`'s signature showing it is unchanged and still takes `existing` plus an injectable `_rng`. THEN paste a search over all five call sites showing none still passes a per-type-only set.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: state the reachability finding for `ipd_authoring.py:152` in one or two sentences, with the evidence that decided it (which callers reach it, and whether any omits `plan_id`). Paste the resulting code: either the global set being passed, or the comment recording why it is deliberately unchecked. A bare `set()` with no comment is a FAILED validation regardless of test results.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ACTUAL passing output of the declared-duplicate test AND of the negative tests (a conformant pair produces nothing; legacy slug names are not mass-flagged). Paste the per-rule finding counts before and after from `aw check all --agent`, and state explicitly whether any pair now yields BOTH `check.id6-collision` and `check.id6-identity-slot`; if any does, that is a failure of this item's no-double-reporting requirement.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of the fixture-based parser test, and quote the fixture's body line so it is visible that the `- Id:` sits in PROSE. Paste the new bound in `_ID_LINE_RE` (or its replacement) with its comment. THEN state the `uyeko5` verdict explicitly: whether the finding disappeared (meaning it was a parser artifact) or a genuine collision remains, per OQ-03. Paste `git status --porcelain .aw/records/` proving NO records file was edited to satisfy the parser.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste all THREE commands' id6-collision output after the change (`aw check all`, `aw check all --all`, `aw doctor --agent`) and confirm in one sentence that the three sets are identical. Paste the wall-clock cost of `aw check all` before and after. Paste the per-rule finding counts before and after, and confirm that NO rule other than the collision scan changed its count; a changed count elsewhere means the enumeration widened beyond scope.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw check research`'s output after the change and its unpiped exit code, showing that a clean per-type report no longer implies collision-clean. Quote the report line (or the scan result) that removes the false clean. State which of the three options E-06 implemented and why, and if a CLI edit turned out to be required, say so plainly as a scope-widening finding rather than committing it silently.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is Order 01 of a two-child Set. It owns PREVENTION and DETECTION; Order 02 (`paw8so`) owns PRESENTATION on the lookup surfaces and depends on this one, because E-04 changes what counts as a collision and Order 02 must display the corrected answer rather than the current one.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here, because `check_engine.py` and the mint call sites are under concurrent edit. Do NOT edit or rename any file under `.aw/records/` as part of this work: if a genuine collision survives E-04, report it for a human. Paste ACTUAL command and test output; compare `aw check` findings per RULE and never by total. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the three-command agreement check and the explicit `uyeko5` verdict.
