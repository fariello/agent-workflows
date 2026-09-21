# IPD: Resolve a setid within the requested type and report candidates per type when it cannot

- Date: 2026-09-10
- Kind: child
- Concern: A setid is now a SHARED cross-type TOPIC label (DECISIONS D153, spec `2lcqno` N1), so one token routinely names artifacts of several types. The UNTYPED setter fans out across every type and then fails on the first artifact whose type cannot take the requested status. MEASURED at HEAD: `aw set approved agentadhere --dry-run` refuses with `Validation error ... Status 'approved' is not valid for backlog (valid: ['blocked', 'done', 'graduated', 'open', 'parked'])`, naming a BACKLOG item, when the operator plainly meant the plan Set. Nothing is wrong with the artifacts; the resolver simply has no way to hear "the plans called agentadhere".
  THE AUTHORED PREMISE WAS WRONG AND MEASUREMENT CORRECTED IT, WHICH CHANGES THIS PLAN'S SCOPE. The spec and the parent checklist both describe the defect as a TYPED-path failure, citing the historical error `Type mismatch: selector 'agentadhere' resolved to artifact(s) of type ['backlog', 'research'] ... scoped to 'plans'` (`status_set.py:1265`). For a SETID that path is ALREADY FIXED: `match_selector` accepts `scoped_type` and restricts `record_types` to it (`status_set.py:315-317`), so `match_selector('agentadhere', ..., scoped_type='plans')` returns 7 matches, all of type `plans`, while the unscoped call returns 13 across three types. So this plan must fix the UNTYPED path, not "add type scoping" that already exists for setids.
  BUT THE FOLLOW-ON INFERENCE WAS ALSO WRONG, AND IT WAS THE DANGEROUS ONE (corrected at review, F-7). This plan concluded that the `:1259-1268` refusal is therefore DEAD CODE and told E-02 to remove it. It is NOT dead. The pre-filter narrows which types the RESOLVER is queried for, but `selectors.resolve`'s precedence rule 1 matches an existing FILE regardless of the requested type, and the record's type is then read from the real path. MEASURED: `match_selector(<a plan path>, scoped_type='specs')` returns one match of type `plans`, and on HEAD `aw specs set approved <that plan path> --yes --by-human` is refused by exactly that branch. With the branch deleted the same command SUCCEEDS, writing the PLAN to `approved` and appending a forged `--by-human` history line to it, while the full suite stays green. So the branch is the only guard on a cross-type write and must be PINNED, not retired. E-02 is inverted accordingly.
  WHY THE UNTYPED PATH CANNOT SIMPLY GUESS: `aw set` is deliberately record-type-agnostic and serves plans, specs, prompts and backlog at once. Silently picking the type whose status vocabulary happens to accept the requested value would be a guess dressed as resolution, and would act on artifacts the operator never named. Spec `2lcqno` N4 requires the opposite: report the CANDIDATES BY TYPE and how to disambiguate, never guess.
- Scope: The untyped setter's behavior when one selector resolves across several record types, and the now-dead typed-mismatch refusal. IN: making the untyped `aw set` report candidates grouped BY TYPE with the exact typed command that would act on each, instead of failing on whichever foreign artifact it reached first; deciding and implementing what the untyped verb does when the requested status IS valid for several matched types; removing or repurposing the dead type-mismatch branch; a regression fixture built from the measured `agentadhere` case. OUT: the collision-check re-scope (Order 01, the sibling child); the status vocabularies themselves, which are correct per type; any change to what a bare setid MEANS for a single type (a whole Set, per IPD `laykok` E-07, which stays); artifact renaming, which the ruling forbids.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: setidfix
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: w2y5ac
- From-Spec: 2lcqno

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: w2y5ac verified (set setidfix, attempt 1).
- 2026-09-21 executed (opencode/its_direct/pt3-claude-opus-5-1m-us via aw oc run): all 5 E-items performed, all 5 V-items `pass` with pasted evidence including three MUTATION CHECKS. Suite `7748 passed, 3 skipped, 2 xfailed` bare. THE PLAN'S CENTRAL INSTRUCTION WAS FOLLOWED AND ITS INVERSION CONFIRMED CORRECT: the `Type mismatch` refusal was NOT removed, and deleting it in a scratch experiment reproduced the measured harm independently, a `specs`-scoped verb rewriting a PLAN `to-review -> approved` and appending `- 2026-09-21 approved (aw set, --by-human): cross-type write` to that plan's own history, i.e. a machine-forged human-approval attestation. E-03/E-04 landed as ONE refusal path keyed on the number of matched TYPES, so the vocabulary-error case and the multi-type-valid case share it; no new CLI flag (`grep -c add_argument` on the diff is 0), no `--force` override, and confirmation deliberately left to plan `4bc1nd`. THREE MEASURED CORRECTIONS TO THE PLAN'S OWN PREDICTIONS, recorded because each would otherwise read as a shortfall. (1) The setid resolves across TWO types (`backlog`, `plans`), not the predicted three: research uses YAML front matter while `read_artifact_record` reads the bullet dialect, so research never resolves by setid and reaches a token only by filename substring. That gap is owned by approved plan `xo3244`; the fixture keeps its research member and asserts the honest two-type resolution with a comment telling a future reader what to change when `xo3244` lands. (2) MY FIRST VERSION OF E-01's TEST WAS VACUOUS and the V-01 mutation check caught it: passing a pre-narrowed inventory made the assertion hold even with `match_selector`'s narrowing removed; fixed to pass the full inventory so `scoped_type` is the only filter. (3) The suite total is 7748, not the plan's `5959`, because that baseline is eleven days and many merged lanes old; the failing NODE-ID set is empty before and after, which is the comparison the plan mandates. OQ-01 RESOLVED WITHOUT TOUCHING THE SPEC: the amendment it asked for was already made during the spec's own review on 2026-09-13 by the owner it named, verified three ways against the spec file, and `2lcqno` is now `approved`. Five uncarried obligations were closed with typed `- Carrier:`/`- Carrier-Evidence:`/`- Carrier-Declined:` fields, so `aw ipd lint --phase pre-transition` reports 0 findings. One environmental suite failure (`test_turn_bounds.py::...IS_isolation_scoped`) was proven pre-existing by reproducing it with my changes stashed; it asserts `OPENCODE_CONFIG_CONTENT` is absent and this agent turn exports it.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 (BLOCKER) through PR-009, all 9 FIXED, none deferred; readiness GO - PENDING HUMAN APPROVAL. Also written into `- Readiness:`. E-02 WAS INVERTED (PR-001): this plan concluded the `Type mismatch` refusal is dead code because `match_selector` pre-filters by `scoped_type`, and told the executor to remove it. The pre-filter narrows which types the RESOLVER is asked about, but `selectors.resolve`'s direct-PATH kind matches an existing file regardless, so the branch is live. MEASURED end to end: on HEAD `aw specs set approved <a plan path> --yes --by-human` is refused by that branch at exit 2; with it deleted the SAME command SUCCEEDS, writing the PLAN `reviewed -> approved` and appending a forged `- 2026-09-11 approved (aw set, --by-human): ...` line to the plan's own history; and the full suite stays green (`5959 passed`) with the branch gone, so nothing pins it and the deletion would have landed silently. E-02 now PINS the guard and E-05 asserts it instead of asserting its absence. E-04 IS THE WIDER HOLE, NOT THE RESIDUAL (PR-004): 15 statuses are valid for 2+ types, and `aw set to-review shared --yes` was measured writing both a plan and a spec at exit 0. E-03 needs NO new flag (PR-005): `aw set <type> <status> <selector>` already exists and resolves the 7 plans cleanly. E-01's pin was narrowed to the setid kind, since claiming it proves general type safety is the exact over-generalization that produced the bad instruction. F-3 withdrawn as measured-false; F-7/F-8/F-9 added.
- 2026-09-10 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from spec `2lcqno` N3/N4 as checklist item T-09, after the maintainer chose "write plans for both, ready for review" over coding directly. THE CENTRAL FINDING IS THAT THE AUTHORED DIAGNOSIS WAS WRONG, and it was caught by executing rather than reading: the typed path the spec blames is already correct (`match_selector` pre-filters by `scoped_type`, verified live at 7 plans versus 13 unscoped), so the `Type mismatch` refusal the spec quotes is unreachable on a scoped call. The live defect is on the UNTYPED path and produces a DIFFERENT error naming a backlog item's status vocabulary. Both facts are pasted in F-1 and F-2. A plan written from the spec's prose alone would have "fixed" working code and left the real failure in place. ALSO RECORDED, because it cost a near-miss during authoring: `aw ipd set` WRITES BY DEFAULT with no confirmation, so an attempt to REPRODUCE the historical error instead reverted 7 executed plans to `approved`/`pending` in one command; reverted with no commit, and filed as backlog `f5pttg` (high). That is why every reproduction step in this plan specifies `--dry-run`.
- 2026-09-10 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one shared topic name usable as a selector: when an operator names a type, act within that type (already true, and pin it); when they do not, tell them exactly which types the name matched and what to run, instead of refusing on an artifact they did not mean.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin what already works, retire what is dead

