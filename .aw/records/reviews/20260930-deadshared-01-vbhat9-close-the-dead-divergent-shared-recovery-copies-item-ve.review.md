# Review findings: plan vbhat9

- Subject-Id: vbhat9
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-V01 (HIGH, fixed), PR-V02 (HIGH, fixed), PR-V03 (MEDIUM, fixed), PR-V04 (MEDIUM, fixed), PR-V05 (LOW, fixed), PR-V06 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `10c679bb`. The plan file was committed (`46c73da8`) and
byte-identical to the lane input (`diff` reported no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize` reports `conforming` after revision. The plan is `- Kind: child`,
so the `IPD-S407` orchestrator row check does not apply.

THIS PLAN'S MEASUREMENTS ARE UNUSUALLY GOOD AND I RE-RAN THEM RATHER THAN TRUSTING THEM. Nine of the ten
authored findings reproduce exactly:

- F-01: `oc_runipd.classify_recovery_disposition is runner_shared.classify_recovery_disposition` True, same
  for `agy_runipd` and for `build_verify_and_continue_notice`; `route_recovery_turn` False on both, the
  expected injecting wrapper. `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` is `frozenset()`.
- F-02: `rg -n "wip\(snapshot\)" --glob '*.py' .` exits 1 with no output. The string IS present in
  `git show 2d04ef8b:agent_workflows/runner_shared.py`.
- F-03: the dead body at `2d04ef8b` does filter with `subj.startswith("wip(snapshot):")`, and it does read
  `st.path` / `st.base_commit` where `worktree_lease.LaneState._fields` carries `worktree_path` and
  `base_sha`, so the `AttributeError` claim is real. The canonical prefix is
  `"WIP INTERRUPTED SNAPSHOT (not finished work):"`, so the dead predicate matched no real snapshot.
- F-04: `python3 -m pytest tests/test_recovone_single_definition.py -o addopts=""` -> `8 passed in 0.92s`.
- F-05: `--triples` reports exactly one entry, `StallWatchdog  shared copy identical to the hosts': False`,
  while the same run classes it `BOTH-DELEGATE` at `1.000`. MRO is
  `[StallWatchdog@oc_runipd, StallWatchdog@runner_shared, object]`, own members are `['__init__']` alone on
  both hosts, and the shared base carries all eight members including `_run`.
- F-06: reproduces TO THE DIGIT under a monkeypatched predicate: `triples 1 -> 0`,
  `sanctioned_wrappers 46 -> 47`, `real_forks 10 -> 9`, `identical_forks 4 -> 3`, `loose_residue 10 -> 9`,
  `loose_residue_agy_lines 388 -> 384`, `divergent_forks` and `co_defined` unmoved.
- F-08: `git log --diff-filter=D` resolves both deleted paths to `19313eed`; `MOVE_UNSETTLED` survives in no
  `.py` file. (One sub-claim corrected: `19313eed` deleted ELEVEN `test_rununify_*` files, not four.)
- F-09: the six required-keyword-only sets match what the plan and `4mdi4v` record.
- F-10: the AST census returns exactly three `build_lane_outcome` calls, one with `run_checked=` inside
  `integrate_lane_branch` and two inside `execute_item_core` after the local rebinding, so the plan's own
  self-correction is right and there is no third live instance.

I also verified the plan's PROPOSED work rather than only its findings: E-02's sweep passes at this HEAD with
an empty failure list and fails naming `StallWatchdog` under the unpatched predicate (so the guard is
discriminating, not vacuous); E-03's synthetic three-way fork is reported by the same core shape; E-04's case
drives live to `verify-and-continue` with `snapshot_only False`; and `support.load_module` does load
`tools/runner_fork_scan.py` as E-02 assumes.

TWO SERIOUS FINDINGS, both of which the authoring measurements could not have surfaced from the probes they
used.

PR-V01 is a defect in the fix itself, not in the diagnosis. E-01 as authored required only that a base be
`runner_shared.<same-name>`. I built that exact predicate and drove it over a synthetic
`class StallWatchdog(runner_shared.StallWatchdog)` carrying a second method `_run` that OVERRIDES a name the
shared base defines: it returned True. So a subclass whose logic genuinely diverges from the shared body
would have been promoted out of the reported triples into `sanctioned_wrappers` and disappeared from
`--triples` entirely. That is the suppression-rather-than-truth outcome E-01's own Expected outcome forbids
("empties `--triples` truthfully rather than by suppression"), and it is the same failure mode OQ-02
correctly rejected for the different-base case, so the plan already holds the standard it missed here. The
fix is free: I measured two independent tightened variants (own members a subset of `{"__init__"}`, and no
own member overriding a shared-base member) and BOTH produce a census byte-identical to the loose predicate
at this HEAD, because the two real host subclasses override nothing. E-01 now requires the constructor-only
body, with a class-level assignment disqualifying, and new E-07 / V-07 pin the refusal on three synthetic
cases.

PR-V02 is a cross-plan collision on a measured number, and it is live rather than hypothetical. Pending plan
`9oj6t2` (`.aw/records/plans/pending/20260929-baskrx-01-9oj6t2-...ipd.md`, Set `baskrx`) consumes the scanner
census as a NUMERIC ACCEPTANCE CRITERION: its E-06 requires `REAL FORKS` to move `10 -> 8` and
`byte-identical` `4 -> 2`, its V-06 demands that output pasted, and its F-1 names `StallWatchdog` as one of
the four byte-identical forks. E-01 moves that baseline to `9` / `3` BEFORE `9oj6t2` lifts anything. That
plan carries `- Status: reviewed`, `- Readiness: go-pending-approval` and `- Item-Dependencies: none`, so a
runner may dispatch it in either order, and its own E-01 gate says "if the re-measurement disagrees with
F-1, F-2, F-3 or F-6, stop and report" - where F-1 is precisely the figure E-01 changes. So the likely
outcome of shipping both as written is a CORRECT refusal on a stale number, costing a human round trip on
work that is not wrong. Worktree isolation does not help: the two plans' `- Scope-Paths:` are disjoint, so
there is no file conflict for a lease to catch; the collision is on a number. New E-06 records the change in
`9oj6t2`'s workflow history, deliberately as an append and not an amendment (see D-2 and OQ-04).

TWO CORRECTIONS, one of which is why PR-V02 went unseen.

PR-V03: F-07 asserted that `rg -l "runner_fork_scan|lift_drift_scan"` over `*.py` and `*.md` "matches only
the two tool files themselves". That is an artifact of ripgrep's default hidden-file exclusion, not a fact
about the repository: `.aw/` is a dot-directory, so the entire records tree was invisible to the probe. The
same pattern with `--hidden` matches 27 markdown files, one of which is `9oj6t2`. The finding's useful claim
survives (no TEST pins the scanner output: `rg -l ... tests/` exits 1), but the probe that produced it would
have hidden the plan-level consumer, so the row now states the correction and the method.

PR-V04: E-02's Expected outcome told the executor to expect "the scanner measures 56 co-defined symbols".
But 56 is the scanner's `co_defined`, the TWO-HOST intersection; E-02's sweep is a THREE-WAY intersection
(shared AND oc AND agy), which measures 42. An executor comparing against 56 would find a 14-symbol
shortfall and either chase a non-bug or widen the sweep to the wrong population. Per the live-artifact
convention the item now states the property and requires re-derivation, with 42 as context.

PR-V05 and PR-V06 are smaller. The gate was missing the honesty rule, the finalize-ownership statement, and
a scope fence for the path E-06 needs; and the P16 tension over an AST-enumerating test was argued only in
the conventions section, where a later reader could read P16's placement bullet as a refusal and delete the
guard. F-14 now records the two passing in-tree precedents that settle it, including the STRICTER
`test_add_output_mode_flags_not_reforked_in_hosts`, which asserts a per-host `FunctionDef` statement count by
AST and passes.

NOTHING ELSE WAS FOUND WRONG. The plan's central judgement - that `2yjc5l`'s reported defect is already
fixed and what the release is owed is proof plus the two residues - is correct and well evidenced. Its
refusal to touch `runner_shared.py` is the right fence for a release-blocking verification plan, its
`Carrier-Declined` reasoning on the deleted guards is sound, and its self-correction on the third
`build_lane_outcome` instance is exactly the honesty the record should carry. E-05's re-verification of
`4mdi4v` at the executed HEAD (rather than merely citing it) is better than the deferral convention requires.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-V01 | HIGH | IN-SCOPE | Rubric D (anti-regression), G (executability) | `.aw/records/plans/pending/20260929-deadshared-01-vbhat9-...ipd.md` E-01; `tools/runner_fork_scan.py::is_pure_delegation` | E-01's predicate as authored was a BARE INHERITANCE CHECK: any `ClassDef` with a `runner_shared.<same-name>` base counted as a wrapper. Measured returning True for a subclass overriding `_run`, a name the shared base defines, so a genuinely divergent subclass would leave `--triples` and join `sanctioned_wrappers` - suppression, not truth, which E-01's own Expected outcome forbids and OQ-02 rejected for the sibling case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires BOTH the same-name shared base AND a constructor-only body (own non-docstring members a subset of `{"__init__"}`, a class-level assignment disqualifying). New E-07 / V-07 pin the refusal on three synthetic cases (True / False / False). Two tightened variants measured producing a census identical to the loose one at this HEAD, so the strictness costs nothing. |
| PR-V02 | HIGH | UNDER-SCOPE | Rubric C (operability), G (dependencies and sequencing) | `.aw/records/plans/pending/20260929-baskrx-01-9oj6t2-...ipd.md` E-06 and F-1; that plan's `- Status:` / `- Readiness:` / `- Item-Dependencies:` bullets | E-01 invalidates a NUMERIC ACCEPTANCE CRITERION in another PENDING plan. `9oj6t2` E-06 requires `REAL FORKS 10 -> 8` and `byte-identical 4 -> 2` and its F-1 names `StallWatchdog`; E-01 moves the baseline to 9 / 3 first. That plan is `reviewed`, `go-pending-approval`, `Item-Dependencies: none`, so either may run first, and its own refusal condition ("if the re-measurement disagrees with F-1 ... stop and report") would correctly fire on a number this plan moved. Disjoint `Scope-Paths` means worktree isolation cannot catch it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-06 / V-06 append a dated history note to `9oj6t2` recording the moved baseline and the recomputed target (9->7, 3->1), explicitly as an APPEND that touches no status, readiness, checklist or finding of that reviewed plan. `.aw/records/plans/pending/` added to `- Scope-Paths:` and fenced in the gate to that one append. OQ-04 records the four options and why amendment and an `Item-Dependencies` edge were both rejected. |
| PR-V03 | MEDIUM | IN-SCOPE | Step 1 evidence quality | plan F-07; `rg -l --hidden "runner_fork_scan" --glob '*.md' .` | F-07's probe ran without `rg --hidden`, so the whole `.aw/` records tree was invisible and the row concluded "matches only the two tool files themselves". With `--hidden` the same pattern matches 27 markdown files, including the `9oj6t2` plan of PR-V02. The row's useful claim (no TEST pins the output) holds, but the method that produced it hid a live consumer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 rewritten to claim only what it proved (`rg -l ... tests/` exits 1), to state the hidden-file correction and the 27-against-0 measurement, and to name F-12 as what the flawed probe concealed. |
| PR-V04 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria) | plan E-02 Expected outcome; scanner `co_defined` | E-02 told the executor to expect a population "on the order of the scanner's 56 co-defined symbols", but 56 is the TWO-HOST intersection while E-02's sweep is a THREE-WAY one measuring 42. An executor comparing against 56 sees a 14-symbol shortfall and either chases a non-bug or widens the sweep to the wrong population. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and V-02 now name the three-way population, forbid comparing against 56, require re-derivation at execution time, and carry 42 as context rather than as the bar. New F-13 records both numbers with the measurement. |
| PR-V05 | LOW | UNDER-SCOPE | Step 4 execution contract | plan gate, final paragraph | The gate carried the scope fence and the never-push rule but not the hard-MUST honesty rule (paste actual runner output), not the conditional runner-versus-executor finalize ownership, and no fence for the `.aw/records/plans/pending/` path E-06 needs. It also stated a STOP directive loosely. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the honesty rule, the conditional finalize ownership (runner owns it under `aw oc run` / `aw agy run`; executor calls `aw ipd finalize` for a hand run), the out-of-scope-edit rule as make-then-justify with `--scope-reason`, and exactly two named STOP conditions (a census mismatch against F-06, and an E-07 negative case returning True). |
| PR-V06 | LOW | IN-SCOPE | Rubric D, project principle P16 | GUIDING_PRINCIPLES.md section 16; `tests/test_runner_shared.py::test_add_output_mode_flags_not_reforked_in_hosts` | The P16 tension over a test that parses production source was argued only in the conventions section. P16's "No architectural placement pins" bullet reads as a flat refusal, so a later reader could delete E-02's guard on principle. The repository already ships two passing precedents, one STRICTER than E-02, and neither was cited. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 records the AST-enumerates / `getattr`-decides split, cites the shipped constant sweep as the same shape and `test_add_output_mode_flags_not_reforked_in_hosts` as a stricter passing precedent, and states why the row exists (to stop a later reader deleting the guard). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's class branch must recognize a delegating subclass; how strict should the body test be, given the plan wrote none at all? | Require the own non-docstring body to be members only, with names a subset of `{"__init__"}`, so a class-level assignment or any second method disqualifies. | (a) Base-only, as authored: rejected, measured returning True for a `_run`-overriding subclass. (b) No own member overriding a SHARED-BASE member: equally correct and measured identical, but it needs the shared class parsed to evaluate, so it is more machinery for the same verdict. (c) An allowlist naming `StallWatchdog`: rejected by the plan's own E-01 prose and by OQ-02's fail-closed reasoning. | Probe over the committed `tools/runner_fork_scan.py::is_pure_delegation` plus three synthetic `ast.ClassDef` nodes; both tightened variants produce `triples=[] wrappers=47 real=9 ident=3 div=6 loose=9/384`, identical to the base-only predicate and to plan F-06. | yes |
| D-2 | `9oj6t2` is `reviewed` with `go-pending-approval` and pins census numbers E-01 moves. Amend it, order it, or inform it? | INFORM: a dated `## Workflow history` append naming the moved baseline and the recomputed target, touching no other field (plan E-06 / V-06, OQ-04). | (a) Do nothing: rejected, that plan's own refusal condition would fire on a stale number. (b) Edit its E-06 targets to 9->7 / 3->1: rejected, rewriting a `reviewed` plan's acceptance criteria from another Set is a silent cross-plan amendment. (c) Declare an `Item-Dependencies` edge: rejected, the grammar admits only `executed:` / `exists:` / `state:` edges and neither plan is the other's prerequisite, so an edge would misstate the relation. (d) Re-review `9oj6t2`: outside this review's one-plan ledger. | `9oj6t2` front matter (`reviewed`, `go-pending-approval`, `Item-Dependencies: none`) and its E-06 / F-1 text; `Item-Dependencies` grammar in `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 2.7. | yes |
| D-3 | Does GUIDING_PRINCIPLES P16 forbid E-02's guard, which parses production source to enumerate symbol names? | NO. Permitted on the AST-enumerates / `getattr`-decides split, and recorded as F-14 so it is not re-litigated. | Rejecting E-02 and demanding a purely behavioral form: rejected because the question the guard asks ("does a shared def exist that no host reaches?") has no behavioral surface - a dead definition by construction changes no observable output, which is exactly why the defect hid for a year. | GUIDING_PRINCIPLES.md section 16; the shipped `test_no_divergent_codefined_constants_in_runner_shared` (same split, `1 passed`) and the stricter `test_add_output_mode_flags_not_reforked_in_hosts` (per-host AST statement count, `1 passed`). | yes |
| D-4 | Should E-07 be a throwaway probe whose evidence is pasted, or a committed test? | A probe, pasted as V-07 evidence. | A committed test: rejected as redundant, because E-02's guard already imports the same predicate and would itself start failing if the predicate were loosened to admit an overriding subclass, so a second committed assertion pins the same property twice. | Plan E-02 imports the predicate via `support.load_module`, verified loading `tools/runner_fork_scan.py` from `tests/`; the shipped constant sweep is the precedent for one guard per property. | yes |

No `Reversible: no` decision was taken in this round.
