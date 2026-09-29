# Review findings: plan 3xd1pm

- Subject-Id: 3xd1pm
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `86fafc93` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after. No pre-review snapshot was owed: the plan was committed and unmodified. `aw check` reports no
finding against this plan in either state. `agent_workflows/selectors.py` was mutated SIX times as a
measurement technique and reverted with `git checkout --` each time; `git diff --stat` on it is empty
and the working tree holds only the plan's own edit.

THE ENTIRE MUTATION CENSUS WAS REPRODUCED INDEPENDENTLY, not spot-checked, because every one of this
plan's seven items is justified by it and a stale census would justify the wrong tests. The baseline
is unchanged from authoring (`3246 passed, 2 skipped, 3 warnings`, 207 deselected as
`slow`/`livecorpus`). Every mutation returned the plan's exact figure:

- M5 (unbound all three readers from the metadata region, the full `76w6mq` revert): `3246 passed, 2 skipped`. UNGUARDED, as claimed.
- M1a (remove the YAML `id:` fallback from `_read_id` alone): `3246 passed, 2 skipped`. UNGUARDED.
- M2 (make the YAML key lookup case-tolerant): `3246 passed, 2 skipped`. UNGUARDED.
- M6 (bypass `_normalize_yaml_scalar`): `3246 passed, 2 skipped`. UNGUARDED.
- M1b (remove the `status` fallback): `5 failed, 3241 passed, 2 skipped`, failures in `tests/test_cli_find.py::CliFindResearchStatusTests` and `tests/test_research_archive.py`, exactly as F-2 describes.
- M1c (remove the `setid` fallback): `3 failed, 3243 passed, 2 skipped`, failures in `tests/test_research_archive.py::BehavioralParityAndRefusalTests`.

The live-tree consequence reproduced to the individual file. Clean, repository-wide id6 collisions
through `_read_id` are 0; under M5 exactly one id6 collides, `uyeko5`, across its own executed plan
plus the two `research/reference/202609/` documents (`takpys`, `27rjro`) that quote its metadata
block. That is the precise state `76w6mq` records as "not overridable by --force", so the plan's
central claim about user-visible harm is exact rather than rhetorical.

The supporting corpus measurements reproduced too: 130 tracked research `.md` with `_read_id`
answering 123, `_read_setid` 123, `_read_status` 116 (F-1); ZERO research records declaring an id6
absent from their own filename, which is what makes E-05's naive test genuinely vacuous; ZERO tracked
fenced non-research records and no `prompts/untracked/` lane in an isolated worktree, which is E-04's
correction of `xo3244` and is the reason a census-shaped case would pass vacuously in a runner lane.
Each fixture behavior E-03 through E-07 asserts was driven directly and matched the plan's stated
values, including the deliberate bullet asymmetry (`'`bulletset`'`, backticks intact) and the
capitalized-key parser dict (`{'Kind': 'session-handoff', 'Status': 'draft', 'Date': '2026-09-28'}`).

This is an unusually well-measured plan and the review found no fault in its reasoning, its scope, or
its choice of properties. What it found is one API shape error that would have cost an execution cycle,
one dead citation in the production code that changes what half of an item means, and two evidence
precision slips.

**`resolve_for_mutation` RETURNS A 2-TUPLE AND E-05 DESCRIBED A RESULT OBJECT (PR-201, HIGH).** E-05
writes "`resolve_for_mutation` succeeds with `n=1`" in the same sentence as a `resolve` call whose
`kind`/`n` it has just described, and `resolve` does return an object carrying `.kind` and `.paths`.
But `resolve_for_mutation` returns `(paths, error_message)` per its own docstring, with
`error_message` None on success and `paths` empty on refusal. Review hit
`AttributeError: 'tuple' object has no attribute 'paths'` while reproducing E-05's own fixture, which
is exactly where an executor would hit it. Two sibling calls with different shapes is precisely the
kind of thing a plan must state rather than leave to discovery. Fixed in E-05 and V-05, which now
mandate `paths, err = ...` unpacking. The same fix carries a second measured detail: the refusal
message interpolates ABSOLUTE tempdir paths, so it must be matched on a distinctive substring
(`is ambiguous (substring)`) and never compared whole, since a `TemporaryDirectory` differs every run.

