# Review findings: plan olmvgw

- Subject-Id: olmvgw
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `db2c6e3d`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

I CHECKED THE TIME-CRITICAL CLAIM FIRST, BEFORE ANYTHING ELSE, because the whole plan is worthless if the
bytes are gone. BOTH RECOVERED BLOBS ARE STILL PRESENT AND EXTRACTABLE:

```
git cat-file -s 9effdcef169e7ad8eafc0c3b22f5432cf1384dc6  ->  138154
git cat-file -s de2fbe7ceb1918551ea8f03fc0e8467f056119be  ->  114999
```

Both sizes match the plan exactly. I extracted both to gitignored scratch, read them, and deleted them. So
E-01 is still performable and the plan has not expired.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ESSENTIALLY EVERY CLAIM REPRODUCES. I re-drove all of it:

- F-01/F-02/F-03 reproduce. `git show main:agent_workflows/attention.py | grep -c inbox` is `0`, same for the
  test file and for the live tree; `hasattr(attention, "inbox_waiting")` is False; `git log --all -S'waiting
  in `.aw/inbox/`' -- '*.py'` is empty; and a real board driven through `cli.main(["attention", "--dir",
  <tmp>, "--no-color"])` against a temp repo with four inbox drops printed `## ready (1)`, one row,
  `1 artifact shown`, and NO footer line, with `"inbox" in out` False.
- F-06 reproduces in full, including the dangling-ness. All three holding commits (`5c55d020`, `888c20a1`
  dated 2026-09-20; `3569ed07` dated 2026-09-23) are reachable from no ref, and `gc.pruneExpire` and
  `gc.auto` are both UNSET (`git config --get` exits 1 for each).
- F-07 IS THE PLAN'S BEST FINDING AND IT REPRODUCES PRECISELY. I diffed the two footer blocks. The recovered
  blob patches `if needs_setup and has_hidden / elif needs_setup / elif has_hidden and colored`, and its
  comment argues at length that the new block must be "AN INDEPENDENT `if`, NOT another `elif` on the chain
  above ... the chain renders exactly ONE line". Today `attention.run`'s footer is `footer_lines: list[str] =
  []`, `needs_setup = setup_needed(repo_root)`, then a single `if needs_setup:` whose comment reads "The
  --all hint lives on the count line now; do not repeat it here". So a verbatim port really would ship a
  comment describing code that does not exist, and E-03 is right to make rewriting it the item's whole point.
  `attention.py`'s import block is `functools, json, re, sys, from pathlib import Path` with no `os`, exactly
  as stated.
- F-08 reproduces: `git ls-files .aw/inbox` returns `.aw/inbox/README.md`, so the exclusion is
  measured-necessary rather than predicted. The `/inbox/` anchoring rationale is in `.aw/.gitignore` as
  quoted, including the comms-lane hazard.
- F-09 reproduces exactly. A clean `CommandResult` returns `{'outcome': 'clean', 'exit': 0, 'findings': 0}`;
  the same result carrying one `severity="warning"` `Diagnostic` returns `findings: 1` with `outcome` still
  `clean`. So OQ-02's refusal to take the obvious route is well founded.
- F-12's other halves reproduce: `SCHEMA_VERSION` is `4`, and `tests/test_attention.py`'s contextlib import
  is exactly `redirect_stderr, redirect_stdout` with no `ExitStack`.
- `aw adopt` is shipped (`python3 -m agent_workflows adopt --help` exits 0, `artifact_adopt.py` present), so
  the nudge can name a real remedy, and E-03 is right to require invoking it rather than reading a status.

THE FINDINGS ARE THEREFORE REFINEMENTS, NOT REPAIRS OF A BROKEN ANALYSIS.

THE PRUNE URGENCY IS WRONG IN BOTH DIRECTIONS AT ONCE, AND AN EXECUTOR NEEDS BOTH HALVES (PR-001). The plan
treats "prunable" as a single fact. Measured, it is two. STRONGER THAN STATED: `git count-objects -v` reports
`count: 8875` loose objects against git's default `gc.auto` threshold of 6700, so auto-gc is ALREADY ARMED
rather than a future possibility, which is a better argument for E-01's ordering than the plan gives.
SOFTER THAN STATED: `git gc`'s `--cruft` behavior is ON BY DEFAULT, so an expiring collection repacks
unreachable objects into a cruft pack rather than deleting them, and both blobs are PACKED rather than loose
(neither appears at `.git/objects/<2>/<38>`), so a single auto-gc is less likely to destroy them than
"prunable" implies. Both halves are now stated as new F-14, because an executor who finds the blobs intact
after some unrelated command should not conclude the warning was false and relax the ordering.

THERE ARE FOUR ATTENTION SUITES, NOT THREE, AND THE MISSED ONE IS THE MOST EXPOSED (PR-002). F-12 and E-06
both say three. `ls tests/ | grep -i attention` returns FOUR: the three named plus
`tests/test_attention_blind_spot.py`, which passes today (`9 passed`) and which drives `attention.scan` and
asserts the records-scan drift rules (`attention.unclassified-tree`, `attention.uninventoried-tree`) over
fixture trees. That is precisely the surface a change to the scanned module could perturb, so an executor
following E-06 literally would leave it unrun. I also measured the reassuring half and recorded it so the
run is a confirmation rather than a discovery: a fixture repo holding `.aw/inbox/drop.md` yields an EMPTY
drift rule set from `attention.scan`, so the inbox does not trip the records scan.

THE SUITE IS NOT GREEN AND THE PLAN'S OWN ADVICE ALREADY IMPLIED THE RIGHT BAR (PR-003). Bare
`python3 -m pytest` at review: `1 failed, 3491 passed, 2 skipped, 3 warnings in 153.50s`, 208 deselected,
against the authored `3387 passed` and 207 deselected. The failure is
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a
pre-existing date-boundary bug pinning a workflow-history line against a hardcoded date the clock has
passed; it touches neither declared path. Validation step 2's "ZERO failures" was unachievable. Note the
plan was already half-right here: F-13 and the `## Required tests` preamble both say to compare failing
NODE IDS rather than totals, which is exactly the correct bar; only the "zero failures" sentence contradicted
it. Fixed in both places, with an explicit instruction not to fix that test.

