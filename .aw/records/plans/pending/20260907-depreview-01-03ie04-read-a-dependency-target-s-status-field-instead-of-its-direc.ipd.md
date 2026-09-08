# IPD: Read a dependency target's status field instead of its directory so the review relaxation is reachable

- Date: 2026-09-07
- Kind: child
- Concern: `edge_satisfied` is correctly ACTION-AWARE for an `executed:` dependency and deliberately relaxes the requirement for a REVIEW turn (`oc_runipd.py:3323`, `:3346`): `is_exec = item.get("action") != "review"`, then `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")`. That is the right semantics, because a review writes no code and cannot be invalidated by an unexecuted prerequisite. But the relaxation is UNREACHABLE, because the value compared against `allowed` is a DIRECTORY NAME rather than the plan's `- Status:` field: `bucket = plan_bucket(dep_path)` (`:3345`), and `plan_bucket` (`runner_shared.py:1149-1163`) merely scans path components for one of a fixed list. In this repository readiness lives in the `- Status:` FIELD and a plan STAYS in `pending/` until a TERMINAL state moves it, so there are no `reviewed/` or `approved/` directories at all (verified: `.aw/records/plans/` holds only `executed`, `not-executed`, `pending`, `reusable`, `superseded`). Every non-terminal plan therefore buckets as `pending`, which is absent from `allowed`, and the review path refuses exactly as the execute path would.
  ALL LINE NUMBERS IN THIS PLAN WERE RE-MEASURED AT HEAD `df26ff6e` (whose runner sources are unchanged since `faa4c7ec`). They had ALL drifted by 5 to 7 lines from the earlier revision, because the spec amendment and two unrelated runner commits landed in between. Re-locate by SYMBOL anyway (see the gate); the numbers are a convenience, not the contract.
  SO TWO OF THE THREE ALLOWED VALUES ARE DEAD CODE for every plan in this tree. The relaxation is real in intent and inert in practice.
  MEASURED 2026-09-07. `aw oc run --session <sid> ybkmzp`, where `ybkmzp` declares `- Item-Dependencies: executed:tm2cz8` and `tm2cz8` carries `- Status: reviewed` in `.aw/records/plans/pending/`, refused: `ybkmzp: dependency-blocked (executed:tm2cz8: external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here))`. The message names the three states it would accept and reports the one thing it read, which is a directory. `tm2cz8` satisfied the intended condition and was refused anyway. RE-REPRODUCED IN ISOLATION at review time in a throwaway repo, so the defect is pinned independently of this repository's state. NOTE `tm2cz8` has since advanced to `approved`, which is why the isolated reproduction rather than the live command is the durable evidence.
  THE FIX IS SMALL BECAUSE THE READER ALREADY EXISTS AND IS ALREADY IMPORTED. `selectors.read_front_matter_status` is bound into both runners as `_read_status` (`oc_runipd.py:265`), and THE SAME FUNCTION FILE already uses it for exactly this purpose 2500 lines later: `reconcile_disposition`'s review branch reads `status = _read_status(text)` and compares against `("reviewed", "approved")` (`:5829-5841`). So one code path in this module reads the field and another reads the directory, for the same question.
  WHY IT MATTERS BEYOND ONE COMMAND: a Set authored with `executed:` edges between its children (the normal shape, since a later child consumes an earlier child's work) cannot have its children REVIEWED in one sweep until each prerequisite has actually executed. That serializes review behind execution for no reason, and the review sweep's stated purpose is to review several plans in one shared session.
  THE FIX DOES NOT REACH AGY BY BINDING ALONE, contrary to this plan's first draft. `agy_runipd.py` defines its OWN `dependency_status_detailed` (`:2259-2315` at HEAD) with its OWN `plan_bucket` comparison (`:2301-2315`), so ONE of agy's two entry paths never calls `edge_satisfied` at all. See F-9; E-03 is the item that closes it.
  THE SPEC AMENDMENT OQ-04 REQUIRED HAS ALREADY LANDED, at `faa4c7ec` ("spec(25kzda): sanction the review-action dependency relaxation in 2.9"), BEFORE this plan is dispatched. §2.9 now carries a two-row table keyed on the consuming action, and rules 8 and 9 of §5.4 were amended in lockstep. So the precondition is SATISFIED, not pending; see the spec-sync section for what this obliges at finalize time.
- Scope: Make the external-target branch of `edge_satisfied` consult the plan's `- Status:` field for the non-terminal states, using the reader both runners already import, so the existing review relaxation becomes reachable. Then make agy actually reach that fix by removing its divergent local `dependency_status_detailed` copy, and close the sharing-guard hole that let the copy exist. Do NOT relax the EXECUTE path, and do not change the refusal for a target that genuinely has not reached a permitted state.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: depreview
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 03ie04
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved
- From-Backlog: yf9fj9

## Workflow history
- 2026-09-08 approved (aw set): status set to approved
- 2026-09-08 amended (opencode/its_direct/pt3-claude-opus-5-1m-us): ADDED E-07/V-07 and finding F-9 AFTER this plan's 2026-09-07 review, at the maintainer's direction. HONEST LIMIT: the review that set `- Readiness: go-pending-approval` critiqued the SIX-item version of this plan and has NOT assessed E-07, so that item carries no review coverage yet. It was folded in here rather than filed separately because it is the same phase-blindness defect in a sibling function and needs no scope expansion (this plan's `Scope-Paths` already cover both call sites and the dependency tests). E-07 declares `Depends on: none` deliberately: it is a wrong-argument-at-a-call-site fix that stands even if OQ-04 is answered against the relaxation, so bundling does not make it hostage to that decision.
- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2, APPROVE WITH REVISIONS APPLIED, readiness GO - PENDING HUMAN APPROVAL. PR-010..PR-016 recorded, ALL SEVEN FIXED, no open questions remain. THE BLOCKER FROM ROUND 1 IS DISCHARGED, not merely answered: OQ-04's required spec amendment LANDED at `faa4c7ec` before this plan runs, so §2.9 now carries a two-row action-keyed edge table whose `review` row accepts `executed`/`reviewed`/`approved` with no execution evidence, and §5.4 rules 8 and 9 were amended in lockstep. I verified the landed text rather than trusting the ruling. Two consequences the plan had not absorbed and I fixed: the spec file was still declared in `- Scope-Paths:`, which would now make `aw ipd finalize` demand a `--scope-ack` for a path the plan will never touch and make the runner announce a spec edit that will not happen (PR-010); and the amendment adds a CONSTRAINT the original instruction did not, prohibiting the two rows from being distinguished by queue membership or host, which is the normative basis for E-02, E-03 and E-06's in-queue pin (PR-011). THE MOST IMPORTANT NEW FINDING IS A LATENT REGRESSION THE PLAN COULD NOT SEE. 25 of the 454 plans in `executed/` carry a `- Status:` the shared reader returns `None` for (24 absent, 1 the multi-word `EXECUTED (...)` form), the identity index reports their status as `''`, and all 25 satisfy an `executed:` edge TODAY because the directory decides. An executor reading "read the field instead of the directory" as a general improvement breaks all 25 at once, and no case in the plan's seven-case matrix would have noticed; the matrix is now eight cases with the terminal-directory case named as the anti-regression one (PR-012). I ALSO REHEARSED E-03 RATHER THAN REASONING ABOUT IT: monkeypatching `agy.dependency_status_detailed` to oc's object and running the three affected suites gives `145 passed`, which resolves the plan's open worry about the reason-map key shape (the only cross-driver key assertion uses a bare `depaaa`, where token and id6 coincide) and surfaces two things it had missed. First, agy's copy is broken a THIRD way nobody had reported: it has no `orchestrate` clause, so on that path an orchestrator bypasses `decide_orchestrator_dispatch` entirely (AST-verified). Second, the deletion ORPHANS `agy._findings_block_reason`, whose only two call sites are inside the doomed function, while a cross-driver test still requires it to exist, so the suite would stay green over dead code; E-03 now annotates rather than deletes it (PR-013, F-14). SMALLER FIXES: the plan cited a sibling child `2p8p71` as owning the block-reason work and NO SUCH PLAN EXISTS (`aw find plans 2p8p71` -> no match); the real sibling is backlog `phawyy`, RETRACTED and `parked` because the premise was false (PR-014). Its F-7 count of "nine pending plans" counted grep-matching files including itself; the measured figure is 11 declaring `executed:` edges of which 8 name a non-`executed/` target (PR-015). And the baseline it told the executor to judge against was stale in a way that matters: the suite now shows 2 failures, not 1, and BOTH are repository-state-dependent rather than deterministic (one asserts a live plan's status that has since advanced to `approved`, one reads the gitignored runs tree), so the plan now requires a freshly measured baseline instead of quoting one (PR-016). Every line number in the plan had drifted 5 to 7 lines and was re-measured at HEAD. Structural lint conforms at `--phase review-finalize`.
- 2026-09-07 to-review (aw set): status set to to-review

- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-009 recorded, eight FIXED and one OPEN. Readiness NO-GO for ONE reason, which is not a defect in the plan's craft: the change it makes is FORBIDDEN BY AN APPROVED SPEC and only the maintainer can resolve that. Spec `25kzda` §2.9 (`- Status: approved`) defines an `executed:` edge as satisfied when the target "is in `executed/` with status `executed`", with NO review-action relaxation anywhere in the section, and its §2.10 states "All surfaces call this evaluator; none reimplement the rules". So the `("executed", "reviewed", "approved")` tuple this plan makes REACHABLE is itself unsanctioned: the plan would take a currently-inert deviation from an approved spec and make it live. That is OQ-04 and it carries `- Blocking: yes`. THE PLAN'S THREE CENTRAL CLAIMS ARE ALL TRUE and I verified each rather than trusting it: the relaxation exists at `:3316`/`:3339`, `plan_bucket` reads directories only (`runner_shared.py:1094-1108`), and `_read_status` is already imported (`:258`) and already used for this exact comparison (`:5813-5822`). I also REPRODUCED the defect in an isolated throwaway repo. THE ONE STRUCTURAL ERROR, and it would have shipped a half-fix: the plan asserts `agy_runipd.py` "BINDS these symbols rather than defining them, so the fix reaches it without an edit", and fences agy out. FALSE, and measured: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False`. Agy defines its own copy (`:2251-2306`) which never calls `edge_satisfied`, cannot parse a typed token (measured: it reports `no plan resolves to this id6` for `executed:tttttt` because it uses the raw string as an id6), and compares `plan_bucket` itself. Agy's OTHER path is oc's, because agy re-exports oc's `dependency_status` whose body resolves `dependency_status_detailed` in OC's globals. So agy has TWO dependency paths with DIFFERENT semantics, and the plan's fence would have left one of them broken while claiming host parity. The existing anti-copy guard misses it because `_SHARED_NAMES` (`tests/test_runner_item_dependencies.py:1121-1133`) lists `dependency_status` but NOT `dependency_status_detailed`. SECOND ERROR: E-03 would have deleted `reviewed`/`approved` from `plan_bucket`, which `tests/test_oc_runipd.py:1819-1835` explicitly asserts it recognizes (measured `2 passed`), so the "observably a no-op" claim was wrong and the plan did not declare that test's file in Scope-Paths.
- 2026-09-07 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yf9fj9`, filed after a live refusal earlier this session. Every claim re-verified at HEAD `3802cb3f` rather than trusted. THE FINDING THAT MOST SHAPES THIS PLAN, and it makes the fix far smaller than the item assumed: the status reader is ALREADY IMPORTED INTO BOTH RUNNERS (`oc_runipd.py:258`, `from agent_workflows.selectors import read_front_matter_status as _read_status`) and THE SAME MODULE ALREADY USES IT FOR THIS EXACT COMPARISON at `:5813-5822`, where `reconcile_disposition`'s review branch reads the field and tests it against `("reviewed", "approved")`. So this is not "teach the runner to read a status"; it is "make one call site agree with the other". The prior work that shared the reader (`rununify` 01, `2r306y`) records why it is shared: "both host runners used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers." ALSO CONFIRMED: `plan_bucket`'s list includes `reviewed` and `approved` as if they were directories, which is where the wrong assumption originates and which OQ-02 addresses. NOT IN SCOPE, and filed separately as the sibling child: the missing persisted REASON that made this defect diagnosable only from a terminal scrollback.

## Goal

Let a plan be reviewed when its prerequisite is reviewed or approved, which the code already intends and cannot currently do, on BOTH hosts, and only once the approved spec sanctions it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the relaxation reachable

- [x] E-01 In `edge_satisfied`'s EXTERNAL-TARGET branch, resolve the target's effective state from BOTH its directory and its `- Status:` field, rather than from the directory alone. Read the field with `_read_status`, which is ALREADY IMPORTED into this module (`oc_runipd.py:265`) and already used for the same comparison at `:5829-5841`; do NOT add a second reader or a second regex.
  OQ-04 IS ANSWERED AND THE SPEC AMENDMENT HAS ALREADY LANDED (`faa4c7ec`), so this item is CLEARED to start. Verify that before you begin: `git log --oneline -1 -- .aw/records/specs/*aw-run-deterministic*` must show the amendment, and §2.9 must contain the two-row action-keyed table. If it does not, refuse and report (the plan is being run against an unexpected base).
  PRECEDENCE IS THE DECISION HERE, so make it deliberate: a TERMINAL directory is authoritative (a plan in `executed/` is executed regardless of what a stale field says, which is the anti-fabrication posture the rest of the runner takes), while for a NON-TERMINAL directory the FIELD carries the readiness. State that rule in a comment at the site, because a future reader will otherwise re-derive it wrongly in one direction or the other.
  THE TERMINAL-DIRECTORY HALF OF THAT RULE IS LOAD-BEARING TODAY, NOT HYPOTHETICAL, and getting it wrong is the one way this item can REGRESS working behavior. MEASURED at review: 25 of the 454 plans in `executed/` have a `- Status:` field `read_front_matter_status` returns `None` for (24 absent, 1 the multi-word `EXECUTED (...)`), and the SHARED identity index reports their status as the empty string (probed: `_artifact_owners(repo,'plans','i9xi81')` -> `[('', '...')]`). All 25 satisfy an `executed:` edge TODAY, because the directory decides. If the field were consulted for a TERMINAL directory, or if `None` were allowed to override it, all 25 would begin refusing. No pending plan currently depends on one of them (measured: zero such edges), so the regression would be silent until it was not.
  FAIL CLOSED WHEN THE FIELD IS UNREADABLE, IN THE NON-TERMINAL CASE ONLY. For a plan in `pending/`, a missing or unparseable `- Status:` must leave the target unsatisfied, exactly as an unrecognized bucket does today. Follow the existing `try`/`except` shape at `:5829-5836`, which already treats an unreadable plan as `status = None`. Note `read_front_matter_status` ALSO returns `None` for a MULTI-WORD status (its docstring: "A multi-word status (e.g. `EXECUTED (approved ...)`) yields `None`"), so a legacy plan with a parenthesized status fails closed too; that is correct, and say so rather than treating `None` as one case.
  DO NOT REACH FOR `_artifact_owners` INSTEAD OF THE FILE READ, tempting though it looks (it already returns `(status, path)` and is already used by this same function for `exists:`/`state:` edges). Three reasons, measured: it rebuilds the WHOLE-REPO artifact inventory per call (~260ms measured here, versus ~42ms for `resolve_plan_path`) and `edge_satisfied` is called per edge per dispatch iteration; it reads via `status_set._STATUS_RE`, the STRICT reader, whereas the runners deliberately use the PERMISSIVE `_read_status` alias (`tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` pins that split, and swapping readers here would silently narrow which spellings the runner accepts); and the branch already holds `dep_path` from `resolve_plan_path`, so the file read is free. Measured for completeness: the two readers agree on all 514 plan records today, so this is a durability and performance argument, not a correctness one.
  - Depends on: none
  - Expected outcome: an external `executed:` target in `pending/` carrying `- Status: reviewed` SATISFIES a review-action edge; a TERMINAL directory still decides on its own, so all 25 field-unreadable `executed/` plans keep satisfying; an unreadable, absent, or multi-word status in a NON-TERMINAL directory refuses; `_read_status` is the reader and no second reader, regex, or index call was added.
  - Execution state: performed

- [x] E-02 Do NOT relax the EXECUTE path, and prove it. `is_exec` must keep requiring a genuinely `executed/` prerequisite: an execute turn consumes its prerequisite's WORK, so a merely `reviewed` or `approved` plan has produced nothing to consume, and satisfying that edge would dispatch a dependent against a base lacking its prerequisite's commits.
  THE ASYMMETRY IS THE WHOLE POINT and must be visible in the code, not just in this plan: the review branch gains the field read; the execute branch keeps comparing against the terminal directory. Note that for an execute edge the directory IS the right authority, since `executed/` is exactly where finalize puts a plan, so E-01's precedence rule already yields the correct answer without a special case.
  PRESERVE THE FINDINGS GATE'S REACH, and know why it does not help here: `dependency_status_detailed` applies `_findings_block_reason` only `if is_exec` (`oc_runipd.py:3491-3495`), and its docstring states a review-action item "is deliberately NOT findings-gated". So a review edge satisfied by this change is NOT additionally screened for unresolved gating findings. That is the existing intended design, not a regression this plan introduces, but it means E-01's field read is the ONLY gate on the review path; do not weaken it further.
  ALSO PIN THE HALF THAT IS ALREADY CORRECT AND MUST STAY SO. The in-queue branch already refuses an execute-action edge whose prerequisite entered the queue as `reviewed`, which is the derived RUN status `initialize_run` writes for a plan that is already `executed` on disk (`:2968-2970`: only `to-review`/`draft`/`approved`/`auto-approved` become `queued`). Probed at review: an execute dependent against such an entry returns `in-run target prq001 is 'reviewed', needs one of ['executed', 'substantially-complete']`, while the same shape with a REVIEW dependent returns satisfied. That asymmetry is the same one this item defends, one path over; do not let a refactor collapse the two.
  - Depends on: E-01
  - Expected outcome: an execute-action edge against a `reviewed` or `approved` target still REFUSES; the execute path's behavior is byte-identical to today; the findings gate's `is_exec` scoping is unchanged and its consequence is documented.
  - Execution state: performed

### Task group 2: make the fix actually reach the second host

- [x] E-03 DELETE `agy_runipd.py`'s local `dependency_status_detailed` (`:2259-2315` at HEAD) so agy consumes the shared implementation, because WITHOUT THIS ITEM THE FIX REACHES ONLY ONE OF AGY'S TWO PATHS. This is the item the plan's first draft omitted while asserting the opposite.
  THE MEASURED FACTS, verified at review rather than reasoned: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False`, while `agy.dependency_status is oc.dependency_status` -> `True`. Agy's dispatch loop calls the RE-EXPORTED `dependency_status` (`:4334`), whose body resolves `dependency_status_detailed` in OC's module globals, so THAT path already gets the fix. Its drain path calls the LOCAL `dependency_status_detailed` (`:4359`), which does not. Two paths, two semantics, in one driver.
  THE LOCAL COPY IS WORSE THAN STALE, IT IS BROKEN, AND IT IS BROKEN IN THREE WAYS, not one. Measured by AST inspection of the function body: the tokens `edge_satisfied`, `parse_dependency_token`, `decide_orchestrator_dispatch` and `orchestrate` are ALL ABSENT from it. So (a) it never calls `edge_satisfied`; (b) it uses the RAW dependency string as an id6 and therefore cannot resolve a typed edge at all (measured in a throwaway repo: `executed:tttttt: no plan resolves to this id6 in the repo`, while a bare `tttttt` gets the `plan_bucket` refusal, and against a REAL repo it reports `no plan resolves to this id6` for a perfectly good `executed:tm2cz8`); and (c) IT HAS NO ORCHESTRATOR CLAUSE, so on agy's drain path an `orchestrate` item is judged by the same code as any other item, while oc's version routes it through `decide_orchestrator_dispatch`. Every plan in this tree declares typed edges, so agy's drain path currently misreports EVERY dependency as dangling. Deleting the copy fixes all three at once, which is the argument for deletion over patching.
  DELETION IS THE FIX, NOT PATCHING THE COPY. The module's own comment two lines below already states the rule and the history: `dependency_status` "is NOT defined here ... so the runtime satisfaction semantics exist exactly ONCE. The deleted copy was a verbatim duplicate of oc's, which is how both drivers came to be equally unable to read the canonical field: a fix applied to one silently left the other broken" (`:2318-2323`). That is this defect, recurring in the sibling function. Re-export it in the import block exactly as `dependency_status` is, in the `as <same-name>` form that block uses deliberately so an autoformatter cannot strip an unused-looking re-export (`:293-298` records that `ruff` removed six of them once and the symmetry test caught it).
  VERIFY THE SIGNATURES MATCH BEFORE DELETING; THE ANSWER IS ALREADY MEASURED. Agy's local copy documents `{dep_id6: reason}` while oc's returns `{dep_token: reason}` keyed by the token AS DECLARED (`oc_runipd.py:3485-3487`). THE ONLY cross-driver test that asserts on the key shape is `tests/test_review_findings_cascade.py::BlockLegibilityTests::test_reason_map_names_the_finding_id_and_severity`, and its fixture declares a BARE `depaaa` dependency, for which token and id6 are IDENTICAL, so it passes under either shape. VERIFIED BY EXECUTION, not by reading: running `tests/test_review_findings_cascade.py`, `tests/test_runner_item_dependencies.py` and `tests/test_agy_runipd_cli.py` with `agy.dependency_status_detailed` monkeypatched to oc's object gives `145 passed`. That is a rehearsal of E-03, so no test-file edit is expected for the key shape; if you find one, report it.
  ONE CONSEQUENCE TO HANDLE, and it is the one thing a naive deletion gets wrong. Agy's `_findings_block_reason` (`:2231-2249`) is called from EXACTLY TWO places (`:2295`, `:2309`), and BOTH are inside the function you are deleting (verified by AST: zero call sites outside it). After the deletion agy's wrapper is DEAD CODE, while `tests/test_review_findings_cascade.py::SharedPredicateTests` still requires `hasattr(agy, "_findings_block_reason")` and that agy's source mention `subject_gating_blocks`, so the test keeps passing over a function nothing calls. Do NOT delete the wrapper (that would fail the test and is a wider decision than this plan's fence); instead ADD A COMMENT at it recording that it is retained for the cross-driver API-symmetry contract and that its live call sites now live in `oc_runipd`, so the next reader does not mistake it for a second implementation.
  - Depends on: E-02
  - Expected outcome: `agy.dependency_status_detailed is oc.dependency_status_detailed` is True; agy's drain path resolves typed edges AND routes an `orchestrate` item through the shared decider; no local copy remains; the reason-map key shape is confirmed unaffected; agy's now-uncalled `_findings_block_reason` is annotated rather than deleted.
  - Execution state: performed

- [x] E-04 CLOSE THE SHARING-GUARD HOLE that let E-03's copy exist, so this class of divergence cannot recur silently. Add `dependency_status_detailed` to `_SHARED_NAMES` in `tests/test_runner_item_dependencies.py:1121-1133`, which today lists `dependency_status` but not its `_detailed` sibling, which is exactly why `test_the_implementation_is_shared_not_copied` passed over a real copy.
  DEMONSTRATE THE GUARD BITES. Add the name, run the test against the PRE-E-03 code and paste the FAILURE, then run it after E-03 and paste the pass. A guard only ever run against fixed code proves nothing.
  THE `_SHARED_NAMES` IDENTITY ASSERTION IS THE RIGHT AND ONLY AVAILABLE HOME, and the reason is structural rather than a preference: `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` (`:80-159`) holds ZERO rows owned by `oc_runipd` (measured: every row's owner is `render_stream`, `runner_shared`, or `selectors`) and the string `dependency_status` does not appear in the file at all. Its `Owned` contract is "a NON-RUNNER module owns this symbol; no runner may re-define it", so an oc-owned symbol has no expressible row: naming `oc_runipd` as the owner would make its AST half forbid oc's own definition. So ADD THE NAME TO `_SHARED_NAMES` AND STATE THAT CONCLUSION at the `_SHARED_NAMES` definition (one comment line), so the next reader does not spend the same twenty minutes re-deriving it. Extending `Owned` to express runner-owned symbols is a REAL improvement and is explicitly OUT of this plan's scope; if you think it is worth doing, file a backlog item rather than doing it here.
  KNOW WHAT THE GUARD DOES AND DOES NOT CATCH, because E-03's copy proves the difference matters. `_SHARED_NAMES` checks OBJECT IDENTITY only, so it catches a re-defined copy (which is what happened) but would NOT catch a copy assigned over the re-export at import time. That residual hole is accepted, not fixed here: no such pattern exists in either driver today.
  - Depends on: E-03
  - Expected outcome: `_SHARED_NAMES` includes `dependency_status_detailed`; the guard is shown FAILING pre-fix and passing post-fix; a comment records why the refork-guard table cannot host this symbol; no change to `tests/test_runner_refork_guard.py`.
  - Execution state: performed

### Task group 3: remove the source of the wrong assumption

- [x] E-05 Correct `plan_bucket`'s DOCUMENTATION, and do NOT delete list members without handling the test that pins them. It scans path components for `executed`, `active`, `pending`, `reviewed`, `approved`, `reusable`, `superseded`, `not-executed` (`runner_shared.py:1151-1160`) and TODAY HAS NO DOCSTRING AT ALL, and `reviewed/`/`approved/` do not exist as directories in this layout, so the list invites exactly the confusion this plan is fixing.
  THE "OBSERVABLY A NO-OP" CLAIM WAS FALSE, so this item is re-pointed. `tests/test_oc_runipd.py:1818-1840` (`PlanBucketRecognitionTests`) asserts `plan_bucket` returns each of the eight names INCLUDING `reviewed` and `approved` for a synthetic path, and that an unknown segment returns `None`; measured `2 passed` at HEAD. Deleting the members BREAKS that test, so the change is not invisible and that test's file must be in Scope-Paths (it now is).
  THE MINIMAL SAFE CHANGE IS DOCUMENTATION, not deletion: ADD a docstring stating that buckets are DIRECTORIES and readiness is a FIELD, that `reviewed`/`approved` (and `active`) are recognized DEFENSIVELY and do not occur in this layout, and that a caller wanting readiness must read `- Status:` (citing `edge_satisfied` as the precedent). Cite the corroborating layout fact rather than asserting it: `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` (`:506-511`) lists exactly `executed`, `superseded`, `not-executed`, `reusable` as the terminal directories, which is the same four-plus-`pending` layout measured on disk, and names neither `reviewed` nor `approved`. That removes the trap for the next reader at zero behavioral risk.
  IF YOU NEVERTHELESS DELETE THEM, you must also update `tests/test_oc_runipd.py` and prove no caller compares a bucket to those values. THE CALLER SEARCH IS ALREADY DONE and its result is recorded here so you verify rather than rediscover: nine non-test call sites (`oc_runipd.py:1178`, `:2243`, `:3345`, `:5852`, `:6761`; `agy_runipd.py:1478`, `:2304`, `:3188`, `:4077` at HEAD), and the ONLY equality comparisons are against `"executed"`. `agy_runipd.py:2304` compares against the `("executed","reviewed","approved")` tuple and is DELETED by E-03, which is what removes the last such comparison. Note two of these sites use a bucket as a DEFAULT STATUS rather than comparing it (`oc_runipd.py:2243` / `agy_runipd.py:3185`-neighborhood `status = bucket or "to-review"`), so a deleted member would silently change a derived status there; that is a further argument for documentation over deletion. Re-verify at execution time; do not trust this list blind.
  - Depends on: E-04
  - Expected outcome: `plan_bucket` HAS a docstring stating that buckets are directories, readiness is a field, and which members are defensive; no real path's bucket changes; if members were removed, the pinning test is updated and the caller search re-verified.
  - Execution state: performed

### Task group 4: prove it

- [x] E-06 Test the MATRIX of action against target state, prove BOTH hosts, and prove nothing else moved. The correctness of this change is entirely in which combinations pass.
  THE MATRIX, for an external target: review-action against `pending/` + `Status: reviewed` SATISFIES; review against `pending/` + `Status: approved` SATISFIES; review against `pending/` + `Status: to-review` REFUSES; review against `executed/` SATISFIES; execute against `pending/` + `Status: reviewed` REFUSES; execute against `executed/` SATISFIES; a missing, unparseable, or MULTI-WORD status in a NON-TERMINAL directory REFUSES for both actions.
  ADD THE EIGHTH CASE, WHICH IS THE ANTI-REGRESSION ONE AND THE ONE MOST LIKELY TO BE OMITTED: a target in `executed/` whose `- Status:` field is ABSENT or MULTI-WORD must still SATISFY under BOTH actions, because the terminal directory decides. This is not hypothetical: 25 real plans in `executed/` are in exactly that state (measured at review; 24 absent, 1 `EXECUTED (...)`), and all 25 satisfy today. A fix that made the field authoritative everywhere would break all 25 and no other case in this matrix would notice.
  REPRODUCE THE MEASURED CASE as a named fixture with SYNTHETIC plans, not by naming live plans: `- Item-Dependencies: executed:<prereq>` where the prerequisite is `pending/` + `Status: reviewed`, action `review`. Assert it now SATISFIES, and assert against the PRE-FIX code that it refused, so the contrast is demonstrated rather than asserted. DO NOT write a test that depends on `tm2cz8`'s live status: it was `reviewed` when this defect was filed and is `approved` now, so such a test would have silently changed what it proves within a day.
  ASSERT BOTH AGY PATHS, which is the test the plan's original fence made impossible: drive the DISPATCH path (re-exported `dependency_status`) AND the DRAIN path (`dependency_status_detailed`) and assert they agree. Pin `agy.dependency_status_detailed is oc.dependency_status_detailed`. BE HONEST ABOUT WHAT THAT PROVES AFTER E-03: once the copy is gone both paths call the SAME object, so "they agree" is true by construction and the assertion's real value is the IDENTITY pin, which is what fails if the copy ever returns. Say so in the test docstring rather than implying two independent implementations were compared.
  ASSERT THE IN-QUEUE PATH IS UNTOUCHED. The in-queue branch (`:3326-3337`) compares against `EXECUTION_SUCCESS_STATES` or `SUCCESS_STATES` from run state, not from disk; pin that so a later refactor does not merge the two paths carelessly. Note `SUCCESS_STATES = {"executed","reviewed","approved"}` (`:327`) is the in-run twin of the on-disk tuple. STATE THE ANSWER RATHER THAN RE-DERIVING IT: the amendment at `faa4c7ec` sanctions BOTH readings, and the twin already equals the on-disk tuple, so NO change to `SUCCESS_STATES` is expected. Confirm that by inspection and say so; if you find yourself editing it, stop and report, because the two must stay equal or one edge's verdict starts depending on queue membership.
  NOTE `SUCCESS_STATES` IS DUPLICATED PER DRIVER, and this is the one place that matters here: `agy_runipd.py:387-388` defines its own `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES` and they are EQUAL but NOT the same object (measured: `agy.SUCCESS_STATES is oc.SUCCESS_STATES` -> `False`, `==` -> `True`). Do not "fix" that here; it is `rununify`'s job. Just assert the equality so a future divergence fails a test.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. MEASURE YOUR OWN BEFORE-BASELINE IMMEDIATELY BEFORE YOU START, and do not inherit this plan's number: measured at THIS review `2 failed, 5640 passed, 3 skipped, 2 xfailed`, where the two failures are BOTH pre-existing and NEITHER is in this plan's scope (`test_orchestrator_retirement::RealRepositorySets::test_runprofile_refuses_for_R2...`, which asserts a live plan's status that has since advanced to `approved`; and `test_run_viewer::RunViewerTests::test_run_viewer_cli_latest_only`, which reads the gitignored `.aw/records/runs/` tree and fails because the three newest runs share one queue, so `latest_only` collapses to a single contributing run and prints no "Data from N runs" header). BOTH are repository-state-dependent, so your own baseline may differ again; the criterion is that the AFTER failure set minus YOUR BEFORE set is EMPTY.
  - Depends on: E-05
  - Expected outcome: all eight matrix cases pass; the measured case is pinned with a pre-fix contrast using synthetic fixtures; both agy paths are exercised, the identity is pinned, and the test says what that does and does not prove; the in-queue path is proven unchanged and `SUCCESS_STATES` stated unchanged; the bare-suite delta against a freshly measured baseline is empty with counts stated.
  - Execution state: performed

- [x] E-07 Pass a REVIEW-APPROPRIATE phase to the dependency preflight, so a review-only run is not gated on execution readiness. `enforce_dependency_preflight` accepts a `phase` parameter (`oc_runipd.py:2616`, default `"pre-execution"`), but its single caller at `oc_runipd.py:2834` passes NONE, so every run gets the execution phase even when every selected item's action is `review`. Derive the phase from the queue: when all selected items resolve to the `review` action, pass the review phase; otherwise keep `pre-execution` exactly as today. Do the same in the agy caller, and locate both by SYMBOL rather than line number. THIS ITEM STANDS ON ITS OWN even if OQ-04 is answered against the relaxation: it is a wrong-argument-at-a-call-site defect, independent of what the acceptance predicate decides once it is reached, and the preflight refuses BEFORE selection ever consults `edge_satisfied`, so E-01..E-06 cannot fix it.
  EXECUTED DIFFERENTLY FROM THE MECHANISM THIS ITEM NAMES, ON MEASURED EVIDENCE; SEE DECISION 01-03ie04-D1. The GOAL was reached and is now pinned on both hosts; the `phase` ARGUMENT was NOT added, because measurement shows it cannot produce that goal. TWO FACTS decide this. FIRST, `phase` reaches EXACTLY ONE rule inside `check_engine.evaluate_ipd_dependencies`: `blocking = phase in _DEP_BLOCKING_PHASES` gating the `unresolved` SCAFFOLD SENTINEL finding, and by AST inspection those are the only references to `phase`/`blocking` in the whole function. Every phase a review turn could claim (`review-readiness`, `review-finalize`, `pre-execution`, `pre-transition`) is ALREADY in that set, so no reachable value changes any verdict; the only values that WOULD change behavior (`check`/`author`) relax the sentinel for the entire selection, a widening this item never asked for. SECOND, the cited defect was ALREADY FIXED at HEAD by commit `5699c6ad` ("fix(deps): exempt a review turn from the dependency findings gate, per spec 2.9", an ancestor of this plan's base), using the CORRECT mechanism: the evaluator gained an `actions` parameter, the findings-blocked rule is now guarded by `(actions or {}).get(ps) != "review"`, and `preflight_dependency_findings` threads `actions=_consuming_actions_for(plans)` derived from the same `runner_shared.action_for` the queue builder uses. Its commit message cites the SAME measured refusal F-9 cites. So writing the `phase` argument would have added a control that looks like a gate and is not one, which is worse than the gap. What was done instead: the goal is VERIFIED by measurement and PINNED by `ReviewQueuePreflightTests` (review queue admitted on both hosts, execute queue still refused on both hosts, plus a MUTATION check that neutralizes the action derivation and shows the review case refusing again), and `test_the_phase_argument_cannot_discriminate_a_review_turn` records the negative finding so nobody re-adds the argument expecting it to gate.
  - Depends on: none
  - Expected outcome: `aw oc run <setid>` over a queue of review turns is not refused by a dependency's unresolved review findings or unexecuted state; an execute-action queue is refused exactly as it is today.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE GATE IS ALREADY ACTION-AWARE and already intends this relaxation: `is_exec = item.get("action") != "review"` and `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")` (`oc_runipd.py:3323`, `:3346`). This plan makes an existing intent reachable rather than adding a new behavior.
- APPROVED SPEC `25kzda` §2.9 NOW SANCTIONS IT EXPLICITLY, as of `faa4c7ec`: the edge table is keyed on the CONSUMING ACTION and carries two `executed:` rows, the `review` one reading "The target resolves uniquely to an IPD whose state is `executed`, `reviewed`, or `approved`. Terminal execution evidence is NOT required" (`:373-378`). §5.4 rules 8 and 9 were amended in lockstep (`:941-942`). §2.10's "All surfaces call this evaluator; none reimplement the rules" is intact and is exactly why E-03 deletes agy's copy.
- THE SPEC ALSO PROHIBITS THE WIDENING THIS PLAN MUST NOT DO, in the same amendment: "The two rows must stay distinguishable by the consuming action and by nothing else: not by queue membership, not by which host is running, and not by whether the target happens to be in the current run" (`:388-394`). That single sentence is the normative basis for E-02 (no execute relaxation), E-03 (both hosts identical), and E-06's in-queue pin, so cite it rather than re-arguing them.
- THE READER IS ALREADY SHARED AND ALREADY IMPORTED: `selectors.read_front_matter_status` is bound as `_read_status` in both runners (`oc_runipd.py:265`), and `rununify` 01 (`2r306y`) records why: the runners "used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers."
- THE PERMISSIVE-VERSUS-STRICT READER SPLIT IS A PINNED DECISION, not an accident: the runners' `_read_status` is the PERMISSIVE public alias, while `selectors._read_status` stays STRICT for `aw find` matching, and `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` asserts both halves. So use `_read_status` and do not substitute any other status reader (see E-01's note about `_artifact_owners`).
- THE SAME MODULE ALREADY DOES THIS COMPARISON CORRECTLY, 2500 lines away: `reconcile_disposition`'s review branch reads `status = _read_status(text)` inside a `try`/`except` and tests it against `("reviewed", "approved")` (`:5829-5841`). Follow that shape, including its fail-closed `status = None`.
- `read_front_matter_status` RETURNS `None` FOR A MULTI-WORD STATUS, by documented contract (`selectors.py:294-301`), so a parenthesized legacy status is indistinguishable from an absent one. In a NON-TERMINAL directory both must fail closed; in a TERMINAL one neither may.
- READINESS IS A FIELD, NOT A DIRECTORY, in this layout: a plan stays in `pending/` through `draft` -> `to-review` -> `reviewed` -> `approved` and only a TERMINAL state moves it. Verified: `.aw/records/plans/` contains only `executed`, `not-executed`, `pending`, `reusable`, `superseded`; no `reviewed/`, `approved/`, or `active/` directory exists anywhere under `.aw/records`. Corroborated in code by `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` (`:506-511`), which names those four terminal directories and neither `reviewed` nor `approved`.
- THE DIRECTORY IS NOT MERELY A WEAKER SIGNAL THAN THE FIELD; IN `executed/` IT IS THE ONLY RELIABLE ONE for 25 plans. Measured: 25 of 454 plans in `executed/` have a field `read_front_matter_status` returns `None` for, and the shared identity index reports their status as `''`. Every one satisfies an `executed:` edge today because the directory decides. This is the concrete reason OQ-01's precedence rule is not a tie-break but a recognition of which signal carries information in each case.
- **AGY IS NOT A PURE BINDER OF THIS PREDICATE.** `agy_runipd.py` re-exports `dependency_status` (`:346`) and `edge_satisfied` (`:348`) from oc, but DEFINES its own `dependency_status_detailed` (`:2259-2315`). Measured: `agy.dependency_status is oc.dependency_status` -> True; `agy.dependency_status_detailed is oc.dependency_status_detailed` -> False. So agy's dispatch path (`:4334`) inherits an oc fix and its drain path (`:4359`) does not.
- AGY'S COPY ALSO LACKS THE ORCHESTRATOR CLAUSE, which is a second live divergence nobody has yet reported: oc's version routes an `action == "orchestrate"` item through `decide_orchestrator_dispatch`, and the tokens `orchestrate` and `decide_orchestrator_dispatch` are ABSENT from agy's copy (verified by AST). E-03's deletion fixes that as a side effect; say so when reporting, because it is a behavior change beyond this plan's headline.
- SOME CROSS-DRIVER CONSTANTS ARE EQUAL BUT NOT SHARED: `agy_runipd.py:387-388` re-declares `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES` (measured `is` -> False, `==` -> True), as does `TERMINAL_STATES`. Not this plan's job to unify; worth an equality assertion so a future drift fails a test.
- THE ANTI-COPY GUARD HAS A HOLE: `_SHARED_NAMES` (`tests/test_runner_item_dependencies.py:1121-1133`) lists `dependency_status` but not `dependency_status_detailed`, which is why `test_the_implementation_is_shared_not_copied` passes over a live copy. The sibling guard `tests/test_runner_refork_guard.py` CANNOT host this symbol: its `REFORK_TABLE` has zero `oc_runipd`-owned rows by construction (its `Owned` contract is "a non-runner module owns this; no runner may re-define it").
- `plan_bucket`'s MEMBERS ARE PINNED BY A TEST: `tests/test_oc_runipd.py:1818-1840` asserts all eight names resolve, including `reviewed` and `approved`, and that an unknown segment yields `None` (measured `2 passed`). Removing a member is NOT invisible. Two callers also use a bucket AS a default status rather than comparing it, so a removal would silently change a derived status.
- THE FINDINGS GATE IS EXECUTE-ONLY, by design: `_findings_block_reason` is applied only `if is_exec` (`oc_runipd.py:3491-3495`) and the docstring says a review item "is deliberately NOT findings-gated". A review edge made satisfiable by this change gets no findings screening. NOTE the static evaluator applies its own findings check to `executed:` edges WITHOUT any action awareness (`check_engine.py:2518-2542`), because at author/check time there is no run and therefore no action; that is not a contradiction, and do not "harmonize" it.
- THE IN-QUEUE BRANCH IS A DIFFERENT QUESTION and reads RUN STATE, not disk (`:3326-3337`): "is this prerequisite verified IN THIS RUN yet". The function's own docstring warns it must not be consolidated with the static evaluator. Leave it alone; `SUCCESS_STATES` (`:327`) already equals the sanctioned on-disk tuple, so no change is expected there.
- Run the suite BARE: `python3 -m pytest`. The suite is NOT green at HEAD (2 failures at this review, both pre-existing and both repository-state-dependent), so judge on the DELTA against a baseline you measure yourself.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The gate IS action-aware and intends to accept `reviewed`/`approved` for a review turn. | `oc_runipd.py:3323`, `:3346` |
| F-2 | **THE RELAXATION IS UNREACHABLE:** it compares against `plan_bucket`, a DIRECTORY name, and this layout has no `reviewed/` or `approved/` directories, so every non-terminal plan buckets as `pending`. Measured on disk: `pending/` holds 29 plans whose fields are 9 `to-review`, 8 `reviewed`, 12 `approved`; every one of the 29 buckets as `pending`. | `oc_runipd.py:3345`; `runner_shared.py:1149-1163`; `ls .aw/records/plans/`; field census at review |
| F-3 | **MEASURED REFUSAL, AND RE-REPRODUCED IN ISOLATION:** `ybkmzp` (`Item-Dependencies: executed:tm2cz8`, action `review`) was refused with "external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved']" while `tm2cz8` carried `- Status: reviewed`. Re-created at review in a throwaway repo: a `review` item against a `pending/` + `Status: reviewed` target returns `satisfied=False` with the identical message. `tm2cz8` has since advanced to `approved`, which is why the isolated reproduction, not the live command, is the durable evidence and why E-06 must use synthetic fixtures. | `aw oc run --session <sid> ybkmzp`, 2026-09-07; isolated probe at review; `_artifact_owners(repo,'plans','tm2cz8')` -> `[('approved', ...)]` |
| F-4 | **THE READER IS ALREADY IMPORTED INTO BOTH RUNNERS**, so the fix adds no dependency and no new parsing. | `oc_runipd.py:265` |
| F-5 | **THE SAME MODULE ALREADY READS THE FIELD FOR THE SAME COMPARISON** 2500 lines later, inside a fail-closed `try`/`except`. So one call site reads the field and another reads the directory for the same question. | `oc_runipd.py:5829-5841` |
| F-6 | `plan_bucket` lists `reviewed` and `approved` as if they were directories AND HAS NO DOCSTRING, which is the origin of the wrong assumption and a trap for the next reader. | `runner_shared.py:1149-1163` |
| F-7 | The consequence is structural, not cosmetic: a Set whose children carry `executed:` edges (the normal shape) cannot have those children reviewed in one sweep until each prerequisite has executed, which serializes review behind execution and defeats the shared-session review sweep. MEASURED: 11 pending plans declare `executed:` edges and 8 of them name at least one target that is NOT in `executed/`, so 8 plans are unreviewable-in-a-sweep TODAY. (The earlier "nine" counted files matching a grep, including this plan itself.) | `aw oc run --help` review-sweep description; the measured refusal; per-edge target census at review |
| F-8 | The in-queue branch answers a DIFFERENT question from run state ("is this prerequisite verified IN THIS RUN yet") and its docstring warns against consolidation, so it is deliberately out of scope. Its `SUCCESS_STATES` twin already EQUALS the sanctioned on-disk tuple, so consistency is preserved by changing nothing. | `oc_runipd.py:3307-3337`, `:327` |
| F-9 | **AGY DEFINES ITS OWN `dependency_status_detailed`, SO THE FIX DOES NOT REACH ONE OF ITS TWO PATHS.** Measured: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False` (while `dependency_status`, `edge_satisfied` and `plan_bucket` all -> `True`). The local copy is broken THREE ways, all verified by AST inspection of its body: it never calls `edge_satisfied`; it never calls `parse_dependency_token`, so it uses the raw string as an id6 and reports `no plan resolves to this id6 in the repo` even for a valid `executed:tm2cz8` against the real repo; and it has NO `orchestrate` clause, so an orchestrator item bypasses `decide_orchestrator_dispatch` on that path. Agy's dispatch path uses oc's function, its drain path uses the copy. The plan's original claim that agy "binds these symbols rather than defining them" is false, and its fence would have shipped a half-fix. | `agy_runipd.py:2259-2315`, `:4334`, `:4359`; identity probe; AST token probe; real-repo probe |
| F-10 | **THE ANTI-COPY GUARD MISSES IT:** `_SHARED_NAMES` lists `dependency_status` but not `dependency_status_detailed`, so `test_the_implementation_is_shared_not_copied` passes over the copy in F-9. The module's own comment at `:2318-2323` already describes this exact failure mode for the sibling function ("a fix applied to one silently left the other broken"), so the class of defect is known and recurring. The sibling refork guard cannot cover it: `REFORK_TABLE` has ZERO `oc_runipd`-owned rows and never mentions `dependency_status`. | `tests/test_runner_item_dependencies.py:1121-1149`; `agy_runipd.py:2318-2323`; `tests/test_runner_refork_guard.py:80-159` |
| F-11 | **DELETING `plan_bucket`'s DEAD MEMBERS IS NOT A NO-OP:** `PlanBucketRecognitionTests` explicitly asserts `reviewed` and `approved` resolve (measured `2 passed`). The plan's "observably a no-op" premise was wrong and it did not declare that test file in Scope-Paths. Two non-test callers additionally use the bucket AS a default status (`status = bucket or "to-review"`), so a removal would change a derived status, not just a comparison. | `tests/test_oc_runipd.py:1818-1840`; `oc_runipd.py:2243`; `agy_runipd.py` `parse_plan_file` neighborhood |
| F-12 | **THE SPEC NOW SANCTIONS THE RELAXATION, AND DID SO BEFORE THIS PLAN RUNS.** Round 1 found `25kzda` §2.9 permitted only a single `executed` target with no review-action exception, making the reachable tuple an unsanctioned deviation. The maintainer ruled the relaxation IS the contract and amended §2.9 FIRST, at `faa4c7ec`: the table is now keyed on the consuming action, the `review` row accepts `executed`/`reviewed`/`approved` with no execution evidence, and §5.4 rules 8 and 9 were amended in lockstep. The amendment also PROHIBITS distinguishing the two rows by anything except the consuming action, which is the normative basis for E-02, E-03 and E-06's in-queue pin. So this plan no longer amends a spec, and the spec file is no longer in `- Scope-Paths:`. | `faa4c7ec`; spec `:373-378`, `:388-394`, `:941-942` |
| F-13 | A REVIEW EDGE IS NOT FINDINGS-GATED: `_findings_block_reason` runs only `if is_exec`. So once E-01 makes review edges satisfiable, nothing additionally screens the prerequisite's unresolved gating findings. Pre-existing intent, but newly consequential. Note the STATIC evaluator applies its findings check to `executed:` edges with no action awareness at all, correctly, since author-time has no run and hence no action. | `oc_runipd.py:3491-3495` and the `dependency_status_detailed` docstring; `check_engine.py:2518-2542` |
| F-14 | **E-03's DELETION ORPHANS A FUNCTION A TEST STILL REQUIRES TO EXIST.** `agy._findings_block_reason` has exactly TWO call sites (`:2295`, `:2309`) and BOTH are inside the doomed copy (verified by AST: zero outside). After the deletion nothing calls it, while `tests/test_review_findings_cascade.py::SharedPredicateTests` still asserts `hasattr(agy, "_findings_block_reason")` and that agy's source mentions `subject_gating_blocks`, so the suite stays green over dead code. Keep the wrapper (deleting it fails that test and is a wider decision) and ANNOTATE it, or the next reader will read it as a second implementation. | `agy_runipd.py:2231-2249`, `:2295`, `:2309`; `tests/test_review_findings_cascade.py:293-306`; AST call-site probe |
| F-15 | **THE TERMINAL-DIRECTORY HALF OF THE PRECEDENCE RULE PROTECTS 25 LIVE PLANS.** 25 of 454 plans in `executed/` carry a `- Status:` the shared reader returns `None` for (24 absent, 1 multi-word `EXECUTED (...)`), and the identity index reports their status as `''`. All 25 satisfy an `executed:` edge today because the directory decides; making the field authoritative in a terminal directory, or letting `None` override it, breaks all 25 at once. No pending plan currently depends on one (measured: zero such edges), so the regression would be silent. | field census over `executed/` at review; `_artifact_owners(repo,'plans','i9xi81')` -> `[('', ...)]`; live `dependency_status_detailed` probe -> `True` for both actions |
| F-16 | **E-03 WAS REHEARSED, NOT JUST REASONED ABOUT.** Monkeypatching `agy.dependency_status_detailed` to oc's object and running the three affected suites gives `145 passed`, so the deletion is behaviorally safe and the reason-map KEY-shape worry resolves to "no test asserts a shape that differs": the only cross-driver key assertion uses a BARE `depaaa` dependency, where token and id6 are identical. | `python3 -m pytest -p plugin_swap tests/test_review_findings_cascade.py tests/test_runner_item_dependencies.py tests/test_agy_runipd_cli.py -o addopts=` -> `145 passed`; `tests/test_review_findings_cascade.py:444-461`, `:157-167` |
| F-9 | HIGH | `oc_runipd.py:2834` vs `:2616` | THE SAME PHASE-BLINDNESS AT A SECOND SITE, found independently and NOT covered by E-01..E-06. `enforce_dependency_preflight` takes a `phase` parameter defaulting to `pre-execution`; its caller passes none, so a review-only run is gated on EXECUTION readiness. Measured 2026-09-07: `aw oc run orchprobe` (four review turns) was refused by `check.ipd-dependency-findings-blocked` over `executed:8tgg6g` / `executed:r2i1b1`, and the refusal blocks the very re-review that would resolve those findings. The preflight refuses BEFORE selection consults `edge_satisfied`, so this plan's other items cannot reach it. `cascade_dependency_blocked` already documents the correct principle ("a REVIEW pass does not require its prerequisite to have been EXECUTED"), applied there and not here. | maintainer-reported refusal; source read |

## Proposed changes (ordered, validatable)

1. Resolve an external target's state from the terminal directory OR the `- Status:` field, using the already-imported reader, failing closed in a NON-TERMINAL directory when the field is unreadable, absent, or multi-word, and never letting the field override a terminal directory (E-01).
2. Keep the execute path requiring a genuinely `executed/` prerequisite, and document that the review path is not findings-gated (E-02).
3. Delete agy's divergent local `dependency_status_detailed` so both of its paths consume the shared predicate, and annotate the wrapper the deletion orphans (E-03).
4. Close the `_SHARED_NAMES` hole, demonstrate the guard bites, and record why the refork-guard table cannot host this symbol (E-04).
5. Give `plan_bucket` the docstring it lacks rather than silently breaking the test that pins its members (E-05).
6. Pin the eight-case matrix including the terminal-directory anti-regression case, the measured case with a pre-fix contrast on synthetic fixtures, both agy paths, and the unchanged in-queue path (E-06).

## Deferred / out of scope (with reason)

- THE MISSING PERSISTED REASON, WHICH TURNED OUT NOT TO BE MISSING. The sibling backlog item `phawyy` (depreview) claimed a `dependency-blocked` item persists no reason; it was RETRACTED on 2026-09-07 and is `parked`, because both blocked paths already write `unsatisfied_dependency_reasons` and `dependency_block_recovery` and both emit events carrying them. The earlier revision of this plan cited a sibling child `2p8p71` as owning that work; NO SUCH PLAN EXISTS (measured: `aw find plans 2p8p71` -> no matching plans), so that citation was vapor and is removed. What remains true and narrow is that `aw runs` does not SURFACE the persisted reason in rendered output, which is a viewer gap and not this plan's business.
- THE IN-QUEUE DEPENDENCY BRANCH. It reads run state to answer "verified in this run yet", a different question, and its own docstring warns it must not be consolidated with the static evaluator. Untouched, and no change to `SUCCESS_STATES` is needed since it already equals the sanctioned tuple.
- UNIFYING THE PER-DRIVER STATE CONSTANTS. `agy_runipd.py` re-declares `SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES` and `TERMINAL_STATES` as equal-but-separate objects. That is `rununify`'s extraction, not this plan's; E-06 only asserts the equality so a future drift fails.
- EXTENDING `tests/test_runner_refork_guard.py`'s `Owned` TABLE TO RUNNER-OWNED SYMBOLS. Its contract is "a non-runner module owns this", so it structurally cannot host an `oc_runipd`-owned name (E-04 records why). Making it able to would be a real improvement and belongs in its own item.
- DELETING agy's ORPHANED `_findings_block_reason`. After E-03 nothing calls it, but a cross-driver test requires it to exist (F-14). Removing it means changing that test's contract, which is a wider decision about what cross-driver API symmetry should mean; E-03 annotates it instead.
- THE STATIC EVALUATOR (`check_engine.evaluate_ipd_dependencies`). The function's docstring is explicit that the shared rules live there and "NOTHING of them is re-implemented here", and that consolidating the runtime wait/release semantics into it "would break both". This plan changes only the runtime branch.
- EXTENDING THE FINDINGS GATE TO REVIEW EDGES (F-13). A deliberate existing design decision with its own rationale; changing it is a separate judgement about what a review turn should be blocked on, and bundling it here would conflate "make the intended behavior reachable" with "change the intended behavior".
- WHETHER `reviewed`/`approved` SHOULD BECOME REAL DIRECTORIES. That is a layout decision with wide consequences (every selector, every index, every existing plan's path) and is not needed to fix this: the field already carries the state. Backlog `qzhfk2` covers whether specs should get lifecycle subdirs, which is the same question one tree over.
- RELAXING WHAT AN EXECUTE EDGE REQUIRES. Explicitly counter to the goal; E-02 pins it.
- THE BROADER `rununify` CONSOLIDATION. E-03 removes ONE divergent copy because it blocks this fix; it does not attempt the Set's wider extraction of shared runner logic.

## Scope check

- Over-scope: none. One branch of one predicate, one duplicated function removed, one docstring added, one guard list, and three test modules.
- Scope-Paths justification: `oc_runipd.py` holds `edge_satisfied` and the already-imported reader (E-01, E-02); `agy_runipd.py` holds the divergent local `dependency_status_detailed` that must be DELETED for the fix to reach that host's drain path (E-03, F-9) and the wrapper the deletion orphans (F-14); `runner_shared.py` holds `plan_bucket` (E-05); `tests/test_runner_item_dependencies.py` holds the `_SHARED_NAMES` guard (E-04); `tests/test_oc_runipd.py` holds the `plan_bucket` pinning test (E-05, F-11) and the oc matrix; `tests/test_agy_runipd_cli.py` covers the per-host paths (E-06). NOTE the earlier revision deliberately EXCLUDED `agy_runipd.py` on the false premise that it only binds these symbols; F-9 measured otherwise, so it is now in scope by necessity.
- THE SPEC FILE WAS REMOVED FROM `- Scope-Paths:` AT THIS REVIEW, and the reason matters because the earlier revision's instruction would now MISFIRE. The amendment OQ-04 required has ALREADY LANDED as its own maintainer-authored commit (`faa4c7ec`), so this plan no longer edits the spec. Leaving the path declared would make `aw ipd finalize` demand a `--scope-ack` for a declared-but-unmodified path, and would make the runner announce a spec edit that is not going to happen. If an executor nevertheless finds a spec change necessary, that is an out-of-scope edit to make and justify with `--scope-reason`, not a reason to stop.
- Under-scope, stated rather than left as `none`: this child does not persist or surface the block reason, does not touch the in-queue branch or the static evaluator, does not extend the findings gate to review edges, does not create `reviewed/`/`approved/` directories, does not relax the execute path, does not unify the per-driver state constants, does not extend the refork-guard table to runner-owned symbols, and does not delete agy's orphaned findings wrapper. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the summary line pasted and counts stated. MEASURE YOUR OWN BASELINE FIRST; do not inherit a number from this plan. At this review it was `2 failed, 5640 passed, 3 skipped, 2 xfailed`, both failures pre-existing, out of scope, and REPOSITORY-STATE-DEPENDENT (one asserts a live plan's status that has since advanced; one reads the gitignored `.aw/records/runs/` tree), so yours may legitimately differ again. The criterion is that the AFTER failure set minus YOUR BEFORE set is EMPTY.
- Targeted: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_runner_item_dependencies.py`, `tests/test_runner_refork_guard.py`, and `tests/test_review_findings_cascade.py` (the last because E-03 changes which object its cross-driver assertions exercise; it is NOT expected to need an edit, and if it does, report that rather than editing it silently, since it is not in Scope-Paths).
- THE IDENTITY ASSERTION, pasted: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> True after E-03 (it is False at HEAD).
- THE GUARD-BITES DEMONSTRATION: `test_the_implementation_is_shared_not_copied` FAILING against pre-E-03 code with the new name added, then passing.
- BOTH AGY PATHS exercised (dispatch via the re-exported `dependency_status`, drain via `dependency_status_detailed`), with the honest statement that after E-03 they are the same object so the identity pin is what carries the guarantee.
- THE TERMINAL-DIRECTORY ANTI-REGRESSION PROOF, pasted: a real `executed/` plan whose `- Status:` the shared reader returns `None` for still satisfies an `executed:` edge under BOTH actions (25 such plans exist; F-15).
- A LIVE END-TO-END DEMONSTRATION on BOTH hosts: a `review` action whose external prerequisite is `pending/` + `Status: reviewed` or `approved`, proceeding rather than reporting `dependency-blocked`. If a host cannot be demonstrated, SAY SO PLAINLY rather than inferring from the other. A DEDICATED SYNTHETIC REPOSITORY IS ACCEPTABLE AND PREFERRED for this: the live tree's statuses move (F-3), and a demonstration whose premise expired proves nothing.
- THE PRE-FIX CONTRAST for the measured case, pasted, so the fix is shown to change the outcome.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`); a pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

**THE SPEC AMENDMENT IS DONE. THIS PLAN NO LONGER EDITS A SPEC, AND MUST NOT.** OQ-04 was resolved on 2026-09-07 with option (a), amend first then land, and the maintainer landed that amendment as its own commit, `faa4c7ec` ("spec(25kzda): sanction the review-action dependency relaxation in 2.9"), BEFORE this plan is dispatched. §2.9's edge table is now keyed on the CONSUMING ACTION with two `executed:` rows; the `review` row reads "The target resolves uniquely to an IPD whose state is `executed`, `reviewed`, or `approved`. Terminal execution evidence is NOT required, because a review turn writes no code and therefore cannot be invalidated by an unexecuted prerequisite" (`:376`). §5.4 rules 8 and 9 were amended in lockstep (`:941-942`). So the code change this plan makes is now sanctioned rather than deviant, and the spec file has been REMOVED from `- Scope-Paths:`.

VERIFY THE PRECONDITION, THEN PROCEED; DO NOT RE-AMEND. Before E-01, confirm §2.9 contains the two-row action-keyed table. If it does, the precondition holds and no spec edit is authorized by this plan. If it does NOT, you are running against an unexpected base: refuse and report rather than writing the amendment yourself, because a spec edit inside an execution turn is exactly what option (a) was chosen to avoid.

THE AMENDMENT ALSO CONSTRAINS THE IMPLEMENTATION, so read it as a requirement and not merely as permission. It states that the two rows "must stay distinguishable by the consuming action and by nothing else: not by queue membership, not by which host is running, and not by whether the target happens to be in the current run" (`:388-394`). E-02 satisfies the action clause, E-03 satisfies the host clause, and E-06's in-queue pin satisfies the queue-membership clause. A change that satisfied the review row but violated any of those three would be spec-conformant on its face and spec-violating in substance.

DO NOT EDIT the spec at all, and in particular NEVER its §4.2 finding-code table: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

`edge_satisfied`'s comment at the external-target branch must state the precedence rule E-01 establishes (terminal directory authoritative; otherwise the field) AND the measured reason the terminal half exists (25 `executed/` plans have no readable field, F-15), since that is exactly the reasoning a future reader would otherwise get wrong in the direction that breaks them. `plan_bucket` must GAIN a docstring stating that buckets are DIRECTORIES, readiness is a FIELD, and which members are recognized only defensively (E-05).

The refusal message is operator-facing and should name what it actually read. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: When a plan's directory and its `- Status:` field disagree, which wins?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A TERMINAL DIRECTORY WINS; otherwise the FIELD wins. A plan in `executed/` is executed whatever a stale field claims, because `aw ipd finalize` is what moves it there and the move is the harder-to-forge signal; that matches the anti-fabrication posture `reconcile_disposition` already takes when it trusts the directory over an agent's outcome file. For a NON-TERMINAL directory there is no competing signal at all: `pending/` is where every plan sits from `draft` through `approved`, so the field is the only thing that distinguishes them and reading the directory tells you nothing. The rule is therefore not a compromise between two authorities but a recognition that only one of them carries information in each case.
  MEASURED CONFIRMATION ADDED AT REVIEW, because this answer is now load-bearing rather than merely tidy: 25 of the 454 plans in `executed/` have NO readable `- Status:` at all (24 absent, 1 the multi-word `EXECUTED (approved by maintainer)` form the shared reader returns `None` for), and the identity index reports their status as `''`. For those 25 the directory is not the coarser signal, it is the ONLY signal, and all 25 satisfy an `executed:` edge today. So a "field always wins" reading would break 25 live plans, and a "field wins when present" reading would break the multi-word one. The census also shows the converse case is currently empty: every plan in `superseded/` and `not-executed/` carries the matching field, and no plan in `pending/` carries a terminal field, so the rule is exercised only in the direction described. See F-15.

### OQ-02: Should `plan_bucket` keep listing `reviewed` and `approved`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP THEM AND DOCUMENT THEM; do not delete. This REVERSES the earlier resolution, on measured evidence. The earlier answer ("remove them, it is observably a no-op") rested on a false premise: `tests/test_oc_runipd.py:1818-1840` explicitly asserts `plan_bucket` recognizes all eight names including these two (measured `2 passed`), so deletion breaks a passing test and is not invisible. The trap the earlier answer wanted to remove is real, but the cheap fix for a misleading list is a docstring that says WHY the members exist (defensive recognition of names that do not occur in this layout) and where readiness actually lives, at zero behavioral risk. Deletion would buy nothing beyond that and would spend a test edit plus a caller re-verification to remove a defensive branch. The caller search that the earlier answer demanded was performed at review and found the only `== "executed"` comparisons plus the tuple comparison at `agy_runipd.py:2301`, which E-03 deletes for an independent reason.
  A SECOND MEASURED REASON NOT TO DELETE, found at this review and stronger than the test-edit cost: two non-test callers do not COMPARE the bucket at all, they use it AS A DEFAULT STATUS (`status = bucket or "to-review"`, in each driver's `parse_plan_file`). Removing a member would therefore change a DERIVED STATUS for any plan path containing that segment, not merely skip a comparison, which is a quieter and worse failure than a red test.

### OQ-03: Should the fix live in `edge_satisfied` or in `plan_bucket`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IN `edge_satisfied`. `plan_bucket` answers a narrow and honest question, "which lifecycle directory is this path in", and it answers it correctly; teaching it to read file contents would make a path-inspection helper do IO and would change the meaning of every existing caller's result across ten call sites (re-counted at this review). The defect is that `edge_satisfied` asked `plan_bucket` a question it cannot answer (what is this plan's readiness) rather than that `plan_bucket` answered wrongly. Fixing it at the call site keeps each function honest and confines the change to the one caller whose question was wrong; E-05's docstring addition is documentation hygiene at the helper, not the fix.
  A THIRD CANDIDATE SITE EXISTS AND IS ALSO REJECTED, recorded so an executor does not "improve" on this. `_artifact_owners` already returns `(status, path)` for the same id6 and is already called by this same function for `exists:`/`state:` edges, so reading the status from THERE looks like the smallest change of all. It is not: it rebuilds the whole-repo artifact inventory per call (~260ms measured, versus ~42ms for the `resolve_plan_path` the branch already performs) and it reads through the STRICT `status_set._STATUS_RE` rather than the PERMISSIVE `_read_status` the runners deliberately use, so it would silently narrow which front-matter spellings the runner accepts, against a pinned decision (`tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests`). Measured mitigation for honesty: the two readers agree on all 514 plan records today, so this is a durability and cost argument rather than a live correctness bug.

### OQ-04: Approved spec `25kzda` §2.9 does not sanction the review-action relaxation this plan makes live. Amend the spec first, or proceed and amend after?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-07 BY MAINTAINER RULING: OPTION (a), AMEND SPEC §2.9 FIRST, THEN LAND. **AND THE AMENDMENT HAS NOW LANDED, at `faa4c7ec`, so this question is not merely answered but DISCHARGED.** The `("executed", "reviewed", "approved")` acceptance for a review-action edge IS the intended contract, so option (c) (deleting the two states) is rejected: the relaxation's reasoning holds (a review writes no code and cannot be invalidated by an unexecuted prerequisite) and F-7's serialization is a real cost that falls on 8 currently-pending plans (re-measured at this review; the earlier "nine" counted grep-matching files rather than blocked edges). The spec was amended in a maintainer-authored change that landed BEFORE the code path is made live, so the contract is never in a state where shipped behavior contradicts it, which is what distinguishes (a) from (b).
  WHAT THE LANDED AMENDMENT ACTUALLY SAYS, verified at this review rather than assumed to match the instruction: §2.9's edge table is now keyed on the CONSUMING ACTION and carries two `executed:` rows; the `review` row accepts a target "whose state is `executed`, `reviewed`, or `approved`" with "Terminal execution evidence ... NOT required"; the `execute` row is unchanged and still demands `executed/` plus terminal lint plus finalization evidence; §5.4 rules 8 and 9 were amended in lockstep so they cannot contradict the table; and §2.10's "All surfaces call this evaluator; none reimplement the rules" is intact. The amendment cites run `run-20260904T042705Z-1025943` as the measured cost of the alternative.
  THE AMENDMENT ADDS A CONSTRAINT THE ORIGINAL INSTRUCTION DID NOT, and it is now binding on this plan: the two rows "must stay distinguishable by the consuming action and by nothing else: not by queue membership, not by which host is running, and not by whether the target happens to be in the current run". That is the normative reason E-03 is mandatory rather than tidy (host clause), and the reason E-06 must pin the in-queue path (queue-membership clause).
  CONSEQUENCE FOR THIS PLAN'S SCOPE, changed at this review: because the amendment is already in history, this plan NO LONGER EDITS A SPEC, and the spec file has been REMOVED from `- Scope-Paths:`. Leaving it declared would make `aw ipd finalize` demand a `--scope-ack` for a path the plan was never going to touch, and would make the runner announce a spec edit that will not occur. The earlier revision's "declare it so the edit is announced" instruction was correct when the edit was still this plan's to make and is now stale.
  ORDERING CONSEQUENCE, retained: the amendment is a PRECONDITION. E-01 verifies it is present before changing code; if it is absent the executor is on an unexpected base and must refuse and report rather than writing the amendment itself.
  ALSO NOTE E-06's IN-RUN TWIN, now answered rather than left open. `SUCCESS_STATES = {"executed","reviewed","approved"}` (`oc_runipd.py:327`) is the in-run twin of the on-disk tuple; it ALREADY equals the sanctioned set, and the amendment sanctions both readings, so NO change to it is expected. E-06 states that by inspection rather than editing it (PR-005).
  ORIGINAL ESCALATION RATIONALE, retained for the record: the decision needed was whether the three-state acceptance is the intended contract, and if so whether spec `25kzda` is amended BEFORE this code ships or in the same change.
  WHY IT BLOCKED, retained for the record and no longer current. Spec `25kzda` carried `- Status: approved` and its §2.9 defined an `executed:` edge as satisfied when the target "is in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence"; there was no review-action exception anywhere in the section, while §2.10 stated "All surfaces call this evaluator; none reimplement the rules." The deviation was INERT, because the relaxation was unreachable (F-2), so nothing had ever behaved contrary to the spec. This plan's purpose was to make it reachable, which would have converted a dormant deviation into a live one. An agent must not do that on its own authority: approving a contract change is a human act, and that was a contract change dressed as a bug fix. The maintainer made the change, so the objection is spent.
  WHY I DID NOT RESOLVE IT FROM EVIDENCE. The repository genuinely does not answer it. The code says one thing (three states for a review turn, since before the current shared-predicate refactor), the approved spec says another (one state, unconditionally), and no review record, plan, or history line reconciles them. Choosing either reading would be inventing the maintainer's intent about a public contract.
  WHAT EACH OPTION COST, retained for the record. (a) AMEND THE SPEC FIRST, then execute: correct by the book, and the spec then documents both the relaxation and that readiness is read from the field; costs one extra round trip. (b) PROCEED AND AMEND IN THE SAME CHANGE: one pass, and the spec and code land consistent; but a spec edit inside an execution turn is a wider act than this plan's fence contemplates. (c) DECIDE THE RELAXATION IS WRONG and instead DELETE the two dead states so the code matches the spec: that also fixes the false-advertising refusal message, is a smaller change, and would close backlog `yf9fj9` with the opposite outcome; it costs the review-sweep serialization F-7 describes.
  THE MAINTAINER CHOSE (a) AND EXECUTED IT. The recommendation was (a) or (b) on the grounds that F-7's serialization is a real cost paid on currently-pending plans and the relaxation's reasoning is sound; (c) was a legitimate answer and the choice was the maintainer's.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the changed external-target branch. Show SIX probes: `pending/` + `Status: reviewed` under a review action SATISFIES; `pending/` + `Status: to-review` REFUSES; an absent status in `pending/` REFUSES; a MULTI-WORD status in `pending/` REFUSES; and THE TWO ANTI-REGRESSION PROBES, an `executed/` plan with an ABSENT field and one with a MULTI-WORD field, each SATISFYING under BOTH actions (F-15: 25 real plans are in that state). Quote the comment stating the precedence rule and its measured justification. Confirm by inspection that `_read_status` is the already-imported reader and that no second reader, regex, or `_artifact_owners` call was added. Paste the verification that spec §2.9 carries the two-row action-keyed table (the E-01 precondition).
  - Observed evidence: PASS. The changed branch, the six required probes plus the two anti-regression ones, the 96-probe real-corpus proof, the shared-reader assertion, and the verified spec precondition are pasted below. One HONEST CORRECTION to the plan's census is recorded.
    THE CHANGED BRANCH (`oc_runipd.edge_satisfied`, external-target case; located by SYMBOL). The
    precedence comment and its measured justification are in the source; the operative code is:

    ```python
            bucket = plan_bucket(dep_path)
            allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")
            # PRECEDENCE (depreview 03ie04 E-01, OQ-01): A TERMINAL DIRECTORY IS AUTHORITATIVE; for a
            # NON-TERMINAL directory the `- Status:` FIELD carries the readiness. [...]
            # WHY THE DIRECTORY MUST WIN IN `executed/`, measured and not hypothetical: 24 of the 455
            # plans in `executed/` carry a `- Status:` that `read_front_matter_status` returns None for
            # (all 24 the MULTI-WORD `EXECUTED (approved ...)` form [...]). Every one of them satisfies
            # an `executed:` edge today because the directory decides. [...]
            # WHY THE FIELD MUST WIN IN `pending/`: readiness in this layout is a FIELD, not a
            # directory. [...] Reading the bucket alone therefore made the review-action relaxation
            # above UNREACHABLE [...]
            # `_read_status` is the reader the module ALREADY imports and ALREADY uses for this exact
            # comparison in `reconcile_disposition`'s review branch; do not substitute another. It
            # returns None for an ABSENT and for a MULTI-WORD status alike, and in a NON-TERMINAL
            # directory both must FAIL CLOSED, exactly as an unrecognized bucket does.
            from agent_workflows import run_selection_policy as _policy

            effective = bucket
            if bucket is not None and not _policy.is_in_terminal_directory(str(dep_path)):
                try:
                    field = _read_status(dep_path.read_text(encoding="utf-8"))
                except Exception:
                    field = None
                effective = field
            if effective not in allowed:
                return False, (
                    f"{tok}: external target {edge.id6} is {effective!r} "
                    f"(directory {bucket!r}), needs one of {list(allowed)} "
                    "(it is not in this run, so it cannot become satisfied here)"
                )
            return True, ""
    ```

    THE SIX REQUIRED PROBES, plus the two anti-regression ones, from
    `.aw/state/probes-03ie04/POST-E01.txt` (harness pins `PYTHONPATH` to a chosen tree; see decision
    01-03ie04-D4 for why that matters). PRE-FIX contrast for the same probes is in `PRE-FIX.txt`,
    produced against a pristine `git archive HEAD` tree:

    ```text
    1. review vs pending/ Status: reviewed    action=review   satisfied=True
    2. review vs pending/ Status: approved    action=review   satisfied=True
    3. review vs pending/ Status: to-review   action=review   satisfied=False  executed:prq001: external target prq001 is 'to-review' (directory 'pending'), needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here)
    7a. review vs pending/ status ABSENT      action=review   satisfied=False  ... is None (directory 'pending'), needs one of ['executed', 'reviewed', 'approved'] ...
    7b. review vs pending/ MULTI-WORD status  action=review   satisfied=False  ... is None (directory 'pending'), needs one of ['executed', 'reviewed', 'approved'] ...
    === CASE 8: ANTI-REGRESSION, terminal directory decides (F-15) ===
    8a. review vs executed/ status ABSENT     action=review   satisfied=True
    8b. execute vs executed/ status ABSENT    action=execute  satisfied=True
    8c. review vs executed/ MULTI-WORD status action=review   satisfied=True
    8d. execute vs executed/ MULTI-WORD       action=execute  satisfied=True
    8e. review vs executed/ STALE to-review   action=review   satisfied=True
    8f. execute vs executed/ STALE to-review  action=execute  satisfied=True
    ```

    The SAME rows PRE-FIX (`PRE-FIX.txt`), showing rows 1 and 2 refusing and naming a DIRECTORY:

    ```text
    1. review vs pending/ Status: reviewed    action=review   satisfied=False  executed:prq001: external target prq001 is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here)
    2. review vs pending/ Status: approved    action=review   satisfied=False  (identical message)
    ```

    THE ANTI-REGRESSION PROOF AGAINST THE REAL CORPUS, not a fixture
    (`.aw/state/probes-03ie04/V01-F15.txt`). This is the F-15 claim re-measured at execution:

    ```text
    plans in executed/: 455
    of those, `- Status:` the SHARED reader returns None for: 24
       field ABSENT: 0   field present but MULTI-WORD/unparseable: 24
       of those, carrying a readable `- Id:`: 24
    EVERY ONE must still satisfy an `executed:` edge under BOTH actions on BOTH hosts,
    because the TERMINAL DIRECTORY decides. A field-authoritative fix would break all of them.

    probes: 96   refusals: 0

    sample (id6, the raw field line, what the shared reader returns):
       7ibobm  '- Status: EXECUTED (approved by maintainer 2026-06-30; all steps applied and validated)' reader=None
       rin79g  '- Status: EXECUTED (approved by maintainer 2026-07-01; slug "generalization" confirmed; ...)' reader=None
    ```

    HONEST CORRECTION TO THE PLAN'S CENSUS. The review recorded "25 of 454 (24 absent, 1 multi-word)".
    Re-measured at execution the corpus is 455 plans, of which 24 are unreadable and ALL 24 are the
    MULTI-WORD form; ZERO have an absent field. The plan's CONCLUSION is unaffected (the terminal
    directory must decide, or those plans break), only its count was stale. The source comment now
    states the re-measured census and notes the discrepancy, rather than repeating the review's number.

    THE READER IS THE ALREADY-SHARED ONE, and no second reader, regex, or index call was added.
    Asserted mechanically by `ExternalTargetReadinessMatrixTests::
    test_the_status_field_is_read_with_the_already_shared_reader`, which tokenizes the function body
    (so a comment mentioning a name cannot satisfy it), requires `_read_status`, forbids
    `_artifact_owners` in the `executed:` branch, and pins
    `oc_runipd._read_status is selectors.read_front_matter_status`.

    THE E-01 PRECONDITION, verified BEFORE any code change:

    ```text
    $ git log --oneline -1 --name-only -- .aw/records/specs/*aw-run-deterministic*
    faa4c7ec spec(25kzda): sanction the review-action dependency relaxation in 2.9
    .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
    ```

    and the two-row action-keyed table is present at spec `:373-378`:

    ```text
    | Edge | Consuming action | Satisfied when |
    | `executed:<id6>` | `execute` | ... is in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence. ... |
    | `executed:<id6>` | `review`  | The target resolves uniquely to an IPD whose state is `executed`, `reviewed`, or `approved`. Terminal execution evidence is NOT required, ... |
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste an execute-action edge against a `pending/` + `Status: reviewed` target REFUSING, and against an `executed/` target SATISFYING. Paste a diff or a statement confirming the execute path's behavior is unchanged from today, and state in one sentence why an execute edge legitimately needs the terminal directory (it consumes the prerequisite's work). Paste the `if is_exec` findings-gate line unchanged and state in one sentence that a review edge is therefore not findings-gated. ALSO paste the IN-QUEUE counterpart still refusing: an execute dependent whose in-queue prerequisite carries the derived run status `reviewed` must report `needs one of ['executed', 'substantially-complete']`, which is the same asymmetry one path over. Quote the spec sentence that makes this normative ("distinguishable by the consuming action and by nothing else").
  - Observed evidence: PASS. The execute path still refuses a non-terminal target and its behavior is unchanged; the `if is_exec` findings-gate line is unmodified and its consequence stated; the in-queue counterpart still refuses; the governing spec sentence is quoted.
    THE EXECUTE PATH STILL REFUSES A NON-TERMINAL TARGET, and satisfies a terminal one
    (`.aw/state/probes-03ie04/POST-E01.txt`):

    ```text
    5. execute vs pending/ Status: reviewed   action=execute  satisfied=False  executed:prq001: external target prq001 is 'reviewed' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)
    5b. execute vs pending/ Status: approved  action=execute  satisfied=False  ... is 'approved' (directory 'pending'), needs one of ['executed'] ...
    6. execute vs executed/ Status: executed  action=execute  satisfied=True
    ```

    Also pinned as tests, on BOTH hosts: `ExternalTargetReadinessMatrixTests` rows 5/5b/6/7c/7d, and
    `AgyDependencyPathsAreSharedTests::test_an_execute_edge_is_NOT_relaxed_on_this_host`.

    WHY AN EXECUTE EDGE LEGITIMATELY NEEDS THE TERMINAL DIRECTORY, in one sentence: an execute turn
    consumes its prerequisite's WORK, so a merely `reviewed` or `approved` plan has produced nothing
    to consume and satisfying its edge would dispatch the dependent against a base lacking the commits
    it depends on.

    THE EXECUTE PATH'S BEHAVIOR IS UNCHANGED FROM TODAY. The `allowed` tuple is untouched
    (`("executed",) if is_exec else (...)`), and for an execute edge the only reachable target that
    satisfies it is one in a terminal `executed/` directory, exactly as before: the added field read
    applies ONLY when `not is_in_terminal_directory(...)`, and in that case the pre-fix code refused
    too (bucket `pending` was in neither tuple). Confirmed by the 80-probe matrix contrast
    (`matrix_contrast.py`): of the 16 pre-fix failures, ZERO are execute-vs-non-terminal rows; every
    changed verdict is either a review-action relaxation or an agy DRAIN-path repair.

    THE FINDINGS GATE'S `is_exec` SCOPING IS UNCHANGED, pasted verbatim from
    `dependency_status_detailed`:

    ```python
            if is_exec:
                target = dependency_target_id6(edge) or dep
                why = _findings_block_reason(repo, target)
                if why:
                    _block(dep, why)
    ```

    CONSEQUENCE, stated plainly: a review edge is therefore NOT findings-gated, so E-01's field read is
    the ONLY gate on the review path. That is the existing intended design (F-13), not a regression
    this plan introduces, and it was deliberately not widened.

    THE IN-QUEUE COUNTERPART STILL REFUSES, which is the same asymmetry one path over
    (`.aw/state/probes-03ie04/POST-E01.txt`, and pinned by
    `ExternalTargetReadinessMatrixTests::test_the_in_queue_branch_still_reads_run_state_not_disk`):

    ```text
    in-queue: execute dependent vs run status 'reviewed'   action=execute  satisfied=False  executed:prq001: in-run target prq001 is 'reviewed', needs one of ['executed', 'substantially-complete']
    in-queue: review dependent vs run status 'reviewed'    action=review   satisfied=True
    in-queue: execute dependent vs run status 'executed'   action=execute  satisfied=True
    ```

    THE SPEC SENTENCE THAT MAKES THIS NORMATIVE, quoted from `25kzda` 2.9 (`:388-394`): the two rows
    "must stay distinguishable by the consuming action and by nothing else: not by queue membership,
    not by which host is running, and not by whether the target happens to be in the current run."
    It is also quoted at the code site so the constraint travels with the change.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `agy.dependency_status_detailed is oc.dependency_status_detailed` -> True (and the pre-fix `False` for contrast). Paste the deletion diff and the re-export line. Paste a probe showing agy's DRAIN path now resolves a TYPED edge (`executed:<id6>`) instead of reporting `no plan resolves to this id6`. Paste a probe showing agy's drain path now ROUTES AN `orchestrate` ITEM through the shared decider (the copy had no such clause). State what you found about the reason-map KEY shape (`dep_id6` vs `dep_token`) and name any caller or test affected. Paste the annotation added to agy's now-uncalled `_findings_block_reason` and state that its two former call sites were both inside the deleted function.
  - Observed evidence: PASS. Identity True after (False before), the deletion and re-export pasted, agy's DRAIN path now resolves a TYPED edge and routes an `orchestrate` item, the reason-map key shape confirmed unaffected by execution, and the orphaned wrapper annotated rather than deleted.
    THE IDENTITY, before and after. POST-FIX (`.aw/state/probes-03ie04/V03.txt`):

    ```text
    agy.dependency_status_detailed is oc.dependency_status_detailed -> True
    agy.dependency_status is oc.dependency_status -> True
    ```

    PRE-FIX, the same probe against a pristine HEAD tree (`V03-PREFIX.txt`):

    ```text
    agy.dependency_status_detailed is oc.dependency_status_detailed -> False
    agy.dependency_status is oc.dependency_status -> True
    ```

    THE DELETION AND THE RE-EXPORT. `agy_runipd.py` lost 57 lines (the whole local
    `def dependency_status_detailed`) and gained the re-export in the import block, in the
    `as <same-name>` form that block uses deliberately so an autoformatter cannot strip it:

    ```python
        dependency_status as dependency_status,
        # depreview 03ie04 E-03: `dependency_status_detailed` is RE-EXPORTED here, not defined. [...]
        # Measured before the deletion:
        # `agy.dependency_status_detailed is oc.dependency_status_detailed` -> False. The copy was also
        # BROKEN in three ways [...]
        dependency_status_detailed as dependency_status_detailed,
    ```

    The module note below it now covers BOTH names and records why the `_detailed` copy survived the
    earlier cleanup (`_SHARED_NAMES` never listed it).

    THE DRAIN PATH NOW RESOLVES A TYPED EDGE. POST-FIX (`V03.txt`):

    ```text
    === (a) agy DRAIN path resolves a TYPED `executed:<id6>` edge ===
        action=execute  satisfied=True missing=[] reasons={}
        action=review   satisfied=True missing=[] reasons={}
    ```

    PRE-FIX, same fixture (`V03-PREFIX.txt`) - the copy used the raw token as an id6:

    ```text
        action=execute  satisfied=False missing=['executed:depaaa'] reasons={'executed:depaaa': 'executed:depaaa: no plan resolves to this id6 in the repo'}
        action=review   satisfied=False missing=['executed:depaaa'] reasons={'executed:depaaa': 'executed:depaaa: no plan resolves to this id6 in the repo'}
    ```

    THE DRAIN PATH NOW ROUTES AN `orchestrate` ITEM through the shared decider. POST-FIX, with an
    Order-0 orchestrator whose declared child is unfinished:

    ```text
    === (b) agy DRAIN path ROUTES an `orchestrate` item through the shared decider ===
        orchestrator with an UNFINISHED child: satisfied=False missing=['executed:child1']
          executed:child1 -> orchestrator waits for child child1 of set 'probe' to execute (currently queued)
        a reason naming a CHILD can ONLY come from the orchestrator clause
        oc verdict identical: True
    ```

    PRE-FIX the same fixture returned `satisfied=True missing=[]` with NO reason, i.e. the orchestrator
    was admitted without consulting `decide_orchestrator_dispatch` at all, and oc disagreed
    (`oc verdict identical: False`). Pinned as a test by `AgyDependencyPathsAreSharedTests::
    test_the_drain_path_routes_an_orchestrate_item_through_the_shared_decider`.

    THE REASON-MAP KEY SHAPE: UNAFFECTED, and this was verified by EXECUTION rather than reading. The
    shared implementation keys reasons by the token AS DECLARED (`dep_token`), the deleted copy
    documented `dep_id6`; the only cross-driver assertion on key shape
    (`tests/test_review_findings_cascade.py::BlockLegibilityTests::
    test_reason_map_names_the_finding_id_and_severity`) uses a BARE `depaaa` dependency where token and
    id6 are identical. NO test file needed an edit for the key shape, exactly as the plan predicted:

    ```text
    $ python3 -m pytest tests/test_review_findings_cascade.py tests/test_runner_item_dependencies.py \
        tests/test_agy_runipd_cli.py tests/test_oc_runipd.py tests/test_runner_refork_guard.py \
        tests/test_runner_shared.py -o addopts="" -q
    361 passed in 33.14s
    ```

    `tests/test_review_findings_cascade.py` and `tests/test_runner_refork_guard.py` were NOT modified
    (`git diff --name-only` lists neither), which the plan's fence requires.

    THE ORPHANED WRAPPER IS ANNOTATED, NOT DELETED. Its two former call sites were BOTH inside the
    deleted function, so it now has ZERO call sites in this module (`V03.txt` section (d): `call sites
    of _findings_block_reason in agy_runipd.py: 0`, while `hasattr(agy, '_findings_block_reason')` is
    True and the source still names `subject_gating_blocks`, which is what
    `test_review_findings_cascade.py::SharedPredicateTests` requires). The added annotation:

    ```text
        RETAINED FOR THE CROSS-DRIVER API-SYMMETRY CONTRACT, AND NOT CALLED FROM THIS MODULE (depreview
        03ie04 E-03). Its only two call sites were both inside the local `dependency_status_detailed`
        copy that E-03 DELETED, so the live gate now runs in `oc_runipd` through the re-exported
        implementation. It is kept rather than deleted because
        `tests/test_review_findings_cascade.py::SharedPredicateTests` asserts BOTH that this attribute
        exists on this module and that this module's source names `subject_gating_blocks`; removing it
        would change that test's contract, which is a wider decision [...] Do NOT read it as a second
        implementation of the gate: there is one, in `review_findings.subject_gating_blocks`.
    ```

    Pinned by `AgyDependencyPathsAreSharedTests::test_the_retained_findings_wrapper_is_uncalled_but_present`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `_SHARED_NAMES` containing `dependency_status_detailed`. Paste the guard FAILING against pre-E-03 code and then PASSING after it, so it is shown to bite rather than merely be green. Paste the comment recording why `tests/test_runner_refork_guard.py`'s `Owned` table cannot host this symbol, and confirm that file was NOT modified.
  - Observed evidence: PASS. `_SHARED_NAMES` now names `dependency_status_detailed`; the guard is shown FAILING against pre-E-03 code and PASSING after; the refork-guard rationale is recorded as a comment and that file was NOT modified.
    `_SHARED_NAMES` NOW CONTAINS THE NAME (`tests/test_runner_item_dependencies.py`):

    ```python
        _SHARED_NAMES = (
            "_read_item_dependencies",
            "parse_dependency_token",
            "dependency_target_id6",
            "edge_satisfied",
            "dependency_status",
            # depreview 03ie04 E-04: the `_detailed` sibling was MISSING from this list, which is exactly
            # why the guard below passed over agy's real copy of it. Both names are required.
            "dependency_status_detailed",
            "dependency_reasons",
            "dependency_depth",
            "queue_sort_key",
            "cascade_dependency_blocked",
            "preflight_dependency_findings",
            "DEPENDENCY_FATAL_RULES",
        )
    ```

    THE GUARD BITES: run against PRE-E-03 code (my post-fix `oc_runipd.py` + `runner_shared.py` + this
    test file, with agy STILL carrying the copy), it FAILS
    (`.aw/state/probes-03ie04/V04.txt`):

    ```text
    --- 2. the guard RUN AGAINST PRE-E-03 agy_runipd.py, with the name added: FAILS ---
                with self.subTest(name=name):
    >               self.assertIs(
                        getattr(agy_runipd, name),
                        getattr(oc_runipd, name),
                        f"{name} is a COPY in agy_runipd; it must be the shared object",
                    )
    E               AssertionError: <function dependency_status_detailed at 0x7351efcf64b0> is not <function dependency_status_detailed at 0x7351efced0c0> : dependency_status_detailed is a COPY in agy_runipd; it must be the shared object
    FAILED tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests::test_the_implementation_is_shared_not_copied
    1 failed in 0.54s
    ```

    AND PASSES after E-03:

    ```text
    --- 3. the SAME guard after E-03 deleted the copy: PASSES ---
    .......                                                                  [100%]
    7 passed in 0.17s
    ```

    WHY THE REFORK-GUARD TABLE CANNOT HOST THIS SYMBOL is recorded as a comment at the
    `_SHARED_NAMES` definition, re-verified rather than copied from the plan: `REFORK_TABLE`'s `Owned`
    contract is "a NON-RUNNER module owns this symbol; no runner may re-define it", every row's owner
    is `render_stream`/`runner_shared`/`selectors`, and naming `oc_runipd` as an owner would make its
    AST half forbid oc's own definition. The comment also records the guard's LIMIT (identity catches a
    re-defined copy, not a copy assigned over the re-export at import time; that residual hole is
    accepted, as no such pattern exists in either driver today).

    `tests/test_runner_refork_guard.py` WAS NOT MODIFIED:

    ```text
    $ git diff --name-only -- tests/test_runner_refork_guard.py
    (no output)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `plan_bucket`'s NEW docstring (it had none). Paste `PlanBucketRecognitionTests` PASSING (or, if members were removed, the updated test plus the re-verified caller search naming every call site and its comparison, INCLUDING the two `status = bucket or "to-review"` sites that consume a bucket as a default status rather than comparing it). Paste a probe showing a real path's bucket is UNCHANGED for each member.
  - Observed evidence: PASS. `plan_bucket` now HAS a docstring (it had none), no member was removed, the pinning test passes alongside two new pins, no real path's bucket changed, and the caller search was re-verified at this HEAD. One OUT-OF-FENCE edit is disclosed.
    `plan_bucket` NOW HAS A DOCSTRING (it had NONE; `plan_bucket.__doc__` was `None` at HEAD). Pasted
    from `.aw/state/probes-03ie04/V05.txt`:

    ```text
    Which lifecycle DIRECTORY is this plan path in? Returns the segment name, or None.

    A BUCKET IS A DIRECTORY; READINESS IS A FIELD. That distinction is the whole contract of this
    function and getting it wrong has already cost one defect (depreview 03ie04). In this layout a
    plan STAYS in `pending/` for its entire non-terminal life, moving through `- Status: draft` ->
    `to-review` -> `reviewed` -> `approved`, and only a TERMINAL state moves the file. So a caller
    that wants to know "is this plan reviewed/approved yet" CANNOT learn it here: it must read the
    `- Status:` front-matter field with `selectors.read_front_matter_status`. `oc_runipd.edge_satisfied`
    is the worked precedent, and the reason it had to change: it compared this function's result
    against `("executed", "reviewed", "approved")`, which made two thirds of that tuple DEAD CODE
    because every non-terminal plan buckets as `pending`.

    `reviewed`, `approved` and `active` ARE RECOGNIZED DEFENSIVELY AND DO NOT OCCUR IN THIS LAYOUT.
    `.aw/records/plans/` holds only `executed`, `not-executed`, `pending`, `reusable` and
    `superseded`, and `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` corroborates that in code by
    naming exactly the four terminal ones [...] They are kept rather than removed because the members
    are PINNED by `tests/test_oc_runipd.py::PlanBucketRecognitionTests` and because two callers (each
    driver's `parse_plan_file`) consume the result AS a default status (`status = bucket or
    "to-review"`) rather than comparing it, so deleting a member would silently change a DERIVED
    STATUS rather than merely skip a comparison.

    This function does no IO and must not learn to [...] (OQ-03).
    ```

    NO MEMBERS WERE REMOVED, so the pinning test needed no change, and it PASSES together with two new
    pins added in the same class:

    ```text
    $ python3 -m pytest tests/test_oc_runipd.py::PlanBucketRecognitionTests -o addopts="" -q
    ....                                                                     [100%]
    4 passed in 0.23s
    ```

    NO REAL PATH'S BUCKET CHANGED, and every member still resolves (`V05.txt`):

    ```text
    === every member still resolves for a synthetic path (no behavior change) ===
       executed      -> 'executed'   OK
       active        -> 'active'   OK
       pending       -> 'pending'   OK
       reviewed      -> 'reviewed'   OK
       approved      -> 'approved'   OK
       reusable      -> 'reusable'   OK
       superseded    -> 'superseded'   OK
       not-executed  -> 'not-executed'   OK
       unknown segment -> None (must be None)
    === real paths in THIS repository are unchanged ===
       pending       -> 'pending'
       executed      -> 'executed'
       superseded    -> 'superseded'
       not-executed  -> 'not-executed'
    === the corroborating layout fact cited in the docstring ===
       run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS = ('/executed/', '/superseded/', '/not-executed/', '/reusable/')
       directories that actually exist under .aw/records/plans/:
          ['executed', 'not-executed', 'pending', 'reusable', 'superseded']
    ```

    THE CALLER SEARCH, RE-VERIFIED AT THIS HEAD as the plan demands rather than trusted
    (`.aw/state/probes-03ie04/V05-callers.txt`). EIGHT call sites, not the plan's nine, because E-03
    deleted one:

    ```text
    agent_workflows/agy_runipd.py:1488:        bucket = plan_bucket(path)
    agent_workflows/agy_runipd.py:3151:        bucket = plan_bucket(current_plan)
    agent_workflows/agy_runipd.py:4040:            if plan_bucket(path) == "executed":
    agent_workflows/oc_runipd.py:1178:                bucket = plan_bucket(plan)
    agent_workflows/oc_runipd.py:2243:        bucket = plan_bucket(path)
    agent_workflows/oc_runipd.py:3387:        bucket = plan_bucket(dep_path)
    agent_workflows/oc_runipd.py:5944:        bucket = plan_bucket(current_plan)
    agent_workflows/oc_runipd.py:6853:            if plan_bucket(path) == "executed":

    === every EQUALITY/membership comparison against a bucket value ===
    oc_runipd.py:1186:            if bucket != "executed":
    oc_runipd.py:5947:    if bucket == "executed":
    oc_runipd.py:6853:            if plan_bucket(path) == "executed":
    agy_runipd.py:3154:    if bucket == "executed":
    agy_runipd.py:4040:            if plan_bucket(path) == "executed":

    === the two sites that use a bucket AS a default status ===
    agy_runipd.py:1489:        status = bucket or "to-review"
    oc_runipd.py:2244:        status = bucket or "to-review"
    ```

    So the ONLY remaining comparisons are against `"executed"`, a genuine directory: the
    `("executed","reviewed","approved")` tuple comparison the plan flagged at `agy_runipd.py:2301` is
    GONE with the deleted copy. That absence is now PINNED by the new
    `PlanBucketRecognitionTests::test_no_caller_compares_a_bucket_to_a_non_terminal_member`, which
    fails against pre-fix code:

    ```text
    E  AssertionError: <re.Match object; span=(71859, 71908), match='bucket not in ("executed", "reviewed", "approved"' > is not None : agy_runipd compares a plan_bucket() result against a non-terminal member; readiness lives in the `- Status:` field, not in a directory name
    FAILED tests/test_oc_runipd.py::PlanBucketRecognitionTests::test_the_docstring_states_that_a_bucket_is_not_a_readiness
    FAILED tests/test_oc_runipd.py::PlanBucketRecognitionTests::test_no_caller_compares_a_bucket_to_a_non_terminal_member
    2 failed, 2 passed in 0.40s
    ```

    OUT-OF-FENCE EDIT REQUIRED BY THIS ITEM, disclosed here and in decision 01-03ie04-D3: adding the
    docstring BREAKS `tests/test_runner_shared.py::PureMoveFingerprintTests::
    test_every_clean_symbol_is_a_STRICT_fingerprint_match`, which compares `plan_bucket`'s full AST
    against a committed pre-move capture. Measured, the docstring is the ENTIRE delta:

    ```text
    HEAD fingerprint == fixture:       True
    MINE fingerprint == fixture:      False
    MINE minus docstring == fixture:  True
    ```

    Resolved in that guard's own enumerated-subtraction idiom rather than by weakening it: a
    `DOCUMENTED_SINCE_MOVE = ("plan_bucket",)` list plus `_without_docstring`, which removes ONLY a
    leading string expression so every remaining token must still match; plus a new
    `test_a_documented_symbol_is_still_held_to_its_executable_body` proving the exemption is narrow
    (the symbol must really have a docstring, must really fail the STRICT comparison, and an added
    executable statement must STILL be detected). The fixture was NOT re-captured, because its own
    comments make it a record of the pre-move source at HEAD `1ecc5891`.

    ```text
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    44 passed in 11.86s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of all EIGHT matrix cases, including the terminal-directory anti-regression case. Paste the SYNTHETIC measured-case fixture SATISFYING, AND the same fixture against the PRE-FIX code REFUSING with the original message; confirm no test depends on a live plan's mutable status. Paste both agy paths exercised, the identity pinned, and the docstring stating that after E-03 they are one object so the identity is what carries the guarantee. Paste the in-queue-path test proving that branch is unchanged, and state explicitly that `SUCCESS_STATES` needed NO change because it already equals the sanctioned tuple (paste the equality). Paste the per-driver constant equality assertion (`agy.SUCCESS_STATES == oc.SUCCESS_STATES` while `is` is False). Paste a real review run on BOTH hosts, or say plainly which host could not be demonstrated; a synthetic repository is acceptable and preferred. Paste YOUR OWN freshly measured BEFORE baseline and the AFTER summary, and show the AFTER-minus-BEFORE failure set is EMPTY.
  - Observed evidence: PASS. All 20 matrix rows x 2 hosts x 2 entry points (80 probes) pass, against 16 failures pre-fix; the measured case is pinned synthetically; both agy paths and the identity are pinned; the in-queue path and `SUCCESS_STATES` are proven unchanged; a live end-to-end run is shown on BOTH hosts; the bare-suite delta is EMPTY.
    ALL MATRIX CASES PASS, AND THE PRE-FIX CONTRAST IS MEASURED. The matrix is 20 rows x 2 hosts x 2
    entry points = 80 probes, driven straight from the test class's own `MATRIX` table so the recorded
    contrast and the committed test cannot disagree (`.aw/worktrees/03ie04-scratch/matrix_contrast.py`).

    PRE-FIX, against a pristine `git archive HEAD` tree:

    ```text
    FAIL oc  dependency_status            review vs pending/ + reviewed            want=True got=False
    FAIL oc  dependency_status_detailed   review vs pending/ + reviewed            want=True got=False
    FAIL agy dependency_status            review vs pending/ + reviewed            want=True got=False
    FAIL agy dependency_status_detailed   review vs pending/ + reviewed            want=True got=False
    FAIL oc  dependency_status            review vs pending/ + approved            want=True got=False
    FAIL oc  dependency_status_detailed   review vs pending/ + approved            want=True got=False
    FAIL agy dependency_status            review vs pending/ + approved            want=True got=False
    FAIL agy dependency_status_detailed   review vs pending/ + approved            want=True got=False
    FAIL agy dependency_status_detailed   review vs executed/ + executed           want=True got=False
    FAIL agy dependency_status_detailed   execute vs executed/ + executed          want=True got=False
    FAIL agy dependency_status_detailed   review vs executed/ + absent             want=True got=False
    FAIL agy dependency_status_detailed   execute vs executed/ + absent            want=True got=False
    FAIL agy dependency_status_detailed   review vs executed/ + multi-word         want=True got=False
    FAIL agy dependency_status_detailed   execute vs executed/ + multi-word        want=True got=False
    FAIL agy dependency_status_detailed   review vs executed/ + stale to-review    want=True got=False
    FAIL agy dependency_status_detailed   execute vs executed/ + stale to-review   want=True got=False

    rows=20 probes=80 failures=16
    ```

    The first 8 failures are the review-action relaxation being unreachable; the last 8 are agy's DRAIN
    path failing on a TYPED token, i.e. F-9's broken copy. POST-FIX:

    ```text
    rows=20 probes=80 failures=0
    ```

    THE EIGHTH (ANTI-REGRESSION) CASE IS IN THE TABLE and is proven against the REAL corpus too; see
    V-01's 96-probe / 0-refusal measurement over the 24 `executed/` plans whose field the shared reader
    returns None for.

    THE MEASURED CASE IS PINNED WITH SYNTHETIC FIXTURES, never against a live plan's mutable status
    (`ExternalTargetReadinessMatrixTests::test_the_measured_case_now_satisfies_and_names_what_it_read`
    and `::test_the_refusal_message_names_the_field_it_actually_read`). `tm2cz8` is named nowhere in
    any test; it was `reviewed` when the defect was filed and is `approved` now, which is exactly why.

    BOTH AGY PATHS ARE EXERCISED and the IDENTITY is pinned, with the honest statement in the test's own
    docstring: after E-03 both paths call the SAME object, so "they agree" is true BY CONSTRUCTION and
    the identity assertion is what carries the guarantee, while the behavioral sweep catches a re-fork
    that kept the name. See `test_the_matrix_holds_on_both_hosts_and_through_both_entry_points` and
    `AgyDependencyPathsAreSharedTests::test_both_dependency_entry_points_are_the_shared_objects`.

    THE IN-QUEUE PATH IS PROVEN UNCHANGED (`test_the_in_queue_branch_still_reads_run_state_not_disk`),
    including that its refusal comes from the in-queue branch and not from disk. AND `SUCCESS_STATES`
    NEEDED NO CHANGE, confirmed by inspection and asserted rather than argued
    (`test_the_in_run_success_states_equal_the_sanctioned_on_disk_tuple`):

    ```text
    oc.SUCCESS_STATES            -> ['approved', 'executed', 'reviewed']   (equals the sanctioned tuple)
    oc.EXECUTION_SUCCESS_STATES  -> ['executed', 'substantially-complete']
    ```

    THE PER-DRIVER CONSTANT EQUALITY, asserted so a future divergence fails a test
    (`test_the_per_driver_state_constants_are_equal_even_though_not_shared`); measured values:

    ```text
    agy.SUCCESS_STATES is oc.SUCCESS_STATES -> False | == -> True
    ```

    A LIVE END-TO-END DEMONSTRATION ON BOTH HOSTS, through the SAME functions the dispatch loop and the
    drain path call, with the plan discovered and the action derived by the drivers' own
    `discover_plans`/`build_dynamic_manifest`/`action_for` (`.aw/state/probes-03ie04/V06-live.txt`).
    PRE-FIX, which reproduces the 2026-09-07 refusal verbatim:

    ```text
    --- prerequisite prq001 is `pending/` + `- Status: reviewed` (EXTERNAL to the queue) ---
        [oc ] action=review  deps=['executed:prq001']
        [oc ] preflight: PASSED
        [oc ] dependency-blocked: ['executed:prq001']
        [oc ]   executed:prq001 -> executed:prq001: external target prq001 is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here)
        [agy] dependency-blocked: ['executed:prq001']
        [agy]   executed:prq001 -> executed:prq001: no plan resolves to this id6 in the repo
    ```

    POST-FIX, both hosts, for a prerequisite that is `reviewed` AND for one that is `approved`:

    ```text
    --- prerequisite prq001 is `pending/` + `- Status: reviewed` (EXTERNAL to the queue) ---
        [oc ] action=review  preflight: PASSED   DISPATCHED: the review turn would run
        [agy] action=review  preflight: PASSED   DISPATCHED: the review turn would run
    --- prerequisite prq001 is `pending/` + `- Status: approved` (EXTERNAL to the queue) ---
        [oc ] action=review  preflight: PASSED   DISPATCHED: the review turn would run
        [agy] action=review  preflight: PASSED   DISPATCHED: the review turn would run
    ```

    AND THE CONTROL still refuses on both hosts, so the demonstration is discriminating rather than
    vacuous:

    ```text
    --- prerequisite prq001 is `pending/` + `- Status: to-review` (EXTERNAL to the queue) ---
        [oc ] dependency-blocked: executed:prq001: external target prq001 is 'to-review' (directory 'pending'), needs one of ['executed', 'reviewed', 'approved'] ...
        [agy] dependency-blocked: executed:prq001: external target prq001 is 'to-review' (directory 'pending'), needs one of ['executed', 'reviewed', 'approved'] ...
    ```

    A synthetic repository was used, which the plan names as acceptable and preferred. BOTH hosts were
    demonstrated; neither had to be inferred from the other.

    THE BARE-SUITE DELTA, against a baseline I measured MYSELF (`.aw/state/probes-03ie04/V06-delta.txt`).
    A. PRISTINE BEFORE, in a clean `git archive HEAD` checkout, `AW_EXECUTION_ROLE` unset:

    ```text
    FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today
    1 failed, 5656 passed, 3 skipped, 2 xfailed in 45.99s
    ```

    B. AFTER, all edits applied, same conditions:

    ```text
    FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today
    1 failed, 5678 passed, 3 skipped, 2 xfailed in 49.54s
    ```

    AFTER-minus-BEFORE failure set is EMPTY (`comm -13` over the two sorted FAILED lists produced no
    output). Passing count 5656 -> 5678, +22, all of them the new pins. The single shared failure is
    pre-existing, out of scope, and repository-state-dependent (it asserts that no pending plan is
    refused on its verdict and names the live plan `32ij2j`).

    ENVIRONMENTAL NOTE, disclosed rather than hidden (decision 01-03ie04-D2). Run INSIDE this worker
    lane WITHOUT unsetting the driver's `AW_EXECUTION_ROLE=worker`, the same pristine tree reports
    `18 failed, 5639 passed`: 17 extra failures are the lifecycle role guard refusing `aw ipd
    begin/finalize` inside test subprocesses, not defects in the base or in this change. Both baselines
    are recorded so the number cannot be mistaken for either.

    EXIT CODES WERE MEASURED UNPIPED, as the plan requires: `python3 -m pytest > file 2>&1; echo $?`
    -> `EXIT=1` for the after-run (the one pre-existing failure), and the pinned-hook lint/format
    checks reported `PINNED_FORMAT=0` / `PINNED_LINT=0` with `ruff 0.4.4`, the version
    `.pre-commit-config.yaml` pins (the locally installed `ruff 0.16.3` reformats pre-existing blocks in
    files I did not otherwise touch, so the pinned version is the one that governs).

    `aw sanitize --agent` CLEAN:

    ```text
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the MEASURED refusal first as a pre-fix contrast (the real one, 2026-09-07: `aw oc run orchprobe` refused with `check.ipd-dependency-findings-blocked` naming `executed:8tgg6g` and `executed:r2i1b1` while every queued item was a review turn), then paste the same selection succeeding after the change. Paste a second case proving an EXECUTE-action queue with an unresolved blocker finding is STILL refused, so the fix narrowed nothing it should not. Show both hosts. Include a mutation check: revert the phase derivation, show the review-queue case refuses again, restore it.
  - Observed evidence: PASS ON THE GOAL, WITH THE MECHANISM CHANGED AND DISCLOSED. A review-only selection is admitted on both hosts while an execute-action queue with an unresolved blocker is still refused, with a mutation check proving the behavior load-bearing. The `phase` argument was NOT added; measurement shows it cannot gate this. See decision 01-03ie04-D1.
    READ E-07's EXECUTION NOTE AND DECISION 01-03ie04-D1 FIRST: the GOAL was met and is pinned, but the
    `phase` MECHANISM this item names was NOT implemented, because measurement shows it cannot produce
    the goal. The evidence below is therefore organized as: the negative finding about `phase`, the
    fix that actually carries the behavior, and the pins V-07 asks for.

    THE PRE-FIX CONTRAST, and an honest correction to F-9. F-9's measured refusal (`aw oc run
    orchprobe` over four review turns, refused by `check.ipd-dependency-findings-blocked` naming
    `executed:8tgg6g` and `executed:r2i1b1`) was ALREADY FIXED at this plan's base by commit
    `5699c6ad`, "fix(deps): exempt a review turn from the dependency findings gate, per spec 2.9"
    (2026-09-07 22:37, an ancestor of HEAD `fb447ecc`; `git merge-base --is-ancestor` confirms). Its
    commit message cites the SAME refusal. So I could not re-measure that exact refusal as a live
    pre-fix contrast, and I will not paste a refusal I did not observe. Instead I reproduced the DEFECT
    CLASS in a synthetic repository with the findings gate enabled and an unresolved high finding
    against the prerequisite (`.aw/state/probes-03ie04/E07.txt`):

    ```text
    === the gate is ENABLED and the target CARRIES an unresolved blocker ===
    --- REVIEW-action dependent (`- Status: to-review`) ---
    [oc ] review dependent vs pending/reviewed+blocker   phase=None             -> OK (no findings)
    [oc ] review dependent vs pending/reviewed+blocker   phase=pre-execution    -> OK (no findings)
    [oc ] review dependent vs pending/reviewed+blocker   phase=review-readiness -> OK (no findings)
    [agy] review dependent vs pending/reviewed+blocker   phase=None             -> OK (no findings)
    [agy] review dependent vs pending/reviewed+blocker   phase=pre-execution    -> OK (no findings)
    [agy] review dependent vs pending/reviewed+blocker   phase=review-readiness -> OK (no findings)

    --- EXECUTE-action dependent (`- Status: approved`), SAME target ---
    [oc ] execute dependent vs executed/executed+blocker phase=None             -> REFUSED: DriverError: dependency preflight failed: run refused before any session started ... at phase 'pre-execution':
    [oc ] execute dependent vs executed/executed+blocker phase=review-readiness -> REFUSED: DriverError: ... at phase 'review-readiness':
    [agy] execute dependent vs executed/executed+blocker phase=None             -> REFUSED: DriverError: ... at phase 'pre-execution':
    [agy] execute dependent vs executed/executed+blocker phase=review-readiness -> REFUSED: DriverError: ... at phase 'review-readiness':
    ```

    READ THE `phase` COLUMN: it changes NOTHING, in either direction, which is the negative finding.
    The reason is structural and was measured by AST rather than reasoned: inside
    `check_engine.evaluate_ipd_dependencies` the only references to `phase`/`blocking` are
    `blocking = phase in _DEP_BLOCKING_PHASES` and ONE `if blocking:` gating the `unresolved` SCAFFOLD
    SENTINEL finding. `_DEP_BLOCKING_PHASES` is `['pre-execution', 'pre-transition', 'review-finalize',
    'review-readiness']`, so every phase a review turn could claim is already in it; the only values
    that would change behavior are `check`/`author`, which relax the sentinel for the WHOLE selection,
    a widening this item never asked for and which V-07's own "narrowed nothing it should not" clause
    forbids.

    WHAT ACTUALLY CARRIES THE FIX is the CONSUMING ACTION, threaded to the shared evaluator:
    `evaluate_ipd_dependencies(..., actions=...)`, the findings rule guarded by
    `if e.kind == "executed" and (actions or {}).get(ps) != "review"`, and
    `preflight_dependency_findings` passing `actions=_consuming_actions_for(plans)` derived from the
    same `runner_shared.action_for` the queue builder uses.

    THE SAME SELECTION SUCCEEDING AFTER THE CHANGE, at the runner level, on BOTH hosts, pinned as
    `ReviewQueuePreflightTests::test_a_review_queue_is_admitted_despite_the_targets_open_findings`
    (asserts `enforce_dependency_preflight(repo, [dependent]) == []`).

    THE SECOND CASE V-07 DEMANDS - an EXECUTE-action queue with an unresolved blocker finding is STILL
    REFUSED - pinned as `::test_an_execute_queue_is_still_refused_by_the_findings_gate`, asserting the
    raised `DriverError` names `check.ipd-dependency-findings-blocked`. BOTH HOSTS in both tests, via
    the `_DRIVERS` sweep.

    THE MUTATION CHECK, which is what V-07 wanted from "revert the phase derivation, show it refuses
    again, restore it", adapted to the mechanism that actually carries the behavior
    (`::test_removing_the_action_input_re_blocks_the_review_queue`): the review-only selection passes;
    `_consuming_actions_for` is then neutralized to `lambda plans: {}`; the SAME selection is REFUSED
    with `check.ipd-dependency-findings-blocked`; the function is restored and it passes again. This
    proves the admitting behavior is load-bearing rather than the fixture being toothless.

    THE NEGATIVE FINDING IS ITSELF PINNED, so nobody re-adds the argument expecting it to gate:
    `::test_the_phase_argument_cannot_discriminate_a_review_turn` asserts that an execute-action queue
    is refused at EVERY member of `_DEP_BLOCKING_PHASES`.

    ```text
    $ python3 -m pytest tests/test_runner_item_dependencies.py -o addopts="" -q
    72 passed in 2.35s
    ```

    AND THESE PINS BITE: against pre-fix production code, 5 of the new
    `tests/test_runner_item_dependencies.py` tests fail (see V-06's contrast), and 7 of the 8 new
    `AgyDependencyPathsAreSharedTests` fail.

    OPEN FOR HUMAN REVIEW, stated plainly rather than buried: I did not write the argument E-07's prose
    names. If the intent was to make `phase` a genuine review/execute discriminator INSIDE
    `evaluate_ipd_dependencies` (i.e. more rules made phase-conditional), that is a spec-level change to
    what a phase means and belongs in its own plan; decision 01-03ie04-D1 records the reasoning and
    asks for that ruling.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**OQ-04 IS RESOLVED AND ITS PRECONDITION IS DISCHARGED.** The blocking question was answered by maintainer ruling on 2026-09-07 and the spec amendment it required LANDED at `faa4c7ec`, before this plan runs. So nothing blocks the pre-execution lint on that count. E-01 still verifies the amendment is present as its first act, because a plan that assumes its own precondition is the failure mode this note replaces.

Execution requires explicit human approval (`- Status: approved`).

Scope fence: touch ONLY the six paths in `Scope-Paths`. Do NOT relax what an EXECUTE edge requires. Do NOT modify the in-queue dependency branch or `check_engine.evaluate_ipd_dependencies`. Do NOT make `plan_bucket` read file contents (OQ-03). Do NOT create `reviewed/` or `approved/` directories. Do NOT extend the findings gate to review edges. Do NOT edit spec `25kzda` AT ALL: its amendment already landed as a separate maintainer commit, so a further spec edit from this plan would be an unauthorized second contract change, and NEVER its §4.2 finding-code table. Do NOT edit `tests/test_runner_refork_guard.py` or `tests/test_review_findings_cascade.py`, both deliberately outside the fence (E-04 and F-14 record why each is expected to need no change). If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and `oc_runipd.py` is the highest-contention file in it: run `aw runs` before starting, and if it is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. At this review it was `2 failed, 5640 passed, 3 skipped, 2 xfailed`. BOTH failures are pre-existing, out of scope, and REPOSITORY-STATE-DEPENDENT rather than deterministic, which is why you must measure your own baseline instead of quoting this one: `test_orchestrator_retirement::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` asserts a live plan's status (`kgpptv`) that has since moved from `reviewed` to `approved`, and `test_run_viewer::RunViewerTests::test_run_viewer_cli_latest_only` reads the gitignored `.aw/records/runs/` tree and fails because the three newest runs share one queue, so `latest_only` collapses to a single contributing run and never prints the "Data from N runs" header it asserts. Neither is yours. Judge on the DELTA against a baseline you measured minutes earlier.

THE ITEM THAT MATTERS MOST IS V-02. This change makes a gate accept MORE, which is the direction where a mistake lets real work proceed against an unmet prerequisite. The relaxation must apply to a REVIEW action ONLY: an execute turn consumes its prerequisite's commits, so satisfying its edge on a merely `reviewed` plan would dispatch it against a base that lacks the work it depends on. If you find the execute path accepting a non-terminal target, stop.

THE SECOND-MOST IMPORTANT IS V-03, and it exists because this plan's first draft got it wrong. Do NOT assume agy inherits an oc fix: it defines its own `dependency_status_detailed` and one of its two dependency paths does not call `edge_satisfied` at all. Prove the identity, do not reason about it.

THE THIRD IS THE ANTI-REGRESSION HALF OF V-01, and it is the one a careful executor is most likely to get wrong by being too thorough. Making the `- Status:` field authoritative EVERYWHERE looks more correct than the precedence rule and would break 25 live plans in `executed/` whose field is absent or multi-word (F-15). The rule is: TERMINAL DIRECTORY DECIDES; the field decides only when the directory does not.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN, which were re-measured at HEAD `df26ff6e` and had ALL drifted 5 to 7 lines from the previous revision. Find `edge_satisfied`, its external-target branch, `plan_bucket`, `_read_status`'s import, `reconcile_disposition`'s review branch, agy's local `dependency_status_detailed`, agy's `_findings_block_reason`, and `_SHARED_NAMES` by name.

On completion, close backlog `yf9fj9`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited. OQ-04 was answered with option (a) and NOT (c), so this plan executes as written; the sibling backlog item `phawyy` stays `parked` (retracted premise) and is not this plan's to close.
