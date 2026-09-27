# Review findings: plan fsme8o

- Subject-Id: fsme8o
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--porcelain` was empty, so the plan was committed and unmodified, and the lane input under
`.aw/state/lane-inputs/rev-5/` is byte-identical to the tracked file (`diff` reported no
difference).

THE PREMISE IS CORRECT AND I RE-MEASURED EVERY PART OF IT RATHER THAN TRUSTING THE FINDINGS TABLE.
The note exists at the cited range (the file is 31 lines; the heading `### Interim: IPD sets that
cannot yet carry the field (pending vwios6)` is line 23 and its paragraph runs to 31). Both blockers
it waits on are done: `.aw/records/backlog/done/20260824-vwios6-01-vwios6-ipd-set-blocks-release-parity.backlog.md`
and `...-w6mqc0-ipd-set-approved-writes-approval-field.backlog.md`. The setter it says does not exist
does exist: `aw ipd set --help` prints `--blocks-release BLOCKS_RELEASE`. And the four Sets it names
are gone from every non-terminal disposition, which I checked more widely than the plan did: `pending/`,
`reusable/`, `superseded/` and `not-executed/` hold no `execset`, `ipdgates`, `proclint` or
`unifyfileio` plan, while `executed/` holds 6, 9, 1 and 6. So the note's stated deletion condition is
met and its subject is gone. The plan is right, and the work it proposes is correct.

**THE PLAN'S ONLY VALIDATION IS BLIND TO THE CHANGE IT VALIDATES.** This is the finding that justifies
the review. The plan's "Required tests / validation" section rests entirely on `aw check releases
--agent` conforming before and after. I drove the validator directly on three variants of this file:
the original returns `[]`, the correctly deleted text returns `[]`, and a text STRIPPED TO FRONT
MATTER ALONE, with the Summary, the `## Blockers` rule and everything else removed, ALSO returns `[]`.
`releases.validate_release` checks `- Id:`, `- Status:` and `- Version:` and nothing else. So a green
`aw check releases` would have been reported as validation of a body edit it cannot see, and it would
equally have stayed green if the executor had destroyed the `## Blockers` rule paragraph the plan is
meant to preserve. `aw attention --check` is no better: it reads the per-item `Blocks-Release` field
and never this record's prose. The remedy is not a new test (a test pinning this record's text would be
exactly the source-text pin sibling Set `srcguard` is deleting, and the maintainer's standing rule is
to test outcomes); it is HONESTY about what proves what. The diff is the proof, so V-02 now carries
that burden with four explicit confirmations, and V-03 must state the limit in the executor's own words
rather than presenting `conforms` as confirmation.

**A LITERAL READING OF THE AUTHORED E-02 WOULD HAVE BOUNCED THE COMMIT.** "Delete the subsection
starting at the heading ... through the end of its paragraph" removes lines 23-31 and strands the blank
line on 22, leaving the file ending `...on each item).\n\n`. `.pre-commit-config.yaml` runs
`end-of-file-fixer`, and its `exclude` covers `^(\.agents/docs/research/|\.aw/records/docs/research/|\.aw/system/)`
but NOT `.aw/records/releases/`, so the hook rewrites the file and REJECTS the commit, and the retry must
re-stage the rewritten path. The plan even asked for the right END STATE ("keep the file ending with a
single trailing newline") while its own instruction produced a different one, which is the kind of
internal contradiction an executor resolves by guessing. E-02 now names the blank line, states TEN lines
and 22-31, gives the exact expected file ending, and V-02 makes a 9-deletion diff a FAILED validation.

ON THE THING THE PLAN ASSERTED BUT NEVER DROVE, which turned out to support it. The whole justification
for deleting a prose blocker list is that the per-item field is the single source of truth. That is a
claim about a live mechanism, so I ran it: `aw releases show f33nrj` prints the record and
`release-blockers (218)` read from the field. The information is genuinely not lost, and the approver can
now see that from the plan instead of taking it on faith. I also checked the authorization question the
plan skipped: `.aw/records/releases/README.md` says "Managed by `aw` (do not hand-edit status/history;
use the aw verbs)", and `aw releases --help` exposes `list`/`show`/`new` only. The hand edit is in
bounds (it touches neither status nor history) AND it is the only available route (no verb edits a
record body). Worth recording because a plan hand-editing an `aw`-managed record should say why that is
allowed rather than leave a reviewer to wonder whether it is a violation.

