# Review findings: plan pw2ln3

- Subject-Id: pw2ln3
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree at HEAD `7cba3a3f`. Structural preflight `aw ipd lint --phase
author --detail` reported one ADVISORY (`IPD-Z602`: E-04 bundling three action clauses) and no
conformance error; `--phase review-finalize --detail` now conforms with the advisory gone, because the
split this review made for other reasons also resolved it. No pre-review snapshot was needed: `git
status --short` was empty. Suite baseline re-measured before touching anything: `2590 passed, 2
skipped, 3 warnings in 40.77s`.

THE DIAGNOSIS IS CORRECT AND THE DESIGN IS THE RIGHT ONE. F-1 reproduces verbatim: `aw graduation
cfgj8s` prints "nothing yet: no plan or spec links to source cfgj8s. Proceed." at exit 0, while the
item carries `- Graduated-To: envhermet` and `parse_graduated_to` returns `['envhermet']`. F-3 holds:
`check_graduated_to` really does build its own `known_setids` with a private `_iter_plan_ipds` +
`_parse_setid` loop, and `graduation_cluster` never reads `Graduated-To`. F-5 holds: the forward check
returns 0 findings, so E-03 has a fixed target. And F-4, the design constraint, is stronger than the
plan claimed: I measured the reverse-index setid set at 215 against the sweep's 422, with `sweep -
reverse` = 207 and `reverse - sweep` = 0, so the reverse index is a STRICT SUBSET and substituting it
would make 207 real Sets unresolvable, i.e. mass false `check.graduated-to-dangling`. The backlog item
`knvpiv` independently names the same remedy ("the sharable unit is the underlying PLAN-SETID
ENUMERATION"), so E-02 is the shape the obligation actually asks for. The `has_any_link` /
keep-`artifacts`-meaning-unchanged decision in OQ-01 is right, and I verified its premise: the three
consumers are exactly `cli._run_graduation`, `runner_shared.summarize_graduation_cluster`, and
`graduation_cluster` itself, and `summarize_graduation_cluster` does report `artifact_count` as
"linked artifact(s)", so silently widening it would change a shipped line.

**THE PLAN WOULD HAVE SHIPPED A SPEC PATH THAT NEVER RUNS, AND NOTHING WOULD HAVE SAID SO.** E-04
instructed the executor to call `selectors.resolve(repo_root, t, source_id6)` for `t` in `backlog`,
`specs`, while restricting to "the kinds `source_kind` allows". The trap is that the two vocabularies
differ by one letter: `GRADUATION_SOURCE_KINDS` is `("backlog", "spec")` SINGULAR, and
`selectors.KNOWN_PRIMARY_TYPES` contains `specs` PLURAL. I built a temp repo with a real spec and
measured both spellings: `resolve(repo, "specs", id6)` finds it, and `resolve(repo, "spec", id6)`
returns an EMPTY `Resolution` with NO exception and no diagnostic. So an executor threading
`source_kind` through unmapped gets silence, not an error, and every spec source is forward-linkless
while the code reads as correct. That is F-6, and E-04 now requires the mapping explicitly and E-07
asserts it.

**AND THE ONE MECHANISM ADDED SPECIFICALLY TO SURVIVE `--agent` WOULD HAVE DROPPED ITS PAYLOAD.** E-05
told the executor to add "a `graduation-forward` `Evidence` item (count and setids) so `--agent`, which
drops `data`, still carries it". I read `agent_schema.sanitize_evidence_item` and then drove it: it
returns `f"{key}:{val}"` only when the value is `int`/`float`/`bool` or a clean `str`, and returns the
BARE KEY for anything else, including a dict. A dict-valued `graduation-forward` therefore compacts to
the string `'graduation-forward'`, carrying neither count nor setids past exactly the boundary it was
added to cross. This is not speculative: the PRE-EXISTING `graduation-cluster` item beside it is
dict-valued, and live `aw graduation z7nbn1 --agent` emits `['graduation-cluster', 'limit:...', ...]`
with that first item already value-less. That is F-7. The plan's own comment in `cli.py` even states
the rule correctly ("renders a string-valued Evidence as `key:value`"), so the instruction contradicted
the code comment it cited.

**WORSE, THE TEST FOR IT COULD NOT FAIL.** E-06 case (7) asserted that the `--agent` output "contains
the `graduation-forward` evidence key". The key is precisely what survives the broken path, so the
assertion PASSES whether the value is carried or discarded. I confirmed that directly:
`'graduation-forward' in sanitize_evidence_item(<dict-valued>)` is True. Case (7) now asserts the
compacted item carries a colon and the setid, and V-08 requires a counter-run against a dict-valued
implementation, so the assertion is load-bearing rather than decorative.

**AND THE TWO DEFECTS WOULD HAVE MASKED EACH OTHER, BECAUSE A THIRD CLAIM WAS FALSE.** The plan's
deferred row asserted that reading `Graduated-To` on specs changes nothing live because "0 specs carry
it today". One does: `.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`
carries `- Graduated-To: artdispatch`, `artdispatch` IS in the plan-setid sweep, and `z7nbn1` already
has 6 reverse artifacts in that same Set. So it is a LIVE both-directions agreement case, which is the
single most valuable fixture this plan could have, and the false premise meant an executor hitting F-6
would have seen no spec output and concluded the plan predicted it. That is F-8, and E-08 now has a
case (8) driving a spec source both with and without `source_kind`.

ON RIGHT-SIZING, which the count-based lint flagged as an advisory and which I did not dismiss. The
authored E-04 bundled a `NamedTuple` field addition, a new source-resolution path, three derived
properties, and an injection parameter; E-05 bundled five numbered CLI changes plus a separate module's
advisory line. Both fail diagnostic (a) (multiple independent code regions) and (b) (independent test
surfaces). I split them into E-04 (locate the source and read the field), E-05 (the cluster fields),
E-06 (the CLI render), and E-07 (the runner advisory), which is also why the `IPD-Z602` advisory
cleared. Checklist 7 -> 9 E-items, renumbered, V-* re-bijected 1:1.

ON THE COUNTS, all of which had drifted in the days between authoring and review, and none of which
should have been written as a bar. Authored at `f46b6775`: 102 records, 97 graduated items, 401 setids.
Re-measured at `7cba3a3f`: 152 records carrying `^- Graduated-To:` (149 backlog, 1 spec, 0 plans), 111
graduated backlog items, 422 setids over 825 plans. The load-bearing 40 held exactly. These are live
artifact populations, so E-01 now states the required PROPERTY (a non-zero forward-only population and
`envhermet` present) with the observed numbers as context, per the re-derivation convention.

ON WHAT THIS PLAN RISKS. It changes a read-only advisory view and a checker's internal sweep source,
not a gate that refuses anything, so the blast radius is bounded. But F-9 is worth recording: there is
NO existing test for `graduation_cluster`, `check_graduated_to`, `summarize_graduation_cluster`, or the
`graduation` verb, so this plan's new file is the first coverage these functions have ever had, and a
regression in the REVERSE path would be caught by nothing but its case (2) and V-03's unchanged-findings
check. I also measured the cost of the added sweep (one `_iter_plan_ipds` pass is ~0.11s against a
command that already takes ~1.2s, and the reverse index alone is ~0.66s), so the forward read is not a
perceptible regression. Separately noted and explicitly out of scope: `tests/test_runner_shared.py`
cites `tests/test_graduation_dispatch.py`, which does not exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A. correctness; F. prevent silent failure | `selectors.resolve(tmp,'specs','aa11bb').paths` -> non-empty; `selectors.resolve(tmp,'spec','aa11bb').paths` -> `[]` with NO exception; `GRADUATION_SOURCE_KINDS == ('backlog','spec')` vs `KNOWN_PRIMARY_TYPES` containing `specs` | **THE GRADUATION KIND AND THE SELECTOR RECORD TYPE DIFFER BY ONE LETTER AND THE MISMATCH IS SILENT.** E-04 told the executor to resolve with the kind `source_kind` allows; forwarding `spec` unmapped returns an empty resolution with no error, so every SPEC source would be forward-linkless while the code looked correct. Combined with PR-703 the plan even predicted no spec output, so nothing would have surfaced it. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 now requires mapping `spec` -> `specs` at the call site, states the measured silent-empty behavior as the reason, and V-04 demands the value passed to `selectors.resolve` plus a real spec source's resolved PATH. E-08 case (8) drives a spec source with `source_kind="spec"`, the only spelling that exercises the mapping. Recorded as F-6. |
| PR-702 | HIGH | IN-SCOPE | E. verification; F. prevent silent failure | `sanitize_evidence_item(Evidence(key='graduation-forward', value={'count':1,'setids':['envhermet']}))` -> `'graduation-forward'`; with a string value -> `'graduation-forward:1 Set(s): envhermet'`; live `aw graduation z7nbn1 --agent` evidence `['graduation-cluster', ...]` already value-less | **THE `--agent` EVIDENCE ITEM WOULD HAVE DROPPED THE COUNT AND SETIDS IT EXISTS TO CARRY.** E-05 specified a dict value ("count and setids"); `sanitize_evidence_item` preserves only scalars and clean strings and returns the BARE KEY otherwise. The plan contradicted the `cli.py` comment it cited, which states the rule correctly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 requires a string (or scalar) value with a worked example compacting to `graduation-forward:1 Set(s): envhermet`, and records that the pre-existing `graduation-cluster` item has the same latent flaw and is deliberately out of scope. V-06 fails the item if the compacted evidence has no colon. Recorded as F-7. |
| PR-703 | HIGH | IN-SCOPE | E. testing (an assertion that cannot fail) | `'graduation-forward' in sanitize_evidence_item(<dict-valued>)` -> True | **THE TEST FOR PR-702 PASSED IN THE BROKEN STATE.** Authored case (7) asserted the output "contains the `graduation-forward` evidence key", and the key is exactly what survives value loss, so the case could not detect the defect it was written for. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Case (7) now asserts the compacted item startswith `graduation-forward:` AND contains the setid; V-08 requires a counter-run showing it FAIL against a dict-valued implementation. |
| PR-704 | MEDIUM | IN-SCOPE | A. correctness (a false premise that hid two defects) | `git grep -l "^- Graduated-To:" -- .aw/records/specs` -> `20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`, `- Graduated-To: artdispatch`; `artdispatch` in the sweep; `graduation_cluster(repo,'z7nbn1').artifact_count == 6` in Set `artdispatch` | **A SPEC DOES CARRY `Graduated-To` TODAY,** so the deferred row's "0 specs carry it, so no live output changes" is false. It matters twice: it is the live proof the spec path is exercised, AND it is a both-directions AGREEMENT case (the plan's most valuable fixture) that the plan did not know it had. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The deferred row corrected; F-8 records the file, its Set and its reverse cluster; E-05's and E-09's expected outcomes now assert the live agreement for `z7nbn1`. |
| PR-705 | MEDIUM | IN-SCOPE | E. verification (a bar that expires) | Authored `f46b6775`: 102 records / 97 items / 401 setids. Re-measured `7cba3a3f`: 152 / 111 / 422 (the 40 held) | **EVERY BASELINE COUNT HAD ALREADY DRIFTED,** and E-01 stated them as expected outcomes, so an honest executor would face a mismatch on four numbers with no guidance on whether that is drift or defect. These are live artifact populations and belong in prose as context. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's Expected outcome now states the required PROPERTIES (non-zero forward-only population; `envhermet` present) with both measured snapshots as context, and says explicitly not to fail on a moved count. V-01 mirrors it. Recorded in F-2 and F-4. |
| PR-706 | MEDIUM | UNDER-SCOPE | G. executability (right-sizing) | `IPD-Z602` advisory on E-04; authored E-04 spanned a NamedTuple field set, a new resolution path, three properties and an injection parameter; authored E-05 spanned five CLI changes plus another module | **TWO E-ITEMS EACH CARRIED SEVERAL INDEPENDENT DELIVERABLES,** failing right-sizing diagnostics (a) and (b); the linter's own advisory said so for E-04 and a count-based pass does not clear conceptual density. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-04 (source lookup), E-05 (cluster fields), E-06 (CLI render), E-07 (runner advisory); checklist 7 -> 9, renumbered, V-* re-bijected. `aw ipd lint --phase review-finalize` conforming and the `IPD-Z602` advisory cleared. |
| PR-707 | MEDIUM | IN-SCOPE | D. anti-regression | `grep -rln "graduation_cluster\|check_graduated_to\|summarize_graduation_cluster" tests/` -> no matches; `ls tests/test_graduation_dispatch.py` -> No such file | **THESE FUNCTIONS HAVE NO EXISTING TEST COVERAGE AT ALL,** which the plan did not state. It changes what an executor should treat as evidence: a green suite proves almost nothing about the reverse path, and case (2) plus V-03 are the only guards on it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-9; Required tests states that this is the first coverage and names case (2) and V-03 as load-bearing despite passing before and after; the gate says a green suite is weak evidence here. The stale `test_graduation_dispatch.py` citation is noted as out of scope. |
| PR-708 | LOW | IN-SCOPE | C. architecture (undeclared boundaries an executor could cross) | `sanitize_evidence_item` lives in `agent_schema.py`; `selectors.resolve`'s empty-on-unknown-type behavior; `GRADUATION_SOURCE_KINDS` is read by `build_graduation_reverse_index` and every reverse consumer | Three tempting fixes sit OUTSIDE the fence: "fix" the Evidence compaction, "fix" `selectors.resolve` to raise, or rename the `spec` kind to `specs`. The plan named none of them, so an executor meeting F-6/F-7 had no guidance and the largest of the three would change a shipped contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Three Scope-check bullets forbid each, with the reason; the gate adds a STOP condition for the `GRADUATION_SOURCE_KINDS` rename specifically, since that key is read by every reverse consumer. |
| PR-709 | LOW | IN-SCOPE | A. correctness (a NamedTuple compatibility detail) | `GraduationCluster` is a `NamedTuple` with four positional fields; its `artifact_count` docstring records that a member named `count` would shadow `tuple.count` | Adding fields to a `NamedTuple` without defaults breaks positional construction, and the `count` naming hazard is already documented for the reverse property but was not restated for `forward_count`. Small, but it is the kind of detail that costs a failed run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires `()` defaults on the new fields, cites the existing `count`-shadowing note as the precedent for `forward_count`, and V-05 requires a pasted positional construction with the old four arguments still working. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `spec`/`specs` spelling mismatch (PR-701). Map at the call site, or rename the graduation kind? | MAP AT THE CALL SITE, and forbid the rename in the fence. | (a) Rename `GRADUATION_SOURCE_KINDS`' `spec` to `specs`: rejected, that token is a KEY in `build_graduation_reverse_index`'s `(kind, id6)` tuples and is read by `graduation_cluster` and both its consumers, so renaming it is a contract change far larger than this plan's concern and would silently break any caller passing `source_kind="spec"`. (b) Make `selectors.resolve` raise on an unknown record type: rejected, it is a shared resolver outside the fence and changing its failure mode could affect every caller. (c) Resolve both types unconditionally and ignore `source_kind`: rejected, it discards a documented narrowing parameter. | Measured: `resolve(repo,'spec',id6)` returns an empty `Resolution` with no error while `'specs'` resolves; `GRADUATION_SOURCE_KINDS` is the reverse index's key vocabulary. | yes |
| D-2 | The `Evidence` value must survive `--agent` (PR-702). String value, or change the compaction rule? | STRING VALUE. Comply with `sanitize_evidence_item`'s existing contract. | (a) Extend `sanitize_evidence_item` to serialize dicts: rejected, it is in `agent_schema.py` outside the fence and would change the compact record shape for EVERY command that emits a dict-valued Evidence, which is a machine-surface change no part of this plan's concern justifies. (b) Rely on `--json`, which keeps `data`: rejected, the whole reason the item exists is that `--agent` drops `data`. (c) Also fix the pre-existing `graduation-cluster` item: rejected as out of scope, but recorded in the plan so the next author sees it rather than assuming it correct. | Driven `sanitize_evidence_item` on dict, int and str values; the `cli.py` comment already states the string rule; live `--agent` output showing `graduation-cluster` value-less today. | yes |
| D-3 | Should the false "0 specs carry Graduated-To" claim just be corrected, or exploited? | EXPLOITED. Correct it AND use `z7nbn1` as a live agreement assertion. | (a) Correct the sentence only: rejected, it wastes the best fixture available; a real both-directions agreement case on the live tree is stronger evidence than any synthetic one, and the plan's central claim is that the two directions agree. (b) Leave the row and treat the spec as an edge case: rejected, it is exactly the case PR-701 breaks, so leaving it unasserted is what let the two defects hide each other. | `z7nbn1` carries `- Graduated-To: artdispatch`; `artdispatch` is in the sweep; its reverse cluster is 6 artifacts in the same Set. | yes |
| D-4 | The authored baseline counts have all drifted (PR-705). Update the numbers, or change what E-01 asserts? | CHANGE WHAT IT ASSERTS: state the required property, keep both measured snapshots as context. | (a) Just refresh the numbers to my measurements: rejected, they will drift again before execution and the item would fail for the same wrong reason; the repository's own re-derivation convention exists for exactly this. (b) Drop the counts entirely: rejected, they are genuinely useful as an order-of-magnitude sanity check and as evidence the defect is common rather than anecdotal. | The re-derivation convention for live-artifact success criteria; two measurements days apart differing on three of four numbers while the load-bearing 40 held. | yes |
| D-5 | Is a green suite adequate evidence for this plan? | NO. Record that there is no prior coverage and name case (2) and V-03 as the reverse-path guards. | (a) Leave it implicit: rejected, an executor reasonably reads a green suite as "nothing broke", and here it is nearly uninformative because nothing ever tested these functions. (b) Require broader characterization tests of the reverse path first: rejected as scope growth; case (2) plus the live unchanged-findings check in V-03 cover the realistic regression, and demanding a full characterization suite for a read-only view would be gold-plating. | `grep` over `tests/` returns no reference to any of the four symbols; `check_graduated_to` returns 0 findings live, which makes V-03 a usable fixed target. | yes |
| D-6 | Where should the new forward read cost be accepted? | ACCEPT IT: one extra `_iter_plan_ipds` pass inside a command that already takes ~1.2s. | (a) Cache the plan-setid index across calls: rejected, premature for a ~0.11s pass and it would add invalidation risk to a read-only view. (b) Read the forward field only when the reverse cluster is empty: rejected, that would break the AGREEMENT case (both directions non-empty), which is the plan's main new signal. | Measured: `_iter_plan_ipds` + `_parse_setid` over 825 plans is 0.113s; `build_graduation_reverse_index` is 0.658s; `aw graduation cfgj8s` wall time 1.208s. | yes |

### Deferred and open

- (none). All nine findings were FIXED in place. None reached Medium-High or High Remediation Risk
  (PR-701 is the only Medium overall, on the functionality axis, and its fix is a one-line mapping at a
  single call site), so the Fix Bar permitted no deferral and none was taken. Because nothing was left
  `OPEN` or `DEFERRED`, no escalation to a `- Blocking: yes` question was required.
- Both authored open questions were re-verified rather than accepted. OQ-01 (keep the directions
  separate) is corroborated: `GraduationCluster.artifacts` is documented as the reverse set and
  `summarize_graduation_cluster` renders `artifact_count` as "linked artifact(s)", so widening it would
  change a shipped line in a second module. OQ-02 (do not make the reverse index read `Graduated-To`) is
  corroborated by a stronger measurement than the plan's: the reverse-index setid set is a strict subset
  of the sweep's, missing 207 real Sets.
- The plan's two `Carrier-Declined` rows were checked against the tooling:
  `check_engine.evaluate_durable_carrier` returns `[]`, so no obligation is uncarried. One row's PREMISE
  was false (PR-704) and was corrected; the declination itself stands.
- No `Reversible: no` decision was made. All six decisions are plan-text choices on an unexecuted plan;
  none changes a published interface or deletes anything.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I executed no part of the plan:
`build_plan_setid_index` does not exist, `tests/test_graduation_forward_links.py` does not exist, and my
confidence that E-02's helper will reproduce the sweep's setid set rests on driving `_iter_plan_ipds` +
`_parse_setid` myself (422 setids over 825 plans), not on the authored helper. SECOND, I verified the
`spec`/`specs` mismatch on a synthetic temp repo and by reading `KNOWN_PRIMARY_TYPES`; I did not trace
every branch of `selectors.resolve` to confirm that an unknown type can never raise under some other
input shape, so F-6's claim is about the measured path. THIRD, my F-7 measurement is of
`sanitize_evidence_item` in isolation plus one live `--agent` run; I did not audit every other command's
Evidence values, so the statement that `graduation-cluster` shares the flaw is about that one item and
is not a survey. FOURTH, the population numbers are a snapshot of a shared checkout that other agents
are committing to, so they will differ again at execution; that is precisely why E-01 now asserts a
property. FIFTH, I did not review whether spec `4sd62s`'s eventual unification makes any of this
interim work wasted; I accepted the plan's framing that it is an interim fix, which is a scope judgement
the maintainer already made when the item was graduated.
