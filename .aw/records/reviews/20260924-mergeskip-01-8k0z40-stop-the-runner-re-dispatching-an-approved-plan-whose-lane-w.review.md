# Review findings: plan 8k0z40

- Subject-Id: 8k0z40
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `mergeskip`, the sole child, graduated from backlog `zmo0ao`
(`Work-Kind: bug`, `Blocks-Release: next`; the gate is correctly inherited by the plan). Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review,
and `--phase review-finalize` conforms after the revisions. The plan file was committed and unchanged
(byte-identical to the lane input), so no pre-review snapshot was needed.

DISCLOSURE: a sibling model of the same family authored this plan, so treat this as near-self-review.
Every finding below came from executing something rather than from reading: the two spec mutations that
disproved PR-001, the two probe shapes that exposed PR-002, and the grep that found PR-003's enforcer
missing.

WHAT HOLDS, AND IT IS THE DESIGN. F-1 reproduces exactly: no landing predicate has any caller in either
`*runipd.py` (callers are only `runner_shared` itself, `worktree_lease.lane_merged_into_target`, and
`attention` comments), so there is genuinely no dispatch-time landing check. F-3's false-positive is real
and its whole five-lane table reproduces byte-for-byte once the probe is built correctly (see PR-002):
the zero-commit DIRTY lane does classify `LANDED` with `landed=True`, which is exactly why E-02's
`commits_ahead > 0` rule is load-bearing rather than defensive. F-4 reproduces: `reintegrate_lane`
refuses with `REINTEGRATE_PLAN_NOT_FINALIZED` when the plan is not finalized on the lane, so `aw oc
integrate <id6>` is correctly rejected as the remedy and `aw ipd finalize` is correctly named instead.
The architecture is right on the repository's own terms: the gate CONSUMES `classify_lane_integration`
rather than forking a third landing reading (the one-reader constraint `attention` and the classifier's
own docstring both insist on), host functions are INJECTED as `handle_zero_work_retry` does, and the
placement after the orchestrate branch and before `execute_item` is precisely mirrored in both hosts.
E-03's `initial_status != "reusable"` guard is well-founded: `determine_action("reusable")` is `execute`
and `initial_queue_status("reusable")` is `queued`, so a reusable plan really would be dispatched and
really does need the exemption. E-04's `--retry-incomplete` reasoning is right for the right reason
(the branch matches an EXPLICIT status allowlist, so omission suffices), and OQ-01's nonzero-exit
default is consistent with `EXECUTE_REPORTING_SUCCESS_STATES` and the `em0z50`/`zz5yxq` precedent.

WHAT DOES NOT HOLD. Three things, and the first is a false justification for editing an approved spec.

