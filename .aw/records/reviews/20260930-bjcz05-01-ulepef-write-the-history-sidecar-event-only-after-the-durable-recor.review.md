# Review findings: plan ulepef

- Subject-Id: ulepef
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (LOW, fixed), PR-807 (LOW, fixed), PR-808 (LOW, fixed), PR-809 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and unmodified before editing
(`git status --porcelain` empty on the whole tree), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with one `IPD-Z602`
density advisory on E-02 which the plan did not assess; review added that assessment (PR-809). This
plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not
apply. No production file, test, document or spec was modified by this review. Four throwaway probe
repositories were created under `.aw/state/tmp/revprobe/` and deleted; the tree is clean of them.

THE DEFECT IS REAL, USER-VISIBLE, AND EVERY CENTRAL MEASUREMENT REPRODUCES. The plan's subject was
re-derived independently rather than read back:

```
AST order, re-measured:
  backlog.run_set    append_advisory 1697  ->  atomic_write 1707  ->  src.unlink 1709
  backlog.run_note   append_advisory 1787  ->  atomic_write 1812
  specs.run_set      _sidecar_append 867   ->  git_mv 872 -> atomic_write 877 / atomic_write 880
  specs.run_note     _sidecar_append 1098  ->  atomic_write 1100
  backlog.run_new    atomic_write 1362     ->  append_advisory 1371      (already correct, F-10)

F-01 already-fixed halves:
  backlog.run_set  evaluate_blocking_close 1655 -> dry_run if 1684 -> append 1697
  specs.run_set    validate_spec 831           -> dry_run if 857  -> append 867
  status_set.py: grep -c record_history = 0

F-02 live probe (chmod 500 destination, euid 1000, no monkeypatching):
  backlog set  --status graduated  -> RC 1, PermissionError, item still "- Status: open" in open/
     sidecar: {"id6":"bk0004","date":"20261001","tree":"backlog","workflow":"aw backlog set",
               "actor":"aw backlog","message":"probe"}
  backlog note --message hello     -> RC 1, sidecar "note: hello", grep -c hello in item = 0
  specs note   --message hello     -> RC 1, sidecar "note: hello", inline absent
  specs set    --status to-review   -> RC 1, sidecar "to-review: m", file still in draft/,
                                       to-review/ empty, git status shows only ?? history.jsonl

F-04 operator-visible phantom:
  $ aw record-history bk0004 --dir <probe>
  History for bk0004
  - 20261001 [backlog] aw backlog set (aw backlog): probe
  RC=0                       <-- reports a transition that did not happen

F-06 malformed id6 false negative:
  append raised ValueError: record_history.append: 'bk9' is not a valid id6
  append_advisory returned False ; sidecar exists: False

PR-801 instrumented specs moving case:
  destination UNWRITABLE -> RAISED out of main: PermissionError
                            TRACE: [('git_mv', 'RAISED PermissionError')]     <-- atomic_write NOT reached
  destination WRITABLE   -> RC 0  TRACE: [('git_mv','OK'), ('atomic_write','OK')]
  direct `git mv` in the same fixture: fatal: renaming ... failed: Permission denied

PR-802 specs note has no --dir:
  aw specs note --dir <d> <path>  ->  RC 2  "unrecognized arguments: --dir ..."  no sidecar

PR-806 suite:
  bare python3 -m pytest -> 3887 passed, 2 skipped, 3 warnings in 247.19s   (zero failures)
  test_release_exempt_setter_roundtrip_and_parity alone -> 1 passed
```

Per-finding against the plan's own Findings table:

- F-01 REPRODUCES in all three parts (gate ordering, validation ordering, `status_set` silence).
- F-02 REPRODUCES on all four verbs; one SUB-CLAIM is wrong, corrected as PR-801 and new F-13.
- F-03 REPRODUCES, including the stronger half: for both `run_note` verbs the inline record is
  measurably absent while the sidecar holds the event.
- F-04 REPRODUCES verbatim including the exit code 0.
- F-05 not re-driven (it is an authoring-time emulation of the post-fix order); its conclusion is
  implied by the measurements above and by the fix being a pure statement move.
- F-06 REPRODUCES with the warning text verbatim.
- F-07 CONFIRMED in substance; its grep claim is wrong on one entry, corrected as PR-808.
- F-08 DRIFTED; corrected as PR-807, and its central prediction is now proven rather than predicted.
- F-09 NOT REPRODUCIBLE; corrected as PR-806.
- F-10 REPRODUCES.
- F-11 REPRODUCES on all four verbs (every probe raised rather than returning); it is what forces
  PR-803.