ON THE DANGLING-REFERENCE QUESTION, which the plan answered with a bare "N/A". A repository-wide grep
for the note's distinctive strings finds four internal references besides the note itself, and they are
NOT interchangeable. The executed plan `40it5e` and its review record report the note as stale (that
plan is why backlog `wxypal` exists, and it was explicitly barred from editing this record); an executed
plan must not be edited in place, and both statements are historically true. Backlog `wxypal` is this
plan's own source item. The interesting one is the research prompt `5ek188`, which cites the note as
numbered evidence item 3 in a research question about human-owned task tracking, quoting it as "A human
TODO living inside a release record, in prose, in acknowledged violation of the system's own
single-source rule". Deleting the note does not falsify that observation and a research prompt is not a
live contract, so it is correctly left alone, but a reader who finds it later should not have to
re-derive that judgement. All four are now enumerated with the reason each is untouched, and the scope
fence names them so an executor does not tidy them.

ON THE GREP EXIT CODE, the same class of defect my sibling review caught on `3rsdbj`. Three of this
plan's checks are bare `grep` invocations whose PASS case is "no output", which exits 1 and aborts a
`set -e` step in a runner lane. Verified here: the pending-plan precondition grep returns rc=1 today
(the pass case) and the post-deletion note grep will too. Each now carries `|| echo "... (pass)"`.

ON THE BACKLOG CLOSE, where this plan differs from its sibling in a way worth recording rather than
assuming. `3rsdbj`'s close FAILS CLOSED while that plan is pending, because its item carries a release
gate handed off to an unexecuted carrier. I drove the same predicate here: `evaluate_blocking_close(repo,
<wxypal>, "done")` returns `legitimate=True`, severity `ok`, reason "no release gate to preserve", path
`DE-GATED`, because `wxypal` carries no `- Blocks-Release:` at all. The gate now states that measured
result. I also checked that the ABSENCE of a gate is correct rather than an omission: AGENTS.md gates
LIVE items whose `- Work-Kind:` is in the repository's gating set (default `bug`), and both the item and
the plan are `chore`. And I confirmed the plan's own field links are sound:
`releases.check_from_backlog` and `releases.check_blocks_release` both report no drift for `fsme8o`, so
`- From-Backlog: wxypal` resolves.