```text
does any test read spec uonrjg Section 7.2?                                  NO
  mutation 1: E-04 code half applied, spec NOT edited
              python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q   ->  12 passed  rc=0
  mutation 2: shipped 7.2 blocked row GUTTED to  | `blocked`, `dependency-blocked` | blocked |
              python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q   ->  12 passed  rc=0
  grep -n "_parse_spec_section" tests/test_lifecycle_style.py  -> ONE def, _parse_spec_section5 (Section 5)
  grep -rn "7\.2"              tests/test_lifecycle_style.py  -> two docstring mentions, no parse
  (both mutations reverted; git status --porcelain clean)

probe lane cut from `main` (the plan's authored shape) vs from a RESOLVED sha (production's shape)
  symbolic:  before merge  state=HOLDS-WORK ahead=1 base=b01d493d
             after  merge  state=EMPTY      ahead=0 base=87e4e45f   classify=EMPTY      <- F-3 hidden
             (lane_work_has_landed independently returns True the whole time)
  resolved:  before merge  state=HOLDS-WORK ahead=1 base=1b5e7a54
             after  merge  state=HOLDS-WORK ahead=1 base=1b5e7a54   classify=LANDED landed_by=ancestor

F-3 table re-measured with the resolved-sha shape (matches the plan exactly)
  aaaaaa           STALE       ahead=0 dirty=False  EMPTY     landed=None
  bbbbbb           HOLDS-WORK  ahead=0 dirty=True   LANDED    landed=True     <- the false positive
  cccccc           HOLDS-WORK  ahead=1 dirty=False  LANDED    landed=True     <- merged --no-ff
  dddddd           HOLDS-WORK  ahead=1 dirty=False  STRANDED  landed=False
  cccccc_attempt2  HOLDS-WORK  ahead=1 dirty=False  STRANDED  landed=False

grep -rn "NoRunnerImport" tests/                             -> no match  (cited by E-02/E-03/V-03)
git log --oneline -S NoRunnerImportTests -- tests/           -> 19313eed  test: trim test suite
runner_shared comment above AGY_IMPORTS_FROM_OC_RUNIPD       still says "enforced by ...NoRunnerImportTests"

TERMINAL_STATES identity   oc is rs -> False    agy is rs -> False   (three separate literals)
full E-04 code half simulated, then
  python3 -m pytest tests/test_lifecycle_style.py tests/test_runner_shared.py -o addopts="" -q -> 101 passed
premove fingerprint fixture   describe_lane pinned -> True    classify_lane_integration pinned -> False
tests/test_runner_shared.py   _dispatch_repo/_dispatch_run are private to IntegrationDeferralLadderTests
                              dir(module) dispatch helpers -> []   ; item writes configured_file: ""
F-5 lane census (re-measured)  4 approved plans in pending/, ZERO lane refs; lkexaw now in executed/
                               git for-each-ref refs/heads/aw/lane/* -> 2 refs, both review-sweep-run-*
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / C (architecture) | plan `E-04` and `F-6` as authored; `tests/test_lifecycle_style.py` `_parse_spec_section5`; spec `uonrjg`'s own 2026-09-21 history line | THE STATED REASON FOR AMENDING AN `approved` SPEC IS FALSE. E-04 bundled the `uonrjg` Section 7.2 amendment into a code item and justified it "since `tests/test_lifecycle_style.py` parses that spec file and fails on a code mapping absent there". It does not: the module's only spec-reading function is `_parse_spec_section5`, which parses SECTION 5 (the glyph/color stage table), and nothing in `tests/` parses Section 7.2. Two mutations prove it, both reverted: E-04's code half with NO spec edit gives `12 passed`, and GUTTING the shipped 7.2 blocked row (deleting two live `merge-*` words) also gives `12 passed`. Three harms. (a) Editing an approved spec is the highest-leverage act a run can make and a false reason means nobody weighed the real contract question. (b) An executor who applies only the code half sees a GREEN suite and may reasonably conclude the amendment is unnecessary, leaving the normative table describing a vocabulary the code no longer has. (c) The identical false claim is in the SPEC'S OWN history line, so the error is propagating between artifacts and would propagate again. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The amendment is KEPT (it is correct) but split into a new `E-09` with the honest reason: Section 7.2 is the normative stage table and Section 0.5 makes this spec the display authority, so a shipped status absent from it leaves the spec stale. E-09 must record IN THE AMENDMENT NOTE that 7.2 is normative-but-unenforced, stopping the propagation. New `V-09` requires the diff AND re-derivation of the unenforcement (revert the spec edit, keep the code, show the suite still green). E-04 now covers the five CODE surfaces only and states the `KNOWN_ITEM_STATUSES`/`_RUNNER_ITEM_PAIRS` coupling that IS test-enforced. F-6 corrected, F-7 added, spec-sync section and Proposed-changes list rewritten. `Highest E allocated` 08 -> 09. |
| PR-002 | HIGH | IN-SCOPE | E (verification) | `worktree_lease._lane_base_sha`; plan `E-01` step (2) and `E-07`'s fixture instructions | THE PLAN'S OWN PROBE AND TESTS WOULD HAVE MEASURED AN ARTIFACT AND CONCLUDED THE DEFECT WAS FIXED. `_lane_base_sha` reads the branch's creation reflog entry and RE-RESOLVES the recorded text, so a lane cut with `git worktree add -b <br> <path> main` records `branch: Created from main` and its computed base FOLLOWS main. The positive case requires a `--no-ff` merge, which advances main, so `commits_ahead` collapses 1 -> 0 and the merged lane classifies `EMPTY` rather than `LANDED`. Measured both ways. This is the worst shape of test defect here: E-01 step (2) explicitly instructs STOP-and-report if the zero-commit-dirty lane no longer reads `LANDED`, so an author using the natural `main` base would hit a false STOP and could report the bug fixed; and E-07 case A would fail for a fixture reason indistinguishable from a real gate failure. Production is immune because `allocate_worktree` passes a resolved `base_sha`. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-01 gained a paragraph naming the mechanism, instructing `base=$(git rev-parse HEAD)`, pasting the correct five-lane table measured at review, and adding "if the merged lane reads EMPTY, suspect the symbolic base before concluding the defect is fixed". E-07 now requires every lane branch cut from a resolved sha, citing E-01. F-9 added. |
| PR-003 | MEDIUM | IN-SCOPE | E (verification) | plan `E-02`, `E-03`, `V-03`; `runner_shared`'s comment above `AGY_IMPORTS_FROM_OC_RUNIPD` | THE VALIDATION WOULD HAVE PASSED VACUOUSLY. E-02/E-03 cite `tests/test_runner_shared.py::NoRunnerImportTests` as the guard obliging injection, and V-03 required `python3 -m pytest ... -k NoRunnerImport` passing. No such class exists (deleted by the suite trim `19313eed`), and a `-k` selector matching zero tests is reported by pytest as a pass, so V-03 would have been green while proving nothing. The plan inherited the citation from `runner_shared`'s own comment, which still asserts the prohibition is "enforced by" it. The RULE is correct and still holds, so the injection design is unaffected. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now records that the citation `runner_shared` itself gives is stale, that the rule holds but is currently unenforced, and that no test will catch a violation. V-03 replaced the dead `-k` selector with two DIRECT checks: a grep for runner import statements in `runner_shared.py` returning nothing, and importing `runner_shared` then asserting no `*_runipd` module entered `sys.modules`. F-8 added. |
| PR-004 | MEDIUM | IN-SCOPE | G (executability) | plan `E-04` as authored; `oc_runipd.TERMINAL_STATES`, `agy_runipd.TERMINAL_STATES`, `runner_shared.TERMINAL_STATES`; `tests/test_lifecycle_style.py::MappingTotalityTests` | THE COUPLING THAT IS ACTUALLY TEST-ENFORCED WENT UNSTATED WHILE A FALSE ONE WAS EMPHASIZED. `MappingTotalityTests._assert_covered` asserts `KNOWN_ITEM_STATUSES <= NATIVE_MAPS[FAMILY_RUNNER_ITEM]` and that each member resolves to a non-`UNKNOWN` stage, so adding the status to the owner enum WITHOUT the `_RUNNER_ITEM_PAIRS` row turns that test red - the one real test consequence in E-04, unmentioned, while the imaginary spec-parse consequence was given as the reason for a spec edit. E-04 also did not say that the three `TERMINAL_STATES` are three separate literals (verified by identity), leaving "add it to all three" looking like redundant belt-and-braces rather than three necessary edits. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now states the identity measurement for the three sets, names the `KNOWN_ITEM_STATUSES`/`_RUNNER_ITEM_PAIRS` coupling as the load-bearing test constraint with the instruction to land both in one edit, and notes `--retry-incomplete` needs no edit because its branch is an explicit allowlist. V-04 now requires `lifecycle_style.resolve(FAMILY_RUNNER_ITEM, "already-landed")` probed by name and returning the blocked stage with no diagnostic. F-6 rewritten. |
| PR-005 | LOW | IN-SCOPE | E (verification) | plan `E-07`; `tests/test_runner_shared.py` `IntegrationDeferralLadderTests._dispatch_repo`/`_dispatch_run` | THE CITED FIXTURE CANNOT BE REUSED AS INSTRUCTED. E-07 said to reuse `_dispatch_repo`/`_dispatch_run` from `tests/test_runner_shared.py`; both are private members of `IntegrationDeferralLadderTests` (a `@staticmethod` and a `@classmethod`), not module-level helpers, so no import reaches them by name. Its queue item also writes `configured_file: ""`, which resolves to no plan, while this plan's cases need a real pending plan path for the gate and for `execute_item`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now says COPY the shape rather than import it, records the measurement showing why, and requires a real `configured_file` naming an approved plan in the fixture repo's `pending/`. Also added a docstring requirement stating that patching `execute_item` proves dispatch was skipped and does NOT prove the launcher was unreachable, so the guarantee is not over-read. F-10 added. |
| PR-006 | LOW | IN-SCOPE | G (executability) / A (correctness) | plan `F-5` and `## Scope check` over-scope bullet; `tests/fixtures/runner_shared_premove_fingerprints.json` | TWO STALE FACTS PRESENTED AS CURRENT. (a) F-5's lane census is already wrong: `lkexaw` (its only example of an approved plan with lanes) is now in `executed/`, the four approved plans in `pending/` have ZERO lane refs, and the only `aw/lane/*` refs are two review-sweep lanes. The CONCLUSION it supports (the gate parks nothing today, the fail-closed direction) still holds, but the counts are a live population presented as a measurement. (b) The over-scope bullet justifies leaving `classify_lane_integration` alone by citing the premove fingerprint fixture; that fixture pins `describe_lane` and does NOT contain `classify_lane_integration`. Both should stay out of scope, but on the real reason (one landing reader), not a pin that does not cover one of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 now carries the re-measured census, labels it context rather than a bar, and forbids treating any of the counts as an expected outcome; E-01 repeats that prohibition. The over-scope bullet now states which symbol the fixture actually pins and keeps both out of scope on the one-reader reason. The under-scope bullet carries the review measurement that the full E-04 code half gives `101 passed` with no test edit, marked re-derive-rather-than-trust, and routes any real need to `--scope-reason` instead of a stall. |
| PR-007 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE DID NOT SAY WHAT A HUMAN IS APPROVING, for a plan that adds a dispatch-time refusal to run an approved plan AND amends an approved spec. It carried commit discipline, the honesty rule, the OQ-01 note and the lifecycle transition, but no statement of the false-positive risk and what bounds it, no note that a new item status is a durable vocabulary change written into ledgers that outlive the release, no scope fence in declaration form, and no bare-suite instruction. Its stop conditions were also undifferentiated: "if E-01 finds any of its three facts moved, stop" gives the executor no idea that fact (1) moving means the plan should be RETIRED rather than executed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`: the two things being approved with the spec amendment called out as the consequential one and as a contract decision rather than a mechanical consequence; the false-positive failure mode with the three rules that bound it and the tests that cover each; the durable-vocabulary warning citing the `TERMINAL_QUEUE_STATUSES` measured failure; a declaration-style scope fence routing excess to `--scope-reason`; the hard-MUST honesty rule including "a `-k` selector that matches zero tests is NOT a pass" (which PR-003 caught in practice); the bare-`pytest` instruction with the `-n0`/`-q`/`-p no:randomly` prohibitions; and per-fact stop conditions naming the distinct consequence of each. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: the reason given for amending approved spec `uonrjg` is false. Drop the amendment, or keep it on a different reason? | KEEP it, split into its own `E-09`, restated on the contract reason, and require the amendment note to record that Section 7.2 is normative-but-unenforced. | (a) DROP the spec edit, since no test demands it. Rejected: Section 7.2 is the normative stage table and Section 0.5 makes this spec the single display authority, so shipping `already-landed` without the row leaves the spec describing a vocabulary the code no longer has - the drift the spec exists to prevent. (b) Keep it inside E-04 with a corrected sentence. Rejected: a spec amendment is a different KIND of act from a code edit (it changes the contract every future plan is reviewed against) and AGENTS.md obliges declaring and justifying it, which is easier to review and to gate as its own item with its own V-item. | Measured: `tests/test_lifecycle_style.py` parses only Section 5 (`_parse_spec_section5`, one definition, one call site), and two mutations (code-half-only; 7.2 row gutted) each gave `12 passed`. Spec `uonrjg` Section 7.2 is titled "Runner item outcomes" and is a normative table; Section 0.5 records the 2026-09-13 maintainer ruling that this spec is the single authority for lifecycle presentation. The plan already declared the spec path in `- Scope-Paths:`, so both runners announce the edit. | yes |
| D-2 | PR-002: should the plan mandate a resolved-sha probe base, or note the hazard and leave the shape to the executor? | MANDATE `base=$(git rev-parse HEAD)` in both E-01 and E-07, and paste the correct expected table so a wrong shape is self-evident. | Noting the hazard only. Rejected: E-01's instruction is a STOP condition, so an executor who builds the probe the natural way (`... <path> main`) gets a false STOP and the most likely misreading is "the defect is fixed, retire the plan". A hazard note the executor reads AFTER measuring does not prevent that. | `worktree_lease._lane_base_sha` parses `branch: Created from <text>` and re-resolves the text; `allocate_worktree` passes a resolved `base_sha`, so the mandated shape IS production's. Measured both ways at review: symbolic base -> merged lane `EMPTY` `ahead=0`; resolved base -> `LANDED` `landed_by=ancestor` and the authored F-3 table reproduces exactly. | yes |
| D-3 | PR-003: `NoRunnerImportTests` is gone. Should this plan re-add the guard, or just stop citing it? | Stop citing it and prove the property directly in V-03; do NOT re-add the test here. | Re-adding a structural no-runner-import test. Rejected: `19313eed` deleted 7,000+ tests deliberately and `80db6750`'s subject is "delete 366 tests that pinned code structure instead of behaviour", so re-adding a structure-pinning test is a policy decision against a recorded sweep and is out of scope for a dispatch-gate plan. Filing it as backlog is the right route if wanted. | `grep -rn "NoRunnerImport" tests/` -> no match; `git log --oneline -S NoRunnerImportTests -- tests/` names `19313eed`. The property itself is directly checkable without a test file (no runner import statement in the module; no `*_runipd` in `sys.modules` after importing it), which is what V-03 now requires. | yes |
| D-4 | Is `blocked` the right `lifecycle_style` stage for `already-landed`, rather than `done` or a new stage? | `blocked`, as the plan proposed. | (a) `done`. Rejected: the plan is still `approved` in `pending/` and a human act is owed, so `done` would assert a completion that did not happen and would contradict OQ-01's nonzero exit. (b) A new stage. Rejected: Section 5's stage set is normative and adding a stage is a far larger spec change than adding a status to an existing row. | The existing precedent is exact: `merge-needs-human` is `blocked` for the same reason (the item cannot proceed without a person). `already-landed` needs `aw ipd finalize`, an attested act the runner must not perform. Keeping it out of `EXECUTION_SUCCESS_STATES`/`SUCCESS_STATES` is consistent with `EXECUTE_REPORTING_SUCCESS_STATES` and the `em0z50`/`zz5yxq` ruling that an execute item which did no work must not exit 0. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent 8k0z40 -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent 8k0z40 -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)
aw check release-gates                             -> errors 0  warnings 0
aw sanitize --agent                                -> {"outcome":"clean","exit":0,"findings":0}

HEAD at review                        0c2e7970   (plan authored against 877545fc)
lane input vs pending/ copy           byte-identical -> no pre-review snapshot needed

F-1 REPRODUCED   no landing-predicate caller in either *runipd.py
F-3 REPRODUCED   full five-lane table, with the resolved-sha probe shape (see PR-002)
F-4 REPRODUCED   reintegrate_lane returns REINTEGRATE_PLAN_NOT_FINALIZED when not finalized on lane
F-5 STALE        re-measured: 4 approved plans, 0 lane refs; lkexaw now executed/   -> PR-006

spec uonrjg 7.2 read by any test      NO (two reverted mutations, each 12 passed)   -> PR-001
probe base main vs resolved sha       EMPTY/ahead=0 vs LANDED/ahead=1               -> PR-002
NoRunnerImportTests exists            NO (deleted by 19313eed)                      -> PR-003
TERMINAL_STATES identity              three separate literals                       -> PR-004
full E-04 code half + two test modules  101 passed, no test edit needed             -> PR-006 under-scope
premove fingerprint pins              describe_lane yes / classify_lane_integration no -> PR-006
_dispatch_repo/_dispatch_run          private to a TestCase; configured_file ""     -> PR-005

determine_action / initial_queue_status   approved -> execute/queued ; reusable -> execute/queued
                                          (so E-03's reusable exemption is necessary, not decorative)
--retry-incomplete branch                 explicit status allowlist -> omission suffices, no edit
gate placement                            after the orchestrate block, before execute_item, in BOTH hosts
```

