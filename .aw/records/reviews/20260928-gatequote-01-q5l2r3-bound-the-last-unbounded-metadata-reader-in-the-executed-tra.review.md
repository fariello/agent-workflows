# Review findings: plan q5l2r3

- Subject-Id: q5l2r3
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `4985a12b` in a lane worktree; the plan was authored at `1553abce`, which is an
ancestor. Structural preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0,
`findings: 0`) and `--phase review-finalize --agent` conforms after revision with zero findings. No
pre-review snapshot was owed: the plan was committed and unmodified with `git status --short` empty at
review start. `- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. `aw check
release-gates` CONFORMS and `aw sanitize --agent` is clean. Two probe patches were applied to
`agent_workflows/hooks/executed_transition_gate.py` and both were reverted; `git diff --stat` verified
empty afterwards.

THE PLAN'S DIAGNOSIS IS RIGHT, ITS RE-AIMING IS RIGHT, AND ITS FIX DOES NOT WORK. Those three
sentences are the whole review, and the third is the blocker. Taking them in order.

THE DIAGNOSIS REPRODUCES IN FULL, INDEPENDENTLY. F-1: `_has_executed_status` reads
`selectors.metadata_region(text)` and returns `False` on `vnzm27`'s exact reported shape (own status
`approved`, a fenced four-line `grep -m1 '^- Status:'` transcript of `- Status: executed`), and `True`
when the metadata status is itself `executed`, so the reported defect is genuinely already fixed. F-3:
`_plan_id_of` applies `(?m)^- Id:\s*([0-9a-z]{6})\s*$` to the whole text and returns `bbbbbb` for a
record whose preamble fences that id above its real metadata `- Id: 3v7wo6`. F-4, the severity claim,
reproduces END TO END in a temp repo: with `git merge --no-commit --no-ff` of a side branch whose only
commit subject is `artifact_core.finalize_commit_subject('bbbbbb')`, `MERGE_HEAD` present and seen by
`_merge_incoming_commits`, and the plan `git mv`ed into `executed/`, `check()` returns exit `0` with NO
refusals. That is a false ACCEPT in a prevention layer. F-5 reproduces: with no merge, the refusal's
parenthesized id6 is `bbbbbb`, so the prescribed remedy is `aw ipd finalize bbbbbb`, a command that
cannot succeed for the plan being committed. F-6's corpus claim reproduces (876 plans now, 867 at
authoring, `divergent=0`). F-7 verifies: `axayfn` is `open`, `bug`, `Blocks-Release: next`, names three
readers and does NOT name `_plan_id_of`. F-8 verifies: `check_engine._status_meta` returns `None` for a
quoted-only status.

THE RE-AIMING IS THE RIGHT CALL. The plan declines to execute its backlog item literally because
`kecxnb` already did that work, and it instead fixes the sibling reader in the same file. That is
correct: executing `vnzm27` verbatim would be a no-op edit to a function that already reads the way the
item asks, and F-4 establishes real remaining harm in the same file and the same declared scope.

THE FIX AS AUTHORED DOES NOT FIX IT, AND THAT IS THE BLOCKER. E-01 specified bounding `_plan_id_of` to
`selectors.metadata_region`. Review APPLIED THAT EXACT CHANGE to the real file and re-ran both
reproductions: F-4 still returned exit `0` and F-5's refusal still named `bbbbbb`. The cause is
structural and is stated in `metadata_region`'s own docstring: the region is "everything before the
first `##`+ heading", and the quoted `- Id:` in the shape F-3 and F-4 themselves describe sits in the
PREAMBLE, above the metadata bullets, therefore INSIDE the region. The boundary falls on the wrong side
of the quote. Unit reads make it unambiguous: on the preamble-fence shape, unbounded returns `bbbbbb`
and region-bounded ALSO returns `bbbbbb`; on a HEADINGLESS record of the same shape, likewise. Region
bounding changes behavior only when the quote sits AFTER the first `##` heading AND the record declares
no real `- Id:` at all, and in that case it yields `None`, which takes the gate's separate "no readable
'- Id:' handle" branch rather than attributing correctly.

