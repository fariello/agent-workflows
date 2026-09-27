# IPD: Delete the stale interim Blocks-Release note from the 2.0.0 release record

- Date: 2026-09-26
- Kind: child
- Concern: The 2.0.0 release record carries a subsection "### Interim: IPD sets that cannot yet carry the field (pending vwios6)" that documents a TEMPORARY EXCEPTION to the record's own no-prose-blocker-list rule. Its stated deletion condition is met (backlog `vwios6` and `w6mqc0` are both done; `aw ipd set --blocks-release` exists) and the four Sets it names (execset, ipdgates, proclint, unifyfileio) have all executed. It now tells a reader the per-item field cannot be set on a plan, which is false.
- Scope: IN: delete that subsection (its heading, its paragraph, and the blank line separating the heading from the `## Blockers` paragraph above it: ten lines total, 22-31 at HEAD `61ef21d8`) from `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`. OUT: every other line of the release record (Summary, Blockers rule paragraph, metadata), any plan or backlog item, the executed plan `40it5e` and its review record and the `5ek188` research prompt (all three mention the note and are each correct as historical statements), migrating intent to per-plan fields (nothing is left to migrate: all four Sets executed and 0 of their 22 executed plans carries a `- Blocks-Release:` line to migrate to).
- Scope-Paths: .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: wxypal
- Set: staledocs
- Order: 3
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: fsme8o

## Workflow history
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-305 all FIXED. Premise re-measured and holds. Corrected the deletion from 9 lines to 10 (a stranded blank line would have been rewritten and rejected by end-of-file-fixer) and recorded that the plan's only validation, aw check releases, reads front matter only and is blind to the body it validates.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog wxypal: Delete the stale interim note from the 2.0.0 release record.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Remove the stale interim note so the release record states only its standing rule: blockers are declared by `- Blocks-Release:` on each item, and the record carries no prose blocker list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Baseline, delete, re-check

- [ ] E-01 Capture the baseline and re-derive the deletion precondition. Run `aw check releases --agent` and record its line. Then re-derive all four precondition properties, each as a PROPERTY and not against any count in this plan: (a) both blockers are done, `ls .aw/records/backlog/done/ | grep -E "vwios6|w6mqc0"` lists both files; (b) the setter exists, `aw ipd set --help | grep -- --blocks-release` prints a line; (c) NO plan of the four named Sets is live, checked across EVERY non-terminal disposition, not just `pending/` (`for d in pending reusable; do ls .aw/records/plans/$d 2>/dev/null | grep -E -- "-(execset|ipdgates|proclint|unifyfileio)-"; done` prints nothing; measured in review: `pending/` and `reusable/` are both empty of them, and `executed/` holds 6/9/1/6); (d) the note's own migration target is moot, i.e. no executed plan of those Sets carries a `- Blocks-Release:` line to migrate TO (`for s in execset ipdgates proclint unifyfileio; do grep -l "^- Blocks-Release:" .aw/records/plans/executed/*-$s-*.ipd.md 2>/dev/null; done` prints nothing; measured in review: 0 of 22). Note on (c)/(d): a bare `grep` that finds nothing exits 1, which is the PASS case here and aborts a `set -e` lane, so append `|| echo "none (pass)"` to each.
  - Depends on: none
  - Expected outcome: baseline check line recorded (at authoring: `"outcome":"conforms","exit":0`, one unrelated `check.collisions-not-checked` diagnostic). All four properties hold. GENUINE STOP CONDITION: property (a) or (c) fails, i.e. a blocker is not done or a named Set still has a live plan, because either would mean the note's stated precondition is NOT met and the deletion premise is false. Property (d) failing is NOT a stop: it would mean an executed plan does carry the gate, which only strengthens the case that the note is stale; record it and continue.
  - Execution state: pending