- [x] E-01 PIN THE TYPED PATH WITH A TEST, BECAUSE NOTHING CURRENTLY PROVES IT AND THIS PLAN'S WHOLE PREMISE DEPENDS ON IT. Add a case asserting that a SETID shared across types, resolved with `scoped_type='plans'`, returns ONLY plan artifacts. Use the measured shape: a setid carried by plans AND a backlog item AND research reports (verified at HEAD: 7 matches scoped to plans versus 13 unscoped across `['backlog','plans','research']`). Without it, a future change to `match_selector`'s `record_types` narrowing (`status_set.py:315-317`) would silently reintroduce the original failure with no test failing.
  STATE THE PIN'S LIMIT PRECISELY, because the authored version over-claimed it and that over-claim is what produced E-02's dangerous instruction. This test pins the SETID kind only. It does NOT prove scoped resolution is type-safe in general: the DIRECT-PATH kind deliberately bypasses the type narrowing (E-02, measured), so "scoped resolution filters by type" is true for id6/setid/status/stem/substring and FALSE for a path. Write the test name and its docstring to say so, and add the companion path-kind assertion in E-02 rather than letting a reader infer from this one that every kind is filtered.
  - Depends on: none
  - Expected outcome: a test fails if scoped SETID resolution ever stops filtering by type, and its docstring states that the direct-path kind is deliberately exempt and is pinned separately by E-02.
  - Execution state: performed
    Added `SharedSetidCrossTypeResolutionTests::test_scoped_setid_resolution_returns_only_the_scoped_type` (`tests/test_status_set.py`), plus the `create_research` fixture helper the measured corpus shape needs. The docstring states the pin covers the SETID kind ONLY and that the direct-path kind is deliberately exempt and pinned by E-02's test, naming the over-generalization that produced the bad instruction.
    ONE VACUITY TRAP FOUND AND FIXED DURING THE MUTATION CHECK, worth recording because the first version of this test passed under the mutation: passing `inventory_all_artifacts(scoped_type="plans")` as the candidate list pre-filters the records, so the assertion held even with `match_selector`'s own narrowing removed. The test now passes the FULL unnarrowed inventory so `scoped_type` is the only thing filtering, and an in-code comment says why.
    ALSO CORRECTED AGAINST MEASUREMENT: the plan predicted the setid resolves across `['backlog','plans','research']` (13 files). It resolves across `['backlog','plans']` (8 records) at HEAD, because research carries YAML front matter (`set:`) while `read_artifact_record` reads the bullet dialect (`- Set:`), so a research doc's `set_id` is None and only the last-resort FILENAME substring rule reaches it. The fixture KEEPS its research member so the corpus shape is the measured one, and asserts the honest two-type resolution with a comment pointing at approved plan `xo3244` (Set `selfmdialect`), which owns that dialect gap.

- [x] E-02 DO NOT REMOVE THE TYPE-MISMATCH BRANCH. PIN IT, AND CORRECT THIS PLAN'S CLAIM THAT IT IS DEAD. THIS ITEM WAS INVERTED AT REVIEW and the reason is a security-shaped one, so read it before touching `status_set.py:1259-1268`. The authored item asserted the branch is unreachable because `match_selector` pre-filters by `scoped_type`. THAT IS FALSE FOR ONE SELECTOR KIND. The pre-filter narrows which `record_types` the RESOLVER is asked about, but the DIRECT-PATH kind (`selectors.resolve` precedence rule 1) matches an existing file regardless of the type it was asked for, and the returned record's `record_type` comes from `detect_artifact_type` on the real path. MEASURED: `selectors.resolve(root, "specs", <a plan path>)` returns `kind=path` with that plan, and `match_selector(<plan path>, scoped_type="specs")` returns 1 match of type `plans`. So the branch fires, and it is the ONLY thing standing between a scoped verb and a foreign-type artifact.
  WHAT DELETING IT DOES, MEASURED END TO END IN A SCRATCH REPO. On HEAD, `aw specs set approved <a plan path> --yes --by-human` REFUSES with exactly this branch's message (exit 2, file unchanged). With the branch deleted, the SAME command SUCCEEDS: it rewrote the plan `reviewed -> approved` and appended `- 2026-09-11 approved (aw set, --by-human): ...` to the plan's history. That is a cross-type write that also FORGES A HUMAN APPROVAL ATTESTATION on a plan, through a verb the operator invoked for specs. And the whole suite (`5959 passed`) is green with the branch removed, so NOTHING pins it and this deletion would land silently. The vocabulary check does not save you: 15 statuses are valid for two or more types (`approved`, `reviewed`, `to-review`, `superseded`, `done`, ... measured from `TYPE_STATUSES`), so the overlap is the common case rather than a corner.
  SO THE WORK IS: add a test pinning the refusal (a scoped verb given a foreign-type PATH must refuse, exit 2, write nothing), and REPLACE the branch's comment with one stating WHY it is reachable, naming the direct-path kind, so the next reader does not repeat this plan's inference. Leave the user-facing message intact. If you still believe some part is genuinely unreachable, prove it with a test that fails when the branch is removed; absent such a test, do not remove anything.
  - Depends on: E-01
  - Expected outcome: the refusal survives and is PINNED by a test that fails if it is deleted; its comment explains the direct-path reachability; the measured `aw specs set approved <plan path>` case still refuses with exit 2 and no write.
  - Execution state: performed
    THE BRANCH WAS NOT REMOVED. Its user-facing message is byte-identical; only a 14-line comment was added ABOVE it, stating that it is live and load-bearing, naming the direct-PATH selector kind as the reason, and naming the measured harm (a cross-type write that also forges a `--by-human` attestation) plus the test that pins it. The companion note was added to `match_selector`'s docstring: `scoped_type` narrows every selector kind EXCEPT the direct path, so a caller that must not act across types needs its own post-resolution check, and this refusal is that check.
    PINNED BY `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`, which drives the real CLI (`specs set approved <a plan path> --yes --by-human`) and asserts exit 2, the `Type mismatch` string, byte-identical file content, and the absence of `--by-human` from the plan.
    THIS PLAN'S ORIGINAL F-3 IS CONFIRMED WITHDRAWN AS MEASURED-FALSE, and the review's inversion is confirmed correct: with the branch deleted, the same command exits 0 and writes. Evidence in V-02.

### Task group 2: fix the untyped path

- [x] E-03 MAKE THE UNTYPED SETTER REPORT CANDIDATES BY TYPE INSTEAD OF FAILING ON THE FIRST FOREIGN ARTIFACT. Today `aw set approved <shared-setid>` reaches the per-record `validate_transition_allowed` loop (`status_set.py:1287-1310`) and dies on whichever artifact's vocabulary rejects the status, naming that artifact (measured verbatim: `Validation error on 20260823-agentadhere-01-3gr7fk-....backlog.md: Status 'approved' is not valid for backlog`, exit 1, when the operator meant the plan Set). Per spec `2lcqno` N4 the tool MUST report the candidates grouped BY TYPE and how to disambiguate, and MUST NOT guess. Emit, for each matched type, the count and the exact typed command that would act on it, so the operator's next keystroke is in the message. DO NOT change the per-type status vocabularies: `approved` genuinely is invalid for a backlog item and that validation is correct.
  THE DISAMBIGUATING COMMAND ALREADY EXISTS AND MUST BE THE ONE YOU PRINT, not a new flag. `run_set_command` already accepts a LEADING TYPE TOKEN on the untyped verb (`status_set.py:1185-1194`: when `scoped_type is None` and the first token names a type and there are 3+ args, it adopts that type). MEASURED: `aw set plans approved agentadhere --dry-run` resolves exactly the 7 plans and previews them cleanly. So the message should recommend `aw set <type> <status> <selector>` (and may also mention the typed verb, e.g. `aw ipd set`), and E-03 needs no new CLI surface at all. Say this in the code so nobody adds a `--type` flag that duplicates a shipped spelling.
  - Depends on: E-01
  - Expected outcome: the measured `agentadhere` case prints one line per matched type with counts and a runnable `aw set <type> ...` command, exits nonzero, and writes nothing; no new flag was added.
  - Execution state: performed
    Added a cross-type candidate report in `run_set_command`, placed AFTER the kind-aware ambiguity block and the type-mismatch guard and BEFORE the per-record `validate_transition_allowed` loop, so it preempts the foreign-vocabulary error rather than competing with it. It fires only when `scoped_type_canonical is None` (the untyped `aw set` surface) AND the matched records span more than one type. For each matched type it prints the count and a runnable `aw set <type> <status> <selector>`, then refuses at exit 2 having written nothing.
    NO NEW FLAG WAS ADDED: `git diff agent_workflows/status_set.py | grep -c add_argument` is 0, and the printed remedy is the SHIPPED leading-type-token spelling. An in-code comment says so explicitly ("DO NOT ADD A `--type` FLAG") so a later reader does not duplicate it.
    THE PER-TYPE VOCABULARIES WERE NOT TOUCHED: `approved` is still invalid for a backlog item, which is correct.
    MEASURED ON THE REAL TREE, the exact `agentadhere` case the plan cites: before, `FAIL Validation error on 20260823-agentadhere-01-3gr7fk-...backlog.md: Status 'approved' is not valid for backlog (valid: [...])` at exit 1; after, a two-line per-type report naming 1 backlog and 7 plans with both runnable commands, at exit 2, and `git status --porcelain` shows only my two source files. Full output in V-03.

