# Review findings: plan 75ic2f

- Subject-Id: 75ic2f
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201, PR-202 (HIGH, fixed), PR-203 (MEDIUM, fixed), PR-204, PR-205, PR-206 (LOW, fixed)

## Round 1

Reviewed at lane HEAD `f49b7a3c` in an isolated review lane. The plan file was committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) with one advisory `IPD-Z602` on E-01 BEFORE semantic review; `--phase
review-finalize --agent` reports `conforming` after revision. I assessed the advisory and judged it a
false positive: it fires from `S.e_item_density_advisory` on three clause-like fragments in E-01's action
text, but E-01 produces one deliverable (one test file's one assertion) and the fragments it counted are
guard clauses telling the executor what NOT to do. I did not restructure E-01 to silence an advisory that
does not affect the disposition.

THE PLAN'S EVIDENCE IS UNUSUALLY GOOD AND ITS CORE ARGUMENT SURVIVES INTACT. I re-measured every
material claim rather than reading it, and the numbers are exact. The defect reproduces: `python3 -m
agent_workflows find plans --agent --fields findings` exits 2 with `unrecognized arguments: --fields`,
and the guide's row quotes that command verbatim. The parser walk returns 151 unique leaves with 139
carrying `--agent`, 139 `--json`, 9 `--limit`, 4 `--fields` (exactly the four `runs` leaves the plan
names) and 1 `--verbose` (`upgrade-test new`), and the `--agent`-without-`--fields` gap is exactly the
135 the plan predicts. F-04's build-time conflict raises on a minimal parent/child repro and on the real
tree. F-05 is precisely right: patching `common` alone yields 133 leaves and leaves exactly `upgrade-test
clean/env/list/new/probe/sandboxes` behind, and patching both parents closes the gap to zero. F-06's
sweep reproduces all 14 rows with the same prefixes, the same before-meanings and the same leaves, and
`aw check-local-leaks --fi --help` exits 0 today while `--fix` is documented as rewriting files. F-10's
early return and truthiness guard are as described. F-07's "safe to pass on any command" sentence appears
verbatim in both protocol documents, and OQ-03's cited pitfall line ("`aw check` finding problems returns
`1`, which is not a crash") is in the guide as quoted.

WHAT REVIEW FOUND. Three corrections, two of which would have cost the executor real time.

FIRST, E-01's central instruction cannot be followed. It tells the executor to obtain the leaf set by
reusing `command_surface.discover_parser_leaves` "which already does this", and that helper is annotated
`-> Set[str]` and returns leaf PATH NAMES. Measured: its return value is a `set` of `str`, and a `str`
has no `_actions`, so no option set can be read from it. Nor is there a resolver to turn a name back into
a parser: its two siblings in that module (`get_declared_leaves`, `find_undeclared_leaves`) are both
name-set functions. So an executor following E-01 hits `AttributeError` on the first line of the
assertion and must invent the walk anyway, without the identity-deduplication guidance the helper's
docstring holds. The helper is still the right REFERENCE, so I kept the citation and changed its role
from "call this" to "re-implement this rule", and I addressed the code-pinning question explicitly
because it is the reason an executor might hesitate: reading `parser._actions` inspects the parser the
production code BUILT at runtime, not its source text, and `tests/test_flag_surface_uniformity.py`
already calls `cli._build_parser()` for the same purpose.

SECOND, F-08 contains a false measurement, and it is the one the plan leans on hardest. The row claims
`aw find plans rcjorx --agent --fields findings` "DOES project correctly under the patch, emitting
{...findings:0} with next projected away". It does not. The branch condition is `getattr(args, "paths",
False) or (ctx.is_agent and all_paths)`, which keys on `all_paths` being TRUTHY rather than on the
absence of a selector, so a MATCHING selector takes the same bare-path branch: measured under the patch,
that command prints one bare path and zero `aw.agent/v1` records. What actually reaches the record branch
is a selector matching NOTHING (`find plans zzzzzz`), which projects correctly but is a useless
demonstration. The correction cuts both ways honestly: it removes a candidate the plan offered and it
STRENGTHENS the plan's own case for replacing the guide row, because `--fields` turns out to be inert on
essentially every useful `aw find` invocation rather than only on the bare one. That also makes the
`wdazvp` carrier a bigger defect than it was filed as, which I noted in the deferral row.

THIRD, the plan's safety probe names a nondeterministic command. `aw check plans --agent` printed a
different `next` value on each of three consecutive runs of the UNMODIFIED tree. Both the Required tests
byte-identity probe and V-02's closing clause ask for byte-identical stdout before and after, and
authoring's own F-08 chose `aw check plans` as its worked example, so the two instructions together steer
an executor into a false disagreement on the single probe that licenses widening a flag to 139 leaves. I
ran the probe properly to establish the bar: six commands spanning both shared parents, five
byte-identical across the patch, and `check plans` differing only in `next` with an identical length and
an identical key set, reproducing the same variance with no patch applied. The probe is sound; its sample
was not.

I ALSO VERIFIED THE PLAN'S OWN HONESTY CLAIMS, since several are unusual and load-bearing. The
`--verbose` deferral row corrects an earlier draft of itself, saying plainly that claiming the flag has
no consumer "was wrong"; I checked, and `context.verbose` does reach three branches (through
`is_verbose` in `to_agent_record`), so the row's correction is the accurate version. OQ-02's rejection of
renaming the flag is right for the reason it gives. The plan's decision to file rather than fix two
adjacent defects matches the in-tree precedent it cites, and both carriers exist, are `open`, and conform.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | G. Plan executability (an instruction that cannot be followed) | `command_surface.discover_parser_leaves` signature `-> Set[str]`; `type()` probe returns `set` of `str`; `hasattr(leaf, "_actions")` is `False`; `grep` of `command_surface.py` returns three name-set functions (`get_declared_leaves`, `discover_parser_leaves`, `find_undeclared_leaves`) and no name-to-parser resolver | **E-01 tells the executor to obtain the leaf set by reusing a helper that returns leaf NAMES, not parsers, so the reach assertion cannot be written as instructed.** A `str` has no option set to read, and no resolver exists to recover the parser, so the executor hits `AttributeError` on the first line and must invent the walk anyway, losing the alias-identity guidance the helper's docstring carries. The helper remains the right reference for the dedupe rule, but not the right callee | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-13 records the probes, the absent resolver, and why the reach test is not thereby code-pinning (reading `parser._actions` inspects the built parser, not source text, and `test_flag_surface_uniformity.py` already does it). E-01 rewritten to require a local recursive walk deduplicating `sa.choices` by `id(subparser)`, citing the helper's docstring as the PATTERN being re-implemented rather than the function being called; its Expected outcome now names the `AttributeError` as the symptom of reusing it anyway |
| PR-202 | HIGH | IN-SCOPE | Evidence accuracy (a measurement the plan relies on) | Branch condition `getattr(args, "paths", False) or (ctx.is_agent and all_paths)` with its own comment "this branch returns before any `CommandResult` is built"; patched in-process runs: `find plans rcjorx --agent --fields findings` prints 1 line with 0 `aw.agent/v1` records, `find plans zzzzzz --agent --fields findings` prints 1 projected record | **F-08 claims a `find` command with a selector projects correctly, and it does not.** The branch keys on `all_paths` being truthy, not on selector absence, so a MATCHING selector takes the same bare-path branch and projects nothing; only a ZERO-MATCH query reaches the record branch. The error matters twice: it offers a candidate guide example that would silently fail the very trap F-08 exists to warn about, and it understates the deferred gap, which is that `--fields` is inert on essentially every useful `aw find` invocation | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-08 rewritten with the corrected measurement, the condition quoted, the zero-match case named as what actually projects, and the note that this STRENGTHENS the case for replacing the row. E-05 gained an explicit prohibition on substituting a selector-bearing `find` command as a third option. OQ-03's "three candidates" claim corrected to two plus a withdrawn one. V-06's rejection clause extended to cover the matching-selector case. The `wdazvp` deferral row now records that the gap is wider than authoring measured. The stale `985` figure removed from all three sites |
| PR-203 | MEDIUM | IN-SCOPE | E. Testing (a probe that yields a false result) | Three consecutive unpatched runs of `aw check plans --agent` printing `next` as `<collisions>`, then `...oi0sv9...`, then `...vnt9it...`; six-command before/after comparison: five byte-identical, `check plans` identical in length and key set with only `next` unequal, same variance with no patch | **The no-change byte-identity probe names a command whose output varies between consecutive runs of the unmodified tree**, and F-08's worked example points at the same command, so an executor running the probe as written sees a disagreement that has nothing to do with the change. That probe is the sole justification for widening a flag to 139 leaves, so a false failure there either halts the work or, worse, gets rationalized away and takes the real safety check with it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-14 records the three-run variance, the six-command measurement, and that the variance reproduces unpatched. The Required tests probe now forbids `aw check plans --agent` by name, lists four measured-deterministic alternatives spanning both parents, and permits the volatile command only with the excluded key named. V-02's closing clause carries the same restriction. E-07 is told to assert `target` or `diagnostics` absent rather than `next` (PR-205) |
| PR-204 | LOW | IN-SCOPE | Evidence accuracy (live-artifact counts stated as fixed) | `aw find plans --agent` prints 1033 lines at review HEAD, not 985; `grep -c` for `Scope-Paths:.*cli\.py` over pending plans returns 43 files, not 33; `z593o5` now `reviewed`, `zyj8io` `to-review` | **Two live-tree counts are quoted as settled facts and both have already drifted.** Neither is load-bearing (the `--limit` row is inert whatever the count, and F-09's conclusion survives any number of concurrent plans), but a plan whose Step-0 conventions section explicitly warns that offsets go stale should not quote a path count as though it will not | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both re-derived with instructions to re-derive rather than quote. New F-15 records the 33-to-43 growth, both plans' current statuses, and adds a substantive note F-09 lacked: `zyj8io` changes `aw find`'s zero-match behavior, which after PR-202's correction is the ONLY `find` invocation that projects, so the two plans touch the same narrow path. F-12 gained the review-HEAD baseline as context, explicitly not as a bar |
| PR-205 | LOW | IN-SCOPE | E. Testing (an assertion inviting future flakiness) | Projected vs unprojected key sets for `aw check plans --agent`: dropped exactly `diagnostics`, `evidence`, `next`, `target`; `diagnostics` confirmed non-empty unprojected; `next` measured volatile (F-14) | **E-07 says to assert "a named non-envelope key" is absent without naming one**, and the projection drops four keys of which one (`next`) has a volatile value. An author picking `next` writes a passing test today that a later author may strengthen into a value assertion, which would be flaky for a reason unrelated to this plan | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now names `target` or `diagnostics` as the absent key and forbids `next`, with the reason stated. It also records the full measured drop set and that `diagnostics` is non-empty unprojected, so its absence is evidence of projection rather than of an empty field, which the original wording did not establish |
| PR-206 | LOW | UNDER-SCOPE | G. Plan executability (unverified ownership claims) | `aw find backlog wdazvp qm04zi rcjorx`: `rcjorx` graduated, `wdazvp` open, `qm04zi` open; `aw backlog check` reports "all backlog items conform." | **The plan asserts two carrier items were filed and are live without recording their measured state**, and V-05 asks the executor to check them without saying what a correct answer looks like. Both being `open` rather than `graduated` is correct and worth stating, since a reader who expects `graduated` (as `rcjorx` is) might think the carriers were mis-filed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-16 records all three items' measured statuses, the clean `aw backlog check` line, and why `open` is the correct state for a carrier with no plan yet |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-201: should E-01 keep citing `discover_parser_leaves` at all, given it cannot be called? | Keep the citation, changed from "reuse this" to "re-implement this rule", and state what it actually returns | Deleting the reference entirely; adding an E-item to extend `command_surface` with a name-to-parser resolver; leaving E-01 alone and letting the executor discover the problem | Deleting it loses real value: that docstring is where the alias-identity rule and the measurement behind it (63 aliases surfacing as undeclared leaves) are written down, and an executor writing a fresh walk without it will likely double-count aliases. Extending `command_surface` is out of this plan's fence, needs its own decision about a public helper's shape, and would be gold-plating for a single test. Letting the executor discover it wastes a turn on a problem review already measured | yes |
| D-2 | PR-202: F-08's error removes a guide-example candidate. Should OQ-03 be reopened for the maintainer? | No; leave it resolved at `aw check plans --agent --fields findings` and record that review re-measured the surviving candidates | Reopening OQ-03 as a maintainer question; switching the recommendation to the `aw status` fallback; adding the zero-match `find` command as a candidate | The correction eliminates a candidate but does not disturb the chosen one, which review re-measured projecting correctly and which OQ-03 argued for on grounds the correction does not touch (it keeps the field name `findings` the row already teaches, and it drops four keys including a populated `diagnostics`, which is the strongest illustration available). The zero-match `find` command is not a candidate at all, since a guide example that demonstrates projection only on an empty result teaches nothing. Reopening would cost the maintainer a turn to re-affirm a decision whose basis is unchanged | yes |
| D-3 | PR-203: should the byte-identity probe forbid the volatile command, or permit it with the volatile key excluded? | Both: forbid it by name as the default, and permit it only when the excluded key is named and the variance is shown without the patch | Forbidding it outright; permitting it with a general "ignore volatile fields" caveat; dropping the probe | Forbidding outright is slightly too strong, because `check plans` is a legitimate and interesting subject (it is the very command E-07 drives) and an executor who understands the volatility can use it honestly. A general caveat is too weak: "ignore volatile fields" is exactly the license under which a real regression gets waved through, which defeats the probe. Requiring the key to be NAMED and the unpatched variance to be SHOWN keeps the escape hatch open while making its use auditable. Dropping the probe is not an option, since it is what licenses the whole change | yes |
| D-4 | The `IPD-Z602` density advisory fires on E-01. Should E-01 be split or restructured? | Neither; assessed as a false positive and left alone, with the assessment recorded in the workflow history | Splitting E-01 into a walk item and an assertion item; rewording E-01 to reduce its clause count; treating the advisory as a finding to fix | The advisory counts clause-like fragments in the action text, and E-01's fragments are GUARD CLAUSES (do not hardcode a count, do not read source text) rather than deliverables; the item produces one test file with one assertion. Splitting it would create an E-item whose only output is a helper function with nothing asserting on it, which is worse structure and would need its own V-item asserting nothing observable. Rewording to satisfy a count would mean deleting guidance that PR-201 shows the executor needs; the advisory does not affect the disposition, and the workflow's own rubric says a passing count lint does not clear density and (symmetrically) a count advisory does not establish it | yes |
| D-5 | The plan defers three adjacent defects (`find` bare-path branch, inert `--limit`, `--verbose` reach). Should any be pulled into scope? | None; all three deferrals upheld | Pulling `--verbose` in as a symmetric fix; pulling the `--limit` row's fix in since E-05 already edits that table | `--verbose` is genuinely a second surface: each flag added to a shared parent creates new prefix collisions that must be re-measured, so folding it in would require re-running the F-06 sweep for a second flag and would double E-03's blast radius, for a flag the graduating item does not name. The `--limit` and bare-path defects are ONE contract decision (what should `aw find --agent` emit at all), that decision affects every consumer parsing its bare-path stream line by line, and the branch's own comment records the byte-identity guarantee deliberately. PR-202's correction makes that decision LARGER, not smaller, which is a further reason it belongs in its own plan | yes |
