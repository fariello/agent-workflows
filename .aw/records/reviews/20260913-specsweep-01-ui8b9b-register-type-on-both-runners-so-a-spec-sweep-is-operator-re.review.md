# Review: register --type on both runners so a spec sweep is operator-reachable, child ui8b9b (Set specsweep)

- Subject-Id: ui8b9b
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2674c250`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review. Both checkpoints conform after the revisions with no advisories; note
one of my own first-pass edits tripped the `IPD-Z602` conceptual-density advisory by lengthening E-01's
action text, and I moved that prose into a sub-bullet rather than leaving an advisory the author did not
earn. The `[blocking]` marker the linter shows is the release gate (`- Blocks-Release: next`), not an
open question.

DISCLOSURE: same repository and same model family as the author, so this is close to a self-review and
worth less than an independent one. Its value rests on what was DRIVEN. Measured here: the shipped sweep
CALLED for the spec type rather than read about; all four named specs' current statuses read from disk
and the predicate evaluated against them; the whole specs tree grepped for `to-review`; both hosts'
subparsers enumerated by walking `build_parser()`; the dispatch table dumped; all three code citations
opened at their exact lines; the flag registry row and the pin test read; `6m4kow`'s front matter and
history read; `aw check --agent` run and filtered; the sibling plan located; and `aw find specs --status`
re-exercised against a valid and an invalid value.

THE PREMISE IS CORRECT AND SURVIVED RE-VERIFICATION, which matters because most of what follows is
about staleness. `grep -c '"--type"'` returns 0 in BOTH `oc_runipd.py` and `agy_runipd.py`, so the
capability really is built and unreachable, and that is the whole reason this plan exists. F-2's
dispatch table verified exactly as described (`approved` -> `plan`, `implementing` ABSENT,
`to-review` -> `review`, four skip rows), which is what makes the plan's refusal to promise execution
honest rather than timid. All three of F-3's citations are exact: `oc_runipd.py:2959` writes
`"configured_file": plan["file"]`, and both hosts' sweep call sites are at `oc_runipd.py:2276` and
`agy_runipd.py:1569` verbatim. F-4's pin test exists and asserts what the plan says. F-6 is still broken
and I reproduced it: `aw find specs --status to-review` and `--status bogusvalue` both return 33 lines at
exit 0, and the `to-review` output visibly lists `approved` specs. This is a carefully evidenced plan
whose scope discipline (selection now, execution as its own blocker) is right.

THE FINDING THAT MATTERS MOST IS THAT THE PLAN'S HEADLINE MEASUREMENT WENT STALE WITHIN HOURS OF BEING
WRITTEN. The Concern, Goal and F-1 all rest on `sweep_review_candidates_for_type(repo, "spec")`
returning `6m4kow`, `2lcqno`, `6kwd2e`, `w15vzb`. I called it: it returns `[]`. All four specs were
advanced `to-review` -> `approved` by the SAME spec-review round that authored this plan (commit
`b16e1108`), `needs_review('spec','approved')` is False, and there is now no spec at `to-review`
anywhere in the repository (the 14 discovered id6-carrying specs are 11 `approved`, 1 `superseded`, 1
`draft`, 1 `implementing`). I want to be precise about what this does and does not damage. It does NOT
touch the unreachability claim, which is the plan's actual thesis and which I re-verified. What it
destroys is the ACCEPTANCE TEST: E-02's positive case cannot be demonstrated against the live tree at
all, and worse, a validation written as "paste the selection for `--type spec`" would now pass vacuously
against UNCHANGED code, since an unregistered flag and an empty population produce indistinguishable
emptiness. E-02 and V-02 now require a FIXTURE, with an explicit prohibition on manufacturing a
population by advancing a real spec's status, which would be a tooled lifecycle change made to satisfy
a test.

THE FINDING THAT WOULD HAVE STOPPED AN EXECUTOR OUTRIGHT IS A SELF-CONTRADICTION. The gate paragraph
said OQ-01 "is `- Blocking: yes` and unresolved, so this plan is not executable until the maintainer
answers", while OQ-01's own fields read `- Blocking: no` and `- Status: resolved` and carry the
maintainer's 2026-09-13 ruling in full. So the plan refused itself in prose while the linter and a
runner, which read the FIELDS, find nothing blocking and would dispatch it. That divergence is worse
than either answer alone, because which one wins depends on whether a human or a machine picks the plan
up. The fields are authoritative and the prose was stale, so I corrected the prose and voided the
conditional "supersede this plan with a Set" instruction, which was contingent on an answer that was
not given.

HALF OF E-05 IS ALREADY DONE, WHICH MADE ITS EVIDENCE UNOBTAINABLE BY EXECUTING IT. `6m4kow` carries no
`- Blocks-Release:` line at all, and its own workflow history records "this spec's gate is cleared in
this same call" as part of the authoring round. `aw check` is clean on all three artifacts (zero
diagnostics naming `ui8b9b`, `mng63x` or `6m4kow`, zero `blocks-release`/`from-spec` rule hits), and the
sibling `mng63x` exists in `pending/` carrying its own gate, so the maintainer's ruling was carried out
as described. E-05 therefore must not re-run `--blocks-release -` against an absent field, which would
at best no-op and at worst write a spurious history line onto an approved spec this plan's author did
not approve. What genuinely remains is real and worth doing: the spec's Section 0 R-15 row (`:40`) still
asserts `--type` is registered on neither host, which E-01 falsifies, AND it carries a stale measurement
of its own ("returns the four `to-review` specs") which is the same rot as F-7. E-05 is re-aimed at
those two, with an instruction to phrase the replacement as a predicate rather than a population so it
cannot rot twice.

ONE SMALL BUT PURELY WASTEFUL ERROR: E-01 said to register on the `run` and `resume` parsers. There is
no `run` subparser on either host; both expose `['report', 'resume', 'start', 'status', 'stop']`. The
operator spelling `aw oc run reviews` reaches `start` through the CLI wrapper, which is why the plan's
command-line prose is right and its parser instruction wrong. The shipped pin test already iterates the
correct pair, so an executor following the item literally would satisfy neither the flag nor the test.

WHAT I DELIBERATELY LEFT ALONE. E-03 is correct as written: it names `uyeko5`'s recorded divergence
(only `--retry-budget` is refused on resume, because the `--full-auto` handler overwrites) and tells the
executor to decide `--type`'s rule explicitly and pin it rather than copy a neighbour. That is exactly
the right instruction and I did not pre-empt which rule to choose, because the spec line governs it and
the executor will have the code in front of them. E-04's insistence that the superseded pin test be
INVERTED rather than deleted is also right, and V-04's refusal to accept a `gate_applied=False` verdict
is a genuinely good trap: that value is what a still-unreachable gate would also return, so without it
the item would be satisfiable without the change. F-6 is correctly out of scope and correctly recorded.

No product code was modified by this review. Full suite run bare and unchanged:
`6280 passed, 3 skipped, 2 xfailed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | E (testing), D (anti-regression) | measured: `sweep_review_candidates_for_type(repo,"spec")` -> `[]`; all four named specs `- Status: approved`; `needs_review('spec','approved')` False; zero specs at `to-review` repo-wide; 14 discovered = 11 approved + 1 superseded + 1 draft + 1 implementing | THE HEADLINE MEASUREMENT WENT STALE WITHIN HOURS AND THE ACCEPTANCE TEST IS NOW VACUOUS. The Concern, Goal and F-1 rest on the sweep returning four named specs; the same spec-review round that authored this plan advanced all four to `approved`, so the sweep returns nothing and no spec is at `to-review` anywhere. The unreachability thesis is UNAFFECTED and was re-verified. But E-02's positive case cannot be shown against the live tree, and a validation phrased as "paste the selection for `--type spec`" would pass against UNCHANGED code, since an unregistered flag and an empty population are indistinguishable. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New F-7. Concern and F-1 corrected in place with the staleness left VISIBLE rather than rewritten. E-02 now requires a FIXTURE spec at `to-review` and forbids manufacturing one by advancing a real spec's status; its expected outcome and V-02 rewritten, with V-02 told to expect an EMPTY live result and to explain a non-empty one. Required tests gains both the fixture case and a live empty-is-success case. Scope check records that the fixture machinery already exists in the declared test file. |
| PR-702 | HIGH | IN-SCOPE | G (executability) | gate paragraph: OQ-01 "is `- Blocking: yes` and unresolved"; OQ-01 fields: `- Blocking: no`, `- Status: resolved`, with the 2026-09-13 ruling recorded; `aw ipd lint` conforming | THE PLAN CONTRADICTED ITSELF ABOUT WHETHER IT MAY BE EXECUTED, AND ITS TWO READERS DISAGREE. A human reading the gate stops; the linter and a runner read the fields, find no blocking-open question, and dispatch it. The outcome depends on which reader acts, which is worse than either answer. The conditional instruction to supersede the plan with a Set was contingent on an answer that was not given. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8. Gate paragraph rewritten to state the ruling (selection ships now, execution filed as `mng63x`, verified present and carrying its own gate) and to void the supersede instruction. |
| PR-703 | MEDIUM | IN-SCOPE | G (honest documentation), A | `6m4kow` front matter has NO `- Blocks-Release:`; its history records the clearing in `b16e1108`; `aw check --agent` zero relevant diagnostics; `mng63x` present in `pending/` with the gate; stale row at `6m4kow:40` | HALF OF E-05 IS ALREADY DONE, SO ITS EVIDENCE AS WRITTEN CANNOT BE PRODUCED BY EXECUTING IT. The gate was cleared at AUTHORING time by the same round that filed this plan, so `--blocks-release -` would act on an absent field (at worst writing a spurious history line onto an approved spec this author did not approve), and the ordering worry the item raises was already discharged. What remains undone is the Section 0 R-15 row and Section 6 limit, which E-01 falsifies, and which ALSO carry the same stale four-spec population claim as F-7. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-9. E-05 re-aimed: the clearing is a CONFIRMATION not an action, the setter must not be re-run, and the real deliverable is the two stale assertions plus a non-rotting rephrasing. V-05 rewritten accordingly; scope check records that the declared spec file IS still modified, so no `--scope-ack` is expected. |
| PR-704 | MEDIUM | IN-SCOPE | G (executability) | both hosts' subparsers are exactly `['report','resume','start','status','stop']`; pin test iterates `("start","resume")` at `tests/test_run_flag_surface.py:464` | E-01 NAMED A SUBCOMMAND THAT DOES NOT EXIST. It said to register on the `run` and `resume` parsers; there is no `run` subparser. `aw oc run reviews` reaches `start` through the CLI wrapper, so the command-line prose is right while the parser instruction is wrong, and an executor following it would satisfy neither the flag nor the shipped pin test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10. E-01's title corrected to `start` and `resume`, with the measurement in a sub-bullet (kept out of the action text so it does not trip the `IPD-Z602` density advisory); expected outcome and V-01 both name the real subparsers. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's four-spec population is stale and no spec is at `to-review`. Does that invalidate the plan? | No. Keep it, and convert E-02's positive case to a fixture. | Retire the plan as resting on a collapsed premise; or leave the live-tree assertion and let the executor discover the emptiness. | The plan's thesis is UNREACHABILITY, which I re-verified (zero `--type` registrations on either host) and which no status change can affect. Only the illustrative population moved. Leaving the live assertion would be the real danger, because emptiness from an unregistered flag is indistinguishable from emptiness from an empty population, so the item would pass without the change. | yes |
| D-2 | The gate says OQ-01 is blocking and unresolved; the fields say otherwise. Which is authoritative? | The FIELDS. Correct the prose. | Treat the prose as a later, more considered statement and re-open OQ-01 as blocking. | The fields carry the maintainer's ruling in full with its date and its consequences, and `mng63x` was verified to exist carrying the gate the ruling promised, so the ruling demonstrably happened. AGENTS.md also makes the machine-readable field the signal automation reads, and `aw ipd lint` agrees with the fields. Re-opening a question the maintainer already answered would waste their time. | yes |
| D-3 | E-05's gate-clearing half is already done. Delete the item, or re-aim it? | Re-aim it. The gate half becomes a confirmation; the two stale spec assertions become the deliverable. | Delete E-05 as satisfied; or leave it and let the executor no-op the setter. | Deleting would drop the genuinely undone work: the spec still asserts `--type` is registered on neither host, which this plan falsifies, and leaving that would ship a spec contradicting the code. Leaving the setter instruction risks a spurious history line on an approved spec whose approver this plan's author is not. | yes |
| D-4 | Should review pick `--type`'s resume rule (refuse versus frozen-value-wins) for E-03? | No. Leave E-03's explicit-decision instruction intact. | Pick "refuse", following `--retry-budget`, the one flag that does refuse. | E-03 already forbids the real hazard (copying `--full-auto`, which overwrites and would let a resume re-scope the queue) and requires the choice be recorded and pinned. The governing input is a spec line the executor will have in front of them, and `uyeko5`'s recorded divergence means the shipped precedents disagree, so a reviewer picking from outside the code would be guessing at exactly the point the plan already handles well. | yes |

No decision this round is `Reversible: no`, so none required escalation as a blocking question. That is
the honest state of this plan: its one genuine judgement call (is reachable-but-not-executable enough to
clear a release gate) was already put to the maintainer and answered, and the sibling blocker that
answer promised was verified to exist.