- [x] E-04 DECIDE AND IMPLEMENT THE MULTI-TYPE-VALID CASE, which E-03 does not cover and which is the genuinely ambiguous one, AND WHICH IS THE COMMON CASE RATHER THAN A CORNER. When the requested status is valid for SEVERAL matched types there is no vocabulary error to stop on, so the untyped setter acts on ALL of them. Under N4 that is a guess. MEASURED AT REVIEW, which changes this item's priority: 15 statuses are valid for two or more types (`approved`, `reviewed`, `to-review`, `draft`, `superseded`, `done`, `parked`, `executed`, `pending`, `open`, `blocked`, `active`, `reusable`, `auto-approved`, `not-executed`), and the silent multi-type write was reproduced end to end: `aw set to-review shared --yes` on a tree holding one plan and one spec sharing setid `shared` transitioned BOTH at exit 0, printing `plan ... draft -> to-review` and `spec ... draft -> to-review`. So E-03 (the vocabulary-error path) is the NARROWER case and this one is the wider hole.
  Choose ONE: refuse with the same per-type candidate report and require a type scope; or act on all types but require an explicit confirmation flag; or act on all silently (the status quo, which N4 forbids). RECORD THE CHOICE AND ITS REASON in the code. RECOMMENDATION, offered because the evidence points one way: REFUSE and require the type scope, reusing E-03's exact report, because the remedy is a shipped spelling (`aw set <type> <status> <selector>`) rather than a new flag, and because a refusal is the only option that satisfies N4's "never guess" for BOTH cases with ONE code path.
  NOTE THE `f5pttg` INTERACTION HONESTLY, AND NOTE THAT IT HAS MOVED: the authored item says `aw ipd set` writes without confirmation so adding a confirmation here would be inconsistent. That defect is now carried by plan `4bc1nd` (Set `setterguard`, reviewed 2026-09-10), whose E-01 extends the shipped confirmation refusal to every flagless caller. If you pick the confirmation-flag option, you are choosing an outcome that overlaps that plan; prefer the refusal option, which does not. Either way state which sibling plan owns confirmation so the two do not implement it twice.
  - Depends on: E-03
  - Expected outcome: a shared setid whose status is valid for two types produces a deliberate, documented outcome rather than an unannounced multi-type write; the measured `aw set to-review shared` case no longer writes both types silently; the code names which plan owns the confirmation question.
  - Execution state: performed
    CHOICE: REFUSE AND REQUIRE A TYPE SCOPE, the plan's own recommendation, implemented as ONE code path shared with E-03. The refusal keys on the number of matched TYPES, not on whether a vocabulary error happens to occur, so the multi-type-valid case and the vocabulary-error case take the same branch and print the same report. That is the only option satisfying N4's "never guess" for both cases at once.
    THE DECISION AND ITS REASON ARE RECORDED IN THE CODE, including two rejected alternatives. (1) A CONFIRMATION FLAG was rejected because plan `4bc1nd` (Set `setterguard`, carrying backlog `f5pttg`) OWNS confirmation-before-write for every setter; implementing it here would be a second implementation of that fix. The code names `4bc1nd` so the two cannot collide. (2) `--force` was deliberately NOT made an override, on the id6-collision precedent: `--force` means "act on all files this ONE type matched", while cross-type fan-out asks a different question (which tree did you mean?) whose answer is a type scope, not a louder yes.
    MEASURED BEFORE AND AFTER on a scratch tree with one plan and one spec sharing setid `shared`: before, `aw set to-review shared --yes` printed `plan ... draft -> to-review` and `spec ... draft -> to-review` and exited 0, with both files rewritten; after, it prints the two-type candidate report, exits 2, and both files still read `- Status: draft`. Full output in V-04.
    WITHIN-TYPE FAN-OUT IS UNTOUCHED and separately pinned (`test_within_type_setid_fanout_still_acts_on_the_whole_set`), because conflating it with the cross-type case would break every bulk Set transition (IPD `laykok` E-07).

### Task group 3: pin the measured failure