- [ ] E-02 Delete the subsection: the heading `### Interim: IPD sets that cannot yet carry the field (pending vwios6)` through the end of its paragraph (`...and delete this interim note.`), AND the blank line that separated the heading from the `## Blockers` paragraph above it, so no trailing blank line is left behind. Measured in review at HEAD `61ef21d8`: the file is 31 lines; keep lines 1-21 and delete lines 22-31 (TEN lines: the separating blank on 22, the heading on 23, and the paragraph through 31). Deleting only 23-31 leaves the file ending `...on each item).\n\n`, which `end-of-file-fixer` (`.pre-commit-config.yaml:31`, and note its `exclude` does NOT cover `.aw/records/`) rewrites and REJECTS the commit for; the retry must then re-stage the rewritten path. Treat the line numbers as a hint and anchor on the quoted strings. Leave the `## Blockers` rule paragraph byte-identical and end the file with exactly one trailing newline.
  - Depends on: E-01
  - Expected outcome: `grep -n "Interim\|vwios6\|w6mqc0" <release file>` returns nothing (exit 1; append `|| echo "absent (pass)"`); the `## Blockers` rule paragraph is unchanged; the file ends `...(single source of truth is the field on each item).\n` with no trailing blank line; `git diff --stat` shows exactly `10 deletions(-)` and 0 insertions.
  - Execution state: pending
- [ ] E-03 Re-run `aw check releases --agent` and `aw attention --check` and compare with the E-01 baseline. RECORD THE HONEST LIMIT rather than presenting these as proof of the edit: measured in review by driving `releases.validate_release` on the post-deletion text, the validator reads FRONT MATTER ONLY (`- Id:`, `- Status:`, `- Version:`; `agent_workflows/releases.py:91`) and returns `[]` for the original text, for the deleted text, AND for a text stripped to front matter alone. So `conforms` here proves only that the front matter was not damaged; it CANNOT detect whether the right body lines went or whether the `## Blockers` paragraph survived. The actual proof of this plan's change is the diff in V-02, read by a human. State this in the V-03 evidence rather than letting a green check stand in for it.
  - Depends on: E-02
  - Expected outcome: `aw check releases --agent` still reports `"outcome":"conforms"` with exit 0 and the SAME diagnostic set as E-01 (the unrelated `check.collisions-not-checked`); `aw attention --check` exit status unchanged (measured in review pre-edit: rc=0). Both are NO-REGRESSION checks, not confirmations of the deletion.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Release records live under `.aw/records/releases/`; the single source of truth for blockers is the `- Blocks-Release:` field on each item (AGENTS.md "Release gates (Blocks-Release)").
- The release record is an internal artifact, not user-facing prose. So the no-em-dash rule does NOT apply here (AGENTS.md scopes it to user-facing prose the agent authors), and in any case this plan only DELETES lines.
- Commit via `aw commit fsme8o -- <release file>`; never push.
- `aw releases show f33nrj` is the LIVE view this deletion defers to, and it works: driven in review, it prints the record plus `release-blockers (218)` read from the per-item field. That is what makes removing a nine-line prose note safe rather than a loss of information (added in review, F-6).
- The `.aw/records/releases/README.md` says "Managed by `aw` (do not hand-edit status/history; use the aw verbs)". This deletion is in bounds: it touches neither status nor history, only body prose, and there is deliberately no `aw releases` verb that edits a record body (`aw releases` exposes `list`/`show`/`new` only, driven in review), so a hand edit is the only available route (added in review, F-7).
- Sibling scope, checked because three `staledocs` plans are pending at once: Order 01 (`3rsdbj`) declares six docs, Order 02 (`xts8ux`) declares `agent_workflows/work_cmd.py`, and neither names this release record, so the fences are DISJOINT. This is a note for a HAND execution only; the runner isolates each item in its own worktree, so it is not a runtime hazard.

## Findings

