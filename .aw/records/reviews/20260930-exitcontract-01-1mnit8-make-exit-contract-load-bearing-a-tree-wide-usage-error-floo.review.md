# Review findings: plan 1mnit8

- Subject-Id: 1mnit8
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (HIGH, fixed), PR-603 (MEDIUM, fixed), PR-604 (MEDIUM, fixed), PR-605 (LOW, fixed), PR-606 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72b8d317c`. The plan file was committed and unmodified
before editing (`git status --short` on the plan path empty), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with two
`IPD-Z602` density advisories on E-04 and E-06; the plan did not assess them, so review added that
assessment to the Scope check and concurs with accepting both (E-04 is one test built from one leaf
dict driven by one runner and verified by one `V-*`; E-06's extra clauses are PROHIBITIONS, not extra
deliverables). This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply.

No production file and no test was modified by this review. One probe test file was created under
`tests/` to demonstrate PR-602 and was deleted immediately; `ls` confirms its absence and the tree is
clean of it.

THE DESIGN IS CONFIRMED SOUND AND REVIEW CHANGED NO E-ITEM'S PURPOSE. Every measurement the plan
rests on was re-driven independently rather than read back, and the central ones reproduce exactly:

```
declared leaves: 162  elapsed 0.086s  Counter({'2': 162})
VIOLATIONS 6
   ('ipd-executed-gate', (0, 1), 2)
   ('run finalize', (0, 1, 4, 6), 2)
   ('run cancel', (0, 5, 6), 2)
   ('runs status', (0, 1, 3, 5), 2)
   ('ipd-status-untooled-gate', (0, 1), 2)
   ('runs next', (0, 3), 2)