SIBLING SAFETY, checked because three `staledocs` plans are pending at once. Order 01 (`3rsdbj`) declares
six docs, Order 02 (`xts8ux`) declares `agent_workflows/work_cmd.py`, Order 03 (this plan) declares one
release record. The fences are DISJOINT. Recorded as a note for a HAND execution and explicitly flagged
as NOT a runtime hazard, since the runner isolates each item in its own worktree; the repository's
guidance is emphatic that file overlap is not a reason to warn a maintainer about a queue.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | UNDER-SCOPE | E. verification (a check blind to its subject) | drove `releases.validate_release` (`agent_workflows/releases.py`, `def validate_release`) on three variants: original -> `[]`, subsection deleted -> `[]`, stripped to front matter alone -> `[]`; the function reads only `- Id:`, `- Status:`, `- Version:` | **THE PLAN'S ONLY VALIDATION CANNOT SEE THE BODY IT VALIDATES.** "Required tests / validation" rested on `aw check releases --agent` conforming before and after, but the validator checks front matter and returns clean even for a file whose entire body, including the `## Blockers` rule this plan must preserve, has been deleted. A green check would have been reported as proof of a prose deletion it is structurally incapable of observing, and would equally have masked collateral damage. `aw attention --check` shares the limit (it reads the per-item field, never this record's prose). | C:Low; U:Low; S:Low; F:Medium (a wrong edit validates clean); Overall:Low | FIXED | Recorded as F-9. NOT closed by adding a test: pinning this record's text would be the source-text pin `srcguard` is removing and the maintainer's rule is to test outcomes. Closed by honesty instead: E-03 and the Required-tests section now state the measured limit, V-02 is designated the plan's only real proof and carries four explicit diff confirmations (only interim lines removed, zero insertions, `## Blockers` absent from the diff, no trailing-blank artifact), and V-03 requires the executor to state the limit in their own words, making a V-03 that presents `conforms` as confirmation a FAILED validation. |
| PR-302 | MEDIUM | IN-SCOPE | A. correctness; G. executability | file is 31 lines, line 22 is `\n` and 23 is the heading; keeping 1-22 ends `...on each item).\n\n` while keeping 1-21 ends `...on each item).\n`; `.pre-commit-config.yaml` `- id: end-of-file-fixer` with `exclude: '^(\.agents/docs/research/\|\.aw/records/docs/research/\|\.aw/system/)'`, which does not cover `.aw/records/releases/` | **THE AUTHORED DELETION INSTRUCTION WOULD HAVE BOUNCED THE COMMIT AND CONTRADICTED ITS OWN EXPECTED OUTCOME.** "From the heading through the end of its paragraph" removes 23-31 and strands the blank on 22, so the file ends with a trailing blank line; `end-of-file-fixer` then rewrites it and REJECTS the commit, forcing a re-stage round trip inside a lane. The same item asked for "a single trailing newline", so the instruction and its expected outcome disagreed and the executor would have had to guess. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-8. E-02 now names the separating blank line explicitly, states TEN lines and the range 22-31 as a hint anchored on quoted strings, cites the hook and its non-covering `exclude`, and gives the exact expected ending. Expected outcome adds `git diff --stat` showing `10 deletions(-)`, 0 insertions. V-02 makes a 9-deletion diff an explicit FAILED validation and requires an `od -c` tail proving no second newline. The line count in the Concern, Scope and gate was corrected from 9 to 10. |
| PR-303 | LOW | UNDER-SCOPE | F. honest documentation; C. architecture | `aw releases show f33nrj` driven: prints the record plus `release-blockers (218)`; `.aw/records/releases/README.md` "Managed by `aw` (do not hand-edit status/history; use the aw verbs)"; `aw releases --help` exposes `list`/`show`/`new` only | **THE TWO CLAIMS THAT MAKE THE DELETION SAFE WERE ASSERTED AND NEVER DRIVEN.** The plan justified removing a prose blocker list by pointing at the per-item field as the single source of truth without demonstrating that the live view works, and it hand-edits an `aw`-MANAGED record without addressing the README's own "do not hand-edit" line. Both check out (218 blockers listed from the field; the prohibition is scoped to status and history, and no verb edits a record body so a hand edit is the only route), but an approver should not have to re-derive either. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-6 and F-7 with the driven output, plus two Project-conventions bullets. The gate gained a "WHAT IS NOT LOST" paragraph so the approver can judge the deletion rather than trust it. |
| PR-304 | LOW | UNDER-SCOPE | G. executability (dangling references) | repo-wide grep for "Interim: IPD sets" / "cannot yet carry the field": the note, executed plan `40it5e` (two findings plus a "NOTED BUT NOT OWNED HERE" paragraph), its review record (PR-005), backlog `wxypal` Summary, and research prompt `5ek188` numbered evidence item 3 | **"N/A: no spec or user doc references this interim note" WAS TRUE BUT INCOMPLETE, AND THE OMITTED CASES ARE THE ONES NEEDING JUDGEMENT.** Four internal artifacts reference the note and they are not interchangeable: two live in an EXECUTED plan and its review record (which must not be edited in place and are historically true), one is this plan's own source item, and one is a research prompt citing the note as evidence for a design question. The last is the only genuinely debatable case, and an executor finding it mid-run with no guidance might either "fix" the research prompt or stop. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Spec/documentation-sync section now enumerates all four with a per-class reason for leaving each alone, and explains why deleting the note does not falsify the research prompt's point-in-time observation. The scope fence names the three out-of-fence files so an executor does not tidy them. |
| PR-305 | LOW | IN-SCOPE | E. verification (checks that abort on success); A. live-artifact counts | pending-plan precondition grep returns rc=1 today, which is its PASS case; `printf 'clean\n' \| grep -n "Interim"` -> rc 1; authored E-01 checked only `pending/` and compared against the live counts 6/9/1/6 | **THREE CHECKS EXIT NONZERO WHEN THEY PASS, AND THE PRECONDITION WAS NARROWER THAN ITS CLAIM.** A bare `grep` finding nothing returns 1, which under `set -e` in a runner lane aborts the step on the success path. Separately, E-01 proved "no pending plan" while the note's premise needs "no LIVE plan in any non-terminal disposition", and it quoted drifting live-artifact counts inside the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each grep gained `\|\| echo "... (pass)"`. E-01 was restructured into four named PROPERTIES re-derived at execution time, widened to sweep `pending` and `reusable`, and given a fourth property (no executed plan of those Sets carries a `- Blocks-Release:` line to migrate to; measured 0 of 22, which independently confirms nothing is left to migrate). V-01 forbids comparing any measured count against a number in the plan and says the plan's number is stale context if they disagree. The stop condition was sharpened to properties (a) and (c) only, with (d) explicitly not a stop. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `aw check releases` cannot see the body this plan edits (PR-301). Add a real check, or make the plan honest about the gap? | MAKE IT HONEST: designate the V-02 diff as the only proof, state the validator's measured limit in E-03, Required-tests and the gate, and require the executor to restate it in V-03. | (a) Add a test asserting the note's absence from the record: rejected, that is precisely the production-text pin the maintainer ruled out on 2026-09-26 and that sibling Set `srcguard` is deleting 37 instances of; it would also go red on any future record that legitimately quotes the phrase. (b) Extend `validate_release` to check body structure: rejected, a production code change to satisfy one prose deletion, far outside a fence declaring one release record, and nobody has asked for a body schema. (c) Leave the validation claim as authored: rejected outright, it presents a check that returns clean for a fully-deleted body as proof of a nine-line prose edit. | Drove `releases.validate_release` on three variants (original, correctly deleted, front-matter-only): all three return `[]`. The function's own body reads `- Id:`, `- Status:`, `- Version:` and returns. So the limit is structural, not incidental. | yes |
| D-2 | Is the removal 9 lines or 10 (PR-302)? | TEN: lines 22-31, including the blank line that separated the heading from the `## Blockers` paragraph. | (a) Nine (23-31), the literal reading of the authored instruction: rejected, it strands a trailing blank line that `end-of-file-fixer` rewrites and rejects the commit over, and it contradicts the item's own stated expected outcome of a single trailing newline. (b) Leave it ambiguous and let the executor sort it out: rejected, an ambiguity whose two readings differ by a commit rejection is exactly what a review is for. | Measured the file at 31 lines with `\n` on 22 and the heading on 23; computed both endings (`...item).\n` vs `...item).\n\n`); read `.pre-commit-config.yaml`'s `end-of-file-fixer` `exclude` and confirmed it does not cover `.aw/records/releases/`. | yes |
| D-3 | The research prompt `5ek188` cites this note as evidence. Update it when the note goes? | LEAVE IT UNTOUCHED, and record why in the plan. | (a) Edit the prompt to note the paragraph was since deleted: rejected, it is a POINT-IN-TIME observation supporting a research question, it was true when written, and deleting the note does not falsify "a release record contained a human TODO in prose". A research prompt is not a live contract. (b) Say nothing: rejected, an executor grepping for the note mid-run will find it and needs to know it is deliberate, otherwise they either edit an out-of-fence file or stop. | AGENTS.md treats research records as durable reference immortalizing analysis relied on for a decision, not as a live rule surface; the prompt's own framing is a numbered list of observed evidence. The executed plan `40it5e` is a stronger case of the same principle and is additionally protected by the no-edits-to-executed-plans rule. | yes |
| D-4 | Does the absence of `- Blocks-Release:` on this plan and on backlog `wxypal` violate the release-gate policy? | NO, it is correct; record the measured close verdict instead of adding a field. | (a) Add `Blocks-Release: next` to match sibling `3rsdbj`: rejected, that sibling inherits a gate from a `bug`-kind item (`sm0vgn`); this one descends from a `chore` and inventing a gate would falsely claim the 2.0.0 release cannot ship without a nine-line prose deletion. (b) Say nothing about the close: rejected, the sibling's close FAILS CLOSED while pending and a reader comparing the two plans would reasonably expect the same trap here. | AGENTS.md gates LIVE items whose `- Work-Kind:` is in the gating set (default `bug`); both item and plan are `chore`. Drove `evaluate_blocking_close(repo, <wxypal>, "done")`: `legitimate=True`, `ok`, "no release gate to preserve", path `DE-GATED`. Also drove `releases.check_from_backlog` and `check_blocks_release`: no drift for `fsme8o`. | yes |

