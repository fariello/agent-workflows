# Review findings: plan lqzoi9

- Subject-Id: lqzoi9
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b4a7de46` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `"outcome":"clean"`, `findings: 0`) and `--phase
review-finalize --agent` conforms after revision with `findings: 0`.
`check_engine.evaluate_durable_carrier` returned ZERO drifts. `aw check` reports 3 repository errors
and NONE names this plan: two are `check.ipd-uncarried-obligation` on other agents' pending plans
(`iq3txw`, `4er1ev`) and one is a pre-existing `check.system-layout-missing` on `.aw/system/layout.json`.
No pre-review snapshot was owed: `git status --short` reported the tree clean with the plan committed
and unmodified.

THIRTEEN OF THE FOURTEEN AUTHORED FINDINGS REPRODUCED, and the one exception is a figure that makes the
finding stronger rather than weaker. F-01: `tests/test_plan_readiness.py` deleted in `19313eed`, and a
tree-wide search for `ApprovalGateRealCorpusTests` or its test name returns ZERO hits. F-02: zero
refusals and zero verdict-class refusals for `s0gnha`, `ty7w6o` and `svacmz`, with `ty7w6o` confirmed to
carry the real `/askme` record and `is_review_history_entry` returning False for it. F-03: exactly two
source hits for `negative_readiness_asserted` (its own `def` and the comment in `history_verdict_approves`
saying it is deliberately NOT used there), and `xpta5g` E-04's "Keep `negative_readiness_asserted` itself
(it is a pure helper and removing it is out of scope)" quoted verbatim. F-04: `grep` over `tests/`
returns 0. F-05: all six incident shapes correct, including the regression direction. F-06: no test
mentions `/askme`, and the two variants classify False and True exactly as described. F-07: no
`pytestmark`, no `@pytest.mark`, no `import pytest`, 5 tests collected, against `tests/test_ipd_lint.py`'s
method-level `@pytest.mark.livecorpus` precedent. F-08 and F-11: bare suite `2935 passed, 2 skipped,
3 warnings in 41.90s` with the "201 tests were deselected ... skips 'slow' and 'livecorpus'" notice, and
the edited file `5 passed`. F-09: zero `reaskscore` plans in `pending/`, six in `executed/`. F-10: the
`_CLEARED_NEGATIVE_READINESS_RE` note names that exact test verbatim. F-13: `xpta5g`'s "EXPLICITLY NOT
IN SCOPE" line quoted accurately. The incident message is recoverable at `a03b4c5b^` as E-02 claims.

THE PLAN'S DIAGNOSIS AND ITS HARDEST JUDGEMENT ARE BOTH RIGHT. OQ-01 asks whether an item whose headline
symptom no longer reproduces should be closed as fixed, and answers GRADUATE on three measured grounds -
the shape is unpinned, the named guard no longer covers the plans it was written for, and the repair left
a predicate with zero callers AND zero tests. That is the correct reading: "the bug stopped reproducing"
and "the bug is guarded" are different claims, and only the second justifies closing. E-01's application
of the `livecorpus` marker is likewise exactly the rule the incident produced, cited from the marker's own
definition, and marking rather than deleting respects the same definition's instruction that such tests
are valuable.

WHAT REVIEW FOUND IS THAT ONE ASSERTION THE PLAN MANDATES IS FALSE AT HEAD, WHICH MADE THE PLAN
UNEXECUTABLE AS WRITTEN.

**E-03 REQUIRED PINNING A CLAIM THE PREDICATE DOES NOT HONOR (PR-701, BLOCKER).** The
`_CLEARED_NEGATIVE_READINESS_RE` note closes: "The 80-character bound and the `[^.]` class keep the
clearing verb and the token inside ONE SENTENCE, so a record that resolves one question and separately
reports a new no-go is still refused." E-03 instructed: "Also pin the one-sentence bound the comment
claims is load-bearing: a message that clears one no-go and then, AFTER a sentence break, asserts a new
one must return True." MEASURED, that returns **False**, and so do three other phrasings of the same
idea. The cause is structural rather than a bad fixture: the predicate's body ends `return not
_CLEARED_NEGATIVE_READINESS_RE.search(message)`, and `search` succeeds on the FIRST clearing clause
anywhere in the message, so one clearing clause excuses the entire record regardless of what follows. The
`[^.]` class and `{0,80}` bound constrain each individual MATCH to one sentence; they do not constrain the
PREDICATE to one sentence. An executor following E-03 literally writes a test that fails at HEAD, and the
likely reactions are both bad: conclude the repository is broken, or quietly flip the expected value to
False without noticing that the comment it was drawn from is wrong.

V-03'S DELIBERATE-FAILURE DEMONSTRATION COULD NOT HAVE CAUGHT IT EITHER. It said to drop the `[^.]`
sentence bound and watch the sentence-break row go red. Measured, that row is False both with the shipped
bound and with `[^.]` widened, so the demonstration shows nothing - the one check designed to prove the
new test is a real guard would itself have been vacuous.

A WORKING DISCRIMINATOR EXISTS, so this is a repairable blocker and not a replan. `negative_readiness_asserted("we cleared OQ-01. readiness no-go")`
returns **True** at HEAD, and flips to False when `[^.]{0,80}?` is widened to `[\s\S]{0,400}?` while the
bare `readiness no-go` and `REJECT - NEEDS REPLAN; readiness no-go` controls stay True. So the bound IS
load-bearing - for ADJACENCY and ORDERING (a clearing verb must sit within 80 characters and one sentence
OF THE TOKEN IT EXCUSES) rather than for the sentence break the comment names. Pinning that row gives
E-03 a real guard, pinning the clear-then-assert case at its measured False documents the residual limit
truthfully, and correcting the note in E-04 stops the false claim propagating.

Two smaller items: F-02's polarity figure was wrong in a direction that strengthens it (PR-702), and the
gate lacked a declared scope fence with its two load-bearing negative constraints, conditional finalize
ownership, and any statement of the pin-a-false-claim failure mode (PR-703).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-701 | BLOCKER | IN-SCOPE | E. Testing / A. Correctness (a mandated assertion that is false at HEAD) | E-03 as authored: "pin the one-sentence bound ... a message that clears one no-go and then, AFTER a sentence break, asserts a new one must return True"; the `_CLEARED_NEGATIVE_READINESS_RE` note's closing sentence "...so a record that resolves one question and separately reports a new no-go is still refused"; `negative_readiness_asserted`'s body ending `return not _CLEARED_NEGATIVE_READINESS_RE.search(message)`; measured `False` for "clearing OQ-01 and with it its no-go. A new blocking question asserts readiness no-go", "resolved OQ-01, clearing its no-go. However OQ-02 is open so readiness no-go.", "no-go -> go-pending-approval. Later re-review set readiness no-go." and "cleared the no-go for OQ-01. readiness no-go"; the same row measured `False` with `[^.]` widened, so V-03's mutation is inert on it; `negative_readiness_asserted("we cleared OQ-01. readiness no-go")` -> `True`, flipping to `False` when `[^.]{0,80}?` becomes `[\s\S]{0,400}?` while both controls stay `True` | **THE PLAN MANDATES AN ASSERTION THAT FAILS AT HEAD, AND ITS PROOF-OF-GUARD MUTATION IS INERT ON THAT ROW.** The comment E-03 draws the row from is factually wrong: the bound constrains each MATCH to one sentence, not the predicate, so one clearing clause anywhere excuses the whole message. E-03 as written is unexecutable; V-03 as written could not have revealed why. The failure mode if an executor "fixes" it by editing the expected value is worse than a red test: the guard becomes a tautology and the false comment survives. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-03 now states the false claim, the measurement, the structural cause, and the correct instruction: pin `we cleared OQ-01. readiness no-go` at True as the row the bound actually protects, and pin the clear-then-assert case at its MEASURED False with an inline known-limit comment. New F-14 records all measurements including the working mutation. E-04 gains an obligation to correct the note's false closing sentence, stating what the bound really buys plus the residual limit, while explicitly forbidding a regex change (this plan changes no classification and the shape is unobserved in the corpus). V-03's mutation is replaced with the widen-the-whole-bound one and warns that the authored mutation proves nothing. Required tests and Proposed change 3 updated to match; the gate gains this as a named second silent-failure mode with an explicit prohibition on editing an expected value to match observed output. |
| PR-702 | LOW | IN-SCOPE | F. Honest documentation (a wrong figure in a load-bearing finding) | F-02 as authored: "`newest_verdict` -> `neutral` ... for `s0gnha`, `ty7w6o` and `svacmz`"; measured at review: `s0gnha` neutral / 0 refusals / 0 verdict-class, `ty7w6o` neutral / 0 / 0, `svacmz` **positive** / 0 / 0 | One of three polarity figures is wrong. The finding's load-bearing claim (zero refusals for all three) holds exactly, and `positive` is further from a refusal than `neutral`, so the error is harmless in substance - but an executor re-measuring at execution sees a mismatch on a plan this item is named after, and a mismatch in a finding is indistinguishable from a regression until someone checks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 restated to give refusal counts as the claim and the per-plan polarities correctly (`neutral`, `neutral`, `positive`), with the review re-derivation noted. New F-15 records the correction explicitly so a re-measuring executor reads `positive` as expected rather than as drift. |
| PR-703 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: path-scoped `aw commit`, no-push, staged-set verification, the bare-pytest honesty rule, the corpus-diff silent-failure warning and the inherited `Blocks-Release: next` statement all PRESENT and unusually complete; ABSENT: a declared scope fence with the make-and-justify disposition, conditional runner-versus-executor finalize ownership, and any statement of the pin-a-false-claim failure mode | Three elements missing from an otherwise strong gate. Finalize ownership matters because an unconditional instruction makes an executor under `aw oc run` double-finalize. The scope fence matters here in a specific way: two NEGATIVE constraints inside the declared files are load-bearing (the regex pattern must not move, and `TestLivePendingCorpus`'s assertion must not be weakened) and neither was stated as a fence obligation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a DECLARATION-style scope fence naming `--scope-reason`/`--scope-ack` and both negative constraints with the V-items that verify them, a statement that the plan's one STOP directive (non-empty corpus diff) is narrow and correct, conditional finalize ownership forbidding a hand-rolled `git mv`, and the PR-701 failure mode with the prohibition on adjusting an expected value until a test passes. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-701: the predicate does not honor its comment's clear-then-assert claim. Fix the regex to close the gap, drop the row, or pin the measured limit and correct the comment? | PIN THE MEASURED LIMIT AND CORRECT THE COMMENT. Change no regex. | (a) Tighten `_CLEARED_NEGATIVE_READINESS_RE` (or the predicate) to refuse a clear-then-assert record: rejected on this plan's own fence. The plan claims to change NO classification and proves it with a corpus diff; a regex change is exactly a classification change, it lands on the surface `xpta5g` was reviewed for, and the shape has never been observed in the repository's history lines, so the fix would carry real lockout risk (the call-site comment records that an approval-gate false positive is an UNOVERRIDABLE LOCKOUT) to close a hypothetical. (b) Drop the row entirely: rejected, that leaves the false comment standing and loses the one row that makes the bound's real purpose legible. (c) Keep the row as authored: rejected, it fails at HEAD. | Measured the predicate on four clear-then-assert phrasings (all False) and read its three-line body, which shows `search` succeeding anywhere suppresses the result; measured the adjacency row True and bound-dependent, with both controls stable; confirmed the shape appears nowhere in the corpus that the plan's own F-02/F-05 probes cover. | yes |
| D-2 | Is PR-701 a BLOCKER, or a MEDIUM the executor would work around? | BLOCKER. | Classify MEDIUM: rejected. The item cannot be completed as written - the mandated assertion fails - and the two plausible executor workarounds are each harmful: abandon the row (losing the coverage E-03 exists to add) or edit the expected value to match observed output (producing a tautological guard and leaving the false comment in place, which is the exact rot F-04 identifies). A defect that makes an item unexecutable and whose natural workaround degrades the deliverable is a blocker regardless of how small the edit to fix it is. | The workflow's severity definition (a BLOCKER includes a normal-path failure or a silent invariant violation); measured failure of the mandated assertion; measured inertness of V-03's mutation on that same row. | yes |
| D-3 | OQ-01 resolved to GRADUATE rather than close `a3ugp1` as already-fixed. Accept? | ACCEPT, independently confirmed, and it is the best judgement in the plan. | Close the item `done`: rejected on the plan's own three grounds, all of which I verified: the `/askme` shape is mentioned by ZERO tests; the guard the module's comment names no longer covers the three plans (zero `reaskscore` in `pending/`); and the predicate has zero callers and zero tests. "Stopped reproducing" is not "guarded", and closing would assert a guarantee that does not exist. | Verified all three measurements independently (F-06, F-09, F-03/F-04); confirmed the named test and its file are absent at HEAD (F-01); confirmed the item inherits `Priority: high` and `Blocks-Release: next` unchanged, so no priority or risk-appetite call is being made on the human's behalf. | yes |
| D-4 | OQ-02 resolved to KEEP AND TEST rather than delete the uncalled predicate. Accept? | ACCEPT, and PR-701 strengthens it. | (a) Delete it: rejected. It is genuinely uncalled, so deletion is a fair reading, but `xpta5g` E-04 made that exact call on the same evidence ("Keep `negative_readiness_asserted` itself ... removing it is out of scope"), and reversing a reviewed decision with no new facts is churn. PR-701 adds a further reason: deleting it would leave a comment describing a behavior nothing implements. (b) Re-call it from `newest_verdict`: rejected, and the plan already refuses this; PR-701 makes the refusal stronger, since re-calling would newly expose the unclosed clear-then-assert limit on the approval-gate path where a false positive is an unoverridable lockout. | `xpta5g` E-04 quoted verbatim and confirmed `executed`; the predicate measured correct on all six documented shapes; `newest_verdict` confirmed to no longer call it (its docstring states an unrecognized token yields `(None, candidate)`); the call-site comment in `history_verdict_approves` confirming the two gates accept opposite risks deliberately. | yes |
| D-5 | PR-702: F-02's polarity figure is wrong. Correct the number, or restate the finding? | RESTATE THE FINDING around the refusal counts (its actual claim) and give the polarities correctly, plus a separate finding recording the correction. | Silently fix `neutral` to `positive`: rejected. An executor re-measuring needs to know the plan EXPECTS `positive` for `svacmz`; a corrected number with no note reads identically to an uncorrected one when the next reader measures something different again. | Measured all three plans' polarity, refusal count and verdict-class count at review. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. Both of the plan's open questions were already `resolved` at authoring and both were
independently re-measured and upheld (D-3, D-4), so the plan carries no open question.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0` BEFORE any
  edit; `--phase review-finalize --agent` -> exit 0, `"findings":0` after all edits.
