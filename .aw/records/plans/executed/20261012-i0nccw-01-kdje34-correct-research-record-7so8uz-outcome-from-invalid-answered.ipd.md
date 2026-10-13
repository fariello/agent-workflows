# IPD: Correct research record 7so8uz outcome from invalid answered to adopted so aw research index passes

- Date: 2026-10-12
- Kind: child
- Concern: Research record `7so8uz` carries `outcome: answered`, a value outside the closed research outcome vocabulary, so `aw research index --check` (and `aw index research --check`) fails closed repository-wide with `frontmatter-invalid`.
- Scope: Change the single frontmatter value in `7so8uz` to the valid `adopted` (its declared consumer `0b7fic` already exists) through the tooled `aw research set-outcome` verb, and prove the index gate returns to exit 0. No code, spec, or other record changes.
- Scope-Paths: .aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md, .aw/records/plans/pending/20261012-i0nccw-01-kdje34-correct-research-record-7so8uz-outcome-from-invalid-answered.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: i0nccw
- Blocks-Release: next
- Set: i0nccw
- Order: 1
- Highest E allocated: 03
- Author: opencode/claude-opus
- Id: kdje34

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: kdje34 verified (set i0nccw, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-12 draft (opencode/claude-opus): created.
- 2026-10-12 to-review (opencode/claude-opus): authored from backlog `i0nccw`; fix rehearsed in the authoring lane (then reverted) to confirm it clears the gate.

## Goal

Make `aw research index --check` pass again by replacing the invalid `outcome: answered` in research record `7so8uz` with the valid `outcome: adopted`, which is the truthful value because executed plan `0b7fic` consumed the record and the record already declares `consumed-by: [0b7fic]`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reproduce, fix, verify

- [x] E-01 REPRODUCE THE FAILURE before changing anything: run `aw research index --check` and capture its exit code and the `frontmatter-invalid` line naming `20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md` with `outcome must be one of ['adopted', 'informational', 'none-yet', 'rejected']`. If the line is ABSENT (someone already fixed it), record that; E-02 then performs as a recorded no-op (see E-02), and E-03 still runs.
  - Depends on: none
  - Expected outcome: the failing exit code (1) and the exact `frontmatter-invalid` diagnostic for `7so8uz` are recorded, or its absence is recorded.
  - Execution state: performed

- [x] E-02 APPLY THE FIX WITH THE TOOLED VERB, not a hand edit: `aw research set-outcome 7so8uz --to adopted --consumed-by 0b7fic --apply`. Then confirm with `git diff` that the ONLY change to the record is the single line `-outcome: answered` / `+outcome: adopted` (the `consumed-by: [0b7fic]`, `status: active`, body, and every other field unchanged). Commit via `aw commit kdje34 -- <record path> <this plan path>` and record the resulting commit hash. If E-01 found the line already absent, do NOT run the verb or commit: paste `grep -n '^outcome:\|^consumed-by:' <record path>` showing `outcome: adopted` and `consumed-by: [0b7fic]` and mark E-02 performed as a no-op.
  - Depends on: E-01
  - Expected outcome: the record reads `outcome: adopted` with `consumed-by: [0b7fic]`; the diff is exactly one changed line in that file.
  - Execution state: performed
  - Commit hash: 025a3fd648247abeb4a68e60c21dcde810a77ff9

- [x] E-03 RE-RUN THE GATE: `aw research index --check` and confirm exit 0 and zero `frontmatter-invalid` lines; also run `aw research index` (regenerates the GITIGNORED `INDEX.json`/`INDEX.md`, which must NOT be staged) and `python3 -m pytest tests/test_research_index.py -o addopts=""` to confirm no research-index regression.
  - Depends on: E-02
  - Expected outcome: `aw research index --check` exits 0 with no `frontmatter-invalid` finding (remaining `info`-severity findings such as `dangling-citation` and `adopted-without-consumer` do not affect the exit code); the research-index tests pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The research outcome vocabulary is closed and defined once in `research_contract.OUTCOMES` (`("adopted", "rejected", "informational", "none-yet")`); the CLI `research set-outcome` restricts `--to` to the same four choices (`cli.py`, `choices=["adopted", "informational", "rejected", "none-yet"]`), and `docs/artifact-lifecycles.md` documents the same set ("A separate `outcome:` field (`none-yet`, `adopted`, `informational`, `rejected`)").
- Research frontmatter is tool-owned: the documented way to change an outcome is `aw research set-outcome <id6> --to adopted --consumed-by <plan-id6> --apply` (`docs/artifact-lifecycles.md`), implemented by `research_cmd.run_set_outcome` / `research_cmd.plan_set_outcome`.
- `adopted` requires a non-empty `consumed-by` (rule `adopted-without-consumer`, `research_index.ADOPTED_NO_CONSUMER_RULE`); `7so8uz` already carries `consumed-by: [0b7fic]`, so `adopted` satisfies it.
- `info`-severity research rules (`dangling-citation`, `adopted-without-consumer`, `stale-state-to-promote`, `check.stale-index-missing`) are exempt from the drift exit code (`check_engine` RuleSpec comments: "artifact_core.drift_exit_code exempts ONLY `info`"), so `frontmatter-invalid` is the sole reason the gate is red.
- Executed plans are immutable records: `0b7fic` (executed) and review `0b7fic` mention `outcome: answered` as what authoring set; they are NOT edited (AGENTS.md execution contract).
- Commits go through `aw commit`; never push.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | `aw research index --check` exits 1 in this lane at HEAD `eed711d76`. | Measured at authoring: `rc=1`, with the line `20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md: frontmatter-invalid: outcome: outcome must be one of ['adopted', 'informational', 'none-yet', 'rejected']`. |
| F2 | It is the ONLY non-`info` finding. | Rule census of the same run: 274 `dangling-citation`, 35 `adopted-without-consumer`, 21 `stale-state-to-promote`, 2 `check.stale-index-missing`, 1 `frontmatter-invalid`; all but the last are registered `info` in `check_engine`. |
| F3 | The value was introduced by plan `0b7fic`'s authoring commit `59f685721`, which hand-set `status: active`, `outcome: answered` (plan `0b7fic` E-06 text: "AUTHORING ALREADY SET ... `outcome: answered`"). Executed plan `rdjka2` independently noted the breakage ("carried an invalid `outcome: answered` frontmatter value that broke `aw research index`"). | `git log -- <record>`; grep of executed plans. |
| F4 | `adopted` is the correct replacement: the record was consumed by executed plan `0b7fic` and already declares `consumed-by: [0b7fic]`. `informational` would understate a record a plan acted on. | Record frontmatter; plan `0b7fic` in `executed/`. |
| F5 | The fix works. Rehearsed in the authoring lane: `aw research set-outcome 7so8uz --to adopted --consumed-by 0b7fic --apply` produced a one-line diff and `aw research index --check` returned `rc=0` with 0 `frontmatter-invalid` lines; the change was then reverted (`git checkout`) so execution performs it. | Authoring lane transcript. |
| F6 | No other record carries `outcome: answered`. | Repository grep: the only research hit is `7so8uz`; other hits are prose in an executed plan and a review. |
| F7 | Re-measured at review HEAD `8a523e16e`: `aw research index --check` still exits 1 with the same single `frontmatter-invalid` line for `7so8uz`; `dangling-citation` now counts 275 (live count, context only, not a bar). Rehearsal repeated and reverted: `set-outcome --apply` gave a one-line diff (`-outcome: answered` / `+outcome: adopted`), the check exited 0 with 0 `frontmatter-invalid` lines, `INDEX.json`/`INDEX.md` are gitignored (`.aw/.gitignore` lines 50-51), and `tests/test_research_index.py` reported `51 passed`. | Commands run in the review lane. |

## Proposed changes (ordered, validatable)

1. Reproduce the gate failure (E-01).
2. Run `aw research set-outcome 7so8uz --to adopted --consumed-by 0b7fic --apply` and commit the single-line change (E-02).
3. Re-run `aw research index --check` and the research-index tests (E-03).

## Deferred / out of scope (with reason)

- Hardening authoring so a hand-written invalid research outcome cannot be committed (for example a pre-commit hook on research frontmatter): out of scope; the backlog item asks only to fix the record, and the existing `aw research index --check` gate already detected it. Fileable as separate backlog if the maintainer wants it.
  - Carrier-Declined: the existing `aw research index --check` gate detected the defect; no measured recurrence (F6 finds no other `outcome: answered` record), so no hardening obligation is carried.
- The executed plan `0b7fic` and its review text that mention `outcome: answered`: not edited, because executed records are immutable.
  - Carrier-Declined: executed plans and review records are historical; the prose accurately records what authoring set at the time.
- The 274 `dangling-citation` and other `info` findings: not defects of this item and do not gate.
  - Carrier-Declined: `info` severity is exempt from the drift exit code (`artifact_core.drift_exit_code`), so these do not gate the index and are outside this item.

## Scope check

- Over-scope: none. One frontmatter line in one record plus this plan.
- Under-scope: none. F2 shows the invalid outcome is the sole gating finding, so fixing it restores the gate.

## Required tests / validation

- `aw research index --check` exits 0 with no `frontmatter-invalid` finding (performed by E-03, validated by V-03).
- `python3 -m pytest tests/test_research_index.py -o addopts=""` passes (performed by E-03).
- `git diff` of the record shows exactly one changed line (performed by E-02, validated by V-02).

## Spec / documentation sync

N/A: the outcome vocabulary is unchanged and already documented (`docs/artifact-lifecycles.md`); this plan corrects one record to conform to it. No spec is touched.

## Open questions

### OQ-01: adopted or informational?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `adopted`, because executed plan `0b7fic` consumed the record and it already declares `consumed-by: [0b7fic]` (F4); this also satisfies the `adopted-without-consumer` rule.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the actual pre-fix `aw research index --check` exit code and the `frontmatter-invalid` line for `7so8uz` (or the pasted output proving it was already absent).
  - Observed evidence:
```
$ aw research index --check
EXIT_CODE=1
20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md: frontmatter-invalid: outcome: outcome must be one of ['adopted', 'informational', 'none-yet', 'rejected']
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git show --stat <E-02 commit>` and the `git show <E-02 commit> -- <record path>` hunk (the hash E-02 recorded, not a bare `HEAD`, which a later commit may move) proving the only change is `-outcome: answered` / `+outcome: adopted`, with `consumed-by: [0b7fic]` present in the resulting file. In the E-01 already-fixed branch, paste instead the `grep` output E-02 recorded and `git log --oneline -1 -- <record path>` naming the commit that fixed it.
  - Observed evidence:
```
$ git show --stat 025a3fd648247abeb4a68e60c21dcde810a77ff9
commit 025a3fd648247abeb4a68e60c21dcde810a77ff9 (HEAD -> aw/lane/kdje34)
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Tue Oct 13 07:11:35 2026 -0400

    work(kdje34): Correct research record 7so8uz outcome from invalid answered to adopted so aw research index passes

    AW-Run: run-20261013T014119Z-1382357
    AW-Item: kdje34

 ...20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git show 025a3fd648247abeb4a68e60c21dcde810a77ff9 -- .aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md
diff --git a/.aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md b/.aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md
index 7502f578a..16e607d02 100644
--- a/.aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md
+++ b/.aw/records/research/20261001-4xtpvg-00-7so8uz-permission-ask-observability.assessment.md
@@ -7,7 +7,7 @@ topic: [turn-bounds, lane-containment, permission-deadlock]
 model:
 kind: assessment
 status: active
-outcome: answered
+outcome: adopted
 summary: Measured: an opencode permission ask never reaches the driver's stdout stream, so A10c option (i) is unsatisfiable there; the log is the only carrier and the 2026-09-05 deny posture already closed the isolated-turn case
 consumed-by: [0b7fic]
 priority: medium
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the post-fix `aw research index --check` exit code (must be 0) with a count of `frontmatter-invalid` lines (must be 0), plus the actual pytest summary line for `tests/test_research_index.py`; paste `git status --short` showing no `INDEX.json`/`INDEX.md` staged.
  - Observed evidence:
```
$ aw research index --check
EXIT_CODE=0

$ aw research index --check 2>&1 | grep -c "frontmatter-invalid"
0

$ python3 -m pytest tests/test_research_index.py -o addopts=""
============================== 51 passed in 1.73s ==============================

$ git status --short
# (no output, clean working tree; INDEX.json and INDEX.md are gitignored and not staged)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute only after human approval. Commit only the `- Scope-Paths:` files through `aw commit kdje34 -- <paths>`; never `git add -A` or `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before committing, and never stage the gitignored `INDEX.json`/`INDEX.md`. Paste the ACTUAL command and runner output for every claim; never assert a pass you did not run. OQ-01 is resolved.

SCOPE FENCE. The declared change is one frontmatter line in `7so8uz` plus this plan; no code, spec, test, or other record is in scope. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`, never silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` reads `pass` with pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. In a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`; executing by hand, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit status or `git mv` the plan into `executed/`.