--help: elapsed 0.253s  Counter({'0': 149, '2': 13})   decls omitting 0: []
usage-error: sampled 30 leaves; in-process vs subprocess disagreements: 0
live matrix: 16 leaves x 2 surfaces = 32 invocations, VIOLATIONS: 0
no-project: next/att/todo/attention/ipd board all human rc=3 member=False, agent rc=2, json rc=2
```

- F-01 REPRODUCES and is now understated rather than overstated: `exit_contract` appears in SIX test
  files, not four (`test_oc_runipd.py` and `test_agy_runipd_cli.py` carry it only inside a test NAME,
  not as a field read, so the plan's "four live test files that READ it" is correct as written).
- F-02 REPRODUCES at 162 of 162 in 0.086s.
- F-03 REPRODUCES: the same six leaves, byte for byte the same tuples.
- F-04 REPRODUCES: 32 live invocations, zero membership violations, and none of the six violating
  leaves is a `LIVE_SAFE_LEAVES` key, so the item's own proposed shape really would have found nothing.
- F-05 REPRODUCES in both directions, which is the plan's most load-bearing measurement: 30 of 30
  agreement on the usage-error path, and on `--help` all 13 named leaves diverge except `prompts set`
  (in-process 2 / subprocess 0 for twelve; `prompts set` agrees at 2), with `status` and `ipd lint`
  agreeing at 0 as controls.
- F-07 REPRODUCES exactly (149/13 split, zero declarations omitting 0).
- F-08 REPRODUCES: both former driver files absent; `rg` finds no live importer of
  `tests/conformance_matrix.py`; `build_matrix` reports `declared_absent: ['prompts set',
  'upgrade-test']` and zero undeclared leaves.
- F-09 REPRODUCES on all five spellings in a `HOME`-redirected non-git temp directory.
- F-12 REPRODUCES: no spec mentions `exit_contract`.

FOUR THINGS REVIEW FOUND THAT THE PLAN DID NOT, two of them HIGH.

PR-601 is the one that would have caused real damage. Two of the six corrections are OWNED BY AN
APPROVED SIBLING whose corrected tuples ALREADY CONTAIN 2, so executing this plan's authored list
after that sibling lands would NARROW a correct tuple and silently re-open the defect the sibling
exists to fix. Approved pending plan `69rdv6` (Set `runsexits`, `- Status: approved`,
`- Readiness: go-pending-approval`) declares the same `agent_workflows/command_surface.py` in its
`Scope-Paths`, and its E-01/E-02 widen `runs next` to `(0,2,3,5,7)` and `runs status` to
`(0,1,2,3,5,7)` on independently measured reachability. This plan told the executor to set those two
to `(0,2,3)` and `(0,1,2,3,5)`, which deletes the reachable 5 and 7. NOTHING IN THE RUNNER PREVENTS
IT: `runner_shared.dependency_depth` contributes only edges DECLARED in `Item-Dependencies`, this
plan declares `none`, and the merge-and-revalidate gate sees no conflict because the second writer
simply overwrites a tuple and the floor gate still passes. Neither plan named the other
(`grep -c 69rdv6` here: 0; `grep -c 1mnit8` there: 0), although a third pending plan, `u28vqb`, had
independently spotted the same overlap and fenced itself out of all four leaves. Fixed by making E-03
act on E-01's MEASURED census instead of the authored list, with an explicit never-narrow rule, a
stop condition in the gate, and V-03 now demanding both tuples be pasted whether or not they were
edited.

PR-602 is a false premise the plan reasoned from, and review demonstrated it rather than arguing it.
OQ-01 and E-04 treat `@pytest.mark.slow` as the lever that relieves the timeout risk. It is not:
`conftest._test_timeout_seconds` consults a `timeout` marker, then `AW_TEST_TIMEOUT`, then
`_DEFAULT_TEST_TIMEOUT = 90.0`, and never the `slow` marker. Probe:

```
tests/test_zz_hangprobe.py  @pytest.mark.slow  time.sleep(95)
FAILED tests/test_zz_hangprobe.py::test_slow_marked_still_hang_guarded - conf...
========================= 1 failed in 90.19s (0:01:30) =========================
```

And the risk is worse than the plan believed, because the authored 61.3s was concurrency-assisted.
Review's SERIAL total for the same 32 invocations, which is how pytest runs them inside one function,
is 88.9s (the `doctor` pair alone 51.8s, the other 15 leaves 37.1s), i.e. 99 percent of the guard.
Fixed by splitting the two decisions in E-04, V-04 and OQ-01: an explicit `@pytest.mark.timeout(...)`
sized from the measured total (or a split across functions) is now MANDATORY and independent of the
`slow` decision, and V-04 explicitly rejects a `slow` mark offered as the hang-budget fix.

PR-603: the baseline bar was a spent constant and the stated failure was not reproducible as stated.
F-10 asserted the tree carries one date-rollover failure (`1 failed, 3419 passed` at `ed3e462a0`) and
V-06 told the executor to reconcile "the baseline plus the tests this plan adds". Review's bare run at
`72b8d317c` is FULLY GREEN at `3538 passed, 2 skipped, 3 warnings in 200.58s`, with that very test
passing, which both confirms the flake diagnosis (it fails only across a UTC date rollover) and proves
the authored total drifted by 119 collected tests in under a day. A reconciliation against either
number is wrong. Fixed by rewriting F-10 and V-06 onto a by-NAME before/after failure-set comparison,
explicitly rejecting both "zero failures" and any constant written in the plan, and requiring the
executor to say so plainly if the flake appears in the after-set but not the before-set rather than
assuming it.

PR-604: the gate was missing the scope fence the workflow requires. The execution contract carried the
commit scoping, the honesty rule and the lifecycle, but no DECLARATION of the declared-scope semantics,
so nothing told the executor what to do about an out-of-scope edit. Fixed by adding a scope fence in
the mandated shape: a declaration, with out-of-scope edits to be MADE and then JUSTIFIED at finalize
(`--scope-reason` / `--scope-ack`), explicitly NOT a stop directive for a scope question, plus the one
genuine stop condition that PR-601 creates. Also added the missing conditional-ownership wording to
the lifecycle paragraph (`aw ipd finalize` when the executor owns it, the runner when a run does) and
the "do not mark a `V-*` from the matching execution checkmark" line.

PR-605: E-02's own justification for the in-process shortcut overstated the subprocess cost in a way a
reader could catch and distrust. It claimed "roughly 0.5s and 162 leaves is about 80 seconds, which
exceeds the 90s budget". Review measured a real `python3 -m agent_workflows <leaf> --bad-flag` at
0.369s, so 162 leaves is about 60s, which does NOT exceed 90s. The conclusion survives (60s against a
90s guard leaves no useful headroom, versus 0.086s in process) but the stated reason was false. Fixed
by replacing the figure with the measurement and restating the conclusion honestly, and by telling the
executor to take the measurement rather than quote this plan's.

PR-606: three stale status claims. `858lhj` and `cn5np0` are both `graduated`, not `open`, yet the
plan calls `858lhj` "open backlog" in its Scope line and F-11; only `h0tiaw` is genuinely `open`.
Fixed at all three sites. Also added the two missing carrier rows to the deferred list (`69rdv6` for
the full measured widening of those two leaves, `u28vqb` for the `oc runipd`/`agy runipd` exit-3
correction), since both are real adjacent work this plan deliberately does not do and neither was
named.

OPEN QUESTIONS. Both pre-existing questions are `Blocking: no` and `Status: resolved`. OQ-01's
resolution was materially WRONG (PR-602) and has been corrected in place to resolve on the demonstrated
behavior of the hang guard rather than on the false premise that `slow` relieves it; it remains
resolved because E-04 now names both decision procedures and V-04 requires both answers as evidence.
OQ-02 was re-checked against `engine.py`'s generated hook block and holds: both gates are generated as
`language: system` hooks with `pass_filenames: false` and `always_run: true`, and pre-commit fails such
a hook on ANY non-zero exit, so exit 2 already refuses the commit and no hook-contract change is owed.
No new question was created: PR-601 and PR-602 were both resolvable from repository evidence, so they
are recorded as decisions below rather than escalated.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | D. Anti-regression and domain invariants | `.aw/records/plans/pending/20260930-exitcontract-01-1mnit8-...ipd.md` E-03; `.aw/records/plans/pending/20260930-runsexits-01-69rdv6-...ipd.md` E-01/E-02; `agent_workflows/runner_shared.py` symbol `dependency_depth` | E-03 instructs setting `runs next` to `(0,2,3)` and `runs status` to `(0,1,2,3,5)` from a list written at authoring. Approved sibling `69rdv6` widens the same two declarations in the same file to `(0,2,3,5,7)` and `(0,1,2,3,5,7)`, both of which already contain 2. Executing the authored list after that sibling lands DELETES the reachable 5 and 7, re-opening the defect it fixed. The runner cannot order them: `dependency_depth` honors only declared `Item-Dependencies` edges and this plan declares `none`; merge-and-revalidate sees no conflict because the file still parses and the floor gate still passes. Neither plan named the other | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 rewritten to act on E-01's measured census with an explicit never-narrow rule and a named stop condition; F-13 added recording the collision and the runner's limits; Scope, Proposed changes, Scope check, E-02 expected outcome and V-03 swept; `69rdv6` added as a deferral carrier; gate carries the stop condition |
| PR-602 | HIGH | IN-SCOPE | E. Testing and verification | `conftest.py` symbol `_test_timeout_seconds` and `_DEFAULT_TEST_TIMEOUT = 90.0`; plan E-04 and OQ-01 | The plan treats `@pytest.mark.slow` as the remedy for the live gate's runtime risk. `slow` does not raise the 90s hang guard: `_test_timeout_seconds` reads a `timeout` marker, then `AW_TEST_TIMEOUT`, then the 90s default, and never `slow`. Demonstrated by probe (`slow`-marked 95s sleep: `1 failed in 90.19s`, `TEST HANG GUARD`). Review's SERIAL total for the 32 live invocations is 88.9s (the authored 61.3s was concurrency-assisted), i.e. 99 percent of the guard, so the test as specified would flake | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04, V-04 and OQ-01 rewritten to separate the hang budget from the marker: an explicit `@pytest.mark.timeout(...)` sized from the measured serial total (or a split) is mandatory and independent; V-04 rejects a `slow` mark offered as the budget fix; F-14 added with the probe transcript; F-06 corrected to carry the serial number |
| PR-603 | MEDIUM | IN-SCOPE | E. Testing and verification | plan F-10 and V-06; bare suite at HEAD `72b8d317c` | F-10 asserts the base tree carries one date-rollover failure at `1 failed, 3419 passed`, and V-06 tells the executor to reconcile the passed count against "the baseline plus the tests this plan adds". Review's bare run is fully green at `3538 passed, 2 skipped, 3 warnings in 200.58s` with that test passing, so the authored total drifted by 119 in under a day and the asserted failure is not a property of the tree | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten to state the failure set as a LIVE property with review's green run pasted; V-06 rewritten onto a by-NAME before/after failure-set comparison, explicitly rejecting "zero failures" and any constant written in the plan, and requiring an explicit statement if the flake appears only in the after-set |
| PR-604 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan `## Approval and execution gate` | The gate carried path-scoped commit, never-push, the honesty rule and a lifecycle paragraph, but NO scope fence, so nothing declared the scope semantics or told the executor what to do about an out-of-scope edit. The lifecycle paragraph also omitted the conditional runner-versus-executor ownership of the terminal transition, and the gate omitted the "do not mark a `V-*` from the execution checkmark" rule the plan states only in its checklist preamble | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE as a declaration (make the out-of-scope edit, justify it at finalize via `--scope-reason`/`--scope-ack`), explicitly not a stop directive for a scope question, carrying the one genuine stop PR-601 creates; added conditional finalize ownership and the separate-pass `V-*` rule; added a WHAT THE HUMAN IS ACCEPTING paragraph |
| PR-605 | LOW | IN-SCOPE | E. Testing and verification | plan E-02 | E-02 justifies the in-process parser by claiming a subprocess sweep costs "about 80 seconds, which exceeds the 90s per-test hang budget". Measured, a real subprocess costs 0.369s, so 162 leaves is about 60s, which does not exceed 90s. The conclusion is right for a different reason (no useful headroom, versus 0.086s in process) but the stated reason is false and an executor re-measuring it would find the plan wrong | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02's justification replaced with the measured 0.369s/60s figures and the honest conclusion, and the executor is told to take the measurement rather than quote the plan |
| PR-606 | LOW | IN-SCOPE | F. Honest documentation | plan Scope line, F-11, Scope check; `.aw/records/backlog/graduated/20260929-858lhj-...backlog.md` `- Status: graduated` | The plan calls `858lhj` "open backlog" in two places; it is `graduated`. `cn5np0` is also `graduated`. Only `h0tiaw` is `open`. Separately, the deferral list named no carrier for the full measured widening of `runs next`/`runs status` (`69rdv6`) or for the `oc runipd`/`agy runipd` exit-3 correction (`u28vqb`), both real adjacent work this plan declines | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Status claims corrected at all three sites; two carrier rows added to the deferred list; Scope check now distinguishes which of the three cited items is actually open, and records the two `IPD-Z602` advisories the plan had not assessed |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Two of this plan's six corrections collide with approved sibling `69rdv6` in the same file. Should the plan declare an `Item-Dependencies` edge on it, drop the two leaves, or re-derive the acted-on set at execution? | RE-DERIVE: E-03 now acts on E-01's measured census, with an explicit never-narrow rule and a stop condition, so the plan is correct in either execution order. | (a) Declare an `Item-Dependencies` edge on `69rdv6`, rejected because it serializes two plans that are independently correct once E-03 stops trusting a written list, and because an edge would also block this plan if the sibling were retired; (b) drop `runs next` and `runs status` from E-03 outright, rejected because they ARE floor violations today and dropping them would leave the gate red if the sibling never lands; (c) leave the authored list and warn in prose, rejected because the authored list is the thing that deletes codes and a warning does not stop a mechanical executor. | `69rdv6` front matter (`- Status: approved`) and E-01/E-02 read in full; tuple arithmetic showing 2 already present in both target tuples; `runner_shared.dependency_depth` docstring ("Only IPD-typed edges whose target is IN THE QUEUE contribute") with this plan's `Item-Dependencies: none`; `u28vqb` F-11 independently naming the same overlap. Recorded as F-13. | yes |
| D-2 | `slow` does not raise the hang budget and the live gate serially measures 88.9s against 90s. Mark it `slow`, raise the budget, split the test, or drop `doctor`? | BOTH an explicit `@pytest.mark.timeout(...)` sized from the measured total (240 recommended) OR a split, AND the `slow` marker; the two decisions are independent and E-04 now requires both answers. | (a) `slow` alone, rejected and DISPROVED by probe: the guard fires on a `slow` test at 90s regardless; (b) raise the budget without `slow`, rejected because an 89s test in the default fast suite taxes every run for a declaration chore; (c) drop `doctor` to get under 90s, rejected explicitly because shrinking coverage to pass a timing gate is the failure mode the plan itself names; (d) leave it to the executor's taste, rejected because the plan's own decision procedure was built on the false `slow` premise. | `conftest._test_timeout_seconds` and `_DEFAULT_TEST_TIMEOUT = 90.0` read; probe transcript `1 failed in 90.19s` on a `slow`-marked 95s sleep; 32-row serial timing transcript summing to 88.9s with the `doctor` pair at 51.8s. Recorded as F-14. | yes |
| D-3 | F-10 asserts a pre-existing failure that review cannot reproduce (tree fully green). Does that block the plan, or change a bar? | Change the BAR to a by-name before/after failure-set comparison, and record BOTH observations (authoring's failure and review's green run) so the executor treats the set as live. | (a) Delete F-10 as wrong, rejected because the flake is real and date-dependent, and deleting it would leave an executor who hits it at midnight with no context; (b) keep "baseline plus the tests added" with the new number 3538, rejected because that constant will drift exactly as 3419 did (119 in one day); (c) tell the executor to ignore that test by name, rejected because a hard-coded exemption masks a genuine future regression in it. | Bare run at `72b8d317c`: `3538 passed, 2 skipped, 3 warnings in 200.58s`, with `test_release_exempt_setter_roundtrip_and_parity` passing; the plan's own authored `1 failed, 3419 passed` at `ed3e462a0`. | yes |
| D-4 | The two `IPD-Z602` density advisories (E-04, E-06) are unassessed. Split those items, or accept them with a recorded rationale? | ACCEPT both, with the rationale written into the Scope check. | Splitting E-04, rejected because its clauses are one test over one leaf dict driven by one runner and verified by one `V-*`, so a split would create two items sharing one fixture and one green run; splitting E-06, rejected because it is a single docstring edit whose extra clauses are PROHIBITIONS, not deliverables. | `ipd_lint.check_density` / `ipd_schema.e_item_density_advisory` are explicitly advisory and do not affect disposition; both items read against the four right-sizing diagnostics in `plan-review.md` Section G. | yes |

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. Six findings, all FIXED, zero deferred, zero open. Structural lint
`conforming` at both `--phase author` and `--phase review-finalize` (two accepted `IPD-Z602`
advisories, now assessed in the plan). No unresolved blocking question, so readiness is
`go-pending-approval`: the plan passed review and awaits human sign-off.