**THE BULLET-ASYMMETRY PIN THE CODE CITES NO LONGER EXISTS (PR-202, MEDIUM).** Both
`_normalize_yaml_scalar`'s docstring and the deleted `YamlScalarNormalizationTests` name
`tests/test_cli_find.py::BacktickSetValueIsPinnedTests` as the guard that keeps normalization off the
bullet dialect. That class is present nowhere under `tests/`, and `git log -S` shows `19313eed`
removed it in the same trim that deleted this plan's two ancestors. This does not change E-06's
instruction, which already asserts the bullet side, but it changes its STATUS from a belt-and-braces
precaution to a genuine restoration, and it means no executor should read the cited class as existing
coverage. E-06 and a new F-8 now record it. The stale comment is deliberately NOT fixed: this plan
forbids itself any `selectors.py` edit and a comment correction is one.

**TWO EVIDENCE PRECISION SLIPS (PR-203 LOW, PR-204 LOW).** The Concern says the four restorable
classes sit "between" the two deleted files; three of the four (`ResearchResolvesByYamlFrontMatterTests`,
`YamlFallbackIsCaseSensitiveTests`, `YamlScalarNormalizationTests`) are all in
`test_selector_zero_open.py`, as are all four P16-violating pins, leaving only `BoundedReaderTests` in
`test_id_metadata_region.py`. An executor recovering prior art should look in the right file. And the
deleted pair also held a `LiveTreeTests` class asserting over this repository's own `.aw/records/`
tree, which is exactly the shape `pyproject.toml`'s `livecorpus` marker now deselects for its measured
integration-blocking reason; that is a THIRD independent argument against verbatim restoration,
beside P16, and it corroborates the plan's fixture-only choice. Both recorded in F-4.

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed.