ONE VALIDATION DEMAND ASKED THE EXECUTOR TO WRITE WRONG CODE (PR-004). V-05 required proof the patched-open
test bites "by showing it FAIL against a deliberately-parsing implementation (or by pasting the exception the
patched `open` raises when reached)". The first branch asks the executor to author a knowingly-incorrect
version of the function they have just ported, inside a plan whose entire subject is an undisclosed
substitution, and to then not commit it. The second branch establishes the same property at no cost. The
first is removed and the second made the requirement.

THE PLAN CARRIED NO CROSS-PLAN SURVEY DESPITE DECLARING A HEAVILY CONTENDED MODULE (PR-005), so I did one and
recorded it as new F-15. Two APPROVED siblings declare paths this plan declares: `r61br4` declares BOTH
`agent_workflows/attention.py` and `tests/test_attention.py`, and `o6ksmw` declares the test file. NEITHER
collides: measured, neither mentions `footer` or `footer_lines` anywhere, so neither touches the block E-03
edits. Seven further approved plans declare `attention.py` for unrelated functions. I did NOT add a
dependency edge: the runner isolates each item in its own worktree and revalidates on merge, so file overlap
is not a hazard, and an unnecessary edge would delay both plans. The row exists so a surprising diff is
interpretable.

TWO SMALL ONES. The gate's pre-finalize guard (`git show HEAD:... | grep -c inbox`) is a good idea and the
best thing in this plan's gate, but `grep -c` EXITS 1 when the count is zero (verified: it printed `0` and
returned 1), so the failing case's exit status is indistinguishable from a broken command and, chained with
`&&`, would skip the report that matters; `|| true` added with the reason (PR-006). And the gate asserted
"carries NO `- Readiness:` field", which was correct as authored and became false the moment this review
wrote one, so that paragraph now distinguishes the authored state from the reviewed state (PR-007).

