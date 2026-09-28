# Review findings: plan 3dexf1

- Subject-Id: 3dexf1
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bd06f361` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --json`
conforms after revision with zero diagnostics. No pre-review snapshot was owed: the plan was committed
and unmodified. `aw sanitize --agent` clean. No production code was modified by this review; every
measurement was taken with standalone probes over `check_engine`'s own readers.

THE DESIGN IS SOUND AND ITS TWO LOAD-BEARING MEASUREMENTS REPRODUCE EXACTLY. F-03, which the plan calls
the finding that most changes the design, is exact: scoping coverage to `ipd_lint.parse().valid_leaves`
reports `uonrjg` with 6 uncovered criteria and the uncovered set is precisely
`['A12b','A12c','A12d','A15','A16','A20']`; adding the `## Required tests / validation` body drops it to
0; and the two lines F-03 quotes from plan `bn026f` are verbatim and genuinely inside that section.
F-06, the counterfactual, is the strongest evidence in the plan and it replays correctly: at commit
`516eb661` ("plan(lifeglyph): author the nine-plan Set implementing spec uonrjg") with 9 linked plans
and 25 criteria, scope `V` gives TP=5 FP=4, scope `doc` gives TP=0 FN=5, and the chosen `V + Required
tests` scope gives TP=5 FP=0 FN=0 for the exact set `{A1, A4, A6, A19, A21}` that human review
escalated. F-02's bare-digit refutation is decisive on inspection (every match of `1`, `2`, `4`, `5`
across `2lcqno`'s two linked plans is incidental prose such as `- Order: 1` and `2 xfailed`). F-04's
namespace mechanism, F-05's 0-finding corpus with the gate, F-08's 56-plans-zero-pending census, and
every infrastructure claim (`drift_exit_code` exempting only `info`, `_DEFAULT_RULESPEC` at `error`,
`valid_titles = {H_VALIDATION_CHILD, H_VALIDATION_ORCH}`, `_structural_lines` fence-awareness via
`_FENCE_RE`, `source_link_is_absent` sentinels, `aw check plans` as a fail-closed CI step, the `216rgg`
precedent declaring `pqsx96`) all check out.

WHAT REVIEW FOUND IS ONE DEFECT THAT MAKES THE PLAN'S OWN GOALS MUTUALLY UNSATISFIABLE, plus a cluster
of stale or conflated measurements in the evidence requirements. No design decision needed changing.

**THE PARSER NEEDS FOUR ROW SHAPES AND THE PLAN NAMES THREE (PR-601, HIGH).** `7ckptx` and `c4gd2h`
write criteria as `- A1. ...`, a dash followed by the enumerated id, which matches none of E-01's three
shapes (bold needs `**`, table needs a leading `|`, bare-enumerated as specified has no dash). Measured
per shape across the 19 id6-bearing specs: three shapes reach 6 specs and `7ckptx` yields ZERO criteria;
four reach 8, with `7ckptx` at 36 and `c4gd2h` at 10. This makes E-01's "exactly the 8 specs", E-03's
"`uonrjg` and `7ckptx` fully covered" and V-03's "`7ckptx` as fully covered" impossible to satisfy
together, so an executor building the parser to spec would have to contradict one of its own acceptance
statements. The fix is one optional `- ` prefix, so the omission is purely an authoring miss.

**FIVE PER-SPEC COUNTS ARE STALE AND TWO VALIDATION ITEMS DEMAND THEM AS EQUALITIES (PR-602, MEDIUM).**
`uonrjg` has 25 criteria, not F-01's 21 (which counts only un-suffixed ids while V-01 separately requires
`A12b`-`A12d` be matched); `6kwd2e` has 49, not 41; `7ckptx` has 36, not V-03's 33; and three
id6-bearing specs have no acceptance heading (`25kzda`, `77tr3o`, `pqsx96`), not two. The 19-of-38,
16-of-19 and 8-declaring figures reproduce. No conclusion moves, but V-01 and V-03 ask for these as
pasted facts, so an honest executor would measure correctly and appear to fail.

**"22 FINDINGS" CONFLATES CRITERIA WITH DRIFTS AND CONTRADICTS E-04 (PR-603, MEDIUM).** F-04, E-03,
F-05 and V-03 all describe the ungated rule as producing 22 findings. E-04 mandates one `Drift` per
spec, and the 22 is 11+11 uncovered CRITERIA across exactly TWO specs, so the finding count is 2.
Measured under both gate settings: 2 reported specs ungated, 0 gated. A reader checking "22" against
`aw check` output would never see it.