THE FIX THAT WORKS WAS ALSO MEASURED, so the repair is not speculative. Adding a fenced-line skip on
top of the region bound makes the preamble shape, the post-heading shape and the headingless shape all
read `3v7wo6`; applied to the real file, F-4 returns exit `1` with the refusal naming `3v7wo6`, F-5
names `3v7wo6`, and `tests/test_executed_transition_gate.py` plus
`tests/test_executed_transition_gate_e2e.py` stay green at `13 passed`. The corpus is likewise clean
for it (`fenceaware_None=0`, `divergent_vs_unbounded=0` over 876 plans). And this is the repository's
OWN answer rather than an invention: `check_engine._fenced_line_numbers` already exists and
`check_engine.check_id_outside_metadata_region` already applies it to this exact judgement, recording
the principle in its docstring ("a line inside a fenced code block is a QUOTATION by construction ...
so it can never be a misplaced declaration") along with the maintainer's 2026-09-05 "fix AND warn"
ruling, of which this plan is the "fix" half for one reader.

THE MOST DANGEROUS PROPERTY OF THE AUTHORED PLAN WAS THAT IT WOULD HAVE LOOKED SUCCESSFUL. Review
measured that all three reader variants agree across the whole 876-plan corpus, so V-01's corpus check
passes for the ineffective fix; the existing 13 gate tests pass for it; and E-02's tests (a) and (b), if
written with the fence after a `##` heading rather than in the preamble, would also have passed. An
executor could therefore have shipped the authored change, seen green everywhere, and closed a
release-gated bug item on a defect that still reproduces. That is why the revision adds two unit cases
(headingless, and preamble-versus-body), instructs (a) and (b) to place the fence in the PREAMBLE, and
gives V-02 a SECOND differential against the region-only variant, which is the check that would have
caught this.

SMALLER CORRECTIONS. F-2's "`vnzm27` was left `open`" is stale by one lifecycle step: it is
`graduated`, to this very Set, recorded in its own history. V-03 demanded a bare suite "showing 0
failed" while the tree already carries one pre-existing unrelated failure
(`test_drain_and_cascade_mapped_reasons_rendered_once`, hardcoding `executed:5o1jye` after that plan
reached `executed/`), which would have forced the executor either to fix an out-of-scope test or to
report a failure this plan did not cause. The gate section asserted the gate's test file keeps "its
existing five"; it holds six. The scope fence asserted `selectors.py` would need no edit, which is no
longer safe to promise once a fence helper is involved, so it now names that edit as one to make and
justify rather than a reason to stop. And F-6's row overstated by omission: it establishes safety, not
efficacy, which is now said explicitly.

WHAT REVIEW CHECKED AND LEFT ALONE. The plan's own flagged unfiled-carrier gap was verified rather than
taken on trust: `cli._artifact_status` does exist (as a NESTED function inside the `search`
implementation, so a module-level lookup finds nothing, which is worth recording) and searches
`(?m)^-\s*Status:\s*(\S+)` over the whole text; `artifact_audit.read_declared_status` and
`ipd_schema.read_readiness` likewise make no `metadata_region` call. So the list is accurate and the gap
is real. Review did NOT file the item: OQ-02's owner is correctly `human`, and filing on an agent's own
initiative would manufacture a tracked obligation the maintainer has not accepted. One note was added
for whoever decides, that `read_readiness` is the one to weigh first because `- Readiness:` is the
attestation the auto-approve predicate reads first. OQ-01's release-gate handoff reasoning is correct
and was left as written. The severity reasoning (MED, argued in both directions) is honest and was kept.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness / G. Plan executability | Region-only fix APPLIED to the real file: F-4 -> exit `0` (still a false accept), F-5 -> refusal still names `bbbbbb`. Unit reads on the preamble-fence shape: unbounded `bbbbbb`, region-bounded `bbbbbb`, fence-aware `3v7wo6`; headingless shape identical. `selectors.metadata_region`'s docstring ("everything before the first `##`+ heading"). Fence-aware fix applied: F-4 -> exit `1` naming `3v7wo6`, F-5 -> `3v7wo6`, gate suites `13 passed` | THE AUTHORED FIX DOES NOT FIX THE AUTHORED DEFECT. E-01 specified region bounding only; review applied exactly that and both F-4's false accept and F-5's misattribution survive, because the quoted `- Id:` in this defect's own shape sits in the PREAMBLE and is therefore INSIDE `metadata_region`. Region bounding helps only when the quote sits after the first `##` AND no real `- Id:` exists, where it yields `None` rather than the right id6. | C:Low; U:Low; S:Medium; F:High on the AUTHORED plan (it would close a release-gated bug item on a defect that still reproduces, in a prevention layer); Low on the corrected plan (one additional condition, reusing an existing helper, measured working with all existing tests green) | FIXED | E-01 rewritten to require BOTH region bounding AND a fenced-line skip, reusing `check_engine._fenced_line_numbers`, with the measured evidence for both variants. Title, Concern, Scope and Goal corrected so the deliverable is FENCE-IMMUNITY rather than "bounded to the region", a property that can be satisfied without fixing the defect. Recorded as F-9 and OQ-03. |
| PR-002 | HIGH | IN-SCOPE | E. Testing and verification | All three reader variants agree across 876 plans; the 13 existing gate tests pass under the region-only variant; (a)/(b) as specified do not fix the fence position | THE AUTHORED VALIDATION WOULD HAVE CERTIFIED THE BROKEN FIX. V-01's corpus check passes for the ineffective variant, the existing suites pass for it, and E-02's (a) and (b) would have passed too if their fence sat after a `##` heading. So nothing in the plan could distinguish the correct fix from the plausible one, which is how the defect would have shipped as closed. | C:Low; U:Low; S:Low; F:High; Overall:High | FIXED | E-02 gains case (e) HEADINGLESS and case (f) PREAMBLE-VERSUS-BODY, plus an instruction that (a) and (b) place the fence in the PREAMBLE. V-01 requires all three shapes read correctly. V-02 gains a SECOND differential: the tests must be RED against a region-bounded-only implementation. A new STOP condition fires if they are not. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing | Measured bare suite at review: `1 failed, 3031 passed, 2 skipped`; `tests/test_dependency_block_reporting.py:122` `assert not sat`; `5o1jye` now in `executed/` | V-03 DEMANDS "0 failed" ON AN ALREADY-RED TREE. The one failure is pre-existing and unrelated (a test hardcoding `executed:5o1jye`), so the authored bar would force the executor either to fix a test outside `- Scope-Paths:` or to report a failure this plan did not cause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 carries the measured baseline, the exact node id with its cause, and the bar "that one node id and no other, count at or above 3031"; the honesty rule now says expect one pre-existing failure, do not fix it and do not claim it. |
| PR-004 | MEDIUM | IN-SCOPE | G. Plan executability | E-01's "the fix CONSUMES `metadata_region` unchanged, and adding a second local region parser is the precise drift that helper exists to prevent"; `check_engine._fenced_line_numbers`; this hook's lazy-import style | THE SCOPE FENCE PROMISED `selectors.py` NEEDS NO EDIT, which is no longer safe once a fence test is required. The corrected fix needs a fenced-line helper, and the two acceptable sources are a lazy `check_engine` import (heavy for an import-light hook) or moving the helper into `selectors` (an out-of-scope edit the fence forbade). Left as authored, an executor would have faced a fence that appeared to forbid the only clean implementations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The fence now names both acceptable routes, states the preference (move the helper into `selectors`), declares the resulting `selectors.py`/`check_engine.py` edits as out-of-scope-but-justifiable at finalize, and keeps the prohibition on a THIRD local fence parser. Recorded as OQ-04, left `open` with `- Owner: executor` since it is an implementation judgement no `V-*` depends on. |
| PR-005 | LOW | IN-SCOPE | Step 1 evidence | `vnzm27` `- Status: graduated`, `- Graduated-To: gatequote`, history line "2026-09-28 set (aw backlog): graduated by run ...: q5l2r3" | F-2's "`vnzm27` was left `open`" IS STALE BY ONE LIFECYCLE STEP. It is `graduated`, to this plan's own Set. The part that matters, that it still carries `- Blocks-Release: next`, is correct and is what OQ-01 disposes of. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2's finding and evidence columns corrected. |
| PR-006 | LOW | IN-SCOPE | F. Honest documentation | All three reader variants agree across 876 plans | F-6 OVERSTATES BY OMISSION. "The fix cannot regress any existing plan" is true and is presented as if it also supported the fix; because every variant agrees corpus-wide, the measurement cannot distinguish the working fix from the broken one. It establishes safety, never efficacy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 re-measured at 876 with both variants and now states explicitly that it proves safety and not efficacy, pointing at F-4/F-5 as the load-bearing tests; V-01 repeats the caveat. |
| PR-007 | LOW | IN-SCOPE | Step 1 evidence | `grep -c "def test" tests/test_executed_transition_gate.py` -> `6` | THE GATE SECTION MISCOUNTS THE EXISTING TESTS as "its existing five"; the file holds six. Minor, but an executor reconciling counts after adding cases would be chasing a missing test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to SIX in the scope fence, with a note in Required tests. |
| PR-008 | LOW | IN-SCOPE | Step 1 evidence | `cli._artifact_status` is a NESTED function inside `search` (module-level lookup finds nothing) searching `(?m)^-\s*Status:\s*(\S+)` over whole text; `artifact_audit.read_declared_status` and `ipd_schema.read_readiness` make no `metadata_region` call | THE FLAGGED UNFILED GAP IS REAL AND THE LIST IS ACCURATE, verified rather than trusted. The plan asked the reviewer to decide whether to file it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A REVIEW DISPOSITION, not a code change: citations verified and recorded, including that `_artifact_status` is nested so a later reader does not mistake the citation for stale. The filing decision is left with the maintainer per OQ-02, whose owner is correctly `human`; review declines to file, since doing so would manufacture a tracked obligation the maintainer has not accepted. Added a note that `ipd_schema.read_readiness` is the one to weigh first, being adjacent to the auto-approve predicate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The authored fix does not fix the authored defect. Repair the plan, REPLAN, or supersede it? | REPAIR: keep the diagnosis, findings, scope and handoff; correct E-01's mechanism to add a fenced-line skip, and harden the validation so the broken variant cannot pass. | (a) REPLAN - rejected: the problem statement, nine findings, severity reasoning and test surface are all sound; one item needed one more clause, which is the textbook bounded-edit case, and a replan would discard correct measured findings to re-derive them. (b) Supersede and close `vnzm27` on the records side (an option the plan's own Scope check invites) - rejected: F-4 is a MEASURED false accept, so there IS code to fix, and `vnzm27` carries `- Blocks-Release: next` with this plan as its only carrier. (c) Ship the authored region-only fix and file the remainder - rejected outright: it closes a release-gated bug item on a defect that still reproduces. | Region-only fix applied to the real file leaving F-4 at exit `0` and F-5 naming `bbbbbb`; fence-aware fix closing both with 13 existing tests green; `metadata_region`'s `##` boundary docstring | yes |
| D-2 | Which fence mechanism should `_plan_id_of` use, given the hook is deliberately import-light? | LEAVE IT TO THE EXECUTOR as an `open`, non-blocking OQ naming two acceptable routes and one forbidden one, with a stated preference. | (a) Mandate importing `check_engine._fenced_line_numbers` - rejected: `check_engine` is large and this hook lazily imports even `re`, so the cost deserves weighing with the code in hand. (b) Mandate moving the helper into `selectors` - rejected as over-specification for a judgement with identical observable behavior either way. (c) Allow a local fence parser as a third option - rejected outright: that is the duplication `metadata_region` exists to prevent and `check_id_outside_metadata_region` already solves. | This hook's lazy-import style; `check_engine.check_id_outside_metadata_region` using the helper for this exact judgement; review measuring route (a) working end to end | yes |
| D-3 | Should the review file the unfiled backlog item the plan flagged (`cli._artifact_status`, `artifact_audit.read_declared_status`, `ipd_schema.read_readiness`, the `attention.py` readers)? | NO: verify the citations, record them, and leave the filing decision with the maintainer via OQ-02. | (a) File it - rejected: which of these is worth tracking and at what priority is a scope-and-priority judgement reserved to the maintainer, and an agent filing it creates a tracked obligation nobody accepted. (b) Delete the flag as out of scope noise - rejected: the readers are genuinely unbounded (verified) and one of them backs the forgeable `- Readiness:` attestation, so silence would lose a real finding. | `cli._artifact_status` read in full (nested, unbounded); `artifact_audit.read_declared_status` and `ipd_schema.read_readiness` confirmed to make no `metadata_region` call; `AGENTS.md` on `- Readiness:` forgery | yes |
| D-4 | V-03 demands "0 failed" but the tree is red. Relax the bar, or leave it? | RELAX it to the named pre-existing node id, with the count floor and an attribution instruction. | (a) Leave "0 failed" - rejected: it forces the executor to fix an out-of-scope test or to report a failure this plan did not cause. (b) Drop the suite requirement - rejected: this change touches a pre-commit gate every commit runs, so a full-suite check is exactly right. | Measured `1 failed, 3031 passed, 2 skipped` on a clean tree; `tests/test_dependency_block_reporting.py:122`; `5o1jye` in `executed/`; `verify-execution` Dimension 3's attribution rule | yes |

