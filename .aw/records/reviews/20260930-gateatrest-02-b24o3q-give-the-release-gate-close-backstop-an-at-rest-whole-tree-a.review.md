# Review findings: plan b24o3q

- Subject-Id: b24o3q
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
both `--phase author` and `--phase review-finalize` report `clean` after revision. The plan is
`- Kind: child`, so `IPD-S407` does not apply. Its declared dependency `executed:f7igdu` resolves to a
real sibling (`gateatrest` Order 01, `- Status: reviewed`, `- Readiness: go-pending-approval`), and the
ordering argument is sound: an at-rest arm shipped before the `SATISFIED` citation is durable would report
a legitimate evidence-satisfied close as an error.

THE CENTRAL ARGUMENT IS CORRECT AND THE KEY FINDINGS REPRODUCE. I drove the defect rather than reading it:

- F-01 reproduces EXACTLY. In a scratch repo with a gated `done` item STAGED,
  `check_release_gate_consistency` returned `['check.blocking-item-closed-without-gate']`; after
  `git commit` the same call returned `[]` while `evaluate_blocking_close` on the same file still returned
  `legitimate=False, severity='error'`. The mechanism is confirmed too:
  `_staged_backlog_done_items` runs `git diff --cached --name-status -M` over the two backlog roots, so a
  fresh CI checkout has nothing to examine. The structural-blindness claim is not rhetoric.
- F-03's REASONING fully verifies and its conclusion STRENGTHENS. Re-measured: 226 of 242 gated `done`
  items were closed later than their filename date, 0 have no parseable close date, and at a 2026-09-30
  boundary the filename key judges 0 while the close-date key judges 27 (it judged 9 one day earlier), so
  the "hole that keeps widening" is demonstrated rather than predicted. The safety fact also re-confirms:
  the illegitimate population's newest close date is 2026-09-26, newest filename date 2026-09-25, and ZERO
  illegitimate items fall on or after the boundary by either key.
- F-04's shape verifies. 242 per-item `evaluate_blocking_close` calls took 63.1 s against 0.389 s for one
  `_from_backlog_carrier_index` walk (481 keys), with the pre-change `check_release_gate_consistency` at
  0.449 s. Two orders of magnitude, on a command a human waits on, and the single-item contract test exists
  as described.
- F-05 verifies and is the sharpest risk in the plan. `hooks/backlog_blocking_close_gate.check` calls
  `_ce.check_release_gate_consistency(root)` DIRECTLY, and the commit aggregator composes it too, with the
  aggregator's own comment stating verbatim why whole-tree rules must not be added there.
- F-08 verifies: `_backlog_done_dirs` has exactly one definition site and no caller anywhere.
- F-02's PROPERTY verifies (a large gated-and-illegitimate population invisible to the authoritative
  surface; `aw check release-gates --agent` reports `findings: 0` today), though every count has drifted.
- E-01's mechanism, E-02's two shared readers, and F-03's `SetidPolicy` precedent all verify verbatim,
  including the quoted "ONE RULE" docstring and the "a missing date is its own defect owned by another
  rule" reasoning.

THE BLOCKER IS THAT THIS PLAN CAN LAND AND DO NOTHING, and no test it writes would notice. The at-rest arm
is cutover-gated and skips every item when `resolve_cutover_date` returns `None`. Measured in THIS
repository: `.aw/config/project.json`'s `cutovers` block holds five keys and NOT `setid_length`, even
though `setid_length` IS registered in `KNOWN_FEATURE_CUTOVERS`, so
`resolve_cutover_date(repo, "setid_length")` returns `None`; and `.aw/state/history/installs.jsonl` DOES
NOT EXIST, so the install-history tier resolves `None` for every feature. So a registered-but-unstamped
feature is not hypothetical, it is the live state of a sibling. With `None`, E-03's arm judges zero items,
E-08's census reports zero findings, every fixture test passes, and the plan ships as the decoration the
config block comment warns about. V-01 half-saw this and then accepted it, requiring the executor to
explain a `None` result where "the answer must be 'everything grandfathered', not 'undefined'" - which
treats the self-defeating outcome as a pass. I then verified the fix is reachable:
`sync_cutovers_on_install` against a COPY of this repo's `project.json` added the missing key and preserved
the five existing boundaries, so the remaining question is the VALUE, not the mechanism.

