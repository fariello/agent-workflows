# Review findings: plan 2wmwf7

- Subject-Id: 2wmwf7
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed)

## Round 1

Reviewed at HEAD `c8730ebb` in an isolated review lane. The plan file was committed and unmodified
(`git status --porcelain` on it returns nothing), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize --agent` reports `conforming` (exit 0, zero findings) after
revision, including the new `E-07`/`E-08` and `V-07`/`V-08` pairs.

THE PLAN'S CENTRAL JUDGEMENT IS CORRECT AND IS THE BEST THING IN IT. The backlog item names two
dangling citations as if both were typos; the plan establishes that ONE OF THEM MUST NOT BE FIXED,
because it lives in an executed plan and was CORRECT WHEN WRITTEN. I verified that chain of evidence
independently rather than accepting it: `git ls-tree -r --name-only 7c68a4e3` lists the spec at the
FLAT `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md` path the plan
cites, and `2fa65732` ("migrate specs into status subdirectories") is what moved it to
`implemented/`. So rewriting the citation would make a 2026-09-20 plan appear to cite a path that
did not exist until 2026-09-24. That reasoning is sound and it is the plan's load-bearing
contribution; it survives review untouched.

EVERY OTHER MATERIAL CLAIM ALSO VERIFIES. `agent_workflows/agy_run.py`'s `--spec` epilog example
(line 122) cites a path `ls` cannot find; the real file is
`.aw/records/specs/superseded/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`,
so F-5's warning that the SLUG differs and a mechanical directory-prefix rewrite would still dangle
is correct and worth the words it spends. `check_engine.py`'s I-07 comment cites the flat
`pqsx96` path (real file under `draft/`), and I confirmed the `:135` anchor still holds: line 135 of
that spec IS the `I-07` / `Release-gate preservation` row. F-7's bug is real and worse than a code
read would suggest: I CALLED `resolve_spec` and it raised `No specification matching ... found` for
a bare filename, for the bare id6 `pqsx96`, AND for a correct-looking flat full path, while
succeeding only on the true `draft/` path. `Path('.aw/records/specs').glob('*.md')` yields
`['README.md']` against `rglob('*.spec.md')`'s 38. F-8 also holds: `y4bdoz` asserts "exactly ONE
non-recursive site" while `tools/agy_run.py` existed from `1ca197c7` and was packaged at
`4579ba87`, both before its review, and `grep -rn resolve_spec tests/` returns nothing.

WHAT REVIEW CHANGED, AND WHY EACH CHANGE MATTERS. The two HIGH findings are both about E-04, the
regression test, which is the only DURABLE artifact this plan leaves behind: the two comment repoints
are one-line edits, so if the test is wrong, the plan's lasting contribution is wrong. PR-901: the
scan root included `tools/`, which holds ZERO such citations (measured: the only two hits in either
tree are the ones E-02/E-03 fix) but DOES hold three test files full of deliberately unresolvable
spec fixture names, so including it buys no coverage and arms a future false positive. Sibling plan
`68hdic`'s review raised precisely this class in `tools/` as its BLOCKER. PR-902: the repository has
a named, MEASURED policy for a test shaped like this one and the plan never mentions it. A test
asserting a property over `.aw/records/` is marked `livecorpus` and deselected by default because any
agent authoring a plan can turn it red and a red test blocks integration for EVERY concurrent lane
(`pyproject.toml` markers, measured 2026-09-19 at 2h 10m and $55.02 with nothing integrated). The
plan's bound to package source is therefore not tidiness, it is what keeps the test in the default
run and thus able to catch anything; the plan now says so, and V-04 demands proof the test is
SELECTED rather than deselected.

PR-905 IS THE FINDING I EXPECT TO BE ARGUED WITH, so I state its limit rather than overselling it.
The same defect class sits in a WHEEL-PACKAGED install template
(`.aw/system/workflows/templates/agents-docs-research-README.md`), force-included into the wheel and
written into a managed target repo by `engine.ensure_docs_readmes`. That is closer to "live source"
than anything the plan correctly excludes, and it was neither fixed nor recorded. I added E-07 to fix
it and declared the path. BUT I held it at MEDIUM and wrote the limit INTO the finding: in a target
repo NEITHER the stale nor the corrected path resolves, because the target has its own specs tree and
never contains this repository's spec. So the propagation is real, and it does not make a target's
copy newly wrong. Anyone reading F-16 as "every target repo is broken" is reading more than the
evidence supports, which is why the row says so.

PR-903 and PR-904 are corrections to the plan's own numbers, in the same spirit the plan applies to
its backlog item. The census pattern counts ELLIDED strings that cite no real path, and this plan's
own prose contains several, so the authoring figure was not reproducible (I measured 487 across 159
files where the plan records 470 across 151, using the same loose definition); E-05 now must state
its definition and count ellided forms separately. And the `u06zo2` claim of "five" citations is
wrong in a direction that CUTS AGAINST THE PLAN'S OWN ARGUMENT: the filename appears seven times and
only ONE carries the `.aw/records/specs/` prefix, the other six being bare filenames a status
transition cannot invalidate. The immutable record holds one stale path citation, not five. The
plan's conclusion is unaffected and its evidence is now accurate.

I ALSO STRENGTHENED OQ-01 RATHER THAN RESOLVING IT, because it is genuinely the maintainer's call
(whether a status transition should refuse on a stale in-tree citation is a policy question with a
real cost). What review supplied is the measurement the decision turns on, re-derived: 456 of 487
dangling citations sit in files whose only correct response to a warning is to ignore it, about 94
percent, against 2 in package source. The row previously cited "404 of 470", both stale. The
corrected ratio STRENGTHENS the plan's argument for not adding a transition-time guard. I also noted
a scope point the question misses: F-16's instance is in neither a record nor package source, so a
guard scoped to "package source and live plans" would not have caught it either.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | E. Testing / F. Prevent silent failure | Scan of both trees at `c8730ebb` yields exactly two hits, the `Example: python3 tools/agy_run.py --spec` line in `agent_workflows/agy_run.py` (122) and the comment after `I-07 IS THE RIGHT HOME AND THE FIT WAS VERIFIED` in `agent_workflows/check_engine.py` (289), none in `tools/`; `tools/test_agy_run.py` cites `.agents/docs/specs/test.spec.md` (71) and `20260810-01-feature.spec.md` (186) as fixtures; `68hdic` review PR-701 | E-04's scan root included `tools/**/*.py`, which carries ZERO in-scope citations so adds no coverage, while holding three test files of deliberately unresolvable spec fixture names. The first `tmp_path` fixture written there under the scanned prefix turns the test red on correct code. The sibling plan's review classed the same hazard a BLOCKER | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-12 records the measurement. E-04 is now bound to `agent_workflows/**/*.py` ONLY, with the `tools/` exclusion justified from measurement and a condition (carry `68hdic`'s test-file exclusion) if an executor still wants it. V-04 demands pasted proof of the scan root |
| PR-902 | HIGH | UNDER-SCOPE | E. Testing / C. Operability | `pyproject.toml` `markers`: a `livecorpus` test "asserts a property over EVERY artifact in this repository's own .aw/records/ tree, so ANY agent writing a plan can turn it red", measured cost "2h 10m and $55.02 with nothing integrated" (2026-09-19); `addopts` carries `-m 'not slow and not livecorpus'`; examples `tests/test_ipd_lint.py` (2145), `tests/test_orchestrator_probe_payload.py` (246) | The plan never mentions the repository's named, measured policy for exactly this test shape. E-04's package-source bound is what keeps the test SELECTED by the default run; had it scanned the records trees it would have had to be `livecorpus`-marked and deselected, and a deselected test would not have caught either dangler. Nothing in the plan recorded this, so an executor could reasonably have widened the scan and silently destroyed the test's value | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-13 records the policy with its measured cost. E-04 now forbids the `livecorpus` marker and forbids reading the records trees, stating the reason. V-04 demands a run showing the test is collected rather than `deselected` |
| PR-903 | MEDIUM | IN-SCOPE | G. Executability / live-artifact criteria | Re-measured at `c8730ebb`: the loose pattern yields 487 hits across 159 files, not F-6's 470/151; the pending-plans subset includes this plan's own ellided strings `.aw/records/specs/...spec.md` and `.aw/records/specs/20260815-0151-01-...spec.md` | The census counts ELLIDED forms that cite no real path, so E-05's per-class numbers are not reproducible by a reader and the plan's own prose inflates them. Re-measuring at HEAD without fixing the DEFINITION reproduces the same unreproducible figure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 records the measured drift and the cause. E-05 must now state the scan's exact definition beside its numbers, exclude ellided forms, and report them separately; its Expected outcome is updated to match |
| PR-904 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | `grep -n` on `.aw/records/plans/executed/20260908-lcpolicy-01-u06zo2-...ipd.md` returns SEVEN lines (26, 68, 88, 103, 107, 148, 720), not the five the plan lists; classifying each, only line 107 carries the `.aw/records/specs/` prefix, the rest being bare filenames | The `u06zo2` count is wrong in both directions and the error cuts AGAINST the plan's own argument: the immutable record holds ONE stale path citation, not five, plus six bare-filename citations a status transition cannot invalidate | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records the correct count and the classification. The plan's conclusion (do not edit the executed plan) is unaffected and now rests on accurate evidence |
| PR-905 | MEDIUM | UNDER-SCOPE | A. Correctness / C. Architecture | The `Research artifacts follow the grammar (spec` line in `.aw/system/workflows/templates/agents-docs-research-README.md` (9) cites `20260730-2152-01-agents-artifact-organization.spec.md`, real path under `implemented/`; `pyproject.toml` `force-include` maps `".aw/system"` to `agent_workflows/_data/.aw/system`; `engine.ensure_docs_readmes` reads `plan.source_root / "templates" / f"agents-docs-{tmpl_bucket}-README.md"`; also `ipd-lifecycle.md` (7), `TODO.md` (15, 28), `DECISIONS.md` (2569) | The same defect class sits in editable NON-test, NON-record files the plan's test cannot see, one of them a wheel-packaged install template copied into every managed target repo at install time. This is closer to the plan's stated "live source" concern than the record-tree danglers it correctly excludes, yet was neither fixed nor recorded | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-16, with its own limit stated (in a target repo neither path resolves, so the fix's benefit is scoped to this repo and a citation-following reader; NOT "every target is broken"). New E-07 fixes the template and declares the path in `Scope-Paths`; new E-08 records the three deliberately unfixed instances with a live-pointer-versus-history judgement each; V-07/V-08 demand existence checks, the packaging proof, and that the installed `.aw/records/research/README.md` is NOT touched |
| PR-906 | LOW | IN-SCOPE | OQ quality | Re-measured at `c8730ebb`: 456 of 487 dangling citations (about 94 percent) sit in immutable or fixture files, 2 in package source; OQ-01's row cited "404 of 470", both stale | OQ-01 asked the maintainer to weigh a noise ratio it quantified with stale numbers, and it scoped any future guard to "package source and live plans", which would not have caught F-16's template instance | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 left `open` and `Owner: maintainer` (correctly a policy call), but supplied with the re-derived ratio, an explicit note that the corrected figure STRENGTHENS the argument against a transition-time guard, and the scope point that a guard must decide its own scope, not merely whether to exist |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the E-04 regression test scan `tools/` as well as `agent_workflows/`? | No: bind it to `agent_workflows/**/*.py`, with a stated condition if an executor still wants `tools/` | Keep both trees (rejected: zero coverage gained, future false positive armed); both trees plus a test-file exclusion (rejected as the DEFAULT, kept as the documented option) | Measured at `c8730ebb`: both in-scope hits are under `agent_workflows/`, none under `tools/`; `tools/test_agy_run.py` (71, 186) holds unresolvable spec fixture names; `68hdic` review PR-701 classed the same hazard a BLOCKER | yes |
| D-2 | Should the new test be allowed to scan the records trees (and so need the `livecorpus` marker)? | No: forbid both the records-tree scan and the marker | Allow a records-tree scan marked `livecorpus` (rejected: deselected by default, so it would not have caught either dangler and would red-flag every concurrent lane) | `pyproject.toml` `markers` + `addopts` `-m 'not slow and not livecorpus'`, with the 2026-09-19 measured cost of 2h 10m / $55.02 recorded in the marker text | yes |
| D-3 | Is the wheel-packaged install template dangler in scope for this `chore`, or should it be filed separately? | In scope: fix it here as E-07 and declare the path | File a separate backlog item (rejected: it is the identical defect class, a comment-string repoint, changing no behavior, so splitting it would cost a permanent record for a one-line edit); leave it unrecorded (rejected: it is closer to the plan's own concern than what it excludes) | `pyproject.toml` `force-include` of `".aw/system"`; `engine.ensure_docs_readmes`'s template read; the plan's own `- Work-Kind: chore` rationale that a comment repoint is imperceptible | yes |
| D-4 | Should the three other live-editable instances (`ipd-lifecycle.md`, `TODO.md`, `DECISIONS.md`) be fixed too? | No: RECORD them (E-08) with a live-pointer-versus-history judgement each | Fix all three (rejected: `ipd-lifecycle.md` is a workflow BODY, so editing it changes controlling instructions and belongs to a plan that owns it; `DECISIONS.md` is an append-only dated log, so the same falsify-history reasoning that protects `u06zo2` applies); ignore them (rejected: silent omission of a measured instance) | `AGENTS.md` immutability contract as applied in this plan's own F-3; `DECISIONS.md` header "Append-only, dated record"; `TODO.md` header declaring itself deprecated notes-only | yes |
| D-5 | Should OQ-01 be resolved at review instead of left to the maintainer? | No: leave `open`, `Blocking: no`, `Owner: maintainer`, but supply the measurement | Resolve it as "add a narrow guard" (rejected: it commits the maintainer to a cost, and whether a transition should refuse is a policy judgement, not a repository fact); resolve it as "never add one" (same objection inverted) | plan-review Step 3.1: resolve from authoritative evidence, never guess a human decision; the repository answers the RATIO but not the POLICY | yes |
