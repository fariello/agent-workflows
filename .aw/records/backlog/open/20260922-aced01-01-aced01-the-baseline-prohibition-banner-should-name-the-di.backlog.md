- Id: aced01
- Status: open
- Set: aced01
- Priority: medium
- Work-Kind: chore
- Summary: The THE PRE-WORK SUITE BASELINE prohibition banner in runner_shared states 'NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT' without naming the DIRECTION it forbids, so it reads as barring a baseline-relative gate that only ever makes an outcome more permissive

## Workflow history
- 2026-09-22 created (aw backlog): The THE PRE-WORK SUITE BASELINE prohibition banner in runner_shared states 'NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT' without naming the DIRECTION it forbids, so it reads as barring a baseline-relative gate that only ever makes an outcome more permissive

FOUND while executing plan `tgyfs2` (revalbase 01), which had to interpret this banner before it could proceed; the interpretation is recorded as that lane's DECISION 01-tgyfs2-D1 and is flagged for maintainer review.

THE TEXT AS WRITTEN. The banner's headline sentence is absolute ('NOTHING MAY REFUSE, DOWNGRADE, OR OTHERWISE CHANGE AN OUTCOME ON THE STRENGTH OF IT') and its body then makes clear what was actually rejected: the proposal to 'refuse `not-mine` for any failing id ABSENT from the baseline'. All four of its numbered reasons are reasons a baseline cannot be used to DISBELIEVE an agent - a gate cannot detect deception, a capable model can make tests pass, a malicious agent would rewrite the gate, the target is sloppiness not malice. Spec `25kzda` 5.1's 'THE HONEST LIMIT' paragraph carries the same ruling in the same shape.

THE GAP. Every reason is directional (it forbids using the baseline to make an outcome WORSE), but the headline is not, so a reader meets an absolute prohibition and only discovers its scope by reading four paragraphs down and cross-checking which enforcement surface the tests actually guard. `tgyfs2` needed a baseline-relative post-merge verdict that can ONLY make the gate more permissive and judges nobody's fault, and deciding whether that was permitted cost a full pass over the banner, the spec section, and `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`.

WHY THIS IS A DOCUMENTATION DEFECT AND NOT A DESIGN ONE. The ruling is right and the guards are right; the four reasons and their tests are exactly correct for the thing they forbid. What is missing is one sentence naming the direction, so the next reader neither re-derives the scope nor - the worse outcome - abandons a legitimate change believing it is forbidden. `tgyfs2` added that distinction beside its own new section, but the authoritative place for it is the banner itself and, if the maintainer agrees, the spec paragraph.

WHERE: agent_workflows/runner_shared.py, the 'THE PRE-WORK SUITE BASELINE (integearn-05, `9lyg5h`)' banner; and .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md section 5.1 'THE HONEST LIMIT'.

NOTE the banner's wording is pinned by `tests/test_suite_baseline.py::test_THE_RULING_IS_RECORDED_AT_THE_CODE_with_its_reasoning`, which asserts five exact phrases; an edit must keep those and ADD to them.