THE HIGH FINDING IS A DEFAULT POINTING THE WRONG WAY, which would reintroduce the exact defect F-05
documents. E-05 suggested "for example `at_rest=True` by default". Under that default all four callers
acquire the widened behavior, and three of them must not: the commit aggregator, the opt-in hook, and the
scope gate that inherits the aggregator. The plan then relies on remembering to disable it at each. A
`False` default makes the safe behavior automatic and needs one explicit opt-in at `check_release_gates`.
I also measured a mechanical obstacle the item does not mention: `check_commit_invariants` composes its
rules as a tuple of BARE CALLABLES invoked uniformly as `fn(repo_root)`, so there is no per-callable
argument site at all. With the corrected default the tuple needs no edit, which is the strongest argument
for `False`; with `True` the executor would have to unroll that loop and would thereby lift one rule out of
its `except Exception: continue` guard, whose stated purpose is that one rule's failure must not take down
the gate.

ON THE OPEN QUESTIONS, I ADDED ONE AND ANSWERED NONE THAT WAS THE MAINTAINER'S. OQ-02 (amend the draft
spec `pqsx96`) stays `open` with `Owner: maintainer` and is correctly reasoned: nothing in that row becomes
false when this plan lands, and editing a spec another agent is actively authoring is the collision the
shared-checkout rule warns about. I added OQ-04 because the fix to PR-001 exposes a decision only the
maintainer can make: `sync_cutovers_on_install` stamps the INSTALL DATE, so whatever day the stamp runs
becomes the enforcement boundary, and that choice decides which historical closes are judged. Today the
answer is benign (any boundary at or after 2026-09-27 grandfathers all 53), which is why it is
`Blocking: no`; but a boundary stamped earlier would red CI, and each passing day enlarges the enforced
set (9 judged items at authoring, 27 one day later). This run is non-interactive
(`AW_EXECUTION_ROLE=worker`, neither stream a TTY), so I recorded it rather than guessing. E-08's
zero-findings stop condition is the backstop that makes an unanswered OQ-04 safe.

READINESS IS `go-pending-approval` DESPITE THE `REVIEWED - OPEN QUESTIONS` VERDICT, on the same basis
recorded in the `uh9jsk` review: the workflow's readiness table lists that verdict as a `NO-GO` condition
while the paragraph below it records the 2026-09-10 maintainer ruling that a NON-BLOCKING open question
does not make a plan `NO-GO`, and repository precedent is one-directional (66 of 77 plans with this verdict
carry `go-pending-approval`, the discriminator being the blocking flag). This plan carries zero
`Blocking: yes` questions.

TWO SIBLING PLANS HAD LANDED UNDER THE DOCUMENT, WHICH `aw check` WAS ALREADY SAYING. Running `aw check`
surfaced TWO `check.ipd-carrier-finished-unverified` findings naming this plan, because its two
`- Carrier:` rows point at backlog items that are now `done`: `2o5wka` (the any-carrier-to-all-carrier
tightening) and `47ttnv` (the positional-spelling gate) have BOTH executed, and `lsbd32` and `mawwlc` are
both closed. That is not a bookkeeping nit, because the plan reasons from their pendency in three
load-bearing ways: it predicts the illegitimate population "becomes 53 rather than 49" if `2o5wka` lands,
when the strict predicate is already live and 53 IS that post-change figure (confirmed by reading the
shipped `if same_gate_carriers and all(_carrier_is_executed(_c) ...)` arm); it describes the positional
bypass as future work when `status_set.py` already calls the shared predicate; and E-07 instructs the
executor to "state which of them has landed" before editing `AGENTS.md`, which is answerable now and whose
answer is that BOTH landed and both declared `AGENTS.md`, so their sentences are at HEAD to be edited
around rather than reverted. All five stale references are swept and both findings are cleared.