**V-04 DEMANDS OUTPUT FROM A DELETED TEST (PR-604, MEDIUM).** E-04 cites
`tests/test_graduation_view.py::NoUniquenessRuleTests` as structurally prohibiting the substrings
`graduation` and `duplicate`, and V-04 requires pasting its result. The whole file was deleted in
`19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") and the class name appears nowhere
in `tests/`. The prohibition itself stands on its recorded merits, recoverable from git history, and
costs nothing to honor since no registered rule id contains either substring. This is the third plan in
this review sweep to cite a guard that commit removed.

**TWO MISQUOTATIONS, ONE IN THE WORST PLACE FOR ONE (PR-605, LOW).** F-05's parenthetical says an empty
drift list exits 1; it exits 0. And F-07 attributes to survey `vkub9o` the figures "37 plans mentioning
it" and "41 criteria", where the survey says `c4gd2h` and `6kwd2e` "have 25 and 52 requirement ids
respectively". F-07 exists precisely to represent a prior recommendation AGAINST this work fairly, which
makes it the least defensible place for a misquotation; its substance and its verbatim B-minus quote are
otherwise accurate.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 is left `open` DELIBERATELY: it is a genuine priority/ordering call the maintainer owns, it
is correctly flagged `Blocking: no`, and it carries `Carrier: 1zknu7`, so the lint gate does not hold
the plan. Review independently confirmed the survey premise it rests on (4 criteria-declaring specs have
zero linked plans and are unreachable by this rule). OQ-02 is new, recording that the parser correction
is not a scope change.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | plan E-01 (three shapes), E-03 and V-03 ("`7ckptx` fully covered"); `7ckptx`'s acceptance section line `- A1. Build an isolated prompt from BOTH drivers ...` | THE CORPUS NEEDS A FOURTH ROW SHAPE THE PLAN DOES NOT NAME, and without it the plan's own goals conflict. `7ckptx` and `c4gd2h` use `- A1.` (dash plus enumerated id), matching none of the three specified shapes. Measured: three shapes reach 6 specs with `7ckptx` at ZERO criteria; four reach 8, `7ckptx` at 36, `c4gd2h` at 10. E-01's 8-spec outcome, E-03's and V-03's `7ckptx`-fully-covered requirements cannot all hold as authored. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one optional `- ` prefix on a regex the plan already specifies, in a file already declared) | FIXED | Added F-09 with the per-shape table. E-01 now specifies FOUR shapes and names the dash form explicitly with the measured consequence of omitting it. E-03's and V-01's expected outcomes updated (`7ckptx` 36 of 36, reachable only via the fourth shape). Added OQ-02 recording that this is not a scope change and that the risk direction is favourable. Proposed-changes item 1 updated. |
| PR-602 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact convention) | plan F-01 (`uonrjg` 21, `6kwd2e` 41), V-03 (`7ckptx` 33 of 33), E-01 and F-05 (two heading-less specs); re-measurement (25, 49, 36, three) | FIVE PER-SPEC COUNTS DO NOT REPRODUCE, AND TWO VALIDATION ITEMS DEMAND THEM AS EQUALITIES. `uonrjg` is 25 (F-01's 21 omits the four `A12a`-`A12d` ids V-01 separately requires), `6kwd2e` is 49, `7ckptx` is 36, and three id6-bearing specs lack an acceptance heading rather than two. The structural figures (19 of 38, 16 of 19, 8 declaring) reproduce. No conclusion changes, but an executor measuring honestly would appear to fail V-01 and V-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 enumerating all five with measurements. Corrected F-01, F-04, F-05 and F-08's disposition split in place. V-01 now requires re-derivation, keeps only the 8-spec total and the zero-count specs as equalities, and instructs the executor to report divergence as a finding rather than adjusting code to match stale prose. |
| PR-603 | MEDIUM | IN-SCOPE | A. Correctness (internal consistency) | plan F-04, E-03, F-05 and V-03 ("22 findings"); E-04's one-`Drift`-per-spec mandate; corpus run (2 reported specs ungated, 0 gated) | THE PLAN REPORTS ITS OWN OUTPUT IN THE WRONG UNIT, contradicting its own aggregation rule. 22 is the uncovered CRITERIA total across two specs; the emitted `Drift` count is 2. V-03 asks the executor to paste a total "rising to 22", which `aw check` would never show. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11 with both units measured. E-03 now says count Drifts not criteria and states both. F-04 and F-05 corrected to name two reported specs covering 22 criteria. V-03 requires BOTH units explicitly and forbids pasting "22 findings". |
| PR-604 | MEDIUM | IN-SCOPE | E. Testing (dangling citation) | plan E-04 and V-04 citing `tests/test_graduation_view.py::NoUniquenessRuleTests`; `ls` -> No such file; `git log --diff-filter=D` -> `19313eed` | V-04 DEMANDS OUTPUT FROM A TEST THAT NO LONGER EXISTS. The file was deleted in the repository-wide suite trim and the class name appears nowhere in `tests/`. The prohibition it encoded remains valid and free to honor (no registered rule id contains either substring), but an executor would search, find nothing, and either fabricate the paste or skip the item. Third occurrence of this deleted-guard class in this sweep. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the deletion evidence and the class's recorded reason recovered from git history. V-04 no longer asks for the test result; it requires the grep plus a driven `RULE_REGISTRY` probe returning `[]`, cites `git show 19313eed^:...` for the reasoning, and explicitly forbids recreating the deleted guard. Gate repeats the prohibition. |
| PR-605 | LOW | IN-SCOPE | A. Correctness (citation accuracy) | plan F-05's "empty -> 1"; F-07's "37 plans"/"41 criteria" against survey `vkub9o`'s "25 and 52 requirement ids respectively" | TWO MISQUOTATIONS. `drift_exit_code([])` returns 0, not 1 (the predicate is `any(...)`), though the three terms carrying the severity argument are right. And F-07 misattributes figures to the survey it cites; since F-07's entire purpose is to represent a prior recommendation AGAINST this work fairly, a wrong number there is the least defensible kind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with both driven/read corrections. F-05's parenthetical corrected in place with a note that the conclusion is unaffected. F-07 now quotes the survey's actual figures and marks the correction, keeping its verbatim B-minus recommendation. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The parser needs a fourth row shape. Add it to E-01, or narrow E-03/V-03 to drop `7ckptx`? | ADD THE SHAPE to E-01 and keep `7ckptx` in scope. | (a) Narrow the expected outcomes to 6 specs and drop `7ckptx` - rejected: `7ckptx` is one of only two specs that are genuinely fully covered today, so it is the plan's best evidence that the rule is silent on correct work, and dropping it weakens the 0-finding corpus claim. (b) Leave the contradiction for the executor - rejected: they would have to violate either E-01 or E-03, and either choice silently changes what ships. (c) Treat it as a scope change needing re-approval - rejected: it is one optional `- ` in a regex E-01 already mandates, in a declared file, with no new item or test surface (recorded as OQ-02). | Per-shape yields across the 19 id6-bearing specs: three shapes -> 6 specs, `7ckptx` = 0; four -> 8 specs, `7ckptx` = 36, `c4gd2h` = 10. Re-measured whole corpus WITH the fourth shape: still 0 reported findings at HEAD. | yes |
| D-2 | Five per-spec counts are stale. Correct the digits, or mark all counts as re-derive-at-execution? | BOTH: correct each in place and require re-derivation, keeping only the 8-spec total and the zero-count specs as equalities. | (a) Just fix the digits - rejected: they are a live corpus and will drift again before execution, and the repository convention forbids a live-artifact count as an acceptance bar. (b) Strip the numbers - rejected: F-01's and F-05's arguments depend on showing the corpus shape concretely, and a claim with no number cannot be disputed. | Independent parser over `_iter_spec_records`: `uonrjg` 25 (ordered-dedup list including `A12a`-`A12d`), `6kwd2e` 49, `7ckptx` 36, heading-less = `['25kzda','77tr3o','pqsx96']`. The 19/38, 16/19 and 8 figures reproduce. | yes |
| D-3 | V-04 cites a deleted test. Require the executor to restore it, or replace the evidence clause? | REPLACE THE CLAUSE with a driven registry probe, and explicitly forbid restoring the guard. | (a) Require restoring `NoUniquenessRuleTests` - rejected: the deletion was part of a deliberate repository-wide trim with its own test-count budget, so restoring it is a decision about that trim rather than work this plan carries; the same reasoning was applied to backlog `1bxw6o` earlier in this sweep. (b) Drop the prohibition entirely - rejected: the reason survives in the deleted source and is sound (such a rule "would fire on every legitimate multi-artifact cluster on every `aw check` run"), and honoring it costs nothing. | `git show 19313eed^:tests/test_graduation_view.py` showing the class and its recorded reason; `rg` finding the name nowhere at HEAD; `[k for k in RULE_REGISTRY if 'graduation' in k or 'duplicate' in k]` -> `[]`. | yes |
| D-4 | OQ-01 asks whether this rule should ship before or after `1zknu7`, and is `open` with `Owner: maintainer`. Resolve it at review? | LEAVE IT OPEN, and confirm the premise it rests on. | (a) Resolve it to "ship this first" on the author's recommendation - rejected: it is an ordering and priority call the maintainer owns, exactly the class the execution contract reserves for a human, and it is correctly non-blocking with a carrier so nothing is held up. (b) Escalate it to `Blocking: yes` - rejected: the plan is correct on its own terms in either order, so blocking would stop work for a question that does not gate correctness. | The survey's decisive premise verified independently: 4 criteria-declaring specs (`c4gd2h`, `6kwd2e`, `w15vzb`, `4sd62s`) have ZERO linked plans and are unreachable by this rule regardless of its quality. `- Blocking: no` plus `- Carrier: 1zknu7` already recorded. | yes |
