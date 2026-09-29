# Review findings: plan y43g6q

- Subject-Id: y43g6q
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bf3cf2d7` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified. `agent_workflows/check_engine.py` was NEVER written: the mutation was
staged by rebinding `_identity_finding` in memory from a pytest plugin and a script under the
gitignored `.aw/state/`, exactly as the plan's own E-02 mandates. `tests/test_find_filters.py` was
temporarily renamed to verify F-4 and restored byte-for-byte (`git status --porcelain` and
`git diff --stat` both empty afterwards).

THE PLAN'S DIAGNOSIS IS CORRECT AND WAS CONFIRMED INDEPENDENTLY. F-1 reproduces: with the
`elif modern:` arm made unreachable in memory, a BARE `python3 -m pytest` reported
`3246 passed, 2 skipped`, byte-identical to the clean baseline, so the `drift` branch really is
unguarded on this tree. The mutation is not a silent no-op: on a synthetic fixture the unmutated
rule emits `[drift] declared \`Set: topic\` is absent from an otherwise MODERN id6-clustered
filename` and the mutated one emits `[legacy] ...`. F-2 reproduces exactly (`46fd3754` added the
module, `19313eed` "trim test suite from 9,136 to under 2,000 tests" deleted it). F-4 reproduces
(`11 passed` after the four renames). F-5, F-6, F-7 and F-8 all reproduce, F-8 down to the three
failing node ids.

WHAT REVIEW FOUND IS THAT THE PLAN'S REMEDY COULD NOT HAVE WORKED, AND WOULD HAVE REPORTED SUCCESS.
This is a single root cause with two measured halves, and it is the reason this review is not a
rubber stamp on an otherwise careful plan.

**THE RULE IS NOT IN THE COLLISIONS PASS, SO THE CHOSEN TABLE CANNOT ASSERT THE BUCKET (PR-801,
BLOCKER).** E-01 placed the restored coverage in `CollisionTests.COLLISIONS`. That table's runner
builds its needle haystack from `drift = ce.check_collisions(root)` and matches
`required_detail_substrings`/`forbidden_substrings` against THAT, while comparing the expected RULE
set against `ce.check_types(root, ["all"])`. Measured on the exact fixture E-01 prescribes:
`check_collisions` returns ZERO findings and `check_types(["all"])` returns the one
`check.identity-absent-from-name`, because the rule comes from `check_name_identity` on the types
sweep. So `'[drift]'` can never appear in that haystack and a row there can assert only the rule id.

**AND A RULE-ID-ONLY ASSERTION SURVIVES E-02's OWN MUTANT, SO E-01 AND E-02 WERE JOINTLY
UNSATISFIABLE (PR-802, BLOCKER).** Under the mutation the rule STILL fires with the SAME id; only
the bucket prefix flips. Review ran both candidate shapes: the detail-asserting test passes clean and
FAILS mutated; the rule-id-only shape passes BOTH (`unmutated: PASS (rules=['check.identity-absent-from-name'])`
/ `mutated: PASS (rules=['check.identity-absent-from-name'])`). The plan would therefore have added a
decorative test, found E-02's mutant unable to kill it, and either recorded a false pass or stalled
with no guidance. Both findings share one fix, applied in place: E-01 now adds a small focused test
that drives `check_name_identity` directly and asserts the `[drift]` marker, following
`SetidLengthTests`' established in-module precedent for a non-collisions rule. This is emphatically
NOT the deleted 585-line module, so OQ-01's valid half (do not walk back into the trim policy)
survives.

**OQ-01's RESOLUTION WAS FALSIFIED ON MECHANISM (PR-803, HIGH).** It concluded "IN THE EXISTING
TABLE" and called the alternative "a style call with no correctness consequence". Per PR-801/PR-802
the placement was a correctness question, and the answer was the third option the question never
offered. Re-resolved, with the reasoning and the measurement recorded, and its owner changed from
`none` to the reviewer since a reviewer's own choice now backs it.

**E-02's MUTATION MECHANISM WAS UNDERSPECIFIED AND ITS KILL CRITERION ABSENT (PR-804, MEDIUM).**
E-02 said to prefer monkeypatching but named no working route, and gave no criterion for WHAT the
failure must say. Since the mutant leaves the rule id intact, a failure reading "expected rule set X,
got Y" would mean the mutation changed something unintended. E-02 now carries the exact in-memory
rebind review used, and V-02 requires the failure to name the missing `[drift]` marker, plus an
explicit instruction not to record V-02 verified if the mutant fails to kill the test.

