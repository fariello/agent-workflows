# Review findings: plan vsgd48

- Subject-Id: vsgd48
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fd7457f1` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and unmodified, and the
lane-input snapshot is byte-identical to the tracked file. No production code and no tracked record
other than the plan was modified by this review; every measurement was taken by driving the shipped
setters against throwaway git repositories under the system temp dir, and by reading source with
`rg`, `inspect` and `ast`.

THE DIAGNOSIS IS CORRECT, EVERY ROUTE REPRODUCED, AND THE PLAN'S CORRECTION OF ITS BACKLOG ITEM IS
THE RIGHT CALL. Driven through `backlog.run_set` and, for the positional spelling, through the real
`python3 -m agent_workflows backlog set` CLI: route (a) `chore -> bug` while `open` writes
`- Blocks-Release: next` and announces it, so F-01 and F-02 hold; routes (b) `open -> graduated`,
(c) `parked -> open` and (d) `done -> open` each write NO gate, print no notice, and each leave a
tree on which `check_engine.check_live_bug_gate` returns `['check.live-bug-ungated']` - on BOTH
spellings, so F-03, F-04 and F-05 hold exactly as written. F-07 re-measured as zero gateless live
bugs repo-wide. F-10 re-confirmed: neither `decide_gate_default` nor `di08i9` appears anywhere under
`tests/`. The predicate's four conditions, the skip set, the shared write primitive and the notice
shape are all as the Step-0 notes describe. Declining to claim the backlog item's unreproducible
"regrowth" measurement, and saying so explicitly in F-07/F-08/F-09, is unusually honest plan
authorship.

WHAT REVIEW FOUND IS ONE INSTRUCTION THAT CANNOT BE FOLLOWED AND FAILS SILENTLY, one undisclosed
downstream behavior change, one entirely missing live route, and four smaller corrections. None
required redesigning the approach.

**E-02 NAMES A VALUE THAT DOES NOT EXIST, AND THE FAILURE IS SILENT (PR-901, HIGH).** E-02 tells the
executor to pass "the record's existing parsed `- Work-Kind:`" when the flag is absent.
`status_set.apply_status_change` has no such binding: its only work-kind value is
`work_kind = getattr(args, "work_kind", None)`, which is the FLAG and is exactly `None` in the
status-only case this plan exists to cover. `rg -n "Work-Kind" agent_workflows/status_set.py` returns
five hits, all comments or the `set_work_kind_line` WRITE; nothing parses the record's own value and
`rec` exposes no such attribute. The consequence is worse than a compile error: passing `kind=None`
makes the predicate decline on condition 1, so the fix would appear to land and do nothing on the
positional spelling - precisely the "fires for one spelling and not the other" outcome the plan's own
Step-0 note calls worse than not shipping. `backlog.run_set` by contrast already binds
`item = parse_item(text)` before its gate block (AST-verified), which is why E-01's `item.kind` is
sound and E-02 is not a mechanical copy.

**GATING AT `graduated` MAKES A LATER CLOSE REFUSE, AND THE PLAN NEVER SAYS SO (PR-902, HIGH).**
Measured end to end: an ungated bug taken `open -> graduated -> done` closes cleanly today (`rc=0`,
no refusal). With the gate present at `graduated`, the same `set done` exits `rc=1` with "refused:
backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate"
and offers the three shipped remedies. The refusal is CORRECT - it is the close-legitimacy policy
AGENTS.md describes, and handing a graduated item's gate to its plan is exactly what the repository
wants - so this is a disclosure finding rather than a blocker. But the plan asserts a two-call-site
change whose Scope check says nothing outside those sites moves, and a previously-silent close path
becoming interactive for every graduated bug is a consequence a maintainer approving this must see
stated, not discover.

**`blocked` IS A FIFTH LIVE ROUTE AND THE TEST TABLE OMITS IT ENTIRELY (PR-903, HIGH).** The live set
is `STATUSES - _GATE_DEFAULT_SKIP_STATUSES`, driven as exactly `['blocked', 'graduated', 'open']`,
and creation already gates `blocked` consistently with the other two. Measured, `parked -> blocked`
and `done -> blocked` on an ungated bug both leave no gate and both trip `check.live-bug-ungated`,
identically to routes (b)/(c)/(d). E-03's four-route table would therefore have shipped a fix with a
third of its own live surface untested. There is a trap in adding it, too: a transition to `blocked`
exits `rc=2` with "moving to blocked requires --gate-kind and --gate-ref" and writes nothing, so a
row that omits those flags would pass for the wrong reason, asserting an absent gate on an item the
setter never moved.

**FOUR SMALLER CORRECTIONS.** E-04's three negative properties all already hold (driven: the
`--blocks-release -` case stays ungated, the pre-gated `rel001` case keeps `rel001`), so E-04 is a
FENCE and must not claim a pre-fix failure for them (PR-904). V-03 instructs `git stash` to obtain
the pre-fix contrast, which AGENTS.md forbids in this shared checkout because a stash operates on the
whole working tree and can discard a co-worker's uncommitted work; the contrast must be taken in
memory (PR-905). The plan records NO suite baseline while asking for a full-suite no-regression
proof, re-driven here as `3115 passed, 2 skipped, 3 warnings` with zero failures and all four named
regression files present (PR-906). F-06 cites `RULE_SPECS`, which does not exist - the symbol is
`RULE_REGISTRY`, though the severity claim itself reproduces exactly as
`RuleSpec(severity='error', ..., invariant='I-07')` (PR-907).

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed. OQ-01 was re-verified and survives unchanged (the predicate composes its own notice, so a
trigger-specific string would have to be assembled at the call site, which is the drift its
"SINGLE AUTHORITY" docstring exists to prevent). OQ-02 is new, recording why the `graduated` close
friction is accepted rather than avoided. All five `Carrier-Declined` rows were checked against
evidence and all five are legitimate: the backfill row's empty-population claim re-measured as zero,
and the hand-authoring row is right that a write-path default structurally cannot cover a route that
never calls a write path.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability | plan E-02 ("the record's existing parsed `- Work-Kind:`"); `status_set.apply_status_change`'s sole `work_kind = getattr(args, "work_kind", None)`; `rg -n "Work-Kind" agent_workflows/status_set.py` -> 5 hits, all comments or the write; `backlog.parse_item("- Work-Kind: bug...").kind` -> `'bug'`; AST-verified `item = parse_item(text)` precedes `run_set`'s gate block | E-02's INSTRUCTION CANNOT BE FOLLOWED AND ITS FAILURE IS SILENT. No parsed work-kind exists on the positional path; the only binding is the flag, which is `None` in exactly the status-only case this plan targets. Passing `kind=None` makes the predicate decline on condition 1, so the fix lands and does nothing on one spelling - the "fires for one spelling and not the other" outcome the plan's own Step-0 note calls worse than not shipping. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (name the shipped reader; no design change) | FIXED | E-02 now names `backlog.parse_item(...).kind` as the reader, forbids a second local regex, notes it also resolves the legacy `- Kind:` fallback, and explains the asymmetry with E-01. Added F-13. V-02 requires pasting the committed read plus a driven status-only positional transition that would fail if `kind=None` reached the predicate. A Scope-check bullet records that E-02 introduces a new read on a declared path. |
| PR-902 | HIGH | IN-SCOPE | C. Architecture and operability / F. UX | driven `backlog.run_set` twice: PRE-FIX `open -> graduated -> done` -> `rc=0` no refusal; with a gate at `graduated`, `set done` -> `rc=1` "refused: backlog item carries Blocks-Release 'next'..." with the `--from-backlog` / `--evidence` / `--blocks-release -` remedies | THE PLAN DOES NOT DISCLOSE THAT IT MAKES A LATER CLOSE REFUSE. Gating at `graduated` converts a previously-silent `set done` into an interactive refusal for every graduated bug. The refusal is correct policy (AGENTS.md wants a graduated item's gate handed to its plan), so this is a disclosure gap rather than a defect, but the plan's Scope check asserts nothing outside the two call sites moves and a maintainer approving it would not see this. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium (disclose and evidence it; the behavior itself is intended) | FIXED | Added F-12 with the driven before/after. E-01 carries the disclosure and requires it in the code comment; a Scope-check bullet declares it as foreseen rather than a breach; new OQ-02 records why it is accepted over skipping `graduated`; a Required-tests bullet and V-04 demand the refusal and the de-gate remedy be driven and pasted; the gate paragraph states it plainly. |
| PR-903 | HIGH | UNDER-SCOPE | E. Testing and verification | `sorted(backlog.STATUSES - backlog._GATE_DEFAULT_SKIP_STATUSES)` -> `['blocked','graduated','open']`; `aw backlog new --work-kind bug --status blocked` -> gated `next`; driven `parked -> blocked` and `done -> blocked` -> no gate, `['check.live-bug-ungated']`; `run_set(status='blocked')` without flags -> `rc=2` "moving to blocked requires --gate-kind and --gate-ref" | THE FIFTH LIVE ROUTE IS ABSENT FROM THE TEST TABLE. `blocked` is as live as `open` and `graduated`, creation already gates it, and transitions into it reproduce the same hole, so the authored four-route table would ship a third of the fix's live surface untested. Adding it naively also fails: without `--gate-kind`/`--gate-ref` the setter writes nothing, so the row would pass by asserting an absent gate on an unmoved item. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (one more test row with two flags) | FIXED | E-03 covers FIVE routes; case (e) added with the required flags and driven working values called out, plus the wrong-reason-pass trap stated. Added F-11. Expected outcome now names (b)/(c)/(d)/(e) as the red-to-green set. V-03 requires pasting the `blocked` row's flags and its `rc=0`. |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing (fence vs fix) | driven: `parked -> open --blocks-release -` -> ungated; pre-gated `rel001` `parked -> open` -> keeps `- Blocks-Release: rel001`, not rewritten to `next` | E-04's THREE NEGATIVES ALREADY HOLD, SO IT IS A FENCE AND MUST SAY SO. Unlike E-03's transition rows these do not go red-to-green. Left unlabelled, an executor following the plan's "PRE-FIX FALSIFICATION IS REQUIRED" instruction could try to produce a pre-fix failure for them and, failing, either fabricate one or doubt a correct implementation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states all three hold at this HEAD with the driven values, requires the fence labelling in each docstring, and forbids claiming a pre-fix failure. Added F-16. V-04 requires the one-sentence statement. |
| PR-905 | MEDIUM | IN-SCOPE | B. Security and safety (shared checkout) | plan V-03 ("e.g. `git stash` of the E-01/E-02 edits, or `git stash push -- agent_workflows/`"); AGENTS.md shared-checkout rule | V-03 INSTRUCTS AN OPERATION AGENTS.md FORBIDS HERE. A stash operates on the whole working tree, so in a checkout other agents are using it can discard or unstage a co-worker's uncommitted work. The plan's own execution contract cites the shared-checkout rule elsewhere, so this is an internal contradiction as well as a hazard. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium (name a safe route; no loss of evidence value) | FIXED | V-03 now forbids `git stash`, requires the pre-fix contrast in memory (patch the broadened guard off) or before applying the edits, and requires stating which route was used. The gate paragraph repeats the prohibition with the reason. |
| PR-906 | MEDIUM | IN-SCOPE | E. Testing (baseline) | bare `python3 -m pytest` -> `3115 passed, 2 skipped, 3 warnings in 69.19s`, zero failures; all four named regression files present | THE PLAN ASKS FOR A NO-REGRESSION PROOF WITHOUT STATING THE CLEAN STATE. With no baseline recorded, an executor meeting a failure has nothing to compare against and may accept it as pre-existing noise - a trap a sibling plan reviewed in this same sweep had actually shipped, where a spent "one pre-existing failure" row would have excused a real regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with the re-driven green figure and the file-existence check. Required tests and V-04 now demand a baseline re-measured in-lane immediately before the change, explicitly not a comparison against any figure written in the plan, and state that any failure is a signal. |
| PR-907 | LOW | IN-SCOPE | A. Correctness (citation accuracy) | `hasattr(ce,'RULE_SPECS')` -> `False`; `hasattr(ce,'RULE_REGISTRY')` -> `True`; `ce.rule_spec('check.live-bug-ungated')` -> `RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-07')` | F-06 CITES A SYMBOL THAT DOES NOT EXIST. The registry is `RULE_REGISTRY`; `RULE_SPECS` is absent. The claim it supports (the rule is an exit-blocking `error`) reproduces exactly, so no conclusion moves, but a finding that names a nonexistent attribute sends the next reader looking for it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06's evidence now cites `check_engine.rule_spec(...)` and notes the registry symbol, with the correction carried in new F-15. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02 must obtain the record's own `- Work-Kind:` but no such value exists on that path. Which reader should it use? | `backlog.parse_item(<text>).kind`, the same accessor `backlog.run_set` already uses for `item.kind`. | (a) A fresh local regex in `status_set` - rejected: it forks the field's reader, which the predicate's "SINGLE AUTHORITY" discipline forbids in spirit, and it would silently skip the legacy `- Kind:` fallback that `parse_item` resolves (`item.kind = work_kind if work_kind is not None else legacy_kind`). (b) Add the kind to `rec` / the resolver - rejected as out of scope: it changes a shared record type consumed by plans and specs to serve one call site. (c) Leave E-02 consuming only the flag - rejected: that IS the bug, since the flag is `None` in every status-only transition. | `rg -n "work_kind = " agent_workflows/status_set.py` -> the `getattr(args, ...)` only; `backlog.parse_item("- Work-Kind: bug...").kind` -> `'bug'`; the legacy-fallback line in `backlog.parse_item`; AST-verified `run_set` binds `item` before its gate block. | yes |
| D-2 | Gating at `graduated` makes a later `set done` refuse. Accept the friction, or exclude `graduated` from the default? | ACCEPT IT and DISCLOSE it, in E-01, the Scope check, OQ-02 and V-04. | (a) Add `graduated` to `_GATE_DEFAULT_SKIP_STATUSES` - rejected on three grounds: it is a predicate change this plan's scope refuses, it would contradict the CREATION default (driven: `aw backlog new --work-kind bug --status graduated` is already gated), and it would put the default and the checker's live set back out of agreement, which the Step-0 notes identify as the root shape of this entire defect. (b) Fix the hole but suppress the close refusal - rejected: that means weakening `evaluate_blocking_close`, an unrelated shipped gate, to hide a consequence of implementing written policy. (c) Ship it silently - rejected: it is a workflow change every maintainer closing a graduated bug will meet, and the plan claimed none. | AGENTS.md naming `graduated` as LIVE and requiring the gate there; the driven `rc=1` refusal text and its three remedies; the driven creation-time gating of `graduated`; the live set `['blocked','graduated','open']`. | yes |
| D-3 | `blocked` is live but absent from E-03's table. Add a fifth row, or treat the four as sufficient? | ADD THE FIFTH ROW, with `--gate-kind`/`--gate-ref` and the wrong-reason-pass trap documented. | (a) Treat four as sufficient - rejected on measurement: `parked -> blocked` and `done -> blocked` both reproduce the hole and trip the same ERROR, so a third of the live surface would ship unpinned. (b) Add the row without the gate flags - rejected: driven, the setter exits `rc=2` writing nothing, so the assertion would hold vacuously on an item that never transitioned, which is worse than no test because it reads as coverage. | Driven live set `['blocked','graduated','open']`; `parked -> blocked` / `done -> blocked` -> `['check.live-bug-ungated']`; `rc=2` "moving to blocked requires --gate-kind and --gate-ref"; creation gating `blocked`. | yes |
| D-4 | V-03 instructs `git stash` in a shared checkout. Replace it, or keep it with a warning? | REPLACE IT: require the pre-fix contrast in memory or before applying the edits, and forbid the stash. | (a) Keep it with a caution - rejected: AGENTS.md's shared-checkout rule is a prohibition, not a caution, and the plan's own execution contract cites that rule, so keeping it leaves the plan self-contradictory. (b) Drop the pre-fix requirement to avoid the question - rejected: the falsification is the most valuable evidence this plan asks for, and only its mechanism was unsafe. | AGENTS.md shared-checkout rule ("never revert, stage, commit, discard ... another party's work"); the plan's own gate paragraph citing the same rule; the in-memory route demonstrated at review for every measurement taken. | yes |