### Deferred and open

- (none). All five findings were FIXED. No deferral was taken on the Fix Bar: nothing reached
  Medium-High or High Remediation Risk, and no finding reached the repository's `HIGH` escalation
  threshold, so no `- Blocking: yes` question was owed. The plan carries no open questions and needed
  none: every question this review raised was answerable from the repository by driving the code.
- No `Reversible: no` decision was made. All four decisions are plan-text or triage choices on an
  unexecuted plan, each undoable by editing the plan. The one decision that touches something
  irreversible in principle (D-3, whether a record gets edited) resolves toward NOT editing, which is
  the reversible direction.
- The underlying work is correct and I am not carrying anything to a new backlog item. PR-301 is worth
  being precise about: what was FIXED is the plan's dishonesty about its validation, not the validator.
  `releases.validate_release` still cannot see a release record's body after this plan executes, and
  that is a defensible design (a release record is a thin ship-gate anchor, per its README) rather than
  a defect I am papering over. If a future plan wants body-level validation of release records, that is
  a new design question, not this plan's debt.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified that the note's
stated deletion condition is met and that removing it loses no live information; I did NOT verify that
the maintainer still wants those four Sets' release-blocker intent forgotten entirely. The note recorded
an INTENT that was never migrated to any field (measured: 0 of the 22 executed plans carries
`Blocks-Release`), so deleting it deletes the last written trace of "these four Sets were intended 2.0.0
blockers". I judged that harmless because all four have executed, so the intent is satisfied rather than
lost, but a maintainer who disagrees would want that history preserved somewhere and this is the moment
to say so. SECOND, I did not run the suite: this review changed no code, the plan changes no code, and I
confirmed instead that nothing under `tests/` references this file or the note (the only
`2-0-0.release.md` hits are synthetic fixtures under id6 `aaaaaa`). THIRD, my dangling-reference sweep
matched two distinctive phrases across `*.md` and `*.py`; a fifth reference paraphrasing the note without
either phrase would have been missed. FOURTH, the line numbers I recorded (31 lines, blank on 22, heading
on 23) were measured at HEAD `61ef21d8` and the plan now instructs anchoring on quoted strings with the
numbers as hints, so drift degrades to a hint mismatch rather than a wrong deletion.
