# Review: Make staged prompts a full artifact-organization and attention adopter

- Subject-Id: dx0u4s
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4e91bb1b`. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` after the revisions.

THE PLAN'S DIAGNOSIS IS CORRECT IN EVERY STRUCTURAL PARTICULAR AND I VERIFIED EACH ONE. `aw index
prompts` prints "WARN 'index' is not supported for prompts."; `TYPE_BACKENDS["prompts"]` carries only
`new`/`rename`/`group`; `SUPPORTED["prompts"]` is `("names",)`; the `prompts` `TreePolicy` is
`tracked=False` with the "deferred to Phase 3 (OQ3)" reason; `.aw/records/prompts` is absent from
`SCAN_ROOTS`; and `aw attention -t prompts --format json` really does report `valid: true` with ZERO
items over a live 17-prompt corpus holding 2 queued prompts. The two `Status:`-versus-bucket mismatches
are exactly the two files it names. Both specs it proposes to amend exist at the declared paths and say
what it says they say. So the premise is sound and the shape of the fix is right.

WHAT THE PLAN GOT WRONG IS THE ORDER, THE CORPUS, AND WHAT ITS OWN EVIDENCE CAN PROVE.

PR-801 IS THE ONE THAT WOULD HAVE BROKEN THE BUILD, and it is a sequencing error rather than a design
one. `tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root`
asserts that every member of `TRACKED_TREES` is covered by some `SCAN_ROOTS` entry. I drove its helper:
NO current scan root satisfies `_scan_root_covers_tree(r, "prompts")`. The authored plan flips the policy
to `tracked=True` in E-03 and adds the scan root in E-05, so that guard is RED for the whole E-03/E-04/E-05
window. That matters beyond a transient red: the guard exists precisely because `releases` once shipped
tracked-with-no-scan-root and was invisible while the view reported valid, and its own docstring says so.
An executor who hits it mid-plan cannot distinguish its own new failures from the one the plan created,
and the nearest "fix" is to weaken the guard that would have caught the real bug. The reverse order is
strictly safe and I checked why: `attention.scan` skips an untracked policy BEFORE reading the file, so a
scan root on an untracked tree changes nothing observable. E-03 and E-04 are now swapped, with V-03
requiring the guard green while prompts is still untracked and V-04 requiring it green after the flip.

PR-802 IS THE CORPUS FINDING AND IT CHANGES A DESIGN DETAIL. The plan says the record's id "comes from
`prompts.read_metadata_id6(text)`" and mentions an "empty id for a legacy comment-less file" only in
passing, inside E-02's fixture description. I drove `read_metadata_id6` over all 17 prompts: exactly ONE
returns a value. So an empty id is not the legacy edge case, it is 16 of 17, and the record builder must
treat it as a normal record rather than as drift. A fixture built on the plan's implied distribution
(most files carrying an id) would be testing a corpus this repository does not have, and the one shape
that must not regress is the common one.

PR-803 IS AN ENFORCEMENT CLAIM THE PLAN CANNOT CASH. E-07 adds three content rules, and the plan's
`Expected outcome` asks only for "exactly the 2 live `check.prompt-status-mismatch` findings". I drove
`check_engine._prompt_requires_id6` over all 17 prompts: it returns False for EVERY ONE, because
`PROMPT_ID6_CUTOVER_DATE` is `20260921` and every filename date precedes it. That constant's own comment
says the value was chosen to sit strictly after the single conforming prompt so "that file's conformance
stays incidental rather than load-bearing". So `check.prompt-metadata-missing` can never fire on the
current tree, and `check.prompt-id-mismatch` cannot either, since the one prompt declaring an `Id:`
matches its filename. The plan's phrasing ("pre-cutover files are grandfathered, which covers all 9
comment-less files") reads as a narrow carve-out when the grandfathering is TOTAL. These are legitimate
forward-looking guards; what is not legitimate is evidencing them with live silence, which is the
expected no-op. E-07 now says so and V-07 demands synthetic-fixture evidence for both.

PR-804 is a nonexistent symbol used as an acceptance bar. E-05's `Expected outcome` required
`ScanRootClassificationInvariantTests` to stay green. That class does not exist, and neither does the
`tests/test_artifact_core.py` that `artifact_core.py`'s own comment points at; the real guard is
`TrackedTreeScanCoverageTests` in `tests/test_attention_contract.py`. An executor would have found
nothing to run and either invented a test or recorded the item satisfied by an empty search, which is the
failure mode the plan's own citation convention exists to prevent (and a test-class name is a symbol).

PR-805 is two inverted counts. The plan says "8 carry the `aw-prompt` comment" and "9 of 17 files have
no comment"; measured, it is 9 with and 8 without. The conclusion the numbers support is unchanged and in
fact slightly stronger, so this is low severity, but the figure appears in a Findings row and in E-04's
justification, and a reviewer checking the reasoning would have found the arithmetic not matching.

PR-806 is a risk the plan flagged as unknown that I was able to measure and largely retire. E-05 (now
E-03) widens `SCAN_ROOTS`, and the plan correctly notes that the dangling checks consume it, then asks the
executor to stop if new findings appear. I confirmed the mechanism (`find_dangling_citations`' `scan_roots`
parameter defaults to the module constant and `plans_index.check_drift` passes no override) and then drove
it: the widening adds 23 files to a 1592-file scan and produces ZERO new dangling citations for plans and
zero for research. I also confirmed the 6 README files the widening pulls in never become attention items,
because `attention.scan` filters them through `is_nonartifact_name` before `_record_for`. The stop
condition is worth keeping; the plan now carries the measurement so an executor knows what "unchanged"
looks like, and knows the baseline is not clean (both checks already report findings at HEAD).

PR-807 is a drifting-count problem the plan half-anticipated. It pins the whole-view total at `True 1508`
and asks the executor to "STOP and report" if any claim moved. That total is `True 1540` at review, 32
items later, because it counts a live corpus. Under the authored wording the first thing the executor does
is stop on an expected change. E-01 now distinguishes a STRUCTURAL claim (whose movement really does
invalidate the premise) from a COUNT (which is recorded), and states every figure as context to re-derive.

PR-808 is the gate: three sentences, no approval statement, no scope fence across seventeen declared
paths, no stop conditions, and a transition instruction naming a directory move.

I RESOLVED OQ-01's CARRIER RATHER THAN ITS SUBSTANCE. The question (does a `reusable/` prompt get `parked`
or plans-parity `ready`) is genuinely the maintainer's and stays open and non-blocking. I verified its
counter-evidence is real (`_PLANS_MAP` does map plans `reusable` to `READY`) and that `reusable/` is empty,
so neither answer changes live output, and I added the consequence the plan omitted: `parked` items are
auto-hidden from the default board, which is what the default is chosen for. I gave it a
`Carrier-Declined` because the answer is one dict entry inside this plan's own diff and leaves no work
behind it.

RECORDED SO A LATER READER DOES NOT RE-DERIVE IT: `.aw/records/prompts` and `.aw/records/prompt-library`
classify to DIFFERENT policies (`prompts` versus `docs-prompts`) through `attention._classify_tree`'s
`.aw/records/` rewrite, so the `prompts` `TreePolicy.root` spelling needs no change and
`_TREE_TO_SCAN_ROOTS["prompts"]` listing both roots is harmless. `tests/test_check_engine.py`'s
`"content over prompts"` row keeps its expected `()` because that shared fixture holds a plan and a spec
and no prompt. `V-05`'s predicted `True 17` is correct given the README filter. Backlog `oxjt1d` carries no
`- Blocks-Release:` and is `Work-Kind: feature`, so no release gate is owed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | D. Anti-regression / G. Plan executability | Drove `TrackedTreeScanCoverageTests`' own `_scan_root_covers_tree` helper: no entry of `SCAN_ROOTS` covers `prompts` today; `attention.scan` skips a policy with `tracked=False` before reading the file; that test's docstring records `releases` shipping tracked-with-no-scan-root as the drift it exists to stop | THE ITEM ORDER LEAVES A SHIPPED GUARD RED ACROSS THREE ITEMS. Authored E-03 flips `tracked=True` while the scan root arrives only in E-05, so `test_every_tracked_tree_has_a_scan_root` fails throughout E-03/E-04/E-05. An executor then cannot separate its own new failures from the self-inflicted one, and the nearest apparent fix is weakening the guard that would catch the real bug this plan is avoiding. The reverse order is strictly inert, because an untracked tree with a scan root changes no output. | C:Low; U:Low; S:Low; F:Medium (a red guard invites its own weakening); Overall:Medium | FIXED | Swapped: E-03 is now the `SCAN_ROOTS` widening with the inertness argument stated, E-04 the policy flip, E-05 the record builder. V-03 requires `tests/test_attention_contract.py` PASSING while prompts is still untracked (the ordering proof) and V-04 requires `-k TrackedTreeScanCoverage` passing after the flip. Added F-9, a conventions bullet, and a Proposed-changes note that the order is deliberately reversed. |
| PR-802 | MEDIUM | UNDER-SCOPE | A. Correctness / E. Testing | Drove `prompts.read_metadata_id6` over all 17 live prompts: exactly ONE (`ng0ga4`) returns a value; the other 16 return `None` (8 have no leading comment at all, 8 have a comment with no `Id:`) | AN EMPTY ID IS THE NORM, NOT THE LEGACY EDGE CASE, and the plan treated it as an aside. E-04 said the id "comes from `read_metadata_id6`" with the empty case mentioned only inside E-02's fixture prose. At 16 of 17 files, the empty-id path is the one that must not regress, and a fixture built on the implied distribution (most files carrying an id) would test a corpus this repository does not have. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 states the measurement and requires an empty id be handled as NORMAL rather than drift. E-02 requires a fixture matching the live distribution (at least one with an id, at least two without, one of those with no comment). V-05 requires the executor to state how many of the 17 items carry an empty id. Added F-7. |
| PR-803 | MEDIUM | IN-SCOPE | B. Security-adjacent honesty / F. Honest documentation | Drove `check_engine._prompt_requires_id6` over all 17 prompts: False for EVERY one, because `PROMPT_ID6_CUTOVER_DATE` is `20260921` and every filename date precedes it; that constant's comment states the value was chosen so the one conforming prompt's "conformance stays incidental rather than load-bearing"; the single prompt declaring an `Id:` matches its filename | TWO OF THE THREE NEW RULES FIRE ON ZERO LIVE FILES AND THE PLAN'S EVIDENCE COULD NOT TELL. `check.prompt-metadata-missing` and `check.prompt-id-mismatch` have no live subjects at all, and E-07's expected outcome asked only for the 2 `status-mismatch` findings, so their live SILENCE would have been recorded as a passing validator. The wording "pre-cutover files are grandfathered, which covers all 9 comment-less files" implies a narrow carve-out where the grandfathering is total. They are legitimate forward-looking guards; evidencing them with an expected no-op is not. | C:Low; U:Low; S:Low; F:Medium (a rule believed active that cannot fire); Overall:Low | FIXED | E-07 states plainly that both rules have zero live subjects, why (the cutover), and that their only possible evidence is synthetic fixtures; it requires fixture coverage including a post-cutover-dated comment-less prompt. Its expected outcome now also asserts ZERO findings for those two rules. V-07 demands the fixture evidence and forbids citing live silence. The gate names this as a honesty-rule temptation. Added F-8 and an Under-scope note. |
| PR-804 | MEDIUM | IN-SCOPE | G. Plan executability (citation) | `rg ScanRootClassification` matches ONE line, a comment inside `agent_workflows/artifact_core.py`; `tests/test_artifact_core.py` does not exist; the real guard is `tests/test_attention_contract.py::TrackedTreeScanCoverageTests` | AN ACCEPTANCE BAR NAMED A TEST CLASS THAT DOES NOT EXIST. E-05 required `ScanRootClassificationInvariantTests` to stay green. An executor would find nothing to run and would either invent a test or record the item satisfied by an empty search. The stale name survives only inside a source comment pointing at an absent test file, which is exactly the expiring-citation failure the plan's own convention bullet warns about; a test-class name is a symbol and must resolve. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the real class in E-03's expected outcome and V-03, with its live count (26 tests passing at review). Added an Under-scope note and extended the citation convention bullet to say a test-class name is a symbol that must exist. |
| PR-805 | LOW | IN-SCOPE | F. Honest documentation | Counted over the 17 live files: 9 carry the leading `aw-prompt` comment, 8 do not; the plan's E-01 says "8 carry" and F-5 says "9 of 17 files have no `aw-prompt` comment" | TWO COUNTS ARE INVERTED, in E-01's baseline table and in Findings row F-5. The conclusion they support (the directory is the only total status source) is unchanged and slightly strengthened, so nothing downstream breaks; but the figures appear in a justification a reviewer is meant to check, and arithmetic that does not reconcile undermines the rest of the measurement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in both places, with the inversion called out explicitly so the old figure is not restored, and with the note that the conclusion is unaffected. |
| PR-806 | LOW | IN-SCOPE | C. Architecture / E. Testing | `find_dangling_citations`' `scan_roots` parameter defaults to `SCAN_ROOTS` and `plans_index.check_drift` passes no override (confirmed in source); driven with both cite matchers, the widening adds 23 files to a 1592-file scan and yields 0 new danglers for plans and 0 for research; `attention.scan` applies `is_nonartifact_name` before `_record_for`, so the 6 READMEs never become items; both `index --check` commands already report findings at HEAD | A REAL RISK WAS LEFT UNMEASURED, AND ITS ACCEPTANCE BAR WAS WRONG. The plan correctly identified that widening `SCAN_ROOTS` feeds the dangling detectors, but left the blast radius unknown and asked for "dangling-citation counts unchanged" against a baseline it did not establish as already-dirty. Measured, the risk is essentially nil, and the correct bar is UNCHANGED-FROM-BASELINE rather than clean. The 6 extra README files were also unaddressed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 carries the measurement (23 files, zero new danglers) and keeps the stop condition for the unexpected case. E-01 states that both checks already report findings so the bar is unchanged-from-baseline, never clean, and names the default-parameter mechanism. E-05 records the README filter. V-03 requires a line-for-line comparison. Added F-10. |
| PR-807 | LOW | IN-SCOPE | G. Plan executability (live-artifact criteria) | Whole-view total was `True 1508` at authoring and `True 1540` at review; the prompt corpus counts are live populations | A LIVE-ARTIFACT COUNT WAS USED AS A STOP CONDITION. E-01 said "if any claim moved, STOP and report" while pinning a whole-repository item count that moves with every commit; it had already moved by 32 when I measured. The executor's first action would be to stop on an expected change, and the more likely response is to silently absorb the difference, which defeats the re-measurement the item exists for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now separates a STRUCTURAL change (index backend appeared, tree already tracked, mismatches already fixed) which IS a stop, from a changed COUNT which is recorded; every figure is labelled context to re-derive, with the 1508 -> 1540 movement given as the illustration. V-01 requires each number stated as measured now. |
| PR-808 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: three sentences (approve-first, commit path, "Move to `executed/`"); `- Cohesion rationale: not required`; 17 declared Scope-Paths | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS on a plan that changes a daily-read surface and amends TWO implemented specs. No statement of what a human is approving (three things here deserve a look: two prompts becoming visible `ready` work, two new rules that govern only future prompts, and OQ-01); no scope fence across seventeen paths, two of which are content files whose bodies must stay byte-identical; no stop conditions; and a transition instruction naming a directory move rather than the runner's ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph naming all three; a per-path scope fence stated as a DECLARATION (including "the two prompt files' `Status:` field ONLY, bodies byte-identical") with an explicitly-not-in-scope list mirroring Deferred, and the finalize-justifies-afterwards rule; the hard-MUST honesty rule naming three specific temptations; three genuine stop conditions; and the transition with conditional runner/executor ownership and no hand-rolled `git mv`. Filled in the cohesion rationale. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The authored order flips the tree to tracked before adding its scan root, which reddens a shipped guard. Reorder, or add a note telling the executor to expect the failure? | Reorder: scan root first, policy second. | (a) Keep the order and warn about the transient failure - rejected: a red guard across three items means the executor cannot attribute its own failures, and the nearest apparent fix is weakening the guard that exists to catch precisely this class of bug. (b) Combine the two edits into one item - rejected: they have distinct evidence (an inertness proof versus a coverage-guard proof) and combining them hides the ordering constraint that caused the problem. | Drove `_scan_root_covers_tree`: no current root covers `prompts`; `attention.scan` skips an untracked policy before reading the file, so the reverse order is observably inert | yes |
| D-2 | E-07's two id6 rules have no live subjects. Drop them, or keep them with fixture-only evidence? | Keep them, and require synthetic-fixture evidence while stating plainly that live output cannot evidence them. | (a) Drop both rules - rejected: they are the enforcement for prompts created after the cutover, which is the direction the repository is moving, and `ubac5n` already established the grammar they police. (b) Keep them and accept the live-silence evidence as written - rejected: that records a passing validator from an expected no-op, which is the fail-open shape. (c) Lower `PROMPT_ID6_CUTOVER_DATE` so they have live subjects - rejected outright: that mass-invalidates 17 grandfathered names and reverses a deliberate decision recorded in the constant's own comment. | `_prompt_requires_id6` False for all 17 (driven); `PROMPT_ID6_CUTOVER_DATE`'s comment on keeping the one conforming prompt's conformance incidental | yes |
| D-3 | The plan leaves the SCAN_ROOTS widening's dangling-citation blast radius unknown. Measure it at review, or leave it to execution? | Measure it now and record the result, keeping the stop condition for the unexpected case. | (a) Leave it to execution as authored - rejected: the acceptance bar was "counts unchanged" against a baseline never established, and both checks are already dirty at HEAD, so the executor could read a pre-existing finding as one it caused. (b) Declare it safe and drop the stop condition - rejected: my measurement is of today's corpus, and a new prompt citing a retired id is exactly the case the condition should still catch. | Driven with both cite matchers: 23 files added to a 1592-file scan, 0 new danglers for plans and research; `find_dangling_citations` defaults `scan_roots` to the module constant | yes |
| D-4 | OQ-01 (`reusable` -> `parked` versus plans-parity `ready`) is unresolved and uncarried. Resolve it, or leave it open? | Leave the SUBSTANCE open to the maintainer; decline a carrier with a reason and add the consequence the plan omitted. | (a) Resolve it myself to `parked` - rejected: it is a contract choice about a user-visible board and the plan's own counter-evidence (plans map `reusable` to `READY`) is real, so the two trees would disagree on the same word; that is the maintainer's call. (b) File a backlog carrier - rejected: the answer is one dict entry inside this plan's own diff and leaves no work behind it, so a carrier would track nothing. | Verified `_PLANS_MAP["reusable"] == READY`; measured `reusable/` holds zero `.prompt.md` files; `parked` items are auto-hidden from the default board | yes |
