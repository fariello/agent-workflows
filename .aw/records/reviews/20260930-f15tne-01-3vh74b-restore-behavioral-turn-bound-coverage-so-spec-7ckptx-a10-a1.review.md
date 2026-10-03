# Review findings: plan 3vh74b

- Subject-Id: 3vh74b
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (MEDIUM, fixed), PR-803 (MEDIUM, fixed), PR-804 (LOW, fixed), PR-805 (LOW, fixed), PR-806 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f82d7ea53`. The plan file was committed and unmodified
before editing (`git status --short` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) with ZERO diagnostics and ZERO
advisories across all seven E-items. This plan's own first `- Kind:` bullet reads `child`, so the
`IPD-S407` orchestrator child-row check does not apply.

All probe work was done under the gitignored `tmp/` and removed afterwards. NO production file was
modified and no mutation was left in the tree; every mutation below was applied with
`mock.patch.object` in a throwaway process, and `git status --short` is empty.

THIS IS AN EXCEPTIONALLY WELL MEASURED PLAN AND ITS DESIGN SURVIVES INTACT. I re-executed every
route rather than re-reading the findings, and all of the following reproduce (recorded as F13):

```
IMPORT ORIGIN: <this worktree>/agent_workflows/__init__.py
max   rc=-2 elapsed=0.481 fired='max-turn-timeout'  record disposition="failed-safely" timeout_seconds=0.3
      EVENT event='turn-bound-expired' id6='f15tne'
perm  rc=-2 elapsed=0.415 fired='permission-timeout' record bound="permission-timeout"
      EVENT event='turn-bound-expired' id6='f15tne'
clean shutdown: children_reaped (R1): ok - reaped [...]; ledger_coherent (R3): NOT SATISFIED

perm disarmed by progress (expect empty): {}
max-turn survives repeated note_progress: {'bound': 'max-turn-timeout'} fired: max-turn-timeout
dead child reaped again (expect []): []
reap despite unwritable run dir: ['r']
both-zero enabled: False   both-zero reap list: []