**TWO COUNTS IN THE PLAN HAVE ALREADY DRIFTED (PR-805, LOW).** F-8's bare baseline of `3158 passed`
now measures `3246 passed, 2 skipped`, and F-7's `aw check all` "findings: 2" now reports 9. Neither
conclusion moves (the three named failures are still exactly those three; no
`check.identity-absent-from-name` appears on the live tree), and the plan's own contract already
forbids asserting against its counts. Recorded with the fresh figures so V-04 compares against a
re-derived baseline rather than a stale digit.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-02 survives review unchanged: its test (does the module resolve a Set?) is sound, its
per-module measurement of zero `check_name_identity`/`check_collisions`/`check_types` references is
consistent with what review observed, and its stated honest limit is the right one. A new Deferred
entry records that the other three buckets gain no coverage here, since the plan's own framing could
otherwise be read as closing the whole rule.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | blocker | IN-SCOPE | E. Testing and verification | `tests/test_check_engine.py` `test_one_pass_reports_exactly_the_collisions_present` (`haystack` built from `ce.check_collisions(root)`); review probe | `check.identity-absent-from-name` is produced by `check_name_identity` on the TYPES sweep, not by `check_collisions`. Measured on E-01's fixture: `check_collisions` 0 findings, `check_types(["all"])` 1 finding. The table's detail columns see only collisions output, so a row there cannot assert the `[drift]` bucket. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 rewritten to add a focused test driving `check_name_identity` directly and asserting `[drift]`; new F-9; V-01(c) fails the item if the coverage is placed in `COLLISIONS`. |
| PR-802 | blocker | IN-SCOPE | D. Anti-regression and domain invariants | review probe running both candidate shapes under the mutation | Under E-02's mutation the rule still reports the SAME id (only the bucket prefix changes), so the rule-id-only row E-01 could have written passes mutated AND clean. E-01 and E-02 were jointly unsatisfiable: the plan would have closed a coverage hole with a test proving nothing. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | Same fix as PR-801 (assert the bucket marker); new F-10 records both shapes measured; the approval paragraph now states what review changed and why. |
| PR-803 | high | IN-SCOPE | G. Plan executability | plan OQ-01; F-9/F-10 measurements | OQ-01 resolved "in the existing table" and declared the alternative a consequence-free style call. It was a correctness question and the resolution was wrong on mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | OQ-01 re-resolved to the third option (a focused test in the same module), with the falsification and measurement recorded; `Owner` changed from `none` to the reviewer. |
| PR-804 | medium | IN-SCOPE | E. Testing and verification | plan E-02; review's working rebind of `_identity_finding` | E-02 named no working in-memory mutation route and gave no criterion for what the failure must say, so a mutation that changed something unintended would read as a successful kill. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-02 now carries the exact rebind used; V-02(c) requires the failure to name the missing `[drift]` marker and V-02(d) forbids recording it verified if the mutant does not kill the test. |
| PR-805 | low | IN-SCOPE | Evidence freshness | bare run `3246 passed, 2 skipped` at `bf3cf2d7`; `aw check all --agent` findings 9 | F-8's `3158 passed` and F-7's "findings: 2" have both drifted. No conclusion moves, and the plan already forbids asserting against its counts, but a reader could mistake them for current. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-8 updated with the re-measured total and the three failing node ids; V-04 now names both figures as stale context and requires a re-derived baseline. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The COLLISIONS table cannot express the `[drift]` assertion. Move the coverage to a focused test in the same module, recreate the deleted dedicated module, or extend the table runner to also match needles against the types sweep? | A small focused test in the surviving `tests/test_check_engine.py`, driving `check_name_identity` directly. | (a) Recreate `tests/test_name_identity_report.py`: rejected on OQ-01's surviving reasoning, since the trim commits `19313eed`/`80db6750` removed it deliberately and a few assertions are not a 585-line module. (b) Extend the table runner's haystack to include `check_types` output: rejected as materially wider scope than this plan claims, since it changes the assertion semantics of every existing row in a shared table another pending plan (`tl2b2r`) declares. | `test_one_pass_reports_exactly_the_collisions_present` building `haystack` from `ce.check_collisions(root)`; probe measuring `check_collisions` 0 vs `check_types(["all"])` 1 on the fixture; `SetidLengthTests` precedent of driving its own rule function directly. | yes |
| D-2 | E-02's mutant does not kill a rule-id-only test. Raise this as a blocking question for the maintainer, or fix E-01's assertion in place? | Fix E-01 in place to assert the bucket marker, and add the kill criterion to V-02. | (a) Raise as `- Blocking: yes`: rejected because the repository answers it decisively (review ran both shapes and measured which the mutant kills), so it is resolvable from evidence rather than a maintainer judgement. (b) Weaken E-02 to accept the rule-id-only row: rejected outright, as that is precisely the decorative-test outcome the plan's own validation section forbids. | Probe: detail-asserting test `unmutated: PASS` / `mutated: FAIL -> no [drift] bucket`; rule-id-only `unmutated: PASS` / `mutated: PASS`. | yes |
| D-3 | F-1's claim required re-verification, but the mutation target is a shared-checkout file outside Scope-Paths. Verify by editing it briefly, or in memory? | In memory, via a pytest plugin rebinding `_identity_finding` to force `modern=False`. | (a) Edit-then-revert the tracked module: rejected on the plan's own reasoning and the shared-checkout rule, since a failed revert leaves the repository's rule mutated with the suite green. (b) Take F-1 on trust: rejected because it is the plan's central justification and a green mutated suite is cheap to confirm. | Two bare suite runs (clean and plugin-mutated) both `3246 passed, 2 skipped`; `git status --porcelain agent_workflows/check_engine.py` empty throughout. | yes |
