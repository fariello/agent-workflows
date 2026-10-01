# Review findings: plan 4x9min

- Subject-Id: 4x9min
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (MEDIUM, fixed), PR-402 (MEDIUM, fixed), PR-403 (MEDIUM, fixed), PR-404 (LOW, fixed), PR-405 (LOW, fixed), PR-406 (LOW, fixed)

## Round 1

Reviewed at HEAD `13cf0fcc`. Structural preflight `aw ipd lint --phase author --agent` reported
`clean` (exit 0) before semantic review, and `--phase review-finalize --agent` reported `clean`
(exit 0) after every revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply.

THE PLAN IS UNUSUALLY WELL EVIDENCED AND ITS CENTRAL CLAIM REPRODUCES ON LIVE DATA. I ran the real
commands rather than reading the branches. On one artifact, same selector, only the flag differing:
`aw set approved 95jk4s --json --dry-run` reports `would update status on 1 artifact(s)` with
`kind: update` and `detail: status: approved -> approved`, while `--json --yes` reports
`updated status on 0 artifact(s)` with `kind: noop` and `detail: status: approved (unchanged)`,
leaving the tree byte-identical (`git status --short` empty afterwards). Every other material claim
verified too: the human form prints `unchanged` on both paths (F-04); the defect reproduces on a
backlog item and under the untyped `aw set` spelling (F-05); the apply path's predicate really is
post-write (`(old_text != new_text) or (dest_path.resolve() != rec.path.resolve())`, computed after
`apply_status_change`) and so is structurally unavailable in a dry run (F-06); `noop` in
`tests/test_status_set.py` is only a fixture name and an unrelated local, and no test asserts on any
dry-run `changes[].kind` (F-08); no spec mentions `noop` and the agent schema validates the record
ENVELOPE kind rather than `Change.kind` (F-11); and `run_selection_policy` does import `status_set`,
so OQ-02's cycle argument holds structurally (not merely editorially).