WHAT I DELIBERATELY DID NOT FLAG. The plan's refusal to soften the rule to `warning` (correct, and its
reasoning about `drift_exit_code` exempting only `info` is verified). Its decision to keep the staged arm
rather than replace it (F-07 is right: the staged arm reads the `:0:` blob and answers a different question
at a different time). Its refusal to touch `_backlog_done_dirs` or to mutate any historical item. And its
`Carrier-Declined` rows, each of which records a prohibition or a settled decision rather than deferred
work.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / G (executability) | `config.resolve_cutover_date(repo, "setid_length")` returns `None` in this repo though `setid_length` is in `KNOWN_FEATURE_CUTOVERS`; `.aw/config/project.json` `cutovers` holds 5 keys without it; `.aw/state/history/installs.jsonl` absent | THE PLAN CAN LAND AND DO NOTHING, AND NOTHING IT WRITES WOULD NOTICE. The at-rest arm skips every item when the cutover resolves `None`, and `None` is this repository's live state for a registered-but-unstamped feature (measured on `setid_length`, the exact precedent E-01 leans on). With `None`: zero items judged, zero findings, all fixture tests green, plan shipped as decoration - the outcome the config block comment warns about and that E-01 quotes against itself. V-01 compounded it by accepting a `None` result as a pass ("the answer must be 'everything grandfathered'"). | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-01 now states that registration alone produces no boundary here, names `setid_length` as the live proof, and makes the item complete only on a NON-`None` resolution; it also records (verified against a copy) that `sync_cutovers_on_install` does write the key and preserves existing boundaries, so the fix is reachable. V-01 now FAILS on a `None` resolution, requires the `cutovers` block before and after plus the mechanism that wrote it, and requires one real at-rest finding produced through the actually-resolved value. V-08 additionally requires the judged-item count, so "zero findings with zero judged" is reported as a failure of E-01 rather than a success of E-08. New OQ-04 carries the boundary-value question. |
| PR-002 | HIGH | IN-SCOPE | B/C (operability) / D | `check_commit_invariants`' `for fn in (check_status_untooled, check_release_gate_consistency, check_scope_drift): ... drift.extend(fn(repo_root))`; `hooks/backlog_blocking_close_gate.check` calling `_ce.check_release_gate_consistency(root)` | THE SUGGESTED DEFAULT INVERTS THE SAFE DIRECTION AND THE AGGREGATOR CANNOT PASS AN ARGUMENT. E-05 proposed "for example `at_rest=True` by default", which silently widens the commit aggregator, the opt-in hook, and the scope gate that inherits the aggregator, i.e. exactly the F-05 defect this item exists to prevent, leaving safety dependent on remembering three disables. Measured obstacle: the aggregator composes bare callables invoked as `fn(repo_root)`, so there is NO per-callable argument site; obeying E-05 literally would force unrolling that loop and lifting one rule out of its `except Exception: continue` guard. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Default corrected to `at_rest=False`, with `check_release_gates` passing `at_rest=True` explicitly, so the three unwidened callers are safe BY CONSTRUCTION and the aggregator tuple needs no edit. E-05 records the measured tuple shape and forbids unrolling the loop (with the guard's stated purpose as the reason). V-05 now additionally requires the default value itself be pasted from `inspect.signature` and the single `at_rest=True` call site be shown by grep, because fixture results that merely look right would not prove safety-by-construction. |
| PR-003 | HIGH | IN-SCOPE | A / G | `.aw/records/plans/executed/20260929-anycarrier-01-2o5wka-...ipd.md` and `...-47ttnv-...ipd.md` both `- Status: executed`; `lsbd32` and `mawwlc` both `- Status: done`; `evaluate_blocking_close`'s live `if same_gate_carriers and all(_carrier_is_executed(_c) ...)`; `status_set.py` calling `_ce.evaluate_blocking_close` | TWO PLANS THE DOCUMENT TREATS AS PENDING HAVE ALREADY EXECUTED, AND `aw check` WAS ALREADY REPORTING IT. The plan describes `2o5wka` and `47ttnv` as pending in five places, defers work to them with `- Carrier: lsbd32` and `- Carrier: mawwlc`, and predicts the all-carrier change as a future event. All four artifacts are finished, so `aw check` raised TWO `check.ipd-carrier-finished-unverified` findings naming this plan. Three substantive consequences: the strict all-carrier predicate is LIVE, so the 53 this review measures already IS the post-`2o5wka` figure and there is no further delta to re-derive; the positional spelling is already gated, so the complementarity claim is realised rather than prospective; and E-07's instruction to "state which of them has landed" before editing `AGENTS.md` was asking the executor to discover something determinable now, with both plans' `AGENTS.md` edits already at HEAD to be edited around rather than reverted. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both deferral rows rewritten from `- Carrier:` to `Carrier-Declined` recording that the work is DONE rather than deferred, with the executed paths, the live predicate text and the `status_set` call site cited; both `aw check` findings are cleared (verified: zero mentions of this plan in `aw check` afterwards). The five stale "pending plan" references swept. E-07 now carries the ANSWER to its own co-edit question (both landed, both declared `AGENTS.md`, edit around them) plus the re-verified placement facts (marker at line 125, target paragraph at 239 to 245, no later `aw:` marker) and names the exact sentence this plan owns versus the adjacent one to leave alone. |
| PR-004 | MEDIUM | UNDER-SCOPE | G | `- Scope-Paths:` versus E-05's and V-05's requirements on `hooks/backlog_blocking_close_gate` | THE ONE FILE MOST AT RISK WAS NOT DECLARED. E-05 and V-05 both reason about the opt-in hook, which calls the widened function directly and is named twice in the plan, yet `agent_workflows/hooks/backlog_blocking_close_gate.py` was absent from `- Scope-Paths:`. Under the original `True` default it would have REQUIRED an edit in an undeclared path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The hook path ADDED to `- Scope-Paths:`. The Scope check records it as the one declared path the plan EXPECTS NOT to modify (unnecessary under the corrected default) and states that a declared-but-unmodified path reconciles with `--scope-ack`; V-05 requires that ack and an explicit statement of whether the file was touched. |
| PR-005 | MEDIUM | IN-SCOPE | A | Re-measured census: 798 item files, 445 `done`, 242 gated, 189 legitimate, 53 illegitimate, `findings: 0` | EVERY CORPUS NUMBER HAS DRIFTED IN ONE DAY and several were stated as current fact or as acceptance bars. Authoring recorded 420 `done` / 224 gated / 175 legitimate / 49 illegitimate; review measured 445 / 242 / 189 / 53. F-03's derived figures moved with them (208 to 226 closed-later; 9 to 27 judged at the boundary). The PROPERTY each finding rests on is intact, but an executor comparing against the recorded numbers would read correct measurements as discrepancies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 and F-03 now carry both measurements, attribute each to its moment, and state explicitly that the counts are context and must not be used as an acceptance bar. The Concern and the approval gate are reworded from "49 items" to "dozens (49 at authoring, 53 at review)". E-02's prose likewise. V-02 already required re-derivation and was left as the correct model. |
| PR-006 | MEDIUM | IN-SCOPE | A | The `2o5wka` deferral row versus today's unmodified-predicate count of 53 | A PREDICTION NOW READS AS A FALSE COINCIDENCE. The row says that if `2o5wka` lands "the illegitimate population becomes 53 rather than 49". But 53 is what the UNMODIFIED predicate measures TODAY, with `2o5wka` not landed. Anyone comparing a later measurement against 53 could conclude `2o5wka` had landed when it had not, or that it had no effect when it had. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The row now flags the collision explicitly, forbids carrying either number forward, and restates the interaction as a PROPERTY (an all-carrier rule strictly grows the illegitimate set by the items whose carriers are not all executed) with the delta to be re-derived by running the predicate both ways. The non-blocking conclusion is re-confirmed: every affected item is grandfathered by close date. |
| PR-007 | LOW | IN-SCOPE | E | F-04 and V-04's recorded timings | TIMING BARS WERE STATED AS CONSTANTS THAT NO LONGER REPRODUCE. V-04 required the after numbers be judged against "the authoring baselines 0.34 s and 1.08 s" and against "the 84.0 s a per-item carrier scan costs"; review measured 0.449 s and 63.1 s on the grown corpus, so both anchors are stale and the 84.0 s figure does not reproduce at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 carries both measurement sets and states that the RATIO is the finding rather than the seconds. V-04 now requires the executor to take its OWN before numbers in the same session and judge against those, and to re-derive the naive cost rather than quoting the recorded one. |
| PR-008 | LOW | IN-SCOPE | G | V-08's "six declared scope paths" | A COUNT MADE STALE BY PR-003's FIX. V-08 required the staged diff be a subset of "the six declared scope paths"; there are now seven. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-08 updated to SEVEN and told which one is expected to be declared-but-unmodified. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The cutover resolves `None` here, so the plan could ship as a no-op. Fail the item on `None`, hand-write a boundary, or accept fail-open? | FAIL the item on a `None` resolution in this repository, and require the stamp to be run and shown. | (a) Accept `None` as "fail-open as designed" (what V-01 did): REJECTED, it conflates two different situations - fail-open is correct for a FOREIGN repo with no boundary and is a silent self-defeat for the repo the plan is meant to protect, and it would let the plan pass every one of its own checks while doing nothing. (b) Instruct the executor to hand-write a date into `project.json`: REJECTED, the boundary decides which historical closes become enforceable, which is a maintainer policy choice, not an implementation detail; recorded as OQ-04 instead. (c) Drop the cutover and enforce everything: REJECTED outright, it would red CI on 53 historical items and contradicts the plan's whole blast-radius argument. | `resolve_cutover_date(repo, "setid_length")` measured `None` despite registration; `project.json` `cutovers` holding 5 keys without it; `installs.jsonl` absent so tier 2 cannot resolve; `sync_cutovers_on_install` verified against a copy to add the missing key and preserve existing boundaries; the `KNOWN_FEATURE_CUTOVERS` block comment's own "would ship as decoration" warning. | yes |
| D-2 | Should the at-rest arm default to on or off? | OFF (`at_rest=False`), with one explicit `at_rest=True` at `check_release_gates`. | `at_rest=True` by default, as E-05 suggested: REJECTED on two measurements. It widens three callers that must stay commit-scoped (aggregator, opt-in hook, scope gate), making safety depend on remembering three disables rather than on construction; and the aggregator composes bare callables as `fn(repo_root)` with no argument site, so a `True` default would force unrolling that loop and lift one rule out of its `except Exception: continue` guard. A `False` default leaves the tuple untouched and the hook untouched. | `check_commit_invariants`' composition loop read in full including the guard comment; `hooks/backlog_blocking_close_gate.check`'s direct call; the aggregator's own "DELIBERATELY *NOT* added inside `check_commit_invariants`" comment; `AGENTS.md`'s shared-checkout rule. | yes |
| D-3 | OQ-02 asks whether draft spec `pqsx96` row I-07 needs amending. Resolve it, or leave it open? | LEAVE IT OPEN with `Owner: maintainer`, unchanged. | (a) Resolve it "no amendment needed" on the reviewer's authority: REJECTED, the plan's reasoning is already sound (nothing in the row becomes false) but the question is about SPEC WORDING a maintainer owns, and editing a spec under active authorship by another agent is the collision the shared-checkout rule warns about. (b) Amend the spec in this plan: REJECTED for the same reason plus it is outside `- Scope-Paths:`. | The plan's own reasoning verified: `pqsx96` is `- Status: draft`; its I-07 honest-limits column speaks about the local hook's reach, not the check's temporal scope, so the row survives this plan. Non-interactive run (`AW_EXECUTION_ROLE=worker`, no TTY) so the maintainer could not be asked. | yes |
| D-4 | The verdict is `REVIEWED - OPEN QUESTIONS`, which the readiness table lists as a `NO-GO` condition, while the ruling below it says a non-blocking question does not gate. Which governs? | `go-pending-approval`. | Write `no-go` per the table's literal text: REJECTED, it contradicts the 2026-09-10 maintainer ruling recorded in the same section and would hold a plan whose two open questions its author and this review both judged non-stopping. Omitting the field: REJECTED, automation fails closed on absence and would strand a reviewed plan. | Repository precedent is one-directional: 66 of 77 review records with this verdict correspond to plans carrying `go-pending-approval`, 11 to `no-go`, and every sampled `no-go` carries a `Blocking: yes` question still open. `b24o3q` carries zero `Blocking: yes` questions (measured). | yes |
| D-5 | Should review re-run the 84 s per-item measurement and the full corpus census, or accept them? | RE-RUN both. | Accept the recorded figures: REJECTED. The census is the plan's justification (if the population were empty the plan would be unwarranted) and the timing is its design constraint (if the naive form were cheap, E-04 would be over-engineering), so both are load-bearing and both are exactly the kind of claim that rots daily. Re-running cost about two minutes and found that every number had drifted, that one of them now collides with the `2o5wka` prediction, and that F-03's conclusion had strengthened. | Re-measured: 242 gated / 189 legitimate / 53 illegitimate; 63.1 s per-item versus 0.389 s indexed; 226 closed-later; 27-versus-0 at the boundary; illegitimate newest close 20260926 with 0 on or after the boundary. | yes |