- `check_engine.evaluate_durable_carrier` -> `drifts: 0`. `aw check` -> 3 errors, enumerated and
  attributed: `check.ipd-uncarried-obligation` on `iq3txw` and `4er1ev` (other agents' pending plans)
  and `check.system-layout-missing` on `.aw/system/layout.json`. None names this plan or Set.
- Suite baseline BARE: `2935 passed, 2 skipped, 3 warnings in 41.90s`. Edited file:
  `python3 -m pytest tests/test_review_record_classifier.py -o addopts="" -q` -> `5 passed in 0.83s`.
  No code, test, configuration, spec or doc file was modified by this review.
- **F-01 reproduced.** `git log --oneline --diff-filter=D -- tests/test_plan_readiness.py` -> `19313eed`;
  tree-wide `grep` for `ApprovalGateRealCorpusTests` and the test name -> 0 hits.
- **F-02 re-derived, with one correction (PR-702).** `s0gnha` neutral / 0 refusals / 0 verdict-class;
  `ty7w6o` neutral / 0 / 0; `svacmz` **positive** / 0 / 0. Per-history-line
  `is_review_history_entry` printed for all three: `ty7w6o` carries the real
  `- 2026-09-19 reviewed (opencode ...): /askme: OQ-04 RESOLVED BY THE MAINTA...` record and it
  classifies **False**, confirming the stated mechanism.
- **F-03 reproduced exactly.** Tree-wide `grep --include=*.py` -> exactly two hits, both in
  `agent_workflows/plan_readiness.py`: the `def` and the `# DELIBERATELY THE PLAIN SCAN, NOT
  negative_readiness_asserted` comment. `xpta5g` E-04 read at the symbol and quoted verbatim.
- **F-04 reproduced exactly.** `grep -rn "negative_readiness_asserted" tests/` -> 0 lines.
- **F-05 reproduced exactly.** All six documented shapes match: three CLEARED -> False (clearing verb,
  arrow transition, "resolved ... the no-go with it"), three ASSERTED -> True (bare, `REJECT - NEEDS
  REPLAN`, and the regression direction `go-pending-approval -> no-go`).
- **PR-701 / F-14 measured, four ways plus the mutation.** Four clear-then-assert phrasings all return
  `False`; the predicate body read at the symbol confirming `return not
  _CLEARED_NEGATIVE_READINESS_RE.search(message)`; the regex's first clause shown matching
  `'clearing OQ-01 and with it its no-go'` inside the longer message; `[^.]`-widened recompilation
  giving `False` for that row both ways (so V-03's authored mutation is inert); and
  `"we cleared OQ-01. readiness no-go"` -> `True` shipped, `False` with
  `[^.]{0,80}?` -> `[\s\S]{0,400}?`, while `readiness no-go` and `REJECT - NEEDS REPLAN; readiness
  no-go` stay `True` under both.
- **F-06 reproduced exactly.** `grep -rn "askme" tests/` -> empty. Four record shapes probed through
  `is_review_history_entry`: `/askme`-led -> `False`; `/askme` naming `/plan-review` -> `True`; plain
  `/plan-review` -> `True`; `/plan-review ... REJECT - NEEDS REPLAN; readiness no-go` -> `True`.
- **F-07 reproduced exactly.** `grep -n "pytestmark\|@pytest.mark\|^import pytest"` on the classifier
  file -> empty; `--collect-only -q` -> `5`; `tests/test_ipd_lint.py` carries
  `@pytest.mark.livecorpus` at method level. `TestLivePendingCorpus`'s body read and confirmed to glob
  `.aw/records/plans/pending/*.ipd.md` and call `approval_refusals` on each; `_make_plan_text` confirmed
  present as E-02's in-memory helper.
- **F-08 reproduced exactly**, including the deselection notice and the `addopts` value in
  `pyproject.toml`, whose `livecorpus` marker text was read and confirmed to cite this incident by name
  and cost.
- **F-09 reproduced exactly.** Zero `reaskscore` in `pending/`; six in `executed/`, listed.
- **F-10 reproduced verbatim.** The `#:` note above `_CLEARED_NEGATIVE_READINESS_RE` names
  `tests/test_review_record_classifier.py::TestLivePendingCorpus::test_no_pending_plan_has_verdict_class_refusal`
  and says it "reads the LIVE pending tree".
- **F-12 / F-13 confirmed.** `a03b4c5b`'s message read (its subject is "fix(plan-readiness): stop
  reading a CLEARED no-go as an asserted one" and it records the run id, 2h 10m and $55.02);
  `xpta5g`'s "EXPLICITLY NOT IN SCOPE" line read and confirmed to list every vocabulary the plan says it
  does.
- **E-02's fixture provenance confirmed.** `git show a03b4c5b^:<ty7w6o pending path> | grep -c
  "clearing this plan"` -> `1`, so the verbatim incident message is recoverable exactly where E-02 says.
- **Release gate verified.** Backlog `a3ugp1` is `graduated` with `- Priority: high`, `- Work-Kind: bug`
  and `- Blocks-Release: next`; the plan inherits all three unchanged.
- All probes ran in-process or via `git show` against in-memory strings; no repository file was written
  by a probe, and `git status --short` reports only the plan and this record.