PERMISSION_TIMEOUT 0.0 | MAX_TURN_TIMEOUT 14400.0 (== 4*60*60: True) | HOST_CEILING_OFFSET 300.0
parse 240m -> 14400.0 | parse banana -> None | bound(None) -> 14400.0 | bound(14400) -> 14100.0
gap 300.0 == offset: True | has PERMISSION_DEADLINE: False | has MAX_TURN_DEADLINE: False
```

- F1 REPRODUCES EXACTLY, all twelve symbols. `19313eed` `--stat` shows `tests/test_turn_bounds.py |
  2417 -----` and `tests/test_lane_permission_posture.py | 529 ---`, both absent from disk, and the
  only two `bound_expiry_reaper` files are the two the plan names.
- F2, F3, F4, F8 REPRODUCE verbatim, including the `clean shutdown:` stderr report E-01 warns about
  and both prompt renderings ("about 4 hours" / "about 3.9 hours").
- F7 REPRODUCES AND IS LIVE IN THIS VERY TURN: `OPENCODE_CONFIG_CONTENT` is ambient in my own
  environment, and `conftest.py` pops `AW_EXECUTION_ROLE` while deliberately NOT popping this one, so
  the historical flake is exactly as described and E-04's hermeticity requirement is justified.
- F10's SUBSTANTIVE claim REPRODUCES: `rg -n '\.note_permission_request\(' agent_workflows/ tools/`
  returns NOTHING, while both drivers call `turn_bounds.note_progress()`
  (`oc_runipd.py:3127`, `agy_runipd.py:2617`). The permission bound has no production trigger.
- The spec text is as quoted: `7ckptx` is `- Status: approved` with `- Blocks-Release: next`, and
  A10/A10b/A10c/A10d read as the plan says. The deferred carrier `4xtpvg` EXISTS and is `open`, so
  the Deferred section's carrier claim is real rather than aspirational.
- V-07's MUTATION MATRIX IS ACHIEVABLE, verified cell by cell (recorded as F15), which matters because
  the plan calls it the decisive evidence: (b) `_expired -> None` leaves the child ALIVE
  (`rc='TIMEOUT(survived)' fired=None record=None`); (c) `driver_bound_for_host -> MAX_TURN_TIMEOUT`
  gives `14400.0` so the strict `<` is False; (d) `note_progress -> no-op` produces the REQUIRED SPLIT,
  half one firing `permission-timeout` (fails) while half two still fires `max-turn-timeout` (passes).

THE ONE SUBSTANTIVE DEFECT IS A TIMING CLAIM THAT WOULD HAVE MADE THE NEW FILE RED ON ITS FIRST RUN
(PR-801). E-01 instructs the executor to assert that "the wait completes inside the bound's own
window". That is false. `TurnBoundWatch.__init__` carries `check_interval: float = 1.0` and the thread
loop is `while not self._stop.wait(self.check_interval)`, so an expired bound is noticed AT A POLL
TICK, not when it elapses; against a 0.3s bound the first tick is at 1.0s and elapsed is
POLL-DOMINATED. Measured: `check_interval` default -> `rc=-2 elapsed=0.475`, `check_interval=0.05` ->
`rc=-2 elapsed=0.382`, both firing correctly. The word `check_interval` appeared ZERO times in the plan
as authored, so the number that governs the whole timing envelope of its slowest tests was invisible.
The design is fine and both bounds do fire; only the assertion shape was wrong. Fixed in E-01 and V-01
with the correct shape (lower bound at the bound, generous ceiling above `bound + check_interval`) and
a requirement to state the interval used, plus a new F12 carrying the measurement.

TWO CITATION DEFECTS, both in findings the plan leans on (PR-802, PR-803). F10 claims
`git log -S'note_permission_request('` "returns exactly one commit". It returns FIVE at review HEAD,
because `-S` counts occurrence changes in ANY tracked file and this string moves with the deleted TEST
file and with plan prose. The substantive zero-caller claim survives on the call-site search, but the
citation does not. F9 claims "both hosts' parsers register 72 option strings"; that figure reproduces
under no accessor I tried (recursive subparser walk gives 225 for `oc` and 197 for `agy`; the hosts'
own module parsers give 2 each). The ABSENCE of all four flag spellings does reproduce, which is what
A10e actually needs, so the conclusion stands and the count is unreliable and must not be asserted.

The remaining two findings are a drifted baseline (PR-804: `3387 passed` authored,
`3559 passed` measured, both fully green, a drift of 172) and a wrong call signature in V-05's required
evidence (PR-805: `build_turn_budget_notice` takes a STATE DICT, not a ceiling float; a bare float
raises `AttributeError`).

ONE THING I CHECKED AND DID NOT FLAG, recorded because a later reviewer may wonder. A10's own text
says the reaper attribution is "checked structurally, not by text grep, since a test file contains the
symbols". That phrase could be read as licensing the structural pins P16 forbids. It does not conflict
here: the plan discharges attribution by exercising the DEFAULT reaper with no `reap=` override, so the
kill is attributable by construction rather than by inspecting code, which satisfies A10's intent
(distinguish a real reaper from a double) without reading source. F5 and F6's honest refusals to
restore the docstring and prose pins are consistent with that and with P16.

OPEN QUESTIONS. Both are `Blocking: no` and `Status: resolved`, each resolved at authoring with its
basis cited, and I re-checked both. OQ-01 (keep the permission-policy contrast only if scrubbed, prefer
omitting) holds and is strengthened by F7 reproducing in this turn. OQ-02 (assert max-turn-only
coverage behaviorally rather than as a caller count) holds and is the right call: a caller-count pin
would be P16-prohibited AND would turn red the day someone correctly wires the detector. No new
question was created; all five findings were resolvable from repository evidence and are recorded as
decisions below.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | E. Testing and verification | plan E-01, V-01; `agent_workflows/lane_containment.py` symbol `TurnBoundWatch.__init__` (`check_interval: float = 1.0`) and `TurnBoundWatch._run` (`while not self._stop.wait(self.check_interval)`) | E-01 requires asserting that the child's wait "completes inside the bound's own window", which is FALSE and would make both real-child tests red at their first run. The watch notices expiry only at a poll tick, so against a 0.3s bound the first tick is at 1.0s and elapsed is poll-dominated: measured `elapsed=0.475` at the default interval and `0.382` at `check_interval=0.05`, both firing correctly. `check_interval` appeared ZERO times in the plan, so the number governing the timing envelope of its slowest tests was invisible to the executor, and a tight upper bound is the likeliest source of flake under `-n auto` | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now forbids the within-the-bound assertion, states the correct shape (lower bound at the bound, ceiling above `bound + check_interval`) and requires the interval used to be stated; V-01 rejects the tighter claim and requires the interval pasted; new F12 carries both measurements |
| PR-802 | MEDIUM | IN-SCOPE | F. Honest documentation | plan F-10; `git log -S'note_permission_request('` at review HEAD | F-10 states the method "has NEVER had a caller" on the evidence that `git log -S` "returns exactly one commit, `8a491d4c`". It returns FIVE (`e03c4ee4d`, `19313eed7`, `ba4f205b2`, `8a491d4c1`, `bfa81215c`), because `-S` counts occurrence changes in any tracked file and the string moves with the deleted TEST file and with plan prose. The substantive zero-caller claim is CORRECT (re-verified by call-site search) but its stated evidence is not, and F-10 is the finding that justifies the deferred carrier | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected: the `-S` figure is named wrong with the five commits listed and the reason, the substantive claim is re-affirmed on the call-site search, and the durable evidence is identified as the search rather than a `-S` count |
| PR-803 | MEDIUM | IN-SCOPE | F. Honest documentation | plan F-9; `cli._build_parser()` subparser walk for the `oc` and `agy` nouns | F-9 asserts "both hosts' parsers register 72 option strings". That figure reproduces under no accessor tried (recursive walk: 225 for `oc`, 197 for `agy`; the hosts' own module parsers: 2 each). The ABSENCE of all four bound-flag spellings does reproduce and is what A10e needs. An unreliable census figure in a finding about a negative-direction criterion is exactly the number a later reader would turn into a brittle assertion | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 rewritten to assert the verified ABSENCE of all four spellings, to name the authored count as non-reproducing with the figures review did measure, and to forbid re-citing or asserting the count |
| PR-804 | LOW | IN-SCOPE | E. Testing and verification | plan F-11, Required tests item 1; bare suite at HEAD `f82d7ea53` | F-11 records `3387 passed, 2 skipped` and Required tests item 1 cites it as "authoring baseline". Review measures `3559 passed, 2 skipped, 3 warnings in 195.65s`, a drift of 172 collected tests and one more deselected, both runs fully green. The plan already says to gate on "no NEW failures", so the intent is right, but citing a single spent total invites reconciliation against it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-11 now carries BOTH baselines with their HEADs and the drift stated; Required tests item 1 requires re-deriving the before-run and comparing by NODE ID, naming neither total as a bar |
| PR-805 | LOW | IN-SCOPE | E. Testing and verification | plan E-05, V-05; `runner_shared.build_turn_budget_notice` signature `(state: dict[str, Any]) -> str` | E-05 and V-05 require pasting "a `build_turn_budget_notice` rendering for one nonzero ceiling" without naming the call shape. The function takes a STATE DICT and reads `state["options"]["turn_ceiling"]`; a bare float raises `AttributeError: 'float' object has no attribute 'get'`, a wasted cycle the plan can prevent. Review also measured that with both bounds disabled it returns the EMPTY string, which bounds what E-05 may claim | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and V-05 now give the exact call (`build_turn_budget_notice({'options': {'turn_ceiling': 14100.0}})`) and note that a pasted `AttributeError` does not satisfy the item; new F14 records the signature, both renderings, and the empty-string case |
| PR-806 | LOW | UNDER-SCOPE | G. Plan executability (traceability) | `aw check` rule `check.plan-spec-link-missing` naming this plan; plan front matter (no `- From-Spec:`) | The plan is governed end to end by spec `7ckptx` (its title, Concern, Goal, Spec-sync section and all four criteria cite it) but carried no `- From-Spec:` field, so the spec-to-plan handoff was prose-only and `aw check` reported the advisory. This is not cosmetic here: `7ckptx` is `approved` and carries `- Blocks-Release: next`, and `From-Spec` is the field a release-gate carrier check reads, so an unlinked plan cannot be seen as discharging a gated spec's criteria | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set `- From-Spec: 7ckptx` through `aw ipd set ... --from-spec 7ckptx` (the tooled route, not a hand edit); `aw check` no longer reports this plan and lint remains `conforming` at both checkpoints |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's "wait completes inside the bound's own window" is false because the watch polls at `check_interval` (default 1.0s). Change the assertion, change the interval, or drop the timing assertion? | CHANGE THE ASSERTION SHAPE: lower bound at the bound, generous ceiling above `bound + check_interval`, and require the test to state the interval it uses. | (a) Mandate a small `check_interval` (e.g. 0.05) so elapsed approximates the bound, rejected because it would make the test assert a tighter timing property than the production default exhibits, and the DEFAULT path is the one worth exercising; (b) drop the elapsed assertion entirely, rejected because A10's "within the permission deadline" and the permission case's 20x margin both need a timing claim, and dropping it would weaken the criterion; (c) leave it and let the executor discover the red, rejected because the plan would then ship a known-false instruction. | `TurnBoundWatch.__init__` `check_interval: float = 1.0`; `_run`'s `while not self._stop.wait(self.check_interval)`; measured real-child runs at `elapsed=0.475` (default) and `0.382` (`check_interval=0.05`), both `rc=-2` and both `fired='max-turn-timeout'`. Recorded as F12. | yes |
| D-2 | F-10's `git log -S` citation is wrong (five commits, not one) while its substantive zero-caller claim is right. Delete the finding, or correct the citation? | CORRECT THE CITATION and name the durable evidence (the call-site search), keeping the substantive claim. | Deleting F-10, rejected because the zero-caller fact is real, is the most consequential thing the plan measured, and is what justifies the `4xtpvg` carrier; silently dropping the `-S` sentence, rejected because a later reader re-running it would get five and distrust the whole finding. | `rg -n '\.note_permission_request\(' agent_workflows/ tools/` returns nothing; `git log -S'note_permission_request('` returns `e03c4ee4d`, `19313eed7`, `ba4f205b2`, `8a491d4c1`, `bfa81215c`; `8a491d4c1` is the introducing commit as claimed. | yes |
| D-3 | V-07 calls its mutation matrix the decisive evidence but nobody had shown the cells obtainable. Verify them at review, or leave it to execution? | VERIFY ALL THREE CELLS AT REVIEW and record the result, so execution is not asked for evidence of unproven feasibility. | Leaving it to execution, rejected because a matrix that turned out unobtainable would stall the plan at its most important validation item, and because cell (b)'s stub has a non-obvious arity requirement (`_expired(now)`) that would otherwise cost the executor a confusing `TypeError`; weakening V-07 to fewer cells, rejected because the plan is right that without them there is no evidence of sensitivity. | Cell (b): `_expired -> None` gives `rc='TIMEOUT(survived)' fired=None record=None`. Cell (c): `driver_bound_for_host -> MAX_TURN_TIMEOUT` gives `14400.0`, strict `<` False. Cell (d): `note_progress -> no-op` fires `permission-timeout` in half one and `max-turn-timeout` in half two, the required split. All via `mock.patch.object`, no production edit. Recorded as F15. | yes |
| D-4 | A10's text says the reaper attribution is "checked structurally, not by text grep", which could be read as licensing the structural pins P16 forbids. Flag a conflict, or accept the plan's reading? | ACCEPT the plan's reading and record why, rather than raising a finding. | Raising it as a spec-versus-principle conflict needing a maintainer ruling, rejected because the plan's method already satisfies both readings: exercising the DEFAULT reaper with no `reap=` override makes the kill attributable BY CONSTRUCTION, which is stronger than any structural check and reads no source, so there is nothing for a human to decide. | A10's quoted text; E-01's no-override requirement and V-01's rejection of an injected reaper there; `GUIDING_PRINCIPLES.md` P16's prohibition list and its narrow "text itself is the artifact" exception; F5/F6's honest refusals. | yes |

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. Six findings, all FIXED, zero deferred, zero open. Structural lint
`conforming` with zero diagnostics and zero advisories at both `--phase author` and
`--phase review-finalize`. No unresolved blocking question, so readiness is `go-pending-approval`: the
plan passed review and awaits human sign-off.

A NOTE ON WHAT THIS PLAN GETS RIGHT, since the findings above are necessarily about what it got wrong.
Its central discipline is unusually sound: every route was executed before being written down, the two
criterion clauses P16 makes untestable are declared as human-verified rather than faked (F5, F6), the
most-filed flake in the repository's history is identified and guarded in both ambient directions, the
mutation matrix exists at all, and the one product gap it discovered was filed as a carrier rather than
fixed opportunistically. The defects found here are a false timing claim and three bad citations, not
design errors.
