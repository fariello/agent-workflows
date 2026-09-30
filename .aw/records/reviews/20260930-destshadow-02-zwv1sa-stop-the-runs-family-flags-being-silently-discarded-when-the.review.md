# Review findings: plan zwv1sa

- Subject-Id: zwv1sa
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (HIGH, fixed), PR-1002 (MEDIUM, fixed), PR-1003 (MEDIUM, fixed), PR-1004 (LOW, fixed), PR-1005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY MATERIAL CLAIM, INCLUDING BUILDING A FIXTURE AND REPRODUCING THE DEFECT END TO END.
This plan's factual core is unusually strong and essentially all of it holds:

- F-01 verbatim: `argparse._SubParsersAction.__call__` on CPython 3.14.6 does
  `subnamespace, arg_strings = subparser.parse_known_args(arg_strings, None)` then
  `for key, value in vars(subnamespace).items(): setattr(namespace, key, value)`.
- F-02 REPRODUCED END TO END, which took two attempts and is worth recording: my first fixture wrote
  `.aw/state/runs/...` and `discover_run_dirs` found nothing, because `state_root()` resolves to an
  out-of-tree per-project path; the run must live under `<repo>/.aw/runs/`. With a discoverable run,
  `aw runs --dir <tmp> list` prints `no matching runs found` at exit 0 while
  `aw runs list --dir <tmp>` prints `run-20260101T000000Z-1`. Silent, plausible, exit 0 both ways.
- F-04: `releases --dir X list` and `releases list --dir X` both resolve `dir='/tmp/XYZ'`; the same
  comparison on `runs` gives `None` then `'/tmp/XYZ'`. The remedy is proven in this tree.
- F-05: applying `default=argparse.SUPPRESS` in memory to the 26 colliding operational actions makes
  both orderings resolve `'/tmp/XYZ'`, leaves a bare `runs list` with NO `dir` attribute (so
  `getattr(ns,'dir',None)` still yields `None`), and `runs --active list` correctly resolves `True`.
- F-06: zero direct `args.<dest>` reads for all fourteen affected dests across the three consumer
  modules. I also widened the search to the WHOLE package, which the plan's E-03 promises: four
  `args.dir` hits exist elsewhere, and I checked each - `leak_sanitizer` has its own standalone
  parser, `work_cmd` WRITES not reads, `runner_shared`'s is a docstring, and `cli.py`'s `args.set`
  is guarded by a preceding `getattr` test. None is reachable from a `runs` leaf. F-06 holds.
- F-07: `tests/test_runs_repo_alias.py` and `tests/test_run_viewer.py` are green (62 passed).
- F-08 exactly: `runs list`'s `--dir` action IS the family's action object (identity true) and all
  twelve other leaves' are distinct.
- F-12: every one of the twenty alias shapes places the flag AFTER the leaf, so the suite is blind
  to this defect by construction.

THE ONE SERIOUS FINDING IS AN UNDISCLOSED SCOPE NARROWING WITH A WORSE DEFECT INSIDE IT (PR-1001).
Every census in this plan silently counts "non-presentation" dests. F-10 uses the word once, in
passing, and no section states that `--json`, `--agent`, `--color`, `--no-color`, `--interactive` and
`--no-interactive` were EXCLUDED, why, or that they are affected at all. Measured at review: they are
lost by the identical mechanism, and the consequence is HARDER than the `--dir` case the plan fixes.
End to end, `aw runs --json list --dir <tmp>` prints HUMAN TEXT at exit 0 where
`aw runs list --json --dir <tmp>` prints the JSON object. A wrong `--dir` gives a human a plausible
empty table they may question; a discarded `--json` hands a machine consumer unparseable prose with no
signal, on the surface `docs/cli-output-contract.md` governs. It also affects the `run` writing noun,
whose family declares these flags even though it declares no `--dir`, which bounds OQ-02's "no
collision to fix" more narrowly than that question states. Step 0 makes this sharper rather than
softer: it cites `common_upgrade` fixing exactly `--json`/`--agent` with `SUPPRESS` as the precedent
legitimising the remedy, and then does not apply it to the same flags one family over. I did NOT widen
the plan, because 78 further presentation pairs under `runs` alone plus the `run` noun plus the output
contract is a size and blast-radius judgement that belongs to the maintainer. I made the exclusion
EXPLICIT in Scope, F-10, E-02 and a new deferral row with item `0b290s` as carrier, recorded the
measurement as F-15, and raised OQ-03 with a recommendation.