Every mutation described above was reverted and `git status --porcelain` was verified to show only the
plan file. NOT RE-RUN AT REVIEW beyond the targeted modules: the full suite. This review changed only
planning prose, so no suite baseline is claimed; E-08 requires a bare `python3 -m pytest` at execution.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001 through PR-007 all FIXED, none deferred, none open. OQ-01 remains
`- Status: open` with `- Blocking: no` and a stated default, which per the 2026-09-10 maintainer ruling
does not make the plan `NO-GO`; it is a genuine maintainer preference (nonzero versus benign exit) with a
one-line change either way, and the default is the conservative direction.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding. FIRST, this
plan gives the runner authority to DECLINE to run an approved plan. The failure mode is a false positive
parking work that needed doing; three rules bound it (committed-work, not-dirty, fail-closed across all
of an id6's lanes) and E-07 cases C/D/E test each, and the gate never deletes, merges, or finalizes.
SECOND, it amends an `approved` spec, and review established that no test forces that amendment, so it is
a pure contract decision the maintainer should make knowingly. THIRD, `already-landed` is a permanent
addition to a status vocabulary written into durable run ledgers, so the five-surface registration is not
bureaucracy: a partially admitted status makes a run refuse its own resume. FOURTH, `runner_shared.py`,
`oc_runipd.py` and `agy_runipd.py` are also named by other pending plans; that is not a hazard (isolated
lanes plus merge-and-revalidate) but serial execution is the lower-surprise order.