- F-12 REPRODUCES (`19lmbe` still `open` with `- Blocks-Release: next`).
- OQ-01's four cited spec locations all read as quoted (C5 line 88, C2 line 82, 4.2 line 161, E4 line
  74 citing `.aw/.gitignore:11`), AC-7 does say "the JOURNAL write", the `vhbvwz` ruling quotes
  verbatim from `record_history.append_advisory`, and `check_engine._CARRIER_TARGET_TYPES` is
  `('backlog', 'plans')` as the Carrier-Note claims. Every carrier resolves: `ms06pi` graduated with
  `- Blocks-Release: next`, `fcnz1r` open, `fnb8pl`/`lq2w86`/`2wae2x` open, `19lmbe` open.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | A (correctness), E (verification) | `agent_workflows/artifact_core.py:359` (`git_mv`, its `shutil.move` fallback at `:371`); the two instrumented traces; `agent_workflows/specs.py:866-881` (the `if moving:` construct) | The plan asserts in four places (F-02, E-03, E-06, V-03) that the specs moving case is "`git_mv` succeeded and `atomic_write` failed". Measured by wrapping both functions and driving the real CLI: the trace is `[('git_mv','RAISED PermissionError')]` and `atomic_write` is NEVER REACHED, because `git_mv` falls back to `shutil.move` which raises copying into the unwritable destination. The defect and the fix are unaffected (the phantom event and the partial state both reproduce), but E-06 and V-03 DEMANDED evidence of a state the prescribed `chmod` probe cannot produce, so an honest executor could not satisfy them; and whether a half-completed move is reachable in production at all was never established. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-13 records the measurement in both directions. E-03 now states the placement POSITIONALLY (after the whole `if moving: / else:` construct, exactly once, not duplicated into both branches) and explicitly forbids reasoning from the old claim. E-06 and V-03 may assert only the observable outcome, must not assert `git_mv` succeeded, and must label a half-completed move as deliberately CONSTRUCTED if they build one. F-02's sub-claim corrected in place with a pointer to F-13 |