- [x] E-05 ADD THE REGRESSION FIXTURE FROM THE MEASURED CASE, not a synthetic one, because the synthetic version is what let the wrong diagnosis survive review. Build a tree with one setid carried by plans, a backlog item and research docs, then assert: the untyped setter reports per-type candidates and writes NOTHING; the typed setter (and the `aw set <type> ...` spelling) acts on the plans only. Run every reproduction with `--dry-run` where the verb supports it: during authoring, a bare `aw ipd set approved agentadhere` WROTE, reverting 7 executed plans, filed as `f5pttg` and now carried by plan `4bc1nd`.
  DROP THE THIRD ASSERTION THE AUTHORED ITEM DEMANDED, AND ASSERT ITS OPPOSITE. It said to assert the `Type mismatch` string "appears NOWHERE, because its reappearance would mean the branch came back". E-02 is inverted: that branch is LIVE, load-bearing, and must stay, so an assertion that its message never appears would either be vacuous or would pressure a later executor into deleting a guard that prevents a cross-type write with a forged `--by-human` attestation. Replace it with the E-02 pin: a scoped verb given a foreign-type PATH must refuse with exit 2 and write nothing, and that assertion must FAIL if the branch is removed. Add the E-04 case too: a status valid for two matched types produces the chosen deliberate outcome rather than a silent two-type write (measured today: `aw set to-review shared --yes` writes both).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: four assertions pinning untyped per-type reporting, typed/`aw set <type>` narrowing, the foreign-type-path refusal (failing if E-02's branch is deleted), and the multi-type-valid outcome.
  - Execution state: performed
    Added test class `SharedSetidCrossTypeResolutionTests` (`tests/test_status_set.py`) with SIX tests covering the four required assertions plus two boundary pins: scoped setid narrowing (E-01), the foreign-type-PATH refusal (E-02), untyped per-type reporting with nothing written (E-03), the printed command actually resolving within one type, the multi-type-valid refusal (E-04), and within-type fan-out surviving.
    THE CORPUS SHAPE IS THE MEASURED ONE, not a simplified two-type tree: the fixture carries one setid on two plans AND a backlog item AND a research doc, mirroring `agentadhere`. A `create_research` helper was added because research uses YAML front matter, so modelling it on `create_plan` would have produced a file the real code never sees.
    THE THIRD AUTHORED ASSERTION WAS DROPPED AND ITS OPPOSITE ASSERTED, as the review directed: there is NO assertion that `Type mismatch` is absent. Instead `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing` asserts the message IS present, exit 2, and the file byte-unchanged, and that test FAILS when the branch is deleted (mutation check pasted in V-02).
    EVERY EXPLORATORY SETTER RUN ON THE REAL TREE USED `--dry-run`, per `f5pttg`; every writing reproduction ran against a gitignored scratch tree under `.aw/state/scratch/`, never the repository's own records. `git status --porcelain` after all of it shows only the two files this plan declares.

## Project conventions discovered (Step 0)

- `match_selector` NARROWS BY TYPE FOR EVERY SELECTOR KIND EXCEPT THE DIRECT PATH (`status_set.py:296-320`): given `scoped_type` it sets `record_types = (canonical,)`, but `selectors.resolve`'s precedence rule 1 matches an existing FILE regardless of the type it was asked for, and the record's `record_type` is then read from the real path by `detect_artifact_type`. So scoped resolution is type-safe for id6/setid/status/stem/substring and NOT for a path. MEASURED both directions. This is the single most load-bearing fact in this plan, and getting it half right is what made E-02 dangerous.
- THE TYPE-MISMATCH REFUSAL AT `:1259-1268` IS THE ONLY GUARD ON THAT HOLE, it is unpinned by any test, and deleting it lets `aw specs set approved <plan path> --by-human` write a plan and forge a human attestation (F-7). Treat it as load-bearing, not as leftover.
- THE UNTYPED VERB ALREADY ACCEPTS A LEADING TYPE TOKEN (`status_set.py:1185-1194`), so `aw set <type> <status> <selector>` is a shipped disambiguating spelling. No new flag is needed for E-03/E-04.
- 15 STATUSES ARE VALID FOR TWO OR MORE TYPES (measured from `TYPE_STATUSES`), so an untyped multi-type write is the ordinary case and the vocabulary error that produced the reported symptom is the narrower one.
- A BARE SETID LEGITIMATELY MEANS THE WHOLE SET for a mutating setter, made deliberate by IPD `laykok` E-07, which distinguishes a setid fan-out (act on all, no `--force`) from a unique-id collision (always refuse) and a filename substring multi-match (refuse unless `--force`). This plan must NOT weaken that; the problem is cross-TYPE fan-out, not within-type fan-out.
- STATUS VOCABULARIES ARE PER TYPE and are correct: `approved` is valid for a plan and invalid for a backlog item (`['blocked', 'done', 'graduated', 'open', 'parked']`). The fix belongs in resolution and reporting, never in the vocabularies.
- `aw set` IS DELIBERATELY UNTYPED (`cli.py:10929` passes `scoped_type=None`) while `aw ipd set`, `aw spec set`, `aw backlog set` and the prompts setter pass a concrete type. So the untyped verb is the ONE surface that must handle multi-type resolution.
- MUTATING SETTERS HERE WRITE BY DEFAULT. `aw ipd set` has `--dry-run` as opt-in and did not prompt before a seven-file transition. Use `--dry-run` for every exploratory run; see backlog `f5pttg`.
- SUITE BARE: `python3 -m pytest`. Compare failing NODE IDS, never totals. Known environmental failure in the primary checkout only: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (a gitignored local `opencode-recovery/` dump); it passes in a clean worktree.

## Findings

| Id | Severity | Location (measured at HEAD) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `status_set.py:296-320` | THE TYPED PATH IS ALREADY CORRECT, so the spec's stated defect is stale. `match_selector` restricts `record_types` to the scoped type. | `match_selector('agentadhere', ..., scoped_type='plans')` -> 7 matches, types `['plans']`; unscoped -> 13 matches, types `['backlog', 'plans', 'research']` |
| F-2 | HIGH | the untyped `aw set` path | THE LIVE DEFECT IS ON THE UNTYPED PATH AND HAS A DIFFERENT ERROR than the one the spec quotes. | `aw set approved agentadhere --dry-run` -> `FAIL Validation error on ...3gr7fk...backlog.md: Status 'approved' is not valid for backlog (valid: ['blocked', 'done', 'graduated', 'open', 'parked'])` |
| F-3 | ~~MEDIUM~~ WITHDRAWN | `status_set.py:1259-1268` | AUTHORED CLAIM, MEASURED FALSE, SUPERSEDED BY F-7. The `Type mismatch` refusal is NOT unreachable: the DIRECT-PATH selector kind bypasses the type pre-filter, so a scoped verb given a foreign-type path reaches this branch. It is live, load-bearing, and must NOT be removed. | see F-7 |
| F-4 | MEDIUM | `status_set.py:1287-1310` | The untyped setter validates per artifact and dies on the FIRST foreign one, so the operator sees an unrelated type's vocabulary rather than a disambiguation prompt. | the F-2 output names a backlog item's valid-status list |
| F-5 | MEDIUM | this plan's own authoring | `aw ipd set` WRITES BY DEFAULT with no confirmation: `aw ipd set approved agentadhere` moved 7 plans from `executed/` to `pending/` and rewrote their status. Reverted, uncommitted. Filed as `f5pttg`, NOW CARRIED BY PLAN `4bc1nd` (Set `setterguard`, reviewed 2026-09-10), which is where the confirmation fix lives; E-04 must not duplicate it. | the seven `executed → approved` lines and the resulting `git status`; restored byte-identical to HEAD |
| F-6 | LOW | IPD `laykok` E-07 | Within-type setid fan-out is DELIBERATE and must survive; only cross-type fan-out is the defect. Conflating them would break bulk Set transitions. | the kind-aware ambiguity block at `status_set.py:1229-1258` |
| F-7 | BLOCKER | `status_set.py:1259-1268`; `selectors.py:509` (path precedence rule 1) | E-02 AS AUTHORED WOULD REMOVE A LIVE SAFETY GUARD AND PERMIT A CROSS-TYPE WRITE WITH A FORGED HUMAN ATTESTATION. The type pre-filter narrows which types the RESOLVER is queried for; the direct-path kind matches an existing file regardless, and the record's type is then read from the real path. MEASURED: `match_selector(<plan path>, scoped_type='specs')` returns 1 match of type `plans`; on HEAD `aw specs set approved <plan path> --yes --by-human` REFUSES via this branch (exit 2, unchanged); with the branch deleted the SAME command SUCCEEDS, rewriting the plan `reviewed -> approved` and appending `- 2026-09-11 approved (aw set, --by-human): ...` to the PLAN's history. And the full suite passes with the branch removed (`5959 passed`), so nothing pins it and the deletion lands silently. | the two scratch runs (refused at exit 2, then written at exit 0 with the forged attestation line); `grep "Type mismatch" tests/` -> no matches |
| F-8 | HIGH | `status_set.py` `TYPE_STATUSES`; measured scratch run | E-04's "multi-type-valid" case is the COMMON case, not a corner: 15 statuses are valid for 2+ types. Reproduced: `aw set to-review shared --yes` on a tree with one plan and one spec sharing setid `shared` wrote BOTH at exit 0. So E-04 covers a wider hole than E-03 and should not be treated as the residual. | the vocabulary census; the two `draft -> to-review` lines across two types |
| F-9 | LOW | `status_set.py:1185-1194` | THE DISAMBIGUATING SPELLING ALREADY EXISTS: the untyped verb accepts a leading type token, so `aw set plans approved agentadhere` resolves exactly the 7 plans. E-03 must print THAT rather than invent a `--type` flag. | `aw set plans approved agentadhere --dry-run` previewing 7 plans at exit 0 |

## Proposed changes (ordered, validatable)

1. E-01 pins the typed SETID path, stating explicitly that the direct-path kind is exempt.
2. E-02 PINS the type-mismatch refusal (it is live, not dead) and corrects the comment that misled this plan.
3. E-03 replaces the untyped path's first-foreign-artifact failure with a per-type candidate report that names the shipped `aw set <type> ...` spelling.
4. E-04 settles the multi-type-valid case, which measurement showed is the wider hole, with a recorded decision.
5. E-05 pins all of it with a fixture built from the measured corpus shape, including the foreign-type-path refusal.

## Deferred / out of scope (with reason)

EVERY ROW BELOW NOW CARRIES A TYPED CARRIER FIELD, added at execution because the prose alone left five obligations with no durable carrier (`check.ipd-uncarried-obligation`, advisory at `info` here). Two rows hand off to a live artifact; two decline explicitly, because they record a DECISION that something is correct as-is rather than an outstanding obligation, and inventing a backlog item for "this code is right" would be noise a reader has to dismiss forever.

- THE COLLISION-CHECK RE-SCOPE: Order 01 of this Set (`216rgg`). Independent of resolution, separately reviewable.
  - Carrier-Evidence: .aw/records/plans/executed/20260910-setidfix-01-216rgg-re-scope-check-setid-collision-to-its-within-type-half-and-s.ipd.md
- MAKING MUTATING SETTERS SAFE BY DEFAULT (dry-run default, confirmation on bulk, refusing backwards terminal transitions): backlog `f5pttg`. It is a real and arguably higher-severity defect, but it spans several verbs and its own decision about default behavior; E-04 must only state whether it depends on that outcome. VERIFIED AT EXECUTION: `f5pttg` is `open` and plan `4bc1nd` (Set `setterguard`) is `pending`, so both halves of this deferral are live. E-04 does NOT depend on that outcome; it chose the refusal option precisely so it does not overlap `4bc1nd`.
  - Carrier: f5pttg, 4bc1nd
- THE PER-TYPE STATUS VOCABULARIES: correct as they are. The defect is resolution, not validation.
  - Carrier-Declined: this row records a DECISION that the vocabularies are correct (`approved` genuinely is invalid for a backlog item), not an outstanding obligation. There is nothing for a carrier to track, and filing one would assert a defect that measurement says does not exist.
- WITHIN-TYPE SETID FAN-OUT: deliberate (`laykok` E-07) and preserved.
  - Carrier-Declined: this row records a deliberate SHIPPED behavior this plan preserves and separately pins (`test_within_type_setid_fanout_still_acts_on_the_whole_set`), not future work. A carrier would imply it needs changing, which is the opposite of the finding.

## Scope check

- Over-scope: none. Both declared paths are touched by named items: `status_set.py` (E-02's comment, E-03, E-04) and `tests/test_status_set.py` (E-01, E-02's pin, E-05).
- Under-scope: none remaining. The measurement sweep added E-01 (nothing pinned the typed path) and E-04 (the multi-type-valid case, which the spec's N4 requires but the checklist never named). AT REVIEW: E-02 was INVERTED from "remove the dead branch" to "pin the live guard" after measuring that its deletion permits a cross-type write with a forged `--by-human` attestation (F-7); E-01's claim was narrowed to the setid kind only; E-03 was pointed at the shipped leading-type-token spelling instead of a new flag (F-9); E-04 was re-weighted as the wider hole (F-8); and E-05's third assertion was replaced with its opposite.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there and pasted, compared by failing NODE ID rather than by total. THE BASELINE AND THE E-02 EXPERIMENT ARE ALREADY MEASURED at `3e6c6bf4` and must be reproduced rather than re-derived: unpatched, `5959 passed, 3 skipped, 2 xfailed`; with the type-mismatch branch DELETED, also `5959 passed` and zero failures, which is the finding that proves the guard is unpinned and that E-02's authored instruction would have landed invisibly. Note the plan's claimed environmental `tests/test_reporting_contract.py` failure did NOT reproduce in a clean worktree.

Beyond the suite: the measured `agentadhere` case run BEFORE and AFTER on both the untyped and typed paths, with output pasted, always with `--dry-run`; the foreign-type-path case (`aw specs set approved <a plan path>`) run before and after, showing exit 2 and no write; the multi-type-valid case (`aw set to-review <a setid shared by a plan and a spec>`) run before and after, showing the two-type write is gone; plus `git status --porcelain` after each exploratory run proving nothing was written, given F-5.

### Measured at execution (2026-09-21, this lane worktree)

THE SUITE, RUN BARE, WITH THE CHANGE IN PLACE. `7748 passed, 3 skipped, 2 xfailed`:

```
$ python3 -m pytest
7748 passed, 3 skipped, 2 xfailed, 3 warnings in 101.21s (0:01:41)
```

THE TOTAL MOVED FROM THE PLAN'S `5959` AND THAT IS EXPECTED, NOT A DISCREPANCY: the plan's baseline was measured at `3e6c6bf4` on 2026-09-10 and this lane is at `7a7b46a7`, eleven days and many merged lanes later. The plan's own instruction is to compare FAILING NODE IDS, not totals, and the failing set is EMPTY both before and after. The `+6` over the bare run is the six tests this plan adds.

ONE ENVIRONMENTAL FAILURE, DIAGNOSED RATHER THAN EXPLAINED AWAY. A first bare run reported `1 failed, 7747 passed`:

```
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
E       AssertionError: a non-isolated turn must get NO denial policy ...
E       assert 'OPENCODE_CONFIG_CONTENT' not in {'AGENT': '1', ...}
```

PROVEN UNRELATED TO THIS CHANGE, TWO WAYS. (1) It reproduces with my changes STASHED, i.e. on a clean tree: `git stash push -- agent_workflows/status_set.py tests/test_status_set.py` then the same node id -> `1 failed, 42 deselected`. (2) It passes with the ambient variable unset: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest ... -k test_the_permission_policy_by_contrast_IS_isolation_scoped` -> `1 passed`. CAUSE: this agent turn runs with `OPENCODE_CONFIG_CONTENT` exported into its environment, and the test asserts that variable is ABSENT from a non-isolated turn's env; the harness inherits it. It touches no code this plan modifies. The green run above was taken with that one variable unset, which is the only environmental adjustment made. NOTE the plan's predicted `tests/test_reporting_contract.py` environmental failure did NOT reproduce here either, matching the review's finding.

`aw check` IS NO WORSE THAN BASELINE (spec criterion 8), measured on the SAME tree before and after by stashing:

```
before findings: 655   after findings: 661
new in after: []      (no new rule/location pair)
gone: []
extra occurrences in after: 6
  2 check.scope-drift  .aw/records/plans/pending/20260910-planprio-03-lc4unl-...ipd.md
  2 check.scope-drift  .aw/records/plans/pending/20260919-lifeglyph-07-qdd5jq-...ipd.md
  2 check.scope-drift  .aw/records/plans/pending/20260908-integearn-03-daexj1-...ipd.md
```

THE `+6` IS NOT A REGRESSION AND ITS CAUSE IS NAMED: zero NEW rules fire and zero findings land on anything this plan wrote. All six are `check.scope-drift` on THREE OTHER PENDING PLANS which also declare `agent_workflows/status_set.py` and `tests/test_status_set.py` in their own `- Scope-Paths:`; the rule reports them because those files are currently DIRTY in my working tree. The count returns to 655 once this lane's work is committed and merged, and it is a property of an uncommitted working tree rather than of the change. The absolute number is not zero either way, because this tree carries known unrelated findings, which is exactly why criterion 8 is phrased as "no worse than baseline" rather than "green".


## Spec / documentation sync

NO SPEC IS AMENDED and none is declared in `- Scope-Paths:`. This plan IMPLEMENTS spec `2lcqno` N3 and N4 rather than changing them. CONFIRMED AT EXECUTION: `git status --porcelain` lists no `.spec.md` path, so this plan changed zero specs, declared and actual agree, and the runner's end-of-run spec-edit reconciliation has nothing to report.

WHICH ACCEPTANCE CRITERIA THIS PLAN SATISFIES, since spec `2lcqno` Section 5 spans both children of this Set. Criterion 5 (`aw ipd set approved <a shared setid>` acts on the plan Set only, evidenced by a REGRESSION TEST that fails when the type narrowing is reverted) is satisfied by E-01 plus V-01's mutation check. Criterion 6 (the direct-PATH cross-type write remains REFUSED, with a test, since nothing pinned it) is satisfied by E-02 plus V-02. Criterion 7 (an untyped setter facing a cross-type setid reports candidates GROUPED BY TYPE with a runnable command, exits nonzero, and WRITES NOTHING, evidenced by the `agentadhere` output plus a clean `git status`) is satisfied by E-03 and E-04 plus V-03 and V-04. Criterion 8 (full suite passes and `aw check all` is NO WORSE than baseline, both counts pasted) is satisfied in Required tests below. Criteria 1 through 4 belong to Order 01 (`216rgg`, executed), not to this plan.

BUT ONE SPEC STATEMENT IS NOW KNOWN TO BE IMPRECISE AND THE REVIEWER SHOULD DECIDE WHAT TO DO WITH IT: `2lcqno` Section 1 finding 3 and its N3 both describe the defect as the TYPED setter giving up, citing the historical `Type mismatch` error. F-1 shows the typed path already resolves correctly, so that framing is stale even though N3's REQUIREMENT (resolve within the requested type) is satisfied by the code and worth keeping as a pinned invariant. Options: leave it (the requirement is right, only the example is dated), or amend Section 1 to name the untyped path as the live surface. Deliberately NOT amended here, because editing the governing spec from inside its own implementing plan is the kind of change a reviewer should sanction; raised as OQ-01.

## Open questions

### OQ-01: Should spec `2lcqno`'s stale example be amended, and by whom?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Carrier-Declined: RESOLVED BY EVENTS BEFORE EXECUTION, so there is no outstanding obligation to carry. The amendment this question asked for was MADE, by the party it named (the spec's own reviewer, not this plan), and verified at execution against the spec file itself. Nothing is left for a carrier to track.
- Resolution or deferral rationale: NOT blocking, because this plan's deliverables do not depend on the answer: N3's requirement stands either way and E-01 pins it. The question is bookkeeping about the SPEC's accuracy. It matters because the spec's stale example is exactly what produced this plan's original wrong diagnosis, so leaving it invites the next reader to repeat the error. NOT resolved unilaterally: the spec is `to-review`, and a plan editing its own governing spec's problem statement is a change a reviewer should sanction rather than inherit. RECOMMENDATION: amend Section 1 finding 3 to state that the typed path was fixed and the untyped path is the live surface, and add a one-line note under N3 that it is now a PINNED invariant rather than a fix to build. Cheapest done during the spec's own review, before either child executes.
  RESOLVED AT EXECUTION (2026-09-21) WITHOUT THIS PLAN TOUCHING THE SPEC, which is the outcome this question asked for. The amendment happened during the SPEC'S OWN REVIEW on 2026-09-13, exactly as recommended and by exactly the party named as owner, so the plan never had to edit its governing spec. VERIFIED against the spec file at execution, three ways: (1) Section 1 finding 3 now opens `THIS QUOTED FAILURE NO LONGER REPRODUCES ON THE TYPED PATH, AND THE CORRECTION MATTERS BECAUSE IT MOVES THE DELIVERABLE`, names commit `91077905` (2026-08-27) as the fix that predates the spec, and says the UNTYPED path is the live surface; (2) N3 now carries `ALREADY SATISFIED FOR A SETID ... so the work N3 authorizes is a REGRESSION PIN, not a build`; and (3) N3 also carries the exact sentence the review asked for, `scoped resolution is type-safe for every selector kind EXCEPT a direct PATH ... The `Type mismatch` refusal is the ONLY guard on that case ... must be PINNED, never retired as dead code`. The spec is now `- Status: approved`, so the "prefer letting the spec clear review first" preference in the post-gate note was satisfied too. NO SPEC EDIT WAS MADE BY THIS PLAN and none is declared in `- Scope-Paths:`.
  STRENGTHENED AT REVIEW, AND THE AMENDMENT NOW HAS A SECOND, SHARPER REASON. The stale example did not merely mislead this plan's problem statement; it produced an instruction (the original E-02) to DELETE a live safety guard, which measurement showed permits `aw specs set approved <a plan path> --by-human` to write a plan and forge a human attestation (F-7). So the cost of leaving the example stale is no longer "a reader repeats a harmless misreading": it is that the same inference chain, followed by someone with less time, removes a guard nothing pins. If the spec is amended, say IN IT that scoped resolution filters every selector kind EXCEPT the direct path, and that the `Type mismatch` refusal is the intended guard for that kind. That single sentence is what would have prevented this plan's worst instruction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new SETID test passing, AND a MUTATION CHECK proving it bites: break `match_selector`'s type narrowing (make `record_types` ignore `scoped_type`), show the test FAILS, restore, show it passes. Without the mutation this test could pass vacuously. Paste the test's docstring showing it states the direct-path kind is deliberately exempt, so the pin cannot be misread as proving general type safety (which is the misreading that produced E-02's original instruction).
  - Observed evidence: the new SETID pin passes, its docstring states the direct-path exemption, and the mutation check FAILS it (it also exposed and fixed a vacuity bug in my first version). Detail below.

    THE TEST PASSING:

    ```
    $ python3 -m pytest tests/test_status_set.py -o addopts="" -q -k 'test_scoped_setid_resolution_returns_only_the_scoped_type' -v
    rootdir: /.../w2y5ac_attempt2
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 62 items / 61 deselected / 1 selected

    tests/test_status_set.py .                                               [100%]

    ======================= 1 passed, 61 deselected in 0.21s =======================
    ```

    THE DOCSTRING, which states the limit the review required (`tests/test_status_set.py`):

    ```
    """E-01: scoped SETID resolution narrows to the requested type.

    SCOPE OF THIS PIN, STATED PRECISELY BECAUSE OVER-READING IT CAUSED REAL HARM: this asserts
    the SETID selector kind only. It does NOT prove scoped resolution is type-safe in general.
    The DIRECT-PATH kind is deliberately EXEMPT from the type narrowing (`selectors.resolve`'s
    first precedence rule matches an existing file regardless of the type requested, and the
    record's type is then read off the real path), and that exemption is pinned separately by
    `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`. Reading this test as
    "scoped resolution filters by type" is the over-generalization that produced an instruction
    to delete the `Type mismatch` refusal as dead code; it is not dead.
    ...
    """
    ```

    THE MUTATION CHECK, and it found a REAL VACUITY BUG IN MY FIRST VERSION OF THE TEST, which is exactly what this V-item exists to catch. First attempt: I mutated both narrowing sites (`if scoped_type:` -> `if False:` so `record_types` ignores `scoped_type`, and the fast path's `cands` filter -> `list(all_records)`) and the test STILL PASSED:

    ```
    $ python3 ... (mutation applied)
    mutation applied
    $ python3 -m pytest tests/test_status_set.py -o addopts="" -q -k 'test_scoped_setid_resolution_returns_only_the_scoped_type'
    .                                                                        [100%]
    1 passed, 61 deselected in 0.18s
    ```

    CAUSE: the test passed `inventory_all_artifacts(root, scoped_type="plans")` as the candidate list, which pre-filters the records, so the assertion held with `match_selector`'s own narrowing gone. FIX: pass the FULL unnarrowed inventory (`scoped_type=None`) so `scoped_type` is the only filter, with an in-code comment recording this trap. RE-RUN WITH THE SAME MUTATION, which now FAILS:

    ```
    MUTATION APPLIED: scoped_type no longer narrows record_types
    --- E-01 pin under the mutation (MUST FAIL) ---
    E       First differing element 0:
    E       'backlog'
    E       'plans'
    E
    E       - ['backlog', 'plans']
    E       + ['plans'] : scoped SETID resolution stopped filtering by type, which is the exact defect spec `2lcqno` N3 requires to stay fixed: [('plans', 'sh0002'), ('plans', 'sh0001'), ('backlog', 'sh0003')]

    tests/test_status_set.py:1811: AssertionError
    =========================== short test summary item ============================
    FAILED tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_scoped_setid_resolution_returns_only_the_scoped_type
    1 failed, 61 deselected in 0.22s
    ```

    RESTORED AND PASSING, with the file digest proving the mutation left no residue (it matches the pre-mutation copy byte for byte; the working file was edited ONCE more AFTER all mutation experiments, to replace a brittle `:341-355` line-number citation in E-02's comment with a symbol reference, so its current digest is `b3ff44fa3bd12d084677e123a908b7532f738479054d42c38dc4397126cf4562` and `diff` against the snapshot shows exactly that one comment hunk and nothing else):

    ```
    $ cp .aw/state/scratch/w2y5ac/status_set.py.bak agent_workflows/status_set.py && sha256sum agent_workflows/status_set.py && python3 -m pytest ... -k 'test_scoped_setid_resolution_returns_only_the_scoped_type'
    08d5018d44fc88bdc08d2e353bf20bcd5f8dc20863603d4170ed8872dcb826e2  agent_workflows/status_set.py
    .                                                                        [100%]
    1 passed, 61 deselected in 0.19s
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the branch STILL PRESENT and its new comment explaining direct-path reachability. Paste the new pin passing: `aw specs set approved <a plan path> --yes --by-human` (or the equivalent in-process call) REFUSING with exit 2 and the file unchanged. Then paste the MUTATION CHECK that is the whole point of this item: delete the branch, show the pin FAILS (and, if you can, show the cross-type write succeeding with the forged `--by-human` history line, which is the measured harm), restore, show it passes. State plainly that you did NOT remove the branch and that this plan's original F-3 was withdrawn as measured-false.
  - Observed evidence: the branch was NOT removed and is now pinned; the pin passes, and deleting the branch both FAILS the pin and reproduces the cross-type write with a forged `--by-human` attestation. Detail below.

    STATED PLAINLY FIRST: I DID NOT REMOVE THE BRANCH. Its user-facing message is unchanged; I added a comment above it and a paragraph to `match_selector`'s docstring. This plan's original F-3 ("the refusal is unreachable dead code") is CONFIRMED WITHDRAWN AS MEASURED-FALSE, and the review's inversion (PR-001 / D-1) is confirmed correct by the mutation below.

    THE BRANCH IS STILL PRESENT:

    ```
    $ grep -n 'Type mismatch: selector' agent_workflows/status_set.py
    1552:                    f"Type mismatch: selector '{tok}' resolved to artifact(s) of type {mismatch_types}, "
    ```

    ITS NEW COMMENT, explaining the direct-path reachability (`agent_workflows/status_set.py`, immediately above the branch):

    ```
    # setidfix `w2y5ac` E-02: THIS REFUSAL IS LIVE AND LOAD-BEARING. DO NOT DELETE IT AS DEAD
    # CODE. `match_selector` does narrow `record_types` to `scoped_type` (its `if scoped_type:`
    # branch setting `record_types = (canonical,)`), so it is
    # tempting to conclude a scoped call can never surface a foreign type and that this branch is
    # unreachable. That conclusion is FALSE FOR ONE SELECTOR KIND: the pre-filter only narrows
    # which types the RESOLVER is QUERIED for, while `selectors.resolve`'s FIRST precedence rule
    # (direct PATH) matches an existing FILE regardless of the type it was asked about, after
    # which `detect_artifact_type` reads the record's real type off the real path. MEASURED:
    # `match_selector(<a plan path>, scoped_type="specs")` returns one match of type `plans`.
    # So a type-scoped verb handed a foreign-type PATH reaches here, and this is the ONLY guard
    # between it and a cross-type write. ...
    ```

    THE RESOLVER PROBE CONFIRMING REACHABILITY, run against a scratch tree:

    ```
    match_selector(plan path, scoped specs): [('plans', 'aaa001')]
    selectors.resolve kind: path ['20260921-shartop-01-aaa001-scratch-plan-one.ipd.md']
    ```

    THE LIVE CLI REFUSING ON HEAD-PLUS-THIS-CHANGE (exit 2, digest identical before and after):

    ```
    $ sha256sum $P
    6e4268bf7b584c69a8ea6f9854b9f2f6f6a300da710792a41da282b7df1e1a76  ...20260921-shartop-02-aaa002-scratch-plan-two.ipd.md
    $ python3 -m agent_workflows specs set approved "$P" --yes --by-human --message 'cross-type probe' --dir "$D"
    FAIL     Type mismatch: selector '...20260921-shartop-02-aaa002-scratch-plan-two.ipd.md' resolved to artifact(s) of type ['plans'], but command is scoped to 'specs'. Refusing before making changes.
    EXIT=2
    $ sha256sum $P
    6e4268bf7b584c69a8ea6f9854b9f2f6f6a300da710792a41da282b7df1e1a76  ...20260921-shartop-02-aaa002-scratch-plan-two.ipd.md
    ```

    THE NEW PIN PASSING:

    ```
    $ python3 -m pytest tests/test_status_set.py -o addopts="" -q -k 'test_scoped_verb_refuses_a_foreign_type_path'
    .                                                                        [100%]
    1 passed, 61 deselected in 0.23s
    ```

    THE MUTATION CHECK. Branch deleted, pin FAILS, and the failure message contains the write that should not have happened:

    ```
    MUTATION APPLIED: type-mismatch branch deleted
    --- E-02 pin under the mutation (MUST FAIL) ---
    E       AssertionError: 0 != 2 : a type-scoped verb handed a FOREIGN-TYPE path must refuse at exit 2. If this now exits 0, the `Type mismatch` guard in `run_set_command` was removed and a cross-type write is possible: '-    plan        20260921-fpath-01-fp0001  reviewed \u2192 \u25d5  approved\n...'
    tests/test_status_set.py:1864: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing
    1 failed, 61 deselected in 0.34s
    ```

    AND THE MEASURED HARM ITSELF, REPRODUCED END TO END with the branch deleted: a `specs`-scoped verb wrote a PLAN and appended a FORGED `--by-human` human-approval attestation to that plan's own history. This is the exact harm the review measured, reproduced independently:

    ```
    === MEASURED HARM with the branch DELETED: specs verb writes a PLAN ===
    5:- Status: to-review
    $ python3 -m agent_workflows specs set approved "$P" --yes --by-human --message 'cross-type write' --dir "$D"
    -    plan        20260921-shartop-01-aaa001  to-review → ◕  approved
    EXIT=0
    --- the plan afterwards ---
    5:- Status: approved
    12:- 2026-09-21 approved (aw set, --by-human): cross-type write
    ```

    RESTORED, BRANCH BACK, PIN PASSING:

    ```
    $ cp .aw/state/scratch/w2y5ac/status_set.py.bak agent_workflows/status_set.py && sha256sum agent_workflows/status_set.py && grep -n 'Type mismatch' ... && python3 -m pytest ... -k 'test_scoped_verb_refuses_a_foreign_type_path'
    08d5018d44fc88bdc08d2e353bf20bcd5f8dc20863603d4170ed8872dcb826e2  agent_workflows/status_set.py
    321:    their own post-resolution type check; ``run_set_command``'s ``Type mismatch`` refusal is that
    1551:                    f"Type mismatch: selector '{tok}' resolved to artifact(s) of type {mismatch_types}, "
    .                                                                        [100%]
    1 passed, 61 deselected in 0.23s
    ```

    ALL WRITING REPRODUCTIONS RAN AGAINST A GITIGNORED SCRATCH TREE under `.aw/state/scratch/w2y5ac/measure/`, never the repository's own records, so no tracked artifact was touched by any of this.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the BEFORE output (the measured `Validation error ... not valid for backlog` line, exit 1) and the AFTER output for the same untyped command, showing one line per matched type with counts and a runnable `aw set <type> <status> <selector>` command. Paste `git status --porcelain` proving nothing was written. Confirm the exit code is nonzero. Confirm NO new CLI flag was added, since the leading-type-token spelling already exists.
  - Observed evidence: the measured `agentadhere` case now prints per-type candidates with runnable commands at exit 2 and writes nothing; no new flag was added. Detail below.

    BEFORE, on the REAL repository tree, the exact case this plan measured (the installed `aw` is an editable install pointing at the MAIN checkout, so the before/after distinction is real: `aw` runs unmodified code and `python3 -m agent_workflows` runs this worktree's code):

    ```
    $ aw set approved agentadhere --dry-run
    FAIL     Validation error on 20260823-agentadhere-01-3gr7fk-address-agent-process-adherence-findings.backlog.md: Status 'approved' is not valid for backlog (valid: ['blocked', 'done', 'graduated', 'open', 'parked']). Refusing before making changes.
    EXIT=1
    ```

    AFTER, same selector, this worktree's code. One line per matched type, with counts and a runnable command, exit 2:

    ```
    $ python3 -m agent_workflows set approved agentadhere --dry-run
    FAIL     Selector 'agentadhere' names artifacts of 2 types (backlog, plans), so 'aw set' cannot tell which you meant. A setid is a shared cross-type topic label, not an identity; name the type you meant. Candidates by type:
      backlog  1 artifact(s): aw set backlog approved agentadhere
      plans    7 artifact(s): aw set plans approved agentadhere
    Refusing before making changes; nothing was written.
    EXIT=2
    ```

    EXIT CODE IS NONZERO (2), and the foreign type's status vocabulary is gone from the message.

    THE PRINTED COMMAND ACTUALLY WORKS, which is what makes the report actionable rather than decorative:

    ```
    $ python3 -m agent_workflows set plans approved agentadhere --dry-run
    -    plan        20260825-agentadhere-02-uisjns  executed → ◕  approved  (dry-run)
    -    plan        20260825-agentadhere-05-diundn  executed → ◕  approved  (dry-run)
    - >  plan        20260825-agentadhere-00-3b4f8u  [blocking]  executed → ◕  approved  (dry-run)
    -    plan        20260825-agentadhere-01-gfokao  executed → ◕  approved  (dry-run)
    -    plan        20260825-agentadhere-03-8dto0g  executed → ◕  approved  (dry-run)
    -    plan        20260825-agentadhere-06-r2ks4k  executed → ◕  approved  (dry-run)
    -    plan        20260825-agentadhere-04-wqj1ne  executed → ◕  approved  (dry-run)
    EXIT=0
    ```

    NOTHING WAS WRITTEN. `git status --porcelain` after every exploratory run lists only the files this plan declares plus this plan itself (the plan file appears because I am recording this evidence into it):

    ```
    $ git status --porcelain
     M .aw/records/plans/pending/20260910-setidfix-02-w2y5ac-...ipd.md
     M agent_workflows/status_set.py
     M tests/test_status_set.py
    ```

    NO NEW CLI FLAG:

    ```
    $ git diff agent_workflows/status_set.py | grep -c add_argument
    0
    ```

    ONE MEASURED CORRECTION TO THE PLAN'S EXPECTATION, recorded because the plan predicted three types: the report names TWO (`backlog`, `plans`), not three. The five `agentadhere` research files are in the corpus but do not RESOLVE by setid, because research carries YAML front matter while `read_artifact_record` reads the bullet dialect; they match only by the last-resort filename substring rule, which the setid fast path preempts. That gap is owned by approved plan `xo3244` (Set `selfmdialect`) and is out of this plan's scope; when it lands, this report will name research too, with no change needed here.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the BEFORE behavior on a fixture where the status is valid for two matched types (measured today: `aw set to-review shared --yes` writing BOTH a plan and a spec at exit 0) and the AFTER behavior showing the chosen deliberate outcome. Paste the code comment recording the decision and its reason. State which sibling plan owns the confirmation question (`4bc1nd`, which carries `f5pttg`) and confirm you did not implement confirmation here as well.
  - Observed evidence: the silent two-type write is gone (refuse-and-require-a-type), the decision and both rejected alternatives are recorded in code, and plan `4bc1nd` is named as confirmation owner. Detail below.

    THE VOCABULARY CENSUS, re-derived rather than quoted: 15 statuses are valid for two or more types, so this case is ordinary and not a corner.

    ```
    $ python3 -c "... census over TYPE_STATUSES ..."
    15
    active ['other', 'research']
    approved ['other', 'plans', 'prompts', 'specs']
    auto-approved ['other', 'plans', 'prompts']
    blocked ['backlog', 'releases']
    done ['backlog', 'other', 'plans', 'prompts', 'research']
    draft ['other', 'plans', 'prompts', 'specs']
    executed ['other', 'plans', 'prompts']
    not-executed ['other', 'plans', 'prompts']
    open ['backlog', 'other', 'research']
    parked ['backlog', 'other', 'research', 'specs']
    pending ['other', 'plans', 'prompts']
    reusable ['plans', 'prompts']
    reviewed ['other', 'plans', 'prompts', 'specs']
    superseded ['other', 'plans', 'prompts', 'specs']
    to-review ['other', 'plans', 'prompts', 'specs']
    ```

    BEFORE, on a scratch tree holding one plan and one spec sharing setid `shared`, both `draft`. The silent two-type write reproduces exactly as the review measured it:

    ```
    $ aw set to-review shared --yes --dir "$D"
    -    plan        20260921-shared-01-ddd001  draft → ◔  to-review
    -    spec        20260921-shared-01-eee001  draft → ◔  to-review
    EXIT=0
    --- resulting statuses ---
    ...ddd001-scratch-plan-shared.ipd.md:- Status: to-review
    ...eee001-scratch-spec-shared.spec.md:- Status: to-review
    ```

    AFTER, same tree reset to `draft`, same command, this worktree's code. Refuses with the per-type report and writes NOTHING:

    ```
    $ python3 -m agent_workflows set to-review shared --yes --dir "$D"
    FAIL     Selector 'shared' names artifacts of 2 types (plans, specs), so 'aw set' cannot tell which you meant. A setid is a shared cross-type topic label, not an identity; name the type you meant. Candidates by type:
      plans  1 artifact(s): aw set plans to-review shared
      specs  1 artifact(s): aw set specs to-review shared
    Refusing before making changes; nothing was written.
    EXIT=2
    ...ddd001-scratch-plan-shared.ipd.md:- Status: draft
    ...eee001-scratch-spec-shared.spec.md:- Status: draft
    ```

    THE CODE COMMENT RECORDING THE DECISION AND ITS REASON (`agent_workflows/status_set.py`), including both rejected alternatives:

    ```
    # SO WE REFUSE AND ASK FOR THE TYPE, with ONE code path covering both cases, and print the
    # candidates grouped by type with a RUNNABLE disambiguating command for each.
    # THE DISAMBIGUATING SPELLING ALREADY SHIPS: `run_set_command` accepts a LEADING TYPE TOKEN
    # on the untyped verb ... DO NOT ADD A `--type` FLAG; it would be a second spelling for a
    # shipped one.
    # NOT OVERRIDABLE BY `--force`, on the id6-collision precedent above: `--force` means "yes,
    # act on all the files this ONE type matched", and cross-type fan-out is a different
    # question (which tree did you mean?) whose answer is a type scope. A confirmation flag was
    # the considered alternative and was REJECTED here because plan `4bc1nd` (Set `setterguard`,
    # carrying backlog `f5pttg`) OWNS the confirmation-before-write question for every setter;
    # implementing confirmation here too would be a second implementation of that fix.
    # WITHIN-TYPE setid fan-out is untouched and stays deliberate (IPD `laykok` E-07): this
    # refusal fires only when the matched records span MORE THAN ONE type.
    ```

    CONFIRMATION IS OWNED BY PLAN `4bc1nd` (Set `setterguard`, which carries backlog `f5pttg`), and I DID NOT implement confirmation here. The chosen outcome is a refusal, which is the option the plan recommended precisely because it does not overlap `4bc1nd`. No confirmation prompt, no new flag, no change to `--yes` handling.

    THE MUTATION CHECK, proving the new refusal is pinned rather than merely present. With the refusal disabled (`if len(matched_types) > 1:` -> `if False:`), BOTH the E-03 and E-04 pins fail, and the E-04 failure message contains the silent two-type write itself:

    ```
    MUTATION APPLIED: cross-type candidate refusal disabled
    E       AssertionError: 0 != 2 : a status valid for BOTH matched types silently wrote both, which is the wider hole E-04 exists to close: '-    plan        20260921-bothok-01-bo0001  draft → ◔  to-review\n-    spec        20260921-bothok-01-bo0002  draft → ◔  to-review\n...'
    =========================== short test summary info ============================
    FAILED tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_untyped_setter_reports_candidates_by_type_instead_of_a_foreign_vocabulary
    FAILED tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_a_status_valid_for_two_matched_types_refuses_instead_of_writing_both
    2 failed, 60 deselected in 0.40s
    ```

    RESTORED AND PASSING (all six of the new tests):

    ```
    $ cp .aw/state/scratch/w2y5ac/status_set.py.bak agent_workflows/status_set.py && python3 -m pytest tests/test_status_set.py -o addopts="" -q -k 'SharedSetidCrossType'
    ......                                                                   [100%]
    6 passed, 56 deselected in 0.54s
    ```

    WITHIN-TYPE FAN-OUT STILL WORKS, verified live so the refusal cannot be accused of breaking bulk Set transitions:

    ```
    $ python3 -m agent_workflows set plans to-review shartop --yes --dir "$D"
    -    plan        20260921-shartop-01-aaa001  reviewed → ◔  to-review
    -    plan        20260921-shartop-02-aaa002  reviewed → ◔  to-review
    EXIT=0
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste all FOUR assertions passing (untyped reports per-type and writes nothing; typed/`aw set <type>` acts on plans only; a foreign-type PATH under a scoped verb refuses with exit 2; a multi-type-valid status produces the chosen outcome). Paste the fixture's corpus shape showing it spans plans, backlog and research, so it matches the measured case rather than a simplified one. Do NOT assert that the `Type mismatch` message is absent; that assertion was removed at review because the message is live behavior this plan now preserves.
  - Observed evidence: all six tests pass, mapped one by one onto the four required assertions; the fixture spans plans + backlog + research and asserts the `Type mismatch` message IS present, not absent. Detail below.

    ALL SIX TESTS PASSING BY NAME (the four required assertions plus two boundary pins):

    ```
    $ python3 -m pytest tests/test_status_set.py -o addopts="" -k 'SharedSetidCrossType' -v
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_within_type_setid_fanout_still_acts_on_the_whole_set PASSED [ 16%]
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_scoped_setid_resolution_returns_only_the_scoped_type PASSED [ 33%]
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_the_printed_disambiguating_command_resolves_within_one_type PASSED [ 50%]
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_untyped_setter_reports_candidates_by_type_instead_of_a_foreign_vocabulary PASSED [ 66%]
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing PASSED [ 83%]
    tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_a_status_valid_for_two_matched_types_refuses_instead_of_writing_both PASSED [100%]
    ======================= 6 passed, 56 deselected in 0.90s =======================
    ```

    MAPPING TO THE FOUR REQUIRED ASSERTIONS, so the count is not taken on trust:
    1. untyped reports per-type and writes NOTHING -> `test_untyped_setter_reports_candidates_by_type_instead_of_a_foreign_vocabulary` (asserts exit 2, the absence of `is not valid for backlog`, a runnable `aw set <type> approved shartop` per resolved type, per-type counts, and byte-identical content for all four fixture files);
    2. the `aw set <type> ...` spelling acts on the plans ONLY -> `test_the_printed_disambiguating_command_resolves_within_one_type` (both plans `approved`, the backlog item still `open`, the research doc still `active`);
    3. a foreign-type PATH under a scoped verb refuses with exit 2 and writes nothing -> `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`, which FAILS when E-02's branch is deleted (mutation pasted in V-02);
    4. a multi-type-valid status produces the chosen deliberate outcome -> `test_a_status_valid_for_two_matched_types_refuses_instead_of_writing_both`, which FAILS when the new refusal is disabled (mutation pasted in V-04).

    THE FIXTURE'S CORPUS SHAPE spans plans + backlog + research, mirroring the measured `agentadhere` topic rather than a simplified two-type tree: `_build_shared_topic` creates two plans (`sh0001`, `sh0002`), one backlog item (`sh0003`) and one research doc (`sh0004`), all carrying setid `shartop`. A `create_research` helper was added for the research member because research uses YAML front matter (`id:`/`status:`/`set:`), not the bullet dialect.

    THE RESEARCH MEMBER IS IN THE CORPUS BUT NOT IN THE RESOLUTION, and the test says so honestly instead of quietly dropping it. Measured: `match_selector('shartop')` returns `['backlog', 'plans']`, while a separate assertion (`_research_in_corpus`) proves the research file IS present in the inventory. The test's failure message tells a future reader that research appearing in the resolution means plan `xo3244` has landed and is CORRECT, and what to change. Measured against the real tree too: `match_selector('agentadhere')` returns 8 records across `['backlog', 'plans']` while `selectors.resolve(root, 'research', 'agentadhere')` returns 5 paths at `kind='substring'`.

    NO ASSERTION THAT `Type mismatch` IS ABSENT. The opposite is asserted: `self.assertIn("Type mismatch", buf.getvalue())`. The authored third assertion was dropped exactly as the review directed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 3 groups, unchanged in COUNT by the review but E-02 was INVERTED in intent (from removing a branch to pinning it) after its deletion was measured to permit a cross-type write with a forged human attestation. Two of the five (E-01, E-02) exist only because measurement contradicted the authored premise, and one (E-04) because the spec's N4 implies a case the checklist never named.
- Cohesion rationale: E-01 and E-02 are one concern seen from two sides, pinning what scoped resolution DOES filter (the setid kind) and pinning the guard that covers what it does NOT (the path kind); they must land together, because each one alone invites the false generalization that produced this plan's original E-02. E-03 and E-04 are the untyped path's two distinct outcomes (one type valid, several types valid) and are split because they have different failure modes and different tests, though after review E-04 is known to be the wider of the two. E-05 is the shared regression surface.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. USE `--dry-run` FOR EVERY EXPLORATORY SETTER RUN: `aw ipd set` writes by default and reverted 7 executed plans during this plan's authoring (backlog `f5pttg`). This is a SHARED CHECKOUT: never revert or commit a file you did not change.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved w2y5ac --by-human --message ...`) before execution. Its governing spec `2lcqno` is `to-review`, and OQ-01 asks whether that spec's stale example should be amended during its review; prefer letting the spec clear review first. On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