The findings therefore improve the plan's MECHANISM and its EVIDENCE DISCIPLINE rather than
challenging its premise. Three concern facts the plan would have had to rediscover during execution,
and three concern measurements that had already drifted.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | IN-SCOPE | Rubric C (canonical mechanisms), F (single source of truth) | `status_set.run_set_command` apply-path row `{"path":..., "type":..., "old_status":..., "new_status":..., "changed": changed}`; measured key lists: apply `['changed','new_status','old_status','path','type']`, dry-run `['dry_run','new_status','old_status','path','type']` | E-02 LEFT THE KEY NAME OPEN WHEN THE REPOSITORY ALREADY FIXES IT. The apply path's `items` rows already carry a `changed` key, so the dry-run branch is not missing a fact needing a new name, it is missing a key its own sibling branch publishes. An executor free to choose would plausibly write `is_noop` or `unchanged`, creating exactly the two-branch divergence this plan exists to remove. E-02 also asked the executor to decide at execution time whether the fact ends up carried twice, when the apply path already answers that by carrying it in both `changes` and `items` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now mandates the key name `changed`, names the three wrong spellings it forbids, and states that the duplication is DELIBERATE with `changes[].kind` authoritative for a cross-verb consumer and `items[].changed` the mirror, matching the apply path. Expected outcome now requires the two branches' row key sets to differ only by `dry_run`. V-02 requires both key lists pasted and compared. Recorded as F-13 |
| PR-402 | MEDIUM | IN-SCOPE | Rubric A (correctness), B (no false claim) | apply path `Change(... applied=changed ...)`; dry-run branch's existing `applied=False`; measured apply no-op payload `applied: false` | THE `applied` FIELD WAS AN UNGUARDED TRAP. E-01 says to emit the kind and detail "exactly as the APPLY path does", and the apply path's parallel line is `applied=changed`. A mechanical reading would copy it, making a PREVIEW of a real transition report `applied: true` for work that did not happen, which is a worse defect than the mislabelled kind being fixed and one no listed test would catch | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states `applied` stays `False` on every dry-run entry of both kinds, explains that the apply path's no-op is also `applied=False` so the two branches legitimately differ only on a real transition, and the Expected outcome asserts it. V-01 requires it shown. Recorded as F-14 |
| PR-403 | MEDIUM | IN-SCOPE | live-artifact re-derivation convention; Rubric E | bare `python3 -m pytest` at review: `1 failed, 3401 passed, 2 skipped` against the authored `3246 passed, 2 skipped`; the failure re-run in isolation showing `- 2026-09-30 HIST_ACTOR` / `+ 2026-10-01 HIST_ACTOR` | THE BASELINE WAS WRONG TWICE OVER, AND IT WAS WRITTEN AS AN ACCEPTANCE BAR. The authored total had drifted by 155 tests within a day, and the tree carries a midnight-boundary flake (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`) that fails whenever the UTC date rolls over between two writes, so "compare against 3246 passed" is unachievable at some hours and misleading at all of them. That file is outside this plan's scope and unmodified in this lane. Order 01 of this same Set recorded the identical finding independently | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten with the re-measurement, the flake named and diagnosed, and the consequence stated. The Required-tests item and V-03 now demand a self-derived pre-change baseline compared by failing NODE IDS, and explicitly forbid comparing against any total written in the plan |
| PR-404 | LOW | IN-SCOPE | live-artifact re-derivation convention | Set `awrenamesel` re-read at review: all five plans `approved`, against the authored three `reviewed` / two `to-review` | THE SHARPEST EVIDENCE CITED A FIXTURE THAT HAD DRIFTED. F-03 and the Goal's fact 3 both describe a mixed Set that no longer exists, so a reader reproducing the plan's own headline measurement would get different output and might doubt the defect | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03, the Goal's fact 3, the Concern line and F-02 all now carry the review re-proof on the current tree, which is a STRONGER case (machine says 5, human says 0, versus the authored 5 against 2). Each also tells the executor to build its own fixture rather than selecting a tracked Set |
| PR-405 | LOW | IN-SCOPE | Rubric A (correctness), D | `_format_status_transition_line` computes `old_status = (rec.status or "draft")` and renders `unchanged` when `old_status == norm_stat_clean`; the prescribed predicate compares `(r.status or "")` | THE PRESCRIBED PREDICATE AND THE HUMAN RENDERER CAN DISAGREE, for an artifact with an empty or absent `- Status:` targeted at `draft`: the predicate yields `changed=True` while the human line prints `unchanged`. Measured UNREACHABLE today: zero of 1098 plans, 779 backlog items and 38 specs carry an empty or absent status. Worth recording because this plan's whole thesis is that two code paths must agree about one artifact | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the case with its measurement, tells the executor not to chase it with a second default inside the new helper, and asks for it in V-01's evidence if a fixture makes it reachable. Recorded as F-15 |
| PR-406 | LOW | IN-SCOPE | live-artifact re-derivation convention | re-scan of every pending `- Scope-Paths:` with each plan's `- Id:`: 8 plans declare `status_set.py` and 4 declare its test file, against the authored 10 and 5 | F-09's CONTENTION COUNTS HAD DRIFTED IN BOTH DIRECTIONS (`e25iy9`, `izh17y` arrived; `0ykozn`, `ghna7l`, `4a8yws`, `tr8ugt` left the module list), and the gate restated the stale figure as fact | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 carries both measurements, notes membership changed both ways, and states the numbers are context and never an acceptance criterion. The gate no longer quotes a figure |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02 left the `items` key name to the executor. Mandate one, or leave the choice open? | MANDATE `changed`, the name the apply path already uses. | (a) Leave it open, rejected because a free choice invites `is_noop` or `will_change` and recreates the two-branch divergence the plan exists to remove. (b) Mandate a new, more descriptive name, rejected for the same reason plus it would leave the apply path and the dry-run path disagreeing about what to call one fact. | Measured: the apply path's `items` rows already carry `changed` (key list `['changed','new_status','old_status','path','type']`, `changed: false` on a no-op) while the dry-run rows carry `['dry_run','new_status','old_status','path','type']`. The plan's own thesis is that the two branches must converge, so adopting the shipped name is the only choice consistent with it. | yes |
| D-2 | The stale kind-vocabulary comment on `result_types.Change` lists neither `update` nor `noop`. Fix it here, file it, or record it? | RECORD it as out of scope with the measurement, and decline a carrier. | (a) Fix it, rejected: it would put the shared machine-contract type every verb's payload flows through into `- Scope-Paths:` for a comment. (b) File a backlog item, rejected because it would assert that this plan discovered a defect it is declining to fix, when the inaccuracy predates this plan and is unchanged by it. | `result_types.Change`'s docstring reads `kind: str  # "modify", "create", "delete", "rename"`, while `update` ships in 10 sites and `noop` in exactly one (`status_set.py`, the apply path this plan copies). So the comment was already wrong before this plan and this plan does not worsen it. | yes |

### Verdict

APPROVE WITH REVISIONS APPLIED. Readiness `go-pending-approval`: the verdict is clean, no BLOCKER or
HIGH finding was raised, and no open question remains (all three were resolved from in-tree evidence
at authoring and each was independently verified at review). Human approval is the remaining step.
