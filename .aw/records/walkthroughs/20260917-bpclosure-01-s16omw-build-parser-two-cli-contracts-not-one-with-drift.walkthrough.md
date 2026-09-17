# build_parser: two CLI contracts, not one with drift

- Date: 2026-09-17
- Plan: `.aw/records/plans/executed/20260915-rununify-10-s16omw-split-build-parser-into-a-shared-core-and-a-thin-host-hook.ipd.md`
- Id: s16omw
- Set: rununify (Order 10)
- Execution HEAD: `4a1bb873e68d8c5a52a3c735a1d5a04c2ef11adf`
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us

## What this plan did, and what it did not

Plan `s16omw` is named "split `build_parser` into a shared core and a thin host hook". It did NOT
perform that split. As re-scoped at its own 2026-09-16 review it is a measure-and-guard plan: E-01
measures, E-02 pins the per-host flag contract, E-03 accounts for what is already shared, E-04
delivers this analysis, and E-05 guards what was measured. Every one of the five items was performed.

This document is E-04's deliverable. It is a TRACKED record rather than a lane note, deliberately:
the lane submission tree is gitignored, which is a correction sibling `yrqyxb` had to make after the
fact.

## The measurement, reproduced at execution HEAD

Every number below was re-derived at `4a1bb873`, not copied from the review.