No `Reversible: no` decision was made. Every decision above is a specification or wording change inside
one pending plan plus this review record; each is undone by editing the plan, and none touches
production code, a published interface, a migration, or an executed record. This review modified NO
production or test file: the two probe patches to `executed_transition_gate.py` were reverted and
`git diff --stat` verified empty.

No finding is left `OPEN` or `DEFERRED`, so no escalation into the plan as a `- Blocking: yes` question
is owed under `review_findings_gate.block_at` (default `HIGH`). The BLOCKER and both HIGH findings are
`FIXED` in place. OQ-01 was pre-existing, resolved and non-blocking and is correct as written; OQ-02 was
pre-existing and stays `open` with `- Owner: human` by design (its facts are now verified); OQ-03 was
added by this review to carry D-1 and is resolved and non-blocking; OQ-04 was added to carry D-2 and is
deliberately `open` with `- Owner: executor`, non-blocking, since either acceptable route yields
identical behavior and no `V-*` depends on the choice.

### Structural and consistency checks at review

- `aw ipd lint --phase author --agent` before revision: `outcome: clean`, `exit 0`, `findings: 0`.
- `aw ipd lint --phase review-finalize --agent` after revision: `outcome: clean`, `exit 0`,
  `findings: 0`.
- `aw check release-gates`: `CONFORMS`, 0 errors, so `- Blocks-Release: next` and
  `- From-Backlog: vnzm27` both resolve.