ONE THING I CHECKED AND DID NOT FLAG. The plan resolves OQ-01 as NO and leaves OQ-02 open with a filed
carrier (`xqem10`), and it resolves three further design questions from evidence. I re-drove the two that
turn on facts and both hold: the `README.md` exclusion is genuinely forced by a tracked file, and the
singularization precedent (`count_noun = "artifact" if shown_count == 1 else "artifacts"`) really is in the
same function. OQ-02 is correctly left open: it is a question about audience and about what `findings` means
on a shared contract, F-09 reproduces the blocker that makes the obvious route wrong, and the plan's
sequencing note (do not decide against today's tally if the tally is about to change) is sound. The two
carriers `gmbdxe` and `xqem10` were filed at authoring rather than left to the executor, which is the right
call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C (operability), honest bounds | Plan E-01 and F-06 ("prunable"); `git count-objects -v` -> `count: 8875`; `git config --get gc.auto`/`gc.autoPackLimit` both exit 1; `git help gc` on `--cruft`; loose-path check for both shas | The prune urgency is stated as one fact and is two, wrong in both directions. STRONGER: 8875 loose objects against git's default `gc.auto` threshold of 6700 means auto-gc is ALREADY ARMED, not a future possibility. SOFTER: `gc --cruft` is on by default, so an expiring collection repacks unreachable objects into a cruft pack rather than deleting them, and both blobs are PACKED not loose, so one auto-gc is less likely to destroy them than "prunable" implies. An executor who finds them intact after an unrelated command could wrongly conclude the warning was false and relax E-01's ordering. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-14 records both halves with the commands; E-01 gains a paragraph stating the window is open, its closing unpredictable, and the ordering unchanged as the mitigation; E-01's expected outcome notes a differing byte size is itself a finding. |
| PR-002 | HIGH | UNDER-SCOPE | Rubric E (testing coverage) | Plan F-12 and E-06 ("Those three are what exists"); `ls tests/ \| grep -i attention` returning four; `pytest tests/test_attention_blind_spot.py` -> `9 passed` | There are FOUR attention suites and the plan names three. The missed one, `tests/test_attention_blind_spot.py`, drives `attention.scan` and asserts the records-scan drift rules over fixture trees, which is the surface most exposed to a change in the scanned module, so an executor following E-06 literally would leave it unrun by a change to `attention.py`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-12 corrected and the convention bullet updated; E-06 now names all four with the reason the fourth matters, plus the reassuring review measurement that `.aw/inbox/` yields an empty drift set from `attention.scan` so the run confirms rather than discovers; validation steps 1 and 4 and V-06 all updated to four files. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (honest baselines) | Plan F-13 and validation step 2 ("ZERO failures"); `python3 -m pytest` at review -> `1 failed, 3491 passed, 2 skipped`, 208 deselected | The suite is not green, so step 2's bar is unachievable. The failure is a pre-existing date-boundary bug in `tests/test_backlog.py` touching neither declared path. An executor held to zero failures would either misattribute it or paper over it. Note the plan was already half-right: F-13 and the preamble both say to compare failing node ids rather than totals, which is the correct bar; only one sentence contradicted it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 rewritten with both measurements and the named failure; the convention bullet and the `## Required tests` preamble updated; step 2's bar changed from "ZERO failures" to an unchanged failing node-id set; V-06 likewise; fixing that test explicitly forbidden as out of scope and another party's. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric E, Rubric F (KISS) | Plan V-05 ("showing it FAIL against a deliberately-parsing implementation") | V-05's first proof branch asks the executor to author a knowingly-wrong implementation of the function they have just ported, inside a plan whose whole subject is an undisclosed substitution, and then to not commit it. The alternative branch the same sentence offers (paste the exception the patched `open` raises when reached) establishes the identical property at no cost and no risk. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05's first branch removed; the sentinel demonstration (calling the patched sentinel inside the test's own context) is now the requirement, with the reason for the change recorded in the item so a reader does not restore the removed branch. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric G (executability), cross-plan consistency | `- Scope-Paths:` scan over `.aw/records/plans/pending/`; `grep -n "footer\|footer_lines"` returning nothing in `r61br4` and `o6ksmw` | The plan declares a heavily contended module and carried no sibling survey. Two APPROVED plans declare paths it declares (`r61br4` both, `o6ksmw` the test file) and seven more declare `attention.py`. Without the survey an executor meeting a surprising diff cannot tell whether a sibling landed or their own change misfired. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records the survey and the measured non-collision (neither sibling touches the footer block E-03 edits); a `Cross-plan` bullet added to `## Scope check`. No dependency edge declared: the runner isolates each item and revalidates on merge, so an edge would delay both plans for no safety gain. |
| PR-006 | LOW | IN-SCOPE | Rubric A (correctness), Rubric F (prevent silent failure) | Plan's POST-GATE LIFECYCLE guard; `git show HEAD:agent_workflows/attention.py \| grep -c inbox` printing `0` and returning 1 | The pre-finalize guard is the best thing in this plan's gate (it is the direct countermeasure to the defect being remediated) and it has a shell trap: `grep -c` exits 1 when the count is zero, so the FAILING case's exit status is indistinguishable from a broken command, and chained with `&&` it would skip the very report that matters. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `\|\| true` added to the guard with the measured reason stated inline, plus an explicit instruction to read the printed NUMBER and never the exit status. |
| PR-007 | LOW | IN-SCOPE | Rubric G, internal consistency | Plan's `## Approval and execution gate` ("carries NO `- Readiness:` field") | The gate asserts the plan carries no `- Readiness:` field. That was correct as authored and became false the moment this review wrote one, which is the self-invalidating shape: a future reader comparing the paragraph to the front matter would see a contradiction and could not tell which was intended. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The paragraph now records that the AUTHORED copy correctly carried no field, that `/plan-review` wrote `go-pending-approval` as its own output, and that `reviewed` is still not approval. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Two APPROVED siblings declare this plan's paths. Declare an `- Item-Dependencies:` edge, or treat it as evidence guidance? | Evidence guidance: new finding row plus a `Cross-plan` scope bullet, no edge. | Declaring a dependency on `r61br4` and/or `o6ksmw`, rejected because neither touches the footer block this plan edits (measured: neither mentions `footer` or `footer_lines`) so neither needs to precede it, and an unnecessary edge delays both plans. | `grep -n "footer\|footer_lines"` over both sibling plans returning nothing; AGENTS.md records that the runner gives each item an isolated worktree and returns changes through the merge-and-revalidate gate, so file overlap is not a hazard. | yes |
| D-2 | V-05 offers two ways to prove the patched-open test bites, one of which requires authoring a wrong implementation. Keep both, or narrow to one? | Narrow to the sentinel demonstration; remove the deliberately-parsing-implementation branch. | Keeping both branches, rejected because an executor may take the riskier one: writing a knowingly-wrong version of the just-ported function, in a plan whose subject is an undisclosed substitution, creates an uncommitted artifact that must not land. | The two branches establish the same property (that the patched `open` raises when reached), and the sentinel one needs no extra code; GUIDING_PRINCIPLES KISS. | yes |
| D-3 | `gc --cruft` means a collection may not destroy the blobs. Does that weaken E-01's extract-first ordering? | No: record both halves, keep the ordering unchanged as the mitigation. | Softening E-01 on the strength of the cruft-pack behavior, rejected because 8875 loose objects against a 6700 default threshold means auto-gc is already armed and the exact outcome is not predictable. | `git count-objects -v` -> `count: 8875`; `git config --get gc.auto` exits 1 (default governs); `git help gc` documents `--cruft` on by default; both blobs measured packed rather than loose. | yes |
| D-4 | The suite has a pre-existing failure. Fix it, or carry it? | Carry it; the plan now forbids fixing it. | Fixing it inside this plan, rejected as an undeclared out-of-scope edit to another party's test in a shared checkout, and this plan declares exactly two paths. | The failure is a hardcoded date versus the current date in `tests/test_backlog.py`, touching neither declared path; AGENTS.md's shared-checkout rule against modifying work that is not yours. | yes |
| D-5 | Does the new counter risk tripping the records-scan drift rules that `test_attention_blind_spot.py` pins? | No; recorded as a confirmation the executor should run rather than discover. | Leaving the fourth suite unnamed (the authored state), rejected because it is the suite most exposed to a change in the scanned module. | Driven at review: a fixture repo holding `.aw/inbox/drop.md` produces an empty drift rule set from `attention.scan`, and `.aw/inbox/` sits outside `.aw/records/` by design so no records sweep enumerates it. | yes |