PR-1002: the 29-pair figure reproduces only if the `targets` POSITIONAL is counted. Measured, option
dests alone give 26 over 13 leaves; the three remaining are `targets` re-declared by `list`, `analyze`
and `export`. The plan never states the rule, so an executor following E-01(c) gets 26, and worse, an
E-04 derivation keyed on `a.option_strings` would leave three pairs broken while reporting a passing
lower bound. The Scope section names the `targets` positional as in scope, so this is an internal
inconsistency rather than a scope change.

PR-1003: the gate instructed `aw ipd begin` and `aw ipd finalize` unconditionally. Under a runner both
refuse a worker-role process (`AW-LIFECYCLE-ROLE-001`), so as written the executor is sent into a
refusal on the runner path. The gate also carried no scope-fence declaration and no make-then-justify
route, though it did carry an unusually good set of behavioral prohibitions.

WHAT I DID NOT WEAKEN, and what is genuinely strong here. The plan implemented and measured its own
fix before proposing it, which is why F-05 is evidence rather than a hypothesis. Its insistence on
seeing the new test RED first is correct and I left it intact. Its P16 discipline is precise: it
forbids asserting that a declaration says `SUPPRESS` and explains why (such a pin would pass while the
value was still lost), and it permits walking a BUILT parser's `_actions`, which is the right line.
The F-08 shared-action trap is a real implementation hazard found by identity comparison rather than
assumed. The `releases` control in E-04 is the right way to prove the test measures something. And the
deferral of a build-time refusal is well-argued on a cost basis rather than dismissed.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | UNDER-SCOPE | B. Security / F. UX / A. Correctness (an undisclosed narrowing hiding a worse defect) | Measured at review: `runs --json list` resolves `json=False`, `runs list --json` resolves `json=True` (same for `--agent`, `--no-color`). END TO END on a temp repo with one discoverable run, `aw runs --json list --dir <tmp>` prints human text at exit 0 while `aw runs list --json --dir <tmp>` prints JSON. `run --json start run-x` loses it too. `result_types.select_output` reads each through `getattr(args, name, <default>)` | **Every census in the plan counts "non-presentation" dests and no section states that the presentation flags were EXCLUDED, why, or that they are affected at all.** They are lost by the identical mechanism with a HARDER consequence: a discarded `--json` hands a machine consumer unparseable prose at exit 0 on the surface `docs/cli-output-contract.md` governs, where a discarded `--dir` at least gives a human a questionable empty table. Step 0 cites `common_upgrade` fixing exactly `--json`/`--agent` with `SUPPRESS` as its precedent and then does not apply it to those flags | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | The FINDING (an undisclosed narrowing) is fixed: the exclusion is now explicit in `- Scope:`, in F-10's row, and as an E-02 prohibition with the reason; F-15 records the measurement including the `run`-noun bound; a new deferral row carries it on item `0b290s`; OQ-03 raises the residual SCOPE CHOICE to the maintainer with a recommendation (exclude, on size) and states what changes if overruled. Not widened unilaterally: 78 further presentation pairs plus the `run` noun plus a public output contract is a blast-radius decision, not a reviewer's |
| PR-1002 | MEDIUM | IN-SCOPE | A. Correctness (a count that does not reproduce under the stated rule) | Measured at review: colliding OPTION dests excluding presentation and `SUPPRESS` give 26 pairs over 13 leaves; adding the family `targets` POSITIONAL re-declared by `list`, `analyze` and `export` gives exactly 29 | **The plan's 29-pair figure reproduces only if positionals are counted, and no section says so.** E-01(c) asks the executor to re-derive the count and they will get 26; worse, an E-04 derivation keyed on `a.option_strings` would omit three pairs and still report a passing lower bound, leaving `list --targets` broken while the Scope section names it in scope | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires the `targets` positional be included with the measured 26-versus-29 split; E-04's derivation rule states "a leaf action whose dest collides with a family action's dest, over BOTH options and positionals", with the SUPPRESS and presentation exclusions named; V-04 requires the option/positional breakdown reported, not just the total, and states that a 26 total means positionals were dropped; F-16 records it |
| PR-1003 | MEDIUM | UNDER-SCOPE | G. Plan executability (an instruction that refuses on the runner path) | The gate read "Execute through `aw ipd begin` before any edit and `aw ipd finalize` for the terminal transition" with no condition. Under `aw oc run` / `aw agy run` both refuse a worker-role process with `AW-LIFECYCLE-ROLE-001` | **The lifecycle instruction was unconditional where ownership is conditional, so a runner-driven executor is sent into a refusal.** The gate also carried no scope-fence declaration and no make-then-justify route for a necessary out-of-scope edit, on a plan touching one of the repository's highest-contention files | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a declaration-style scope fence (explicitly not a tripwire, with the `--scope-reason`/`--scope-ack` route) whose one STOP condition is a genuine concurrent-edit conflict rather than a scope question, and a conditional transition-ownership paragraph naming the refusal code |
| PR-1004 | LOW | IN-SCOPE | A. Correctness (a resolved question stated wider than it is true) | Verified at review: the `run` family declares only `agent color help interactive json no_color no_interactive`, so there is indeed no family `--dir`; but `run --json start run-x` resolves `json=False` against `run start run-x --json` resolving `True` | **OQ-02 concludes "there is no collision to fix" on the `run` noun, which is true of `--dir` and false of the presentation flags.** As written it reads as a clean bill of health for a noun that does carry an instance of the same defect | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 gains the measured bound and restates its conclusion as "no OPERATIONAL collision on the `run` noun", pointing at OQ-03 for the presentation case |
| PR-1005 | LOW | IN-SCOPE | E. Testing (a stale baseline figure) | F-13 recorded `3246 passed, 2 skipped` at HEAD `69a31fca`; measured bare at review, `3387 passed, 2 skipped, 3 warnings in 59.29s`, same 207-deselected notice | **The authoring baseline has already moved by 141 tests**, which does not invalidate anything (the plan tells the executor to re-derive) but leaves a figure a reader may anchor on when comparing by node id | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests section records the review-time baseline beside the authoring one and states plainly that both are historical; F-17 records the measurement as confirmation of the re-derivation instruction rather than as a defect |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-1001: the presentation flags are lost by the same mechanism with a worse consequence. Widen the plan to fix them, or document the exclusion and escalate? | DOCUMENT the exclusion explicitly, record the measurement, carry it on item `0b290s`, and raise OQ-03 to the maintainer with a recommendation to exclude | (a) Widen E-02 and E-04 to cover all presentation pairs under `runs`; (b) widen to `runs` and `run` both, since `run` is affected too; (c) leave the plan as authored, treating the narrowing as implicit in F-10's wording | Option (c) is the finding and is the one option I rejected outright: an unstated narrowing means the next reader sees a census that excludes a live defect and concludes the defect does not exist, which is exactly how these 29 pairs accumulated (F-12). Between fixing and deferring, I declined to widen because the numbers make it a different plan: 78 further presentation pairs under `runs` alone against 29 operational ones, plus the `run` writing noun the plan deliberately does not touch (OQ-02), plus `docs/cli-output-contract.md` as the governing surface and `tests/test_flag_surface_uniformity.py` as the module that owns presentation-flag coverage. That is a size and public-contract judgement, which `AGENTS.md` reserves for the human. What a reviewer CAN settle is that the exclusion must be visible and carried, so it cannot vanish, and that the remedy is known-safe if the maintainer says yes (`select_output` reads all six through `getattr` with matching defaults, measured) | yes |
| D-2 | PR-1002: the 29 figure needs positionals. Correct the figure to 26, or state the rule that yields 29? | STATE THE RULE (collisions over options AND positionals) and keep 29 | (a) Change every occurrence of 29 to 26 and scope E-02 to options only; (b) leave 29 unexplained, since the plan already says to re-derive | Option (a) would silently DROP three real pairs, including `list`'s `targets`, which the `- Scope:` section names as in scope and which loses its value exactly like any other dest; that is a narrowing disguised as a correction. Option (b) leaves an executor whose honest re-derivation disagrees with the plan, and the plan's own lower-bound convention would let them proceed at 26 having left three pairs broken. Stating the rule makes the number reproducible from the parser rather than from this document, which is the standard the plan itself sets for every other count | yes |
| D-3 | PR-1003: should the scope fence carry a "STOP on an out-of-scope edit" directive, given this plan touches the highest-contention file in the repo? | NO: declare the fence and route an out-of-scope edit through `--scope-reason`; reserve STOP for an unresolvable concurrent-edit conflict | (a) Add a STOP-and-report directive for any out-of-scope edit, which the file's contention arguably justifies; (b) add no fence at all, since the gate already carries strong behavioral prohibitions | Option (a) is forbidden by the 2026-09-01 maintainer ruling recorded in the review workflow: that wording propagated into 224 executed plans and contradicts the work done to stop `aw oc run` stranding unfinished turns; the correct requirement is that an out-of-scope edit be MADE and then JUSTIFIED, which `aw ipd finalize` already enforces. Option (b) leaves the runner nothing to reconcile the diff against. The contention concern is real and is answered by the narrow STOP the fence does carry (a concurrent edit that cannot be safely combined), which is the genuinely-unsafe case the same ruling keeps | yes |