| # | Evidence (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | release file `### Interim: IPD sets that cannot yet carry the field (pending vwios6)` (~:23-31, the file's last lines) | Confirmed at the brief's cited range. Re-measured in review: the subsection body is 23-31, but the removal is TEN lines (22-31) because the separating blank on 22 must go too, see F-8. |
| F-2 | `.aw/records/backlog/done/20260824-vwios6-01-...backlog.md`, `.aw/records/backlog/done/20260824-w6mqc0-01-...backlog.md` | Both blockers are done. Confirmed. |
| F-3 | `aw ipd set --help` lists `--blocks-release BLOCKS_RELEASE` | Setter exists. Confirmed. |
| F-4 | pending/ holds no plan for execset, ipdgates, proclint, unifyfileio; executed/ holds 6, 9, 1, 6 respectively | All four Sets executed; nothing to migrate. Widened in review: `reusable/`, `superseded/` and `not-executed/` hold none of them either, so no live plan of those Sets exists in ANY disposition. These are LIVE-ARTIFACT counts; E-01 re-derives the PROPERTY and does not compare against 6/9/1/6. |
| F-5 | `aw check releases --agent` at authoring: `"outcome":"conforms","exit":0`, one diagnostic `check.collisions-not-checked` | Baseline. That diagnostic is unrelated to this file and is expected to persist. SEE F-9: this check cannot see the body, so it is a no-regression signal only. |
| F-6 | `aw releases show f33nrj` driven in review: prints the record plus `release-blockers (218)`, e.g. `dhuape backlog graduated medium ...` | THE INFORMATION IS NOT LOST BY DELETING THE NOTE. The live per-item view the record's own rule points at exists and works, listing 218 blockers from the field. So the deletion removes a stale prose duplicate, not the only record of intent. This is the positive evidence the authored plan asserted by reference but never drove. |
| F-7 | `.aw/records/releases/README.md`: "Managed by `aw` (do not hand-edit status/history; use the aw verbs)"; `aw releases --help` exposes `list`/`show`/`new` only | THE HAND EDIT IS IN BOUNDS AND IS THE ONLY ROUTE. The README's prohibition is scoped to status and history, which this edit does not touch, and no `aw` verb edits a release-record BODY. Checked because a plan hand-editing an `aw`-managed record should say why that is allowed rather than leave a reviewer to wonder. |
| F-8 | measured: the file is 31 lines; line 22 is `\n`, 23 is the heading; keeping 1-21 ends `...on each item).\n`, keeping 1-22 ends `...on each item).\n\n`; `.pre-commit-config.yaml:31` runs `end-of-file-fixer` whose `exclude` covers `^(\.agents/docs/research/\|\.aw/records/docs/research/\|\.aw/system/)` and NOT `.aw/records/releases/` | A LITERAL READING OF THE AUTHORED E-02 WOULD HAVE BOUNCED THE COMMIT. "Delete from the heading through the end of its paragraph" removes 23-31 and strands the blank on 22, leaving a trailing blank line that `end-of-file-fixer` rewrites and then REJECTS the commit over, costing a re-stage round trip inside a lane. The instruction now names the blank line, the 10-line count, and the exact expected file ending. |
| F-9 | drove `releases.validate_release` (`agent_workflows/releases.py:91`) on three variants of this file: original -> `[]`, subsection deleted -> `[]`, stripped to front matter alone -> `[]` | THE PLAN'S ONLY VALIDATION IS BLIND TO THE CHANGE IT VALIDATES. The validator checks `- Id:`, `- Status:` and `- Version:` and nothing else, so `conforms` is returned even for a file whose entire body including the `## Blockers` rule has been deleted. `aw check releases` therefore proves only that the front matter survived; it can neither confirm the right lines went nor catch collateral damage to the `## Blockers` paragraph. The authored plan presented it as the validation. E-03 and V-03 now state this limit explicitly and the diff in V-02 is named as the actual proof. |

## Proposed changes (ordered, validatable)

1. E-01 baseline and precondition.
2. E-02 delete the subsection.
3. E-03 re-check.

## Deferred / out of scope (with reason)

none

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

