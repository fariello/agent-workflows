# Review findings: plan 2c0enr

- Subject-Id: 2c0enr
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ccf525e0` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and unmodified, and the
lane-input snapshot is byte-identical to the tracked file. No production code was modified by this
review; every measurement was taken by driving the shipped functions against synthetic run
directories in temp dirs, or by reading source with `inspect` and `ast`.

THE DIAGNOSIS IS CORRECT AND REPRODUCES IN FULL, AND THE PLAN'S MEASUREMENT DISCIPLINE IS STRONG.
F-01 reproduces exactly: of the eight columns the report-table branch reads, 1/2/3/7 are
backtick-stripped and 0/4/5/6 are not. F-03 reproduces end to end: the bare row renders
`[verified]` and the backticked twin does not. F-04 reproduces in every particular, including the
detail most plans would have missed, that `summary.counts` is keyed `` {'`executed`': 1} `` so an
operator's status counts are corrupted too. F-05 reproduces (one search hit, the bare fixture
header, which passes either way) and the deleted producer guard is where the plan says it is. F-06,
F-07, F-09 and F-11 all hold. The approach (normalize once at the read, not at the three comparison
sites) matches the two in-tree precedents the plan cites and is the right shape.

WHAT REVIEW FOUND IS TWO DEFECTS THAT WOULD HAVE BITTEN AT EXECUTION, one gate that cannot see its
own subject, and two spent baselines. The code change itself needed no redesign; what needed work
was the empty-cell policy, one test's premise, and E-04's verification.

**THE SINGLE HELPER WOULD HAVE SILENTLY CHANGED EVERY SHIPPED RUN WITH AN UNRUN ITEM (PR-701,
HIGH).** The `Verify` and `Last session` columns want OPPOSITE empty-cell answers and both are live.
Driven against a real `runner_shared.write_report` row for an item with `verification_status=""` and
`attempts=[]`, the producer writes cell 5 EMPTY and cell 7 as `` `` ``, and today's parse yields
`verification_status=None` but `session_id=''`. The natural helper shape
(`v = c.replace("`","").strip(); return v if v else None`) therefore flips `session_id` from `''` to
`None` for every queued-but-unrun item in every report. Nothing in the plan's own validation would
have caught it: no test in the tree asserts that value, E-02's parity fixture uses a populated
session so it cannot see it, and V-03's byte-identity check inspects the PRODUCER rather than the
parse, so all three pass. This is the review's most consequential finding because the plan's whole
claim is that no shipped behavior moves.

**E-03 AS WRITTEN FAILS ON ARRIVAL, AND ITS NATURAL REPAIR IS THE FORBIDDEN ONE (PR-702, HIGH).**
E-03 asserts the two readers agree on all eight fields. They already disagree on two for the
empty-verify / no-attempts shape: driven, `verification_status state='' report=None EQ=False` and
`session_id state=None report='' EQ=False`, with the other six equal. The cause is not markup and
E-01 does not fix it: the `state.json` branch takes `item.get("verification_status")` verbatim and
initializes `session_id = None`, while the report branch folds an empty cell to `None` and reads
cell 7 as a string. F-06 did not see this only because it chose a fully-populated state. The
compounding danger is that an executor meeting this failure would most plausibly "fix" it by folding
empty to `None` in the helper, which is exactly PR-701's shipped-behavior break. Fixed by bounding
E-03 to a fully-populated row, naming the divergence in its docstring, and recording OQ-03 plus a
Deferred row for why reconciling it here would be an unmeasured semantic change.

**E-04's OWN VERIFICATION COMMAND CANNOT SEE ONE OF ITS SIX TARGETS (PR-703, MEDIUM).** E-04 says
four citations across two comments and gates on `rg -n "run_viewer\.py:[0-9]" agent_workflows/`
returning nothing. Measured: that pattern returns FIVE hits, and the `agy_runipd.py` comment carries
a SIXTH on the following line written as a bare `` `:1370` `` continuation, which the pattern cannot
match. So the gate can pass while that file still tells the next reader the cell is compared to
`verified`. A second pattern is now required, with the honest note that it also matches legitimate
spec-offset citations that must be left alone. Separately, F-02's own re-derived targets have
drifted AGAIN since authoring (1008 is now `except OSError:` inside `load_run_summary`, not
`if setid:`; 1370 is docstring prose inside `_state_setids`; 1476/1483 are in
`resolve_target_runs_detailed` and 1926/1939 in `format_artifact_audit_summary`), so E-04 must
re-derive rather than quote them. The conclusion is unchanged and stronger.

**TWO BASELINES ARE SPENT (PR-704, MEDIUM; PR-705, LOW).** F-08 tells the executor to expect
`1 failed, 3006 passed, 2 skipped` and names the failure as stale-fixture noise. Commit `f1b5b9ff`
repaired it after authoring: a bare run now reports `3109 passed, 2 skipped` with ZERO failures, and
the named test file reports `8 passed`. An executor who saw one failure and matched it against F-08
would have excused a real regression. F-10's two named co-edit plans (`mlhryi`, `otr54d`) are both
`executed` now; re-derived, the one genuine live overlap is `t0ovw6`, which shares
`agent_workflows/agy_runipd.py` but whose E-04 corrects anti-re-fork citations and whose own
enumeration of its six targets in that file does not include the `write_report` comment.

**TWO `Attempts` FALLBACKS ARE EASY TO COLLAPSE (PR-706, LOW).** E-01 says an unparseable `Attempts`
falls back to `1`, which is true of the `except ValueError` branch, but an ABSENT column 6 yields `0`
from the `attempts = 0` initializer. Driven: `x` in column 6 gives `attempts_count=1`, a five-column
row gives `0`. Both must survive a refactor of that expression, and a plan that names only one
invites unifying them.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 and OQ-02 were both re-verified and survive: the three comparison sites are confirmed as
two in `format_step_line` and one in `render_steps_table`, and the producer's eight cell values are
all generated and pipe-free. OQ-03 is new. Two supporting facts were also established that the plan
did not claim and that strengthen it: the header/separator skip guards match the real producer and
the `## Dependency blocks` section's lines never reach the row loop (F-14), and no historical report
in-tree exercises the old backticked form, so E-01 changes the parse of no committed artifact (F-15).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A. Correctness and data integrity | driven `runner_shared.write_report` row `'\| 1 \| `aaa111` \| `s` \| `execute` \| executed \|  \| 0 \| `` \|'`; `load_run_summary` -> `verification_status=None`, `session_id=''`; naive-helper contrast over cells `''`, `` '``' ``, `` '` `' `` | THE SINGLE HELPER WOULD SILENTLY CHANGE EVERY SHIPPED RUN WITH AN UNRUN ITEM. The `Verify` and `Last session` columns want opposite empty-cell answers and both are live: the producer writes cell 5 empty and cell 7 as `` `` ``, and today's parse gives `None` and `''` respectively. A helper folding empty to `None` flips `session_id` for every queued-but-unrun item. No test asserts that value, E-02's fixture uses a populated session, and the byte-identity check inspects the producer, so every stated check passes. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (a stated helper contract plus one driven probe, decided before code exists) | FIXED | E-01 now mandates a `str`-returning helper that does NOT fold empty, with the `Verify` column's `None`-folding kept at its existing call site and explicitly not tidied inside. Added F-12. E-01's Expected outcome and a new Required-tests bullet demand the shipped no-attempts row still yield `None`/`''`. V-01 demands the driven probe plus the helper's signature. The gate's "one way this can fail silently" paragraph is now two, with this named as the likelier. |
| PR-702 | HIGH | IN-SCOPE | E. Testing and verification | driven both readers over a `verification_status=""`/`attempts=[]` run: `verification_status state='' report=None EQ=False`, `session_id state=None report='' EQ=False`, other six equal; `load_run_summary`'s state branch `item.get("verification_status")` and `session_id = None` | E-03 FAILS ON ARRIVAL AND ITS NATURAL REPAIR IS THE FORBIDDEN ONE. The two readers already disagree on two of the eight fields for the empty-verify / no-attempts shape; the cause is not markup and E-01 does not fix it. F-06 missed it by choosing a fully-populated state. An executor meeting the failure would most plausibly fold empty to `None` in the helper, which is PR-701's shipped-behavior break. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (bound the assertion and document the limit; no code change) | FIXED | E-03 is bounded to a fully-populated row (non-empty verify, at least one attempt), must name the divergence in its docstring, and must NOT assert equality over the empty shape. Added F-13. New OQ-03 and a Deferred row record why reconciling it here would be an unmeasured semantic change in a plan claiming none. V-03 requires pasting the driven divergence table so the bound is measured rather than asserted. |
| PR-703 | MEDIUM | IN-SCOPE | G. Plan executability | `rg -n "run_viewer\.py:[0-9]" agent_workflows/` -> 5 hits; `agy_runipd.py` line following its `run_viewer.py:1008` hit reads `# `:1370` compares it to the bare string `verified``; `ast`-mapped current targets for 1008/1370/1476/1483/1926/1939 | E-04's OWN GATE CANNOT SEE ONE OF ITS TARGETS. The count is six citations across three blocks, not four across two, and the sixth is a bare `` `:1370` `` continuation invisible to the stated `rg` pattern, so the gate can return nothing while a stale `run_viewer` offset survives in `agy_runipd.py`. F-02's re-derived targets have also drifted again since authoring, so quoting them would plant new expiring anchors in the very plan about expiring anchors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 restated as six citations across three blocks, with a second required pattern (`` `:[0-9]{3,4}` `` over the two files) and the honest note that it also matches legitimate spec-offset citations to be left alone. E-04 must re-derive each offset's current target rather than quote F-02's. Expected outcome and V-04 both carry the two-pattern gate. |
| PR-704 | MEDIUM | IN-SCOPE | E. Testing (live-artifact baseline) | bare `python3 -m pytest` -> `3109 passed, 2 skipped, 3 warnings in 49.44s`, zero failures; `tests/test_dependency_block_reporting.py -o addopts=""` -> `8 passed`; `git log --oneline -3 -- tests/test_dependency_block_reporting.py` -> `f1b5b9ff` | THE "PRE-EXISTING FAILURE" BASELINE IS SPENT AND ITS PERSISTENCE IS DANGEROUS. F-08 tells the executor to expect one failure and excuse it. That test was repaired by `f1b5b9ff` after authoring and the suite is now green, so an executor who saw one failure and matched it against F-08 would have excused a genuine regression introduced by this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 rewritten as SUPERSEDED with the re-driven green figures and the repairing commit named, and with the consequence stated (any failure is now a signal). The Step-0 convention line inverted. Required tests and V-04 both now demand a baseline re-measured in-lane immediately before the change, explicitly not a comparison against F-08. |
| PR-705 | LOW | IN-SCOPE | C. Architecture (concurrency claim currency) | `aw find plans mlhryi` -> `executed`; `otr54d` -> `executed`; `rg -l run_viewer .aw/records/plans/pending/*.ipd.md` -> `gygujf`, `t0ovw6`, `ck0vya`, self; `t0ovw6` `- Scope-Paths:` including `agent_workflows/agy_runipd.py` and its E-04 target enumeration | F-10's CO-EDIT ANALYSIS IS STALE AND MISSES THE ONE LIVE OVERLAP. Both plans it discusses have shipped. The genuine live overlap is `t0ovw6` (`reviewed`), which shares `agent_workflows/agy_runipd.py`. It is still not an expression conflict (it edits anti-re-fork citations; its own enumeration of its six targets in that file excludes the `write_report` comment), but a plan that names the wrong neighbours gives a finalize reconciliation no useful prior. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 re-derived: both cited plans marked `executed`, the four pending `run_viewer` mentions enumerated, `t0ovw6` named as the single real overlap with the reason it is not a conflict. A Scope-check bullet declares it so the reconciliation reads as expected. |
| PR-706 | LOW | IN-SCOPE | A. Correctness | driven: column 6 = `x` -> `attempts_count=1`; five-column row -> `attempts_count=0`; the `attempts = 0` initializer and the `except ValueError: attempts = 1` branch | THE TWO `Attempts` FALLBACKS ARE DIFFERENT NUMBERS AND THE PLAN NAMES ONLY ONE. An unparseable cell yields `1`; an absent column 6 yields `0`. Naming only the `1` invites a refactor that unifies them, silently changing the five-column case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01's tolerance list now states both fallbacks, with the driven values and an explicit "do not unify them". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The `Verify` and `Last session` columns want opposite empty-cell answers. Should the helper fold empty to `None`, or return a plain string with the folding kept per-column? | RETURN A PLAIN STRING; keep the `Verify` column's `None`-folding at its existing call site. | (a) Fold empty to `None` inside the helper - rejected on measurement: it changes `session_id` from `''` to `None` for every shipped run with an unrun item, and no stated check would catch it. (b) Have the helper take a `fold_empty` flag - rejected as a worse shape than leaving the existing call-site guard alone: the guard already exists, reads clearly, and moving the policy into a parameter re-creates the per-column branching inside the one function meant to be uniform. (c) Fold for both columns and "fix" the session field downstream - rejected: it changes a shipped parse to satisfy a refactor, which is the opposite of this plan's claim. | Driven `write_report` row for `verification_status=""`/`attempts=[]` giving cell 5 empty and cell 7 `` `` ``; today's parse `verification_status=None`, `session_id=''`; the existing `if len(cols) > 5 and cols[5].strip()` guard. | yes |
| D-2 | The two readers disagree on two fields for an empty-verify / no-attempts row. Reconcile them in this plan, or bound E-03's claim? | BOUND THE CLAIM: assert equivalence for a fully-populated row and name the divergence in the docstring. | (a) Reconcile by folding the state branch's `''` to `None` - rejected: unmeasured consumer impact, and it is a `state.json`-branch change E-01 explicitly excludes. (b) Reconcile by stopping the report branch folding - rejected for the same reason and because it is PR-701's break in another guise. (c) Assert equality over the empty shape anyway - rejected as actively harmful: it fails on arrival and its natural repair is the forbidden helper change. (d) Ask the maintainer - rejected: the repository answers what the behavior IS by running it, and the decision not to change unmeasured semantics inside a no-behavior-change plan follows from the plan's own stated claim. | Driven per-field table showing the two `EQ=False` fields; `load_run_summary`'s state branch taking the value verbatim and initializing `session_id = None`; E-01's own exclusion of the `state.json` branch. | yes |
| D-3 | E-04's `rg` gate misses a bare `` `:1370` `` continuation. Add a second pattern, or require the broad pattern to be empty? | ADD A SECOND PATTERN AND READ ITS OUTPUT, confirming only that no remaining hit refers to `run_viewer`. | (a) Require `` `:[0-9]{3,4}` `` to return nothing - rejected on measurement: that pattern legitimately matches several `` spec `:131` ``-style citations in `runner_shared.py` and `oc_runipd.py` that are not this plan's business, so an emptiness requirement would either fail forever or push an executor into out-of-scope edits. (b) Keep only the original pattern - rejected: it provably cannot see one of the six targets. | `rg -n "run_viewer\.py:[0-9]" agent_workflows/` -> 5 hits; the sixth citation read directly at `agy_runipd.py`'s following line; `rg -n '`:[0-9]{3,4}`' agent_workflows/` showing the unrelated spec-offset population. | yes |
| D-4 | F-08's pre-existing-failure baseline is spent and the suite is green. Update the number, or change what the executor compares against? | BOTH: mark F-08 superseded with the re-driven green figures, and require an in-lane baseline taken immediately before the change. | (a) Just update the count - rejected: it has now drifted twice and would drift again before execution; the repository's live-artifact-count convention says such a figure is context, not a bar. (b) Leave the row and let the executor notice - rejected as the most dangerous option: the row actively instructs excusing a failure, so a real regression introduced by this plan would be attributed to stale noise. | Bare suite re-driven green (`3109 passed, 2 skipped`); `tests/test_dependency_block_reporting.py` -> `8 passed`; `f1b5b9ff` named as the repair; `aw find plans 5o1jye` -> `executed`. | yes |
