# Review: Compare release gates by the release they resolve to, not by spelling

- Subject-Id: ooydp3
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `79726960`. The plan cites `0c2e7970`, an ancestor; both were checked and
the measurements agree. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` afterwards.

THE PLAN IS CORRECT, WELL SCOPED, AND ITS FIX IS THE RIGHT SHAPE. I reproduced F-1 and F-2 in a fresh
scratch repo WITH A CONTROL, which is what makes them conclusive rather than suggestive: with the item
spelling `next` and the carrier spelling `f33nrj`, `evaluate_blocking_close(..., 'done')` returns
`legitimate=False severity=error` with the "would silently drop that release gate" reason, and
`check_release_gate_consistency` emits one `check.from-backlog-gate-mismatch`; re-spelling the item to
`f33nrj` and changing nothing else makes the verdict `legitimate=True` with reason "gate 'f33nrj'
handed off to a From-Backlog plan or spec" and the Drift list empty. Both sites are raw string
comparisons at the two places the plan names, and `releases.resolve_release` exists and behaves as
described. The plan's completeness claim also survived checking, which I did rather than trusting the
grep it cited: gate-value comparisons exist only in `check_engine` (the two named sites) and in
`attention.py`, and `attention.py` already resolves each value through `_resolve_release_version`
before comparing, so it genuinely does not share the defect.

THE MOST IMPORTANT THING I ADDED IS PR-A01: THE DEFECT IS ALREADY LIVE IN THIS TREE. The plan's F-3
says the live tree is quiet because the two cited carriers have executed, which is true, and I verified
the mechanism precisely. But "quiet" is not "absent". Driving the real tree, the ONLY two raw-unequal
(item, carrier) gate pairs that exist are items `hdhzr2` and `x15f0q`, each spelling `next` against a
carrier spelling `f33nrj`, and both resolve to the SAME release file. Those two items are already
`done`, and `evaluate_blocking_close(..., 'done')` returns `legitimate=False` for BOTH of them RIGHT
NOW. The reason nothing reports it is a conjunction the plan never stated: the consistency rule skips
retired carriers AND `check.blocking-item-closed-without-gate` is commit-scoped, so the refusal
surfaces only when such a close is re-staged or the opt-in pre-commit hook runs. That makes this a
latent inconsistency in committed history rather than a scratch-repo curiosity, and it is the fact most
relevant to whether the maintainer prioritizes the fix. It also gives the plan a live positive test it
did not have (E-04 now asserts both items flip to `legitimate=True`).

PR-A02 IS THE FINDING AN EXECUTOR WOULD HAVE TRIPPED OVER IN THE FIRST FIVE MINUTES. E-03 required
asserting "legitimate with basis `HANDOFF`". `CloseVerdict` is a NamedTuple of
`(legitimate, severity, reason, fixes, path)` and the legitimacy route lives in `path`; there is no
`basis`. I did not deduce this, I hit the `AttributeError` myself while reproducing F-1, twice, once
for `basis` and once for `summary`. The likely executor response to an `AttributeError` in a validation
item is to weaken the assertion to bare `legitimate`, which silently drops the half that proves the
HANDOFF branch specifically was repaired rather than some other branch accidentally returning True.

PR-A03 records a side effect the plan neither claims nor bounds, and it broadens the change:
`resolve_release` accepts a VERSION string as well as `next` and an id6, so `_same_release('next',
'2.0.0')` is True. That is correct and desirable, but it means the helper unifies three spellings while
the plan's title and Goal speak of two, and an executor told to test "the two spellings" would leave
the version path untested. I reframed it as in scope rather than as a surprise.

PR-A04 is about evidence that cannot support its claim. E-04 runs `check release-gates` on the real
tree and expects it to conform. Measured: it ALREADY conforms with 0 findings before any change, for
the reasons F-3/PR-A01 establish. So a clean run afterwards is a no-regression check and nothing more,
and presenting it as proof the fix works would be the same category of error this sweep has now seen in
three plans. V-04 says so and supplies the live evidence that does discriminate.

ON THE CACHING INSTRUCTION in E-02, which I checked because an unmeasured performance directive is
usually either wrong or noise: it is neither here, but it needed honest framing. Measured, the tree has
exactly ONE release record, one `resolve_release` call costs about 0.2ms, and the worst uncached case
across all 259 carrier rows is about 0.05s, so caching buys almost nothing today. It is still right to
do, because `resolve_release` reads every release file on every call and this module has already
learned that lesson twice: `_from_backlog_carrier_index`'s own docstring records a measured 11.13s
versus 207ms (54x) regression from a per-item re-walk and notes that `release_gate_warnings` had to
learn it first. E-02 now says "prudence, not a measured fix" and cites that history, so a later reader
does not mistake it for a hot path.

I ALSO ESTABLISHED A REGRESSION BASELINE the plan did not offer, because this change makes a gate more
permissive and that is the direction that can quietly disable a check. `tests/test_check_engine_release_gate.py`
has 13 tests and they pass (`13 passed in 0.70s`). I then re-ran the whole file with the fix's
suppression applied and got `13 passed` again, including
`test_rule_from_backlog_gate_mismatch_reachable`, which I inspected specifically because it is the test
most likely to break: it uses TWO `planned` releases, `rel001` and `rel002`, and I confirmed those
resolve to DIFFERENT paths so the mismatch must still fire. A pleasing detail falls out of that same
fixture: with two `planned` releases, `resolve_release(repo,'next')` returns None by design, which is
exactly the unresolvable case OQ-01 rules on, and `check.blocks-release-dangling` does fire on it. No
item tested that behavior, so E-03 gained case (d) to pin the string fallback rather than assume it.

OQ-01's resolution is correct and I re-verified it rather than accepting it: falling back to string
equality when either side is unresolvable never treats two different releases as one, and the
ambiguity it declines to report is reported by `check.blocks-release-dangling` at error. I also added
the `None` guard the helper needs but the item did not mention: `_from_backlog_carrier_index`
deliberately keeps a missing `- Blocks-Release:` line as `None`, distinct from the empty string, so
`None` must never resolve or compare equal to a real gate.

Backlog item `4le6yz` carries `- Blocks-Release: next`; the plan correctly inherits it, so the gate is
preserved by the handoff, and the gate section now says so, including the closing observation that this
plan's own eventual item close will be evaluated by the predicate it repairs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | MEDIUM | UNDER-SCOPE | A. Correctness / D. Anti-regression | Driven on the real tree: the only two raw-unequal (item, carrier) gate pairs are items `hdhzr2` and `x15f0q`, each `next` vs carrier `f33nrj`, both `retired=True` and both resolving to the SAME release file; `evaluate_blocking_close(..., 'done')` -> `legitimate=False path=None` for BOTH today; `check_release_gates` -> no rules fire | THE DEFECT IS ALREADY LATENT IN COMMITTED HISTORY, NOT ONLY IN A SCRATCH REPO, and the plan presented it as hypothetical. F-3 correctly explains why the tree is QUIET but stops there, so a reader concludes nothing is actually wrong today. Two real `done` items fail the close predicate right now; the refusal is invisible only because the consistency rule skips retired carriers AND the closed-without-gate rule is commit-scoped, a conjunction the plan never states. This is both the priority argument and a live positive test the plan lacked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern rewritten to state the live latency with both item ids and the two-part reason it is invisible; F-4 added with the driven measurement; E-04 and V-04 now require those two items to flip to `legitimate=True` with `path="HANDOFF"`; the gate carries it as the priority argument; Deferred records that no record edit is needed because the fix resolves both. |
| PR-A02 | MEDIUM | IN-SCOPE | E. Testing (a validation naming a nonexistent field) | `CloseVerdict._fields` -> `('legitimate', 'severity', 'reason', 'fixes', 'path')`; `v.basis` -> `AttributeError`, hit twice at review while reproducing F-1 | E-03 ASSERTS ON A FIELD THAT DOES NOT EXIST. It requires "legitimate with basis `HANDOFF`"; the legitimacy route is `path`, and there is no `basis` attribute. The failure is immediate rather than subtle, which is the problem: the natural recovery from an `AttributeError` inside a validation item is to weaken the assertion to bare `legitimate`, dropping the half that proves the HANDOFF branch specifically was fixed rather than another branch incidentally returning True. | C:Low; U:Low; S:Low; F:Medium (a weakened assertion stops pinning which branch was repaired); Overall:Low | FIXED | E-03 now names `path` with the full `CloseVerdict` shape and records that the reviewer hit the `AttributeError`; V-04 likewise asserts `path="HANDOFF"`; added F-5 and a conventions bullet stating the NamedTuple's fields so no later reader reinvents `basis`. |
| PR-A03 | LOW | IN-SCOPE | A. Correctness / F. KISS (an unstated broadening) | Driven: `_same_release('next','2.0.0')` -> True; `resolve_release` matches `_VERSION_RE` after its id6 branch | THE HELPER UNIFIES THREE SPELLINGS WHILE THE PLAN DESCRIBES TWO. Because `resolve_release` accepts a version string, the change also makes `next` and `2.0.0` one gate. That is correct and desirable, but unstated it means an executor testing "the two spellings" leaves the version path unexercised, and a reviewer of the resulting diff cannot tell whether the breadth was intended. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states the three-spelling behavior explicitly, flags it as a deliberate side effect rather than scope creep, and instructs that a version-spelling test is IN scope; V-01 requires the version case among the five pasted answers; added F-6 and a conventions bullet recording that `resolve_release` accepts three spellings. |
| PR-A04 | MEDIUM | IN-SCOPE | E. Testing (evidence that cannot support its claim) | `aw check release-gates --agent` on the real tree BEFORE any change -> `outcome:conforms, findings:0`; the reason is F-3/F-4's retired-carrier skip | E-04'S LIVE EVIDENCE PROVES NOTHING ABOUT THE FIX AND READS AS IF IT DOES. `check release-gates` already conforms with zero findings, so "release-gates still conforms" afterwards is a no-regression statement, not a demonstration. An executor could truthfully paste a clean line and leave the actual behavior change unverified on the live tree, which is exactly where PR-A01 shows it is observable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now state plainly that the clean run is a no-regression check and supply the discriminating live evidence instead (the two items' verdicts before and after); the gate's honesty rule names this as one of three easily faked claims. |
| PR-A05 | LOW | IN-SCOPE | A. Correctness (an unhandled input the helper will receive) | `_from_backlog_carrier_index`'s docstring: the carrier gate "is None when the artifact carries no `- Blocks-Release:` line at all, and is kept DISTINCT from the empty string so a caller can tell 'no gate field' from a malformed one"; the mismatch site iterates exactly those rows | E-01 NEVER SAYS WHAT HAPPENS WHEN A CARRIER GATE IS `None`, AND THE CALL SITE WILL PASS IT. The carrier index yields `None` for an artifact with no gate line, deliberately distinguished from `""`. A helper written as "resolve both and compare paths" must not let `None` resolve or compare equal to a real gate, or an ungated carrier could read as preserving a gate it does not carry, which inverts the whole point of the check. | C:Low; U:Low; S:Low; F:Medium (an ungated carrier reading as a preserved gate); Overall:Low | FIXED | E-01 now requires an explicit `None` guard and cites the index's docstring for why `None` is distinct from `""`; V-01 requires a pasted `None`-versus-real-gate case returning False. |
| PR-A06 | LOW | UNDER-SCOPE | G. Plan executability (execution contract, baselines, framing) | Plan gate as authored: two sentences, no fence, no approval paragraph, no stop conditions, unconditional finalize; V-01's evidence was "paste the helper's diff"; `tests/test_check_engine_release_gate.py` baseline `13 passed in 0.70s`, and `13 passed` again with the fix's suppression applied; the measured caching numbers (1 release record, 0.2ms per resolve, 0.05s worst case) versus the module's recorded 54x history | THE GATE CARRIED ONLY THE COMMIT RULE, THE VALIDATION HAD NO BASELINES, AND ONE INSTRUCTION WAS UNJUSTIFIED. No scope fence, no statement of what approval means for a change that makes a gate more permissive, no stop conditions, unconditional finalize. V-01 asking only for a diff cannot show a predicate's behavior. No item recorded the existing 13-test baseline, so a regression would read as expected churn. And E-02's "resolve at most once per call" was asserted with no measurement, which is how a directive becomes cargo cult. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: approval paragraph (permissive direction, the three spellings, the third inheriting surface), the live-inconsistency priority argument, a per-path scope fence naming `releases.py`/`attention.py`/the commit-scoped rule as expected-unmodified and stating no record is edited, the honesty rule naming three easily faked claims, two genuine stop conditions, conditional runner/executor finalize ownership, and the `4le6yz` close with its inherited gate. V-01 now demands five observed answers; V-03 adds the 13 -> 17 count and the (c)/(d)-in-both-states split; E-02 reframes caching as prudence with the measured numbers and the module's own 54x precedent. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-3 says the live tree is quiet. Accept that as "nothing is wrong today", or determine whether the defect is live? | Drive the real tree and record that it IS live: two `done` items fail the close predicate now. | (a) Accept F-3 as written - rejected: "quiet" is not "absent", and the distinction decides both priority and whether a live positive test exists. (b) Report it as a separate defect - rejected: it is the SAME defect this plan fixes, and the fix resolves both items with no record edit, so a second artifact would double-count one bug. | the two raw-unequal pairs (`hdhzr2`, `x15f0q`), both `same_release=True`; `evaluate_blocking_close` -> `legitimate=False` for both; the retired-carrier skip plus the commit-scoped rule | yes |
| D-2 | This change makes a gate more permissive and the plan offered no regression argument. Accept it, or establish a baseline? | Establish one: run the existing 13 tests, then re-run them with the fix's suppression applied. | (a) Accept the plan's assertion that a genuinely different release still mismatches - rejected: that is the entire risk surface of a permissive change to a release gate, and it was asserted rather than shown. (b) Reason about the diff - rejected: the most fragile existing test uses TWO `planned` releases, and only running it reveals that `resolve_release('next')` returns None there, which is the behavior OQ-01 turns on. | `13 passed in 0.70s` baseline; `13 passed` with the suppression applied; `rel001` and `rel002` resolving to different paths; `resolve_release('next')` -> None with two planned | yes |
| D-3 | E-02 instructs caching with no measurement. Drop it, keep it, or justify it? | Keep it, reframed as prudence, with both the measured numbers and the module's own precedent. | (a) Drop it - rejected: `resolve_release` reads every release file per call, and this module has twice shipped exactly this defect, so removing the guardrail invites a third. (b) Keep it as written - rejected: an unmeasured performance directive reads as a hot-path claim, and the measurement (1 release record, 0.05s worst case) does not support that, so a later reader would either over-engineer or dismiss it. | 1 release record; ~0.2ms per resolve; ~0.05s across 259 carrier rows; `_from_backlog_carrier_index`'s recorded 11.13s vs 207ms | yes |
| D-4 | E-03 asserts on `CloseVerdict.basis`, which does not exist. Correct it silently, or record it? | Record it as a finding and correct both the item and the validation to `path`. | (a) Fix it silently - rejected: the failure mode matters, because the natural recovery from an `AttributeError` in a validation item is to weaken the assertion to bare `legitimate`, which stops pinning which legitimacy branch was repaired. (b) Assert only `legitimate` - rejected for the same reason: `path="HANDOFF"` is what proves the HANDOFF branch was fixed rather than another branch incidentally returning True. | `CloseVerdict._fields`; the `AttributeError` hit twice at review; the three legitimacy routes in the docstring | yes |
