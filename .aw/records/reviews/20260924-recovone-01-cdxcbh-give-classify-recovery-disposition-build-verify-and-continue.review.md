# Review findings: plan cdxcbh

- Subject-Id: cdxcbh
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `recovone`, the sole child, graduated from backlog `zt2b16` (`bug`,
`Blocks-Release: next`; gate correctly inherited) and also covering `2t4v1j`. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions. The plan file was committed and unchanged
(byte-identical to the lane input), so no pre-review snapshot was needed.

DISCLOSURE: a sibling model of the same family authored this plan, so treat this as near-self-review.
Its value rests on RE-MEASURING rather than reading, and the headline result is unusually good: EVERY
authored finding reproduces exactly, including both pytest baselines to the test and the scanner census
to the number. The findings below are things the plan MISSED, not things it got wrong.

WHAT HOLDS, AND IT IS ESSENTIALLY THE WHOLE PLAN. F-1: the shared classifier raises
`AttributeError: 'LaneState' object has no attribute 'path'` on a real lane, while both hosts return
`verify-and-continue`; `LaneState._fields` confirms `worktree_path`/`base_sha` and no `path`/`base_commit`,
and `INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX` is `'WIP INTERRUPTED SNAPSHOT (not finished work):'`, so the
shared body's `"wip(snapshot):"` filter matches nothing the driver writes. F-3: `oc_runipd.reconcile_disposition`
raises `KeyError: 'configured_file'` at BOTH exit codes where agy and shared return `('partial', None)`
and `('failed-safely', None)`. F-4: the shared `route_recovery_turn` raises
`TypeError: save_state() missing 1 required keyword-only argument: 'write_report'`. F-2: oc's and shared's
notice output is byte-equal for a real dirty `verify-and-continue` disposition, so OQ-01's "the choice
cannot change behavior" is sound. F-5: the scanner reports `co-defined in both runners : 61`, the same six
`NEITHER-DELEGATES` names, and `reconcile_disposition BOTH-DELEGATE . 40 40 0.976`. F-6: no in-tree test
mentions `classify_recovery_disposition`/`route_recovery_turn`/`recovery_routing`, and `19313eed` deleted
`tests/test_resumedupe.py` (675 lines). F-7: `RecoveryDisposition` and `_lane_commit_subjects` are
AST-identical oc-vs-shared, `TERMINAL_STATES` symmetric difference is `[]` against BOTH hosts, the five
named helpers are already the same objects in oc, and no `isinstance(..., RecoveryDisposition)` exists.
E-06's patch-compatibility reasoning is correct: `mock.patch.object` redirects on a module ATTRIBUTE
whether that attribute is a `def` or a re-export, verified by simulating the `getattr(driver_module, ...)`
resolution under the patch. E-07's "exactly three" arithmetic is also internally sound (see D-2).

WHAT THE PLAN MISSED. Three things, none of which invalidates the design; the first changes what the
new test must assert.