OQ-01 SURVIVES REVIEW UNCHANGED AND ITS HANDLING IS CORRECT, which is worth stating because it is the
plan's only open question and it is `Status: open` with `Owner: maintainer`. It is genuinely a scope
question (whether the public runner readers' bullet-only contract belongs in this file, its own file,
or nowhere), it is correctly marked non-blocking since no item depends on the answer, its recommended
option is argued from a verified property (the pair's loose whitespace tolerance), and its
`Carrier-Declined` reasoning is the strongest in the plan: each candidate answer implies a different
carrier, so minting one now would record a decision the maintainer has not made. Under the
2026-09-10 maintainer ruling a non-blocking open question does not make a plan NO-GO, so this does not
hold the plan back.

The plan's other structural choices were checked and are right. The fixture-only decision is
justified by a measured cost ($55.02 and 2h 10m for one `livecorpus` failure), the no-`slow`-marker
decision matches `pyproject.toml`'s KIND-based definition, the deferral rows all carry typed carriers
or well-argued declines, F-5's two unobservable properties are correctly retired rather than left
implied, and the gate carries the honesty rule, the revert obligation, the path-scoped commit rule and
a STOP condition that is about a genuinely unsafe state (a required production edit) rather than about
scope.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | high | IN-SCOPE | G. Plan executability | `agent_workflows/selectors.py` `resolve_for_mutation` docstring ("Returns ``(paths, error_message)``") and its `return [], f"no {record_type} artifact matched ..."` branches; review probe raising `AttributeError: 'tuple' object has no attribute 'paths'` on E-05's own fixture | E-05 describes `resolve_for_mutation` as if it returned a result object with `n`/`.paths`, in the same sentence as a `resolve` call that does. It returns a 2-tuple, so a test written the way E-05 reads raises `AttributeError` and fails for the wrong reason. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-05 mandates `paths, err = ...` unpacking and substring matching of the refusal (which interpolates per-run absolute paths); V-05 fails the item on a `.paths` form; new F-7; two conventions bullets record the differing shapes. |
| PR-202 | medium | IN-SCOPE | D. Anti-regression and domain invariants | `_normalize_yaml_scalar` docstring naming `tests/test_cli_find.py::BacktickSetValueIsPinnedTests`; `rg BacktickSetValueIsPinnedTests tests/` -> no match; `git log -S` -> removed by `19313eed` | The pin the production code cites for the bullet-side asymmetry does not exist, so that contract is unguarded on both sides and E-06's second half is a restoration rather than a precaution. An executor could read the citation as existing coverage and skip it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 records the dead citation and forbids relying on it; new F-8, which also notes the stale comment is deliberately not fixed because the plan forbids itself any `selectors.py` edit. |
| PR-203 | low | IN-SCOPE | Evidence accuracy | class listings of both files at `19313eed^` | The Concern says the four restorable classes sit "between them"; three of four and all four P16-violating pins are in `test_selector_zero_open.py` alone, with only `BoundedReaderTests` in the other file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-4 gains a per-file column and a corrective paragraph. |
| PR-204 | low | UNDER-SCOPE | Evidence accuracy | `test_id_metadata_region.py::LiveTreeTests` at `19313eed^`; `pyproject.toml` `livecorpus` marker rationale | F-4 argued against verbatim restoration on P16 grounds only, omitting that the pair also contained a live-corpus test of exactly the shape now deselected by default. A second independent argument for the plan's own fixture-only choice was left unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-4 records `LiveTreeTests` as a third reason not to restore verbatim. |
| PR-205 | low | UNDER-SCOPE | E. Testing and verification | review probe confirming `Path(selectors.__file__)` resolves under the test file's repo root in this lane | V-02 demands a demonstrated failure mode for the provenance assertion but names no workable route, and the obvious one (re-import from a sibling checkout) is both unreachable in-process and an out-of-lane read the lane forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | V-02 now names the acceptable route (invert the assertion's own comparison against a deliberately wrong root, mutating only this plan's scope path) and requires the executor to state which route it took. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's whole justification is a seven-mutation census measured at a different HEAD. Trust it, spot-check it, or reproduce it in full? | Reproduce every consequential mutation in full, with a full bare suite each time. | (a) Trust it: rejected because each E-item exists ONLY because its property is green under mutation, so a single stale row would justify writing a test for a property that is already covered (or omitting one that is not). The plan's own history records three earlier measurements that were false for a path-resolution reason. (b) Spot-check one or two: rejected because the rows are not interchangeable; M1a/M2/M5/M6 each drive a different E-item, and M1b/M1c justify E-07's existence as a distinct item. | Six mutations applied and reverted, each with a full bare suite: M5/M1a/M2/M6 all `3246 passed, 2 skipped`; M1b `5 failed, 3241 passed`; M1c `3 failed, 3243 passed`; plus the `uyeko5` three-way collision under M5 and 0 collisions clean. | yes |
| D-2 | E-05's `resolve_for_mutation` shape error: raise it as a blocking question, or fix the wording in place? | Fix in place, naming the tuple unpacking and the substring-matching requirement. | (a) Blocking question: rejected because the repository answers it outright. The function's own docstring states the return contract and review reproduced both the success and refusal shapes, so this is a documented fact, not a maintainer judgement. (b) Leave it, on the grounds an executor would discover it on the first run: rejected because the plan's gate forbids a production edit and instructs the executor to STOP on one, so an `AttributeError` in the test could plausibly be misread as the kind of trouble that warrants stopping rather than as a one-line fix. | `resolve_for_mutation`'s docstring; measured clean `(len 1, err None)` and mutated `([], 'selector ... is ambiguous (substring) ...')`. | yes |
| D-3 | The production docstring cites a test class that no longer exists. Fix the comment, or record the fact and leave it? | Record it in F-8 and E-06; leave the comment alone. | (a) Fix the comment here: rejected because this plan declares exactly one scope path (`tests/test_selector_two_dialect_readers.py`) and its gate makes any `agent_workflows/selectors.py` edit a STOP-and-report condition, so correcting a comment would breach the plan's own fence for a non-behavioral gain. (b) File a carrier for the comment: rejected as disproportionate, since E-06 is about to assert the behavior the comment claims is pinned, which is the substantive remedy; the stale reference is then a cosmetic residue a later reader can fix in passing. | The plan's `- Scope-Paths:` single entry and its gate wording; `rg` showing the class absent and `git log -S` naming `19313eed`. | yes |