- `python3 -m pytest tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py -o addopts=""`:
  `13 passed` before any probe, and `13 passed` again with the fence-aware fix applied.
- Bare `python3 -m pytest` on a clean tree: `1 failed, 3031 passed, 2 skipped, 3 warnings in 43.75s`,
  the one failure pre-existing and unrelated (see PR-003).
- Corpus measurement over 876 tracked `.ipd.md` plans: region variant
  `unbounded_None=0 bounded_None=0 divergent=0`; fence-aware variant
  `fenceaware_None=0 divergent_vs_unbounded=0`.
- `aw sanitize --agent`: clean.
- ONE SELF-INFLICTED GATE FINDING, CAUGHT AND FIXED DURING THIS REVIEW, recorded because it is exactly
  the kind of thing this record exists to make auditable. The first draft of this file wrote PR-008's
  Decision cell as `FIXED (as a review disposition, not a code change)`, and
  `aw ipd lint --phase review-finalize` then reported `check.review-finding-unescalated` against the
  PLAN with the detail "review artifact for plan q5l2r3 is malformed (REV-P003), so its findings cannot
  be checked for escalation". `review_findings.DECISIONS` is the closed tuple
  `('fixed', 'deferred', 'open', 'replan')`, and the parenthetical put the cell outside it, which the
  evaluator's documented case (b) correctly treats as fail-closed rather than as an absence. The cell
  was normalized to bare `FIXED` with the qualification moved into the Resolution column;
  `review_findings.parse_review_text` then reported no diagnostics and the lint returned clean. Nothing
  about PR-008's substance changed.
- Probe hygiene: two patches to `agent_workflows/hooks/executed_transition_gate.py` (region-only, then
  fence-aware), each measured and then reverted; `git diff --stat` empty and `git status --short` clean
  afterwards. The only files this review modified are the plan and this record.