```text
F-1 / F-3 / F-4 re-measured on a real lane at HEAD fcc30bdb
  LaneState: HOLDS-WORK 1 has path? False
  oc      verify-and-continue
  agy     verify-and-continue
  shared  RAISED AttributeError 'LaneState' object has no attribute 'path'
  shared route RAISED TypeError save_state() missing 1 required keyword-only argument: 'write_report'
  exit=0 oc RAISED KeyError 'configured_file' | agy ('partial', None)       | shared ('partial', None)
  exit=1 oc RAISED KeyError 'configured_file' | agy ('failed-safely', None) | shared ('failed-safely', None)

PR-001  the shared classifier ALSO lies about `dirty`, and nothing recorded it
  shared classifier, count of `dirty=False` literals        5   (of 5 RecoveryDisposition constructions)
  shared classifier, count of `st.dirty`                    0
  oc classifier,     count of `st.dirty`                    1   (threaded via `common = {...}`)
  build_verify_and_continue_notice reads decision.dirty     yes  -> reaches operator-visible output

PR-002  the test E-05 names as its proof is a CEILING
  test_oc_to_agy_import_count_did_not_increase   assertLessEqual(len(oc_imports), 4)
  agy MODULE-LEVEL oc imports                    ['record_item_spec_edits']          (one)
  agy ALL oc imports via ast.walk                4  (three are function-local lazy, inside the delegators)
  sorted(AGY_IMPORTS_FROM_OC_RUNIPD) == walk     True   -> declared set matches reality today

PR-003  the fingerprint pin agy's prose invokes covers none of the moved symbols
  classify_recovery_disposition    pinned: False        route_recovery_turn   pinned: False
  build_verify_and_continue_notice pinned: False        reconcile_disposition pinned: False
  RecoveryDisposition              pinned: False        _lane_commit_subjects pinned: False
  describe_lane                    pinned: True         UNMOVABLE = ("disable_lane_prompt",)

closure safety of the three lifted bodies (free_names ∩ oc index, then checked against shared index)
  classify_recovery_disposition     NOT resolvable in runner_shared: none
  build_verify_and_continue_notice  NOT resolvable in runner_shared: none
  route_recovery_turn               NOT resolvable in runner_shared: none   (save_state is the injected one)
  DISPOSITION_* values equal; RECOVERY_DISPOSITIONS equal;
  RecoveryDisposition._fields identical; _field_defaults {'real_commits': ()} on both

baselines, re-measured (both reproduce the authored figures exactly)
  tests/test_oc_runipd.py tests/test_runner_shared.py tests/test_defect_report.py      274 passed
  tests/test_hostdedup_third_host.py tests/test_orchestrator_shape_gate.py             23 passed
  tools/runner_fork_scan.py --triples    co-defined 61; NEITHER-DELEGATES 6 (same names)
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D (anti-regression / invariants) / E (verification) | `runner_shared.classify_recovery_disposition` (all five `RecoveryDisposition(...)` constructions); `oc_runipd.classify_recovery_disposition`'s `common = {...}`; `build_verify_and_continue_notice` reading `decision.dirty` | A FOURTH DIVERGENCE THE PLAN AND BOTH BACKLOG ITEMS MISSED: THE SHARED CLASSIFIER ALSO LIES ABOUT `dirty`. It passes `dirty=False` in EVERY branch (5 of 5) and the string `st.dirty` does not appear in it at all, while oc's body threads the real `st.dirty` and `st.commits_ahead` off the `LaneState`. This is not a dormant field: `build_verify_and_continue_notice` BRANCHES on `decision.dirty`, so the falsehood reaches operator-visible prompt output. Two harms. (a) It is further justification for E-03's "take oc's body whole", which the plan argued only from the field names and guards - a reader who fixed just `st.path`/`st.base_commit` would still ship a classifier reporting every recovered lane clean. (b) MORE IMPORTANTLY, E-02's compared tuple was `disposition`, `snapshot_only`, `inspected_worktree`/`inspected_branch` only, so the new test - the ONLY coverage these paths will have (F-6) - would have passed against exactly that half-fix. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 gained a paragraph naming the divergence with its measurement and forbidding a "tidy" back to a constant. E-02 now requires `dirty` AND `commits_ahead` in the compared tuple plus a FIFTH lane shape (one real commit AND an uncommitted file) asserting `dirty is True`/`commits_ahead == 1`, and requires lane branches cut from a RESOLVED sha so those two fields are not measured against a moving base. V-03 now demands the before/after `dirty=False` and `st.dirty` counts plus a dirty-lane disposition. F-9 added; Proposed-changes and Scope-check updated. |
| PR-002 | MEDIUM | IN-SCOPE | E (verification) | plan `E-05` expected outcome; `tests/test_orchestrator_shape_gate.py::BothHostsShareOneDefinition::test_oc_to_agy_import_count_did_not_increase` | THE TEST E-05 NAMES AS ITS PROOF CANNOT PROVE IT. That test asserts `assertLessEqual(len(oc_imports), 4)`, so it passes at 4 AND at 1: it is a no-regression CEILING and will pass unchanged whether or not E-05 removes a single import. Citing it as the success criterion lets a partial or entirely absent lift read as validated. A related measurement is counter-intuitive enough to be worth recording: agy has exactly ONE module-level oc import and THREE function-local lazy ones inside the very delegator bodies E-05 deletes, and `ast.walk` counts all four, which is why the declared `AGY_IMPORTS_FROM_OC_RUNIPD` set and the walk agree today. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05's expected outcome now names the exact test method, states that it is a ceiling that cannot distinguish 1 from 4, forbids citing it as evidence the lift happened, and identifies the real proof (the `AGY_IMPORTS_FROM_OC_RUNIPD` equality plus an `ast.walk` VALUE assertion) while recording the module-level-versus-lazy measurement. V-05 now requires the walk value and labels the shape-gate run a no-regression check only. F-10 added. |
| PR-003 | LOW | IN-SCOPE | C (architecture) / G (executability) | `agy_runipd`'s "resumedupe (`txc9l1`) E-04" block; `tests/fixtures/runner_shared_premove_fingerprints.json`; `tests/test_runner_shared.py` `UNMOVABLE` | ONE OF THE STALE PROSE CLAIMS E-05 MUST REWRITE IS NOT MERELY STALE, IT IS FALSE, AND E-05 ONLY ASKED FOR AN UPDATE. Agy's block says "`runner_shared` ... holds a strict AST fingerprint pin proving a PURE MOVE of the symbols it received, so adding new logic there is out of this plan's scope". Measured: the fixture contains NONE of the six symbols this plan moves (it pins 34 named symbols such as `describe_lane`), and `UNMOVABLE` is exactly `("disable_lane_prompt",)`. So the pin never blocked this work. Left uncorrected, the next reader re-derives the same false obstacle and defers again - which is how these three names survived `1f7xno`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires that claim CORRECTED rather than updated, states the measurement, and explicitly forbids adding any moved symbol to the fingerprint fixture (which would pin a just-changed body against a capture it never had). V-05 requires the replacement prose quoted. F-12 added. |
| PR-004 | LOW | IN-SCOPE | E (verification) | plan `E-02` expected outcome; plan `E-07` baselines | TWO VERIFICATION WEAKNESSES OF THE SAME SHAPE: A PASS/FAIL BAR THAT DOES NOT SAY WHICH THING FAILED. (a) E-02's red-state outcome listed four failure modes with "at least", so a run where ONLY the identity pin went red would satisfy it - and an identity-only red is also satisfied by a wrapper that still calls a broken body, which is precisely the state `1f7xno` shipped. (b) E-07 quoted `274 passed` and `23 passed` as authoring baselines without saying what a DIFFERENT number means; both are live measurements of a tree other plans are changing concurrently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now records which assertion is red for which reason with the re-measured messages, states that the behavioral failures are the ones that matter and why an identity-only red is insufficient, and its expected outcome requires NAMING the assertion behind each failure. E-07 states the census DELTA of three is the bar while the absolute 61 must be re-derived, and that a changed pytest baseline is information to report rather than a failure. Both baselines were re-measured at review and reproduce exactly. |
| PR-005 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE DID NOT SAY WHAT A HUMAN IS APPROVING, for a plan that deletes six host definitions across both runners and replaces a shared body wholesale. It carried commit discipline, the honesty rule, three stop conditions and the lifecycle transition, but nothing about the blast radius, nothing about why this attempt is safer than the `1f7xno`-era one the in-code prose explicitly warns against re-attempting, and nothing about the coverage hole (F-6) that makes E-02 the only safety net. Its stop conditions were also undifferentiated, giving no sense that a non-reproducing F-1 means the plan should be RE-SCOPED rather than pressed on. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`: what is being approved and which defect is actually live (F-3) versus loaded-but-unreached; why the ordering (classifier first, on oc's body, behavioral tests first) satisfies the very rule the reverted attempt violated, with F-11's re-verification cited; the coverage hole named as the real risk with E-02's three obligations; a declaration-style scope fence including the do-not-touch-the-fixture rule; the honesty rule with the bare-`pytest` flags prohibition and the do-not-cite-the-ceiling rule; and per-condition stop consequences. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: the shared classifier's hardcoded `dirty=False` is a fourth divergence in neither backlog item. Fix it here, or file it separately? | Fix it HERE, as an inherent consequence of E-03 taking oc's body whole, and extend E-02 to detect it. | (a) File a separate backlog item and keep E-03 to the field names. Rejected: E-03 replaces the whole shared body with oc's, so the `dirty` fix lands whether or not anyone names it; the real risk was the TEST not detecting a half-fix, which is what needed changing. (b) Patch the shared body's field names only and keep its `dirty=False`. Rejected: that ships a classifier whose `dirty` is always wrong into a function whose consumer branches on it. | `build_verify_and_continue_notice` reads `decision.dirty`, so the field is consumed, not dormant. Measured: 5 of 5 shared constructions pass `dirty=False`, `st.dirty` appears 0 times in the shared classifier and once in oc's (inside `common`). The plan's own Scope already says `classify_recovery_disposition` "takes oc's body", so no scope widening is required. | yes |
| D-2 | E-07 predicts the co-defined census falls by exactly three while `route_recovery_turn` becomes `BOTH-DELEGATE`. Is that arithmetic right? | YES, verified; recorded in E-07 so it is checkable rather than asserted. | Assuming four names leave the census. Rejected by measurement: a wrapper is still a `def`, so `route_recovery_turn` stays co-defined and only reclassifies. | `census()` computes `co_defined = set(top_level_defs(OC)) & set(top_level_defs(AGY))`, and `top_level_defs` collects only `FunctionDef`/`AsyncFunctionDef`/`ClassDef`, so a `from ... import (n as n,)` re-export is invisible to it (verified by parsing one: the imported name does not appear). A one-line `return runner_shared.route_recovery_turn(...)` body satisfies `is_pure_delegation`, giving `residue_class` `BOTH-DELEGATE` (verified). So 61 -> 58 and NEITHER-DELEGATES 6 -> 3. | yes |
| D-3 | Does E-06's re-export break `tests/test_defect_report.py`'s `mock.patch.object(oc_runipd, "reconcile_disposition", ...)`, as the plan claims it does not? | No; the plan is right and no extra work is needed. | Converting `reconcile_disposition` to a wrapper to be safe. Rejected: nothing in it is host-bound, a wrapper would break the identity pin the plan wants, and the patch concern it would address does not exist. | Simulated the `execute_item_core` resolution (`getattr(driver_module, "reconcile_disposition", ...)`) under the patch: it resolves to the sentinel during the patch and restores after, and the shared object is unaffected. `mock.patch.object` operates on a module ATTRIBUTE, which a re-export is, so whether the attribute came from a `def` or an import is irrelevant. | yes |
| D-4 | Is lifting oc's bodies into `runner_shared` safe against the `NameError`/wrong-resolution class that killed the shared copies (the trap the in-code prose warns about)? | Yes, verified before approval rather than trusted; recorded as F-11 and in the Scope-check's under-scope note. | Taking the plan's word for it. Rejected: this is precisely the class of error that produced F-1 and F-4, and the in-code prose explicitly says not to re-attempt the consolidation on a fingerprint alone. | For each of the three bodies, `free_names` intersected with oc's module index, then each survivor checked against `runner_shared`'s index: nothing missing for any of them (`save_state` is present and is the one E-05 injects). Values also verified identical: all three `DISPOSITION_*` literals, `RECOVERY_DISPOSITIONS`, and `RecoveryDisposition._fields`/`_field_defaults`. Plus F-12: no moved symbol is fingerprint-pinned. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent cdxcbh -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent cdxcbh -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)

HEAD at review                    fcc30bdb   (plan authored against 877545fc)
lane input vs pending/ copy        byte-identical -> no pre-review snapshot needed

AUTHORED FINDINGS, ALL REPRODUCE
  F-1 shared classifier AttributeError; both hosts verify-and-continue          reproduced
  F-2 oc vs shared notice output byte-equal for a dirty verify-and-continue     reproduced (True)
  F-3 oc reconcile KeyError at exit 0 AND 1; agy/shared correct both times      reproduced
  F-4 shared route_recovery_turn TypeError on save_state write_report           reproduced
  F-5 co-defined 61; NEITHER-DELEGATES 6 (identical name list)                 reproduced
  F-6 no test mentions the recovery-routing names; 19313eed deleted 675 lines   reproduced
  F-7 RecoveryDisposition/_lane_commit_subjects AST-identical; TERMINAL_STATES
      symdiff [] vs BOTH hosts; 5 helpers already shared objects; no isinstance reproduced
  baselines 274 passed / 23 passed                                             reproduced exactly

FOUND AT REVIEW
  shared classifier dirty=False x5, st.dirty x0; oc st.dirty x1                -> PR-001
  shape-gate import test is assertLessEqual(..., 4)                            -> PR-002
  fingerprint fixture pins none of the six moved symbols                       -> PR-003
  closure check: nothing unresolvable in runner_shared for any lifted body     -> F-11
  mock.patch.object still redirects through getattr(driver_module, ...)        -> D-3
  top_level_defs ignores re-exports; wrapper satisfies is_pure_delegation      -> D-2
```

NOT RE-RUN AT REVIEW beyond the targeted modules: the full suite. This review changed only planning
prose, so no suite baseline is claimed; E-08 requires a bare `python3 -m pytest` at execution. No
production file was modified at any point (`git status --porcelain` showed only the plan).

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-005 all FIXED, none deferred, none open. OQ-01 and
OQ-02 were both already `resolved` from evidence by the author and both were independently confirmed
(byte-equal notice output for OQ-01; the shared `route_recovery_turn` `TypeError` for OQ-02), so this
plan carries no open questions.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding. FIRST, the
user-visible defect here is F-3 (`oc_runipd.reconcile_disposition` raising `KeyError` on a live path,
including from the deliberate-stop handlers); the other three are dead code, and the value of fixing them
is removing loaded guns before a future consolidation picks one up - which is exactly what `1f7xno` did
and had to revert. SECOND, that history is the reason to read the ordering carefully, and it holds up:
classifier first on oc's body, behavioral tests written first and shown red, caller lifted only after,
with every closure dependency verified resolvable. THIRD, the coverage hole is real and is not this
plan's fault: the four tests that caught the original regression were deleted by `19313eed`, so E-02 is
the only safety net these paths will have, which is why its fixture discipline (real `inspect_lane`,
resolved-sha lane bases, `dirty`/`commits_ahead` compared) matters more than its line count suggests.
FOURTH, `runner_shared.py`, `oc_runipd.py` and `agy_runipd.py` are also named by other pending plans;
not a hazard given isolated lanes and merge-and-revalidate, but serial execution is the lower-surprise
order, and this plan deletes host definitions that a sibling plan might expect to find.
