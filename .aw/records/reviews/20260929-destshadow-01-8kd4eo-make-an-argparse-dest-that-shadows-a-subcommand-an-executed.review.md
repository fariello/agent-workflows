# Review findings: plan 8kd4eo

- Subject-Id: 8kd4eo
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-501 (HIGH, fixed), PR-502 (HIGH, fixed), PR-503 (HIGH, fixed), PR-504 (MEDIUM, fixed), PR-505 (MEDIUM, fixed), PR-506 (LOW, fixed), PR-507 (LOW, fixed), PR-508 (LOW, fixed)

## Round 1

Reviewed at HEAD `7b2ff77b` in an isolated review lane. The plan file was tracked, unmodified, and
byte-identical to the lane input (`diff` reported no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported exit 0 (`outcome: clean`) with one
advisory, `IPD-Z602` against E-04, BEFORE semantic review; `--phase review-finalize` reports `conforming`
with NO advisory after revision, the advisory having been cleared by rewriting E-04 to one concern rather
than dismissed.

I DID NOT READ THIS PLAN'S NUMBERS; I RE-RAN ITS WORK, AND TWO OF ITS THREE LOAD-BEARING CLAIMS DID NOT
SURVIVE. That is the headline, and it matters because those two claims are the entire justification for
substituting a different remedy from the one the backlog item prescribes.

WHAT REPRODUCED EXACTLY. F-01 is exact to the digit: re-pointing `integration-lock`'s `locked_command`
action's `dest` to `command` and dispatching `["integration-lock","--status","--dir","."]` returns
`rc: 2`, prints `stdout lines: 215` whose first line is
`usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |`, and writes NOTHING to stderr
(`stderr: ''`), with `looks like top-level help: True`. F-02's mechanism is exact. F-03 reproduced: the
walk reports `cli: canonical=151 parsed_ok=151 findings=0` and zero findings on the other six builders.
F-05 reproduced verbatim, including the finding string: clean `[]` against mutated
`[('integration-lock', "command=[] expected 'integration-lock'")]`. F-06's progression reproduced at four
of its five stages (86, 136, 150, 151). F-08's clean-tree narrowing counts reproduced exactly
(1160 -> 33 -> 30 -> 29, the 29 survivors being the `runs` pairs alone). OQ-01's subparsers-dest census
reproduced (`cli` 23, the two runners and `upgrade_rehearsal` 1 each, the other three 0). All cited
anchors resolve: `cli.py`'s `dest="locked_command"` comment, `command_surface.discover_parser_leaves`'s
alias docstring with its 63-leaf figure, `tests/conformance_matrix.py`'s
`"usage_error",  # invalid flag -> exit 2`, `tests/test_flag_surface_uniformity.py`'s five-entry
`SAMPLED_PARSED_SUBCOMMANDS`, `_ViewerOrLeafSubParsersAction`, spec `ipd-structure-and-linting`
Section 10.2, backlog `sq1go0` (live, `open`), and `s6om7k`.

WHAT DID NOT (PR-501, PR-502). F-07 claims the backlog item's literally prescribed rule "FIRES 1160 TIMES
on a clean tree" and is therefore unimplementable. It fires ZERO times. The item's words name an
"ANCESTOR SUBPARSERS ACTION's `dest`", which is the 23 subparsers dests; authoring measured a BROADER
rule whose ancestor set is every dest seen anywhere on the chain, and that one is where 1160 comes from. I
implemented both. The item's rule: `total occurrences: 0, distinct dests: 0` clean, 0 on each of the other
six builders, and `[('integration-lock', 'command')]` on the mutated tree. So the item's own prescription
works, and works precisely. F-08 then claims no narrowing covers both defect shapes; I re-ran narrowing
(iii) against the MUTATED tree and it reports 30 findings, the thirtieth being
`('integration-lock', 'command')`, because a REMAINDER's default is `[]` and not `argparse.SUPPRESS`, so
no exemption fires. One static rule DOES cover both shapes.

WHY THAT DOES NOT SINK THE PLAN, and why I applied revisions rather than marking REPLAN. The deliverable
is still the right thing to build; only its stated reason was wrong. The reachability walk has three
properties the static rule lacks and they are sufficient on their own: it asserts reachability DIRECTLY
(when it is red a leaf is provably unreachable, where a static red means a leaf MIGHT be), it carries no
by-name exemption list for the seven shared `common` flags that the eighth such flag would silently rot,
and it is mechanism-agnostic in a tree that already subclasses the very action the defect lives in
(`_ViewerOrLeafSubParsersAction`). I wrote that as F-15 and re-pointed the Goal, the Step 0 convention,
the Deferred row, the Scope check and the gate at it, so the plan now records a weighed TRADE with its
costs instead of a false impossibility. A future author who prefers the cheaper rule will find the
corrected measurements rather than repeat the probes.

THE ONE THAT WOULD HAVE FAILED AT EXECUTION (PR-503). E-02's synthesizer spec derives required options
from `action.required`, and argparse sets that on NO member of a required mutually exclusive group. Built
to the authored spec, the walk reports `oc_runipd: canonical=7 parsed_ok=6` and `agy_runipd: 7 / 6`,
failing on `runipd stop: error: one of the arguments --after-call --after-set --now --now-force is
required`. The plan's own total-coverage assertion would therefore have been red, and its gate explicitly
forbids weakening it, so an executor would have been stuck between two of its own instructions. The fix
is four lines and measured: emit one member per required group and exclude that group's members from the
per-action pass; with it all seven builders reach total coverage. This is also the strongest vindication
of OQ-01's decision to walk all seven, since `cli` alone has no required mutex group anywhere and would
never have exposed it.

THE SELF-CONTRADICTION (PR-504). E-03 requires driving `cli._dispatch` against the mutated parser and, in
the same breath, forbids monkeypatching `cli._build_parser`. `_dispatch`'s first statement is
`parser = _build_parser()` and its signature takes only `argv`, so the two instructions cannot both be
obeyed. I could not satisfy it myself without a patch either, which is how I found it. Resolved by
permitting the SCOPED form only: `patch.object` as a context manager restores on exit including on
exception, which answers the leak hazard the prohibition was actually written for (an unscoped
module-level rebind), and V-03 now demands the containment be PROVED after the block rather than asserted.
Demonstrated: `patched rc: 2 top-level usage: True lines: 215`, then
`post-patch clean walk findings: []`.

WHAT I DELIBERATELY DID NOT FLAG. The plan changes no production code and says so four times; that is
correct, F-03 measured zero live instances of this shape and I reproduced it. The two-plan split is right,
though not for the reason the plan gave (PR-505), and I withdrew the coverage argument rather than the
split. I left OQ-02 deferred: where a refusal belongs is genuinely the maintainer's call, it carries a real
live carrier (`sq1go0`), and only one of its two supporting premises needed correcting. I left the
four-item structure alone; each item now addresses one concern, and E-01's measure-first item is
load-bearing for a plan whose entire argument is a set of counts. I did not flag the absence of
`- Readiness:`, which is correct at `to-review` and which the plan explicitly explains.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | D (evidence accuracy); G (plan rationale) | plan F-07 ("that rule as literally stated FIRES 1160 TIMES on a clean tree"); review re-run of the item's rule: `total occurrences: 0, distinct dests: 0` clean and `[('integration-lock', 'command')]` mutated; broader rule: 1160 over 23 dests | **THE PLAN'S CENTRAL JUSTIFICATION MEASURES A DIFFERENT RULE FROM THE ONE THE ITEM ASKS FOR.** The item says "ANCESTOR SUBPARSERS ACTION's `dest`" (23 dests); authoring measured any-dest-repeat-along-the-chain. The item's own rule fires ZERO times clean, so it is implementable and the plan's "unusable as written" premise is false. A reviewer or executor reading only F-07 would believe the prescribed remedy had been ruled out when it had not been tried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 rewritten to report BOTH rules with both measurements and to state that the static rule is VIABLE; new F-15 supplies the walk's real justification (directness, no exemption list to rot, mechanism-agnostic, with its costs); Goal, Step 0 convention, Deferred row, Scope check, workflow history and the gate all re-pointed; E-01(c) split into c1/c2 so an executor re-derives both and cannot re-conflate them; V-01 requires them labelled separately |
| PR-502 | HIGH | IN-SCOPE | D (evidence accuracy) | plan F-08 ("One static rule cannot cover both shapes"); review re-run of narrowing (iii) on the MUTATED tree: `total 30`, including `('integration-lock', 'command')` | **THE CLAIM THAT NO NARROWING COVERS BOTH DEFECT SHAPES IS FALSIFIED.** Narrowing (iii) exempts a child or ancestor whose default is `argparse.SUPPRESS`; a REMAINDER positional's default is `[]`, so nothing exempts the mutated `integration-lock` and the rule reports it. The clean-tree counts (1160/33/30/29) are all correct; only the conclusion drawn from them is wrong, and it is the conclusion the plan's shape and its Deferred rejection both rest on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 rewritten: clean counts confirmed reproduced, conclusion retracted with the mutated-tree measurement; the Deferred row now declines the static rule as a weighed DESIGN TRADE citing F-15 rather than on feasibility; OQ-02's deferral rationale annotated to name the one premise removed (its remaining two, refusal-placement and import-time cost, stand); the gate directive rewritten so an executor who discovers the census works does not conclude the plan was mistaken |
| PR-503 | HIGH | UNDER-SCOPE | E (testing); G (executability) | plan E-02 ("for an option, supply it ONLY when `required` is true"); review probe on `oc_runipd`'s `stop`: `required option actions: []` beside `mutex group required= True actions=['level_flag' x4]`; walk built to spec: `oc_runipd 7/6`, `agy_runipd 7/6`, failing on `error: one of the arguments --after-call --after-set --now --now-force is required` | **THE SYNTHESIZER AS SPECIFIED CANNOT REACH TOTAL COVERAGE, SO THE PLAN'S OWN COVERAGE ASSERTION WOULD BE RED AT EXECUTION.** A required mutually exclusive group sets `required` on no member action, so an `action.required`-only synthesizer misses it entirely. The executor would face a red coverage assertion that the gate forbids weakening, with no instruction naming the cause. F-06's progression never caught it because it was measured on `cli` alone, which has no such group on any leaf. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-17 with the probe output and the measured fix; E-02 now carries the required-mutex corner as a mandatory paragraph (iterate `_mutually_exclusive_groups`, emit one member of each required group, exclude its members from the per-action pass) with the resulting per-builder coverage (151/151, 7/7, 7/7, 6/6, 0/0 x3) and an explicit note that the three flat builders' `0/0` is a PASS; V-02 now demands a PER-BUILDER table because an aggregate would have buried exactly this gap; the gate names the expected red and its fix |
| PR-504 | MEDIUM | IN-SCOPE | G (executability); internal contradiction | plan E-03 ("drive `cli._dispatch(...)`" and "never monkeypatch `cli._build_parser`"); `cli._dispatch`'s first line `parser = _build_parser()`; its signature `_dispatch(argv)` | **TWO INSTRUCTIONS IN ONE E-ITEM CANNOT BOTH BE OBEYED.** `_dispatch` builds its own parser and accepts none, so there is no route to the mutated tree that does not replace what `_build_parser` returns. An executor must either drop the symptom assertion (losing the pin on F-01's misleading exit-2-plus-help, which is the item's central complaint) or violate a stated prohibition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-18. E-03 now permits `unittest.mock.patch.object` AS A CONTEXT MANAGER only, explains that the prohibition targets an unscoped module-level rebind, and requires the containment be PROVED by re-walking a fresh parser after the block; the gate's blanket prohibition rewritten to forbid the unscoped forms specifically (assignment, class/module setup scope, cross-test patches); V-03 requires the post-block `[]` and confirmation the patch is a context manager; E-01(a) re-pointed at the same route |
| PR-505 | MEDIUM | IN-SCOPE | C (architecture); G (rationale) | plan workflow history ("They are INDEPENDENT ... because this guard's shape-based sibling would have caught the `runs` defect and this guard's reachability walk does NOT") | **THE SPLIT'S STATED JUSTIFICATION ARGUES AGAINST THE SPLIT.** Once F-08 is corrected, the sentence reduces to "the alternative would have covered both and we chose one that does not", which is a reason to reconsider the remedy, not a reason the two plans are independent. The split is nonetheless correct on the reasons the same note gives first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-16 stating the withdrawal explicitly. The history note now grounds independence in the absence of a deliverable dependency (neither reads the other's output) and in RISK and REVIEWABILITY (test-only versus a `cli.py` edit that changes a documented invocation; clean baseline versus failing baseline), and records that the coverage argument is withdrawn so a later reader does not restore it |
| PR-506 | LOW | IN-SCOPE | G (execution contract) | plan gate ("Execute through `aw ipd begin` before any edit and `aw ipd finalize` for the terminal transition"); `ipd_lifecycle`'s `AW-LIFECYCLE-ROLE-001` | **THE FINALIZE INSTRUCTION WAS UNCONDITIONAL AND THE PLAN CARRIED NO SCOPE FENCE.** An unconditional `aw ipd finalize` instruction is wrong in a managed lane, where the runner owns the transition and the verb refuses an agent; and the workflow requires a declared fence so the runner can reconcile an out-of-scope edit afterwards. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The transition is now stated as unconditionally OWED with a CONDITIONAL OWNER (runner in a managed lane per `AW-LIFECYCLE-ROLE-001`, executor only in an unmanaged run), still forbidding a hand `git mv` or a hand-edited status. Added a SCOPE FENCE as a declaration for reconciliation, naming the four evidence-only test files and the production module not to touch and the OQ-02 refusal not to implement, stating that a necessary out-of-scope edit is MADE and then JUSTIFIED with `--scope-reason`, and reserving a stop for the genuinely unsafe cases only (unresolvable concurrent edit; an absent depended-on symbol). `aw commit <plan>` replaced with the literal `aw commit 8kd4eo` |
| PR-507 | LOW | IN-SCOPE | E (testing); live-artifact convention | plan F-13 and Required tests (`3246 passed, 2 skipped, 3 warnings in 52.31s`); review's bare run: `3312 passed, 2 skipped, 3 warnings in 62.71s`; plan F-06 ("adding required OPTIONS reaches 147"); review: 146 | **TWO TRANSCRIBED FIGURES NO LONGER REPRODUCE.** The suite total moved by 66 passes in a single day on a shared tree, and the third stage of the coverage progression measures 146 rather than 147. Neither changes any conclusion, and leaving them uncorrected would have an executor reporting a divergence from a figure this review already knew was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 now records BOTH baselines with both HEADs and states the 66-pass movement as the concrete reason E-01(d) re-derives and V-04 reconciles by node id; Required tests carries both; E-01(d) and V-01 use the review figure; F-06's third stage corrected to 146 with a note to use the re-derived value; the gate's count-pinning prohibition cites the movement and notes that two of THIS plan's own figures failed to reproduce |
| PR-508 | LOW | IN-SCOPE | G (right-sizing); citation accuracy | `aw ipd lint --long`: `IPD-Z602 (line 68): E-04: action text may bundle multiple concerns (3 clauses)`; plan citations to "P16's location-dependence subsection"; `- Scope:` ("all 151 canonical leaves") | **A DENSITY ADVISORY WAS LEFT UNADDRESSED AND TWO CITATIONS DO NOT RESOLVE.** The rubric requires investigating a sizing signal by decomposition rather than dismissing it. Separately, `GUIDING_PRINCIPLES` P16 has no "location-dependence subsection" (the applicable rule is "Verify test sensitivity with mutation"), and the walk covers 171 canonical leaves across seven builders, of which 151 are `cli`'s. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten to ONE concern (prove the module perturbs nothing else), folding the twice-run check into that same reconciliation rather than standing as a second deliverable; `IPD-Z602` no longer fires and `--phase review-finalize` reports `conforming` with no advisory. Assessed as a genuine signal, not waived: the item was carrying a distinct concern in a subordinate clause. Both P16 citations re-pointed at the mutation-sensitivity rule (D78's vacuous-pass precedent kept, since it resolves and is apt); `- Scope:` corrected to 171 with the `cli` breakdown; the two 172 figures corrected to 171 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Two of the plan's three load-bearing measurements are wrong and they are the justification for substituting a different remedy from the item's. Is that REPLAN, or repairable with bounded edits? | Repairable: keep the deliverable, replace its stated reason | Mark REPLAN and require re-authoring around the static rule; leave the measurements and note the discrepancy only in the review record | The DELIVERABLE is unaffected by the error: `tests/test_cli_dest_shadowing.py` is still the right artifact, still measures the tree clean, and still fails for the item's defect (F-05 reproduced verbatim). What was wrong was the ARGUMENT, and an argument is exactly what a bounded plan edit can replace. The walk independently earns its place on three properties the static rule lacks, each checkable: directness (a red means provably unreachable, not maybe), no by-name exemption list for the seven shared `common` flags, and mechanism-agnosticism in a tree that already subclasses `_SubParsersAction` (`_ViewerOrLeafSubParsersAction`). Leaving the measurements uncorrected was never an option: they are the plan's own Findings table, an executor re-derives them at E-01, and the plan would be caught contradicting itself at execution | yes |
| D-2 | Should the plan be re-pointed at the item's static rule now that review measured it viable (0 clean, 1 mutated, and narrowing (iii) covering both shapes)? | No: keep the reachability walk, record the trade | Switch to the item's rule as the deliverable; build both | The static rule needs a hand-maintained exemption list for the seven shared flags (`help`/`agent`/`json`/`no_color`/`color`/`interactive`/`no_interactive`, 161 occurrences each), and the eighth flag added to `common` re-breaks it into a false-positive storm with nothing telling the author. It also asserts a SHAPE and infers unreachability, so a red does not prove a leaf is unreachable. Building both doubles the surface for one property. The costs of the walk are real and are now stated in F-15 (more code, the F-06/F-17 synthesizer, 171 parses per run) so a maintainer can overrule this on the evidence | yes |
| D-3 | E-02's synthesizer cannot satisfy a required mutually exclusive group. Fix the spec, or narrow the walk to `cli` where the gap does not bite? | Fix the spec; keep all seven builders | Exempt the `stop` leaf; drop the two runner builders from the walk; lower the coverage assertion to a fraction | Exempting or dropping is precisely the vacuous pass the plan's own gate forbids and which D78 records having happened here. The fix is four lines and measured to reach total coverage on all seven. Dropping the runner builders would also discard the only place in the package with a required mutex group, which is what exposed the gap at all: the same coverage would then be wrong for the next builder that grows one, silently | yes |
| D-4 | E-03 forbids monkeypatching `_build_parser` yet requires driving `_dispatch`, which builds its own. Permit a patch, or drop the symptom assertion? | Permit a SCOPED `patch.object` context manager and require the containment be proved | Drop the dispatch assertion and pin only the walk finding; refactor `_dispatch` to accept a parser | Dropping loses the pin on F-01's misleading symptom (exit 2 plus a well-formed top-level help page), which is the item's central complaint and the thing that makes this guard read as non-hypothetical. Refactoring `_dispatch` is a production edit in a plan whose entire claim is that it changes no production code. The prohibition's real target is an unscoped rebind outliving the test under `-n auto --dist=worksteal`; `patch.object` as a context manager restores on exit including on exception, and review measured no residue (`post-patch clean walk findings: []`), so the hazard the prohibition guards is answered rather than accepted | yes |
| D-5 | `IPD-Z602` fired on E-04. Split it, or record the advisory as accepted? | Rewrite E-04 to one concern (the advisory now silent) | Accept it with a rationale; split into a suite item and a repeat-run item | The rubric is explicit that a sizing signal is "an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed", and here the decomposition was clean rather than forced: the item's three clauses were one concern (prove the module perturbs nothing else) plus narration. Splitting off the twice-run check was rejected as over-split, since a second-run difference IS part of the same perturbation reconciliation and would otherwise need its own V-item asserting nearly the same property | yes |
| D-6 | The plan's suite baseline moved 3246 -> 3312 in one day. Update the figure, or state the shape? | Record BOTH measurements with their HEADs and keep node-id reconciliation as the bar | Replace with review's figure alone; drop the figure | Replacing just relocates the staleness, since more work lands before this plan executes. Recording both makes a third figure read as expected drift rather than as a failure, and it supplies the concrete evidence for why V-04 compares by node id instead of by total. This follows the workflow's live-artifact convention: the plan states the property and re-derives the count at execution | yes |