No new test. The maintainer's standing rule is to test OUTCOMES only; deleting prose from a record has no behavior to test, and a test pinning the record's text would be a source-text pin (the class of test sibling Set `srcguard` is deleting). Confirmed in review that no test references this file or this note: nothing under `tests/` greps for "Interim" or "cannot yet carry", and the only `2-0-0.release.md` occurrences in `tests/` are synthetic fixtures under a different id6, each writing the string `20260101-aaaaaa-01-aaaaaa-2-0-0.release.md` into a temp dir (`tests/test_releases.py` ~:126 and `tests/test_releases_cli.py` ~:79), so the suite is a genuine no-op here.

HONEST LIMIT ON THE VALIDATION, added in review (F-9), because the authored plan presented a check that cannot see this change as the validation. `aw check releases --agent` validates FRONT MATTER ONLY: driving `releases.validate_release` (`agent_workflows/releases.py:91`) returns `[]` for the original text, for the correctly deleted text, and for a text stripped to front matter alone. So a green check proves the front matter was not damaged and NOTHING about the body. The same is true of `aw attention --check`, which reads the per-item field and never this record's prose. THE ACTUAL PROOF IS THE DIFF: V-02's `git diff` read by a human, showing exactly ten deletions, zero insertions, and the `## Blockers` paragraph untouched. The two checks are recorded as no-regression signals, not as confirmations.

## Spec / documentation sync

No spec or user-facing doc requires an update, verified rather than asserted: a repository-wide grep for "Interim: IPD sets" / "cannot yet carry the field" finds the note itself plus four INTERNAL references that must each be left alone, and the reason differs per class.

- the executed plan `40it5e` (`20260921-rununify-12-40it5e-verify-the-rununify-set-...ipd.md`, at "NOTED BUT NOT OWNED HERE: the 2.0.0 release record's ..." and in finding F-07) and its review record (finding PR-005) REPORT the note as stale (that plan is why backlog `wxypal` exists, and it was explicitly barred from editing this record). An executed plan MUST NOT be edited in place (AGENTS.md), and these are historically true statements about what was found then.
- the backlog item `wxypal` (`20260923-wxypal-01-wxypal-stale-release-interim-note.backlog.md`, its `- Summary:` bullet) is this plan's own source item; the gate settles its status after execution and that Summary is a true description of the work.
- the research prompt `5ek188` (`20260830-humanchk-00-5ek188-human-owned-task-tracking.research-prompt.md`, numbered evidence item 3, "A release record contains a prose paragraph titled ...") cites the note as evidence in a research prompt about human-owned task tracking ("A human TODO living inside a release record, in prose, in acknowledged violation of the system's own single-source rule"). It is a POINT-IN-TIME observation supporting a research question, and deleting the note does not falsify it; a research prompt is not a live contract. Left alone deliberately.

