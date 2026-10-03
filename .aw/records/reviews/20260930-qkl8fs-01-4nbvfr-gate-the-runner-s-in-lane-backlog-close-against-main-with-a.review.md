# Review findings: plan 4nbvfr

- Subject-Id: 4nbvfr
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (MEDIUM, fixed), PR-903 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `816f4a2e0`. The plan file was committed and unmodified
before editing (`git status --short` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) with ZERO diagnostics and ZERO
advisories across all nine E-items. This plan's own first `- Kind:` bullet reads `child`, so the
`IPD-S407` orchestrator child-row check does not apply.

All probe work was done under the gitignored `tmp/` and removed afterwards, including the scratch
`git worktree` fixtures (`git worktree prune` run). NO production file and no test was modified by this
review; `git status --short` shows only the plan and this record.

THE DESIGN IS SOUND AND REVIEW CHANGED NO E-ITEM'S PURPOSE. I built a REAL two-tree fixture
(`git worktree add`, so the lane genuinely shares main's object store) and drove the shipped predicate
directly rather than reading the findings back. The architecture claims all hold:

```
=== shared object store ===
main .git == lane .git (git-common-dir): YES
git ls-tree aw/lane/qq0001  -> .aw/records/plans/executed/...aaa111...   (finalized lane)
git ls-tree aw/lane/nofinal -> .aw/records/plans/pending/...aaa111...    (NEGATIVE CONTROL)

=== F-03 / F-04 / F-05, single-carrier shape ===
gate=LANE, evidence=lane executed/ path   legitimate=True   path='HANDOFF'
gate=MAIN, evidence=lane executed/ path   legitimate=False  (carrier is not executed/implemented)
gate=MAIN, NO evidence                    legitimate=False  (carrier is not executed/implemented)
gate=MAIN, evidence=main pending/ path    legitimate=True   path='SATISFIED'   <-- F-04, the trap

resolve_evidence_artifact: (lane, lane exec)=True (lane, main pend)=False
                           (main, lane exec)=False (main, main pend)=True

=== the override's verifiability ===
ref=aw/lane/qq0001  shows aaa111 under executed/: True
ref=aw/lane/nofinal shows aaa111 under executed/: False
ref=no/such/ref     shows aaa111 under executed/: False
```

- F-01 REPRODUCES: `rg 'gate_dir|gate_root' agent_workflows/runner_shared.py` returns NOTHING, while
  `backlog.run_set` does resolve `gate_root`. The shipped flag has no runner caller.
- F-03 REPRODUCES exactly, including both evidence variants. A naive `--gate-dir <main>` really does
  refuse the ordinary close, so the override is load-bearing rather than a convenience.
- F-04 REPRODUCES and is the sharpest hazard in the plan: citing main's `pending/` path satisfies the
  gate via SATISFIED with an UNEXECUTED carrier. The gate's SECOND paragraph is right to forbid that
  route explicitly.
- F-05 REPRODUCES cell for cell (all four).
- F-07 REPRODUCES including the negative control, which is what makes E-02 a VERIFIED override rather
  than a `--trust-me` flag.
- The symbol claims all hold. `evaluate_blocking_close`'s signature ends `*, item_text=None,
  prior_priority=None`, so a new keyword-only parameter is additive. `check_engine._git_capture` and
  `_blob_text` exist. `_carrier_is_executed` is path-based for `.ipd.md` and reads `- Status:
  implemented` for `.spec.md`, exactly the asymmetry E-02 must honor. The HANDOFF fold is
  `if same_gate_carriers and all(_carrier_is_executed(_c) ...)`, the call site E-02 targets.
- THE INJECTED-CALLABLE TRAP IS REAL, and it is the trap the plan says made `9vglxd` unexecutable:
  `runner_shared.close_backlog_item` requires `run_checked` keyword-only, while the call site in
  `process_backlog_close` invokes the INJECTED callable with FIVE POSITIONAL arguments and no
  `run_checked`; both host wrappers (`oc_runipd.close_backlog_item`, `agy_runipd.close_backlog_item`)
  are five-positional shims that inject their own `run_checked`. E-04's keyword-only instruction and
  its widen-both-wrappers warning are both correct and necessary.

ONE PREMISE DOES NOT REPRODUCE, AND IT IS THE ONE THE PLAN CALLS "THE DEFECT" (PR-901). F-02 claims
that a TWO-carrier item with an unexecuted sibling returns `legitimate=True` via HANDOFF when gated
against the lane. Measured, BOTH roots refuse:

```
=== F-02 as authored: TWO carriers, sibling unexecuted in both trees ===
gate tree = LANE, no evidence   legitimate=False  (naming BOTH carriers)
gate tree = MAIN, no evidence   legitimate=False  (naming BOTH carriers)
```

The cause is structural rather than fixture-dependent: `2o5wka` tightened the HANDOFF arm to
`all(_carrier_is_executed(...))`, so ONE unexecuted sibling refuses in EVERY tree. Critically,
`git show 8163b62ad:agent_workflows/check_engine.py` confirms that `all(...)` was ALREADY PRESENT at
this plan's own authoring HEAD, so the authored verdict could not have been produced by the code it
claims to have been driven against; it appears to describe pre-`2o5wka` ANY semantics.

THE DEFECT IS NONETHELESS REAL, AND WORSE THAN THE PLAN SAID. The split appears on the SINGLE-CARRIER
close:

```
=== single-carrier shape, no evidence ===
gate=LANE  legitimate=True   path='HANDOFF'
gate=MAIN  legitimate=False  (carrier is not executed/implemented)
```

That is the ORDINARY shape every isolated turn with one carrier takes, so the leak is on the common
path rather than a rarer multi-carrier one. This is why the finding is FIXED rather than REPLAN: the
mechanism, the override design, and E-02 through E-09 are all unaffected; what was wrong is which
shape demonstrates the defect, and that wrong shape had propagated into E-01's re-measurement
instruction, E-01's STOP condition, E-06's case mapping, V-01's required evidence, V-02's cell (2),
V-06, the Required-tests section, the Goal and the gate's FIRST paragraph. Two of those were actively
dangerous: V-01(a) demanded evidence that CANNOT be produced (so the plan would fail its own first
validation), and E-01's STOP condition could lead an executor who correctly measures both roots
refusing to conclude the premise had expired and abandon a plan whose defect is real.

The remaining findings are a spent baseline (PR-902: `3419` authored, review measures `3560` fully
green with the named time-dependent failure PASSING) and two stale cross-references (PR-903: `47ttnv`
is `executed` not pending, and the approved pending plan `2misq5` that carries its residue was unnamed;
checked, `2misq5` overlaps none of this plan's eleven scope paths, so it is not a collision).

WHAT I CHECKED AND DID NOT FLAG. The four open questions are all `Blocking: no` and `Status: resolved`
with measured bases, and all four survive: OQ-01's rejection of route (b) is strengthened by F-04
reproducing; OQ-02's isolated-only decision rests on F-10, which I did not re-drive but whose mechanism
(`lane_executed_carrier_override` short-circuiting on same-tree) I confirmed exists at
`runner_shared.lane_executed_carrier_override`; OQ-03's one-plan decision is sound given E-02 is this
plan's own deliverable; OQ-04's no-grandfathering conclusion follows from the change being inert for
every caller passing no override, which cell (4) of V-02 pins. The eleven-path `Scope-Paths` is large
but every path is justified in the Scope check and I found no unjustified entry. The carrier-scan AST
guard (`tests/test_carrier_scan_single_item_contract.py`) is real and E-02's instruction to keep
`find_from_backlog_artifacts` as the single discovery call respects it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | A. Correctness (premise) | plan F-02, Goal, E-01, E-06, V-01, V-02, V-06, Required tests, gate para 1; `check_engine.evaluate_blocking_close` HANDOFF fold `if same_gate_carriers and all(_carrier_is_executed(_c) ...)`; `git show 8163b62ad:agent_workflows/check_engine.py` | F-02, the finding the plan labels "THE DEFECT", does not reproduce. On the two-carrier sibling-unexecuted shape BOTH roots return `legitimate=False`, because `2o5wka`'s `all(...)` fold makes one unexecuted sibling fatal in every tree, and that fold was ALREADY in the tree at this plan's authoring HEAD, so the authored verdict could not have been measured as written. The DEFECT IS REAL on the SINGLE-CARRIER shape (gate=LANE `legitimate=True path='HANDOFF'` versus gate=MAIN `legitimate=False`), which is the common path, so the correction makes the defect more serious. The wrong shape had propagated into eight places, two of them dangerous: V-01(a) demanded unproducible evidence, and E-01's STOP condition would let an executor who correctly measures both roots refusing conclude the premise expired and abandon the plan | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-02 rewritten with both shapes measured and the authoring-HEAD proof; new F-13 records the non-reproduction and its cause; the Goal gains a NOTE WHICH SHAPE DEMONSTRATES IT paragraph; E-01 is told to measure the single-carrier shape and that both-roots-refuse on the two-carrier shape CONFIRMS rather than contradicts; E-01's STOP condition narrowed to the one real reversal; E-06 gains case (1b) as the tightening proof and relabels case (2) as the siblings-stay-unoverridden guard; V-01, V-02, V-06 and Required tests swept |
| PR-902 | MEDIUM | IN-SCOPE | E. Testing and verification | plan F-12, E-08, V-08, Required tests; bare suite at HEAD `816f4a2e0` | The baseline is a hard bar in three places ("pass count at or above 3419"). Review measures `3560 passed, 2 skipped, 3 warnings in 160.38s`, FULLY GREEN, with the named time-dependent failure PASSING, a drift of 141. The authored bar is therefore not a property of the tree, and worse, an executor holding it would treat the ABSENCE of `test_release_exempt_setter_roundtrip_and_parity` as a discrepancy when the plan itself says the failure is clock-dependent | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 carries both baselines with their HEADs and the drift; E-08, V-08 and Required tests all rewritten onto a by-node-id comparison against a re-derived baseline, explicitly stating that the known failure's absence is not a discrepancy |
| PR-903 | LOW | IN-SCOPE | F. Honest documentation | plan gate para 1 and the positional-bypass deferred row; `.aw/records/plans/executed/20260929-gatebypass-01-47ttnv-...ipd.md` `- Status: executed`; `.aw/records/plans/pending/20260929-posgate-01-2misq5-...ipd.md` `- Status: approved` | The gate's first paragraph calls `47ttnv` "pending against the adjacent spelling" while the Deferred row already cites its `executed/` path, so the plan contradicts itself. Its residue is carried by `2misq5`, an APPROVED pending plan this plan never names; a reviewer must re-derive whether that is a collision. Checked: `2misq5` declares only `tests/test_backlog_production.py` plus a backlog item, so it overlaps none of this plan's eleven scope paths | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate paragraph corrected to `47ttnv` EXECUTED and names `2misq5` with its non-overlap stated; the deferred row carries the same correction; new F-14 records all three status checks (`lsbd32` done and `fnb8pl` open both confirmed as claimed) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-02, the plan's stated defect, does not reproduce. Is the plan unnecessary, is the finding wrong, or is the shape wrong? | THE SHAPE IS WRONG: correct F-02 to the single-carrier split, which does reproduce, and sweep the eight places the wrong shape propagated into. | (a) REPLAN, rejected because the defect, the mechanism, the override design and E-02 through E-09 are all unaffected; only which fixture demonstrates the leak changed, and the corrected shape is the COMMON one, so the plan's value rises; (b) declare the plan unnecessary, rejected because the single-carrier shape measurably leaks (gate=LANE `True` versus gate=MAIN `False`) and the plan's own STOP condition names exactly that cell as the test of necessity, which it passes; (c) raise it as a blocking open question, rejected because the repository answered it: driving both shapes against both roots settles which one splits, with no human judgement needed; (d) leave F-02 and let E-01 discover it, rejected because V-01(a) demanded unproducible evidence and E-01's STOP condition could cause a correct measurement to abandon a real defect. | Two-tree `git worktree` fixture at HEAD `816f4a2e0`: two-carrier shape both roots `legitimate=False`; single-carrier shape gate=LANE `legitimate=True path='HANDOFF'` and gate=MAIN `legitimate=False`. Cause read at `check_engine.evaluate_blocking_close`'s `all(...)` fold and confirmed present at `8163b62ad`. Recorded as F-13. | yes |
| D-2 | Two suite baselines disagree and the authored one is a hard `>= 3419` bar. Pin the new number or change the bar? | CHANGE THE BAR to by-node-id against a re-derived baseline, recording both measurements. | Pinning `3560`, rejected because it will drift exactly as `3419` did (141 in under two days); keeping the authored bar, rejected because the tree is now green so the bar's own named failure is absent, which the plan would read as a discrepancy; exempting the test by name, rejected because that masks a genuine future regression in it. | Bare run at `816f4a2e0`: `3560 passed, 2 skipped, 3 warnings in 160.38s` with `test_release_exempt_setter_roundtrip_and_parity` passing; authored `1 failed, 3419 passed` at `8163b62ad`. Recorded as F-12. | yes |
| D-3 | `47ttnv` is executed and its residue plan `2misq5` is approved-pending and unnamed. Is that a collision needing an `Item-Dependencies` edge? | NO EDGE: correct the status, name `2misq5`, and record the measured non-overlap. | Declaring an `executed:` edge on `2misq5`, rejected because the two plans share NO file (`2misq5` declares `tests/test_backlog_production.py` and a backlog item; this plan declares eleven other paths), so an edge would serialize two independent plans for no benefit; leaving `2misq5` unmentioned, rejected because a reviewer reading "the adjacent spelling" must otherwise re-derive whether the adjacent work collides. | `- Status:` read on `47ttnv` (executed), `2misq5` (approved), `lsbd32` (done), `fnb8pl` (open); `2misq5`'s `- Scope-Paths:` compared against this plan's. Recorded as F-14. | yes |

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. Three findings, all FIXED, zero deferred, zero open. Structural lint
`conforming` with zero diagnostics and zero advisories at both `--phase author` and
`--phase review-finalize`. No unresolved blocking question, so readiness is `go-pending-approval`: the
plan passed review and awaits human sign-off.

A NOTE ON WHAT THIS PLAN GETS RIGHT. Its hazard analysis is unusually good and review confirmed every
piece of it by measurement: F-04's false-citation trap is real and is correctly forbidden at the gate;
the injected-callable five-positional trap that broke `9vglxd` is real and correctly handled with
keyword-only parameters; the two-host wrapper symmetry hazard is real; the verified-not-trusted
override is genuinely verifiable through the shared object store, with a working negative control; and
the plan explicitly refuses the smaller route (b) because it would widen an already-permissive arm.
The defect found here is a wrong demonstrating fixture, not a design error, and correcting it makes the
plan's case stronger.
