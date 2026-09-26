# IPD: Delete the stale interim Blocks-Release note from the 2.0.0 release record

- Date: 2026-09-26
- Kind: child
- Concern: The 2.0.0 release record carries a subsection "### Interim: IPD sets that cannot yet carry the field (pending vwios6)" that documents a TEMPORARY EXCEPTION to the record's own no-prose-blocker-list rule. Its stated deletion condition is met (backlog `vwios6` and `w6mqc0` are both done; `aw ipd set --blocks-release` exists) and the four Sets it names (execset, ipdgates, proclint, unifyfileio) have all executed. It now tells a reader the per-item field cannot be set on a plan, which is false.
- Scope: IN: delete that subsection (heading plus its paragraph) from `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`. OUT: every other line of the release record (Summary, Blockers rule paragraph, metadata), any plan or backlog item, migrating intent to per-plan fields (nothing is left to migrate: all four Sets executed).
- Scope-Paths: .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: wxypal
- Set: staledocs
- Order: 3
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: fsme8o

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog wxypal: Delete the stale interim note from the 2.0.0 release record.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Remove the stale interim note so the release record states only its standing rule: blockers are declared by `- Blocks-Release:` on each item, and the record carries no prose blocker list.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Baseline, delete, re-check

- [ ] E-01 Capture the baseline: run `aw check releases --agent` and re-confirm the deletion precondition: `ls .aw/records/backlog/done/ | grep -E "vwios6|w6mqc0"` lists both, `aw ipd set --help | grep -- --blocks-release` shows the setter, and `ls .aw/records/plans/pending | grep -E -- "-(execset|ipdgates|proclint|unifyfileio)-"` is empty.
  - Depends on: none
  - Expected outcome: baseline check outcome recorded (at authoring: `"outcome":"conforms","exit":0`); precondition holds. If any of the four Sets has a pending plan or either backlog item is not done, stop and report.
  - Execution state: pending
- [ ] E-02 Delete the subsection starting at the heading "### Interim: IPD sets that cannot yet carry the field (pending vwios6)" through the end of its paragraph ("...and delete this interim note."). Leave the "## Blockers" paragraph above it intact and keep the file ending with a single trailing newline.
  - Depends on: E-01
  - Expected outcome: `grep -n "Interim\|vwios6\|w6mqc0" <release file>` returns nothing; the "## Blockers" rule paragraph is unchanged.
  - Execution state: pending
- [ ] E-03 Re-run `aw check releases --agent` and `aw attention --check` and compare with the E-01 baseline.
  - Depends on: E-02
  - Expected outcome: `aw check releases --agent` still reports `"outcome":"conforms"` with exit 0 and no new diagnostic; `aw attention --check` exit status unchanged from before the edit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Release records live under `.aw/records/releases/`; the single source of truth for blockers is the `- Blocks-Release:` field on each item (AGENTS.md "Release gates (Blocks-Release)").
- The release record is an internal artifact, not user-facing prose.
- Commit via `aw commit fsme8o -- <release file>`; never push.

## Findings

| # | Evidence (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | release file "### Interim: IPD sets that cannot yet carry the field (pending vwios6)" (~:23-31, the file's last lines) | Confirmed at the brief's cited range. |
| F-2 | `.aw/records/backlog/done/20260824-vwios6-01-...backlog.md`, `.aw/records/backlog/done/20260824-w6mqc0-01-...backlog.md` | Both blockers are done. Confirmed. |
| F-3 | `aw ipd set --help` lists `--blocks-release BLOCKS_RELEASE` | Setter exists. Confirmed. |
| F-4 | pending/ holds no plan for execset, ipdgates, proclint, unifyfileio; executed/ holds 6, 9, 1, 6 respectively | All four Sets executed; nothing to migrate. |
| F-5 | `aw check releases --agent` at authoring: `"outcome":"conforms","exit":0`, one diagnostic `check.collisions-not-checked` | Baseline. That diagnostic is unrelated to this file and is expected to persist. |

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

No new test. The maintainer's standing rule is to test OUTCOMES only; deleting prose from a record has no behavior to test, and a test pinning the record's text would be a source-text pin. Validation is `aw check releases --agent` conforming before and after, plus `aw attention --check` unchanged.

## Spec / documentation sync

N/A: no spec or user doc references this interim note.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full `aw check releases --agent` line (expected `"outcome":"conforms","exit":0`) and the three precondition commands' output (both backlog files listed under `done/`, the `--blocks-release` help line, an empty pending grep).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` showing only the subsection's lines removed, and `grep -n "Interim\|vwios6\|w6mqc0" <file>` returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the post-edit `aw check releases --agent` line (expected `"outcome":"conforms","exit":0`, same diagnostics as V-01) and `aw attention --check; echo rc=$?` with the same rc as a pre-edit run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: deletion of one stale subsection (9 lines) from the 2.0.0 release record.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the release file only. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. Genuine stop condition: the E-01 precondition fails (a named Set still pending, or a blocker not done).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`.

Commit ONLY the release file through `aw commit fsme8o -- .aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize fsme8o --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). Then set backlog `wxypal` done citing the executed plan.