So the deletion leaves no dangling reference that asserts the note currently exists as a live rule.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full `aw check releases --agent` line (expected `"outcome":"conforms","exit":0`) AND all four precondition commands' output: both backlog files listed under `done/`; the `--blocks-release` help line; the live-plan sweep across `pending` and `reusable` printing `none (pass)` for each; and the migration-target sweep over `executed/` printing `none (pass)`. Do NOT compare any count against a number in this plan: state the PROPERTY that held (no live plan of the four Sets in any non-terminal disposition; no executed plan of those Sets carrying a `- Blocks-Release:` line to migrate to). If a count in the Findings table disagrees with what you measure, the plan's number is stale context and yours is the truth; record both.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02. THIS IS THE PLAN'S ONLY REAL PROOF (see F-9), so it carries the burden the two checks cannot.
  - Required evidence: paste the FULL `git diff -- .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` and confirm from it, explicitly, all four of: (1) every removed line belongs to the interim subsection or is the blank line that preceded its heading; (2) there are ZERO added lines; (3) the `## Blockers` heading and its rule paragraph appear nowhere in the diff, i.e. they were not touched; (4) the diff shows no trailing-blank-line artifact. Also paste `git diff --stat` (expect `10 deletions(-)`, 0 insertions), `grep -n "Interim\|vwios6\|w6mqc0" <file> || echo "absent (pass)"` printing the pass line, and `tail -c 90 <file> | od -c | tail -3` showing the file ends `on each item).\n` with no second newline. A diff showing 9 deletions is a FAILED validation: it means the stranded blank line is still there and `end-of-file-fixer` will reject the commit.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the post-edit `aw check releases --agent` line (expected `"outcome":"conforms","exit":0`, same diagnostic set as V-01) and `aw attention --check; echo rc=$?` with the same rc as a pre-edit run. THEN state, in your own words, the limit these two do NOT cover: `releases.validate_release` reads front matter only and returns `[]` even for a body deleted entirely (measured in review on three variants), so this item proves NO REGRESSION and proves nothing about the deletion itself, which V-02 owns. A V-03 that presents `conforms` as confirmation of the edit is a FAILED validation even when the command output is genuine.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: deletion of TEN lines from the 2.0.0 release record (the interim subsection's heading and paragraph, lines 23-31, plus the blank line on 22 that preceded the heading). Nothing is added. No code, no spec, no test, no other record. Corrected in review from "9 lines": the ninth-line reading strands a trailing blank that `end-of-file-fixer` rejects the commit over (F-8).

WHAT IS NOT LOST, so the approver can judge the deletion rather than trust it. The note's content was a pointer to work that is finished: both blockers it waited on (`vwios6`, `w6mqc0`) are done, the `aw ipd set --blocks-release` setter it said did not exist does exist, and all four Sets it named as intended blockers (`execset`, `ipdgates`, `proclint`, `unifyfileio`) have executed with no live plan remaining in any disposition. There is also nothing left to migrate: 0 of those 22 executed plans carries a `- Blocks-Release:` line, so the "migrate this intent to the per-item field" instruction has no target. The live view the record's own rule defers to works: `aw releases show f33nrj` lists 218 release-blockers from the per-item field (F-6).

WHAT THE VALIDATION DOES NOT PROVE, stated plainly because the authored plan implied otherwise. `aw check releases` reads this record's FRONT MATTER ONLY and returns clean even for a file whose entire body has been deleted (measured on three variants, F-9). So the green check is a no-regression signal, and the approval rests on the V-02 DIFF being read, not on a passing command.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the release file only. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. In particular do NOT edit the executed plan `40it5e`, its review record, or the `5ek188` research prompt, all of which mention this note and are each correct as historical statements (see Spec / documentation sync). Genuine stop condition: E-01 property (a) or (c) fails, i.e. a blocker is not done or a named Set still has a live plan, since either falsifies the deletion premise. Property (d) failing is NOT a stop.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`. A DIFF IS THE ONLY PROOF HERE: a passing `aw check releases` does not substitute for it, and V-03 must say so.

Commit ONLY the release file through `aw commit fsme8o -- .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`; never `git add -A`, never push. If `end-of-file-fixer` rewrites the file and rejects (which E-02 is written to avoid), re-stage the rewritten path and retry; `aw commit` handles that retry itself. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize fsme8o --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane).

THEN CLOSE THE BACKLOG ITEM, and the ORDER is safe here for a reason worth stating. Set `wxypal` done with `--evidence` citing the executed plan. Unlike sibling `3rsdbj`, this close does NOT fail closed while the plan is pending: driven in review, `evaluate_blocking_close(repo, <wxypal>, "done")` returns `legitimate=True`, severity `ok`, reason "no release gate to preserve", path `DE-GATED`, because `wxypal` carries no `- Blocks-Release:` at all. Closing it after execution is still the right order; the point is that no gate handoff is involved, so neither this plan nor the item needs a `Blocks-Release` field. That is correct rather than an omission: `- Work-Kind: chore` is outside the repository's gating set (`bug`), so AGENTS.md's live-bug gate does not apply.