| PR-802 | HIGH | IN-SCOPE | E (verification) | `aw specs note --help` (options are `--message`/`--date` plus shared output flags only); `agent_workflows/specs.py` `_repo_root_of`; the invocation exiting 2 | `aw specs note` accepts no `--dir`, while the other three verbs in scope do. A failure case written with `--dir` exits 2 on `unrecognized arguments` and writes no sidecar, so it asserts "no sidecar" and goes GREEN while never reaching the code under test. This is the same class of silent false negative the plan already guards against for a malformed id6 (F-06), and E-06's eight-case design makes it likely: three verbs take `--dir` and one does not | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-14 records it beside F-06 as the same class. E-06 now names the asymmetry, requires the path-only invocation for that verb, and requires its SUCCESS case to assert sidecar CONTENT so a usage error cannot masquerade as the fix working; V-06 carries the same requirement |
| PR-803 | MEDIUM | IN-SCOPE | E (verification) | every `chmod` probe raising rather than returning; the plan's own F-11 | F-11 correctly measures that the `PermissionError` propagates uncaught out of `cli.main`, and the plan's Deferred row correctly says the tests must not depend on the F-11 fix. But E-06 only said the failure cases "assert on sidecar contents, artifact bytes and exit codes", which includes an exit code the failure path never returns: a direct `cli.main` call RAISES. The two statements contradict, and following the E-item literally produces a test that errors on the exception | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now requires the failure cases to wrap the invocation in `pytest.raises(OSError)` (or equivalent) and assert on the sidecar and artifact only, with the exit-code assertion confined to the SUCCESS cases; V-06 confirms it |
| PR-804 | MEDIUM | UNDER-SCOPE | G (execution contract) | the plan's `## Approval and execution gate`; `plan-review.md` Step 4; AGENTS.md 2026-09-01 scope-fence ruling | The gate carried the honesty rule, path-scoped commit, never-push and a conditional-free lifecycle paragraph, but no SCOPE FENCE declaration, and its lifecycle instruction said only "through `aw ipd`" without naming `aw ipd finalize` or the runner/executor split. It also did not record that backlog `bjcz05` is already `graduated`, which an executor could read as an owed transition | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE as a DECLARATION naming all five paths and the `--scope-reason`/`--scope-ack` reconciliation, while preserving the three genuine stop conditions (a normative spec row needing change, all four sites already correct, an unsafe concurrent edit). POST-GATE LIFECYCLE now names `aw ipd finalize` with conditional runner ownership, forbids a hand `git mv` and a hand `- Status:` edit, and records `bjcz05` as already `graduated` with its gate discharged by this plan's execution |
| PR-805 | MEDIUM | IN-SCOPE | A (correctness) | `agent_workflows/backlog.py` `if item.id:` at the append, `if dest.resolve() != src.resolve():` at the unlink; `agent_workflows/specs.py` `if moving:` | "Move the call after the write" is underspecified at three guarded sites, in a way that permits a half-made move. In `backlog.run_set` the append is inside an `if item.id:` block (so the block moves, not the bare call) and the `src.unlink()` is itself inside a conditional (so "after the unlink" means after that block, not inside it). In `specs.run_set` there are TWO `atomic_write` calls on two branches, so a naive move lands after only one | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now specifies that the whole `if item.id:` block moves and that "after the unlink" means after the enclosing conditional; E-03 specifies a single placement after the whole `if moving: / else:` construct with an explicit prohibition on duplicating the call into both branches; V-03 checks the "exactly once" property |
| PR-806 | LOW | IN-SCOPE | E (verification bar) | bare run at review HEAD; `tests/test_backlog.py` `_DATE` normalization and its `fnb8pl` comment | F-09's baseline is not reproducible and three places treat it as a constant (F-09, Required tests, the gate's "THE BASELINE IS NOT GREEN" paragraph). Measured: `3887 passed, 2 skipped`, zero failures, and the authored date-skew failure PASSES, because that test normalizes every history date with `_DATE.sub("- HIST_DATE ", ...)` and records the skew as live bug `fnb8pl` in a comment rather than asserting a literal date. The authored `3487` and the measured `3887` differ by 400, so a count comparison is guaranteed to mislead, and a gate paragraph promising a non-green baseline invites an executor to excuse a real failure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 rewritten with both observations and the structural reason the authored failure is gone. The Required tests bullet, V-06 and the gate paragraph all now require a by-name FAILURE SET comparison against an empty set, forbid every pass-count constant, and require any observed failure to be shown reproducing on an unmodified tree. The skew itself is still recorded as real and still deferred to its three open carriers |
| PR-807 | LOW | IN-SCOPE | G (live-artifact criteria) | each named plan re-read; `find .aw/records/plans -name '*<id6>*'`; `git show --stat da04c5cf0` and its `backlog.py` diff | F-08 enumerates a LIVE population and has drifted: `8rsxy1`, `f7igdu` and `jbipfa` are now in `executed/`, and `4nbvfr` and `izh17y` have advanced a status each. The row's conclusion holds, and in the one case that actually resolved it is now PROVEN rather than predicted: `jbipfa` was named as the closest neighbour and has landed in the same function without moving the append (its diff adds a `label` parameter and a `prior_status` computation; the post-merge AST still shows append 1697 before write 1707) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 refreshed with the measured statuses and locations, and rewritten to record the `jbipfa` outcome as evidence rather than prediction, with the AST re-check pasted. The no-dependency-edge conclusion is unchanged and now rests partly on an observed merge |
| PR-808 | LOW | IN-SCOPE | E | `grep -rln history.jsonl tests/` | F-07 claims the grep matches `test_history_provenance.py`. It does not: that module reaches the sidecar through the `record_history` API and by monkeypatching `record_history.append`, never by naming the file. The actual matches are `test_backlog.py`, `test_specs_status_dirs.py`, `test_installer.py` and `tests/fixtures/derive_plan_status_baseline.json`. The row's conclusion (this direction is uncovered, `tests/test_history_write_order.py` absent) is correct and was independently confirmed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07's evidence cell corrected with the measured match list and the reason the module does not appear, plus the test count (the class carries 4 of the module's 7 tests). Conclusion unchanged |
| PR-809 | LOW | IN-SCOPE | G (right-sizing) | `aw ipd lint --phase author --long` reporting `IPD-Z602` on E-02 | The one structural advisory the linter raises was unassessed, and the workflow requires conceptual density to be evaluated in semantic review rather than cleared by a passing count lint | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check now carries a per-E-item right-sizing assessment. The E-02 advisory is ACCEPTED with the reason recorded (two call sites in one function pair, one concern, one `V-*`; two of its four "clauses" are prohibitions, and splitting would risk landing `run_set` while leaving `run_note`, which F-03 calls the purest breach, behind). E-03 and E-06 assessed and kept whole for stated reasons |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's prescribed `chmod` probe cannot produce the half-completed move (`git_mv` done, `atomic_write` failed) that E-06 and V-03 demand as evidence, and review did not establish that state is reachable in production. Should the plan require a constructed probe for it, drop the claim, or escalate? | DROP THE CLAIM as a required assertion and keep the CASE: E-06 and V-03 now assert only the observable outcome of the directory-crossing probe (no sidecar, source still in place, destination empty) and are forbidden from asserting that `git_mv` succeeded; a constructed half-move is permitted as an optional ninth case that must declare itself constructed. | (a) Require a constructed probe (patch `core.atomic_write` to raise after letting `git_mv` run), rejected as mandatory because it would make a required validation item depend on monkeypatching production code to reach a state nobody has shown production can reach, which is the opposite of the plan's own stated preference for the shipped path; (b) drop the directory-crossing case entirely, rejected because that branch has its own placement hazard (two `atomic_write` calls on two branches, PR-805) and an in-place-only test would not cover it; (c) escalate as a blocking question, rejected because the reachability of a half-move changes nothing about where the append goes or whether the defect is real, both of which are independently measured, so it is a test-evidence question and not a contract one. | The two instrumented traces (`[('git_mv','RAISED PermissionError')]` with the destination unwritable; `[('git_mv','OK'),('atomic_write','OK')]` with it writable); `artifact_core.git_mv`'s `shutil.move` fallback; the phantom event and partial on-disk state reproducing regardless. Recorded as F-13. | yes |