| Quantity | Review (2026-09-16) | Execution HEAD | Verdict |
|---|---|---|---|
| Raw source lines (oc / agy) | 347 / 264 | 352 / 266 | Reproduces; drifted by 5 and 2 lines |
| Normalized code lines (oc / agy) | 46 / 47 | 46 / 47 | Exact |
| Differing normalized lines | 47 | 23 identical, so 23 oc-side and 24 agy-side differ | Reproduces (the review's "47" is the SUM of both sides) |
| SequenceMatcher similarity | 0.4946 | 0.4946 | Exact |
| Flag partition | 17 shared / 7 oc-only / 10 agy-only | 17 / 7 / 10 by source literal; 51 / 8 / 8 live | Reproduces by the review's method; see below |
| Closure free names | 7, of which 2 still double-defined | 7, of which 2 still double-defined | Exact |
| String-literal share (oc / agy) | 50% / 41% | 52.1% / 42.0% | Reproduces |
| Source-inspection pins on `build_parser` | 0 | 0 (across 35 test files that touch it) | Exact |
| `RUN_POLICY_FLAGS` rows, calls per host | 12, 2 | 12, 2 | Exact |

### The one number that moved, and why both values are correct

The review recorded the flag surface as 17 shared / 7 oc-only / 10 agy-only. That figure is a count
of option-string LITERALS written inside each `build_parser`, and it reproduces exactly by that
method. It is not, however, what an operator meets, because it cannot see two whole classes of flag:

1. a `--no-X` that `argparse.BooleanOptionalAction` auto-generates from a registered `--X`, and
2. anything a shared helper registers, which here is 21 live option strings coming from the twelve
   `RUN_POLICY_FLAGS` rows plus the `--quiet`/`--raw`/`-v` set from `_add_output_mode_flags` and the
   whole `stop` subparser from `runner_stop.add_stop_parser`.

Counted on the LIVE parser objects the partition is 51 shared / 8 oc-only / 8 agy-only. The
difference is not an error in the review; it is two different questions. The literal count is what a
source-level de-duplication changes. The live count is the operator-visible contract. Both are now
pinned, by the method that produced each, in
`tests/test_rununify_build_parser.py::TheFlagPartitionIsPinnedByBothMeasurementMethods`, together
with an assertion that the two methods still DISAGREE, so that nobody later "fixes" one to match the
other.

Two members also moved. `--no-auto` appears in the live oc-only set because `--auto` is a
`BooleanOptionalAction`; and `--no-audit`/`--no-verify` are LIVE-shared (both hosts register those
spellings) while being literal-agy-only, which is precisely the F-7 trap: the two hosts spell the
same flag and mean different things by it.

## The Concern is wrong about this symbol, and the plan's own F-1 is right

The plan's Concern says "most of the divergence is DRIFT in shared logic rather than genuine host
specificity". That sentence is the boilerplate shared by all five split children, and for this symbol
the measurement refutes it. 23 identical normalized lines out of 46 and 47 means the two functions
share half their content; similarity 0.4946 is the LOWEST of the five large functions, against 0.851
for `execute_item` and 0.9345 for `initialize_run`. F-1 in the same plan says this is "the MOST
host-specific of the five", and F-1 is correct.

An executor who trusted the Concern would go looking for drift to reconcile and would find two
intentionally different CLI contracts that agree on a spec-governed core which is ALREADY shared.

## (a) The residual payoff against the cost

E-03's accounting, in numbers rather than impressions:

**What is already shared.** `runner_shared.register_run_policy_flags` registers the twelve
spec-governed `RUN_POLICY_FLAGS` rows and is called exactly twice per host (`start` and `resume`).
Those twelve rows account for 21 of the 51 shared live option strings. Three more shared helpers are
already single-implementation and reached from both hosts: `runner_stop.add_stop_parser` (the entire
`stop` subparser, 8 option strings), and the two still-forked-but-called helpers below.

**What relocating the function would actually remove.** 23 identical normalized code lines. That is
the CEILING, and it is now pinned as `IDENTICAL_NORMALIZED_LINES = 23`. Those 23 lines are, verbatim
from the measurement: the `def` line, the `add_subparsers` call, four `add_parser` calls (`start`,
`resume`, `status`, `report`), the two `_add_output_mode_flags` calls, one
`register_run_policy_flags` call, the `add_stop_parser` call, the `return`, and nine byte-identical
`add_argument` registrations (`--run-id`, `--no-self-finalize`, `--no-isolate-worktree`,
`--max-items-per-session` twice, `--repo` three times, `run_id` twice, `--retry-incomplete`).

**What it would cost.** Parameterizing 16 host-specific option strings (8 each way) and 13,956
characters of divergent help and description text (8,761 on oc, 5,195 on agy: 52.1% and 42.0% of each
function's source). The help text is not host names sprinkled through shared prose. oc's `start`
description documents the `as <profile>` positional clause, per-field precedence, and profile
freezing, a subsystem agy lacks entirely (zero `runner_profiles` references in agy against 17 in oc);
agy's documents clean-session skeptical self-validation. A host-name substitution cannot turn one
into the other, and imposing one host's help on the other is an operator-visible change this plan
forbids itself.

**So the trade is: remove 23 duplicated lines, add a parameter surface of 16 flag strings and ~14,000
characters of text.** That is the honest arithmetic, and it is the arithmetic the maintainer's
directive has to be applied to rather than around.

## (b) The oc-preferred ruling cannot apply here, and the code says so

The Set's rule is to resolve a difference to the `oc_runipd` version except where the difference is a
real capability. For this symbol one difference is neither drift nor a capability gap but an
INCOMPATIBLE CONTRACT, measured live:

| Spelling | oc dest (`start`) | agy dest (`start`) |
|---|---|---|
| `--validate` | `validate` | `validate` |
| `--no-validate` | `validate` | `validate` |
| `--verify` | `validate` | ABSENT |
| `--no-verify` | `validate` | `no_verify` |
| `--audit` | `validate` | `no_verify` (as `--no-audit`); `--audit` itself ABSENT |
| `--no-audit` | `validate` | `no_verify` |

On `resume`, agy registers NONE of the six.

agy defends this with a build-time guard oc does not have,
`assert_verification_flags_are_distinct` (`agent_workflows/agy_runipd.py:2034`), called at the end of
its `build_parser`. Its docstring records the hazard verbatim:

> `BooleanOptionalAction` auto-generates a `--no-X` for every option string it is given, so
> registering `--validate` with oc's alias list (`--verify`, `--audit`) would generate `--no-verify`
> and `--no-audit`, which this parser already declares. With the default `conflict_handler` that
> raises at build time and is impossible to miss. With `conflict_handler="resolve"` it does something
> far worse and SILENT: the new action STEALS `--no-verify`/`--no-audit`, and the shipped spelling
> stops meaning what every existing invocation and every piece of documentation says it means.

**Both branches of that docstring were EXECUTED, not taken on trust.** Registering oc's alias list on
agy exactly as a naive oc-preferred split would:

```
E       argparse.ArgumentError: argument --validate/--no-validate/--verify/--no-verify/--audit/--no-audit: conflicting option strings: --no-verify, --no-audit
```

And the silent branch, reproduced in isolation with `conflict_handler="resolve"`:

```
after resolve-handler theft: namespace = Namespace(validate=False)
has no_verify attr: False
--no-verify now resolves to dest: validate
```

`args.no_verify` ceases to exist, so agy's freeze site reads `False` unconditionally: verification
silently OFF by default on the host whose entire posture is verification ON. This is an A / NOT-A
case, not an oc-preferred case, and it is now pinned in both directions by
`tests/test_rununify_build_parser_characterization.py::TheVerificationDestAsymmetryIsPinnedPerHost`.

## (c) The orphaned `_add_output_mode_flags`

Of the closure's seven free names, only two are still double-defined: `_add_output_mode_flags` and
`_detect_driver_command`. F-8 says the first is owned by no sibling plan, and that reproduces:

* child 04 (`tx6q0h`, pending/approved) lifts `_detect_driver_command` and explicitly assigns
  `_add_output_mode_flags` to child 03;
* child 03 (`i3d6ml`, pending/approved) was re-scoped at its own review from 48 symbols to 9 (groups
  A and B). `_add_output_mode_flags` is in group H, which the re-scope dropped.

So `_add_output_mode_flags` is currently owned by NOBODY.

**DISPOSITION: it should NOT move under this plan, and the reason is scope rather than difficulty.**
This plan as re-scoped changes no product code, and lifting a shared helper is product code. Two
further facts decide where it belongs. First, the two bodies genuinely DIFFER (asserted, so the
orphan status stays meaningful), so lifting it needs a body decision and not just a move; the
difference is that agy's help text names its own host. Second, it registers three operator-visible
option strings (`--quiet`, `--raw`, `-v`/`--verbose`) on two subparsers per host with a deliberate
`verbosity_default` asymmetry (0 on `start`, `None` on `resume`, so an omitted `-v` does not reset a
frozen tier). That asymmetry is now characterized behaviorally on BOTH hosts by
`test_resume_leaves_verbosity_absent_so_a_frozen_tier_survives_on_both_hosts`, so whichever plan
takes the lift inherits a test that already spans both hosts.

RECOMMENDED OWNER: child 03 (`i3d6ml`), by re-adding group H to its scope, since that plan already
owns the "lift a non-conflicting shared symbol" mechanism and its `tests/test_rununify_lift.py`
already carries the named-table pattern. Failing that, a new precursor child. This is filed as a
defect finding, so it has a durable carrier rather than living only in this prose.

## (d) Route recommendation

The maintainer resolved OQ-03 on 2026-09-16 with a Set-wide directive: at the end of the Set there
should be one shared code base containing 100% of the otherwise redundant code, i.e. route (A) as the
OBJECTIVE, with route (B)'s ordering permitted as a tactic. So the question this plan answers is not
"should the split happen" but "what does 100% de-duplication MEAN for this symbol, and what is the
next honest step".

**RECOMMENDATION: route (B) as the tactic, with an explicit statement of what route (A) can and
cannot mean here.**

What route (A) CAN mean for `build_parser`: the 23 identical lines become one shared skeleton builder
in `runner_shared` that creates the parser and the five subparsers and registers the byte-identical
`--repo`/`run_id`/`--json`/`--run-id`/`--max-items-per-session`/`--no-self-finalize`/`--no-isolate-worktree`
arguments, with each host then adding its own flags and its own help. That removes the whole
measured redundancy, which is what the directive asks for.

What route (A) CANNOT mean here, and this is the part that needs stating rather than discovering
mid-refactor: it cannot mean ONE function that emits both hosts' flag surfaces, because the two
surfaces are 16 strings apart and one of those differences is the verification-dest incompatibility
in (b). A single function producing both would need either a host branch inside the shared core, or a
caller-supplied dict of everything host-specific. The first is the duplication this Set exists to
remove wearing a different shape, which is exactly the mechanical test this plan's own OQ-01 states.
The second reduces the shared core's contribution to the skeleton, i.e. to route (B). So route (B) is
not a lesser version of route (A) for this symbol: it is what route (A) resolves to once the
verification asymmetry is respected.

**Sequencing.** The two forks in the closure should land first, because after they do the shared
skeleton has NO remaining host-specific dependency: `_detect_driver_command` is child 04's and
`_add_output_mode_flags` needs the owner named in (c). Both are one-symbol lifts with behavioral
pins already written. Then the skeleton extraction is a mechanical move with zero source-inspection
pins to re-base, which is unique in this Set. Do not re-order plans by hand; the runner sorts by
dependency depth and re-checks at dispatch, so declared `Item-Dependencies` are sufficient.

**Why this plan did not just do the skeleton extraction.** Two reasons, both about authority rather
than difficulty. Its own re-scope, written into the E-items and the scope check at review, states
that it changes NO product code and that E-04's deliverable is analysis; performing the extraction
would exceed the scope the plan was approved with. And its declared `Item-Dependencies: executed:tx6q0h`
is UNMET at execution HEAD (`tx6q0h` is `approved` in `pending/`, not `executed`), so the one
prerequisite the plan itself names has not landed. Doing the extraction anyway would have meant
lifting a symbol another approved plan owns, in a plan whose dependency is unmet, against its own
stated scope. The maintainer's directive is a Set-level objective, and it is served better by an
accurate map plus guards than by one child reaching across two siblings' scopes.

## (e) Does the spec acknowledge the per-host asymmetry? No.

Spec `25kzda` 2.1's grammar block declares neither `--validate` nor `--verify` nor `--no-verify`, so
the twelve `RUN_POLICY_FLAGS` rows are the only part of this surface the spec governs.
`tests/test_run_flag_surface.py` therefore cannot see the F-7 asymmetry at all: it checks the surface
against the SPEC, in both directions, for the flags the spec declares.

The consequence worth reporting: the runner flag `--no-verify` is discussed in the spec only in
Section 2.1's amendment note and in the `RUN-COMMIT-GATEWAY` rows, and there only to separate the
RUNNER sense from the GIT sense. Nothing in the spec says that the runner flag means
`--no-validate` on agy and is an alias of `--validate`'s tri-state on oc, nor that `--verify` and
`--audit` do not exist on agy at all. So the spec is INCOMPLETE with respect to a live, shipped,
operator-visible per-host difference. Fixing that is not this plan's job (this plan registers no flag
and so forces no amendment), but the gap is real and is filed as a defect finding.

## What this plan delivered

* **E-01**: both measurements at execution HEAD, including the literal-versus-live reconciliation,
  the six verification dests per host, the seven-name closure classification, and confirmation of
  ZERO source-inspection pins across 35 test files.
* **E-02**: `tests/test_rununify_build_parser_characterization.py`, 18 tests. The per-host flag
  contract as a table (so an addition or removal fails naming the flag), the verification-dest
  asymmetry asserted directly in both directions, agy's build-time guard proven still called and
  still non-vacuous, and behavioral characterization of what each parser PRODUCES on both hosts.
* **E-03**: the residual-payoff accounting above, in lines and characters.
* **E-04**: this analysis.
* **E-05**: `tests/test_rununify_build_parser.py`, 21 tests. Both flag partitions pinned by the
  method that produced each, the closure classification pinned, the residual payoff pinned as a
  number, and the inverse assertions that make the un-performed split MECHANICAL: both forks still
  forked, `runner_shared` holds no `build_parser`, neither host delegates, and no source pin has
  appeared.

## Defects found

Three, each filed as a backlog item so it has a durable carrier:

1. `_add_output_mode_flags` is owned by no pending plan, having been assigned by child 04 to child 03
   and then dropped in child 03's re-scope.
2. Spec `25kzda` does not document the per-host verification-flag asymmetry, and its contract test
   structurally cannot catch it.
3. 31 tests fail in a lane because the driver exports `AW_EXECUTION_ROLE=worker` and five test files
   call `aw ipd begin`/`finalize` directly without neutralizing it. The suite is green with the
   variable cleared, so this is a test-isolation defect, not a product defect, but it makes every
   lane's baseline red and invites an executor to attribute the failures to their own work.
